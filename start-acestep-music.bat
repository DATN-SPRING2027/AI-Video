@echo off
chcp 65001 >nul
set "PYTHONUTF8=1"
set "HF_HOME=%~dp0.cache\huggingface"
set "UV_CACHE_DIR=%~dp0.cache\uv"
echo [CreateVideo] Khoi dong ACE-Step 1.5 Music AI Web UI (http://127.0.0.1:7860)...
cd /d "%~dp0ACE-Step-1.5"
"%~dp0ACE-Step-1.5\.venv\Scripts\acestep.exe"
