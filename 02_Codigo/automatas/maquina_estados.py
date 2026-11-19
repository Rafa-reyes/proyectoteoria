"""
Procesamiento del monitoreo (secciones 9, 10 y 10.9 del documento).

Cada línea del archivo de monitoreo se valida con R4 (validar_linea_monitoreo)
y su secuencia de eventos se traduce a Σm = {r, l, t}. Después:

  * el AFN y el AFD de falla responden «¿hubo dos timeouts consecutivos?»;
  * la máquina de estados (un AFD completo) responde «¿en qué estado quedó el
    dispositivo?», y ese estado se aplica al grafo: los dispositivos en Falla se
    retiran al recalcular rutas.
"""
from dataclasses import dataclass

from automatas.afd import AFD
from automatas.afn import crear_afn_falla
from automatas.conversion import afn_a_afd
from lenguajes.lexico import validar_linea_monitoreo
from red.grafo import leer_texto, ErrorEntrada

ACTIVO, SOBRECARGADO, FALLA, RECUPERACION = "Activo", "Sobrecargado", "Falla", "Recuperación"

EFECTO_EN_GRAFO = {
    ACTIVO: "Participa normalmente.",
    SOBRECARGADO: "Participa; se marca en el reporte.",
    FALLA: "Se retira del grafo y se recalculan las rutas.",
    RECUPERACION: "Vuelve a participar.",
}


def crear_maquina_estados():
    """AFD completo sobre {r, l, t} (tabla 19 del documento). No tiene estados finales:
    lo que interesa es el estado en el que termina."""
    t = {
        (ACTIVO, "r"): ACTIVO, (ACTIVO, "l"): SOBRECARGADO, (ACTIVO, "t"): SOBRECARGADO,
        (SOBRECARGADO, "r"): ACTIVO, (SOBRECARGADO, "l"): SOBRECARGADO, (SOBRECARGADO, "t"): FALLA,
        (FALLA, "r"): RECUPERACION, (FALLA, "l"): RECUPERACION, (FALLA, "t"): FALLA,
        (RECUPERACION, "r"): ACTIVO, (RECUPERACION, "l"): SOBRECARGADO, (RECUPERACION, "t"): FALLA,
    }
    return AFD([ACTIVO, SOBRECARGADO, FALLA, RECUPERACION], ("r", "l", "t"), t, ACTIVO, set())


# Los tres autómatas se construyen una sola vez. El AFD de falla NO se escribe a
# mano: se obtiene del AFN con la construcción de subconjuntos.
AFN_FALLA = crear_afn_falla()
AFD_FALLA, PASOS_CONVERSION, NOMBRES_CONVERSION = afn_a_afd(AFN_FALLA)
MAQUINA = crear_maquina_estados()


@dataclass
class ResultadoMonitoreo:
    linea: int
    dispositivo: str
    eventos: list
    simbolos: str
    recorrido_afn: object      # ResultadoRecorrido
    recorrido_afd: object
    recorrido_estados: object

    @property
    def falla_detectada(self):
        return self.recorrido_afd.aceptada

    @property
    def estado_final(self):
        return self.recorrido_estados.pasos[-1][1]


def procesar_lineas_monitoreo(lineas):
    """Devuelve (resultados, errores). errores = [(número de línea, texto, motivo)]."""
    resultados, errores = [], []
    for numero, linea in enumerate(lineas, start=1):
        texto = linea.strip()
        if texto == "" or texto.startswith("#"):
            continue
        r = validar_linea_monitoreo(texto)
        if not r.valida:
            errores.append((numero, texto, r.motivo))
            continue
        simbolos = r.datos["simbolos"]
        resultados.append(ResultadoMonitoreo(
            numero, r.datos["dispositivo"], r.datos["eventos"], simbolos,
            AFN_FALLA.procesar(simbolos), AFD_FALLA.procesar(simbolos), MAQUINA.procesar(simbolos)))
    return resultados, errores


def procesar_monitoreo(ruta):
    texto = leer_texto(ruta)
    lineas = texto.splitlines()
    if not any(l.strip() and not l.strip().startswith("#") for l in lineas):
        raise ErrorEntrada(f"el archivo '{ruta}' no contiene eventos de monitoreo")
    return procesar_lineas_monitoreo(lineas)


def aplicar_estados(grafo, resultados):
    """Asigna a cada vértice el estado final de su secuencia.

    Si un dispositivo aparece en varias líneas, cuenta la última. Devuelve la
    lista de advertencias (dispositivos del monitoreo que no están en la red).
    """
    advertencias = []
    for r in resultados:
        if grafo.existe(r.dispositivo):
            grafo.dispositivos[r.dispositivo].estado = r.estado_final
        else:
            advertencias.append(f"Línea {r.linea}: {r.dispositivo} no existe en la red cargada; se ignora")
    return advertencias


def dispositivos_en_falla(grafo):
    return [n for n, d in grafo.dispositivos.items() if d.estado == FALLA]
