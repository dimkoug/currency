from celery import shared_task
from django.conf import settings
from rates.fetcher import fetch_latest_rates
from rates.services import save_snapshot, broadcast_latest


@shared_task
def fetch_rates():
    """Poll the forex API, persist a snapshot, and broadcast the latest rates."""
    snapshot = fetch_latest_rates(
        base=settings.BASE_CURRENCY,
        symbols=settings.SUPPORTED_CURRENCIES,
        api_base_url=settings.FOREX_API_BASE_URL,
    )
    save_snapshot(snapshot)
    broadcast_latest()
