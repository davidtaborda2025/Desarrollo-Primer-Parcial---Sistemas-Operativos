# Desarrollo Parcial 1 de Sistemas Operativos por David Taborda Montenegro (202242264-3743).

from typing import Any, Callable, List, Optional, Tuple
import os
import sys

class Proceso:
    """Modela el Bloque de Control de Procesos (PCB) dentro del simulador.

    Encapsula los atributos nativos del proceso cargado desde el archivo de entrada y gestiona de manera autónoma el
    estado de sus métricas temporales y de sincronía a lo largo del ciclo de vida en la CPU.
    """

    def __init__(self, etiqueta: Any, bt: float | int, at: float | int, q: int, prioridad: int) -> None:
        """Inicializa un nuevo proceso y configura su estado inicial de PCB.

        Args:
            etiqueta: Identificador alfanumérico único del proceso (ej. 'P1'). Es decir, su PID.
            bt: Burst Time (Ráfaga de CPU inicial requerida por el proceso).
            at: Arrival Time (Instante de tiempo global en el que arriba a la cola de listos).
            q: Nivel de cola de prioridad estricta asignado (1, 2 ó 3).
            prioridad: Nivel de prioridad interna del proceso.
        """
        self.etiqueta: str = str(etiqueta)
        self.bt: float = float(bt)
        self.at: float = float(at)
        self.q: int = int(q)
        self.prioridad: int = int(prioridad)

        # Variables de control de métricas calculadas.
        self.tiempo_restante: float = self.bt
        self.rt: float = -1.0  # Se inicializa en -1.0, para denotar que el proceso no ha tocado la CPU.
        self.ct: float = 0.0
        self.tat: float = 0.0
        self.wt: float = 0.0

    def registrar_primer_toque(self, tiempo_actual: float) -> None:
        """Registra el Response Time (RT) en el primer encuentro con la CPU.

        Garantiza que el tiempo de respuesta capture el instante exacto del reloj global únicamente cuando el proceso
        pasa del estado de 'Listo' a 'Ejecución' por primera vez, es decir, cuando 'toca' por primera vez la CPU.

        Args:
            tiempo_actual: Valor actual del reloj global del simulador.
        """
        if self.rt == -1.0:
            self.rt = tiempo_actual

    def finalizar(self, tiempo_actual: float) -> None:
        """Calcula y consolida las métricas temporales finales del proceso.

        Se ejecuta en el momento exacto en que el tiempo restante de ráfaga llega a cero, calculando el tiempo de
        completado (CT), Turn Around Time (TAT) y tiempo de espera (WT).

        Args:
            tiempo_actual: Instante del reloj global donde el proceso termina su ejecución.
        """
        self.ct = tiempo_actual
        self.tat = self.ct - self.at
        self.wt = self.tat - self.bt

