from rest_framework import serializers
from rates.models import Currency, ExchangeRate


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ["code", "name", "symbol"]


class HistoryPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = ["rate", "fetched_at"]
