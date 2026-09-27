# DOCUMENTACIÓN TÉCNICA DEL ESQUEMÁTICO: PCB_MARCADOR_LISA (V1.0)
**Proyecto de Grado / Tesis:** Marcador Electrónico para Natación  
**Autor:** Lisandra García  
**Fecha de Revisión Esquemática:** 25 de Septiembre de 2026  
**Herramienta de Diseño:** EasyEDA (EasyEDA.com) — Formato A4, Hoja 1 de 1  
**Placa Diseñada:** `PCB_MARCADOR_LISA` (V1.0 / Board1)  

---

## 1. Resumen Ejecutivo y Alcance

El presente documento técnico describe exhaustivamente el circuito esquemático correspondiente a la tarjeta electrónica de circuito impreso (**PCB**) diseñada a medida: **`PCB_MARCADOR_LISA` (Versión 1.0)**. 

Este diseño de hardware representa una evolución crítica en el proyecto de tesis, permitiendo la transición desde una placa comercial de prototipado rápido (**Adafruit MatrixPortal S3**) hacia una **solución de hardware dedicada, modular, robusta e industrializable**. La PCB integra el procesamiento principal, los adaptadores de nivel para la pantalla matricial, la transducción analógica de temperatura, el mantenimiento horario autónomo por batería, la señalización acústica y visual para los nadadores y los jueces, y una botonera física de control local.

```mermaid
graph TD
    subgraph ALIMENTACION ["Sistema de Potencia"]
        VIN["Fuente Externa 5V DC"] --> RAIL_5V["Riel +5V Principal"]
        RAIL_5V --> ESP_5V["ESP32-S3 (Pin 21 - 5V0)"]
        ESP_5V --> REG_3V3["LDO Interno 3.3V"]
        REG_3V3 --> RAIL_3V3["Riel +3.3V Lógico"]
        RAIL_5V --> BUZZ_VCC["BUZZER1 (+5V)"]
        RAIL_5V --> U2_VCC["U2: 74HC245 (VCC=5V)"]
        RAIL_5V --> U3_VCC["U3: 74HC245 (VCC=5V)"]
    end

    subgraph MCU ["Unidad de Procesamiento Central (ESP32-S3 DevKitC-1)"]
        ESP32["ESP32-S3 Microcontroller<br/>Wi-Fi 2.4GHz + MQTT + CircuitPython"]
    end

    subgraph DISPLAY ["Subsistema de Despliegue HUB75 (Matriz LED RGB)"]
        U2["U2: 74HC245N<br/>Level Shifter 3.3V->5V<br/>(Datos RGB + CLK + ADDR_B)"]
        U3["U3: 74HC245N<br/>Level Shifter 3.3V->5V<br/>(Direcciones A,C,D,E + LAT + OE)"]
        J2["J2: Conector IDC 2x8<br/>Cabezal HUB75 (5V)"]
        R4["R4: 10kΩ Pull-Up (3.3V)<br/>Protección Anti-Glitches OE"]
    end

    subgraph PERIFERICOS ["Subsistemas de Entrada / Salida"]
        BUZZ["BUZZER1 + LED1<br/>Driver NPN Q1 (MMBT4401)<br/>R1 (1kΩ), R2 (1kΩ), R3 (51Ω)"]
        LM35["U4: Sensor LM35<br/>Salida Analógica 10mV/°C"]
        DS1307["U5: RTC DS1307<br/>Bus I2C (SDA, SCL) + Pila Backup"]
        BUTTONS["Pulsadores Físicos U6, U7, U8<br/>Active-HIGH a +3.3V"]
    end

    %% Conexiones
    ESP32 -->|GPIO4 (Digital OUT)| BUZZ
    LM35 -->|GPIO5 (ADC1_CH4)| ESP32
    DS1307 <-->|GPIO8: SDA, GPIO9: SCL (I2C)| ESP32
    BUTTONS -->|GPIO15, 16, 17 (Digital IN)| ESP32

    ESP32 -->|GPIO2, 42, 41, 40, 39, 38, 37, 36| U2
    ESP32 -->|GPIO35, 45, 48, 47, 21, 14| U3
    R4 -.->|Pull-up| U3
    U2 -->|Lógica 5V| J2
    U3 -->|Lógica 5V| J2
```

