"""
Genera el Plan de Trabajo del Proyecto 4 (Network Graph Analyzer) en PDF.

Uso:
    python diagramas_plan.py        # figuras
    python generar_plan_trabajo.py  # PDF en 01_Documentacion/

Las tablas del AFN, del AFD (construccion de subconjuntos) y las trazas del
autómata de pila se CALCULAN aquí mismo para que el plan no contenga errores
de transcripción.
"""
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                PageBreak, PageTemplate, Paragraph, Preformatted,
                                Spacer, Table, TableStyle, NextPageTemplate,
                                CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents

import diagramas_plan as dg

RAIZ = Path(__file__).resolve().parent.parent
BUILD = Path(__file__).resolve().parent / "build"
SALIDA_PDF = RAIZ / "01_Documentacion" / "Plan_de_Trabajo_Proyecto4.pdf"

# ----------------------------------------------------------------------
# Fuentes (DejaVu cubre Σ, δ, ε, →, ∈, ∪, ⇒, ✓, ✗ ...)
# ----------------------------------------------------------------------
FUENTES = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("DV", str(FUENTES / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DV-B", str(FUENTES / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DV-I", str(FUENTES / "DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFont(TTFont("DV-BI", str(FUENTES / "DejaVuSans-BoldOblique.ttf")))
pdfmetrics.registerFont(TTFont("DVM", str(FUENTES / "DejaVuSansMono.ttf")))
pdfmetrics.registerFont(TTFont("DVM-B", str(FUENTES / "DejaVuSansMono-Bold.ttf")))
addMapping("DV", 0, 0, "DV")
addMapping("DV", 1, 0, "DV-B")
addMapping("DV", 0, 1, "DV-I")
addMapping("DV", 1, 1, "DV-BI")
addMapping("DVM", 0, 0, "DVM")
addMapping("DVM", 1, 0, "DVM-B")
addMapping("DVM", 0, 1, "DVM")
addMapping("DVM", 1, 1, "DVM-B")

AZUL = colors.HexColor("#1F4E79")
AZUL_CLARO = colors.HexColor("#DEEBF7")
NARANJA = colors.HexColor("#C55A11")
NARANJA_CLARO = colors.HexColor("#FBE5D6")
VERDE = colors.HexColor("#548235")
VERDE_CLARO = colors.HexColor("#E2EFDA")
GRIS = colors.HexColor("#595959")
GRIS_CLARO = colors.HexColor("#F2F2F2")

# ----------------------------------------------------------------------
# Estilos
# ----------------------------------------------------------------------
ST = {
    "body": ParagraphStyle("body", fontName="DV", fontSize=9.6, leading=13.6,
                           alignment=TA_JUSTIFY, spaceAfter=5),
    "h1": ParagraphStyle("h1", fontName="DV-B", fontSize=16, leading=20,
                         textColor=AZUL, spaceBefore=4, spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName="DV-B", fontSize=12.5, leading=16,
                         textColor=AZUL, spaceBefore=10, spaceAfter=6),
    "h3": ParagraphStyle("h3", fontName="DV-B", fontSize=10.5, leading=14,
                         textColor=NARANJA, spaceBefore=8, spaceAfter=4),
    "cell": ParagraphStyle("cell", fontName="DV", fontSize=8.2, leading=10.6),
    "cellb": ParagraphStyle("cellb", fontName="DV-B", fontSize=8.2, leading=10.6,
                            textColor=colors.white),
    "cellm": ParagraphStyle("cellm", fontName="DVM", fontSize=7.8, leading=10.2),
    "bullet": ParagraphStyle("bullet", fontName="DV", fontSize=9.6, leading=13.4,
                             leftIndent=14, bulletIndent=4, spaceAfter=2,
                             alignment=TA_JUSTIFY),
    "code": ParagraphStyle("code", fontName="DVM", fontSize=8, leading=10.4,
                           backColor=GRIS_CLARO, borderPadding=6, leftIndent=6,
                           rightIndent=6, spaceBefore=4, spaceAfter=8),
    "caption": ParagraphStyle("caption", fontName="DV-I", fontSize=8.2, leading=11,
                              alignment=TA_CENTER, textColor=GRIS, spaceAfter=8),
    "nota": ParagraphStyle("nota", fontName="DV", fontSize=8.8, leading=12.4,
                           backColor=AZUL_CLARO, borderPadding=7, leftIndent=7,
                           rightIndent=7, spaceBefore=6, spaceAfter=10,
                           alignment=TA_JUSTIFY),
    "toc1": ParagraphStyle("toc1", fontName="DV-B", fontSize=10, leading=15, leftIndent=0),
    "toc2": ParagraphStyle("toc2", fontName="DV", fontSize=9, leading=12.5, leftIndent=16),
}


def nt(nombre):
    """No terminal escrito para Paragraph: <nombre>."""
    return f"&lt;{nombre}&gt;"


def P(texto, estilo="body"):
    return Paragraph(texto, ST[estilo])


def H1(texto):
    p = Paragraph(texto, ST["h1"])
    p.toc_nivel = 0
    return p


def H2(texto):
    p = Paragraph(texto, ST["h2"])
    p.toc_nivel = 1
    return p


def H3(texto):
    return Paragraph(texto, ST["h3"])


def bullets(items, estilo="bullet"):
    return [Paragraph(i, ST[estilo], bulletText="•") for i in items]


def numerados(items):
    return [Paragraph(i, ST["bullet"], bulletText=f"{n}.") for n, i in enumerate(items, 1)]


def code(texto):
    return Preformatted(texto, ST["code"])


def nota(texto):
    return Paragraph(texto, ST["nota"])


def figura(nombre, ancho_cm, pie):
    ruta = BUILD / nombre
    img = Image(str(ruta))
    proporcion = img.imageHeight / img.imageWidth
    img.drawWidth = ancho_cm * cm
    img.drawHeight = ancho_cm * cm * proporcion
    return KeepTogether([img, Paragraph(pie, ST["caption"])])


def tabla(filas, anchos, encabezado=True, mono=(), color=AZUL, zebra=True,
          alinear_centro=(), escapar=()):
    """Convierte texto en Paragraph y aplica el estilo común de tablas."""
    datos = []
    for i, fila in enumerate(filas):
        nueva = []
        for j, celda in enumerate(fila):
            if not isinstance(celda, str):
                nueva.append(celda)
                continue
            texto = escape(celda) if (j in escapar or j in mono) and not (encabezado and i == 0) else celda
            if encabezado and i == 0:
                estilo = ST["cellb"]
            elif j in mono:
                estilo = ST["cellm"]
            else:
                estilo = ST["cell"]
            nueva.append(Paragraph(texto, estilo))
        datos.append(nueva)
    t = Table(datos, colWidths=[a * cm for a in anchos], repeatRows=1 if encabezado else 0)
    estilos = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if encabezado:
        estilos.append(("BACKGROUND", (0, 0), (-1, 0), color))
    if zebra:
        for r in range(1 if encabezado else 0, len(datos)):
            if r % 2 == 0:
                estilos.append(("BACKGROUND", (0, r), (-1, r), GRIS_CLARO))
    for c in alinear_centro:
        estilos.append(("ALIGN", (c, 0), (c, -1), "CENTER"))
    t.setStyle(TableStyle(estilos))
    return t


# ----------------------------------------------------------------------
# Modelos formales (se calculan para que las tablas sean exactas)
# ----------------------------------------------------------------------
SIGMA_M = ["r", "l", "t"]
AFN_DELTA = {
    ("q0", "r"): {"q0"}, ("q0", "l"): {"q0"}, ("q0", "t"): {"q0", "q1"},
    ("q1", "r"): set(), ("q1", "l"): set(), ("q1", "t"): {"q2"},
    ("q2", "r"): {"q2"}, ("q2", "l"): {"q2"}, ("q2", "t"): {"q2"},
}
AFN_ESTADOS = ["q0", "q1", "q2"]
AFN_FINALES = {"q2"}


def fmt_conj(s):
    return "{" + ", ".join(sorted(s)) + "}" if s else "∅"


def mover(conjunto, simbolo):
    resultado = set()
    for q in conjunto:
        resultado |= AFN_DELTA[(q, simbolo)]
    return frozenset(resultado)


def subconjuntos():
    """Construcción de subconjuntos; devuelve nombres, tabla y pasos."""
    inicial = frozenset({"q0"})
    nombres = {inicial: "A"}
    pendientes = [inicial]
    tabla_afd, pasos = {}, []
    while pendientes:
        actual = pendientes.pop(0)
        for s in SIGMA_M:
            destino = mover(actual, s)
            nuevo = destino not in nombres
            if nuevo:
                nombres[destino] = chr(ord("A") + len(nombres))
                pendientes.append(destino)
            tabla_afd[(nombres[actual], s)] = nombres[destino]
            detalle = " ∪ ".join(f"δ({q},{s})={fmt_conj(AFN_DELTA[(q, s)])}" for q in sorted(actual))
            pasos.append((nombres[actual], fmt_conj(actual), s, detalle, fmt_conj(destino),
                          nombres[destino], "Sí" if nuevo else "No"))
    return nombres, tabla_afd, pasos


NOMBRES_AFD, TABLA_AFD, PASOS_AFD = subconjuntos()
CONJ_DE = {v: k for k, v in NOMBRES_AFD.items()}
FINALES_AFD = {n for c, n in NOMBRES_AFD.items() if c & AFN_FINALES}


def traza_afn(cadena):
    actual = frozenset({"q0"})
    partes = [fmt_conj(actual)]
    for s in cadena:
        actual = mover(actual, s)
        partes.append(f"—{s}→ {fmt_conj(actual)}")
    return " ".join(partes), bool(actual & AFN_FINALES)


def traza_afd(cadena):
    estado = "A"
    partes = ["A"]
    for s in cadena:
        estado = TABLA_AFD[(estado, s)]
        partes.append(f"—{s}→ {estado}")
    return " ".join(partes), estado in FINALES_AFD


# Autómata de pila determinista sobre tokens del archivo .red
AP_DELTA = {
    ("q0", "RED", "Z0"): ("q1", ["Z0"]),
    ("q1", "id", "Z0"): ("q2", ["Z0"]),
    ("q2", "{", "Z0"): ("q3", ["R", "Z0"]),
    ("q3", "ZONA", "X"): ("q4", ["X"]),
    ("q4", "id", "X"): ("q5", ["X"]),
    ("q5", "{", "X"): ("q3", ["Z", "X"]),
    ("q3", "DISPOSITIVO", "X"): ("q6", ["X"]),
    ("q6", "id", "X"): ("q7", ["X"]),
    ("q7", "tipo", "X"): ("q8", ["X"]),
    ("q8", "ip", "X"): ("q9", ["X"]),
    ("q9", ";", "X"): ("q3", ["X"]),
    ("q3", "ENLACE", "X"): ("q10", ["X"]),
    ("q10", "id", "X"): ("q11", ["X"]),
    ("q11", "id", "X"): ("q12", ["X"]),
    ("q12", "num", "X"): ("q9", ["X"]),
    ("q3", "}", "Z"): ("q3", []),
    ("q3", "}", "R"): ("q13", []),
}


def simular_ap(tokens):
    """Simula el AP. Devuelve (aceptada, filas_traza, motivo)."""
    estado, pila, i = "q0", ["Z0"], 0
    filas = [("0", estado, " ".join(tokens), "—", " ".join(reversed(pila)) or "vacía")]
    paso = 0
    while True:
        if estado == "q13" and pila[-1] == "Z0":
            paso += 1
            estado = "qf"
            filas.append((str(paso), estado, " ".join(tokens[i:]) or "ε", "ε, Z0 / Z0",
                          " ".join(reversed(pila))))
        if i == len(tokens):
            if estado == "qf":
                return True, filas, "Entrada consumida, estado final qf y pila = Z0."
            return False, filas, (f"Fin de entrada en {estado} con pila "
                                  f"{' '.join(reversed(pila))}: hay bloques sin cerrar.")
        if estado == "qf":
            return False, filas, f"Sobra entrada después de cerrar RED: '{' '.join(tokens[i:])}'."
        tok, tope = tokens[i], pila[-1]
        clave = (estado, tok, tope)
        if clave not in AP_DELTA and tope in ("R", "Z"):
            clave = (estado, tok, "X")
        if clave not in AP_DELTA:
            return False, filas, f"No existe δ({estado}, {tok}, {tope}): token inesperado."
        nuevo, empuje = AP_DELTA[clave]
        pila.pop()
        for simbolo in reversed([tope if s == "X" else s for s in empuje]):
            pila.append(simbolo)
        i += 1
        paso += 1
        estado = nuevo
        filas.append((str(paso), estado, " ".join(tokens[i:]) or "ε",
                      f"{tok}, {tope} / {' '.join([tope if s == 'X' else s for s in empuje]) or 'ε'}",
                      " ".join(reversed(pila)) or "vacía"))


# ----------------------------------------------------------------------
# Documento con índice automático, encabezado y pie
# ----------------------------------------------------------------------
class Plantilla(BaseDocTemplate):
    def __init__(self, archivo, **kw):
        super().__init__(archivo, pagesize=letter, leftMargin=2.1 * cm, rightMargin=2.1 * cm,
                         topMargin=2.3 * cm, bottomMargin=2.0 * cm,
                         title="Plan de Trabajo — Network Graph Analyzer",
                         author="Hiram Alejandro Almendarez Hernández; Axel Rafael Reyes Lara",
                         subject="Proyecto 4. Analizador de redes mediante grafos", **kw)
        marco = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal")
        self.addPageTemplates([
            PageTemplate(id="portada", frames=[marco], onPage=self._portada),
            PageTemplate(id="contenido", frames=[marco], onPage=self._pagina),
        ])

    def afterFlowable(self, flowable):
        nivel = getattr(flowable, "toc_nivel", None)
        if nivel is not None:
            texto = flowable.getPlainText()
            clave = f"sec-{id(flowable)}"
            self.canv.bookmarkPage(clave)
            self.canv.addOutlineEntry(texto, clave, level=nivel, closed=nivel > 0)
            self.notify("TOCEntry", (nivel, texto, self.page, clave))

    @staticmethod
    def _portada(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(AZUL)
        canvas.rect(0, letter[1] - 5.2 * cm, letter[0], 5.2 * cm, stroke=0, fill=1)
        canvas.setFillColor(NARANJA)
        canvas.rect(0, letter[1] - 5.45 * cm, letter[0], 0.25 * cm, stroke=0, fill=1)
        canvas.restoreState()

    @staticmethod
    def _pagina(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(AZUL)
        canvas.setLineWidth(0.8)
        y = letter[1] - 1.55 * cm
        canvas.line(doc.leftMargin, y, letter[0] - doc.rightMargin, y)
        canvas.setFont("DV", 7.8)
        canvas.setFillColor(GRIS)
        canvas.drawString(doc.leftMargin, y + 0.18 * cm,
                          "Network Graph Analyzer — Plan de trabajo")
        canvas.drawRightString(letter[0] - doc.rightMargin, y + 0.18 * cm,
                               "Teoría Computacional · Proyecto Final Integrador")
        canvas.line(doc.leftMargin, 1.45 * cm, letter[0] - doc.rightMargin, 1.45 * cm)
        canvas.drawString(doc.leftMargin, 1.0 * cm, "H. A. Almendarez Hernández · A. R. Reyes Lara")
        canvas.drawRightString(letter[0] - doc.rightMargin, 1.0 * cm, f"Página {doc.page}")
        canvas.restoreState()


# ======================================================================
# CONTENIDO
# ======================================================================
def portada():
    estilo_t = ParagraphStyle("t", fontName="DV-B", fontSize=26, leading=32,
                              textColor=colors.white, alignment=TA_CENTER)
    estilo_st = ParagraphStyle("st", fontName="DV", fontSize=12.5, leading=17,
                               textColor=colors.white, alignment=TA_CENTER)
    estilo_c = ParagraphStyle("c", fontName="DV", fontSize=12, leading=18, alignment=TA_CENTER)
    estilo_cb = ParagraphStyle("cb", fontName="DV-B", fontSize=13, leading=19,
                               alignment=TA_CENTER, textColor=AZUL)
    return [
        Spacer(1, 0.2 * cm),
        Paragraph("Network Graph Analyzer", estilo_t),
        Spacer(1, 0.3 * cm),
        Paragraph("Proyecto 4 · Analizador de redes mediante grafos", estilo_st),
        Spacer(1, 4.2 * cm),
        Paragraph("PLAN DE TRABAJO", ParagraphStyle("pt", parent=estilo_cb, fontSize=20, leading=26)),
        Spacer(1, 0.4 * cm),
        Paragraph("Cronograma, división de tareas, actividades detalladas,<br/>"
                  "entregables, requisitos y stack tecnológico", estilo_c),
        Spacer(1, 2.2 * cm),
        Paragraph("Teoría Computacional — Proyecto Final Integrador", estilo_c),
        Spacer(1, 1.6 * cm),
        Paragraph("Integrantes", estilo_cb),
        Paragraph("Hiram Alejandro Almendarez Hernández", estilo_c),
        Paragraph("Axel Rafael Reyes Lara", estilo_c),
        Spacer(1, 1.6 * cm),
        Paragraph("10 de noviembre de 2026", estilo_c),
        NextPageTemplate("contenido"),
        PageBreak(),
    ]


def indice():
    toc = TableOfContents()
    toc.levelStyles = [ST["toc1"], ST["toc2"]]
    toc.dotsMinLevel = 0
    return [Paragraph("Índice", ST["h1"]), toc, PageBreak()]


def seccion_resumen():
    s = [H1("1. Resumen del proyecto")]
    s.append(P(
        "<b>Network Graph Analyzer</b> es un prototipo funcional en Python que representa una "
        "infraestructura tecnológica (routers, switches, servidores, equipos de usuario) como un "
        "<b>grafo no dirigido y ponderado</b> y permite analizar sus nodos, conexiones, rutas y estados. "
        "El sistema recibe la descripción de la red desde archivos de texto o desde el teclado, "
        "<b>valida</b> cada entrada mediante lenguajes formales, expresiones regulares, autómatas y "
        "una gramática libre de contexto, y después aplica algoritmos sobre el grafo para responder "
        "preguntas típicas de un administrador de redes: ¿están conectados dos equipos?, ¿cuál es la "
        "ruta de menor latencia?, ¿qué dispositivo es un punto único de falla?, ¿qué pasa con la red "
        "si un servidor deja de responder?"))
    s.append(P(
        "El proyecto integra los temas del curso en una sola cadena de procesamiento, de modo que "
        "cada modelo teórico resuelve una parte concreta del problema:"))
    s.append(tabla([
        ["Concepto", "Dónde se aplica en el sistema", "Qué problema resuelve"],
        ["Grafos", "Modelo de la infraestructura (dispositivos = vértices, enlaces = aristas con latencia).",
         "Conectividad, rutas, ruta más corta, grados, aislados, ciclos, puntos críticos y rutas alternativas."],
        ["Lenguaje formal", "L<sub>enlaces</sub>: formato de cada línea del archivo de topología.",
         "Definir con precisión qué entradas son aceptables antes de construir el grafo."],
        ["Expresiones regulares", "Analizador léxico: nombres, líneas de enlace, IPv4 y eventos de monitoreo.",
         "Separar y validar la información y reportar errores por línea."],
        ["AFN / AFD", "Detector de falla sobre secuencias de monitoreo (ping ok / lento / timeout).",
         "Reconocer el patrón «dos timeouts consecutivos» de forma determinista."],
        ["Máquina de estados", "Estado de cada dispositivo: Activo, Sobrecargado, Falla, Recuperación.",
         "Retirar del grafo los nodos en falla y recalcular rutas (une autómatas con grafos)."],
        ["Gramática / LLC", "Archivo de configuración .red con zonas anidadas.",
         "Describir estructuras jerárquicas que una expresión regular no puede reconocer."],
        ["Autómata de pila", "Validación del anidamiento de bloques RED / ZONA.",
         "Detectar bloques sin cerrar o llaves sobrantes mostrando la pila paso a paso."],
    ], [3.0, 6.6, 7.1]))
    s.append(Spacer(1, 6))
    s.append(P("La secuencia de evaluación que exige el curso —<b>problema → modelo formal → solución → "
               "implementación → pruebas → explicación</b>— se refleja directamente en las fases del "
               "cronograma (sección 5) y en la matriz de trazabilidad (sección 7.4)."))
    s.append(H2("1.1 Fechas clave"))
    s.append(tabla([
        ["Hito", "Fecha", "Resultado esperado"],
        ["Inicio formal del proyecto", "11/11/2026", "Plan aprobado por ambos integrantes; repositorio listo."],
        ["H1 · Problema y grafo", "17/11/2026", "Etapas 1 y 2 documentadas; versión 0.1 del programa (grafo y carga)."],
        ["H2 · Lenguajes y autómatas", "24/11/2026", "Etapas 3 a 6 documentadas; versión 0.2 (léxico, AFN, AFD)."],
        ["H3 · Gramática, pila e integración", "01/12/2026", "Etapas 7 a 9; versión 0.3 con CLI integrada; revisión cruzada."],
        ["H4 · Pruebas y documento", "05/12/2026", "Etapa 10 completa; versión 1.0; Proyecto_Final.pdf terminado."],
        ["H5 · Empaquetado y ensayo", "07/12/2026", "ZIP verificado; ensayo de demostración y defensa."],
        ["Entrega y presentación", "08/12/2026", "Presentación, demostración en vivo y defensa individual."],
    ], [5.2, 2.3, 9.2]))
    s.append(KeepTogether(nota("<b>Nota de calendario:</b> el cronograma está programado para entregar el "
                  "<b>8 de diciembre de 2026</b>. Si la fecha oficial es distinta, todas las actividades "
                  "se recorren conservando su orden y duración relativa; la semana 4 contiene la holgura "
                  "necesaria para absorber retrasos.")))
    return s


def seccion_equipo():
    s = [H1("2. Equipo y división de responsabilidades")]
    s.append(P("El equipo está formado por dos integrantes. El documento del proyecto propone una "
               "división para tres personas; se reorganizó en dos bloques de carga equivalente según la "
               "rúbrica (cada bloque concentra aproximadamente 45 de los 100 puntos) y se dejaron como "
               "tareas compartidas las pruebas, el documento final, la presentación y la defensa."))
    s.append(tabla([
        ["Integrante", "Responsabilidades principales", "Puntos de rúbrica que lidera"],
        ["<b>Hiram Alejandro Almendarez Hernández</b><br/>(Integrante 1)",
         "• Definición del problema (Etapa 1)<br/>• Modelado del grafo y sus representaciones (Etapa 2)<br/>"
         "• Algoritmos sobre grafos<br/>• Gramática y lenguaje libre de contexto (Etapa 7)<br/>"
         "• Parser descendente recursivo<br/>• Autómata de pila (Etapa 8)<br/>"
         "• Aplicación CLI e integración de módulos (Etapa 9)<br/>• README.md y empaquetado final",
         "Problema (5) · Grafos (10) · Gramática y LLC (10) · Autómata de pila (10) · Implementación (10)"],
        ["<b>Axel Rafael Reyes Lara</b><br/>(Integrante 2)",
         "• Definición formal del lenguaje (Etapa 3)<br/>• Expresiones regulares y analizador léxico (Etapa 4)<br/>"
         "• AFN (Etapa 5)<br/>• Conversión AFN → AFD (Etapa 6)<br/>• Máquina de estados de dispositivos<br/>"
         "• Visualización (PNG de grafo y autómatas)<br/>• Diseño de casos de prueba (Etapa 10)<br/>"
         "• Bitácora y presentación",
         "Lenguaje (10) · Regex (10) · AFN (10) · AFN→AFD (10) · Casos de prueba (5)"],
        ["<b>Ambos</b>",
         "• Revisión cruzada de cada entregable<br/>• Ejecución de pruebas y corrección de errores<br/>"
         "• Documento final (Proyecto_Final.pdf)<br/>• Ensayo de demostración y defensa",
         "Documentación (5) · Presentación y defensa (5)"],
    ], [4.2, 7.6, 4.9]))
    s.append(Spacer(1, 6))
    s.append(H2("2.1 Reglas de trabajo del equipo"))
    s += bullets([
        "<b>Conocimiento completo de ambos.</b> La división indica quién <i>lidera</i> cada parte, no quién la "
        "conoce. Cada entregable lo revisa el otro integrante antes de darlo por terminado, y la "
        "actividad A22 está dedicada a que cada uno explique la parte del otro.",
        "<b>Revisión cruzada obligatoria.</b> Ningún cambio se integra a la rama principal sin que el otro "
        "integrante lo lea. En la revisión se verifica que el código esté comentado y que el revisor "
        "pueda explicarlo.",
        "<b>Bitácora diaria.</b> Cada sesión de trabajo se registra (fecha, actividad, responsable, "
        "resultado y, si aplica, problema encontrado y solución). Esto alimenta la sección 17 del "
        "documento final.",
        "<b>Uso responsable de IA.</b> Las herramientas de IA se usan para explicar errores, comparar "
        "alternativas y mejorar redacción. Todo lo entregado se verifica a mano (tablas, derivaciones, "
        "trazas) y cada integrante debe poder defenderlo sin apoyo.",
        "<b>Comunicación.</b> Reunión corta de sincronización cada dos días (15 min) y una sesión larga "
        "por semana para integrar y revisar hitos.",
    ])
    return s


def seccion_stack():
    s = [H1("3. Stack tecnológico")]
    s.append(P("El documento del proyecto recomienda Python y prohíbe bibliotecas que construyan "
               "automáticamente los autómatas o parsers que sustituyan la construcción solicitada. Por "
               "ello, <b>toda la lógica de Teoría Computacional se programa a mano</b> con la biblioteca "
               "estándar, y las bibliotecas externas se limitan a visualización y pruebas, que son usos "
               "explícitamente permitidos."))
    s.append(tabla([
        ["Componente", "Herramienta", "Versión", "Uso en el proyecto"],
        ["Lenguaje", "Python", "3.14.7", "Lenguaje de toda la aplicación (recomendado por el curso)."],
        ["Expresiones regulares", "Módulo <font name='DVM'>re</font> (estándar)", "—",
         "Compilar y aplicar las regex R1–R4 del analizador léxico."],
        ["Estructuras de datos", "dict, set, list, <font name='DVM'>collections.deque</font>, "
         "<font name='DVM'>heapq</font>, <font name='DVM'>dataclasses</font>", "—",
         "Lista de adyacencia, conjuntos de estados del AFN, cola de BFS, cola de prioridad de "
         "Dijkstra, pila del autómata de pila, registros de dispositivos."],
        ["Interfaz", "CLI con <font name='DVM'>input/print</font> y <font name='DVM'>argparse</font>", "—",
         "Menú interactivo y ejecución directa con argumentos."],
        ["Archivos", "<font name='DVM'>pathlib</font>, <font name='DVM'>open(..., encoding='utf-8')</font>", "—",
         "Lectura de topologías (.txt), configuraciones (.red) y monitoreo; escritura de reportes."],
        ["Pruebas", "pytest", "9.2.0", "Pruebas unitarias por módulo y pruebas del sistema completo."],
        ["Visualización", "matplotlib", "3.11.2", "Generar Grafo.png, AFN.png, AFD.png, AP.png y la "
         "máquina de estados desde el propio programa."],
        ["Apoyo de dibujo", "networkx", "3.7", "<b>Solo</b> para posicionar y dibujar el grafo, y como "
         "verificación cruzada dentro de las pruebas. Ningún algoritmo del programa la utiliza."],
        ["Documentación", "Microsoft Word → PDF / reportlab", "5.1.0", "Proyecto_Final.pdf y este plan."],
        ["Presentación", "Microsoft PowerPoint", "—", "Presentacion.pptx con los 13 puntos requeridos."],
        ["Pruebas y bitácora", "Microsoft Excel o Markdown", "—", "casos_prueba.xlsx y Bitacora.xlsx."],
        ["Control de versiones", "Git + GitHub", "—", "Repositorio <font name='DVM'>proyecto-4</font>, "
         "una rama por integrante y revisión antes de integrar."],
        ["Editor", "Visual Studio Code + extensión Python", "—", "Desarrollo, depuración y ejecución de pruebas."],
    ], [3.0, 4.6, 1.8, 7.3]))
    s.append(Spacer(1, 6))
    s.append(H2("3.1 Qué se programa a mano y qué no se utilizará"))
    s.append(tabla([
        ["Se implementa a mano (sin bibliotecas)", "Bibliotecas que NO se utilizarán"],
        ["• Estructura Grafo (lista y matriz de adyacencia)<br/>• BFS, DFS, Dijkstra<br/>"
         "• Detección de ciclos, componentes conexas<br/>• Puntos de articulación y puentes (Tarjan)<br/>"
         "• Rutas alternativas (backtracking)<br/>• Simulación de AFN y AFD<br/>"
         "• Construcción de subconjuntos AFN → AFD<br/>• Máquina de estados de dispositivos<br/>"
         "• Analizador léxico (con <font name='DVM'>re</font>)<br/>• Parser descendente recursivo<br/>"
         "• Autómata de pila con traza",
         "• automata-lib, pyformlang (construyen autómatas)<br/>• lark, ply, sly, ANTLR (generadores de parsers)<br/>"
         "• Algoritmos de networkx (shortest_path, articulation_points, cycle_basis, etc.) dentro "
         "del programa<br/>• Código copiado íntegramente de Internet"],
    ], [8.35, 8.35], color=VERDE))
    s.append(H2("3.2 Requisitos de instalación"))
    s.append(code("python -m pip install -r requirements.txt\n\n"
                  "# requirements.txt\nmatplotlib>=3.8\nnetworkx>=3.2      # solo dibujo / verificación en pruebas\n"
                  "pytest>=8.0"))
    s.append(P("El núcleo del programa (análisis, autómatas, parser) funciona <b>sin</b> dependencias "
               "externas; si matplotlib no está instalado, la aplicación sigue funcionando y solo "
               "desactiva la exportación de imágenes con un aviso claro."))
    return s


# ----------------------------------------------------------------------
# Propuesta técnica
# ----------------------------------------------------------------------
def propuesta_problema():
    s = [H1("4. Propuesta técnica detallada"),
         P("Esta sección describe, etapa por etapa, el diseño que se desarrollará. Funciona como "
           "borrador técnico del documento final: cada subsección corresponde a una etapa del documento "
           "del proyecto y se completará y verificará en las actividades de la sección 6."),
         H2("4.1 Definición del problema (Etapa 1)")]
    s.append(tabla([
        ["Pregunta guía", "Respuesta propuesta"],
        ["¿Cuál es el problema?",
         "En redes pequeñas y medianas (laboratorios, oficinas, centros de datos escolares) la topología "
         "se documenta en listas o diagramas estáticos. Con ellos es difícil responder rápidamente si dos "
         "equipos tienen comunicación, cuál es la ruta de menor latencia, qué dispositivo es un punto único "
         "de falla o cómo cambia la red cuando un equipo deja de responder. Además, los archivos de "
         "configuración escritos a mano suelen contener errores de formato que no se detectan hasta que "
         "causan fallas."],
        ["¿En qué contexto de TI se presenta?",
         "Administración de redes e infraestructura: diseño de topologías, monitoreo de disponibilidad "
         "(ping), análisis de redundancia y planeación de mantenimiento."],
        ["¿Quién utilizaría el sistema?",
         "Administradores de red, personal de soporte técnico, estudiantes y docentes de redes que necesitan "
         "analizar o validar una topología antes de implementarla o modificarla."],
        ["¿Qué información recibirá?",
         "(1) Archivo de topología .txt con líneas «origen,destino[,latencia]»; (2) archivo de configuración "
         ".red con zonas anidadas, dispositivos (tipo e IP) y enlaces; (3) archivo de monitoreo con "
         "secuencias de eventos por dispositivo (ok, lento, timeout); (4) consultas por teclado."],
        ["¿Qué información producirá?",
         "Conjuntos V y E, lista y matriz de adyacencia, árbol de la red, rutas y costos, grados, "
         "dispositivos aislados, ciclos, puntos críticos, rutas alternativas, estado de cada dispositivo, "
         "impacto de fallas, trazas de AFN/AFD/autómata de pila, mensajes de error por línea, reporte .txt "
         "e imágenes PNG."],
        ["¿Qué problemas debe detectar o resolver?",
         "Errores de formato (léxicos), errores de estructura (sintácticos, bloques sin cerrar), "
         "inconsistencias (enlace a dispositivo no declarado, lazos, duplicados), equipos sin "
         "comunicación, puntos únicos de falla, dispositivos en falla y su efecto sobre las rutas."],
        ["¿Cuáles son sus limitaciones?",
         "No se conecta a una red real: el monitoreo se simula con archivos. Enlaces no dirigidos con "
         "latencia entera positiva (1–9999 ms), a lo sumo un enlace entre cada par de dispositivos, "
         "nombres de hasta 20 caracteres, topologías pensadas para decenas de nodos (prototipo académico)."],
    ], [4.0, 12.7]))
    s.append(Spacer(1, 6))
    s.append(H3("Elementos mínimos requeridos"))
    s.append(tabla([
        ["Elemento", "Contenido"],
        ["Descripción del problema", "Texto anterior, ampliado con un escenario: la red del laboratorio "
         "(Router1, Switch1, Switch2, PC1, PC2, Server, DB, Impresora1)."],
        ["Objetivo del proyecto", "Desarrollar un prototipo que modele una infraestructura tecnológica "
         "como grafo, valide sus descripciones mediante lenguajes formales y autómatas, y permita "
         "analizar conectividad, rutas, puntos críticos y estados de los dispositivos."],
        ["Alcance", "<b>Incluye:</b> carga y validación de 3 formatos de entrada, 8 análisis sobre el grafo, "
         "detección de falla con AFN/AFD, máquina de estados, parser y autómata de pila, reportes y figuras. "
         "<b>No incluye:</b> captura de tráfico real, enrutamiento dinámico, interfaz web, base de datos."],
        ["Entradas", "red .txt, configuración .red, monitoreo .txt, consultas y datos por teclado."],
        ["Procesos principales", "1) Análisis léxico con regex · 2) Validación estructural con autómata de pila · "
         "3) Análisis sintáctico con la gramática · 4) Construcción del grafo · 5) Análisis del grafo · "
         "6) Procesamiento de monitoreo con AFN/AFD y máquina de estados · 7) Recalcular la red con fallas · "
         "8) Reporte."],
        ["Salidas", "Resultados en consola, reporte .txt, imágenes PNG, mensajes de error comprensibles."],
        ["Restricciones", "Python, CLI, sin bibliotecas que construyan autómatas o parsers, latencias enteras "
         "positivas, grafo no dirigido simple."],
    ], [4.0, 12.7]))
    return s


def propuesta_grafo():
    s = [H2("4.2 Modelado mediante grafos (Etapa 2)"), H3("4.2.1 Elementos del grafo")]
    s.append(tabla([
        ["Elemento", "Definición", "Significado en el dominio"],
        ["Vértices V", "Cada dispositivo de la red.", "Router, switch, servidor, PC, firewall, punto de "
         "acceso. Atributos: tipo, IP, zona y estado (Activo/Sobrecargado/Falla/Recuperación)."],
        ["Aristas E", "Par no ordenado {u, v} con peso w(u,v).", "Enlace físico o lógico entre dos "
         "dispositivos; el peso es la latencia del enlace en milisegundos."],
        ["Tipo", "Grafo simple, <b>no dirigido</b> y <b>ponderado</b>.", "Ver justificación."],
    ], [2.6, 5.6, 8.5]))
    s.append(Spacer(1, 4))
    s += bullets([
        "<b>¿Por qué no dirigido?</b> Un enlace Ethernet o inalámbrico transmite en ambos sentidos: si "
        "Router1 alcanza a Switch1, Switch1 alcanza a Router1. Modelarlo dirigido duplicaría cada arista "
        "sin aportar información. (Se documentará que, si se quisieran modelar reglas de firewall de un "
        "solo sentido, se necesitaría un grafo dirigido; queda fuera del alcance.)",
        "<b>¿Por qué ponderado?</b> Sin pesos, la «ruta más corta» solo cuenta saltos. Con la latencia como "
        "peso, el análisis responde a la pregunta real del administrador (ruta más rápida) y permite "
        "comparar rutas alternativas por costo. Los pesos son enteros positivos, condición necesaria "
        "para que Dijkstra sea correcto.",
    ])
    s.append(KeepTogether([H3("4.2.2 Representación del grafo de ejemplo"), figura("grafo_ejemplo.png", 13.5, "Figura 1. Topología de ejemplo (basada en el escenario "
                                                "del documento del proyecto) con latencias en ms.")]))
    nodos = ["Router1", "Switch1", "Switch2", "PC1", "PC2", "Server", "DB", "Impresora1"]
    enlaces = [("Router1", "Switch1", 2), ("Router1", "Switch2", 3), ("Switch1", "PC1", 1),
               ("Switch1", "PC2", 1), ("Switch2", "Server", 1), ("PC2", "DB", 4), ("Server", "DB", 2)]
    s.append(P("<b>V</b> = {Router1, Switch1, Switch2, PC1, PC2, Server, DB, Impresora1}, |V| = 8"))
    s.append(P("<b>E</b> = {" + ", ".join(f"{{{u}, {v}}}<sub>{w}</sub>" for u, v, w in enlaces) +
               "}, |E| = 7"))
    ady = {n: [] for n in nodos}
    for u, v, w in enlaces:
        ady[u].append(f"{v}({w})")
        ady[v].append(f"{u}({w})")
    filas = [["Vértice", "Lista de adyacencia: vecino(latencia)", "Grado"]]
    for n in nodos:
        filas.append([n, ", ".join(ady[n]) if ady[n] else "∅ (aislado)", str(len(ady[n]))])
    s.append(KeepTogether([P("<b>Lista de adyacencia</b>"), tabla(filas, [3.0, 11.5, 2.2], alinear_centro=(2,))]))
    s.append(Spacer(1, 6))
    abrev = ["R1", "S1", "S2", "PC1", "PC2", "Srv", "DB", "Imp"]
    peso = {}
    for u, v, w in enlaces:
        peso[(u, v)] = peso[(v, u)] = w
    filas = [[""] + abrev]
    for i, n in enumerate(nodos):
        filas.append([abrev[i]] + [str(peso.get((n, m), "0")) for m in nodos])
    s.append(KeepTogether([P("<b>Matriz de adyacencia ponderada</b> (0 = sin enlace; es simétrica porque el "
                             "grafo es no dirigido)"),
                           tabla(filas, [1.6] + [1.6] * 8, alinear_centro=range(9))]))
    s.append(H3("4.2.3 Análisis sobre el grafo y su utilidad"))
    s.append(P("El documento pide al menos dos análisis significativos; se implementarán ocho porque "
               "cada uno responde una pregunta distinta del administrador. Los resultados esperados en el "
               "grafo de ejemplo se resolverán a mano y servirán como prueba del programa."))
    s.append(tabla([
        ["Análisis", "Algoritmo", "Utilidad en el proyecto", "Resultado esperado en el ejemplo"],
        ["Existencia de ruta / conectividad", "BFS, O(V+E)", "¿Pueden comunicarse dos equipos?",
         "PC1 ↔ DB: sí. PC1 ↔ Impresora1: no."],
        ["Componentes conexas", "BFS/DFS repetido", "Detectar segmentos incomunicados.",
         "2 componentes: {7 nodos} y {Impresora1}."],
        ["Ruta más corta", "Dijkstra con heapq, O((V+E) log V)", "Ruta de menor latencia.",
         "Router1 → Switch2 → Server → DB = 6 ms."],
        ["Grados y aislados", "Recorrido de la lista de adyacencia", "Identificar equipos muy cargados "
         "o sin conexión.", "Máximo: Switch1 (3). Aislado: Impresora1."],
        ["Detección de ciclos", "DFS con control de padre", "Un ciclo indica redundancia (camino de respaldo).",
         "Router1–Switch1–PC2–DB–Server–Switch2–Router1."],
        ["Puntos críticos", "Tarjan (tiempos de descubrimiento y low)", "Puntos únicos de falla "
         "(articulaciones) y enlaces críticos (puentes).", "Articulación: Switch1. Puente: Switch1–PC1."],
        ["Rutas alternativas", "DFS con backtracking (rutas simples) ordenadas por costo",
         "Plan de respaldo si la ruta principal falla.",
         "Router1→DB: vía Switch2 (6 ms) y vía Switch1–PC2 (7 ms)."],
        ["Impacto de falla", "Quitar nodo + componentes/Dijkstra", "Qué se pierde si un equipo falla "
         "(se conecta con la máquina de estados).", "Si falla Server: Router1→DB pasa a 7 ms."],
    ], [3.2, 3.6, 4.6, 5.3]))
    s.append(Spacer(1, 4))
    s.append(P("<b>Salida visual en árbol</b> (árbol BFS desde un nodo elegido, como pide el documento):"))
    s.append(code("Router1\n├── Switch1 (2 ms)\n│   ├── PC1 (1 ms)\n│   └── PC2 (1 ms)\n└── Switch2 (3 ms)\n"
                  "    └── Server (1 ms)\n        └── DB (2 ms)\n\nNo alcanzables desde Router1: Impresora1"))
    return s


def propuesta_lenguaje():
    s = [H2("4.3 Definición formal del lenguaje (Etapa 3)")]
    s.append(P("Se define formalmente el lenguaje de las líneas del archivo de topología. Es el primer "
               "filtro del sistema: solo las cadenas que pertenecen a L<sub>enlaces</sub> se convierten en "
               "vértices y aristas."))
    s.append(H3("4.3.1 Alfabeto"))
    s.append(tabla([
        ["Subconjunto", "Símbolos", "Significado"],
        ["Letras", "{a, …, z, A, …, Z}", "Forman los nombres de dispositivo."],
        ["Dígitos", "{0, 1, …, 9}", "Forman parte de nombres y de la latencia."],
        ["Especiales de nombre", "{_ , -}", "Separadores permitidos dentro de un nombre (sw-core_01)."],
        ["Separador de campos", "{ , }", "Coma: separa origen, destino y latencia."],
        ["Espacio", "{sp}", "Espacio opcional alrededor de las comas."],
    ], [3.6, 4.8, 8.3]))
    s.append(P("Σ = Letras ∪ Dígitos ∪ {_, -, ',', sp}"))
    s.append(H3("4.3.2 Lenguaje"))
    s.append(code(
        "ID   = Letra · (Letra ∪ Dígito ∪ {_, -})^k ,        0 ≤ k ≤ 19     (1 a 20 símbolos)\n"
        "PESO = (Dígito − {0}) · Dígito^k ,                  0 ≤ k ≤ 3      (1 a 9999 ms)\n"
        "SEP  = sp* · ',' · sp*\n\n"
        "L_enlaces = { x               | x ∈ ID }                        (dispositivo sin enlaces)\n"
        "          ∪ { x·SEP·y         | x, y ∈ ID }                     (enlace, latencia 1 por omisión)\n"
        "          ∪ { x·SEP·y·SEP·p   | x, y ∈ ID, p ∈ PESO }           (enlace con latencia)"))
    s.append(P("Condición semántica adicional (se valida después del análisis léxico, no forma parte de "
               "la definición regular): x ≠ y, porque un enlace de un dispositivo consigo mismo no tiene "
               "sentido en la red."))
    s.append(P("Se define además el lenguaje de monitoreo, que usan los autómatas de las etapas 5 y 6. "
               "Cada evento del archivo de monitoreo se traduce a un símbolo: <font name='DVM'>ok → r</font> "
               "(respuesta), <font name='DVM'>lento → l</font> (latencia alta), <font name='DVM'>timeout → t</font>."))
    s.append(code("Σ_m = {r, l, t}\nL_falla = { w ∈ Σ_m* | w contiene la subcadena tt }"
                  "      (dos timeouts consecutivos = falla)"))
    s.append(H3("4.3.3 Ejemplos (10 válidas y 10 inválidas)"))
    validas = ["Router1,Switch1", "Router1,Switch2,3", "Switch1, PC1, 1", "PC2,DB,4", "Server,DB,2",
               "Impresora1", "sw-core_01,fw-perimetral,15", "AP3,Switch2,9999", "A,B",
               "Firewall_Edge,Router1,120"]
    invalidas = [
        ("Router1;Switch1", "El separador ';' no pertenece a Σ; el separador definido es la coma."),
        ("Router1,", "Falta el identificador de destino después de la coma."),
        ("1Router,Switch1", "Un ID debe iniciar con letra; inicia con dígito."),
        ("Router1,Switch1,0", "PESO no puede iniciar con 0: la latencia mínima es 1."),
        ("Router1,Switch1,10000", "PESO tiene como máximo 4 dígitos (≤ 9999)."),
        ("Router1,Switch1,2.5", "El punto no pertenece a Σ: la latencia es entera."),
        ("Router1,Switch1,3,7", "Tiene cuatro campos; el lenguaje admite como máximo tres."),
        ("Router 1,Switch1", "Un ID no puede contener espacios internos."),
        ("Router1,Switch1,05", "PESO con cero a la izquierda no está en (Dígito − {0})·Dígito^k."),
        ("Nodo_de_distribucion_principal,PC1", "El ID tiene 31 símbolos; el máximo es 20."),
    ]
    filas = [["#", "Cadena válida", "#", "Cadena inválida", "Motivo"]]
    for i in range(10):
        filas.append([str(i + 1), validas[i], str(i + 1), invalidas[i][0], invalidas[i][1]])
    s.append(tabla(filas, [0.8, 4.3, 0.8, 5.0, 5.8], mono=(1, 3), alinear_centro=(0, 2)))
    return s


def propuesta_regex():
    s = [H2("4.4 Expresiones regulares (Etapa 4)")]
    s.append(P("Se usarán cuatro expresiones regulares (el mínimo es tres). Todas se construyen a partir "
               "de las definiciones formales de la sección 4.3 y se aplican en el analizador léxico. "
               "Las cuatro se probaron en Python con los ejemplos que se muestran."))
    ID = "[A-Za-z][A-Za-z0-9_-]{0,19}"
    regex = [
        ("R1 · Nombre de dispositivo",
         "Reconocer identificadores válidos de dispositivos (vértices).",
         f"^{ID}$",
         "<font name='DVM'>[A-Za-z]</font>: el primer símbolo es una letra. "
         "<font name='DVM'>[A-Za-z0-9_-]{0,19}</font>: de 0 a 19 símbolos más entre letras, dígitos, guion "
         "bajo y guion (longitud total 1–20). <font name='DVM'>^…$</font>: la cadena completa debe "
         "coincidir, no solo una parte.",
         "Router1 · PC_01 · sw-core", "1Router · _pc · Ser ver · (21 letras A)",
         "<font name='DVM'>lenguajes/lexico.py → validar_nombre()</font>; lo reutilizan R2, R4 y el token "
         "<i>id</i> del parser."),
        ("R2 · Línea de enlace",
         "Validar cada línea del archivo de topología y extraer origen, destino y latencia.",
         rf"^\s*({ID})\s*,\s*({ID})\s*(?:,\s*([1-9][0-9]{{0,3}}))?\s*$",
         "Dos grupos con la estructura de R1 separados por coma; <font name='DVM'>\\s*</font> permite "
         "espacios opcionales. <font name='DVM'>(?:, …)?</font> hace opcional el tercer campo. "
         "<font name='DVM'>[1-9][0-9]{0,3}</font> es PESO: primer dígito distinto de cero y hasta 3 "
         "dígitos más (1–9999). Los grupos capturan los datos para construir la arista.",
         "Router1,Switch1 · Router1, Switch1, 5 · PC1,Switch1,9999",
         "PC1,Switch1,0 · PC1,Switch1,10000 · PC1;Switch1 · PC1, · PC1,Switch1,-3 · R1,S1,05",
         "<font name='DVM'>lenguajes/lexico.py → validar_linea_enlace()</font>, llamada por "
         "<font name='DVM'>red/grafo.py → cargar_desde_archivo()</font>."),
        ("R3 · Dirección IPv4",
         "Validar la IP de cada DISPOSITIVO en el archivo .red (token <i>ip</i>).",
         r"^((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])$",
         "Cada octeto se divide en casos para limitarlo a 0–255: <font name='DVM'>25[0-5]</font> (250–255), "
         "<font name='DVM'>2[0-4][0-9]</font> (200–249), <font name='DVM'>1[0-9]{2}</font> (100–199), "
         "<font name='DVM'>[1-9]?[0-9]</font> (0–99, sin ceros a la izquierda). "
         "<font name='DVM'>(octeto\\.){3}</font> exige tres octetos seguidos de punto y luego un cuarto "
         "octeto. Mejora la regex del documento <font name='DVM'>([0-9]{1,3}\\.){3}[0-9]{1,3}</font>, "
         "que aceptaría 999.999.999.999.",
         "192.168.1.10 · 10.0.0.1 · 255.255.255.255 · 0.0.0.0",
         "256.1.1.1 · 192.168.01.1 · 192.168.1 · 1.2.3.4.5",
         "<font name='DVM'>lenguajes/lexico.py → tokenizar_config()</font> (clasifica el token como ip)."),
        ("R4 · Línea de monitoreo",
         "Validar las líneas del archivo de monitoreo y extraer la secuencia de eventos de cada dispositivo.",
         rf"^\s*({ID})\s*:\s*((?:ok|lento|timeout)(?:\s*,\s*(?:ok|lento|timeout))*)\s*$",
         "Un nombre (R1), dos puntos y una lista de uno o más eventos del conjunto "
         "{ok, lento, timeout} separados por comas. <font name='DVM'>(?:ok|lento|timeout)</font> es una "
         "unión de tres palabras; <font name='DVM'>(?:,…)*</font> es la cerradura de Kleene para repetir "
         "eventos. El grupo 2 contiene la secuencia que se traduce a r/l/t para el AFN y el AFD.",
         "Server: ok, ok, timeout, timeout · DB:lento",
         "PC1: ping · PC1 ok · PC1: · PC1: ok,,timeout",
         "<font name='DVM'>lenguajes/lexico.py → validar_linea_monitoreo()</font>, llamada por "
         "<font name='DVM'>automatas/maquina_estados.py</font>."),
    ]
    for nombre, prop, expr, expl, val, inv, lugar in regex:
        s.append(KeepTogether([
            H3(nombre),
            tabla([
                ["Nombre", nombre.split("· ")[1]],
                ["Propósito", prop],
                ["Expresión regular", Paragraph(escape(expr), ST["cellm"])],
                ["Explicación", expl],
                ["Ejemplos válidos", Paragraph(escape(val), ST["cellm"])],
                ["Ejemplos inválidos", Paragraph(escape(inv), ST["cellm"])],
                ["Lugar de uso", lugar],
            ], [3.3, 13.4], encabezado=False, zebra=False),
        ]))
    s.append(nota("<b>Para la defensa:</b> cada integrante debe poder reconstruir cualquiera de las cuatro "
                  "expresiones a partir de las definiciones ID, PESO y SEP, y explicar por qué cada ejemplo "
                  "inválido es rechazado señalando el símbolo exacto donde falla."))
    return s


def propuesta_afn_afd():
    s = [H2("4.5 Autómata finito no determinista (Etapa 5)")]
    s.append(P("El AFN reconoce L<sub>falla</sub>: secuencias de monitoreo que contienen dos timeouts "
               "consecutivos, criterio con el que el sistema declara que un dispositivo presentó una falla "
               "en la ventana analizada. Está directamente relacionado con el lenguaje del proyecto: "
               "su entrada es el grupo 2 de la regex R4 traducido a Σ<sub>m</sub>."))
    s.append(code("N = (Q, Σ, δ, q0, F)\n"
                  "Q  = {q0, q1, q2}\n"
                  "Σ  = {r, l, t}        r = respuesta ok, l = respuesta lenta, t = timeout\n"
                  "q0 = estado inicial   (vigilando)\n"
                  "F  = {q2}             (falla detectada)"))
    s += bullets([
        "<b>q0 · vigilando:</b> lee cualquier evento y permanece; con <i>t</i> además «apuesta» a que ese "
        "timeout inicia una falla y pasa a q1. <b>Aquí está el no determinismo:</b> δ(q0, t) = {q0, q1}.",
        "<b>q1 · primer timeout:</b> solo continúa si el siguiente evento también es <i>t</i>; con r o l "
        "esa rama muere (δ = ∅).",
        "<b>q2 · falla detectada (aceptación):</b> ya se observaron dos timeouts seguidos; permanece "
        "con cualquier evento, porque la falla ya ocurrió en la ventana.",
    ])
    s.append(figura("afn_falla.png", 12.5, "Figura 2. Diagrama del AFN que reconoce L_falla."))
    filas = [["δ", "r", "l", "t"]]
    for q in AFN_ESTADOS:
        etiqueta = ("→ " if q == "q0" else "") + ("* " if q in AFN_FINALES else "") + q
        filas.append([etiqueta] + [fmt_conj(AFN_DELTA[(q, a)]) for a in SIGMA_M])
    s.append(KeepTogether([P("<b>Tabla de transiciones del AFN</b> (→ inicial, * aceptación)"),
                           tabla(filas, [3.0, 4.5, 4.5, 4.7], alinear_centro=(0, 1, 2, 3))]))
    s.append(Spacer(1, 6))
    pruebas = ["tt", "rtt", "ttr", "rltlttr", "lttl", "", "t", "rtrt", "tltl", "rrllr"]
    filas = [["Cadena", "Recorrido (conjunto de estados activos)", "Resultado"]]
    for w in pruebas:
        tr, ok = traza_afn(w)
        filas.append([w or "ε", tr, "Aceptada" if ok else "Rechazada"])
    s.append(KeepTogether([P("<b>Pruebas del AFN</b> (5 aceptadas y 5 rechazadas, recorrido calculado):"),
                           tabla(filas, [2.2, 11.8, 2.7], mono=(0, 1))]))

    s.append(H2("4.6 Conversión AFN → AFD por construcción de subconjuntos (Etapa 6)"))
    s.append(P("Se aplica el método de subconjuntos: el estado inicial del AFD es {q0}; para cada "
               "conjunto pendiente y cada símbolo se calcula mover(S, a) = ⋃ δ(q, a) para q ∈ S; cada "
               "conjunto nuevo se agrega a la lista de pendientes hasta que no aparecen conjuntos nuevos. "
               "Un estado del AFD es de aceptación si contiene algún estado final del AFN (q2). "
               "El procedimiento completo, calculado paso a paso, es:"))
    filas = [["Edo.", "Conjunto", "a", "mover(S, a)", "Resultado", "Nom.", "¿Nuevo?"]]
    for nombre, conj, a, det, dest, nom, nuevo in PASOS_AFD:
        filas.append([nombre, conj, a, det, dest, nom, nuevo])
    s.append(tabla(filas, [1.1, 2.4, 0.6, 6.9, 2.5, 1.2, 2.0], mono=(1, 3, 4),
                   alinear_centro=(0, 2, 5, 6)))
    s.append(Spacer(1, 6))
    filas = [["Estado AFD", "Conjunto del AFN", "r", "l", "t", "Tipo"]]
    for nombre in sorted(CONJ_DE):
        tipo = []
        if nombre == "A":
            tipo.append("Inicial")
        if nombre in FINALES_AFD:
            tipo.append("Final (contiene q2)")
        filas.append([nombre, fmt_conj(CONJ_DE[nombre])] + [TABLA_AFD[(nombre, a)] for a in SIGMA_M]
                     + [", ".join(tipo) or "—"])
    s.append(KeepTogether([P("<b>Nuevos estados y tabla de transición del AFD</b>"),
                           tabla(filas, [2.2, 3.8, 1.5, 1.5, 1.5, 6.2], mono=(1,), alinear_centro=(0, 2, 3, 4))]))
    s.append(figura("afd_falla.png", 15.5, "Figura 3. AFD obtenido. Estado inicial A; estados finales C y D."))
    s.append(P("<b>Estado inicial:</b> A = {q0}. <b>Estados finales:</b> C = {q0, q1, q2} y D = {q0, q2}, "
               "porque contienen q2. Observación para la defensa: C y D son equivalentes (ambos finales y "
               "con las mismas clases de destino), por lo que el AFD mínimo tiene 3 estados; se mostrará "
               "como análisis adicional."))
    pruebas = ["tt", "rtt", "ttr", "rltlttr", "lttl", "", "t", "rtrt", "tltl", "rrllr"]
    filas = [["Cadena", "Recorrido en el AFD", "AFD", "AFN", "¿Coinciden?"]]
    for w in pruebas:
        tr, ok = traza_afd(w)
        _, ok_n = traza_afn(w)
        filas.append([w or "ε", tr, "Acepta" if ok else "Rechaza", "Acepta" if ok_n else "Rechaza",
                      "✓" if ok == ok_n else "✗"])
    s.append(KeepTogether([P("<b>Comprobación de equivalencia AFN ↔ AFD</b> con las mismas cadenas:"),
                           tabla(filas, [2.2, 8.0, 2.0, 2.0, 2.5], mono=(0, 1), alinear_centro=(4,))]))
    s.append(P("Además, en las pruebas automáticas se comparará el AFN contra el AFD para <b>todas</b> las "
               "cadenas de Σ<sub>m</sub> de longitud 0 a 8 (9 841 cadenas). Esta verificación ya se realizó "
               "durante la planeación para longitudes 0 a 7 y ambos autómatas coincidieron en todos los casos."))

    s.append(H2("4.7 Máquina de estados de los dispositivos (extensión del proyecto)"))
    s.append(P("El documento del proyecto sugiere modelar los estados de cada dispositivo. Se diseñó un AFD "
               "completo sobre el mismo alfabeto Σ<sub>m</sub> que indica en qué estado se encuentra un "
               "dispositivo después de procesar su secuencia de monitoreo. A diferencia del AFN de falla "
               "(que responde «¿hubo falla?»), esta máquina responde «¿cómo está ahora?», y su resultado "
               "modifica el grafo."))
    s.append(figura("maquina_estados.png", 10.5, "Figura 4. Máquina de estados de un dispositivo."))
    s.append(tabla([
        ["Estado", "r (ok)", "l (lento)", "t (timeout)", "Efecto sobre el grafo"],
        ["→ Activo", "Activo", "Sobrecargado", "Sobrecargado", "Participa normalmente."],
        ["Sobrecargado", "Activo", "Sobrecargado", "Falla", "Participa; se marca en el reporte."],
        ["Falla", "Recuperación", "Recuperación", "Falla", "Se retira del grafo y se recalculan rutas."],
        ["Recuperación", "Activo", "Sobrecargado", "Falla", "Vuelve a participar."],
    ], [3.0, 2.4, 2.6, 2.6, 6.1]))
    s.append(P("Consistencia entre modelos: desde Activo, dos timeouts consecutivos llevan a Falla "
               "(Activo —t→ Sobrecargado —t→ Falla), exactamente el patrón que detecta el AFN. Ejemplo: "
               "<font name='DVM'>Server: ok, timeout, timeout</font> → r t t → Falla; al retirar Server, la ruta "
               "Router1 → DB cambia de 6 ms (vía Switch2) a 7 ms (vía Switch1 y PC2)."))
    return s


def propuesta_gramatica():
    s = [H2("4.8 Gramática y lenguaje libre de contexto (Etapa 7)")]
    s.append(P("Para describir redes con estructura jerárquica (una red con zonas, y zonas dentro de zonas, "
               "como edificio → piso → rack) se define el formato de configuración <b>.red</b>. "
               "Un ejemplo de archivo válido:"))
    s.append(code("RED campus {\n"
                  "    DISPOSITIVO Router1 router 192.168.1.1 ;\n"
                  "    ZONA datacenter {\n"
                  "        DISPOSITIVO Switch2 switch 192.168.1.3 ;\n"
                  "        DISPOSITIVO Server servidor 192.168.1.10 ;\n"
                  "        ZONA rack1 {\n"
                  "            DISPOSITIVO DB servidor 192.168.1.11 ;\n"
                  "        }\n"
                  "        ENLACE Switch2 Server 1 ;\n"
                  "        ENLACE Server DB 2 ;\n"
                  "    }\n"
                  "    ENLACE Router1 Switch2 3 ;\n"
                  "}"))
    s.append(P("El análisis léxico (regex) convierte el texto en tokens; la gramática define cómo deben "
               "combinarse. Los tokens <i>id</i>, <i>ip</i> y <i>num</i> se reconocen con R1, R3 y PESO."))
    s.append(H3("4.8.1 Definición formal G = (V, Σ, P, S)"))
    s += bullets([
        f"<b>V</b> = {{ {nt('red')}, {nt('bloque')}, {nt('elementos')}, {nt('elemento')}, {nt('zona')}, "
        f"{nt('dispositivo')}, {nt('tipo')}, {nt('enlace')} }}",
        "<b>Σ</b> = { RED, ZONA, DISPOSITIVO, ENLACE, {, }, ;, id, ip, num, router, switch, pc, servidor, firewall }",
        f"<b>S</b> = {nt('red')}",
    ])
    prods = [
        (1, nt("red"), f"RED id {nt('bloque')}"),
        (2, nt("bloque"), f"{{ {nt('elementos')} }}"),
        (3, nt("elementos"), f"{nt('elemento')} {nt('elementos')}"),
        (4, nt("elementos"), "ε"),
        (5, nt("elemento"), nt("zona")),
        (6, nt("elemento"), nt("dispositivo")),
        (7, nt("elemento"), nt("enlace")),
        (8, nt("zona"), f"ZONA id {nt('bloque')}"),
        (9, nt("dispositivo"), f"DISPOSITIVO id {nt('tipo')} ip ;"),
        (10, nt("tipo"), "router | switch | pc | servidor | firewall"),
        (11, nt("enlace"), "ENLACE id id num ;"),
    ]
    filas = [["#", "Producción", "Significado"]]
    signif = ["Una red tiene nombre y un bloque.", "Un bloque es una lista de elementos entre llaves.",
              "Lista de elementos (recursiva).", "La lista puede terminar (bloque vacío permitido).",
              "Un elemento puede ser una zona…", "…un dispositivo…", "…o un enlace.",
              "Una zona tiene nombre y su propio bloque: <b>aquí está la recursión que produce anidamiento</b>.",
              "Declaración de dispositivo con tipo e IP.", "Tipos de dispositivo admitidos (10a–10e).",
              "Enlace entre dos dispositivos con latencia."]
    for (n, izq, der), sig in zip(prods, signif):
        filas.append([str(n), f"{izq} → {der}", sig])
    s.append(tabla(filas, [0.8, 7.6, 8.3], alinear_centro=(0,)))
    s.append(Spacer(1, 6))
    s.append(H3("4.8.2 ¿Por qué es libre de contexto y no regular?"))
    s.append(P(f"Las producciones 2 y 8 permiten anidar zonas sin límite: "
               "RED id { ZONA id { ZONA id { … } } }. El número de llaves que cierran debe ser igual al número "
               "de llaves que abren, es decir, el lenguaje contiene la familia "
               "{ RED id { (ZONA id {)<super>n</super> }<super>n+1</super> | n ≥ 0 }. Por el lema de bombeo "
               "para lenguajes regulares, un AFD tendría que «contar» n con un número finito de estados, lo "
               "cual es imposible; por lo tanto se necesita una gramática libre de contexto (y un autómata de "
               "pila para reconocerla). La gramática es <b>LL(1)</b>: cada alternativa de "
               f"{nt('elemento')} y {nt('tipo')} comienza con un terminal distinto, lo que permite el parser "
               "descendente recursivo sin retroceso."))
    s.append(P("Validaciones semánticas que la gramática <b>no</b> puede expresar (dependen del contexto) y "
               "que se hacen después del análisis: un ENLACE solo puede usar dispositivos declarados, los "
               "nombres y las IP no se repiten y un enlace no conecta un dispositivo consigo mismo."))
    s.append(H3("4.8.3 Derivaciones por la izquierda (5 cadenas válidas)"))
    s.append(P("Se muestran sobre tokens; entre paréntesis, la producción aplicada."))
    E, EL, ELM, B = nt("elementos"), nt("elemento"), nt("elementos"), nt("bloque")
    deriv = [
        ("D1 · RED campus { }", [
            (nt("red"), ""), (f"RED id {B}", "1"), (f"RED id {{ {E} }}", "2"), ("RED id { }", "4")]),
        ("D2 · RED lab { DISPOSITIVO R1 router 10.0.0.1 ; }", [
            (nt("red"), ""), (f"RED id {B}", "1"), (f"RED id {{ {E} }}", "2"),
            (f"RED id {{ {EL} {E} }}", "3"), (f"RED id {{ {nt('dispositivo')} {E} }}", "6"),
            (f"RED id {{ DISPOSITIVO id {nt('tipo')} ip ; {E} }}", "9"),
            (f"RED id {{ DISPOSITIVO id router ip ; {E} }}", "10a"),
            ("RED id { DISPOSITIVO id router ip ; }", "4")]),
        ("D3 · RED lab { ENLACE PC1 Switch1 1 ; }", [
            (nt("red"), ""), (f"RED id {B}", "1"), (f"RED id {{ {E} }}", "2"),
            (f"RED id {{ {EL} {E} }}", "3"), (f"RED id {{ {nt('enlace')} {E} }}", "7"),
            (f"RED id {{ ENLACE id id num ; {E} }}", "11"), ("RED id { ENLACE id id num ; }", "4")]),
        ("D4 · RED campus { ZONA dc { } }", [
            (nt("red"), ""), (f"RED id {B}", "1"), (f"RED id {{ {E} }}", "2"),
            (f"RED id {{ {EL} {E} }}", "3"), (f"RED id {{ {nt('zona')} {E} }}", "5"),
            (f"RED id {{ ZONA id {B} {E} }}", "8"), (f"RED id {{ ZONA id {{ {E} }} {E} }}", "2"),
            (f"RED id {{ ZONA id {{ }} {E} }}", "4"), ("RED id { ZONA id { } }", "4")]),
        ("D5 · RED campus { DISPOSITIVO S servidor 10.0.0.5 ; ZONA dc { ENLACE A B 5 ; } }", [
            (nt("red"), ""), (f"RED id {B}", "1"), (f"RED id {{ {E} }}", "2"),
            (f"RED id {{ {EL} {E} }}", "3"), (f"RED id {{ {nt('dispositivo')} {E} }}", "6"),
            (f"RED id {{ DISPOSITIVO id {nt('tipo')} ip ; {E} }}", "9"),
            (f"RED id {{ DISPOSITIVO id servidor ip ; {E} }}", "10d"),
            (f"RED id {{ DISPOSITIVO id servidor ip ; {EL} {E} }}", "3"),
            (f"RED id {{ DISPOSITIVO id servidor ip ; {nt('zona')} {E} }}", "5"),
            (f"RED id {{ DISPOSITIVO id servidor ip ; ZONA id {B} {E} }}", "8"),
            (f"RED id {{ DISPOSITIVO id servidor ip ; ZONA id {{ {E} }} {E} }}", "2"),
            (f"RED id {{ DISPOSITIVO id servidor ip ; ZONA id {{ {EL} {E} }} {E} }}", "3"),
            (f"RED id {{ DISPOSITIVO id servidor ip ; ZONA id {{ {nt('enlace')} {E} }} {E} }}", "7"),
            (f"RED id {{ DISPOSITIVO id servidor ip ; ZONA id {{ ENLACE id id num ; {E} }} {E} }}", "11"),
            (f"RED id {{ DISPOSITIVO id servidor ip ; ZONA id {{ ENLACE id id num ; }} {E} }}", "4"),
            ("RED id { DISPOSITIVO id servidor ip ; ZONA id { ENLACE id id num ; } }", "4")]),
    ]
    for titulo, pasos in deriv:
        filas = [["Paso", "Forma sentencial", "Prod."]]
        for i, (forma, prod) in enumerate(pasos):
            filas.append([str(i), ("⇒ " if i else "") + forma, prod or "S"])
        s.append(KeepTogether([P(f"<b>{titulo}</b>"),
                               tabla(filas, [1.1, 14.2, 1.4], alinear_centro=(0, 2)),
                               Spacer(1, 6)]))
    s.append(H3("4.8.4 Cadenas que no pueden generarse (5)"))
    s.append(tabla([
        ["Cadena", "Motivo"],
        ["ZONA dc { }", f"Toda derivación inicia en {nt('red')}, que exige el terminal RED al principio."],
        ["RED campus { ZONA dc { }", "Falta una llave de cierre: cada producción 2 genera { y } en pareja."],
        ["RED campus { ENLACE R1 R2 ; }", "La producción 11 exige num antes de ';' (falta la latencia)."],
        ["RED campus { DISPOSITIVO R1 modem 10.0.0.1 ; }", f"«modem» no es terminal de {nt('tipo')} (prod. 10)."],
        ["RED a { } RED b { }", f"{nt('red')} genera una sola red; no hay producción que concatene dos."],
    ], [7.2, 9.5], mono=(0,)))
    return s


def propuesta_pila():
    s = [H2("4.9 Autómata de pila (Etapa 8)")]
    s.append(P("El autómata de pila valida la <b>estructura de bloques</b> del archivo .red antes del parser, "
               "y muestra cómo cambia la pila conforme se abren y cierran bloques. Trabaja sobre la secuencia "
               "de tokens producida por el analizador léxico (<i>tipo</i> representa cualquiera de router, "
               "switch, pc, servidor, firewall)."))
    s.append(tabla([
        ["Aspecto", "Diseño"],
        ["¿Qué estructura reconoce?", "Archivos .red bien anidados: una RED con zonas, dispositivos y enlaces, "
         "con zonas dentro de zonas a cualquier profundidad."],
        ["¿Qué se almacena en la pila?", "Un símbolo por cada bloque abierto: <b>R</b> para el bloque de la RED "
         "y <b>Z</b> por cada ZONA abierta. Z0 marca el fondo. El programa muestra además el nombre "
         "(p. ej. Z[datacenter]) para que la traza sea legible."],
        ["¿Cuándo se introduce información?", "Al leer '{' después de RED id (push R) o después de ZONA id (push Z)."],
        ["¿Cuándo se retira?", "Al leer '}': si el tope es Z se cierra una zona; si el tope es R se cierra la red."],
        ["Condición de aceptación", "Estado final qf, entrada consumida por completo y pila con solo Z0 "
         "(todos los bloques cerrados)."],
    ], [4.4, 12.3]))
    s.append(Spacer(1, 6))
    s.append(code("M = (Q, Σ, Γ, δ, q0, Z0, F)\n"
                  "Q = {q0, q1, …, q13, qf}      Γ = {Z0, R, Z}      F = {qf}\n"
                  "Σ = {RED, ZONA, DISPOSITIVO, ENLACE, id, tipo, ip, num, {, }, ;}\n"
                  "X representa cualquier símbolo del tope en {R, Z} (se conserva)."))
    s.append(tabla([
        ["Estado", "Significado"],
        ["q0", "Inicio: se espera RED."], ["q1, q2", "Se leyó RED; se espera su nombre y luego '{'."],
        ["q3", "<b>Dentro de un bloque</b>: se espera ZONA, DISPOSITIVO, ENLACE o '}'."],
        ["q4, q5", "Se leyó ZONA; se espera su nombre y luego '{'."],
        ["q6, q7, q8", "Declaración DISPOSITIVO: se esperan id, tipo e ip."],
        ["q10, q11, q12", "Declaración ENLACE: se esperan id, id y num."],
        ["q9", "Fin de declaración: se espera ';' para volver a q3."],
        ["q13", "Se cerró el bloque de la RED."], ["qf", "Aceptación."],
    ], [3.0, 13.7]))
    s.append(Spacer(1, 6))
    filas = [["#", "δ(estado, entrada, tope)", "→ (estado, cadena que reemplaza al tope)", "Acción en la pila"]]
    accion = {"R": "push R", "Z": "push Z"}
    for i, ((q, a, x), (p, emp)) in enumerate(AP_DELTA.items(), 1):
        if not emp:
            acc = f"pop {x}"
        elif len(emp) == 2:
            acc = accion[emp[0]]
        else:
            acc = "sin cambio"
        filas.append([str(i), f"δ({q}, {a}, {x})", f"({p}, {' '.join(emp) if emp else 'ε'})", acc])
    filas.append([str(len(AP_DELTA) + 1), "δ(q13, ε, Z0)", "(qf, Z0)", "sin cambio · aceptar"])
    s.append(KeepTogether([P("<b>Función de transición</b>"),
                           tabla(filas, [0.8, 5.6, 6.4, 3.9], mono=(1, 2), alinear_centro=(0,))]))
    s.append(P("El diagrama AP.png se generará con la misma convención que los demás autómatas: las "
               "transiciones se etiquetan «entrada, tope / reemplazo»."))
    ejemplos = [
        ("Aceptada 1", "RED id { }"),
        ("Aceptada 2", "RED id { DISPOSITIVO id tipo ip ; ENLACE id id num ; }"),
        ("Aceptada 3", "RED id { ZONA id { ZONA id { DISPOSITIVO id tipo ip ; } } }"),
        ("Rechazada 1", "RED id { ZONA id { }"),
        ("Rechazada 2", "RED id { } }"),
        ("Rechazada 3", "RED id DISPOSITIVO id tipo ip ;"),
    ]
    s.append(H3("Trazas con el contenido de la pila (3 aceptadas, 3 rechazadas)"))
    s.append(P("Columna «Pila»: el tope está a la izquierda. Las trazas se calcularon simulando el autómata."))
    for titulo, cad in ejemplos:
        ok, filas_t, motivo = simular_ap(cad.split())
        filas = [["#", "Estado", "Entrada restante", "Transición", "Pila"]] + [list(f) for f in filas_t]
        color = VERDE if ok else NARANJA
        s.append(KeepTogether([
            P(f"<b>{titulo}:</b> <font name='DVM'>{escape(cad)}</font>"),
            tabla(filas, [1.0, 1.4, 7.4, 4.0, 2.9], mono=(2, 3, 4), color=color, alinear_centro=(0, 1)),
            P(f"<b>Resultado: {'ACEPTADA' if ok else 'RECHAZADA'}.</b> {motivo}"),
            Spacer(1, 4)]))
    return s


def propuesta_implementacion():
    s = [H2("4.10 Implementación computacional (Etapa 9)"), H3("4.10.1 Arquitectura")]
    s.append(P("La aplicación sigue una arquitectura en capas, en el mismo orden en que la teoría procesa "
               "la información. Cada capa es un módulo independiente con pruebas propias, lo que permite "
               "que ambos integrantes trabajen en paralelo y que cualquier fragmento pueda explicarse aislado."))
    s.append(code(
        "  Entrada (archivo .txt / .red / monitoreo, o teclado)\n"
        "        │\n"
        "        ▼\n"
        "  [1] Analizador léxico ── regex R1–R4 ──────────────► errores léxicos (línea, motivo)\n"
        "        │ tokens / registros\n"
        "        ▼\n"
        "  [2] Autómata de pila ── anidamiento de bloques ────► bloques sin cerrar / '}' sobrante\n"
        "        ▼\n"
        "  [3] Parser descendente recursivo ── gramática G ──► errores sintácticos y semánticos\n"
        "        │ estructura validada\n"
        "        ▼\n"
        "  [4] Grafo (lista de adyacencia) ◄── [6] Máquina de estados ◄── AFN/AFD de falla ◄── monitoreo\n"
        "        │                              (retira nodos en Falla)\n"
        "        ▼\n"
        "  [5] Algoritmos: BFS, DFS, Dijkstra, grados, ciclos, Tarjan, rutas alternativas\n"
        "        ▼\n"
        "  Salida: consola · reporte .txt · PNG (grafo, AFN, AFD, AP)"))
    s.append(H3("4.10.2 Estructura del código"))
    s.append(code(
        "02_Codigo/\n"
        "├── main.py                    # menú CLI, argumentos, manejo de errores\n"
        "├── red/\n"
        "│   ├── grafo.py               # clase Grafo: lista/matriz de adyacencia, carga de archivos\n"
        "│   └── algoritmos.py          # BFS, DFS, Dijkstra, grados, ciclos, Tarjan, rutas alternativas\n"
        "├── lenguajes/\n"
        "│   └── lexico.py              # regex R1–R4, validación por línea, tokenizador de .red\n"
        "├── automatas/\n"
        "│   ├── afn.py                 # clase AFN y simulación con traza de conjuntos\n"
        "│   ├── afd.py                 # clase AFD y simulación con traza\n"
        "│   ├── conversion.py          # construcción de subconjuntos (tabla de pasos)\n"
        "│   └── maquina_estados.py     # estados Activo/Sobrecargado/Falla/Recuperación\n"
        "├── gramatica/\n"
        "│   ├── parser.py              # parser descendente recursivo + derivación + semántica\n"
        "│   └── automata_pila.py       # autómata de pila con traza de la pila\n"
        "├── reportes/\n"
        "│   ├── visualizacion.py       # PNG con matplotlib y árbol de texto\n"
        "│   └── reporte.py             # exportar reporte .txt\n"
        "├── datos/                     # red_ejemplo.txt, red_campus.red, monitoreo.txt, invalidos/\n"
        "├── tests/                     # pytest: un archivo por módulo + prueba de sistema\n"
        "├── requirements.txt\n"
        "└── README.md"))
    s.append(H3("4.10.3 Funcionamiento de la CLI"))
    s.append(tabla([
        ["Opción", "Función", "Modelo aplicado"],
        ["1", "Cargar topología desde archivo .txt", "Lenguaje L_enlaces + R1/R2"],
        ["2", "Cargar configuración .red", "R1/R3 + autómata de pila + gramática"],
        ["3", "Capturar enlaces por teclado", "R2 en cada línea"],
        ["4", "Mostrar el grafo (V, E, lista, matriz, árbol, PNG)", "Grafos"],
        ["5", "Análisis: ruta, ruta más corta, grados, aislados, ciclos, puntos críticos, rutas alternativas",
         "Algoritmos sobre grafos"],
        ["6", "Procesar monitoreo y ver impacto de fallas", "R4 + AFN/AFD + máquina de estados + grafos"],
        ["7", "Laboratorio teórico: probar cadenas en AFN, AFD y autómata de pila con traza; ver la "
              "tabla de conversión", "AFN, AFD, subconjuntos, AP"],
        ["8", "Exportar reporte .txt e imágenes", "—"],
        ["0", "Salir", "—"],
    ], [1.4, 10.0, 5.3], alinear_centro=(0,)))
    s.append(Spacer(1, 6))
    s.append(P("Ejemplo de salida esperada:"))
    s.append(code(
        "==========================================\n"
        "        NETWORK GRAPH ANALYZER\n"
        "==========================================\n"
        "> Opción: 1\n"
        "Archivo: datos/red_ejemplo_errores.txt\n"
        "Analizando...\n\n"
        "Línea 1  Router1,Switch1,2        ✓ válida\n"
        "Línea 2  Router1;Switch2          ✗ RECHAZADA\n"
        "         Motivo: el separador ';' no pertenece al alfabeto; se esperaba ','.\n"
        "Línea 3  Switch1,PC1,0            ✗ RECHAZADA\n"
        "         Motivo: la latencia debe ser un entero entre 1 y 9999.\n"
        "Línea 4  PC1,PC1                  ✗ RECHAZADA\n"
        "         Motivo: un dispositivo no puede enlazarse consigo mismo.\n\n"
        "Resultado: 1 enlace cargado, 3 líneas rechazadas.\n\n"
        "> Opción: 5 → Ruta más corta\n"
        "Origen: Router1   Destino: DB\n"
        "Ruta: Router1 → Switch2 → Server → DB    Latencia total: 6 ms"))
    s.append(P("Cumplimiento de «El programa deberá»: (1) recibe datos por archivo y teclado; (2) los procesa "
               "por capas; (3) los valida con regex, AP y gramática; (4) aplica grafo, AFN, AFD, máquina de "
               "estados, gramática y AP; (5) muestra resultados formateados; (6) identifica la línea y el "
               "símbolo incorrectos; (7) muestra mensajes en lenguaje natural, nunca un traceback de Python."))
    return s


CASOS_PRUEBA = [
    ("P01", "Cargar red_ejemplo.txt", "Válida / normal", "8 dispositivos, 7 enlaces cargados"),
    ("P02", "Ruta más corta Router1 → DB", "Válida / normal", "Router1→Switch2→Server→DB, 6 ms"),
    ("P03", "¿Existe ruta PC1 → Impresora1?", "Válida / normal", "No existe ruta (componentes distintas)"),
    ("P04", "Puntos críticos de la red de ejemplo", "Válida / normal", "Articulación: Switch1; puente: Switch1–PC1"),
    ("P05", "Detectar ciclos", "Válida / normal", "Ciclo Router1–Switch1–PC2–DB–Server–Switch2–Router1"),
    ("P06", "Grados y aislados", "Válida / normal", "Switch1 = 3 (máximo); Impresora1 aislado"),
    ("P07", "Línea «Router1;Switch1»", "Inválida", "Rechazada: separador no válido (línea indicada)"),
    ("P08", "Línea «Router1,Switch1,0»", "Inválida", "Rechazada: latencia fuera de rango"),
    ("P09", "Archivo vacío", "Límite", "Mensaje: el archivo no contiene dispositivos"),
    ("P10", "Archivo con un solo dispositivo «Impresora1»", "Límite", "Grafo de 1 vértice, 0 aristas, aislado"),
    ("P11", "Nombre de exactamente 20 caracteres / de 21", "Límite", "20: aceptado · 21: rechazado"),
    ("P12", "Lazo «PC1,PC1»", "Inesperada", "Rechazada: enlace consigo mismo"),
    ("P13", "Enlace duplicado «PC1,Switch1» dos veces", "Inesperada", "Advertencia; se conserva el primero"),
    ("P14", "Monitoreo «Server: ok, timeout, timeout»", "Válida / normal",
     "AFN y AFD aceptan; Server → Falla; Router1→DB = 7 ms"),
    ("P15", "Monitoreo «DB: timeout, ok, timeout»", "Válida / normal", "AFN y AFD rechazan; DB → Sobrecargado"),
    ("P16", "Monitoreo «PC1: ping»", "Inválida", "Error léxico: evento desconocido «ping»"),
    ("P17", "Archivo .red con zonas anidadas (3 niveles)", "Válida / normal",
     "AP acepta; profundidad máxima de pila 3; grafo construido"),
    ("P18", ".red con una ZONA sin cerrar", "Inválida", "AP rechaza: termina con pila Z R Z0; indica la zona"),
    ("P19", ".red con tipo «modem»", "Inválida", "Error sintáctico: se esperaba un tipo de dispositivo"),
    ("P20", ".red con ENLACE a dispositivo no declarado", "Inválida", "Error semántico: «X» no fue declarado"),
    ("P21", "Ruta más corta entre un nodo y él mismo", "Límite", "Ruta de 0 ms con un solo vértice"),
    ("P22", "Archivo inexistente / opción de menú «abc»", "Inesperada", "Mensaje claro, el programa no se cierra"),
]


def propuesta_pruebas():
    s = [H2("4.11 Plan de casos de prueba (Etapa 10)")]
    s.append(P("Se diseñaron 22 casos del sistema completo (el mínimo es 15) que cubren las cinco "
               "categorías del documento. El resultado esperado se fija <b>antes</b> de ejecutar; las "
               "columnas «Resultado obtenido» y «Estado» se llenan en la actividad A24."))
    filas = [["ID", "Entrada", "Categoría", "Resultado esperado", "Obtenido", "Estado"]]
    for c in CASOS_PRUEBA:
        filas.append(list(c) + ["", ""])
    s.append(tabla(filas, [1.0, 4.6, 2.4, 5.0, 1.9, 1.8], alinear_centro=(0,)))
    s.append(Spacer(1, 4))
    s.append(P("Además de esta tabla, cada módulo tendrá pruebas automáticas con pytest (regex con las 20 "
               "cadenas de la Etapa 3, equivalencia AFN/AFD exhaustiva, trazas del autómata de pila, "
               "resultados de los algoritmos contra los resueltos a mano). Si un caso falla, se documenta "
               "la causa, la corrección y la re-prueba, o bien la limitación."))
    return s


# ----------------------------------------------------------------------
# Cronograma y actividades
# ----------------------------------------------------------------------
D = lambda d, m: date(2026, m, d)  # noqa: E731

ACTIVIDADES = [
    # id, título, responsable, apoyo, inicio, fin, etapa, objetivo, pasos, entregable, criterio
    ("A01", "Análisis del documento y matriz de requisitos", "Ambos", "—", D(11, 11), D(11, 11),
     "Todas (secciones 1–22)",
     "Comprender cada requisito del proyecto, sus mínimos cuantitativos y su peso en la rúbrica, para "
     "que ningún punto quede sin responsable.",
     ["Leer completas las 22 secciones del documento del proyecto y el desglose del Proyecto 4.",
      "Extraer cada requisito con su mínimo (10/10 cadenas, 3 regex, 5/5 cadenas en el AFN, 5 derivaciones, "
      "3/3 ejemplos del AP, 15 casos de prueba, etc.).",
      "Construir la matriz de trazabilidad (sección 7.4) y asignar actividad, responsable y fecha.",
      "Identificar riesgos: demostración con entradas no preparadas y restricción de bibliotecas.",
      "Acordar convenciones: nombres en español, snake_case, docstrings en cada función, comentarios "
      "que expliquen el «por qué»."],
     "Este plan de trabajo y la matriz de requisitos.",
     "Cada requisito del documento tiene responsable, actividad y fecha."),
    ("A02", "Repositorio, estructura de carpetas y entorno", "Hiram", "Axel", D(11, 11), D(12, 11),
     "Secciones 11 y 17",
     "Dejar listo el entorno común para trabajar en paralelo sin conflictos.",
     ["Crear las carpetas 01_Documentacion a 07_Evidencias y la estructura de 02_Codigo (sección 4.10.2).",
      "Crear requirements.txt, .gitignore y un main.py mínimo con el menú vacío.",
      "Definir el flujo de Git: rama por integrante (feature/grafos-gramatica, feature/lenguajes-automatas), "
      "integración a master solo con revisión del compañero.",
      "Verificar Python 3.14 y las dependencias en ambas computadoras.",
      "Acordar las interfaces entre módulos (firmas de funciones del léxico que usará el parser y el grafo)."],
     "Repositorio en GitHub con el esqueleto del proyecto.",
     "Ambos clonan el repositorio y ejecutan main.py y pytest sin errores."),
    ("A03", "Bitácora de trabajo", "Axel", "Hiram", D(12, 11), D(12, 11), "Sección 15",
     "Documentar la evolución del proyecto y la participación de cada integrante.",
     ["Crear 07_Evidencias/Bitacora.xlsx con columnas Fecha, Actividad, Responsable(s), Resultado y "
      "Problema / Solución.",
      "Registrar la sesión de análisis (10/11/2026) y la planeación.",
      "A partir de aquí, registrar cada sesión de trabajo y vincularla con los commits correspondientes.",
      "Marcar los problemas encontrados para usarlos en la sección 17 del documento final."],
     "07_Evidencias/Bitacora.xlsx (actualizada durante todo el proyecto).",
     "Al menos un registro por cada actividad terminada."),
    ("A04", "Definición del problema (Etapa 1)", "Hiram", "Axel", D(13, 11), D(14, 11), "Etapa 1",
     "Explicar con claridad qué problema se resuelve, para quién y con qué límites.",
     ["Redactar las respuestas a las 7 preguntas guía (base: sección 4.1 de este plan).",
      "Desarrollar los 7 elementos mínimos: descripción, objetivo, alcance (incluye / no incluye), entradas, "
      "procesos principales, salidas y restricciones.",
      "Describir el escenario de ejemplo (red del laboratorio) que se usará en todo el documento.",
      "Revisión de Axel: verificar que alcance y restricciones coincidan con lo que realmente se programará."],
     "Secciones 1 a 5 del documento final (borrador).",
     "Cubre las 7 preguntas y los 7 elementos «deberán incluir al menos»."),
    ("A05", "Diseño del modelo de grafo (Etapa 2.1)", "Hiram", "Axel", D(13, 11), D(14, 11), "Etapa 2.1",
     "Definir los elementos del grafo y justificar su tipo.",
     ["Definir vértices (dispositivos y sus atributos) y aristas (enlaces con latencia).",
      "Justificar «no dirigido» y «ponderado», y explicar por qué se descarta la alternativa dirigida.",
      "Fijar la topología de ejemplo (8 dispositivos, 7 enlaces) y diseñar una segunda topología de unos "
      "15 nodos con dos ciclos y dos componentes para las pruebas.",
      "Resolver a mano los 8 análisis en la topología de ejemplo (tabla de la sección 4.2.3)."],
     "Tabla de elementos del grafo con su justificación y resultados resueltos a mano.",
     "Cada elemento tiene significado en el dominio y la elección está justificada."),
    ("A06", "Representaciones del grafo (Etapa 2.2)", "Hiram", "Axel", D(15, 11), D(16, 11), "Etapa 2.2",
     "Presentar las cuatro representaciones que pide el documento.",
     ["Representación gráfica (Grafo.png) con latencias en las aristas.",
      "Conjunto de vértices V y conjunto de aristas E con pesos.",
      "Lista de adyacencia y matriz de adyacencia ponderada 8×8.",
      "Comprobar a mano que la matriz es simétrica y que la suma de grados es 2|E| = 14."],
     "04_Grafos/Grafo.png y las tablas de la sección 6 del documento.",
     "La lista y la matriz coinciden exactamente con E."),
    ("A07", "Estructura Grafo y carga de topologías", "Hiram", "Axel", D(15, 11), D(17, 11), "Etapas 2 y 9",
     "Implementar la estructura de datos sobre la que trabajan todos los análisis.",
     ["Clase Grafo con un diccionario de diccionarios {nodo: {vecino: latencia}} y atributos por dispositivo.",
      "Métodos: agregar_dispositivo, agregar_enlace (rechaza lazos y avisa de duplicados), "
      "eliminar_dispositivo (para simular fallas), vecinos, lista_adyacencia, matriz_adyacencia.",
      "cargar_desde_archivo(ruta): lee línea por línea, ignora líneas vacías y comentarios '#', y valida "
      "con el léxico (al principio con una versión provisional; se integra con A11).",
      "Árbol BFS en texto (├──, └──) desde un nodo elegido.",
      "Pruebas en tests/test_grafo.py."],
     "02_Codigo/red/grafo.py y tests/test_grafo.py — versión 0.1.",
     "Carga red_ejemplo.txt y muestra V, E, lista, matriz y árbol correctos."),
    ("A08", "Algoritmos de análisis sobre el grafo (Etapa 2.3)", "Hiram", "Axel", D(16, 11), D(20, 11),
     "Etapa 2.3",
     "Implementar análisis útiles para el administrador de la red.",
     ["BFS: alcanzables, existencia de ruta y ruta con menos saltos.",
      "DFS: componentes conexas y detección de ciclos (vecino visitado que no es el padre).",
      "Dijkstra con heapq para la ruta de menor latencia, con reconstrucción del camino.",
      "Grados de cada nodo, nodo de mayor grado y dispositivos aislados.",
      "Puntos de articulación y puentes con el algoritmo de Tarjan (disc[] y low[]).",
      "Rutas alternativas: todas las rutas simples entre dos nodos (DFS con backtracking y límite), "
      "ordenadas por costo.",
      "Impacto de falla: copiar el grafo sin el nodo y recalcular componentes y rutas.",
      "Documentar la complejidad de cada algoritmo y preparar la explicación paso a paso de cada uno."],
     "02_Codigo/red/algoritmos.py y tests/test_algoritmos.py.",
     "Los resultados del programa coinciden con los resueltos a mano en A05."),
    ("A09", "Definición formal del lenguaje (Etapa 3)", "Axel", "Hiram", D(13, 11), D(15, 11), "Etapa 3",
     "Definir formalmente el lenguaje de entrada del sistema.",
     ["Especificar Σ y el significado de cada subconjunto de símbolos.",
      "Definir ID, PESO y SEP y, con ellos, L_enlaces por comprensión (sección 4.3.2).",
      "Definir Σ_m y L_falla para el monitoreo.",
      "Escribir 10 cadenas válidas y 10 inválidas, cada inválida con su motivo.",
      "Distinguir errores léxicos (no pertenecen a L) de errores semánticos (lazo, duplicado)."],
     "Sección 7 del documento final.",
     "Al menos 10/10 cadenas con motivo, todas comprobadas contra la regex correspondiente."),
    ("A10", "Diseño de las expresiones regulares (Etapa 4)", "Axel", "Hiram", D(16, 11), D(18, 11), "Etapa 4",
     "Construir las regex a partir de las definiciones formales y saber explicarlas símbolo por símbolo.",
     ["Construir R1 (nombre), R2 (línea de enlace), R3 (IPv4) y R4 (monitoreo) por partes.",
      "Para cada una: nombre, propósito, expresión, explicación, válidos, inválidos y lugar de uso.",
      "Probar cada regex en Python con listas de cadenas válidas e inválidas.",
      "Preparar la explicación de por qué R3 mejora la regex de IP del documento del proyecto."],
     "Sección 8 del documento final.",
     "Cada integrante explica cualquier regex sin apoyo."),
    ("A11", "Analizador léxico (lexico.py)", "Axel", "Hiram", D(18, 11), D(19, 11), "Etapas 4 y 9",
     "Aplicar las regex dentro del programa con diagnósticos precisos.",
     ["Compilar R1–R4 una sola vez como constantes del módulo.",
      "validar_linea_enlace(linea, numero) → datos o un error con número de línea y motivo.",
      "Diagnóstico del motivo: probar por partes (separador, ID de origen, ID de destino, latencia) para "
      "decir exactamente qué falló.",
      "tokenizar_config(texto): convierte un .red en tokens (palabras reservadas, id, ip, num, símbolos) "
      "con su línea.",
      "validar_linea_monitoreo(linea) → (dispositivo, secuencia r/l/t)."],
     "02_Codigo/lenguajes/lexico.py y tests/test_regex.py.",
     "Las 20 cadenas de la Etapa 3 y los ejemplos de las regex se clasifican bien en pytest."),
    ("A12", "Diseño del AFN (Etapa 5)", "Axel", "Hiram", D(19, 11), D(20, 11), "Etapa 5",
     "Diseñar el AFN que reconoce L_falla y documentarlo completo.",
     ["Definir la quíntupla (Q, Σ, δ, q0, F) y el significado de cada estado.",
      "Dibujar AFN.png y construir la tabla de transiciones.",
      "Explicar dónde está el no determinismo, δ(q0, t) = {q0, q1}.",
      "Probar 5 cadenas aceptadas y 5 rechazadas mostrando el recorrido de conjuntos (sección 4.5)."],
     "03_Automatas/AFN.png y sección 9 del documento.",
     "Los recorridos a mano coinciden con la simulación del programa."),
    ("A13", "Conversión AFN → AFD (Etapa 6)", "Axel", "Hiram", D(21, 11), D(22, 11), "Etapa 6",
     "Mostrar el procedimiento completo de la construcción de subconjuntos.",
     ["Partir del AFN original y su tabla.",
      "Calcular mover(S, a) para cada conjunto pendiente y cada símbolo, registrando cada paso.",
      "Nombrar los nuevos estados A–D e identificar el inicial (A) y los finales (C y D).",
      "Construir la tabla de transición del AFD y su diagrama AFD.png.",
      "Comprobar con las mismas 10 cadenas que el AFN y el AFD dan el mismo resultado.",
      "Análisis adicional: mostrar que C y D son equivalentes (AFD mínimo de 3 estados)."],
     "03_Automatas/AFD.png y sección 10 del documento.",
     "El documento muestra el procedimiento, no solo el resultado (los 8 puntos de la Etapa 6)."),
    ("A14", "Implementación de AFN, AFD y conversión", "Axel", "Hiram", D(22, 11), D(24, 11), "Etapas 5, 6 y 9",
     "Programar los autómatas y la conversión sin bibliotecas de autómatas.",
     ["Clase AFN: δ como diccionario {(estado, símbolo): conjunto}; simulación con traza de conjuntos.",
      "Clase AFD: δ como diccionario {(estado, símbolo): estado}; simulación con traza.",
      "subconjuntos(afn): devuelve el AFD y la lista de pasos para imprimir el procedimiento en la CLI.",
      "Traducción de eventos (ok/lento/timeout → r/l/t).",
      "Prueba exhaustiva: AFN y AFD coinciden en todas las cadenas de longitud 0 a 8 (9 841 cadenas)."],
     "02_Codigo/automatas/afn.py, afd.py, conversion.py y tests/test_afn_afd.py — versión 0.2.",
     "La tabla generada por el programa es idéntica a la construida a mano en A13."),
    ("A15", "Máquina de estados e integración con el grafo", "Axel", "Hiram", D(23, 11), D(25, 11),
     "Extensión del Proyecto 4",
     "Determinar el estado de cada dispositivo y reflejarlo en los análisis del grafo.",
     ["Implementar el AFD de 4 estados (tabla de la sección 4.7).",
      "Procesar monitoreo.txt: validar con R4, traducir a r/l/t y calcular el historial de estados.",
      "Ejecutar también el AFN/AFD de falla e informar si hubo falla en la ventana.",
      "Integración (con Hiram): los dispositivos en Falla se retiran del grafo; se recalculan componentes "
      "y rutas y se informa qué dispositivos quedaron incomunicados."],
     "02_Codigo/automatas/maquina_estados.py y el caso de prueba P14.",
     "Al fallar Server, la ruta Router1 → DB cambia de 6 ms a 7 ms."),
    ("A16", "Diseño de la gramática (Etapa 7)", "Hiram", "Axel", D(21, 11), D(23, 11), "Etapa 7",
     "Definir formalmente la gramática del formato .red y justificar que es libre de contexto.",
     ["Presentar G = (V, Σ, P, S) con las 11 producciones (sección 4.8.1).",
      "Justificar por qué no es regular (anidamiento, lema de bombeo) y por qué es LL(1).",
      "Escribir las 5 derivaciones por la izquierda paso a paso, indicando la producción aplicada.",
      "Dibujar el árbol de derivación de al menos una cadena (D4).",
      "Escribir las 5 cadenas que no pueden generarse y su motivo.",
      "Preparar respuestas a «¿qué pasa si eliminamos la producción n?»."],
     "Secciones 11 y 12 del documento final.",
     "Cada derivación puede verificarse producción por producción."),
    ("A17", "Parser descendente recursivo", "Hiram", "Axel", D(24, 11), D(26, 11), "Etapas 7 y 9",
     "Implementar a mano el reconocimiento sintáctico de la gramática.",
     ["Una función por no terminal: parse_red, parse_bloque, parse_elementos, parse_elemento, parse_zona, "
      "parse_dispositivo, parse_tipo, parse_enlace.",
      "Consumir los tokens de A11 y registrar la derivación aplicada para mostrarla en la CLI.",
      "Mensajes de error del tipo «Línea 7: se esperaba ';' y se encontró ENLACE».",
      "Validación semántica: dispositivos declarados antes de enlazarse, nombres e IP únicos, sin lazos.",
      "Construir el Grafo a partir del .red (la zona queda como atributo de cada dispositivo)."],
     "02_Codigo/gramatica/parser.py y tests/test_parser.py.",
     "Las 5 derivaciones del documento coinciden con las que imprime el programa."),
    ("A18", "Diseño del autómata de pila (Etapa 8)", "Hiram", "Axel", D(24, 11), D(26, 11), "Etapa 8",
     "Diseñar el autómata de pila que valida el anidamiento de bloques.",
     ["Definir M = (Q, Σ, Γ, δ, q0, Z0, F) y el significado de cada estado.",
      "Explicar qué reconoce, qué guarda la pila, cuándo se apila, cuándo se desapila y la condición de aceptación.",
      "Dibujar AP.png con transiciones «entrada, tope / reemplazo».",
      "Elaborar las trazas de 3 cadenas aceptadas y 3 rechazadas con el contenido de la pila en cada paso."],
     "03_Automatas/AP.png y sección 13 del documento.",
     "Cada paso de la traza muestra estado, entrada restante, transición y pila."),
    ("A19", "Implementación del autómata de pila", "Hiram", "Axel", D(26, 11), D(28, 11), "Etapas 8 y 9",
     "Programar el autómata de pila con traza para la CLI.",
     ["Función de transición como diccionario; pila implementada con list (append/pop).",
      "reconocer(tokens) → aceptada o rechazada, con la traza completa.",
      "Mostrar el nombre de la zona junto al símbolo de pila (Z[datacenter]).",
      "Ante un rechazo, indicar la zona sin cerrar o la llave sobrante y su línea.",
      "Ejecutarlo como validación estructural antes del parser."],
     "02_Codigo/gramatica/automata_pila.py y tests/test_pila.py — versión 0.3.",
     "Las 6 trazas del documento se reproducen exactamente."),
    ("A20", "Aplicación CLI e integración (Etapa 9)", "Hiram", "Axel", D(27, 11), D(30, 11), "Etapa 9",
     "Unir todos los módulos en una aplicación funcional y robusta.",
     ["Menú principal con las opciones 0–8 (sección 4.10.3) y validación de la opción elegida.",
      "Entrada por archivo y por teclado; argumentos opcionales: python main.py --red datos/red_ejemplo.txt.",
      "Manejo de errores con try/except (archivo inexistente, codificación, valores inválidos) y mensajes "
      "en lenguaje natural, sin tracebacks.",
      "Laboratorio teórico: probar cualquier cadena en AFN, AFD y AP, con traza.",
      "Exportar el reporte .txt."],
     "02_Codigo/main.py integrado.",
     "Se cumplen los 7 puntos de «El programa deberá» de la Etapa 9."),
    ("A21", "Visualización y figuras", "Axel", "Hiram", D(27, 11), D(30, 11), "Etapas 2, 5, 6 y 8",
     "Generar desde el programa todas las figuras del proyecto y explicar cómo se obtienen.",
     ["Grafo.png resaltando la ruta más corta, los puntos críticos y los nodos en falla.",
      "AFN.png, AFD.png, AP.png y maquina_estados.png con matplotlib.",
      "Árbol de texto en consola.",
      "Redactar para cada diagrama cómo se obtuvo (requisito: no presentar diagramas sin explicar)."],
     "03_Automatas/*.png, 04_Grafos/Grafo.png y 02_Codigo/reportes/visualizacion.py.",
     "Todas las figuras se regeneran ejecutando el programa."),
    ("A22", "Revisión cruzada de conocimiento", "Ambos", "—", D(1, 12), D(1, 12), "Secciones 14 y 19",
     "Garantizar que ambos dominan el proyecto completo.",
     ["Hiram explica a Axel: grafo, algoritmos, gramática, parser y autómata de pila.",
      "Axel explica a Hiram: lenguaje, regex, AFN, conversión, AFD y máquina de estados.",
      "Cada uno resuelve a mano un ejercicio de la parte del otro: Dijkstra, una conversión, una "
      "derivación y una traza de pila.",
      "Registrar las dudas en la bitácora y resolverlas antes del 3 de diciembre."],
     "Registro en la bitácora.",
     "Ambos responden correctamente el banco de preguntas de la sección 10."),
    ("A23", "Diseño de casos de prueba (Etapa 10)", "Axel", "Hiram", D(25, 11), D(27, 11), "Etapa 10",
     "Diseñar las pruebas antes de ejecutarlas.",
     ["Completar los 22 casos (sección 4.11) con su categoría y resultado esperado.",
      "Preparar los archivos de datos de cada caso en 05_Pruebas/datos/.",
      "Verificar que se cubren las 5 categorías: válidas, inválidas, normales, límite e inesperadas."],
     "05_Pruebas/casos_prueba.xlsx.",
     "Al menos 15 casos y las 5 categorías cubiertas."),
    ("A24", "Ejecución de pruebas", "Ambos", "—", D(1, 12), D(3, 12), "Etapa 10",
     "Ejecutar las pruebas y documentar los resultados obtenidos.",
     ["Ejecutar pytest completo y guardar la salida.",
      "Ejecutar manualmente los 22 casos en la CLI y llenar «Resultado obtenido» y «Estado».",
      "Tomar capturas de pantalla como evidencia (07_Evidencias/capturas/)."],
     "Tabla de pruebas completa y evidencias.",
     "El 100 % de los casos ejecutados y documentados."),
    ("A25", "Corrección de errores y registro de problemas", "Ambos", "—", D(2, 12), D(3, 12),
     "Etapa 10 y sección 17 del documento",
     "Corregir los fallos detectados y documentar qué salió mal y cómo se resolvió.",
     ["Para cada caso con estado «Error»: causa, corrección y nueva prueba.",
      "Si no se corrige a tiempo, documentarlo como limitación.",
      "Redactar la sección 17 a partir de los problemas reales registrados en la bitácora."],
     "Sección 17 del documento final.",
     "Ningún error queda sin explicación."),
    ("A26", "README.md", "Hiram", "Axel", D(3, 12), D(3, 12), "Sección 11",
     "Documentar cómo instalar, ejecutar y usar el programa.",
     ["Incluir: nombre del proyecto, integrantes, descripción, requisitos, lenguaje, instrucciones para "
      "ejecutar, estructura del proyecto y ejemplos de uso.",
      "Probar las instrucciones en una carpeta limpia."],
     "02_Codigo/README.md.",
     "Contiene los 8 elementos y las instrucciones funcionan tal como están escritas."),
    ("A27", "Documento final (Proyecto_Final.pdf)", "Ambos", "—", D(1, 12), D(5, 12), "Sección 16",
     "Integrar todo en el reporte con la estructura exacta del documento del proyecto.",
     ["Seguir la estructura: portada y secciones 1 a 20 (reparto en la sección 7.2).",
      "Insertar figuras, tablas, procedimientos y resultados reales de las pruebas.",
      "Cada integrante escribe su propia conclusión (sección 18).",
      "Revisión cruzada de ortografía y de coherencia entre el documento y el código.",
      "Exportar a PDF."],
     "01_Documentacion/Proyecto_Final.pdf — versión 1.0.",
     "Las 20 secciones presentes; todo lo que dice el documento se puede demostrar en el programa."),
    ("A28", "Presentación", "Axel", "Hiram", D(4, 12), D(6, 12), "Sección 18",
     "Preparar la presentación con los 13 puntos requeridos.",
     ["Unas 18 diapositivas: problema, solución, grafo, lenguaje, regex, AFN, conversión, gramática, "
      "LLC/AP, implementación, pruebas, resultados y conclusiones.",
      "Repartir la exposición de modo que cada integrante presente también partes que no lideró.",
      "Preparar el guion de la demostración en vivo."],
     "06_Presentacion/Presentacion.pptx.",
     "Los 13 puntos incluidos; duración ensayada."),
    ("A29", "Ensayo de demostración y defensa", "Ambos", "—", D(6, 12), D(7, 12), "Secciones 18 y 19",
     "Llegar preparados a la demostración con entradas no preparadas y a la defensa individual.",
     ["Ensayo cronometrado de la presentación completa.",
      "Simulacro de entrada no preparada: cada integrante crea una topología y un .red con errores para el otro.",
      "Practicar el banco de preguntas de la sección 10 (estado de aceptación, procesar cadena en el AFD, "
      "eliminar una producción, contenido de la pila).",
      "Lista de verificación: computadora cargada, Python y dependencias, datos, respaldo en GitHub y USB."],
     "Registro del ensayo en la bitácora.",
     "Demostración sin fallas con entradas nuevas; ambos responden las preguntas."),
    ("A30", "Empaquetado y entrega", "Hiram", "Axel", D(7, 12), D(7, 12), "Sección 17",
     "Entregar un único ZIP completo y verificado.",
     ["Armar Equipo_XX_Proyecto.zip con la estructura de la sección 7.1.",
      "Descomprimirlo en otra carpeta y ejecutar el programa y las pruebas desde cero.",
      "Revisar la matriz de trazabilidad punto por punto."],
     "Equipo_XX_Proyecto.zip.",
     "Todos los elementos solicitados se encuentran fácilmente y el programa se ejecuta."),
]


def seccion_cronograma():
    s = [H1("5. Cronograma")]
    s.append(P("El proyecto se organiza en cinco fases a lo largo de cuatro semanas. Las actividades de "
               "Hiram y de Axel corren en paralelo y se sincronizan en cada hito. La figura muestra el "
               "diagrama de Gantt; el detalle de cada actividad está en la sección 6."))
    gantt = [(a[0], a[1] if len(a[1]) <= 44 else a[1][:42] + "…", a[2], a[4], a[5]) for a in ACTIVIDADES]
    dg.dibujar_gantt(gantt)
    s.append(figura("gantt.png", 16.2, "Figura 5. Diagrama de Gantt (azul: Hiram, naranja: Axel, verde: ambos)."))
    s.append(H2("5.1 Fases y semanas"))
    s.append(tabla([
        ["Fase", "Fechas", "Actividades", "Resultado de la fase"],
        ["0 · Arranque", "11–12 nov", "A01–A03", "Plan, matriz de requisitos, repositorio y bitácora."],
        ["1 · Problema y grafos", "13–20 nov", "A04–A08 (Hiram) · A09–A10 (Axel)",
         "Etapas 1 y 2; programa v0.1 con grafo y análisis."],
        ["2 · Lenguajes y autómatas", "18–25 nov", "A11–A15 (Axel) · A16 (Hiram)",
         "Etapas 3–6; léxico, AFN, AFD y máquina de estados (v0.2)."],
        ["3 · Gramática, pila e integración", "24 nov–1 dic", "A17–A21, A23",
         "Etapas 7–9; CLI integrada (v0.3); casos de prueba diseñados."],
        ["4 · Pruebas, documento y presentación", "1–7 dic", "A22, A24–A30",
         "Etapa 10, Proyecto_Final.pdf, presentación, ZIP; v1.0."],
        ["Entrega", "8 dic", "—", "Presentación, demostración y defensa."],
    ], [4.3, 2.4, 4.4, 5.6]))
    s.append(H2("5.2 Calendario semanal"))
    semanas = [
        ("Semana 1 · 11–17 nov",
         "A01, A02, A04, A05, A06, A07 (inicio de A08)",
         "A01, A03, A09, A10 (inicio)"),
        ("Semana 2 · 18–24 nov",
         "A08, A16; inicio de A17 y A18",
         "A10, A11, A12, A13, A14; inicio de A15"),
        ("Semana 3 · 25 nov–1 dic",
         "A17, A18, A19, A20; A22",
         "A15, A21, A23; A22"),
        ("Semana 4 · 2–8 dic",
         "A24, A25, A26, A27, A29, A30",
         "A24, A25, A27, A28, A29"),
    ]
    s.append(tabla([["Semana", "Hiram", "Axel"]] + [list(x) for x in semanas], [4.5, 6.1, 6.1]))
    s.append(H2("5.3 Hitos y versiones del programa"))
    s.append(tabla([
        ["Hito", "Fecha", "Versión", "Criterio de cumplimiento"],
        ["H1", "17/11", "v0.1", "Grafo cargado desde archivo; V, E, lista, matriz y árbol correctos."],
        ["H2", "24/11", "v0.2", "Léxico con R1–R4; AFN, AFD y conversión con trazas; análisis de grafo completos."],
        ["H3", "01/12", "v0.3", "Parser, autómata de pila y CLI integrados; revisión cruzada realizada."],
        ["H4", "05/12", "v1.0", "22 casos ejecutados, errores corregidos, documento final terminado."],
        ["H5", "07/12", "Entrega", "ZIP verificado en una carpeta limpia; ensayo completo."],
    ], [1.4, 1.8, 2.0, 11.5], alinear_centro=(0, 1, 2)))
    return s


def tarjeta_actividad(a):
    aid, titulo, resp, apoyo, ini, fin, etapa, obj, pasos, entregable, criterio = a
    color = {"Hiram": AZUL, "Axel": NARANJA, "Ambos": VERDE}[resp]
    claro = {"Hiram": AZUL_CLARO, "Axel": NARANJA_CLARO, "Ambos": VERDE_CLARO}[resp]
    encabezado = Table([[Paragraph(f"<b>{aid}</b>", ST["cellb"]),
                         Paragraph(f"<b>{titulo}</b>", ST["cellb"])]],
                       colWidths=[1.4 * cm, 15.3 * cm])
    encabezado.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color),
                                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    meta = Table([[
        Paragraph(f"<b>Responsable:</b> {resp}", ST["cell"]),
        Paragraph(f"<b>Apoyo / revisión:</b> {apoyo}", ST["cell"]),
        Paragraph(f"<b>Fechas:</b> {ini:%d/%m} – {fin:%d/%m/%Y}", ST["cell"]),
        Paragraph(f"<b>Requisito:</b> {etapa}", ST["cell"]),
    ]], colWidths=[3.5 * cm, 4.0 * cm, 4.2 * cm, 5.0 * cm])
    meta.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), claro),
                              ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    cuerpo = [encabezado, meta, Spacer(1, 3),
              P(f"<b>Objetivo.</b> {obj}"),
              P("<b>Descripción de las tareas:</b>")]
    cuerpo += numerados(pasos)
    cuerpo += [Spacer(1, 2), P(f"<b>Entregable:</b> {entregable}"),
               P(f"<b>Criterio de terminado:</b> {criterio}"), Spacer(1, 8)]
    return KeepTogether(cuerpo)


def seccion_actividades():
    s = [H1("6. Actividades detalladas")]
    s.append(P("Cada actividad indica su responsable, quién la revisa, sus fechas, el requisito del "
               "documento del proyecto que cubre, las tareas concretas, el entregable y el criterio con el "
               "que se considera terminada. El color del encabezado indica el responsable."))
    fases = {"A01": "Fase 0 · Arranque", "A04": "Fase 1 · Problema y grafos",
             "A09": "Fase 1–2 · Lenguaje, expresiones regulares y autómatas finitos",
             "A16": "Fase 2–3 · Gramática, autómata de pila e integración",
             "A22": "Fase 4 · Pruebas, documentación, presentación y entrega"}
    for a in ACTIVIDADES:
        if a[0] in fases:
            s.append(CondPageBreak(6 * cm))
            s.append(H2(fases[a[0]]))
        s.append(tarjeta_actividad(a))
    return s


def seccion_entregables():
    s = [H1("7. Entregables")]
    s.append(H2("7.1 Estructura del archivo ZIP"))
    s.append(code(
        "Equipo_XX_Proyecto.zip\n"
        "├── 01_Documentacion\n"
        "│   ├── Proyecto_Final.pdf            ← A27\n"
        "│   └── Plan_de_Trabajo_Proyecto4.pdf ← este documento\n"
        "├── 02_Codigo\n"
        "│   ├── main.py, red/, lenguajes/, automatas/, gramatica/, reportes/\n"
        "│   ├── datos/, tests/, requirements.txt\n"
        "│   └── README.md                     ← A26\n"
        "├── 03_Automatas\n"
        "│   ├── AFN.png                       ← A12 / A21\n"
        "│   ├── AFD.png                       ← A13 / A21\n"
        "│   ├── AP.png                        ← A18 / A21\n"
        "│   └── Maquina_estados.png           ← A15 / A21\n"
        "├── 04_Grafos\n"
        "│   └── Grafo.png                     ← A06 / A21\n"
        "├── 05_Pruebas\n"
        "│   ├── casos_prueba.xlsx             ← A23 / A24\n"
        "│   ├── datos/                        (archivos de entrada de cada caso)\n"
        "│   └── salida_pytest.txt             ← A24\n"
        "├── 06_Presentacion\n"
        "│   └── Presentacion.pptx             ← A28\n"
        "└── 07_Evidencias\n"
        "    ├── Bitacora.xlsx                 ← A03 (continua)\n"
        "    └── capturas/                     ← A24"))
    s.append(H2("7.2 Documento final: secciones y responsables"))
    s.append(tabla([
        ["Sección del reporte", "Contenido", "Responsable", "Fuente"],
        ["Portada", "Universidad, carrera, materia, proyecto, integrantes, profesor, fecha", "Hiram", "Datos del equipo"],
        ["1. Introducción", "Contexto y organización del documento", "Hiram", "A04"],
        ["2. Descripción del problema", "Problema, contexto de TI, usuarios", "Hiram", "A04"],
        ["3. Objetivo general", "Objetivo del prototipo", "Hiram", "A04"],
        ["4. Alcance y restricciones", "Incluye / no incluye, limitaciones", "Hiram", "A04"],
        ["5. Descripción de la solución", "Arquitectura y flujo general", "Hiram", "A04, A20"],
        ["6. Modelado mediante grafos", "Vértices, aristas, representación, operaciones, resultados", "Hiram", "A05–A08"],
        ["7. Lenguajes formales", "Alfabeto, lenguaje, cadenas válidas e inválidas", "Axel", "A09"],
        ["8. Expresiones regulares", "R1–R4 con sus 7 elementos", "Axel", "A10, A11"],
        ["9. AFN", "Definición, diagrama, tabla, pruebas", "Axel", "A12"],
        ["10. Conversión AFN → AFD", "Procedimiento, tabla, diagrama, pruebas", "Axel", "A13, A14"],
        ["11. Gramática", "Definición formal, producciones, derivaciones", "Hiram", "A16"],
        ["12. Lenguaje libre de contexto", "Justificación de no regularidad, validación semántica", "Hiram", "A16, A17"],
        ["13. Autómata de pila", "Definición, estados, transiciones, pila, ejemplos", "Hiram", "A18, A19"],
        ["14. Implementación", "Arquitectura, componentes, funcionamiento", "Hiram", "A20"],
        ["15. Casos de prueba", "Tabla de 22 casos", "Axel", "A23, A24"],
        ["16. Resultados", "Salidas reales del programa y capturas", "Axel", "A24"],
        ["17. Problemas encontrados y soluciones", "Qué salió mal y cómo se resolvió", "Ambos", "A25, bitácora"],
        ["18. Conclusiones", "Una conclusión individual por integrante", "Cada uno", "—"],
        ["19. Referencias", "Bibliografía del curso y documentación técnica", "Axel", "—"],
        ["20. Anexos", "Responsabilidades, bitácora, código relevante", "Ambos", "A03"],
    ], [4.4, 6.2, 2.8, 3.3]))
    s.append(H2("7.3 Presentación (13 puntos requeridos)"))
    s.append(tabla([
        ["#", "Punto", "Expone", "Contenido clave"],
        ["1", "Problema", "Hiram", "Escenario de la red del laboratorio y preguntas que se responden."],
        ["2", "Solución propuesta", "Axel", "Arquitectura en capas y relación teoría–módulo."],
        ["3", "Grafo", "Axel", "Tipo, representaciones y resultados de los análisis."],
        ["4", "Lenguaje", "Hiram", "Σ, L_enlaces y ejemplos."],
        ["5", "Regex", "Hiram", "R1–R4 explicadas por partes."],
        ["6", "AFN", "Axel", "Definición, no determinismo y recorridos."],
        ["7", "Conversión AFN → AFD", "Axel", "Tabla de subconjuntos y equivalencia."],
        ["8", "Gramática", "Axel", "Producciones y una derivación."],
        ["9", "LLC / autómata de pila", "Hiram", "Por qué no es regular y traza de la pila."],
        ["10", "Implementación", "Hiram", "Estructura del código y demostración en vivo."],
        ["11", "Pruebas", "Axel", "Tabla de casos y pruebas automáticas."],
        ["12", "Resultados", "Ambos", "Qué funciona, limitaciones."],
        ["13", "Conclusiones", "Ambos", "Conclusión de cada integrante."],
    ], [0.8, 4.0, 1.9, 10.0], alinear_centro=(0,)))
    s.append(P("Cada integrante expone partes que <b>no</b> lideró, como evidencia de que conoce el proyecto "
               "completo."))
    s.append(H2("7.4 Matriz de trazabilidad de requisitos"))
    filas = [["Requisito del documento", "Mínimo exigido", "Actividad", "Evidencia / archivo"]]
    filas += [
        ["Etapa 1 · Definición del problema", "7 preguntas + 7 elementos", "A04", "Proyecto_Final §1–5"],
        ["Etapa 2.1 · Elementos del grafo", "V, E, tipo, justificación", "A05", "§6"],
        ["Etapa 2.2 · Representación", "Dibujo, V, E, lista o matriz", "A06, A07", "Grafo.png, §6"],
        ["Etapa 2.3 · Análisis", "≥ 2 análisis útiles", "A08 (8 análisis)", "algoritmos.py, §6"],
        ["Etapa 3 · Lenguaje", "Σ, L, 10 válidas, 10 inválidas con motivo", "A09", "§7"],
        ["Etapa 4 · Regex", "≥ 3 regex con 7 elementos cada una", "A10, A11 (4 regex)", "lexico.py, §8"],
        ["Etapa 5 · AFN", "Quíntupla, diagrama, tabla, 5+5 cadenas con recorrido", "A12, A14", "AFN.png, §9"],
        ["Etapa 6 · AFN → AFD", "8 elementos + comprobación con cadenas", "A13, A14", "AFD.png, §10"],
        ["Etapa 7 · Gramática", "G = (V, Σ, P, S), 5 derivaciones, 5 no generables", "A16, A17", "parser.py, §11–12"],
        ["Etapa 8 · Autómata de pila", "Explicación, transiciones, pila, 3+3 ejemplos", "A18, A19", "AP.png, §13"],
        ["Etapa 9 · Implementación", "7 puntos de «El programa deberá»", "A20", "main.py, §14"],
        ["Etapa 10 · Casos de prueba", "≥ 15 casos, 5 categorías, tabla", "A23–A25 (22 casos)", "casos_prueba.xlsx, §15"],
        ["11 · Código fuente", "Nombres, funciones, comentarios, validación, errores", "A07–A21", "02_Codigo/"],
        ["11 · README.md", "8 elementos", "A26", "02_Codigo/README.md"],
        ["12 · Restricciones", "Sin bibliotecas de autómatas ni parsers", "Todas", "Sección 3.1 de este plan"],
        ["13 · Uso de IA", "Comprender y defender todo", "A22, A29", "Banco de preguntas (§10 del plan)"],
        ["14 · Organización del equipo", "Responsabilidades documentadas", "A01", "Sección 2 de este plan; anexo"],
        ["15 · Bitácora", "Fecha, actividad, responsable, resultado", "A03", "Bitacora.xlsx"],
        ["16 · Documento final", "Portada + 20 secciones", "A27", "Proyecto_Final.pdf"],
        ["17 · Archivos a entregar", "ZIP con 7 carpetas", "A30", "Equipo_XX_Proyecto.zip"],
        ["18 · Presentación y demostración", "13 puntos, demo en vivo con entrada no preparada", "A28, A29", "Presentacion.pptx"],
        ["19 · Defensa individual", "Preguntas a cada integrante", "A22, A29", "Banco de preguntas"],
    ]
    s.append(tabla(filas, [4.7, 5.0, 2.8, 4.2]))
    return s


def seccion_rubrica():
    s = [H1("8. Rúbrica y estrategia para cada criterio")]
    s.append(tabla([
        ["Criterio", "Pts.", "Cómo se asegura", "Líder"],
        ["Definición y análisis del problema", "5", "7 preguntas y 7 elementos con escenario concreto.", "Hiram"],
        ["Grafos y operaciones", "10", "Tipo justificado, 4 representaciones y 8 análisis con utilidad real, "
         "resultados verificados a mano.", "Hiram"],
        ["Definición formal del lenguaje", "10", "Σ con significado, L por comprensión, 10/10 cadenas con motivo.", "Axel"],
        ["Expresiones regulares", "10", "4 regex construidas desde la definición formal, probadas y usadas en el código.", "Axel"],
        ["AFN", "10", "Quíntupla, diagrama, tabla, no determinismo explicado, 5/5 recorridos.", "Axel"],
        ["Conversión AFN → AFD", "10", "Procedimiento paso a paso, tabla y diagrama, equivalencia exhaustiva, "
         "minimización como extra.", "Axel"],
        ["Gramática y LLC", "10", "G formal, justificación de no regularidad, LL(1), 5 derivaciones, 5 no generables.", "Hiram"],
        ["Autómata de pila", "10", "AP completo (no una justificación de su ausencia), trazas de pila 3/3.", "Hiram"],
        ["Implementación funcional", "10", "Toda la teoría implementada a mano, CLI robusta, mensajes claros.", "Hiram"],
        ["Casos de prueba", "5", "22 casos en 5 categorías + pytest.", "Axel"],
        ["Documentación y organización", "5", "20 secciones, README, bitácora, ZIP ordenado.", "Ambos"],
        ["Presentación, demostración y defensa", "5", "Ensayos, simulacro con entradas no preparadas, banco de preguntas.", "Ambos"],
        ["<b>Total</b>", "<b>100</b>", "", ""],
    ], [4.8, 1.1, 9.0, 1.8], alinear_centro=(1,)))
    return s


def seccion_riesgos():
    s = [H1("9. Riesgos y plan de mitigación")]
    s.append(tabla([
        ["Riesgo", "Prob.", "Impacto", "Mitigación"],
        ["La fecha oficial de entrega es anterior a la planeada.", "Media", "Alto",
         "Cronograma relativo; se prioriza por puntos de rúbrica; la semana 4 tiene holgura."],
        ["El profesor da una entrada no prevista y el programa falla.", "Media", "Alto",
         "Validación en todas las capas, manejo de excepciones, simulacro A29 con entradas creadas por el otro integrante."],
        ["Un integrante no domina la parte del otro.", "Media", "Alto",
         "Revisión cruzada en cada actividad, A22 y banco de preguntas."],
        ["Retraso en el léxico bloquea al parser.", "Baja", "Medio",
         "Interfaces acordadas en A02; el parser se desarrolla primero con tokens de prueba."],
        ["Diferencias entre el documento y el código.", "Media", "Medio",
         "Las tablas (AFD, trazas, derivaciones) se generan desde el programa y se comparan con las hechas a mano."],
        ["Pérdida de trabajo o conflictos en Git.", "Baja", "Alto",
         "Push diario, ramas por integrante, respaldo del ZIP en USB."],
        ["Uso de bibliotecas no permitidas por descuido.", "Baja", "Alto",
         "Lista de la sección 3.1; revisión de los import antes de cada integración."],
        ["Problemas de instalación el día de la demostración.", "Baja", "Alto",
         "El núcleo no depende de bibliotecas externas; ensayo en la computadora que se usará."],
    ], [5.0, 1.4, 1.9, 8.4], alinear_centro=(1, 2)))
    return s


def seccion_defensa():
    s = [H1("10. Preparación para la demostración y la defensa")]
    s.append(P("El documento del proyecto indica que el profesor puede elegir cualquier expresión regular, "
               "transición, estado, producción, fragmento de código o algoritmo y pedir a cualquier integrante "
               "que lo explique. El siguiente banco de preguntas se practicará en A22 y A29; ambos integrantes "
               "deben poder responder todas."))
    s.append(tabla([
        ["Pregunta", "Idea clave de la respuesta"],
        ["¿Por qué el grafo es no dirigido y ponderado?", "Los enlaces son bidireccionales; la latencia permite "
         "calcular la ruta más rápida y no solo la de menos saltos."],
        ["¿Por qué Dijkstra y no BFS para la ruta más corta?", "BFS minimiza saltos; Dijkstra minimiza la suma de "
         "pesos. Funciona porque las latencias son positivas (la regex PESO lo garantiza)."],
        ["¿Qué es un punto de articulación y cómo se detecta?", "Un nodo cuya eliminación desconecta la red. Tarjan: "
         "u es articulación si tiene un hijo v con low[v] ≥ disc[u] (o si es raíz con ≥ 2 hijos)."],
        ["Explica <font name='DVM'>[1-9][0-9]{0,3}</font>.", "Primer dígito 1–9 (sin cero inicial), luego de 0 a 3 dígitos: "
         "1 a 9999."],
        ["¿Por qué 256.1.1.1 no es una IP válida en R3?", "Ninguna alternativa del octeto produce 256: 25[0-5] llega "
         "solo a 255."],
        ["¿Por qué q2 es estado de aceptación?", "Llegar a q2 significa haber leído dos t consecutivas: la cadena ya "
         "pertenece a L_falla sin importar lo que siga."],
        ["¿Dónde está el no determinismo del AFN?", "δ(q0, t) = {q0, q1}: con un timeout hay dos opciones."],
        ["Procesa «rtlt» con el AFD.", "A —r→ A —t→ B —l→ A —t→ B; B no es final → rechazada."],
        ["¿Por qué D = {q0, q2} es final?", "Porque contiene q2, que es final en el AFN."],
        ["¿Qué pasa si eliminamos la producción 4 (lista → ε)?", f"{nt('elementos')} nunca desaparece; ninguna "
         "derivación termina y L(G) = ∅."],
        ["¿Qué pasa si eliminamos la producción 5?", "Ya no hay zonas: desaparece el anidamiento y el lenguaje "
         "resultante sería regular."],
        ["¿Qué contiene la pila después de «RED a { ZONA b {»?", "Z R Z0 (tope a la izquierda)."],
        ["¿Por qué una regex no basta para el archivo .red?", "Haría falta contar llaves abiertas sin límite; los "
         "autómatas finitos tienen memoria finita."],
        ["¿Por qué «enlace a dispositivo no declarado» no se valida en la gramática?", "Depende del contexto "
         "(lo declarado antes); una GLC no lo puede expresar, por eso es una validación semántica."],
        ["¿Qué complejidad tiene BFS?", "O(V + E): cada vértice y cada arista se procesan una vez."],
    ], [6.5, 10.2]))
    s.append(H2("10.1 Lista de verificación para el día de la presentación"))
    s += bullets([
        "Computadora con Python 3.14, dependencias instaladas y el repositorio actualizado.",
        "Datos de demostración en 02_Codigo/datos/ y archivos con errores listos para mostrar el rechazo.",
        "Respaldo del ZIP en USB y en GitHub.",
        "Presentación abierta y terminal con tamaño de letra legible.",
        "Ambos integrantes con el banco de preguntas repasado.",
    ])
    return s


def seccion_bitacora():
    s = [H1("11. Bitácora inicial")]
    s.append(P("Formato que se utilizará en 07_Evidencias/Bitacora.xlsx, con los primeros registros:"))
    s.append(tabla([
        ["Fecha", "Actividad", "Responsable(s)", "Resultado", "Problema / solución"],
        ["10/11/2026", "Análisis del documento del proyecto", "Hiram y Axel",
         "Requisitos identificados por etapa y criterio de rúbrica.", "—"],
        ["10/11/2026", "Propuesta técnica y plan de trabajo", "Hiram y Axel",
         "Este documento: diseño, cronograma, actividades y entregables.",
         "Se verificaron las regex y la equivalencia AFN/AFD antes de fijar el diseño."],
        ["11/11/2026", "A01 · Matriz de requisitos", "Hiram y Axel", "", ""],
        ["11–12/11/2026", "A02 · Repositorio y entorno", "Hiram", "", ""],
        ["12/11/2026", "A03 · Bitácora", "Axel", "", ""],
    ], [2.3, 4.0, 2.6, 4.4, 3.4]))
    return s


def construir():
    SALIDA_PDF.parent.mkdir(parents=True, exist_ok=True)
    dg.dibujar_grafo()
    dg.dibujar_afn()
    dg.dibujar_afd()
    dg.dibujar_maquina_estados()
    historia = []
    historia += portada()
    historia += indice()
    historia += seccion_resumen()
    historia.append(CondPageBreak(9 * cm))
    historia += seccion_equipo()
    historia.append(CondPageBreak(9 * cm))
    historia += seccion_stack()
    historia.append(CondPageBreak(9 * cm))
    historia += propuesta_problema()
    historia.append(CondPageBreak(9 * cm))
    historia += propuesta_grafo()
    historia.append(CondPageBreak(9 * cm))
    historia += propuesta_lenguaje()
    historia.append(CondPageBreak(9 * cm))
    historia += propuesta_regex()
    historia.append(CondPageBreak(9 * cm))
    historia += propuesta_afn_afd()
    historia.append(CondPageBreak(9 * cm))
    historia += propuesta_gramatica()
    historia.append(CondPageBreak(9 * cm))
    historia += propuesta_pila()
    historia.append(CondPageBreak(9 * cm))
    historia += propuesta_implementacion()
    historia.append(CondPageBreak(9 * cm))
    historia += propuesta_pruebas()
    historia.append(CondPageBreak(9 * cm))
    historia += seccion_cronograma()
    historia.append(CondPageBreak(9 * cm))
    historia += seccion_actividades()
    historia.append(CondPageBreak(9 * cm))
    historia += seccion_entregables()
    historia.append(CondPageBreak(9 * cm))
    historia += seccion_rubrica()
    historia += seccion_riesgos()
    historia.append(CondPageBreak(9 * cm))
    historia += seccion_defensa()
    historia += seccion_bitacora()
    doc = Plantilla(str(SALIDA_PDF))
    doc.multiBuild(historia)
    print("PDF generado:", SALIDA_PDF)


if __name__ == "__main__":
    construir()
