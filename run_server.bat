@echo off
cd /d "%~dp0"

set VENV_PATH=%~dp0.venv

if not exist "%VENV_PATH%\Scripts\activate" (
    echo [!] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

call "%VENV_PATH%\Scripts\activate"

python run.py