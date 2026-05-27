import pytest
from decimal import Decimal
from unittest.mock import patch
from rates.fetcher import RateSnapshot
from rates.models import ExchangeRate


@pytest.mark.django_db
@patch("rates.tasks.broadcast_latest")
@patch("rates.tasks.fetch_latest_rates")
def test_fetch_rates_task_persists_and_broadcasts(mock_fetch, mock_broadcast):
    from rates.tasks import fetch_rates
    mock_fetch.return_value = RateSnapshot(
        base="EUR", rates={"EUR": Decimal("1"), "USD": Decimal("1.08")}, date="2026-05-27"
    )
    fetch_rates()
    assert ExchangeRate.objects.filter(base__code="EUR", quote__code="USD").count() == 1
    mock_broadcast.assert_called_once()
