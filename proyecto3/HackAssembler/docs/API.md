# API Reference — HackAssembler

**Organización de Computadores 2026-1**  
**Proyecto 3**  
Universidad EAFIT — Ingeniería de Sistemas

---

## Módulos

El proyecto está compuesto por cuatro módulos Python con responsabilidades claramente separadas:

| Módulo | Responsabilidad |
|--------|----------------|
| `Parser.py` | Lectura y clasificación de instrucciones `.asm` |
| `SymbolTable.py` | Gestión de símbolos y variables |
| `Code.py` | Traducción de mnemónicos a bits |
| `HackAssembler.py` | Orquestación del ensamblado (dos pasadas) |
| `HackDisassembler.py` | Traducción inversa de binario a assembler |

---

## Parser

### Constantes de tipo de instrucción

```python
A_INSTRUCTION     = "A_INSTRUCTION"     # @valor o @simbolo
C_INSTRUCTION     = "C_INSTRUCTION"     # dest=comp;jump
SHIFT_INSTRUCTION = "SHIFT_INSTRUCTION" # dest=reg<<1 / dest=reg>>1
L_INSTRUCTION     = "L_INSTRUCTION"     # (ETIQUETA)
```

### `Parser(filepath: str)`

Abre el archivo `.asm` y carga todas las líneas válidas eliminando comentarios y espacios.

**Parámetros:**
- `filepath` — ruta al archivo `.asm`

**Lanza:** `FileNotFoundError` si el archivo no existe.

---

### Métodos

#### `has_more_lines() → bool`
Devuelve `True` si quedan instrucciones por procesar.

#### `advance()`
Avanza a la siguiente instrucción. Solo llamar si `has_more_lines()` es `True`.

#### `current_line_number() → int`
Devuelve el número de línea original en el archivo fuente (útil para mensajes de error).

#### `instruction_type() → str`
Devuelve el tipo de la instrucción actual: `A_INSTRUCTION`, `C_INSTRUCTION`, `SHIFT_INSTRUCTION` o `L_INSTRUCTION`.

**Lanza:** `SyntaxError` si la instrucción no encaja en ningún tipo conocido.

#### `symbol() → str`
- Para `A_INSTRUCTION`: devuelve el valor o símbolo después del `@`.
- Para `L_INSTRUCTION`: devuelve el nombre de la etiqueta sin paréntesis.

**Lanza:** `TypeError` si se llama sobre otro tipo de instrucción.

#### `dest() → str`
Para `C_INSTRUCTION`: devuelve la parte `dest` (antes del `=`). Cadena vacía si no hay `=`.

#### `comp() → str`
Para `C_INSTRUCTION`: devuelve la parte `comp` (entre `=` y `;`).

#### `jump() → str`
Para `C_INSTRUCTION`: devuelve la parte `jump` (después del `;`). Cadena vacía si no hay `;`.

#### `shift_dest() → str`
Para `SHIFT_INSTRUCTION`: devuelve el campo `dest` (antes del `=`).

**Ejemplo:** `'AM=D>>1'` → `'AM'`

#### `shift_source() → str`
Para `SHIFT_INSTRUCTION`: devuelve el registro fuente (`D`, `A` o `M`).

**Ejemplo:** `'D=M<<1'` → `'M'`

**Lanza:** `SyntaxError` si el registro no es `D`, `A` ni `M`.

#### `shift_direction() → str`
Para `SHIFT_INSTRUCTION`: devuelve `'LEFT'` o `'RIGHT'`.

---

## SymbolTable

### `SymbolTable()`

Inicializa la tabla con los símbolos predefinidos del lenguaje Hack:

| Símbolo | Dirección |
|---------|-----------|
| `R0`–`R15` | 0–15 |
| `SP` | 0 |
| `LCL` | 1 |
| `ARG` | 2 |
| `THIS` | 3 |
| `THAT` | 4 |
| `SCREEN` | 16384 |
| `KBD` | 24576 |

---

### Métodos

#### `add_entry(symbol: str, address: int)`
Agrega un símbolo con su dirección a la tabla.

**Lanza:** `ValueError` si el símbolo ya existe.

#### `add_variable(symbol: str) → int`
Registra una variable nueva asignándole la siguiente dirección RAM disponible (desde 16). Si ya existe, devuelve su dirección sin duplicar.

**Retorna:** dirección asignada.

#### `contains(symbol: str) → bool`
Devuelve `True` si el símbolo ya está registrado.

#### `get_address(symbol: str) → int`
Devuelve la dirección numérica del símbolo.

**Lanza:** `KeyError` si el símbolo no existe.

---

## Code

Todos los métodos son **estáticos**. No es necesario instanciar la clase.

### `Code.dest(mnemonic: str) → str`
Traduce el campo `dest` a 3 bits.

| Mnemónico | Bits |
|-----------|------|
| `""` (null) | `000` |
| `M` | `001` |
| `D` | `010` |
| `MD` | `011` |
| `A` | `100` |
| `AM` | `101` |
| `AD` | `110` |
| `AMD` | `111` |

### `Code.comp(mnemonic: str) → str`
Traduce el campo `comp` de una instrucción C estándar a 7 bits (`a` + `c1–c6`).

### `Code.jump(mnemonic: str) → str`
Traduce el campo `jump` a 3 bits.

| Mnemónico | Bits |
|-----------|------|
| `""` (null) | `000` |
| `JGT` | `001` |
| `JEQ` | `010` |
| `JGE` | `011` |
| `JLT` | `100` |
| `JNE` | `101` |
| `JLE` | `110` |
| `JMP` | `111` |

### `Code.comp_shift(source: str, direction: str) → str`
Traduce una instrucción shift a 7 bits basándose en la implementación del `ALU.hdl`.

| source | direction | Bits |
|--------|-----------|------|
| `D` | `LEFT` | `0110000` |
| `A` | `LEFT` | `0100000` |
| `M` | `LEFT` | `1100000` |
| `D` | `RIGHT` | `0010000` |
| `A` | `RIGHT` | `0000000` |
| `M` | `RIGHT` | `1000000` |

### `Code.address_to_binary(address: int) → str`
Convierte una dirección entera a 15 bits en binario (para instrucciones tipo A).

**Lanza:** `ValueError` si la dirección está fuera del rango 0–32767.

---

## HackAssembler

### `assemble(input_path: str) → str`
Ejecuta las dos pasadas del ensamblado sobre el archivo `.asm` indicado.

**Retorna:** ruta del archivo `.hack` generado.

**Lanza:** `FileNotFoundError`, `SyntaxError`, `KeyError`, `ValueError`.

### `first_pass(filepath, symbol_table)`
Primera pasada: registra etiquetas `(ETIQUETA)` en la tabla de símbolos.

### `second_pass(filepath, symbol_table, output_path)`
Segunda pasada: traduce cada instrucción a binario y escribe el `.hack`.

---

## HackDisassembler

### `HackDisassembler(filepath: str)`
Inicializa el desensamblador con la ruta del archivo `.hack`.

**Lanza:** `FileNotFoundError` si el archivo no existe. `ValueError` si no tiene extensión `.hack`.

### `disassemble() → str`
Ejecuta el desensamblado completo y escribe el archivo `*Dis.asm`.

**Retorna:** ruta del archivo de salida generado.

### `disassemble(input_path: str) → str` *(función de módulo)*
Función de conveniencia para invocar el desensamblador directamente.
