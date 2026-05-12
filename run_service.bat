@echo off
set "PYTHON_EXE=C:\Users\LONG\AppData\Local\Programs\Python\Python313\python.exe"
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

echo Starting Waitress server...
start /high /b /wait "" "%PYTHON_EXE%" -c "from app import create_app; from waitress import serve; app = create_app(); print('Serving on http://0.0.0.0:8001'); serve(app, host='0.0.0.0', port=8001)"
pause