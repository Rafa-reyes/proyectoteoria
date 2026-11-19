# Network Graph Analyzer

**Proyecto 4 · Analizador de redes mediante grafos** — Teoría Computacional, Proyecto Final Integrador.

## Integrantes

| Integrante | Responsabilidades principales |
|---|---|
| Hiram Alejandro Almendarez Hernández | Grafos y algoritmos, gramática, parser, autómata de pila, CLI e integración |
| Axel Rafael Reyes Lara | Lenguaje formal, expresiones regulares, AFN, conversión AFN → AFD, máquina de estados, pruebas |

## Descripción

Aplicación de consola que representa una infraestructura de red como un **grafo no dirigido y ponderado**
(dispositivos = vértices, enlaces = aristas con latencia en ms) y permite analizar sus nodos, conexiones,
rutas y estados. Antes de construir el grafo, toda entrada se valida con los modelos del curso:

| Concepto | Dónde se usa | Módulo |
|---|---|---|
| Lenguaje formal L_enlaces y expresiones regulares R1–R4 | Validación de líneas de topología, IPs y monitoreo | `lenguajes/lexico.py` |
| Grafos (BFS, DFS, Dijkstra, Tarjan, ciclos, rutas alternativas) | Análisis de la red | `red/grafo.py`, `red/algoritmos.py` |
| AFN y conversión AFN → AFD (subconjuntos) y minimización | Detección de falla: dos timeouts consecutivos | `automatas/afn.py`, `afd.py`, `conversion.py` |
| Máquina de estados (AFD) | Estado de cada dispositivo: Activo, Sobrecargado, Falla, Recuperación | `automatas/maquina_estados.py` |
| Gramática libre de contexto (parser descendente recursivo) | Archivos de configuración `.red` con zonas anidadas | `gramatica/parser.py` |
| Autómata de pila | Validación del anidamiento de bloques RED / ZONA | `gramatica/automata_pila.py` |

Toda la lógica de Teoría Computacional está programada a mano. No se usan bibliotecas que construyan
autómatas ni generadores de parsers. `matplotlib` solo dibuja las imágenes y `networkx` solo calcula la
posición de los nodos en el dibujo; ningún algoritmo depende de ellas.

## Requisitos

- **Lenguaje:** Python 3.10 o superior (desarrollado con Python 3.14).
- **Núcleo:** solo la biblioteca estándar (`re`, `heapq`, `collections`, `dataclasses`, `argparse`, `pathlib`).
- **Opcionales:** `matplotlib` y `networkx` (exportar imágenes PNG) y `pytest` (pruebas).

```bash
python -m pip install -r requirements.txt
```

Si `matplotlib` no está instalado, el programa funciona igual y solo avisa que no puede exportar imágenes.

## Instrucciones para ejecutar

Desde la carpeta `02_Codigo`:

```bash
python main.py                                   # menú interactivo
python main.py --red datos/red_ejemplo.txt       # menú con una red ya cargada
python main.py --red datos/red_ejemplo.txt --ruta Router1 DB          # responde y termina
python main.py --red datos/red_ejemplo.txt --monitoreo datos/monitoreo.txt --reporte salida
python -m pytest                                 # 121 pruebas automáticas
python ejecutar_casos_prueba.py                  # casos P01–P22 → ../05_Pruebas/casos_prueba.md y .csv
```

### Menú principal

| Opción | Función | Modelo aplicado |
|---|---|---|
| 1 | Cargar topología desde archivo `.txt` | L_enlaces + R1/R2 |
| 2 | Cargar configuración `.red` | R1/R3 + autómata de pila + gramática + semántica |
| 3 | Capturar enlaces por teclado | R2 en cada línea |
| 4 | Mostrar el grafo (V, E, lista, matriz, árbol de rutas, PNG) | Grafos |
| 5 | Análisis: ruta, ruta más corta, grados, componentes, ciclos, puntos críticos, rutas alternativas, recorridos | Algoritmos sobre grafos |
| 6 | Procesar monitoreo y ver el impacto de las fallas | R4 + AFN/AFD + máquina de estados + grafos |
| 7 | Laboratorio teórico: probar cadenas en AFN/AFD/máquina/pila, ver la conversión, minimización, derivaciones, equivalencia AFN = AFD, regex | Todos |
| 8 | Exportar reporte `.txt` e imágenes PNG | — |
| 0 | Salir | — |

## Formatos de entrada

