"""
Casos de prueba del sistema completo (sección 15 del documento, P01-P22).

Cada caso ejecuta el programa por sus módulos y devuelve (resultado_obtenido, correcto).
Los usan tests/test_sistema.py (pytest) y ejecutar_casos_prueba.py (tabla de 05_Pruebas).
"""
from pathlib import Path

from automatas.maquina_estados import procesar_lineas_monitoreo, aplicar_estados, dispositivos_en_falla
from gramatica.parser import analizar_archivo_config
from main import Aplicacion
from red import algoritmos as alg
from red.grafo import cargar_desde_archivo, cargar_desde_lineas, ErrorEntrada

DATOS = Path(__file__).resolve().parent.parent / "datos"


def relativo(mensaje):
    """Quita la ruta absoluta del equipo de los mensajes (la tabla se entrega)."""
    return mensaje.replace(str(DATOS), "datos")


def red_ejemplo():
    return cargar_desde_archivo(DATOS / "red_ejemplo.txt").grafo


def p01():
    r = cargar_desde_archivo(DATOS / "red_ejemplo.txt")
    g = r.grafo
    obtenido = f"{g.num_vertices()} dispositivos, {r.enlaces_cargados} enlaces cargados"
    return obtenido, g.num_vertices() == 8 and r.enlaces_cargados == 7 and not r.rechazadas


def p02():
    camino, costo = alg.ruta_mas_corta(red_ejemplo(), "Router1", "DB")
    return f"{'→'.join(camino)}, {costo} ms", camino == ["Router1", "Switch2", "Server", "DB"] and costo == 6


def p03():
    camino = alg.existe_ruta(red_ejemplo(), "PC1", "Impresora1")
    return ("No existe ruta" if camino is None else "→".join(camino)), camino is None


def p04():
    art, puentes = alg.puntos_criticos(red_ejemplo())
    obtenido = f"Articulación: {', '.join(art)}; puente: {', '.join(f'{u}–{v}' for u, v in puentes)}"
    return obtenido, art == ["Switch1"] and puentes == [("Switch1", "PC1")]


def p05():
    ciclos = alg.detectar_ciclos(red_ejemplo())
    obtenido = "; ".join("–".join(c) for c in ciclos)
    esperado = ["Router1", "Switch1", "PC2", "DB", "Server", "Switch2", "Router1"]
    return obtenido, ciclos == [esperado]


def p06():
    g = red_ejemplo()
    grados = alg.grados(g)
    maximo = max(grados, key=grados.get)
    obtenido = f"{maximo} = {grados[maximo]} (máximo); aislados: {', '.join(alg.aislados(g))}"
    return obtenido, maximo == "Switch1" and grados[maximo] == 3 and alg.aislados(g) == ["Impresora1"]


def _linea_rechazada(texto, fragmento):
    r = cargar_desde_lineas([texto])
    rechazada = r.rechazadas[0].mensaje if r.rechazadas else ""
    return (f"Rechazada: {rechazada}" if rechazada else "Aceptada"), fragmento in rechazada


def p07():
    return _linea_rechazada("Router1;Switch1", "separador ';'")


def p08():
    return _linea_rechazada("Router1,Switch1,0", "entre 1 y 9999")


def p09():
    try:
        cargar_desde_archivo(DATOS / "invalidos" / "vacio.txt")
    except ErrorEntrada as e:
        return f"Mensaje: {relativo(str(e))}", "no contiene dispositivos" in str(e)
    return "Se cargó sin error", False


def p10():
    g = cargar_desde_archivo(DATOS / "invalidos" / "un_dispositivo.txt").grafo
    obtenido = f"{g.num_vertices()} vértice, {g.num_aristas()} aristas, aislados: {', '.join(alg.aislados(g))}"
    return obtenido, g.num_vertices() == 1 and g.num_aristas() == 0 and alg.aislados(g) == ["Impresora1"]


