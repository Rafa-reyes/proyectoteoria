"""Reporte de texto con el análisis completo de la red."""
from datetime import datetime
from pathlib import Path

from red import algoritmos as alg
from reportes.visualizacion import tabla_texto, arbol_rutas


def generar_reporte(grafo, origen=None, descripcion=""):
    """Devuelve el texto del reporte. `origen` define el árbol de rutas."""
    s = []
    s.append("=" * 64)
    s.append("NETWORK GRAPH ANALYZER — REPORTE DE LA RED")
    s.append("=" * 64)
    s.append(f"Fecha: {datetime.now():%d/%m/%Y %H:%M}")
    if descripcion:
        s.append(f"Origen de los datos: {descripcion}")
    s.append("")
    s.append(f"|V| = {grafo.num_vertices()}    |E| = {grafo.num_aristas()}")
    s.append("V = {" + ", ".join(grafo.vertices()) + "}")
    s.append("E = {" + ", ".join(f"{{{u}, {v}}}({w})" for u, v, w in grafo.aristas()) + "}")

    s.append("\n--- Lista de adyacencia ---")
    filas = [[v, ", ".join(f"{n} ({w})" for n, w in grafo.vecinos(v).items()) or "∅ (aislado)",
              grafo.grado(v)] for v in grafo.vertices()]
    s.append(tabla_texto(["Vértice", "Vecinos (latencia ms)", "Grado"], filas))

    if grafo.num_vertices() <= 20:
        s.append("\n--- Matriz de adyacencia ponderada ---")
        orden, matriz = grafo.matriz_adyacencia()
        s.append(tabla_texto([""] + orden, [[orden[i]] + fila for i, fila in enumerate(matriz)]))

    s.append("\n--- Dispositivos ---")
    s.append(tabla_texto(["Nombre", "Tipo", "IP", "Zona", "Estado"],
                         [[d.nombre, d.tipo, d.ip or "—", d.zona or "—", d.estado]
                          for d in grafo.dispositivos.values()]))

    componentes = alg.componentes_conexas(grafo)
    s.append(f"\n--- Componentes conexas: {len(componentes)} ---")
    for i, c in enumerate(componentes, 1):
        s.append(f"  {i}. {{{', '.join(c)}}}")

    grados = alg.grados(grafo)
    if grados:
        maximo = max(grados.values())
        s.append("\n--- Grados ---")
        s.append(f"  Grado máximo: {maximo} ({', '.join(v for v, g in grados.items() if g == maximo)})")
        s.append(f"  Aislados: {', '.join(alg.aislados(grafo)) or 'ninguno'}")

    ciclos = alg.detectar_ciclos(grafo)
    s.append("\n--- Ciclos (redundancia) ---")
    s.append("\n".join("  " + " – ".join(c) for c in ciclos) if ciclos else "  No hay ciclos.")

    articulaciones, puentes = alg.puntos_criticos(grafo)
    s.append("\n--- Puntos críticos ---")
    s.append(f"  Articulaciones (puntos únicos de falla): {', '.join(articulaciones) or 'ninguna'}")
    s.append(f"  Puentes (enlaces críticos): {', '.join(f'{u}–{v}' for u, v in puentes) or 'ninguno'}")

    if grafo.num_vertices():
        origen = origen if origen and grafo.existe(origen) else grafo.vertices()[0]
        s.append(f"\n--- Árbol de rutas más cortas desde {origen} ---")
        s.append(arbol_rutas(grafo, origen))
    return "\n".join(s) + "\n"


def guardar_reporte(texto, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")
    return ruta
