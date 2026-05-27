from django.urls import path
from rates.consumers import RatesConsumer

websocket_urlpatterns = [
    path("ws/rates/", RatesConsumer.as_asgi()),
]
