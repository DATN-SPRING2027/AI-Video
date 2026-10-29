---
name: ai-video-pipeline
description: End-to-end local AI video production orchestrator inside CreateVideo combining Piper TTS, Whisper SRT, HyperFrames + GSAP + Three.js + 2D/3D Knowledge Graph, ComfyUI/Wan 2.2 (6GB VRAM GGUF), ACE-Step 1.5 Music, and FFmpeg post-production.
---

# AI Video Studio Pipeline (CreateVideo)

Use this skill whenever the user asks to generate a complete explainer, motion graphics, 3D knowledge-graph, or AI B-roll video from a single prompt inside `F:\LEARN KÌ 8\ĐATN\CreateVideo`.

## Hardware Constraints (Mandatory)

- **GPU**: NVIDIA GeForce RTX 4050 Laptop GPU (**6 GB VRAM**).
- **Disk**: Keep all caches and outputs on `F:\LEARN KÌ 8\ĐATN\CreateVideo` (`HF_HOME`, `UV_CACHE_DIR`), never filling `C:`.
- **Sequential GPU Rule**: Never run **ACE-Step 1.5** and **ComfyUI Wan 2.2** simultaneously on the 6 GB GPU. Generate music and AI B-roll sequentially so each model gets the full 6 GB VRAM.

## 6-Stage Automated Production Pipeline

### Stage 1 — Script & Vietnamese/English Voiceover (Piper TTS)
1. Write narration script (`.txt` UTF-8) and measure exact audio duration using `ffprobe` so visual scenes match narration timing to the millisecond:
   ```powershell
   .\run-piper-tts.bat --file studio\script.txt studio\voiceover.wav vi_VN-vais1000-medium
   ffprobe -v error -show_entries format=duration -of csv=p=0 studio\voiceover.wav
   ```
   Available voices in `piper-tts\voices\`:
   - `vi_VN-vais1000-medium` (Primary Vietnamese voice)
   - `vi_VN-25hours_single-low` (Alternative Vietnamese voice)
   - `vi_VN-vivos-x_low` (Fast Vietnamese voice)
   - `en_US-lessac-medium` (English narration voice)

### Stage 2 — Word-Accurate Subtitles (Whisper)
Generate `.srt` and word-level `.transcript.json` directly from `voiceover.wav`:
```powershell
.\run-whisper-srt.bat studio\voiceover.wav small vi
```
Use the timestamps in `voiceover.transcript.json` to synchronize GSAP / Three.js scene transitions in HyperFrames!

### Stage 3 — AI Realistic B-Roll Clips (Optional — ComfyUI + Wan 2.2 TI2V-5B GGUF)
When realistic footage (nature, people, cities, cinematic B-roll) is needed:
1. Ensure ComfyUI is running (`.\start-comfyui-wan22.bat` on `http://127.0.0.1:8188`).
2. Call the CLI client (keep `832x480`, `33` or `49` frames for 6 GB VRAM safety):
   ```powershell
   .\ComfyUI\.venv\Scripts\python.exe .\ComfyUI\generate_wan22_api.py `
     --prompt "Cinematic aerial view of modern city skyline at dusk, golden hour, smooth drone motion" `
     --width 832 --height 480 --frames 33 --fps 16 `
     --output studio\broll_clip1.mp4
   ```

### Stage 4 — Motion Graphics, 3D Scenes & Knowledge Graph Capture (HyperFrames + GSAP + Three.js + Playwright)
- Offline vendor bundles live in `studio\vendor\gsap\` and `studio\vendor\three\`.
- Build deterministic GSAP / Three.js / 2D-3D Knowledge Graph HTML compositions (see `studio\demo-video` and `studio\threejs-gsap-demo`), set `data-duration` to match `voiceover.wav`, validate, and render to 1080p MP4:
  ```powershell
  npx hyperframes check
  npx hyperframes render -o raw_visuals.mp4
  ```

### Stage 5 — AI Background Music (ACE-Step 1.5)
Generate royalty-free background music via ACE-Step 1.5 (`.\start-acestep-music.bat` Web UI at `:7860` or `acestep-api` at `:8001`).

### Stage 6 — Final Master Composition (FFmpeg)
Merge `raw_visuals.mp4` + `voiceover.wav` + `bgm.wav` (20% volume) + burned-in `voiceover.srt` in a single pass:
```powershell
powershell -ExecutionPolicy Bypass -File .\ffmpeg-tools\media_pipeline.ps1 `
  -Action full-compose `
  -InputVideo studio\raw_visuals.mp4 `
  -InputVoice studio\voiceover.wav `
  -InputAudio studio\bgm.wav `
  -BgmVolume 0.18 `
  -InputSrt studio\voiceover.srt `
  -Output studio\final_master_1080p.mp4
```
