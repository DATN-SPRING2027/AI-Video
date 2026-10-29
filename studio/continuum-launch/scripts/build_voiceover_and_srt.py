"""Synthesize 5 Vietnamese scene voiceovers via Cloud AI TTS (LucyLab / TikTok Neural, with offline Piper-TTS option),
assemble 75.0s 48kHz master WAV, transcribe via Faster-Whisper, and sync both vo-master.srt & captions-overlay.html."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CREATE_VIDEO_DIR = PROJECT_ROOT.parent.parent
AUDIO_DIR = PROJECT_ROOT / "assets" / "audio"
CAPTIONS_HTML = PROJECT_ROOT / "compositions" / "captions-overlay.html"

LUCYLAB_DIR = CREATE_VIDEO_DIR / "lucylab-tts"
if str(LUCYLAB_DIR) not in sys.path:
    sys.path.insert(0, str(LUCYLAB_DIR))

from lucylab_tts import InsufficientCreditsError, synthesize_cloud_vi  # noqa: E402

PIPER_PYTHON = CREATE_VIDEO_DIR / "piper-tts" / ".venv" / "Scripts" / "python.exe"
PIPER_SPEAK = CREATE_VIDEO_DIR / "piper-tts" / "speak.py"
WHISPER_PYTHON = CREATE_VIDEO_DIR / "whisper" / ".venv" / "Scripts" / "python.exe"
WHISPER_SCRIPT = CREATE_VIDEO_DIR / "whisper" / "transcribe_srt.py"

# Each entry: (id, start_s, max_end_s, tts_spoken_vi, display_phrases)
SCENES = [
    (
        "vo-01",
        0.35,
        11.55,
        "Trong mọi dự án phần mềm, rủi ro lớn nhất là khoảnh khắc người hiểu rõ hệ thống rời đi. Tài liệu cũ kỹ, tin nhắn trôi mất, còn trí tuệ nhân tạo thông thường lại dễ bịa ra câu trả lời.",
        [
            "Trong mọi dự án phần mềm, rủi ro lớn nhất",
            "là khoảnh khắc người hiểu rõ hệ thống rời đi.",
            "Tài liệu cũ kỹ, chat trôi mất, còn AI thường dễ bịa câu trả lời.",
        ],
    ),
    (
        "vo-02",
        12.35,
        26.55,
        "Cơn ti niu um ây ai biến công việc hằng ngày thành dòng chảy tri thức sống. Mọi ghi chú và phiên ghi âm bàn giao đều được bóc tách tự động, rồi kiểm chứng bởi chuyên gia trước khi kích hoạt.",
        [
            "Continuum AI biến công việc hằng ngày thành dòng chảy tri thức sống.",
            "Mọi Work Note và phiên ghi âm bàn giao được bóc tách tự động,",
            "rồi kiểm chứng bởi chuyên gia trước khi kích hoạt ACTIVE.",
        ],
    ),
    (
        "vo-03",
        27.35,
        44.55,
        "Hệ thống khóa phân quyền ngay trước khi truy hồi dữ liệu. Mọi câu trả lời từ ét a gờ en gin đều đính kèm trích dẫn và mã băm minh bạch, hoặc tự động đánh dấu khoảng trống tri thức khi thiếu bằng chứng.",
        [
            "Hệ thống khóa phân quyền Pre-Retrieval ACL trước khi truy hồi dữ liệu.",
            "Mọi câu trả lời từ SAG Engine đều đính kèm trích dẫn và mã băm SHA-256,",
            "hoặc tự động đánh dấu Knowledge Gap khi thiếu bằng chứng.",
        ],
    ),
    (
        "vo-04",
        45.35,
        61.55,
        "Từ bản đồ tri thức hai chiều, ba chiều trực quan đến lộ trình bàn giao tự động, thành viên kế nhiệm có thể nắm bắt toàn bộ ngữ cảnh dự án ngay từ ngày đầu tiên.",
        [
            "Từ bản đồ tri thức 2D / 3D trực quan đến lộ trình bàn giao tự động,",
            "thành viên kế nhiệm nắm bắt toàn bộ ngữ cảnh dự án ngay từ ngày đầu tiên.",
        ],
    ),
    (
        "vo-05",
        62.35,
        73.80,
        "Cơn ti niu um ây ai. Bảo toàn tri thức, minh bạch dẫn chứng, sẵn sàng cho mọi thế hệ kế tiếp của dự án.",
        [
            "Continuum AI — Bảo toàn tri thức, minh bạch dẫn chứng,",
            "sẵn sàng cho mọi thế hệ kế tiếp của dự án.",
        ],
    ),
]


def _format_srt_ts(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1_000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _read_wav_mono(path: Path, sample_rate: int = 48000) -> np.ndarray:
    norm_path = path.with_suffix(".norm.wav")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-ar",
            str(sample_rate),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(norm_path),
        ],
        check=True,
    )
    with wave.open(str(norm_path), "rb") as wf:
        frames = wf.readframes(wf.getnframes())
    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    norm_path.unlink(missing_ok=True)
    return samples


def _time_fit_if_needed(raw_wav: Path, max_dur: float) -> Path:
    with wave.open(str(raw_wav), "rb") as wf:
        dur = wf.getnframes() / float(wf.getframerate())
    if dur <= max_dur:
        return raw_wav
    ratio = min(1.35, (dur / max_dur) * 1.03)
    fitted = raw_wav.with_name(raw_wav.stem + "-fit.wav")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(raw_wav),
            "-filter:a",
            f"atempo={ratio:.3f}",
            str(fitted),
        ],
        check=True,
    )
    return fitted


def _align_phrases_to_whisper(
    whisper_json: dict,
    placed_windows: list[tuple[str, float, float, list[str]]],
) -> list[dict]:
    """Use Whisper's exact detected word timestamps inside each scene window to time clean display phrases."""
    all_words: list[dict] = []
    for seg in whisper_json.get("segments", []):
        for w in seg.get("words", []):
            all_words.append(w)

    aligned: list[dict] = []
    idx = 1
    for seg_id, win_start, win_end, phrases in placed_windows:
        scene_words = [
            w for w in all_words if (w["start"] >= win_start - 0.25 and w["end"] <= win_end + 0.35)
        ]
        if scene_words:
            speech_start = max(win_start, float(scene_words[0]["start"]))
            speech_end = min(win_end + 0.15, float(scene_words[-1]["end"]) + 0.12)
        else:
            speech_start = win_start
            speech_end = win_end

        char_counts = [max(1, len(p)) for p in phrases]
        total_chars = sum(char_counts)
        cursor = speech_start
        cum_chars = 0
        for p_i, phrase in enumerate(phrases):
            cum_chars += char_counts[p_i]
            if p_i == len(phrases) - 1:
                p_end = speech_end
            else:
                frac = cum_chars / total_chars
                target_t = speech_start + frac * (speech_end - speech_start)
                if scene_words:
                    nearest = min(scene_words, key=lambda w: abs(float(w["end"]) - target_t))
                    p_end = max(cursor + 0.8, min(speech_end - 0.6, float(nearest["end"])))
                else:
                    p_end = target_t
            aligned.append(
                {
                    "index": idx,
                    "scene": seg_id,
                    "start": round(cursor, 2),
                    "end": round(p_end, 2),
                    "text": phrase,
                }
            )
            idx += 1
            cursor = round(p_end + 0.06, 2)
    return aligned


