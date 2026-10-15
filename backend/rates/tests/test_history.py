from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from rates.models import Currency, ExchangeRate

NOW = datetime(2026, 10, 15, 12, 30, tzinfo=dt_timezone.utc)


@pytest.fixture
def frozen_now(monkeypatch):
    monkeypatch.setattr(timezone, "now", lambda: NOW)
    return NOW


@pytest.fixture
def add_rate(db):
    for code in ("EUR", "USD", "GBP"):
        Currency.objects.get_or_create(code=code, defaults={"name": code})

    def _add(when, rate, quote="USD"):
        row = ExchangeRate.objects.create(base_id="EUR", quote_id=quote, rate=Decimal(rate))
        # fetched_at is auto_now_add, so backdate with an update.
        ExchangeRate.objects.filter(pk=row.pk).update(fetched_at=when)

    return _add


def _get(**params):
    resp = APIClient().get("/api/rates/history/", {"base": "EUR", "quote": "USD", **params})
    return resp


def test_history_returns_recent_data_not_oldest(frozen_now, add_rate):
    # 600 old rows used to fill the 500-row window and hide everything recent.
    old = NOW - timedelta(days=200)
    for i in range(600):
        add_rate(old + timedelta(seconds=10 * i), "1.1403")
    add_rate(NOW - timedelta(days=2), "1.2000")

    points = _get().json()
    assert points[-1]["rate"] == "1.200000"


def test_history_daily_one_point_per_day_forward_filled(frozen_now, add_rate):
    add_rate(NOW - timedelta(days=40), "1.10")  # before window: seeds the start
    add_rate(datetime(2026, 10, 10, 15, tzinfo=dt_timezone.utc), "1.12")
    add_rate(datetime(2026, 10, 10, 16, tzinfo=dt_timezone.utc), "1.13")  # last of day wins
    add_rate(datetime(2026, 10, 13, 15, tzinfo=dt_timezone.utc), "1.15")

    points = _get(days=7).json()
    days = [p["fetched_at"][:10] for p in points]
    rates = [p["rate"] for p in points]
    assert days == [f"2026-10-{d:02d}" for d in range(9, 16)]
    assert rates == [
        "1.100000",  # 09: carried from before the window
        "1.130000",  # 10
        "1.130000",  # 11
        "1.130000",  # 12
        "1.150000",  # 13
        "1.150000",  # 14
        "1.150000",  # 15 (today)
    ]


def test_history_starts_at_first_known_value(frozen_now, add_rate):
    add_rate(datetime(2026, 10, 14, 9, tzinfo=dt_timezone.utc), "1.10")
    points = _get(days=30).json()
    assert [p["fetched_at"][:10] for p in points] == ["2026-10-14", "2026-10-15"]


def test_history_hourly(frozen_now, add_rate):
    add_rate(datetime(2026, 10, 15, 9, 5, tzinfo=dt_timezone.utc), "1.10")
    add_rate(datetime(2026, 10, 15, 11, 59, tzinfo=dt_timezone.utc), "1.11")
    points = _get(interval="hour", days=1).json()
    assert [(p["fetched_at"][11:16], p["rate"]) for p in points] == [
        ("09:00", "1.100000"),
        ("10:00", "1.100000"),
        ("11:00", "1.110000"),
        ("12:00", "1.110000"),
    ]


def test_history_filters_by_quote(frozen_now, add_rate):
    add_rate(NOW - timedelta(hours=1), "0.86", quote="GBP")
    add_rate(NOW - timedelta(hours=1), "1.08", quote="USD")
    points = _get(days=1).json()
    assert {p["rate"] for p in points} == {"1.080000"}


def test_history_clamps_days(frozen_now, add_rate):
    add_rate(NOW - timedelta(days=500), "1.10")
    assert len(_get(days=10000).json()) == 90  # 90 daily buckets ending today
    assert len(_get(interval="hour", days=10000).json()) == 7 * 24


@pytest.mark.parametrize("params", [{"quote": ""}, {"days": "abc"}, {"interval": "minute"}])
def test_history_rejects_bad_params(db, params):
    assert _get(**params).status_code == 400


def test_history_empty(frozen_now, add_rate):
    resp = _get()
    assert resp.status_code == 200
    assert resp.json() == []
