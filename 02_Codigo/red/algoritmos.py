"""
Algoritmos sobre el grafo de la red (sección 6.5 del documento).

Todos están programados a mano; ninguno usa bibliotecas de grafos.

    existe_ruta / bfs           -> conectividad (BFS)
    componentes_conexas         -> segmentos incomunicados
    dijkstra / ruta_mas_corta   -> ruta de menor latencia
    grados / aislados           -> carga de cada dispositivo
    detectar_ciclos             -> redundancia (DFS con control del padre)
    puntos_criticos             -> articulaciones y puentes (Tarjan)
    rutas_alternativas          -> rutas simples ordenadas por costo (DFS con retroceso)
    impacto_falla               -> qué cambia al retirar dispositivos
"""
import heapq
from collections import deque

INFINITO = float("inf")


# ----------------------------------------------------------------------
# Recorridos
# ----------------------------------------------------------------------
def bfs(grafo, origen):
    """Búsqueda en amplitud. Devuelve (orden de visita, padre de cada vértice)."""
    visitados = {origen}
    padre = {origen: None}
    orden = []
    cola = deque([origen])
    while cola:
        u = cola.popleft()
        orden.append(u)
        for v in grafo.vecinos(u):
            if v not in visitados:
                visitados.add(v)
                padre[v] = u
                cola.append(v)
    return orden, padre


def dfs(grafo, origen):
    """Búsqueda en profundidad (recursiva). Devuelve el orden de visita."""
    orden, visitados = [], set()

    def visitar(u):
        visitados.add(u)
        orden.append(u)
        for v in grafo.vecinos(u):
            if v not in visitados:
                visitar(v)

    visitar(origen)
    return orden


def reconstruir_camino(padre, destino):
    """Sigue los padres desde el destino hasta el origen."""
    camino = []
    actual = destino
    while actual is not None:
        camino.append(actual)
        actual = padre[actual]
    return list(reversed(camino))


def existe_ruta(grafo, origen, destino):
    """Devuelve el camino con menos saltos (BFS) o None si no hay ruta."""
    _, padre = bfs(grafo, origen)
    if destino not in padre:
        return None
    return reconstruir_camino(padre, destino)


def componentes_conexas(grafo):
    """BFS repetido desde cada vértice todavía no visitado."""
    visitados, componentes = set(), []
    for v in grafo.vertices():
        if v not in visitados:
            orden, _ = bfs(grafo, v)
            visitados.update(orden)
            componentes.append(orden)
    return componentes


# ----------------------------------------------------------------------
# Ruta más corta
# ----------------------------------------------------------------------
def dijkstra(grafo, origen):
    """Algoritmo de Dijkstra con cola de prioridad (heapq).

    Devuelve (distancia, padre, traza). La traza tiene una entrada por vértice
    extraído: (vértice, distancia, [(vecino, distancia_anterior, distancia_nueva), ...]).
    """
    distancia = {v: INFINITO for v in grafo.vertices()}
    padre = {v: None for v in grafo.vertices()}
    distancia[origen] = 0
    cola = [(0, origen)]
    definitivos = set()
    traza = []
    while cola:
        d, u = heapq.heappop(cola)
        if u in definitivos:          # entrada vieja de la cola: ya se procesó
            continue
        definitivos.add(u)
        relajaciones = []
        for v, w in grafo.vecinos(u).items():
            if v not in definitivos and d + w < distancia[v]:
                relajaciones.append((v, distancia[v], d + w))
                distancia[v] = d + w
                padre[v] = u
                heapq.heappush(cola, (distancia[v], v))
        traza.append((u, d, relajaciones))
    return distancia, padre, traza


def ruta_mas_corta(grafo, origen, destino):
    """Devuelve (camino, latencia_total) o None si el destino no es alcanzable."""
    distancia, padre, _ = dijkstra(grafo, origen)
    if distancia[destino] == INFINITO:
        return None
    return reconstruir_camino(padre, destino), distancia[destino]


def costo_camino(grafo, camino):
    return sum(grafo.latencia(camino[i], camino[i + 1]) for i in range(len(camino) - 1))


# ----------------------------------------------------------------------
# Grados y aislados
# ----------------------------------------------------------------------
def grados(grafo):
    return {v: grafo.grado(v) for v in grafo.vertices()}


def aislados(grafo):
    return [v for v in grafo.vertices() if grafo.grado(v) == 0]


