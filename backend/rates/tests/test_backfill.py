from datetime import date, datetime, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.management import call_command

from rates.models import Currency, ExchangeRate
from rates.services import backfill_history


def D(v):
    return Decimal(v)


def rows(quote="USD"):
    return [
        (r.fetched_at, str(r.rate))
        for r in ExchangeRate.objects.filter(quote_id=quote).order_by("fetched_at")
    ]


def at(day, hour=15):
    return datetime(2026, 10, day, hour, tzinfo=dt_timezone.utc)


@pytest.fixture
def live_row(db):
    """An existing polled row, as stored by save_snapshot."""
    for code in ("EUR", "USD"):
        Currency.objects.create(code=code, name=code)

    def _add(when, rate):
        r = ExchangeRate.objects.create(base_id="EUR", quote_id="USD", rate=D(rate))
        ExchangeRate.objects.filter(pk=r.pk).update(fetched_at=when)

    return _add


@pytest.mark.django_db
def test_backfill_stores_only_changes_at_publication_time():
    series = {
        date(2026, 10, 5): {"USD": D("1.10")},
        date(2026, 10, 6): {"USD": D("1.10")},
        date(2026, 10, 7): {"USD": D("1.11")},
    }
    created = backfill_history("EUR", series)
    assert rows() == [(at(5), "1.100000"), (at(7), "1.110000")]
    assert created == 2
    assert Currency.objects.filter(code="USD").exists()


@pytest.mark.django_db
def test_backfill_only_fills_before_existing_data(live_row):
    live_row(at(8, 9), "1.12")
    series = {
        date(2026, 10, 6): {"USD": D("1.10")},
        date(2026, 10, 8): {"USD": D("1.99")},  # overlaps polled data: ignored
        date(2026, 10, 9): {"USD": D("1.99")},
    }
    backfill_history("EUR", series)
    assert rows() == [(at(6), "1.100000"), (at(8, 9), "1.120000")]


@pytest.mark.django_db
def test_backfill_drops_polled_row_that_repeats_the_backfilled_rate(live_row):
    # Polling started on a Sunday and stored Friday's fixing; once Friday is
    # backfilled, the Sunday row is a duplicate and is pruned.
    live_row(datetime(2026, 9, 27, 1, tzinfo=dt_timezone.utc), "1.1403")
    backfill_history("EUR", {date(2026, 9, 25): {"USD": D("1.1403")}})
    assert rows() == [(datetime(2026, 9, 25, 15, tzinfo=dt_timezone.utc), "1.140300")]


@pytest.mark.django_db
def test_backfill_is_idempotent():
    series = {date(2026, 10, 5): {"USD": D("1.10")}, date(2026, 10, 7): {"USD": D("1.11")}}
    backfill_history("EUR", series)
    assert backfill_history("EUR", series) == 0
    assert len(rows()) == 2


@pytest.mark.django_db
@patch("rates.management.commands.backfill_history.fetch_rate_series")
def test_backfill_command(mock_series, settings):
    settings.BASE_CURRENCY = "EUR"
    settings.SUPPORTED_CURRENCIES = ["EUR", "USD"]
    mock_series.return_value = {date(2026, 10, 5): {"USD": D("1.10")}}
    call_command("backfill_history", days=10)
    kwargs = mock_series.call_args.kwargs
    assert (kwargs["end"] - kwargs["start"]).days == 10
    assert kwargs["symbols"] == ["EUR", "USD"]
    assert len(rows()) == 1
