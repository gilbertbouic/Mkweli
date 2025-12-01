@echo off
:: Mkweli AML - Setup Configuration Script
:: Helper script for Docker check, environment setup, and application management
:: Usage: setup-config.bat [check|setup|start|stop|status]

setlocal EnableDelayedExpansion

:: Configuration
set APP_NAME=Mkweli AML
set MIN_RAM_MB=4096
set MIN_DISK_GB=5
set DOCKER_URL=https://www.docker.com/products/docker-desktop/
set APP_URL=http://localhost:8000

:: Colors for output (Windows 10+)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "RESET=[0m"

:: Parse command line argument
set "COMMAND=%~1"
if "%COMMAND%"=="" set "COMMAND=help"

goto %COMMAND% 2>nul || goto help

:check
:: Comprehensive system requirements check
echo.
echo %BLUE%========================================%RESET%
echo %BLUE%  %APP_NAME% - System Check%RESET%
echo %BLUE%========================================%RESET%
echo.

call :check_windows
call :check_ram
call :check_disk
call :check_docker

echo.
echo %BLUE%System check complete.%RESET%
echo.
goto end

:check_windows
echo Checking Windows version...
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
if "%VERSION%"=="10.0" (
    echo %GREEN%[PASS]%RESET% Windows 10/11 detected
) else (
    echo %YELLOW%[WARN]%RESET% Windows version %VERSION% - Windows 10/11 recommended
)
exit /b 0

:check_ram
echo Checking system RAM...
for /f "skip=1" %%p in ('wmic computersystem get TotalPhysicalMemory') do (
    set /a RAM_MB=%%p / 1024 / 1024 2>nul
    if defined RAM_MB goto ram_result
)
:ram_result
if !RAM_MB! GEQ %MIN_RAM_MB% (
    echo %GREEN%[PASS]%RESET% RAM: !RAM_MB! MB ^(Minimum: %MIN_RAM_MB% MB^)
) else (
    echo %RED%[FAIL]%RESET% RAM: !RAM_MB! MB ^(Minimum: %MIN_RAM_MB% MB required^)
    echo        Application may run slowly with insufficient RAM.
)
exit /b 0

:check_disk
echo Checking disk space...
for /f "tokens=3" %%a in ('dir /-c "%~dp0" 2^>nul ^| find "bytes free"') do set FREE_BYTES=%%a
set /a FREE_GB=!FREE_BYTES:~0,-9! 2>nul
if not defined FREE_GB set FREE_GB=10
if !FREE_GB! GEQ %MIN_DISK_GB% (
    echo %GREEN%[PASS]%RESET% Disk space: !FREE_GB! GB free ^(Minimum: %MIN_DISK_GB% GB^)
) else (
    echo %YELLOW%[WARN]%RESET% Disk space: !FREE_GB! GB free ^(Minimum: %MIN_DISK_GB% GB recommended^)
)
exit /b 0

:check_docker
echo Checking Docker installation...
where docker >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=3" %%v in ('docker --version 2^>nul') do set DOCKER_VER=%%v
    echo %GREEN%[PASS]%RESET% Docker installed: !DOCKER_VER!
    
    :: Check if Docker is running
    docker info >nul 2>&1
    if !errorlevel!==0 (
        echo %GREEN%[PASS]%RESET% Docker daemon is running
    ) else (
        echo %YELLOW%[WARN]%RESET% Docker is installed but not running
        echo        Please start Docker Desktop before using %APP_NAME%
    )
) else (
    echo %RED%[FAIL]%RESET% Docker Desktop not found
    echo.
    echo %YELLOW%Docker Desktop is required to run %APP_NAME%.%RESET%
    echo.
    echo To install Docker Desktop:
    echo   1. Visit: %DOCKER_URL%
    echo   2. Download Docker Desktop for Windows
    echo   3. Run the installer and follow the prompts
    echo   4. Restart your computer when prompted
    echo   5. Run this setup again
    echo.
    
    :: Offer to open download page
    choice /c YN /m "Would you like to open the Docker download page now"
    if !errorlevel!==1 start "" "%DOCKER_URL%"
)
exit /b 0

:setup
:: Initial environment setup
echo.
echo %BLUE%Setting up %APP_NAME%...%RESET%
echo.

:: Create .env file if it doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        echo Creating configuration file...
        copy ".env.example" ".env" >nul
        echo %GREEN%[DONE]%RESET% Configuration file created
    )
)

:: Build Docker containers
echo Building application containers...
docker-compose build
if %errorlevel%==0 (
    echo %GREEN%[DONE]%RESET% Containers built successfully
) else (
    echo %RED%[FAIL]%RESET% Failed to build containers
    exit /b 1
)

echo.
echo %GREEN%Setup complete!%RESET%
echo Run 'setup-config.bat start' to launch the application.
goto end

:start
:: Start the application
echo.
echo %BLUE%Starting %APP_NAME%...%RESET%
echo.

:: Check if Docker is running
docker info >nul 2>&1
if not %errorlevel%==0 (
    echo %YELLOW%Docker is not running. Starting Docker Desktop...%RESET%
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Waiting for Docker to start...
    timeout /t 30 /nobreak >nul
)

:: Start containers
docker-compose up -d
if %errorlevel%==0 (
    echo.
    echo %GREEN%[DONE]%RESET% Application started successfully!
    echo.
    echo %BLUE%Opening dashboard in your browser...%RESET%
    timeout /t 5 /nobreak >nul
    start "" "%APP_URL%"
    echo.
    echo Access the application at: %APP_URL%
    echo Default password: admin123 ^(please change immediately^)
) else (
    echo %RED%[FAIL]%RESET% Failed to start application
    echo Run 'docker-compose logs' for more information
    exit /b 1
)
goto end

:stop
:: Stop the application
echo.
echo %BLUE%Stopping %APP_NAME%...%RESET%
echo.

docker-compose down
if %errorlevel%==0 (
    echo %GREEN%[DONE]%RESET% Application stopped
) else (
    echo %YELLOW%[WARN]%RESET% Could not stop containers ^(may already be stopped^)
)
goto end

:restart
:: Restart the application
echo.
echo %BLUE%Restarting %APP_NAME%...%RESET%
echo.

docker-compose restart
if %errorlevel%==0 (
    echo %GREEN%[DONE]%RESET% Application restarted
    echo Access the application at: %APP_URL%
) else (
    echo %RED%[FAIL]%RESET% Failed to restart application
    exit /b 1
)
goto end

:status
:: Check application status
echo.
echo %BLUE%%APP_NAME% Status%RESET%
echo ========================================
echo.

docker-compose ps
echo.

:: Check if the application is responding
curl -s -o nul -w "%%{http_code}" %APP_URL%/health >nul 2>&1
if %errorlevel%==0 (
    echo %GREEN%Application is running and healthy%RESET%
    echo Dashboard: %APP_URL%
) else (
    echo %YELLOW%Application may not be running or is still starting%RESET%
)
goto end

:logs
:: View application logs
echo.
echo %BLUE%%APP_NAME% Logs%RESET%
echo ========================================
echo.

docker-compose logs --tail=50
goto end

:help
echo.
echo %BLUE%%APP_NAME% - Configuration Script%RESET%
echo.
echo Usage: setup-config.bat [command]
echo.
echo Commands:
echo   check    - Check system requirements
echo   setup    - Initial setup ^(build containers^)
echo   start    - Start the application
echo   stop     - Stop the application
echo   restart  - Restart the application
echo   status   - Check application status
echo   logs     - View application logs
echo   help     - Show this help message
echo.
goto end

:end
endlocal
