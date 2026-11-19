"""
Autómata finito no determinista (sección 9 del documento).

Un AFN se representa con:
    estados       conjunto Q
    alfabeto      tupla Σ (el orden se usa para imprimir tablas)
    transiciones  diccionario (estado, símbolo) -> conjunto de estados
    inicial       q0
    finales       conjunto F

Para procesar una cadena se lleva el CONJUNTO de estados activos: en cada
símbolo se calcula mover(S, a) = ∪ δ(q, a) para q en S. Se admiten
transiciones ε (símbolo EPSILON) aunque el AFN del proyecto no las usa.
"""
from dataclasses import dataclass, field

EPSILON = "ε"


def formatear_conjunto(conjunto):
    """{q0, q1} ordenado, o ∅ si está vacío."""
    return "{" + ", ".join(sorted(conjunto)) + "}" if conjunto else "∅"


@dataclass
class ResultadoRecorrido:
    """Resultado de procesar una cadena en un AFN o AFD.

    pasos: lista de (símbolo leído, estado o conjunto alcanzado); el primer
    elemento tiene símbolo None y contiene la configuración inicial.
    """
    aceptada: bool
    pasos: list = field(default_factory=list)
    motivo: str = ""

    def texto(self, formato=str):
        partes = [formato(self.pasos[0][1])]
        for simbolo, estado in self.pasos[1:]:
            partes.append(f"—{simbolo}→ {formato(estado)}")
        return " ".join(partes)


class AFN:
    def __init__(self, estados, alfabeto, transiciones, inicial, finales):
        self.estados = set(estados)
        self.alfabeto = tuple(alfabeto)
        self.transiciones = {clave: frozenset(destinos) for clave, destinos in transiciones.items()}
        self.inicial = inicial
        self.finales = set(finales)
        self._validar()

    def _validar(self):
        """Comprueba que la definición formal sea consistente."""
        if self.inicial not in self.estados:
            raise ValueError(f"el estado inicial {self.inicial} no está en Q")
        if not self.finales <= self.estados:
            raise ValueError("F debe ser subconjunto de Q")
        for (q, a), destinos in self.transiciones.items():
            if q not in self.estados or not destinos <= self.estados:
                raise ValueError(f"la transición δ({q}, {a}) usa estados que no están en Q")
            if a not in self.alfabeto and a != EPSILON:
                raise ValueError(f"el símbolo {a} no pertenece a Σ")

    def delta(self, estado, simbolo):
        return self.transiciones.get((estado, simbolo), frozenset())

    def cerradura_epsilon(self, conjunto):
        """Estados alcanzables desde `conjunto` usando solo transiciones ε."""
        resultado = set(conjunto)
        pila = list(conjunto)
        while pila:
            q = pila.pop()
            for p in self.delta(q, EPSILON):
                if p not in resultado:
                    resultado.add(p)
                    pila.append(p)
        return frozenset(resultado)

    def mover(self, conjunto, simbolo):
        """mover(S, a) = ∪ δ(q, a) para q ∈ S."""
        resultado = set()
        for q in conjunto:
            resultado |= self.delta(q, simbolo)
        return frozenset(resultado)

    def procesar(self, cadena):
        """Procesa la cadena y devuelve el recorrido con los conjuntos de estados activos."""
        actual = self.cerradura_epsilon({self.inicial})
        pasos = [(None, actual)]
        for simbolo in cadena:
            if simbolo not in self.alfabeto:
                return ResultadoRecorrido(False, pasos,
                                          f"el símbolo '{simbolo}' no pertenece al alfabeto {formatear_conjunto(self.alfabeto)}")
            actual = self.cerradura_epsilon(self.mover(actual, simbolo))
            pasos.append((simbolo, actual))
        aceptada = bool(actual & self.finales)
        motivo = ("el conjunto final contiene un estado de aceptación" if aceptada
                  else "el conjunto final no contiene ningún estado de aceptación")
        return ResultadoRecorrido(aceptada, pasos, motivo)

    def acepta(self, cadena):
        return self.procesar(cadena).aceptada

    def tabla(self):
        """Filas de la tabla de transiciones: [estado marcado, δ(q, a) por cada a]."""
        simbolos = list(self.alfabeto)
        if any(a == EPSILON for (_, a) in self.transiciones):
            simbolos.append(EPSILON)
        filas = []
        for q in sorted(self.estados):
            marca = ("→ " if q == self.inicial else "") + ("* " if q in self.finales else "")
            filas.append([marca + q] + [formatear_conjunto(self.delta(q, a)) for a in simbolos])
        return ["δ"] + simbolos, filas


def crear_afn_falla():
    """AFN que reconoce L_falla = { w ∈ {r, l, t}* | w contiene tt }.

    q0 vigilando: con t "apuesta" a que inicia una falla -> δ(q0, t) = {q0, q1}
    q1 primer timeout: solo sigue si llega otro t
    q2 falla detectada (aceptación): permanece con cualquier evento
    """
    return AFN(
        estados={"q0", "q1", "q2"},
        alfabeto=("r", "l", "t"),
        transiciones={
            ("q0", "r"): {"q0"}, ("q0", "l"): {"q0"}, ("q0", "t"): {"q0", "q1"},
            ("q1", "t"): {"q2"},
            ("q2", "r"): {"q2"}, ("q2", "l"): {"q2"}, ("q2", "t"): {"q2"},
        },
        inicial="q0",
        finales={"q2"},
    )
