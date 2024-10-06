from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('start_crawling/', views.start_crawling_view, name='start_crawling'),
    path('stop_crawling/', views.stop_crawling_view, name='stop_crawling'),
    path('notifications/', views.notifications, name='notifications'),
    path('clear_database/', views.clear_database_view, name='clear_database'),
    path('check_updates/', views.check_updates, name='check_updates'),
    path('recommend_keywords/', views.recommend_keywords, name='recommend_keywords'),
    path('toggle_data/', views.toggle_data_view, name='toggle_data'),
    path('get_crawled_data/', views.get_crawled_data, name='get_crawled_data'),
]