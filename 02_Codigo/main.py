"""
Network Graph Analyzer — aplicación de consola (sección 14 del documento).

Uso:
    python main.py                                      menú interactivo
    python main.py --red datos/red_ejemplo.txt          carga una topología al iniciar
    python main.py --config datos/red_campus.red        carga una configuración .red al iniciar
    python main.py --red datos/red_ejemplo.txt --ruta Router1 DB
    python main.py --red datos/red_ejemplo.txt --monitoreo datos/monitoreo.txt --reporte salida/reporte.txt

Con --ruta o --reporte el programa responde y termina sin abrir el menú.
"""
import argparse
import sys
from itertools import product
from pathlib import Path

from automatas.conversion import minimizar, formatear_particion
from automatas.afn import formatear_conjunto
from automatas.maquina_estados import (AFN_FALLA, AFD_FALLA, MAQUINA, PASOS_CONVERSION, EFECTO_EN_GRAFO,
                                       procesar_monitoreo, aplicar_estados, dispositivos_en_falla)
from gramatica.automata_pila import AutomataPila
from gramatica.parser import analizar_archivo_config
from lenguajes import lexico
from red import algoritmos as alg
from red.grafo import (Grafo, ErrorEntrada, ResultadoCarga, cargar_desde_archivo,
                       procesar_linea_enlace)
from reportes.reporte import generar_reporte, guardar_reporte
from reportes.visualizacion import (tabla_texto, arbol_rutas, dibujar_grafo, dibujar_automata,
                                    VisualizacionNoDisponible)

OK, NO = "✓", "✗"


class Salir(Exception):
    """El usuario cerró la entrada (Ctrl+C / Ctrl+Z) o eligió salir."""


