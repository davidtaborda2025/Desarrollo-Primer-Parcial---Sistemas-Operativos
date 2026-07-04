class Proceso:
    def __init__(self, etiqueta, bt, at, q, prioridad):
        self.etiqueta = str(etiqueta)
        self.bt = float(bt)
        self.at = float(at)
        self.q = int(q)
        self.prioridad = int(prioridad)

        self.tiempo_restante = self.bt
        self.rt = -1.0
        self.ct = 0.0
        self.tat = 0.0
        self.wt = 0.0

class SimuladorMLQ:
    def __init__(self):
        self.procesos = []
        self.q1 = []  # RR(3)
        self.q2 = []  # RR(5)
        self.q3 = []  # Prioridad (5 > 1)

    def cargar_procesos(self, ruta_archivo):
        with open(ruta_archivo, 'r') as f:
            for linea in f:
                if linea.startswith('#') or not linea.strip():
                    continue
                partes = linea.strip().split(';')
                if len(partes) >= 5:
                    proc = Proceso(partes[0].strip(), partes[1], partes[2], partes[3], partes[4])
                    self.procesos.append(proc)

    def simular(self):
        tiempo_actual = 0.0
        procesos_por_llegar = sorted(self.procesos, key=lambda x: x.at)
        procesos_terminados = []

        proceso_en_cpu = None
        quantum_restante = 0
        cola_actual_cpu = 0

        while procesos_por_llegar or self.q1 or self.q2 or self.q3 or proceso_en_cpu:
            # 1. Cargar los procesos que entran en este instante de tiempo
            llegados = [p for p in procesos_por_llegar if p.at <= tiempo_actual]
            for p in llegados:
                if p.q == 1: self.q1.append(p)
                elif p.q == 2: self.q2.append(p)
                elif p.q == 3: self.q3.append(p)
                procesos_por_llegar.remove(p)

            # Ordenar la Q3 internamente por Prioridad de mayor a menor
            self.q3.sort(key=lambda x: x.prioridad, reverse=True)

            # 2. Verificar expropiación por prioridad estricta entre colas
            if proceso_en_cpu:
                if self.q1 and cola_actual_cpu > 1:
                    self.reencolar(proceso_en_cpu, cola_actual_cpu)
                    proceso_en_cpu = None
                elif self.q2 and cola_actual_cpu == 3:
                    self.reencolar(proceso_en_cpu, cola_actual_cpu)
                    proceso_en_cpu = None
                elif quantum_restante <= 0 and cola_actual_cpu in [1, 2]:
                    self.reencolar(proceso_en_cpu, cola_actual_cpu)
                    proceso_en_cpu = None

            # 3. Asignar CPU al proceso correspondiente si está libre
            if not proceso_en_cpu:
                if self.q1:
                    proceso_en_cpu = self.q1.pop(0)
                    quantum_restante = 3
                    cola_actual_cpu = 1
                elif self.q2:
                    proceso_en_cpu = self.q2.pop(0)
                    quantum_restante = 5
                    cola_actual_cpu = 2
                elif self.q3:
                    proceso_en_cpu = self.q3.pop(0)
                    quantum_restante = float('inf')
                    cola_actual_cpu = 3

                if proceso_en_cpu and proceso_en_cpu.rt == -1.0:
                    proceso_en_cpu.rt = tiempo_actual - proceso_en_cpu.at

            # 4. Incrementar tiempos de espera (WT) "a ojo" para los que están en colas
            for p in self.q1: p.wt += 1
            for p in self.q2: p.wt += 1
            for p in self.q3: p.wt += 1

            # 5. Ejecutar la unidad de tiempo en la CPU
            if proceso_en_cpu:
                proceso_en_cpu.tiempo_restante -= 1
                quantum_restante -= 1
                tiempo_actual += 1

                if proceso_en_cpu.tiempo_restante <= 0:
                    proceso_en_cpu.ct = tiempo_actual
                    proceso_en_cpu.tat = proceso_en_cpu.ct - proceso_en_cpu.at
                    procesos_terminados.append(proceso_en_cpu)
                    proceso_en_cpu = None
            else:
                tiempo_actual += 1

        self.procesos = procesos_terminados
        self.mostrar_resultados()

    def reencolar(self, proc, cola):
        if cola == 1: self.q1.append(proc)
        elif cola == 2: self.q2.append(proc)
        elif cola == 3: self.q3.append(proc)

    def mostrar_resultados(self):
        print("# archivo: mlq002.txt")
        print("# etiqueta; BT; AT; Q; Pr; WT; CT; RT; TAT")

        sum_wt, sum_ct, sum_rt, sum_tat = 0, 0, 0, 0
        for p in sorted(self.procesos, key=lambda x: x.etiqueta):
            print(f"{p.etiqueta};{int(p.bt)};{int(p.at)};{p.q};{p.prioridad};{int(p.wt)};{int(p.ct)};{int(p.rt)};{int(p.tat)}")
            sum_wt += p.wt
            sum_ct += p.ct
            sum_rt += p.rt
            sum_tat += p.tat

        n = len(self.procesos)
        print(f"# WT={sum_wt/n:.1f}; CT={sum_ct/n:.1f}; RT={sum_rt/n:.1f}; TAT={sum_tat/n:.1f};")

# Para ejecutarlo:
# sim = SimuladorMLQ()
# sim.cargar_procesos("mlq001.txt")
# sim.simular()

if __name__ == "__main__":
    sim = SimuladorMLQ()
    sim.cargar_procesos("mlq002.txt")
    sim.simular()