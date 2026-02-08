import json
import logging
import asyncio
from email.message import EmailMessage

import aio_pika
import paho.mqtt.client as mqtt
import aiosmtplib

from app.core.config import settings

# -----------------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------------
# Creamos un logger con nombre específico para este "bridge_consumer".
# Esto ayuda a filtrar logs y a identificar este componente en producción.
logger = logging.getLogger("bridge_consumer")

# Configura logging a nivel INFO por defecto (para ver eventos normales).
# Si quieres más detalle, puedes subirlo a DEBUG.
logging.basicConfig(level=logging.INFO)


# -----------------------------------------------------------------------------
# MQTT PUBLISHER (Sync)
# -----------------------------------------------------------------------------
def mqtt_publish(topic: str, payload: dict) -> None:
    """
    Publica el evento en MQTT para que Backend B lo consuma y lo emita por WebSocket.

    Flujo recomendado:
      Backend A -> RabbitMQ (exchange "events", topic routing_key task.*)
      Bridge (este archivo) -> MQTT (ej. task/events)
      Backend B -> MQTT listener -> WS broadcast -> Dashboard en vivo

    IMPORTANTE:
    - Este publish es síncrono (bloqueante) porque usa paho-mqtt en modo simple.
    - Está bien si el volumen de eventos es bajo/moderado.
    - Si el volumen crece, conviene reutilizar conexión o usar cliente async.
    """
    try:
        # 1) Crear un cliente MQTT por evento (simple, pero no el más eficiente).
        client = mqtt.Client()

        # 2) Conectar al broker MQTT definido en settings (host/port).
        #    keepalive=60: intervalo para mantener viva la conexión.
        client.connect(settings.MQTT_HOST, settings.MQTT_PORT, 60)

        # 3) Publicar el mensaje:
        #    - Convertimos el dict a JSON.
        #    - default=str permite serializar objetos no JSON (ej. datetime),
        #      convirtiéndolos a string.
        client.publish(topic, json.dumps(payload, default=str))

        # 4) Cerrar conexión (porque creamos un cliente por evento).
        client.disconnect()

        logger.info(f"[MQTT] publicado en topic={topic}")

    except Exception as e:
        # logger.exception imprime stacktrace completo, útil para depurar.
        logger.exception(f"[MQTT] error publicando: {e}")


# -----------------------------------------------------------------------------
# SMTP EMAIL NOTIFICATION (Async)
# -----------------------------------------------------------------------------
async def send_admin_email(subject: str, body: str) -> None:
    """
    Notificación por email al admin (Kafka-like notification).

    Diseño defensivo:
    - Si falta configuración SMTP, no se envía y NO se cae el consumer.
    - Si falla el envío, se loguea el error y el consumer sigue vivo.

    Esto simula "notificaciones" tipo Kafka/email/SMS como parte del requisito.
    """
    # 1) Validación de configuración mínima:
    #    Si no están credenciales o destinatario, no intentamos enviar nada.
    #    Esto evita romper el proceso por simple falta de secrets/config.
    if not (settings.SMTP_USER and settings.SMTP_PASS and settings.ADMIN_NOTIFY_TO):
        logger.warning(
            "[SMTP] Config incompleta: no se enviará email "
            "(SMTP_USER/SMTP_PASS/ADMIN_NOTIFY_TO)"
        )
        return

    # 2) Construcción del email:
    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM            # remitente (ej. tu correo)
    msg["To"] = settings.ADMIN_NOTIFY_TO        # destinatario admin
    msg["Subject"] = subject                    # asunto
    msg.set_content(body)                       # contenido plano

    try:
        # 3) Enviar email de forma asíncrona con aiosmtplib:
        #    - start_tls=True: negocia STARTTLS (común en Gmail)
        #    - timeout: para no quedarse colgado indefinidamente
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
        # IMPORTANTÍSIMO:
        # - Si falla el email, NO tumbamos el bridge.
        # - Solo logueamos el fallo (stacktrace) y continuamos.
        logger.exception(f"[SMTP] fallo enviando email: {e}")


