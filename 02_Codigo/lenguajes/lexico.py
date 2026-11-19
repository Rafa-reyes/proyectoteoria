"""
Analizador léxico de Network Graph Analyzer.

Implementa las cuatro expresiones regulares del documento (sección 8):

    R1  nombre de dispositivo          -> validar_nombre()
    R2  línea de enlace (topología)    -> validar_linea_enlace()
    R3  dirección IPv4                 -> tokenizar_config() (token ip)
    R4  línea de monitoreo             -> validar_linea_monitoreo()

y el tokenizador del archivo de configuración .red, que entrega la secuencia
de tokens que procesan el autómata de pila y el parser.

Las expresiones se construyen a partir de las definiciones formales de la
sección 7.2 (ID, PESO), por eso se arman con f-strings y no se escriben
"a mano" cuatro veces.
"""
import re
from dataclasses import dataclass, field

# ----------------------------------------------------------------------
# Definiciones base (sección 7.2)
# ----------------------------------------------------------------------
# ID = Letra · (Letra ∪ Dígito ∪ {_, -})^k , 0 <= k <= 19   -> de 1 a 20 símbolos
ID = "[A-Za-z][A-Za-z0-9_-]{0,19}"
# PESO = (Dígito − {0}) · Dígito^k , 0 <= k <= 3          -> de 1 a 9999
PESO = "[1-9][0-9]{0,3}"
# Un octeto IPv4 dividido en casos para limitarlo a 0-255 sin ceros a la izquierda
OCTETO = r"(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"

# ----------------------------------------------------------------------
# Expresiones regulares R1 - R4
# ----------------------------------------------------------------------
R1_NOMBRE = f"^{ID}$"
R2_ENLACE = rf"^\s*({ID})\s*,\s*({ID})\s*(?:,\s*({PESO}))?\s*$"
R3_IPV4 = rf"^({OCTETO}\.){{3}}{OCTETO}$"
R4_MONITOREO = rf"^\s*({ID})\s*:\s*((?:ok|lento|timeout)(?:\s*,\s*(?:ok|lento|timeout))*)\s*$"

REGEX_NOMBRE = re.compile(R1_NOMBRE)
REGEX_ENLACE = re.compile(R2_ENLACE)
REGEX_IPV4 = re.compile(R3_IPV4)
REGEX_MONITOREO = re.compile(R4_MONITOREO)
REGEX_PESO = re.compile(f"^{PESO}$")

LONGITUD_MAXIMA_NOMBRE = 20
LATENCIA_MAXIMA = 9999

# Alfabeto Σ de las líneas de topología: letras, dígitos, '_', '-', ',' y espacio.
SIMBOLOS_EXTRA_TOPOLOGIA = set("_-, \t")

# Traducción de eventos de monitoreo al alfabeto Σm = {r, l, t} del AFN/AFD
EVENTO_A_SIMBOLO = {"ok": "r", "lento": "l", "timeout": "t"}


@dataclass
class ResultadoLinea:
    """Resultado de validar una línea: si es válida, sus datos; si no, el motivo."""
    valida: bool
    motivo: str = ""
    datos: dict = field(default_factory=dict)


# ----------------------------------------------------------------------
# R1 · Nombre de dispositivo
# ----------------------------------------------------------------------
def validar_nombre(nombre):
    """Aplica R1. Devuelve (True, "") o (False, motivo comprensible)."""
    # fullmatch y no match: con match, "Router1\n" sería aceptado porque $
    # también coincide antes de un salto de línea final.
    if REGEX_NOMBRE.fullmatch(nombre):
        return True, ""
    return False, diagnosticar_nombre(nombre)


def diagnosticar_nombre(nombre):
    """Explica por qué una cadena no pertenece al lenguaje de R1."""
    if nombre == "":
        return "el nombre está vacío"
    if not re.fullmatch("[A-Za-z]", nombre[0]):
        return f"un nombre debe iniciar con una letra y '{nombre}' inicia con '{nombre[0]}'"
    if any(c.isspace() for c in nombre):
        return f"un nombre no puede contener espacios ('{nombre}')"
    for c in nombre:
        if not re.fullmatch("[A-Za-z0-9_-]", c):
            return f"el símbolo '{c}' no está permitido en un nombre (solo letras, dígitos, '_' y '-')"
    if len(nombre) > LONGITUD_MAXIMA_NOMBRE:
        return (f"el nombre '{nombre}' tiene {len(nombre)} símbolos; "
                f"el máximo es {LONGITUD_MAXIMA_NOMBRE}")
    return f"'{nombre}' no es un nombre válido"


