@echo off
chcp 65001 >nul
echo [CreateVideo] Khoi dong 2D/3D Knowledge Graph Demo (The Meridian Archive - port 8792)...
cd /d "%~dp02d-3d-knowledge-graph"
start "" "http://127.0.0.1:8792"
node demo/serve.mjs

