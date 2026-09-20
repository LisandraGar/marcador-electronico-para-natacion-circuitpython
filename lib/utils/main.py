import os
import time
import board
import json
from adafruit_display_text import label
from adafruit_matrixportal.matrix import Matrix
import displayio
import terminalio
from utils.mqtt_client import MQTTClient
from utils.screen import show_text, show_multiline
from utils.rtc import init_timer, get_hours, get_minutes, get_seconds, get_ampm, get_milliseconds
from utils.topic_manager import get_temp, get_color, get_scores, get_screentype, record_chrono_stop
from utils.file_system import lee_valor
from utils.config import TOPIC_SENDTIME, TOPIC_SENDCHRONO
from utils.chrono import get_chrono_formatted, get_chrono_status
from utils.time_updates import handle_time_updates
from utils.display_content import get_display_content
from utils.touch_sensor import arrival_sensor
from utils.buzzer import buzzer

mqtt_client = MQTTClient()

def main():
    mqtt_client.connect_wifi()
    mqtt_client.setup_mqtt()
    mqtt_client.connect_mqtt()
    
    print("🚀 Iniciando loop principal...")
    
    # Estado inicial
    bandera = True
    m_antes = None
    s_antes = None
    last_reconnect_attempt = 0

    while True:
        try:
            mqtt_client.loop()

            # Comprobar sensor capacitivo sumergible de llegada
            if arrival_sensor.check_arrival():
                if get_chrono_status() == 'started':
                    chrono_now = get_chrono_formatted()
                    active_id = chrono_now.get("id", "0")
                    print(f"🏊 ¡LLEGADA DETECTADA POR SENSOR! Nadador #{active_id}")
                    buzzer.sound_arrival()
                    record_chrono_stop(active_id, mqtt_client)
                else:
                    buzzer.beep(0.08)

            # Agrupamos los datos para que sean fáciles de pasar
            time_data = {
                "hours": get_hours(), "minutes": get_minutes(), 
                "seconds": get_seconds(), "ampm": get_ampm()
            }
            chrono = get_chrono_formatted()
            status = get_chrono_status()
            
            # Solo publicamos la hora si cambia el minuto
            m_antes = handle_time_updates(mqtt_client, time_data["minutes"], m_antes, time_data)

            # Enviamos el estado del cronómetro en cada segundo solo si está activo
            if status == 'started' and s_antes != chrono["ss"]:
                s_antes = chrono
                mqtt_client.publish(TOPIC_SENDCHRONO, json.dumps(chrono))

            # Actualizamos de la pantalla
            scores = get_scores()
            lines = get_display_content(bandera, time_data, chrono, scores, mqtt_client)
            show_multiline(lines, x=0, y=2, color=get_color(), line_spacing=9)

        except Exception as e:
            print(f"Error en main: {e}")
            # Estrategia de reconexión controlada
            if not mqtt_client.connected:
                print("Intentando reconectar...")
                try:
                    mqtt_client.connect_mqtt()
                except Exception as inner_e:
                    print(f"Reconexión fallida: {inner_e}")
                    time.sleep(2) # Evita un bucle de error infinito si el servidor cayó