def p11():
    r20 = cargar_desde_lineas(["A" * 20 + ",PC1"])
    r21 = cargar_desde_lineas(["A" * 21 + ",PC1"])
    ok20, ok21 = not r20.rechazadas, not r21.rechazadas
    obtenido = f"20: {'aceptado' if ok20 else 'rechazado'} · 21: {'aceptado' if ok21 else 'rechazado'}"
    return obtenido, ok20 and not ok21


def p12():
    return _linea_rechazada("PC1,PC1", "consigo mismo")


def p13():
    r = cargar_desde_archivo(DATOS / "invalidos" / "enlace_duplicado.txt")
    avisos = [l.mensaje for l in r.advertencias]
    obtenido = f"Advertencia: {avisos[0]}" if avisos else "Sin advertencia"
    return obtenido, bool(avisos) and r.grafo.latencia("PC1", "Switch1") == 1


def p14():
    g = red_ejemplo()
    resultados, _ = procesar_lineas_monitoreo(["Server: ok, timeout, timeout"])
    r = resultados[0]
    aplicar_estados(g, resultados)
    camino, costo = alg.ruta_mas_corta(g.subgrafo_sin(dispositivos_en_falla(g)), "Router1", "DB")
    obtenido = (f"AFN {'acepta' if r.recorrido_afn.aceptada else 'rechaza'}, AFD "
                f"{'acepta' if r.recorrido_afd.aceptada else 'rechaza'}; Server → {r.estado_final}; "
                f"Router1→DB = {costo} ms")
    return obtenido, (r.recorrido_afn.aceptada and r.recorrido_afd.aceptada
                      and r.estado_final == "Falla" and costo == 7)


def p15():
    r = procesar_lineas_monitoreo(["DB: timeout, ok, timeout"])[0][0]
    obtenido = (f"AFN {'acepta' if r.recorrido_afn.aceptada else 'rechaza'}, AFD "
                f"{'acepta' if r.recorrido_afd.aceptada else 'rechaza'}; DB → {r.estado_final}")
    return obtenido, (not r.recorrido_afn.aceptada and not r.recorrido_afd.aceptada
                      and r.estado_final == "Sobrecargado")


def p16():
    resultados, errores = procesar_lineas_monitoreo(["PC1: ping"])
    obtenido = f"Error léxico: {errores[0][2]}" if errores else "Aceptada"
    return obtenido, not resultados and bool(errores) and "ping" in errores[0][2]


def p17():
    c = analizar_archivo_config(DATOS / "red_campus.red")
    ap = c.resultado_pila
    obtenido = (f"AP {'acepta' if ap.aceptada else 'rechaza'}; profundidad máxima {ap.profundidad_maxima}; "
                f"grafo con {c.grafo.num_vertices() if c.grafo else 0} dispositivos")
    return obtenido, c.valida and ap.aceptada and ap.profundidad_maxima == 3 and c.grafo.num_vertices() == 4


def p18():
    c = analizar_archivo_config(DATOS / "invalidos" / "zona_sin_cerrar.red")
    ap = c.resultado_pila
    pila_final = ap.pasos[-1].pila
    obtenido = f"AP rechaza: termina con pila {pila_final}"
    return obtenido, (not ap.aceptada and pila_final == "Z[datacenter] R[campus] Z0"
                      and "ZONA 'datacenter'" in ap.motivo)


def p19():
    c = analizar_archivo_config(DATOS / "invalidos" / "tipo_invalido.red")
    e = c.error_sintactico
    return (f"Error sintáctico: {e}" if e else "Sin error"), e is not None and "tipo de dispositivo" in str(e)


def p20():
    c = analizar_archivo_config(DATOS / "invalidos" / "enlace_no_declarado.red")
    errores = c.errores_semanticos
    return (f"Error semántico: {errores[0]}" if errores else "Sin error"), bool(errores) and "'X'" in errores[0]


