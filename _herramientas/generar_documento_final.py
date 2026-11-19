"""
Genera el documento final del Proyecto 4 (Network Graph Analyzer) en Word:

    01_Documentacion/Proyecto_Final.docx

Uso:
    python diagramas_final.py           # figuras en 03_Automatas/ y 04_Grafos/
    python generar_documento_final.py   # documento (también regenera las figuras)

El documento sigue la estructura de la sección 16 del enunciado. Todo lo que
depende del código o de datos que el equipo aún no tiene (portada, capturas,
resultados obtenidos, problemas de desarrollo, conclusiones) queda marcado con
[PENDIENTE: ...] resaltado en amarillo. Buscar "PENDIENTE" en Word para
encontrar cada hueco.

Las tablas del AFN, del AFD, de las trazas del autómata de pila y de los casos
de prueba se toman de generar_plan_trabajo.py (misma fuente que el plan), y
los ejemplos de las expresiones regulares y los resultados del grafo se
verifican con assert antes de escribir el documento.
"""
import heapq
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

import diagramas_final as figs
import generar_plan_trabajo as plan

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "01_Documentacion" / "Proyecto_Final.docx"

AZUL = "1F4E79"
NARANJA = "C55A11"
VERDE = "548235"
GRIS_CLARO = "F2F2F2"
AZUL_CLARO = "DEEBF7"

INTEGRANTES = ["Hiram Alejandro Almendarez Hernández", "Axel Rafael Reyes Lara"]


# ======================================================================
# Utilidades de formato
# ======================================================================
TOKEN = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\[\[.+?\]\]|_\{[^}]+\}|\^\{[^}]+\})")


def runs(par, texto, tam=None, color=None, negrita=False):
    """Agrega texto a un párrafo interpretando un marcado mínimo:
    **negrita**, `mono`, [[PENDIENTE: ...]] (resaltado), _{sub}, ^{sup}."""
    for parte in TOKEN.split(texto):
        if not parte:
            continue
        if parte.startswith("**"):
            r = par.add_run(parte[2:-2])
            r.bold = True
        elif parte.startswith("`"):
            r = par.add_run(parte[1:-1])
            r.font.name = "Consolas"
        elif parte.startswith("[["):
            r = par.add_run("[" + parte[2:-2] + "]")
            r.bold = True
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW
        elif parte.startswith("_{"):
            r = par.add_run(parte[2:-1])
            r.font.subscript = True
        elif parte.startswith("^{"):
            r = par.add_run(parte[2:-1])
            r.font.superscript = True
        else:
            r = par.add_run(parte)
        if negrita:
            r.bold = True
        if tam:
            r.font.size = Pt(tam)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
    return par


def P(doc, texto, estilo=None, alinear=None):
    par = doc.add_paragraph(style=estilo)
    runs(par, texto)
    if alinear:
        par.alignment = alinear
    return par


class Salto:
    """Si True, el siguiente título de nivel 1 inicia en página nueva."""
    h1 = False


def H(doc, texto, nivel):
    h = doc.add_heading(texto, level=nivel)
    if nivel == 1 and Salto.h1:
        h.paragraph_format.page_break_before = True
    return h


def bullets(doc, items, estilo="List Bullet"):
    for i in items:
        P(doc, i, estilo)


def pendiente(doc, texto):
    """Párrafo resaltado para completar después."""
    return P(doc, f"[[PENDIENTE: {texto}]]")


def code(doc, texto, tam=8.5):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(4)
    par.paragraph_format.space_after = Pt(8)
    par.paragraph_format.left_indent = Cm(0.3)
    par.alignment = WD_ALIGN_PARAGRAPH.LEFT
    sombrear_parrafo(par, GRIS_CLARO)
    lineas = texto.split("\n")
    for i, linea in enumerate(lineas):
        r = par.add_run(linea)
        r.font.name = "Consolas"
        r.font.size = Pt(tam)
        if i < len(lineas) - 1:
            r.add_break()
    return par


def nota(doc, texto):
    par = P(doc, texto)
    sombrear_parrafo(par, AZUL_CLARO)
    par.paragraph_format.left_indent = Cm(0.3)
    par.paragraph_format.right_indent = Cm(0.3)
    return par


def sombrear_parrafo(par, color):
    pPr = par._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    pPr.append(shd)


def sombrear_celda(celda, color):
    tcPr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


class Contador:
    figura = 0
    tabla = 0


def figura(doc, ruta, ancho_cm, pie):
    Contador.figura += 1
    doc.add_picture(str(ruta), width=Cm(ancho_cm))
    img = doc.paragraphs[-1]
    img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img.paragraph_format.keep_with_next = True
    cap = doc.add_paragraph(style="Caption")
    runs(cap, f"Figura {Contador.figura}. {pie}")
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER


def captura(doc, descripcion, alto_cm=5.0):
    """Recuadro vacío para pegar una captura de pantalla del programa."""
    Contador.figura += 1
    t = doc.add_table(rows=1, cols=1)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    celda = t.rows[0].cells[0]
    celda.width = Cm(15)
    tr = t.rows[0]._tr
    trPr = tr.get_or_add_trPr()
    alto = OxmlElement("w:trHeight")
    alto.set(qn("w:val"), str(int(alto_cm * 567)))
    trPr.append(alto)
    par = celda.paragraphs[0]
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.keep_with_next = True
    runs(par, f"[[PENDIENTE: pegar captura — {descripcion}]]", tam=9)
    cap = doc.add_paragraph(style="Caption")
    runs(cap, f"Figura {Contador.figura}. {descripcion}.")
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER


