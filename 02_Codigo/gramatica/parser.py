"""
Parser descendente recursivo para la gramática G del archivo .red
(secciones 11 y 12 del documento) y validación semántica.

G = (V, Σ, P, S), S = <red>
    1   <red>         → RED id <bloque>
    2   <bloque>      → { <elementos> }
    3   <elementos>   → <elemento> <elementos>
    4   <elementos>   → ε
    5   <elemento>    → <zona>
    6   <elemento>    → <dispositivo>
    7   <elemento>    → <enlace>
    8   <zona>        → ZONA id <bloque>
    9   <dispositivo> → DISPOSITIVO id <tipo> ip ;
    10a-10e <tipo>    → router | switch | pc | servidor | firewall
    11  <enlace>      → ENLACE id id num ;

Hay una función por no terminal. Como G es LL(1), el token actual basta para
elegir la producción, sin retroceso. Cada vez que se aplica una producción se
reescribe el no terminal más a la izquierda de la forma sentencial, de modo que
el parser también construye la DERIVACIÓN POR LA IZQUIERDA paso a paso.
"""
from dataclasses import dataclass, field

from gramatica.automata_pila import AutomataPila
from lenguajes.lexico import tokenizar_config, TIPOS_DISPOSITIVO
from red.grafo import Grafo, leer_texto

PRODUCCIONES = {
    "1": ("<red>", ["RED", "id", "<bloque>"]),
    "2": ("<bloque>", ["{", "<elementos>", "}"]),
    "3": ("<elementos>", ["<elemento>", "<elementos>"]),
    "4": ("<elementos>", []),
    "5": ("<elemento>", ["<zona>"]),
    "6": ("<elemento>", ["<dispositivo>"]),
    "7": ("<elemento>", ["<enlace>"]),
    "8": ("<zona>", ["ZONA", "id", "<bloque>"]),
    "9": ("<dispositivo>", ["DISPOSITIVO", "id", "<tipo>", "ip", ";"]),
    "10a": ("<tipo>", ["router"]),
    "10b": ("<tipo>", ["switch"]),
    "10c": ("<tipo>", ["pc"]),
    "10d": ("<tipo>", ["servidor"]),
    "10e": ("<tipo>", ["firewall"]),
    "11": ("<enlace>", ["ENLACE", "id", "id", "num", ";"]),
}
PRODUCCION_DE_TIPO = {"router": "10a", "switch": "10b", "pc": "10c", "servidor": "10d", "firewall": "10e"}


class ErrorSintactico(Exception):
    def __init__(self, linea, mensaje):
        super().__init__(mensaje)
        self.linea = linea
        self.mensaje = mensaje

    def __str__(self):
        return f"Línea {self.linea}: {self.mensaje}" if self.linea else self.mensaje


# ----------------------------------------------------------------------
# Árbol de la configuración
# ----------------------------------------------------------------------
@dataclass
class DeclDispositivo:
    nombre: str
    tipo: str
    ip: str
    linea: int


@dataclass
class DeclEnlace:
    origen: str
    destino: str
    latencia: int
    linea: int


@dataclass
class Zona:
    nombre: str
    linea: int
    elementos: list = field(default_factory=list)


@dataclass
class Red:
    nombre: str
    elementos: list = field(default_factory=list)