---

## 2. Ficha Técnica del Hardware

| Parámetro | Especificación |
|---|---|
| **Denominación del Esquemático** | `Schematic1` / `PCB_MARCADOR_LISA` |
| **Versión / Revisión** | V1.0 (2026-09-25) |
| **Microcontrolador Central (U1)** | Espressif ESP32-S3 DevKitC-1 (DIP-44, 2x22 pines, 2.54 mm) |
| **Frecuencia de CPU** | 240 MHz (Dual Core Xtensa 32-bit LX7) |
| **Conectividad Inalámbrica** | Wi-Fi 802.11 b/g/n (2.4 GHz) + Bluetooth 5.0 LE |
| **Interfaz de Pantalla (J2)** | Conector estándar HUB75 (IDC macho de 16 pines, 2x8) |
| **Adaptadores de Nivel Lógico (U2, U3)**| 2x 74HC245N (Transceptores Octales con salida tri-estado, DIP-20) |
| **Rango de Multiplexado de Matriz** | Compatible con 1/16 scan (A, B, C, D) y 1/32 scan (A, B, C, D, E) |
| **Alarma Acústica (BUZZER1)** | Zumbador piezoeléctrico/electromagnético 5V excitado por NPN MMBT4401 |
| **Indicador Óptico Local (LED1)** | Diodo LED rojo/verde en paralelo con resistencia limitadora de 51 Ω |
| **Transductor de Temperatura (U4)** | Sensor analógico de precisión LM35 (VCC=3.3V, salida a canal ADC) |
| **Reloj de Tiempo Real (U5)** | Módulo RTC DS1307 con interfaz I2C y batería de respaldo CR2032 |
| **Pulsadores de Operación (U6, U7, U8)**| 3x Pulsadores táctiles momentáneos (Active-HIGH a 3.3V) |
| **Tensión de Entrada Principal** | +5.0 V DC (suministro común para ESP32, Matriz, Buffers y Buzzer) |
| **Tensión Lógica de Periféricos** | +3.3 V DC (generada por el regulador integrado del ESP32-S3) |

---

## 3. Asignación Maestra de Pines del ESP32-S3 (U1)

El esquemático utiliza un módulo **ESP32-S3-DevKitC-1** en encapsulado de 44 pines (22 pines por lado). A continuación se documenta la distribución y función de cada terminal:

### 3.1. Pines del Costado Izquierdo (Pines 1 a 22)

| Pin U1 | Nombre Pin | Red Esquemática | Tipo / Dirección | Dispositivo Destino | Descripción Funcional |
|:---:|:---:|:---:|:---:|:---:|:---|
| **1** | `3V3` | NC | Salida | — | Salida regulada de 3.3V del DevKit. |
| **2** | `3V3` | NC | Salida | — | Salida regulada de 3.3V del DevKit. |
| **3** | `RST` | NC | Entrada | — | Reset / Enable del chip. |
| **4** | `GPIO04` | *Línea Buzzer* | Digital OUT | Base Q1 / LED1 | **Disparo acústico de largada y llegada + LED testigo**. |
| **5** | `GPIO05` | *Línea LM35* | Analógico IN | Pin 2 LM35 (OUT) | **Entrada ADC1_CH4 para telemetría de temperatura**. |
| **6** | `GPIO06` | NC | — | — | Pin libre / reserva. |
| **7** | `GPIO07` | NC | — | — | Pin libre / reserva. |
| **8** | `GPIO15` | *Línea U6* | Digital IN | Pulsador U6 | **Botón 1 de usuario (Active-HIGH a +3.3V)**. |
| **9** | `GPIO16` | *Línea U7* | Digital IN | Pulsador U7 | **Botón 2 de usuario (Active-HIGH a +3.3V)**. |
| **10** | `GPIO17` | *Línea U8* | Digital IN | Pulsador U8 | **Botón 3 de usuario (Active-HIGH a +3.3V)**. |
| **11** | `GPIO18` | NC | — | — | Pin libre / reserva. |
| **12** | `GPIO08` | *Línea I2C SDA* | I/O Bidireccional | Pin 3 DS1307 | **Línea de datos serie I2C (SDA) para el RTC**. |
| **13** | `GPIO03` | NC | — | — | Pin libre / reserva. |
| **14** | `GPIO46` | NC | — | — | Pin libre / reserva. |
| **15** | `GPIO09` | *Línea I2C SCL* | Salida Clock | Pin 4 DS1307 | **Línea de reloj serie I2C (SCL) para el RTC**. |
| **16** | `GPIO10` | NC | — | — | Pin libre / reserva. |
| **17** | `GPIO11` | NC | — | — | Pin libre / reserva. |
| **18** | `GPIO12` | NC | — | — | Pin libre / reserva. |
| **19** | `GPIO13` | NC | — | — | Pin libre / reserva. |
| **20** | `GPIO14` | `OE_3V` | Digital OUT | U3: Pin 9 (A7) | **Habilitación de salida (OE) de la matriz HUB75**. |
| **21** | `5V0` | `+5V` | Entrada Alimentación | Riel +5V DC | **Entrada de alimentación principal del sistema (5V)**. |
| **22** | `GND` | `GND` | Masa | Plano de Tierra | Referencia común de 0V. |

