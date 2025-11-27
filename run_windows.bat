@echo off
REM ==============================================================================
REM MkweliAML - Run Script for Windows
REM ==============================================================================
REM This script handles first-time setup and auto-startup of MkweliAML.
REM Simply double-click this file or run: run_windows.bat
REM ==============================================================================

cd /d "%~dp0"

echo ==============================================
echo   MkweliAML - Sanctions Screening System     
echo ==============================================

REM 1. Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo X Python is required but not installed.
    echo   Please install Python 3.8+ from https://www.python.org/downloads/
    echo   Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

python --version
echo + Python detected

REM 2. Create virtual environment if needed
if not exist "venv" (
    echo - Creating virtual environment...
    python -m venv venv
    echo + Virtual environment created
)

REM 3. Activate virtual environment
echo - Activating virtual environment...
call venv\Scripts\activate.bat

REM 4. Install/upgrade dependencies
echo - Checking dependencies...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

REM 5. Create data folder if it doesn't exist
if not exist "data" (
    echo - Creating data folder...
    mkdir data
)

REM 6. Check for sanctions XML files
set XML_COUNT=0
for %%f in (data\*.xml) do set /a XML_COUNT+=1
if %XML_COUNT% equ 0 (
    echo.
    echo ! No sanctions XML files found in data\ folder!
    echo   Download the following files and place them in data\:
    echo.
    echo   1. UN Consolidated List - Rename to: un_consolidated.xml
    echo      https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list
    echo.
    echo   2. UK Sanctions List - Rename to: uk_consolidated.xml
    echo      https://www.gov.uk/government/publications/the-uk-sanctions-list
    echo.
    echo   3. OFAC SDN List - Rename to: ofac_consolidated.xml
    echo      https://sanctionslist.ofac.treas.gov/Home/SdnList
    echo.
    echo   4. EU Consolidated List - Rename to: eu_consolidated.xml
    echo      https://www.sanctionsmap.eu
    echo.
    echo   The app will start but screening requires these files.
    echo.
) else (
    echo + Found %XML_COUNT% sanctions XML file(s) in data\
)

REM 7. Start the application
echo.
echo ==============================================
echo   Starting MkweliAML...
echo ==============================================
echo   URL: http://localhost:5000
echo   Password: admin123 (change after login)
echo   Press Ctrl+C to stop
echo ==============================================
echo.

python app.py

pause

