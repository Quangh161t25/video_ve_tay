@echo off
title [SRT Whiteboard Animation] - Khoi Dong Server
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set VENV_PY=%~dp0.venv\Scripts\python.exe

echo ===================================================================
echo     HE THONG VE TAY HOAT HOA BANG TRANG SRT WHITEBOARD
echo ===================================================================
echo.

:: 1. Kiem tra moi truong Python ao .venv
if not exist "%VENV_PY%" (
    echo [!] Khong tim thay moi truong ao .venv. Dang khoi tao...
    python scripts\prepare_env.py
)

:: 2. Thong bao khoi dong
echo [*] Dang khoi dong Web Server tai http://127.0.0.1:8000 ...
echo [OK] Trinh duyet web se tu dong duoc mo sau vai giay!
echo.
echo Ghi chu: De dung server, ban hay dong cua so nay hoac nhan Ctrl+C.
echo ===================================================================
echo.

:: 3. Chay server
"%VENV_PY%" server.py

echo.
echo ===================================================================
echo [THONG BAO] Server da dung. Nhan phim bat ky de thoat.
echo ===================================================================
pause