### 3.2. Pines del Costado Derecho (Pines 23 a 44)

| Pin U1 | Nombre Pin | Red Esquemática | Tipo / Dirección | Dispositivo Destino | Descripción Funcional |
|:---:|:---:|:---:|:---:|:---:|:---|
| **23** | `GND` | NC / GND | Masa | — | Terminal de masa del DevKit. |
| **24** | `TX` | NC | Salida Serie | — | UART0 TX (programación/debug USB-Serial). |
| **25** | `RX` | NC | Entrada Serie | — | UART0 RX (programación/debug USB-Serial). |
| **26** | `GPIO01` | NC | — | — | Pin libre / reserva. |
| **27** | `GPIO02` | `CLK_3V` | Digital OUT | U2: Pin 8 (A6) | **Señal de reloj de píxeles (CLK) para la matriz**. |
| **28** | `GPIO42` | `R1_3V` | Digital OUT | U2: Pin 2 (A0) | **Dato color Rojo superior (R1) - HUB75**. |
| **29** | `GPIO41` | `G1_3V` | Digital OUT | U2: Pin 3 (A1) | **Dato color Verde superior (G1) - HUB75**. |
| **30** | `GPIO40` | `B1_3V` | Digital OUT | U2: Pin 4 (A2) | **Dato color Azul superior (B1) - HUB75**. |
| **31** | `GPIO39` | `G2_3V` | Digital OUT | U2: Pin 5 (A3) | **Dato color Verde inferior (G2) - HUB75**. |
| **32** | `GPIO38` | `R2_3V` | Digital OUT | U2: Pin 6 (A4) | **Dato color Rojo inferior (R2) - HUB75**. |
| **33** | `GPIO37` | `B2_3V` | Digital OUT | U2: Pin 7 (A5) | **Dato color Azul inferior (B2) - HUB75**. |
| **34** | `GPIO36` | `ADDRB_3V` | Digital OUT | U2: Pin 9 (A7) | **Línea de dirección B de fila (ADDR_B) - HUB75**. |
| **35** | `GPIO35` | `ADDRD_3V` | Digital OUT | U3: Pin 4 (A2) | **Línea de dirección D de fila (ADDR_D) - HUB75**. |
| **36** | `GPIO00` | NC | — | — | Pin de arranque / Boot strapping. |
| **37** | `GPIO45` | `ADDRA_3V` | Digital OUT | U3: Pin 5 (A3) | **Línea de dirección A de fila (ADDR_A) - HUB75**. |
| **38** | `GPIO48` | `ADDRC_3V` | Digital OUT | U3: Pin 6 (A4) | **Línea de dirección C de fila (ADDR_C) - HUB75**. |
| **39** | `GPIO47` | `LAT_3V` | Digital OUT | U3: Pin 7 (A5) | **Señal de enganche / Latch (LAT/STB) - HUB75**. |
| **40** | `GPIO21` | `ADDRE_3V` | Digital OUT | U3: Pin 8 (A6) | **Línea de dirección E de fila (ADDR_E) - HUB75**. |
| **41** | `GPIO20` | NC | — | — | Pin libre / reserva. |
| **42** | `GPIO19` | NC | — | — | Pin libre / reserva. |
| **43** | `GND` | NC / GND | Masa | — | Terminal de masa. |
| **44** | `GND` | NC / GND | Masa | — | Terminal de masa. |

