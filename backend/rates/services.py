from datetime import datetime, time, timezone as dt_timezone
from decimal import Decimal
from django.conf import settings
from django.db import connection, transaction
from django.db.models import Min
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

    # The upstream (ECB via Frankfurter) changes ~once per working day but is
    # polled every few seconds, so only store a row when a quote's rate differs
    # from its latest stored value. Row timestamps therefore mark *changes*.
    latest = dict(
        ExchangeRate.objects.filter(base_id=snapshot.base, quote_id__in=codes)
        .order_by("quote_id", "-fetched_at")
        .distinct("quote_id")
        .values_list("quote_id", "rate")
    )
    new_rows = [
        ExchangeRate(base_id=snapshot.base, quote_id=code, rate=value)
        for code, value in snapshot.rates.items()
        if code != snapshot.base and latest.get(code) != _quantize_rate(value)
    ]
    if new_rows:
        ExchangeRate.objects.bulk_create(new_rows)


_RATE_FIELD = ExchangeRate._meta.get_field("rate")


def _quantize_rate(value):
    """Round to the column's precision so 1.0800001 == stored 1.080000."""
    return Decimal(value).quantize(Decimal(1).scaleb(-_RATE_FIELD.decimal_places))


# ECB reference rates are published around 16:00 CET (~15:00 UTC).
ECB_PUBLICATION_UTC = time(15, 0)

# Delete every row whose rate equals the previous row for the same pair, so
# only the rows where a rate actually changed remain (matching save_snapshot).
PRUNE_SQL = """
DELETE FROM {table} t
USING (
    SELECT id, rate, LAG(rate) OVER (
        PARTITION BY base_id, quote_id ORDER BY fetched_at, id
    ) AS prev_rate
    FROM {table}
) d
WHERE t.id = d.id AND d.rate = d.prev_rate
"""


def prune_duplicate_rates():
    """Delete rows that repeat their pair's previous rate; return the count."""
    table = connection.ops.quote_name(ExchangeRate._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute(PRUNE_SQL.format(table=table))
        return cursor.rowcount


@transaction.atomic
def backfill_history(base, series):
    """Store daily fixings ({date: {code: Decimal}}) that predate polled data.

    For each pair only days before its earliest stored row are used, and only
    days where the rate changed are stored, timestamped at ECB publication
    time. Re-running is a no-op. Returns the number of rows created.
    """
    codes = {base, *(code for rates in series.values() for code in rates)}
    Currency.objects.bulk_create(
        [Currency(code=code, name=code) for code in codes], ignore_conflicts=True
    )
    earliest = dict(
        ExchangeRate.objects.filter(base_id=base)
        .values("quote_id")
        .annotate(first=Min("fetched_at"))
        .values_list("quote_id", "first")
    )
    new_rows, previous = [], {}
    for day, rates in sorted(series.items()):
        when = datetime.combine(day, ECB_PUBLICATION_UTC, tzinfo=dt_timezone.utc)
        for code, value in rates.items():
            rate = _quantize_rate(value)
            first = earliest.get(code)
            if code == base or (first and when >= first) or previous.get(code) == rate:
                continue
            previous[code] = rate
            new_rows.append(
                ExchangeRate(base_id=base, quote_id=code, rate=rate, fetched_at=when)
            )
    ExchangeRate.objects.bulk_create(new_rows)
    # The first polled row may now repeat the last backfilled rate.
    if new_rows:
        prune_duplicate_rates()
    return len(new_rows)


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
