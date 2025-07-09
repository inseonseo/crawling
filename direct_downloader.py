import requests
import os
import time
from multiprocessing import Process
from datetime import datetime, timedelta
import exchange_calendars as ecals
import pandas as pd
import signal
import sys

# 전역 변수로 현재 파일 번호 추적
current_file_number = None

def signal_handler(sig, frame):
    """Ctrl+C 인터럽트 처리"""
    global current_file_number
    print(f"\n\n=== 프로그램 중단됨 ===")
    print(f"현재 파일 번호: {current_file_number}")
    print(f"다음 파일 번호: {current_file_number + 1 if current_file_number else '알 수 없음'}")
    print("=" * 30)
    
    try:
        new_start = input("새로운 시작 파일 번호를 입력하세요 (엔터 시 종료): ").strip()
        if new_start:
            new_start_num = int(new_start)
            new_date = input("새로운 시작 날짜를 입력하세요 (YYYY-MM-DD 형식, 엔터 시 자동 계산): ").strip()
            
            print(f"\n설정을 업데이트하세요:")
            print(f"DOWNLOAD_CONFIG['file_ranges'] = [({new_start_num}, 2175)]")
            if new_date:
                print(f"DATE_MAPPING_CONFIG['start_file_number'] = {new_start_num}")
                print(f"DATE_MAPPING_CONFIG['start_date'] = '{new_date}'")
            else:
                print(f"DATE_MAPPING_CONFIG['start_file_number'] = {new_start_num}")
                print("DATE_MAPPING_CONFIG['start_date'] = 자동 계산됨")
            
            print("\n프로그램을 다시 실행하세요.")
        else:
            print("프로그램을 종료합니다.")
    except (ValueError, KeyboardInterrupt):
        print("프로그램을 종료합니다.")
    
    sys.exit(0)

# 시그널 핸들러 등록
signal.signal(signal.SIGINT, signal_handler)

# 설정
DOWNLOAD_CONFIG = {
    
    # 파일 번호 범위 - 워커1만 실행
    "file_ranges": [
        (2982, 3435),   # Worker 1: 914~2175 (1261개)
        # (2175, 3435),  # Worker 2: 2175~3435 (1260개) - 주석 처리
    ],
    
    # 다운로드 폴더
    "download_dir": "direct_reports",
    
    # 워커 간 시작 시간 간격 (초)
    "worker_start_delay": 5,
    
    # 다운로드 간격 (초)
    "download_delay": 1,
    
    # 재시도 설정
    "max_retries": 3,
    "retry_delay": 5,
}

# 날짜 매핑 설정 - 사용자가 쉽게 수정 가능
DATE_MAPPING_CONFIG = {
    "start_file_number": 2982,  # 시작 파일 번호 923, 930
    "start_date": "2023-09-05",  # 시작 날짜 (YYYY-MM-DD 형식)
    "end_file_number": 3435,  # 끝 파일 번호
    "end_date": "2025-07-08",  # 끝 날짜 (YYYY-MM-DD 형식)
}

def get_korean_business_days_with_exchange_calendar():
    """exchange_calendars를 사용하여 한국 영업일 가져오기"""
    try:
        # 한국 증시 캘린더 (XKRX)
        XKRX = ecals.get_calendar("XKRX")
        
        # 2015년부터 2025년까지 영업일 가져오기
        start_date = '2015-01-01'
        end_date = '2025-12-31'
        
        # 영업일 리스트 생성
        business_dates = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            if XKRX.is_session(date_str):
                business_dates.append(date_str)
            current_date += timedelta(days=1)
        
        print(f"한국 영업일 {len(business_dates)}개 생성 완료 (exchange_calendars 사용)")
        print(f"시작일: {business_dates[0]}, 종료일: {business_dates[-1]}")
        
        return business_dates
    except Exception as e:
        print(f"exchange_calendars 오류: {e}")
        print("수동 계산 방식으로 대체...")
        return get_korean_business_days_manual()

def get_korean_business_days_manual():
    """직접 계산으로 한국 영업일 생성"""
    from datetime import datetime, timedelta
    
    business_dates = []
    start_date = datetime(2015, 1, 1)
    end_date = datetime(2025, 12, 31)
    current_date = start_date
    
    # 한국 공휴일 (주요 공휴일만)
    korean_holidays = [
        "0101",  # 신정
        "0301",  # 삼일절
        "0505",  # 어린이날
        "0606",  # 현충일
        "0815",  # 광복절
        "1003",  # 개천절
        "1009",  # 한글날
        "1225",  # 크리스마스
    ]
    
    while current_date <= end_date:
        # 주말 제외
        if current_date.weekday() < 5:  # 월~금
            date_str = current_date.strftime('%Y%m%d')
            
            # 공휴일 제외 (간단한 체크)
            month_day = current_date.strftime('%m%d')
            if month_day not in korean_holidays:
                business_dates.append(date_str)
        
        current_date += timedelta(days=1)
    
    print(f"직접 계산: 한국 영업일 {len(business_dates)}개 생성 완료")
    print(f"시작일: {business_dates[0]}, 종료일: {business_dates[-1]}")
    
    return business_dates

