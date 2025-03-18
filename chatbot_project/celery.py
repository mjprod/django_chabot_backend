# chatbot_project/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab, timedelta

from dotenv import load_dotenv

load_dotenv()

environment = os.getenv("DJANGO_ENV", "local")


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'chatbot_project.settings.{environment}')

app = Celery('chatbot_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related config keys should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'streaming-daily-conversations': {
        'task': 'api.tasks.streaming_conversations_to_sap',
        'schedule': crontab(minute=0, hour=2),  # Runs at 2 AM UTC
    },
}

# 
# # Start Celery worker
# celery -A chatbot_project worker --loglevel=info -n worker@%h

# # Start Celery Beat
# celery -A chatbot_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler