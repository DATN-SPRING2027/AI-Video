@echo off
chcp 65001 >nul
set "PYTHONUTF8=1"
set "HF_HOME=%~dp0.cache\huggingface"
if "%~1"=="" (
    echo Cach dung: run-whisper-srt.bat "duong_dan_video_hoac_audio.mp4" [model: small/medium/large-v3] [lang: vi/en]
    echo Vi du:     run-whisper-srt.bat "studio\demo-video\out.mp4" small vi
    exit /b 1
)
set MODEL=%~2
if "%MODEL%"=="" set MODEL=small
if "%~3"=="" (
    "%~dp0whisper\.venv\Scripts\python.exe" "%~dp0whisper\transcribe_srt.py" "%~1" --model %MODEL%
) else (
    "%~dp0whisper\.venv\Scripts\python.exe" "%~dp0whisper\transcribe_srt.py" "%~1" --model %MODEL% --language %~3
)
