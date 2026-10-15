from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

import pytest
from django.core.management import call_command

from rates.models import Currency, ExchangeRate

T0 = datetime(2026, 9, 27, tzinfo=dt_timezone.utc)


@pytest.mark.django_db
def test_prune_keeps_only_changes():
    for code in ("EUR", "USD", "GBP"):
        Currency.objects.create(code=code, name=code)
    series = {"USD": ["1.10", "1.10", "1.11", "1.11", "1.10"], "GBP": ["0.86", "0.86"]}
    for quote, rates in series.items():
        for i, rate in enumerate(rates):
            row = ExchangeRate.objects.create(base_id="EUR", quote_id=quote, rate=Decimal(rate))
            ExchangeRate.objects.filter(pk=row.pk).update(fetched_at=T0 + timedelta(minutes=i))

    call_command("prune_duplicate_rates")

    def remaining(q):
        return [str(r) for r in ExchangeRate.objects.filter(quote_id=q)
                .order_by("fetched_at").values_list("rate", flat=True)]
    assert remaining("USD") == ["1.100000", "1.110000", "1.100000"]
    assert remaining("GBP") == ["0.860000"]
