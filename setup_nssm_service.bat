@echo off
:: ===================================================================
::  CHAY FILE NAY VOI QUYEN ADMIN (Chuot phai > Run as administrator)
:: ===================================================================

setlocal
chcp 65001 >nul

set "NSSM=C:\nssm\nssm.exe"
set "SERVICE=PM_SuaDoiThongTin"
set "APP_DIR=D:\PM_SuaDoiThongTin"
set "PYTHON=C:\Users\LONG\AppData\Local\Programs\Python\Python313\python.exe"

echo.
echo === Kiem tra quyen Admin ===
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Ban chua chay voi quyen Admin!
    echo       Chuot phai vao file nay chon "Run as administrator"
    pause
    exit /b 1
)
echo [OK] Dang chay voi quyen Admin.

echo.
echo === Kiem tra Python tai: %PYTHON% ===
if not exist "%PYTHON%" (
    echo [LOI] Khong tim thay Python tai: %PYTHON%
    pause
    exit /b 1
)
echo [OK] Tim thay Python.

echo.
echo === Dung service ===
"%NSSM%" stop %SERVICE% 2>nul
timeout /t 3 /nobreak >nul

echo.
echo === Xoa cau hinh Python cu ===
"%NSSM%" set %SERVICE% Application "%PYTHON%"
echo [OK] Application = %PYTHON%

"%NSSM%" set %SERVICE% AppDirectory "%APP_DIR%"
echo [OK] AppDirectory = %APP_DIR%

"%NSSM%" set %SERVICE% AppParameters "run_service.py"
echo [OK] AppParameters = run_service.py

"%NSSM%" set %SERVICE% AppStdout "%APP_DIR%\service_log.txt"
"%NSSM%" set %SERVICE% AppStderr "%APP_DIR%\service_log.txt"
"%NSSM%" set %SERVICE% AppStdoutCreationDisposition 4
"%NSSM%" set %SERVICE% AppStderrCreationDisposition 4
echo [OK] Log = %APP_DIR%\service_log.txt

"%NSSM%" set %SERVICE% AppExit Default Restart
"%NSSM%" set %SERVICE% AppRestartDelay 5000
echo [OK] Auto-restart = ON

"%NSSM%" set %SERVICE% AppEnvironmentExtra "PYTHONUTF8=1" "PYTHONUNBUFFERED=1"
"%NSSM%" set %SERVICE% Start SERVICE_AUTO_START

echo.
echo === Xac nhan cau hinh da luu ===
echo Application hien tai:
"%NSSM%" get %SERVICE% Application

echo AppParameters hien tai:
"%NSSM%" get %SERVICE% AppParameters

echo.
echo === Khoi dong service ===
"%NSSM%" start %SERVICE%
timeout /t 5 /nobreak >nul

echo.
echo === Trang thai service ===
"%NSSM%" status %SERVICE%

echo.
echo === XONG! Kiem tra log tai: %APP_DIR%\service_log.txt ===
echo.
pause
