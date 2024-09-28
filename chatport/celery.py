import os
from django.conf import settings
import django
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatport.settings")

# Create Celery app with the new project name
app = Celery('chatport.celery', broker='amqp://guest:guest@localhost:5672')

# Configure Django settings
django.setup()

# Access Django settings
installed_apps = settings.INSTALLED_APPS
debug_mode = settings.DEBUG
database_settings = settings.DATABASES

# Configure Celery app with Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover Celery tasks
app.autodiscover_tasks()

# Additional Celery configuration
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


app.conf.update(
    worker_log_level='INFO',
)


