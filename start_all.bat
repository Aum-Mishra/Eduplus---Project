@echo off
REM ========================================
REM EduPlus - Start All Servers
REM Flask Backend + Rasa Chatbot + React UI
REM ========================================

echo.
echo ========================================
echo  EduPlus - Starting All Servers
echo ========================================
echo.

REM ---- Check Flask venv ----
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Flask venv not found at .venv\
    echo         Run:  python -m venv .venv
    pause
    exit /b 1
)

REM ---- Check Rasa venv ----
if not exist "Chatbot\venv_rasa\Scripts\python.exe" (
    echo [ERROR] Rasa venv not found at Chatbot\venv_rasa\
    echo         Run setup_improved.bat inside the Chatbot\ folder first.
    pause
    exit /b 1
)

echo [1] Starting Rasa Action Server on port 5055...
start "Rasa Action Server" cmd /k "cd /d %~dp0Chatbot && venv_rasa\Scripts\activate.bat && python -m rasa run actions --port 5055"

timeout /t 3 /nobreak > nul

echo [2] Starting Rasa HTTP Server on port 5005...
start "Rasa HTTP Server" cmd /k "cd /d %~dp0Chatbot && venv_rasa\Scripts\activate.bat && python -m rasa run --enable-api --cors * --port 5005"

timeout /t 2 /nobreak > nul

echo [3] Starting Flask Backend on port 5000...
start "Flask Backend" cmd /k "cd /d %~dp0 && .venv\Scripts\activate.bat && python app.py"

echo.
echo ========================================
echo  All servers started in separate windows
echo ----------------------------------------
echo  Flask API   : http://localhost:5000
echo  Rasa API    : http://localhost:5005
echo  Action Srvr : http://localhost:5055
echo.
echo  NOTE: Wait ~60-90 sec for Rasa to load
echo        its model before using the chatbot.
echo.
echo  Start React frontend separately:
echo    cd "UI Eduplus"
echo    npm run dev
echo ========================================
echo.
pause
