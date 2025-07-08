# ========================================
# 환율전망 PDF 다운로더 설정 파일
# ========================================

# 다운로드 설정
DOWNLOAD_CONFIG = {
    # 시작 페이지 설정 (여러 페이지에서 동시에 시작)
    # 예: [1, 50, 100] = 1페이지, 50페이지, 100페이지에서 동시 시작
    "start_pages": [1, 50, 100],
    
    # 워커당 다운로드할 파일 개수
    # 예: 10 = 각 워커가 10개씩 다운로드 (총 30개)
    "max_posts_per_worker": 10,
    
    # 다운로드 폴더 이름
    "download_dir": "parallel_reports",
    
    # 워커 간 시작 시간 간격 (초)
    "worker_start_delay": 15,
    
    # 페이지 이동 시 대기 시간 (초)
    "page_load_delay": 10,
    
    # 다운로드 후 대기 시간 (초)
    "download_delay": 5,
}

# 고급 설정 (변경하지 마세요)
ADVANCED_CONFIG = {
    # Chrome 옵션
    "chrome_options": {
        "disable_images": True,
        "disable_javascript": True,
        "disable_gpu": True,
    },
    
    # 재시도 설정
    "retry_config": {
        "max_retries": 3,
        "retry_delay": 10,
    },
    
    # 파일 대기 설정
    "file_wait_config": {
        "timeout": 45,
        "check_interval": 1,
    }
}

# ========================================
# 사용법 안내
# ========================================
"""
설정 변경 방법:

1. 다운로드 범위 변경:
   - start_pages 값을 변경
   - 예: [1, 100, 200] = 1, 100, 200페이지에서 시작

2. 다운로드 개수 변경:
   - max_posts_per_worker 값을 변경
   - 예: 20 = 워커당 20개씩 다운로드

3. 폴더명 변경:
   - download_dir 값을 변경
   - 예: "my_reports" = my_reports_worker_1, 2, 3 폴더 생성

주의사항:
- start_pages는 3개 이상 설정하지 마세요 (서버 부하)
- max_posts_per_worker는 50 이하로 설정하세요
- 설정 변경 후 parallel_downloader.py를 다시 실행하세요
""" 