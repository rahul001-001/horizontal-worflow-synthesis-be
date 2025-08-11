from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
import pandas

# Set default Django settings module for 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

import logging

# Configure Celery task logger
logger = logging.getLogger("celery")
file_handler = logging.FileHandler("celery_tasks.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
file_handler.setFormatter(formatter)

logger.setLevel(logging.INFO)
logger.addHandler(file_handler)