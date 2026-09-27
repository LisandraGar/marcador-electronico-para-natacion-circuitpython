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
        self._last_press_ms = 0
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
        con detección de flancos de subida y filtro anti-rebote.
        """
        now = supervisor.ticks_ms()
        if (now - self._last_press_ms) & 0x1FFFFFFF < self.debounce_ms:
            return (False, False, False)

        v1 = bool(self.btn1.value) if self.btn1 else False
        v2 = bool(self.btn2.value) if self.btn2 else False
        v3 = bool(self.btn3.value) if self.btn3 else False

        p1 = v1 and not self._last_b1
        p2 = v2 and not self._last_b2
        p3 = v3 and not self._last_b3

        self._last_b1 = v1
        self._last_b2 = v2
        self._last_b3 = v3

        if p1 or p2 or p3:
            self._last_press_ms = now

        return (p1, p2, p3)

# Instancia singleton para el sistema
buttons = ButtonController()
