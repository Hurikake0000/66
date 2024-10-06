import time
import logging
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from .models import CrawledData
from selenium.webdriver.common.by import By
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

crawling_active = False

def search_with_selenium(url, keyword):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    keyword_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
    results = [element.text.strip() for element in keyword_elements if element.text.strip()]
    driver.quit()
    return results

def search_with_bs4(url, keyword):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    elements_with_keyword = soup.find_all(string=lambda text: keyword in text)
    results = [element.strip() for element in elements_with_keyword if element.find_parent().name != 'script']
    return results

def detect_new_data(url, keyword, initial=False):
    selenium_results = search_with_selenium(url, keyword)
    bs4_results = search_with_bs4(url, keyword)
    unique_results = set(selenium_results + bs4_results)
    
    new_data_found = False

    for result in unique_results:
        if not CrawledData.objects.filter(data=result).exists():
            CrawledData.objects.create(url=url, keyword=keyword, data=result, is_new=not initial)
            if not initial:
                new_data_found = True

    return new_data_found

def start_crawling(url, keyword):
    global crawling_active
    crawling_active = True
    detect_new_data(url, keyword, initial=True)  # 초기 크롤링

    while crawling_active:
        time.sleep(30)
        detect_new_data(url, keyword)  # 이후 크롤링에서는 initial=False가 기본값

def stop_crawling_task():
    global crawling_active
    crawling_active = False

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