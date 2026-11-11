# Estado de la entrega pública

Entrega pública autorizada en **CDOM24/Set-Cover**, rama **main**. El contenido aprobado de entrega-publica/ se publica directamente en la raíz, con app.py y requirements.txt. No se modifica el repositorio privado de origen. El despliegue de Streamlit se realizará posteriormente desde la cuenta de los autores.

## Implementado

Interfaz con siete vistas; métricas separadas de AG 49.051, HiGHS 48.878 y cota SCIP 34.532,74; 26 corridas con hashes; datos originales, informe definitivo de 20 páginas, guías, pruebas y flujo Linux preparado. Demostraciones desactivadas por defecto, búsqueda de 1–3 s, tiempo duro del proceso y salidas temporales descargables.

## Python resuelto

Se instaló **Python 3.12.10 oficial**, firmado por Python Software Foundation, en una carpeta nueva del usuario, y se creó un entorno nuevo .venv. Instalador e intérprete tienen firma válida; Smart App Control sigue activado. No se cambió PATH ni se reemplazó el Python portátil anterior.

3.12.10 es la última versión 3.12 con instalador oficial Windows. Se usó para validación local de compatibilidad; los registros históricos conservan su versión 3.12.12. No se presenta 3.12.10 como la revisión de seguridad más reciente. Fuente y firma: docs/INSTALACION_PYTHON_FIRMADO.json.

## Validación realizada

- Auditorías PowerShell y Python: las 26 selecciones mantienen costos y cobertura 500/500. Sin óptimo certificado.
- CPython compiló 19 archivos; pip check no encontró incompatibilidades.
- **108 pruebas aprobadas**, incluidas AppTest y separación del mejor AG frente al global; evidencia en docs/pruebas_pytest.xml.
- Primer intento: 107 aprobadas y timeout de 45 s en el arranque inicial de AppTest. Repetición aislada: aprobada en 9,65 s, sin cambio de código o límite; batería completa posterior: 108 aprobadas.
- Edge con perfil aislado: siete vistas, CSV de 22 antenas y costo 48.878, PDF idéntico al original, carga de archivos y rechazo de demostraciones sin aceptar el supuesto.
- Demostraciones web de 1 s: AG 51.846 y MILP 212.146, ambas con cobertura 500/500. Un diagnóstico MILP adicional de 1 s produjo 414.467. Son pruebas fuera del catálogo; no cambian resultados históricos. Un primer ensayo MILP no dejó descarga recuperable y se documentó.
- **238 copias trazadas** con hashes correctos; **1.044 archivos del origen** sin modificaciones.
- Instaladores, entornos, cachés y materiales operativos excluidos de Git. No se repitieron campañas prolongadas.

## Pendiente

El estado real del workflow Linux está en [GitHub Actions](https://github.com/CDOM24/Set-Cover/actions/workflows/pruebas.yml). El despliegue y la verificación en Community Cloud siguen pendientes; no se presentan como realizados. Continúan las consultas sobre identidad CSV–Excel y exigencia docente de óptimo certificado.

La revisión privada aprobada se conserva como antecedente. El PDF, las 26 corridas y los algoritmos mantienen sus bytes; los ajustes de publicación afectan únicamente la documentación. Las demostraciones permanecen desactivadas por defecto, también en Cloud.
