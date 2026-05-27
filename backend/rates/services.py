from django.conf import settings
from django.db import transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rates.models import Currency, ExchangeRate

RATES_GROUP = "rates"


@transaction.atomic
def save_snapshot(snapshot):
    """Persist a RateSnapshot in a constant number of queries.

    Avoids the N+1 pattern of one get_or_create per currency: fetch the existing
    codes in a single query, bulk-create only the missing currencies, then
    bulk-create the rate rows. Foreign keys are assigned by id (Currency's PK is
    its code), so no Currency instances need to be loaded to build the rates.

    Wrapped in a transaction so a failure can't leave orphan Currency rows or a
    partially-written rate snapshot.
    """
    codes = {snapshot.base, *snapshot.rates.keys()}
    existing = set(
        Currency.objects.filter(code__in=codes).values_list("code", flat=True)
    )
    missing = [Currency(code=code, name=code) for code in codes if code not in existing]
    if missing:
        Currency.objects.bulk_create(missing, ignore_conflicts=True)

    new_rows = [
        ExchangeRate(base_id=snapshot.base, quote_id=code, rate=value)
        for code, value in snapshot.rates.items()
        if code != snapshot.base
    ]
    ExchangeRate.objects.bulk_create(new_rows)


def latest_rates_payload():
    """Build the latest-rates payload (base currency + code->rate string + timestamp)."""
    base_code = settings.BASE_CURRENCY
    latest = (
        ExchangeRate.objects.filter(base__code=base_code)
        .order_by("quote_id", "-fetched_at")
        .distinct("quote_id")
    )
    rates = {base_code: "1.000000"}
    fetched_at = None
    for row in latest:
        rates[row.quote_id] = str(row.rate)
        if fetched_at is None or row.fetched_at > fetched_at:
            fetched_at = row.fetched_at
    return {
        "base": base_code,
        "rates": rates,
        "fetched_at": fetched_at.isoformat() if fetched_at else None,
    }


def broadcast_latest():
    """Send the latest-rates payload to the Channels group."""
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        RATES_GROUP, {"type": "rates.update", "payload": latest_rates_payload()}
    )