# -----------------------------------------------------------------------------
# RABBITMQ CONSUMER (Async) -> BRIDGE TO MQTT + EMAIL
# -----------------------------------------------------------------------------
async def start_bridge_consumer() -> None:
    """
    Consumer de RabbitMQ que escucha eventos task.* y los "puentea" a:
      1) MQTT (para realtime en Backend B)
      2) Email (notificación al admin)

    Nota:
    - NO se hace broadcast WS aquí (WebSockets NO viven en este proceso).
    - El WS se emite desde Backend B escuchando MQTT.

    Este proceso es el "puente" (bridge) entre el bus de eventos (RabbitMQ)
    y el canal realtime + notificaciones.
    """
    logger.info("[BRIDGE] iniciando consumer...")

    # -------------------------------------------------------------------------
    # 1) CONEXIÓN ROBUSTA A RABBITMQ CON REINTENTOS
    # -------------------------------------------------------------------------
    # Usamos connect_robust de aio_pika:
    # - Reintenta reconexiones automáticamente ante cortes.
    # - Aun así, hacemos un bucle inicial por si Rabbit aún no levanta.
    conn = None
    while conn is None:
        try:
            # Conexión a RabbitMQ (credenciales/host/port en settings)
            conn = await aio_pika.connect_robust(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                login=settings.RABBITMQ_USER,
                password=settings.RABBITMQ_PASS,
            )
        except Exception as e:
            # Si RabbitMQ no está listo, esperamos 2 segundos y reintentamos.
            logger.exception(f"[BRIDGE] RabbitMQ no disponible aún: {e}. Reintentando en 2s...")
            await asyncio.sleep(2)

    # Abrimos un canal AMQP sobre esa conexión.
    ch = await conn.channel()

    # -------------------------------------------------------------------------
    # 2) DECLARAR EXCHANGE TOPIC "events"
    # -------------------------------------------------------------------------
    # Este exchange debe "coincidir" con el publisher (Backend A).
    # - type TOPIC: permite routing_keys como "task.created", "task.updated", etc.
    # - durable=True: persiste el exchange si Rabbit reinicia.
    exchange = await ch.declare_exchange(
        "events",
        aio_pika.ExchangeType.TOPIC,
        durable=True,
    )

    # -------------------------------------------------------------------------
    # 3) DECLARAR COLA DURABLE PARA EL BRIDGE
    # -------------------------------------------------------------------------
    # - durable=True: la cola sobrevive reinicios de Rabbit.
    # Nota: para garantizar no perder mensajes, también depende de:
    # - publisher: mensajes "persistent"
    # - y confirmaciones/ACK como aquí.
    queue = await ch.declare_queue("bridge-queue", durable=True)

    # -------------------------------------------------------------------------
    # 4) BIND: ESCUCHAR TODOS LOS EVENTOS task.*
    # -------------------------------------------------------------------------
    # Esto significa:
    # - routing_key="task.*" recibirá: task.created, task.updated, task.deleted...
    # - pero NO: task.user.created (porque ahí serían dos puntos: task.user.*)
    await queue.bind(exchange, routing_key="task.*")

    logger.info("[BRIDGE] conectado a RabbitMQ, escuchando routing_key=task.* en queue=bridge-queue")

    # -------------------------------------------------------------------------
    # 5) LOOP DE CONSUMO CONTINUO
    # -------------------------------------------------------------------------
    # queue.iterator() crea un iterador async que entrega mensajes según llegan.
    # Mientras el servicio esté levantado, procesa eventos indefinidamente.
    async with queue.iterator() as q:
        async for message in q:
            payload = None
            try:
                # 5.1) Parseo del body del mensaje (bytes -> str -> dict).
                payload = json.loads(message.body.decode("utf-8"))

                # 5.2) Metadatos del evento:
                # - event_type: tipo lógico del evento según tu payload
                # - rk: routing_key real de Rabbit (ej. task.created)
                event_type = payload.get("type", "task.event")
                rk = message.routing_key

                logger.info(f"[BRIDGE] evento recibido: {event_type} rk={rk}")

                # -------------------------------------------------------------
                # A) PUBLICAR EN MQTT
                # -------------------------------------------------------------
                # Publicamos el payload (tal cual) al topic MQTT definido.
                # Backend B escucha este topic y lo transmite por WebSocket
                # hacia el dashboard (realtime).
                mqtt_publish(settings.MQTT_TOPIC, payload)

                # -------------------------------------------------------------
                # B) ENVIAR EMAIL AL ADMIN
                # -------------------------------------------------------------
                # Construimos un subject legible y un body JSON formateado.
                subj = f"[TaskManager] {event_type}"
                body = json.dumps(payload, indent=2, default=str)
                await send_admin_email(subj, body)

                # -------------------------------------------------------------
                # 5.3) ACK: confirmamos a Rabbit que el mensaje fue procesado OK
                # -------------------------------------------------------------
                # Con ACK, Rabbit elimina el mensaje de la cola.
                # Si no haces ACK y el consumer muere, Rabbit reentrega el mensaje.
                await message.ack()

            except Exception as e:
                # Si algo falla (JSON inválido, MQTT caído, etc.)
                # registramos el error + el payload (si alcanzó a parsearse).
                logger.exception(f"[BRIDGE] error procesando mensaje: {e} payload={payload}")

                # Estrategia actual:
                # - ACK igual para evitar loops infinitos (mensaje "venenoso").
                #
                # Alternativa (si quieres reintentos reales):
                # - await message.reject(requeue=True)
                #   pero OJO: si el fallo es permanente, esto cicla infinito.
                try:
                    await message.ack()
                except Exception:
                    # Si incluso ACK falla (muy raro), ignoramos para no romper loop.
                    pass
