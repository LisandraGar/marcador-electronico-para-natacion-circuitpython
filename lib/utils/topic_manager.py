import json
import utils.config as config
from utils.file_system import guarda_valor, lee_valor
from utils.rtc import init_timer, get_hours, get_minutes, get_seconds, get_ampm
from utils.chrono import (
    start_chrono,
    stop_chrono,
    start_all_chrono,
    stop_all_chrono,
    clr_chrono,
    get_chrono_formatted
)
from utils.buzzer import buzzer


def set_time_topic(msg, mqtt=None):
    timer = msg.split(':', 1)
    hours = int(timer[0])
    minutes = int(timer[1])
    init_timer(hours, minutes, 0)
    
    
def set_temp_topic(msg, mqtt=None):
    guarda_valor('data.txt', 'temp', msg)
    
    
def get_temp():
    temp = lee_valor('data.txt', 'temp')
    return temp if temp else "25"


def set_color_topic(msg, mqtt=None):
    print(f'color: {msg}')
    color = msg[1:]
    guarda_valor('data.txt', 'color', f'0x{color}')
    
    
def get_color():
    color = lee_valor('data.txt', 'color')
    return int(color, 16)


def set_newuser_topic(msg, mqtt=None):
    records = json.loads(lee_valor('data.txt', 'records'))
    records.append(msg)
    records_txt = json.dumps(records)
    guarda_valor('data.txt', 'records', records_txt)


def send_timetemp(mqtt):
    time_data = {
        "hours": get_hours(), "minutes": get_minutes(), 
        "seconds": get_seconds(), "ampm": get_ampm()
    }

    response = {"timedata": time_data, "temp": get_temp()}
    mqtt.publish(config.TOPIC_SENDTIME, json.dumps(response))

    
def get_users_topic(msg, mqtt):
    records_json = lee_valor('data.txt', 'records')
    records = json.loads(records_json)
        
    scores_json = lee_valor('data.txt', 'scores')
    scores = json.loads(scores_json)
        
    response = {"records": records, "scores": scores}
    
    json_txt = json.dumps(response)
    mqtt.publish(config.TOPIC_USERDATA, json_txt)
    
    # Además enviamos el color de pantalla y modo de visualización actual
    mqtt.publish(config.TOPIC_SENDCOLOR, get_color())
    mqtt.publish(config.TOPIC_SCREENTYPE, get_screentype())
    mqtt.publish(config.TOPIC_SENDCHRONO, json.dumps(get_chrono_formatted()))
    
    # Además enviamos la hora y temperatura
    send_timetemp(mqtt)

def record_chrono_stop(id_num, mqtt=None):
    """
    Detiene el cronómetro para el nadador, formatea su tiempo,
    actualiza la lista de records en almacenamiento y la publica por MQTT.
    """
    stopped_single = stop_chrono(id_num)
    
    full_chrono = get_chrono_formatted()
    single_json_txt = json.dumps(stopped_single)
    full_chrono_txt = json.dumps(full_chrono)
    
    try:
        scores_raw = lee_valor('data.txt', 'scores')
        scores = json.loads(scores_raw) if scores_raw else []
    except Exception:
        scores = []
    
    exist = False
    id_str = str(id_num)
    for i, score in enumerate(scores):
        try:
            curr_score = json.loads(score) if isinstance(score, str) else score
            curr_id = str(curr_score.get('id', ''))
            if curr_id == id_str or (curr_id.isdigit() and id_str.isdigit() and int(curr_id) == int(id_str)):
                scores[i] = single_json_txt
                exist = True
                break
            else:
                scores[i] = score if isinstance(score, str) else json.dumps(score)
        except Exception:
            scores[i] = score
    
    if not exist:
        scores.append(single_json_txt)
    
    scores_txt = json.dumps(scores)
    guarda_valor('data.txt', 'scores', scores_txt)
    if mqtt:
        mqtt.publish(config.TOPIC_SENDSCORES, scores_txt)
        mqtt.publish(config.TOPIC_SENDCHRONO, full_chrono_txt)
    return stopped_single

def record_all_chrono_stop(mqtt=None):
    """
    Detiene ambos cronómetros simultáneamente en el mismo instante (mismo tick)
    y luego persiste ambos récords en una sola operación atómica de I/O y MQTT.
    Garantiza cero diferencia temporal inducida por operaciones lentas.
    """
    f1, f2 = stop_all_chrono()

    full_chrono = get_chrono_formatted()
    full_chrono_txt = json.dumps(full_chrono)

    try:
        scores_raw = lee_valor('data.txt', 'scores')
        scores = json.loads(scores_raw) if scores_raw else []
    except Exception:
        scores = []

    def update_in_scores(target_id, data_obj):
        if not target_id:
            return
        single_txt = json.dumps(data_obj)
        target_str = str(target_id)
        for i, s in enumerate(scores):
            try:
                curr = json.loads(s) if isinstance(s, str) else s
                curr_id = str(curr.get('id', ''))
                if curr_id == target_str or (curr_id.isdigit() and target_str.isdigit() and int(curr_id) == int(target_str)):
                    scores[i] = single_txt
                    return
            except Exception:
                pass
        scores.append(single_txt)

    c1_id = full_chrono.get("c1", {}).get("id", "1")
    c2_id = full_chrono.get("c2", {}).get("id", "2")

    update_in_scores(c1_id, f1)
    update_in_scores(c2_id, f2)

    scores_txt = json.dumps(scores)
    guarda_valor('data.txt', 'scores', scores_txt)

    if mqtt:
        mqtt.publish(config.TOPIC_SENDSCORES, scores_txt)
        mqtt.publish(config.TOPIC_SENDCHRONO, full_chrono_txt)

    return f1, f2

