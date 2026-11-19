"""
Autómata de pila que valida la estructura de bloques del archivo .red
(sección 13 del documento).

    M = (Q, Σ, Γ, δ, q0, Z0, F)
    Q = {q0, ..., q13, qf}     Γ = {Z0, R, Z}     F = {qf}
    Σ = {RED, ZONA, DISPOSITIVO, ENLACE, id, tipo, ip, num, {, }, ;}

La pila es una lista de Python: el tope es el último elemento.
  * push R al abrir el bloque de la RED, push Z al abrir una ZONA;
  * pop al leer '}' (Z cierra una zona, R cierra la red);
  * aceptación: estado qf, entrada consumida y solo Z0 en la pila.

En la tabla, "X" representa cualquier símbolo de bloque en el tope (R o Z),
que la transición conserva.
"""
from dataclasses import dataclass, field

from lenguajes.lexico import Token

FONDO = "Z0"

# δ(estado, entrada, tope) -> (nuevo estado, lista que reemplaza al tope, de abajo hacia arriba)
TRANSICIONES = {
    ("q0", "RED", "Z0"): ("q1", ["Z0"]),
    ("q1", "id", "Z0"): ("q2", ["Z0"]),
    ("q2", "{", "Z0"): ("q3", ["Z0", "R"]),         # push R
    ("q3", "ZONA", "X"): ("q4", ["X"]),
    ("q4", "id", "X"): ("q5", ["X"]),
    ("q5", "{", "X"): ("q3", ["X", "Z"]),           # push Z
    ("q3", "DISPOSITIVO", "X"): ("q6", ["X"]),
    ("q6", "id", "X"): ("q7", ["X"]),
    ("q7", "tipo", "X"): ("q8", ["X"]),
    ("q8", "ip", "X"): ("q9", ["X"]),
    ("q9", ";", "X"): ("q3", ["X"]),
    ("q3", "ENLACE", "X"): ("q10", ["X"]),
    ("q10", "id", "X"): ("q11", ["X"]),
    ("q11", "id", "X"): ("q12", ["X"]),
    ("q12", "num", "X"): ("q9", ["X"]),
    ("q3", "}", "Z"): ("q3", []),                    # pop Z: se cierra una zona
    ("q3", "}", "R"): ("q13", []),                   # pop R: se cierra la red
}
# Única transición ε: δ(q13, ε, Z0) = (qf, Z0)
TRANSICION_EPSILON = {("q13", "Z0"): ("qf", ["Z0"])}
ESTADOS_FINALES = {"qf"}

# Qué espera cada estado (para explicar los rechazos)
ESPERADO = {
    "q0": "la palabra RED",
    "q1": "el nombre de la red",
    "q2": "'{' para abrir el bloque de la red",
    "q3": "ZONA, DISPOSITIVO, ENLACE o '}'",
    "q4": "el nombre de la zona",
    "q5": "'{' para abrir el bloque de la zona",
    "q6": "el nombre del dispositivo",
    "q7": "un tipo de dispositivo (router, switch, pc, servidor, firewall)",
    "q8": "una dirección IPv4",
    "q9": "';' al final de la declaración",
    "q10": "el dispositivo de origen del enlace",
    "q11": "el dispositivo de destino del enlace",
    "q12": "la latencia del enlace (entero de 1 a 9999)",
    "q13": "el fin del archivo",
    "qf": "el fin del archivo",
}


@dataclass
class SimboloPila:
    """Símbolo de la pila. Además del símbolo formal guarda el nombre del bloque
    y la línea donde se abrió, solo para que la traza y los errores sean legibles."""
    simbolo: str
    nombre: str = ""
    linea: int = 0

    def __str__(self):
        return f"{self.simbolo}[{self.nombre}]" if self.nombre else self.simbolo


@dataclass
class PasoPila:
    numero: int
    estado: str
    entrada_restante: str
    transicion: str
    pila: str               # tope a la izquierda


@dataclass
class ResultadoPila:
    aceptada: bool
    pasos: list = field(default_factory=list)
    motivo: str = ""
    profundidad_maxima: int = 0
    linea_error: int = 0


def _normalizar(tokens):
    """Acepta Token o cadenas de tipos de token ("RED id { }")."""
    if isinstance(tokens, str):
        tokens = tokens.split()
    return [t if isinstance(t, Token) else Token(t, t, 0) for t in tokens]


