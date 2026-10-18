import supervisor
import digitalio
import utils.config as config

class ButtonController:
    """
    Controlador para los tres pulsadores físicos U6, U7 y U8
    presentes en la tarjeta PCB_MARCADOR_LISA (V1.0):
      - U6 -> GPIO15 (Llegada / Toque de nadador de respaldo)
      - U7 -> GPIO16 (Play / Pause cronómetro local)
      - U8 -> GPIO17 (Cambio de modo pantalla 'show' <-> 'chrono')
    
    Conexión física: Un terminal a +3.3V, otro a GPIO (Active-HIGH).
    Requiere activación de resistencia interna Pull-Down en el ESP32-S3.
    """
    def __init__(self):
        self.btn1 = self._init_pin(getattr(config, 'btn1_pin_name', 'IO15'))
        self.btn2 = self._init_pin(getattr(config, 'btn2_pin_name', 'IO16'))
        self.btn3 = self._init_pin(getattr(config, 'btn3_pin_name', 'IO17'))
        self._last_b1 = False
        self._last_b2 = False
        self._last_b3 = False
        self._last_b1_ms = 0
        self._last_b2_ms = 0
        self._last_b3_ms = 0
        self.debounce_ms = 200

    def _init_pin(self, pin_name):
        try:
            pin_obj = config.get_board_pin(pin_name) if hasattr(config, 'get_board_pin') else None
            if pin_obj is not None:
                btn = digitalio.DigitalInOut(pin_obj)
                btn.direction = digitalio.Direction.INPUT
                try:
                    btn.pull = digitalio.Pull.DOWN
                except Exception:
                    pass
                return btn
        except Exception:
            pass
        return None

    def read_buttons(self):
        """
        Retorna una tupla (b1_pressed, b2_pressed, b3_pressed)
        con detección independiente de flancos de subida y filtro anti-rebote por botón.
        """
        now = supervisor.ticks_ms()

        v1 = bool(self.btn1.value) if self.btn1 else False
        v2 = bool(self.btn2.value) if self.btn2 else False
        v3 = bool(self.btn3.value) if self.btn3 else False

        p1 = False
        p2 = False
        p3 = False

        if v1 and not self._last_b1:
            if (now - self._last_b1_ms) & 0x1FFFFFFF >= self.debounce_ms:
                p1 = True
                self._last_b1_ms = now

        if v2 and not self._last_b2:
            if (now - self._last_b2_ms) & 0x1FFFFFFF >= self.debounce_ms:
                p2 = True
                self._last_b2_ms = now

        if v3 and not self._last_b3:
            if (now - self._last_b3_ms) & 0x1FFFFFFF >= self.debounce_ms:
                p3 = True
                self._last_b3_ms = now

        self._last_b1 = v1
        self._last_b2 = v2
        self._last_b3 = v3

        return (p1, p2, p3)

# Instancia singleton para el sistema
buttons = ButtonController()
