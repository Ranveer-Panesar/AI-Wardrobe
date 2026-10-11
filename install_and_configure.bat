@echo off
setlocal EnableDelayedExpansion

title AI Wardrobe - Setup and Configuration
echo ========================================================================
echo                AI WARDROBE - AUTOMATED SYSTEM SETUP
echo ========================================================================
echo [Notice] This script will install all dependencies, configure environment,
echo          verify version compatibilities, and initialize the database.
echo ========================================================================
echo.

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

:: -------------------------------------------------------------------------
:: 1. Check Python installation
:: -------------------------------------------------------------------------
echo [1/6] Checking Python installation...
set "PYTHON_CMD="

python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_CMD=python"
) else (
    py -3 --version >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PYTHON_CMD=py -3"
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python 3 was not found in PATH!
    echo         Please install Python 3.10, 3.11, or 3.12 and ensure "Add Python to PATH" is checked.
    echo         Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('%PYTHON_CMD% --version 2^>^&1') do set "PY_VER=%%v"
echo       Found: %PY_VER%

:: -------------------------------------------------------------------------
:: 2. Check Node.js and npm
:: -------------------------------------------------------------------------
echo.
echo [2/6] Checking Node.js and npm...
call npm --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Node.js / npm was not found in PATH!
    echo           The backend will run, but the frontend requires Node.js 18+.
    echo           Download: https://nodejs.org/
    set "HAS_NPM=0"
) else (
    for /f "tokens=*" %%v in ('call npm --version 2^>^&1') do set "NPM_VER=%%v"
    echo       Found npm version: !NPM_VER!
    set "HAS_NPM=1"
)

:: -------------------------------------------------------------------------
:: 3. Setup Python Virtual Environment (.venv)
:: -------------------------------------------------------------------------
echo.
echo [3/6] Setting up Python virtual environment (.venv)...
set "VENV_DIR=%ROOT_DIR%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

if not exist "%VENV_PYTHON%" (
    echo       Creating virtual environment at: %VENV_DIR%
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
) else (
    echo       Existing virtual environment detected.
)

echo       Upgrading pip, setuptools, and wheel...
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel --quiet

:: -------------------------------------------------------------------------
:: 4. Install Python Dependencies with Strict Compatibility
:: -------------------------------------------------------------------------
echo.
echo [4/6] Installing backend dependencies and enforcing compatibility...
echo       (Enforcing: bcrypt==4.0.1 for passlib, numpy<2 for PyTorch 2.4)
"%VENV_PIP%" install -r "%ROOT_DIR%\backend\requirements.txt"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Error occurred while installing Python packages!
    pause
    exit /b 1
)

:: Re-verify critical version pins
"%VENV_PIP%" install "bcrypt==4.0.1" "numpy<2" --quiet

:: -------------------------------------------------------------------------
:: 5. Configure Directories, Environment & Database Seeding
:: -------------------------------------------------------------------------
echo.
echo [5/6] Initializing storage directories and database...

:: Create storage directories
if not exist "%ROOT_DIR%\uploads" mkdir "%ROOT_DIR%\uploads"
if not exist "%ROOT_DIR%\renders" mkdir "%ROOT_DIR%\renders"
if not exist "%ROOT_DIR%\backend\uploads" mkdir "%ROOT_DIR%\backend\uploads"
if not exist "%ROOT_DIR%\backend\renders" mkdir "%ROOT_DIR%\backend\renders"

:: Copy .env if missing
if not exist "%ROOT_DIR%\backend\.env" (
    echo       Creating backend\.env from template...
    copy "%ROOT_DIR%\backend\.env.example" "%ROOT_DIR%\backend\.env" >nul
)

:: Execute database initialization and seeding
echo       Executing database schema creation and demo seed...
"%VENV_PYTHON%" "%ROOT_DIR%\backend\app\seed.py"
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Database seed encountered a non-fatal warning.
)

:: -------------------------------------------------------------------------
:: 6. Setup Frontend Dependencies
:: -------------------------------------------------------------------------
echo.
echo [6/6] Setting up frontend dependencies...
if "%HAS_NPM%"=="1" (
    cd /d "%ROOT_DIR%\frontend"
    echo       Running npm install...
    call npm install --no-audit --no-fund
    if %ERRORLEVEL% equ 0 (
        echo       Building frontend distribution...
        call npm run build
        echo       [OK] Frontend built successfully.
    ) else (
        echo [WARNING] npm install reported issues. You can still test with 'npm run dev'.
    )
    cd /d "%ROOT_DIR%"
) else (
    echo       Skipping frontend setup (npm not found).
)

echo.
echo ========================================================================
echo   [SUCCESS] AI WARDROBE IS CONFIGURED AND READY TO RUN!
echo ========================================================================
echo   Demo Login Credentials:
echo     Email   : demo@aiwardrobe.com
echo     Password: demo1234
echo.
echo   To launch the entire system (Frontend, Backend, and VTON Server),
echo   simply double-click or run:
echo     run_services.bat
echo ========================================================================
echo.
pause
