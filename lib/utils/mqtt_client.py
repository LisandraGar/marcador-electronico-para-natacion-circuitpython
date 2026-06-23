import socketpool
import wifi
import ssl
import utils.config as config
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_minimqtt.adafruit_minimqtt import MMQTTException
from utils.topic_manager import topic_manager

class MQTTClient:
    def __init__(self):
        self.mqtt_client = None
        self.connected = False
        
    def connect_wifi(self):
        """Conectar a WiFi"""
        print(f"Conectando a {config.ssid}...")
        wifi.radio.hostname = "ESP32-S3-MQTT"
        wifi.radio.connect(config.ssid, config.password)
        print(f"✅ Conectado a {config.ssid}!")
        print(f"IP: {wifi.radio.ipv4_address}")
    
    def setup_mqtt(self):
        """Configurar cliente MQTT"""
        pool = socketpool.SocketPool(wifi.radio)
        
        # Configuración SSL para HiveMQ Cloud
        ssl_context = None
        if config.mqtt_ssl:
            print("🔐 Configurando SSL...")
            ssl_context = ssl.create_default_context()
            # HiveMQ Cloud usa certificados estándar, no necesita verificación adicional
        
        self.mqtt_client = MQTT.MQTT(
            broker=config.mqtt_broker,
            port=config.mqtt_port,
            username=config.mqtt_username if config.mqtt_username else None,
            password=config.mqtt_password if config.mqtt_password else None,
            socket_pool=pool,
            ssl_context=ssl_context,
            connect_retries=3,
            keep_alive=60,
            is_ssl=config.mqtt_ssl,  # ✅ Importante para MQTT sobre SSL
        )
        
        # Callbacks
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.on_subscribe = self._on_subscribe
        self.mqtt_client.on_unsubscribe = self._on_unsubscribe
        
        # Will message (última voluntad)
        self.mqtt_client.will_set(config.TOPIC_WILL, "offline", retain=True)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker"""
        self.connected = True
        print("✅ Conectado al broker MQTT!")
        
        # Suscribirse a topics
        topics = [config.TOPIC_SETTIME, config.TOPIC_SETTEMP, config.TOPIC_SETCOLOR, config.TOPIC_NEWUSER,
                  config.TOPIC_GETUSERS, config.TOPIC_CHRONO, config.TOPIC_GETSCORES, config.TOPIC_DELSCORE,
                  config.TOPIC_SCREENTYPE, config.TOPIC_DELRECORD]
        for topic in topics:
            client.subscribe(topic)
        
        
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta"""
        self.connected = False
        print("❌ Desconectado del broker MQTT")
    
    def _on_message(self, client, topic, message):
        """Callback cuando llega un mensaje"""
        print(f"📩 Mensaje recibido: {topic} -> {message}")

        # Procesar comandos
        topic_manager(topic, message, self)
        

    def _on_subscribe(self, client, userdata, topic, granted_qos):
        print(f"✅ Suscrito a: {topic}")
    
    def _on_unsubscribe(self, client, userdata, topic, pid):
        print(f"❌ Cancelada suscripción a: {topic}")
    
    def connect_mqtt(self):
        """Conectar al broker MQTT"""
        try:
            print(f"Conectando a MQTT... {config.mqtt_broker}:{config.mqtt_port}")
            self.mqtt_client.connect()
            # Publicar estado online
            self.mqtt_client.publish(config.TOPIC_WILL, "online", retain=True)
        except MMQTTException as e:
            print(f"❌ Error MQTT: {e}")
        except Exception as e:
            print(f"❌ Error general: {e}")
            
    def publish(self, topic, message, retain=False):
        if self.mqtt_client:
            self.mqtt_client.publish(topic, message, retain=retain)
    
    def loop(self, **kwargs):
        """Mantener la conexión MQTT activa"""
        try:
            self.mqtt_client.loop(**kwargs)
        except Exception as e:
            print(f"Error en loop: {e}")
            self.connected = False