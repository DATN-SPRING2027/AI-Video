@echo off
chcp 65001 >nul
echo [CreateVideo] Khoi dong CreateVideo Vault 2D/3D Knowledge Graph (port 8793)...
cd /d "%~dp0studio\knowledge-graph-viewer"
start "" "http://127.0.0.1:8793"
node serve.mjs

