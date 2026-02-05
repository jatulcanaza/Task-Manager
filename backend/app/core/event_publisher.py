import json
import aio_pika
from app.core.config import settings

class EventPublisher:
    def __init__(self):
        self._conn = None
        self._ch = None
        self._exchange = None

    async def connect(self):
        if self._conn:
            return
        self._conn = await aio_pika.connect_robust(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            login=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASS,
        )
        self._ch = await self._conn.channel()
        self._exchange = await self._ch.declare_exchange(
            "events", aio_pika.ExchangeType.TOPIC, durable=True
        )

    async def publish(self, routing_key: str, payload: dict):
        await self.connect()
        body = json.dumps(payload, default=str).encode("utf-8")
        msg = aio_pika.Message(body=body, content_type="application/json")
        await self._exchange.publish(msg, routing_key=routing_key)

publisher = EventPublisher()
