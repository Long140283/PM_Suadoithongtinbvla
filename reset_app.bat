@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

:: Chuyen vao thu muc chua script
cd /d "%~dp0"

echo ===================================================================
echo   CONG CU RESET DU LIEU UNG DUNG
echo ===================================================================
echo.
echo CANH BAO: Thao tac nay se xoa:
echo - Du lieu benh nhan, cac phieu da nop, hinh anh/chu ky.
echo - Nhat ky hoat dong (Audit Logs).
echo.
echo Luu y: Tai khoan nguoi dung, Khoa phong, Backups va Templates se duoc GIU LAI.
echo ===================================================================
echo.

set /p AREYOUSURE="Ban co chac chan muon RESET TOAN BO du lieu khong? (Y/N): " 
if /i "%AREYOUSURE%" neq "Y" (
    echo.
    echo Da huy thao tac reset.
    pause >nul
    exit /b
)

:: --- Xu ly dung ung dung ---
echo.
echo [+] Dang dung ung dung (neu dang chay)...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM waitress-serve.exe /T 2>nul

:: --- Xac dinh duong dan Python ---
set "PY="
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY=.venv\Scripts\python.exe"
        echo [OK] Su dung Virtual Environment: .venv
    )
)

if not defined PY (
    py --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY=py"
        echo [OK] Su dung Python Launcher (py)
    ) else (
        set "PY=python"
        echo [!] Su dung Python he thong.
    )
)

:: --- RESET PROCESS ---
echo.
echo [+] Dang thuc hien don dep du lieu Database va Tep tin...
"%PY%" "scripts\reset_app_data.py"

if %errorlevel% neq 0 (
    echo.
    echo [!] LOI: Co loi xay ra trong qua trinh don dep.
    pause
    exit /b
)

echo.
echo [+] Dang don dep tep nhat ky (logs)...
if exist "logs" (
    rmdir /s /q "logs"
    echo [OK] Da xoa thu muc logs.
)
if exist "server_log.txt" (
    del /f /q "server_log.txt"
    echo [OK] Da xoa server_log.txt.
)

echo.
echo [+] Dang don dep ma nguon (pycache, test cache)...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
if exist ".pytest_cache" (
    rmdir /s /q ".pytest_cache"
    echo [OK] Da xoa .pytest_cache.
)

echo.
echo ===================================================================
echo  HOAN THANH: Ung dung da duoc lam sach.
echo  - Chi con lai cac du lieu nhat ky va phieu yeu cau bi xoa.
echo  - Nguoi dung, Khoa phong va cac mau phieu duoc giu nguyen.
echo ===================================================================
echo.
echo [Nhan phim bat ky de thoat]
pause >nul