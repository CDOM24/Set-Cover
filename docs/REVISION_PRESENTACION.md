# Revisión de presentación · SET COVER

Revisión local del 11 de noviembre de 2026, aprobada para publicación. La aplicación disponible en https://set-cover-coliva.streamlit.app/ conserva la versión publicada hasta que termine su actualización automática desde main.

## Cambios preparados

- Seis secciones: Inicio, Problema y datos, Método exacto, Algoritmo genético, Comparación y Metodología.
- Se retiraron de la interfaz las demostraciones y la carga de archivos. El código científico local se conserva; consultar la aplicación no inicia búsquedas.
- Título SET COVER, jerarquía de títulos, tarjetas de resultados, tablas legibles, autores una sola vez e informe como recurso secundario.
- Cuatro ecuaciones del modelo con st.latex y dos ecuaciones para interpretar las cotas. Los gráficos históricos mantienen su identificación.
- README más breve: presentación, aplicación, métodos, resultados, estructura e instalación local. Sin captura grande ni anuncio desactualizado de despliegue pendiente.
- Referencias inexistentes del modelo sustituidas por enlaces a archivos reales. El manifiesto conserva el hash documental original y el actualizado; no se cambió el modelo matemático.

## Verificación

**110 pruebas aprobadas en 8,25 s** en Windows con Python 3.12.10 y Streamlit 1.67.0. La comprobación anterior en Linux de 108 pruebas sigue siendo histórica; la batería nueva se ejecutará allí cuando se autorice la publicación.

La revisión de Edge, con perfil aislado, comprobó las seis secciones, cuatro fórmulas del modelo y dos de comparación renderizadas con KaTeX, sin errores JavaScript. La selección descargada contiene 22 antenas y suma 48.878. El PDF descargado conserva su SHA-256 original. La vista inicial a 390 píxeles de ancho no presenta desbordamiento horizontal. Los enlaces públicos del README respondieron HTTP 200 y las rutas documentales relativas existen.

Se comprobaron **244 archivos protegidos idénticos al commit público de referencia**: algoritmos, datos, resultados, registros, capturas históricas y PDF. El catálogo conserva 26 corridas, mejor AG 49.051, mejor global 48.878 y cota 34.532,73615154492. No hay óptimo certificado. No se ejecutaron campañas nuevas ni optimizaciones prolongadas.

Dos incidencias del ensayo quedaron corregidas: una aserción nueva no contemplaba las llaves escapadas de LaTeX; el primer selector del navegador buscaba un identificador distinto del DOM real de KaTeX. No requirieron modificar ecuaciones ni datos.

Evidencia nueva: [pruebas](pruebas_presentacion.xml), [validación general](VALIDACION_PRESENTACION.json), [navegador](VALIDACION_PRESENTACION_NAVEGADOR.json) y [capturas](capturas_presentacion/). Las validaciones y capturas anteriores permanecen intactas.

## Revisar antes de publicar

La vista local está en http://127.0.0.1:8516 mientras el servidor de revisión permanezca activo. Para volver a iniciarlo desde la raíz del proyecto en PowerShell:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8516
```

[Inicio](capturas_presentacion/01.png) · [Modelo matemático](capturas_presentacion/03.png) · [Comparación](capturas_presentacion/05.png) · [Vista móvil](capturas_presentacion/07_movil.png).

El usuario autorizó publicar estos ajustes en main. Las validaciones JSON y XML locales conservan el contexto previo a la publicación; el resultado posterior se consulta en GitHub Actions y en la aplicación pública. El repositorio privado no se modifica.
