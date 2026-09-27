"""
Test Suite completa para circuitpython/lib (Firmware del Marcador de Natación).
Permite verificar la integridad de todos los módulos de 'lib/utils' y librerías
tanto en CI/CD como localmente en PC simulando el entorno de hardware de CircuitPython.

Ejecución:
    python tests/test_lib.py
    o bien:
    pytest
"""

import sys
import os
import json
import tempfile
import unittest
from unittest.mock import MagicMock

# Asegurar que 'lib' esté en sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_DIR = os.path.join(BASE_DIR, "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

# ==============================================================================
# 1. MOCKS DE MÓDULOS DE HARDWARE CIRCUITPYTHON
# ==============================================================================

class MockDirection:
    INPUT = 0
    OUTPUT = 1

class MockPull:
    UP = 0
    DOWN = 1

class MockDigitalInOut:
    def __init__(self, pin):
        self.pin = pin
        self.direction = MockDirection.INPUT
        self.pull = None
        self.value = False

class MockTouchIn:
    def __init__(self, pin):
        self.pin = pin
        self.value = False

class MockGroup:
    def __init__(self):
        self.items = []
    def append(self, item):
        self.items.append(item)

class MockLabel:
    def __init__(self, font, text="", color=0, scale=1):
        self.font = font
        self.text = text
        self.color = color
        self.scale = scale
        self.x = 0
        self.y = 0

class MockMatrix:
    def __init__(self, width=128, height=32, bit_depth=1, tile_rows=1):
        self.width = width
        self.height = height
        self.display = MagicMock()
        self.display.root_group = None

# Inyectar mocks antes de importar módulos de CircuitPython
VALID_PINS = ["A1", "A2", "SDA", "SCL", "IO4", "GPIO4", "IO5", "IO8", "IO9", "IO10", "GPIO10", "IO11", "GPIO11", "IO15", "IO16", "IO17"]
mock_board = MagicMock(spec=VALID_PINS)
mock_board.A1 = "PIN_A1"
mock_board.A2 = "PIN_A2"
mock_board.SDA = "PIN_SDA"
mock_board.SCL = "PIN_SCL"
mock_board.IO4 = "PIN_IO4"
mock_board.GPIO4 = "PIN_GPIO4"
mock_board.IO5 = "PIN_IO5"
mock_board.IO8 = "PIN_IO8"
mock_board.IO9 = "PIN_IO9"
mock_board.IO10 = "PIN_IO10"
mock_board.GPIO10 = "PIN_GPIO10"
mock_board.IO11 = "PIN_IO11"
mock_board.GPIO11 = "PIN_GPIO11"
mock_board.IO15 = "PIN_IO15"
mock_board.IO16 = "PIN_IO16"
mock_board.IO17 = "PIN_IO17"

mock_digitalio = MagicMock()
mock_digitalio.Direction = MockDirection
mock_digitalio.Pull = MockPull
mock_digitalio.DigitalInOut = MockDigitalInOut

mock_touchio = MagicMock()
mock_touchio.TouchIn = MockTouchIn

_current_ticks = [1000]
def _mock_ticks_ms():
    return _current_ticks[0]

mock_supervisor = MagicMock()
mock_supervisor.ticks_ms = _mock_ticks_ms

mock_displayio = MagicMock()
mock_displayio.Group = MockGroup

mock_terminalio = MagicMock()
mock_terminalio.FONT = "TERMINAL_FONT"

mock_matrixportal_matrix = MagicMock()
mock_matrixportal_matrix.Matrix = MockMatrix

mock_display_text_label = MagicMock()
mock_display_text_label.Label = MockLabel

mock_bitmap_font = MagicMock()
mock_bitmap_font.load_font = MagicMock(return_value="BITMAP_FONT")

mock_micropython = MagicMock()
mock_micropython.const = lambda x: x

mock_storage = MagicMock()

class MockAnalogIn:
    def __init__(self, pin):
        self.pin = pin
        self.value = 5557  # ~28.0 °C
        self.reference_voltage = 3.3

mock_analogio = MagicMock()
mock_analogio.AnalogIn = MockAnalogIn

mock_busio = MagicMock()
mock_busio.I2C = MagicMock()

