import pytest
from channels.testing.websocket import WebsocketCommunicator
from channels.layers import get_channel_layer
from config.asgi import application
from rates.services import RATES_GROUP


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_consumer_receives_broadcast():
    communicator = WebsocketCommunicator(application, "/ws/rates/")
    connected, _ = await communicator.connect()
    assert connected

    # Drain the on-connect payload (latest_rates_payload with no seeded data)
    await communicator.receive_json_from(timeout=2)

    layer = get_channel_layer()
    await layer.group_send(
        RATES_GROUP,
        {"type": "rates.update", "payload": {"base": "EUR", "rates": {"USD": "1.08"}}},
    )
    message = await communicator.receive_json_from(timeout=2)
    assert message["base"] == "EUR"
    assert message["rates"]["USD"] == "1.08"
    await communicator.disconnect()