# ----------------------------------------------------------------------
# R2 · Línea de enlace  (lenguaje L_enlaces, sección 7.2)
# ----------------------------------------------------------------------
def validar_linea_enlace(linea):
    """Valida una línea del archivo de topología.

    Formas válidas (L_enlaces):
        x               dispositivo sin enlaces           (R1)
        x,y             enlace con latencia 1 por omisión (R2)
        x,y,p           enlace con latencia p             (R2)
    con la condición semántica x != y.
    datos = {"origen", "destino" (o None), "latencia" (o None)}
    """
    texto = linea.strip()
    if texto == "":
        return ResultadoLinea(False, "la línea está vacía")

    # Caso 1: un solo identificador -> dispositivo aislado
    if REGEX_NOMBRE.fullmatch(texto):
        return ResultadoLinea(True, datos={"origen": texto, "destino": None, "latencia": None})

    # Caso 2: línea de enlace con R2
    coincidencia = REGEX_ENLACE.fullmatch(texto)
    if coincidencia:
        origen, destino, peso = coincidencia.groups()
        if origen == destino:  # condición x != y (no expresable con la regex)
            return ResultadoLinea(False, f"un dispositivo no puede enlazarse consigo mismo ({origen})")
        latencia = int(peso) if peso else 1
        return ResultadoLinea(True, datos={"origen": origen, "destino": destino, "latencia": latencia})

    return ResultadoLinea(False, diagnosticar_enlace(texto))


def diagnosticar_enlace(texto):
    """Explica por qué una línea no pertenece a L_enlaces, señalando el campo que falla."""
    # 1) símbolos fuera del alfabeto Σ
    for c in texto:
        if not (c.isascii() and c.isalnum()) and c not in SIMBOLOS_EXTRA_TOPOLOGIA:
            if c in ";:|":
                return f"el separador '{c}' no pertenece al alfabeto; se esperaba ','"
            if c == ".":
                return "el símbolo '.' no pertenece al alfabeto: la latencia debe ser un número entero"
            return f"el símbolo '{c}' no pertenece al alfabeto"

    campos = [c.strip() for c in texto.split(",")]
    # 2) número de campos
    if len(campos) > 3:
        return f"la línea tiene {len(campos)} campos; el máximo es 3 (origen,destino,latencia)"

    # 3) origen y destino deben cumplir R1
    for posicion, campo in zip(("origen", "destino"), campos[:2]):
        if campo == "":
            if posicion == "destino":
                return "falta el dispositivo de destino después de la coma"
            return "falta el dispositivo de origen antes de la coma"
        ok, motivo = validar_nombre(campo)
        if not ok:
            return f"dispositivo de {posicion}: {motivo}"

    # 4) latencia: PESO = (Dígito − {0}) · Dígito^k
    if len(campos) == 3:
        return diagnosticar_latencia(campos[2])
    return "la línea no tiene la forma origen,destino[,latencia]"


def diagnosticar_latencia(campo):
    if campo == "":
        return "falta la latencia después de la segunda coma"
    if campo.startswith("-"):
        return "la latencia no puede ser negativa; debe ser un entero entre 1 y 9999"
    if not campo.isdigit():
        return f"la latencia '{campo}' no es un número entero entre 1 y 9999"
    if int(campo) == 0:
        return "la latencia debe ser un entero entre 1 y 9999 (se recibió 0)"
    if campo.startswith("0"):
        return f"la latencia '{campo}' no puede tener ceros a la izquierda"
    if len(campo) > 4:
        return f"la latencia debe ser un entero entre 1 y 9999 (se recibió {campo})"
    return f"la latencia '{campo}' no es válida"


