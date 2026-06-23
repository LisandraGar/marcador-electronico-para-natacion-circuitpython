import supervisor

# Variables de estado
_ms_inicio = 0
_offset_segundos = 0

def init_timer(hora=0, minuto=0, segundo=0):
    global _ms_inicio, _offset_segundos, _pm
    _ms_inicio = supervisor.ticks_ms()
    # Convertimos la hora de inicio a un total de segundos
    _offset_segundos = (hora * 3600) + (minuto * 60) + segundo

def _get_total_seconds():
    """Calcula el total de segundos transcurridos desde el inicio + offset."""
    ms_actual = supervisor.ticks_ms()
    # Diferencia de ms convertida a segundos (entero)
    segundos_transcurridos = (ms_actual - _ms_inicio) // 1000
    return _offset_segundos + segundos_transcurridos

def get_milliseconds():
    """Retorna los milisegundos actuales (0-999)"""
    ms_actual = supervisor.ticks_ms()
    # Calculamos el tiempo total transcurrido en ms
    total_ms = ms_actual - _ms_inicio
    # El residuo de dividir entre 1000 son los ms restantes del segundo actual
    return total_ms % 1000

def get_seconds():
    """Retorna los segundos actuales (0-59)"""
    return _get_total_seconds() % 60

def get_minutes():
    """Retorna los minutos actuales (0-59)"""
    return (_get_total_seconds() // 60) % 60

def get_hours():
    """Retorna las horas actuales (0-12)"""
    hora = (_get_total_seconds() // 3600) % 12
    if hora == 0:
        hora = 12
    return hora

def get_ampm():
    total = _get_total_seconds()
    # Obtenemos la hora en formato 24h (0-23)
    hora_24 = (total // 3600) % 24
    
    return "PM" if hora_24 >= 12 else "AM"

def get_full_time():
    """Retorna una cadena formateada HH:MM:SS"""
    return "{:02d}:{:02d}:{:02d}".format(get_hours(), get_minutes(), get_seconds())