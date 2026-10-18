import os
import time
import supervisor
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
    record_chrono_stop,
    record_all_chrono_stop
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


def ensure_chrono_mode():
    """Asegura que el marcador esté en modo cronómetro si inicia una carrera"""
    if get_screentype() != "chrono":
        set_screentype_topic("chrono")
        mqtt_client.publish(TOPIC_SCREENTYPE, "chrono")


def handle_btn_view():
    """Botón 1: Alterna entre Récords ('show') y Cronómetros ('chrono')"""
    curr_type = get_screentype()
    next_type = "show" if curr_type == "chrono" else "chrono"
    print(f"🖥️ Cambio de visualización a modo: {next_type}")
    set_screentype_topic(next_type)
    buzzer.beep(0.08)
    mqtt_client.publish(TOPIC_SCREENTYPE, next_type)


def handle_btn_global(chrono_now):
    """Botón 2: Inicio o Pausa Global simultánea de ambos carriles"""
    if get_chrono_status() == "started":
        print("🛑 ¡PARADA GLOBAL SIMULTÁNEA!")
        record_all_chrono_stop(mqtt_client)
        buzzer.sound_arrival()
    else:
        print("🚀 ¡INICIO GLOBAL SIMULTÁNEO!")
        id1 = chrono_now.get("c1", {}).get("id", "1")
        id2 = chrono_now.get("c2", {}).get("id", "2")
        start_all_chrono(id1, id2)
        ensure_chrono_mode()
        buzzer.sound_start()
        mqtt_client.publish(TOPIC_SENDCHRONO, json.dumps(get_chrono_formatted()))


def handle_lane_buttons(btn_lane1, btn_lane2, chrono_now):
    """Botones 3 y 4: Control individual o simultáneo por carril"""
    stop_lane1 = btn_lane1 and chrono_now.get("c1", {}).get("status") == "started"
    stop_lane2 = btn_lane2 and chrono_now.get("c2", {}).get("status") == "started"
    start_lane1 = btn_lane1 and chrono_now.get("c1", {}).get("status") != "started"
    start_lane2 = btn_lane2 and chrono_now.get("c2", {}).get("status") != "started"

    # Si ambos llegan en el mismo ciclo, detener ambos con el mismo tick exacto
    if stop_lane1 and stop_lane2:
        print("🏊🏊 ¡LLEGADA SIMULTÁNEA CARRILES 1 Y 2!")
        record_all_chrono_stop(mqtt_client)
        buzzer.sound_arrival()
        return

    # Carril 1 individual
    if stop_lane1:
        active_id = chrono_now.get("c1", {}).get("id", "1")
        print(f"🏊 ¡PAUSA / LLEGADA CARRIL 1! Nadador #{active_id}")
        record_chrono_stop(active_id, mqtt_client)
        buzzer.sound_arrival()
    elif start_lane1:
        active_id = chrono_now.get("c1", {}).get("id", "1")
        print(f"▶️ ¡INICIO CARRIL 1! Nadador #{active_id}")
        start_chrono(active_id, slot_num=1)
        ensure_chrono_mode()
        buzzer.sound_start()
        mqtt_client.publish(TOPIC_SENDCHRONO, json.dumps(get_chrono_formatted()))

    # Carril 2 individual
    if stop_lane2:
        active_id = chrono_now.get("c2", {}).get("id", "2")
        print(f"🏊 ¡PAUSA / LLEGADA CARRIL 2! Nadador #{active_id}")
        record_chrono_stop(active_id, mqtt_client)
        buzzer.sound_arrival()
    elif start_lane2:
        active_id = chrono_now.get("c2", {}).get("id", "2")
        print(f"▶️ ¡INICIO CARRIL 2! Nadador #{active_id}")
        start_chrono(active_id, slot_num=2)
        ensure_chrono_mode()
        buzzer.sound_start()
        mqtt_client.publish(TOPIC_SENDCHRONO, json.dumps(get_chrono_formatted()))


def main():
    # Mensaje inicial inmediato para confirmar encendido de matriz y procesador
    try:
        show_multiline(["  MARCADOR NATACION  ", "CONECTANDO WIFI...   "], x=0, y=2, color=0x00FF88)
    except Exception:
        pass

    try:
        mqtt_client.connect_wifi()
        mqtt_client.setup_mqtt()
        mqtt_client.connect_mqtt()
    except Exception as e:
        print(f"⚠️ Conexión inicial demorada/fallida: {e}")
        try:
            show_multiline(["ERROR RED / MQTT", "INICIANDO LOCAL..."], x=0, y=2, color=0xFF5500)
            time.sleep(1.0)
        except Exception:
            pass

    print("🚀 Iniciando loop principal...")

    bandera = True
    m_antes = None
    s_antes = None
    last_reconnect_attempt = supervisor.ticks_ms()

    while True:
        try:
            if mqtt_client.connected:
                mqtt_client.loop()
            else:
                # Intento de reconexión periódico y no bloqueante cada 15 segundos
                now_ms = supervisor.ticks_ms()
                if (now_ms - last_reconnect_attempt) & 0x1FFFFFFF > 15000:
                    last_reconnect_attempt = now_ms
                    print("🔄 Intentando reconectar a MQTT en segundo plano...")
                    try:
                        mqtt_client.connect_mqtt()
                    except Exception:
                        pass

            # Lectura de los 4 botones físicos del sistema
            b1_press, b2_press, b3_press = buttons.read_buttons()
            s1_press = arrival_sensor.check_arrival()
            s2_press = touch_sensor_2.check_arrival()
            s3_press = touch_sensor_3.check_arrival()

            btn_view = b3_press or s3_press
            btn_global = b2_press
            btn_lane1 = b1_press or s1_press
            btn_lane2 = s2_press

            chrono_now = get_chrono_formatted()

            # BOTÓN 1: Cambiar visualización
            if btn_view:
                handle_btn_view()

            # BOTÓN 2: Inicio y Pausa Global
            if btn_global:
                handle_btn_global(chrono_now)

            # BOTONES 3 y 4: Inicio y Pausa Individual de Carriles
            if btn_lane1 or btn_lane2:
                handle_lane_buttons(btn_lane1, btn_lane2, chrono_now)

            # Agrupamos los datos de tiempo y estado
            time_data = {
                "hours": get_hours(),
                "minutes": get_minutes(),
                "seconds": get_seconds(),
                "ampm": get_ampm(),
            }
            chrono = get_chrono_formatted()
            status = get_chrono_status()

            # Publicación de hora y lectura de temperatura LM35 al cambiar de minuto
            if m_antes != time_data["minutes"]:
                try:
                    from utils.temp_sensor import temp_sensor
                    from utils.file_system import guarda_valor
                    if temp_sensor.device is not None:
                        real_t = str(temp_sensor.get_temperature_int())
                        guarda_valor("data.txt", "temp", real_t)
                except Exception:
                    pass
            m_antes = handle_time_updates(mqtt_client, time_data["minutes"], m_antes, time_data)

            # Transmisión continua de segundos de carrera por MQTT
            if status == "started" and s_antes != chrono["ss"]:
                s_antes = chrono["ss"]
                mqtt_client.publish(TOPIC_SENDCHRONO, json.dumps(chrono))

            # Actualización de la pantalla física en cada ciclo
            scores = get_scores()
            lines = get_display_content(bandera, time_data, chrono, scores, mqtt_client)
            show_multiline(lines, x=0, y=2, color=get_color(), line_spacing=9)

        except Exception as e:
            print(f"Error en main: {e}")
            time.sleep(0.05)