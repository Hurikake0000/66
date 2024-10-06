from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('webscraper.urls')),  # 실제 앱의 URL 파일을 포함합니다.
]