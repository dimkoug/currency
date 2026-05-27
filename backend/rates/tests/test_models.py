import pytest
from rates.models import Currency, ExchangeRate


@pytest.mark.django_db
def test_currency_str():
    c = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
    assert str(c) == "USD"


@pytest.mark.django_db
def test_exchange_rate_roundtrip():
    eur = Currency.objects.create(code="EUR", name="Euro", symbol="€")
    usd = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
    rate = ExchangeRate.objects.create(base=eur, quote=usd, rate="1.0850")
    assert rate.base.code == "EUR"
    assert rate.quote.code == "USD"
    assert str(rate.rate) == "1.0850"
    assert rate.fetched_at is not None
