"""Render both HyperFrames visual masters (Captioned & Clean) and master final MP4 deliverables via FFmpeg."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
AUDIO_DIR = PROJECT_ROOT / "assets" / "audio"
DIST_DIR = PROJECT_ROOT / "dist"


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    print(">>", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render & master Continuum AI MP4 deliverables.")
    parser.add_argument(
        "--only-full",
        action="store_true",
        help="Only render & master continuum-ai-full-vo-sub.mp4 (skip re-rendering clean presentation master).",
    )
    args = parser.parse_args()

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    index_path = PROJECT_ROOT / "index.html"
    original_index = index_path.read_text(encoding="utf-8")

    raw_captioned = DIST_DIR / "_render-captioned.mp4"
    raw_clean = DIST_DIR / "_render-clean.mp4"
    final_full = DIST_DIR / "continuum-ai-full-vo-sub.mp4"
    final_clean = DIST_DIR / "continuum-ai-clean.mp4"

    vo_wav = AUDIO_DIR / "vo-master.wav"
    bgm_wav = AUDIO_DIR / "bgm-120bpm.wav"
    srt_file = AUDIO_DIR / "vo-master.srt"

    npx_cmd = "npx.cmd"

    try:
        # 1. Render full visual master (with styled captions overlay)
        print("[1/4] Rendering HyperFrames master with styled Vietnamese captions...")
        _run(
            [npx_cmd, "hyperframes", "render", "--fps", "30", "-o", str(raw_captioned)],
            cwd=PROJECT_ROOT,
        )

        if not args.only_full:
            # 2. Temporarily hide captions & VO to render clean presentation visual master
            print("[2/4] Rendering HyperFrames clean visual master (for live presentation)...")
            clean_html = re.sub(
                r'(<div\s+id="captions")',
                r'\1 data-hidden="true"',
                original_index,
                count=1,
            )
            clean_html = re.sub(
                r'(<audio\s+id="vo-track")',
                r'\1 data-hidden="true"',
                clean_html,
                count=1,
            )
            index_path.write_text(clean_html, encoding="utf-8")
            _run(
                [npx_cmd, "hyperframes", "render", "--fps", "30", "-o", str(raw_clean)],
                cwd=PROJECT_ROOT,
            )
    finally:
        # Always restore index.html to full Studio configuration
        index_path.write_text(original_index, encoding="utf-8")

    # 3. Master Full Narrated + Auto-Ducked BGM + Embedded SRT MP4
    print("[3/4] Mastering continuum-ai-full-vo-sub.mp4 via FFmpeg (VO -16 LUFS + Sidechain BGM + SRT + faststart)...")
    filter_full = (
        "[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        "loudnorm=I=-16:TP=-1.5:LRA=11,asplit=2[vo_main][vo_sc];"
        "[2:a]atrim=0:75,asetpts=PTS-STARTPTS,aresample=48000,"
        "aformat=sample_fmts=fltp:channel_layouts=stereo,"
        "afade=t=in:st=0:d=0.8,afade=t=out:st=72.5:d=2.5,"
        "volume=0.30[bgm_pre];"
        "[bgm_pre][vo_sc]sidechaincompress=threshold=0.02:ratio=5:attack=35:release=420[bgm_duck];"
        "[vo_main][bgm_duck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
        "alimiter=limit=0.92[aout]"
    )
    _run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(raw_captioned),
            "-i",
            str(vo_wav),
            "-i",
            str(bgm_wav),
            "-i",
            str(srt_file),
            "-filter_complex",
            filter_full,
            "-map",
            "0:v:0",
            "-map",
            "[aout]",
            "-map",
            "3:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-c:s",
            "mov_text",
            "-metadata:s:s:0",
            "language=vie",
            "-metadata:s:s:0",
            "title=Tieng Viet",
            "-t",
            "75",
            "-movflags",
            "+faststart",
            str(final_full),
        ]
    )

    if not args.only_full:
        # 4. Master Clean Presentation MP4 (Visuals + BGM -18 LUFS only, no VO, no captions)
        print("[4/4] Mastering continuum-ai-clean.mp4 via FFmpeg (BGM -18 LUFS + faststart)...")
        filter_clean = (
            "[1:a]atrim=0:75,asetpts=PTS-STARTPTS,aresample=48000,"
            "aformat=sample_fmts=fltp:channel_layouts=stereo,"
            "loudnorm=I=-18:TP=-1.5:LRA=11,"
            "afade=t=in:st=0:d=0.8,afade=t=out:st=72.5:d=2.5[aout]"
        )
        _run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(raw_clean),
                "-i",
                str(bgm_wav),
                "-filter_complex",
                filter_clean,
                "-map",
                "0:v:0",
                "-map",
                "[aout]",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-ar",
                "48000",
                "-t",
                "75",
                "-movflags",
                "+faststart",
                str(final_clean),
            ]
        )

    # Remove intermediate unmastered files
    raw_captioned.unlink(missing_ok=True)
    raw_clean.unlink(missing_ok=True)

    # Verify deliverables via ffprobe
    targets = (final_full,) if args.only_full else (final_full, final_clean)
    for target in targets:
        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=filename,duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels",
                "-of",
                "json",
                str(target),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        info = json.loads(probe.stdout)
        print(f"\n[Verified] {target.name}:")
        print(json.dumps(info, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

