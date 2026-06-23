import json
import utils.config as config
from utils.file_system import guarda_valor, lee_valor
from utils.rtc import init_timer, get_hours, get_minutes, get_seconds, get_ampm
from utils.chrono import start_chrono, stop_chrono, clr_chrono, get_chrono_formatted


def set_time_topic(msg, mqtt=None):
    timer = msg.split(':', 1)
    hours = int(timer[0])
    minutes = int(timer[1])
    init_timer(hours, minutes, 0)
    
    
def set_temp_topic(msg, mqtt=None):
    guarda_valor('data.txt', 'temp', msg)
    
    
def get_temp():
    temp = lee_valor('data.txt', 'temp')
    return temp


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
    
    # Además enviamos el color de pantalla
    mqtt.publish(config.TOPIC_SENDCOLOR, get_color())
    
    # Además enviamos la hora y temperatura
    send_timetemp(mqtt)

def chrono_topic(msg, mqtt):
    msg_pair = msg.split(':')
    
    if msg_pair[0] == 'play_chrono':
        start_chrono(msg_pair[1])
    elif msg_pair[0] == 'pause_chrono':
        stop_chrono(msg_pair[1])
        
        time = get_chrono_formatted()
        json_txt = json.dumps(time)
        
        scores = json.loads(lee_valor('data.txt', 'scores'))
        
        exist = False
        for i, score in enumerate(scores):
            curr_score = json.loads(score)
            if curr_score['id'] == msg_pair[1]:
                scores[i] = json_txt
                exist = True
            else:
                scores[i] = score
        
        if not exist:
            scores.append(json_txt)
        
        scores_txt = json.dumps(scores)
        mqtt.publish(config.TOPIC_SENDSCORES, scores_txt)
        guarda_valor('data.txt', 'scores', scores_txt)


def get_scores_topic(msg, mqtt):
    scores = lee_valor('data.txt', 'scores')
    mqtt.publish(config.TOPIC_GETSCORES, scores)
    

def del_score_topic(msg, mqtt=None):
    scores_raw = json.loads(lee_valor('data.txt', 'scores'))
    
    nuevos_scores = []
    for score in scores_raw:
        curr_score = json.loads(score)
        
        if str(curr_score['id']) != msg:
            nuevos_scores.append(json.dumps(curr_score))
    
    guarda_valor('data.txt', 'scores', json.dumps(nuevos_scores))
    clr_chrono() # Borramos el cronómetro de la pantalla


def del_record_topic(msg, mqtt):
    records_raw = json.loads(lee_valor('data.txt', 'records'))
    
    actualizados = []
    for record in records_raw:
        curr_record = json.loads(record)
        
        if str(curr_record['id']) != msg:
            actualizados.append(json.dumps(curr_record))
        
    guarda_valor('data.txt', 'records', json.dumps(actualizados))
    
    # También eliminamos su score (si lo tiene)
    del_score_topic(msg, mqtt)
    

def get_scores():
    scores_raw = json.loads(lee_valor('data.txt', 'scores'))
    
    scores = []
    for score in scores_raw:
        curr_score = json.loads(score)
        scores.append(curr_score)
        
    scores.sort(key=lambda x: int(x["id"]))
    
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
