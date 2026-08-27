@echo off
title SRT Whiteboard Animation Web Server
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set VENV_PY=%~dp0.venv\Scripts\python.exe

echo ========================================================
echo   DANG KHOI DONG SERVER HOAT HOA BANG TRANG SRT...
echo ========================================================
echo.

if not exist "%VENV_PY%" (
    echo [INFO] Dang khoi tao moi truong...
    python scripts\prepare_env.py
)

"%VENV_PY%" server.py
pause
