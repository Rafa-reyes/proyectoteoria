"""
Autómata finito determinista.

    transiciones: diccionario (estado, símbolo) -> UN estado

Si falta una transición, el AFD se detiene y rechaza (equivale a ir a un
estado de error implícito).
"""
from automatas.afn import ResultadoRecorrido, formatear_conjunto


class AFD:
    def __init__(self, estados, alfabeto, transiciones, inicial, finales):
        self.estados = list(estados)          # lista para conservar el orden de creación
        self.alfabeto = tuple(alfabeto)
        self.transiciones = dict(transiciones)
        self.inicial = inicial
        self.finales = set(finales)
        if inicial not in self.estados:
            raise ValueError(f"el estado inicial {inicial} no está en Q")
        for (q, a), p in self.transiciones.items():
            if q not in self.estados or p not in self.estados or a not in self.alfabeto:
                raise ValueError(f"transición inválida δ({q}, {a}) = {p}")

    def delta(self, estado, simbolo):
        return self.transiciones.get((estado, simbolo))

    def es_completo(self):
        return all((q, a) in self.transiciones for q in self.estados for a in self.alfabeto)

    def procesar(self, cadena):
        """Procesa la cadena; pasos = [(símbolo, estado alcanzado), ...]."""
        actual = self.inicial
        pasos = [(None, actual)]
        for simbolo in cadena:
            if simbolo not in self.alfabeto:
                return ResultadoRecorrido(False, pasos,
                                          f"el símbolo '{simbolo}' no pertenece al alfabeto {formatear_conjunto(self.alfabeto)}")
            siguiente = self.delta(actual, simbolo)
            if siguiente is None:
                return ResultadoRecorrido(False, pasos, f"no existe la transición δ({actual}, {simbolo})")
            actual = siguiente
            pasos.append((simbolo, actual))
        aceptada = actual in self.finales
        motivo = (f"termina en {actual}, que es estado de aceptación" if aceptada
                  else f"termina en {actual}, que no es estado de aceptación")
        return ResultadoRecorrido(aceptada, pasos, motivo)

    def acepta(self, cadena):
        return self.procesar(cadena).aceptada

    def estado_final(self, cadena):
        """Estado en el que termina el AFD (útil para la máquina de estados)."""
        r = self.procesar(cadena)
        return r.pasos[-1][1]

    def tabla(self):
        filas = []
        for q in self.estados:
            marca = ("→ " if q == self.inicial else "") + ("* " if q in self.finales else "")
            filas.append([marca + q] + [self.delta(q, a) or "—" for a in self.alfabeto])
        return ["δ"] + list(self.alfabeto), filas
