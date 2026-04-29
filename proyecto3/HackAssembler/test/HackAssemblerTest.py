"""
HackAssemblerTest.py - Suite de pruebas para el ensamblador Hack extendido.

Autor 1: David Guerra Morales
Autor 2: Thomas Bedoya Rendón

Responsabilidad:
    Verifica el correcto funcionamiento de todos los módulos del
    HackAssembler mediante pruebas unitarias e integracion:

        - Parser:           clasificacion y extraccion de campos
        - SymbolTable:      gestion de simbolos y variables
        - Code:             traduccion de mnemonicos a bits
        - HackAssembler:    ensamblado completo de archivos .asm
        - HackDisassembler: desensamblado completo de archivos .hack

    Incluye casos de prueba para instrucciones shift left y right,
    que son la extension del Proyecto 2 integrada en este ensamblador.
"""

import unittest
import os
import sys
import tempfile

# Asegurar que Python encuentre los modulos en src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from Parser import Parser, A_INSTRUCTION, C_INSTRUCTION, L_INSTRUCTION, SHIFT_INSTRUCTION
from SymbolTable import SymbolTable
from Code import Code
from HackAssembler import assemble
from HackDisassembler import disassemble


# ===========================================================================
# Tests del Parser
# ===========================================================================

class TestParser(unittest.TestCase):
    """Pruebas unitarias para el modulo Parser."""

    def _make_temp_asm(self, content: str) -> str:
        """Crea un archivo .asm temporal con el contenido dado."""
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".asm", delete=False, encoding="utf-8"
        )
        f.write(content)
        f.close()
        return f.name

    def tearDown(self):
        """Limpia archivos temporales creados durante los tests."""
        for f in getattr(self, "_temp_files", []):
            if os.path.exists(f):
                os.remove(f)

    # -------------------------------------------------------------------
    # Instrucciones tipo A
    # -------------------------------------------------------------------

    def test_a_instruction_numeric(self):
        """@42 debe reconocerse como A_INSTRUCTION con symbol '42'."""
        path = self._make_temp_asm("@42\n")
        p = Parser(path)
        p.advance()
        self.assertEqual(p.instruction_type(), A_INSTRUCTION)
        self.assertEqual(p.symbol(), "42")
        os.remove(path)

    def test_a_instruction_symbol(self):
        """@variable debe reconocerse como A_INSTRUCTION con symbol 'variable'."""
        path = self._make_temp_asm("@miVariable\n")
        p = Parser(path)
        p.advance()
        self.assertEqual(p.instruction_type(), A_INSTRUCTION)
        self.assertEqual(p.symbol(), "miVariable")
        os.remove(path)

    # -------------------------------------------------------------------
    # Instrucciones tipo C
    # -------------------------------------------------------------------

    def test_c_instruction_full(self):
        """D=M+1;JGT debe reconocerse como C con dest, comp y jump correctos."""
        path = self._make_temp_asm("D=M+1;JGT\n")
        p = Parser(path)
        p.advance()
        self.assertEqual(p.instruction_type(), C_INSTRUCTION)
        self.assertEqual(p.dest(), "D")
        self.assertEqual(p.comp(), "M+1")
        self.assertEqual(p.jump(), "JGT")
        os.remove(path)

    def test_c_instruction_no_dest(self):
        """0;JMP debe tener dest vacio y jump JMP."""
        path = self._make_temp_asm("0;JMP\n")
        p = Parser(path)
        p.advance()
        self.assertEqual(p.instruction_type(), C_INSTRUCTION)
        self.assertEqual(p.dest(), "")
        self.assertEqual(p.comp(), "0")
        self.assertEqual(p.jump(), "JMP")
        os.remove(path)

    def test_c_instruction_no_jump(self):
        """MD=D-1 debe tener jump vacio."""
        path = self._make_temp_asm("MD=D-1\n")
        p = Parser(path)
        p.advance()
        self.assertEqual(p.instruction_type(), C_INSTRUCTION)
        self.assertEqual(p.dest(), "MD")
        self.assertEqual(p.comp(), "D-1")
        self.assertEqual(p.jump(), "")
        os.remove(path)

    # -------------------------------------------------------------------
    # Instrucciones tipo L (etiquetas)
    # -------------------------------------------------------------------

    def test_l_instruction(self):
        """(LOOP) debe reconocerse como L_INSTRUCTION con symbol 'LOOP'."""
        path = self._make_temp_asm("(LOOP)\n")
        p = Parser(path)
        p.advance()
        self.assertEqual(p.instruction_type(), L_INSTRUCTION)
        self.assertEqual(p.symbol(), "LOOP")
        os.remove(path)

    # -------------------------------------------------------------------
    # Instrucciones shift
    # -------------------------------------------------------------------

    def test_shift_left_D(self):
        """D=D<<1 debe ser SHIFT con dest D, source D, direction LEFT."""
        path = self._make_temp_asm("D=D<<1\n")
        p = Parser(path)
        p.advance()
        self.assertEqual(p.instruction_type(), SHIFT_INSTRUCTION)
        self.assertEqual(p.shift_dest(), "D")
        self.assertEqual(p.shift_source(), "D")
        self.assertEqual(p.shift_direction(), "LEFT")
        os.remove(path)

    def test_shift_left_M(self):
        """AM=M<<1 debe ser SHIFT con dest AM, source M, direction LEFT."""
        path = self._make_temp_asm("AM=M<<1\n")
        p = Parser(path)
        p.advance()
        self.assertEqual(p.instruction_type(), SHIFT_INSTRUCTION)
        self.assertEqual(p.shift_dest(), "AM")
        self.assertEqual(p.shift_source(), "M")
        self.assertEqual(p.shift_direction(), "LEFT")
        os.remove(path)

    def test_shift_right_D(self):
        """D=A>>1 debe ser SHIFT con source A, direction RIGHT."""
        path = self._make_temp_asm("D=A>>1\n")
        p = Parser(path)
        p.advance()
        self.assertEqual(p.instruction_type(), SHIFT_INSTRUCTION)
        self.assertEqual(p.shift_source(), "A")
        self.assertEqual(p.shift_direction(), "RIGHT")
        os.remove(path)

    def test_shift_right_M(self):
        """M=D>>1 debe ser SHIFT con dest M, source D, direction RIGHT."""
        path = self._make_temp_asm("M=D>>1\n")
        p = Parser(path)
        p.advance()
        self.assertEqual(p.instruction_type(), SHIFT_INSTRUCTION)
        self.assertEqual(p.shift_dest(), "M")
        self.assertEqual(p.shift_source(), "D")
        self.assertEqual(p.shift_direction(), "RIGHT")
        os.remove(path)

    # -------------------------------------------------------------------
    # Comentarios y lineas vacias
    # -------------------------------------------------------------------

    def test_ignores_comments(self):
        """Las lineas de solo comentario no deben contar como instrucciones."""
        path = self._make_temp_asm("// esto es un comentario\n@5\n")
        p = Parser(path)
        p.advance()
        # Solo debe haber una instruccion: @5
        self.assertEqual(p.instruction_type(), A_INSTRUCTION)
        self.assertEqual(p.symbol(), "5")
        self.assertFalse(p.has_more_lines())
        os.remove(path)

    def test_ignores_inline_comments(self):
        """Los comentarios inline deben eliminarse correctamente."""
        path = self._make_temp_asm("@10 // esta es la direccion\n")
        p = Parser(path)
        p.advance()
        self.assertEqual(p.instruction_type(), A_INSTRUCTION)
        self.assertEqual(p.symbol(), "10")
        os.remove(path)


