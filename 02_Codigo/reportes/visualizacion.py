"""
Presentación de resultados: tablas de texto, árbol de rutas e imágenes PNG.

matplotlib se usa solo para dibujar (uso permitido por el enunciado). networkx,
si está instalado, solo calcula la posición de los nodos en el dibujo; ningún
algoritmo del proyecto depende de esas bibliotecas. Si no están instaladas, el
programa sigue funcionando y solo se desactiva la exportación de imágenes.
"""
import math
from pathlib import Path

from red.algoritmos import dijkstra, INFINITO


# ----------------------------------------------------------------------
# Texto
# ----------------------------------------------------------------------
def tabla_texto(encabezados, filas, margen="  "):
    """Tabla alineada en columnas para la consola."""
    filas = [[str(c) for c in f] for f in filas]
    anchos = [len(h) for h in encabezados]
    for f in filas:
        for i, c in enumerate(f):
            anchos[i] = max(anchos[i], len(c))
    lineas = [margen + "  ".join(h.ljust(anchos[i]) for i, h in enumerate(encabezados)),
              margen + "  ".join("─" * a for a in anchos)]
    for f in filas:
        lineas.append(margen + "  ".join(c.ljust(anchos[i]) for i, c in enumerate(f)))
    return "\n".join(lineas)


def arbol_rutas(grafo, origen):
    """Árbol de rutas más cortas (padres de Dijkstra) dibujado con caracteres.

    Cada nodo muestra su latencia acumulada desde el origen.
    """
    distancia, padre, _ = dijkstra(grafo, origen)
    hijos = {v: [] for v in grafo.vertices()}
    for v in grafo.vertices():
        if padre[v] is not None:
            hijos[padre[v]].append(v)

    lineas = [origen]

    def dibujar(nodo, prefijo):
        for i, h in enumerate(hijos[nodo]):
            ultimo = i == len(hijos[nodo]) - 1
            lineas.append(f"{prefijo}{'└── ' if ultimo else '├── '}{h} ({distancia[h]} ms)")
            dibujar(h, prefijo + ("    " if ultimo else "│   "))

    dibujar(origen, "")
    inalcanzables = [v for v in grafo.vertices() if distancia[v] == INFINITO]
    if inalcanzables:
        lineas.append("")
        lineas.append(f"No alcanzables desde {origen}: {', '.join(inalcanzables)}")
    return "\n".join(lineas)


# ----------------------------------------------------------------------
# Imágenes
# ----------------------------------------------------------------------
class VisualizacionNoDisponible(Exception):
    pass


def _pyplot():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except ImportError:
        raise VisualizacionNoDisponible(
            "matplotlib no está instalado; instale las dependencias con "
            "'python -m pip install -r requirements.txt' para exportar imágenes") from None


def _posiciones(grafo):
    """Posiciones para el dibujo: networkx (solo dibujo) o, si no existe, un círculo."""
    conectados = [v for v in grafo.vertices() if grafo.grado(v) > 0]
    aislados = [v for v in grafo.vertices() if grafo.grado(v) == 0]
    pos = {}
    if len(conectados) > 1:
        try:
            import networkx as nx
            g = nx.Graph()
            g.add_nodes_from(conectados)
            g.add_edges_from((u, v) for u, v, _ in grafo.aristas())
            pos = {v: tuple(p) for v, p in nx.kamada_kawai_layout(g).items()}
        except ImportError:
            n = len(conectados)
            pos = {v: (math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n))
                   for i, v in enumerate(conectados)}
    # Los dispositivos aislados se colocan en una fila debajo del resto
    y = min((p[1] for p in pos.values()), default=0) - 0.45
    for i, v in enumerate(aislados):
        pos[v] = (-0.9 + 0.45 * i, y)
    return pos


COLOR_ESTADO = {"Activo": "#BDD7EE", "Sobrecargado": "#FFE699", "Falla": "#F4B6B6",
                "Recuperación": "#C6E0B4"}


