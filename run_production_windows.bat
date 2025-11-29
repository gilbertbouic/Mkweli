@echo off
REM =============================================================================
REM Mkweli AML - Windows Production Deployment Script
REM Run without Docker using Waitress WSGI server (Windows-compatible)
REM =============================================================================

setlocal EnableDelayedExpansion

echo ========================================
echo   Mkweli AML - Production Server
echo ========================================
echo.

REM Configuration (can be overridden by environment variables)
if "%PORT%"=="" set PORT=8000
if "%WORKERS%"=="" set WORKERS=4
set VENV_DIR=venv

REM Check Python version
echo [1/6] Checking Python version...
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo [OK] Python detected

REM Create virtual environment if not exists
echo.
echo [2/6] Setting up virtual environment...
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
    if %ERRORLEVEL% neq 0 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)

REM Activate virtual environment
call %VENV_DIR%\Scripts\activate.bat

REM Install dependencies
echo.
echo [3/6] Installing production dependencies...
pip install --quiet --upgrade pip
if exist "requirements-prod.txt" (
    pip install --quiet -r requirements-prod.txt
) else (
    pip install --quiet -r requirements.txt
)
REM Install Waitress (Windows-compatible WSGI server)
pip install --quiet waitress
echo [OK] Dependencies installed

REM Check for .env file
echo.
echo [4/6] Checking configuration...
if not exist ".env" (
    if exist ".env.example" (
        echo Warning: .env file not found. Creating from .env.example
        copy .env.example .env >nul
        REM Generate a random SECRET_KEY
        for /f "delims=" %%i in ('python -c "import secrets; print(secrets.token_hex(32))"') do set NEW_SECRET=%%i
        python -c "import sys; content=open('.env').read(); content=content.replace('your-secure-secret-key-here-change-me','%NEW_SECRET%'); open('.env','w').write(content)"
        echo [OK] Generated new SECRET_KEY
    ) else (
        echo Warning: No .env file found. Using defaults.
    )
) else (
    echo [OK] Configuration file found
)

REM Create necessary directories
echo.
echo [5/6] Creating directories...
if not exist "instance" mkdir instance
if not exist "uploads" mkdir uploads
if not exist "data" mkdir data
echo [OK] Directories ready

REM Check for sanctions data
echo.
echo [6/6] Checking sanctions data...
set MISSING_FILES=0
if not exist "data\un_consolidated.xml" (
    echo   Warning: data\un_consolidated.xml not found
    set /a MISSING_FILES+=1
)
if not exist "data\uk_consolidated.xml" (
    echo   Warning: data\uk_consolidated.xml not found
    set /a MISSING_FILES+=1
)
if not exist "data\ofac_consolidated.xml" (
    echo   Warning: data\ofac_consolidated.xml not found
    set /a MISSING_FILES+=1
)
if not exist "data\eu_consolidated.xml" (
    echo   Warning: data\eu_consolidated.xml not found
    set /a MISSING_FILES+=1
)
if %MISSING_FILES%==0 (
    echo [OK] All sanctions data files present
) else (
    echo Note: Some sanctions data files are missing.
    echo       The application will start but screening may be limited.
)

echo.
echo ========================================
echo Starting Production Server
echo ========================================
echo.
echo Port:    %PORT%
echo Workers: %WORKERS%
echo URL:     http://localhost:%PORT%
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start Waitress (Windows-compatible WSGI server)
python -c "from waitress import serve; from app import app; print('Starting Waitress server...'); serve(app, host='0.0.0.0', port=%PORT%, threads=%WORKERS%)"

pause