mock_ds1307_mod = MagicMock()
mock_ds1307_inst = MagicMock()
import time
mock_ds1307_inst.datetime = time.struct_time((2026, 9, 26, 14, 30, 0, 5, 269, -1))
mock_ds1307_mod.DS1307 = MagicMock(return_value=mock_ds1307_inst)

# Asignar a sys.modules
MOCKS = {
    'board': mock_board,
    'digitalio': mock_digitalio,
    'touchio': mock_touchio,
    'analogio': mock_analogio,
    'busio': mock_busio,
    'adafruit_ds1307': mock_ds1307_mod,
    'supervisor': mock_supervisor,
    'displayio': mock_displayio,
    'terminalio': mock_terminalio,
    'adafruit_matrixportal': MagicMock(),
    'adafruit_matrixportal.matrix': mock_matrixportal_matrix,
    'adafruit_display_text': MagicMock(),
    'adafruit_display_text.label': mock_display_text_label,
    'adafruit_bitmap_font': MagicMock(),
    'adafruit_bitmap_font.bitmap_font': mock_bitmap_font,
    'adafruit_ticks': MagicMock(),
    'adafruit_connection_manager': MagicMock(),
    'micropython': mock_micropython,
    'storage': mock_storage,
    'socketpool': MagicMock(),
    'wifi': MagicMock(),
    'ssl': MagicMock(),
}

for name, m in MOCKS.items():
    if name not in sys.modules:
        sys.modules[name] = m

# ==============================================================================
# 2. SUITE DE PRUEBAS UNITARIAS PARA UTILS
# ==============================================================================

