import board
import time
import digitalio
import utils.config as config

class BuzzerController:
    def __init__(self):
        self.device = None
        self.enabled = getattr(config, 'buzzer_enabled', True)
        pin_name = getattr(config, 'buzzer_pin_name', 'A2')

        if not self.enabled:
            print("🔊 Bocina deshabilitada en configuración")
            return

        try:
            pin_obj = getattr(board, pin_name, None)
            if pin_obj is not None:
                self.device = digitalio.DigitalInOut(pin_obj)
                self.device.direction = digitalio.Direction.OUTPUT
                self.device.value = False
                print(f"🔊 Bocina/Buzzer inicializado exitosamente en pin board.{pin_name}")
            else:
                print(f"⚠️ Pin de bocina '{pin_name}' no existe en este board")
        except Exception as e:
            print(f"⚠️ No se pudo inicializar la bocina en pin {pin_name}: {e}")
            self.device = None

    def on(self):
        if self.device:
            self.device.value = True

    def off(self):
        if self.device:
            self.device.value = False

    def beep(self, duration_s=0.1):
        if self.device:
            try:
                self.on()
                time.sleep(duration_s)
                self.off()
            except Exception as e:
                print(f"Error en beep: {e}")

    def sound_start(self):
        """Señal acústica para el inicio de carrera (pitido firme de largada)"""
        print("🔊 Señal acústica: ¡Salida de competencia!")
        self.beep(0.35)

    def sound_arrival(self):
        """Señal acústica cuando el nadador toca la placa de llegada"""
        print("🔊 Señal acústica: ¡Llegada confirmada!")
        if not self.device:
            return
        for _ in range(2):
            self.beep(0.15)
            time.sleep(0.08)

# Instancia singleton para el sistema
buzzer = BuzzerController()
