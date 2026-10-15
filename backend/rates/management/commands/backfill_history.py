from datetime import date, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from rates.fetcher import fetch_rate_series
from rates.services import backfill_history

# First day of ECB reference rates (and of Frankfurter's data).
ECB_FIRST_DAY = "1999-01-04"


def yearly_ranges(start, end):
    """Split [start, end] into calendar-year chunks to keep responses small."""
    while start <= end:
        chunk_end = min(date(start.year, 12, 31), end)
        yield start, chunk_end
        start = chunk_end + timedelta(days=1)


class Command(BaseCommand):
    help = "Backfill daily ECB rates from the forex API for days before polling began."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--days", type=int, default=90)
        group.add_argument(
            "--start", type=date.fromisoformat,
            help=f"Backfill from this date (YYYY-MM-DD); ECB data starts {ECB_FIRST_DAY}.",
        )

    def handle(self, *args, days, start, **options):
        end = timezone.now().date()
        if isinstance(start, str):  # call_command passes options through unparsed
            start = date.fromisoformat(start)
        start = start or end - timedelta(days=days)
        series = {}
        for chunk_start, chunk_end in yearly_ranges(start, end):
            series.update(fetch_rate_series(
                base=settings.BASE_CURRENCY,
                symbols=settings.SUPPORTED_CURRENCIES,
                start=chunk_start,
                end=chunk_end,
                api_base_url=settings.FOREX_API_BASE_URL,
            ))
        created = backfill_history(settings.BASE_CURRENCY, series)
        self.stdout.write(f"Fetched {len(series)} days; stored {created} rate changes.")
