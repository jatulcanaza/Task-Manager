import json
import logging
import asyncio
from email.message import EmailMessage

import aio_pika
import paho.mqtt.client as mqtt
import aiosmtplib

from app.core.config import settings

logger = logging.getLogger("bridge_consumer")
logging.basicConfig(level=logging.INFO)


def mqtt_publish(topic: str, payload: dict) -> None:
    """
    Publica el evento en MQTT para que Backend B lo consuma y lo emita por WebSocket.

    Flujo recomendado:
      Backend A -> RabbitMQ (events topic)
      Bridge (este archivo) -> MQTT (task/events)
      Backend B -> MQTT listener -> WS broadcast -> Dashboard en vivo
    """
    try:
        client = mqtt.Client()
        client.connect(settings.MQTT_HOST, settings.MQTT_PORT, 60)
        client.publish(topic, json.dumps(payload, default=str))
        client.disconnect()
        logger.info(f"[MQTT] publicado en topic={topic}")
    except Exception as e:
        logger.exception(f"[MQTT] error publicando: {e}")


async def send_admin_email(subject: str, body: str) -> None:
    """
    Notificación por email al admin (Kafka-like notification).

    Si la config no está completa, NO revienta el consumer.
    """
    if not (settings.SMTP_USER and settings.SMTP_PASS and settings.ADMIN_NOTIFY_TO):
        logger.warning(
            "[SMTP] Config incompleta: no se enviará email "
            "(SMTP_USER/SMTP_PASS/ADMIN_NOTIFY_TO)"
        )
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
            start_tls=True,  # Gmail: STARTTLS
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            timeout=20,
        )
        logger.info(f"[SMTP] email enviado a {settings.ADMIN_NOTIFY_TO} subject={subject}")
    except Exception as e:
        # IMPORTANTÍSIMO: que el email no tumbe el consumer
        logger.exception(f"[SMTP] fallo enviando email: {e}")


async def start_bridge_consumer() -> None:
    """
    Consumer de RabbitMQ que escucha eventos task.* y los "puentea" a:
      1) MQTT (para realtime en B)
      2) Email (notificación al admin)

    Nota:
    - NO se hace broadcast WS aquí.
    - El WS se emite desde Backend B escuchando MQTT.
    """
    logger.info("[BRIDGE] iniciando consumer...")

    # 1) Conexión robusta a RabbitMQ con reintentos
    conn = None
    while conn is None:
        try:
            conn = await aio_pika.connect_robust(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                login=settings.RABBITMQ_USER,
                password=settings.RABBITMQ_PASS,
            )
        except Exception as e:
            logger.exception(f"[BRIDGE] RabbitMQ no disponible aún: {e}. Reintentando en 2s...")
            await asyncio.sleep(2)

    ch = await conn.channel()

    # 2) Exchange topic "events" (debe coincidir con tu publisher)
    exchange = await ch.declare_exchange(
        "events",
        aio_pika.ExchangeType.TOPIC,
        durable=True,
    )

    # 3) Cola durable para el bridge (si reinicia, no se pierde)
    queue = await ch.declare_queue("bridge-queue", durable=True)

    # 4) Bind: escuchar todos los eventos de tasks
    await queue.bind(exchange, routing_key="task.*")

    logger.info("[BRIDGE] conectado a RabbitMQ, escuchando routing_key=task.* en queue=bridge-queue")

    # 5) Consumir mensajes continuamente
    async with queue.iterator() as q:
        async for message in q:
            payload = None
            try:
                payload = json.loads(message.body.decode("utf-8"))
                event_type = payload.get("type", "task.event")
                rk = message.routing_key

                logger.info(f"[BRIDGE] evento recibido: {event_type} rk={rk}")

                # A) MQTT publish (para que B lo vea y lo mande por WS)
                mqtt_publish(settings.MQTT_TOPIC, payload)

                # B) Email al admin
                subj = f"[TaskManager] {event_type}"
                body = json.dumps(payload, indent=2, default=str)
                await send_admin_email(subj, body)

                # ✅ ACK: procesado OK
                await message.ack()

            except Exception as e:
                logger.exception(f"[BRIDGE] error procesando mensaje: {e} payload={payload}")

                # Para no ciclar infinito, ACK igual.
                # Si quieres reintento real: await message.reject(requeue=True)
                try:
                    await message.ack()
                except Exception:
                    pass
