import time
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime
from multiprocessing import Process, Queue
import multiprocessing

# 설정 파일 불러오기
try:
    from config import DOWNLOAD_CONFIG, ADVANCED_CONFIG
except ImportError:
    # 설정 파일이 없으면 기본값 사용
    DOWNLOAD_CONFIG = {
        "start_pages": [1, 50, 100],
        "max_posts_per_worker": 10,
        "download_dir": "parallel_reports",
        "worker_start_delay": 15,
        "page_load_delay": 10,
        "download_delay": 5,
    }
    ADVANCED_CONFIG = {
        "chrome_options": {
            "disable_images": True,
            "disable_javascript": True,
            "disable_gpu": True,
        },
        "retry_config": {
            "max_retries": 3,
            "retry_delay": 10,
        },
        "file_wait_config": {
            "timeout": 45,
            "check_interval": 1,
        }
    }

class WorkerProcess:
    def __init__(self, start_page, download_dir, worker_id, max_posts=10):
        self.start_page = start_page
        self.download_dir = f"{download_dir}_worker_{worker_id}"
        self.worker_id = worker_id
        self.max_posts = max_posts
        self.driver = None
        
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
    
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("prefs", {
                "download.default_directory": os.path.abspath(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "profile.default_content_setting_values.automatic_downloads": 1,
                "download.open_pdf_in_system_reader": False,
                "plugins.always_open_pdf_externally": True
            })
            
            # 각 워커별로 다른 포트 사용 (충돌 방지)
            chrome_options.add_argument(f"--remote-debugging-port={9222 + self.worker_id}")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            print(f"워커 {self.worker_id}: Chrome 드라이버 설정 완료 (포트: {9222 + self.worker_id})")
            return True
        except Exception as e:
            print(f"워커 {self.worker_id}: 드라이버 설정 실패: {e}")
            return False
    
    def open_page(self):
        """페이지 열기"""
        max_retries = ADVANCED_CONFIG["retry_config"]["max_retries"]
        for attempt in range(max_retries):
            try:
                print(f"워커 {self.worker_id}: 페이지 열기 시도 {attempt + 1}/{max_retries}")
                self.driver.get("https://ksure.or.kr/rh-fx/cntnts/i-505/web.do")
                print(f"워커 {self.worker_id}: 페이지 열기 완료")
                time.sleep(DOWNLOAD_CONFIG["download_delay"])
                return True
            except Exception as e:
                print(f"워커 {self.worker_id}: 페이지 열기 실패 (시도 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(ADVANCED_CONFIG["retry_config"]["retry_delay"])
                else:
                    print(f"워커 {self.worker_id}: 페이지 열기 최종 실패")
                    return False
    
    def navigate_to_page(self, target_page):
        """특정 페이지로 이동"""
        try:
            time.sleep(DOWNLOAD_CONFIG["page_load_delay"])
            
            self.driver.switch_to.default_content()
            
            iframe = None
            try:
                iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe[src*='fxreportlist']")
            except:
                try:
                    iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe")
                except:
                    print(f"워커 {self.worker_id}: iframe을 찾을 수 없습니다.")
                    return False
            
            if iframe:
                self.driver.switch_to.frame(iframe)
                time.sleep(3)
            else:
                print(f"워커 {self.worker_id}: iframe이 없습니다.")
                return False
            
            click_count = target_page // 10
            
            print(f"워커 {self.worker_id}: {click_count}번 다음 버튼 클릭 시작 (목표: {target_page}페이지)")
            
            for i in range(click_count):
                try:
                    next_btn = self.driver.find_element(By.CSS_SELECTOR, "a.next")
                    self.driver.execute_script("arguments[0].click();", next_btn)
                    print(f"워커 {self.worker_id}: {i+1}/{click_count}번째 다음 버튼 클릭")
                    time.sleep(3)
                except Exception as e:
                    print(f"워커 {self.worker_id}: {i+1}번째 다음 버튼 클릭 실패: {e}")
                    break
            
            print(f"워커 {self.worker_id}: 목표 페이지 {target_page} 도달")
            return True
            
        except Exception as e:
            print(f"워커 {self.worker_id}: 페이지 이동 중 오류: {e}")
            return False
    
    def click_first_post(self):
        """첫 번째 게시글 클릭"""
        try:
            self.driver.switch_to.default_content()
            iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe[src*='fxreportlist']")
            self.driver.switch_to.frame(iframe)
            time.sleep(1)
            
            links = self.driver.find_elements(By.TAG_NAME, "a")
            if links:
                first_link = links[0]
                print(f"워커 {self.worker_id}: 첫 번째 게시글 클릭: {first_link.text}")
                self.driver.execute_script("arguments[0].click();", first_link)
                time.sleep(3)
                return True
            return False
        except Exception as e:
            print(f"워커 {self.worker_id}: 첫 번째 게시글 클릭 실패: {e}")
            return False
    
    def extract_date(self):
        """날짜 추출 (iframe 안에서)"""
        try:
            self.driver.switch_to.default_content()
            iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe[src*='fxreportlist']")
            self.driver.switch_to.frame(iframe)
            time.sleep(1)
            
            date = self.driver.find_element(By.CSS_SELECTOR, "span.date")
            date_text = date.text.strip()
            print(f"워커 {self.worker_id}: 상세페이지 날짜: {date_text}")
            return date_text
        except Exception as e:
            print(f"워커 {self.worker_id}: 날짜 추출 실패: {e}")
            return None
    
    def click_pdf_download(self):
        """PDF 다운로드 (default_content에서)"""
        try:
            self.driver.switch_to.default_content()
            pdf_btn = self.driver.find_element(By.CSS_SELECTOR, ".share_wrap .btn_pdf_download")
            print(f"워커 {self.worker_id}: PDF 다운로드 버튼 클릭 중...")
            self.driver.execute_script("arguments[0].click();", pdf_btn)
            time.sleep(5)
            print(f"워커 {self.worker_id}: PDF 다운로드 버튼 클릭 완료")
            return True
        except Exception as e:
            print(f"워커 {self.worker_id}: PDF 다운로드 실패: {e}")
            return False
    
    def rename_downloaded_file(self, new_filename):
        """다운로드된 파일 이름 변경"""
        try:
            old_path = os.path.join(self.download_dir, "일일환율전망.pdf")
            new_path = os.path.join(self.download_dir, new_filename)
            print(f"워커 {self.worker_id}: 변경 대상 파일: {old_path}, 변경할 이름: {new_filename}")
            
            timeout = ADVANCED_CONFIG["file_wait_config"]["timeout"]
            check_interval = ADVANCED_CONFIG["file_wait_config"]["check_interval"]
            waited = 0
            while not os.path.exists(old_path) and waited < timeout:
                time.sleep(check_interval)
                waited += 1
                print(f"워커 {self.worker_id}: 파일 대기 중... ({waited}/{timeout})")
            
            if not os.path.exists(old_path):
                print(f"워커 {self.worker_id}: 파일을 찾을 수 없습니다: {old_path}")
                return False
            
            counter = 1
            while os.path.exists(new_path):
                name, ext = os.path.splitext(new_filename)
                new_path = os.path.join(self.download_dir, f"{name}_{counter}{ext}")
                counter += 1
            
            os.rename(old_path, new_path)
            print(f"워커 {self.worker_id}: 파일 다운로드 완료: {new_path}")
            return True
        except Exception as e:
            print(f"워커 {self.worker_id}: 파일 이름 변경 실패: {e}")
            return False
    
    def click_prev_post(self):
        """이전글 제목 클릭 (iframe 안에서)"""
        try:
            self.driver.switch_to.default_content()
            iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe[src*='fxreportlist']")
            self.driver.switch_to.frame(iframe)
            time.sleep(2)
            
            prev_link = self.driver.find_element(By.CSS_SELECTOR, "div.view_nav li.prev dd.subject a")
            print(f"워커 {self.worker_id}: 이전글 제목 클릭: {prev_link.text}")
            self.driver.execute_script("arguments[0].click();", prev_link)
            time.sleep(3)
            print(f"워커 {self.worker_id}: 이전글 제목 클릭 완료")
            return True
        except Exception as e:
            print(f"워커 {self.worker_id}: 이전글 제목 클릭 실패: {e}")
            return False
    
    def run(self):
        """워커 실행"""
        print(f"워커 {self.worker_id}: === {self.start_page}페이지부터 시작 ===")
        
        if not self.setup_driver():
            return
        
        try:
            # 1. 페이지 열기
            if not self.open_page():
                return
            
            # 2. 목표 페이지로 이동
            if not self.navigate_to_page(self.start_page):
                return
            
            # 3. 첫 번째 게시글 클릭
            if not self.click_first_post():
                return
            
            # 4. 반복 처리
            total_downloaded = 0
            for i in range(self.max_posts):
                print(f"워커 {self.worker_id}: === {i+1}번째 게시글 처리 중 ===")
                
                # 4-1. 날짜 추출
                date_text = self.extract_date()
                if date_text:
                    date_match = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_text)
                    if date_match:
                        date_str = f"{date_match.group(1)}{date_match.group(2)}{date_match.group(3)}"
                        filename = f"{date_str}.pdf"
                        print(f"워커 {self.worker_id}: 생성된 파일명: {filename}")
                    else:
                        filename = f"{datetime.now().strftime('%Y%m%d')}.pdf"
                else:
                    filename = f"{datetime.now().strftime('%Y%m%d')}.pdf"
                
                # 4-2. PDF 다운로드
                if not self.click_pdf_download():
                    print(f"워커 {self.worker_id}: PDF 다운로드 실패. 다음 게시글로.")
                    continue
                
                # 4-3. 파일명 변경
                if self.rename_downloaded_file(filename):
                    total_downloaded += 1
                    print(f"워커 {self.worker_id}: 파일명 변경 성공!")
                else:
                    print(f"워커 {self.worker_id}: 파일명 변경 실패했지만 계속 진행")
                
                # 4-4. 이전글 제목 클릭
                if not self.click_prev_post():
                    print(f"워커 {self.worker_id}: 이전글이 없거나 클릭 실패. 종료.")
                    break
                
                time.sleep(2)
            
            print(f"워커 {self.worker_id}: === 다운로드 완료 ===")
            print(f"워커 {self.worker_id}: 총 {total_downloaded}개의 파일을 다운로드했습니다.")
            print(f"워커 {self.worker_id}: 다운로드 위치: {os.path.abspath(self.download_dir)}")
            
        except Exception as e:
            print(f"워커 {self.worker_id}: 실행 중 오류 발생: {e}")
        finally:
            if self.driver:
                self.driver.quit()

def worker_function(start_page, download_dir, worker_id, max_posts=10):
    """워커 프로세스 함수"""
    worker = WorkerProcess(start_page, download_dir, worker_id, max_posts)
    worker.run()

class ParallelDownloader:
    def __init__(self, download_dir="parallel_reports", max_posts_per_worker=10):
        self.download_dir = download_dir
        self.max_posts_per_worker = max_posts_per_worker
        
    def run_parallel(self, start_pages=[1, 50, 100]):
        """병렬 다운로드 실행"""
        print("=== 병렬 다운로드 시작 ===")
        print(f"시작 페이지: {start_pages}")
        print(f"워커당 다운로드 수: {self.max_posts_per_worker}")
        
        processes = []
        
        # 각 워커 프로세스 시작
        for i, start_page in enumerate(start_pages):
            worker_id = i + 1
            print(f"워커 {worker_id} 시작 (시작 페이지: {start_page})")
            
            process = Process(
                target=worker_function,
                args=(start_page, self.download_dir, worker_id, self.max_posts_per_worker)
            )
            process.start()
            processes.append(process)
            
            # 워커 간 시작 시간 분산 (브라우저 로딩 부하 분산)
            time.sleep(DOWNLOAD_CONFIG["worker_start_delay"])
        
        # 모든 프로세스 완료 대기
        for i, process in enumerate(processes):
            process.join()
            print(f"워커 {i+1} 완료")
        
        print("=== 모든 병렬 다운로드 완료 ===")

if __name__ == "__main__":
    # 멀티프로세싱 설정
    multiprocessing.set_start_method('spawn')
    
    # 설정에서 값 가져오기
    start_pages = DOWNLOAD_CONFIG["start_pages"]
    max_posts_per_worker = DOWNLOAD_CONFIG["max_posts_per_worker"]
    download_dir = DOWNLOAD_CONFIG["download_dir"]
    
    # 병렬 다운로더 실행
    downloader = ParallelDownloader(download_dir=download_dir, max_posts_per_worker=max_posts_per_worker)
    downloader.run_parallel(start_pages=start_pages) 