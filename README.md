# Simulador de Planificación de Procesos con Algoritmo de Colas Multinivel (MLQ)

Este repositorio contiene la implementación formal, robusta y modular de un simulador para el algoritmo de planificación de CPU **Colas Multinivel (MLQ)**, desarrollado bajo el paradigma Orientado a Objetos (POO) siguiendo las directrices de la convención oficial **PEP 8** y el estándar de documentación *Docstrings* estilo Google.

Desarrollo realizado por el estudiante David Taborda Montenegro (202242264-3743), para el componente práctico del Parcial No. 1 de la asignatura **Sistemas Operativos** en la **Universidad del Valle**.

## Arquitectura de la Solución
El código se basa en la aplicación de POO, segregando sus responsabilidades en tres estructuras de clases altamente cohesivas:
* **`Proceso`:** Representación lógica del Bloque de Control de Procesos (PCB), gestionando atómicamente sus métricas ($WT$, $CT$, $RT$, $TAT$).
* **`ColaMLQ`:** Abstracción de una estructura de datos abstracta de almacenamiento que restringe arreglos dinámicos internos bajo una estricta política FIFO (First-In, First-Out), mutando condicionalmente a colas circular y de prioridad.
* **`SimuladorMLQFinal`:** Orquestador central del tiempo a través de un reloj global unificado, respaldado por un mecanismo de sincronización mediante *Funciones Callback* para gestionar llegadas concurrentes por "oleadas".

## Estructura del Repositorio
* `simulador_scheduler_mlq.py`: Archivo de código fuente principal que contiene la lógica de ejecución.
* `mlq001.txt`, `mlq006.txt`, `mlq019.txt`: Escenarios estándar provistos por una carpeta de Google Drive en el enunciado del parcial.
* `mlq_david_final.txt`: Escenario personalizado diseñado originalmente para validación funcional del simulador.

## Instrucciones de Ejecución

El código cuenta con una interfaz híbrida inteligente que permite su ejecución fluida tanto en entornos de desarrollo (IDE) como en consola de línea de comandos.

### Opción 1: Ejecución directa en IDE (IntelliJ IDEA / VS Code)
Simplemente abrir la carpeta del proyecto en su entorno de desarrollo y presione el botón de reproducción (**Play**). Por defecto, el simulador se ejecutará y validará los resultados utilizando el escenario de control `mlq001.txt`.

### Opción 2: Ejecución por Terminal de Comandos
Pasarse al directorio del proyecto y ejecutar el código añadiendo el nombre de cualquiera de los archivos de entrada disponibles:

```bash
python simulador_scheduler_mlq.py mlq001.txt
python simulador_scheduler_mlq.py mlq006.txt
python simulador_scheduler_mlq.py mlq019.txt
python simulador_scheduler_mlq.py mlq_personalizado.txt