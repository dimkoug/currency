from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from datetime import date
import requests


@dataclass
class RateSnapshot:
    base: str
    rates: dict  # code -> Decimal (includes base = Decimal("1"))
    date: str


def fetch_latest_rates(base: str, symbols: list, api_base_url: str) -> RateSnapshot:
    """Fetch latest rates from a Frankfurter-compatible API.

    Returns a RateSnapshot whose `rates` includes the base currency as Decimal('1').
    """
    quotes = [s for s in symbols if s != base]
    resp = requests.get(
        f"{api_base_url}/latest",
        params={"from": base, "to": ",".join(quotes)},
        timeout=10,
    )
    resp.raise_for_status()
    payload = resp.json()
    rates = {base: Decimal("1")}
    for code, value in payload["rates"].items():
        rates[code] = Decimal(str(value))
    return RateSnapshot(base=base, rates=rates, date=payload["date"])


def convert(from_code: str, to_code: str, amount: Decimal, rates: dict) -> Decimal:
    """Convert amount from `from_code` to `to_code` using base-relative rates.

    `rates` maps currency code -> rate relative to a common base (base itself = 1).
    Raises KeyError if either currency is missing.
    """
    value = amount * (rates[to_code] / rates[from_code])
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def fetch_rate_series(base: str, symbols: list, start, end, api_base_url: str) -> dict:
    """Fetch daily rates between two dates from a Frankfurter-compatible API.

    Returns {date: {code: Decimal}} sorted by date. Only working days appear:
    the ECB publishes no fixing on weekends or TARGET holidays.
    """
    quotes = [s for s in symbols if s != base]
    resp = requests.get(
        f"{api_base_url}/{start.isoformat()}..{end.isoformat()}",
        params={"from": base, "to": ",".join(quotes)},
        timeout=30,
    )
    resp.raise_for_status()
    return {
        date.fromisoformat(day): {code: Decimal(str(v)) for code, v in rates.items()}
        for day, rates in sorted(resp.json()["rates"].items())
    }
