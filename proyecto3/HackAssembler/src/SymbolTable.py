"""
SymbolTable.py - Tabla de símbolos para el ensamblador Hack.

Autor 1: David Guerra Morales
Autor 2: Thomas Bedoya Rendón

Responsabilidad:
    Mantiene un diccionario que mapea nombres simbólicos (etiquetas y
    variables) a sus direcciones numéricas en memoria.

    Se inicializa con los símbolos predefinidos del lenguaje Hack y
    permite agregar nuevas entradas durante las dos pasadas del ensamblado:
        - Primera pasada : se registran las etiquetas (L_INSTRUCTION)
        - Segunda pasada : se registran las variables nuevas
"""


class SymbolTable:
    """
    Tabla de símbolos del ensamblador Hack.

    Uso típico:
        tabla = SymbolTable()
        tabla.add_entry("LOOP", 10)
        if tabla.contains("LOOP"):
            addr = tabla.get_address("LOOP")  # → 10
    """

    # Dirección de RAM donde comienzan las variables de usuario.
    # Las primeras 16 direcciones (0–15) son los registros R0–R15,
    # por eso las variables nuevas empiezan en la 16.
    _VARIABLE_BASE = 16

    def __init__(self):
        """
        Inicializa la tabla con todos los símbolos predefinidos del
        lenguaje Hack: registros R0–R15, punteros de E/S y registros
        especiales SP, LCL, ARG, THIS, THAT.
        """
        self._table = {
            # Registros de propósito general R0 – R15
            "R0":  0,  "R1":  1,  "R2":  2,  "R3":  3,
            "R4":  4,  "R5":  5,  "R6":  6,  "R7":  7,
            "R8":  8,  "R9":  9,  "R10": 10, "R11": 11,
            "R12": 12, "R13": 13, "R14": 14, "R15": 15,

            # Punteros de la máquina virtual
            "SP":   0,
            "LCL":  1,
            "ARG":  2,
            "THIS": 3,
            "THAT": 4,

            # Punteros de entrada/salida
            "SCREEN": 16384,
            "KBD":    24576,
        }

        # Próxima dirección disponible en RAM para variables de usuario
        self._next_variable_address = self._VARIABLE_BASE

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def add_entry(self, symbol: str, address: int):
        """
        Agrega un nuevo símbolo con su dirección a la tabla.

        Args:
            symbol:  Nombre del símbolo (ej: 'LOOP', 'var1').
            address: Dirección numérica asociada.

        Raises:
            ValueError: Si el símbolo ya existe en la tabla.
        """
        if self.contains(symbol):
            raise ValueError(
                f"El símbolo '{symbol}' ya existe en la tabla "
                f"con la dirección {self._table[symbol]}."
            )
        self._table[symbol] = address

    def add_variable(self, symbol: str) -> int:
        """
        Registra una variable nueva asignándole la siguiente dirección
        de RAM disponible (empieza en 16 y avanza de uno en uno).

        Si la variable ya existe, simplemente devuelve su dirección sin
        crear una entrada duplicada.

        Args:
            symbol: Nombre de la variable nueva.

        Returns:
            int: Dirección de RAM asignada a la variable.
        """
        if not self.contains(symbol):
            self._table[symbol] = self._next_variable_address
            self._next_variable_address += 1
        return self._table[symbol]

    def contains(self, symbol: str) -> bool:
        """
        Indica si el símbolo ya está registrado en la tabla.

        Args:
            symbol: Nombre del símbolo a buscar.

        Returns:
            bool: True si existe, False si no.
        """
        return symbol in self._table

    def get_address(self, symbol: str) -> int:
        """
        Devuelve la dirección numérica asociada al símbolo.

        Args:
            symbol: Nombre del símbolo a consultar.

        Returns:
            int: Dirección numérica del símbolo.

        Raises:
            KeyError: Si el símbolo no existe en la tabla.
        """
        if not self.contains(symbol):
            raise KeyError(
                f"El símbolo '{symbol}' no existe en la tabla de símbolos."
            )
        return self._table[symbol]

    def __repr__(self) -> str:
        """Representación legible de la tabla, útil para depuración."""
        entries = "\n".join(
            f"  {sym:<10} → {addr}"
            for sym, addr in sorted(self._table.items())
        )
        return f"SymbolTable(\n{entries}\n)"