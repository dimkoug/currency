import os
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("currency")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Register the periodic forex poll directly on the beat schedule. Referencing the
# task by name avoids importing rates.tasks at module load (circular import), and
# setting beat_schedule explicitly is more reliable than the on_after_configure signal.
app.conf.beat_schedule = {
    "poll-forex-rates": {
        "task": "rates.tasks.fetch_rates",
        "schedule": float(settings.POLL_INTERVAL_SECONDS),
    }
}
