from decimal import Decimal
from unittest.mock import patch, MagicMock
from rates.fetcher import fetch_latest_rates


def _mock_response(payload):
    resp = MagicMock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


@patch("rates.fetcher.requests.get")
def test_fetch_latest_rates_parses_payload(mock_get):
    mock_get.return_value = _mock_response({
        "amount": 1, "base": "EUR", "date": "2026-05-27",
        "rates": {"USD": 1.08, "GBP": 0.86},
    })
    result = fetch_latest_rates(
        base="EUR",
        symbols=["USD", "GBP"],
        api_base_url="https://api.frankfurter.app",
    )
    assert result.base == "EUR"
    assert result.rates["EUR"] == Decimal("1")
    assert result.rates["USD"] == Decimal("1.08")
    assert result.rates["GBP"] == Decimal("0.86")


@patch("rates.fetcher.requests.get")
def test_fetch_latest_rates_builds_request(mock_get):
    mock_get.return_value = _mock_response(
        {"amount": 1, "base": "EUR", "date": "2026-05-27", "rates": {"USD": 1.08}}
    )
    fetch_latest_rates(base="EUR", symbols=["USD"], api_base_url="https://api.frankfurter.app")
    args, kwargs = mock_get.call_args
    assert args[0] == "https://api.frankfurter.app/latest"
    assert kwargs["params"] == {"from": "EUR", "to": "USD"}
    assert kwargs["timeout"] == 10
