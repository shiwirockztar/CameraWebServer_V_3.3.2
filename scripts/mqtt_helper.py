"""
Lightweight MQTT helper wrapper for the face detection script.

This module wraps paho.mqtt.client with a small class that manages connect,
loop and publish. It keeps the face detection code cleaner.

Usage:
  from mqtt_helper import MqttPublisher

  pub = MqttPublisher(host, port, topic, user, password)
  pub.connect()
  pub.loop_start()
  pub.publish(payload)
  pub.loop_stop()
  pub.disconnect()

This module uses paho-mqtt. Install with:
  pip install paho-mqtt
"""

from typing import Optional
import json

try:
    import paho.mqtt.client as mqtt
except Exception:
    mqtt = None


class MqttPublisher:
    def __init__(self, host: str, port: int = 1883, topic: str = 'camera/detections',
                 user: Optional[str] = None, password: Optional[str] = None, qos: int = 0):
        self.host = host
        self.port = port
        self.topic = topic
        self.user = user
        self.password = password
        self.qos = qos
        self._client = None

    def _ensure_client(self):
        if mqtt is None:
            raise RuntimeError('paho-mqtt is not installed; run: pip install paho-mqtt')
        if self._client is None:
            self._client = mqtt.Client()
            if self.user:
                self._client.username_pw_set(self.user, self.password)

    def connect(self, timeout: int = 10):
        self._ensure_client()
        self._client.connect(self.host, self.port, keepalive=timeout)

    def loop_start(self):
        if self._client:
            try:
                self._client.loop_start()
            except Exception:
                pass

    def loop_stop(self):
        if self._client:
            try:
                self._client.loop_stop()
            except Exception:
                pass

    def publish(self, payload, topic: Optional[str] = None, qos: Optional[int] = None):
        self._ensure_client()
        t = topic or self.topic
        q = self.qos if qos is None else qos
        # Accept dicts and convert to JSON string
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload)
        return self._client.publish(t, payload, qos=q)

    def disconnect(self):
        if self._client:
            try:
                self._client.disconnect()
            except Exception:
                pass
