"""Pruebas de la gramática, el parser y el autómata de pila (secciones 11 a 13)."""
import pytest

from gramatica.automata_pila import AutomataPila
from gramatica.parser import Parser, ErrorSintactico, analizar_configuracion
from lenguajes.lexico import Token


TIPOS = ("router", "switch", "pc", "servidor", "firewall")


def tokens(texto):
    """Tokens abstractos; router, servidor... llegan como token 'tipo' con su lexema."""
    return [Token("tipo", t, 0) if t in TIPOS else Token(t, t, 0) for t in texto.split()]


def derivar(texto):
    p = Parser(tokens(texto))
    p.parsear()
    return p.derivacion


# Derivaciones D1-D5 del documento (forma final y producciones aplicadas)
DERIVACIONES = [
    ("RED id { }", ["1", "2", "4"]),
    ("RED id { DISPOSITIVO id router ip ; }", ["1", "2", "3", "6", "9", "10a", "4"]),
    ("RED id { ENLACE id id num ; }", ["1", "2", "3", "7", "11", "4"]),
    ("RED id { ZONA id { } }", ["1", "2", "3", "5", "8", "2", "4", "4"]),
    ("RED id { DISPOSITIVO id servidor ip ; ZONA id { ENLACE id id num ; } }",
     ["1", "2", "3", "6", "9", "10d", "3", "5", "8", "2", "3", "7", "11", "4", "4"]),
]


@pytest.mark.parametrize("cadena,producciones", DERIVACIONES)
def test_derivaciones_por_la_izquierda(cadena, producciones):
    derivacion = derivar(cadena)
    assert [p for _, p in derivacion[1:]] == producciones
    assert derivacion[-1][0] == cadena


@pytest.mark.parametrize("cadena", ["ZONA id { }", "RED id { ZONA id { }", "RED id { ENLACE id id ; }",
                                    "RED id { DISPOSITIVO id id ip ; }", "RED id { } RED id { }"])
def test_cadenas_que_no_pueden_generarse(cadena):
    with pytest.raises(ErrorSintactico):
        Parser(tokens(cadena)).parsear()


def test_derivacion_con_tipo_abstracto():
    d = derivar("RED id { DISPOSITIVO id tipo ip ; }")
    assert d[-1][0] == "RED id { DISPOSITIVO id tipo ip ; }"


ACEPTADAS = ["RED id { }", "RED id { DISPOSITIVO id tipo ip ; ENLACE id id num ; }",
             "RED id { ZONA id { ZONA id { DISPOSITIVO id tipo ip ; } } }"]
RECHAZADAS = [("RED id { ZONA id { }", "bloques sin cerrar"), ("RED id { } }", "sobra entrada"),
              ("RED id DISPOSITIVO id tipo ip ;", "se esperaba '{'")]


@pytest.mark.parametrize("cadena", ACEPTADAS)
def test_pila_acepta(cadena):
    r = AutomataPila().procesar(cadena)
    assert r.aceptada and r.pasos[-1].estado == "qf" and r.pasos[-1].pila == "Z0"


@pytest.mark.parametrize("cadena,motivo", RECHAZADAS)
def test_pila_rechaza(cadena, motivo):
    r = AutomataPila().procesar(cadena)
    assert not r.aceptada and motivo in r.motivo


def test_contenido_de_la_pila_en_zonas_anidadas():
    r = AutomataPila().procesar(ACEPTADAS[2])
    assert max(len(p.pila.split()) for p in r.pasos) == 4          # Z Z R Z0
    assert r.profundidad_maxima == 3


def test_pila_y_parser_coinciden():
    for cadena in ACEPTADAS + [c for c, _ in RECHAZADAS]:
        pila = AutomataPila().procesar(cadena).aceptada
        try:
            Parser(tokens(cadena)).parsear()
            parser = True
        except ErrorSintactico:
            parser = False
        assert pila == parser


def test_semantica_detecta_duplicados_e_ip_repetida():
    texto = ("RED a {\n DISPOSITIVO R1 router 10.0.0.1 ;\n DISPOSITIVO R1 pc 10.0.0.2 ;\n"
             " DISPOSITIVO R2 pc 10.0.0.1 ;\n}")
    c = analizar_configuracion(texto)
    assert any("ya fue declarado" in e for e in c.errores_semanticos)
    assert any("ya está asignada" in e for e in c.errores_semanticos)
    assert c.grafo is None


def test_configuracion_valida_construye_grafo_con_zonas():
    texto = "RED campus {\n ZONA dc {\n DISPOSITIVO S servidor 10.0.0.5 ;\n }\n DISPOSITIVO R router 10.0.0.1 ;\n ENLACE R S 4 ;\n}"
    c = analizar_configuracion(texto)
    assert c.valida
    assert c.grafo.dispositivos["S"].zona == "campus/dc"
    assert c.grafo.latencia("R", "S") == 4
