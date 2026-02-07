import asyncio
import json
import paho.mqtt.client as mqtt

from app.core.config import settings
from app.core.ws_manager import ws_manager

def start_mqtt_listener(loop: asyncio.AbstractEventLoop):
    client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        print(
            f"[MQTT-B] connected rc={rc} host={settings.MQTT_HOST}:{settings.MQTT_PORT} "
            f"topic={settings.MQTT_TOPIC}"
        )
        client.subscribe(settings.MQTT_TOPIC)

    def on_message(client, userdata, msg):
        raw = msg.payload.decode("utf-8")
        try:
            payload = json.loads(raw)
            asyncio.run_coroutine_threadsafe(ws_manager.broadcast_json(payload), loop)
        except Exception:
            asyncio.run_coroutine_threadsafe(ws_manager.broadcast_text(raw), loop)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(settings.MQTT_HOST, settings.MQTT_PORT, 60)
    client.loop_start()
    return client
