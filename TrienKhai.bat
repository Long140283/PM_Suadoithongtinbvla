@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo ==========================================================
echo        CHƯƠNG TRÌNH KHỞI ĐỘNG VÀ TRIỂN KHAI TỰ ĐỘNG
echo ==========================================================
echo.
echo Khi copy thu muc ung dung sang mot may tinh khac, moi truong ao
echo cua Python thuong bi hong do sai duong dan.
echo Kich ban nay se tu dong kiem tra va cai dat lai neu can thiet!
echo.

set APP_DIR=%~dp0
cd /d "%APP_DIR%"

:: 1. Kiem tra xem Python da duoc cai dat chua
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LỖI] Khong tim thay Python tren may nay! 
    echo [*] Cach khac phuc:
    echo     1. Tai Python tai: https://www.python.org/downloads/
    echo     2. KHI CAI DAT, BAT BUOC phai tick vao o "Add Python to PATH"
    echo     3. Cai dat xong, chay lai file nay.
    echo.
    pause
    exit /b 1
)

:: 2. Kiem tra moi truong ao (.venv)
set VENV_OK=0
if exist ".venv\Scripts\python.exe" (
    :: Thu chay thuc te xem file co hoat dong khong (vi copy sang may khac se bi loi duong dan)
    ".venv\Scripts\python.exe" -c "print('OK')" >nul 2>&1
    if !errorlevel! equ 0 (
        set VENV_OK=1
    )
)

if !VENV_OK! equ 0 (
    echo [!] Phat hien moi truong ao bi hong hoac chua co (do chuyen may).
    echo [*] He thong dang tu dong thiet lap lai, vui long doi it phut...
    
    if exist ".venv" (
        rmdir /s /q ".venv"
    )
    
    python -m venv .venv
    if !errorlevel! neq 0 (
        echo [LỖI] Khong the tao moi truong ao. Hay thu chay file voi quyen Administrator.
        pause
        exit /b 1
    )
    
    echo [*] Dang cai dat cac thu vien can thiet...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    
    echo [OK] Cai dat moi truong thanh cong!
    echo.
) else (
    echo [OK] Moi truong chay on dinh.
)

:: 3. Chay Server
echo.
echo [*] Dang khoi dong may chu he thong...
echo ==========================================================
echo  May chu dang chay tai: http://localhost:8001
echo  De tat may chu, hay dong cua so mau den nay.
echo ==========================================================

:: Thiet lap Unicode de doc tieng Viet
set PYTHONUTF8=1

start /high /b /wait "" ".venv\Scripts\python.exe" -m waitress --host=0.0.0.0 --port=8001 --threads=8 --call "app:create_app"

if %errorlevel% neq 0 (
    echo [!] Da co loi xay ra hoac server bi dung.
    pause
)
