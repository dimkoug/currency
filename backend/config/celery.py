import os
from celery import Celery
from celery.schedules import schedule

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("currency")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from django.conf import settings
    sender.add_periodic_task(
        schedule(run_every=settings.POLL_INTERVAL_SECONDS),
        fetch_rates_signature(),
        name="poll-forex-rates",
    )


def fetch_rates_signature():
    from rates.tasks import fetch_rates
    return fetch_rates.s()