def p21():
    camino, costo = alg.ruta_mas_corta(red_ejemplo(), "PC1", "PC1")
    return f"Ruta {'→'.join(camino)}, {costo} ms", camino == ["PC1"] and costo == 0


def p22():
    try:
        cargar_desde_archivo(DATOS / "no_existe.txt")
        mensaje = "sin error"
    except ErrorEntrada as e:
        mensaje = relativo(str(e))
    opcion_valida = Aplicacion(interactiva=False).es_opcion_valida("abc")
    obtenido = f"Mensaje: {mensaje}; opción «abc» {'aceptada' if opcion_valida else 'rechazada'}"
    return obtenido, "no existe" in mensaje and not opcion_valida


# (id, entrada, categoría, resultado esperado, función) — igual que la Tabla 27 del documento
CASOS = [
    ("P01", "Cargar red_ejemplo.txt", "Válida / normal", "8 dispositivos, 7 enlaces cargados", p01),
    ("P02", "Ruta más corta Router1 → DB", "Válida / normal", "Router1→Switch2→Server→DB, 6 ms", p02),
    ("P03", "¿Existe ruta PC1 → Impresora1?", "Válida / normal", "No existe ruta (componentes distintas)", p03),
    ("P04", "Puntos críticos de la red de ejemplo", "Válida / normal", "Articulación: Switch1; puente: Switch1–PC1", p04),
    ("P05", "Detectar ciclos", "Válida / normal", "Ciclo Router1–Switch1–PC2–DB–Server–Switch2–Router1", p05),
    ("P06", "Grados y aislados", "Válida / normal", "Switch1 = 3 (máximo); Impresora1 aislado", p06),
    ("P07", "Línea «Router1;Switch1»", "Inválida", "Rechazada: separador no válido (línea indicada)", p07),
    ("P08", "Línea «Router1,Switch1,0»", "Inválida", "Rechazada: latencia fuera de rango", p08),
    ("P09", "Archivo vacío", "Límite", "Mensaje: el archivo no contiene dispositivos", p09),
    ("P10", "Archivo con un solo dispositivo «Impresora1»", "Límite", "Grafo de 1 vértice, 0 aristas, aislado", p10),
    ("P11", "Nombre de exactamente 20 caracteres / de 21", "Límite", "20: aceptado · 21: rechazado", p11),
    ("P12", "Lazo «PC1,PC1»", "Inesperada", "Rechazada: enlace consigo mismo", p12),
    ("P13", "Enlace duplicado «PC1,Switch1» dos veces", "Inesperada", "Advertencia; se conserva el primero", p13),
    ("P14", "Monitoreo «Server: ok, timeout, timeout»", "Válida / normal",
     "AFN y AFD aceptan; Server → Falla; Router1→DB = 7 ms", p14),
    ("P15", "Monitoreo «DB: timeout, ok, timeout»", "Válida / normal", "AFN y AFD rechazan; DB → Sobrecargado", p15),
    ("P16", "Monitoreo «PC1: ping»", "Inválida", "Error léxico: evento desconocido «ping»", p16),
    ("P17", "Archivo .red con zonas anidadas (3 niveles)", "Válida / normal",
     "AP acepta; profundidad máxima de pila 3; grafo construido", p17),
    ("P18", ".red con una ZONA sin cerrar", "Inválida", "AP rechaza: termina con pila Z R Z0; indica la zona", p18),
    ("P19", ".red con tipo «modem»", "Inválida", "Error sintáctico: se esperaba un tipo de dispositivo", p19),
    ("P20", ".red con ENLACE a dispositivo no declarado", "Inválida", "Error semántico: «X» no fue declarado", p20),
    ("P21", "Ruta más corta entre un nodo y él mismo", "Límite", "Ruta de 0 ms con un solo vértice", p21),
    ("P22", "Archivo inexistente / opción de menú «abc»", "Inesperada", "Mensaje claro, el programa no se cierra", p22),
]