# ----------------------------------------------------------------------
# Parser
# ----------------------------------------------------------------------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.forma = ["<red>"]                          # forma sentencial actual
        self.derivacion = [("<red>", "S")]              # (forma, producción aplicada)

    # -------------------------------------------------- utilidades
    def actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def aplicar(self, numero):
        """Reescribe el no terminal más a la izquierda con la producción indicada.

        "10" (sin letra) se usa cuando los tokens son abstractos y el tipo llega
        como «tipo»: representa cualquiera de las producciones 10a-10e.
        """
        izquierda, derecha = PRODUCCIONES.get(numero, ("<tipo>", ["tipo"]))
        i = next(k for k, s in enumerate(self.forma) if s.startswith("<"))
        assert self.forma[i] == izquierda, "el parser aplicó una producción fuera de orden"
        self.forma[i:i + 1] = derecha
        self.derivacion.append((" ".join(self.forma), numero))

    def consumir(self, tipo, descripcion):
        token = self.actual()
        if token is None:
            ultimo = self.tokens[-1].linea if self.tokens else 0
            raise ErrorSintactico(ultimo, f"el archivo terminó cuando se esperaba {descripcion}")
        if token.tipo != tipo:
            raise ErrorSintactico(token.linea, f"se esperaba {descripcion} y se encontró '{token.lexema}'")
        self.pos += 1
        return token

    # -------------------------------------------------- un método por no terminal
    def parsear(self):
        red = self.red()
        sobrante = self.actual()
        if sobrante is not None:
            raise ErrorSintactico(sobrante.linea,
                                  f"sobra contenido después de cerrar la RED: '{sobrante.lexema}'")
        return red

    def red(self):                                          # 1
        self.aplicar("1")
        self.consumir("RED", "la palabra RED al inicio del archivo")
        nombre = self.consumir("id", "el nombre de la red").lexema
        return Red(nombre, self.bloque())

    def bloque(self):                                       # 2
        self.aplicar("2")
        self.consumir("{", "'{' para abrir el bloque")
        elementos = self.elementos()
        self.consumir("}", "ZONA, DISPOSITIVO, ENLACE o '}'")
        return elementos

    def elementos(self):                                    # 3 y 4
        lista = []
        while True:
            token = self.actual()
            if token is not None and token.tipo in ("ZONA", "DISPOSITIVO", "ENLACE"):
                self.aplicar("3")
                lista.append(self.elemento())
            else:
                self.aplicar("4")                           # <elementos> → ε
                return lista

    def elemento(self):                                     # 5, 6, 7
        tipo = self.actual().tipo
        if tipo == "ZONA":
            self.aplicar("5")
            return self.zona()
        if tipo == "DISPOSITIVO":
            self.aplicar("6")
            return self.dispositivo()
        self.aplicar("7")
        return self.enlace()

    def zona(self):                                         # 8
        self.aplicar("8")
        inicio = self.consumir("ZONA", "ZONA")
        nombre = self.consumir("id", "el nombre de la zona").lexema
        return Zona(nombre, inicio.linea, self.bloque())

    def dispositivo(self):                                  # 9
        self.aplicar("9")
        inicio = self.consumir("DISPOSITIVO", "DISPOSITIVO")
        nombre = self.consumir("id", "el nombre del dispositivo").lexema
        tipo = self.tipo()
        ip = self.consumir("ip", "una dirección IPv4").lexema
        self.consumir(";", "';' al final de la declaración DISPOSITIVO")
        return DeclDispositivo(nombre, tipo, ip, inicio.linea)

    def tipo(self):                                         # 10a - 10e
        token = self.actual()
        if token is None or token.tipo != "tipo":
            encontrado = f"'{token.lexema}'" if token else "el fin del archivo"
            linea = token.linea if token else 0
            raise ErrorSintactico(linea, "se esperaba un tipo de dispositivo ("
                                  + ", ".join(TIPOS_DISPOSITIVO) + f") y se encontró {encontrado}")
        self.aplicar(PRODUCCION_DE_TIPO.get(token.lexema, "10"))
        self.pos += 1
        return token.lexema

    def enlace(self):                                       # 11
        self.aplicar("11")
        inicio = self.consumir("ENLACE", "ENLACE")
        origen = self.consumir("id", "el dispositivo de origen del enlace").lexema
        destino = self.consumir("id", "el dispositivo de destino del enlace").lexema
        lexema = self.consumir("num", "la latencia del enlace (entero de 1 a 9999)").lexema
        latencia = int(lexema) if lexema.isdigit() else None   # None con tokens abstractos
        self.consumir(";", "';' al final de la declaración ENLACE")
        return DeclEnlace(origen, destino, latencia, inicio.linea)


