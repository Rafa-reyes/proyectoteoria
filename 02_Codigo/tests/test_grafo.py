"""Pruebas del grafo y de los algoritmos contra los resultados calculados a mano (sección 6.6)."""
import pytest

from red import algoritmos as alg
from red.grafo import Grafo, ErrorEntrada, cargar_desde_lineas
from tests.casos_sistema import red_ejemplo


def test_representacion():
    g = red_ejemplo()
    assert g.num_vertices() == 8 and g.num_aristas() == 7
    orden, matriz = g.matriz_adyacencia()
    # la matriz de un grafo no dirigido es simétrica
    assert all(matriz[i][j] == matriz[j][i] for i in range(8) for j in range(8))
    assert matriz[orden.index("PC2")][orden.index("DB")] == 4
    # lema del apretón de manos
    assert sum(alg.grados(g).values()) == 2 * g.num_aristas()


def test_traza_de_dijkstra_igual_a_la_del_documento():
    _, padre, traza = alg.dijkstra(red_ejemplo(), "Router1")
    extraidos = [(u, d) for u, d, _ in traza]
    assert extraidos == [("Router1", 0), ("Switch1", 2), ("PC1", 3), ("PC2", 3),
                         ("Switch2", 3), ("Server", 4), ("DB", 6)]
    assert padre["DB"] == "Server"


def test_componentes_conexas():
    assert alg.componentes_conexas(red_ejemplo()) == [
        ["Router1", "Switch1", "Switch2", "PC1", "PC2", "Server", "DB"], ["Impresora1"]]


def test_rutas_alternativas_ordenadas_por_costo():
    rutas, completo = alg.rutas_alternativas(red_ejemplo(), "Router1", "DB")
    assert completo
    assert rutas == [(["Router1", "Switch2", "Server", "DB"], 6), (["Router1", "Switch1", "PC2", "DB"], 7)]


def test_impacto_falla_de_switch1_aisla_a_pc1():
    impacto = alg.impacto_falla(red_ejemplo(), ["Switch1"])
    assert ("PC1", "Router1") in impacto["pares_incomunicados"] or \
           ("Router1", "PC1") in impacto["pares_incomunicados"]


def test_arbol_sin_ciclos():
    g = cargar_desde_lineas(["A,B", "B,C", "C,D"]).grafo
    assert alg.detectar_ciclos(g) == []
    art, puentes = alg.puntos_criticos(g)
    assert set(art) == {"B", "C"} and len(puentes) == 3


def test_lazo_y_latencia_no_positiva_se_rechazan():
    g = Grafo()
    with pytest.raises(ErrorEntrada):
        g.agregar_enlace("A", "A", 1)
    with pytest.raises(ErrorEntrada):
        g.agregar_enlace("A", "B", 0)


def test_verificacion_cruzada_con_networkx():
    """networkx solo se usa aquí, como referencia independiente, nunca en el programa."""
    nx = pytest.importorskip("networkx")
    g = red_ejemplo()
    ref = nx.Graph()
    ref.add_nodes_from(g.vertices())
    ref.add_weighted_edges_from(g.aristas())
    assert set(alg.puntos_criticos(g)[0]) == set(nx.articulation_points(ref))
    for o in g.vertices():
        dist, _, _ = alg.dijkstra(g, o)
        esperado = nx.single_source_dijkstra_path_length(ref, o)
        assert {v: d for v, d in dist.items() if d != alg.INFINITO} == esperado