def create_file_number_mapping():
    """파일 번호와 날짜 매핑 생성 - 정확한 날짜 정보 사용"""
    try:
        # 한국 증시 캘린더 (XKRX)
        XKRX = ecals.get_calendar("XKRX")
        
        # 설정에서 시작/끝 정보 가져오기
        start_file_num = DATE_MAPPING_CONFIG["start_file_number"]
        end_file_num = DATE_MAPPING_CONFIG["end_file_number"]
        start_date = DATE_MAPPING_CONFIG["start_date"]
        end_date = DATE_MAPPING_CONFIG["end_date"]
        
        # 시작일과 종료일 사이의 영업일 가져오기
        business_dates = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            if XKRX.is_session(date_str):
                business_dates.append(date_str)
            current_date += timedelta(days=1)
        
        print(f"영업일 {len(business_dates)}개 생성 완료")
        print(f"시작일: {business_dates[0]}, 종료일: {business_dates[-1]}")
        
        # 파일 번호와 날짜 매핑
        file_date_mapping = {}
        
        # 시작 파일 번호부터 순차적으로 매핑
        for i, date in enumerate(business_dates):
            file_number = start_file_num + i
            if file_number <= end_file_num:
                file_date_mapping[file_number] = date
        
        print(f"파일 번호 매핑 생성 완료: {len(file_date_mapping)}개")
        print(f"시작: 파일 {start_file_num} -> {business_dates[0]}")
        print(f"끝: 파일 {start_file_num + len(business_dates) - 1} -> {business_dates[-1]}")
        
        # 매핑 확인 (몇 개 샘플 출력)
        print("매핑 샘플:")
        sample_items = list(file_date_mapping.items())[:5]
        for file_num, date in sample_items:
            print(f"  파일 {file_num} -> {date}")
        
        # 끝부분도 확인
        end_items = list(file_date_mapping.items())[-5:]
        print("매핑 끝부분:")
        for file_num, date in end_items:
            print(f"  파일 {file_num} -> {date}")
        
        return file_date_mapping
        
    except Exception as e:
        print(f"매핑 생성 오류: {e}")
        print("수동 계산 방식으로 대체...")
        return create_file_number_mapping_manual()

def create_file_number_mapping_manual():
    """수동 계산으로 매핑 생성"""
    # 2015/7/1부터 2025/7/8까지의 영업일을 수동으로 계산
    # 실제로는 더 복잡하지만 간단한 버전으로 구현
    
    business_dates = []
    start_date = datetime(2015, 7, 1)
    end_date = datetime(2025, 7, 8)
    current_date = start_date
    
    # 한국 공휴일 (주요 공휴일만)
    korean_holidays = [
        "0101",  # 신정
        "0301",  # 삼일절
        "0505",  # 어린이날
        "0606",  # 현충일
        "0815",  # 광복절
        "1003",  # 개천절
        "1009",  # 한글날
        "1225",  # 크리스마스
    ]
    
    while current_date <= end_date:
        # 주말 제외
        if current_date.weekday() < 5:  # 월~금
            date_str = current_date.strftime('%Y-%m-%d')
            
            # 공휴일 제외 (간단한 체크)
            month_day = current_date.strftime('%m%d')
            if month_day not in korean_holidays:
                business_dates.append(date_str)
        
        current_date += timedelta(days=1)
    
    # 파일 번호와 날짜 매핑
    file_date_mapping = {}
    start_file_num = 914
    end_file_num = 3435
    
    for i, date in enumerate(business_dates):
        file_number = start_file_num + i
        if file_number <= end_file_num:
            file_date_mapping[file_number] = date
    
    print(f"수동 계산: 파일 번호 매핑 {len(file_date_mapping)}개 생성 완료")
    return file_date_mapping

def verify_file_numbers():
    """실제 파일 존재 여부로 매핑 확인"""
    # 914, 915, 916... 순서대로 실제 다운로드 시도
    # 404 에러가 나오는 지점을 찾아서 실제 범위 확인
    pass # Placeholder for actual verification logic

