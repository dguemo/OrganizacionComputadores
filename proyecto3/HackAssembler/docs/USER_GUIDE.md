# Guía de Usuario — HackAssembler

**Organización de Computadores 2026-1**  
**Proyecto 3**  
Universidad EAFIT — Ingeniería de Sistemas

---

## Requisitos

- Python 3.8 o superior
- No requiere librerías externas

---

## Estructura del proyecto

```
HackAssembler/
├── docs/
│   ├── API.md          ← Documentación de todas las clases y métodos
│   ├── DESIGN.md       ← Diagrama de clases y decisiones de diseño
│   └── USER_GUIDE.md   ← Este archivo
├── src/
│   ├── HackAssembler.py
│   ├── HackAssembler.md5
│   ├── Parser.py
│   ├── Parser.md5
│   ├── Code.py
│   ├── Code.md5
│   ├── SymbolTable.py
│   ├── SymbolTable.md5
│   ├── HackDisassembler.py
│   └── HackDisassembler.md5
├── test/
│   ├── HackAssemblerTest.py
│   └── HackAssemblerTest.md5
└── README.md
```

---

## Ensamblar un archivo `.asm`

Desde la carpeta `src/`, ejecutar:

```bash
python HackAssembler.py <archivo.asm>
```

**Ejemplo:**

```bash
python HackAssembler.py Prog.asm
```

Esto genera el archivo `Prog.hack` en el mismo directorio que `Prog.asm`.

### Comportamiento esperado

- Si el archivo no tiene errores de sintaxis, el programa **no imprime nada** y termina silenciosamente.
- Si se encuentra un error, se imprime el número de línea donde ocurrió y el proceso se detiene:

```
Error de traducción: Línea 42: mnemónico no reconocido: 'XYZ'
```

---

## Desensamblar un archivo `.hack`

```bash
python HackAssembler.py -d <archivo.hack>
```

**Ejemplo:**

```bash
python HackAssembler.py -d Prog.hack
```

Esto genera el archivo `ProgDis.asm` en el mismo directorio que `Prog.hack`.

### Comportamiento esperado

- Si el archivo es válido, el programa **no imprime nada** y genera el `.asm` resultante.
- Si se encuentra una línea con formato inválido, se imprime el número de línea y el proceso se detiene:

```
Error de desensamblado: Línea 7: formato inválido → '10110'. Se esperan exactamente 16 bits.
```

---

## Instrucciones soportadas

### Tipo A
```
@42          → dirección literal
@variable    → símbolo o variable (se resuelve en tabla de símbolos)
@LOOP        → etiqueta definida en el programa
```

### Tipo C estándar
```
D=M+1
AMD=D|A
0;JMP
D;JGT
MD=D-1;JNE
```

### Instrucciones shift (extensión Hack — Proyecto 2)
```
D=D<<1       → shift left del registro D, resultado en D
AM=M<<1      → shift left de memoria, resultado en A y M
D=A>>1       → shift right del registro A, resultado en D
M=D>>1       → shift right del registro D, resultado en memoria
```

**Registros válidos como fuente de shift:** `D`, `A`, `M`

**Destinos válidos:** cualquier combinación de `A`, `D`, `M` (igual que instrucciones C normales)

---

## Símbolos predefinidos

El ensamblador reconoce automáticamente los siguientes símbolos sin necesidad de declararlos:

| Símbolo | Dirección RAM |
|---------|--------------|
| `R0` – `R15` | 0 – 15 |
| `SP` | 0 |
| `LCL` | 1 |
| `ARG` | 2 |
| `THIS` | 3 |
| `THAT` | 4 |
| `SCREEN` | 16384 |
| `KBD` | 24576 |

---

## Etiquetas y variables

**Etiquetas** se declaran con paréntesis y no generan código:
```
(LOOP)
   D=D-1
   D;JGT LOOP    ← salta a la instrucción siguiente a (LOOP)
```

**Variables** se declaran implícitamente con `@nombre` y se asignan automáticamente desde la dirección RAM 16:
```
@contador      ← se asigna RAM[16] la primera vez que aparece
@suma          ← se asigna RAM[17]
```

---

## Ejecutar los tests

Desde la carpeta `test/`:

```bash
python HackAssemblerTest.py
```

Los tests verifican ensamblado, desensamblado e instrucciones shift con casos de prueba predefinidos.
