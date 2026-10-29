# CreateVideo — AI Video Production Studio (Trọn Bộ 11 Công Cụ Chạy Local)

Thư mục `F:\LEARN KÌ 8\ĐATN\CreateVideo` đã được cài đặt đầy đủ **11 thành phần** để tự động hóa toàn bộ quy trình sản xuất video từ một câu lệnh: **Kịch bản → Giọng thuyết minh (TTS) → Phụ đề word-timestamp → Đồ thị tri thức 2D/3D + Motion Graphics (GSAP/Three.js/HyperFrames) → Cảnh quay AI thực tế (ComfyUI + Wan 2.2) → Nhạc nền AI (ACE-Step 1.5) → Ghép xuất MP4 1080p/4K (FFmpeg)**.

---

## 1. Cấu Hình Phần Cứng Thực Tế & Tối Ưu Hóa Đã Áp Dụng

- **GPU phát hiện trên máy:** `NVIDIA GeForce RTX 4050 Laptop GPU` — **6 GB VRAM (`6141 MiB`)**, Driver CUDA `13.4`.
- **Dung lượng ổ đĩa:** Ổ `F:` còn trống lớn (~80+ GB), ổ `C:` còn trống ít (~23 GB) → Toàn bộ mô hình AI, môi trường Python `.venv` và bộ nhớ đệm (`HF_HOME`, `UV_CACHE_DIR`, `whisper/models`) đã được **cấu hình lưu hoàn toàn trên ổ `F:`** trong `CreateVideo\`, không làm đầy ổ `C:`.
- **Giải pháp Wan 2.2 chuyên biệt cho 6 GB VRAM:**
  - Bản Wan 2.2 14B hoặc FP16/FP8 gốc (10–33 GB) sẽ gây tràn bộ nhớ (OOM) trên card 6 GB.
  - Hệ thống đã cài đặt **ComfyUI + `ComfyUI-GGUF`** kèm bộ trọng số lượng tử hóa **`Wan2.2-TI2V-5B-Q4_K_M.gguf` (3.27 GB)** + **`umt5-xxl-encoder-Q4_K_M.gguf` (3.49 GB, offload CPU)** + **`wan2.2_vae.safetensors` (1.34 GB, giải mã `VAEDecodeTiled`)** và cờ khởi động `--lowvram --reserve-vram 1.5`.
  - Hỗ trợ **cả 2 chế độ Text-to-Video và Image-to-Video** trong cùng một mô hình `TI2V-5B` ở độ phân giải an toàn `832x480` (`33`–`49` frames).
  - **Lưu ý vận hành 6 GB VRAM:** Không chạy đồng thời render nhạc `ACE-Step 1.5` và render video `ComfyUI Wan 2.2` cùng một lúc — hãy chạy nối tiếp từng bước để mỗi mô hình được sử dụng trọn vẹn 6 GB VRAM.

---

## 2. Bảng Trạng Thái Bộ Công Cụ & Thư Viện Đã Cài Đặt

| # | Công cụ | Đường dẫn trong `CreateVideo` | Vai trò trong Pipeline | Trạng thái |
| :- | :--- | :--- | :--- | :--- |
| **1** | **Antigravity + 13 AI Skills** | [`./.agent/skills`](./.agent/skills) | Nhận prompt, viết kịch bản, điều phối toàn bộ công cụ (`ai-video-pipeline`, `hyperframes`, `saas-product-demo-video`, `supercut`, `playwright-recast`, `shoot-demo-video`...) | Sẵn sàng |
| **2** | **2D–3D Knowledge Graph** | [`./2d-3d-knowledge-graph`](./2d-3d-knowledge-graph) & [`./studio/knowledge-graph-viewer`](./studio/knowledge-graph-viewer) | Trực quan hóa vũ trụ tri thức 2D, 3D Force Graph & 3D Semantic Graph | Đã build `dist/` + Demo |
| **3** | **HyperFrames (`v0.8.210`) + 456 Registry Items** | [`./node_modules/hyperframes`](./node_modules/hyperframes) & [`./hyperframes/registry`](./hyperframes/registry) | Dựng và xuất video MP4 frame-accurate từ HTML/CSS/JS/WebGL kèm 456 block/component sẵn có | Đã cài local + CLI |
| **4** | **GSAP (`v3.14.2` Full Free)** | [`./node_modules/gsap`](./node_modules/gsap) & [`./studio/vendor/gsap`](./studio/vendor/gsap) | Toàn bộ thư viện animation + plugins (`SplitText`, `MorphSVG`, `DrawSVG`, `CustomEase`, `MotionPath`...) chạy 100% offline | Đã cài local + offline bundle |
| **5** | **Three.js (`v0.186.1`)** | [`./node_modules/three`](./node_modules/three) & [`./studio/threejs-gsap-demo`](./studio/threejs-gsap-demo) | Dựng cảnh không gian 3D WebGL & điều khiển quỹ đạo camera | Đã cài local + project mẫu 3D |
| **6** | **Playwright (`v1.58.2`)** | [`./node_modules/playwright`](./node_modules/playwright) | Tự động hóa trình duyệt Headless Chromium để chụp/quay khung hình chuẩn xác | Đã cài + Chromium 156 OK |
| **7** | **ComfyUI + Wan 2.2 (`TI2V-5B GGUF`)** | [`./ComfyUI`](./ComfyUI) | Tạo cảnh quay AI thực tế từ văn bản (Text-to-Video) hoặc từ ảnh (Image-to-Video) tối ưu cho 6 GB VRAM | Đã cài CUDA 12.8 + 8.1 GB models |
| **8** | **Piper TTS (`v1.8.0`)** | [`./piper-tts`](./piper-tts) | Tổng hợp giọng thuyết minh offline Tiếng Việt (`vais1000-medium`, `25hours_single-low`, `vivos-x_low`) & Tiếng Anh (`lessac-medium`) | Đã cài + 4 giọng đọc `.onnx` |
| **8b** | **LucyLab & TikTok Cloud TTS** | [`./lucylab-tts`](./lucylab-tts) & [`./run-lucylab-tts.bat`](./run-lucylab-tts.bat) | Tổng hợp giọng thuyết minh Tiếng Việt Cloud chất lượng cao qua `https://api.lucylab.io/json-rpc` (`VIETNAMESE_API_KEY`) + tự động fallback TikTok Neural (`BV075_streaming` Nam / `BV074_streaming` Nữ qua `TIKTOK_SESSION_ID`) từ `.env` | Sẵn sàng (`48kHz PCM WAV`) |
| **9** | **ACE-Step 1.5** | [`./ACE-Step-1.5`](./ACE-Step-1.5) | Sáng tác nhạc nền AI miễn phí bản quyền chạy local trên GPU CUDA 12.8 | Đã cài `.venv` PyTorch `cu128` |
| **10** | **Whisper AI (`faster-whisper`)** | [`./whisper`](./whisper) | Chuyển giọng đọc thành phụ đề `.srt`, `.txt` và `.transcript.json` (có GPU cuBLAS/cuDNN + tự động fallback CPU) | Đã cài + model `small` offline |
| **11** | **FFmpeg (`v8.1.1-full_build`)** | [`./ffmpeg-tools/media_pipeline.ps1`](./ffmpeg-tools/media_pipeline.ps1) | Ghép video + giọng thuyết minh Piper + nhạc nền ACE-Step + đóng phụ đề `.srt` ra MP4 hoàn chỉnh | Đã nâng cấp `full-compose` |
| **12** | **SaaS Demo Templates & Auto-Zoom Pack (6 MIT Repos)** | [`./saas-demo-templates`](./saas-demo-templates) | Trọn bộ `remotion-cinematic`, `supercut` CLI, `programatic-demo`, `playwright-recast` CLI, `claude-remotion-editor`, `saas-product-demo-video` (Playwright + Auto-Zoom kiểu *Screen Studio*) | Đã cài & build CLI |
| **13** | **Lottie Runtime + 454 Animations & 32 SaaS SFX/BGM** | [`./studio/assets-library`](./studio/assets-library) & [`./studio/vendor/lottie`](./studio/vendor/lottie) | Offline `lottie-web` + `dotlottie-web`, 25 curated SaaS Lottie `.json` (trên tổng 454 file MIT) và 4 nhóm âm thanh UI chuẩn SaaS (*Click, Typing, Whoosh, Pop/Chime* + BGM CC0/MIT) | Đã cài & kiểm thử 100% |

