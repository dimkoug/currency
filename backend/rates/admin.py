from django.contrib import admin
from rates.models import Currency, ExchangeRate

admin.site.register(Currency)
admin.site.register(ExchangeRate)