def chrono_topic(msg, mqtt):
    msg_pair = msg.split(':', 1)
    command = msg_pair[0]
    payload = msg_pair[1] if len(msg_pair) > 1 else ''
    
    if command == 'play_chrono':
        slot_target = None
        target_id = payload
        if ',' in payload:
            parts = payload.split(',')
            target_id = parts[0].strip()
            if len(parts) > 1 and parts[1].strip() in ('1', '2'):
                slot_target = int(parts[1].strip())
        elif ':' in payload:
            parts = payload.split(':')
            target_id = parts[0].strip()
            if len(parts) > 1 and parts[1].strip() in ('1', '2'):
                slot_target = int(parts[1].strip())
        start_chrono(target_id or '1', slot_num=slot_target)
        buzzer.sound_start()
        if mqtt:
            mqtt.publish(config.TOPIC_SENDCHRONO, json.dumps(get_chrono_formatted()))
    elif command == 'pause_chrono':
        target_id = payload
        if ',' in payload:
            parts = payload.split(',')
            target_id = parts[0].strip()
        elif ':' in payload:
            parts = payload.split(':')
            target_id = parts[0].strip()
        record_chrono_stop(target_id or '1', mqtt)
        buzzer.sound_arrival()
    elif command in ('play_all', 'start_all'):
        # Inicio global simultáneo de dos nadadores (Salida general)
        parts = payload.split(',') if payload else ['1', '2']
        id1 = parts[0].strip() if len(parts) > 0 and parts[0].strip() else '1'
        id2 = parts[1].strip() if len(parts) > 1 and parts[1].strip() else '2'
        start_all_chrono(id1, id2)
        buzzer.sound_start()
        if mqtt:
            mqtt.publish(config.TOPIC_SENDCHRONO, json.dumps(get_chrono_formatted()))
    elif command in ('pause_all', 'stop_all'):
        # Parada global de ambos nadadores simultánea e instantánea
        record_all_chrono_stop(mqtt)
        buzzer.sound_arrival()


def get_scores_topic(msg, mqtt):
    scores = lee_valor('data.txt', 'scores')
    mqtt.publish(config.TOPIC_GETSCORES, scores)
    

def del_score_topic(msg, mqtt=None):
    try:
        val = lee_valor('data.txt', 'scores')
        scores_raw = json.loads(val) if val else []
    except Exception:
        scores_raw = []
    
    nuevos_scores = []
    for score in scores_raw:
        try:
            curr_score = json.loads(score) if isinstance(score, str) else score
            if str(curr_score.get('id', '')) != str(msg):
                nuevos_scores.append(json.dumps(curr_score) if isinstance(curr_score, dict) else score)
        except Exception:
            pass
    
    guarda_valor('data.txt', 'scores', json.dumps(nuevos_scores))
    clr_chrono() # Borramos el cronómetro de la pantalla


def del_record_topic(msg, mqtt):
    try:
        val = lee_valor('data.txt', 'records')
        records_raw = json.loads(val) if val else []
    except Exception:
        records_raw = []
    
    actualizados = []
    for record in records_raw:
        try:
            curr_record = json.loads(record) if isinstance(record, str) else record
            if str(curr_record.get('id', '')) != str(msg):
                actualizados.append(json.dumps(curr_record) if isinstance(curr_record, dict) else record)
        except Exception:
            pass
        
    guarda_valor('data.txt', 'records', json.dumps(actualizados))
    
    # También eliminamos su score (si lo tiene)
    del_score_topic(msg, mqtt)
    

def get_scores():
    try:
        val = lee_valor('data.txt', 'scores')
        scores_raw = json.loads(val) if val else []
    except Exception:
        return []
    
    scores = []
    for score in scores_raw:
        try:
            curr_score = json.loads(score) if isinstance(score, str) else score
            scores.append(curr_score)
        except Exception:
            pass
        
    try:
        scores.sort(key=lambda x: int(x.get("id", 0)))
    except Exception:
        pass
    
    return scores


def set_screentype_topic(msg, mqtt=None):
    guarda_valor('data.txt', 'screen_type', msg)


def get_screentype():
    screen_type = lee_valor('data.txt', 'screen_type')
    return screen_type



# Función encargada de ejecutar el topico correspondiente
def topic_manager(topic, msg, mqtt):
    actions = {
        config.TOPIC_SETTIME: set_time_topic,
        config.TOPIC_SETTEMP: set_temp_topic,
        config.TOPIC_SETCOLOR: set_color_topic,
        config.TOPIC_NEWUSER: set_newuser_topic,
        config.TOPIC_GETUSERS: get_users_topic,
        config.TOPIC_CHRONO: chrono_topic,
        config.TOPIC_GETSCORES: get_scores_topic,
        config.TOPIC_DELSCORE: del_score_topic,
        config.TOPIC_DELRECORD: del_record_topic,
        config.TOPIC_SCREENTYPE: set_screentype_topic
    }
    
    actions[topic](msg, mqtt)
