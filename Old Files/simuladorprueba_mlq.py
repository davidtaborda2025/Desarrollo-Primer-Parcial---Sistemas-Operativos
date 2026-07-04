import os

class Proceso:
    def __init__(self, etiqueta, bt, at, q, prioridad):
        self.etiqueta = str(etiqueta)
        self.bt = float(bt)
        self.at = float(at)
        self.q = int(q)
        self.prioridad = int(prioridad)

        # Variables de control de métricas calculadas "a ojo"
        self.tiempo_restante = self.bt
        self.rt = -1.0
        self.ct = 0.0
        self.tat = 0.0
        self.wt = 0.0

class SimuladorMLQFinal:
    def __init__(self):
        self.procesos_globales = []
        self.nombre_archivo = ""

    def cargar_procesos(self, ruta_archivo):
        self.nombre_archivo = os.path.basename(ruta_archivo)
        with open(ruta_archivo, 'r') as f:
            for linea in f:
                if linea.startswith('#') or not linea.strip():
                    continue
                partes = linea.strip().split(';')
                if len(partes) >= 5:
                    proc = Proceso(partes[0].strip(), partes[1], partes[2], partes[3], partes[4])
                    self.procesos_globales.append(proc)

    def simular(self):
        # Clonamos la lista de procesos original
        por_llegar = list(self.procesos_globales)

        # Colas de listos (cronológicos)
        q1_listos = [] # RR(3)
        q2_listos = [] # RR(5)
        q3_listos = [] # Prioridad No-Expropiativa

        procesos_terminados = []
        tiempo_actual = 0.0
        total_procesos = len(por_llegar)

        while len(procesos_terminados) < total_procesos:

            # 1. Capturar los procesos que van llegando en el tiempo_actual
            for p in por_llegar[:]:
                if p.at <= tiempo_actual:
                    if p.q == 1: q1_listos.append(p)
                    elif p.q == 2: q2_listos.append(p)
                    elif p.q == 3: q3_listos.append(p)
                    por_llegar.remove(p)

            # 2. Si la CPU está ociosa esperando que llegue alguien en el futuro
            if not q1_listos and not q2_listos and not q3_listos:
                if por_llegar:
                    tiempo_actual = min(proc.at for proc in por_llegar)
                    continue
                else:
                    break

            # 3. Planificación por fases estrictas (Jerarquía de colas)
            if q1_listos:
                p = q1_listos.pop(0)

                # RT es el INSTANTE EXACTO de tiempo del reloj global en su primer toque
                if p.rt == -1.0:
                    p.rt = tiempo_actual

                quantum = min(3.0, p.tiempo_restante)
                p.tiempo_restante -= quantum
                tiempo_actual += quantum

                # Actualizar arribos durante la ráfaga
                for proc in por_llegar[:]:
                    if proc.at <= tiempo_actual:
                        if proc.q == 1: q1_listos.append(proc)
                        elif proc.q == 2: q2_listos.append(proc)
                        elif proc.q == 3: q3_listos.append(proc)
                        por_llegar.remove(proc)

                if p.tiempo_restante <= 0:
                    p.ct = tiempo_actual
                    p.tat = p.ct - p.at
                    p.wt = p.tat - p.bt
                    procesos_terminados.append(p)
                else:
                    q1_listos.append(p)

            elif q2_listos:
                p = q2_listos.pop(0)

                # RT es el INSTANTE EXACTO de tiempo del reloj global en su primer toque
                if p.rt == -1.0:
                    p.rt = tiempo_actual

                quantum = min(5.0, p.tiempo_restante)
                p.tiempo_restante -= quantum
                tiempo_actual += quantum

                for proc in por_llegar[:]:
                    if proc.at <= tiempo_actual:
                        if proc.q == 1: q1_listos.append(proc)
                        elif proc.q == 2: q2_listos.append(proc)
                        elif proc.q == 3: q3_listos.append(proc)
                        por_llegar.remove(proc)

                if p.tiempo_restante <= 0:
                    p.ct = tiempo_actual
                    p.tat = p.ct - p.at
                    p.wt = p.tat - p.bt
                    procesos_terminados.append(p)
                else:
                    q2_listos.append(p)

            elif q3_listos:
                # Prioridad interna estricta para los que ya están listos en Q3 (5 > 1)
                q3_listos.sort(key=lambda x: -x.prioridad)
                p = q3_listos.pop(0)

                # RT es el INSTANTE EXACTO de tiempo del reloj global en su primer toque
                if p.rt == -1.0:
                    p.rt = tiempo_actual

                # Al ser No-Expropiativa, corre de largo consumiendo todo su BT
                tiempo_actual += p.tiempo_restante
                p.tiempo_restante = 0

                for proc in por_llegar[:]:
                    if proc.at <= tiempo_actual:
                        if proc.q == 1: q1_listos.append(proc)
                        elif proc.q == 2: q2_listos.append(proc)
                        elif proc.q == 3: q3_listos.append(proc)
                        por_llegar.remove(proc)

                p.ct = tiempo_actual
                p.tat = p.ct - p.at
                p.wt = p.tat - p.bt
                procesos_terminados.append(p)

        self.procesos_globales = procesos_terminados
        self.guardar_e_imprimir_resultados()

    def guardar_e_imprimir_resultados(self):
        archivo_salida = f"solved_{self.nombre_archivo}"
        sum_wt, sum_ct, sum_rt, sum_tat = 0, 0, 0, 0
        procesos_ordenados = sorted(self.procesos_globales, key=lambda x: x.etiqueta)
        n = len(procesos_ordenados)

        for p in procesos_ordenados:
            sum_wt += p.wt
            sum_ct += p.ct
            sum_rt += p.rt
            sum_tat += p.tat

        linea_promedios = f"# WT={sum_wt/n:.1f}; CT={sum_ct/n:.1f}; RT={sum_rt/n:.1f}; TAT={sum_tat/n:.1f};"

        print(f"# archivo: {self.nombre_archivo}")
        print("# etiqueta; BT; AT; Q; Pr; WT; CT; RT; TAT")
        for p in procesos_ordenados:
            print(f"{p.etiqueta};{int(p.bt)};{int(p.at)};{p.q};{p.prioridad};{int(p.wt)};{int(p.ct)};{int(p.rt)};{int(p.tat)}")
        print(linea_promedios)

        with open(archivo_salida, 'w') as f:
            f.write(f"# archivo: {self.nombre_archivo}\n")
            f.write("# etiqueta; BT; AT; Q; Pr; WT; CT; RT; TAT\n")
            for p in procesos_ordenados:
                f.write(f"{p.etiqueta};{int(p.bt)};{int(p.at)};{p.q};{p.prioridad};{int(p.wt)};{int(p.ct)};{int(p.rt)};{int(p.tat)}\n")
            f.write(linea_promedios)

if __name__ == "__main__":
    # Cambia aquí el nombre de tu archivo para procesarlo:
    nombre_archivo_prueba = "mlq002.txt"

    sim = SimuladorMLQFinal()
    sim.cargar_procesos(nombre_archivo_prueba)
    sim.simular()