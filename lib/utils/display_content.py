from utils.topic_manager import get_temp, get_screentype
from utils.config import TOPIC_SENDVIEW
import json

seg_antes = 0
index_score = 0
r = None
r_antes = None

def format_record(label, rec):
    if not rec: return label
    return f"{label} {rec['id']}.{rec['hh']:02d}:{rec['mm']:02d}:{rec['ss']:02d}.{rec['ms']:02d}"

def get_display_content(bandera, time_data, chrono, records, mqtt):
    global seg_antes, index_score, r, r_antes

    h, m, s, ampm = time_data["hours"], time_data["minutes"], time_data["seconds"], time_data["ampm"]
    temp = get_temp()

    # Indicador de conectividad: [ON] si MQTT está en línea, [L] si está en modo Local/autónomo
    is_online = bool(mqtt and getattr(mqtt, 'connected', False))
    net_badge = "[ON]" if is_online else "[L]"

    if get_screentype() == 'chrono':
        c1 = chrono.get("c1", chrono)
        c2 = chrono.get("c2", None)

        if c2:
            return [
                f" {h:02d}:{m:02d} {ampm} {temp}°C {net_badge}",
                f"C1: {c1.get('hh', 0):02d}:{c1.get('mm', 0):02d}:{c1.get('ss', 0):02d}.{c1.get('ms', 0):02d}",
                f"C2: {c2.get('hh', 0):02d}:{c2.get('mm', 0):02d}:{c2.get('ss', 0):02d}.{c2.get('ms', 0):02d}"
            ]

        return [
            f" {h:02d}:{m:02d} {ampm} {temp}°C {net_badge}",
            "  Round|HH|MM|SS|MS",
            f"    {chrono.get('id', 0)}  |{chrono.get('hh', 0):02d}|{chrono.get('mm', 0):02d}|{chrono.get('ss', 0):02d}|{chrono.get('ms', 0):02d}"
        ]

    num_rec = len(records)

    if num_rec == 0:
        r = [None, None]
    elif num_rec <= 2:
        index_score = 0
        r = [records[0], records[1] if num_rec == 2 else None]
    else:
        if abs(s - seg_antes) >= 5:
            seg_antes, index_score = s, (index_score + 1) % num_rec
            
        r = [records[index_score], records[(index_score + 1) % num_rec]]

    if r != r_antes:
        r_antes = r
        mqtt.publish(TOPIC_SENDVIEW, json.dumps(r))
        
    return [
        f"{h:02d}:{m:02d} {ampm}  HEAT {temp} {net_badge}",
        format_record("RECORDS", r[0]) if r[0] else "RECORDS",
        format_record("       ", r[1]) if r[1] else ""
    ]