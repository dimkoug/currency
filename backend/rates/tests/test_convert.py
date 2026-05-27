import pytest
from decimal import Decimal
from rates.fetcher import convert


def test_convert_same_currency():
    rates = {"EUR": Decimal("1"), "USD": Decimal("1.08")}
    assert convert("USD", "USD", Decimal("50"), rates) == Decimal("50")


def test_convert_cross_rate():
    # base EUR=1, USD=1.08, GBP=0.86 -> 100 USD to GBP = 100 * 0.86/1.08
    rates = {"EUR": Decimal("1"), "USD": Decimal("1.08"), "GBP": Decimal("0.86")}
    result = convert("USD", "GBP", Decimal("100"), rates)
    assert result == (Decimal("100") * Decimal("0.86") / Decimal("1.08")).quantize(Decimal("0.0001"))


def test_convert_unknown_currency_raises():
    rates = {"EUR": Decimal("1"), "USD": Decimal("1.08")}
    with pytest.raises(KeyError):
        convert("USD", "JPY", Decimal("10"), rates)
