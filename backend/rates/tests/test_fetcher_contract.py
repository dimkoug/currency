"""Contract test for the forex fetcher.

`cassettes/frankfurter_latest.json` is a *real* response captured from the
ECB/Frankfurter API. The test replays it (no network) and asserts our fetcher
still parses the live response shape correctly — so if the upstream response
format drifts, refreshing the cassette will surface it here. To refresh:

    docker run --rm -v "$PWD:/repo" curlimages/curl -sL \\
      "https://api.frankfurter.app/latest?from=EUR&to=USD,GBP,JPY" \\
      -o /repo/backend/rates/tests/cassettes/frankfurter_latest.json
"""
import json
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch, MagicMock

from rates.fetcher import fetch_latest_rates

CASSETTE = Path(__file__).parent / "cassettes" / "frankfurter_latest.json"


@patch("rates.fetcher.requests.get")
def test_fetcher_parses_real_frankfurter_response(mock_get):
    payload = json.loads(CASSETTE.read_text())
    resp = MagicMock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    mock_get.return_value = resp

    snap = fetch_latest_rates(
        base="EUR",
        symbols=["EUR", "USD", "GBP", "JPY"],
        api_base_url="https://api.frankfurter.app",
    )

    # parsed shape
    assert snap.base == "EUR"
    assert snap.date
    assert snap.rates["EUR"] == Decimal("1")
    for code in ("USD", "GBP", "JPY"):
        assert code in snap.rates, f"missing {code} in real API response"
        assert snap.rates[code] > 0
        assert isinstance(snap.rates[code], Decimal)

    # request contract: base in `from`, base excluded from `to`
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["from"] == "EUR"
    assert "EUR" not in kwargs["params"]["to"].split(",")
    assert kwargs["timeout"] == 10
