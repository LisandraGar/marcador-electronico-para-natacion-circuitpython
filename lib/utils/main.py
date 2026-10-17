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
from utils.touch_sensor import arrival_sensor, touch_sensors
from utils.buzzer import buzzer
from utils.buttons import buttons

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

            # Comprobar sensores/botones capacitivos de llegada (Sensor 1 -> Carril 1, Sensor 2 -> Carril 2)
            for idx, sensor in enumerate(touch_sensors, start=1):
                if sensor.check_arrival():
                    if get_chrono_status() == 'started':
                        chrono_now = get_chrono_formatted()
                        target_id = None
                        if idx == 1 and chrono_now.get("c1", {}).get("status") == "started":
                            target_id = chrono_now["c1"]["id"]
                        elif idx == 2 and chrono_now.get("c2", {}).get("status") == "started":
                            target_id = chrono_now["c2"]["id"]
                        else:
                            target_id = chrono_now.get("id", str(idx))

                        print(f"🏊 ¡LLEGADA DETECTADA POR {sensor.label}! Nadador #{target_id}")
                        buzzer.sound_arrival()
                        record_chrono_stop(target_id, mqtt_client)
                    else:
                        buzzer.beep(0.08)

            # Comprobar los 3 pulsadores físicos de la PCB (U6 = Carril 1, U7 = Carril 2, U8 = Control Global)
            b1_press, b2_press, b3_press = buttons.read_buttons()
            chrono_now = get_chrono_formatted()

            if b1_press:
                # Pulsador 1 (U6): Parada individual Carril 1
                c1_data = chrono_now.get("c1", {})
                if c1_data.get("status") == "started":
                    active_id = c1_data.get("id", "1")
                    print(f"🏊 ¡LLEGADA CARRIL 1 (BOTÓN U6)! Nadador #{active_id}")
                    buzzer.sound_arrival()
                    record_chrono_stop(active_id, mqtt_client)
                else:
                    buzzer.beep(0.08)

            if b2_press:
                # Pulsador 2 (U7): Parada individual Carril 2
                c2_data = chrono_now.get("c2", {})
                if c2_data.get("status") == "started":
                    active_id = c2_data.get("id", "2")
                    print(f"🏊 ¡LLEGADA CARRIL 2 (BOTÓN U7)! Nadador #{active_id}")
                    buzzer.sound_arrival()
                    record_chrono_stop(active_id, mqtt_client)
                else:
                    buzzer.beep(0.08)

            if b3_press:
                # Pulsador 3 (U8): Control Global (Salida General / Parada General)
                from utils.chrono import start_all_chrono, stop_all_chrono
                if get_chrono_status() == "started":
                    print("🛑 ¡PARADA GLOBAL POR BOTÓN U8!")
                    c1_data = chrono_now.get("c1", {})
                    c2_data = chrono_now.get("c2", {})
                    if c1_data.get("status") == "started":
                        record_chrono_stop(c1_data.get("id", "1"), mqtt_client)
                    if c2_data.get("status") == "started":
                        record_chrono_stop(c2_data.get("id", "2"), mqtt_client)
                    stop_all_chrono()
                    buzzer.sound_arrival()
                else:
                    print("🚀 ¡SALIDA GLOBAL POR BOTÓN U8!")
                    id1 = chrono_now.get("c1", {}).get("id", "1")
                    id2 = chrono_now.get("c2", {}).get("id", "2")
                    start_all_chrono(id1, id2)
                    buzzer.sound_start()
                    mqtt_client.publish(TOPIC_SENDCHRONO, json.dumps(get_chrono_formatted()))

            # Agrupamos los datos para que sean fáciles de pasar
            time_data = {
                "hours": get_hours(), "minutes": get_minutes(), 
                "seconds": get_seconds(), "ampm": get_ampm()
            }
            chrono = get_chrono_formatted()
            status = get_chrono_status()
            
            # Solo publicamos la hora si cambia el minuto (y actualizamos temperatura desde LM35)
            if m_antes != time_data["minutes"]:
                try:
                    from utils.temp_sensor import temp_sensor
                    from utils.file_system import guarda_valor
                    if temp_sensor.device is not None:
                        real_t = str(temp_sensor.get_temperature_int())
                        guarda_valor('data.txt', 'temp', real_t)
                except Exception:
                    pass
            m_antes = handle_time_updates(mqtt_client, time_data["minutes"], m_antes, time_data)

            # Enviamos el estado del cronómetro en cada segundo solo si está activo
            if status == 'started' and s_antes != chrono["ss"]:
                s_antes = chrono["ss"]
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