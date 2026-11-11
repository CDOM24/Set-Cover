# Reproducibilidad y trazabilidad

La referencia principal es el PDF definitivo de 20 páginas incluido en esta carpeta. Su SHA-256 es `e4bfc2b9c7f0c5e69c72c0e24522b8a195bac5d2870584e0a208b15fddfaca55`; es distinto del PDF local anterior.

Los algoritmos y validadores reutilizados conservan su contenido verificado. Las dos pruebas históricas que leían copias duplicadas de datos se adaptaron a `datos/`; el manifiesto registra el hash base y la adaptación. Los resultados, selecciones, logs y figuras copiados conservan sus bytes originales.

`resultados/procedencia.json` relaciona cada archivo copiado con su origen relativo y SHA-256. `resultados/indice.json` identifica 26 resultados mediante esquemas explícitos. El catálogo separa mejor AG, mejor global y mejor cota, y vuelve a abrir CSV y Excel para auditar cobertura y costos con sumas Python/Decimal.

La Fase 4 conserva su conclusión de costo 49.051 y cota 31.562. Las investigaciones posteriores agregan costo 48.878 (HiGHS) y cota 34.532,73615154492 (SCIP). No se edita el JSON histórico para actualizarlo. La selección final de ambos experimentos posteriores es la misma; SCIP la recibió como inicio.

HiGHS adicional utilizó 1 hilo, semilla 0, presolve y esfuerzo heurístico 0,05, con inicio 49.051 y gaps cero. El presupuesto global era 7.200 s; la llamada duró 7.193,594 s y terminó por tiempo con 287.367 nodos y cota 33.433. El supervisor registró cierre forzado después de exportar el resultado final y sus auditorías; se conserva esa discrepancia en los archivos de evidencia.

SCIP recibió 48.878, con 1 hilo, semilla 0 y gaps cero. Su piloto se extendió sobre el mismo modelo en memoria según el protocolo incluido, con un reinicio automático interno. Las llamadas sumaron 7.160,923 s monotónicos; el reloj interno marcó 7.162 s. Sus 102.702 nodos totales incluyen el tramo anterior al reinicio. El archivo final conserva un campo heredado que dice parcial; el tipo de resultado, el estado nativo y el cierre del supervisor confirman el término por tiempo. No hay recuperación validada del árbol desde disco.

Las brechas nativas se conservan. SCIP informa alrededor de 41,54 % usando otro denominador; 100(U−L)/U da 29,3491 % para la misma pareja de cotas. Se usa la cota completa para calcular, aunque se muestre 34.532,74. No equivale a conocer el error real respecto del óptimo.

Verificar la entrega no requiere nuevas búsquedas: `python -m setcover.cli verificar`. Para ejecutarlas localmente existen interfaces separadas y límites explícitos. La CLI genérica no automatiza el piloto/continuación ni recupera los árboles anteriores; una réplica estricta exige aplicar el protocolo y parámetros conservados. Versiones, hardware, presupuestos, tiempos y semillas están en los JSON y logs. Cambios de plataforma, recursos y límites temporales pueden cambiar selecciones, nodos y tiempos incluso con semillas iguales.

La carpeta pública contiene únicamente evidencia relacionada con los resultados. No incluye las herramientas de instalación, entornos virtuales, instrucciones de operación internas ni los supervisores de Windows. Tampoco incluye resultados nuevos inventados o campañas adicionales.
La revisión de presentación adapta únicamente los enlaces y delimitadores matemáticos de modelo_matematico.md. El manifiesto conserva su hash original, el commit público de referencia y el hash actualizado. Los algoritmos, datos, resultados, registros y PDF mantienen sus bytes. La interfaz pública consulta resultados; no ofrece carga de archivos ni demostraciones.
