"""
HackDisassembler.py - Desensamblador del computador Hack extendido.

Autor 1: David Guerra Morales
Autor 2: Thomas Bedoya Rendón

Responsabilidad:
    Lee un archivo .hack (secuencia de líneas de 16 bits) y traduce
    cada línea de vuelta a su instrucción en assembler Hack:

        - A_INSTRUCTION    : bit 15 = 0  →  @valor
        - C_INSTRUCTION    : bits 15-13 = 111, bits comp no son shift
        - SHIFT_INSTRUCTION: bits 15-13 = 111, bits comp son de shift

    El resultado se escribe en un archivo con el sufijo 'Dis.asm'.

Uso:
    $ python HackAssembler.py -d Prog.hack
    → Genera ProgDis.asm en el mismo directorio

Manejo de errores:
    Si se encuentra una línea con formato inválido, se imprime el número
    de línea donde ocurrió el error, se cierra el archivo de salida y
    se detiene el proceso.
"""

import sys
import os


class HackDisassembler:
    """
    Desensamblador del computador Hack extendido.

    Traduce instrucciones binarias de 16 bits de vuelta a assembler Hack,
    incluyendo soporte para instrucciones de shift left y shift right.

    Uso típico:
        dis = HackDisassembler("Prog.hack")
        dis.disassemble()   # genera ProgDis.asm
    """

    # ------------------------------------------------------------------
    # Tablas inversas: de bits a mnemónicos
    # ------------------------------------------------------------------

    # dest: 3 bits → mnemónico
    _DEST = {
        "000": "",
        "001": "M",
        "010": "D",
        "011": "MD",
        "100": "A",
        "101": "AM",
        "110": "AD",
        "111": "AMD",
    }

    # jump: 3 bits → mnemónico
    _JUMP = {
        "000": "",
        "001": "JGT",
        "010": "JEQ",
        "011": "JGE",
        "100": "JLT",
        "101": "JNE",
        "110": "JLE",
        "111": "JMP",
    }

    # comp: 7 bits (a + c1-c6) → mnemónico (instrucciones C estándar)
    _COMP = {
        "0101010": "0",
        "0111111": "1",
        "0111010": "-1",
        "0001100": "D",
        "0110000": "A",
        "0001101": "!D",
        "0110001": "!A",
        "0001111": "-D",
        "0110011": "-A",
        "0011111": "D+1",
        "0110111": "A+1",
        "0001110": "D-1",
        "0110010": "A-1",
        "0000010": "D+A",
        "0010011": "D-A",
        "0000111": "A-D",
        "0000000": "D&A",
        "0010101": "D|A",
        "1110000": "M",
        "1110001": "!M",
        "1110011": "-M",
        "1110111": "M+1",
        "1110010": "M-1",
        "1000010": "D+M",
        "1010011": "D-M",
        "1000111": "M-D",
        "1000000": "D&M",
        "1010101": "D|M",
    }

    # comp_shift: 7 bits → (registro fuente, dirección)
    # Inverso de Code._COMP_SHIFT
    _COMP_SHIFT = {
        "0110000": ("D", "LEFT"),
        "0100000": ("A", "LEFT"),
        "1100000": ("M", "LEFT"),
        "0010000": ("D", "RIGHT"),
        "0000000": ("A", "RIGHT"),
        "1000000": ("M", "RIGHT"),
    }

    def __init__(self, filepath: str):
        """
        Inicializa el desensamblador con la ruta del archivo .hack.

        Args:
            filepath: Ruta al archivo .hack de entrada.

        Raises:
            FileNotFoundError: Si el archivo no existe.
            ValueError: Si el archivo no tiene extensión .hack.
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(
                f"No se encontró el archivo: '{filepath}'"
            )
        if not filepath.endswith(".hack"):
            raise ValueError(
                f"El archivo de entrada debe tener extensión .hack: '{filepath}'"
            )

        self._input_path = filepath

        # Construir ruta de salida: Prog.hack → ProgDis.asm
        base = os.path.splitext(filepath)[0]
        self._output_path = base + "Dis.asm"

    # ------------------------------------------------------------------
    # Métodos privados de decodificación
    # ------------------------------------------------------------------

    def _decode_a(self, bits: str) -> str:
        """
        Decodifica una instrucción tipo A.
        El valor es simplemente el entero representado por los 15 bits
        menos significativos.

        Args:
            bits: 16 bits de la instrucción (bit 15 = 0).

        Returns:
            str: Instrucción assembler (ej: '@42').
        """
        value = int(bits[1:], 2)  # bits[1:] son los 15 bits de dirección
        return f"@{value}"

    def _is_shift(self, bits: str) -> bool:
        """
        Determina si una instrucción de 16 bits es una instrucción shift.

        En el estándar Nand2Tetris extendido, las instrucciones shift
        se distinguen de las C estándar por los bits 14 y 13:
            - C estándar : bits[1:3] == "11"  (1 1 1 ...)
            - Shift       : bits[1:3] == "10"  (1 0 1 ...)

        Args:
            bits: Los 16 bits completos de la instrucción.

        Returns:
            bool: True si es instrucción shift, False si es C estándar.
        """
        return bits[1:3] == "10"

    def _decode_shift(self, comp_bits: str, dest_bits: str) -> str:
        """
        Decodifica una instrucción shift a assembler.

        Args:
            comp_bits: 7 bits del campo comp (patrón shift).
            dest_bits: 3 bits del campo dest.

        Returns:
            str: Instrucción assembler (ej: 'D=M<<1', 'AM=D>>1').

        Raises:
            KeyError: Si los bits no corresponden a un shift válido.
        """
        source, direction = self._COMP_SHIFT[comp_bits]
        dest = self._DEST[dest_bits]

        operator = "<<1" if direction == "LEFT" else ">>1"

        if dest:
            return f"{dest}={source}{operator}"
        else:
            # Sin dest es inusual en shift, pero lo manejamos igual
            return f"{source}{operator}"

    def _decode_c(self, comp_bits: str, dest_bits: str, jump_bits: str) -> str:
        """
        Decodifica una instrucción C estándar a assembler.

        Args:
            comp_bits: 7 bits del campo comp.
            dest_bits: 3 bits del campo dest.
            jump_bits: 3 bits del campo jump.

        Returns:
            str: Instrucción assembler (ej: 'D=M+1', '0;JMP', 'MD=D-A').

        Raises:
            KeyError: Si los bits comp no son reconocidos.
        """
        if comp_bits not in self._COMP:
            raise KeyError(
                f"Bits comp no reconocidos: '{comp_bits}'"
            )

        comp = self._COMP[comp_bits]
        dest = self._DEST[dest_bits]
        jump = self._JUMP[jump_bits]

        # Reconstruir la instrucción en formato dest=comp;jump
        instruction = comp
        if dest:
            instruction = f"{dest}={instruction}"
        if jump:
            instruction = f"{instruction};{jump}"

        return instruction

    def _decode_line(self, bits: str, line_num: int) -> str:
        """
        Decodifica una línea de 16 bits a su instrucción assembler.

        Args:
            bits:     Cadena de exactamente 16 caracteres '0' o '1'.
            line_num: Número de línea en el archivo (para errores).

        Returns:
            str: Instrucción assembler correspondiente.

        Raises:
            SyntaxError: Si el formato de la línea es inválido.
            KeyError:    Si los bits no corresponden a ninguna instrucción.
        """
        # Validar formato
        if len(bits) != 16 or not all(c in "01" for c in bits):
            raise SyntaxError(
                f"Línea {line_num}: formato inválido → '{bits}'. "
                f"Se esperan exactamente 16 bits (0s y 1s)."
            )

        # Bit más significativo = 0 → instrucción tipo A
        if bits[0] == "0":
            return self._decode_a(bits)

        # bits[0:3] == "101" → instrucción SHIFT (extensión Hack)
        if bits[0:3] == "101":
            comp_bits = bits[3:10]
            dest_bits = bits[10:13]
            return self._decode_shift(comp_bits, dest_bits)

        # bits[0:3] == "111" → instrucción tipo C estándar
        if bits[0:3] == "111":
            comp_bits = bits[3:10]
            dest_bits = bits[10:13]
            jump_bits = bits[13:16]
            return self._decode_c(comp_bits, dest_bits, jump_bits)

        raise SyntaxError(
            f"Línea {line_num}: instrucción no reconocida → '{bits}'. "
            f"El bit más significativo debe ser 0 (tipo A), "
            f"'101' (shift) o '111' (tipo C)."
        )

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def disassemble(self) -> str:
        """
        Ejecuta el proceso de desensamblado completo: lee el archivo
        .hack línea por línea y escribe el archivo *Dis.asm resultante.

        Returns:
            str: Ruta del archivo de salida generado.

        Raises:
            SyntaxError: Si alguna línea tiene formato inválido.
            KeyError:    Si alguna instrucción no puede decodificarse.
        """
        with open(self._input_path, "r", encoding="utf-8-sig") as infile, \
             open(self._output_path, "w", encoding="utf-8") as outfile:

            for line_num, raw_line in enumerate(infile, start=1):
                bits = raw_line.strip()

                # Ignorar líneas vacías
                if not bits:
                    continue

                try:
                    instruction = self._decode_line(bits, line_num)
                    outfile.write(instruction + "\n")

                except (SyntaxError, KeyError) as e:
                    raise type(e)(
                        f"Error al desensamblador línea {line_num}: {e}"
                    )

        return self._output_path


# ----------------------------------------------------------------------
# Punto de entrada (usado desde HackAssembler.py con el flag -d)
# ----------------------------------------------------------------------
def disassemble(input_path: str) -> str:
    """
    Función de conveniencia para invocar el desensamblador desde
    HackAssembler.py.

    Args:
        input_path: Ruta al archivo .hack de entrada.

    Returns:
        str: Ruta del archivo *Dis.asm generado.
    """
    dis = HackDisassembler(input_path)
    return dis.disassemble()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python HackDisassembler.py <archivo.hack>")
        sys.exit(1)

    try:
        output = disassemble(sys.argv[1])

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    except (SyntaxError, KeyError, ValueError) as e:
        print(f"Error de desensamblado: {e}")
        sys.exit(1)