def dibujar_grafo(grafo, archivo, resaltar=(), ruta=(), titulo=""):
    """Guarda el grafo como PNG. `resaltar`: nodos con borde naranja (p. ej. articulaciones);
    `ruta`: lista de nodos cuya ruta se dibuja en rojo."""
    plt = _pyplot()
    if grafo.num_vertices() == 0:
        raise VisualizacionNoDisponible("el grafo está vacío")
    pos = _posiciones(grafo)
    aristas_ruta = {frozenset(p) for p in zip(ruta, ruta[1:])}
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for u, v, w in grafo.aristas():
        (x1, y1), (x2, y2) = pos[u], pos[v]
        en_ruta = frozenset((u, v)) in aristas_ruta
        ax.plot([x1, x2], [y1, y2], color="#C00000" if en_ruta else "#595959",
                lw=3 if en_ruta else 1.6, zorder=1)
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, f"{w} ms", fontsize=8, color="#C55A11",
                ha="center", va="center", zorder=3,
                bbox=dict(facecolor="white", edgecolor="none", pad=0.5))
    for nombre, (x, y) in pos.items():
        d = grafo.dispositivos[nombre]
        borde = "#C55A11" if nombre in resaltar else "#1F4E79"
        color = COLOR_ESTADO.get(d.estado, "#BDD7EE") if grafo.grado(nombre) else "#D9D9D9"
        ax.scatter([x], [y], s=1900, color=color, edgecolors=borde,
                   linewidths=3 if nombre in resaltar else 1.5, zorder=2)
        ax.text(x, y, nombre, ha="center", va="center", fontsize=7.5, zorder=4)
    from matplotlib.patches import Patch
    estados = {d.estado for d in grafo.dispositivos.values()}
    leyenda = [Patch(facecolor=c, edgecolor="#1F4E79", label=e) for e, c in COLOR_ESTADO.items() if e in estados]
    if any(grafo.grado(v) == 0 for v in grafo.vertices()):
        leyenda.append(Patch(facecolor="#D9D9D9", edgecolor="#1F4E79", label="Aislado"))
    if resaltar:
        leyenda.append(Patch(facecolor="white", edgecolor="#C55A11", linewidth=2.5, label="Punto crítico"))
    ax.legend(handles=leyenda, loc="upper left", fontsize=8, frameon=False)
    ax.set_title(titulo or "Grafo de la red (latencia en ms)", fontsize=11)
    ax.set_axis_off()
    ax.margins(0.15)
    fig.tight_layout()
    Path(archivo).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(archivo, dpi=170)
    plt.close(fig)
    return Path(archivo)


def dibujar_automata(afd_o_afn, archivo, titulo=""):
    """Dibuja un AFN o AFD con los estados en línea. Las transiciones hacia
    adelante van por arriba y las de regreso por abajo."""
    plt = _pyplot()
    from matplotlib.patches import Circle, FancyArrowPatch

    estados = (list(afd_o_afn.estados) if isinstance(afd_o_afn.estados, list)
               else sorted(afd_o_afn.estados))
    # Agrupa etiquetas por (origen, destino)
    etiquetas = {}
    for (q, a), destino in afd_o_afn.transiciones.items():
        destinos = destino if isinstance(destino, (set, frozenset)) else {destino}
        for p in destinos:
            etiquetas.setdefault((q, p), []).append(a)

    radio, sep = 0.45, 2.6
    pos = {q: (i * sep, 0) for i, q in enumerate(estados)}
    fig, ax = plt.subplots(figsize=(max(5, 2.2 * len(estados)), 3.6))
    circulos = {}
    for q, (x, y) in pos.items():
        c = Circle((x, y), radio, facecolor="#DEEBF7", edgecolor="#1F4E79", lw=1.5, zorder=3)
        ax.add_patch(c)
        circulos[q] = c
        if q in afd_o_afn.finales:
            ax.add_patch(Circle((x, y), radio * 0.8, facecolor="none", edgecolor="#1F4E79", lw=1.2, zorder=4))
        ax.text(x, y, q, ha="center", va="center", fontsize=8, zorder=5)
    xi, yi = pos[afd_o_afn.inicial]
    ax.add_patch(FancyArrowPatch((xi - radio - 0.8, yi), (xi - radio, yi), arrowstyle="-|>",
                                 mutation_scale=13, color="black"))
    orden = {q: i for i, q in enumerate(estados)}
    for (q, p), simbolos in etiquetas.items():
        texto = ", ".join(simbolos)
        (x1, y1), (x2, y2) = pos[q], pos[p]
        if q == p:
            ax.add_patch(FancyArrowPatch((x1 - 0.25, y1 + radio * 0.9), (x1 + 0.25, y1 + radio * 0.9),
                                         connectionstyle="arc3,rad=-1.8", arrowstyle="-|>",
                                         mutation_scale=11, color="black"))
            ax.text(x1, y1 + radio + 0.65, texto, ha="center", fontsize=8, color="#C55A11")
            continue
        adelante = orden[p] > orden[q]
        saltos = abs(orden[p] - orden[q])
        rad = -0.3 - 0.12 * (saltos - 1)
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), connectionstyle=f"arc3,rad={rad}",
                                     patchA=circulos[q], patchB=circulos[p], arrowstyle="-|>",
                                     mutation_scale=11, color="black"))
        altura = (abs(x2 - x1) / 2) * abs(rad) + 0.18
        ax.text((x1 + x2) / 2, altura if adelante else -altura - 0.1, texto, ha="center",
                fontsize=8, color="#C55A11")
    ax.set_xlim(-1.6, (len(estados) - 1) * sep + 1)
    ax.set_ylim(-2.2, 2.2)
    ax.set_aspect("equal")
    ax.set_axis_off()
    if titulo:
        ax.set_title(titulo, fontsize=10)
    fig.tight_layout()
    Path(archivo).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(archivo, dpi=170)
    plt.close(fig)
    return Path(archivo)
