"""
Ejecuta los 22 casos de prueba del sistema (sección 15 del documento) y escribe
la tabla con el resultado OBTENIDO en 05_Pruebas/:

    05_Pruebas/casos_prueba.md    tabla para consultar o copiar al documento
    05_Pruebas/casos_prueba.csv   la misma tabla para Excel (separador ';')

Uso:  python ejecutar_casos_prueba.py
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

from main import configurar_consola
from tests.casos_sistema import CASOS

SALIDA = Path(__file__).resolve().parent.parent / "05_Pruebas"


def ejecutar():
    filas = []
    for identificador, entrada, categoria, esperado, funcion in CASOS:
        try:
            obtenido, correcto = funcion()
        except Exception as e:                    # un caso que truena cuenta como Error
            obtenido, correcto = f"Excepción {type(e).__name__}: {e}", False
        filas.append([identificador, entrada, categoria, esperado, obtenido,
                      "Correcto" if correcto else "Error"])
    return filas


def escribir(filas):
    SALIDA.mkdir(exist_ok=True)
    encabezados = ["ID", "Entrada", "Categoría", "Resultado esperado", "Resultado obtenido", "Estado"]
    correctos = sum(f[5] == "Correcto" for f in filas)

    md = [f"# Casos de prueba del sistema — Network Graph Analyzer",
          "",
          f"Ejecutados el {datetime.now():%d/%m/%Y %H:%M} con `python ejecutar_casos_prueba.py`.",
          f"Resultado: **{correctos} de {len(filas)} correctos**.",
          "",
          "| " + " | ".join(encabezados) + " |",
          "|" + "---|" * len(encabezados)]
    for f in filas:
        md.append("| " + " | ".join(c.replace("|", "\\|") for c in f) + " |")
    (SALIDA / "casos_prueba.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    with open(SALIDA / "casos_prueba.csv", "w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.writer(archivo, delimiter=";")
        escritor.writerow(encabezados)
        escritor.writerows(filas)
    return correctos


if __name__ == "__main__":
    configurar_consola()
    filas = ejecutar()
    for f in filas:
        print(f"{f[0]}  {f[5]:<8}  {f[4]}")
    correctos = escribir(filas)
    print(f"\n{correctos} de {len(filas)} casos correctos. Tabla guardada en {SALIDA}")
    sys.exit(0 if correctos == len(filas) else 1)
