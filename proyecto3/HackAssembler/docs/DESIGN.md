# Diseño del Sistema — HackAssembler

**Organización de Computadores 2026-1**  
**Proyecto 3**  
Universidad EAFIT — Ingeniería de Sistemas

---

## Diagrama de clases

```
┌─────────────────────────────────────────────────────────────┐
│                      HackAssembler.py                       │
│                                                             │
│  + assemble(input_path) → str                               │
│  + first_pass(filepath, symbol_table)                       │
│  + second_pass(filepath, symbol_table, output_path)         │
└────────┬──────────────┬──────────────┬──────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌──────────────┐ ┌────────────┐ ┌──────────────────┐
│   Parser     │ │SymbolTable │ │      Code        │
│              │ │            │ │                  │
│ +has_more()  │ │+add_entry()│ │+dest() [static]  │
│ +advance()   │ │+add_var()  │ │+comp() [static]  │
│ +instr_type()│ │+contains() │ │+jump() [static]  │
│ +symbol()    │ │+get_addr() │ │+comp_shift()     │
│ +dest()      │ └────────────┘ │+addr_to_bin()    │
│ +comp()      │                └──────────────────┘
│ +jump()      │
│ +shift_dest()│
│ +shift_src() │
│ +shift_dir() │
└──────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   HackDisassembler.py                       │
│                                                             │
│  + disassemble() → str          (método de instancia)       │
│  + disassemble(path) → str      (función de módulo)         │
│  - _decode_a(bits) → str                                    │
│  - _decode_c(comp, dest, jump) → str                        │
│  - _decode_shift(comp, dest) → str                          │
│  - _is_shift(comp, jump) → bool                             │
│  - _decode_line(bits, line_num) → str                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Flujo de ensamblado (dos pasadas)

```
archivo.asm
     │
     ▼
┌─────────────────────────────────────┐
│          PRIMERA PASADA             │
│                                     │
│  Parser recorre el archivo          │
│  Por cada L_INSTRUCTION (ETIQUETA): │
│    SymbolTable.add_entry(label, n)  │
│  A/C/SHIFT cuentan como instrucción │
└─────────────────────────────────────┘
     │
     ▼ (tabla de símbolos poblada con etiquetas)
┌─────────────────────────────────────┐
│          SEGUNDA PASADA             │
│                                     │
│  Parser recorre el archivo de nuevo │
│                                     │
│  A_INSTRUCTION (@x):                │
│    ¿es número? → dirección literal  │
│    ¿es símbolo? → buscar/registrar  │
│    → "0" + 15 bits                  │
│                                     │
│  C_INSTRUCTION (dest=comp;jump):    │
│    Code.comp() + dest() + jump()    │
│    → "111" + 7 + 3 + 3 bits         │
│                                     │
│  SHIFT_INSTRUCTION (dest=reg<<1):   │
│    Code.comp_shift() + dest()       │
│    → "111" + 7 + 3 + "000" bits     │
│                                     │
│  L_INSTRUCTION → se ignora          │
└─────────────────────────────────────┘
     │
     ▼
archivo.hack (16 bits por línea)
```

---

## Flujo de desensamblado

```
archivo.hack
     │
     ▼
┌─────────────────────────────────────┐
│  Por cada línea de 16 bits:         │
│                                     │
│  bit[0] == 0                        │
│    → A_INSTRUCTION                  │
│    → @{int(bits[1:], 2)}            │
│                                     │
│  bits[0:3] == "111"                 │
│    extraer comp[3:10]               │
│            dest[10:13]              │
│            jump[13:16]              │
│                                     │
│    ¿comp en _COMP_SHIFT             │
│       AND jump == "000"?            │
│      → SHIFT_INSTRUCTION            │
│      → dest=source<<1 / >>1         │
│                                     │
│    sino:                            │
│      → C_INSTRUCTION                │
│      → dest=comp;jump               │
└─────────────────────────────────────┘
     │
     ▼
archivoDis.asm
```

---

## Decisiones de diseño

### 1. Separación de responsabilidades
Cada módulo tiene una única responsabilidad (principio SRP). El `HackAssembler.py` no conoce los detalles de parsing ni de codificación binaria — delega completamente en `Parser`, `Code` y `SymbolTable`.

### 2. Dos pasadas obligatorias
La primera pasada es necesaria porque las etiquetas pueden referenciarse antes de ser definidas (saltos hacia adelante). Sin esta pasada, instrucciones como `@END` no podrían resolverse si `(END)` aparece más adelante en el archivo.

### 3. Detección de shift por bits comp + jump
El desensamblador detecta instrucciones shift verificando dos condiciones: que los bits `comp` correspondan a un patrón shift **y** que el campo `jump` sea `000`. Esto evita confusión con instrucciones C estándar cuyos bits comp coincidan parcialmente.

### 4. Codificación shift basada en ALU.hdl
Los bits de comp para shift derivan directamente de la condición de activación del shifter en el `ALU.hdl` del Proyecto 2:
- `zx=0, nx=0, zy=0, ny=0, no=1`
- `f=0` → shift left (direction=0 en Shifter)
- `f=1` → shift right (direction=1 en Shifter)

### 5. Variables en RAM desde dirección 16
Las primeras 16 direcciones RAM (0–15) están reservadas para R0–R15. Las variables de usuario se asignan desde la dirección 16 en adelante, en el orden en que aparecen por primera vez en el código fuente.

### 6. Números de línea originales en errores
El `Parser` guarda el número de línea original del archivo `.asm` junto a cada instrucción. Esto permite que los mensajes de error apunten exactamente a la línea problemática en el archivo fuente, no a la línea de instrucción binaria.
