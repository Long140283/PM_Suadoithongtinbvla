@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

:: ===================================================================
::  KHỞI ĐỘNG MÁY CHỦ (PRODUCTION - WAITRESS 24/7)
::  Chạy tay: double-click file này
::  Chạy ngầm: NSSM gọi thẳng python.exe run_service.py
:: ===================================================================

set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

:: --- Xac dinh Python ---
if exist "%APP_DIR%.venv\Scripts\python.exe" (
    set "PYTHON=%APP_DIR%.venv\Scripts\python.exe"
) else (
    set "PYTHON=C:\Users\LONG\AppData\Local\Programs\Python\Python313\python.exe"
)

set PYTHONUTF8=1

echo ===================================================================
echo  May chu: SDTTBV
echo  Dang khoi dong Waitress...
echo  Nhan Ctrl+C de dung.
echo ===================================================================
echo.

"%PYTHON%" "%APP_DIR%run_service.py"

if %errorlevel% neq 0 (
    echo.
    echo [!] May chu da dung hoac gap loi. Kiem tra file: service_log.txt
)

echo.
pause
