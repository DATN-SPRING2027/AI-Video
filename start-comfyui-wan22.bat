@echo off
chcp 65001 >nul
set "PYTHONUTF8=1"
set "HF_HOME=%~dp0.cache\huggingface"
set "UV_CACHE_DIR=%~dp0.cache\uv"
set "PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True"
echo [CreateVideo] Khoi dong ComfyUI + Wan 2.2 TI2V-5B GGUF (Toi uu cho RTX 4050 6GB VRAM)...
echo [CreateVideo] Truy cap giao dien tai: http://127.0.0.1:8188
cd /d "%~dp0ComfyUI"
"%~dp0ComfyUI\.venv\Scripts\python.exe" main.py --lowvram --reserve-vram 1.5 --listen 127.0.0.1 --port 8188 --auto-launch
