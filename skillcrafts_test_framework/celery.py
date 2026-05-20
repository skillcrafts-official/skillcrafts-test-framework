import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillcrafts_test_framework.settings')

app = Celery('skillcrafts_test_framework')

# Загружаем настройки из settings.py с префиксом CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи в приложениях (tasks.py)
app.autodiscover_tasks()