def _sync_captions_overlay_html(captions: list[dict]) -> None:
    if not CAPTIONS_HTML.exists():
        return
    html = CAPTIONS_HTML.read_text(encoding="utf-8")
    cue_lines = [
        f'        {{ id: "#cap-g{c["index"]}", start: {c["start"]:.2f}, end: {c["end"]:.2f} }}'
        for c in captions
    ]
    replacement_block = "const CUES = [\n" + ",\n".join(cue_lines) + "\n      ];"
    updated, count = re.subn(
        r"const\s+CUES\s*=\s*\[.*?\];",
        replacement_block,
        html,
        count=1,
        flags=re.S,
    )
    if count == 1:
        CAPTIONS_HTML.write_text(updated, encoding="utf-8")
        print(f"[HyperFrames] Synced {len(captions)} caption cue timings into {CAPTIONS_HTML.name}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Build 75.0s Continuum AI voiceover, Whisper SRT, and synced captions.")
    parser.add_argument("--voice", default="male", help="Voice alias ('male', 'female', or LucyLab voiceId).")
    parser.add_argument(
        "--provider",
        choices=("auto", "lucylab", "tiktok"),
        default="auto",
        help="Cloud TTS provider ('auto' tries LucyLab then TikTok Neural fallback).",
    )
    parser.add_argument("--offline", action="store_true", help="Use offline Piper-TTS instead of Cloud TTS.")
    args = parser.parse_args()

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    sample_rate = 48000
    total_samples = int(75.0 * sample_rate)
    master = np.zeros(total_samples, dtype=np.float32)
    placed_windows: list[tuple[str, float, float, list[str]]] = []

    active_provider = args.provider

    for seg_id, start_s, end_s, tts_text, phrases in SCENES:
        out_wav = AUDIO_DIR / f"{seg_id}.wav"
        if args.offline:
            print(f"[Piper-TTS] Synthesizing {seg_id} ({start_s:.2f}s - {end_s:.2f}s)...")
            subprocess.run(
                [
                    str(PIPER_PYTHON),
                    str(PIPER_SPEAK),
                    "--text",
                    tts_text,
                    "--output",
                    str(out_wav),
                    "--voice",
                    "vi_VN-vais1000-medium",
                ],
                check=True,
            )
        else:
            print(f"[Cloud-TTS:{active_provider}] Synthesizing {seg_id} ({start_s:.2f}s - {end_s:.2f}s, voice={args.voice})...")
            try:
                meta = synthesize_cloud_vi(
                    text=tts_text,
                    output_path=out_wav,
                    voice=args.voice,
                    provider=active_provider,
                    sample_rate=sample_rate,
                )
                # Once auto-fallback discovers LucyLab has 0 credits on scene 1, avoid redundant failed RPC calls on scenes 2..5
                if active_provider == "auto" and meta.get("provider") == "tiktok":
                    active_provider = "tiktok"
            except InsufficientCreditsError:
                raise

        max_slot = end_s - start_s
        usable_wav = _time_fit_if_needed(out_wav, max_slot)
        samples = _read_wav_mono(usable_wav, sample_rate=sample_rate)
        if usable_wav != out_wav:
            usable_wav.unlink(missing_ok=True)

        offset = int(round(start_s * sample_rate))
        end_idx = min(total_samples, offset + len(samples))
        master[offset:end_idx] = samples[: end_idx - offset]
        actual_dur = (end_idx - offset) / sample_rate
        placed_windows.append((seg_id, start_s, start_s + actual_dur, phrases))
        print(f"  -> Placed {seg_id}: start={start_s:.2f}s, duration={actual_dur:.2f}s (slot={max_slot:.2f}s)")

    peak = float(np.max(np.abs(master)))
    if peak > 0:
        master = master * (0.86 / peak)

    master_wav = AUDIO_DIR / "vo-master.wav"
    pcm = np.clip(master * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(master_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())

    print(f"[Audio] Wrote 75.0s 48kHz master voiceover: {master_wav}")
    print("[Whisper] Running faster-whisper word-timestamp & SRT extraction (CPU int8)...")
    subprocess.run(
        [
            str(WHISPER_PYTHON),
            str(WHISPER_SCRIPT),
            str(master_wav),
            "--model",
            "small",
            "--device",
            "cpu",
            "--language",
            "vi",
            "--initial-prompt",
            "Continuum AI, SAG Engine, Pre-Retrieval ACL, Work Note, dự án phần mềm, rủi ro, tri thức, mã băm, trích dẫn, bàn giao.",
            "--out-dir",
            str(AUDIO_DIR),
        ],
        check=True,
    )

    srt_path = AUDIO_DIR / "vo-master.srt"
    raw_srt_path = AUDIO_DIR / "vo-master.raw-asr.srt"
    shutil.copyfile(srt_path, raw_srt_path)

    whisper_json = json.loads((AUDIO_DIR / "vo-master.transcript.json").read_text(encoding="utf-8"))
    captions = _align_phrases_to_whisper(whisper_json, placed_windows)

    srt_blocks = [
        f"{c['index']}\n{_format_srt_ts(c['start'])} --> {_format_srt_ts(c['end'])}\n{c['text']}\n"
        for c in captions
    ]
    srt_path.write_text("\n".join(srt_blocks), encoding="utf-8")
    (AUDIO_DIR / "vo-master.captions.json").write_text(
        json.dumps(captions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[Captions] Wrote {len(captions)} Whisper-synced clean Vietnamese caption cues -> {srt_path}")
    _sync_captions_overlay_html(captions)


if __name__ == "__main__":
    main()