---

## 4. Análisis Detallado por Subsistemas

### 4.1. Subsistema de Pantalla LED (HUB75) y Shifters de Nivel 74HC245N

Las pantallas LED basadas en el protocolo **HUB75** operan internamente con niveles lógicos estándar **TTL/CMOS de 5.0 V**. Si bien muchas matrices reconocen señales de 3.3 V directamente en tramos cortos de cinta plana, en ambientes reales con cables largos o ruido electromagnético esto provoca pérdida de paquetes de reloj, parpadeos (*flicker*) o líneas fantasma.

Para solventar esta debilidad de manera profesional, el diseño implementa dos circuitos integrados **74HC245N** (U2 y U3) como **separadores y elevadores de nivel lógico unidireccionales (3.3V → 5.0V)**:

1. **Configuración de Control de U2 y U3:**
   - **`VCC` (Pin 20):** Conectado al riel de **+5V**.
   - **`GND` (Pin 10):** Conectado al plano de masa común.
   - **`DIR` (Pin 1):** Conectado rígidamente a **+5V** (Nivel ALTO), lo que fuerza la dirección de flujo de datos exclusivamente de las entradas **Port A (pines 2-9)** hacia las salidas **Port B (pines 11-18)**.
   - **`OE#` (Pin 19):** Conectado directamente a **GND** (Nivel BAJO), manteniendo las salidas de 5V permanentemente activas y de baja impedancia.

#### Tabla de Enrutamiento: U2 (74HC245N - Datos y Reloj)

| Entrada 3.3V (U2) | Pin U2 | Señal Origen (ESP32) | Salida 5.0V (U2) | Pin U2 | Señal Destino (J2 HUB75) | Función |
|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **A0** | 2 | `R1_3V` (GPIO42) | **B0** | 18 | `M1_R1` (Pin 1) | Datos Rojo fila sup. |
| **A1** | 3 | `G1_3V` (GPIO41) | **B1** | 17 | `M1_G1` (Pin 2) | Datos Verde fila sup. |
| **A2** | 4 | `B1_3V` (GPIO40) | **B2** | 16 | `M1_B1` (Pin 3) | Datos Azul fila sup. |
| **A3** | 5 | `G2_3V` (GPIO39) | **B3** | 15 | `M1_G2` (Pin 6) | Datos Verde fila inf. |
| **A4** | 6 | `R2_3V` (GPIO38) | **B4** | 14 | `M1_R2` (Pin 5) | Datos Rojo fila inf. |
| **A5** | 7 | `B2_3V` (GPIO37) | **B5** | 13 | `M1_B2` (Pin 7) | Datos Azul fila inf. |
| **A6** | 8 | `CLK_3V` (GPIO02) | **B6** | 12 | `CLK` (Pin 13) | Reloj de desplazamiento |
| **A7** | 9 | `ADDRB_3V` (GPIO36) | **B7** | 11 | `M1_B` (Pin 10) | Dirección multiplexado B |

#### Tabla de Enrutamiento: U3 (74HC245N - Direccionamiento y Control)

