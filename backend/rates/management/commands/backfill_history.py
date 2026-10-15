from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from rates.fetcher import fetch_rate_series
from rates.services import backfill_history


class Command(BaseCommand):
    help = "Backfill daily ECB rates from the forex API for days before polling began."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=90)

    def handle(self, *args, days, **options):
        end = timezone.now().date()
        series = fetch_rate_series(
            base=settings.BASE_CURRENCY,
            symbols=settings.SUPPORTED_CURRENCIES,
            start=end - timedelta(days=days),
            end=end,
            api_base_url=settings.FOREX_API_BASE_URL,
        )
        created = backfill_history(settings.BASE_CURRENCY, series)
        self.stdout.write(f"Fetched {len(series)} days; stored {created} rate changes.")
