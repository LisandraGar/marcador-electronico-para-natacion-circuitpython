import analogio
import utils.config as config

class TemperatureSensor:
    """
    Controlador para el sensor analógico de temperatura LM35 (U4)
    presente en el esquemático PCB_MARCADOR_LISA (V1.0):
      - Pin VCC (1) -> +3.3V
      - Pin OUT (2) -> GPIO05 (ESP32-S3 Pin 5 / Canal ADC1_CH4)
      - Pin GND (3) -> GND

    Función de transferencia de LM35:
      V_OUT = 10 mV / °C = 0.010 V / °C
      Temp (°C) = V_OUT / 0.010 = V_OUT * 100
    """
    def __init__(self):
        self.device = None
        self.pin_name = getattr(config, 'temp_pin_name', 'IO5')
        self._last_temp = 25.0
        self._init_sensor()

    def _init_sensor(self):
        try:
            pin_obj = config.get_board_pin(self.pin_name) if hasattr(config, 'get_board_pin') else None
            if pin_obj is not None:
                self.device = analogio.AnalogIn(pin_obj)
                print(f"🌡️ Sensor de temperatura analógico LM35 inicializado en board.{self.pin_name}")
            else:
                print(f"⚠️ Pin de sensor LM35 '{self.pin_name}' no disponible en este board")
        except Exception as e:
            print(f"⚠️ No se pudo inicializar LM35 en {self.pin_name}: {e}")
            self.device = None

    def read_temperature(self):
        """
        Lee el valor analógico del conversor ADC, promedia 10 muestras para filtrar
        ruido eléctrico y retorna la temperatura en grados Celsius (°C).
        """
        if not self.device:
            return self._last_temp

        try:
            total_raw = sum(self.device.value for _ in range(10)) / 10.0
            ref_voltage = getattr(self.device, "reference_voltage", 3.3) or 3.3
            volts = (total_raw * ref_voltage) / 65535.0
            temp_c = volts * 100.0

            # Filtro de sanidad para rango acuático verosímil (10°C a 45°C)
            if 10.0 <= temp_c <= 50.0:
                self._last_temp = round(temp_c, 1)

            return self._last_temp
        except Exception:
            return self._last_temp

    def get_temperature_int(self):
        """Retorna la temperatura redondeada como número entero"""
        return int(round(self.read_temperature()))

# Instancia singleton para el sistema
temp_sensor = TemperatureSensor()
