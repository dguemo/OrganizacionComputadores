"""
HackAssembler.py - Ensamblador principal del computador Hack extendido.

Autor 1: David Guerra Morales
Autor 2: Thomas Bedoya Rendón

Responsabilidad:
    Orquesta las dos pasadas del proceso de ensamblado:

    Primera pasada:
        Recorre el archivo .asm sin generar código. Solo registra las
        etiquetas (L_INSTRUCTION) en la tabla de símbolos, asociándolas
        al número de instrucción donde caerán en el binario final.

    Segunda pasada:
        Recorre el archivo .asm nuevamente traduciendo cada instrucción
        a su representación binaria de 16 bits:
            - A_INSTRUCTION    → 0 + dirección de 15 bits
            - C_INSTRUCTION    → 111 + comp(7) + dest(3) + jump(3)
            - SHIFT_INSTRUCTION→ 111 + comp_shift(7) + dest(3) + 000

        Las variables nuevas se registran automáticamente en la tabla
        de símbolos a partir de la dirección RAM 16.

    El resultado se escribe en un archivo .hack con el mismo nombre
    base que el archivo de entrada.

Uso:
    $ python HackAssembler.py Prog.asm
    → Genera Prog.hack en el mismo directorio

Manejo de errores:
    Si se encuentra un error de sintaxis, se imprime el número de línea
    original del archivo fuente, se cierra el archivo de salida y se
    detiene la traducción.
"""

import sys
import os

from Parser import Parser, A_INSTRUCTION, C_INSTRUCTION, L_INSTRUCTION, SHIFT_INSTRUCTION
from Code import Code
from SymbolTable import SymbolTable
from HackDisassembler import disassemble


def first_pass(filepath: str, symbol_table: SymbolTable) -> None:
    """
    Primera pasada: registra todas las etiquetas (L_INSTRUCTION) en la
    tabla de símbolos.

    Cada etiqueta se asocia al número de instrucción que le seguirá en
    el binario final. Las L_INSTRUCTION no generan código, por eso no
    cuentan como instrucciones al calcular la dirección.

    Args:
        filepath:     Ruta al archivo .asm.
        symbol_table: Tabla de símbolos a poblar con las etiquetas.

    Raises:
        SyntaxError: Si una instrucción no puede ser reconocida.
        ValueError:  Si una etiqueta está definida más de una vez.
    """
    parser = Parser(filepath)
    instruction_number = 0  # Contador de instrucciones reales (no etiquetas)

    while parser.has_more_lines():
        parser.advance()
        itype = parser.instruction_type()

        if itype == L_INSTRUCTION:
            label = parser.symbol()
            if symbol_table.contains(label):
                raise ValueError(
                    f"Línea {parser.current_line_number()}: "
                    f"etiqueta '{label}' definida más de una vez."
                )
            # La etiqueta apunta a la SIGUIENTE instrucción real
            symbol_table.add_entry(label, instruction_number)
        else:
            # A_INSTRUCTION, C_INSTRUCTION y SHIFT_INSTRUCTION
            # generan una instrucción de 16 bits cada una
            instruction_number += 1


