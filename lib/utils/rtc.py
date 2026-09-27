import time
import supervisor
import utils.config as config

# Variables de estado
_ms_inicio = 0
_offset_segundos = 0
_ds1307 = None

def init_hardware_rtc():
    """
    Inicializa el módulo de reloj en tiempo real físico DS1307 (U5)
    en el bus I2C mapeado según el esquemático:
      - SDA -> GPIO08 (ESP32-S3 Pin 12)
      - SCL -> GPIO09 (ESP32-S3 Pin 15)
    """
    global _ds1307
    try:
        import busio
        scl_pin = config.get_board_pin(getattr(config, 'rtc_scl_pin_name', 'IO9'))
        sda_pin = config.get_board_pin(getattr(config, 'rtc_sda_pin_name', 'IO8'))
        if scl_pin is not None and sda_pin is not None:
            i2c = busio.I2C(scl_pin, sda_pin)
            import adafruit_ds1307
            _ds1307 = adafruit_ds1307.DS1307(i2c)
            now = _ds1307.datetime
            init_timer(now.tm_hour, now.tm_min, now.tm_sec, sync_chip=False)
            print(f"⏰ RTC DS1307 conectado en hardware (Hora leída: {now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d})")
            return _ds1307
    except Exception as e:
        # Fallback silencioso si no hay chip físico o no hay batería
        _ds1307 = None
    return None

def init_timer(hora=0, minuto=0, segundo=0, sync_chip=True):
    global _ms_inicio, _offset_segundos
    _ms_inicio = supervisor.ticks_ms()
    # Convertimos la hora de inicio a un total de segundos
    _offset_segundos = (hora * 3600) + (minuto * 60) + segundo

    # Si hay chip físico DS1307 disponible y se solicita, sincronizamos el registro RTC
    if sync_chip and _ds1307 is not None:
        try:
            current = None
            try:
                current = _ds1307.datetime
            except Exception:
                pass
            _ds1307.datetime = time.struct_time((
                current.tm_year if current else 2026,
                current.tm_mon if current else 9,
                current.tm_mday if current else 26,
                hora, minuto, segundo,
                current.tm_wday if current else 0,
                -1, -1
            ))
            print(f"⏰ Hora guardada en hardware RTC DS1307: {hora:02d}:{minuto:02d}:{segundo:02d}")
        except Exception:
            pass

# Inicialización automática al cargar el módulo
init_hardware_rtc()

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