from django.urls import path
from rates.views import CurrencyListView, LatestRatesView, HistoryView, ConvertView

urlpatterns = [
    path("currencies/", CurrencyListView.as_view()),
    path("rates/latest/", LatestRatesView.as_view()),
    path("rates/history/", HistoryView.as_view()),
    path("convert/", ConvertView.as_view()),
]
