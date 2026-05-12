@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

:: ===================================================================
::  KHỞI ĐỘNG MÁY CHỦ (PRODUCTION - WAITRESS)
::  Dành cho việc triển khai để các máy con truy cập.
:: ===================================================================

set APP_DIR=%~dp0
set LOGFILE=%APP_DIR%server_log.txt

echo [%date% %time%] Dang khoi dong may chu... > "%LOGFILE%"

:: Chuyển working directory về thư mục ứng dụng
cd /d "%APP_DIR%"

:: Thiết lập Unicode để hiện thị tiếng Việt đúng
set PYTHONUTF8=1

:: --- Xác định đường dẫn Python ---
:: Ưu tiên Virtual Environment trong thư mục ứng dụng
if exist "%APP_DIR%.venv\Scripts\python.exe" (
    set PYTHON="%APP_DIR%.venv\Scripts\python.exe"
    echo [OK] Su dung Virtual Environment: %PYTHON%
) else (
    set PYTHON=python
    echo [!] Khong tim thay .venv, dang dung Python he thong.
)

echo [%date% %time%] Python: %PYTHON% >> "%LOGFILE%"

:: --- Khởi động Waitress ---
echo.
echo ===================================================================
echo  Khoi dong may chu Waitress tren tat ca cac giao dien mang...
echo  Cac may con co the truy cap qua: http://[IP_MAY_CHU]:8001
echo  Nhan Ctrl+C de dung may chu.
echo ===================================================================
echo.

echo [%date% %time%] Khoi dong Waitress... >> "%LOGFILE%"
start /high /b /wait "" %PYTHON% -m waitress --host=0.0.0.0 --port=8001 --threads=8 --call "app:create_app" >> "%LOGFILE%" 2>&1

if %errorlevel% neq 0 (
    echo.
    echo [!] May chu da dung hoac gap loi. Kiem tra file: server_log.txt
    echo [%date% %time%] May chu da dung (errorlevel=%errorlevel%) >> "%LOGFILE%"
)

echo.
echo [May chu da dung. Nhan phim bat ky de thoat...]
pause >nul