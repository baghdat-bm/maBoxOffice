from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Устанавливаем переменную окружения Django для правильной загрузки настроек
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')

app = Celery('webapp')

# Загружаем конфигурацию из настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Указываем Redis как брокер задач
app.conf.broker_url = settings.CELERY_BROKER_URL

# Автоматически обнаруживаем задачи в приложениях Django
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