---

## 3. Cấu Trúc Thư Mục

```text
CreateVideo/
├── .agent/skills/                  # 13 AI Agent Skills (ai-video-pipeline, hyperframes, saas-product-demo-video, supercut, playwright-recast, shoot-demo-video...)
├── .cache/                         # Cache HuggingFace, uv, npm đặt trên ổ F: (bảo vệ dung lượng ổ C:)
├── saas-demo-templates/            # 6 bộ Template mã nguồn mở chuyên quay & dựng SaaS UI Walkthrough + Auto-Zoom
│   ├── remotion-cinematic/         # Geometry-Aware Cursor + Per-scene AutoZoom + Push Transitions
│   ├── supercut/                   # CLI Playwright tự quay web app thật + camera motion blur (dist/cli/index.js)
│   ├── programatic-demo/           # Playwright record-demo + Remotion Screen Studio framing
│   ├── playwright-recast/          # Chuyển trace.zip của Playwright thành MP4 1080p có zoom, cursor, click-sound (dist/cli.js)
│   ├── claude-remotion-editor/     # SceneDirector + 124 Lottie JSON con trỏ chuột/bàn tay/click burst
│   └── saas-product-demo-video/    # Khung kịch bản chuẩn video SaaS 30–60s
├── 2d-3d-knowledge-graph/          # Thư viện đồ thị tri thức 2D/3D (cổng 8792)
├── ComfyUI/                        # Giao diện & API tạo ảnh/video AI (cổng 8188)
│   ├── custom_nodes/               # ComfyUI-GGUF, ComfyUI-Manager, ComfyUI-VideoHelperSuite
│   ├── models/
│   │   ├── unet/                   # Wan2.2-TI2V-5B-Q4_K_M.gguf (3.27 GB)
│   │   ├── text_encoders/          # umt5-xxl-encoder-Q4_K_M.gguf (3.49 GB)
│   │   └── vae/                    # wan2.2_vae.safetensors (1.34 GB)
│   ├── user/default/workflows/     # wan22_ti2v_5b_6gb_vram.json (Workflow nạp sẵn cho 6GB VRAM)
│   └── generate_wan22_api.py       # CLI gọi tự động Wan 2.2 qua REST API
├── piper-tts/                      # Giọng đọc AI offline (.venv Python 3.11 + speak.py + 4 giọng Việt/Anh)
├── ACE-Step-1.5/                   # AI sáng tác nhạc nền (Gradio cổng 7860 / API cổng 8001)
├── whisper/                        # Nhận diện giọng nói GPU/CPU + xuất .srt / word-timestamps .json
├── ffmpeg-tools/                   # Script media_pipeline.ps1 (add-voiceover, mix-bgm, burn-srt, full-compose)
├── studio/                         # Không gian sản xuất video thực tế
│   ├── vendor/                     # Bản offline của GSAP (25 plugins), Three.js & Lottie/dotLottie (WASM)
│   ├── assets-library/             # Kho dùng chung: 454 Lottie JSON (25 curated SaaS) & 32 file SFX/BGM (Click, Typing, Whoosh, Pop/Chime)
│   ├── continuum-launch/           # Dự án video ra mắt Continuum AI
│   ├── demo-video/                 # Dự án mẫu Motion Graphics 2D (HTML + GSAP -> MP4)
│   ├── threejs-gsap-demo/          # Dự án mẫu Vũ trụ 3D (Three.js + GSAP Camera + HyperFrames -> MP4)
│   ├── notes/                      # Kho ghi chú Markdown mẫu
│   └── knowledge-graph-viewer/     # Ứng dụng xem 2D/3D Knowledge Graph (cổng 8793)
├── start-comfyui-wan22.bat         # Mở ComfyUI + Wan 2.2 chế độ tiết kiệm VRAM (http://127.0.0.1:8188)
├── run-piper-tts.bat               # Xuất file giọng đọc .wav từ câu lệnh hoặc file kịch bản .txt
├── start-acestep-music.bat         # Mở Web UI tạo nhạc nền ACE-Step 1.5 (http://127.0.0.1:7860)
├── run-whisper-srt.bat             # Tạo phụ đề .srt, .txt, .transcript.json từ audio/video
├── start-hyperframes-studio.bat    # Mở HyperFrames Studio Preview
├── start-knowledge-graph-demo.bat  # Mở bản demo gốc 2D-3D Knowledge Graph (http://127.0.0.1:8792)
└── start-createvideo-graph.bat     # Mở 2D-3D Knowledge Graph cho kho Markdown riêng (http://127.0.0.1:8793)
```

