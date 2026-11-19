"""Pruebas del analizador léxico: lenguaje L_enlaces (sección 7) y expresiones R1-R4 (sección 8)."""
import pytest

from lenguajes import lexico

# Sección 7.3 y 7.4 del documento
VALIDAS = ["Router1,Switch1", "Router1,Switch2,3", "Switch1, PC1, 1", "PC2,DB,4", "Server,DB,2",
           "Impresora1", "sw-core_01,fw-perimetral,15", "AP3,Switch2,9999", "A,B", "Firewall_Edge,Router1,120"]
INVALIDAS = [
    ("Router1;Switch1", "separador ';'"),
    ("Router1,", "falta el dispositivo de destino"),
    ("1Router,Switch1", "debe iniciar con una letra"),
    ("Router1,Switch1,0", "se recibió 0"),
    ("Router1,Switch1,10000", "se recibió 10000"),
    ("Router1,Switch1,2.5", "'.'"),
    ("Router1,Switch1,3,7", "4 campos"),
    ("Router 1,Switch1", "espacios"),
    ("PC1,PC1", "consigo mismo"),
    ("Nodo_de_distribucion_principal,PC1", "el máximo es 20"),
]


@pytest.mark.parametrize("cadena", VALIDAS)
def test_cadenas_validas_de_L_enlaces(cadena):
    assert lexico.validar_linea_enlace(cadena).valida


@pytest.mark.parametrize("cadena,motivo", INVALIDAS)
def test_cadenas_invalidas_explican_el_motivo(cadena, motivo):
    r = lexico.validar_linea_enlace(cadena)
    assert not r.valida
    assert motivo in r.motivo


def test_latencia_por_omision_es_1():
    assert lexico.validar_linea_enlace("A,B").datos["latencia"] == 1


@pytest.mark.parametrize("nombre", ["Router1", "PC_01", "sw-core", "A" * 20])
def test_r1_validos(nombre):
    assert lexico.validar_nombre(nombre)[0]


@pytest.mark.parametrize("nombre", ["1Router", "_pc", "Ser ver", "A" * 21, "", "Router1\n"])
def test_r1_invalidos(nombre):
    assert not lexico.validar_nombre(nombre)[0]


@pytest.mark.parametrize("ip", ["192.168.1.10", "10.0.0.1", "255.255.255.255", "0.0.0.0"])
def test_r3_validas(ip):
    assert lexico.REGEX_IPV4.fullmatch(ip)


@pytest.mark.parametrize("ip", ["256.1.1.1", "192.168.01.1", "192.168.1", "1.2.3.4.5", "999.999.999.999"])
def test_r3_invalidas(ip):
    assert not lexico.REGEX_IPV4.fullmatch(ip)


def test_r4_extrae_y_traduce_eventos():
    r = lexico.validar_linea_monitoreo("Server: ok, ok, timeout, timeout")
    assert r.valida and r.datos["dispositivo"] == "Server" and r.datos["simbolos"] == "rrtt"
    assert lexico.validar_linea_monitoreo("DB:lento").datos["simbolos"] == "l"


@pytest.mark.parametrize("linea,motivo", [("PC1: ping", "ping"), ("PC1 ok", "falta ':'"),
                                          ("PC1:", "vacía"), ("PC1: ok,,timeout", "evento vacío")])
def test_r4_invalidas(linea, motivo):
    r = lexico.validar_linea_monitoreo(linea)
    assert not r.valida and motivo in r.motivo


def test_tokenizador_clasifica_cada_lexema():
    tokens, errores = lexico.tokenizar_config("RED lab { DISPOSITIVO R1 router 10.0.0.1 ; ENLACE R1 R2 5 ; }")
    assert not errores
    assert [t.tipo for t in tokens] == ["RED", "id", "{", "DISPOSITIVO", "id", "tipo", "ip", ";",
                                        "ENLACE", "id", "id", "num", ";", "}"]


def test_tokenizador_reporta_ip_invalida_con_linea():
    _, errores = lexico.tokenizar_config("RED a {\n DISPOSITIVO R1 router 256.1.1.1 ;\n}")
    assert errores and errores[0].linea == 2 and "IPv4" in errores[0].motivo


def test_comentarios_se_ignoran():
    tokens, _ = lexico.tokenizar_config("# comentario\nRED a { } # fin")
    assert [t.tipo for t in tokens] == ["RED", "id", "{", "}"]
