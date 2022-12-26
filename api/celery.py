from celery import Celery
from configurations import importer


# Initialize Django Configurations and Django
from django.conf import settings

importer.install()

# Setup Celery
app = Celery('celery_app')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.task_ignore_result = True
app.conf.task_store_errors_even_if_ignored = True
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
