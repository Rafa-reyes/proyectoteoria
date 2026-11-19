"""
Genera las figuras del documento final y las deja en las carpetas de entrega:

    03_Automatas/AFN.png, AFD.png, AFD_minimo.png, AP.png, Maquina_estados.png
    04_Grafos/Grafo.png

Reutiliza las funciones de dibujo de diagramas_plan.py para que el documento
final y el plan de trabajo usen exactamente los mismos diagramas.
"""
import shutil
from pathlib import Path

import diagramas_plan as dg

RAIZ = Path(__file__).resolve().parent.parent
DIR_AUTOMATAS = RAIZ / "03_Automatas"
DIR_GRAFOS = RAIZ / "04_Grafos"


def dibujar_afd_minimo(destino):
    """AFD mínimo: C y D del AFD son equivalentes y se fusionan en CD."""
    estados = {
        "A": (0, 0, "A\n{q0}"), "B": (2.8, 0, "B\n{q0,q1}"), "CD": (5.6, 0, "CD\n(C ≡ D)"),
    }
    trans = [
        ("A", "A", "r, l", 1),
        ("A", "B", "t", -0.3),
        ("B", "A", "r, l", -0.3),
        ("B", "CD", "t", 0.0),
        ("CD", "CD", "r, l, t", 1),
    ]
    dg.dibujar_automata(estados, "A", {"CD"}, trans, destino, radio=0.6, tam=(6.6, 3.1),
                        fuente=8.5)


def dibujar_ap(destino):
    """Autómata de pila que valida el anidamiento de bloques del archivo .red.

    Etiquetas: «entrada, tope / cadena que reemplaza al tope».
    X = cualquier símbolo de bloque en el tope (R o Z), que se conserva.
    """
    estados = {
        "q0": (0.0, 0.0, "q0"), "q1": (2.4, 0.0, "q1"), "q2": (4.8, 0.0, "q2"),
        "q3": (7.6, 0.0, "q3"),
        # rama ZONA (arriba)
        "q4": (5.9, 3.0, "q4"), "q5": (9.3, 3.0, "q5"),
        # rama DISPOSITIVO (abajo a la izquierda)
        "q6": (5.2, -2.2, "q6"), "q7": (4.2, -4.4, "q7"), "q8": (5.6, -6.4, "q8"),
        # punto de reunión: se espera ';'
        "q9": (7.6, -6.4, "q9"),
        # rama ENLACE (abajo a la derecha)
        "q10": (10.0, -2.2, "q10"), "q11": (11.0, -4.4, "q11"), "q12": (9.6, -6.4, "q12"),
        # cierre de la red
        "q13": (11.2, 0.0, "q13"), "qf": (13.6, 0.0, "qf"),
    }
    trans = [
        ("q0", "q1", "RED, Z0/Z0", 0.0),
        ("q1", "q2", "id, Z0/Z0", 0.0),
        ("q2", "q3", "{, Z0/R Z0", 0.0),
        ("q3", "q4", "ZONA, X/X", 0.0),
        ("q4", "q5", "id, X/X", 0.0),
        ("q5", "q3", "{, X/Z X", 0.0),
        ("q3", "q6", "DISPOSITIVO, X/X", 0.0),
        ("q6", "q7", "id, X/X", 0.0),
        ("q7", "q8", "tipo, X/X", 0.0),
        ("q8", "q9", "ip, X/X", 0.0),
        ("q9", "q3", ";, X/X", 0.0),
        ("q3", "q10", "ENLACE, X/X", 0.0),
        ("q10", "q11", "id, X/X", 0.0),
        ("q11", "q12", "id, X/X", 0.0),
        ("q12", "q9", "num, X/X", 0.0),
        ("q3", "q3", "}, Z/ε", 1),
        ("q3", "q13", "}, R/ε", 0.0),
        ("q13", "qf", "ε, Z0/Z0", 0.0),
    ]
    dg.dibujar_automata(estados, "q0", {"qf"}, trans, destino, radio=0.45, tam=(11, 7.6),
                        fuente=8.5)


def generar_todo():
    DIR_AUTOMATAS.mkdir(exist_ok=True)
    DIR_GRAFOS.mkdir(exist_ok=True)

    # Figuras ya existentes en el plan (se regeneran para asegurar la versión vigente)
    dg.dibujar_grafo()
    dg.dibujar_afn()
    dg.dibujar_afd()
    dg.dibujar_maquina_estados()
    shutil.copy(dg.SALIDA / "grafo_ejemplo.png", DIR_GRAFOS / "Grafo.png")
    shutil.copy(dg.SALIDA / "afn_falla.png", DIR_AUTOMATAS / "AFN.png")
    shutil.copy(dg.SALIDA / "afd_falla.png", DIR_AUTOMATAS / "AFD.png")
    shutil.copy(dg.SALIDA / "maquina_estados.png", DIR_AUTOMATAS / "Maquina_estados.png")

    # Figuras nuevas del documento final
    dibujar_afd_minimo(DIR_AUTOMATAS / "AFD_minimo.png")
    dibujar_ap(DIR_AUTOMATAS / "AP.png")
    print("Figuras generadas en", DIR_AUTOMATAS, "y", DIR_GRAFOS)


if __name__ == "__main__":
    generar_todo()
