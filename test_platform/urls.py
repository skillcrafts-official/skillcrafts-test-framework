from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('run-tests/', views.run_tests, name='run_tests'),
    path('check-run-status/<uuid:run_id>/', views.check_run_status, name='check_run_status'),
    path('download-csv/<uuid:run_id>/', views.download_csv, name='download_csv'),
    path('get-history/', views.get_history, name='get_history'),
    path('wiki/', views.wiki_page, name='wiki_index'),
    path('wiki/media/<path:file_path>/', views.wiki_media, name='wiki_media'),
    path('wiki/<path:page_path>/', views.wiki_page, name='wiki_page'),
]
