from django.db import models


class Currency(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=64)
    symbol = models.CharField(max_length=8, blank=True)

    class Meta:
        ordering = ["code"]
        verbose_name_plural = "currencies"

    def __str__(self):
        return self.code


class ExchangeRate(models.Model):
    base = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="rates_as_base")
    quote = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="rates_as_quote")
    rate = models.DecimalField(max_digits=18, decimal_places=6)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["base", "quote", "fetched_at"]),
            models.Index(fields=["fetched_at"]),
        ]
        ordering = ["-fetched_at"]

    def __str__(self):
        return f"{self.base_id}/{self.quote_id}={self.rate}"
