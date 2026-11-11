# Formulación del SET COVER ponderado

## Datos, índices y variables

Sea I = {1,…,500} el conjunto de clientes y J = {1,…,500} el de ubicaciones posibles.

- Aᵢⱼ = 1 si la antena j cubre al cliente i, y 0 en caso contrario. Es un dato del CSV.
- cⱼ ≥ 0 es el costo de instalar la antena j, tomado de Excel según el supuesto de correspondencia explícito documentado.
- xⱼ ∈ {0,1} es la decisión: 1 instala la antena j; 0 la descarta.

Las filas representan clientes y las columnas antenas según la interpretación del enunciado conservada en el [informe definitivo](Informe_Proyecto_Oliva_Moreno.pdf). Por ser una matriz cuadrada, su forma por sí sola no demuestra la orientación: la interpretación procede del enunciado. No se cambia por conveniencia del programa.

## Función objetivo

$$
\min_{x}\; Z = \sum_{j=1}^{500} c_j x_j.
$$

Cada instalación suma su costo una sola vez. Minimizar el número de antenas sería un problema diferente cuando los costos no son iguales. No se presupone moneda ni unidad monetaria que el profesor no haya indicado.

## Restricciones

$$
\sum_{j=1}^{500} A_{ij}x_j \geq 1
\qquad \forall i\in I,
$$

$$
x_j\in\{0,1\}\qquad \forall j\in J.
$$

Cada suma cuenta cuántas antenas instaladas cubren al cliente i. Se requiere al menos una. Se permite cobertura superpuesta; imponer igualdad a 1 excluiría soluciones válidas de SET COVER. La binariedad evita instalar fracciones de una antena o contabilizarla varias veces.

El modelo tiene 500 decisiones binarias y 500 restricciones de cobertura, además de los dominios. Es programación lineal entera binaria: objetivo y restricciones son lineales, con decisiones discretas. Su relajación continua reemplazaría la binariedad por 0 ≤ xⱼ ≤ 1 y podría dar antenas fraccionarias; no es la solución de instalación requerida.

## Notación matricial y correspondencia

$$
\min c^T x,\qquad Ax\geq\mathbf{1},\qquad x\in\{0,1\}^{500}.
$$

En Python, la posición k de un vector comienza en cero. La columna almacenada k conserva su etiqueta CSV. El índice matemático j=k+1 es una convención de escritura; no demuestra que esa misma columna deba tomar el costo del ID Excel j. Para asociar los archivos se adoptó una regla explícita como supuesto autorizado por el estudiante, sin atribuirla al profesor.

Bajo la regla ordinal autorizada, la primera columna (etiqueta CSV 0) toma el costo de conjunto Excel 1 en B2, y la última (etiqueta CSV 499) toma el de conjunto 500 en SG2. La aplicación muestra las 500 asociaciones en Problema y datos, a partir de [la matriz y el Excel originales](../datos/). La función `load_inputs` de [catalog.py](../setcover/catalog.py) construye la correspondencia y la verifica con los cargadores de datos. [El manifiesto de procedencia](../resultados/procedencia.json) conserva los hashes de los originales y [la validación de datos](VALIDACION_DATOS.json) documenta las comprobaciones. La consistencia estructural se comprobó; la identidad física de las ubicaciones permanece como supuesto.

## Supuestos y factibilidad

Se utiliza solo la cobertura binaria suministrada. No se inventan posiciones geográficas, radios, capacidades, demandas, interferencias, presupuestos ni límites de instalaciones.

Con estos únicos requisitos y costos finitos, el modelo es factible si y solo si toda fila contiene al menos un 1. Necesidad: una fila nula no puede alcanzar cobertura 1 con ninguna selección. Suficiencia: seleccionar todas las antenas cubre todas las filas no nulas. Esta observación comprueba existencia de cobertura; no encuentra la instalación más económica.

El verificador independiente revisa Ax ≥ 1 y recalcula cᵀx. Una selección factible no constituye prueba de optimalidad. Ninguna de las corridas conservadas certificó el óptimo global; véanse el [índice de resultados](../resultados/indice.json) y el informe definitivo.

## Ejemplo SINTÉTICO DE PRUEBA

Este ejemplo no corresponde a los datos del profesor:

$$
A=\begin{pmatrix}1&0&1\\1&1&0\\0&1&1\end{pmatrix},
\quad c=(2,3,2),\quad x=(1,0,1).
$$

La selección cubre a los tres clientes y cuesta 4. Ninguna antena individual cubre los tres. Toda pareja cuesta como mínimo 4, alcanzado por la primera y tercera antena; las tres cuestan 7. Por tanto, el óptimo de este ejemplo es 4. El test enumera sus ocho cromosomas para comprobarlo. No se realiza enumeración sobre las 500 antenas reales.
