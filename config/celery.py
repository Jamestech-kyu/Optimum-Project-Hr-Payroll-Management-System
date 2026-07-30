import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

# Explicitly import tasks stored outside conventional app autodiscovery.
app.conf.imports = (
    "config.tasks",
    "payroll.tasks",
)
