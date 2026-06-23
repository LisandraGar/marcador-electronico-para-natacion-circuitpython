import json
from utils.topic_manager import get_temp
from utils.config import TOPIC_SENDTIME

def handle_time_updates(mqtt, current_m, m_antes, time_data):
    if current_m != m_antes:
        response = {"timedata": time_data, "temp": get_temp()}
        mqtt.publish(TOPIC_SENDTIME, json.dumps(response))
        return current_m
    return m_antes