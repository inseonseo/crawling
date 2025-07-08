@echo off
chcp 65001 > nul
echo ========================================
echo    Exchange Rate PDF Downloader Setup
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    echo.
    echo Python installation guide:
    echo 1. Visit https://www.python.org/downloads/
    echo 2. Click "Download Python"
    echo 3. Check "Add Python to PATH" during installation
    echo 4. Run this file again after installation
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Python is installed.
python --version

echo.
echo Installing required libraries...
pip install selenium==4.15.2
pip install webdriver-manager==4.0.1

echo.
echo Checking Chrome browser...
reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Chrome browser may not be installed.
    echo Please install Chrome browser: https://www.google.com/chrome/
) else (
    echo [SUCCESS] Chrome browser is installed.
)

echo.
echo ========================================
echo    Setup Completed!
echo ========================================
echo.
echo Now run run_downloader.bat file.
echo.
pause 