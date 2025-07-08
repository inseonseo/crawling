import requests
import os
import time
from multiprocessing import Process
from datetime import datetime
import pandas_market_calendars as mcal

# 설정
DOWNLOAD_CONFIG = {
    # 파일 번호 범위 (Worker별) - 2개로 분할
    "file_ranges": [
        (914, 2175),   # Worker 1: 914~2175 (1261개)
        (2175, 3435),  # Worker 2: 2175~3435 (1260개)
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

def get_korean_business_days():
    """한국 영업일 가져오기"""
    try:
        # 한국 증시 캘린더 (XKRX)
        krx = mcal.get_calendar('XKRX')
        
        # 10년치 영업일 (2015-01-01 ~ 2025-12-31)
        business_days = krx.schedule(start_date='2015-01-01', end_date='2025-12-31')
        
        # 날짜만 추출하여 리스트로 변환
        business_dates = [date.strftime('%Y%m%d') for date in business_days.index]
        
        print(f"한국 영업일 {len(business_dates)}개 생성 완료")
        print(f"시작일: {business_dates[0]}, 종료일: {business_dates[-1]}")
        
        return business_dates
    except Exception as e:
        print(f"영업일 생성 오류: {e}")
        print("직접 계산 방식으로 대체...")
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
    """파일 번호와 날짜 매핑 생성"""
    business_dates = get_korean_business_days()
    if not business_dates:
        return None
    
    # 역순으로 정렬 (최신이 큰 번호)
    business_dates.reverse()
    
    # 파일 번호와 날짜 매핑
    file_date_mapping = {}
    for i, date in enumerate(business_dates):
        file_number = 3435 - i  # 3435부터 역순으로
        file_date_mapping[file_number] = date
    
    print(f"파일 번호 매핑 생성 완료: {len(file_date_mapping)}개")
    return file_date_mapping

def download_pdf_by_number(file_number, download_dir, worker_id, file_date_mapping=None):
    """파일 번호로 PDF 직접 다운로드"""
    url = f"https://ksureapi.einfomax.co.kr/v2/datafeed/ksure/fxfiledown/{file_number}"
    
    # 날짜 매핑이 있으면 날짜로 파일명 생성
    if file_date_mapping and file_number in file_date_mapping:
        date_str = file_date_mapping[file_number]
        filename = f"{date_str}.pdf"
    else:
        filename = f"{file_number}.pdf"
    
    filepath = os.path.join(download_dir, filename)
    
    # 이미 존재하면 스킵
    if os.path.exists(filepath):
        print(f"워커 {worker_id}: {filename} 이미 존재 - 스킵")
        return True
    
    for attempt in range(DOWNLOAD_CONFIG["max_retries"]):
        try:
            print(f"워커 {worker_id}: {file_number} 다운로드 시도 {attempt + 1}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"워커 {worker_id}: {filename} 다운로드 완료")
                return True
            elif response.status_code == 404:
                print(f"워커 {worker_id}: {file_number} 파일 없음 (404)")
                return False
            else:
                print(f"워커 {worker_id}: {file_number} 다운로드 실패 (상태코드: {response.status_code})")
                
        except Exception as e:
            print(f"워커 {worker_id}: {file_number} 다운로드 오류 - {e}")
        
        if attempt < DOWNLOAD_CONFIG["max_retries"] - 1:
            time.sleep(DOWNLOAD_CONFIG["retry_delay"])
    
    return False

def worker_process(start_num, end_num, download_dir, worker_id, file_date_mapping=None):
    """워커 프로세스"""
    print(f"워커 {worker_id}: {start_num}~{end_num} 범위 다운로드 시작")
    
    # 다운로드 폴더 생성
    worker_dir = f"{download_dir}_worker_{worker_id}"
    if not os.path.exists(worker_dir):
        os.makedirs(worker_dir)
    
    total_downloaded = 0
    total_files = end_num - start_num
    
    for file_number in range(start_num, end_num):
        if download_pdf_by_number(file_number, worker_dir, worker_id, file_date_mapping):
            total_downloaded += 1
        
        # 진행상황 표시
        if file_number % 50 == 0:
            progress = ((file_number - start_num) / total_files) * 100
            print(f"워커 {worker_id}: 진행률 {progress:.1f}% ({file_number}/{end_num})")
        
        time.sleep(DOWNLOAD_CONFIG["download_delay"])
    
    print(f"워커 {worker_id}: 완료! {total_downloaded}개 다운로드")
    print(f"워커 {worker_id}: 저장 위치: {os.path.abspath(worker_dir)}")

def run_parallel_download():
    """병렬 다운로드 실행"""
    print("=== 직접 PDF 다운로드 시작 ===")
    print(f"다운로드 범위: {DOWNLOAD_CONFIG['file_ranges']}")
    
    # 파일 번호와 날짜 매핑 생성
    print("한국 영업일 정보 생성 중...")
    file_date_mapping = create_file_number_mapping()
    
    if file_date_mapping:
        print("날짜 매핑 성공 - 날짜별 파일명으로 저장")
    else:
        print("날짜 매핑 실패 - 파일 번호로 저장")
    
    processes = []
    
    # 각 워커 프로세스 시작
    for i, (start_num, end_num) in enumerate(DOWNLOAD_CONFIG["file_ranges"]):
        worker_id = i + 1
        print(f"워커 {worker_id} 시작 (범위: {start_num}~{end_num})")
        
        process = Process(
            target=worker_process,
            args=(start_num, end_num, DOWNLOAD_CONFIG["download_dir"], worker_id, file_date_mapping)
        )
        process.start()
        processes.append(process)
        
        # 워커 간 시작 시간 분산
        time.sleep(DOWNLOAD_CONFIG["worker_start_delay"])
    
    # 모든 프로세스 완료 대기
    for i, process in enumerate(processes):
        process.join()
        print(f"워커 {i+1} 완료")
    
    print("=== 모든 다운로드 완료 ===")

if __name__ == "__main__":
    run_parallel_download() 