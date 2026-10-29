# REVIEW — Continuum AI Launch & Capstone Defense Video (`continuum-launch`)

## 1. Creative & Engineering Decisions
- **Aesthetic & Brand Alignment:** Strictly aligned with `design-system/continuum-ai/MASTER.md` (Linear / Vercel / Stripe B2B precision). Scenes 1, 4, and 5 use dark studio ground (`#0B0F19` / `#111827`) to frame the incident hook, dark-canvas 3D Knowledge Graph, and architectural pillars; Scenes 2 and 3 open into crisp light B2B SaaS workspaces (`#F9FAFB` / `#FFFFFF`) with WCAG AAA semantic badges (`PROPOSED` `#92400E` on `#FEF3C7`, `ACTIVE` `#065F46` on `#D1FAE5`, `403 / Gap` `#991B1B` on `#FEE2E2`).
- **Authentic Multi-Tool Pipeline:**
  - **2D-3D Knowledge Graph (`kg-links`):** Compiled 25 real Continuum AI Markdown architecture notes (`graph-vault/`) into `assets/data/continuum-links.json` (`25 nodes, 72 links`).
  - **Cloud Vietnamese AI TTS (`lucylab-tts` — LucyLab JSON-RPC + TikTok Neural `BV075_streaming`) + Faster-Whisper (`small`):** Configured dynamic `.env` integration (`VIETNAMESE_API_KEY`, `VIETNAMESE_VOICEID_MALE`, `VIETNAMESE_VOICEID_FEMALE`, `TIKTOK_SESSION_ID`) via `CreateVideo/lucylab-tts/lucylab_tts.py`. Synthesized all 5 scene voiceovers into a `75.0s` `48000 Hz` `vo-master.wav`, extracted real word-level timestamps (`vo-master.transcript.json`), and auto-synced 13 clean Vietnamese subtitle cues across `vo-master.srt` and `compositions/captions-overlay.html` (with `--offline` fallback to `piper-tts`).
  - **ACE-Step 1.5 (`acestep-v15-turbo` on RTX 4050 CUDA + `flash_attention_2`):** Generated a custom `75.0s`, `120 BPM` (`C major`, `4/4`) instrumental electronic product-launch score (`assets/audio/bgm-120bpm.wav`), verified by `npx hyperframes beats .` (`141 beats`, `bpm 120, high`).
  - **FFmpeg 8.1.1:** Mastered two separate `1920x1080` `30fps` H.264 (`+faststart`) deliverables:
    1. `dist/continuum-ai-full-vo-sub.mp4` — Styled Vietnamese captions + `-16 LUFS` voiceover + sidechain-ducked BGM + muxed `.srt` (`mov_text`) subtitle track.
    2. `dist/continuum-ai-clean.mp4` — Clean visuals + `-18 LUFS` BGM only (no voiceover, no burned captions) for live speaking during the Capstone Defense.
- **Storylines Intentionally Deferred:** Skipped generative AI B-roll (`ComfyUI + Wan 2.2`) so 100% of frames remain razor-sharp vector/canvas B2B product UI at `1920x1080`.

## 2. Measured vs. Visually Inspected
- **Measured (`npx hyperframes check --json`):**
  - `lint`: `0 errors` (`7 files scanned`)
  - `runtime`: `0 errors, 0 warnings`
  - `layout`: `0 errors, 0 warnings, 0 info` (`totalIssueCount: 0`)
  - `contrast`: `49/49 passed` (`0 errors, 0 warnings`)
  - `craft`: `0 errors, 0 warnings` across `599` temporal samples
  - `audio`: `0 errors, 0 warnings` (`141 beats` detected at `120 BPM`)
- **Visually Inspected (`npx hyperframes snapshot`):**
  - Audited 14 full-HD snapshots across every shot (`1.5s, 5.5s, 10.3s, 13.5s, 18s, 24s, 30s, 37s, 43s, 50s, 58s, 65s, 71s, 74.75s`).
  - Fixed 3 visual findings caught in Pass 1 (`t=5.5s` & `t=50s` 3D graph node spread + screen-space label collision guard; `t=10.3s` `UNVERIFIED HALLUCINATION` stamp clearance; `t=24s` `AI Extract` connector column width & right-anchored scale origin) and verified all 4 re-captured frames in Pass 2 & Pass 3.
- **Not Heard Directly:** Audio loudness (`LUFS`), peak ceiling (`-1.5 dBTP`), beat grid (`120 BPM`), and Whisper word timings were measured instrumentally; human ear listening is recommended for final subjective voiceover/music balance.

## 3. Weakest Shot & Future Upgrade Path
- **Weakest Shot:** `Shot 1.3` (`8.0s–12.0s`, Legacy RAG Hallucination) uses a static message layout before the crimson stamp lands at `9.5s`. With more time, adding a fast token-by-token streaming cursor for the fabricated answer (`8.2s–9.3s`) would heighten the tension right before the `9.5s` stamp.
- **Voiceover Upgrade:** Upgraded from offline `piper-tts` to `48kHz` Cloud Neural Vietnamese TTS (`lucylab_tts.py`). Once LucyLab account credits are topped up (`available > 0`), re-running `scripts/build_voiceover_and_srt.py --voice male --provider lucylab` will automatically switch from `TIKTOK_SESSION_ID` (`BV075_streaming`) to LucyLab's verified TVC voice (`TVC 4` / `Trung Quân` / `Thanh Mai`) and re-align `captions-overlay.html` in one command.

## 4. Intentional Warnings Kept
- `composition_file_too_large` on `compositions/scene-01-hook.html` (354 lines) and `compositions/scene-04-graph-handover.html` (373 lines): Kept intentionally so the 25-node, 72-edge graph dataset and deterministic 3D projection/collision-free renderer live self-contained inside each scene without any runtime `fetch()` calls (per HyperFrames deterministic render contract).

