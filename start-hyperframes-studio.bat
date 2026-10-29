@echo off
chcp 65001 >nul
echo [CreateVideo] Khoi dong HyperFrames Studio Preview...
cd /d "%~dp0studio\demo-video"
call npx hyperframes preview

