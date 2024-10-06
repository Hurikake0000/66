from django.apps import AppConfig

class WebscraperConfig(AppConfig):
    name = 'webscraper'

    def ready(self):
        from . import signals  # 상대 경로로 임포트
