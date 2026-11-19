"""
Genera las figuras que se incluyen en el Plan de Trabajo (PDF):
  - grafo de la infraestructura de ejemplo
  - AFN de deteccion de falla
  - AFD obtenido por construccion de subconjuntos
  - maquina de estados de un dispositivo
  - diagrama de Gantt del cronograma

Nota: networkx se usa UNICAMENTE para dibujar (posiciones fijas). Ningun
algoritmo del proyecto depende de esta biblioteca.
"""
import math
from datetime import date, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Circle, FancyArrowPatch, Patch

SALIDA = Path(__file__).parent / "build"
SALIDA.mkdir(exist_ok=True)

AZUL = "#1F4E79"
NARANJA = "#C55A11"
VERDE = "#548235"
GRIS = "#595959"

plt.rcParams["font.family"] = "DejaVu Sans"


# ----------------------------------------------------------------------
# Grafo de la infraestructura
# ----------------------------------------------------------------------
def dibujar_grafo():
    import networkx as nx

    enlaces = [
        ("Router1", "Switch1", 2), ("Router1", "Switch2", 3),
        ("Switch1", "PC1", 1), ("Switch1", "PC2", 1),
        ("Switch2", "Server", 1), ("PC2", "DB", 4), ("Server", "DB", 2),
    ]
    pos = {
        "Router1": (0, 3), "Switch1": (-1.6, 2), "Switch2": (1.6, 2),
        "PC1": (-2.6, 0.9), "PC2": (-0.6, 0.9), "Server": (1.6, 0.9),
        "DB": (0.5, 0), "Impresora1": (2.9, 0),
    }
    g = nx.Graph()
    g.add_nodes_from(pos)
    g.add_weighted_edges_from(enlaces)

    colores = []
    for n in g.nodes:
        if n == "Switch1":
            colores.append("#F4B183")      # punto critico
        elif n == "Impresora1":
            colores.append("#D9D9D9")      # aislado
        else:
            colores.append("#BDD7EE")

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    nx.draw_networkx_edges(g, pos, ax=ax, width=1.8, edge_color=GRIS)
    nx.draw_networkx_nodes(g, pos, ax=ax, node_color=colores,
                           node_size=2400, edgecolors=AZUL, linewidths=1.5)
    nx.draw_networkx_labels(g, pos, ax=ax, font_size=7.8)
    etiquetas = {(u, v): f"{w} ms" for u, v, w in enlaces}
    nx.draw_networkx_edge_labels(g, pos, edge_labels=etiquetas, ax=ax,
                                 font_size=8, font_color=NARANJA,
                                 bbox=dict(facecolor="white", edgecolor="none", pad=0.5))
    ax.legend(handles=[
        Patch(facecolor="#BDD7EE", edgecolor=AZUL, label="Dispositivo"),
        Patch(facecolor="#F4B183", edgecolor=AZUL, label="Punto crítico (articulación)"),
        Patch(facecolor="#D9D9D9", edgecolor=AZUL, label="Dispositivo aislado"),
    ], loc="upper left", fontsize=7.5, frameon=False)
    ax.set_axis_off()
    ax.margins(0.12)
    fig.tight_layout()
    fig.savefig(SALIDA / "grafo_ejemplo.png", dpi=200)
    plt.close(fig)


# ----------------------------------------------------------------------
# Utilidad generica para dibujar automatas
# ----------------------------------------------------------------------
def dibujar_automata(estados, inicial, finales, transiciones, archivo,
                     radio=0.38, tam=(7, 3), fuente=10, titulo=None):
    """
    estados: dict nombre -> (x, y, etiqueta_visible)
    transiciones: lista (origen, destino, etiqueta, curvatura)
    """
    fig, ax = plt.subplots(figsize=tam)
    circulos = {}
    for nombre, (x, y, texto) in estados.items():
        c = Circle((x, y), radio, facecolor="#DEEBF7", edgecolor=AZUL, lw=1.6, zorder=3)
        ax.add_patch(c)
        circulos[nombre] = c
        if nombre in finales:
            ax.add_patch(Circle((x, y), radio * 0.82, facecolor="none",
                                edgecolor=AZUL, lw=1.3, zorder=4))
        ax.text(x, y, texto, ha="center", va="center", fontsize=fuente, zorder=5)

    # flecha de inicio
    xi, yi, _ = estados[inicial]
    ax.add_patch(FancyArrowPatch((xi - radio - 0.75, yi), (xi - radio, yi),
                                 arrowstyle="-|>", mutation_scale=14, lw=1.5, color="black"))
    ax.text(xi - radio - 0.78, yi + 0.12, "inicio", fontsize=8, ha="left")

    for origen, destino, etiqueta, curva in transiciones:
        xo, yo, _ = estados[origen]
        if origen == destino:
            # lazo: por arriba (curva >= 0) o por abajo (curva < 0)
            s = 1 if curva >= 0 else -1
            a = (xo - radio * 0.55, yo + s * radio * 0.83)
            b = (xo + radio * 0.55, yo + s * radio * 0.83)
            ax.add_patch(FancyArrowPatch(a, b, connectionstyle=f"arc3,rad={-1.9 * s}",
                                         arrowstyle="-|>", mutation_scale=12, lw=1.3,
                                         color="black", zorder=2))
            ax.text(xo, yo + s * (radio + 0.62), etiqueta, ha="center",
                    va="center", fontsize=fuente - 1, color=NARANJA)
            continue
        xd, yd, _ = estados[destino]
        flecha = FancyArrowPatch((xo, yo), (xd, yd), connectionstyle=f"arc3,rad={curva}",
                                 patchA=circulos[origen], patchB=circulos[destino],
                                 arrowstyle="-|>", mutation_scale=12, lw=1.3,
                                 color="black", zorder=2)
        ax.add_patch(flecha)
        # posicion de la etiqueta: punto medio desplazado segun la curvatura
        mx, my = (xo + xd) / 2, (yo + yd) / 2
        dx, dy = xd - xo, yd - yo
        dist = math.hypot(dx, dy)
        nx_, ny_ = dy / dist, -dx / dist        # normal (lado derecho)
        desplazamiento = curva * dist / 2 + (0.18 if curva >= 0 else -0.18)
        ax.text(mx + nx_ * desplazamiento, my + ny_ * desplazamiento, etiqueta,
                ha="center", va="center", fontsize=fuente - 1, color=NARANJA,
                bbox=dict(facecolor="white", edgecolor="none", pad=0.4), zorder=6)

    xs = [p[0] for p in estados.values()]
    ys = [p[1] for p in estados.values()]
    ax.set_xlim(min(xs) - 1.5, max(xs) + 0.9)
    ax.set_ylim(min(ys) - 1.3, max(ys) + 1.3)
    ax.set_aspect("equal")
    ax.set_axis_off()
    if titulo:
        ax.set_title(titulo, fontsize=10)
    fig.tight_layout()
    fig.savefig(SALIDA / archivo, dpi=200)
    plt.close(fig)


