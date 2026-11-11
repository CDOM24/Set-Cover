# Validación de ejecución

Python funciona con una instalación oficial firmada y un entorno nuevo, conservando el anterior y Smart App Control activado. Python y venv no requieren una compra. Se probó Python 3.12.10 Windows; los experimentos históricos siguen identificando 3.12.12.

**Comprobado:** instalación nueva, pip check, compilación CPython de 19 fuentes, auditoría de 26 corridas, 108 pruebas aprobadas, AppTest y siete vistas en Edge, descarga CSV/PDF, validación de originales y demostraciones AG/MILP. Evidencia: VALIDACION_EJECUCION.json, pruebas_pytest.xml, VALIDACION_NAVEGADOR.json y capturas_revision/.

El primer arranque AppTest superó 45 s: 107 pruebas aprobadas y una fallida. No se amplió el límite ni se cambió la aplicación: la misma prueba aislada aprobó después en 9,65 s y la confirmación completa aprobó las 108. Se ajustaron selectores del ensayo de navegador a etiquetas y búsqueda del control real. Un primer ensayo MILP no produjo descarga recuperable; diagnóstico directo y repetición final sí dieron instalaciones auditadas. Se conservan las salidas disponibles en demostraciones_validacion/.

Las demostraciones tuvieron límite de búsqueda de un segundo. El tiempo total incluye iniciar el proceso, cargar librerías y auditar, por lo que es mayor. No actualizan las estadísticas ni el mejor costo global. No se repitieron búsquedas prolongadas.

**Publicación:** revisión privada aprobada y entrega autorizada en CDOM24/Set-Cover, main, con la aplicación en la raíz. El resultado real de Linux se consulta en [GitHub Actions](https://github.com/CDOM24/Set-Cover/actions/workflows/pruebas.yml). **Pendiente:** despliegue y verificación en Community Cloud. Los JSON y XML de validación local conservan el contexto y las limitaciones de la revisión anterior.

El análisis estático previo con Node queda identificado como comprobación anterior, no como sustituto de las pruebas CPython que ahora sí se ejecutaron. No se desactivó ninguna protección de Windows.

El manifiesto MANIFIESTO_REVISION.json es una instantánea histórica de la copia revisada, anterior a los ajustes de README y estado. No es un manifiesto de hashes de la publicación actual. Los hashes científicos vigentes se verifican mediante resultados/procedencia.json.
