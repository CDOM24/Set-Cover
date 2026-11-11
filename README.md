# SET COVER — Investigación de Operaciones I

Proyecto de **Carlos Daniel Oliva Moreno** y **Camilo Andrés Oliva Moreno**, Universidad Autónoma de Bucaramanga (UNAB), para Investigación de Operaciones I.

## Aplicación interactiva

**[Explorar SET COVER en el navegador](https://set-cover-coliva.streamlit.app/)**

Consulta las antenas seleccionadas, explora la cobertura de los 500 clientes y compara el método exacto con el algoritmo genético. La aplicación también explica el modelo matemático y la metodología del proyecto.

## El problema

Tenemos **500 clientes y 500 ubicaciones posibles para instalar antenas**. Cada ubicación tiene un costo y cubre un conjunto de clientes. Buscamos elegir las antenas de menor costo total que cubran a todos los clientes al menos una vez. La cobertura puede superponerse: minimizar el costo no equivale a minimizar el número de antenas.

La matriz CSV indica quién cubre a quién; el Excel contiene los costos. Adoptamos la correspondencia por posición **columna 0 del CSV ↔ antena 1 del Excel**, hasta la columna 499 y la antena 500. Su estructura se verificó, pero la identidad física de esa asociación no fue confirmada por el profesor.

## Dos métodos sobre los mismos datos

El **método exacto** formula 500 decisiones binarias y una restricción de cobertura por cliente. HiGHS y SCIP buscan soluciones y calculan cotas inferiores para intentar demostrar la optimalidad.

El **algoritmo genético** evoluciona una población de selecciones mediante torneo, cruce, mutación y elitismo. Repara las coberturas faltantes y elimina antenas redundantes. Puede encontrar buenas instalaciones, pero no certifica el óptimo.

## Resultados principales

| Ejecución | Costo factible | Antenas | Cobertura | Tiempo individual | Cota inferior |
|---|---:|---:|---:|---:|---:|
| HiGHS inicial | 49.734 | 21 | 500/500 | 600,018 s | 31.318 |
| Mejor algoritmo genético | **49.051** | 22 | 500/500 | **5,718 s** | — |
| HiGHS posterior | **48.878** | 22 | 500/500 | 7.193,594 s | 33.433 |
| SCIP posterior | 48.878 | 22 | 500/500 | 7.160,923 s | **34.532,74** |

**No se ha certificado el óptimo global.** El mejor AG es 49.051; la mejor solución factible conocida, 48.878, la encontró HiGHS después. SCIP recibió esa selección y elevó la cota inferior a 34.532,73615154492. La separación entre cotas es **29,3491 %**, calculada como `(U − L) / U × 100`; no es el error real respecto de un óptimo conocido.

Los presupuestos y soluciones iniciales fueron distintos. Los 5,718 s corresponden a una corrida genética, no al tiempo de toda la campaña. La aplicación permite explorar las **26 corridas**, consultar las antenas y comparar los resultados sin ejecutar nuevas búsquedas.

## Cómo recorrer la entrega

- **[Aplicación visual](https://set-cover-coliva.streamlit.app/):** Inicio, Problema y datos, Método exacto, Algoritmo genético, Comparación y Metodología.
- **[Código](setcover/):** modelo exacto, algoritmo genético, cargadores y validaciones. La interfaz está en [app.py](app.py).
- **[Datos](datos/):** matriz y costos originales.
- **[Resultados](resultados/):** selecciones, parámetros, registros y figuras. El [índice](resultados/indice.json) identifica las 26 corridas y el [manifiesto](resultados/procedencia.json) permite comprobar su procedencia.
- **[Modelo matemático](docs/modelo_matematico.md)** y **[guía de uso](docs/GUIA_USO.md):** apoyo para comprender y explicar el proyecto.

## Recursos y comprobaciones

- **[Informe definitivo · 20 páginas](docs/Informe_Proyecto_Oliva_Moreno.pdf):** investigación completa, conclusiones y referencias. Se conserva sin cambios.
- **[GitHub Actions](https://github.com/CDOM24/Set-Cover/actions/workflows/pruebas.yml):** consulta el resultado de las pruebas automáticas. La versión publicada de la aplicación aprobó las **110 pruebas en Linux**.

## Ejecución local

Requiere **Python 3.12 de 64 bits**. Descarga este repositorio como ZIP o clónalo y entra en su carpeta:

```bash
git clone https://github.com/CDOM24/Set-Cover.git
cd Set-Cover
python -m venv .venv
```

En Windows (PowerShell), sin activar el entorno:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

En Linux/macOS:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Abre la dirección local que indique Streamlit. La aplicación consulta los resultados guardados; no incluye carga de archivos ni demostraciones de optimización.

Para verificar los datos y ejecutar las pruebas, usa el Python del entorno:

```bash
python -m pip install -r requirements-dev.txt
python -m setcover.cli verificar
python -m pytest -q
```

En Windows sustituye `python` por `.\.venv\Scripts\python.exe`; en Linux/macOS, por `.venv/bin/python`. Las pruebas de optimización usan casos pequeños, sin repetir las campañas históricas. [Condiciones de reproducibilidad](docs/REPRODUCIBILIDAD.md).
