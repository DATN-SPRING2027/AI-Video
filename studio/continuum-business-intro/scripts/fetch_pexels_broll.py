#!/usr/bin/env python3
"""
Fetch curated 1920x1080 landscape corporate B-Roll clips via MoneyPrinterTurbo's
Pexels integration (app.services.material) without copying or exposing API keys.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

CREATE_VIDEO_ROOT = Path(__file__).resolve().parents[3]
MPT_ROOT = CREATE_VIDEO_ROOT / "MoneyPrinterTurbo"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BROLL_DIR = PROJECT_ROOT / "assets" / "broll"
RAW_CACHE_DIR = CREATE_VIDEO_ROOT / ".cache" / "mpt-pexels-raw"

sys.path.insert(0, str(MPT_ROOT))
os.chdir(MPT_ROOT)

from app.models.schema import VideoAspect  # noqa: E402
from app.services.material import save_video, search_videos_pexels  # noqa: E402

SCENES = [
    {
        "id": "broll-01-pain-leaving",
        "queries": [
            "employee packing box office",
            "office worker leaving desk box",
            "stressed manager paperwork office",
        ],
        "trim_seconds": 7.5,
    },
    {
        "id": "broll-02-pain-overwhelmed",
        "queries": [
            "stressed office worker laptop paperwork",
            "confused employee computer office",
            "frustrated businessman desk documents",
        ],
        "trim_seconds": 7.5,
    },
    {
        "id": "broll-03-solution-team",
        "queries": [
            "modern office team collaboration laptop",
            "happy coworkers working together office",
        ],
        "trim_seconds": 8.0,
    },
    {
        "id": "broll-04-solution-handover",
        "queries": [
            "mentor training new employee laptop office",
            "two colleagues discussing project computer",
        ],
        "trim_seconds": 8.0,
    },
    {
        "id": "broll-05-ai-clarity",
        "queries": [
            "confident manager working laptop modern office",
            "creative team meeting glass board office",
        ],
        "trim_seconds": 7.5,
    },
    {
        "id": "broll-06-outcome-success",
        "queries": [
            "business team handshake office success",
            "happy business team celebrating office",
        ],
        "trim_seconds": 7.5,
    },
]


def find_ffmpeg() -> str:
    ff = shutil.which("ffmpeg")
    if ff:
        return ff
    for candidate in CREATE_VIDEO_ROOT.rglob("ffmpeg.exe"):
        return str(candidate)
    raise RuntimeError("ffmpeg not found in PATH or CreateVideo")


def normalize_clip(ffmpeg_bin: str, src: Path, dst: Path, duration: float) -> None:
    cmd = [
        ffmpeg_bin,
        "-y",
        "-i",
        str(src),
        "-t",
        f"{duration:.2f}",
        "-vf",
        "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,format=yuv420p",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "20",
        "-g",
        "30",
        "-keyint_min",
        "30",
        "-movflags",
        "+faststart",
        str(dst),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    BROLL_DIR.mkdir(parents=True, exist_ok=True)
    RAW_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ffmpeg_bin = find_ffmpeg()

    used_urls: set[str] = set()
    manifest: list[dict] = []

    for scene in SCENES:
        chosen = None
        matched_query = ""
        for q in scene["queries"]:
            items = search_videos_pexels(
                search_term=q,
                minimum_duration=6,
                video_aspect=VideoAspect.landscape,
            )
            for item in items:
                if item.url not in used_urls:
                    chosen = item
                    matched_query = q
                    used_urls.add(item.url)
                    break
            if chosen:
                break

        if not chosen:
            raise RuntimeError(f"No Pexels 1920x1080 clip found for {scene['id']}")

        raw_path_str = save_video(chosen.url, save_dir=str(RAW_CACHE_DIR))
        if not raw_path_str:
            raise RuntimeError(f"Failed downloading clip for {scene['id']}")

        out_path = BROLL_DIR / f"{scene['id']}.mp4"
        normalize_clip(ffmpeg_bin, Path(raw_path_str), out_path, scene["trim_seconds"])
        size_mb = round(out_path.stat().st_size / (1024 * 1024), 2)
        print(f"[OK] {scene['id']} <- '{matched_query}' ({size_mb} MB)")
        manifest.append(
            {
                "id": scene["id"],
                "query": matched_query,
                "provider": chosen.provider,
                "source_duration": chosen.duration,
                "trimmed_seconds": scene["trim_seconds"],
                "file": f"assets/broll/{scene['id']}.mp4",
                "size_mb": size_mb,
            }
        )

    manifest_path = BROLL_DIR / "broll-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved manifest -> {manifest_path}")


if __name__ == "__main__":
    main()
