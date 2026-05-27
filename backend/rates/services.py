from django.conf import settings
from django.db import transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rates.models import Currency, ExchangeRate

RATES_GROUP = "rates"


@transaction.atomic
def save_snapshot(snapshot):
    """Persist a RateSnapshot: ensure Currency rows, insert base->quote ExchangeRate rows.

    Wrapped in a transaction so a failure can't leave orphan Currency rows or a
    partially-written rate snapshot.
    """
    base, _ = Currency.objects.get_or_create(
        code=snapshot.base, defaults={"name": snapshot.base}
    )
    new_rows = []
    for code, value in snapshot.rates.items():
        quote, _ = Currency.objects.get_or_create(code=code, defaults={"name": code})
        if code == snapshot.base:
            continue
        new_rows.append(ExchangeRate(base=base, quote=quote, rate=value))
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
