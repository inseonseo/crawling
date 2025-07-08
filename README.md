# 환율전망 PDF 자동 다운로더

한국수출입은행 환율전망 PDF 파일들을 자동으로 다운로드하는 프로그램

## 📋 사전 준비사항

1. **Python 설치**
   - Python 3.8 이상이 설치되어 있어야 합니다
   - [Python 공식 사이트](https://www.python.org/downloads/)에서 다운로드

2. **Chrome 브라우저**
   - Google Chrome이 설치되어 있어야 합니다
   - 최신 버전 권장
   - default : 137버전(137.##)

## 🚀 사용법

### 방법 1: 자동 실행 (권장)
1. 모든 파일을 같은 폴더에 저장
2. `run_downloader.bat` 파일을 **더블클릭**
3. 자동으로 설치 및 실행됩니다

### 방법 2: 수동 실행
1. 명령 프롬프트(cmd) 열기
2. 파일이 있는 폴더로 이동
3. 다음 명령어들을 순서대로 실행:
   ```
   pip install -r requirements.txt
   pip install webdriver-manager
   python parallel_downloader.py
   ```

## ⚙️ 설정 변경

### 다운로드 범위 변경
`parallel_downloader.py` 파일의 마지막 부분을 수정:

```python
# 현재 설정 (1, 50, 100페이지에서 시작)
downloader.run_parallel(start_pages=[1, 50, 100])

# 예시: 다른 페이지에서 시작하려면
downloader.run_parallel(start_pages=[1, 100, 200])  # 1, 100, 200페이지에서 시작
```

### 다운로드 개수 변경
```python
# 현재 설정 (워커당 10개)
downloader = ParallelDownloader(download_dir="parallel_reports", max_posts_per_worker=10)

# 예시: 워커당 20개로 변경
downloader = ParallelDownloader(download_dir="parallel_reports", max_posts_per_worker=20)
```

## 📁 결과물

다운로드가 완료되면 다음 폴더들이 생성됩니다:
- `parallel_reports_worker_1/` - 1페이지부터 시작한 파일들
- `parallel_reports_worker_2/` - 50페이지부터 시작한 파일들  
- `parallel_reports_worker_3/` - 100페이지부터 시작한 파일들

각 파일은 날짜별로 이름이 변경됩니다 (예: `20250708.pdf`)

## ⏱️ 예상 소요 시간

- **현재 설정**: 약 3-4시간 (2500개 파일 기준)
- **워커당 10개**: 30개 파일 다운로드
- **전체 2500개**: 약 83번 실행 필요

## 🔧 문제 해결

### 오류 1: "Chrome 드라이버를 찾을 수 없습니다"
- Chrome 브라우저가 설치되어 있는지 확인
- Chrome을 최신 버전으로 업데이트

### 오류 2: "pip 명령어를 찾을 수 없습니다"
- Python이 제대로 설치되지 않았습니다
- Python 설치 시 "Add Python to PATH" 옵션을 체크했는지 확인

### 오류 3: "네트워크 연결 오류"
- 인터넷 연결 상태 확인
- 방화벽이나 보안 프로그램이 차단하고 있는지 확인

## ⚠️ 주의사항

- 프로그램 실행 중에는 컴퓨터를 끄지 마세요
- 다운로드 중에는 다른 프로그램을 최소화하는 것이 좋습니다
- 안정적인 인터넷 연결이 필요합니다
