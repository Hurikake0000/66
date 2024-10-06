import os
import sys
import time
import logging
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import django
import re

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 환경 변수 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Django 설정 초기화
django.setup()

from webscraper.models import CrawledData  # 수정된 부분: 초기화 후 모델 가져오기

# 로그 설정
logger = logging.getLogger(__name__)

# 크롤링 상태 전역 변수
crawling_active = False


def search_with_selenium(url, keyword):
    logger.info(f"Starting Selenium search on {url} with keyword {keyword}")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
    except Exception as e:
        logger.error(f"Error opening URL with Selenium: {e}")
        driver.quit()
        return []

    keyword_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
    results = [element.text.strip() for element in keyword_elements if element.text.strip()]
    driver.quit()
    logger.info(f"Selenium search results: {results}")
    return results

def search_with_bs4(url, keyword):
    logger.info(f"Starting BeautifulSoup search on {url} with keyword {keyword}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    elements_with_keyword = soup.find_all(string=lambda text: keyword in text)
    results = [element.strip() for element in elements_with_keyword if element.find_parent().name != 'script']
    logger.info(f"BeautifulSoup search results: {results}")
    return results

def detect_new_data(url, keyword, initial=False):
    logger.info(f"Detecting new data for {url} with keyword {keyword}")
    selenium_results = search_with_selenium(url, keyword)
    bs4_results = search_with_bs4(url, keyword)
    unique_results = set(selenium_results + bs4_results)
    
    new_data_found = False

    for result in unique_results:
        if not CrawledData.objects.filter(data=result).exists() and result:
            if not initial:
                CrawledData.objects.create(url=url, keyword=keyword, data=result)
                new_data_found = True
                logger.info(f"New data found and saved: {result}")

    return new_data_found

def start_crawling_task(url, keyword):
    global crawling_active
    crawling_active = True
    logger.info(f"Starting crawling task for {url} with keyword {keyword}")
    detect_new_data(url, keyword, initial=True)

    while crawling_active:
        time.sleep(10)
        new_data_found = detect_new_data(url, keyword)
        
        if new_data_found:
            send_new_data_notification("새로운 정보가 감지되었습니다!")

def stop_crawling_task():
    global crawling_active
    crawling_active = False
    logger.info("Crawling task stopped")

def send_new_data_notification(message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'notifications',
        {
            'type': 'send_notification',
            'message': message,
        }
    )
    logger.info(f"Notification sent: {message}")

