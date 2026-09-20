import os

# Configuración desde settings.toml
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
mqtt_broker = os.getenv("MQTT_BROKER")
mqtt_port = int(os.getenv("MQTT_PORT", 1883))
mqtt_username = os.getenv("MQTT_USERNAME", "")
mqtt_password = os.getenv("MQTT_PASSWORD", "")
mqtt_ssl = os.getenv("MQTT_SSL") == "true"

# Hardware adicional: Sensor de llegada y bocina
touch_pin_name = os.getenv("TOUCH_PIN", "A1")
touch_mode = os.getenv("TOUCH_MODE", "digital")
buzzer_pin_name = os.getenv("BUZZER_PIN", "A2")
buzzer_enabled = os.getenv("BUZZER_ENABLED", "true") == "true"

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