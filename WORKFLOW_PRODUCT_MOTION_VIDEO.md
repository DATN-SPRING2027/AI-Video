# Workflow Sản Xuất Video Giới Thiệu Sản Phẩm (Product Motion Ad — `16:9` & `9:16`)

Tài liệu này ghi lại trọn bộ quy trình thực chiến đã dùng để sản xuất bộ đôi video giới thiệu **Continuum AI cho Doanh nghiệp** (bản ngang `16:9` `1920x1080` và bản dọc `9:16` `1080x1920`, `30fps`, `58.0s`) ngay trong `F:\LEARN KÌ 8\ĐATN\CreateVideo`.

- **Dự án mẫu chuẩn để tham khảo/nhân bản:**
  - Bản Ngang `16:9` (Website / Pitch Deck / YouTube): [`./studio/continuum-business-intro`](./studio/continuum-business-intro)
  - Bản Dọc `9:16` (Reels / TikTok / Shorts): [`./studio/continuum-business-intro-9x16`](./studio/continuum-business-intro-9x16)

---

## 1. Triết Lý & 8 Kỹ Thuật Product Motion Ad Cốt Lõi

Thay vì dựng slide chữ tĩnh hoặc nhồi nhét thuật ngữ kỹ thuật (`RBAC`, `PKCE`, `RAG`, `Vector DB`), video hướng tới khách hàng/doanh nghiệp phải **kể câu chuyện từ nỗi đau thực tế đến kết quả đo đếm được** thông qua 8 kỹ thuật chuyển động:

1. **Sân khấu Mặt bàn Ánh sáng Tự nhiên (*Daylight Tactile Desk Stage*):**
   - Đặt thiết bị trên mặt bàn sáng (`#e5ecfa → #c4d1eb`) có nhiễu hạt giấy nhẹ (`desk-grain`) và đạo cụ văn phòng ở các góc (giấy ghi chú vàng, bút ký, kẹp giấy, chậu sen đá, tách cà phê latte thở nhẹ bằng `GSAP sine.inOut`).
2. **UI Tương tác Sống (*Live Interactive UI Micro-Choreography*):**
   - Không chiếu ảnh chụp màn hình đứng yên: tự động bấm chuyển tab (`Kho Drive` → `Tin nhắn` → `Máy cá nhân`), thả thông báo rơi lệch nhịp (`stagger`), gõ câu hỏi từng ký tự (`steps()`), và bật ngăn kéo `Bàn giao 1 chạm` bằng hiệu ứng lò xo (`back.out(1.5)`).
3. **Nét Bút Dạ SVG Vẽ Tay Khoanh Trực Tiếp (*Hand-Drawn Marker Circles*):**
   - Dùng `<path pathLength="1">` với `stroke-dasharray: 1 1.2; stroke-dashoffset: 1.1 → 0` để khoanh đỏ vào nỗi đau (`Chậm 7 ngày`, `Thiếu 14 tài liệu!`) và khoanh xanh lá vào kết quả (`Bắt nhịp trong 5 phút`, `Biên bản họp BGĐ • 12/10`).
4. **Thẻ 3D Xòe Quạt & Bay Ra Ngoài Khung Thiết Bị (*Out-of-Frame Pop-Out Cards*):**
   - Bật `data-layout-allow-overflow` để 4 thẻ nguồn dữ liệu xòe quạt đối xứng từ sau lưng máy (`17.5s`) và 3 thẻ kết quả bắn vọt từ trong màn hình ra khoảng trống bên cạnh (`26.5s`).
5. **Montage B-Roll Đời Thực Tốc Độ Cao + Thanh Thông Báo Nổi (*Floating App Toasts*):**
   - Xen kẽ 3 cảnh quay văn phòng thật (`~1.0s/cảnh` từ Pexels qua `MoneyPrinterTurbo`) với thông báo ứng dụng nảy từ cạnh trên xuống khớp câu *"Sáng họp nhanh, chiều chốt việc, tối cập nhật tiến độ"*.
6. **Hoạt Ảnh Khiên Phân Quyền & Ẩn Số Nhạy Cảm (*Privacy Shield Masking*):**
   - Khiên bảo mật nảy ở trung tâm màn hình kèm âm `lock-confirm`, làm mờ (`filter: blur(6px)`) con số doanh thu/lương thưởng và biến thành `••••••••••đ`.