def _texto_pila(pila):
    return " ".join(str(s) for s in reversed(pila))


def _texto_entrada(tokens, desde, limite=12):
    resto = [t.tipo for t in tokens[desde:]]
    if not resto:
        return "ε"
    return " ".join(resto[:limite]) + (" …" if len(resto) > limite else "")


class AutomataPila:
    def __init__(self, transiciones=TRANSICIONES, epsilon=TRANSICION_EPSILON):
        self.transiciones = transiciones
        self.epsilon = epsilon

    def buscar_transicion(self, estado, entrada, tope):
        """Primero busca una transición para el tope exacto; si no hay y el tope
        es un bloque (R o Z), busca la transición genérica con X."""
        clave = (estado, entrada, tope)
        if clave in self.transiciones:
            return self.transiciones[clave]
        if tope in ("R", "Z"):
            return self.transiciones.get((estado, entrada, "X"))
        return None

    def procesar(self, tokens):
        tokens = _normalizar(tokens)
        estado, pila, i = "q0", [SimboloPila(FONDO)], 0
        pasos = [PasoPila(0, estado, _texto_entrada(tokens, 0), "—", _texto_pila(pila))]
        profundidad = 0
        ultimo_id, linea_ultimo_id = "", 0

        while True:
            # Transición ε (no consume entrada)
            clave_e = (estado, pila[-1].simbolo)
            if clave_e in self.epsilon:
                estado, _ = self.epsilon[clave_e]
                pasos.append(PasoPila(len(pasos), estado, _texto_entrada(tokens, i),
                                      "ε, Z0 / Z0", _texto_pila(pila)))

            if i == len(tokens):
                if estado in ESTADOS_FINALES and pila[-1].simbolo == FONDO:
                    return ResultadoPila(True, pasos,
                                         "entrada consumida, estado final qf y pila = Z0",
                                         profundidad)
                return ResultadoPila(False, pasos, self._motivo_fin(estado, pila), profundidad,
                                     tokens[-1].linea if tokens else 0)

            token, tope = tokens[i], pila[-1]
            if estado in ESTADOS_FINALES:
                return ResultadoPila(False, pasos,
                                     self._prefijo(token) + f"sobra entrada después de cerrar la RED: '{token.lexema}'",
                                     profundidad, token.linea)

            destino = self.buscar_transicion(estado, token.tipo, tope.simbolo)
            if destino is None:
                return ResultadoPila(False, pasos,
                                     self._prefijo(token) + f"se esperaba {ESPERADO[estado]} y se encontró "
                                     f"'{token.lexema}' (no existe δ({estado}, {token.tipo}, {tope.simbolo}))",
                                     profundidad, token.linea)

            nuevo_estado, reemplazo = destino
            pila.pop()
            escritos = []
            for posicion, s in enumerate(reemplazo):
                if posicion == 0 and s in ("X", tope.simbolo):
                    pila.append(tope)                     # se conserva el tope
                    escritos.append(tope.simbolo)
                else:                                     # push R o Z con el nombre del bloque
                    pila.append(SimboloPila(s, ultimo_id, linea_ultimo_id))
                    escritos.append(s)
            # El nombre solo se conoce cuando los tokens vienen de un archivo real
            if token.tipo == "id" and token.linea:
                ultimo_id, linea_ultimo_id = token.lexema, token.linea
            profundidad = max(profundidad, len(pila) - 1)
            i += 1
            estado = nuevo_estado
            transicion = f"{token.tipo}, {tope.simbolo} / {' '.join(reversed(escritos)) or 'ε'}"
            pasos.append(PasoPila(len(pasos), estado, _texto_entrada(tokens, i), transicion, _texto_pila(pila)))

    @staticmethod
    def _prefijo(token):
        return f"línea {token.linea}: " if token.linea else ""

    @staticmethod
    def _motivo_fin(estado, pila):
        abiertos = [s for s in reversed(pila) if s.simbolo in ("R", "Z")]
        if abiertos:
            descripcion = ", ".join(
                ("ZONA" if s.simbolo == "Z" else "RED")
                + (f" '{s.nombre}'" if s.nombre else "")
                + (f" (abierta en la línea {s.linea})" if s.linea else "")
                for s in abiertos)
            return (f"el archivo terminó con la pila {_texto_pila(pila)}: "
                    f"hay bloques sin cerrar: {descripcion}")
        return f"el archivo terminó cuando se esperaba {ESPERADO[estado]}"
