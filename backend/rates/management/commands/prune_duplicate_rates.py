from django.core.management.base import BaseCommand
from django.db import transaction

from rates.models import ExchangeRate
from rates.services import prune_duplicate_rates


class Command(BaseCommand):
    help = "Delete exchange-rate rows that repeat the previous rate for their pair."

    def handle(self, *args, **options):
        with transaction.atomic():
            deleted = prune_duplicate_rates()
        self.stdout.write(f"Deleted {deleted} duplicate rows; {ExchangeRate.objects.count()} remain.")
        self.stdout.write("Run VACUUM FULL (or pg_repack) on the table to reclaim disk space.")