**Topología `.txt`** — una línea por enlace, `origen,destino[,latencia]`; un nombre solo es un dispositivo sin enlaces.
Las líneas que empiezan con `#` son comentarios.

```
Router1,Switch1,2
Switch1, PC1, 1
Impresora1
```

**Configuración `.red`** — gramática G (sección 11 del documento):

```
RED campus {
    DISPOSITIVO Router1 router 192.168.1.1 ;
    ZONA datacenter {
        DISPOSITIVO Server servidor 192.168.1.10 ;
    }
    ENLACE Router1 Server 3 ;
}
```

Tipos válidos: `router`, `switch`, `pc`, `servidor`, `firewall`.

**Monitoreo** — `Dispositivo: evento, evento, ...` con eventos `ok`, `lento`, `timeout`.

```
Server: ok, timeout, timeout
```

## Estructura del proyecto

```
02_Codigo/
├── main.py                    # menú CLI, argumentos y manejo de errores
├── ejecutar_casos_prueba.py   # ejecuta P01–P22 y escribe la tabla en 05_Pruebas/
├── red/
│   ├── grafo.py               # clase Grafo: lista/matriz de adyacencia, carga de archivos
│   └── algoritmos.py          # BFS, DFS, Dijkstra, grados, ciclos, Tarjan, rutas alternativas, impacto de falla
├── lenguajes/
│   └── lexico.py              # regex R1–R4, validación por línea, tokenizador de .red
├── automatas/
│   ├── afn.py                 # clase AFN (con cerradura-ε) y recorrido por conjuntos de estados
│   ├── afd.py                 # clase AFD y recorrido
│   ├── conversion.py          # construcción de subconjuntos (tabla de pasos) y minimización
│   └── maquina_estados.py     # monitoreo: AFN/AFD de falla + Activo/Sobrecargado/Falla/Recuperación
├── gramatica/
│   ├── parser.py              # parser descendente recursivo + derivación + validación semántica
│   └── automata_pila.py       # autómata de pila con traza de la pila
├── reportes/
│   ├── visualizacion.py       # tablas de texto, árbol de rutas, PNG del grafo y de los autómatas
│   └── reporte.py             # reporte .txt
├── datos/                     # red_ejemplo.txt, red_campus.red, red_laboratorio.red, monitoreo.txt
│   └── invalidos/             # un archivo por cada caso de error de las pruebas
├── tests/                     # pytest: léxico, grafo, autómatas, gramática y sistema (P01–P22)
├── requirements.txt
└── README.md
```

## Ejemplos de uso

Carga con errores (`datos/red_ejemplo_errores.txt`):

```
Línea 1   Router1,Switch1,2              ✓ válida
Línea 2   Router1;Switch2                ✗ RECHAZADA
          Motivo: el separador ';' no pertenece al alfabeto; se esperaba ','.
Línea 3   Switch1,PC1,0                  ✗ RECHAZADA
          Motivo: la latencia debe ser un entero entre 1 y 9999 (se recibió 0).
Línea 4   PC1,PC1                        ✗ RECHAZADA
          Motivo: un dispositivo no puede enlazarse consigo mismo (PC1).

Resultado: 1 enlace(s) cargado(s), 3 línea(s) rechazada(s).
```

Ruta más corta y efecto de una falla:

```
$ python main.py --red datos/red_ejemplo.txt --ruta Router1 DB
Ruta: Router1 → Switch2 → Server → DB    Latencia total: 6 ms

$ python main.py --red datos/red_ejemplo.txt --monitoreo datos/monitoreo.txt --ruta Router1 DB
  Dispositivo  Eventos               Σm   AFN      AFD      Estado final
  Server       ok, timeout, timeout  rtt  acepta   acepta   Falla
  ...
(Se excluyen los dispositivos en Falla: Server)
Ruta: Router1 → Switch1 → PC2 → DB    Latencia total: 7 ms
```

Configuración con una zona sin cerrar (`datos/invalidos/zona_sin_cerrar.red`):

```
[2] Autómata de pila: ✗ RECHAZADA — el archivo terminó con la pila Z[datacenter] R[campus] Z0:
    hay bloques sin cerrar: ZONA 'datacenter' (abierta en la línea 3), RED 'campus' (abierta en la línea 1)
[3] Parser (gramática G): ✗ Error sintáctico. Línea 5: el archivo terminó cuando se esperaba ZONA, DISPOSITIVO, ENLACE o '}'
```
