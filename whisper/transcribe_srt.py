"""Whisper CLI utility for generating SRT subtitles, plain transcripts, and word timestamps."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterable

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"


def _register_nvidia_dlls() -> None:
    """Register nvidia-cublas-cu12 / nvidia-cudnn-cu12 DLL directories on Windows."""
    if os.name != "nt":
        return
    nvidia_root = BASE_DIR / ".venv" / "Lib" / "site-packages" / "nvidia"
    if not nvidia_root.exists():
        return
    extra_bins = [str(p) for p in nvidia_root.glob("*/bin") if p.is_dir()]
    if not extra_bins:
        return
    for b in extra_bins:
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(b)
            except OSError:
                pass
    os.environ["PATH"] = os.pathsep.join(extra_bins + [os.environ.get("PATH", "")])


def _format_srt_timestamp(seconds: float) -> str:
    """Format seconds into SubRip (HH:MM:SS,mmm) timestamp format."""
    total_ms = max(0, int(round(seconds * 1000)))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1_000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(segments: Iterable[dict], out_path: Path) -> None:
    """Write segment dictionaries to a UTF-8 .srt subtitle file."""
    lines: list[str] = []
    for idx, seg in enumerate(segments, start=1):
        start_ts = _format_srt_timestamp(float(seg["start"]))
        end_ts = _format_srt_timestamp(float(seg["end"]))
        text = str(seg["text"]).strip()
        if not text:
            continue
        lines.append(f"{idx}\n{start_ts} --> {end_ts}\n{text}\n")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _run_transcribe(
    model_name: str,
    device: str,
    input_path: Path,
    language: str | None,
    initial_prompt: str | None = None,
):
    from faster_whisper import WhisperModel

    compute_type = "int8" if device == "cpu" else "int8_float16"
    model = WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
        download_root=str(MODELS_DIR),
    )
    raw_segments, info = model.transcribe(
        str(input_path),
        language=language,
        initial_prompt=initial_prompt,
        word_timestamps=True,
        vad_filter=True,
    )
    return list(raw_segments), info


def main() -> None:
    """Run Faster-Whisper transcription on an input audio or video file."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    _register_nvidia_dlls()

    parser = argparse.ArgumentParser(
        description="Transcribe audio/video into SRT subtitles, TXT transcript, and JSON timestamps."
    )
    parser.add_argument("input", type=Path, help="Input audio or video file (.mp4, .mp3, .wav, .m4a)")
    parser.add_argument("--model", default="small", help="Whisper model size (tiny, base, small, medium, large-v3)")
    parser.add_argument("--language", default=None, help="Language code (e.g. vi, en) or omit for auto-detect")
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"], help="Execution device")
    parser.add_argument("--initial-prompt", default=None, help="Optional domain vocabulary hint for Whisper")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory (defaults to input file folder)")
    args = parser.parse_args()

    input_path = args.input.resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input media file not found: {input_path}")

    out_dir = (args.out_dir or input_path.parent).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem

    try:
        segments_list, info = _run_transcribe(
            args.model, args.device, input_path, args.language, args.initial_prompt
        )
    except Exception as exc:
        if args.device == "cpu":
            raise
        print(f"[Whisper] GPU unavailable ({exc}); falling back to CPU int8...", file=sys.stderr)
        segments_list, info = _run_transcribe(
            args.model, "cpu", input_path, args.language, args.initial_prompt
        )

    collected: list[dict] = []
    for seg in segments_list:
        words = [
            {
                "word": w.word,
                "start": round(w.start, 3),
                "end": round(w.end, 3),
                "probability": round(w.probability, 3),
            }
            for w in (seg.words or [])
        ]
        collected.append(
            {
                "id": seg.id,
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": seg.text.strip(),
                "words": words,
            }
        )

    srt_path = out_dir / f"{stem}.srt"
    txt_path = out_dir / f"{stem}.txt"
    json_path = out_dir / f"{stem}.transcript.json"

    write_srt(collected, srt_path)
    txt_path.write_text("\n".join(s["text"] for s in collected if s["text"]), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "source": str(input_path),
                "language": info.language,
                "language_probability": round(info.language_probability, 4),
                "duration": round(info.duration, 3),
                "segments": collected,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Detected language: {info.language} ({info.language_probability:.1%})")
    print(f"SRT subtitles   : {srt_path}")
    print(f"Plain transcript: {txt_path}")
    print(f"Word JSON       : {json_path}")


if __name__ == "__main__":
    main()