class ColaMLQ:
    """Representa la estructura de datos de una cola FIFO, que podrá adaptarse para comportamiento circular o de prioridad.

    Esta estructura encapsula una lista dinámica para comportarse estrictamente como una cola FIFO (First-In, First-Out),
    abstrayendo las políticas de planificación internas (Round Robin o Prioridad) y administrando de forma autónoma su
    subconjunto de procesos listos.
    """

    def __init__(self, numero_cola: int, tipo_algoritmo: str, quantum: Optional[float]= None) -> None:
        """Inicializa la cola de planificación con su política de asignación.

        Args:
            numero_cola: Identificador de la cola (1, 2 o 3).
            tipo_algoritmo: Identificador del algoritmo de despacho ("RR" o "PRIORITY").
            quantum: Tiempo máximo de asignación de CPU continuo (requerido para "RR").
        """
        self.numero_cola: int = numero_cola
        self.tipo_algoritmo: str = tipo_algoritmo  # "RR" o "PRIORITY".
        self.quantum: Optional[float] = quantum
        self.procesos_listos: List[Proceso] = []  # Estructura de almacenamiento interno.

    def insertar(self, proceso: Proceso) -> None:
        """Inserta un proceso al final de la cola (Operación Enqueue).

        Garantiza de forma estricta el comportamiento FIFO al ingresar las nuevas ráfagas o reencolar procesos expropiados
        al final de la cola.

        Args:
            proceso: Instancia del objeto Proceso (PCB) a encolar.
        """
        self.procesos_listos.append(proceso)

    def tiene_procesos(self) -> bool:
        """Determina si la cola cuenta con procesos en estado de 'Listo'.

        Returns:
            True si hay procesos esperando en la fila, False en caso contrario.
        """
        return len(self.procesos_listos) > 0

    def ejecutar_proceso(self, tiempo_actual: float, por_llegar: List[Proceso], registrar_arribos_cb: Callable[[float, List[Proceso]], None]) -> Tuple[float, Optional[Proceso]]:
        """Despacha y ejecuta el proceso al frente de la cola según su política.

        Aplica encapsulamiento al resolver internamente el ordenamiento por prioridades (si aplica) y la reducción del tiempo
        restante de ráfaga.
        Utiliza un callback para sincronizar los arribos en el reloj global durante ejecuciones extendidas.

        Args:
            tiempo_actual: Valor actual del reloj global unificado del sistema.
            por_llegar: Lista de procesos globales que aún no han arribado.
            registrar_arribos_cb: Función callback del simulador para registrar llegadas.

        Returns:
            Una tupla que contiene:
                - float: El nuevo estado del reloj global tras la ejecución.
                - Optional[Proceso]: El objeto Proceso si este finalizó su BT, o None si fue reencolado por quántum.
        """
        if not self.tiene_procesos():
            return tiempo_actual, None

        # Si es la cola 3, aplicamos prioridad interna antes de despachar.
        if self.tipo_algoritmo == "PRIORITY":
            self.procesos_listos.sort(key=lambda x: -x.prioridad)

        # Operación Dequeue: Se extrae estrictamente el primer elemento de la estructura FIFO.
        p: Proceso = self.procesos_listos.pop(0)
        p.registrar_primer_toque(tiempo_actual)

        if self.tipo_algoritmo == "RR":
            # Para asegurar que, en este punto, sí se maneje un quantum existente.
            quantum_seguro: float = float(self.quantum) if self.quantum is not None else 0.0

            # Planificación por Round Robin (Q1 y Q2).
            q_efectivo: float = min(quantum_seguro, p.tiempo_restante)
            p.tiempo_restante -= q_efectivo
            tiempo_actual += q_efectivo

            # Capturar procesos que llegaron durante esta ráfaga de RR.
            registrar_arribos_cb(tiempo_actual, por_llegar)

            if p.tiempo_restante <= 0:
                p.finalizar(tiempo_actual)
                return tiempo_actual, p

            else:
                self.procesos_listos.append(p)  # Reencolado circular FIFO.
                return tiempo_actual, None

        elif self.tipo_algoritmo == "PRIORITY":
            # Planificación por Prioridad No Expropiativa (Q3).
            tiempo_actual += p.tiempo_restante
            p.tiempo_restante = 0.0

            # Capturar procesos que llegaron durante toda la ejecución del proceso.
            registrar_arribos_cb(tiempo_actual, por_llegar)
            p.finalizar(tiempo_actual)
            return tiempo_actual, p

        return tiempo_actual, None

