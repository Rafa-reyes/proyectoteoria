"""Pruebas del AFN, la conversión a AFD, la minimización y la máquina de estados (secciones 9 y 10)."""
from itertools import product

import pytest

from automatas.afn import AFN, EPSILON
from automatas.conversion import afn_a_afd, minimizar
from automatas.maquina_estados import AFN_FALLA, AFD_FALLA, MAQUINA, PASOS_CONVERSION

ACEPTADAS = ["tt", "rtt", "ttr", "rltlttr", "lttl"]
RECHAZADAS = ["", "t", "rtrt", "tltl", "rrllr"]


@pytest.mark.parametrize("cadena", ACEPTADAS)
def test_afn_acepta(cadena):
    assert AFN_FALLA.acepta(cadena)


@pytest.mark.parametrize("cadena", RECHAZADAS)
def test_afn_rechaza(cadena):
    assert not AFN_FALLA.acepta(cadena)


def test_recorrido_del_afn_como_en_el_documento():
    r = AFN_FALLA.procesar("rtt")
    assert [set(c) for _, c in r.pasos] == [{"q0"}, {"q0"}, {"q0", "q1"}, {"q0", "q1", "q2"}]


def test_conversion_produce_la_tabla_del_documento():
    assert AFD_FALLA.estados == ["A", "B", "C", "D"]
    assert AFD_FALLA.inicial == "A" and AFD_FALLA.finales == {"C", "D"}
    esperado = {"A": "AAB", "B": "AAC", "C": "DDC", "D": "DDC"}
    for q, destinos in esperado.items():
        assert [AFD_FALLA.delta(q, a) for a in "rlt"] == list(destinos)
    assert len(PASOS_CONVERSION) == 12
    assert sum(p.nuevo for p in PASOS_CONVERSION) == 3       # B, C y D aparecen una vez


def test_afn_y_afd_equivalentes_hasta_longitud_8():
    total = 0
    for n in range(9):
        for w in product("rlt", repeat=n):
            w = "".join(w)
            total += 1
            assert AFN_FALLA.acepta(w) == AFD_FALLA.acepta(w) == ("tt" in w)
    assert total == 9841


def test_minimizacion_fusiona_C_y_D():
    minimo, historial = minimizar(AFD_FALLA)
    assert minimo.estados == ["A", "B", "CD"]
    assert historial[0] == [["A", "B"], ["C", "D"]]


def test_simbolo_fuera_del_alfabeto():
    r = AFD_FALLA.procesar("rxt")
    assert not r.aceptada and "'x'" in r.motivo


def test_conversion_con_transiciones_epsilon():
    """Caso general: (a|b)*ab con una transición ε."""
    afn = AFN({"p", "q", "s", "f"}, ("a", "b"),
              {("p", "a"): {"p"}, ("p", "b"): {"p"}, ("p", EPSILON): {"q"},
               ("q", "a"): {"s"}, ("s", "b"): {"f"}}, "p", {"f"})
    afd, _, _ = afn_a_afd(afn)
    for n in range(7):
        for w in product("ab", repeat=n):
            w = "".join(w)
            assert afd.acepta(w) == afn.acepta(w) == w.endswith("ab")


@pytest.mark.parametrize("cadena,estado", [("rtt", "Falla"), ("trt", "Sobrecargado"), ("rlr", "Activo"),
                                           ("ttr", "Recuperación"), ("lt", "Falla"), ("", "Activo")])
def test_maquina_de_estados(cadena, estado):
    assert MAQUINA.estado_final(cadena) == estado
    assert MAQUINA.es_completo()
