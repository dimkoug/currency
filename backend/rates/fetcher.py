from decimal import Decimal, ROUND_HALF_UP


def convert(from_code: str, to_code: str, amount: Decimal, rates: dict) -> Decimal:
    """Convert amount from `from_code` to `to_code` using base-relative rates.

    `rates` maps currency code -> rate relative to a common base (base itself = 1).
    Raises KeyError if either currency is missing.
    """
    value = amount * (rates[to_code] / rates[from_code])
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
