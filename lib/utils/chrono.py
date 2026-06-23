import supervisor

_inicio_cronometro = 0
_en_marcha = False
_ultimo_raw = 0
_id_num = '0'

def start_chrono(id_num):
    global _inicio_cronometro, _en_marcha, _id_num
    _inicio_cronometro = supervisor.ticks_ms()
    _en_marcha = True
    _id_num = id_num

def stop_chrono(id_num):
    global _en_marcha, _id_num
    _en_marcha = False
    _id_num = id_num

def clr_chrono():
    global _inicio_cronometro, _en_marcha, _ultimo_raw, _id_num
    _inicio_cronometro = 0
    _en_marcha = False
    _ultimo_raw = 0
    _id_num = '0'

def get_chrono_raw():
    global _ultimo_raw
    # Retorna los ms transcurridos desde que se llamó a start_chrono
    if not _en_marcha:
        return _ultimo_raw
    
    ahora = supervisor.ticks_ms()
    # Maneja el desbordamiento (rollover) de ticks_ms automáticamente
    dif = (ahora - _inicio_cronometro) & 0x1FFFFFFF
    _ultimo_raw = dif
    return dif

def get_chrono_formatted():
    total_ms = get_chrono_raw()
    
    ms = (total_ms % 1000) // 10  # Centésimas
    segundos_totales = total_ms // 1000
    
    ss = segundos_totales % 60
    mm = (segundos_totales // 60) % 60
    hh = (segundos_totales // 3600)
    
    # Formato: "{:02d}:{:02d}:{:02d}:{:02d}".format(hh, mm, ss, ms)
    return {
        "hh": hh,
        "mm": mm,
        "ss": ss,
        "ms": ms,
        "id": _id_num
    }

def get_chrono_status():
    global _en_marcha
    if _en_marcha:
        return 'started'
    return 'stoped'