---

## 4. Hướng Dẫn Sử Dụng Từng Công Cụ

### A. Tạo Giọng Đọc Thuyết Minh Tiếng Việt (LucyLab / TikTok Cloud AI & Piper Offline)
```powershell
# 1. Cloud AI TTS (đọc động từ .env: VIETNAMESE_API_KEY, VIETNAMESE_VOICEID_MALE/FEMALE, TIKTOK_SESSION_ID):
.\run-lucylab-tts.bat --list
.\run-lucylab-tts.bat --file .\studio\kich_ban.txt .\studio\voiceover.wav male auto

# 2. Offline Piper TTS (không cần Internet):
.\run-piper-tts.bat --list
.\run-piper-tts.bat --file .\studio\kich_ban.txt .\studio\voiceover.wav vi_VN-vais1000-medium
```

### B. Tạo Phụ Đề `.srt` Chuẩn Từng Từ (Whisper GPU/CPU)
```powershell
.\run-whisper-srt.bat .\studio\voiceover.wav small vi
# Xuất ra: voiceover.srt, voiceover.txt, voiceover.transcript.json
```

### C. Tạo Cảnh Quay AI Thực Tế Bằng ComfyUI + Wan 2.2 (6GB VRAM)
1. **Cách 1 — Giao diện kéo thả trực quan:**
   ```powershell
   .\start-comfyui-wan22.bat
   ```
   Mở `http://127.0.0.1:8188` → Mở menu **Workflows** bên trái → Chọn **`wan22_ti2v_5b_6gb_vram.json`** → Nhập mô tả cảnh quay (tiếng Anh) → Bấm **Run**.
