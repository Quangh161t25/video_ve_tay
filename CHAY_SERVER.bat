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

:: 1. Kiem tra va giai phong port 8000 neu co tien trinh cu dang chiem
echo [*] Kiem tra cong mang 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo [!] Phat hien tien trinh cu (PID: %%a) dang chiem port 8000, dang giai phong...
    taskkill /F /PID %%a >nul 2>&1
)

:: 2. Kiem tra moi truong Python
if not exist "%VENV_PY%" (
    echo [!] Khong tim thay moi truong ao .venv. Dang khoi tao...
    python scripts\prepare_env.py
)

:: 3. Chay server
echo [*] Dang khoi dong Web Server tai http://127.0.0.1:8000 ...
echo [OK] Trinh duyet se tu dong mo giao dien chinh!
echo (De dung Server, hay dong cua so nay hoac nhan Ctrl+C)
echo ===================================================================
echo.

"%VENV_PY%" server.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Server bi dung dot ngot (Ma loi: %ERRORLEVEL%).
    pause
)