# ----------------------------------------------------------------------
# Validación semántica (lo que la gramática no puede expresar)
# ----------------------------------------------------------------------
def analizar_semantica(red):
    """Recorre el árbol en orden. Devuelve (grafo, errores, advertencias).

    Reglas dependientes del contexto:
      * un ENLACE solo puede usar dispositivos declarados antes;
      * no se repiten nombres de dispositivo ni direcciones IP;
      * un enlace no conecta un dispositivo consigo mismo.
    """
    grafo = Grafo()
    errores, advertencias = [], []
    declarados, ips = {}, {}

    def recorrer(elementos, ruta_zona):
        for e in elementos:
            if isinstance(e, Zona):
                recorrer(e.elementos, f"{ruta_zona}/{e.nombre}")
            elif isinstance(e, DeclDispositivo):
                if e.nombre in declarados:
                    errores.append(f"Línea {e.linea}: el dispositivo '{e.nombre}' ya fue declarado "
                                   f"en la línea {declarados[e.nombre].linea}")
                    continue
                if e.ip in ips:
                    errores.append(f"Línea {e.linea}: la IP {e.ip} ya está asignada a '{ips[e.ip]}'")
                declarados[e.nombre] = e
                ips.setdefault(e.ip, e.nombre)
                grafo.agregar_dispositivo(e.nombre, e.tipo, e.ip, ruta_zona)
            else:  # DeclEnlace
                faltantes = [n for n in (e.origen, e.destino) if n not in declarados]
                if faltantes:
                    for n in faltantes:
                        errores.append(f"Línea {e.linea}: el dispositivo '{n}' no fue declarado "
                                       "antes de usarse en un ENLACE")
                    continue
                if e.origen == e.destino:
                    errores.append(f"Línea {e.linea}: un dispositivo no puede enlazarse consigo mismo "
                                   f"({e.origen})")
                    continue
                aviso = grafo.agregar_enlace(e.origen, e.destino, e.latencia)
                if aviso:
                    advertencias.append(f"Línea {e.linea}: {aviso}")

    recorrer(red.elementos, red.nombre)
    return grafo, errores, advertencias


# ----------------------------------------------------------------------
# Análisis completo de un archivo .red
# ----------------------------------------------------------------------
@dataclass
class ResultadoConfiguracion:
    tokens: list = field(default_factory=list)
    errores_lexicos: list = field(default_factory=list)
    resultado_pila: object = None
    red: Red = None
    derivacion: list = field(default_factory=list)
    error_sintactico: ErrorSintactico = None
    errores_semanticos: list = field(default_factory=list)
    advertencias: list = field(default_factory=list)
    grafo: Grafo = None

    @property
    def valida(self):
        return (not self.errores_lexicos and self.resultado_pila is not None
                and self.resultado_pila.aceptada and self.error_sintactico is None
                and not self.errores_semanticos)


def analizar_configuracion(texto):
    """Léxico (regex) -> autómata de pila -> parser (gramática) -> semántica -> grafo."""
    resultado = ResultadoConfiguracion()
    resultado.tokens, resultado.errores_lexicos = tokenizar_config(texto)
    if resultado.errores_lexicos:
        return resultado
    if not resultado.tokens:
        resultado.error_sintactico = ErrorSintactico(0, "el archivo no contiene ninguna declaración")
        return resultado

    resultado.resultado_pila = AutomataPila().procesar(resultado.tokens)

    parser = Parser(resultado.tokens)
    try:
        resultado.red = parser.parsear()
    except ErrorSintactico as e:
        resultado.error_sintactico = e
    resultado.derivacion = parser.derivacion

    # El AP y el parser reconocen el mismo lenguaje de tokens: deben coincidir.
    if resultado.resultado_pila.aceptada != (resultado.error_sintactico is None):
        raise RuntimeError("el autómata de pila y el parser no coinciden; revisar la implementación")

    if resultado.red is not None:
        grafo, errores, advertencias = analizar_semantica(resultado.red)
        resultado.errores_semanticos, resultado.advertencias = errores, advertencias
        if not errores:
            resultado.grafo = grafo
    return resultado


def analizar_archivo_config(ruta):
    return analizar_configuracion(leer_texto(ruta))
