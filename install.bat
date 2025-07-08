@echo off
echo ========================================
echo    환율전망 PDF 다운로더 설치
echo ========================================
echo.

echo Python 설치 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되지 않았습니다.
    echo.
    echo Python 설치 방법:
    echo 1. https://www.python.org/downloads/ 접속
    echo 2. "Download Python" 클릭
    echo 3. 설치 시 "Add Python to PATH" 체크박스 선택
    echo 4. 설치 완료 후 이 파일을 다시 실행하세요
    echo.
    pause
    exit /b 1
)

echo [성공] Python이 설치되어 있습니다.
python --version

echo.
echo 필요한 라이브러리 설치 중...
pip install selenium==4.15.2
pip install webdriver-manager==4.0.1

echo.
echo Chrome 브라우저 확인 중...
reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version >nul 2>&1
if errorlevel 1 (
    echo [경고] Chrome 브라우저가 설치되지 않았을 수 있습니다.
    echo Chrome 브라우저를 설치해주세요: https://www.google.com/chrome/
) else (
    echo [성공] Chrome 브라우저가 설치되어 있습니다.
)

echo.
echo ========================================
echo    설치 완료!
echo ========================================
echo.
echo 이제 run_downloader.bat 파일을 실행하세요.
echo.
pause 