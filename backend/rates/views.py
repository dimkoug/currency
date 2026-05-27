from decimal import Decimal, InvalidOperation
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rates.models import Currency, ExchangeRate
from rates.serializers import CurrencySerializer, HistoryPointSerializer
from rates.services import latest_rates_payload
from rates.fetcher import convert


class CurrencyListView(ListAPIView):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer


class LatestRatesView(APIView):
    def get(self, request):
        return Response(latest_rates_payload())


class HistoryView(ListAPIView):
    serializer_class = HistoryPointSerializer

    def get_queryset(self):
        base = self.request.query_params.get("base", settings.BASE_CURRENCY)
        quote = self.request.query_params.get("quote")
        qs = ExchangeRate.objects.filter(base__code=base)
        if quote:
            qs = qs.filter(quote__code=quote)
        return qs.order_by("fetched_at")[:500]


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
