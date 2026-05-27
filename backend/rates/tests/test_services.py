import pytest
from decimal import Decimal
from rates.fetcher import RateSnapshot
from rates.models import Currency, ExchangeRate
from rates.services import save_snapshot, latest_rates_payload


@pytest.mark.django_db
def test_save_snapshot_creates_currencies_and_rates():
    snap = RateSnapshot(
        base="EUR",
        rates={"EUR": Decimal("1"), "USD": Decimal("1.08"), "GBP": Decimal("0.86")},
        date="2026-05-27",
    )
    save_snapshot(snap)
    assert Currency.objects.filter(code="USD").exists()
    assert ExchangeRate.objects.filter(base__code="EUR", quote__code="USD").count() == 1
    assert ExchangeRate.objects.filter(base__code="EUR", quote__code="GBP").count() == 1


@pytest.mark.django_db
def test_save_snapshot_query_count_is_constant(django_assert_max_num_queries):
    """save_snapshot must not issue a query per currency (no N+1).

    With 10 currencies the old get_or_create-per-currency approach issued ~20
    queries; the bulk approach is a small constant (savepoint + select + two
    bulk inserts) regardless of currency count.
    """
    codes = ["USD", "GBP", "JPY", "CHF", "AUD", "CAD", "SEK", "NOK", "NZD"]
    rates = {"EUR": Decimal("1")}
    for i, code in enumerate(codes):
        rates[code] = Decimal(f"1.{i:02d}")
    snap = RateSnapshot(base="EUR", rates=rates, date="2026-05-27")

    with django_assert_max_num_queries(6):
        save_snapshot(snap)

    assert ExchangeRate.objects.count() == len(codes)
    assert Currency.objects.count() == len(codes) + 1  # quotes + base


@pytest.mark.django_db
def test_latest_rates_payload_returns_most_recent():
    snap = RateSnapshot(base="EUR", rates={"EUR": Decimal("1"), "USD": Decimal("1.08")}, date="2026-05-27")
    save_snapshot(snap)
    payload = latest_rates_payload()
    assert payload["base"] == "EUR"
    assert payload["rates"]["USD"] == "1.080000"
    assert payload["rates"]["EUR"] == "1.000000"
    assert "fetched_at" in payload