# ----------------------------------------------------------------------
# Ciclos
# ----------------------------------------------------------------------
def detectar_ciclos(grafo):
    """Encuentra un ciclo por cada componente que tenga alguno.

    DFS con control del padre: en un grafo no dirigido, un vecino ya visitado
    que NO es el padre cierra un ciclo. El ciclo se recupera con la cadena de padres.
    """
    visitados, padre, ciclos = set(), {}, []

    def visitar(u):
        visitados.add(u)
        for v in grafo.vecinos(u):
            if v not in visitados:
                padre[v] = u
                ciclo = visitar(v)
                if ciclo:
                    return ciclo
            elif v != padre[u]:
                # u -> ... -> v por padres, y la arista {u, v} cierra el ciclo
                camino = [u]
                while camino[-1] != v:
                    camino.append(padre[camino[-1]])
                ciclo = list(reversed(camino))      # v ... u
                return ciclo + [ciclo[0]]           # se cierra regresando a v
        return None

    for v in grafo.vertices():
        if v not in visitados:
            padre[v] = None
            ciclo = visitar(v)
            if ciclo:
                ciclos.append(ciclo)
            # se marcan como visitados los demás vértices de la componente
            orden, _ = bfs(grafo, v)
            visitados.update(orden)
    return ciclos


# ----------------------------------------------------------------------
# Puntos críticos (Tarjan)
# ----------------------------------------------------------------------
def puntos_criticos(grafo):
    """Articulaciones (puntos únicos de falla) y puentes (enlaces críticos).

    disc[v]: momento en que el DFS descubre v.
    low[v] : menor disc alcanzable desde el subárbol de v usando a lo sumo
             una arista de retroceso.
    u (no raíz) es articulación si tiene un hijo v con low[v] >= disc[u];
    la raíz lo es si tiene 2 o más hijos. {u, v} es puente si low[v] > disc[u].
    """
    disc, low, padre = {}, {}, {}
    articulaciones, puentes = [], []
    reloj = [0]

    def visitar(u):
        reloj[0] += 1
        disc[u] = low[u] = reloj[0]
        hijos = 0
        for v in grafo.vecinos(u):
            if v not in disc:
                padre[v] = u
                hijos += 1
                visitar(v)
                low[u] = min(low[u], low[v])
                if padre[u] is not None and low[v] >= disc[u] and u not in articulaciones:
                    articulaciones.append(u)
                if low[v] > disc[u]:
                    puentes.append((u, v))
            elif v != padre[u]:
                low[u] = min(low[u], disc[v])
        if padre[u] is None and hijos >= 2:
            articulaciones.append(u)

    for v in grafo.vertices():
        if v not in disc:
            padre[v] = None
            visitar(v)
    return articulaciones, puentes


# ----------------------------------------------------------------------
# Rutas alternativas
# ----------------------------------------------------------------------
def rutas_alternativas(grafo, origen, destino, maximo=5, limite_exploracion=20000):
    """Rutas simples de origen a destino ordenadas por latencia (DFS con retroceso).

    Devuelve (rutas, completo). `completo` es False si se alcanzó el límite de
    exploración (en redes grandes el número de rutas simples crece muy rápido).
    """
    encontradas = []
    camino = [origen]
    en_camino = {origen}
    explorados = [0]

    def explorar(u, costo):
        explorados[0] += 1
        if explorados[0] > limite_exploracion:
            return
        if u == destino:
            encontradas.append((list(camino), costo))
            return
        for v, w in grafo.vecinos(u).items():
            if v not in en_camino:
                camino.append(v)
                en_camino.add(v)
                explorar(v, costo + w)
                camino.pop()            # retroceso
                en_camino.discard(v)

    explorar(origen, 0)
    encontradas.sort(key=lambda r: (r[1], len(r[0])))
    return encontradas[:maximo], explorados[0] <= limite_exploracion


# ----------------------------------------------------------------------
# Impacto de falla
# ----------------------------------------------------------------------
def impacto_falla(grafo, nodos_falla):
    """Compara la red antes y después de retirar los dispositivos en falla."""
    restante = grafo.subgrafo_sin(nodos_falla)
    antes = componentes_conexas(grafo)
    despues = componentes_conexas(restante)
    # Pares de dispositivos (que siguen activos) que antes se comunicaban y ahora no
    comp_antes = {v: i for i, c in enumerate(antes) for v in c}
    comp_despues = {v: i for i, c in enumerate(despues) for v in c}
    incomunicados = []
    vivos = restante.vertices()
    for i, u in enumerate(vivos):
        for v in vivos[i + 1:]:
            if comp_antes[u] == comp_antes[v] and comp_despues[u] != comp_despues[v]:
                incomunicados.append((u, v))
    return {"grafo": restante, "componentes_antes": antes, "componentes_despues": despues,
            "pares_incomunicados": incomunicados}
