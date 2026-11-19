"""
Estructura de datos del grafo de la red (sección 6 del documento).

Grafo simple, no dirigido y ponderado, guardado como LISTA DE ADYACENCIA:

    adyacencia = {"Router1": {"Switch1": 2, "Switch2": 3}, "Switch1": {"Router1": 2, ...}, ...}

Cada enlace {u, v} se guarda dos veces (u -> v y v -> u) porque el grafo es no
dirigido; la matriz de adyacencia se calcula a partir de esta lista.
"""
from dataclasses import dataclass
from pathlib import Path

from lenguajes.lexico import validar_linea_enlace

ESTADOS_DISPOSITIVO = ("Activo", "Sobrecargado", "Falla", "Recuperación")


class ErrorEntrada(Exception):
    """Error en los datos de entrada; el mensaje se muestra tal cual al usuario."""


@dataclass
class Dispositivo:
    """Atributos de un vértice."""
    nombre: str
    tipo: str = "sin tipo"
    ip: str = ""
    zona: str = ""
    estado: str = "Activo"


class Grafo:
    def __init__(self):
        self.dispositivos = {}   # nombre -> Dispositivo   (conjunto V con atributos)
        self.adyacencia = {}     # nombre -> {vecino: latencia}

    # ------------------------------------------------------------ altas
    def agregar_dispositivo(self, nombre, tipo=None, ip=None, zona=None):
        """Agrega un vértice. Si ya existe, solo completa sus atributos."""
        if nombre not in self.dispositivos:
            self.dispositivos[nombre] = Dispositivo(nombre)
            self.adyacencia[nombre] = {}
        disp = self.dispositivos[nombre]
        if tipo:
            disp.tipo = tipo
        if ip:
            disp.ip = ip
        if zona:
            disp.zona = zona
        return disp

    def agregar_enlace(self, origen, destino, latencia=1):
        """Agrega la arista {origen, destino} con su latencia.

        Devuelve "" si se agregó o un texto de advertencia si era duplicada
        (se conserva la primera). Lanza ErrorEntrada si es un lazo o la latencia
        no es positiva, porque el grafo es simple y Dijkstra requiere pesos > 0.
        """
        if origen == destino:
            raise ErrorEntrada(f"un dispositivo no puede enlazarse consigo mismo ({origen})")
        if latencia < 1:
            raise ErrorEntrada("la latencia debe ser un entero positivo")
        self.agregar_dispositivo(origen)
        self.agregar_dispositivo(destino)
        if destino in self.adyacencia[origen]:
            return (f"enlace duplicado {origen}–{destino}: se conserva el primero "
                    f"({self.adyacencia[origen][destino]} ms)")
        self.adyacencia[origen][destino] = latencia
        self.adyacencia[destino][origen] = latencia
        return ""

    # ------------------------------------------------------------ consultas
    def existe(self, nombre):
        return nombre in self.dispositivos

    def vertices(self):
        return list(self.dispositivos)

    def vecinos(self, nombre):
        return self.adyacencia[nombre]

    def grado(self, nombre):
        return len(self.adyacencia[nombre])

    def latencia(self, u, v):
        return self.adyacencia[u].get(v)

    def aristas(self):
        """Lista de (u, v, latencia) con cada arista una sola vez."""
        vistas, resultado = set(), []
        for u, vecinos in self.adyacencia.items():
            for v, w in vecinos.items():
                if (v, u) not in vistas:
                    vistas.add((u, v))
                    resultado.append((u, v, w))
        return resultado

    def num_vertices(self):
        return len(self.dispositivos)

    def num_aristas(self):
        return sum(len(v) for v in self.adyacencia.values()) // 2

    def matriz_adyacencia(self):
        """Devuelve (orden_de_vertices, matriz) con la latencia o 0 si no hay enlace."""
        orden = self.vertices()
        matriz = [[self.adyacencia[u].get(v, 0) for v in orden] for u in orden]
        return orden, matriz

    def subgrafo_sin(self, excluidos):
        """Copia del grafo sin los vértices indicados (y sin sus aristas)."""
        excluidos = set(excluidos)
        nuevo = Grafo()
        for nombre, d in self.dispositivos.items():
            if nombre not in excluidos:
                copia = nuevo.agregar_dispositivo(nombre, d.tipo, d.ip, d.zona)
                copia.estado = d.estado
        for u, v, w in self.aristas():
            if u not in excluidos and v not in excluidos:
                nuevo.agregar_enlace(u, v, w)
        return nuevo


# ----------------------------------------------------------------------
# Carga desde texto (archivo .txt o teclado)
# ----------------------------------------------------------------------
@dataclass
class LineaProcesada:
    numero: int
    texto: str
    valida: bool
    mensaje: str = ""        # motivo del rechazo, o advertencia si fue válida


class ResultadoCarga:
    def __init__(self, grafo):
        self.grafo = grafo
        self.lineas = []          # lista de LineaProcesada
        self.enlaces_cargados = 0

    @property
    def rechazadas(self):
        return [l for l in self.lineas if not l.valida]

    @property
    def advertencias(self):
        return [l for l in self.lineas if l.valida and l.mensaje]


def procesar_linea_enlace(grafo, texto, numero, resultado):
    """Valida una línea con L_enlaces (R1/R2) y, si es válida, la agrega al grafo."""
    r = validar_linea_enlace(texto)
    if not r.valida:
        resultado.lineas.append(LineaProcesada(numero, texto, False, r.motivo))
        return
    origen, destino, latencia = r.datos["origen"], r.datos["destino"], r.datos["latencia"]
    if destino is None:
        nuevo = not grafo.existe(origen)
        grafo.agregar_dispositivo(origen)
        aviso = "" if nuevo else f"el dispositivo {origen} ya existía"
        resultado.lineas.append(LineaProcesada(numero, texto, True, aviso))
        return
    aviso = grafo.agregar_enlace(origen, destino, latencia)
    if not aviso:
        resultado.enlaces_cargados += 1
    resultado.lineas.append(LineaProcesada(numero, texto, True, aviso))


def cargar_desde_lineas(lineas, grafo=None):
    """Construye (o amplía) un grafo a partir de líneas de texto.

    Las líneas vacías y las que inician con '#' (comentarios) se ignoran.
    """
    grafo = grafo if grafo is not None else Grafo()
    resultado = ResultadoCarga(grafo)
    for numero, linea in enumerate(lineas, start=1):
        texto = linea.strip()
        if texto == "" or texto.startswith("#"):
            continue
        procesar_linea_enlace(grafo, texto, numero, resultado)
    return resultado


def leer_texto(ruta):
    """Lee un archivo de texto con mensajes de error comprensibles."""
    p = Path(ruta)
    if not p.exists():
        raise ErrorEntrada(f"el archivo '{ruta}' no existe")
    if p.is_dir():
        raise ErrorEntrada(f"'{ruta}' es una carpeta, no un archivo")
    try:
        return p.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raise ErrorEntrada(f"el archivo '{ruta}' no es un archivo de texto UTF-8") from None
    except OSError as e:
        raise ErrorEntrada(f"no se pudo leer '{ruta}': {e.strerror}") from None


def cargar_desde_archivo(ruta):
    """Carga un archivo de topología (.txt). Usa validar_linea_enlace() en cada línea."""
    texto = leer_texto(ruta)
    lineas = texto.splitlines()
    if not any(l.strip() and not l.strip().startswith("#") for l in lineas):
        raise ErrorEntrada(f"el archivo '{ruta}' no contiene dispositivos")
    return cargar_desde_lineas(lineas)