class TestCircuitPythonLib(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Respaldar contenido original de data.txt
        cls.data_file = os.path.join(BASE_DIR, "data.txt")
        cls.original_data = None
        if os.path.exists(cls.data_file):
            with open(cls.data_file, "r") as f:
                cls.original_data = f.read()

        # Importar módulos de utils tras mockear hardware
        import utils.config as config
        import utils.file_system as file_system
        import utils.rtc as rtc
        import utils.chrono as chrono
        import utils.buzzer as buzzer_mod
        import utils.touch_sensor as touch_mod
        import utils.topic_manager as tm
        import utils.display_content as dc
        import utils.time_updates as tu
        import utils.screen as screen
        import utils.mqtt_client as mqtt_cli
        import utils.buttons as buttons_mod
        import utils.temp_sensor as temp_mod

        cls.config = config
        cls.file_system = file_system
        cls.rtc = rtc
        cls.chrono = chrono
        cls.buzzer_mod = buzzer_mod
        cls.touch_mod = touch_mod
        cls.tm = tm
        cls.dc = dc
        cls.tu = tu
        cls.screen = screen
        cls.mqtt_cli = mqtt_cli
        cls.buttons_mod = buttons_mod
        cls.temp_mod = temp_mod

    @classmethod
    def tearDownClass(cls):
        # Restaurar data.txt exactamente como estaba
        if cls.original_data is not None and os.path.exists(cls.data_file):
            with open(cls.data_file, "w") as f:
                f.write(cls.original_data)

    def test_01_config_defaults(self):
        """Verificar valores predeterminados y variables de configuración"""
        self.assertEqual(self.config.touch_pin_name, "A1")
        self.assertEqual(self.config.touch_mode, "digital")
        self.assertEqual(self.config.touch_pin_2_name, "IO10")
        self.assertEqual(self.config.touch_pin_3_name, "IO11")
        self.assertEqual(self.config.buzzer_pin_name, "A2")
        self.assertTrue(self.config.buzzer_enabled)
        self.assertEqual(self.config.TOPIC_CHRONO, "esp32s3/chrono")
        self.assertEqual(self.config.TOPIC_SENDCHRONO, "esp32s3/send_chrono")

    def test_02_file_system(self):
        """Verificar lectura y escritura con persistencia clave:valor"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tf:
            temp_path = tf.name

        try:
            # Guardar valores
            self.assertTrue(self.file_system.guarda_valor(temp_path, "color", "0xFF0000"))
            self.assertTrue(self.file_system.guarda_valor(temp_path, "temp", "28"))

            # Leer valores
            self.assertEqual(self.file_system.lee_valor(temp_path, "color"), "0xFF0000")
            self.assertEqual(self.file_system.lee_valor(temp_path, "temp"), "28")
            self.assertIsNone(self.file_system.lee_valor(temp_path, "inexistente"))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_03_rtc(self):
        """Verificar inicialización de reloj de software y desglose de horas"""
        _current_ticks[0] = 0
        self.rtc.init_timer(hora=14, minuto=30, segundo=15)

        _current_ticks[0] = 5000  # 5 segundos después
        self.assertEqual(self.rtc.get_seconds(), 20)
        self.assertEqual(self.rtc.get_minutes(), 30)
        self.assertEqual(self.rtc.get_hours(), 2)  # 14h en formato 12h = 2
        self.assertEqual(self.rtc.get_ampm(), "PM")
        self.assertEqual(self.rtc.get_full_time(), "02:30:20")

    def test_04_chrono(self):
        """Verificar arranque, parada, formateo y cálculo de centésimas"""
        self.chrono.clr_chrono()
        self.assertEqual(self.chrono.get_chrono_status(), "stoped")

        _current_ticks[0] = 10000
        self.chrono.start_chrono("5")
        self.assertEqual(self.chrono.get_chrono_status(), "started")

        # Simular avance de 65,430 ms (1m 5s 43cs)
        _current_ticks[0] = 75430
        fmt = self.chrono.get_chrono_formatted()
        self.assertEqual(fmt["id"], "5")
        self.assertEqual(fmt["mm"], 1)
        self.assertEqual(fmt["ss"], 5)
        self.assertEqual(fmt["ms"], 43)

        self.chrono.stop_chrono("5")
        self.assertEqual(self.chrono.get_chrono_status(), "stoped")

    def test_05_touch_sensor(self):
        """Verificar detección de llegada y filtro de rebotes por oleaje"""
        sensor = self.touch_mod.ArrivalTouchSensor()
        self.assertIsNotNone(sensor.device)

        # Estado en reposo
        sensor.device.value = False
        _current_ticks[0] = 1000
        self.assertFalse(sensor.check_arrival())

        # Contacto del nadador (flanco de subida)
        sensor.device.value = True
        _current_ticks[0] = 3000
        self.assertTrue(sensor.check_arrival(), "Debe detectar llegada en el primer flanco de subida")

        # Contacto continuo (sin nuevo flanco)
        _current_ticks[0] = 3100
        self.assertFalse(sensor.check_arrival(), "No debe volver a disparar mientras la placa siga tocada")

        # Suelta y vuelve a tocar dentro del tiempo de enfriamiento (cooldown 1500ms)
        sensor.device.value = False
        _current_ticks[0] = 3500
        sensor.check_arrival()

        sensor.device.value = True
        _current_ticks[0] = 4000  # Solo 1000ms después del trigger anterior (menor a 1500ms)
        self.assertFalse(sensor.check_arrival(), "Debe filtrar rebotes espurios dentro del cooldown")

        # Suelta y vuelve a tocar tras expirar el cooldown
        sensor.device.value = False
        _current_ticks[0] = 5000
        sensor.check_arrival()

        sensor.device.value = True
        _current_ticks[0] = 6000  # 3000ms después (> 1500ms)
        self.assertTrue(sensor.check_arrival(), "Debe detectar nueva llegada tras expirar cooldown")

    def test_06_buzzer(self):
        """Verificar controlador acústico de la bocina"""
        buzzer = self.buzzer_mod.BuzzerController()
        self.assertIsNotNone(buzzer.device)

        buzzer.on()
        self.assertTrue(buzzer.device.value)
        buzzer.off()
        self.assertFalse(buzzer.device.value)

        # Señales compuestas (no deben lanzar excepciones)
        buzzer.sound_start()
        buzzer.sound_arrival()
        self.assertFalse(buzzer.device.value)

    def test_07_topic_manager(self):
        """Verificar procesamiento de tópicos MQTT y registro de paradas"""
        mock_mqtt = MagicMock()

        # Probar set_color
        self.tm.topic_manager("esp32s3/setcolor", "#00FF00", mock_mqtt)
        self.assertEqual(self.tm.get_color(), 0x00FF00)

        # Probar set_temp
        self.tm.topic_manager("esp32s3/settemp", "27", mock_mqtt)
        self.assertEqual(self.tm.get_temp(), "27")

        # Probar inicio de cronómetro por comando MQTT
        self.tm.topic_manager("esp32s3/chrono", "play_chrono:3", mock_mqtt)
        self.assertEqual(self.chrono.get_chrono_status(), "started")

        # Probar parada de cronómetro
        self.tm.topic_manager("esp32s3/chrono", "pause_chrono:3", mock_mqtt)
        self.assertEqual(self.chrono.get_chrono_status(), "stoped")
        self.assertTrue(mock_mqtt.publish.called)

    def test_08_display_content(self):
        """Verificar renderizado visual para modo visualización y modo cronómetro"""
        mock_mqtt = MagicMock()
        time_data = {"hours": 10, "minutes": 15, "seconds": 30, "ampm": "AM"}
        chrono_data = {"id": "1", "hh": 0, "mm": 1, "ss": 23, "ms": 45}

        # Modo visualización estándar
        self.tm.set_screentype_topic("show")
        lines = self.dc.get_display_content(True, time_data, chrono_data, [], mock_mqtt)
        self.assertEqual(len(lines), 3)
        self.assertIn("10:15 AM", lines[0])

        # Modo cronómetro
        self.tm.set_screentype_topic("chrono")
        chrono_lines = self.dc.get_display_content(True, time_data, chrono_data, [], mock_mqtt)
        self.assertEqual(len(chrono_lines), 3)
        self.assertIn("Round|HH|MM|SS|MS", chrono_lines[1])
        self.assertIn("1  |00|01|23|45", chrono_lines[2])

    def test_09_screen(self):
        """Verificar creación de grupos gráficos para la matriz 128x32"""
        self.screen.show_text("HOLA", x=0, y=0)
        self.assertIsNotNone(self.screen.display.root_group)

        self.screen.show_multiline(["LINEA 1", "LINEA 2", "LINEA 3"])
        self.assertEqual(len(self.screen.display.root_group.items), 3)

    def test_10_mqtt_client_structure(self):
        """Verificar inicialización de cliente MQTT"""
        client = self.mqtt_cli.MQTTClient()
        self.assertFalse(client.connected)
        self.assertIsNone(client.mqtt_client)

    def test_11_pin_resolver_and_pcb_config(self):
        """Verificar resolución agnóstica de pines (A1/A2 vs IO4/GPIO4) para PCB_MARCADOR_LISA"""
        # Prueba directa y por variantes de prefijo
        self.assertEqual(self.config.get_board_pin("IO4"), "PIN_IO4")
        self.assertEqual(self.config.get_board_pin("GPIO4"), "PIN_GPIO4")
        self.assertEqual(self.config.get_board_pin("A1"), "PIN_A1")
        self.assertEqual(self.config.get_board_pin("A2"), "PIN_A2")
        self.assertEqual(self.config.get_board_pin("IO15"), "PIN_IO15")
        self.assertEqual(self.config.get_board_pin("IO8"), "PIN_IO8")
        self.assertEqual(self.config.get_board_pin("IO9"), "PIN_IO9")
        self.assertEqual(self.config.get_board_pin("IO10"), "PIN_IO10")
        self.assertEqual(self.config.get_board_pin("GPIO10"), "PIN_GPIO10")
        self.assertEqual(self.config.get_board_pin("IO11"), "PIN_IO11")
        self.assertEqual(self.config.get_board_pin("GPIO11"), "PIN_GPIO11")
        self.assertIsNone(self.config.get_board_pin("PIN_INEXISTENTE_XYZ"))
        self.assertIsNone(self.config.get_board_pin(""))

    def test_12_button_controller(self):
        """Verificar controlador de pulsadores físicos U6, U7, U8 de la PCB"""
        btn_ctrl = self.buttons_mod.ButtonController()
        self.assertIsNotNone(btn_ctrl.btn1)
        self.assertIsNotNone(btn_ctrl.btn2)
        self.assertIsNotNone(btn_ctrl.btn3)

        # Reposo (sin presionar)
        btn_ctrl.btn1.value = False
        btn_ctrl.btn2.value = False
        btn_ctrl.btn3.value = False
        _current_ticks[0] = 1000
        self.assertEqual(btn_ctrl.read_buttons(), (False, False, False))

        # Presión en botón 1 (U6 - Llegada)
        btn_ctrl.btn1.value = True
        _current_ticks[0] = 1500
        self.assertEqual(btn_ctrl.read_buttons(), (True, False, False), "Debe detectar flanco en botón U6")

        # Mantener presionado (no debe volver a disparar)
        _current_ticks[0] = 1550
        self.assertEqual(btn_ctrl.read_buttons(), (False, False, False), "No debe re-disparar mientras siga presionado")

        # Soltar y presionar botón 2 (U7 - Cronómetro) tras expirar debounce
        btn_ctrl.btn1.value = False
        btn_ctrl.btn2.value = True
        _current_ticks[0] = 2000
        self.assertEqual(btn_ctrl.read_buttons(), (False, True, False), "Debe detectar flanco en botón U7")

        # Soltar y presionar botón 3 (U8 - Pantalla)
        btn_ctrl.btn2.value = False
        btn_ctrl.btn3.value = True
        _current_ticks[0] = 2500
        self.assertEqual(btn_ctrl.read_buttons(), (False, False, True), "Debe detectar flanco en botón U8")

    def test_13_lm35_temperature_sensor(self):
        """Verificar lectura y conversión analógica de temperatura LM35 en GPIO05"""
        sensor = self.temp_mod.TemperatureSensor()
        self.assertIsNotNone(sensor.device)
        temp_c = sensor.read_temperature()
        self.assertGreaterEqual(temp_c, 20.0)
        self.assertLessEqual(temp_c, 35.0)
        self.assertEqual(sensor.get_temperature_int(), 28)

    def test_14_hardware_rtc_ds1307(self):
        """Verificar inicialización y sincronización de RTC DS1307 en bus I2C"""
        ds = self.rtc.init_hardware_rtc()
        self.assertIsNotNone(ds)
        # La hora mockeada era 14:30:00 -> 2 PM en formato 12h
        self.assertEqual(self.rtc.get_hours(), 2)
        self.assertEqual(self.rtc.get_minutes(), 30)
        self.assertEqual(self.rtc.get_ampm(), "PM")
        # Forzar sincronización desde MQTT
        self.rtc.init_timer(9, 45, 15)
        self.assertEqual(self.rtc.get_hours(), 9)
        self.assertEqual(self.rtc.get_minutes(), 45)
        self.assertEqual(self.rtc.get_ampm(), "AM")

    def test_15_multiple_capacitive_touch_sensors(self):
        """Verificar soporte y detección independiente de 3 sensores táctiles (IO15, IO10, IO11)"""
        # Verificar instancias exportadas en touch_mod
        self.assertIsNotNone(self.touch_mod.arrival_sensor)
        self.assertIsNotNone(self.touch_mod.touch_sensor_2)
        self.assertIsNotNone(self.touch_mod.touch_sensor_3)
        self.assertEqual(len(self.touch_mod.touch_sensors), 3)

        # Crear sensores para IO10 e IO11 en modo capacitivo
        sensor_io10 = self.touch_mod.ArrivalTouchSensor(pin_name="IO10", mode="capacitive", label="Carril 2")
        sensor_io11 = self.touch_mod.ArrivalTouchSensor(pin_name="IO11", mode="capacitive", label="Carril 3")
        self.assertIsNotNone(sensor_io10.device)
        self.assertIsNotNone(sensor_io11.device)

        # Probar detección independiente en IO10
        sensor_io10.device.value = False
        _current_ticks[0] = 1000
        self.assertFalse(sensor_io10.check_arrival())

        sensor_io10.device.value = True
        _current_ticks[0] = 2000
        self.assertTrue(sensor_io10.check_arrival(), "Debe registrar llegada en Carril 2 (IO10)")

        # Probar detección independiente en IO11
        sensor_io11.device.value = False
        _current_ticks[0] = 2100
        self.assertFalse(sensor_io11.check_arrival())

        sensor_io11.device.value = True
        _current_ticks[0] = 3000
        self.assertTrue(sensor_io11.check_arrival(), "Debe registrar llegada en Carril 3 (IO11)")

if __name__ == "__main__":
    print("\n========================================================")
    print("🏊 EJECUTANDO PRUEBAS DE INTEGRIDAD EN CIRCUITPYTHON/LIB")
    print("========================================================\n")
    unittest.main(verbosity=2)
