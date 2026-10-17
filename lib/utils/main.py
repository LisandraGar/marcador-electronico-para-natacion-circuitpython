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
from utils.topic_manager import (
    get_temp,
    get_color,
    get_scores,
    get_screentype,
    set_screentype_topic,
    record_chrono_stop
)
from utils.file_system import lee_valor
from utils.config import TOPIC_SENDTIME, TOPIC_SENDCHRONO, TOPIC_SCREENTYPE
from utils.chrono import (
    start_chrono,
    start_all_chrono,
    stop_all_chrono,
    get_chrono_formatted,
    get_chrono_status
)
from utils.time_updates import handle_time_updates
from utils.display_content import get_display_content
from utils.touch_sensor import arrival_sensor, touch_sensor_2, touch_sensor_3, touch_sensors
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

            # Lectura de los 4 botones físicos del sistema:
            # 1. Cambiar visualización (U8 / IO17 o sensor auxiliar IO11)
            # 2. Inicio y pausa global (U7 / IO16)
            # 3. Inicio y pausa 1 - Carril 1 (U6 / IO15)
            # 4. Inicio y pausa 2 - Carril 2 (IO10)
            b1_press, b2_press, b3_press = buttons.read_buttons()
            s1_press = arrival_sensor.check_arrival()
            s2_press = touch_sensor_2.check_arrival()
            s3_press = touch_sensor_3.check_arrival()

            btn_view = b3_press or s3_press
            btn_global = b2_press
            btn_lane1 = b1_press or s1_press
            btn_lane2 = s2_press

            chrono_now = get_chrono_formatted()

            # BOTÓN 1: Cambiar visualización ('show' Récords <-> 'chrono' Cronómetros)
            if btn_view:
                curr_type = get_screentype()
                next_type = "show" if curr_type == "chrono" else "chrono"
                print(f"🖥️ Cambio de visualización a modo: {next_type}")
                set_screentype_topic(next_type)
                buzzer.beep(0.08)
                mqtt_client.publish(TOPIC_SCREENTYPE, next_type)

            # BOTÓN 2: Inicio y Pausa Global (Ambos cronómetros simultáneamente)
            if btn_global:
                if get_chrono_status() == "started":
                    print("🛑 ¡PARADA GLOBAL!")
                    c1_data = chrono_now.get("c1", {})
                    c2_data = chrono_now.get("c2", {})
                    if c1_data.get("status") == "started":
                        record_chrono_stop(c1_data.get("id", "1"), mqtt_client)
                    if c2_data.get("status") == "started":
                        record_chrono_stop(c2_data.get("id", "2"), mqtt_client)
                    stop_all_chrono()
                    buzzer.sound_arrival()
                    mqtt_client.publish(TOPIC_SENDCHRONO, json.dumps(get_chrono_formatted()))
                else:
                    print("🚀 ¡INICIO GLOBAL SIMULTÁNEO!")
                    id1 = chrono_now.get("c1", {}).get("id", "1")
                    id2 = chrono_now.get("c2", {}).get("id", "2")
                    start_all_chrono(id1, id2)
                    if get_screentype() != "chrono":
                        set_screentype_topic("chrono")
                        mqtt_client.publish(TOPIC_SCREENTYPE, "chrono")
                    buzzer.sound_start()
                    mqtt_client.publish(TOPIC_SENDCHRONO, json.dumps(get_chrono_formatted()))

            # BOTÓN 3: Inicio y Pausa 1 (Carril 1)
            if btn_lane1:
                c1_data = chrono_now.get("c1", {})
                active_id = c1_data.get("id", "1")
                if c1_data.get("status") == "started":
                    print(f"🏊 ¡PAUSA / LLEGADA CARRIL 1! Nadador #{active_id}")
                    buzzer.sound_arrival()
                    record_chrono_stop(active_id, mqtt_client)
                else:
                    print(f"▶️ ¡INICIO CARRIL 1! Nadador #{active_id}")
                    start_chrono(active_id, slot_num=1)
                    if get_screentype() != "chrono":
                        set_screentype_topic("chrono")
                        mqtt_client.publish(TOPIC_SCREENTYPE, "chrono")
                    buzzer.sound_start()
                    mqtt_client.publish(TOPIC_SENDCHRONO, json.dumps(get_chrono_formatted()))

            # BOTÓN 4: Inicio y Pausa 2 (Carril 2)
            if btn_lane2:
                c2_data = chrono_now.get("c2", {})
                active_id = c2_data.get("id", "2")
                if c2_data.get("status") == "started":
                    print(f"🏊 ¡PAUSA / LLEGADA CARRIL 2! Nadador #{active_id}")
                    buzzer.sound_arrival()
                    record_chrono_stop(active_id, mqtt_client)
                else:
                    print(f"▶️ ¡INICIO CARRIL 2! Nadador #{active_id}")
                    start_chrono(active_id, slot_num=2)
                    if get_screentype() != "chrono":
                        set_screentype_topic("chrono")
                        mqtt_client.publish(TOPIC_SCREENTYPE, "chrono")
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