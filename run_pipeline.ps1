param (
    [string]$Command = "help",
    [string]$Arg1,
    [string]$Arg2,
    [string]$Arg3,
    [string]$Arg4
)

$env:PYTHONIOENCODING = "utf-8"
$VenvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPy)) {
    Write-Host "[ERROR] Chua tim thay moi truong ao. Dang khoi tao..." -ForegroundColor Yellow
    python (Join-Path $PSScriptRoot "scripts\prepare_env.py")
}

switch ($Command.ToLower()) {
    "web" {
        Write-Host "[INFO] Dang khoi dong Web Server cuc bo..." -ForegroundColor Cyan
        & $VenvPy (Join-Path $PSScriptRoot "server.py")
    }
    "server" {
        Write-Host "[INFO] Dang khoi dong Web Server cuc bo..." -ForegroundColor Cyan
        & $VenvPy (Join-Path $PSScriptRoot "server.py")
    }
    "demo" {
        Write-Host "[1/3] Phan tich phu de SRT..." -ForegroundColor Cyan
        & $VenvPy (Join-Path $PSScriptRoot "scripts\parse_srt.py") (Join-Path $PSScriptRoot "demo_run\sample_story.srt")
        Write-Host "`n[2/3] Tao anh preview phan vung..." -ForegroundColor Cyan
        & $VenvPy (Join-Path $PSScriptRoot "scripts\render_annotation_preview.py") (Join-Path $PSScriptRoot "demo_run\scene-01.png") (Join-Path $PSScriptRoot "demo_run\scene-01.annotation.json") (Join-Path $PSScriptRoot "demo_run\scene-01_preview.png")
        Write-Host "`n[3/3] Render video whiteboard hoat hoa ve tay..." -ForegroundColor Cyan
        & $VenvPy (Join-Path $PSScriptRoot "scripts\render_stream_whiteboard.py") (Join-Path $PSScriptRoot "demo_run\scene-01.png") (Join-Path $PSScriptRoot "demo_run\scene-01.annotation.json") (Join-Path $PSScriptRoot "demo_run\scene-01_whiteboard.mp4") (Join-Path $PSScriptRoot "assets\drawing-hand.png") --ink-path grid --color-fill contour-wipe
        Write-Host "`n[HOAN TAT] Video da xuat tai: demo_run\scene-01_whiteboard.mp4" -ForegroundColor Green
    }
    "parse" {
        & $VenvPy (Join-Path $PSScriptRoot "scripts\parse_srt.py") $Arg1
    }
    "preview" {
        & $VenvPy (Join-Path $PSScriptRoot "scripts\render_annotation_preview.py") $Arg1 $Arg2 $Arg3
    }
    "render" {
        & $VenvPy (Join-Path $PSScriptRoot "scripts\render_stream_whiteboard.py") $Arg1 $Arg2 $Arg3 (Join-Path $PSScriptRoot "assets\drawing-hand.png") --ink-path grid --color-fill contour-wipe
    }
    default {
        Write-Host "========================================================" -ForegroundColor Cyan
        Write-Host "  SRT WHITEBOARD ANIMATION - HUONG DAN SU DUNG" -ForegroundColor Yellow
        Write-Host "========================================================"
        Write-Host "Cach su dung:"
        Write-Host "  0. Mo Web Server cuc bo de Chinh sua & Render truc tiep tren Web:"
        Write-Host "     .\run_pipeline.ps1 web"
        Write-Host "`n  1. Phan tich file SRT:"
        Write-Host "     .\run_pipeline.ps1 parse duong_dan_file.srt"
        Write-Host "`n  2. Tao anh xem truoc vung ve (Preview Bounding Box):"
        Write-Host "     .\run_pipeline.ps1 preview anh.png chu_thich.json anh_preview.png"
        Write-Host "`n  3. Render video MP4 hoat hoa ve tay:"
        Write-Host "     .\run_pipeline.ps1 render anh.png chu_thich.json output.mp4"
        Write-Host "`n  4. Chay thu nghiem mau (Demo):"
        Write-Host "     .\run_pipeline.ps1 demo"
        Write-Host "========================================================" -ForegroundColor Cyan
    }
}
