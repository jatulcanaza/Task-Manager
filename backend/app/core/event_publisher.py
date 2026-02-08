import json
import aio_pika
from app.core.config import settings

# -----------------------------------------------------------------------------
# EVENT PUBLISHER (RABBITMQ)
# -----------------------------------------------------------------------------
# Esta clase encapsula toda la lógica de publicación de eventos hacia RabbitMQ.
#
# Rol dentro de la arquitectura:
# - Publica eventos de dominio (ej. task.created, task.updated).
# - Desacopla el core de la aplicación de los consumidores.
# - Implementa comunicación asíncrona basada en eventos.
#
# Flujo típico:
#   Backend A
#     → EventPublisher.publish("task.created", payload)
#     → RabbitMQ (exchange "events", tipo TOPIC)
#     → Consumers (Bridge, analytics, auditoría, etc.)
# -----------------------------------------------------------------------------
class EventPublisher:

    def __init__(self):
        # ---------------------------------------------------------------------
        # Atributos internos (lazy initialization)
        # ---------------------------------------------------------------------
        # _conn:
        #   - Conexión AMQP robusta a RabbitMQ
        #
        # _ch:
        #   - Canal AMQP (ligero, multiplexado sobre la conexión)
        #
        # _exchange:
        #   - Exchange "events" de tipo TOPIC
        #   - Se reutiliza para todas las publicaciones
        self._conn = None
        self._ch = None
        self._exchange = None

    # -------------------------------------------------------------------------
    # CONEXIÓN ROBUSTA A RABBITMQ
    # -------------------------------------------------------------------------
    async def connect(self):
        """
        Inicializa la conexión con RabbitMQ si aún no existe.

        Características clave:
        - Lazy initialization:
            La conexión solo se crea cuando realmente se necesita publicar.
        - connect_robust:
            Maneja reconexiones automáticas ante caídas del broker.
        - Reutilización:
            La misma conexión/canal/exchange se usan para múltiples eventos.
        """

        # Si ya existe conexión, no hacemos nada
        if self._conn:
            return

        # 1) Crear conexión robusta a RabbitMQ
        self._conn = await aio_pika.connect_robust(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            login=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASS,
        )

        # 2) Abrir un canal sobre la conexión
        self._ch = await self._conn.channel()

        # 3) Declarar (o asegurar existencia de) exchange "events"
        #    - Tipo TOPIC: soporta routing keys jerárquicas
        #    - durable=True: sobrevive reinicios de RabbitMQ
        self._exchange = await self._ch.declare_exchange(
            "events",
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

    # -------------------------------------------------------------------------
    # PUBLICACIÓN DE EVENTOS
    # -------------------------------------------------------------------------
    async def publish(self, routing_key: str, payload: dict):
        """
        Publica un evento en RabbitMQ.

        Parámetros:
        - routing_key:
            Clave de enrutamiento (ej. "task.created", "task.updated")
        - payload:
            Contenido del evento (dict serializable a JSON)

        Responsabilidades:
        1) Garantizar conexión activa (connect()).
        2) Serializar el payload a JSON.
        3) Publicar el mensaje en el exchange "events".

        Nota:
        - El publisher NO conoce a los consumidores.
        - El publisher NO espera respuesta (fire-and-forget).
        """

        # Asegura que exista conexión/canal/exchange
        await self.connect()

        # ---------------------------------------------------------------------
        # Serialización del mensaje
        # ---------------------------------------------------------------------
        # default=str:
        # - Permite serializar objetos no JSON (ej. datetime, UUID)
        body = json.dumps(payload, default=str).encode("utf-8")

        # ---------------------------------------------------------------------
        # Construcción del mensaje AMQP
        # ---------------------------------------------------------------------
        msg = aio_pika.Message(
            body=body,
            content_type="application/json"
            # (opcionalmente podrías marcar delivery_mode=PERSISTENT)
        )

        # ---------------------------------------------------------------------
        # Publicación en el exchange con routing key
        # ---------------------------------------------------------------------
        await self._exchange.publish(
            msg,
            routing_key=routing_key
        )


# -----------------------------------------------------------------------------
# INSTANCIA GLOBAL DEL PUBLISHER
# -----------------------------------------------------------------------------
# Se crea una única instancia reutilizable para toda la app.
#
# Ventajas:
# - Evita múltiples conexiones innecesarias
# - Centraliza la publicación de eventos
#
# Uso típico:
#   await publisher.publish("task.created", payload)
publisher = EventPublisher()