def download_pdf_by_number(file_number, download_dir, worker_id, file_date_mapping=None, successful_downloads=None):
    """파일 번호로 PDF 직접 다운로드"""
    global current_file_number
    current_file_number = file_number
    
    url = f"https://ksureapi.einfomax.co.kr/v2/datafeed/ksure/fxfiledown/{file_number}"
    
    # 파일명 결정 (다운로드 성공 후에 날짜 매핑 적용)
    filename = f"{file_number}.pdf"
    filepath = os.path.join(download_dir, filename)
    
    # 이미 존재하면 스킵 (파일 번호로 체크)
    if os.path.exists(filepath):
        return True
    
    # 날짜로 저장된 파일도 체크
    if file_date_mapping and file_number in file_date_mapping:
        date_str = file_date_mapping[file_number]
        date_filename = f"{date_str}.pdf"
        date_filepath = os.path.join(download_dir, date_filename)
        if os.path.exists(date_filepath):
            return True
    
    for attempt in range(DOWNLOAD_CONFIG["max_retries"]):
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # PDF 파일 검증 (PDF 시그니처 확인)
                content = response.content
                if len(content) > 4 and content[:4] == b'%PDF':
                    # 실제 PDF 파일인 경우
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    
                    # 다운로드 성공 시 날짜 매핑 적용
                    if file_date_mapping and file_number in file_date_mapping:
                        date_str = file_date_mapping[file_number]
                        new_filename = f"{date_str}.pdf"
                        new_filepath = os.path.join(download_dir, new_filename)
                        
                        # 중복 방지
                        counter = 1
                        while os.path.exists(new_filepath):
                            name, ext = os.path.splitext(new_filename)
                            new_filepath = os.path.join(download_dir, f"{name}_{counter}{ext}")
                            counter += 1
                        
                        # 파일명 변경
                        os.rename(filepath, new_filepath)
                        
                        # 성공한 다운로드 기록
                        if successful_downloads is not None:
                            successful_downloads.append(file_number)
                    
                    return True
                else:
                    # PDF가 아닌 경우 (에러 페이지 등) - 404로 처리
                    with open(filepath, 'wb') as f:
                        f.write(b'')  # 빈 파일 생성
                    return False
            elif response.status_code == 404:
                # 404 에러 시 파일 번호로 저장 (빈 파일 생성) - 날짜 매핑 적용 안함
                with open(filepath, 'wb') as f:
                    f.write(b'')  # 빈 파일 생성
                return False
            else:
                print(f"Worker {worker_id}: {file_number} download failed (status: {response.status_code})")
                
        except Exception as e:
            print(f"Worker {worker_id}: {file_number} download error - {e}")
        
        if attempt < DOWNLOAD_CONFIG["max_retries"] - 1:
            time.sleep(DOWNLOAD_CONFIG["retry_delay"])
    
    return False

def worker_process(start_num, end_num, download_dir, worker_id, file_date_mapping=None):
    """워커 프로세스"""
    # 자식 프로세스에서도 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    
    # 전체 진행도 계산을 위한 고정 범위 (1000 ~ 3435)
    overall_start = 1000
    overall_end = 3435
    total_files = overall_end - overall_start  # 2435개
    
    # 시작 시 진행도 표시
    overall_progress = ((start_num - overall_start) / total_files) * 100
    print(f"Worker {worker_id}: Starting download range {start_num}~{end_num}")
    print(f"Worker {worker_id}: Overall Progress {overall_progress:.1f}% ({start_num}/{overall_end})")
    
    # 다운로드 폴더 생성
    worker_dir = f"{download_dir}_worker_{worker_id}"
    if not os.path.exists(worker_dir):
        os.makedirs(worker_dir)
    
    total_downloaded = 0
    successful_downloads = []  # 성공한 다운로드 기록
    
    try:
        for file_number in range(start_num, end_num):
            if download_pdf_by_number(file_number, worker_dir, worker_id, file_date_mapping, successful_downloads):
                total_downloaded += 1
            
            # 진행상황 표시 (100개마다) - 전체 진행도 기준
            if file_number % 100 == 0:
                # 전체 진행도: 현재 파일 번호가 전체 범위에서 어느 정도인지
                overall_progress = ((file_number - overall_start) / total_files) * 100
                print(f"Worker {worker_id}: Overall Progress {overall_progress:.1f}% ({file_number}/{overall_end})")
            
            time.sleep(DOWNLOAD_CONFIG["download_delay"])
        
        print(f"Worker {worker_id}: Completed! {total_downloaded} files downloaded")
        print(f"Worker {worker_id}: Successful downloads: {len(successful_downloads)}")
        print(f"Worker {worker_id}: Saved to: {os.path.abspath(worker_dir)}")
        
    except KeyboardInterrupt:
        print(f"\nWorker {worker_id}: Interrupted at file {current_file_number}")
        sys.exit(0)

def run_parallel_download():
    """단일 프로세스 다운로드 실행"""
    print("=== Direct PDF Download Started ===")
    print(f"Download ranges: {DOWNLOAD_CONFIG['file_ranges']}")
    
    # 파일 번호와 날짜 매핑 생성
    print("Creating Korean business days mapping...")
    file_date_mapping = create_file_number_mapping()
    
    if file_date_mapping:
        print("Date mapping successful - files will be saved with date names")
    else:
        print("Date mapping failed - files will be saved with file numbers")
    
    # 단일 프로세스로 실행 (Ctrl+C가 바로 작동)
    for i, (start_num, end_num) in enumerate(DOWNLOAD_CONFIG["file_ranges"]):
        worker_id = i + 1
        print(f"Worker {worker_id} started (range: {start_num}~{end_num})")
        
        # 직접 실행 (프로세스 생성 안함)
        worker_process(start_num, end_num, DOWNLOAD_CONFIG["download_dir"], worker_id, file_date_mapping)
        
        # 워커 간 시작 시간 분산
        time.sleep(DOWNLOAD_CONFIG["worker_start_delay"])
    
    print("=== All Downloads Completed ===")

if __name__ == "__main__":
    run_parallel_download() 