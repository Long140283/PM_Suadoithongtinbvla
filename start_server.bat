@echo off
REM Change directory to the project root
cd /d d:\patient_app

REM Define a log file path
set LOGFILE=d:\patient_app\server_log.txt

echo Starting server setup at %date% %time% > %LOGFILE%

REM Set Python to use UTF-8 encoding to prevent Unicode errors
set PYTHONUTF8=1
echo PYTHONUTF8 set to 1 >> %LOGFILE%

REM Activate the virtual environment
echo Activating virtual environment... >> %LOGFILE%
call .venv\Scripts\activate >> %LOGFILE% 2>>&1

REM Start the Flask application using waitress and log output
echo Starting server on 0.0.0.0:5001... >> %LOGFILE%
waitress-serve --host=0.0.0.0 --port=5001 run:app >> %LOGFILE% 2>>&1