| Entrada 3.3V (U3) | Pin U3 | Señal Origen (ESP32) | Salida 5.0V (U3) | Pin U3 | Señal Destino (J2 HUB75) | Función |
|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **A0** | 2 | `GND` | **B0** | 18 | NC | Canal no utilizado (A0 fijado a GND) |
| **A1** | 3 | `GND` | **B1** | 17 | NC | Canal no utilizado (A1 fijado a GND) |
| **A2** | 4 | `ADDRD_3V` (GPIO35) | **B2** | 16 | `M1_D` (Pin 12) | Dirección multiplexado D |
| **A3** | 5 | `ADDRA_3V` (GPIO45) | **B3** | 15 | `M1_A` (Pin 9) | Dirección multiplexado A |
| **A4** | 6 | `ADDRC_3V` (GPIO48) | **B4** | 14 | `M1_C` (Pin 11) | Dirección multiplexado C |
| **A5** | 7 | `LAT_3V` (GPIO47) | **B5** | 13 | `LAT` (Pin 14) | Enganche de fila (Latch/Strobe) |
| **A6** | 8 | `ADDRE_3V` (GPIO21) | **B6** | 12 | `M1_E` (Pin 8) | Dirección multiplexado E (1/32 scan) |
| **A7** | 9 | `OE_3V` (GPIO14) | **B7** | 11 | `OE` (Pin 15) | Habilitación de salida (Display ON/OFF) |

#### Circuito Anti-Flicker de la Señal OE (R4)
En la entrada A7 de U3 (línea `OE_3V`), se incorpora una resistencia **R4 de 10 kΩ conectada como Pull-Up al riel de +3.3V**.
- **Comportamiento en Reset/Arranque:** Durante el encendido del microcontrolador, los pines GPIO entran en modo de alta impedancia (Tri-State). Sin esta resistencia, la línea flotaría y podría hacer que los controladores de corriente de la matriz enciendan LEDs al azar, generando destellos molestos. R4 fuerza la línea a nivel ALTO (+3.3V), garantizando que la salida `OE` de U3 esté en ALTO (matriz completamente apagada) hasta que el firmware tome el control explícito del pin GPIO14.

---

### 4.2. Subsistema Acústico y Óptico (Buzzer + LED Indicador)

El reglamento de la FINA (World Aquatics) y los estándares de natación competitiva exigen una señal sonora clara tanto para la salida de la prueba como para la confirmación de llegada a la placa de toque.

```
       +5V
        │
     ┌──┴──┐
     │ (+) │
     │BUZZ1│
     │ (-) │
     └──┬──┘
        │ Collector
        ├─── Q1 (MMBT4401 NPN)
        │    │ Emitter
        │    └── GND
        │
       Base
        │
       [R2: 1kΩ]
        │
GPIO4 ──┼──────────[R1: 1kΩ]─── GND
        │
       [R3: 51Ω]
        │
      (Anode)
       [LED1]
      (Cathode)
        │
       GND
```

#### Elementos y Parámetros del Circuito:
1. **Transistor Conmutador (Q1 - MMBT4401):**
   - Transistor bipolar NPN en encapsulado SMD SOT-23 ($I_{C,\max} = 600\text{ mA}$, $V_{CEO} = 40\text{ V}$).
   - Configurado en conmutación por el lado bajo (*low-side switch*). Su colector conmuta el terminal negativo del zumbador a masa cuando la base recibe polarización directa.
2. **Resistencia de Base (R2 - 1 kΩ):**
   - Limita la corriente que entrega el pin GPIO4 del ESP32 a la unión base-emisor:
     $$I_B = \frac{V_{OH} - V_{BE}}{R_2} = \frac{3.3\text{ V} - 0.7\text{ V}}{1000\ \Omega} = 2.6\text{ mA}$$
   - Una corriente de base de 2.6 mA asegura que el transistor entre en saturación profunda ($V_{CE(sat)} \approx 0.1\text{ V}$), garantizando máxima potencia acústica en el zumbador.
3. **Resistencia de Pull-Down (R1 - 1 kΩ):**
   - Drena cualquier carga remanente en la línea y mantiene el transistor en corte ($V_{BE} = 0\text{ V}$) si el pin GPIO4 está en alta impedancia, evitando zumbidos involuntarios al arrancar.
4. **Indicador Lumínico Testigo (LED1 y R3 - 51 Ω):**
   - En paralelo con el circuito del transistor se encuentra una rama compuesta por una resistencia de **51 Ω (R3)** y el diodo **LED1**, cuyo cátodo se conecta a masa.
   - Proporciona una señalización visual simultánea con la bocina, de gran utilidad en pruebas ruidosas o para nadadores con discapacidad auditiva.

