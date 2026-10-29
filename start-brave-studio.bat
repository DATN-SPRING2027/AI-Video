@echo off
setlocal
title CreateVideo - Brave Browser Studio (CDP Port 9333)

set "BRAVE_EXE=C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
if not exist "%BRAVE_EXE%" set "BRAVE_EXE=%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"

if not exist "%BRAVE_EXE%" (
    echo [ERROR] Khong tim thay Brave Browser tren may!
    pause
    exit /b 1
)

set "PROFILE_DIR=%~dp0.cache\brave-demo-profile"
if not exist "%PROFILE_DIR%" mkdir "%PROFILE_DIR%"

echo ============================================================================
echo  Mo Brave Browser che do Studio Control (CDP: http://127.0.0.1:9333)
echo  Profile luu tai: %PROFILE_DIR%
echo.
echo  HUONG DAN LAN DAU:
echo  1. Dang nhap san tai khoan Google cua ban trong cua so Brave vua mo.
echo  2. Giu cua so Brave mo de Antigravity tu dong dieu khien va quay video!
echo ============================================================================

start "" "%BRAVE_EXE%" ^
  --remote-debugging-port=9333 ^
  --user-data-dir="%PROFILE_DIR%" ^
  --no-first-run ^
  --no-default-browser-check ^
  --window-size=1920,1080 ^
  "http://localhost:3000/en/signin" "https://accounts.google.com"
