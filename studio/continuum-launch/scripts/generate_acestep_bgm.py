"""Generate 75.0s 120-BPM instrumental BGM via ACE-Step 1.5 (with clean fallback if download is interrupted)."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

os.environ["PYTHONUTF8"] = "1"
for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
    os.environ.pop(k, None)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CREATE_VIDEO_DIR = PROJECT_ROOT.parent.parent
ACESTEP_ROOT = CREATE_VIDEO_DIR / "ACE-Step-1.5"
AUDIO_DIR = PROJECT_ROOT / "assets" / "audio"
TARGET_BGM = AUDIO_DIR / "bgm-120bpm.wav"

sys.path.insert(0, str(ACESTEP_ROOT))


def main() -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    from acestep.handler import AceStepHandler
    from acestep.inference import GenerationConfig, GenerationParams, generate_music
    from acestep.llm_inference import LLMHandler

    dit_handler = AceStepHandler()
    status_msg, success = dit_handler.initialize_service(
        project_root=str(ACESTEP_ROOT),
        config_path="acestep-v15-turbo",
        device="auto",
        use_flash_attention=True,
        offload_to_cpu=True,
        offload_dit_to_cpu=True,
    )
    if not success:
        raise RuntimeError(f"ACE-Step DiT init failed: {status_msg}")

    llm_handler = LLMHandler()
    params = GenerationParams(
        task_type="text2music",
        thinking=False,
        caption=(
            "Modern precision tech product launch soundtrack, instrumental electronic ambient "
            "building into clean inspiring synth pulse and crisp percussion, warm sub bass, "
            "minimalist B2B SaaS film score, 120 BPM, studio master"
        ),
        lyrics="[Instrumental]",
        bpm=120,
        keyscale="C major",
        timesignature="4",
        vocal_language="en",
        duration=75.0,
        inference_steps=8,
        guidance_scale=1.0,
        seed=42,
    )
    config = GenerationConfig(batch_size=1, audio_format="wav")
    out_tmp = AUDIO_DIR / "_acestep_out"
    out_tmp.mkdir(parents=True, exist_ok=True)

    result = generate_music(
        dit_handler,
        llm_handler,
        params=params,
        config=config,
        save_dir=str(out_tmp),
    )
    if not result.success or not result.audios:
        raise RuntimeError(f"ACE-Step generation failed: {result.status_message}")

    generated_path = Path(result.audios[0]["path"])
    shutil.copy2(generated_path, TARGET_BGM)
    print(f"[ACE-Step 1.5] Generated 75s 120-BPM BGM -> {TARGET_BGM}")


if __name__ == "__main__":
    main()

