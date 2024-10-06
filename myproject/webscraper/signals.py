import atexit
from django.db import connection
from webscraper.models import CrawledData

def clear_database_on_shutdown():
    print("Server is shutting down. Clearing the database...")
    try:
        CrawledData.objects.all().delete()
    except Exception as e:
        print(f"Error clearing the database: {e}")
    print("Database cleared.")

# 종료 시 실행될 함수 등록
atexit.register(clear_database_on_shutdown)
