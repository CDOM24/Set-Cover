# Estado de la entrega pública

Entrega pública autorizada en **CDOM24/Set-Cover**, rama **main**. El contenido aprobado de entrega-publica/ se publica directamente en la raíz, con app.py y requirements.txt. No se modifica el repositorio privado de origen. La aplicación está desplegada en https://set-cover-coliva.streamlit.app/.

## Implementado

Interfaz reorganizada en seis vistas: Inicio, Problema y datos, Método exacto, Algoritmo genético, Comparación y Metodología; métricas separadas de AG 49.051, HiGHS 48.878 y cota SCIP 34.532,74; 26 corridas con hashes; datos originales, informe definitivo de 20 páginas, guías, pruebas y flujo Linux preparado. Se retiraron de la interfaz pública las demostraciones y la carga de archivos. Las herramientas científicas locales y sus pruebas se conservan.

## Python resuelto

Se instaló **Python 3.12.10 oficial**, firmado por Python Software Foundation, en una carpeta nueva del usuario, y se creó un entorno nuevo .venv. Instalador e intérprete tienen firma válida; Smart App Control sigue activado. No se cambió PATH ni se reemplazó el Python portátil anterior.

3.12.10 es la última versión 3.12 con instalador oficial Windows. Se usó para validación local de compatibilidad; los registros históricos conservan su versión 3.12.12. No se presenta 3.12.10 como la revisión de seguridad más reciente. Fuente y firma: docs/INSTALACION_PYTHON_FIRMADO.json.

## Validación histórica de la entrega anterior

- Auditorías PowerShell y Python: las 26 selecciones mantienen costos y cobertura 500/500. Sin óptimo certificado.
- CPython compiló 19 archivos; pip check no encontró incompatibilidades.
- **108 pruebas aprobadas**, incluidas AppTest y separación del mejor AG frente al global; evidencia en docs/pruebas_pytest.xml.
- Primer intento: 107 aprobadas y timeout de 45 s en el arranque inicial de AppTest. Repetición aislada: aprobada en 9,65 s, sin cambio de código o límite; batería completa posterior: 108 aprobadas.
- Edge con perfil aislado: siete vistas, CSV de 22 antenas y costo 48.878, PDF idéntico al original, carga de archivos y rechazo de demostraciones sin aceptar el supuesto.
- Demostraciones web de 1 s: AG 51.846 y MILP 212.146, ambas con cobertura 500/500. Un diagnóstico MILP adicional de 1 s produjo 414.467. Son pruebas fuera del catálogo; no cambian resultados históricos. Un primer ensayo MILP no dejó descarga recuperable y se documentó.
- **238 copias trazadas** con hashes correctos; **1.044 archivos del origen** sin modificaciones.
- Instaladores, entornos, cachés y materiales operativos excluidos de Git. No se repitieron campañas prolongadas.

## Pendiente

El estado real del workflow Linux está en [GitHub Actions](https://github.com/CDOM24/Set-Cover/actions/workflows/pruebas.yml). La versión publicada se encuentra en https://set-cover-coliva.streamlit.app/. Los nuevos ajustes de presentación se comprueban localmente y están aprobados para publicarse. Continúan las consultas sobre identidad CSV–Excel y exigencia docente de óptimo certificado.

La revisión privada aprobada se conserva como antecedente. El PDF, las 26 corridas y los algoritmos mantienen sus bytes; esta revisión cambia la interfaz, la documentación y las pruebas de presentación. La nueva interfaz no incluye demostraciones ni carga de archivos.
    
## Revisión de presentación aprobada

Título SET COVER, seis secciones, ecuaciones con st.latex, README breve con enlace a la aplicación y enlaces documentales corregidos. Se conservan el PDF, los algoritmos y las 26 corridas. Las capturas y validaciones anteriores describen la interfaz histórica; la nueva revisión se documenta por separado en docs/REVISION_PRESENTACION.md. El usuario autorizó el commit y push a main. El resultado de publicación se comprueba en GitHub Actions y en la aplicación pública.

Validación actual: 110 pruebas aprobadas en 8,25 s; seis vistas comprobadas en Edge, seis ecuaciones renderizadas, descargas correctas y vista inicial móvil sin desbordamiento. Se contrastaron 244 archivos protegidos sin cambios. Evidencias nuevas en docs/VALIDACION_PRESENTACION.json y docs/VALIDACION_PRESENTACION_NAVEGADOR.json. Linux y Cloud de esta revisión se comprueban tras la publicación autorizada.
