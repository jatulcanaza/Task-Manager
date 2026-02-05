import json
import logging
import aio_pika
import paho.mqtt.client as mqtt
import aiosmtplib
from email.message import EmailMessage
import asyncio

from app.core.config import settings
from app.core.ws_manager import ws_manager

logger = logging.getLogger("bridge_consumer")
logging.basicConfig(level=logging.INFO)

def mqtt_publish(topic: str, payload: dict):
    try:
        client = mqtt.Client()
        client.connect(settings.MQTT_HOST, settings.MQTT_PORT, 60)
        client.publish(topic, json.dumps(payload, default=str))
        client.disconnect()
        logger.info(f"[MQTT] publicado en topic={topic}")
    except Exception as e:
        logger.exception(f"[MQTT] error publicando: {e}")

async def send_admin_email(subject: str, body: str):
    # Si falta config, no hacemos nada
    if not (settings.SMTP_USER and settings.SMTP_PASS and settings.ADMIN_NOTIFY_TO):
        logger.warning("[SMTP] Config incompleta: no se enviará email (SMTP_USER/SMTP_PASS/ADMIN_NOTIFY_TO)")
        return

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = settings.ADMIN_NOTIFY_TO
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            start_tls=True,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            timeout=20,
        )
        logger.info(f"[SMTP] email enviado a {settings.ADMIN_NOTIFY_TO} subject={subject}")
    except Exception as e:
        # IMPORTANTÍSIMO: no dejar que esto mate el consumer
        logger.exception(f"[SMTP] fallo enviando email: {e}")

async def start_bridge_consumer():
    logger.info("[BRIDGE] iniciando consumer...")

    while True:
        try:
            conn = await aio_pika.connect_robust(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                login=settings.RABBITMQ_USER,
                password=settings.RABBITMQ_PASS,
            )
            break
        except Exception as e:
            logger.exception(f"[BRIDGE] RabbitMQ no disponible aún: {e}. Reintentando en 2s...")
            await asyncio.sleep(2)

    ch = await conn.channel()

    exchange = await ch.declare_exchange("events", aio_pika.ExchangeType.TOPIC, durable=True)
    queue = await ch.declare_queue("bridge-queue", durable=True)

    await queue.bind(exchange, routing_key="task.*")

    logger.info("[BRIDGE] conectado a RabbitMQ, escuchando routing_key=task.* en queue=bridge-queue")

    async with queue.iterator() as q:
        async for message in q:
            payload = None
            try:
                payload = json.loads(message.body.decode("utf-8"))
                logger.info(f"[BRIDGE] evento recibido: {payload.get('type')} rk={message.routing_key}")

                # 1) WebSocket realtime
                try:
                    await ws_manager.broadcast_json(payload)
                except Exception as e:
                    logger.exception(f"[WS] error broadcast: {e}")

                # 2) MQTT publish
                mqtt_publish(settings.MQTT_TOPIC, payload)

                # 3) Email al admin
                subj = f"[TaskManager] {payload.get('type','task.event')}"
                body = json.dumps(payload, indent=2, default=str)
                await send_admin_email(subj, body)

                # ✅ ACK manual (si llegamos aquí, procesado)
                await message.ack()

            except Exception as e:
                logger.exception(f"[BRIDGE] error procesando mensaje: {e} payload={payload}")

                # ✅ Para no crear loop infinito si algo está mal, ACK igual.
                # Si quieres reintento real, aquí podrías hacer reject(requeue=True)
                await message.ack()
