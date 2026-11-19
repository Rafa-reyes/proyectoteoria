# Casos de prueba del sistema — Network Graph Analyzer

Ejecutados el 17/11/2026 11:52 con `python ejecutar_casos_prueba.py`.
Resultado: **22 de 22 correctos**.

| ID | Entrada | Categoría | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|---|
| P01 | Cargar red_ejemplo.txt | Válida / normal | 8 dispositivos, 7 enlaces cargados | 8 dispositivos, 7 enlaces cargados | Correcto |
| P02 | Ruta más corta Router1 → DB | Válida / normal | Router1→Switch2→Server→DB, 6 ms | Router1→Switch2→Server→DB, 6 ms | Correcto |
| P03 | ¿Existe ruta PC1 → Impresora1? | Válida / normal | No existe ruta (componentes distintas) | No existe ruta | Correcto |
| P04 | Puntos críticos de la red de ejemplo | Válida / normal | Articulación: Switch1; puente: Switch1–PC1 | Articulación: Switch1; puente: Switch1–PC1 | Correcto |
| P05 | Detectar ciclos | Válida / normal | Ciclo Router1–Switch1–PC2–DB–Server–Switch2–Router1 | Router1–Switch1–PC2–DB–Server–Switch2–Router1 | Correcto |
| P06 | Grados y aislados | Válida / normal | Switch1 = 3 (máximo); Impresora1 aislado | Switch1 = 3 (máximo); aislados: Impresora1 | Correcto |
| P07 | Línea «Router1;Switch1» | Inválida | Rechazada: separador no válido (línea indicada) | Rechazada: el separador ';' no pertenece al alfabeto; se esperaba ',' | Correcto |
| P08 | Línea «Router1,Switch1,0» | Inválida | Rechazada: latencia fuera de rango | Rechazada: la latencia debe ser un entero entre 1 y 9999 (se recibió 0) | Correcto |
| P09 | Archivo vacío | Límite | Mensaje: el archivo no contiene dispositivos | Mensaje: el archivo 'datos\invalidos\vacio.txt' no contiene dispositivos | Correcto |
| P10 | Archivo con un solo dispositivo «Impresora1» | Límite | Grafo de 1 vértice, 0 aristas, aislado | 1 vértice, 0 aristas, aislados: Impresora1 | Correcto |
| P11 | Nombre de exactamente 20 caracteres / de 21 | Límite | 20: aceptado · 21: rechazado | 20: aceptado · 21: rechazado | Correcto |
| P12 | Lazo «PC1,PC1» | Inesperada | Rechazada: enlace consigo mismo | Rechazada: un dispositivo no puede enlazarse consigo mismo (PC1) | Correcto |
| P13 | Enlace duplicado «PC1,Switch1» dos veces | Inesperada | Advertencia; se conserva el primero | Advertencia: enlace duplicado PC1–Switch1: se conserva el primero (1 ms) | Correcto |
| P14 | Monitoreo «Server: ok, timeout, timeout» | Válida / normal | AFN y AFD aceptan; Server → Falla; Router1→DB = 7 ms | AFN acepta, AFD acepta; Server → Falla; Router1→DB = 7 ms | Correcto |
| P15 | Monitoreo «DB: timeout, ok, timeout» | Válida / normal | AFN y AFD rechazan; DB → Sobrecargado | AFN rechaza, AFD rechaza; DB → Sobrecargado | Correcto |
| P16 | Monitoreo «PC1: ping» | Inválida | Error léxico: evento desconocido «ping» | Error léxico: evento desconocido 'ping'; los eventos válidos son ok, lento y timeout | Correcto |
| P17 | Archivo .red con zonas anidadas (3 niveles) | Válida / normal | AP acepta; profundidad máxima de pila 3; grafo construido | AP acepta; profundidad máxima 3; grafo con 4 dispositivos | Correcto |
| P18 | .red con una ZONA sin cerrar | Inválida | AP rechaza: termina con pila Z R Z0; indica la zona | AP rechaza: termina con pila Z[datacenter] R[campus] Z0 | Correcto |
| P19 | .red con tipo «modem» | Inválida | Error sintáctico: se esperaba un tipo de dispositivo | Error sintáctico: Línea 3: se esperaba un tipo de dispositivo (router, switch, pc, servidor, firewall) y se encontró 'modem' | Correcto |
| P20 | .red con ENLACE a dispositivo no declarado | Inválida | Error semántico: «X» no fue declarado | Error semántico: Línea 3: el dispositivo 'X' no fue declarado antes de usarse en un ENLACE | Correcto |
| P21 | Ruta más corta entre un nodo y él mismo | Límite | Ruta de 0 ms con un solo vértice | Ruta PC1, 0 ms | Correcto |
| P22 | Archivo inexistente / opción de menú «abc» | Inesperada | Mensaje claro, el programa no se cierra | Mensaje: el archivo 'datos\no_existe.txt' no existe; opción «abc» rechazada | Correcto |
