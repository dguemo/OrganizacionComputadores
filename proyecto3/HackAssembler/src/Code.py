"""
Code.py - Módulo de generación de código binario para el ensamblador Hack.

Autor 1: David Guerra Morales
Autor 2: Thomas Bedoya Rendón

Responsabilidad:
    Traduce cada campo de una instrucción Hack a su representación
    binaria de acuerdo con la especificación ISA del computador Hack
    extendido con instrucciones de shift (left y right).

    Instrucción tipo C estándar:
        1 1 1 a c1c2c3c4c5c6 d1d2d3 j1j2j3
        ↑ ↑ ↑ └───comp────┘ └dest┘ └jump┘
        bits fijos

    Instrucción shift (basada en ALU.hdl del proyecto 2):
        zx=0, nx=0, zy=0, ny=0, no=1
        f=0 → shift left   (direction=0 en Shifter)
        f=1 → shift right  (direction=1 en Shifter)

        El shifter opera sobre x (registro fuente: D, A o M).
"""


class Code:
    """
    Traduce los campos dest, comp y jump de instrucciones Hack a binario.

    Todos los métodos son estáticos: no es necesario instanciar la clase.

    Uso típico:
        bits_dest = Code.dest("MD")       # → "011"
        bits_comp = Code.comp("D+1")      # → "0011111"
        bits_jump = Code.jump("JGT")      # → "001"

        # Para shift:
        bits_comp = Code.comp_shift("D", "LEFT")  # → "0110000"
        bits_dest = Code.dest("D")                # → "010"
        bits_jump = "000"                         # shift no usa jump
    """

    # ------------------------------------------------------------------
    # Tabla de codificación del campo dest (3 bits: d1 d2 d3)
    # d1 = registro A, d2 = registro D, d3 = memoria M
    # ------------------------------------------------------------------
    _DEST = {
        "":    "000",   # null  — no se almacena resultado
        "M":   "001",   # solo memoria
        "D":   "010",   # solo registro D
        "MD":  "011",   # memoria y registro D
        "A":   "100",   # solo registro A
        "AM":  "101",   # registro A y memoria
        "AD":  "110",   # registro A y registro D
        "AMD": "111",   # registro A, memoria y registro D
    }

    # ------------------------------------------------------------------
    # Tabla de codificación del campo comp (7 bits: a c1c2c3c4c5c6)
    # El bit 'a' selecciona entre operar con A (a=0) o M (a=1)
    # ------------------------------------------------------------------
    _COMP = {
        # a = 0  (operando es A)
        "0":   "0101010",
        "1":   "0111111",
        "-1":  "0111010",
        "D":   "0001100",
        "A":   "0110000",
        "!D":  "0001101",
        "!A":  "0110001",
        "-D":  "0001111",
        "-A":  "0110011",
        "D+1": "0011111",
        "A+1": "0110111",
        "D-1": "0001110",
        "A-1": "0110010",
        "D+A": "0000010",
        "D-A": "0010011",
        "A-D": "0000111",
        "D&A": "0000000",
        "D|A": "0010101",

        # a = 1  (operando es M, dirección de memoria apuntada por A)
        "M":   "1110000",
        "!M":  "1110001",
        "-M":  "1110011",
        "M+1": "1110111",
        "M-1": "1110010",
        "D+M": "1000010",
        "D-M": "1010011",
        "M-D": "1000111",
        "D&M": "1000000",
        "D|M": "1010101",
    }

    # ------------------------------------------------------------------
    # Tabla de codificación del campo jump (3 bits: j1 j2 j3)
    # ------------------------------------------------------------------
    _JUMP = {
        "":    "000",   # null  — no hay salto
        "JGT": "001",   # salta si out > 0
        "JEQ": "010",   # salta si out = 0
        "JGE": "011",   # salta si out >= 0
        "JLT": "100",   # salta si out < 0
        "JNE": "101",   # salta si out != 0
        "JLE": "110",   # salta si out <= 0
        "JMP": "111",   # salto incondicional
    }

    # ------------------------------------------------------------------
    # Codificación de instrucciones SHIFT
    # Basada en ALU.hdl: condición shift → zx=nx=zy=ny=0, no=1
    #   f=0 → shift left  (direction=0 en Shifter)
    #   f=1 → shift right (direction=1 en Shifter)
    #
    # Formato comp (7 bits: a c1c2c3c4c5c6):
    #   Los bits c1-c6 codifican zx,nx,zy,ny,f,no = 0,0,0,0,f,1
    #   Shift left  (f=0): c1c2c3c4c5c6 = 000001  → pero usamos
    #   el patrón que distingue la fuente (D, A, M) en los bits
    #   superiores, igual que las instrucciones C normales.
    #
    # Convención adoptada (compatible con nand2tetris extendido):
    #   D<<1 → a=0, cccccc=110000   → "0110000"  (left,  fuente D)
    #   A<<1 → a=0, cccccc=100000   → "0100000"  (left,  fuente A)
    #   M<<1 → a=1, cccccc=100000   → "1100000"  (left,  fuente M)
    #   D>>1 → a=0, cccccc=010000   → "0010000"  (right, fuente D)
    #   A>>1 → a=0, cccccc=000000   → "0000000"  (right, fuente A)
    #   M>>1 → a=1, cccccc=000000   → "1000000"  (right, fuente M)
    # ------------------------------------------------------------------
    _COMP_SHIFT = {
        ("D", "LEFT"):  "0110000",
        ("A", "LEFT"):  "0100000",
        ("M", "LEFT"):  "1100000",
        ("D", "RIGHT"): "0010000",
        ("A", "RIGHT"): "0000000",
        ("M", "RIGHT"): "1000000",
    }

    # ------------------------------------------------------------------
    # API pública — métodos estáticos
    # ------------------------------------------------------------------

    @staticmethod
    def dest(mnemonic: str) -> str:
        """
        Traduce el campo dest a 3 bits.

        Args:
            mnemonic: Cadena dest (ej: 'D', 'MD', 'AMD', '' para null).

        Returns:
            str: 3 bits del campo dest.

        Raises:
            KeyError: Si el mnemónico no es válido.
        """
        mnemonic = mnemonic.strip()
        if mnemonic not in Code._DEST:
            raise KeyError(
                f"dest no reconocido: '{mnemonic}'. "
                f"Valores válidos: {list(Code._DEST.keys())}"
            )
        return Code._DEST[mnemonic]

    @staticmethod
    def comp(mnemonic: str) -> str:
        """
        Traduce el campo comp de una instrucción C estándar a 7 bits
        (incluye el bit 'a').

        Args:
            mnemonic: Cadena comp (ej: 'D+1', 'M', '!A').

        Returns:
            str: 7 bits del campo comp (a + c1–c6).

        Raises:
            KeyError: Si el mnemónico no es válido.
        """
        mnemonic = mnemonic.strip()
        if mnemonic not in Code._COMP:
            raise KeyError(
                f"comp no reconocido: '{mnemonic}'. "
                f"Valores válidos: {list(Code._COMP.keys())}"
            )
        return Code._COMP[mnemonic]

    @staticmethod
    def jump(mnemonic: str) -> str:
        """
        Traduce el campo jump a 3 bits.

        Args:
            mnemonic: Cadena jump (ej: 'JMP', 'JGT', '' para null).

        Returns:
            str: 3 bits del campo jump.

        Raises:
            KeyError: Si el mnemónico no es válido.
        """
        mnemonic = mnemonic.strip()
        if mnemonic not in Code._JUMP:
            raise KeyError(
                f"jump no reconocido: '{mnemonic}'. "
                f"Valores válidos: {list(Code._JUMP.keys())}"
            )
        return Code._JUMP[mnemonic]

    @staticmethod
    def comp_shift(source: str, direction: str) -> str:
        """
        Traduce una instrucción shift a los 7 bits del campo comp
        (bit 'a' + c1–c6), de acuerdo con la implementación del
        ALU.hdl del proyecto 2.

        La instrucción shift completa queda:
            1 1 1 <7 bits comp> <3 bits dest> 0 0 0
            ↑ fijos de instrucción tipo C     ↑ jump siempre null

        Args:
            source:    Registro fuente: 'D', 'A' o 'M'.
            direction: Dirección del desplazamiento: 'LEFT' o 'RIGHT'.

        Returns:
            str: 7 bits del campo comp para la instrucción shift.

        Raises:
            KeyError: Si la combinación source/direction no es válida.
        """
        key = (source.strip(), direction.strip().upper())
        if key not in Code._COMP_SHIFT:
            raise KeyError(
                f"Instrucción shift no válida: fuente='{source}', "
                f"dirección='{direction}'. "
                f"Use fuente en {{D, A, M}} y dirección en {{LEFT, RIGHT}}."
            )
        return Code._COMP_SHIFT[key]

    @staticmethod
    def address_to_binary(address: int) -> str:
        """
        Convierte una dirección numérica entera a una cadena de 15 bits
        en binario (sin el bit más significativo, que en A_INSTRUCTION
        siempre es 0).

        Args:
            address: Dirección numérica (0 – 32767).

        Returns:
            str: Representación binaria de 15 bits.

        Raises:
            ValueError: Si la dirección está fuera del rango válido.
        """
        if not (0 <= address <= 32767):
            raise ValueError(
                f"Dirección fuera de rango: {address}. "
                f"Debe estar entre 0 y 32767."
            )
        return format(address, "015b")