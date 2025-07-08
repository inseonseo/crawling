@echo off
chcp 65001 > nul
echo ========================================
echo    Exchange Rate PDF Downloader
echo ========================================
echo.

echo 1. Installing required libraries...
pip install -r requirements.txt

echo.
echo 2. Installing Chrome driver...
pip install webdriver-manager

echo.
echo 3. Starting download...
echo    - Start pages: 1, 50, 100
echo    - Downloads per worker: 10
echo    - Estimated time: 3-4 hours
echo.

python parallel_downloader.py

echo.
echo Download completed!
echo Downloaded files are in parallel_reports_worker_1, 2, 3 folders.
echo.
pause 