"""
Parser.py - Módulo de análisis sintáctico para el ensamblador Hack.

Autor 1: David Guerra Morales
Autor 2: Thomas Bedoya Rendón

Responsabilidad:
    Lee un archivo .asm línea por línea, elimina comentarios y espacios
    en blanco, e identifica el tipo de cada instrucción:
        - A_INSTRUCTION  : @valor
        - C_INSTRUCTION  : dest=comp;jump
        - SHIFT_INSTRUCTION: dest=reg<<1  /  dest=reg>>1
        - L_INSTRUCTION  : (ETIQUETA)
"""

# Tipos de instrucción
A_INSTRUCTION   = "A_INSTRUCTION"
C_INSTRUCTION   = "C_INSTRUCTION"
SHIFT_INSTRUCTION = "SHIFT_INSTRUCTION"
L_INSTRUCTION   = "L_INSTRUCTION"


class Parser:
    """
    Recorre un archivo .asm instrucción por instrucción.

    Uso típico:
        parser = Parser("Prog.asm")
        while parser.has_more_lines():
            parser.advance()
            tipo = parser.instruction_type()
            ...
    """

    def __init__(self, filepath: str):
        """
        Abre el archivo y carga todas las líneas válidas (sin comentarios
        ni líneas vacías) junto con su número de línea original en el
        archivo fuente (útil para reportar errores).

        Args:
            filepath: Ruta al archivo .asm a leer.

        Raises:
            FileNotFoundError: Si el archivo no existe.
        """
        self._lines = []          # Lista de (num_linea_original, texto_limpio)
        self._current_index = -1  # Apunta a la instrucción actual
        self._current_line = ""   # Texto limpio de la instrucción actual

        with open(filepath, "r", encoding="utf-8-sig") as f:
            for num, raw in enumerate(f, start=1):
                clean = self._clean(raw)
                if clean:
                    self._lines.append((num, clean))

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    @staticmethod
    def _clean(line: str) -> str:
        """
        Elimina comentarios inline y espacios sobrantes.
        Devuelve cadena vacía si la línea no tiene contenido útil.
        """
        # Quitar comentario (todo lo que esté después de //)
        if "//" in line:
            line = line[:line.index("//")]
        return line.strip()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def has_more_lines(self) -> bool:
        """Devuelve True si quedan instrucciones por procesar."""
        return self._current_index < len(self._lines) - 1

    def advance(self):
        """
        Lee la siguiente instrucción y la convierte en la instrucción
        actual. Solo debe llamarse si has_more_lines() es True.
        """
        self._current_index += 1
        self._current_line = self._lines[self._current_index][1]

    def current_line_number(self) -> int:
        """
        Devuelve el número de línea ORIGINAL en el archivo fuente de la
        instrucción actual (para mensajes de error).
        """
        return self._lines[self._current_index][0]

    def instruction_type(self) -> str:
        """
        Devuelve el tipo de la instrucción actual:
            A_INSTRUCTION    → empieza con @
            L_INSTRUCTION    → tiene formato (SÍMBOLO)
            SHIFT_INSTRUCTION→ contiene << o >>
            C_INSTRUCTION    → cualquier otra instrucción válida

        Raises:
            SyntaxError: Si la instrucción no encaja en ningún tipo.
        """
        line = self._current_line

        if line.startswith("@"):
            return A_INSTRUCTION

        if line.startswith("(") and line.endswith(")"):
            return L_INSTRUCTION

        if "<<" in line or ">>" in line:
            return SHIFT_INSTRUCTION

        # Validación mínima: debe contener = o ; para ser instrucción C
        if "=" in line or ";" in line:
            return C_INSTRUCTION

        raise SyntaxError(
            f"Línea {self.current_line_number()}: "
            f"instrucción no reconocida → '{line}'"
        )

    def symbol(self) -> str:
        """
        Para A_INSTRUCTION: devuelve el símbolo o número después del @.
        Para L_INSTRUCTION: devuelve el nombre de la etiqueta sin paréntesis.

        Returns:
            str: El símbolo extraído.

        Raises:
            TypeError: Si se llama sobre una instrucción que no es A ni L.
        """
        t = self.instruction_type()

        if t == A_INSTRUCTION:
            return self._current_line[1:]  # quita el @

        if t == L_INSTRUCTION:
            return self._current_line[1:-1]  # quita ( y )

        raise TypeError(
            f"Línea {self.current_line_number()}: "
            f"symbol() solo aplica a A_INSTRUCTION o L_INSTRUCTION."
        )

    def dest(self) -> str:
        """
        Para C_INSTRUCTION: devuelve la parte 'dest' (antes del =).
        Si no hay =, devuelve cadena vacía (dest es opcional).

        Raises:
            TypeError: Si se llama sobre una instrucción que no es C.
        """
        if self.instruction_type() != C_INSTRUCTION:
            raise TypeError(
                f"Línea {self.current_line_number()}: "
                f"dest() solo aplica a C_INSTRUCTION."
            )
        if "=" in self._current_line:
            return self._current_line.split("=")[0]
        return ""

    def comp(self) -> str:
        """
        Para C_INSTRUCTION: devuelve la parte 'comp' (entre = y ;).
        Si no hay =, toma desde el inicio; si no hay ;, toma hasta el fin.

        Raises:
            TypeError: Si se llama sobre una instrucción que no es C.
        """
        if self.instruction_type() != C_INSTRUCTION:
            raise TypeError(
                f"Línea {self.current_line_number()}: "
                f"comp() solo aplica a C_INSTRUCTION."
            )
        line = self._current_line
        # Quitar la parte dest si existe
        if "=" in line:
            line = line.split("=", 1)[1]
        # Quitar la parte jump si existe
        if ";" in line:
            line = line.split(";", 1)[0]
        return line

    def jump(self) -> str:
        """
        Para C_INSTRUCTION: devuelve la parte 'jump' (después del ;).
        Si no hay ;, devuelve cadena vacía (jump es opcional).

        Raises:
            TypeError: Si se llama sobre una instrucción que no es C.
        """
        if self.instruction_type() != C_INSTRUCTION:
            raise TypeError(
                f"Línea {self.current_line_number()}: "
                f"jump() solo aplica a C_INSTRUCTION."
            )
        if ";" in self._current_line:
            return self._current_line.split(";", 1)[1]
        return ""

    def shift_dest(self) -> str:
        """
        Para SHIFT_INSTRUCTION: devuelve la parte 'dest' (antes del =).

        Ejemplo: 'D=M<<1'  →  'D'
                 'AM=D>>1' →  'AM'

        Raises:
            TypeError: Si se llama sobre una instrucción que no es SHIFT.
        """
        if self.instruction_type() != SHIFT_INSTRUCTION:
            raise TypeError(
                f"Línea {self.current_line_number()}: "
                f"shift_dest() solo aplica a SHIFT_INSTRUCTION."
            )
        return self._current_line.split("=")[0]

    def shift_source(self) -> str:
        """
        Para SHIFT_INSTRUCTION: devuelve el registro fuente (D, A o M).

        Ejemplo: 'D=M<<1'  →  'M'
                 'AM=D>>1' →  'D'

        Raises:
            TypeError: Si se llama sobre una instrucción que no es SHIFT.
            SyntaxError: Si el registro no es D, A ni M.
        """
        if self.instruction_type() != SHIFT_INSTRUCTION:
            raise TypeError(
                f"Línea {self.current_line_number()}: "
                f"shift_source() solo aplica a SHIFT_INSTRUCTION."
            )
        # Parte derecha del =
        rhs = self._current_line.split("=", 1)[1]
        # Quitar el operador << o >>
        src = rhs.replace("<<1", "").replace(">>1", "").strip()
        if src not in ("D", "A", "M"):
            raise SyntaxError(
                f"Línea {self.current_line_number()}: "
                f"registro de shift no válido → '{src}'. Use D, A o M."
            )
        return src

    def shift_direction(self) -> str:
        """
        Para SHIFT_INSTRUCTION: devuelve 'LEFT' o 'RIGHT'.

        Raises:
            TypeError: Si se llama sobre una instrucción que no es SHIFT.
        """
        if self.instruction_type() != SHIFT_INSTRUCTION:
            raise TypeError(
                f"Línea {self.current_line_number()}: "
                f"shift_direction() solo aplica a SHIFT_INSTRUCTION."
            )
        if "<<" in self._current_line:
            return "LEFT"
        return "RIGHT"
