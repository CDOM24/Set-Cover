# Guía de uso y explicación

1. **Resumen:** distinguir 49.051 del AG, 48.878 encontrado por HiGHS y 34.532,74 como cota de SCIP. No decir que encontramos el óptimo.
2. **Datos y soluciones:** explorar las 22 antenas, su costo individual y la cobertura de cada cliente. Explicar el supuesto CSV j ↔ Excel j+1.
3. **Método exacto:** mostrar la función objetivo, las coberturas y las binarias. Una solución factible da una cota superior; el árbol produce cotas inferiores y no cerró la diferencia.
4. **Algoritmo genético:** cromosoma de 500 bits, torneo, cruce, mutación, elitismo, reparación y poda. La reparación garantiza cobertura de los individuos admitidos; no garantiza optimalidad.
5. **Comparación:** observar todas las semillas. El mejor caso y el promedio son conceptos distintos. El tiempo de una corrida no es el esfuerzo de toda la campaña.
6. **Informe:** descargar el PDF definitivo. La captura que aparece en él corresponde a la interfaz histórica; los números nuevos están en la interfaz actualizada.

Consultar las páginas no inicia optimizadores. Las demostraciones están desactivadas por defecto, no son necesarias para defender los resultados y no sustituyen las corridas del informe.

## Preguntas clave

- ¿Por qué 22 antenas pueden ser más baratas que 21? Porque los costos individuales son diferentes.
- ¿Por qué no imponer cobertura igual a uno? Se permite que varias antenas cubran un cliente.
- ¿48.878 es el óptimo? No se sabe; es la mejor instalación verificada conocida.
- ¿Qué aportó SCIP? La cota inferior de 34.532,74; recibió como inicio la instalación de 48.878.
- ¿Qué significa el 29,3491 %? Separación normalizada entre cotas, no error conocido respecto del óptimo.
- ¿Puede retomarse exactamente el árbol terminado? No hay un mecanismo validado de recuperación desde disco.