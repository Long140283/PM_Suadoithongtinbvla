@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

:: Chuyen working directory ve thu muc chua script
cd /d "%~dp0"

:: --- CAU HINH ---
set "APP_DIR=%~dp0"
set "DEST_DB_FILE=%APP_DIR%new_database.db"
set "DEST_UPLOADS_PATH=%APP_DIR%app\static\uploads"
set "BACKUP_ROOT=%APP_DIR%backups"

:START
cls
echo ===================================================================
echo            HE THONG PHUC HOI DU LIEU TU DONG
echo ===================================================================
echo.
echo [!] CANH BAO QUAN TRONG:
echo [!] 1. He thong se tu dong dung may chu neu dang chay.
echo [!] 2. Toan bo du lieu hien tai se bi GHI DE bang du lieu sao luu.
echo.
echo -------------------------------------------------------------------
echo           CAC BAN SAO LUU HIEN CO
echo -------------------------------------------------------------------
echo.

if not exist "%BACKUP_ROOT%" (
    echo [!] Khong tim thay thu muc 'backups'.
    echo [!] Vui long chay 'backup.bat' de tao sao luu truoc.
    pause
    exit /b
)

:: Dem va liet ke cac ban sao luu
set i=0
for /d %%d in ("%BACKUP_ROOT%\*") do (
    set /a i+=1
    set "backups[!i!]=%%~nxd"
    echo [!i!] - %%~nxd
)

if !i! equ 0 (
    echo [!] Khong tim thay ban sao luu nao trong thu muc 'backups'.
    pause
    exit /b
)

echo.
:CHOOSE
set "choice="
set /p choice="> Vui long chon mot ban sao luu de phuc hoi (nhap so): "

if not defined choice goto :CHOOSE

set /a choiceNum=%choice% 2>nul

if !choiceNum! lss 1 (
    echo [!] Lua chon khong hop le. Vui long chon so tu 1 den !i!.
    goto :CHOOSE
)
if !choiceNum! gtr !i! (
    echo [!] Lua chon khong hop le. Vui long chon so tu 1 den !i!.
    goto :CHOOSE
)

set "SELECTED_NAME=!backups[%choice%]!"
if not defined SELECTED_NAME (
    echo [!] Lua chon khong hop le. Vui long chon so tu 1 den !i!.
    goto :CHOOSE
)

set "SELECTED_BACKUP_DIR=%BACKUP_ROOT%\!SELECTED_NAME!"
set "SOURCE_DB_FILE=!SELECTED_BACKUP_DIR!\new_database.db"
set "SOURCE_UPLOADS_DIR=!SELECTED_BACKUP_DIR!\uploads"

echo.
echo -------------------------------------------------------------------
echo    Ban da chon phuc hoi tu: !SELECTED_NAME!
echo -------------------------------------------------------------------
echo.

:CONFIRM
set "confirm="
set /p confirm="> Ban co chac chan muon GHI DE du lieu hien tai? (y/n): "

if /i "!confirm!"=="n" (
    echo [-] Da huy bo thao tac phuc hoi.
    pause
    exit /b
)
if /i not "!confirm!"=="y" (
    echo [!] Vui long nhap 'y' hoac 'n'.
    goto :CONFIRM
)

echo.
echo [+] Bat dau qua trinh phuc hoi...
echo.

:: Dung ung dung de dam bao co the ghi de file database
echo [+] Dang dung ung dung (neu dang chay)...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM waitress-serve.exe /T 2>nul

:: 1. Phuc hoi Co so du lieu
if not exist "!SOURCE_DB_FILE!" (
    echo [!] LOI: Khong tim thay file 'new_database.db' trong ban sao luu.
    pause
    exit /b
)
echo [1/2] Dang phuc hoi co so du lieu...
copy /Y "!SOURCE_DB_FILE!" "%DEST_DB_FILE%" >nul
if !errorlevel! neq 0 (
    echo [!] LOI: Khong the phuc hoi file database.
    pause
    exit /b
)
echo [OK] Da phuc hoi database.

:: 2. Phuc hoi thu muc Uploads
if exist "%DEST_UPLOADS_PATH%" (
    echo [+] Dang xoa sach thu muc uploads hien tai de dong bo...
    rmdir /S /Q "%DEST_UPLOADS_PATH%"
)
mkdir "%DEST_UPLOADS_PATH%"

if not exist "!SOURCE_UPLOADS_DIR!" (
    echo [!] CANH BAO: Khong tim thay thu muc 'uploads' trong ban sao luu. Bo qua...
) else (
    echo [2/2] Dang phuc hoi tep dinh kem...
    xcopy /E /I /H /Y "!SOURCE_UPLOADS_DIR!" "%DEST_UPLOADS_PATH%" >nul
    if !errorlevel! neq 0 (
        echo [!] LOI: Khong the phuc hoi thu muc uploads.
        pause
        exit /b
    )
    echo [OK] Da phuc hoi uploads.
)

echo.
echo ===================================================================
echo [+] HOAN THANH PHUC HOI TU: !SELECTED_NAME!
echo [+] Ban co the khoi dong lai may chu ngay bay gio.
echo ===================================================================
pause
exit /b