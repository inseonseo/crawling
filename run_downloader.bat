@echo off
echo ========================================
echo    환율전망 PDF 다운로더
echo ========================================
echo.

echo 1. 필요한 라이브러리 설치 중...
pip install -r requirements.txt

echo.
echo 2. Chrome 드라이버 설치 중...
pip install webdriver-manager

echo.
echo 3. 다운로드 시작...
echo    - 시작 페이지: 1, 50, 100
echo    - 워커당 다운로드 수: 10개
echo    - 예상 소요 시간: 3-4시간
echo.

python parallel_downloader.py

echo.
echo 다운로드가 완료되었습니다!
echo 다운로드된 파일들은 parallel_reports_worker_1, 2, 3 폴더에 있습니다.
echo.
pause 