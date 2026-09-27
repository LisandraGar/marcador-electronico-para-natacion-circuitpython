import os

# Configuración desde settings.toml
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
mqtt_broker = os.getenv("MQTT_BROKER")
mqtt_port = int(os.getenv("MQTT_PORT", 1883))
mqtt_username = os.getenv("MQTT_USERNAME", "")
mqtt_password = os.getenv("MQTT_PASSWORD", "")
mqtt_ssl = os.getenv("MQTT_SSL") == "true"

# Detección y compatibilidad de plataforma de hardware
hardware_target = os.getenv("HARDWARE_TARGET", "auto").lower()

def get_board_pin(pin_name):
    """
    Resuelve de forma robusta un pin en el módulo board de CircuitPython,
    soportando prefijos de hardware tanto para MatrixPortal S3 (A1, A2)
    como para ESP32-S3 DevKitC / PCB_MARCADOR_LISA (IO4, GPIO4, 4, etc.).
    """
    if not pin_name:
        return None
    try:
        import board
    except ImportError:
        return None

    if hasattr(board, pin_name):
        return getattr(board, pin_name)

    # Limpieza de prefijos para evaluar variantes (ej. 'GPIO4' -> 'IO4', '4' -> 'IO4')
    cleaned = str(pin_name).upper().replace("GPIO", "").replace("IO", "").replace("D", "")
    for candidate in [f"IO{cleaned}", f"GPIO{cleaned}", f"D{cleaned}", f"A{cleaned}", cleaned]:
        if hasattr(board, candidate):
            return getattr(board, candidate)
    return None

# Hardware adicional y asignación de pines
default_buzzer = "IO4" if hardware_target == "pcb_lisa" else "A2"
default_touch = "IO15" if hardware_target == "pcb_lisa" else "A1"

touch_pin_name = os.getenv("TOUCH_PIN", default_touch)
touch_mode = os.getenv("TOUCH_MODE", "digital")
buzzer_pin_name = os.getenv("BUZZER_PIN", default_buzzer)
buzzer_enabled = os.getenv("BUZZER_ENABLED", "true") == "true"

# Pines específicos de la tarjeta custom PCB_MARCADOR_LISA (V1.0)
temp_pin_name = os.getenv("TEMP_PIN", "IO5")
rtc_sda_pin_name = os.getenv("RTC_SDA_PIN", "IO8")
rtc_scl_pin_name = os.getenv("RTC_SCL_PIN", "IO9")
btn1_pin_name = os.getenv("BTN_1_PIN", "IO15")  # Pulsador U6
btn2_pin_name = os.getenv("BTN_2_PIN", "IO16")  # Pulsador U7
btn3_pin_name = os.getenv("BTN_3_PIN", "IO17")  # Pulsador U8

# Topics
TOPIC_WILL = "esp32s3/status"
TOPIC_SETTIME = "esp32s3/settime"
TOPIC_SETTEMP = "esp32s3/settemp"
TOPIC_SETCOLOR = "esp32s3/setcolor"
TOPIC_NEWUSER = "esp32s3/new_user"
TOPIC_GETUSERS = "esp32s3/get_users"
TOPIC_USERDATA = "esp32s3/user_data"
TOPIC_SENDTIME = "esp32s3/send_time"
TOPIC_CHRONO = "esp32s3/chrono"
TOPIC_SENDCHRONO = "esp32s3/send_chrono"
TOPIC_GETSCORES = "esp32s3/get_scores"
TOPIC_SENDSCORES = "esp32s3/send_scores"
TOPIC_DELSCORE = "esp32s3/del_score"
TOPIC_DELRECORD = "esp32s3/del_record"
TOPIC_SENDCOLOR = "esp32s3/send_color"
TOPIC_SCREENTYPE = "esp32s3/screen_type"
TOPIC_SENDVIEW = "esp32s3/send_view"