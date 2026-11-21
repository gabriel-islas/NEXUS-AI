# NEXUS-AI 8 — Tiny Tapeout GlobalFoundries

**Proyecto:** acelerador aritmético neuronal compacto INT4, con MAC firmado, acumulador firmado de 8 bits, saturación y función ReLU. Se basa en la plantilla GF Verilog suministrada por el alumno para IEEE Open Silicon Bootcamp 2026.

**Restricciones fijas:** `tiles: "1x1"`, **8 entradas** (`ui_in[7:0]`), **8 salidas** (`uo_out[7:0]`). Los 8 `uio` permanecen deshabilitados. Se usan además los pines **dedicados** `clk`, `rst_n` y `ena` de la interfaz Tiny Tapeout. Todos los registros principales son de 8 bits o menos; el sumador temporal usa **9 bits internos** para detectar saturación, sin utilizar pines adicionales.

**Precaución:** `1x1` es la configuración solicitada, **no una certificación de que el diseño quepa**. Se requiere que `gds` termine correctamente en GitHub Actions. La demostración Python y las pruebas Cocotb no reemplazan esta comprobación física.

## Funciones

- `LOAD_X`: guarda un entero de 4 bits con signo (de -8 a +7).
- `LOAD_W`: guarda un entero de 4 bits con signo (de -8 a +7).
- `MAC`: calcula `acc = saturate8(acc + x*w)`, con saturación en `[-128, +127]`.
- `CLEAR`: limpia acumulador y operandos.
- La salida es `ReLU(acc) = max(0, acc)`, un entero de 0 a 127.
- Cada comando se acepta cuando `STROBE` pasa de 0 a 1 **y el flanco es muestreado por `clk`**. Mantener `STROBE=1` no ejecuta repetidamente el comando.

## Asignación de los 8 bits de entrada

| Bits | Señal | Función |
|---|---|---|
| 7:6 | CMD | 00=LOAD_X, 01=LOAD_W, 10=MAC, 11=CLEAR |
| 5 | STROBE | Enviar comando: pulso bajo-alto-bajo sincronizado |
| 4 | RES | Reservado, dejar en 0 |
| 3:0 | DATA | Entero INT4 con complemento a dos (`0000`=0, `0111`=7, `1000`=-8, `1111`=-1) |

`uo_out[7:0]` entrega el valor de salida ReLU en binario, sin pines de estado adicionales. `uio_out=0`, `uio_oe=0`.

### Secuencia ejemplo: 3 × 2 = 6

Un comando utiliza dos ciclos o más con `STROBE=0`, seguido de dos con `STROBE=1`, y finalmente uno o más con `STROBE=0` (para impedir dudas de sincronización).

| Operación | CMD | DATA | ui_in con STROBE=0 | ui_in con STROBE=1 | Resultado tras flanco |
|---|---|---|---|---|---|
| CLEAR | 11 | 0 | `0xC0` | `0xE0` | 0 |
| LOAD_X | 00 | 3 | `0x03` | `0x23` | 0 |
| LOAD_W | 01 | 2 | `0x42` | `0x62` | 0 |
| MAC | 10 | 0 | `0x80` | `0xA0` | 6 |
| MAC de nuevo | 10 | 0 | `0x80` | `0xA0` | 12 |

Nota: enviar directamente `0xA0` repetidamente sin soltar STROBE produce **un solo MAC**, no varios.

## Archivos

- `src/project.v`: módulo sintetizable `tt_um_nexus_ai8` (código principal).
- `info.yaml`: nombre, pines, reloj nominal de 1 MHz y tile `1x1`.
- `test/tb.v`: testbench para Cocotb.
- `test/test.py`: pruebas funcionales, signo, ReLU, saturación, reset, habilitación y STROBE.
- `tools/demo.py`: demostración local Python con operaciones y resultados.
- `tools/check_model.py`: pruebas de modelo independiente en Python (no RTL).
- `docs/info.md`: descripción para la página del proyecto.
- `.github/workflows/`: workflows originales para simulación, GDS y documentación.
- `src/config.json`: configuración física original del template, sin cambios.

## Cómo subir a tu repositorio existente

1. Descarga y descomprime este ZIP.
2. En la **raíz** del repositorio que ya creaste desde `ttgf-verilog-template`, copia los archivos y carpetas **dentro** de `NEXUS-AI8`, no la carpeta completa.
3. Reemplaza `src/project.v`, `info.yaml`, `test/tb.v`, `test/test.py`, `README.md` y `docs/info.md`.
4. Conserva `.github/workflows/`, `src/config.json` y `test/Makefile` del ZIP. Haz commit.
5. En **Actions** revisa `test` y luego `gds`. Si uno falla, **no presentes el proyecto como validado**.
6. Antes de enviar a fabricación, sustituye `author` por el nombre del equipo, y considera personalizar `top_module` con tu usuario GitHub para que sea único en el shuttle; modifica a la vez `src/project.v`, `test/tb.v` e `info.yaml`.

## Pruebas en Ubuntu

Prueba local del modelo de referencia (sin simulador Verilog):

```bash
python3 tools/demo.py
python3 tools/check_model.py
```

Simulación REAL del RTL con Cocotb + Icarus Verilog:

```bash
sudo apt install iverilog make
python3 -m venv .venv
source .venv/bin/activate
pip install -r test/requirements.txt
cd test
make
```

Los tests de Cocotb también corren con GitHub Actions (`test`). Para evaluar **el área real del tile `1x1`** se necesita el workflow `gds`.

## Limitaciones

Este diseño realiza la operación aritmética de una neurona. **No identifica imágenes, voz, personas ni obstáculos de forma autónoma**. Un procesador externo debe proporcionar los operandos y decidir qué significan los resultados. No es un modelo de IA entrenable completo.

La saturación evita desbordamiento aritmético del acumulador de 8 bits. La precisión es INT4 y el máximo valor visible por ReLU es 127.
