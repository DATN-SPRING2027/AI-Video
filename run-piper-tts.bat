@echo off
chcp 65001 >nul
set "PYTHONUTF8=1"
if "%~1"=="" (
    echo Cach dung:
    echo   1. Doc truc tiep van ban:
    echo      run-piper-tts.bat "Xin chao, day la he thong AI tao video tu dong." output.wav [vi_VN-vais1000-medium]
    echo   2. Doc tu file kich ban .txt ^(UTF-8^):
    echo      run-piper-tts.bat --file kich_ban.txt output.wav [vi_VN-vais1000-medium]
    echo   3. Xem danh sach giong doc da cai:
    echo      run-piper-tts.bat --list
    exit /b 1
)

if "%~1"=="--list" (
    "%~dp0piper-tts\.venv\Scripts\python.exe" "%~dp0piper-tts\speak.py" --list-voices
    exit /b 0
)

set VOICE=%~3
if "%VOICE%"=="" set VOICE=vi_VN-vais1000-medium

if "%~1"=="--file" (
    set OUT=%~3
    if "%~3"=="" set OUT=voiceover.wav
    set FVOICE=%~4
    if "%~4"=="" set FVOICE=vi_VN-vais1000-medium
    "%~dp0piper-tts\.venv\Scripts\python.exe" "%~dp0piper-tts\speak.py" --input-file "%~2" --output "%OUT%" --voice "%FVOICE%"
) else (
    set OUT=%~2
    if "%~2"=="" set OUT=voiceover.wav
    "%~dp0piper-tts\.venv\Scripts\python.exe" "%~dp0piper-tts\speak.py" --text "%~1" --output "%OUT%" --voice "%VOICE%"
)
