"""Presentación académica de SET COVER: consulta de resultados históricos."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import streamlit as st
from setcover.catalog import ROOT, load_catalog, csv_bytes, public_rows, additional_progress

st.set_page_config(page_title='SET COVER | Coliva', page_icon='📡', layout='wide')
st.markdown("""<style>
.block-container{max-width:1280px;padding-top:2rem;padding-bottom:3rem}
h1,h2,h3{letter-spacing:-.025em;color:#17312f}
[data-testid="stMetric"]{padding:1.1rem;border:1px solid #dce7e4;border-radius:14px;background:#f6faf9}
[data-testid="stMetricValue"]{color:#0f766e}
.hero{padding:2rem;border-radius:18px;background:linear-gradient(115deg,#16332f,#0f766e);color:white;margin-bottom:1.7rem}
.hero h1{color:white;margin:.35rem 0;font-size:2.8rem}.hero p{color:#e1f1eb;margin-bottom:0;max-width:760px}
.eyebrow{font-size:.8rem;letter-spacing:.13em;text-transform:uppercase}
</style>""", unsafe_allow_html=True)

@st.cache_data(show_spinner='Cargando el proyecto…')
def cached_catalog(signature):
    return load_catalog()


def number(value, digits=0):
    if value is None:
        return '—'
    return f'{value:,.{digits}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


try:
    c = cached_catalog((ROOT/'resultados/procedencia.json').stat().st_mtime_ns)
except (OSError, ValueError, KeyError, TypeError) as exc:
    st.error('No se pudieron cargar los resultados: '+str(exc))
    st.stop()
best, ga = c['mejor_global'], c['mejor_ag']

st.sidebar.caption('UNAB · INVESTIGACIÓN DE OPERACIONES I')
st.sidebar.title('Explorar')
page = st.sidebar.radio('Secciones', ['Inicio', 'Problema y datos', 'Método exacto',
                                      'Algoritmo genético', 'Comparación', 'Metodología'])
st.sidebar.divider()
st.sidebar.caption('500 clientes · 500 ubicaciones')
st.sidebar.caption('Una misma instancia, dos formas de buscar una instalación de menor costo.')


def show_record(r):
    st.subheader('La solución seleccionada')
    cols = st.columns(4)
    for col, label, value in zip(cols, ['Costo de instalación', 'Antenas', 'Clientes cubiertos', 'Tiempo de búsqueda (s)'],
                                 [number(r['costo']), r['antenas'], f"{r['clientes']}/500", number(r['tiempo_s'], 3)]):
        col.metric(label, value)
    st.caption('Tiempo individual de esta corrida. La selección es factible; su optimalidad no está certificada.')
    tabs = st.tabs(['Antenas y costos', 'Cobertura', 'Detalle de la corrida'])
    with tabs[0]:
        rows = r['auditoria']['costos_seleccionados']
        st.dataframe(pd.DataFrame(rows).rename(columns={'id_excel': 'Antena', 'etiqueta_csv': 'Columna CSV', 'costo_original': 'Costo de instalación'}), hide_index=True, width='stretch')
        st.download_button('Descargar selección CSV', csv_bytes(rows), file_name=Path(r['archivo']).parent.name+'_antenas.csv', mime='text/csv', key='csv_'+r['archivo'])
    with tabs[1]:
        values = r['auditoria']['cobertura_por_cliente']
        st.bar_chart(pd.DataFrame({'Cliente': range(1,501), 'Antenas que lo cubren': values}).set_index('Cliente'), height=260, color='#0f766e')
        st.caption('Cada cliente recibe al menos una cobertura. Una barra mayor que uno indica cobertura superpuesta; no distancia ni capacidad.')
        st.download_button('Descargar cobertura por cliente', csv_bytes([{'cliente': i+1, 'coberturas': v} for i,v in enumerate(values)]), file_name='cobertura.csv', key='coverage_'+r['archivo'])
    with tabs[2]:
        st.write('**Estudio:** '+r['estudio']+' · **Estado del solver:** '+r['estado'])
        if r['metodo'] == 'MILP':
            a,b,d = st.columns(3)
            a.metric('Cota inferior de esta corrida', number(r['cota'],2))
            b.metric('Nodos procesados', number(r['nodos']))
            d.metric('Brecha nativa (%)', number(r['brecha_nativa_pct'],4))
            st.caption('HiGHS y SCIP calculan su brecha nativa con distintos denominadores. En Comparación usamos (U−L)/U para la pareja de cotas globales.')
        with st.expander('Parámetros y evidencia original'):
            st.json(r['parametros'])
            st.caption(r['archivo'])
            st.download_button('Descargar resultado JSON', json.dumps(r['documento'], ensure_ascii=False, indent=2), file_name=Path(r['archivo']).name, key='json_'+r['archivo'])
            folder = ROOT/Path(r['archivo']).parent
            for log in ['solver.log', 'highs.log', 'scip.log']:
                path = folder/log
                if path.exists():
                    st.download_button('Descargar '+log, path.read_bytes(), file_name=log, key='log_'+r['archivo']+log)


def plot_history(r):
    if r['historial']:
        frame = pd.DataFrame(r['historial']).set_index('generacion')
        st.subheader('Cómo evoluciona la población')
        st.line_chart(frame[['mejor_costo','costo_medio']].rename(columns={'mejor_costo':'Mejor costo', 'costo_medio':'Costo medio'}), height=280, x_label='Generación', y_label='Costo de instalación')
        st.caption('Corrida seleccionada. La generación cero corresponde a la población inicial.')
        with st.expander('Diversidad de la población'):
            st.line_chart(frame[['diversidad_proporcion']].rename(columns={'diversidad_proporcion':'Diversidad (proporción)'}), height=200, x_label='Generación')
            st.write('La pérdida de diversidad reduce las alternativas que explora la población y puede favorecer el estancamiento.')


if page == 'Inicio':
    st.markdown('<div class="hero"><span class="eyebrow">Cobertura ponderada · Investigación de Operaciones</span><h1>SET COVER</h1><p>¿Qué antenas debemos instalar para cubrir a todos los clientes con el menor costo posible?</p></div>', unsafe_allow_html=True)
    st.write('Comparamos un método exacto y un algoritmo genético sobre una instancia de **500 clientes y 500 ubicaciones**. Ambos usan los mismos datos y buscan cubrir a cada cliente al menos una vez.')
    a,b,d = st.columns(3)
    a.metric('Mejor algoritmo genético', number(ga['costo']))
    a.caption('22 antenas · 500/500 clientes · 5,718 s en esa corrida')
    b.metric('Mejor solución factible · HiGHS', number(best['costo']))
    b.caption('22 antenas · 500/500 clientes · búsqueda posterior')
    d.metric('Cota inferior · SCIP', number(c['cota'],2))
    d.caption('Límite para el costo óptimo; no es una instalación')
    st.subheader('Una buena solución no equivale a una prueba de óptimo')
    st.write('HiGHS encontró la instalación de **48.878** a partir de la mejor solución genética. Después, SCIP mantuvo esa selección y elevó la cota inferior. **No se ha certificado el óptimo global.**')
    st.info('El costo óptimo está entre **34.532,74 y 48.878**. En Comparación explicamos qué permite concluir este intervalo.')
    st.subheader('Un recorrido por el proyecto')
    a,b = st.columns(2)
    with a:
        st.markdown('**Comprender el problema**\n\nEn Problema y datos puedes explorar la matriz y las antenas seleccionadas. Método exacto presenta el modelo y la búsqueda de cotas.')
    with b:
        st.markdown('**Interpretar los resultados**\n\nAlgoritmo genético muestra la evolución de las soluciones. Comparación reúne las corridas; Metodología explica cómo las evaluamos.')
    st.divider()
    st.caption('Carlos Daniel Oliva Moreno · Camilo Andrés Oliva Moreno | Universidad Autónoma de Bucaramanga (UNAB) | Investigación de Operaciones I')

elif page == 'Problema y datos':
    st.title('Problema y datos')
    st.write('Cada ubicación tiene un costo de instalación y cubre un conjunto de clientes. Elegimos un subconjunto de antenas que cubra a todos; un cliente puede recibir cobertura de varias antenas. **Minimizamos el costo total, no el número de antenas.**')
    d = c['entradas']['diagnostico']
    a,b,x = st.columns(3)
    a.metric('Clientes', d['clientes']); b.metric('Ubicaciones candidatas', d['antenas']); x.metric('Densidad de cobertura', number(100*d['densidad'],2)+' %')
    st.subheader('Cómo leemos los datos')
    st.write('En la matriz CSV, cada fila representa un cliente y cada columna una antena. Un **1** indica cobertura y un **0** indica ausencia de cobertura. El Excel contiene el costo de cada ubicación. Los costos se expresan en las unidades del conjunto de datos; no se presupone una moneda.')
    st.info('Supuesto de correspondencia: la columna 0 del CSV toma el costo de la antena 1 del Excel, y así hasta la columna 499 y la antena 500. La estructura coincide; el profesor no confirmó la identidad física de esta asociación.')
    with st.expander('Explorar la matriz y los costos originales'):
        left,right = st.columns([1,1])
        with left:
            rgb = np.where(c['entradas']['A'][:,:,None] == 1, np.array([15,118,110]), np.array([241,245,249])).astype(np.uint8)
            st.image(rgb, width='stretch')
            st.caption('Verde = cobertura. Esta matriz no es un mapa geográfico.')
        with right:
            st.dataframe(pd.DataFrame(c['entradas']['mapeo']).rename(columns={'id_excel':'Antena Excel','etiqueta_csv':'Columna CSV','costo_original':'Costo'}), hide_index=True, height=350)
            for file in ['set_cover_500x500.csv','Costo_S.xlsx']:
                st.download_button('Descargar '+file, (ROOT/'datos'/file).read_bytes(), file_name=file)
    st.subheader('Explorar una selección')
    option = st.radio('Solución de referencia', ['HiGHS · 48.878', 'Algoritmo genético · 49.051'], horizontal=True)
    show_record(best if option.startswith('HiGHS') else ga)

elif page == 'Método exacto':
    st.title('Método exacto')
    st.write('Formulamos el problema como un modelo lineal entero binario. El solver busca instalaciones factibles y calcula cotas inferiores para determinar cuánto falta para demostrar la optimalidad.')
    with st.expander('El modelo matemático', expanded=True):
        st.markdown('Para cada cliente $i$ y ubicación $j$, $A_{ij}$ indica cobertura y $c_j$ es el costo de instalación. La decisión $x_j$ vale uno si instalamos la antena.')
        st.latex(r'\min_{x}\; Z=\sum_{j=1}^{500}c_j x_j')
        st.caption('Objetivo: sumar los costos de las antenas seleccionadas y minimizar el total.')
        st.latex(r'\sum_{j=1}^{500} A_{ij}x_j\geq 1 \qquad \forall i\in\{1,\ldots,500\}')
        st.caption('Cobertura: cada cliente debe estar cubierto por al menos una antena.')
        st.latex(r'x_j\in\{0,1\} \qquad \forall j\in\{1,\ldots,500\}')
        st.caption('Variables binarias: instalar o descartar cada ubicación.')
        st.latex(r'\min\;c^{\mathsf T}x \qquad \text{sujeto a } Ax\geq\mathbf{1},\quad x\in\{0,1\}^{500}')
        st.caption('La misma formulación en notación matricial: 500 decisiones y 500 restricciones de cobertura.')
    st.subheader('Qué aporta cada búsqueda')
    st.write('HiGHS inicial encontró **49.734**. Con más tiempo y una solución inicial del AG, HiGHS alcanzó **48.878**. SCIP recibió esa selección y mejoró la cota inferior hasta **34.532,74**. Ambas búsquedas posteriores terminaron por tiempo, sin certificar el óptimo.')
    records = [r for r in c['corridas'] if r['metodo'] == 'MILP']
    default = next(i for i,r in enumerate(records) if r['archivo'] == best['archivo'])
    index = st.selectbox('Ejecución exacta', range(len(records)), index=default, format_func=lambda i: records[i]['etiqueta'])
    show_record(records[index])

elif page == 'Algoritmo genético':
    st.title('Algoritmo genético')
    st.write('Representamos una instalación con **500 bits**: cada bit indica si elegimos una antena. Una población de soluciones evoluciona al combinar y modificar sus selecciones.')
    with st.expander('De una generación a la siguiente', expanded=True):
        st.markdown('1. Creamos y evaluamos la población inicial.\n2. Seleccionamos padres por torneo y aplicamos cruce uniforme.\n3. Mutamos bits para explorar otras selecciones.\n4. Reparamos las coberturas faltantes y eliminamos antenas redundantes.\n5. Conservamos los mejores individuos mediante elitismo.')
        st.caption('La reparación permite obtener soluciones factibles. El algoritmo no aporta una prueba de optimalidad.')
    records = [r for r in c['corridas'] if r['metodo'] == 'AG']
    default = next(i for i,r in enumerate(records) if r['archivo'] == ga['archivo'])
    index = st.selectbox('Corrida genética', range(len(records)), index=default, format_func=lambda i: f"{records[i]['estudio']} · {records[i]['etiqueta']} · {number(records[i]['costo'])}")
    st.caption('La mejor corrida del AG usó mutación 0,01 y semilla 44: costo 49.051 en 5,718 segundos. El costo 48.878 corresponde a HiGHS posterior.')
    show_record(records[index]); plot_history(records[index])

elif page == 'Comparación':
    st.title('Comparación')
    st.write('Comparamos calidad, tiempo y estabilidad. Los métodos no recibieron siempre el mismo presupuesto ni la misma solución inicial; sus tiempos deben leerse junto con esas condiciones.')
    reference = [next(r for r in c['corridas'] if r['etiqueta'] == 'HiGHS inicial'), ga, best, c['mejor_cota']]
    labels = ['HiGHS inicial', 'Mejor algoritmo genético', 'HiGHS posterior', 'SCIP posterior']
    table = [{'Resultado': label, 'Costo factible': number(r['costo']), 'Antenas': r['antenas'], 'Cobertura': f"{r['clientes']}/500", 'Tiempo (s)': number(r['tiempo_s'],3), 'Cota inferior': number(r['cota'],2)} for label,r in zip(labels,reference)]
    st.dataframe(pd.DataFrame(table), hide_index=True, width='stretch')
    st.subheader('Lo que sabemos del óptimo')
    st.latex(r'34\,532{,}73615154492\leq Z^*\leq48\,878')
    st.latex(r'\frac{U-L}{U}\times100 \approx 29{,}3491\%')
    st.write('La mejor instalación cuesta **48.878** y la mejor cota inferior es **34.532,73615154492**. La separación es **29,3491 %**. Es una brecha entre cotas, no el error real frente a un óptimo conocido. **El óptimo sigue sin certificarse.**')
    with st.expander('Evolución de las cotas en las búsquedas posteriores'):
        data = pd.DataFrame(additional_progress(c))
        if not data.empty:
            st.line_chart(data, x='minutos', y='cota', color='solver', height=300, x_label='Minutos de búsqueda', y_label='Cota inferior')
        st.caption('Investigaciones independientes: HiGHS recibió 49.051 y SCIP recibió 48.878. El eje temporal usa el reloj nativo de cada solver. Las cotas no son costos de instalaciones.')
    st.subheader('Estabilidad del algoritmo genético')
    study = ROOT/'resultados/fase4/estudio_20261107T020734Z_cbfda0ea'
    st.image(str(study/'comparacion_configuraciones_ag.png'), caption='Gráfica histórica de Fase 4: tres configuraciones, cinco semillas comunes por configuración.')
    st.write('La mutación 0,01 produjo el mejor individuo. La estrategia con inmigrantes obtuvo mejor media y menor dispersión, con más esfuerzo de cálculo. Ninguna media superó el costo inicial de HiGHS de 49.734; los resultados no prueban una superioridad general del AG.')
    with st.expander('Estadísticas por configuración'):
        st.dataframe(pd.read_csv(study/'genetico/resumen_configuraciones.csv'), hide_index=True, width='stretch')
    with st.expander('Consultar las 26 corridas'):
        studies = list(dict.fromkeys(r['estudio'] for r in c['corridas']))
        selected = st.multiselect('Estudios', studies, default=studies)
        rows = [r for r in public_rows(c) if r['estudio'] in selected]
        st.dataframe(pd.DataFrame(rows).rename(columns={'etiqueta':'Corrida','metodo':'Método','estudio':'Estudio','costo':'Costo','antenas':'Antenas','clientes':'Clientes','tiempo_s':'Tiempo (s)','cota':'Cota inferior','estado':'Estado','semilla':'Semilla','nodos':'Nodos','optimo_certificado':'Óptimo certificado'}), hide_index=True, width='stretch')
        st.download_button('Descargar comparación CSV', csv_bytes(rows), file_name='comparacion_set_cover.csv')
    st.caption('El tiempo de la mejor corrida genética no incluye las demás semillas ni los experimentos previos. Los nodos de diferentes solvers no representan unidades equivalentes de trabajo.')

elif page == 'Metodología':
    st.title('Metodología')
    st.subheader('La misma instancia para ambos métodos')
    st.write('Usamos la matriz binaria y los costos originales sin alterar su orden. Conservamos el supuesto de correspondencia CSV j ↔ Excel j+1. No añadimos restricciones de distancia, capacidad o interferencia que no aparezcan en los datos.')
    st.subheader('Cómo evaluamos cada solución')
    st.markdown('1. Recalculamos la cobertura de los **500 clientes** con las antenas elegidas.\n2. Sumamos sus costos a partir del **Excel original**.\n3. Registramos tiempo, parámetros, semillas y estado de terminación.\n4. Distinguimos una solución factible de una cota inferior y de un óptimo certificado.')
    st.subheader('Comparaciones con límites explícitos')
    st.write('Conservamos cinco corridas genéticas iniciales y quince de comparación: tres configuraciones con las mismas cinco semillas. Mostramos todos los resultados, incluidos los desfavorables. Las búsquedas exactas posteriores utilizan soluciones iniciales ya conocidas; sus tiempos no incluyen el esfuerzo de encontrarlas.')
    st.subheader('Alcance de las conclusiones')
    st.write('La evidencia respalda la factibilidad de las selecciones y las cotas reportadas. No permite conocer el óptimo ni anticipar cuánto tiempo haría falta para certificarlo. Una ejecución nueva puede producir resultados y tiempos diferentes según el equipo y las versiones.')
    with st.expander('Informe y recursos complementarios'):
        report = ROOT/'docs/Informe_Proyecto_Oliva_Moreno.pdf'
        st.write('El informe definitivo reúne la investigación completa en 20 páginas. Su captura de interfaz corresponde a una versión anterior; se conserva sin modificaciones.')
        st.download_button('Descargar informe definitivo · 20 páginas', report.read_bytes(), file_name=report.name, mime='application/pdf')
        st.link_button('Código, datos y evidencia científica', 'https://github.com/CDOM24/Set-Cover')
        st.caption('El repositorio contiene la formulación, los protocolos, las selecciones y los registros de las 26 corridas.')
