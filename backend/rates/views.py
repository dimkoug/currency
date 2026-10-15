from datetime import timedelta
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.db.models.functions import TruncDay, TruncHour
from django.utils import timezone
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rates.models import Currency, ExchangeRate
from rates.serializers import CurrencySerializer
from rates.services import latest_rates_payload
from rates.fetcher import convert


class CurrencyListView(ListAPIView):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer


class LatestRatesView(APIView):
    def get(self, request):
        return Response(latest_rates_payload())


# interval -> (DB truncation, bucket length, max days of history served)
HISTORY_INTERVALS = {
    "day": (TruncDay, timedelta(days=1), 90),
    "hour": (TruncHour, timedelta(hours=1), 7),
}
HISTORY_DEFAULT_DAYS = 30


class HistoryView(APIView):
    """One point per day (or hour) over the last ``days``, newest bucket last.

    Rows are only stored when a rate changes, so each bucket takes the last
    change inside it and empty buckets carry the previous value forward
    (seeded from the last change before the window).
    """

    def get(self, request):
        params = request.query_params
        base = params.get("base", settings.BASE_CURRENCY)
        quote = params.get("quote")
        interval = params.get("interval", "day")
        if not quote:
            return Response({"error": "quote is required"}, status=400)
        if interval not in HISTORY_INTERVALS:
            return Response({"error": "interval must be day or hour"}, status=400)
        try:
            days = int(params.get("days", HISTORY_DEFAULT_DAYS))
        except ValueError:
            return Response({"error": "invalid days"}, status=400)
        trunc, step, max_days = HISTORY_INTERVALS[interval]
        days = max(1, min(days, max_days))

        now = timezone.now()
        current = now.replace(minute=0, second=0, microsecond=0)
        if interval == "day":
            current = current.replace(hour=0)
        n_buckets = days * (timedelta(days=1) // step)
        start = current - (n_buckets - 1) * step

        pair = ExchangeRate.objects.filter(base_id=base, quote_id=quote)
        seed = (
            pair.filter(fetched_at__lt=start)
            .order_by("-fetched_at")
            .values_list("rate", flat=True)
            .first()
        )
        changes = dict(
            pair.filter(fetched_at__gte=start)
            .annotate(bucket=trunc("fetched_at"))
            .order_by("bucket", "-fetched_at")
            .distinct("bucket")
            .values_list("bucket", "rate")
        )

        as_iso = serializers.DateTimeField().to_representation
        points, rate = [], seed
        for i in range(n_buckets):
            bucket = start + i * step
            rate = changes.get(bucket, rate)
            if rate is not None:
                points.append({"rate": str(rate), "fetched_at": as_iso(bucket)})
        return Response(points)


class ConvertView(APIView):
    def get(self, request):
        from_code = request.query_params.get("from")
        to_code = request.query_params.get("to")
        try:
            amount = Decimal(request.query_params.get("amount", "0"))
        except InvalidOperation:
            return Response({"error": "invalid amount"}, status=400)
        payload = latest_rates_payload()
        rates = {k: Decimal(v) for k, v in payload["rates"].items()}
        try:
            result = convert(from_code, to_code, amount, rates)
        except KeyError:
            return Response({"error": "unknown currency"}, status=400)
        return Response({"from": from_code, "to": to_code, "amount": str(amount), "result": str(result)})
