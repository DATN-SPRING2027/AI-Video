#!/usr/bin/env python3
"""
ComfyUI REST API Client for Wan 2.2 TI2V-5B GGUF (Optimized for 6GB VRAM GPUs).
Allows Antigravity / CLI scripts to generate Text-to-Video or Image-to-Video MP4/WebM clips
automatically via a running ComfyUI server (http://127.0.0.1:8188).
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_NEGATIVE = (
    "blurry, low quality, distorted, watermark, text, deformed, static, "
    "overexposed, underexposed, worst quality, artifacts"
)


def build_wan22_6gb_prompt(
    prompt: str,
    negative_prompt: str = DEFAULT_NEGATIVE,
    width: int = 832,
    height: int = 480,
    frames: int = 33,
    fps: float = 16.0,
    steps: int = 20,
    cfg: float = 5.0,
    seed: int | None = None,
    start_image_name: str | None = None,
) -> dict:
    if seed is None:
        seed = random.randint(1, 2**53 - 1)

    # Ensure multiples of 32 for Wan22ImageToVideoLatent (48-channel 16x spatial patch)
    width = max(256, (width // 32) * 32)
    height = max(256, (height // 32) * 32)
    # Wan temporal stride is 4n + 1
    frames = max(5, ((frames - 1) // 4) * 4 + 1)

    graph: dict = {
        "1": {
            "class_type": "UnetLoaderGGUF",
            "inputs": {"unet_name": "Wan2.2-TI2V-5B-Q4_K_M.gguf"},
        },
        "2": {
            "class_type": "CLIPLoaderGGUF",
            "inputs": {
                "clip_name": "umt5-xxl-encoder-Q4_K_M.gguf",
                "type": "wan",
            },
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "wan2.2_vae.safetensors"},
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["2", 0]},
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative_prompt, "clip": ["2", 0]},
        },
        "6": {
            "class_type": "Wan22ImageToVideoLatent",
            "inputs": {
                "vae": ["3", 0],
                "width": width,
                "height": height,
                "length": frames,
                "batch_size": 1,
            },
        },
        "7": {
            "class_type": "ModelSamplingSD3",
            "inputs": {"model": ["1", 0], "shift": 8.0},
        },
        "8": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "uni_pc",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["7", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0],
            },
        },
        "9": {
            "class_type": "VAEDecodeTiled",
            "inputs": {
                "samples": ["8", 0],
                "vae": ["3", 0],
                "tile_size": 256,
                "overlap": 64,
                "temporal_size": 16,
                "temporal_overlap": 4,
            },
        },
        "10": {
            "class_type": "CreateVideo",
            "inputs": {
                "images": ["9", 0],
                "fps": fps,
            },
        },
        "11": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["10", 0],
                "filename_prefix": "wan22/clip",
                "format": "mp4",
                "codec": "h264",
            },
        },
    }

    if start_image_name:
        graph["12"] = {
            "class_type": "LoadImage",
            "inputs": {"image": start_image_name},
        }
        graph["6"]["inputs"]["start_image"] = ["12", 0]

    return graph


def submit_and_wait(server_url: str, prompt_graph: dict, timeout_s: int = 1800) -> list[Path]:
    data = json.dumps({"prompt": prompt_graph}).encode("utf-8")
    req = urllib.request.Request(
        f"{server_url.rstrip('/')}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    prompt_id = payload["prompt_id"]
    print(f"[Wan 2.2] Queued prompt_id={prompt_id}. Waiting for GPU render...")

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        with urllib.request.urlopen(
            f"{server_url.rstrip('/')}/history/{prompt_id}", timeout=15
        ) as resp:
            hist = json.loads(resp.read().decode("utf-8"))
        if prompt_id in hist:
            entry = hist[prompt_id]
            outputs = entry.get("outputs", {})
            saved_files: list[Path] = []
            comfy_out = Path(__file__).resolve().parent / "output"
            for node_out in outputs.values():
                for key in ("images", "videos", "gifs"):
                    for item in node_out.get(key, []):
                        sub = item.get("subfolder", "")
                        fn = item.get("filename", "")
                        if fn:
                            saved_files.append(comfy_out / sub / fn)
            return saved_files
        time.sleep(3)
    raise TimeoutError(f"Timed out after {timeout_s}s waiting for Wan 2.2 render.")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Generate AI video via ComfyUI + Wan 2.2 TI2V-5B GGUF (6GB VRAM Ready)."
    )
    parser.add_argument("-p", "--prompt", required=True, help="Detailed English/Chinese visual prompt.")
    parser.add_argument("-n", "--negative", default=DEFAULT_NEGATIVE, help="Negative prompt.")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Copy resulting MP4 to this path.")
    parser.add_argument("--width", type=int, default=832, help="Width (multiple of 32, default 832 for 6GB VRAM).")
    parser.add_argument("--height", type=int, default=480, help="Height (multiple of 32, default 480 for 6GB VRAM).")
    parser.add_argument("--frames", type=int, default=33, help="Frame count 4n+1 (33 or 49 recommended on 6GB VRAM).")
    parser.add_argument("--fps", type=float, default=16.0, help="Output frame rate (default 16).")
    parser.add_argument("--steps", type=int, default=20, help="Sampling steps (default 20).")
    parser.add_argument("--seed", type=int, default=None, help="Random seed.")
    parser.add_argument("--image", type=Path, default=None, help="Optional start image for Image-to-Video.")
    parser.add_argument("--server", default="http://127.0.0.1:8188", help="ComfyUI server URL.")
    parser.add_argument("--dump-json", type=Path, default=None, help="Only export API workflow JSON without running.")
    args = parser.parse_args()

    start_img_name = None
    if args.image:
        in_dir = Path(__file__).resolve().parent / "input"
        in_dir.mkdir(parents=True, exist_ok=True)
        dest_img = in_dir / args.image.name
        shutil.copy2(args.image, dest_img)
        start_img_name = args.image.name

    graph = build_wan22_6gb_prompt(
        prompt=args.prompt,
        negative_prompt=args.negative,
        width=args.width,
        height=args.height,
        frames=args.frames,
        fps=args.fps,
        steps=args.steps,
        seed=args.seed,
        start_image_name=start_img_name,
    )

    if args.dump_json:
        args.dump_json.parent.mkdir(parents=True, exist_ok=True)
        args.dump_json.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[Wan 2.2] Exported API workflow JSON to: {args.dump_json}")
        return 0

    files = submit_and_wait(args.server, graph)
    if not files:
        raise RuntimeError("Render finished in ComfyUI, but no video file path was returned.")

    latest = files[-1]
    print(f"[Wan 2.2] Generated video: {latest}")
    if args.output and latest.exists():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(latest, args.output)
        print(f"[Wan 2.2] Copied to: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