7. **Phụ Đề Karaoke Từng Cụm Từ (*Word-by-Word Progressive Highlight*):**
   - Mỗi câu chia thành 2–3 cụm ngắn, chữ chưa đọc có màu xám dịu (`#64748b`), đọc tới đâu bật sáng màu nhấn (`#0f172a`, `#4f46e5`, `#dc2626`, `#047857`) và nhích nhẹ `y: -2px` khớp mili-giây theo `Whisper`. Khi cắt sang cảnh B-Roll tối thì chuyển sang class `.on-dark`.
8. **Màn Kết Thương Hiệu (*Brand Finale Showcase*):**
   - Thiết bị trượt mượt xuống nửa dưới khung hình, nhường nửa trên cho khóa logo thương hiệu chính thức (`continuum-lockup-light.png`), câu định vị và nút CTA nhịp thở.

---

## 2. Quy Trình Thực Hiện 7 Bước Từ A → Z

### Bước 1 — Phân Tích Video Mẫu Tham Chiếu (Nếu Có)
Khi có một video mẫu muốn học nhịp dựng, trích khung chuyển cảnh và đo thông số âm thanh trước khi viết code:
```powershell
# 1. Xem độ phân giải, FPS, thời lượng và chuẩn âm thanh:
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate -show_entries format=duration -of json .\video_mau.mp4

# 2. Trích các khung hình khi chuyển cảnh để đo nhịp cắt (thường 1.5s - 2.5s/cảnh):
ffmpeg -i .\video_mau.mp4 -vf "select='gt(scene,0.28)',showinfo" -vsync vfr .\frames_ref\scene_%03d.jpg

# 3. Đo âm lượng trung bình và đỉnh (chuẩn thương mại: mean ~ -20 dB, max ~ -1.5 dB):
cmd /c "ffmpeg -i .\video_mau.mp4 -af volumedetect -f null NUL 2>&1"
```

### Bước 2 — Kịch Bản Đời Thường, Tạo Giọng Đọc (`TTS`) & Mốc Thời Gian Từng Từ (`Whisper`)
1. Lưu lời bình tiếng Việt vào `narration.txt` (mỗi ý 1 dòng ngắn gọn, câu từ tự nhiên cho chủ doanh nghiệp/quản lý, thời lượng mục tiêu `45s–60s`).
2. Xuất giọng đọc WAV `48kHz` và đo chính xác độ dài:
   ```powershell
   .\run-lucylab-tts.bat --file .\studio\<ten-du-an>\narration.txt .\studio\<ten-du-an>\assets\audio\voiceover.wav male auto
   ffprobe -v error -show_entries format=duration -of csv=p=0 .\studio\<ten-du-an>\assets\audio\voiceover.wav
   ```
3. Chạy `Whisper` để lấy mốc thời gian chuẩn từng từ/câu trong `voiceover.transcript.json`:
   ```powershell
   .\run-whisper-srt.bat .\studio\<ten-du-an>\assets\audio\voiceover.wav small vi
   ```
   > **Nguyên tắc vàng:** Mọi mốc `GSAP` (`tl.to`, `tl.fromTo`), mốc cắt hồi (`data-start`, `data-duration`) và mốc phụ đề Karaoke **phải lấy từ `voiceover.transcript.json`** cộng với độ trễ đầu video (ví dụ `vo-track` bắt đầu tại `1.2s` thì cộng `+1.2s` vào toàn bộ mốc Whisper).

### Bước 3 — Chuẩn Bị Logo Thương Hiệu Chính Thức & Ảnh Giao Diện Thật
> **QUY TẮC BẮT BUỘC (CHỐNG SAI LOGO):**
> Tuyệt đối **không tự vẽ SVG hoặc khối màu giả lập** để thay thế logo sản phẩm. Phải luôn sao chép nguyên bản bộ logo chính thức từ `DATN_FE`:
> - Biểu tượng vuông `C∞` (`512x512` RGBA): `F:\LEARN KÌ 8\ĐATN\DATN_FE\public\images\logo\continuum-mark.png`
> - Khóa thương hiệu ngang `C∞ Continuum AI` (`1200x273` RGBA): `F:\LEARN KÌ 8\ĐATN\DATN_FE\public\images\logo\continuum-lockup-light.png`