# ===========================================================================
# Tests de SymbolTable
# ===========================================================================

class TestSymbolTable(unittest.TestCase):
    """Pruebas unitarias para el modulo SymbolTable."""

    def test_predefined_symbols(self):
        """Los simbolos predefinidos deben estar disponibles al crear la tabla."""
        tabla = SymbolTable()
        self.assertTrue(tabla.contains("R0"))
        self.assertEqual(tabla.get_address("R0"), 0)
        self.assertEqual(tabla.get_address("R15"), 15)
        self.assertEqual(tabla.get_address("SP"), 0)
        self.assertEqual(tabla.get_address("SCREEN"), 16384)
        self.assertEqual(tabla.get_address("KBD"), 24576)

    def test_add_entry(self):
        """add_entry debe registrar un simbolo con su direccion."""
        tabla = SymbolTable()
        tabla.add_entry("LOOP", 10)
        self.assertTrue(tabla.contains("LOOP"))
        self.assertEqual(tabla.get_address("LOOP"), 10)

    def test_add_entry_duplicate_raises(self):
        """add_entry debe lanzar ValueError si el simbolo ya existe."""
        tabla = SymbolTable()
        tabla.add_entry("LOOP", 10)
        with self.assertRaises(ValueError):
            tabla.add_entry("LOOP", 20)

    def test_add_variable_sequential(self):
        """Las variables nuevas deben asignarse desde la direccion 16."""
        tabla = SymbolTable()
        addr1 = tabla.add_variable("x")
        addr2 = tabla.add_variable("y")
        addr3 = tabla.add_variable("z")
        self.assertEqual(addr1, 16)
        self.assertEqual(addr2, 17)
        self.assertEqual(addr3, 18)

    def test_add_variable_idempotent(self):
        """add_variable sobre un simbolo existente devuelve su direccion sin duplicar."""
        tabla = SymbolTable()
        addr1 = tabla.add_variable("x")
        addr2 = tabla.add_variable("x")
        self.assertEqual(addr1, addr2)

    def test_get_address_missing_raises(self):
        """get_address debe lanzar KeyError si el simbolo no existe."""
        tabla = SymbolTable()
        with self.assertRaises(KeyError):
            tabla.get_address("INEXISTENTE")