---

### 4.3. Subsistema de Medición Térmica Ambiental (LM35)

Para el monitoreo continuo de las condiciones ambientales del recinto de la piscina, el diseño incorpora un sensor analógico **LM35** (U4):
- **Pin 1 (VCC):** Conectado al riel de **+3.3V**.
- **Pin 3 (GND):** Conectado al plano de **GND**.
- **Pin 2 (OUT):** Conectado a **GPIO05** del ESP32-S3 (Canal ADC1_CH4).

#### Función de Transferencia:
El LM35 entrega una tensión proporcional a la temperatura en grados Celsius:
$$V_{OUT}(T) = 10\text{ mV/}^\circ\text{C} \times T(^\circ\text{C})$$
- A $20^\circ\text{C} \rightarrow V_{OUT} = 200\text{ mV} = 0.20\text{ V}$
- A $28^\circ\text{C} \rightarrow V_{OUT} = 280\text{ mV} = 0.28\text{ V}$
- A $40^\circ\text{C} \rightarrow V_{OUT} = 400\text{ mV} = 0.40\text{ V}$

#### ⚠️ Nota Crítica de Ingeniería (Para defensa de Tesis):
> La hoja de datos oficial de Texas Instruments especifica una tensión de alimentación mínima para el LM35 de **4.0 V** (rango típico de 4V a 30V). En el esquemático actual, el pin VCC del LM35 está conectado a **+3.3V**. Aunque muchos lotes de LM35 operan de manera lineal hasta 30-35 °C a 3.3V, se recomienda en futuras revisiones alimentar el sensor desde el riel de **+5V** para garantizar exactitud metrológica absoluta. Dado que la salida del LM35 nunca superará 1.0 V para el rango acuático (10 °C a 45 °C), su salida de voltaje es 100% segura para el conversor analógico-digital (ADC) de 3.3V del ESP32-S3.

---

### 4.4. Subsistema de Reloj de Tiempo Real (RTC DS1307)

El marcador requiere mantener la hora exacta incluso si se interrumpe el suministro de energía o se pierde la conexión a Internet / broker MQTT:
- **Módulo:** DS1307 (U5) con zócalo para pila de botón CR2032 (3V litio).
- **Alimentación:** Pin 1 = GND, Pin 2 = VCC (+3.3V).
- **Bus I2C:**
  - **`SDA` (Pin 3):** Conectado a **GPIO08** (U1 Pin 12).
  - **`SCL` (Pin 4):** Conectado a **GPIO09** (U1 Pin 15).

Alimentar el módulo DS1307 con 3.3V en este diseño adapta de forma directa los niveles de voltaje del bus I2C con las entradas lógicas del ESP32-S3, prescindiendo de circuitos adaptadores bidireccionales adicionales.

---

### 4.5. Interfaz de Botonera Local (U6, U7, U8)

Para permitir el control manual del sistema en el borde de la piscina (o como respaldo si falla la red inalámbrica), se incluyen tres pulsadores de 4 pines:
- **U6:** Conectado a **GPIO15** (U1 Pin 8).
- **U7:** Conectado a **GPIO16** (U1 Pin 9).
- **U8:** Conectado a **GPIO17** (U1 Pin 10).

#### Configuración Eléctrica y Lógica:
- Un extremo de cada pulsador está conectado al riel de **+3.3V**.
- Al presionarse el botón, el pin GPIO correspondiente pasa a nivel **ALTO (3.3V)** (*Lógica Active-HIGH*).
- **Requisito de Firmware:** El esquemático no cuenta con resistencias externas de pull-down para U6-U8. En consecuencia, el microcontrolador **debe configurar obligatoriamente sus resistencias internas de pull-down** (`digitalio.Pull.DOWN` en CircuitPython) en los tres pines para evitar falsos disparos por líneas flotantes.

#### Mapeo de Funciones Recomendado para Natación:
1. **Botón U6 (GPIO15):** Respaldo Manual de Llegada / Toque de Nadador (*Stop Chrono*).
2. **Botón U7 (GPIO16):** Inicio / Pausa local del Cronómetro (*Play / Pause*).
3. **Botón U8 (GPIO17):** Alternar vista de pantalla entre modo General (`show`) y modo Cronómetro (`chrono`).

