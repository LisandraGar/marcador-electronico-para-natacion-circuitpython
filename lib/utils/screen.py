from adafruit_display_text import label
from adafruit_matrixportal.matrix import Matrix
from adafruit_bitmap_font import bitmap_font
import displayio
import terminalio

# Inicializacion de variables
font = bitmap_font.load_font("/fonts/12-Fixed-SemiCond.bdf")

import utils.config as config

def create_matrix_display():
    hw = getattr(config, 'hardware_target', 'auto')
    if hw == 'pcb_lisa' or (config.get_board_pin('IO42') is not None and config.get_board_pin('A1') is None):
        try:
            r1 = config.get_board_pin('IO42')
            g1 = config.get_board_pin('IO41')
            b1 = config.get_board_pin('IO40')
            r2 = config.get_board_pin('IO38')
            g2 = config.get_board_pin('IO39')
            b2 = config.get_board_pin('IO37')
            clk = config.get_board_pin('IO2')
            lat = config.get_board_pin('IO47')
            oe = config.get_board_pin('IO14')
            a = config.get_board_pin('IO45')
            b = config.get_board_pin('IO36')
            c = config.get_board_pin('IO48')
            d = config.get_board_pin('IO35')
            if all([r1, g1, b1, r2, g2, b2, clk, lat, oe, a, b, c, d]):
                print("🖥️ Inicializando HUB75 con mapeo de pines dedicado PCB_MARCADOR_LISA...")
                return Matrix(
                    width=128, height=32, bit_depth=1, tile_rows=1,
                    rgb_pins=[r1, g1, b1, r2, g2, b2],
                    clock_pin=clk, latch_pin=lat, output_enable_pin=oe,
                    address_pins=[a, b, c, d]
                )
        except Exception as e:
            pass

    return Matrix(width=128, height=32, bit_depth=1, tile_rows=1)

# Configurar la pantalla
matrix = create_matrix_display()
display = matrix.display

# Función para mostrar texto en la matriz
def show_text(texto, x=0, y=8, color=0xFFFFFF, escala=2):
    # Crear grupo y texto
    grupo = displayio.Group()
    texto_label = label.Label(
        terminalio.FONT,
        text=texto,
        color=color,
        scale=escala
    )
    texto_label.x = x
    texto_label.y = y
    grupo.append(texto_label)

    # Mostrar en pantalla
    display.root_group = grupo
    
def show_multiline(text_lines, x=0, y=4, color=0xFFFFFF, escala=1, line_spacing=12):
    grupo = displayio.Group()
    
    for i, line in enumerate(text_lines):
        texto_label = label.Label(
            font,
            text=line,
            color=color,
            scale=escala
        )
        texto_label.x = x
        texto_label.y = y + 4 + (i * line_spacing) # Cada línea más abajo
        grupo.append(texto_label)
    
    display.root_group = grupo