# ===========================================================================
# Tests de Code
# ===========================================================================

class TestCode(unittest.TestCase):
    """Pruebas unitarias para el modulo Code."""

    # -------------------------------------------------------------------
    # dest
    # -------------------------------------------------------------------

    def test_dest_null(self):
        self.assertEqual(Code.dest(""), "000")

    def test_dest_M(self):
        self.assertEqual(Code.dest("M"), "001")

    def test_dest_D(self):
        self.assertEqual(Code.dest("D"), "010")

    def test_dest_MD(self):
        self.assertEqual(Code.dest("MD"), "011")

    def test_dest_A(self):
        self.assertEqual(Code.dest("A"), "100")

    def test_dest_AM(self):
        self.assertEqual(Code.dest("AM"), "101")

    def test_dest_AD(self):
        self.assertEqual(Code.dest("AD"), "110")

    def test_dest_AMD(self):
        self.assertEqual(Code.dest("AMD"), "111")

    def test_dest_invalid_raises(self):
        with self.assertRaises(KeyError):
            Code.dest("XYZ")

    # -------------------------------------------------------------------
    # comp
    # -------------------------------------------------------------------

    def test_comp_zero(self):
        self.assertEqual(Code.comp("0"), "0101010")

    def test_comp_one(self):
        self.assertEqual(Code.comp("1"), "0111111")

    def test_comp_D_plus_1(self):
        self.assertEqual(Code.comp("D+1"), "0011111")

    def test_comp_M(self):
        self.assertEqual(Code.comp("M"), "1110000")

    def test_comp_D_plus_M(self):
        self.assertEqual(Code.comp("D+M"), "1000010")

    def test_comp_invalid_raises(self):
        with self.assertRaises(KeyError):
            Code.comp("X+Z")

    # -------------------------------------------------------------------
    # jump
    # -------------------------------------------------------------------

    def test_jump_null(self):
        self.assertEqual(Code.jump(""), "000")

    def test_jump_JMP(self):
        self.assertEqual(Code.jump("JMP"), "111")

    def test_jump_JGT(self):
        self.assertEqual(Code.jump("JGT"), "001")

    def test_jump_JEQ(self):
        self.assertEqual(Code.jump("JEQ"), "010")

    def test_jump_invalid_raises(self):
        with self.assertRaises(KeyError):
            Code.jump("JXX")

    # -------------------------------------------------------------------
    # comp_shift
    # -------------------------------------------------------------------

    def test_shift_D_left(self):
        self.assertEqual(Code.comp_shift("D", "LEFT"), "0110000")

    def test_shift_A_left(self):
        self.assertEqual(Code.comp_shift("A", "LEFT"), "0100000")

    def test_shift_M_left(self):
        self.assertEqual(Code.comp_shift("M", "LEFT"), "1100000")

    def test_shift_D_right(self):
        self.assertEqual(Code.comp_shift("D", "RIGHT"), "0010000")

    def test_shift_A_right(self):
        self.assertEqual(Code.comp_shift("A", "RIGHT"), "0000000")

    def test_shift_M_right(self):
        self.assertEqual(Code.comp_shift("M", "RIGHT"), "1000000")

    def test_shift_invalid_raises(self):
        with self.assertRaises(KeyError):
            Code.comp_shift("X", "LEFT")

    # -------------------------------------------------------------------
    # address_to_binary
    # -------------------------------------------------------------------

    def test_address_zero(self):
        self.assertEqual(Code.address_to_binary(0), "0" * 15)

    def test_address_42(self):
        self.assertEqual(Code.address_to_binary(42), "000000000101010")

    def test_address_max(self):
        self.assertEqual(Code.address_to_binary(32767), "1" * 15)

    def test_address_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            Code.address_to_binary(32768)


