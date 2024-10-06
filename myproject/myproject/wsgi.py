import os
import sys
import atexit
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = get_wsgi_application()

def handle_exit():
    print("Signal received, shutting down...")
    from webscraper.signals import clear_database_on_shutdown
    clear_database_on_shutdown()

# 종료 시 실행될 함수 등록
atexit.register(handle_exit)