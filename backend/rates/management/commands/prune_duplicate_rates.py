from django.core.management.base import BaseCommand
from django.db import connection, transaction

from rates.models import ExchangeRate

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


class Command(BaseCommand):
    help = "Delete exchange-rate rows that repeat the previous rate for their pair."

    def handle(self, *args, **options):
        table = connection.ops.quote_name(ExchangeRate._meta.db_table)
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(PRUNE_SQL.format(table=table))
            deleted = cursor.rowcount
        self.stdout.write(f"Deleted {deleted} duplicate rows; {ExchangeRate.objects.count()} remain.")
        self.stdout.write("Run VACUUM FULL (or pg_repack) on the table to reclaim disk space.")
