# Bootstrap external open-source repos ignored by Git (models & heavy engines stay off GitHub)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Clone-IfMissing([string]$Url, [string]$Target) {
  if (-not (Test-Path $Target)) {
    Write-Host "Cloning $Url -> $Target ..." -ForegroundColor Cyan
    git clone --depth 1 $Url $Target
  } else {
    Write-Host "Skip (exists): $Target" -ForegroundColor DarkGray
  }
}

New-Item -ItemType Directory -Force -Path "saas-demo-templates" | Out-Null

Clone-IfMissing "https://github.com/comfyanonymous/ComfyUI.git" "ComfyUI"
Clone-IfMissing "https://github.com/ace-step/ACE-Step-1.5.git" "ACE-Step-1.5"
Clone-IfMissing "https://github.com/harry0703/MoneyPrinterTurbo.git" "MoneyPrinterTurbo"
Clone-IfMissing "https://github.com/hungnv26/2d-3d-knowledge-graph.git" "2d-3d-knowledge-graph"
Clone-IfMissing "https://github.com/codeverbojan/remotion-cinematic.git" "saas-demo-templates/remotion-cinematic"
Clone-IfMissing "https://github.com/Co-Messi/supercut.git" "saas-demo-templates/supercut"
Clone-IfMissing "https://github.com/ashrafchowdury/programatic-demo.git" "saas-demo-templates/programatic-demo"
Clone-IfMissing "https://github.com/ThePatriczek/playwright-recast.git" "saas-demo-templates/playwright-recast"
Clone-IfMissing "https://github.com/ytrofr/claude-remotion-editor.git" "saas-demo-templates/claude-remotion-editor"
Clone-IfMissing "https://github.com/noamdorr/saas-product-demo-video.git" "saas-demo-templates/saas-product-demo-video"

if (Test-Path "ComfyUI") {
  New-Item -ItemType Directory -Force -Path "ComfyUI/user/default/workflows" | Out-Null
  Copy-Item -Force "comfyui-workflows/generate_wan22_api.py" "ComfyUI/generate_wan22_api.py"
  Copy-Item -Force "comfyui-workflows/wan22_ti2v_5b_6gb_vram.json" "ComfyUI/user/default/workflows/wan22_ti2v_5b_6gb_vram.json"
  Write-Host "Synced custom Wan 2.2 6GB VRAM workflow & API client into ComfyUI/." -ForegroundColor Green
}

Write-Host "Installing root Node dependencies..." -ForegroundColor Cyan
npm install
Write-Host "Bootstrap complete!" -ForegroundColor Green
