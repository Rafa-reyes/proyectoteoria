"""
Conversión AFN -> AFD por construcción de subconjuntos (sección 10 del documento)
y minimización del AFD por refinamiento de particiones (sección 10.8).

Procedimiento de subconjuntos:
  1. El estado inicial del AFD es la cerradura-ε de {q0}; se nombra A.
  2. Para cada conjunto pendiente S y cada símbolo a: destino = cerradura-ε(mover(S, a)).
  3. Si el conjunto destino es nuevo, se le asigna un nombre y queda pendiente.
  4. Termina cuando no aparecen conjuntos nuevos.
  5. Un estado del AFD es final si contiene algún estado final del AFN.
"""
from collections import deque
from dataclasses import dataclass

from automatas.afd import AFD
from automatas.afn import formatear_conjunto


@dataclass
class PasoSubconjuntos:
    """Una fila de la tabla del procedimiento."""
    estado: str          # nombre del conjunto que se procesa
    conjunto: frozenset
    simbolo: str
    calculo: str         # δ(q0,t)={q0, q1} ∪ ...
    destino: frozenset
    nombre_destino: str
    nuevo: bool


def nombre_para(indice):
    """A, B, ..., Z, y después S26, S27, ..."""
    return chr(ord("A") + indice) if indice < 26 else f"S{indice}"


def afn_a_afd(afn):
    """Devuelve (afd, pasos, nombres) donde nombres: frozenset -> nombre del estado."""
    inicial = afn.cerradura_epsilon({afn.inicial})
    nombres = {inicial: nombre_para(0)}
    pendientes = deque([inicial])
    transiciones, pasos = {}, []

    while pendientes:
        actual = pendientes.popleft()
        for a in afn.alfabeto:
            destino = afn.cerradura_epsilon(afn.mover(actual, a))
            nuevo = destino not in nombres
            if nuevo:
                nombres[destino] = nombre_para(len(nombres))
                pendientes.append(destino)
            transiciones[(nombres[actual], a)] = nombres[destino]
            calculo = " ∪ ".join(f"δ({q},{a})={formatear_conjunto(afn.delta(q, a))}"
                                 for q in sorted(actual)) or "∅"
            pasos.append(PasoSubconjuntos(nombres[actual], actual, a, calculo, destino,
                                          nombres[destino], nuevo))

    finales = {n for conjunto, n in nombres.items() if conjunto & afn.finales}
    afd = AFD(list(nombres.values()), afn.alfabeto, transiciones, nombres[inicial], finales)
    return afd, pasos, nombres


def estados_alcanzables(afd):
    alcanzados, cola = {afd.inicial}, deque([afd.inicial])
    while cola:
        q = cola.popleft()
        for a in afd.alfabeto:
            p = afd.delta(q, a)
            if p is not None and p not in alcanzados:
                alcanzados.add(p)
                cola.append(p)
    return [q for q in afd.estados if q in alcanzados]


def minimizar(afd):
    """Minimiza un AFD completo por refinamiento de particiones.

    P0 = {finales, no finales}. En cada ronda se separan los estados de un grupo
    cuyos destinos caen en grupos distintos para algún símbolo. Se detiene cuando
    la partición ya no cambia. Devuelve (afd_minimo, historial_de_particiones).
    """
    estados = estados_alcanzables(afd)
    finales = [q for q in estados if q in afd.finales]
    no_finales = [q for q in estados if q not in afd.finales]
    particion = [g for g in (no_finales, finales) if g]
    historial = [particion]

    while True:
        grupo_de = {q: i for i, g in enumerate(particion) for q in g}
        nueva = []
        for grupo in particion:
            # firma: a qué grupo va el estado con cada símbolo
            subgrupos = {}
            for q in grupo:
                firma = tuple(grupo_de.get(afd.delta(q, a)) for a in afd.alfabeto)
                subgrupos.setdefault(firma, []).append(q)
            nueva.extend(subgrupos.values())
        if len(nueva) == len(particion):
            break
        particion = nueva
        historial.append(particion)

    def nombre_grupo(g):
        return "".join(g) if all(len(q) == 1 for q in g) else "/".join(g)

    grupo_de = {q: nombre_grupo(g) for g in particion for q in g}
    transiciones = {}
    for g in particion:
        representante = g[0]
        for a in afd.alfabeto:
            p = afd.delta(representante, a)
            if p is not None:
                transiciones[(nombre_grupo(g), a)] = grupo_de[p]
    minimo = AFD([nombre_grupo(g) for g in particion], afd.alfabeto, transiciones,
                 grupo_de[afd.inicial], {grupo_de[q] for q in finales})
    return minimo, historial


def formatear_particion(particion):
    return "{ " + ", ".join("{" + ", ".join(g) + "}" for g in particion) + " }"
