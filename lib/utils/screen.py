from adafruit_display_text import label
from adafruit_matrixportal.matrix import Matrix
from adafruit_bitmap_font import bitmap_font
import displayio
import terminalio

# Inicializacion de variables
font = bitmap_font.load_font("/fonts/12-Fixed-SemiCond.bdf")

# Configurar la pantalla
matrix = Matrix(width=128, height=64, bit_depth=1, tile_rows=2)
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