# ----------------------------------------------------------------------
# R4 · Línea de monitoreo
# ----------------------------------------------------------------------
def validar_linea_monitoreo(linea):
    """Valida «Dispositivo: evento, evento, ...».

    datos = {"dispositivo", "eventos" (lista), "simbolos" (cadena sobre {r, l, t})}
    """
    texto = linea.strip()
    coincidencia = REGEX_MONITOREO.fullmatch(texto)
    if coincidencia:
        dispositivo, lista = coincidencia.groups()
        eventos = [e.strip() for e in lista.split(",")]
        return ResultadoLinea(True, datos={"dispositivo": dispositivo, "eventos": eventos,
                                           "simbolos": traducir_eventos(eventos)})
    return ResultadoLinea(False, diagnosticar_monitoreo(texto))


def diagnosticar_monitoreo(texto):
    if ":" not in texto:
        return "falta ':' entre el dispositivo y la lista de eventos (formato: Dispositivo: ok, lento, timeout)"
    nombre, resto = texto.split(":", 1)
    ok, motivo = validar_nombre(nombre.strip())
    if not ok:
        return f"dispositivo: {motivo}"
    if resto.strip() == "":
        return "la lista de eventos está vacía"
    for evento in resto.split(","):
        evento = evento.strip()
        if evento == "":
            return "hay un evento vacío entre dos comas"
        if evento not in EVENTO_A_SIMBOLO:
            return f"evento desconocido '{evento}'; los eventos válidos son ok, lento y timeout"
    return "la línea no tiene la forma Dispositivo: evento, evento, ..."


def traducir_eventos(eventos):
    """ok -> r, lento -> l, timeout -> t. Devuelve la cadena para el AFN/AFD."""
    return "".join(EVENTO_A_SIMBOLO[e] for e in eventos)


# ----------------------------------------------------------------------
# Tokenizador del archivo de configuración .red
# ----------------------------------------------------------------------
PALABRAS_RESERVADAS = ("RED", "ZONA", "DISPOSITIVO", "ENLACE")
TIPOS_DISPOSITIVO = ("router", "switch", "pc", "servidor", "firewall")
SIMBOLOS = ("{", "}", ";")

# Un lexema es una llave, un punto y coma, o una secuencia sin espacios ni esos símbolos.
_LEXEMA = re.compile(r"[{};]|[^\s{};]+")


@dataclass
class Token:
    tipo: str      # RED, ZONA, DISPOSITIVO, ENLACE, id, tipo, ip, num, {, }, ;
    lexema: str
    linea: int = 0

    def __str__(self):
        return self.tipo


@dataclass
class ErrorLexico:
    linea: int
    lexema: str
    motivo: str

    def __str__(self):
        return f"Línea {self.linea}: {self.motivo}"


def clasificar_lexema(lexema):
    """Devuelve (tipo_de_token, "") o (None, motivo del error léxico).

    El orden importa: primero palabras reservadas y tipos (que también
    cumplirían R1), después IP (R3), número (PESO) e identificador (R1).
    """
    if lexema in SIMBOLOS or lexema in PALABRAS_RESERVADAS:
        return lexema, ""
    if lexema in TIPOS_DISPOSITIVO:
        return "tipo", ""
    if REGEX_IPV4.fullmatch(lexema):
        return "ip", ""
    if REGEX_PESO.fullmatch(lexema):
        return "num", ""
    if REGEX_NOMBRE.fullmatch(lexema):
        return "id", ""
    # Diagnóstico del error léxico
    if re.fullmatch(r"[0-9.]+", lexema) and "." in lexema:
        return None, (f"'{lexema}' no es una dirección IPv4 válida "
                      "(cuatro octetos de 0 a 255 sin ceros a la izquierda)")
    if lexema.isdigit():
        return None, f"'{lexema}' no es una latencia válida (entero de 1 a 9999 sin ceros a la izquierda)"
    return None, f"lexema no reconocido: {diagnosticar_nombre(lexema)}"


def tokenizar_config(texto):
    """Convierte el texto de un archivo .red en tokens.

    Devuelve (tokens, errores_lexicos). Lo que sigue a '#' en una línea es comentario.
    """
    tokens, errores = [], []
    for numero, linea in enumerate(texto.splitlines(), start=1):
        linea = linea.split("#", 1)[0]
        for m in _LEXEMA.finditer(linea):
            lexema = m.group()
            tipo, motivo = clasificar_lexema(lexema)
            if tipo is None:
                errores.append(ErrorLexico(numero, lexema, motivo))
            else:
                tokens.append(Token(tipo, lexema, numero))
    return tokens, errores