def dibujar_afn():
    estados = {"q0": (0, 0, "q0"), "q1": (2.4, 0, "q1"), "q2": (4.8, 0, "q2")}
    trans = [
        ("q0", "q0", "r, l, t", 1),
        ("q0", "q1", "t", 0.0),
        ("q1", "q2", "t", 0.0),
        ("q2", "q2", "r, l, t", 1),
    ]
    dibujar_automata(estados, "q0", {"q2"}, trans, "afn_falla.png", tam=(7, 2.6))


def dibujar_afd():
    estados = {
        "A": (0, 0, "A\n{q0}"), "B": (2.6, 0, "B\n{q0,q1}"),
        "C": (5.2, 0, "C\n{q0,q1,q2}"), "D": (7.8, 0, "D\n{q0,q2}"),
    }
    trans = [
        ("A", "A", "r, l", 1),
        ("A", "B", "t", -0.3),
        ("B", "A", "r, l", -0.3),
        ("B", "C", "t", 0.0),
        ("C", "C", "t", 1),
        ("C", "D", "r, l", -0.3),
        ("D", "C", "t", -0.3),
        ("D", "D", "r, l", 1),
    ]
    dibujar_automata(estados, "A", {"C", "D"}, trans, "afd_falla.png",
                     radio=0.6, tam=(8, 3.1), fuente=8.5)


def dibujar_maquina_estados():
    estados = {
        "ACT": (0, 0, "Activo"), "SOB": (3.6, 0, "Sobre-\ncargado"),
        "FAL": (3.6, -3.0, "Falla"), "REC": (0, -3.0, "Recupe-\nración"),
    }
    trans = [
        ("ACT", "ACT", "r", 1),
        ("ACT", "SOB", "l, t", -0.25),
        ("SOB", "ACT", "r", -0.25),
        ("SOB", "SOB", "l", 1),
        ("SOB", "FAL", "t", 0.0),
        ("FAL", "FAL", "t", -1),
        ("FAL", "REC", "r, l", 0.0),
        ("REC", "ACT", "r", 0.0),
        ("REC", "SOB", "l", 0.0),
        ("REC", "FAL", "t", 0.3),
    ]
    dibujar_automata(estados, "ACT", set(), trans, "maquina_estados.png",
                     radio=0.62, tam=(6.4, 5.4), fuente=8.5)


# ----------------------------------------------------------------------
# Diagrama de Gantt
# ----------------------------------------------------------------------
def dibujar_gantt(actividades):
    """actividades: lista de (id, nombre, responsable, inicio, fin)"""
    colores = {"Hiram": AZUL, "Axel": NARANJA, "Ambos": VERDE}
    fig, ax = plt.subplots(figsize=(8.2, 9.6))
    for i, (aid, nombre, resp, ini, fin) in enumerate(actividades):
        ax.barh(i, (fin - ini).days + 1, left=mdates.date2num(ini) - 0.4,
                color=colores[resp], height=0.62)
    ax.set_yticks(range(len(actividades)))
    ax.set_yticklabels([f"{a[0]}  {a[1]}" for a in actividades], fontsize=7)
    ax.invert_yaxis()
    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    plt.setp(ax.get_xticklabels(), fontsize=7, rotation=90)
    ax.grid(axis="x", color="#E0E0E0", lw=0.6)
    ax.set_axisbelow(True)
    # separadores de semana
    for d in [date(2026, 11, 18), date(2026, 11, 25), date(2026, 12, 2)]:
        ax.axvline(mdates.date2num(d) - 0.5, color=GRIS, lw=0.9, ls="--")
    ax.axvline(mdates.date2num(date(2026, 12, 8)), color="#C00000", lw=1.4)
    ax.text(mdates.date2num(date(2026, 12, 8)) + 0.15, -0.8, "Entrega", color="#C00000",
            fontsize=7.5)
    ax.legend(handles=[Patch(color=c, label=k) for k, c in colores.items()],
              loc="lower left", fontsize=8, ncol=3, frameon=False)
    fig.tight_layout()
    fig.savefig(SALIDA / "gantt.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    dibujar_grafo()
    dibujar_afn()
    dibujar_afd()
    dibujar_maquina_estados()
    print("Figuras generadas en", SALIDA)
