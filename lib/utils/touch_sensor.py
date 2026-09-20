import board
import supervisor
import utils.config as config

class ArrivalTouchSensor:
    def __init__(self):
        self.device = None
        self.mode = getattr(config, 'touch_mode', 'digital').lower()
        self.pin_name = getattr(config, 'touch_pin_name', 'A1')
        self._last_state = False
        self._last_trigger_ms = 0
        self.cooldown_ms = 1500  # Tiempo mínimo entre paradas para evitar rebotes de agua

        try:
            pin_obj = getattr(board, self.pin_name, None)
            if pin_obj is None:
                print(f"⚠️ Pin de sensor táctil '{self.pin_name}' no existe en este board")
                return

            if self.mode == 'capacitive':
                import touchio
                self.device = touchio.TouchIn(pin_obj)
                print(f"🏊 Sensor capacitivo sumergible inicializado (Modo TouchIO en board.{self.pin_name})")
            else:
                import digitalio
                self.device = digitalio.DigitalInOut(pin_obj)
                self.device.direction = digitalio.Direction.INPUT
                # Sensor digital normalmente en bajo (LOW), pasa a alto (HIGH) al tocar la placa
                try:
                    self.device.pull = digitalio.Pull.DOWN
                except Exception:
                    pass
                print(f"🏊 Sensor de llegada sumergible inicializado (Modo Digital en board.{self.pin_name})")

        except Exception as e:
            print(f"⚠️ No se pudo inicializar el sensor de llegada en {self.pin_name}: {e}")
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

# Instancia singleton para el sistema
arrival_sensor = ArrivalTouchSensor()
