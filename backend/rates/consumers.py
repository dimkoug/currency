from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from rates.services import RATES_GROUP, latest_rates_payload


class RatesConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(RATES_GROUP, self.channel_name)
        await self.accept()
        payload = await sync_to_async(latest_rates_payload)()
        await self.send_json(payload)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(RATES_GROUP, self.channel_name)

    async def rates_update(self, event):
        await self.send_json(event["payload"])
