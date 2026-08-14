import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "activationlab.settings")
app = Celery("activationlab")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