def tabla(doc, filas, anchos, encabezado=True, mono=(), centro=(), color=AZUL, zebra=True,
          pie=None, tam=8.5):
    """Tabla con encabezado coloreado. Las celdas aceptan el marcado de runs();
    las columnas en `mono` se escriben literalmente en Consolas."""
    if pie:  # el pie va arriba de la tabla y se mantiene con ella
        Contador.tabla += 1
        cap = doc.add_paragraph(style="Caption")
        runs(cap, f"Tabla {Contador.tabla}. {pie}")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_after = Pt(3)
        cap.paragraph_format.keep_with_next = True
    # Las tablas cortas no se parten entre páginas; en las largas solo el encabezado
    # se mantiene unido a la primera fila.
    filas_unidas = len(filas) - 1 if len(filas) <= 16 else (1 if encabezado else 0)
    t = doc.add_table(rows=len(filas), cols=len(filas[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, fila in enumerate(filas):
        row = t.rows[i]
        if encabezado and i == 0:
            trPr = row._tr.get_or_add_trPr()
            h = OxmlElement("w:tblHeader")
            h.set(qn("w:val"), "true")
            trPr.append(h)
        for j, texto in enumerate(fila):
            celda = row.cells[j]
            celda.width = Cm(anchos[j])
            lineas = str(texto).split("\n")
            for k, linea in enumerate(lineas):
                par = celda.paragraphs[0] if k == 0 else celda.add_paragraph()
                par.paragraph_format.space_after = Pt(0)
                par.paragraph_format.space_before = Pt(0)
                par.alignment = WD_ALIGN_PARAGRAPH.CENTER if j in centro else WD_ALIGN_PARAGRAPH.LEFT
                if encabezado and i == 0:
                    runs(par, linea, tam=tam, color="FFFFFF", negrita=True)
                elif j in mono:
                    r = par.add_run(linea)
                    r.font.name = "Consolas"
                    r.font.size = Pt(tam - 0.5)
                else:
                    runs(par, linea, tam=tam)
                if i < filas_unidas:
                    par.paragraph_format.keep_with_next = True
            if encabezado and i == 0:
                sombrear_celda(celda, color)
            elif zebra and i % 2 == 0:
                sombrear_celda(celda, GRIS_CLARO)
    espacio = doc.add_paragraph()
    espacio.paragraph_format.space_after = Pt(4)
    return t


def campo(par, instruccion, texto_previo=""):
    """Inserta un campo de Word (TOC, PAGE...)."""
    r = par.add_run()
    ini = OxmlElement("w:fldChar")
    ini.set(qn("w:fldCharType"), "begin")
    r._r.append(ini)
    r = par.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruccion
    r._r.append(instr)
    r = par.add_run()
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    r._r.append(sep)
    par.add_run(texto_previo)
    r = par.add_run()
    fin = OxmlElement("w:fldChar")
    fin.set(qn("w:fldCharType"), "end")
    r._r.append(fin)


def salto_pagina(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ======================================================================
# Modelos y verificaciones
# ======================================================================
NODOS = ["Router1", "Switch1", "Switch2", "PC1", "PC2", "Server", "DB", "Impresora1"]
ENLACES = [("Router1", "Switch1", 2), ("Router1", "Switch2", 3), ("Switch1", "PC1", 1),
           ("Switch1", "PC2", 1), ("Switch2", "Server", 1), ("PC2", "DB", 4), ("Server", "DB", 2)]
ADY = {n: {} for n in NODOS}
for _u, _v, _w in ENLACES:
    ADY[_u][_v] = _w
    ADY[_v][_u] = _w


def dijkstra_traza(origen):
    """Dijkstra con cola de prioridad; devuelve distancias, padres y traza por iteración."""
    dist = {n: float("inf") for n in NODOS}
    padre = {n: None for n in NODOS}
    dist[origen] = 0
    cola = [(0, origen)]
    visitados = set()
    traza = []
    while cola:
        d, u = heapq.heappop(cola)
        if u in visitados:
            continue
        visitados.add(u)
        cambios = []
        for v, w in sorted(ADY[u].items()):
            if v not in visitados and d + w < dist[v]:
                antes = "∞" if dist[v] == float("inf") else str(dist[v])
                dist[v] = d + w
                padre[v] = u
                heapq.heappush(cola, (dist[v], v))
                cambios.append(f"{v}: {antes} → {dist[v]}")
        traza.append((u, d, ", ".join(cambios) or "—"))
    return dist, padre, traza


DIST_R1, PADRE_R1, TRAZA_DIJKSTRA = dijkstra_traza("Router1")
assert DIST_R1["DB"] == 6 and PADRE_R1["DB"] == "Server"
assert {n: len(ADY[n]) for n in NODOS}["Switch1"] == 3 and not ADY["Impresora1"]
assert sum(len(a) for a in ADY.values()) == 2 * len(ENLACES)

ID = "[A-Za-z][A-Za-z0-9_-]{0,19}"
R1 = f"^{ID}$"
R2 = rf"^\s*({ID})\s*,\s*({ID})\s*(?:,\s*([1-9][0-9]{{0,3}}))?\s*$"
OCT = r"(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"
R3 = rf"^({OCT}\.){{3}}{OCT}$"
R4 = rf"^\s*({ID})\s*:\s*((?:ok|lento|timeout)(?:\s*,\s*(?:ok|lento|timeout))*)\s*$"

REGEX = [
    dict(
        clave="R1", nombre="Nombre de dispositivo",
        proposito="Reconocer identificadores válidos de dispositivos (vértices del grafo).",
        expr=R1,
        expl="`[A-Za-z]`: el primer símbolo es una letra. `[A-Za-z0-9_-]{0,19}`: de 0 a 19 "
             "símbolos más entre letras, dígitos, guion bajo y guion, de modo que la longitud total "
             "va de 1 a 20. `^` y `$` obligan a que coincida la cadena completa y no solo una parte. "
             "Corresponde directamente a la definición ID de la sección 7.2.",
        validos=["Router1", "PC_01", "sw-core"],
        invalidos=[("1Router", "inicia con dígito"), ("_pc", "inicia con guion bajo"),
                   ("Ser ver", "contiene un espacio"), ("A" * 21, "21 símbolos (máximo 20)")],
        lugar="`lenguajes/lexico.py → validar_nombre()`; lo reutilizan R2, R4 y el token id del parser."),
    dict(
        clave="R2", nombre="Línea de enlace",
        proposito="Validar cada línea del archivo de topología y extraer origen, destino y latencia.",
        expr=R2,
        expl="Dos grupos con la estructura de R1 separados por coma; `\\s*` permite espacios "
             "opcionales alrededor de los campos. `(?:,\\s*(…))?` hace opcional el tercer campo. "
             "`[1-9][0-9]{0,3}` es PESO: primer dígito distinto de cero y hasta tres dígitos más "
             "(1 a 9999). Los grupos 1, 2 y 3 capturan los datos con los que se construye la arista. "
             "Una línea con un solo ID (dispositivo sin enlaces) se valida con R1.",
        validos=["Router1,Switch1", "Router1, Switch1, 5", "PC1,Switch1,9999"],
        invalidos=[("PC1,Switch1,0", "latencia 0"), ("PC1,Switch1,10000", "más de 4 dígitos"),
                   ("PC1;Switch1", "separador ';'"), ("PC1,", "falta el destino"),
                   ("PC1,Switch1,-3", "signo negativo"), ("R1,S1,05", "cero a la izquierda")],
        lugar="`lenguajes/lexico.py → validar_linea_enlace()`, llamada por "
              "`red/grafo.py → cargar_desde_archivo()`."),
    dict(
        clave="R3", nombre="Dirección IPv4",
        proposito="Validar la IP de cada DISPOSITIVO del archivo de configuración .red (token ip).",
        expr=R3,
        expl="Cada octeto se separa en casos para limitarlo a 0–255: `25[0-5]` (250–255), "
             "`2[0-4][0-9]` (200–249), `1[0-9]{2}` (100–199) y `[1-9]?[0-9]` (0–99, sin ceros a la "
             "izquierda). `(octeto\\.){3}` exige tres octetos seguidos de punto y después un cuarto "
             "octeto. Mejora la expresión `([0-9]{1,3}\\.){3}[0-9]{1,3}` del enunciado, que aceptaría "
             "999.999.999.999.",
        validos=["192.168.1.10", "10.0.0.1", "255.255.255.255", "0.0.0.0"],
        invalidos=[("256.1.1.1", "octeto mayor que 255"), ("192.168.01.1", "cero a la izquierda"),
                   ("192.168.1", "solo tres octetos"), ("1.2.3.4.5", "cinco octetos")],
        lugar="`lenguajes/lexico.py → tokenizar_config()` (clasifica el lexema como token ip)."),
    dict(
        clave="R4", nombre="Línea de monitoreo",
        proposito="Validar las líneas del archivo de monitoreo y extraer la secuencia de eventos "
                  "de cada dispositivo.",
        expr=R4,
        expl="Un nombre (estructura de R1), dos puntos y una lista de uno o más eventos de "
             "{ok, lento, timeout} separados por comas. `(?:ok|lento|timeout)` es la unión de tres "
             "palabras y `(?:\\s*,\\s*(…))*` es la cerradura de Kleene que permite repetir eventos. "
             "El grupo 2 contiene la secuencia que se traduce a los símbolos r, l, t del AFN y del AFD.",
        validos=["Server: ok, ok, timeout, timeout", "DB:lento"],
        invalidos=[("PC1: ping", "evento desconocido"), ("PC1 ok", "faltan los dos puntos"),
                   ("PC1:", "lista de eventos vacía"), ("PC1: ok,,timeout", "evento vacío entre comas")],
        lugar="`lenguajes/lexico.py → validar_linea_monitoreo()`, llamada por "
              "`automatas/maquina_estados.py`."),
]
for _r in REGEX:
    for _c in _r["validos"]:
        assert re.fullmatch(_r["expr"], _c), (_r["clave"], _c)
    for _c, _ in _r["invalidos"]:
        assert not re.fullmatch(_r["expr"], _c), (_r["clave"], _c)


def en_lenguaje_enlaces(cadena):
    """Pertenencia a L_enlaces (R1 o R2) más la condición x ≠ y."""
    if re.fullmatch(R1, cadena):
        return True
    m = re.fullmatch(R2, cadena)
    return bool(m) and m.group(1) != m.group(2)


VALIDAS_L = ["Router1,Switch1", "Router1,Switch2,3", "Switch1, PC1, 1", "PC2,DB,4", "Server,DB,2",
             "Impresora1", "sw-core_01,fw-perimetral,15", "AP3,Switch2,9999", "A,B",
             "Firewall_Edge,Router1,120"]
INVALIDAS_L = [
    ("Router1;Switch1", "El separador ';' no pertenece a Σ; el separador definido es la coma."),
    ("Router1,", "Falta el identificador de destino después de la coma."),
    ("1Router,Switch1", "Un ID debe iniciar con letra; esta cadena inicia con dígito."),
    ("Router1,Switch1,0", "PESO no puede iniciar con 0: la latencia mínima es 1."),
    ("Router1,Switch1,10000", "PESO tiene como máximo 4 dígitos (≤ 9999)."),
    ("Router1,Switch1,2.5", "El punto no pertenece a Σ: la latencia es entera."),
    ("Router1,Switch1,3,7", "Tiene cuatro campos; el lenguaje admite como máximo tres."),
    ("Router 1,Switch1", "Un ID no puede contener espacios internos."),
    ("PC1,PC1", "Origen y destino iguales: no cumple la condición x ≠ y."),
    ("Nodo_de_distribucion_principal,PC1",
     f"El primer ID tiene {len('Nodo_de_distribucion_principal')} símbolos; el máximo es 20."),
]
assert all(en_lenguaje_enlaces(c) for c in VALIDAS_L)
assert not any(en_lenguaje_enlaces(c) for c, _ in INVALIDAS_L)

PRUEBAS_AUTOMATAS = ["tt", "rtt", "ttr", "rltlttr", "lttl", "", "t", "rtrt", "tltl", "rrllr"]
for _w in PRUEBAS_AUTOMATAS:
    assert plan.traza_afn(_w)[1] == plan.traza_afd(_w)[1] == ("tt" in _w)


def nt(nombre):
    return f"<{nombre}>"


# ======================================================================
# Estilos del documento
# ======================================================================
def configurar(doc):
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.59), Cm(27.94)
    sec.left_margin = sec.right_margin = Cm(2.3)
    sec.top_margin, sec.bottom_margin = Cm(2.4), Cm(2.2)
    sec.different_first_page_header_footer = True

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.12
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    for nivel, tam, color, antes in [(1, 16, AZUL, 18), (2, 13, AZUL, 12), (3, 11, NARANJA, 10)]:
        st = doc.styles[f"Heading {nivel}"]
        st.font.name = "Calibri"
        st.font.size = Pt(tam)
        st.font.bold = True
        st.font.italic = False
        st.font.color.rgb = RGBColor.from_string(color)
        rpr = st.element.get_or_add_rPr()
        fuentes = rpr.find(qn("w:rFonts"))
        for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if fuentes is not None and fuentes.get(qn(attr)) is not None:
                del fuentes.attrib[qn(attr)]
        st.paragraph_format.space_before = Pt(antes)
        st.paragraph_format.space_after = Pt(6)
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    cap = doc.styles["Caption"]
    cap.font.name = "Calibri"
    cap.font.size = Pt(9)
    cap.font.italic = True
    cap.font.bold = False
    cap.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
    cap.paragraph_format.space_after = Pt(10)

    for nombre in ("List Bullet", "List Number"):
        doc.styles[nombre].font.name = "Calibri"
        doc.styles[nombre].font.size = Pt(10.5)
        doc.styles[nombre].paragraph_format.space_after = Pt(3)

    # Encabezado y pie (no aparecen en la portada)
    enc = sec.header.paragraphs[0]
    runs(enc, "Network Graph Analyzer — Proyecto Final Integrador · Teoría Computacional",
         tam=8, color="595959")
    enc.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pie = sec.footer.paragraphs[0]
    pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = pie.add_run("Página ")
    r.font.size = Pt(8.5)
    campo(pie, "PAGE", "1")

    # Pedir a Word que actualice el índice al abrir el archivo
    upd = OxmlElement("w:updateFields")
    upd.set(qn("w:val"), "true")
    doc.settings.element.append(upd)

    doc.core_properties.title = "Network Graph Analyzer — Proyecto Final"
    doc.core_properties.author = "; ".join(INTEGRANTES)
    doc.core_properties.subject = "Teoría Computacional · Proyecto 4. Analizador de redes mediante grafos"


# ======================================================================
# Contenido
# ======================================================================
def portada(doc):
    def linea(texto, tam=12, negrita=False, color=None, despues=6):
        par = doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.space_after = Pt(despues)
        runs(par, texto, tam=tam, color=color, negrita=negrita)
        return par

    linea("[[PENDIENTE: logotipo de la universidad]]", tam=10, despues=18)
    linea("[[PENDIENTE: nombre de la universidad]]", tam=15, negrita=True, color=AZUL)
    linea("[[PENDIENTE: carrera]]", tam=12.5, despues=40)
    linea("Materia: Teoría Computacional", tam=12.5)
    linea("Proyecto Final Integrador", tam=12.5, despues=44)
    linea("Network Graph Analyzer", tam=28, negrita=True, color=AZUL, despues=4)
    linea("Proyecto 4 · Analizador de redes mediante grafos", tam=14, color=NARANJA, despues=60)
    linea("Integrantes", tam=12.5, negrita=True, color=AZUL, despues=2)
    for n in INTEGRANTES:
        linea(n, tam=12.5, despues=2)
    linea("", despues=24)
    linea("Profesor", tam=12.5, negrita=True, color=AZUL, despues=2)
    linea("[[PENDIENTE: nombre del profesor]]", tam=12.5, despues=30)
    linea("[[PENDIENTE: fecha de entrega]]", tam=12.5)
    salto_pagina(doc)


def indice(doc):
    par = doc.add_paragraph()
    runs(par, "Índice", tam=16, color=AZUL, negrita=True)
    par = doc.add_paragraph()
    campo(par, 'TOC \\o "1-2" \\h \\z \\u',
          "Haga clic derecho aquí y elija «Actualizar campo» para generar el índice.")
    salto_pagina(doc)


def s01_introduccion(doc):
    H(doc, "1. Introducción", 1)
    P(doc, "Las redes de datos de una escuela, una oficina o un centro de datos pequeño son, en esencia, "
           "un conjunto de dispositivos (routers, switches, servidores y equipos de usuario) unidos por "
           "enlaces. Esa descripción coincide exactamente con la definición de **grafo**, por lo que muchas "
           "preguntas cotidianas de un administrador de red —¿se pueden comunicar dos equipos?, ¿cuál es la "
           "ruta más rápida?, ¿qué equipo, si falla, deja incomunicada a una parte de la red?— son "
           "problemas clásicos de teoría de grafos.")
    P(doc, "Sin embargo, antes de analizar una red es necesario **leer y validar** su descripción, que "
           "normalmente se escribe a mano en archivos de texto. Ahí intervienen los demás temas de Teoría "
           "Computacional: un **lenguaje formal** define qué líneas son correctas, las **expresiones "
           "regulares** las reconocen y extraen sus datos, los **autómatas finitos** procesan secuencias de "
           "eventos de monitoreo para detectar fallas, y una **gramática libre de contexto** con su "
           "**autómata de pila** valida archivos de configuración con zonas anidadas, una estructura que "
           "ninguna expresión regular puede reconocer.")
    P(doc, "Este documento presenta **Network Graph Analyzer**, un prototipo funcional en Python que integra "
           "esos modelos en una sola cadena de procesamiento. Para cada concepto se explica qué es, por qué "
           "se eligió, cómo funciona y qué parte del problema resuelve, siguiendo la secuencia "
           "**problema → modelo formal → solución → implementación → pruebas → explicación**.")


def s02_problema(doc):
    H(doc, "2. Descripción del problema", 1)
    P(doc, "En redes pequeñas y medianas la topología suele documentarse en listas o diagramas estáticos. "
           "Con ellos es difícil responder rápido si dos equipos tienen comunicación, cuál es la ruta de "
           "menor latencia, qué dispositivo es un punto único de falla o cómo cambia la red cuando un "
           "equipo deja de responder. Además, los archivos de configuración escritos a mano contienen "
           "errores de formato que pasan desapercibidos hasta que provocan fallas.")
    P(doc, "Como escenario de trabajo se usa la red de un laboratorio con ocho dispositivos: Router1, "
           "Switch1, Switch2, PC1, PC2, Server, DB e Impresora1 (sección 6).")
    tabla(doc, [
        ["Pregunta guía", "Respuesta"],
        ["¿Cuál es el problema?",
         "Analizar una infraestructura de red (conectividad, rutas, puntos críticos y estado de los "
         "dispositivos) a partir de descripciones en texto que pueden contener errores."],
        ["¿En qué contexto de TI se presenta?",
         "Administración de redes e infraestructura: diseño de topologías, monitoreo de disponibilidad "
         "(ping), análisis de redundancia y planeación de mantenimiento."],
        ["¿Quién utilizaría el sistema?",
         "Administradores de red, personal de soporte técnico, y estudiantes y docentes de redes que "
         "necesitan analizar o validar una topología antes de implementarla o modificarla."],
        ["¿Qué información recibirá?",
         "(1) Archivo de topología .txt con líneas «origen,destino[,latencia]»; (2) archivo de "
         "configuración .red con zonas anidadas, dispositivos (tipo e IP) y enlaces; (3) archivo de "
         "monitoreo con la secuencia de eventos de cada dispositivo (ok, lento, timeout); (4) consultas "
         "por teclado."],
        ["¿Qué información producirá?",
         "Conjuntos V y E, lista y matriz de adyacencia, árbol de rutas, rutas y costos, grados, "
         "dispositivos aislados, ciclos, puntos críticos, rutas alternativas, estado de cada dispositivo, "
         "impacto de fallas, recorridos del AFN, del AFD y del autómata de pila, mensajes de error por "
         "línea, reporte .txt e imágenes PNG."],
        ["¿Qué problemas debe detectar o resolver?",
         "Errores de formato (léxicos), errores de estructura (sintácticos, bloques sin cerrar), "
         "inconsistencias (enlace a un dispositivo no declarado, lazos, duplicados), equipos sin "
         "comunicación, puntos únicos de falla, dispositivos en falla y su efecto sobre las rutas."],
        ["¿Cuáles son sus limitaciones?",
         "No se conecta a una red real: el monitoreo se lee desde archivos de eventos. Enlaces no "
         "dirigidos con latencia entera de 1 a 9999 ms, a lo sumo un enlace por par de dispositivos, "
         "nombres de hasta 20 caracteres y topologías del orden de decenas de nodos."],
    ], [4.2, 12.6], pie="Preguntas guía de la definición del problema.")


def s03_objetivo(doc):
    H(doc, "3. Objetivo general", 1)
    P(doc, "Desarrollar un prototipo funcional que modele una infraestructura tecnológica como un grafo "
           "ponderado, valide sus descripciones mediante lenguajes formales, expresiones regulares, "
           "autómatas finitos y una gramática libre de contexto, y permita analizar conectividad, rutas, "
           "puntos críticos y estados de los dispositivos, demostrando la relación entre los modelos "
           "teóricos del curso y un problema real de Tecnologías de la Información.")
    H(doc, "3.1 Objetivos específicos", 2)
    bullets(doc, [
        "Modelar la red como un grafo no dirigido y ponderado, y representarlo con conjuntos, lista y "
        "matriz de adyacencia.",
        "Implementar al menos ocho análisis útiles sobre el grafo (conectividad, componentes, ruta más corta, "
        "grados, ciclos, puntos críticos, rutas alternativas e impacto de fallas).",
        "Definir formalmente el lenguaje de las líneas de topología y el lenguaje de los eventos de monitoreo.",
        "Construir cuatro expresiones regulares con una función real dentro del analizador léxico.",
        "Diseñar un AFN que detecte fallas, convertirlo a AFD por construcción de subconjuntos y comprobar "
        "que ambos reconocen el mismo lenguaje.",
        "Definir una gramática libre de contexto para archivos de configuración con zonas anidadas y un "
        "autómata de pila que valide su estructura.",
        "Integrar todo en una aplicación de consola que muestre resultados claros y mensajes de error "
        "comprensibles, y validarla con al menos 15 casos de prueba.",
    ])


def s04_alcance(doc):
    H(doc, "4. Alcance y restricciones", 1)
    H(doc, "4.1 Alcance", 2)
    tabla(doc, [
        ["Incluye", "No incluye"],
        ["• Carga y validación de tres formatos de entrada (.txt, .red y monitoreo) y captura por teclado.\n"
         "• Ocho análisis sobre el grafo.\n"
         "• Detección de falla con AFN y AFD, y máquina de estados de los dispositivos.\n"
         "• Parser descendente recursivo y autómata de pila con traza.\n"
         "• Reporte .txt e imágenes PNG del grafo y de los autómatas.",
         "• Captura de tráfico o ping sobre una red real.\n"
         "• Protocolos de enrutamiento dinámico.\n"
         "• Interfaz web o gráfica (la aplicación es de consola).\n"
         "• Base de datos o almacenamiento persistente."],
    ], [8.4, 8.4], color=VERDE)
    H(doc, "4.2 Entradas, procesos y salidas", 2)
    tabla(doc, [
        ["Elemento", "Descripción"],
        ["Entradas", "Topología .txt, configuración .red, monitoreo .txt, consultas y datos por teclado."],
        ["Procesos principales",
         "1) Análisis léxico con expresiones regulares · 2) Validación de bloques con el autómata de pila · "
         "3) Análisis sintáctico con la gramática · 4) Construcción del grafo · 5) Análisis del grafo · "
         "6) Procesamiento del monitoreo con AFN/AFD y máquina de estados · 7) Recalcular la red sin los "
         "dispositivos en falla · 8) Reporte."],
        ["Salidas", "Resultados en consola, reporte .txt, imágenes PNG y mensajes de error con línea y motivo."],
    ], [3.6, 13.2])
    H(doc, "4.3 Restricciones", 2)
    bullets(doc, [
        "Lenguaje Python 3 y aplicación de consola (CLI).",
        "Toda la lógica de Teoría Computacional (grafos, autómatas, conversión, parser y autómata de pila) "
        "se programa a mano. No se usan bibliotecas que construyan autómatas (automata-lib, pyformlang) ni "
        "generadores de parsers (lark, ply, ANTLR).",
        "Bibliotecas externas solo para lo permitido: matplotlib para visualización y pytest para pruebas; "
        "networkx únicamente para dibujar el grafo, nunca para sus algoritmos.",
        "Grafo simple no dirigido, latencias enteras positivas (1–9999 ms), nombres de 1 a 20 caracteres.",
    ])


def s05_solucion(doc):
    H(doc, "5. Descripción de la solución propuesta", 1)
    P(doc, "Network Graph Analyzer recibe la descripción de la red desde archivos o desde el teclado, la "
           "valida por capas y construye un grafo sobre el que ejecuta los análisis. Cada modelo teórico "
           "resuelve una parte concreta del problema:")
    tabla(doc, [
        ["Concepto", "Dónde se aplica", "Qué problema resuelve"],
        ["Grafos", "Modelo de la infraestructura: dispositivos = vértices, enlaces = aristas con latencia.",
         "Conectividad, rutas, ruta más corta, grados, aislados, ciclos, puntos críticos y rutas alternativas."],
        ["Lenguaje formal", "L_{enlaces}: formato de cada línea del archivo de topología; L_{falla}: "
         "secuencias de monitoreo.", "Definir con precisión qué entradas son aceptables."],
        ["Expresiones regulares", "Analizador léxico: nombres, líneas de enlace, IPv4 y líneas de monitoreo.",
         "Separar y validar la información, y reportar errores por línea."],
        ["AFN / AFD", "Detector de falla sobre la secuencia ok / lento / timeout.",
         "Reconocer el patrón «dos timeouts consecutivos» de forma determinista."],
        ["Máquina de estados", "Estado de cada dispositivo: Activo, Sobrecargado, Falla, Recuperación.",
         "Retirar del grafo los nodos en falla y recalcular rutas."],
        ["Gramática / LLC", "Archivo de configuración .red con zonas anidadas.",
         "Describir estructuras jerárquicas que una expresión regular no puede reconocer."],
        ["Autómata de pila", "Validación del anidamiento de bloques RED / ZONA.",
         "Detectar bloques sin cerrar o llaves sobrantes mostrando la pila paso a paso."],
    ], [3.2, 6.8, 6.8], pie="Relación entre los conceptos del curso y el sistema.")
    H(doc, "5.1 Flujo de procesamiento", 2)
    code(doc,
         "Entrada (.txt / .red / monitoreo / teclado)\n"
         "   │\n"
         "   ▼\n"
         "[1] Analizador léxico (R1–R4) ───────────────► errores léxicos (línea y motivo)\n"
         "   ▼\n"
         "[2] Autómata de pila (bloques RED/ZONA) ──────► bloques sin cerrar / '}' sobrante\n"
         "   ▼\n"
         "[3] Parser descendente recursivo (G) ─────────► errores sintácticos y semánticos\n"
         "   ▼\n"
         "[4] Grafo (lista de adyacencia) ◄── [6] Máquina de estados ◄── AFN/AFD ◄── monitoreo\n"
         "   ▼                                 (retira los nodos en Falla)\n"
         "[5] BFS · DFS · Dijkstra · grados · ciclos · Tarjan · rutas alternativas\n"
         "   ▼\n"
         "Salida: consola · reporte .txt · PNG (grafo, AFN, AFD, AP)")
    H(doc, "5.2 Organización del equipo", 2)
    P(doc, "El equipo está formado por dos integrantes. La división indica quién **lidera** cada parte; "
           "ambos integrantes conocen y pueden explicar el funcionamiento completo del proyecto, y cada "
           "entregable fue revisado por el otro integrante.")
    tabla(doc, [
        ["Integrante", "Responsabilidades principales"],
        [f"**{INTEGRANTES[0]}**\n(Integrante 1)",
         "Definición del problema · Modelado del grafo y algoritmos sobre grafos · Gramática y lenguaje "
         "libre de contexto · Parser descendente recursivo · Autómata de pila · Aplicación CLI e "
         "integración de módulos · README.md"],
        [f"**{INTEGRANTES[1]}**\n(Integrante 2)",
         "Definición formal del lenguaje · Expresiones regulares y analizador léxico · AFN · Conversión "
         "AFN → AFD · Máquina de estados de dispositivos · Visualización · Diseño de casos de prueba · "
         "Bitácora y presentación"],
        ["**Ambos**", "Revisión cruzada · Ejecución de pruebas y corrección de errores · Documento final · "
         "Ensayo de la demostración y defensa"],
    ], [5.2, 11.6], pie="Responsabilidades del equipo.")


def s06_grafos(doc):
    H(doc, "6. Modelado mediante grafos", 1)
    H(doc, "6.1 Vértices", 2)
    P(doc, "Cada **vértice** representa un dispositivo de la red: router, switch, servidor, PC, firewall o "
           "impresora. Cada vértice guarda como atributos su tipo, su dirección IP, la zona a la que "
           "pertenece y su estado (Activo, Sobrecargado, Falla o Recuperación).")
    H(doc, "6.2 Aristas", 2)
    P(doc, "Cada **arista** {u, v} representa un enlace físico o lógico entre dos dispositivos. Su peso "
           "w(u, v) es la latencia del enlace en milisegundos.")
    H(doc, "6.3 Tipo de grafo y justificación", 2)
    P(doc, "Se utiliza un grafo **simple, no dirigido y ponderado**.")
    bullets(doc, [
        "**No dirigido:** un enlace Ethernet o inalámbrico transmite en ambos sentidos; si Router1 alcanza a "
        "Switch1, Switch1 alcanza a Router1. Un grafo dirigido duplicaría cada arista sin aportar "
        "información. Modelar reglas de firewall de un solo sentido sí requeriría un grafo dirigido, pero "
        "queda fuera del alcance.",
        "**Ponderado:** sin pesos, la «ruta más corta» solo cuenta saltos. Con la latencia como peso, el "
        "análisis responde la pregunta real del administrador (la ruta más rápida) y permite comparar "
        "rutas alternativas por costo. Los pesos son enteros positivos, condición necesaria para que el "
        "algoritmo de Dijkstra sea correcto.",
        "**Simple:** no hay lazos (un dispositivo no se enlaza consigo mismo) ni aristas múltiples entre el "
        "mismo par de dispositivos.",
    ])
    H(doc, "6.4 Representación", 2)
    figura(doc, figs.DIR_GRAFOS / "Grafo.png", 14.5,
           "Topología de ejemplo con latencias en ms (archivo 04_Grafos/Grafo.png).")
    P(doc, "**Conjunto de vértices:**")
    P(doc, "V = {" + ", ".join(NODOS) + "},   |V| = 8")
    P(doc, "**Conjunto de aristas** (el subíndice es la latencia en ms):")
    P(doc, "E = {" + ", ".join(f"{{{u}, {v}}}_{{{w}}}" for u, v, w in ENLACES) + "},   |E| = 7")
    filas = [["Vértice", "Lista de adyacencia: vecino (latencia)", "Grado"]]
    for n in NODOS:
        vecinos = ", ".join(f"{v} ({w})" for v, w in ADY[n].items())
        filas.append([n, vecinos or "∅ (aislado)", str(len(ADY[n]))])
    tabla(doc, filas, [3.0, 11.6, 2.2], centro=(2,), pie="Lista de adyacencia del grafo de ejemplo.")
    abrev = ["R1", "S1", "S2", "PC1", "PC2", "Srv", "DB", "Imp"]
    filas = [[""] + abrev]
    for i, n in enumerate(NODOS):
        filas.append([abrev[i]] + [str(ADY[n].get(m, 0)) for m in NODOS])
    tabla(doc, filas, [1.8] + [1.85] * 8, centro=range(9),
          pie="Matriz de adyacencia ponderada (0 = sin enlace). Es simétrica porque el grafo es no dirigido.")
    P(doc, "Comprobación: la suma de los grados es 14 = 2·|E|, como establece el lema del apretón de manos.")

    H(doc, "6.5 Operaciones sobre el grafo", 2)
    P(doc, "Se implementan ocho análisis; cada uno responde una pregunta distinta del administrador de red.")
    tabla(doc, [
        ["Análisis", "Algoritmo", "Utilidad en el proyecto"],
        ["Existencia de ruta / conectividad", "BFS, O(V + E)", "¿Pueden comunicarse dos equipos?"],
        ["Componentes conexas", "BFS repetido desde cada vértice no visitado", "Detectar segmentos incomunicados."],
        ["Ruta más corta", "Dijkstra con cola de prioridad (heapq), O((V + E) log V)", "Ruta de menor latencia."],
        ["Grados y aislados", "Recorrido de la lista de adyacencia", "Equipos muy cargados o sin conexión."],
        ["Detección de ciclos", "DFS con control del padre", "Un ciclo indica redundancia (camino de respaldo)."],
        ["Puntos críticos", "Tarjan (tiempos de descubrimiento y low)",
         "Puntos únicos de falla (articulaciones) y enlaces críticos (puentes)."],
        ["Rutas alternativas", "DFS con retroceso (rutas simples) ordenadas por costo",
         "Plan de respaldo si la ruta principal falla."],
        ["Impacto de falla", "Retirar el nodo y repetir componentes y Dijkstra",
         "Qué se pierde si un equipo falla (se conecta con la máquina de estados)."],
    ], [4.0, 6.0, 6.8], pie="Análisis implementados sobre el grafo.")
    H(doc, "Funcionamiento de los algoritmos principales", 3)
    bullets(doc, [
        "**BFS (búsqueda en amplitud):** parte del origen, lo marca como visitado y lo mete en una cola. "
        "Mientras la cola no esté vacía, saca un vértice y encola a sus vecinos no visitados. Si el destino "
        "llega a visitarse, existe una ruta. Repetir BFS desde cada vértice no visitado da las componentes "
        "conexas.",
        "**Dijkstra:** mantiene la distancia tentativa de cada vértice (∞ al inicio, 0 en el origen). En cada "
        "iteración extrae de la cola de prioridad el vértice no visitado con menor distancia y «relaja» sus "
        "aristas: si d(u) + w(u, v) < d(v), actualiza d(v) y guarda u como padre de v. La ruta se "
        "reconstruye siguiendo los padres desde el destino.",
        "**Tarjan:** un DFS asigna a cada vértice su tiempo de descubrimiento disc(v) y el valor low(v), el "
        "menor tiempo alcanzable desde su subárbol usando a lo sumo una arista de retroceso. Un vértice u "
        "(no raíz) es articulación si tiene un hijo v con low(v) ≥ disc(u); la raíz lo es si tiene dos o más "
        "hijos. La arista {u, v} es puente si low(v) > disc(u).",
        "**Ciclos:** en un DFS de un grafo no dirigido, encontrar un vecino ya visitado que no es el padre "
        "indica un ciclo; el ciclo se recupera con la cadena de padres.",
    ])

    H(doc, "6.6 Resultados sobre la red de ejemplo", 2)
    P(doc, "Los siguientes resultados se calcularon a mano y sirven como referencia para verificar el "
           "programa (secciones 15 y 16).")
    tabla(doc, [
        ["Análisis", "Resultado en la red de ejemplo"],
        ["Conectividad", "PC1 ↔ DB: sí existe ruta. PC1 ↔ Impresora1: no existe ruta."],
        ["Componentes conexas", "2 componentes: {Router1, Switch1, Switch2, PC1, PC2, Server, DB} e {Impresora1}."],
        ["Ruta más corta Router1 → DB", "Router1 → Switch2 → Server → DB = 3 + 1 + 2 = **6 ms**."],
        ["Grados y aislados", "Grado máximo: Switch1 (3). Aislado: Impresora1 (grado 0)."],
        ["Ciclos", "Router1 – Switch1 – PC2 – DB – Server – Switch2 – Router1."],
        ["Puntos críticos", "Articulación: Switch1 (si falla, PC1 queda aislado). Puente: {Switch1, PC1}."],
        ["Rutas alternativas Router1 → DB", "1) vía Switch2 – Server: 6 ms. 2) vía Switch1 – PC2: 2 + 1 + 4 = 7 ms."],
        ["Impacto de falla de Server", "La ruta Router1 → DB pasa de 6 ms a 7 ms (vía Switch1 – PC2); "
         "la red sigue conectada."],
    ], [4.6, 12.2], pie="Resultados esperados de los análisis.")
    filas = [["Iteración", "Vértice extraído (d)", "Relajaciones d(v): antes → después"]]
    for i, (u, d, cambios) in enumerate(TRAZA_DIJKSTRA, 1):
        if u == "Impresora1":
            continue
        filas.append([str(i), f"{u} ({d})", cambios])
    tabla(doc, filas, [2.0, 4.2, 10.6], centro=(0,),
          pie="Traza de Dijkstra desde Router1. Impresora1 nunca entra a la cola: queda con d = ∞.")
    P(doc, "Siguiendo los padres que deja Dijkstra se obtiene el **árbol de rutas más cortas** desde "
           "Router1, que es la salida en forma de árbol que muestra el programa:")
    code(doc, "Router1\n├── Switch1 (2 ms)\n│   ├── PC1 (3 ms)\n│   └── PC2 (3 ms)\n└── Switch2 (3 ms)\n"
              "    └── Server (4 ms)\n        └── DB (6 ms)\n\nNo alcanzables desde Router1: Impresora1")
    assert PADRE_R1["PC1"] == PADRE_R1["PC2"] == "Switch1" and PADRE_R1["Server"] == "Switch2"


def s07_lenguajes(doc):
    H(doc, "7. Lenguajes formales", 1)
    P(doc, "Se define formalmente el lenguaje de las líneas del archivo de topología, L_{enlaces}. Es el "
           "primer filtro del sistema: solo las cadenas que pertenecen a L_{enlaces} se convierten en "
           "vértices y aristas. Además se define L_{falla}, el lenguaje de las secuencias de monitoreo que "
           "reconocen el AFN y el AFD.")
    H(doc, "7.1 Alfabeto", 2)
    tabla(doc, [
        ["Subconjunto", "Símbolos", "Significado"],
        ["Letras", "{a, …, z, A, …, Z}", "Forman los nombres de dispositivo."],
        ["Dígitos", "{0, 1, …, 9}", "Forman parte de los nombres y de la latencia."],
        ["Especiales de nombre", "{ _ , - }", "Separadores permitidos dentro de un nombre (sw-core_01)."],
        ["Separador de campos", "{ , }", "La coma separa origen, destino y latencia."],
        ["Espacio", "{ sp }", "Espacio opcional alrededor de las comas."],
    ], [3.8, 4.4, 8.6], pie="Símbolos del alfabeto Σ.")
    P(doc, "**Σ = Letras ∪ Dígitos ∪ { _, -, ',', sp }**")
    H(doc, "7.2 Lenguaje", 2)
    code(doc,
         "ID   = Letra · (Letra ∪ Dígito ∪ {_, -})^k ,      0 ≤ k ≤ 19    (1 a 20 símbolos)\n"
         "PESO = (Dígito − {0}) · Dígito^k ,                0 ≤ k ≤ 3     (1 a 9999 ms)\n"
         "SEP  = sp* · ',' · sp*\n\n"
         "L_enlaces = { x             | x ∈ ID }                   (dispositivo sin enlaces)\n"
         "          ∪ { x·SEP·y       | x, y ∈ ID, x ≠ y }         (enlace con latencia 1 por omisión)\n"
         "          ∪ { x·SEP·y·SEP·p | x, y ∈ ID, x ≠ y, p ∈ PESO } (enlace con latencia p)")
    P(doc, "La condición x ≠ y prohíbe que un dispositivo se enlace consigo mismo. Como no puede "
           "expresarse con una expresión regular sin enumerar todos los nombres, el programa la comprueba "
           "después del análisis léxico.")
    P(doc, "**Lenguaje de monitoreo.** Cada evento del archivo de monitoreo se traduce a un símbolo: "
           "ok → r (respuesta), lento → l (latencia alta) y timeout → t.")
    code(doc, "Σ_m = { r, l, t }\nL_falla = { w ∈ Σ_m* | w contiene la subcadena tt }   (dos timeouts consecutivos = falla)")
    H(doc, "7.3 Cadenas válidas", 2)
    filas = [["#", "Cadena", "Resultado"]]
    for i, c in enumerate(VALIDAS_L, 1):
        filas.append([str(i), c, "Válida"])
    tabla(doc, filas, [1.0, 10.8, 5.0], mono=(1,), centro=(0, 2), pie="Cadenas que pertenecen a L_enlaces.")
    H(doc, "7.4 Cadenas inválidas", 2)
    filas = [["#", "Cadena", "Motivo"]]
    for i, (c, m) in enumerate(INVALIDAS_L, 1):
        filas.append([str(i), c, m])
    tabla(doc, filas, [1.0, 6.4, 9.4], mono=(1,), centro=(0,), color=NARANJA,
          pie="Cadenas que no pertenecen a L_enlaces y motivo.")


def s08_regex(doc):
    H(doc, "8. Expresiones regulares", 1)
    P(doc, "Se usan cuatro expresiones regulares, construidas a partir de las definiciones ID, PESO y SEP de "
           "la sección 7.2. Todas se aplican en el analizador léxico y sus ejemplos se verificaron en Python "
           "con `re.fullmatch`.")
    for r in REGEX:
        H(doc, f"8.{r['clave'][1]} {r['clave']} · {r['nombre']}", 2)
        t = tabla(doc, [
            ["Nombre", r["nombre"]],
            ["Propósito", r["proposito"]],
            ["Expresión regular", r["expr"]],
            ["Explicación", r["expl"]],
            ["Ejemplos válidos", "\n".join(r["validos"])],
            ["Ejemplos inválidos", "\n".join(f"{c}   ({m})" for c, m in r["invalidos"])],
            ["Lugar de uso", r["lugar"]],
        ], [3.4, 13.4], encabezado=False, zebra=False)
        # Columnas de texto literal: expresión y ejemplos
        for fila in (2, 4, 5):
            celda = t.rows[fila].cells[1]
            for par in celda.paragraphs:
                for run in par.runs:
                    run.font.name = "Consolas"
                    run.font.size = Pt(8)
        for fila in t.rows:
            sombrear_celda(fila.cells[0], AZUL_CLARO)
            for run in fila.cells[0].paragraphs[0].runs:
                run.bold = True


def s09_afn(doc):
    H(doc, "9. Autómata finito no determinista (AFN)", 1)
    H(doc, "9.1 Definición", 2)
    P(doc, "El AFN reconoce L_{falla}: secuencias de monitoreo que contienen dos timeouts consecutivos, "
           "criterio con el que el sistema declara que un dispositivo presentó una falla. Su entrada es el "
           "grupo 2 de la expresión R4 traducido a Σ_{m}.")
    code(doc, "N = (Q, Σ, δ, q0, F)\n"
              "Q  = {q0, q1, q2}\n"
              "Σ  = {r, l, t}        r = respuesta ok, l = respuesta lenta, t = timeout\n"
              "q0 = estado inicial   (vigilando)\n"
              "F  = {q2}             (falla detectada)")
    bullets(doc, [
        "**q0 · vigilando:** lee cualquier evento y permanece; con t además «apuesta» a que ese timeout "
        "inicia una falla y pasa a q1. **Aquí está el no determinismo:** δ(q0, t) = {q0, q1}.",
        "**q1 · primer timeout:** solo continúa si el siguiente evento también es t; con r o l esa rama "
        "muere (δ = ∅).",
        "**q2 · falla detectada (aceptación):** ya se observaron dos timeouts seguidos; permanece con "
        "cualquier evento, porque la falla ya ocurrió dentro de la ventana analizada.",
    ])
    H(doc, "9.2 Diagrama", 2)
    figura(doc, figs.DIR_AUTOMATAS / "AFN.png", 13, "Diagrama del AFN que reconoce L_falla (03_Automatas/AFN.png).")
    H(doc, "9.3 Tabla de transiciones", 2)
    tabla_afn(doc, "Tabla de transiciones del AFN (→ estado inicial, * estado de aceptación).")
    H(doc, "9.4 Pruebas", 2)
    P(doc, "En cada paso se muestra el conjunto de estados activos del AFN. La cadena se acepta si el "
           "conjunto final contiene q2.")
    filas = [["Cadena", "Recorrido (conjuntos de estados activos)", "Resultado"]]
    for w in PRUEBAS_AUTOMATAS:
        tr, ok = plan.traza_afn(w)
        filas.append([w or "ε", tr, "Aceptada" if ok else "Rechazada"])
    tabla(doc, filas, [2.0, 12.0, 2.8], mono=(0, 1), pie="Cinco cadenas aceptadas y cinco rechazadas por el AFN.")


def tabla_afn(doc, pie):
    filas = [["δ", "r", "l", "t"]]
    for q in plan.AFN_ESTADOS:
        etiqueta = ("→ " if q == "q0" else "") + ("* " if q in plan.AFN_FINALES else "") + q
        filas.append([etiqueta] + [plan.fmt_conj(plan.AFN_DELTA[(q, a)]) for a in plan.SIGMA_M])
    tabla(doc, filas, [3.2, 4.5, 4.5, 4.6], centro=(0, 1, 2, 3), pie=pie)


def s10_conversion(doc):
    H(doc, "10. Conversión AFN → AFD", 1)
    H(doc, "10.1 AFN original y su tabla", 2)
    P(doc, "Se parte del AFN de la sección 9 (Figura 2), cuya tabla de transiciones es:")
    tabla_afn(doc, "Tabla del AFN original.")
    H(doc, "10.2 Procedimiento: construcción de subconjuntos", 2)
    P(doc, "Como el AFN no tiene transiciones ε, la cerradura-ε de cada conjunto es el propio conjunto. El "
           "procedimiento es:")
    bullets(doc, [
        "El estado inicial del AFD es el conjunto {q0}, que se nombra A.",
        "Para cada conjunto pendiente S y cada símbolo a se calcula mover(S, a) = ⋃ δ(q, a) para q ∈ S.",
        "Si el conjunto resultante no se había obtenido antes, se le asigna un nombre nuevo y se agrega a "
        "la lista de pendientes.",
        "El proceso termina cuando ya no aparecen conjuntos nuevos.",
        "Un estado del AFD es de aceptación si contiene algún estado final del AFN (q2).",
    ], "List Number")
    filas = [["Edo.", "Conjunto S", "a", "Cálculo de mover(S, a)", "Resultado", "Nombre", "¿Nuevo?"]]
    for nombre, conj, a, det, dest, nom, nuevo in plan.PASOS_AFD:
        filas.append([nombre, conj, a, det, dest, nom, nuevo])
    tabla(doc, filas, [1.1, 2.4, 0.7, 6.9, 2.5, 1.4, 1.8], mono=(1, 3, 4), centro=(0, 2, 5, 6),
          pie="Procedimiento de construcción de subconjuntos, paso por paso.")
    H(doc, "10.3 Nuevos estados obtenidos", 2)
    filas = [["Estado del AFD", "Conjunto de estados del AFN", "¿Contiene q2?"]]
    for nombre in sorted(plan.CONJ_DE):
        filas.append([nombre, plan.fmt_conj(plan.CONJ_DE[nombre]),
                      "Sí" if nombre in plan.FINALES_AFD else "No"])
    tabla(doc, filas, [4.0, 8.0, 4.8], mono=(1,), centro=(0, 2), pie="Estados del AFD.")
    H(doc, "10.4 Tabla de transición del AFD", 2)
    filas = [["δ_D", "r", "l", "t"]]
    for nombre in sorted(plan.CONJ_DE):
        etiqueta = ("→ " if nombre == "A" else "") + ("* " if nombre in plan.FINALES_AFD else "") + nombre
        filas.append([etiqueta] + [plan.TABLA_AFD[(nombre, a)] for a in plan.SIGMA_M])
    tabla(doc, filas, [3.2, 4.5, 4.5, 4.6], centro=(0, 1, 2, 3),
          pie="Tabla de transición del AFD (→ inicial, * final).")
    H(doc, "10.5 Diagrama final del AFD", 2)
    figura(doc, figs.DIR_AUTOMATAS / "AFD.png", 16,
           "AFD obtenido por construcción de subconjuntos (03_Automatas/AFD.png).")
    H(doc, "10.6 Estado inicial y estados finales", 2)
    bullets(doc, [
        "**Estado inicial:** A = {q0}, porque el AFN comienza únicamente en q0.",
        "**Estados finales:** C = {q0, q1, q2} y D = {q0, q2}, porque ambos contienen q2, el estado de "
        "aceptación del AFN. A y B no contienen q2 y no son finales.",
    ])
    H(doc, "10.7 Comprobación con cadenas de prueba", 2)
    filas = [["Cadena", "Recorrido en el AFD", "AFD", "AFN", "¿Coinciden?"]]
    for w in PRUEBAS_AUTOMATAS:
        tr, ok = plan.traza_afd(w)
        _, ok_n = plan.traza_afn(w)
        filas.append([w or "ε", tr, "Acepta" if ok else "Rechaza", "Acepta" if ok_n else "Rechaza",
                      "Sí" if ok == ok_n else "No"])
    tabla(doc, filas, [2.0, 8.4, 2.0, 2.0, 2.4], mono=(0, 1), centro=(2, 3, 4),
          pie="El AFN y el AFD dan el mismo resultado para las diez cadenas de prueba.")
    P(doc, "Además, las pruebas automáticas comparan el AFN contra el AFD para **todas** las cadenas de Σ_{m} "
           "de longitud 0 a 8 (9 841 cadenas).")
    pendiente(doc, "confirmar con el programa que las 9 841 cadenas coinciden y anotar el resultado de pytest")
    H(doc, "10.8 Minimización (análisis adicional)", 2)
    P(doc, "Se aplica el método de particiones. La partición inicial separa estados finales y no finales: "
           "P0 = { {A, B}, {C, D} }. En {A, B}, con el símbolo t, A va a B (grupo no final) y B va a C "
           "(grupo final), así que A y B se separan. En {C, D}, ambos van a D con r y l, y a C con t: "
           "siempre al mismo grupo, por lo que **C ≡ D**. El AFD mínimo tiene tres estados.")
    figura(doc, figs.DIR_AUTOMATAS / "AFD_minimo.png", 11.5,
           "AFD mínimo: los estados equivalentes C y D se fusionan (03_Automatas/AFD_minimo.png).")
    H(doc, "10.9 Aplicación: máquina de estados de los dispositivos", 2)
    P(doc, "Mientras el AFD de falla responde «¿hubo falla en la ventana?», la máquina de estados responde "
           "«¿en qué estado está el dispositivo ahora?». Es un AFD completo sobre el mismo alfabeto Σ_{m}, y "
           "su resultado modifica el grafo: los dispositivos en Falla se retiran y se recalculan las rutas.")
    figura(doc, figs.DIR_AUTOMATAS / "Maquina_estados.png", 10,
           "Máquina de estados de un dispositivo (03_Automatas/Maquina_estados.png).")
    tabla(doc, [
        ["Estado", "r (ok)", "l (lento)", "t (timeout)", "Efecto sobre el grafo"],
        ["→ Activo", "Activo", "Sobrecargado", "Sobrecargado", "Participa normalmente."],
        ["Sobrecargado", "Activo", "Sobrecargado", "Falla", "Participa; se marca en el reporte."],
        ["Falla", "Recuperación", "Recuperación", "Falla", "Se retira del grafo y se recalculan las rutas."],
        ["Recuperación", "Activo", "Sobrecargado", "Falla", "Vuelve a participar."],
    ], [3.0, 2.4, 2.6, 2.6, 6.2], pie="Transiciones de la máquina de estados.")
    P(doc, "Ejemplo: `Server: ok, timeout, timeout` se traduce a r t t y recorre Activo → Activo → "
           "Sobrecargado → Falla. Al retirar Server, la ruta Router1 → DB cambia de 6 ms (vía Switch2) a "
           "7 ms (vía Switch1 y PC2). Desde Activo, dos timeouts consecutivos siempre llevan a Falla, el mismo "
           "patrón que detecta el AFN; la máquina además pasa a Falla con «lento, timeout», porque un "
           "dispositivo sobrecargado que deja de responder también se considera caído.")


GRAMATICA = [
    ("1", nt("red"), f"RED id {nt('bloque')}", "Una red tiene nombre y un bloque."),
    ("2", nt("bloque"), f"{{ {nt('elementos')} }}", "Un bloque es una lista de elementos entre llaves."),
    ("3", nt("elementos"), f"{nt('elemento')} {nt('elementos')}", "Lista de elementos (recursiva)."),
    ("4", nt("elementos"), "ε", "La lista puede terminar (se permite un bloque vacío)."),
    ("5", nt("elemento"), nt("zona"), "Un elemento puede ser una zona…"),
    ("6", nt("elemento"), nt("dispositivo"), "…un dispositivo…"),
    ("7", nt("elemento"), nt("enlace"), "…o un enlace."),
    ("8", nt("zona"), f"ZONA id {nt('bloque')}",
     "Una zona tiene nombre y su propio bloque: **aquí está la recursión que produce el anidamiento**."),
    ("9", nt("dispositivo"), f"DISPOSITIVO id {nt('tipo')} ip ;", "Declaración de dispositivo con tipo e IP."),
    ("10a–10e", nt("tipo"), "router | switch | pc | servidor | firewall", "Tipos de dispositivo admitidos."),
    ("11", nt("enlace"), "ENLACE id id num ;", "Enlace entre dos dispositivos con su latencia."),
]


def s11_gramatica(doc):
    H(doc, "11. Gramática", 1)
    P(doc, "Para describir redes con estructura jerárquica (una red con zonas, y zonas dentro de zonas, como "
           "edificio → piso → rack) se define el formato de configuración **.red**. Ejemplo de archivo válido:")
    code(doc, "RED campus {\n"
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
              "}")
    P(doc, "El analizador léxico convierte el texto en tokens y la gramática define cómo deben combinarse. "
           "Los tokens id, ip y num se reconocen con R1, R3 y la definición PESO, respectivamente.")
    H(doc, "11.1 Definición formal", 2)
    P(doc, "G = (V, Σ, P, S), donde:")
    bullets(doc, [
        f"**V** (variables) = {{ {nt('red')}, {nt('bloque')}, {nt('elementos')}, {nt('elemento')}, "
        f"{nt('zona')}, {nt('dispositivo')}, {nt('tipo')}, {nt('enlace')} }}",
        "**Σ** (terminales) = { RED, ZONA, DISPOSITIVO, ENLACE, {, }, ;, id, ip, num, router, switch, pc, "
        "servidor, firewall }",
        "**P** (producciones) = las de la tabla siguiente",
        f"**S** (símbolo inicial) = {nt('red')}",
    ])
    H(doc, "11.2 Producciones", 2)
    filas = [["#", "Producción", "Significado"]]
    for n, izq, der, sig in GRAMATICA:
        filas.append([n, f"{izq} → {der}", sig])
    tabla(doc, filas, [1.5, 7.3, 8.0], mono=(1,), centro=(0,), pie="Producciones de la gramática G.")
    H(doc, "11.3 Derivaciones de cadenas válidas", 2)
    P(doc, "Derivaciones por la izquierda sobre tokens; la columna «Prod.» indica la producción aplicada.")
    E, EL, B = nt("elementos"), nt("elemento"), nt("bloque")
    derivaciones = [
        ("D1", "RED campus { }", [
            (nt("red"), ""), (f"RED id {B}", "1"), (f"RED id {{ {E} }}", "2"), ("RED id { }", "4")]),
        ("D2", "RED lab { DISPOSITIVO R1 router 10.0.0.1 ; }", [
            (nt("red"), ""), (f"RED id {B}", "1"), (f"RED id {{ {E} }}", "2"),
            (f"RED id {{ {EL} {E} }}", "3"), (f"RED id {{ {nt('dispositivo')} {E} }}", "6"),
            (f"RED id {{ DISPOSITIVO id {nt('tipo')} ip ; {E} }}", "9"),
            (f"RED id {{ DISPOSITIVO id router ip ; {E} }}", "10a"),
            ("RED id { DISPOSITIVO id router ip ; }", "4")]),
        ("D3", "RED lab { ENLACE PC1 Switch1 1 ; }", [
            (nt("red"), ""), (f"RED id {B}", "1"), (f"RED id {{ {E} }}", "2"),
            (f"RED id {{ {EL} {E} }}", "3"), (f"RED id {{ {nt('enlace')} {E} }}", "7"),
            (f"RED id {{ ENLACE id id num ; {E} }}", "11"), ("RED id { ENLACE id id num ; }", "4")]),
        ("D4", "RED campus { ZONA dc { } }", [
            (nt("red"), ""), (f"RED id {B}", "1"), (f"RED id {{ {E} }}", "2"),
            (f"RED id {{ {EL} {E} }}", "3"), (f"RED id {{ {nt('zona')} {E} }}", "5"),
            (f"RED id {{ ZONA id {B} {E} }}", "8"), (f"RED id {{ ZONA id {{ {E} }} {E} }}", "2"),
            (f"RED id {{ ZONA id {{ }} {E} }}", "4"), ("RED id { ZONA id { } }", "4")]),
        ("D5", "RED campus { DISPOSITIVO S servidor 10.0.0.5 ; ZONA dc { ENLACE A B 5 ; } }", [
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
    for clave, cadena, pasos in derivaciones:
        P(doc, f"**{clave} ·** `{cadena}`").paragraph_format.keep_with_next = True
        filas = [["Paso", "Forma sentencial", "Prod."]]
        for i, (forma, prod) in enumerate(pasos):
            filas.append([str(i), ("⇒ " if i else "") + forma, prod or "S"])
        tabla(doc, filas, [1.2, 14.0, 1.6], mono=(1,), centro=(0, 2), tam=8)
    H(doc, "11.4 Cadenas que no pueden generarse", 2)
    tabla(doc, [
        ["Cadena", "Motivo"],
        ["ZONA dc { }", f"Toda derivación inicia en {nt('red')}, que exige el terminal RED al principio."],
        ["RED campus { ZONA dc { }", "Falta una llave de cierre: la producción 2 siempre genera { y } en pareja."],
        ["RED campus { ENLACE R1 R2 ; }", "La producción 11 exige num antes de ';' (falta la latencia)."],
        ["RED campus { DISPOSITIVO R1 modem 10.0.0.1 ; }", f"«modem» no es un terminal de {nt('tipo')} (producción 10)."],
        ["RED a { } RED b { }", f"{nt('red')} genera una sola red; ninguna producción concatena dos."],
    ], [7.4, 9.4], mono=(0,), color=NARANJA, pie="Cadenas que G no puede generar.")


def s12_llc(doc):
    H(doc, "12. Lenguaje libre de contexto", 1)
    P(doc, "L(G) es un **lenguaje libre de contexto**: todas las producciones de G tienen un solo no terminal "
           "del lado izquierdo, de modo que cada variable se reescribe sin importar lo que la rodea.")
    H(doc, "12.1 ¿Por qué no es un lenguaje regular?", 2)
    P(doc, "Las producciones 2 y 8 permiten anidar zonas sin límite, y cada llave que abre debe tener su "
           "llave de cierre. Sea R el lenguaje regular RED id { (ZONA id {)* }*. Entonces:")
    code(doc, "L(G) ∩ R = { RED id { (ZONA id {)^n  }^(n+1)  |  n ≥ 0 }")
    P(doc, "Supongamos que L(G) ∩ R es regular y sea p la constante del lema de bombeo. Tomamos "
           "w = RED id { (ZONA id {)^p }^(p+1). Cualquier división w = xyz con |xy| ≤ p y |y| ≥ 1 coloca a y "
           "dentro de la parte inicial, antes de las llaves de cierre. Al bombear (xy²z), o bien cambia el "
           "número de «{» sin cambiar el de «}», o bien se rompe el patrón RED id { (ZONA id {)*; en ambos "
           "casos xy²z ∉ L(G) ∩ R, lo cual es una contradicción. Como los lenguajes regulares son cerrados "
           "bajo intersección y R es regular, **L(G) no es regular**. Por eso no basta con expresiones "
           "regulares y se necesitan una gramática libre de contexto y un autómata de pila.")
    H(doc, "12.2 Propiedades útiles para la implementación", 2)
    bullets(doc, [
        f"**G es LL(1):** cada alternativa de {nt('elemento')} y de {nt('tipo')} comienza con un terminal "
        f"distinto (ZONA, DISPOSITIVO, ENLACE; router, switch…), y {nt('elementos')} → ε solo se elige cuando "
        "el siguiente token es «}». Con un solo token de anticipación se sabe qué producción aplicar, lo que "
        "permite un parser descendente recursivo sin retroceso: una función por no terminal.",
        "**Validaciones semánticas** que la gramática no puede expresar porque dependen del contexto, y que se "
        "hacen después del análisis: un ENLACE solo puede usar dispositivos ya declarados, los nombres y las "
        "IP no se repiten y un enlace no conecta un dispositivo consigo mismo.",
    ])


def s13_pila(doc):
    H(doc, "13. Autómata de pila", 1)
    P(doc, "El autómata de pila valida la **estructura de bloques** del archivo .red y muestra cómo cambia la "
           "pila conforme se abren y cierran bloques. Trabaja sobre la secuencia de tokens del analizador "
           "léxico; tipo representa cualquiera de router, switch, pc, servidor o firewall.")
    tabla(doc, [
        ["Aspecto", "Diseño"],
        ["¿Qué estructura reconoce?", "Archivos .red bien anidados: una RED con zonas, dispositivos y "
         "enlaces, con zonas dentro de zonas a cualquier profundidad."],
        ["¿Qué se almacena en la pila?", "Un símbolo por cada bloque abierto: **R** para el bloque de la RED "
         "y **Z** por cada ZONA abierta. Z0 marca el fondo de la pila. El programa muestra además el nombre "
         "(por ejemplo Z[datacenter]) para que la traza sea legible."],
        ["¿Cuándo se introduce información?", "Al leer «{» después de RED id (push R) o después de ZONA id "
         "(push Z)."],
        ["¿Cuándo se retira?", "Al leer «}»: si el tope es Z se cierra una zona; si el tope es R se cierra la red."],
        ["Condición de aceptación", "Estado final qf, entrada consumida por completo y pila con solo Z0 "
         "(todos los bloques cerrados)."],
    ], [4.6, 12.2], pie="Diseño del autómata de pila.")
    H(doc, "13.1 Representación del autómata", 2)
    code(doc, "M = (Q, Σ, Γ, δ, q0, Z0, F)\n"
              "Q  = {q0, q1, …, q13, qf}        Γ = {Z0, R, Z}        F = {qf}\n"
              "Σ  = {RED, ZONA, DISPOSITIVO, ENLACE, id, tipo, ip, num, {, }, ;}\n"
              "X representa cualquier símbolo de bloque en el tope (R o Z), que se conserva.")
    figura(doc, figs.DIR_AUTOMATAS / "AP.png", 16,
           "Diagrama del autómata de pila. Etiquetas: «entrada, tope / cadena que reemplaza al tope» "
           "(03_Automatas/AP.png).")
    H(doc, "13.2 Explicación de los estados", 2)
    tabla(doc, [
        ["Estado", "Significado"],
        ["q0", "Inicio: se espera RED."],
        ["q1, q2", "Se leyó RED; se espera su nombre y después «{»."],
        ["q3", "**Dentro de un bloque:** se espera ZONA, DISPOSITIVO, ENLACE o «}»."],
        ["q4, q5", "Se leyó ZONA; se espera su nombre y después «{»."],
        ["q6, q7, q8", "Declaración DISPOSITIVO: se esperan id, tipo e ip."],
        ["q10, q11, q12", "Declaración ENLACE: se esperan id, id y num."],
        ["q9", "Fin de una declaración: se espera «;» para volver a q3."],
        ["q13", "Se cerró el bloque de la RED."],
        ["qf", "Aceptación."],
    ], [3.2, 13.6], pie="Estados del autómata de pila.")
    H(doc, "13.3 Transiciones", 2)
    filas = [["#", "δ(estado, entrada, tope)", "→ (estado, reemplazo del tope)", "Acción en la pila"]]
    accion = {"R": "push R", "Z": "push Z"}
    for i, ((q, a, x), (p, emp)) in enumerate(plan.AP_DELTA.items(), 1):
        if not emp:
            acc = f"pop {x}"
        elif len(emp) == 2:
            acc = accion[emp[0]]
        else:
            acc = "sin cambio"
        filas.append([str(i), f"δ({q}, {a}, {x})", f"({p}, {' '.join(emp) if emp else 'ε'})", acc])
    filas.append([str(len(plan.AP_DELTA) + 1), "δ(q13, ε, Z0)", "(qf, Z0)", "sin cambio · aceptar"])
    tabla(doc, filas, [1.0, 5.8, 6.0, 4.0], mono=(1, 2), centro=(0,), pie="Función de transición del autómata de pila.")
    P(doc, "El autómata es determinista: para cada combinación de estado, token y tope existe a lo sumo una "
           "transición, y la única transición ε (desde q13) no compite con ninguna otra.")
    H(doc, "13.4 Contenido de la pila durante el procesamiento", 2)
    P(doc, "En la columna «Pila» el tope está a la izquierda. Las trazas se obtuvieron ejecutando la función de "
           "transición anterior token por token.")
    ejemplos = [
        ("Aceptada 1", "RED id { }"),
        ("Aceptada 2", "RED id { DISPOSITIVO id tipo ip ; ENLACE id id num ; }"),
        ("Aceptada 3", "RED id { ZONA id { ZONA id { DISPOSITIVO id tipo ip ; } } }"),
        ("Rechazada 1", "RED id { ZONA id { }"),
        ("Rechazada 2", "RED id { } }"),
        ("Rechazada 3", "RED id DISPOSITIVO id tipo ip ;"),
    ]
    for titulo, cadena in ejemplos:
        ok, filas_t, motivo = plan.simular_ap(cadena.split())
        assert ok == titulo.startswith("Aceptada")
        P(doc, f"**{titulo}:** `{cadena}`").paragraph_format.keep_with_next = True
        filas = [["#", "Estado", "Entrada restante", "Transición", "Pila"]] + [list(f) for f in filas_t]
        tabla(doc, filas, [0.9, 1.4, 7.6, 4.0, 2.9], mono=(2, 3, 4), centro=(0, 1),
              color=VERDE if ok else NARANJA, tam=7.8)
        P(doc, f"**Resultado: {'ACEPTADA' if ok else 'RECHAZADA'}.** {motivo}")


def s14_implementacion(doc):
    H(doc, "14. Implementación", 1)
    H(doc, "14.1 Arquitectura", 2)
    P(doc, "La aplicación sigue una arquitectura en capas, en el mismo orden en que la teoría procesa la "
           "información (sección 5.1). Cada capa es un módulo independiente con pruebas propias, lo que "
           "permite explicar cualquier fragmento de forma aislada.")
    H(doc, "14.2 Componentes", 2)
    code(doc,
         "02_Codigo/\n"
         "├── main.py                    # menú CLI, argumentos y manejo de errores\n"
         "├── red/\n"
         "│   ├── grafo.py               # clase Grafo: lista/matriz de adyacencia, carga de archivos\n"
         "│   └── algoritmos.py          # BFS, DFS, Dijkstra, grados, ciclos, Tarjan, rutas alternativas\n"
         "├── lenguajes/\n"
         "│   └── lexico.py              # regex R1–R4, validación por línea, tokenizador de .red\n"
         "├── automatas/\n"
         "│   ├── afn.py                 # clase AFN y recorrido con conjuntos de estados\n"
         "│   ├── afd.py                 # clase AFD y recorrido\n"
         "│   ├── conversion.py          # construcción de subconjuntos (tabla de pasos)\n"
         "│   └── maquina_estados.py     # Activo / Sobrecargado / Falla / Recuperación\n"
         "├── gramatica/\n"
         "│   ├── parser.py              # parser descendente recursivo + validación semántica\n"
         "│   └── automata_pila.py       # autómata de pila con traza de la pila\n"
         "├── reportes/\n"
         "│   ├── visualizacion.py       # PNG con matplotlib y árbol de texto\n"
         "│   └── reporte.py             # exportar reporte .txt\n"
         "├── datos/                     # red_ejemplo.txt, red_campus.red, monitoreo.txt\n"
         "├── tests/                     # pruebas con pytest\n"
         "├── requirements.txt\n"
         "└── README.md")
    tabla(doc, [
        ["Componente", "Responsabilidad", "Modelo teórico"],
        ["red/grafo.py", "Estructura del grafo, alta de vértices y aristas, lista y matriz de adyacencia.", "Grafos"],
        ["red/algoritmos.py", "Los ocho análisis de la sección 6.5.", "Grafos"],
        ["lenguajes/lexico.py", "Expresiones R1–R4, mensajes de error por línea, tokens del archivo .red.",
         "Lenguajes y regex"],
        ["automatas/afn.py, afd.py", "Representación con diccionarios de transiciones y recorrido con traza.",
         "AFN, AFD"],
        ["automatas/conversion.py", "Construcción de subconjuntos con la tabla de pasos de la sección 10.2.",
         "AFN → AFD"],
        ["automatas/maquina_estados.py", "Estado de cada dispositivo a partir de su monitoreo.", "AFD"],
        ["gramatica/parser.py", "Una función por no terminal de G; errores sintácticos y semánticos.",
         "Gramática / LLC"],
        ["gramatica/automata_pila.py", "Función δ de la sección 13.3 con lista de Python como pila.",
         "Autómata de pila"],
        ["main.py", "Menú, lectura de archivos y teclado, manejo de errores sin cerrar el programa.", "—"],
    ], [4.6, 8.6, 3.6], mono=(0,), pie="Componentes del programa.")
    pendiente(doc, "ajustar la estructura y los nombres de funciones si cambian en el código final "
                   "(también en la fila «Lugar de uso» de cada expresión regular, sección 8)")
    H(doc, "14.3 Funcionamiento", 2)
    tabla(doc, [
        ["Opción", "Función", "Modelo aplicado"],
        ["1", "Cargar topología desde archivo .txt", "L_enlaces + R1 / R2"],
        ["2", "Cargar configuración .red", "R1 / R3 + autómata de pila + gramática"],
        ["3", "Capturar enlaces por teclado", "R2 en cada línea"],
        ["4", "Mostrar el grafo (V, E, lista, matriz, árbol, PNG)", "Grafos"],
        ["5", "Análisis: ruta, ruta más corta, grados, aislados, ciclos, puntos críticos, rutas alternativas",
         "Algoritmos sobre grafos"],
        ["6", "Procesar monitoreo y ver el impacto de las fallas", "R4 + AFN/AFD + máquina de estados + grafos"],
        ["7", "Laboratorio teórico: probar cadenas en AFN, AFD y autómata de pila con traza; ver la tabla de "
              "conversión", "AFN, AFD, subconjuntos, AP"],
        ["8", "Exportar reporte .txt e imágenes", "—"],
        ["0", "Salir", "—"],
    ], [1.5, 10.0, 5.3], centro=(0,), pie="Opciones del menú principal.")
    P(doc, "Ejemplo de ejecución con un archivo que contiene errores:")
    code(doc,
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
         "Resultado: 1 enlace cargado, 3 líneas rechazadas.")
    pendiente(doc, "reemplazar el ejemplo anterior por la salida real del programa si el formato cambia")
    captura(doc, "menú principal de Network Graph Analyzer")
    captura(doc, "carga de red_ejemplo.txt y visualización del grafo")
    captura(doc, "procesamiento de monitoreo con la traza del AFN y del AFD")
    captura(doc, "validación de un archivo .red con la traza de la pila")
    P(doc, "Los requisitos de instalación, las instrucciones de ejecución y más ejemplos de uso se encuentran "
           "en `02_Codigo/README.md`.")


def s15_pruebas(doc):
    H(doc, "15. Casos de prueba", 1)
    P(doc, f"Se diseñaron {len(plan.CASOS_PRUEBA)} casos del sistema completo (el mínimo es 15) que cubren entradas "
           "válidas, inválidas, casos normales, casos límite y entradas inesperadas. El resultado esperado se "
           "fijó **antes** de ejecutar el programa.")
    filas = [["ID", "Entrada", "Categoría", "Resultado esperado", "Resultado obtenido", "Estado"]]
    for c in plan.CASOS_PRUEBA:
        filas.append(list(c) + ["", ""])
    tabla(doc, filas, [1.1, 4.4, 2.3, 4.6, 2.6, 1.8], centro=(0, 5), pie="Casos de prueba del sistema completo.")
    pendiente(doc, "llenar «Resultado obtenido» y «Estado» (Correcto / Error) al ejecutar cada caso; "
                   "la misma tabla va en 05_Pruebas/casos_prueba")
    P(doc, "Además de esta tabla, cada módulo tiene pruebas automáticas con pytest: las expresiones regulares "
           "con las 20 cadenas de la sección 7, la equivalencia exhaustiva AFN/AFD, las trazas del autómata de "
           "pila y los resultados de los algoritmos contra los calculados a mano en la sección 6.6.")
    pendiente(doc, "pegar el resumen de la ejecución de pytest (número de pruebas y resultado)")


def s16_resultados(doc):
    H(doc, "16. Resultados", 1)
    H(doc, "16.1 Resumen de las pruebas", 2)
    tabla(doc, [
        ["Indicador", "Valor"],
        ["Casos de prueba del sistema ejecutados", f"[[PENDIENTE]] de {len(plan.CASOS_PRUEBA)}"],
        ["Casos con estado «Correcto»", "[[PENDIENTE]]"],
        ["Casos con estado «Error» (corregidos o documentados en la sección 17)", "[[PENDIENTE]]"],
        ["Pruebas automáticas (pytest) aprobadas", "[[PENDIENTE]]"],
    ], [11.0, 5.8], pie="Resumen de resultados.")
    H(doc, "16.2 Comparación con los resultados esperados", 2)
    tabla(doc, [
        ["Análisis", "Esperado (sección 6.6)", "Obtenido por el programa"],
        ["Ruta más corta Router1 → DB", "Router1 → Switch2 → Server → DB, 6 ms", ""],
        ["Componentes conexas", "2 componentes", ""],
        ["Puntos críticos", "Articulación Switch1; puente {Switch1, PC1}", ""],
        ["Grados", "Máximo Switch1 (3); aislado Impresora1", ""],
        ["Monitoreo Server: ok, timeout, timeout", "AFN y AFD aceptan; Server → Falla; Router1 → DB = 7 ms", ""],
        [".red con zonas anidadas (3 niveles)", "AP acepta; profundidad máxima de la pila 3", ""],
    ], [5.0, 6.4, 5.4], pie="Resultados esperados contra resultados obtenidos.")
    pendiente(doc, "llenar la columna «Obtenido por el programa»")
    H(doc, "16.3 Cumplimiento de los requisitos", 2)
    tabla(doc, [
        ["Requisito del proyecto", "Mínimo", "Entregado", "Sección"],
        ["Análisis sobre el grafo", "2", "8", "6.5"],
        ["Cadenas válidas / inválidas del lenguaje", "10 / 10", "10 / 10", "7.3, 7.4"],
        ["Expresiones regulares", "3", "4", "8"],
        ["Cadenas aceptadas / rechazadas por el AFN", "5 / 5", "5 / 5", "9.4"],
        ["Conversión AFN → AFD con procedimiento", "Sí", "Sí, más minimización", "10"],
        ["Derivaciones válidas / cadenas no generables", "5 / 5", "5 / 5", "11.3, 11.4"],
        ["Ejemplos aceptados / rechazados del AP", "3 / 3", "3 / 3", "13.4"],
        ["Casos de prueba del sistema", "15", str(len(plan.CASOS_PRUEBA)), "15"],
    ], [7.4, 2.6, 4.0, 2.8], centro=(1, 2, 3), pie="Requisitos mínimos del enunciado y lo entregado.")
    H(doc, "16.4 Evidencia de funcionamiento", 2)
    captura(doc, "análisis de puntos críticos y rutas alternativas")
    captura(doc, "impacto de la falla de Server sobre la ruta Router1 → DB")


def s17_problemas(doc):
    H(doc, "17. Problemas encontrados y soluciones", 1)
    P(doc, "La tabla registra los problemas que surgieron durante el diseño y el desarrollo, su causa y cómo se "
           "resolvieron. Los dos primeros corresponden a la etapa de diseño.")
    tabla(doc, [
        ["#", "Problema", "Causa", "Solución", "Responsable"],
        ["1", "La expresión para IP sugerida en el enunciado aceptaba 999.999.999.999.",
         "`[0-9]{1,3}` no limita el valor de cada octeto.",
         "Se dividió cada octeto en casos (250–255, 200–249, 100–199, 0–99) en la expresión R3.", "Axel"],
        ["2", "El árbol de salida se describió inicialmente como árbol BFS, pero DB colgaba de Server.",
         "BFS pone a DB bajo PC2 (menos saltos); bajo Server solo queda con Dijkstra (menor latencia).",
         "Se definió la salida como árbol de rutas más cortas de Dijkstra y se agregó su traza (sección 6.6).",
         "Hiram"],
        ["3", "", "", "", ""],
        ["4", "", "", "", ""],
        ["5", "", "", "", ""],
        ["6", "", "", "", ""],
    ], [0.8, 4.4, 4.2, 5.2, 2.2], centro=(0,), pie="Problemas encontrados y soluciones.")
    pendiente(doc, "registrar los problemas reales del desarrollo del código (errores, pruebas fallidas, "
                   "cambios de diseño) con su causa y solución; tomarlos de la bitácora")


def s18_conclusiones(doc):
    H(doc, "18. Conclusiones", 1)
    for n in INTEGRANTES:
        H(doc, n, 2)
        pendiente(doc, f"conclusión personal de {n.split()[0]}: qué aprendió, qué concepto le pareció más "
                       "útil y cómo se relaciona la teoría con la implementación")


def s19_referencias(doc):
    H(doc, "19. Referencias", 1)
    refs = [
        "Aho, A. V., Lam, M. S., Sethi, R. y Ullman, J. D. (2006). *Compilers: Principles, Techniques, and "
        "Tools* (2.ª ed.). Addison-Wesley.",
        "Cormen, T. H., Leiserson, C. E., Rivest, R. L. y Stein, C. (2022). *Introduction to Algorithms* "
        "(4.ª ed.). MIT Press.",
        "Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. *Numerische Mathematik*, "
        "1, 269–271.",
        "Hopcroft, J. E., Motwani, R. y Ullman, J. D. (2007). *Introducción a la teoría de autómatas, "
        "lenguajes y computación* (3.ª ed.). Pearson.",
        "Python Software Foundation. (2026). *re — Regular expression operations*. Documentación de Python 3. "
        "https://docs.python.org/3/library/re.html",
        "Sipser, M. (2012). *Introduction to the Theory of Computation* (3.ª ed.). Cengage Learning.",
        "Tarjan, R. E. (1972). Depth-first search and linear graph algorithms. *SIAM Journal on Computing*, "
        "1(2), 146–160.",
    ]
    for r in refs:
        par = doc.add_paragraph()
        par.paragraph_format.left_indent = Cm(1)
        par.paragraph_format.first_line_indent = Cm(-1)
        par.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for i, parte in enumerate(r.split("*")):
            run = par.add_run(parte)
            run.italic = i % 2 == 1


def s20_anexos(doc):
    H(doc, "20. Anexos", 1)
    H(doc, "Anexo A. Bitácora de trabajo", 2)
    P(doc, "La bitácora completa se encuentra en `07_Evidencias/`. Resumen:")
    tabla(doc, [
        ["Fecha", "Actividad", "Responsable(s)", "Resultado"],
        ["10/11/2026", "Análisis del enunciado y plan de trabajo", "Ambos", "Plan de trabajo"],
        ["17/11/2026", "Estructura del documento final y diagramas (grafo, AFN, AFD, AP)", "Ambos",
         "Documento base y figuras"],
        ["", "", "", ""], ["", "", "", ""], ["", "", "", ""], ["", "", "", ""],
    ], [2.4, 7.4, 3.0, 4.0], pie="Bitácora de trabajo.")
    pendiente(doc, "completar con cada sesión de trabajo (diseño, programación, pruebas, documento)")
    H(doc, "Anexo B. Archivos de entrada de ejemplo", 2)
    P(doc, "**datos/red_ejemplo.txt** (L_{enlaces}):")
    code(doc, "\n".join(f"{u},{v},{w}" for u, v, w in ENLACES) + "\nImpresora1")
    P(doc, "**datos/monitoreo.txt** (líneas validadas con R4):")
    code(doc, "Router1: ok, ok, ok\nServer: ok, timeout, timeout\nDB: timeout, ok, timeout\nSwitch1: ok, lento, ok")
    P(doc, "**datos/red_campus.red**: el archivo de la sección 11.")
    H(doc, "Anexo C. Estructura de la entrega", 2)
    code(doc,
         "Equipo_XX_Proyecto.zip\n"
         "├── 01_Documentacion/   Proyecto_Final.pdf\n"
         "├── 02_Codigo/          main.py, módulos, README.md\n"
         "├── 03_Automatas/       AFN.png, AFD.png, AFD_minimo.png, AP.png, Maquina_estados.png\n"
         "├── 04_Grafos/          Grafo.png\n"
         "├── 05_Pruebas/         casos_prueba\n"
         "├── 06_Presentacion/    Presentacion\n"
         "└── 07_Evidencias/      Bitacora")


def construir():
    figs.generar_todo()
    doc = Document()
    configurar(doc)
    portada(doc)
    indice(doc)
    secciones = [s01_introduccion, s02_problema, s03_objetivo, s04_alcance, s05_solucion, s06_grafos,
                 s07_lenguajes, s08_regex, s09_afn, s10_conversion, s11_gramatica, s12_llc, s13_pila,
                 s14_implementacion, s15_pruebas, s16_resultados, s17_problemas, s18_conclusiones,
                 s19_referencias, s20_anexos]
    for i, seccion in enumerate(secciones):
        # Cada sección inicia en página nueva, salvo las cortas que continúan a la anterior
        Salto.h1 = bool(i) and seccion not in (s03_objetivo, s04_alcance, s12_llc, s19_referencias)
        seccion(doc)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    doc.save(SALIDA)
    print("Documento generado:", SALIDA)


if __name__ == "__main__":
    construir()
