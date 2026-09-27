import board
import supervisor
import utils.config as config

class ArrivalTouchSensor:
    def __init__(self, pin_name=None, mode=None, label="Sensor 1"):
        self.device = None
        self.label = label
        self.mode = (mode or getattr(config, 'touch_mode', 'digital')).lower()
        self.pin_name = pin_name or getattr(config, 'touch_pin_name', 'IO15')
        self._last_state = False
        self._last_trigger_ms = 0
        self.cooldown_ms = 1500  # Tiempo mínimo entre paradas para evitar rebotes de agua

        try:
            pin_obj = config.get_board_pin(self.pin_name) if hasattr(config, 'get_board_pin') else getattr(board, self.pin_name, None)
            if pin_obj is None:
                print(f"⚠️ Pin de sensor táctil '{self.pin_name}' no existe en este board ({self.label})")
                return

            if self.mode == 'capacitive':
                import touchio
                self.device = touchio.TouchIn(pin_obj)
                print(f"🏊 Botón/Sensor capacitivo inicializado (Modo TouchIO en board.{self.pin_name} - {self.label})")
            else:
                import digitalio
                self.device = digitalio.DigitalInOut(pin_obj)
                self.device.direction = digitalio.Direction.INPUT
                # Sensor digital normalmente en bajo (LOW), pasa a alto (HIGH) al tocar la placa
                try:
                    self.device.pull = digitalio.Pull.DOWN
                except Exception:
                    pass
                print(f"🏊 Botón/Sensor táctil inicializado (Modo Digital en board.{self.pin_name} - {self.label})")

        except Exception as e:
            print(f"⚠️ No se pudo inicializar {self.label} en {self.pin_name}: {e}")
            self.device = None

    def read_raw(self):
        """Lee el estado instantáneo del sensor (True = tocado, False = reposo)"""
        if not self.device:
            return False
        try:
            return bool(self.device.value)
        except Exception:
            return False

    def check_arrival(self):
        """
        Detecta flanco de subida (cuando el nadador hace contacto con la placa).
        Aplica filtro de anti-rebote y enfriamiento para evitar lecturas espurias por oleaje.
        Retorna True únicamente en el instante en que se detecta la llegada.
        """
        if not self.device:
            return False

        current_state = self.read_raw()
        now = supervisor.ticks_ms()

        # Detección de flanco positivo: no estaba tocado y ahora sí
        triggered = False
        if current_state and not self._last_state:
            # Comprobar cooldown
            elapsed = (now - self._last_trigger_ms) & 0x1FFFFFFF
            if elapsed >= self.cooldown_ms:
                self._last_trigger_ms = now
                triggered = True

        self._last_state = current_state
        return triggered

# Instancias para los 3 sensores/botones capacitivos
arrival_sensor = ArrivalTouchSensor(
    pin_name=getattr(config, 'touch_pin_name', 'IO15'),
    mode=getattr(config, 'touch_mode', 'digital'),
    label="Sensor 1 (IO15)"
)
touch_sensor_1 = arrival_sensor  # Alias de compatibilidad

touch_sensor_2 = ArrivalTouchSensor(
    pin_name=getattr(config, 'touch_pin_2_name', 'IO10'),
    mode=getattr(config, 'touch_mode_2', getattr(config, 'touch_mode', 'digital')),
    label="Sensor 2 (IO10)"
)

touch_sensor_3 = ArrivalTouchSensor(
    pin_name=getattr(config, 'touch_pin_3_name', 'IO11'),
    mode=getattr(config, 'touch_mode_3', getattr(config, 'touch_mode', 'digital')),
    label="Sensor 3 (IO11)"
)

touch_sensors = [arrival_sensor, touch_sensor_2, touch_sensor_3]
