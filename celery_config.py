import os
from celery_config import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CFIT.settings')
app = Celery('CFIT')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()