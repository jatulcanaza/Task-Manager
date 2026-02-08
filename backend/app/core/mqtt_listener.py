import asyncio
import json
import paho.mqtt.client as mqtt

from app.core.config import settings
from app.core.ws_manager import ws_manager

# -----------------------------------------------------------------------------
# MQTT LISTENER (BACKEND B)
# -----------------------------------------------------------------------------
# Este componente actúa como:
# - Suscriptor MQTT
# - Puente entre MQTT y WebSockets
#
# Rol en la arquitectura:
# RabbitMQ → Bridge → MQTT → ESTE LISTENER → WebSocket → Frontend (dashboard)
#
# Importante:
# - MQTT corre en un hilo propio (loop_start)
# - FastAPI corre sobre un event loop asyncio
# - Por eso se usa run_coroutine_threadsafe
# -----------------------------------------------------------------------------

def start_mqtt_listener(loop: asyncio.AbstractEventLoop):
    """
    Inicializa un listener MQTT y lo conecta con el sistema de WebSockets.

    Parámetros:
    - loop:
        Event loop principal de FastAPI / asyncio.
        Se usa para ejecutar coroutines desde el hilo MQTT.

    Retorna:
    - client:
        Instancia del cliente MQTT activo (útil para shutdown controlado).
    """

    # -------------------------------------------------------------------------
    # 1) CREAR CLIENTE MQTT
    # -------------------------------------------------------------------------
    # Usamos paho-mqtt:
    # - Librería estándar y estable
    # - Corre su propio loop de red en un hilo separado
    client = mqtt.Client()

    # -------------------------------------------------------------------------
    # 2) CALLBACK: CONEXIÓN EXITOSA AL BROKER
    # -------------------------------------------------------------------------
    def on_connect(client, userdata, flags, rc):
        """
        Se ejecuta cuando el cliente se conecta al broker MQTT.

        rc (return code):
        - 0  → conexión exitosa
        - !=0 → error
        """
        print(
            f"[MQTT-B] connected rc={rc} "
            f"host={settings.MQTT_HOST}:{settings.MQTT_PORT} "
            f"topic={settings.MQTT_TOPIC}"
        )

        # Suscribirse al topic definido en settings
        # Aquí llegarán todos los eventos publicados por el Bridge
        client.subscribe(settings.MQTT_TOPIC)

    # -------------------------------------------------------------------------
    # 3) CALLBACK: MENSAJE RECIBIDO
    # -------------------------------------------------------------------------
    def on_message(client, userdata, msg):
        """
        Se ejecuta cada vez que llega un mensaje MQTT.

        Responsabilidad:
        - Decodificar el payload
        - Intentar parsear JSON
        - Emitir el evento por WebSocket a todos los clientes conectados
        """

        # Payload llega como bytes → se decodifica a string
        raw = msg.payload.decode("utf-8")

        try:
            # -------------------------------------------------------------
            # Caso 1: El mensaje es JSON válido
            # -------------------------------------------------------------
            payload = json.loads(raw)

            # broadcast_json es una coroutine asyncio
            # Como MQTT corre en OTRO hilo, usamos:
            # asyncio.run_coroutine_threadsafe
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast_json(payload),
                loop
            )

        except Exception:
            # -------------------------------------------------------------
            # Caso 2: El mensaje NO es JSON
            # -------------------------------------------------------------
            # Fallback defensivo:
            # - Se envía el texto crudo por WebSocket
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast_text(raw),
                loop
            )

    # -------------------------------------------------------------------------
    # 4) REGISTRAR CALLBACKS
    # -------------------------------------------------------------------------
    client.on_connect = on_connect
    client.on_message = on_message

    # -------------------------------------------------------------------------
    # 5) CONECTAR AL BROKER MQTT
    # -------------------------------------------------------------------------
    # keepalive=60:
    # - Intervalo para mantener viva la conexión
    client.connect(
        settings.MQTT_HOST,
        settings.MQTT_PORT,
        60
    )

    # -------------------------------------------------------------------------
    # 6) INICIAR LOOP MQTT EN HILO SEPARADO
    # -------------------------------------------------------------------------
    # loop_start():
    # - Inicia un thread interno
    # - Maneja red y callbacks sin bloquear FastAPI
    client.loop_start()

    # Retornamos el cliente por si se necesita detenerlo luego
    return client