2. **Cách 2 — Dòng lệnh tự động cho AI Agent:**
   *(Khi `start-comfyui-wan22.bat` đang chạy nền ở cổng `8188`)*
   ```powershell
   .\ComfyUI\.venv\Scripts\python.exe .\ComfyUI\generate_wan22_api.py `
     --prompt "Cinematic aerial drone shot of misty terraced rice fields in Vietnam at sunrise, golden volumetric light" `
     --width 832 --height 480 --frames 33 --fps 16 `
     --output .\studio\broll_vietnam.mp4
   ```
   *(Muốn tạo video từ ảnh có sẵn — Image-to-Video: chỉ cần thêm `--image duong_dan_anh.png`).*

### D. Dựng Video Motion Graphics 2D & Không Gian 3D (HyperFrames + GSAP + Three.js)
```powershell
# Render video mẫu 3D Knowledge Universe (Three.js + GSAP offline):
cd .\studio\threejs-gsap-demo
npx hyperframes check
npx hyperframes render -o ..\raw_3d_video.mp4
cd ..\..
```

### E. Tạo Nhạc Nền AI (ACE-Step 1.5)
```powershell
.\start-acestep-music.bat
# Mở http://127.0.0.1:7860 để tạo nhạc nền .wav/.mp3
```

### F. Ghép Hoàn Chỉnh Video + Giọng Đọc + Nhạc Nền + Đóng Phụ Đề Trong 1 Lệnh (FFmpeg)
```powershell
powershell -ExecutionPolicy Bypass -File .\ffmpeg-tools\media_pipeline.ps1 `
  -Action full-compose `
  -InputVideo .\studio\raw_3d_video.mp4 `
  -InputVoice .\studio\voiceover.wav `
  -InputAudio .\studio\nhac_nen.wav `
  -BgmVolume 0.18 `
  -InputSrt .\studio\voiceover.srt `
  -Output .\studio\video_hoan_chinh_1080p.mp4
```
