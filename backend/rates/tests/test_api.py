import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from rates.fetcher import RateSnapshot
from rates.services import save_snapshot
from rates.models import Currency


@pytest.fixture
def seeded(db):
    save_snapshot(RateSnapshot(
        base="EUR",
        rates={"EUR": Decimal("1"), "USD": Decimal("1.08"), "GBP": Decimal("0.86")},
        date="2026-05-27",
    ))


def test_currencies_endpoint(seeded):
    client = APIClient()
    resp = client.get("/api/currencies/")
    assert resp.status_code == 200
    codes = {c["code"] for c in resp.json()}
    assert {"EUR", "USD", "GBP"} <= codes


def test_latest_endpoint(seeded):
    client = APIClient()
    resp = client.get("/api/rates/latest/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["base"] == "EUR"
    assert body["rates"]["USD"] == "1.080000"


def test_history_endpoint(seeded):
    client = APIClient()
    resp = client.get("/api/rates/history/?base=EUR&quote=USD")
    assert resp.status_code == 200
    points = resp.json()
    assert len(points) >= 1
    assert "rate" in points[0] and "fetched_at" in points[0]


def test_convert_endpoint(seeded):
    client = APIClient()
    resp = client.get("/api/convert/?from=USD&to=GBP&amount=100")
    assert resp.status_code == 200
    body = resp.json()
    expected = (Decimal("100") * Decimal("0.86") / Decimal("1.08")).quantize(Decimal("0.0001"))
    assert body["result"] == str(expected)


def test_convert_unknown_currency_returns_400(seeded):
    client = APIClient()
    resp = client.get("/api/convert/?from=USD&to=JPY&amount=100")
    assert resp.status_code == 400
