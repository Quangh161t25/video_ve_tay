@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set VENV_PY=%~dp0.venv\Scripts\python.exe

if "%~1"=="" goto help
if /i "%~1"=="help" goto help
if /i "%~1"=="web" goto web
if /i "%~1"=="server" goto web
if /i "%~1"=="demo" goto demo
if /i "%~1"=="parse" goto parse
if /i "%~1"=="preview" goto preview
if /i "%~1"=="render" goto render
if /i "%~1"=="merge" goto merge

echo [ERROR] Lenh khong hop le.
goto help

:web
echo [INFO] Dang khoi dong Web Server cuc bo...
"%VENV_PY%" "%~dp0server.py"
goto end

:demo
echo [1/3] Phan tich phu de SRT...
"%VENV_PY%" "%~dp0scripts\parse_srt.py" "%~dp0demo_run\sample_story.srt"
echo.
echo [2/3] Tao anh preview phan vung...
"%VENV_PY%" "%~dp0scripts\render_annotation_preview.py" "%~dp0demo_run\scene-01.png" "%~dp0demo_run\scene-01.annotation.json" "%~dp0demo_run\scene-01_preview.png"
echo.
echo [3/3] Render video whiteboard hoat hoa ve tay...
"%VENV_PY%" "%~dp0scripts\render_stream_whiteboard.py" "%~dp0demo_run\scene-01.png" "%~dp0demo_run\scene-01.annotation.json" "%~dp0demo_run\scene-01_whiteboard.mp4" "%~dp0assets\drawing-hand.png" --ink-path grid --color-fill contour-wipe
echo.
echo [HOAN TAT] Video da xuat tai: demo_run\scene-01_whiteboard.mp4
goto end

:parse
shift
"%VENV_PY%" "%~dp0scripts\parse_srt.py" %*
goto end

:preview
"%VENV_PY%" "%~dp0scripts\render_annotation_preview.py" "%~2" "%~3" "%~4"
goto end

:render
"%VENV_PY%" "%~dp0scripts\render_stream_whiteboard.py" "%~2" "%~3" "%~4" "%~dp0assets\drawing-hand.png" --ink-path grid --color-fill contour-wipe %5 %6 %7 %8
goto end

:merge
shift
"%VENV_PY%" "%~dp0scripts\merge_scenes.py" %*
goto end

:help
echo ========================================================
echo   SRT WHITEBOARD ANIMATION - HUONG DAN SU DUNG
echo ========================================================
echo.
echo Cach su dung:
echo   0. Mo giao dien Web chinh sua va Render truc tiep tren trinh duyet:
echo      .\run_pipeline.bat web
echo.
echo   1. Phan tich file SRT:
echo      .\run_pipeline.bat parse duong_dan_file.srt
echo.
echo   2. Tao anh xem truoc vung ve (Preview Bounding Box):
echo      .\run_pipeline.bat preview anh.png chu_thich.json anh_preview.png
echo.
echo   3. Render video MP4 hoat hoa ve tay:
echo      .\run_pipeline.bat render anh.png chu_thich.json output.mp4
echo.
echo   4. Chay thu nghiem mau (Demo):
echo      .\run_pipeline.bat demo
echo ========================================================

:end
endlocal
