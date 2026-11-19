"""Pruebas del sistema completo: los 22 casos de la sección 15 del documento."""
import pytest

from tests.casos_sistema import CASOS


@pytest.mark.parametrize("caso", CASOS, ids=[c[0] for c in CASOS])
def test_caso_del_documento(caso):
    identificador, entrada, _, esperado, funcion = caso
    obtenido, correcto = funcion()
    assert correcto, f"{identificador} «{entrada}»: se esperaba «{esperado}» y se obtuvo «{obtenido}»"
