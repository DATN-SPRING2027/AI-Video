@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PY_BIN=%~dp0piper-tts\.venv\Scripts\python.exe"
if not exist "%PY_BIN%" set "PY_BIN=python"

if "%~1"=="" (
    echo Cach dung LucyLab ^& TikTok Vietnamese Cloud AI TTS:
    echo   1. Kiem tra ket noi, quota va danh sach giong doc tu .env:
    echo      run-lucylab-tts.bat --list
    echo   2. Doc truc tiep van ban ^(mac dinh: male, tu dong fallback TikTok TTS neu LucyLab het credit^):
    echo      run-lucylab-tts.bat "Xin chao, day la Continuum AI." output.wav [male^|female^|voiceId] [auto^|lucylab^|tiktok]
    echo   3. Doc tu file kich ban .txt ^(UTF-8^):
    echo      run-lucylab-tts.bat --file kich_ban.txt output.wav [male^|female^|voiceId] [auto^|lucylab^|tiktok]
    exit /b 1
)

if "%~1"=="--list" (
    "%PY_BIN%" -X utf8 "%~dp0lucylab-tts\lucylab_tts.py" --list-voices
    exit /b !ERRORLEVEL!
)

if "%~1"=="--file" (
    set "OUT=%~3"
    if "!OUT!"=="" set "OUT=voiceover.wav"
    set "FVOICE=%~4"
    if "!FVOICE!"=="" set "FVOICE=male"
    set "FPROV=%~5"
    if "!FPROV!"=="" set "FPROV=auto"
    "%PY_BIN%" -X utf8 "%~dp0lucylab-tts\lucylab_tts.py" --input-file "%~2" --output "!OUT!" --voice "!FVOICE!" --provider "!FPROV!"
    exit /b !ERRORLEVEL!
) else (
    set "OUT=%~2"
    if "!OUT!"=="" set "OUT=voiceover.wav"
    set "VOICE=%~3"
    if "!VOICE!"=="" set "VOICE=male"
    set "PROV=%~4"
    if "!PROV!"=="" set "PROV=auto"
    "%PY_BIN%" -X utf8 "%~dp0lucylab-tts\lucylab_tts.py" --text "%~1" --output "!OUT!" --voice "!VOICE!" --provider "!PROV!"
    exit /b !ERRORLEVEL!
)