```powershell
$logoSrc = "F:\LEARN KÌ 8\ĐATN\DATN_FE\public\images\logo"
$brandDst = "F:\LEARN KÌ 8\ĐATN\CreateVideo\studio\<ten-du-an>\assets\brand"
New-Item -ItemType Directory -Force -Path $brandDst | Out-Null
Copy-Item "$logoSrc\continuum-mark.png", "$logoSrc\continuum-lockup-light.png" $brandDst -Force
```
- Ảnh giao diện sản phẩm (`assets/ui/ui-01-dashboard.png`, ...) chụp trực tiếp từ ứng dụng thật đang chạy qua Playwright / Brave CDP (`scripts/capture_continuum_screens.mjs`).

### Bước 4 — Tải B-Roll Đời Thực Đúng Khổ Ngang (`16:9`) & Khổ Dọc (`9:16`)
Dùng môi trường Python của `MoneyPrinterTurbo` kết nối `PEXELS_API_KEY` trong `CreateVideo/.env` để tải B-Roll **đúng tỉ lệ gốc** (không kéo giãn hay cắt cúp thô từ video ngang sang dọc):
- Dự án `16:9`: tải nguồn Pexels `landscape` → chuẩn hóa `1920x1080`, `30fps`, `libx264`.
- Dự án `9:16`: tải nguồn Pexels `portrait` → chuẩn hóa `1080x1920`, `30fps`, `libx264` (xem mẫu trong `studio/continuum-business-intro/scripts/fetch_pexels_broll.py`).

### Bước 5 — Dựng Tổ Hợp `HyperFrames` + `GSAP` (Xuất Kép `16:9` & `9:16`)
Mỗi dự án trong `studio/<ten-du-an>/` tổ chức thành các module độc lập, sạch gọn:
```text
studio/<ten-du-an>/
├── index.html                      # Sân khấu mặt bàn + ghép các hồi (act1..act4) + captions + VO + BGM + 22 điểm SFX
├── hyperframes.json                # Cấu hình fps: 30, entry: index.html
├── package.json                    # Lệnh dev, check, render
├── STORYBOARD.md                   # Tóm tắt kịch bản & bố cục
├── narration.txt                   # Kịch bản thuyết minh gốc
├── assets/
│   ├── brand/                      # continuum-mark.png & continuum-lockup-light.png chính chủ
│   ├── ui/                         # Ảnh chụp giao diện sản phẩm thật
│   ├── broll/                      # Các clip B-Roll Pexels 1080p đã chuẩn hóa 30fps
│   ├── audio/                      # voiceover.wav + bgm-upbeat.mp3
│   ├── sfx/                        # Các hiệu ứng âm thanh UI ngắn (click, whoosh, pop, lock, sparkle...)
│   └── vendor/gsap.min.js          # Bản GSAP offline chạy deterministic
└── compositions/
    ├── act-01-pain.html            # Hồi 1: Nỗi đau rời rạc, đối chiếu khoanh đỏ & cú lật thương hiệu
    ├── act-02-solution.html        # Hồi 2: Tự gom gọn, Montage 3 cảnh B-Roll + Toast & Bàn giao 1 chạm
    ├── act-03-ai-clarity.html      # Hồi 3: Gõ câu hỏi thật, khoanh xanh nguồn gốc & Khiên phân quyền
    ├── act-04-outcome.html         # Hồi 4: Tổng quan lãnh đạo & Brand Finale CTA
    └── captions-overlay.html       # Phụ đề Karaoke đổi màu từng cụm từ
```

**Lưu ý khi chuyển thể sang bản dọc `9:16` (`1080x1920`):**
- Không thu nhỏ nguyên màn hình ngang `16:9` vào giữa khung dọc (chữ sẽ quá bé trên điện thoại).
- Đổi khung thiết bị trung tâm sang tỉ lệ dọc (`820x1100`, bo góc `48px`), cỡ chữ tối thiểu `25px–28px`, đặt phụ đề trong vùng an toàn dưới (`bottom: 340px–380px`) để không đè lên giao diện TikTok/Reels/Shorts.

### Bước 6 — Phối Âm Thanh 3 Lớp (Audio Mastering)
Trong `index.html`, phối 3 lớp âm thanh với mức âm lượng đã cân chỉnh sẵn để giọng đọc luôn nổi rõ:
- **Lớp 1 — Giọng thuyết minh (`voiceover.wav`):** `data-volume="1"`.
- **Lớp 2 — Nhạc nền (`bgm-upbeat-58s.mp3`):** `data-volume="0.19"` (có fade-in đầu và fade-out cuối).
- **Lớp 3 — Micro-Foley SFX (18–25 điểm):** `data-volume="0.24"` đến `"0.38"` đặt trùng khớp từng thời điểm thẻ trượt vào (`whoosh-snappy`), bấm tab (`click-crisp`), cảnh báo rơi (`error-alert`), bút khoanh tròn (`ping-marker`), gõ phím (`typing-burst`), bật khóa (`lock-confirm`) và bung logo kết (`sparkle`).