---

### 4.6. Conector J2 (Cabezal HUB75)

El conector J2 es un cabezal macho de 2x8 pines (IDC-16). La siguiente tabla muestra la correspondencia exacta entre las líneas del conector físico y las redes del esquemático:

```
          J2 (Conector HUB75)
         ┌───────────────┐
   R1  1 │ ○  ○ │ 2   G1
   B1  3 │ ○  ○ │ 4   GND
   R2  5 │ ○  ○ │ 6   G2
   B2  7 │ ○  ○ │ 8   E
    A  9 │ ○  ○ │ 10  B
    C 11 │ ○  ○ │ 12  D
  CLK 13 │ ○  ○ │ 14  LAT
   OE 15 │ ○  ○ │ 16  GND
         └───────────────┘
```

| Pin J2 | Señal HUB75 | Red PCB | Origen Lógico (Buffer) | Pin ESP32-S3 |
|:---:|:---:|:---:|:---:|:---:|
| **1** | R1 | `M1_R1` | U2: Pin 18 (B0) | GPIO42 |
| **2** | G1 | `M1_G1` | U2: Pin 17 (B1) | GPIO41 |
| **3** | B1 | `M1_B1` | U2: Pin 16 (B2) | GPIO40 |
| **4** | GND | `GND` | Plano de Masa | GND |
| **5** | R2 | `M1_R2` | U2: Pin 14 (B4) | GPIO38 |
| **6** | G2 | `M1_G2` | U2: Pin 15 (B3) | GPIO39 |
| **7** | B2 | `M1_B2` | U2: Pin 13 (B5) | GPIO37 |
| **8** | E | `M1_E` | U3: Pin 12 (B6) | GPIO21 |
| **9** | A | `M1_A` | U3: Pin 15 (B3) | GPIO45 |
| **10** | B | `M1_B` | U2: Pin 11 (B7) | GPIO36 |
| **11** | C | `M1_C` | U3: Pin 14 (B4) | GPIO48 |
| **12** | D | `M1_D` | U3: Pin 16 (B2) | GPIO35 |
| **13** | CLK | `CLK` | U2: Pin 12 (B6) | GPIO02 |
| **14** | LAT | `LAT` | U3: Pin 13 (B5) | GPIO47 |
| **15** | OE | `OE` | U3: Pin 11 (B7) | GPIO14 |
| **16** | GND | `GND` | Plano de Masa | GND |

---

## 5. Comparativa Crítica: Prototipo Inicial vs. PCB Dedicada

| Característica | Prototipo Comercial (MatrixPortal S3) | PCB Dedicada (`PCB_MARCADOR_LISA` V1.0) |
|---|---|---|
| **Enfoque de Proyecto** | Placa de experimentación educativa / Maker | Hardware a medida optimizado para tesis de grado |
| **Shifter de Nivel HUB75** | Integrado en placa comercial (74HCT245 interno) | 2x 74HC245N discretos reemplazables en zócalo DIP-20 |
| **Driver de Buzzer** | Salida analógica básica o puerto STEMMA | Driver de potencia con transistor NPN Q1 y LED testigo |
| **Pines del Buzzer** | Pin genérico `board.A2` (o `board.D2`) | Pin dedicado **`GPIO04`** |
| **Medición de Temperatura** | Requiere cableado externo en protoboard | Conexión directa del sensor LM35 al pin **`GPIO05`** |
| **RTC Hardware** | I2C en pines predeterminados STEMMA (SDA=IO15, SCL=IO16) | Conexión directa en pines dedicados **`GPIO08` (SDA)** y **`GPIO09` (SCL)** |
| **Pulsadores Físicos** | Botones UP/DOWN miniatura del MatrixPortal | 3x Pulsadores táctiles dedicados en **`GPIO15`**, **`GPIO16`**, **`GPIO17`** |
| **Confiabilidad Mecánica** | Susceptible a desconexión accidental de cables jumper | Pistas de cobre directas en placa impresa, conector IDC HUB75 firme |

