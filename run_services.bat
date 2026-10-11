@echo off
setlocal EnableDelayedExpansion

title AI Wardrobe - Service Manager
echo ========================================================================
echo                 AI WARDROBE - LAUNCHING ALL SERVICES
echo ========================================================================

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

:: 1. Determine Python executable
set "PYTHON_EXE="
if exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
    echo [Environment] Using virtual environment Python: .venv
) else (
    python --version >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PYTHON_EXE=python"
        echo [Environment] Using system Python
    ) else (
        echo [ERROR] Python not found! Please run 'install_and_configure.bat' first.
        pause
        exit /b 1
    )
)

:: 2. Ensure directories & environment exist
if not exist "%ROOT_DIR%\uploads" mkdir "%ROOT_DIR%\uploads"
if not exist "%ROOT_DIR%\renders" mkdir "%ROOT_DIR%\renders"
if not exist "%ROOT_DIR%\backend\uploads" mkdir "%ROOT_DIR%\backend\uploads"
if not exist "%ROOT_DIR%\backend\renders" mkdir "%ROOT_DIR%\backend\renders"

if not exist "%ROOT_DIR%\backend\.env" (
    if exist "%ROOT_DIR%\backend\.env.example" (
        copy "%ROOT_DIR%\backend\.env.example" "%ROOT_DIR%\backend\.env" >nul
    )
)

echo.
echo [1/3] Starting Virtual Try-On Server (Port 8001)...
start "AI Wardrobe - VTON Server [Port 8001]" cmd /k "title AI Wardrobe - VTON Server [Port 8001] && cd /d "%ROOT_DIR%" && "%PYTHON_EXE%" ml-colab/local_vton_server.py"

echo [2/3] Starting FastAPI Backend Server (Port 8000)...
start "AI Wardrobe - Backend API [Port 8000]" cmd /k "title AI Wardrobe - Backend API [Port 8000] && cd /d "%ROOT_DIR%\backend" && "%PYTHON_EXE%" -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0"

echo [3/3] Starting React Vite Frontend (Port 5173)...
start "AI Wardrobe - Frontend [Port 5173]" cmd /k "title AI Wardrobe - Frontend [Port 5173] && cd /d "%ROOT_DIR%\frontend" && npm run dev"

echo.
echo Waiting 4 seconds for services to bind ports...
timeout /t 4 /nobreak >nul

echo Opening browser at http://localhost:5173 ...
start http://localhost:5173

:MENU
cls
echo ========================================================================
echo                 AI WARDROBE - ACTIVE SERVICE DASHBOARD
echo ========================================================================
echo   [Frontend Application] : http://localhost:5173
echo   [FastAPI Backend API]  : http://localhost:8000
echo   [Interactive Docs API] : http://localhost:8000/docs
echo   [VTON Inference Server]: http://localhost:8001
echo   [Health Check]         : http://localhost:8000/health
echo ------------------------------------------------------------------------
echo   Demo Credentials:
echo     Email   : demo@aiwardrobe.com
echo     Password: demo1234
echo ========================================================================
echo   [O] Open Web App in browser
echo   [D] Open API Documentation (Swagger)
echo   [S] Run Database Seed / Synthetic Closet
echo   [Q] Stop all AI Wardrobe services and exit
echo ========================================================================
set /p CHOICE="Select an option [O, D, S, Q]: "

if /i "%CHOICE%"=="O" (
    start http://localhost:5173
    goto MENU
)
if /i "%CHOICE%"=="D" (
    start http://localhost:8000/docs
    goto MENU
)
if /i "%CHOICE%"=="S" (
    echo.
    echo Running database seed...
    "%PYTHON_EXE%" "%ROOT_DIR%\backend\app\seed.py"
    echo [Done]
    pause
    goto MENU
)
if /i "%CHOICE%"=="Q" (
    echo.
    echo Stopping AI Wardrobe service windows...
    taskkill /fi "WINDOWTITLE eq AI Wardrobe*" /f >nul 2>&1
    echo All services stopped. Goodbye!
    timeout /t 2 >nul
    exit /b 0
)

goto MENU
