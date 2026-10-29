# Studio Assets Library — Lottie JSON Animations & Royalty-Free SaaS SFX

Kho tài nguyên dùng chung (100% Offline & Miễn phí bản quyền MIT / CC0) để ghép trực tiếp vào mọi dự án video trong `CreateVideo/studio/` (cả **HyperFrames** lẫn **Remotion**).

---

## 1. Thư Viện Lottie Animations (`./lottie/` & `../vendor/lottie/`)

- **Offline Player đã cài sẵn tại `../vendor/lottie/`:**
  - `lottie.min.js` & `lottie_svg.min.js` (`lottie-web`)
  - `dotlottie-web/index.js` & `dotlottie-web/dotlottie-player.wasm` (`@lottiefiles/dotlottie-web`)
- **25 Animation chọn lọc cho SaaS Workflow (`./lottie/curated-saas/`):**
  - **Hoàn thành / Thành công:** `checkmark-success.json`, `check-circle-complete.json`, `checkbox-toggle.json`
  - **Tạo Project / Thư mục:** `folder-project-open.json`, `folder-plus-new-project.json`, `file-plus-create.json`, `plus-circle-create.json`
  - **Tạo Organization / Thành viên / Quyền:** `users-organization.json`, `user-plus-invite-member.json`, `user-check-verified.json`, `settings-gear.json`, `lock-permissions.json`
  - **Con trỏ chuột & Vòng sóng Click:** `cursor-click-cta.json`, `cursor-click-effect.json`, `cursor-mouse-click.json`, `cursor-mouse-scroll.json`, `click-sunburst-soft.json`, `cursor-black-click-burst.json`, `cursor-swish-trail.json`
  - **Mũi tên chỉ dẫn & Trạng thái tải:** `hand-drawn-arrow-guide.json` *(mũi tên cong vẽ tay chỉ vào nút bấm)*, `arrow-right-circle.json`, `arrow-down-circle.json`, `arrow-up-right-launch.json`, `loading-spinner.json`, `loading-dots.json`
- **Tổng kho đầy đủ (`430+` file `.json`):** Được lập chỉ mục sẵn trong [`./lottie/CATALOG.json`](./lottie/CATALOG.json) (từ `useAnimations` MIT, `spemer/lottie-animations-json` MIT và `claude-remotion-editor` MIT).

### Cách nhúng Lottie chuẩn frame-accurate trong HyperFrames
```html
<div id="check-icon" style="width:96px;height:96px;"></div>
<script src="../vendor/lottie/lottie.min.js"></script>
<script>
  const anim = lottie.loadAnimation({
    container: document.getElementById("check-icon"),
    renderer: "svg",
    loop: false,
    autoplay: false,
    path: "assets/checkmark-success.json"
  });
  window.__hfLottie = window.__hfLottie || [];
  window.__hfLottie.push(anim);
</script>
```

---

## 2. Bộ 4 Nhóm Âm Thanh "Ăn Tiền" Cho Video Demo App (`./sfx/`)

Toàn bộ file âm thanh đã được phân loại sẵn để đồng bộ đúng từng frame thao tác trên UI (khuyến nghị âm lượng SFX `0.25`–`0.35` dưới giọng thuyết minh):

1. **`./sfx/01-soft-mouse-click/`** *(Đặt đúng frame con trỏ bấm nút Create / Submit)*:
   - `click-soft.mp3`, `send-click-soft.wav`, `ui-click-clean.wav`, `click-crisp.mp3`, `cinematic-ui-click.mp3`, `openverse-cc0-mouse-click.*`
2. **`./sfx/02-soft-mechanical-typing/`** *(Đặt lúc gõ tên Organization / Project vào ô input)*:
   - `typing-soft-mechanical.wav`, `typing-burst-1.5s.mp3`, `key-press-single.mp3`, `key-tap-clean.wav`, `typing-flow.wav`, `openverse-cc0-keyboard-typing.*`
3. **`./sfx/03-subtle-whoosh/`** *(Đặt lúc camera zoom-in vào form hoặc chuyển cảnh)*:
   - `whoosh-short-snappy.mp3`, `whoosh-swipe-pixabay.mp3`, `whoosh-punchy.mp3`, `whoosh-transition.mp3`, `whoosh-cinematic-5.5s.mp3`, `openverse-cc0-subtle-whoosh.*`
4. **`./sfx/04-ui-pop-chime/`** *(Đặt lúc hiện Toast / tạo Organization hoặc Project thành công)*:
   - `ui-pop-quick.mp3`, `ui-pop-clean.wav`, `success-chime-melodic.mp3`, `confirm-success.wav`, `notification-toast.mp3`, `ping-highlight.mp3`, `sparkle-shimmer.mp3`, `openverse-cc0-ui-chime.*`
5. **`./sfx/05-transitions-impacts/`**: `riser-build-10s.mp3`, `impact-bass-hit.mp3`, `impact-swell.mp3`, `error-alert.mp3`
6. **`./sfx/06-bgm-royalty-free/`** *(Nhạc nền SaaS miễn phí bản quyền MIT)*:
   - `daybreak-upbeat-saas.mp3`, `momentum-launch.mp3`, `midnight-tech.mp3`, `pulse-minimal.mp3`

Xem thông tin nguồn & giấy phép CC0/MIT tại [`./sfx/CREDITS.md`](./sfx/CREDITS.md).