---

## 6. Guía de Adaptación del Firmware (CircuitPython)

Para operar de forma óptima con la tarjeta `PCB_MARCADOR_LISA`, se debe configurar el entorno de software de la siguiente manera:

### 6.1. Configuración de `settings.toml`
```toml
# ==========================================
# Configuración para PCB_MARCADOR_LISA V1.0
# ==========================================
CIRCUITPY_WIFI_SSID = "TU_RED_WIFI"
CIRCUITPY_WIFI_PASSWORD = ""

MQTT_BROKER = "90ee163ce96e47e2ab0300d92f22e9d5.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "marcador_esp32"
MQTT_PASSWORD = ""
MQTT_SSL = "true"

# Pines de la PCB a medida
BUZZER_PIN = "IO4"
TOUCH_PIN = "IO15"       # Botón U6 configurado como respaldo de llegada
TOUCH_MODE = "digital"

# Módulos adicionales de la PCB
TEMP_PIN = "IO5"
RTC_SDA_PIN = "IO8"
RTC_SCL_PIN = "IO9"
BTN_1_PIN = "IO15"
BTN_2_PIN = "IO16"
BTN_3_PIN = "IO17"
```

### 6.2. Inicialización de la Matriz HUB75 en CircuitPython
Si se usa `rgbmatrix.RGBMatrix` de forma directa sin la capa MatrixPortal:

```python
import board
import displayio
import rgbmatrix
import framebufferio

displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=128,
    height=32,
    bit_depth=1,
    rgb_pins=[
        board.IO42, board.IO41, board.IO40,  # R1, G1, B1
        board.IO38, board.IO39, board.IO37   # R2, G2, B2
    ],
    clock_pin=board.IO2,                     # CLK
    latch_pin=board.IO47,                    # LAT
    output_enable_pin=board.IO14,            # OE
    address_pins=[
        board.IO45, board.IO36, board.IO48, board.IO35  # A, B, C, D
    ],
)
display = framebufferio.FramebufferDisplay(matrix)
```

---

## 7. Lista de Materiales (Bill of Materials - BOM)

| Referencia | Componente / Valor | Encapsulado | Cantidad | Función Principal |
|---|---|---|:---:|---|
| **U1** | ESP32-S3 DevKitC-1 | DIP-44 (2x22, 2.54mm) | 1 | Microcontrolador central Wi-Fi/BLE |
| **U2, U3** | 74HC245N | DIP-20 (o SOIC-20) | 2 | Level shifters octales 3.3V a 5V para HUB75 |
| **U4** | LM35 Precision Centigrade Sensor | TO-92 | 1 | Transductor de temperatura ambiente |
| **U5** | Módulo RTC DS1307 | Módulo de 4 pines (con pila) | 1 | Reloj de tiempo real autónomo (I2C) |
| **U6, U7, U8** | Pulsadores Momentáneos Táctiles | THT 4-pin 6x6mm | 3 | Botonera de control manual y respaldo |
| **Q1** | MMBT4401 (NPN, 600mA, 40V) | SOT-23 (o 2N4401 TO-92) | 1 | Conmutador de potencia para la bocina |
| **BUZZER1** | Zumbador Acústico 5V | Circular 12mm | 1 | Emisor de señales acústicas de salida y llegada |
| **LED1** | Diodo LED 3mm / 5mm (Rojo/Verde) | THT 2-pin | 1 | Indicador visual de disparo de bocina |
| **R1, R2** | Resistencia 1.0 kΩ (1/4W, 5%) | Axial / 0805 | 2 | Pull-down y limitación de base para Q1 |
| **R3** | Resistencia 51 Ω (1/4W, 5%) | Axial / 0805 | 1 | Resistencia limitadora de corriente para LED1 |
| **R4** | Resistencia 10 kΩ (1/4W, 5%) | Axial / 0805 | 1 | Pull-up anti-flicker para señal OE (3.3V) |
| **J2** | Conector Macho Acodado 2x8 | IDC 16 pines (2.54mm) | 1 | Conexión hacia cinta plana de la matriz HUB75 |