# ===========================================================================
# Tests de integracion — HackAssembler completo
# ===========================================================================

class TestHackAssemblerIntegration(unittest.TestCase):
    """Pruebas de integracion del ensamblador completo."""

    def _assemble_and_read(self, asm_content: str) -> list:
        """
        Helper: ensambla el contenido dado y devuelve las lineas del .hack.
        Limpia los archivos temporales al terminar.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".asm", delete=False, encoding="utf-8"
        ) as f:
            f.write(asm_content)
            asm_path = f.name

        hack_path = asm_path.replace(".asm", ".hack")

        try:
            assemble(asm_path)
            with open(hack_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
        finally:
            if os.path.exists(asm_path):
                os.remove(asm_path)
            if os.path.exists(hack_path):
                os.remove(hack_path)

        return lines

    def test_a_instruction_numeric(self):
        """@2 debe generar 0000000000000010."""
        lines = self._assemble_and_read("@2\n")
        self.assertEqual(lines[0], "0000000000000010")

    def test_a_instruction_zero(self):
        """@0 debe generar 16 ceros."""
        lines = self._assemble_and_read("@0\n")
        self.assertEqual(lines[0], "0000000000000000")

    def test_c_instruction_D_equals_A(self):
        """D=A debe generar 1110110000010000."""
        lines = self._assemble_and_read("D=A\n")
        # 111 + comp(A)=0110000 + dest(D)=010 + jump()=000
        self.assertEqual(lines[0], "1110110000010000")

    def test_c_instruction_jump(self):
        """0;JMP debe generar 1110101010000111."""
        lines = self._assemble_and_read("0;JMP\n")
        # 111 + comp(0)=0101010 + dest()=000 + jump(JMP)=111
        self.assertEqual(lines[0], "1110101010000111")

    def test_shift_left_D(self):
        """D=D<<1 debe generar 101 + comp_shift(D,LEFT) + dest(D) + 000."""
        lines = self._assemble_and_read("D=D<<1\n")
        expected = "101" + "0110000" + "010" + "000"
        self.assertEqual(lines[0], expected)

    def test_shift_right_M(self):
        """M=D>>1 debe generar 101 + comp_shift(D,RIGHT) + dest(M) + 000."""
        lines = self._assemble_and_read("M=D>>1\n")
        expected = "101" + "0010000" + "001" + "000"
        self.assertEqual(lines[0], expected)

    def test_shift_left_AM(self):
        """AM=M<<1 debe generar 101 + comp_shift(M,LEFT) + dest(AM) + 000."""
        lines = self._assemble_and_read("AM=M<<1\n")
        expected = "101" + "1100000" + "101" + "000"
        self.assertEqual(lines[0], expected)

    def test_label_resolution(self):
        """Las etiquetas deben resolverse al numero de instruccion correcto."""
        asm = (
            "@2\n"
            "D=A\n"
            "(LOOP)\n"
            "D=D-1\n"
            "@LOOP\n"
            "D;JGT\n"
        )
        lines = self._assemble_and_read(asm)
        # (LOOP) apunta a la instruccion 2 (D=D-1 es la tercera instruccion, indice 2)
        # @LOOP debe generar @2 → 0000000000000010
        self.assertEqual(lines[2], "1110001110010000")  # D=D-1
        self.assertEqual(lines[3], "0000000000000010")  # @LOOP = @2

    def test_variable_allocation(self):
        """Las variables nuevas deben asignarse desde RAM[16]."""
        asm = "@x\n@y\n"
        lines = self._assemble_and_read(asm)
        # x → RAM[16] → @16 → 0000000000010000
        # y → RAM[17] → @17 → 0000000000010001
        self.assertEqual(lines[0], "0000000000010000")
        self.assertEqual(lines[1], "0000000000010001")

    def test_predefined_symbol_R0(self):
        """@R0 debe resolverse como @0."""
        lines = self._assemble_and_read("@R0\n")
        self.assertEqual(lines[0], "0000000000000000")

    def test_predefined_symbol_SCREEN(self):
        """@SCREEN debe resolverse como @16384."""
        lines = self._assemble_and_read("@SCREEN\n")
        self.assertEqual(lines[0], "0100000000000000")

    def test_comments_and_blank_lines_ignored(self):
        """Comentarios y lineas vacias no deben generar instrucciones."""
        asm = (
            "// programa de prueba\n"
            "\n"
            "@5  // cargar 5\n"
        )
        lines = self._assemble_and_read(asm)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "0000000000000101")


# ===========================================================================
# Tests de integracion — HackDisassembler completo
# ===========================================================================

class TestHackDisassemblerIntegration(unittest.TestCase):
    """Pruebas de integracion del desensamblador completo."""

    def _disassemble_and_read(self, hack_content: str) -> list:
        """
        Helper: desensambla el contenido dado y devuelve las lineas del .asm.
        Limpia los archivos temporales al terminar.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".hack", delete=False, encoding="utf-8"
        ) as f:
            f.write(hack_content)
            hack_path = f.name

        dis_path = hack_path.replace(".hack", "Dis.asm")

        try:
            disassemble(hack_path)
            with open(dis_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
        finally:
            if os.path.exists(hack_path):
                os.remove(hack_path)
            if os.path.exists(dis_path):
                os.remove(dis_path)

        return lines

    def test_decode_a_instruction(self):
        """0000000000000010 debe decodificarse como @2."""
        lines = self._disassemble_and_read("0000000000000010\n")
        self.assertEqual(lines[0], "@2")

    def test_decode_a_instruction_zero(self):
        """0000000000000000 debe decodificarse como @0."""
        lines = self._disassemble_and_read("0000000000000000\n")
        self.assertEqual(lines[0], "@0")

    def test_decode_c_D_equals_A(self):
        """1110110000010000 debe decodificarse como D=A."""
        lines = self._disassemble_and_read("1110110000010000\n")
        self.assertEqual(lines[0], "D=A")

    def test_decode_c_jump(self):
        """1110101010000111 debe decodificarse como 0;JMP."""
        lines = self._disassemble_and_read("1110101010000111\n")
        self.assertEqual(lines[0], "0;JMP")

    def test_decode_shift_left_D(self):
        """101 0110000 010 000 debe decodificarse como D=D<<1."""
        bits = "101" + "0110000" + "010" + "000"
        lines = self._disassemble_and_read(bits + "\n")
        self.assertEqual(lines[0], "D=D<<1")

    def test_decode_shift_right_M(self):
        """101 0010000 001 000 debe decodificarse como M=D>>1."""
        bits = "101" + "0010000" + "001" + "000"
        lines = self._disassemble_and_read(bits + "\n")
        self.assertEqual(lines[0], "M=D>>1")

    def test_decode_shift_left_AM(self):
        """101 1100000 101 000 debe decodificarse como AM=M<<1."""
        bits = "101" + "1100000" + "101" + "000"
        lines = self._disassemble_and_read(bits + "\n")
        self.assertEqual(lines[0], "AM=M<<1")

    def test_roundtrip_assemble_disassemble(self):
        """
        Prueba de ida y vuelta: ensamblar y luego desensamblar debe
        recuperar las instrucciones originales (sin simbolos ni etiquetas).
        """
        asm_original = (
            "@42\n"
            "D=A\n"
            "D=D+1\n"
            "D=D<<1\n"
            "M=D>>1\n"
            "0;JMP\n"
        )
        expected = [
            "@42",
            "D=A",
            "D=D+1",
            "D=D<<1",
            "M=D>>1",
            "0;JMP",
        ]

        # Ensamblar
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".asm", delete=False, encoding="utf-8"
        ) as f:
            f.write(asm_original)
            asm_path = f.name

        hack_path = asm_path.replace(".asm", ".hack")
        dis_path  = hack_path.replace(".hack", "Dis.asm")

        try:
            assemble(asm_path)
            disassemble(hack_path)
            with open(dis_path, "r", encoding="utf-8") as f:
                result = [l.strip() for l in f.readlines() if l.strip()]
        finally:
            for path in [asm_path, hack_path, dis_path]:
                if os.path.exists(path):
                    os.remove(path)

        self.assertEqual(result, expected)


# ===========================================================================
# Punto de entrada
# ===========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)