class SimuladorMLQFinal:
    """Orquestador central del simulador de Planificación Multinivel (MLQ).

    Tiene la responsabilidad responsabilidad única (SRP) al coordinar de forma sincrónica el flujo del reloj global unificado,
    la captura de llegadas a la CPU, la delegación de la CPU a las colas y la persistencia física de los reportes de salida.
    """

    def __init__(self) -> None:
        """Inicializa el entorno del simulador y configura las colas con sus algoritmos internos."""
        self.procesos_globales: List[Proceso] = []
        self.nombre_archivo: str = ""

        # Definición formal de las colas para MLQ, manteniendo el orden definido.
        self.colas: List[ColaMLQ] = [
            ColaMLQ(1, "RR", quantum=3.0),  # Q1 - Round Robin con q = 3.0
            ColaMLQ(2, "RR", quantum=5.0),  # Q2 - Round Robin con q = 5.0
            ColaMLQ(3, "PRIORITY")  # Q3 - Prioridad No Expropiativa (5 > 1).
        ]

    def cargar_procesos(self, ruta_archivo: str) -> None:
        """Lee el archivo plano de entrada e instancia los objetos PCB.

        Limpia espacios en blanco, ignora líneas de comentarios generadas por las cabeceras y encapsula los datos en la
        estructura central.

        Args:
            ruta_archivo: Ruta física o nombre del archivo de texto (.txt).
        """
        self.nombre_archivo = os.path.basename(ruta_archivo)
        with open(ruta_archivo, 'r') as f:
            for linea in f:
                if linea.startswith('#') or not linea.strip():
                    continue
                partes: List[str] = linea.strip().split(';')
                if len(partes) >= 5:
                    # Instanciación del PCB con los datos del archivo de entrada.
                    proc = Proceso(partes[0].strip(), float(partes[1]), float(partes[2]), int(partes[3]), int(partes[4]))
                    self.procesos_globales.append(proc)

    def _registrar_arribos(self, tiempo_actual: float, por_llegar: List[Proceso]) -> None:
        """Monitorea y distribuye los procesos entrantes.

        Actúa como el despachador de interrupciones por reloj. Examina el tiempo de llegada (AT) real y delega el proceso
         a la estructura de cola correspondiente.

        Args:
            tiempo_actual: Instante cronológico actual del reloj global.
            por_llegar: Lista de control de procesos pendientes por llegar al sistema.
        """
        for p in por_llegar[:]:
            if p.at <= tiempo_actual:
                self.colas[p.q - 1].insertar(p)  # Direccionamiento por nivel (q-1).
                por_llegar.remove(p)

    def simular(self) -> None:
        """Ejecuta el ciclo de vida principal de la simulación mediante reloj global unificado.

        Controla de forma estricta las transiciones de estados de la CPU y el orden de las colas, resolviendo de manera
        nativa los momentos en que no hayan procesos en ejecución y el retorno inmediato ante colas superiores mediante
        rupturas de bucle (break).
        """
        por_llegar: List[Proceso] = list(self.procesos_globales)
        procesos_terminados: List[Proceso] = []
        tiempo_actual: float = 0.0
        total_procesos: int = len(por_llegar)

        while len(procesos_terminados) < total_procesos:
            # 1. Registrar arribos en el tiempo actual
            self._registrar_arribos(tiempo_actual, por_llegar)

            # 2. Manejo de tiempos donde no llegan procesos.
            if not any(q.tiene_procesos() for q in self.colas):
                if por_llegar:
                    tiempo_actual = min(proc.at for proc in por_llegar)  # Salto del reloj global al AT pendiente más cercano.
                    continue
                else:
                    break

            # 3. Planificación jerárquica estricta
            for q in self.colas:
                if q.tiene_procesos():
                    # Se delega la ráfaga a la cola pasándole la referencia del método de llegadas (callback).
                    tiempo_actual, proc_finalizado = q.ejecutar_proceso(
                        tiempo_actual, por_llegar, self._registrar_arribos
                    )

                    if proc_finalizado:
                        procesos_terminados.append(proc_finalizado)

                    # Ruptura Crítica: Obliga al sistema a reevaluar Q1 inmediatamente después de que una ráfaga termine,
                    # impidiendo expropiaciones ilegales en medio de quántums.
                    break

        self.procesos_globales = procesos_terminados
        self.guardar_e_imprimir_resultados()

    def guardar_e_imprimir_resultados(self) -> None:
        """Consolida las métricas del sistema, genera reportes en consola y escribe el archivo .txt."""
        archivo_salida: str = f"metrics_{self.nombre_archivo}"
        sum_wt: float = 0.0
        sum_ct: float = 0.0
        sum_rt: float = 0.0
        sum_tat: float = 0.0

        procesos_ordenados: List[Proceso] = sorted(self.procesos_globales, key=lambda x: x.etiqueta)
        n: int = len(procesos_ordenados)

        for p in procesos_ordenados:
            sum_wt += p.wt
            sum_ct += p.ct
            sum_rt += p.rt
            sum_tat += p.tat

        # Para la impresión de los valores promedio con un decimal.
        linea_promedios: str = f"# WT={sum_wt/n:.1f}; CT={sum_ct/n:.1f}; RT={sum_rt/n:.1f}; TAT={sum_tat/n:.1f};\n"

        # Reporte 1: Para mostrar los valores en consola.
        print(f"# Archivo: {self.nombre_archivo}")
        print("# Etiqueta; BT; AT; Q; Pr; WT; CT; RT; TAT")
        for p in procesos_ordenados:
            print(f"{p.etiqueta};{int(p.bt)};{int(p.at)};{p.q};{p.prioridad};{int(p.wt)};{int(p.ct)};{int(p.rt)};{int(p.tat)}")
        print(linea_promedios.strip())

        # Reporte 2: Para guardar los valores en un archivo .txt.
        with open(archivo_salida, 'w') as f:
            f.write(f"# Archivo: {self.nombre_archivo}\n")
            f.write("# Etiqueta; BT; AT; Q; Pr; WT; CT; RT; TAT\n")
            for p in procesos_ordenados:
                f.write(f"{p.etiqueta};{int(p.bt)};{int(p.at)};{p.q};{p.prioridad};{int(p.wt)};{int(p.ct)};{int(p.rt)};{int(p.tat)}\n")
            f.write(linea_promedios)

if __name__ == "__main__":
    # Configuración de entrada inteligente, para funcionar en llamados tanto por consola interna como externa.
    if len(sys.argv) >= 2:
        archivo_objetivo: str = sys.argv[1]
    else:
        archivo_objetivo = "mlq001.txt"  # Por defecto, se carga el archivo de prueba mlq001.txt

    sim = SimuladorMLQFinal()
    sim.cargar_procesos(archivo_objetivo)
    sim.simular()