def second_pass(filepath: str, symbol_table: SymbolTable, output_path: str) -> None:
    """
    Segunda pasada: traduce cada instrucción a binario y escribe el
    archivo .hack resultante.

    Args:
        filepath:     Ruta al archivo .asm de entrada.
        symbol_table: Tabla de símbolos ya poblada con las etiquetas.
        output_path:  Ruta donde se escribirá el archivo .hack.

    Raises:
        SyntaxError: Si se encuentra una instrucción con sintaxis inválida.
        KeyError:    Si un mnemónico de comp/dest/jump no es reconocido.
    """
    parser = Parser(filepath)

    with open(output_path, "w", encoding="utf-8") as out:
        while parser.has_more_lines():
            parser.advance()
            itype = parser.instruction_type()
            line_num = parser.current_line_number()

            # ----------------------------------------------------------
            # A_INSTRUCTION: @valor o @simbolo
            # Formato binario: 0 + 15 bits de dirección
            # ----------------------------------------------------------
            if itype == A_INSTRUCTION:
                symbol = parser.symbol()

                # ¿Es un número literal?
                if symbol.isdigit():
                    address = int(symbol)
                    if address > 32767:
                        raise ValueError(
                            f"Línea {line_num}: "
                            f"dirección '@{address}' excede el máximo (32767)."
                        )
                else:
                    # Es un símbolo: buscar en tabla o registrar como variable
                    if not symbol_table.contains(symbol):
                        symbol_table.add_variable(symbol)
                    address = symbol_table.get_address(symbol)

                binary = "0" + Code.address_to_binary(address)
                out.write(binary + "\n")

            # ----------------------------------------------------------
            # C_INSTRUCTION: dest=comp;jump
            # Formato binario: 111 + comp(7bits) + dest(3bits) + jump(3bits)
            # ----------------------------------------------------------
            elif itype == C_INSTRUCTION:
                try:
                    bits_comp = Code.comp(parser.comp())
                    bits_dest = Code.dest(parser.dest())
                    bits_jump = Code.jump(parser.jump())
                except KeyError as e:
                    raise KeyError(
                        f"Línea {line_num}: mnemónico no reconocido. {e}"
                    )

                binary = "111" + bits_comp + bits_dest + bits_jump
                out.write(binary + "\n")

            # ----------------------------------------------------------
            # SHIFT_INSTRUCTION: dest=reg<<1 o dest=reg>>1
            # Formato binario: 111 + comp_shift(7bits) + dest(3bits) + 000
            # El campo jump siempre es 000 para instrucciones shift
            # ----------------------------------------------------------
            elif itype == SHIFT_INSTRUCTION:
                try:
                    source    = parser.shift_source()
                    direction = parser.shift_direction()
                    bits_comp = Code.comp_shift(source, direction)
                    bits_dest = Code.dest(parser.shift_dest())
                except (KeyError, SyntaxError) as e:
                    raise type(e)(
                        f"Línea {line_num}: error en instrucción shift. {e}"
                    )

                binary = "101" + bits_comp + bits_dest + "000"
                out.write(binary + "\n")

            # ----------------------------------------------------------
            # L_INSTRUCTION: (ETIQUETA)
            # No genera código binario, solo se usó en la primera pasada
            # ----------------------------------------------------------
            # elif itype == L_INSTRUCTION → se ignora silenciosamente


def assemble(input_path: str) -> str:
    """
    Función principal de ensamblado: ejecuta las dos pasadas y devuelve
    la ruta del archivo .hack generado.

    Args:
        input_path: Ruta al archivo .asm de entrada.

    Returns:
        str: Ruta del archivo .hack generado.

    Raises:
        FileNotFoundError: Si el archivo de entrada no existe.
        SyntaxError:       Si hay errores de sintaxis en el .asm.
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"No se encontró el archivo: '{input_path}'")

    if not input_path.endswith(".asm"):
        raise ValueError(f"El archivo de entrada debe tener extensión .asm: '{input_path}'")

    # Construir la ruta de salida: mismo nombre, extensión .hack
    base = os.path.splitext(input_path)[0]
    output_path = base + ".hack"

    # Inicializar tabla de símbolos con los predefinidos de Hack
    symbol_table = SymbolTable()

    # Ejecutar las dos pasadas
    first_pass(input_path, symbol_table)
    second_pass(input_path, symbol_table, output_path)

    return output_path


# ----------------------------------------------------------------------
# Punto de entrada del programa
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Modo desensamblador: python HackAssembler.py -d Prog.hack
    if len(sys.argv) == 3 and sys.argv[1] == "-d":
        try:
            disassemble(sys.argv[2])
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except (SyntaxError, KeyError, ValueError) as e:
            print(f"Error de desensamblado: {e}")
            sys.exit(1)

    # Modo ensamblador: python HackAssembler.py Prog.asm
    elif len(sys.argv) == 2:
        input_file = sys.argv[1]
        try:
            assemble(input_file)
            # Si todo fue bien, no se imprime nada (según el enunciado)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except (SyntaxError, KeyError, ValueError) as e:
            print(f"Error de traducción: {e}")
            sys.exit(1)

    else:
        print("Uso:")
        print("  Ensamblar:    python HackAssembler.py <archivo.asm>")
        print("  Desensamblar: python HackAssembler.py -d <archivo.hack>")
        sys.exit(1)
