@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

:: Chuyen vao thu muc chua script
cd /d "%~dp0"

:: --- CONFIGURATION ---
set "APP_DIR=%~dp0"
set "SOURCE_DB=%APP_DIR%new_database.db"
set "SOURCE_UPLOADS=%APP_DIR%app\static\uploads"
set "BACKUP_ROOT=%APP_DIR%backups"
set RETENTION_DAYS=30

echo ===================================================================
echo   HE THONG SAO LUU DU LIEU TU DONG (BACKUP)
echo ===================================================================
echo [+] Thu muc lam viec : %APP_DIR%
echo [+] Thu muc sao luu   : %BACKUP_ROOT%
echo ===================================================================
echo.

:: Kiem tra database
if not exist "%SOURCE_DB%" (
    echo [!] LOI: Khong tim thay file database tai:
    echo [!]   %SOURCE_DB%
    echo [!] Qua trinh sao luu da bi huy bo.
    pause
    exit /b
)

:: Lay timestamp bang PowerShell de tranh loi locale va WMIC deprecated
for /f "usebackq delims=" %%A in (`powershell -NoProfile -Command "Get-Date -Format 'yyyyMMdd_HHmm'"`) do set "TIMESTAMP=%%A"

if not defined TIMESTAMP (
    echo [!] LOI: Khong lay duoc thoi gian he thong.
    pause
    exit /b
)

set "BACKUP_SUBDIR=%BACKUP_ROOT%\backup_!TIMESTAMP!"
echo [+] Thoi gian sao luu : !TIMESTAMP!
echo [+] Thu muc luu tru  : !BACKUP_SUBDIR!
echo.

:: Dung ung dung de dam bao tinh toan ven du lieu
echo [+] Dang dung ung dung de sao luu...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM waitress-serve.exe /T 2>nul

if not exist "%BACKUP_ROOT%" (
    mkdir "%BACKUP_ROOT%"
    if errorlevel 1 (
        echo [!] LOI: Khong the tao thu muc backup goc.
        pause
        exit /b
    )
)

mkdir "!BACKUP_SUBDIR!"
if errorlevel 1 (
    echo [!] LOI: Khong the tao thu muc sao luu con.
    pause
    exit /b
)
echo [OK] Da tao thu muc sao luu.

echo.
echo [1/2] Dang sao luu database...
copy /Y "%SOURCE_DB%" "!BACKUP_SUBDIR!\new_database.db" >nul
if errorlevel 1 (
    echo [!] LOI: Khong the sao luu database.
) else (
    echo [OK] Da sao luu database.
)

if exist "%SOURCE_UPLOADS%" (
    echo [2/2] Dang sao luu uploads...
    xcopy /E /I /H /Y "%SOURCE_UPLOADS%" "!BACKUP_SUBDIR!\uploads" >nul
    if errorlevel 1 (
        echo [!] LOI: Khong the sao luu thu muc uploads.
    ) else (
        echo [OK] Da sao luu thu muc uploads.
    )
) else (
    echo [SKIP] Thu muc uploads khong ton tai, bo qua.
    mkdir "!BACKUP_SUBDIR!\uploads"
)

echo.
echo [+] Dang don dep cac ban sao luu cu (hon %RETENTION_DAYS% ngay)...
forfiles /P "%BACKUP_ROOT%" /D -%RETENTION_DAYS% /C "cmd /c if @isdir==TRUE rd /s /q @path" 2>nul

echo.
echo ===================================================================
echo [OK] HOAN THANH SAO LUU: !TIMESTAMP!
echo ===================================================================
echo.

if "%1"=="" (
    echo [Nhan phim bat ky de thoat]
    pause >nul
)