### Bước 7 — Cổng Kiểm Định Chất Lượng 5 Bước (Bắt Buộc Trước Bàn Giao)
Luôn chạy đủ 5 bước kiểm định cho **cả hai bản `16:9` và `9:16`**:

```powershell
cd "F:\LEARN KÌ 8\ĐATN\CreateVideo\studio\<ten-du-an>"

# 1. Kiểm tra cú pháp & cấu trúc timeline (phải đạt errorCount: 0, warningCount: 0):
npx hyperframes lint --json

# 2. Chụp ảnh tĩnh tại các giây quan trọng và MỞ XEM BẰNG MẮT từng ảnh PNG:
npx hyperframes snapshot --at 9.7,14.2,18.2,24.6,34.4,43.0,46.6,54.0 --no-end -o .\qa_snapshots

# 3. Kiểm tra tự động 400+ mẫu khung hình (layout, font, media):
npx hyperframes check --json

# 4. Xuất video MP4 1080p 30fps chất lượng phát hành:
npm run render

# 5. Xác minh file MP4 đầu ra bằng ffprobe & xóa sạch thư mục nháp qa_snapshots:
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate,channels -show_entries format=duration,size -of json .\dist\<ten-file>.mp4
Remove-Item -Recurse -Force .\qa_snapshots -ErrorAction SilentlyContinue
```

---

## 3. Kinh Nghiệm Xương Máu & Cách Tránh Lỗi Thường Gặp

| Tình huống lỗi thực tế | Nguyên nhân | Cách xử lý triệt để |
| :--- | :--- | :--- |
| **Sai logo thương hiệu trong video** | Tự dựng khối gradient/SVG gần giống thay vì lấy file gốc của Frontend | Luôn copy nguyên bản `continuum-mark.png` & `continuum-lockup-light.png` từ `DATN_FE/public/images/logo/`. |
| **Cảnh báo `duplicate_media_discovery_risk` khi chạy `lint`** | Dùng nhiều thẻ `<img src="assets/brand/continuum-mark.png">` giống hệt nhau trong cùng 1 file composition | Chỉ giữ tối đa 1 thẻ `<img>`, các vị trí icon lặp lại (như 3 thanh thông báo nổi) dùng CSS `background: url("assets/brand/continuum-mark.png") center / contain no-repeat`. |
| **Khung video bị trắng xóa sau vài giây cuối cảnh** | Thẻ `<video>` B-Roll có `data-duration="3.2"` ngắn hơn tổng thời lượng hồi (`10.0s`) | Đặt 1 lớp `<img>` giao diện thật (`data-duration="10.0"`) nằm dưới `<video>`, rồi dùng `GSAP` fade `<video>` về `opacity: 0` ở `2.75s`. |
| **Thẻ xòe quạt bên phải ở bản `9:16` bị khuất chữ đầu** | Thẻ căn trái (`text-align: left`) nên phần chữ đầu nằm lọt dưới viền phải của điện thoại | Đặt `align-items: flex-end; text-align: right` cho các thẻ xòe sang bên phải (`#fc-3`, `#fc-4`). |
| **Chữ cảnh cũ lộ mờ phía sau banner hoặc popup** | Nền popup bán trong suốt (`rgba`) hoặc chưa ẩn pane bên dưới trước khi thả chồng cảnh báo | Dùng nền đặc (`#0f172a` / `#ffffff`) cho khiên/toast đè lên chữ và `tl.to(paneCu, { opacity: 0 })` đúng nhịp chuyển. |
| **PowerShell 5.1 báo lỗi đỏ khi chạy `ffmpeg volumedetect`** | `FFmpeg` ghi log thống kê ra luồng `stderr` khiến `$ErrorActionPreference = "Stop"` dừng lệnh | Đặt `$ErrorActionPreference = "Continue"` và chạy qua `cmd /c "ffmpeg ... 2>&1"`. |
| **Rác dung lượng trong Git** | Để sót file MP4/PNG/MP3 thử nghiệm từ bản nháp cũ hoặc thư mục `.hf-transaction*` | Rà soát toàn bộ `index.html` & `compositions/*.html` để xóa mọi asset không còn tham chiếu trước khi `git commit`. |