# ----------------------------------------------------------------------
# Utilidades de consola
# ----------------------------------------------------------------------
def configurar_consola():
    """En Windows la consola puede no usar UTF-8; sin esto, Σ, δ, ✓ o → fallarían."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def entrada(mensaje):
    try:
        return input(mensaje).strip()
    except (EOFError, KeyboardInterrupt):
        raise Salir from None


def confirmar(mensaje):
    return entrada(f"{mensaje} (s/N): ").lower() in ("s", "si", "sí")


def titulo(texto):
    print(f"\n{texto}\n{'─' * len(texto)}")


def flecha(camino):
    return " → ".join(camino)


def leer_cadena_monitoreo(texto):
    """Acepta «rtt», «r t t», «r,t,t» u «ok, timeout, timeout». «ε» o «-» = cadena vacía."""
    if texto in ("ε", "-"):
        return ""
    partes = [p for p in texto.replace(",", " ").split() if p]
    if any(p in lexico.EVENTO_A_SIMBOLO for p in partes):
        desconocidos = [p for p in partes if p not in lexico.EVENTO_A_SIMBOLO]
        if desconocidos:
            raise ErrorEntrada(f"evento desconocido '{desconocidos[0]}'; use ok, lento o timeout")
        return lexico.traducir_eventos(partes)
    return "".join(partes)


# ----------------------------------------------------------------------
# Aplicación
# ----------------------------------------------------------------------
class Aplicacion:
    def __init__(self, interactiva=True):
        self.grafo = None
        self.descripcion = ""
        self.monitoreo = []
        self.interactiva = interactiva
        self.opciones = {
            "1": ("Cargar topología desde archivo .txt", self.opcion_cargar_topologia),
            "2": ("Cargar configuración .red (zonas anidadas)", self.opcion_cargar_config),
            "3": ("Capturar enlaces por teclado", self.opcion_capturar),
            "4": ("Mostrar el grafo (V, E, lista, matriz, árbol)", self.opcion_mostrar),
            "5": ("Análisis del grafo (rutas, grados, ciclos, puntos críticos...)", self.opcion_analisis),
            "6": ("Procesar monitoreo y ver el impacto de las fallas", self.opcion_monitoreo),
            "7": ("Laboratorio teórico (AFN, AFD, conversión, pila, gramática, regex)", self.opcion_laboratorio),
            "8": ("Exportar reporte .txt e imágenes PNG", self.opcion_exportar),
            "0": ("Salir", None),
        }

    # -------------------------------------------------- ciclo principal
    def ejecutar(self):
        print("=" * 50)
        print("            NETWORK GRAPH ANALYZER")
        print("   Analizador de redes mediante grafos")
        print("=" * 50)
        while True:
            print()
            if self.grafo is not None:
                fallas = dispositivos_en_falla(self.grafo)
                print(f"Red actual: {self.descripcion} · {self.grafo.num_vertices()} dispositivos, "
                      f"{self.grafo.num_aristas()} enlaces" + (f" · en falla: {', '.join(fallas)}" if fallas else ""))
            else:
                print("Red actual: ninguna")
            for clave, (texto, _) in self.opciones.items():
                print(f"  {clave}. {texto}")
            opcion = entrada("> Opción: ")
            if opcion == "0":
                return
            if not self.es_opcion_valida(opcion):
                print(f"{NO} Opción no válida: '{opcion}'. Escriba un número del 0 al 8.")
                continue
            self.ejecutar_seguro(self.opciones[opcion][1])

    def es_opcion_valida(self, opcion):
        return opcion in self.opciones

    def ejecutar_seguro(self, accion, *args):
        """Ejecuta una acción mostrando los errores como mensajes, nunca como traceback."""
        try:
            accion(*args)
            return True
        except Salir:
            raise
        except (ErrorEntrada, VisualizacionNoDisponible) as e:
            print(f"\n{NO} Error: {e}.")
        except RecursionError:
            print(f"\n{NO} Error: la red es demasiado grande para este análisis recursivo.")
        except Exception as e:  # último recurso: el programa no debe cerrarse
            print(f"\n{NO} Error inesperado ({type(e).__name__}): {e}")
        return False

    # -------------------------------------------------- helpers
    def establecer_grafo(self, grafo, descripcion):
        self.grafo, self.descripcion, self.monitoreo = grafo, descripcion, []

    def hay_grafo(self):
        if self.grafo is None or self.grafo.num_vertices() == 0:
            print(f"{NO} Primero cargue una red (opciones 1, 2 o 3).")
            return False
        return True

    def grafo_operativo(self):
        """El grafo sin los dispositivos en Falla (la máquina de estados los retira)."""
        fallas = dispositivos_en_falla(self.grafo)
        if fallas:
            print(f"(Se excluyen los dispositivos en Falla: {', '.join(fallas)})")
            return self.grafo.subgrafo_sin(fallas)
        return self.grafo

    def pedir_dispositivo(self, mensaje, grafo=None):
        grafo = grafo or self.grafo
        while True:
            nombre = entrada(mensaje)
            if nombre == "":
                return None
            if grafo.existe(nombre):
                return nombre
            parecidos = [v for v in grafo.vertices() if v.lower() == nombre.lower()]
            if len(parecidos) == 1:
                print(f"  (se usa '{parecidos[0]}': los nombres distinguen mayúsculas)")
                return parecidos[0]
            if self.grafo.existe(nombre):
                print(f"  {NO} '{nombre}' está en Falla y fue retirado del grafo.")
                continue
            print(f"  {NO} No existe el dispositivo '{nombre}'. Disponibles: {', '.join(grafo.vertices())}")

    # ================================================== 1. topología .txt
    def opcion_cargar_topologia(self, ruta=None):
        ruta = ruta or entrada("Archivo de topología (.txt): ")
        resultado = cargar_desde_archivo(ruta)
        print("Analizando...\n")
        for l in resultado.lineas:
            if l.valida:
                extra = f"   (advertencia: {l.mensaje})" if l.mensaje else ""
                print(f"Línea {l.numero:<3} {l.texto:<30} {OK} válida{extra}")
            else:
                print(f"Línea {l.numero:<3} {l.texto:<30} {NO} RECHAZADA")
                print(f"          Motivo: {l.mensaje}.")
        print(f"\nResultado: {resultado.enlaces_cargados} enlace(s) cargado(s), "
              f"{len(resultado.rechazadas)} línea(s) rechazada(s).")
        g = resultado.grafo
        if g.num_vertices() == 0:
            print(f"{NO} No se cargó ningún dispositivo; la red anterior se conserva.")
            return
        print(f"Red cargada: {g.num_vertices()} dispositivo(s), {g.num_aristas()} enlace(s).")
        self.establecer_grafo(g, Path(ruta).name)

    # ================================================== 2. configuración .red
    def opcion_cargar_config(self, ruta=None):
        ruta = ruta or entrada("Archivo de configuración (.red): ")
        c = analizar_archivo_config(ruta)
        print("Analizando...\n")
        print(f"[1] Análisis léxico (R1, R3, PESO): {len(c.tokens)} tokens")
        if c.errores_lexicos:
            for e in c.errores_lexicos:
                print(f"    {NO} {e}")
            print(f"\n{NO} La configuración no se cargó: hay errores léxicos.")
            return
        if c.resultado_pila is None:
            print(f"    {NO} {c.error_sintactico}")
            return

        ap = c.resultado_pila
        if ap.aceptada:
            print(f"[2] Autómata de pila: {OK} ACEPTADA (profundidad máxima de la pila: {ap.profundidad_maxima})")
        else:
            print(f"[2] Autómata de pila: {NO} RECHAZADA — {ap.motivo}")
        if self.interactiva and confirmar("    ¿Mostrar la traza de la pila?"):
            self.imprimir_traza_pila(ap)

        if c.error_sintactico:
            print(f"[3] Parser (gramática G): {NO} Error sintáctico. {c.error_sintactico}")
            print(f"\n{NO} La configuración no se cargó.")
            return
        print(f"[3] Parser (gramática G): {OK} estructura válida "
              f"({len(c.derivacion) - 1} producciones aplicadas)")

        if c.errores_semanticos:
            print(f"[4] Validación semántica: {NO}")
            for e in c.errores_semanticos:
                print(f"    {NO} Error semántico. {e}")
            print(f"\n{NO} La configuración no se cargó.")
            return
        print(f"[4] Validación semántica: {OK} sin errores")
        for a in c.advertencias:
            print(f"    Advertencia: {a}")
        g = c.grafo
        print(f"\nRed '{c.red.nombre}' cargada: {g.num_vertices()} dispositivo(s), {g.num_aristas()} enlace(s).")
        self.establecer_grafo(g, Path(ruta).name)

    @staticmethod
    def imprimir_traza_pila(ap):
        print(tabla_texto(["#", "Estado", "Entrada restante", "Transición", "Pila (tope a la izquierda)"],
                          [[p.numero, p.estado, p.entrada_restante, p.transicion, p.pila] for p in ap.pasos]))

    # ================================================== 3. teclado
    def opcion_capturar(self):
        print("Escriba un enlace por línea: origen,destino[,latencia]  (un nombre solo = dispositivo).")
        print("Línea vacía para terminar.")
        grafo = self.grafo if self.grafo is not None else Grafo()
        resultado = ResultadoCarga(grafo)
        numero = 0
        while True:
            texto = entrada("> ")
            if texto == "":
                break
            numero += 1
            procesar_linea_enlace(grafo, texto, numero, resultado)
            l = resultado.lineas[-1]
            if l.valida:
                print(f"  {OK} válida" + (f" (advertencia: {l.mensaje})" if l.mensaje else ""))
            else:
                print(f"  {NO} RECHAZADA. Motivo: {l.mensaje}.")
        if grafo.num_vertices():
            if self.grafo is None:
                self.establecer_grafo(grafo, "captura por teclado")
            print(f"Red: {grafo.num_vertices()} dispositivo(s), {grafo.num_aristas()} enlace(s).")

    # ================================================== 4. mostrar
    def opcion_mostrar(self):
        if not self.hay_grafo():
            return
        g = self.grafo
        titulo("Conjuntos")
        print(f"V = {{{', '.join(g.vertices())}}}    |V| = {g.num_vertices()}")
        print("E = {" + ", ".join(f"{{{u}, {v}}}({w})" for u, v, w in g.aristas()) + f"}}    |E| = {g.num_aristas()}")
        titulo("Lista de adyacencia")
        print(tabla_texto(["Vértice", "Vecinos (latencia ms)", "Grado"],
                          [[v, ", ".join(f"{n} ({w})" for n, w in g.vecinos(v).items()) or "∅ (aislado)",
                            g.grado(v)] for v in g.vertices()]))
        titulo("Matriz de adyacencia ponderada (0 = sin enlace)")
        if g.num_vertices() <= 20:
            orden, matriz = g.matriz_adyacencia()
            print(tabla_texto([""] + orden, [[orden[i]] + f for i, f in enumerate(matriz)]))
        else:
            print("(más de 20 dispositivos: consulte la matriz en el reporte exportado)")
        titulo("Dispositivos")
        print(tabla_texto(["Nombre", "Tipo", "IP", "Zona", "Estado"],
                          [[d.nombre, d.tipo, d.ip or "—", d.zona or "—", d.estado] for d in g.dispositivos.values()]))
        origen = g.vertices()[0]
        if self.interactiva:
            origen = self.pedir_dispositivo(f"Origen del árbol de rutas [{origen}]: ") or origen
        titulo(f"Árbol de rutas más cortas desde {origen}")
        print(arbol_rutas(g, origen))
        if self.interactiva and confirmar("¿Exportar el grafo como imagen PNG?"):
            articulaciones, _ = alg.puntos_criticos(g)
            ruta = dibujar_grafo(g, Path("salida") / "Grafo.png", resaltar=articulaciones)
            print(f"{OK} Imagen guardada en {ruta}")

    # ================================================== 5. análisis
    def opcion_analisis(self):
        if not self.hay_grafo():
            return
        submenu = {
            "a": ("¿Existe ruta entre dos dispositivos? (BFS)", self.analisis_existe_ruta),
            "b": ("Ruta más corta (Dijkstra)", self.analisis_ruta_corta),
            "c": ("Grados y dispositivos aislados", self.analisis_grados),
            "d": ("Componentes conexas", self.analisis_componentes),
            "e": ("Detección de ciclos", self.analisis_ciclos),
            "f": ("Puntos críticos: articulaciones y puentes (Tarjan)", self.analisis_criticos),
            "g": ("Rutas alternativas", self.analisis_alternativas),
            "h": ("Recorridos BFS y DFS", self.analisis_recorridos),
        }
        self.submenu("ANÁLISIS DEL GRAFO", submenu)

    def submenu(self, nombre, opciones):
        while True:
            titulo(nombre)
            for clave, (texto, _) in opciones.items():
                print(f"  {clave}) {texto}")
            print("  0) Regresar")
            op = entrada("> Opción: ").lower()
            if op in ("0", ""):
                return
            if op not in opciones:
                print(f"{NO} Opción no válida: '{op}'.")
                continue
            self.ejecutar_seguro(opciones[op][1])

    def pedir_par(self, grafo):
        origen = self.pedir_dispositivo("Origen: ", grafo)
        if origen is None:
            return None, None
        destino = self.pedir_dispositivo("Destino: ", grafo)
        return origen, destino

    def analisis_existe_ruta(self):
        g = self.grafo_operativo()
        o, d = self.pedir_par(g)
        if d is None:
            return
        camino = alg.existe_ruta(g, o, d)
        if camino:
            print(f"{OK} Sí existe ruta entre {o} y {d}: {flecha(camino)} ({len(camino) - 1} saltos)")
        else:
            print(f"{NO} No existe ruta entre {o} y {d}: están en componentes conexas distintas.")

    def analisis_ruta_corta(self):
        g = self.grafo_operativo()
        o, d = self.pedir_par(g)
        if d is None:
            return
        resultado = alg.ruta_mas_corta(g, o, d)
        if resultado is None:
            print(f"{NO} No existe ruta entre {o} y {d}.")
            return
        camino, costo = resultado
        print(f"Ruta: {flecha(camino)}    Latencia total: {costo} ms")
        if confirmar("¿Mostrar la traza de Dijkstra?"):
            _, _, traza = alg.dijkstra(g, o)
            print(tabla_texto(["Iteración", "Vértice extraído (d)", "Relajaciones d(v): antes → después"],
                              [[i, f"{u} ({dist})",
                                ", ".join(f"{v}: {'∞' if a == alg.INFINITO else a} → {n}" for v, a, n in rel) or "—"]
                               for i, (u, dist, rel) in enumerate(traza, 1)]))

    def analisis_grados(self):
        g = self.grafo_operativo()
        grados = alg.grados(g)
        print(tabla_texto(["Dispositivo", "Grado"], sorted(grados.items(), key=lambda x: -x[1])))
        maximo = max(grados.values())
        print(f"\nGrado máximo: {maximo} ({', '.join(v for v, x in grados.items() if x == maximo)})")
        print(f"Aislados: {', '.join(alg.aislados(g)) or 'ninguno'}")
        print(f"Comprobación: suma de grados = {sum(grados.values())} = 2·|E| = {2 * g.num_aristas()}")

    def analisis_componentes(self):
        componentes = alg.componentes_conexas(self.grafo_operativo())
        print(f"La red tiene {len(componentes)} componente(s) conexa(s):")
        for i, c in enumerate(componentes, 1):
            print(f"  {i}. {{{', '.join(c)}}}")
        if len(componentes) > 1:
            print("Los dispositivos de componentes distintas no pueden comunicarse entre sí.")

    def analisis_ciclos(self):
        ciclos = alg.detectar_ciclos(self.grafo_operativo())
        if not ciclos:
            print("No hay ciclos: la red no tiene caminos de respaldo (cada enlace es único).")
            return
        for c in ciclos:
            print(f"Ciclo: {' – '.join(c)}")
        print("Un ciclo indica redundancia: si falla un enlace del ciclo, sigue existiendo otro camino.")

    def analisis_criticos(self):
        articulaciones, puentes = alg.puntos_criticos(self.grafo_operativo())
        print(f"Puntos de articulación (puntos únicos de falla): {', '.join(articulaciones) or 'ninguno'}")
        print(f"Puentes (enlaces críticos): {', '.join(f'{u}–{v}' for u, v in puentes) or 'ninguno'}")
        if articulaciones:
            print("Si falla un punto de articulación, la red queda dividida en partes incomunicadas.")

    def analisis_alternativas(self):
        g = self.grafo_operativo()
        o, d = self.pedir_par(g)
        if d is None:
            return
        rutas, completo = alg.rutas_alternativas(g, o, d)
        if not rutas:
            print(f"{NO} No existe ruta entre {o} y {d}.")
            return
        for i, (camino, costo) in enumerate(rutas, 1):
            print(f"  {i}) {flecha(camino)}    {costo} ms")
        if not completo:
            print("(Se alcanzó el límite de exploración; se muestran las mejores rutas encontradas.)")

    def analisis_recorridos(self):
        g = self.grafo_operativo()
        origen = self.pedir_dispositivo("Origen: ", g)
        if origen is None:
            return
        orden_bfs, _ = alg.bfs(g, origen)
        print(f"BFS: {flecha(orden_bfs)}")
        print(f"DFS: {flecha(alg.dfs(g, origen))}")

    # ================================================== 6. monitoreo
    def opcion_monitoreo(self, ruta=None):
        ruta = ruta or entrada("Archivo de monitoreo: ")
        resultados, errores = procesar_monitoreo(ruta)
        print("Analizando...\n")
        for numero, texto, motivo in errores:
            print(f"Línea {numero:<3} {texto:<30} {NO} Error léxico: {motivo}.")
        if not resultados:
            print(f"\n{NO} No hay secuencias válidas que procesar.")
            return
        if resultados:
            print(tabla_texto(["Dispositivo", "Eventos", "Σm", "AFN", "AFD", "Estado final"],
                              [[r.dispositivo, ", ".join(r.eventos), r.simbolos,
                                "acepta" if r.recorrido_afn.aceptada else "rechaza",
                                "acepta" if r.recorrido_afd.aceptada else "rechaza", r.estado_final]
                               for r in resultados]))
            print("\nAFN/AFD aceptan = la secuencia contiene dos timeouts consecutivos (falla detectada).")
        if self.interactiva and resultados and confirmar("¿Mostrar los recorridos del AFN, AFD y máquina de estados?"):
            for r in resultados:
                print(f"\n{r.dispositivo}: {r.simbolos or 'ε'}")
                print(f"  AFN:     {r.recorrido_afn.texto(formatear_conjunto)}")
                print(f"  AFD:     {r.recorrido_afd.texto()}")
                print(f"  Estados: {r.recorrido_estados.texto()}")
        self.monitoreo = resultados
        if self.grafo is None:
            print("\nCargue una red (opción 1 o 2) para aplicar los estados y ver el impacto de las fallas.")
            return
        for a in aplicar_estados(self.grafo, resultados):
            print(f"Advertencia: {a}")
        fallas = dispositivos_en_falla(self.grafo)
        if not fallas:
            print("\nNingún dispositivo quedó en Falla; la red no cambia.")
            return
        self.mostrar_impacto(fallas)

    def mostrar_impacto(self, fallas, consulta=None):
        titulo("Impacto de las fallas")
        print(f"Dispositivos en Falla (se retiran del grafo): {', '.join(fallas)}")
        impacto = alg.impacto_falla(self.grafo, fallas)
        print(f"Componentes conexas: antes {len(impacto['componentes_antes'])}, "
              f"después {len(impacto['componentes_despues'])}")
        pares = impacto["pares_incomunicados"]
        if pares:
            print("Pares de dispositivos que quedaron incomunicados:")
            for u, v in pares[:15]:
                print(f"  {u} – {v}")
            if len(pares) > 15:
                print(f"  ... y {len(pares) - 15} más")
        else:
            print("Todos los dispositivos activos siguen comunicados entre sí.")
        if consulta is None and self.interactiva:
            print("Compare una ruta antes y después de la falla (Enter para omitir).")
            o, d = self.pedir_par(impacto["grafo"])
            consulta = (o, d) if d else None
        if consulta:
            o, d = consulta
            antes = alg.ruta_mas_corta(self.grafo, o, d)
            despues = alg.ruta_mas_corta(impacto["grafo"], o, d)
            print(f"Antes:   {flecha(antes[0]) + f'  = {antes[1]} ms' if antes else 'sin ruta'}")
            print(f"Después: {flecha(despues[0]) + f'  = {despues[1]} ms' if despues else 'sin ruta'}")

    # ================================================== 7. laboratorio
    def opcion_laboratorio(self):
        submenu = {
            "a": ("Probar una cadena en el AFN de falla", lambda: self.lab_cadena(AFN_FALLA, "AFN")),
            "b": ("Probar una cadena en el AFD obtenido", lambda: self.lab_cadena(AFD_FALLA, "AFD")),
            "c": ("Comparar AFN y AFD con la misma cadena", self.lab_comparar),
            "d": ("Tabla del AFN y construcción de subconjuntos (AFN → AFD)", self.lab_conversion),
            "e": ("Minimización del AFD", self.lab_minimizacion),
            "f": ("Máquina de estados de un dispositivo", lambda: self.lab_cadena(MAQUINA, "Máquina de estados")),
            "g": ("Autómata de pila con tokens (ej.: RED id { ZONA id { } })", self.lab_pila),
            "h": ("Derivación por la izquierda de un archivo .red", self.lab_derivacion),
            "i": ("Verificar AFN = AFD para todas las cadenas hasta longitud n", self.lab_equivalencia),
            "j": ("Probar las expresiones regulares R1–R4", self.lab_regex),
        }
        self.submenu("LABORATORIO TEÓRICO", submenu)

    def lab_cadena(self, automata, nombre):
        print("Cadena sobre Σm = {r, l, t} (r = ok, l = lento, t = timeout). Ej.: rltt, «ok, timeout». ε o - = vacía.")
        cadena = leer_cadena_monitoreo(entrada("Cadena: "))
        r = automata.procesar(cadena)
        formato = formatear_conjunto if nombre == "AFN" else str
        print(f"Recorrido: {r.texto(formato)}")
        if nombre == "Máquina de estados":
            estado = r.pasos[-1][1]
            print(f"Estado final: {estado}. Efecto: {EFECTO_EN_GRAFO[estado]}")
        else:
            print(f"Resultado: {'ACEPTADA' if r.aceptada else 'RECHAZADA'} — {r.motivo}")

    def lab_comparar(self):
        cadena = leer_cadena_monitoreo(entrada("Cadena (r, l, t): "))
        a, d = AFN_FALLA.procesar(cadena), AFD_FALLA.procesar(cadena)
        print(f"AFN: {a.texto(formatear_conjunto)}  → {'acepta' if a.aceptada else 'rechaza'}")
        print(f"AFD: {d.texto()}  → {'acepta' if d.aceptada else 'rechaza'}")
        print(f"{OK} Coinciden." if a.aceptada == d.aceptada else f"{NO} NO coinciden.")

    def lab_conversion(self):
        titulo("AFN original (→ inicial, * final)")
        encabezados, filas = AFN_FALLA.tabla()
        print(tabla_texto(encabezados, filas))
        titulo("Construcción de subconjuntos")
        print(tabla_texto(["Edo.", "Conjunto S", "a", "mover(S, a)", "Resultado", "Nombre", "¿Nuevo?"],
                          [[p.estado, formatear_conjunto(p.conjunto), p.simbolo, p.calculo,
                            formatear_conjunto(p.destino), p.nombre_destino, "Sí" if p.nuevo else "No"]
                           for p in PASOS_CONVERSION]))
        titulo("AFD obtenido")
        encabezados, filas = AFD_FALLA.tabla()
        print(tabla_texto(encabezados, filas))
        print(f"Estado inicial: {AFD_FALLA.inicial}. Estados finales: {', '.join(sorted(AFD_FALLA.finales))} "
              "(contienen q2).")

    def lab_minimizacion(self):
        minimo, historial = minimizar(AFD_FALLA)
        for i, p in enumerate(historial):
            print(f"P{i} = {formatear_particion(p)}")
        print("La partición ya no cambia: los estados de un mismo grupo son equivalentes.")
        encabezados, filas = minimo.tabla()
        print(tabla_texto(encabezados, filas))

    def lab_pila(self):
        print("Tokens separados por espacio: RED ZONA DISPOSITIVO ENLACE id tipo ip num { } ;")
        texto = entrada("Tokens: ")
        r = AutomataPila().procesar(texto)
        self.imprimir_traza_pila(r)
        print(f"Resultado: {'ACEPTADA' if r.aceptada else 'RECHAZADA'} — {r.motivo}")

    def lab_derivacion(self):
        ruta = entrada("Archivo .red: ")
        c = analizar_archivo_config(ruta)
        if c.errores_lexicos:
            for e in c.errores_lexicos:
                print(f"{NO} {e}")
            return
        for i, (forma, prod) in enumerate(c.derivacion):
            print(f"{i:>3}  {'⇒ ' if i else '  '}{forma}    [{prod}]")
        if c.error_sintactico:
            print(f"{NO} La derivación se detuvo: {c.error_sintactico}")
        else:
            print(f"{OK} La cadena de tokens pertenece a L(G).")

    def lab_equivalencia(self):
        n = entrada("Longitud máxima n [8]: ") or "8"
        if not n.isdigit() or not 0 <= int(n) <= 10:
            raise ErrorEntrada("n debe ser un entero entre 0 y 10")
        total, diferentes = 0, []
        for longitud in range(int(n) + 1):
            for simbolos in product("rlt", repeat=longitud):
                w = "".join(simbolos)
                total += 1
                if AFN_FALLA.acepta(w) != AFD_FALLA.acepta(w):
                    diferentes.append(w)
        if diferentes:
            print(f"{NO} {len(diferentes)} de {total} cadenas no coinciden: {diferentes[:10]}")
        else:
            print(f"{OK} El AFN y el AFD coinciden en las {total} cadenas de longitud 0 a {n}.")

    def lab_regex(self):
        expresiones = {
            "1": ("R1 · Nombre de dispositivo", lexico.R1_NOMBRE, lexico.validar_nombre),
            "2": ("R2 · Línea de enlace (L_enlaces)", lexico.R2_ENLACE, lexico.validar_linea_enlace),
            "3": ("R3 · Dirección IPv4", lexico.R3_IPV4, None),
            "4": ("R4 · Línea de monitoreo", lexico.R4_MONITOREO, lexico.validar_linea_monitoreo),
        }
        for k, (nombre, expr, _) in expresiones.items():
            print(f"  {k}) {nombre}")
        op = entrada("Expresión: ")
        if op not in expresiones:
            raise ErrorEntrada("elija 1, 2, 3 o 4")
        nombre, expr, validar = expresiones[op]
        print(f"Regex: {expr}")
        while True:
            cadena = entrada("Cadena (Enter para terminar): ")
            if cadena == "":
                return
            if op == "3":
                ok = bool(lexico.REGEX_IPV4.fullmatch(cadena))
                print(f"  {OK if ok else NO} {'válida' if ok else 'inválida'}")
                continue
            r = validar(cadena)
            if isinstance(r, tuple):            # validar_nombre devuelve (bool, motivo)
                ok, motivo, datos = r[0], r[1], {}
            else:
                ok, motivo, datos = r.valida, r.motivo, r.datos
            print(f"  {OK} válida  {datos if datos else ''}" if ok else f"  {NO} inválida: {motivo}")

    # ================================================== 8. exportar
    def opcion_exportar(self, carpeta=None):
        if not self.hay_grafo():
            return
        carpeta = Path(carpeta or (entrada("Carpeta de salida [salida]: ") or "salida"))
        texto = generar_reporte(self.grafo, descripcion=self.descripcion)
        if self.monitoreo:
            texto += "\n--- Monitoreo ---\n" + tabla_texto(
                ["Dispositivo", "Σm", "Falla (AFD)", "Estado final"],
                [[r.dispositivo, r.simbolos, "sí" if r.falla_detectada else "no", r.estado_final]
                 for r in self.monitoreo]) + "\n"
        ruta = guardar_reporte(texto, carpeta / "reporte.txt")
        print(f"{OK} Reporte guardado en {ruta}")
        try:
            articulaciones, _ = alg.puntos_criticos(self.grafo)
            figuras = [
                dibujar_grafo(self.grafo, carpeta / "Grafo.png", resaltar=articulaciones),
                dibujar_automata(AFN_FALLA, carpeta / "AFN.png", "AFN de falla"),
                dibujar_automata(AFD_FALLA, carpeta / "AFD.png", "AFD obtenido por subconjuntos"),
                dibujar_automata(minimizar(AFD_FALLA)[0], carpeta / "AFD_minimo.png", "AFD mínimo"),
            ]
            for f in figuras:
                print(f"{OK} Imagen guardada en {f}")
        except VisualizacionNoDisponible as e:
            print(f"{NO} No se exportaron imágenes: {e}.")


# ----------------------------------------------------------------------
# Línea de comandos
# ----------------------------------------------------------------------
def crear_argumentos():
    p = argparse.ArgumentParser(description="Network Graph Analyzer — analizador de redes mediante grafos")
    p.add_argument("--red", help="archivo de topología .txt a cargar")
    p.add_argument("--config", help="archivo de configuración .red a cargar")
    p.add_argument("--monitoreo", help="archivo de monitoreo a procesar")
    p.add_argument("--ruta", nargs=2, metavar=("ORIGEN", "DESTINO"), help="mostrar la ruta más corta y salir")
    p.add_argument("--reporte", metavar="CARPETA", help="exportar reporte e imágenes en CARPETA y salir")
    return p


def main(argv=None):
    configurar_consola()
    args = crear_argumentos().parse_args(argv)
    no_interactivo = bool(args.ruta or args.reporte)
    app = Aplicacion(interactiva=not no_interactivo)
    try:
        if args.red and not app.ejecutar_seguro(app.opcion_cargar_topologia, args.red):
            return 1
        if args.config and not app.ejecutar_seguro(app.opcion_cargar_config, args.config):
            return 1
        if args.monitoreo and not app.ejecutar_seguro(app.opcion_monitoreo, args.monitoreo):
            return 1
        if args.ruta:
            if not app.hay_grafo():
                return 1
            o, d = args.ruta
            for n in (o, d):
                if not app.grafo.existe(n):
                    print(f"{NO} No existe el dispositivo '{n}'.")
                    return 1
            g = app.grafo_operativo()
            if not (g.existe(o) and g.existe(d)):
                print(f"{NO} No existe ruta: el origen o el destino está en Falla.")
                return 1
            r = alg.ruta_mas_corta(g, o, d)
            print(f"Ruta: {flecha(r[0])}    Latencia total: {r[1]} ms" if r else f"{NO} No existe ruta entre {o} y {d}.")
        if args.reporte:
            app.ejecutar_seguro(app.opcion_exportar, args.reporte)
        if not no_interactivo:
            app.ejecutar()
    except Salir:
        pass
    print("\nHasta luego.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
