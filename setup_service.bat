@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "NSSM_PATH=%~dp0tools\nssm.exe"
set "SCRIPT_PATH=%~dp0run_server.bat"

if not exist "%NSSM_PATH%" (
    echo [!] Khong tim thay nssm.exe tai duong dan: %NSSM_PATH%
    echo [!] Vui long tai NSSM ve va dat vao thu muc 'tools'.
    pause
    goto :EOF
)

:MENU
cls
echo =================================================
echo        CAI DAT DICH VU VOI NSSM
echo =================================================
echo.
echo   1. Cai dat dich vu moi
echo   2. Xoa dich vu da co
echo   3. Thoat
echo.
set /p choice="Chon mot tuy chon: "

if "%choice%"=="1" goto :INSTALL
if "%choice%"=="2" goto :UNINSTALL
if "%choice%"=="3" goto :EOF
goto :MENU

:INSTALL
cls
echo --- CAI DAT DICH VU ---
set /p SERVICE_NAME="Nhap ten cho dich vu (vi du: MyWebApp): "
if not defined SERVICE_NAME (
    echo [!] Ten dich vu khong duoc de trong.
    pause
    goto :INSTALL
)

"%NSSM_PATH%" install "%SERVICE_NAME%" ""%SCRIPT_PATH%""
if errorlevel 1 (
    echo [!] Co loi xay ra khi cai dat dich vu.
) else (
    echo [+] Da cai dat dich vu '%SERVICE_NAME%' thanh cong.
    "%NSSM_PATH%" set "%SERVICE_NAME%" AppDirectory "%~dp0"
    "%NSSM_PATH%" set "%SERVICE_NAME%" AppStopMethodSkip 6
    echo [+] Da cau hinh thu muc goc va phuong thuc dung.
    
    :START_SERVICE
    set /p start_choice="Ban co muon khoi dong dich vu ngay bay gio? (y/n): "
    if /i "%start_choice%"=="y" (
        "%NSSM_PATH%" start "%SERVICE_NAME%"
    ) else if /i not "%start_choice%"=="n" (
        goto :START_SERVICE
    )
)
pause
goto :MENU

:UNINSTALL
cls
echo --- XOA DICH VU ---
set /p SERVICE_NAME="Nhap ten dich vu can xoa: "
if not defined SERVICE_NAME (
    echo [!] Ten dich vu khong duoc de trong.
    pause
    goto :UNINSTALL
)

"%NSSM_PATH%" remove "%SERVICE_NAME%" confirm
if errorlevel 1 (
    echo [!] Co loi xay ra khi xoa dich vu. Kiem tra lai ten dich vu.
) else (
    echo [+] Da xoa dich vu '%SERVICE_NAME%' thanh cong.
)
pause
goto :MENU