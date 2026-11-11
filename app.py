"""Streamlit académico: consulta auditada; demostraciones opcionales, sin campañas."""
from pathlib import Path
import json
import io
import zipfile
import os
import subprocess
import sys
import tempfile
import threading
import numpy as np
import pandas as pd
import streamlit as st
from setcover.catalog import ROOT, load_catalog, csv_bytes, public_rows, additional_progress

st.set_page_config(page_title='SET COVER · UNAB',page_icon='📡',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
.block-container{max-width:1440px;padding-top:2.3rem}
h1,h2,h3{letter-spacing:-.025em;color:#0f172a}
[data-testid="stMetric"]{padding:1rem;border:1px solid #dbe5ea;border-radius:14px;background:#f8fafc}
[data-testid="stMetricValue"]{color:#0f766e}
.hero{padding:1.8rem 2rem;border-radius:18px;background:linear-gradient(115deg,#0f172a,#115e59);color:white;margin-bottom:1.3rem}
.hero h1{color:white;margin:0;font-size:2.5rem}.hero p{color:#d1fae5;margin-bottom:0}
</style>''',unsafe_allow_html=True)

@st.cache_data(show_spinner='Verificando datos, archivos y soluciones…')
def cached_catalog(signature):
    return load_catalog()

@st.cache_resource
def demo_lock():
    return threading.Lock()

def number(value,digits=0):
    if value is None:
        return '—'
    return f'{value:,.{digits}f}'.replace(',','_').replace('.',',').replace('_','.')

try:
    c=cached_catalog((ROOT/'resultados/procedencia.json').stat().st_mtime_ns)
except (OSError,ValueError,KeyError,TypeError) as exc:
    st.error('No se puede presentar una entrega verificada: '+str(exc))
    st.stop()
best=c['mejor_global'];ga=c['mejor_ag'];bound=c['mejor_cota']

st.sidebar.caption('UNAB · INVESTIGACIÓN DE OPERACIONES I')
st.sidebar.title('SET COVER')
st.sidebar.caption('500 clientes · 500 ubicaciones')
page=st.sidebar.radio('Explorar el proyecto',['Resumen','Datos y soluciones','Método exacto','Algoritmo genético','Comparación','Informe y metodología','Demostraciones'])
st.sidebar.divider()
st.sidebar.warning('Óptimo entero no certificado')
st.sidebar.caption('Datos originales y 26 resultados conservados. Consultar o recargar no ejecuta búsquedas.')
st.sidebar.caption('Carlos Daniel Oliva Moreno · Camilo Andrés Oliva Moreno')

def summary_metrics():
    a,b,d=st.columns(3)
    a.metric('Mejor algoritmo genético',number(ga['costo']))
    a.caption('Mutación 0,01 · semilla 44 · '+number(ga['tiempo_s'],3)+' s individuales')
    b.metric('Mejor solución factible global',number(best['costo']))
    b.caption('Encontrada por HiGHS posterior · 22 antenas · 500/500 clientes')
    d.metric('Mejor cota inferior',number(c['cota'],2))
    d.caption('SCIP posterior · límite inferior; no representa una instalación')

def show_record(r):
    st.subheader(r['etiqueta'])
    cols=st.columns(4)
    for col,label,value in zip(cols,['Costo verificado','Antenas','Clientes cubiertos','Tiempo de búsqueda (s)'],
        [number(r['costo']),r['antenas'],f"{r['clientes']}/500",number(r['tiempo_s'],3)]):
        col.metric(label,value)
    st.success('La selección pasó la auditoría contra el CSV y Excel originales.')
    st.caption('Estudio: '+r['estudio']+' · Estado: '+r['estado']+' · Óptimo certificado: '+('sí' if r['optimo_certificado'] else 'no'))
    if r['metodo']=='MILP':
        x,y,z=st.columns(3)
        x.metric('Cota propia',number(r['cota'],2));y.metric('Nodos procesados',number(r['nodos']))
        z.metric('Brecha nativa (%)',number(r['brecha_nativa_pct'],4))
        st.caption('Las brechas nativas de HiGHS y SCIP usan distintos denominadores. La comparación global usa 100 × (U−L)/U.')
    tabs=st.tabs(['Antenas y costos','Cobertura','Registro y parámetros'])
    with tabs[0]:
        rows=r['auditoria']['costos_seleccionados']
        st.dataframe(pd.DataFrame(rows).rename(columns={'id_excel':'Antena Excel','etiqueta_csv':'Etiqueta CSV','costo_original':'Costo original'}),hide_index=True,width='stretch')
        st.download_button('Descargar selección CSV',csv_bytes(rows),file_name=Path(r['archivo']).parent.name+'_antenas.csv',mime='text/csv',key='csv_'+r['archivo'])
    with tabs[1]:
        values=r['auditoria']['cobertura_por_cliente']
        st.bar_chart(pd.DataFrame({'Cliente':range(1,501),'Antenas que lo cubren':values}).set_index('Cliente'),height=230)
        st.caption('Cada cliente necesita al menos una cobertura. No representa distancia ni capacidad.')
        st.download_button('Descargar 500 coberturas',csv_bytes([{'cliente':i+1,'coberturas':v} for i,v in enumerate(values)]),file_name='cobertura.csv',key='coverage_'+r['archivo'])
    with tabs[2]:
        st.caption('Archivo histórico inalterado: '+r['archivo'])
        st.json(r['parametros'])
        st.download_button('Descargar resultado original JSON',json.dumps(r['documento'],ensure_ascii=False,indent=2),file_name=Path(r['archivo']).name,key='json_'+r['archivo'])
        folder=ROOT/Path(r['archivo']).parent
        for log in ['solver.log','highs.log','scip.log']:
            path=folder/log
            if path.exists():
                st.download_button('Descargar '+log,path.read_bytes(),file_name=log,key='log_'+r['archivo']+log)
                with st.expander('Últimas líneas de '+log):
                    st.text(path.read_text(encoding='utf-8',errors='replace')[-10000:])

def plot_history(r):
    if r['historial']:
        frame=pd.DataFrame(r['historial']).set_index('generacion')
        st.line_chart(frame[['mejor_costo','costo_medio']],height=270)
        st.caption('Convergencia histórica de la corrida seleccionada; generación cero = inicialización.')
        st.line_chart(frame[['diversidad_proporcion']],height=170)

def additional_chart():
    data=pd.DataFrame(additional_progress(c))
    if not data.empty:
        st.line_chart(data,x='minutos',y='cota',color='solver',height=300)
        st.caption('Dos investigaciones independientes. Eje: tiempo nativo de cada solver. Inicios: HiGHS 49.051; SCIP 48.878. Las cotas no son costos de instalaciones.')

if page=='Resumen':
    st.markdown('<div class="hero"><small>COBERTURA PONDERADA · RESULTADOS REALES</small><h1>Cubrir a todos, al menor costo</h1><p>Dos métodos, una misma instancia y evidencia verificable.</p></div>',unsafe_allow_html=True)
    summary_metrics()
    st.subheader('Qué está demostrado')
    a,b=st.columns([3,2])
    with a:
        st.write('Una instalación de **22 antenas** cubre a los **500 clientes** y cuesta **48.878**. HiGHS la encontró utilizando como inicio la mejor selección genética de 49.051. SCIP recibió la selección de 48.878 y mejoró la cota inferior.')
        st.info(f"{number(c['cota'],2)} ≤ Z* ≤ {number(best['costo'])}. Separación entre cotas: {number(c['separacion'],4)} %. El óptimo sigue desconocido.")
        st.caption('La separación no es el error real respecto del óptimo. Costos en unidades no especificadas por el enunciado.')
    with b:
        st.markdown('**Recorrido sugerido**\n\n1. Examinar la matriz y una selección.\n2. Entender qué aporta cada método.\n3. Comparar costo, tiempo y evidencia.\n4. Consultar el informe definitivo.')
    st.latex(r'\min\sum_j c_jx_j\quad\text{s.a.}\quad\sum_j A_{ij}x_j\ge1\;\forall i,\quad x_j\in\{0,1\}')
    st.caption('Se minimiza costo, no cantidad. La cobertura superpuesta está permitida.')
    st.warning('Supuesto declarado: CSV j ↔ Excel j+1. La identidad física no fue confirmada por el profesor.')

elif page=='Datos y soluciones':
    st.title('Datos originales y selecciones verificadas')
    d=c['entradas']['diagnostico']
    a,b,x,y=st.columns(4)
    a.metric('Clientes',d['clientes']);b.metric('Antenas candidatas',d['antenas']);x.metric('Entradas con cobertura',number(d['unos']));y.metric('Densidad',number(100*d['densidad'],4)+' %')
    with st.expander('Matriz y correspondencia de costos'):
        st.caption('Filas = clientes; columnas = ubicaciones. El gráfico no es un mapa geográfico.')
        rgb=np.where(c['entradas']['A'][:,:,None]==1,np.array([15,118,110]),np.array([241,245,249])).astype(np.uint8)
        st.image(rgb,width=550)
        st.dataframe(pd.DataFrame(c['entradas']['mapeo']),hide_index=True,height=220)
        for file in ['set_cover_500x500.csv','Costo_S.xlsx']:
            st.download_button('Descargar '+file,(ROOT/'datos'/file).read_bytes(),file_name=file)
        st.json(c['entradas']['hashes'])
    with st.expander('Validar otros archivos sin cambiar los originales'):
        with st.form('validar_upload'):
            upload_csv=st.file_uploader('Matriz CSV 500×500',type=['csv'])
            upload_xlsx=st.file_uploader('Costos Excel de 500 antenas',type=['xlsx'])
            agreed=st.checkbox('Aplicar explícitamente CSV j ↔ Excel j+1 a estos archivos')
            submit=st.form_submit_button('Validar archivos')
        if submit:
            if upload_csv is None or upload_xlsx is None or not agreed:
                st.error('Se necesitan ambos archivos y aceptar el supuesto de correspondencia.')
            elif upload_csv.size>5_000_000 or upload_xlsx.size>5_000_000:
                st.error('Límite de 5 MB por archivo.')
            else:
                try:
                    from setcover.catalog import load_inputs
                    raw_csv=upload_csv.getvalue();raw_excel=upload_xlsx.getvalue()
                    if len(raw_csv)>1_000_000 or raw_csv.count(b'\n')>502 or raw_csv.count(b'\r')>502:
                        raise ValueError('La matriz supera el tamaño previsto para 500×500.')
                    with zipfile.ZipFile(io.BytesIO(raw_excel)) as book_zip:
                        entries=book_zip.infolist()
                        if len(entries)>100 or sum(i.file_size for i in entries)>20_000_000 or any(i.file_size>8_000_000 for i in entries):
                            raise ValueError('El Excel supera el tamaño descomprimido permitido.')
                    with tempfile.TemporaryDirectory(prefix='setcover_validacion_') as tmp:
                        temp=Path(tmp);(temp/'datos').mkdir()
                        (temp/'datos/set_cover_500x500.csv').write_bytes(upload_csv.getvalue())
                        (temp/'datos/Costo_S.xlsx').write_bytes(upload_xlsx.getvalue())
                        uploaded=load_inputs(temp)
                    st.success('Archivos estructuralmente válidos; los originales no cambiaron.')
                    st.json(uploaded['diagnostico'])
                    if uploaded['identidad']!=c['entradas']['identidad']:
                        st.warning('Es una instancia distinta. Los resultados publicados no se atribuyen a estos archivos y las demostraciones siguen usando únicamente los originales.')
                    else:
                        st.info('La matriz y los costos coinciden con la instancia del informe.')
                except Exception as exc:
                    st.error('No se pudieron validar los archivos: '+str(exc))
    option=st.radio('Selección de referencia',['Mejor global · HiGHS 48.878','Mejor AG · 49.051'],horizontal=True)
    show_record(best if option.startswith('Mejor global') else ga)

elif page=='Método exacto':
    st.title('Método exacto: buscar y demostrar')
    st.write('El modelo binario busca instalaciones factibles y mantiene una cota inferior. Terminar por tiempo conserva una solución; no demuestra que sea óptima.')
    records=[r for r in c['corridas'] if r['metodo']=='MILP']
    default=next(i for i,r in enumerate(records) if r['archivo']==best['archivo'])
    index=st.selectbox('Ejecución exacta',range(len(records)),index=default,format_func=lambda i:records[i]['etiqueta'])
    show_record(records[index])
    st.subheader('Progreso de las investigaciones posteriores')
    additional_chart()
    with st.expander('Incidencias y lectura correcta de estados'):
        st.write('HiGHS adicional exportó el resultado final y su auditoría antes del cierre forzado registrado por el supervisor. SCIP terminó normalmente por tiempo; su resultado final conserva un campo heredado que dice parcial. El log nativo, el tipo de resultado y los archivos de cierre permiten interpretar ambos casos. No se modificaron los originales.')
        st.write('Los inicios son información previa: HiGHS adicional recibió 49.051 y SCIP recibió 48.878. El tiempo para obtenerlos no forma parte del tiempo de sus nuevas llamadas.')

elif page=='Algoritmo genético':
    st.title('Algoritmo genético: evolución con cobertura')
    st.info('Mejor resultado del AG: **49.051**, semilla **44**, mutación **0,01**, **5,718 s** en esa corrida. El resultado global de 48.878 corresponde a HiGHS posterior.')
    st.write('Cromosoma binario → torneo → cruce uniforme → mutación → reparación de cobertura → poda de antenas redundantes. El elitismo conserva los mejores individuos.')
    records=[r for r in c['corridas'] if r['metodo']=='AG']
    default=next(i for i,r in enumerate(records) if r['archivo']==ga['archivo'])
    index=st.selectbox('Corrida genética',range(len(records)),index=default,format_func=lambda i:f"{records[i]['estudio']} · {records[i]['etiqueta']} · {number(records[i]['costo'])}")
    show_record(records[index]);plot_history(records[index])
    st.caption('Se conservan las cinco corridas originales y las quince de comparación. El tiempo del mejor individuo no es el costo total de buscar entre todas las semillas.')

elif page=='Comparación':
    st.title('Comparar calidad, tiempo y evidencia')
    summary_metrics()
    studies=list(dict.fromkeys(r['estudio'] for r in c['corridas']))
    selected=st.multiselect('Estudios',studies,default=studies)
    rows=[r for r in public_rows(c) if r['estudio'] in selected]
    st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
    st.download_button('Descargar comparación CSV',csv_bytes(rows),file_name='comparacion_set_cover.csv')
    st.subheader('Variación entre las cinco semillas comunes')
    study=ROOT/'resultados/fase4/estudio_20261107T020734Z_cbfda0ea'
    st.dataframe(pd.read_csv(study/'genetico/resumen_configuraciones.csv'),hide_index=True)
    st.image(str(study/'comparacion_configuraciones_ag.png'),caption='Gráfica histórica de Fase 4: tres configuraciones, cinco semillas cada una.')
    st.warning('Mutación 0,01 produjo el mejor individuo del AG; inmigrantes produjo mejor media y menor dispersión con más esfuerzo. Ninguna media superó el costo inicial 49.734. No se demuestra superioridad general del AG.')
    st.subheader('Las cotas después de Fase 4')
    additional_chart()
    st.caption('Los pilotos de 30 s y las búsquedas de dos horas tienen presupuestos e inicios distintos. Los nodos de diferentes solvers no son unidades equivalentes de trabajo.')

elif page=='Informe y metodología':
    st.title('Informe definitivo y reproducción')
    report=ROOT/'docs/Informe_Proyecto_Oliva_Moreno.pdf'
    st.download_button('Descargar informe definitivo · 20 páginas',report.read_bytes(),file_name=report.name,mime='application/pdf',type='primary')
    st.write('**Autores:** Carlos Daniel Oliva Moreno y Camilo Andrés Oliva Moreno. **Docente:** Dilan Jhoanny Mogollon Carreño. **UNAB · Investigación de Operaciones I · 10 de noviembre de 2026.**')
    for title,file in [('Modelo matemático','modelo_matematico.md'),('Reproducción y trazabilidad','REPRODUCIBILIDAD.md'),('Guía de lectura','GUIA_USO.md')]:
        with st.expander(title):
            st.markdown((ROOT/'docs'/file).read_text(encoding='utf-8'))
    st.code('python -m setcover.cli verificar\npython -m pytest -q\npython -m streamlit run app.py',language='bash')
    st.caption(f"{c['archivos_verificados']} archivos contrastados con el manifiesto; 26 selecciones auditadas contra originales. Las pruebas de una instalación nueva deben ejecutarse en su propio entorno; no se confunden con los tests históricos.")

else:
    st.title('Demostraciones breves opcionales')
    st.write('La consulta académica funciona sin ejecutar optimizadores. Una demostración nueva no modifica ni actualiza los resultados históricos.')
    if os.environ.get('SETCOVER_ENABLE_DEMOS')!='1':
        st.info('Demostraciones desactivadas por defecto. Para uso local, iniciarlas con SETCOVER_ENABLE_DEMOS=1. Se recomienda mantenerlas desactivadas en Community Cloud.')
    else:
        with st.form('demo'):
            method=st.selectbox('Método',['AG','MILP'])
            seconds=st.slider('Límite de búsqueda (s)',1,3,1)
            accepted=st.checkbox('Aplicar el supuesto CSV j ↔ Excel j+1 en esta demostración')
            clicked=st.form_submit_button('Ejecutar demostración')
        if clicked:
            if not accepted:
                st.error('Debes aceptar el supuesto antes de ejecutar.')
            elif not demo_lock().acquire(blocking=False):
                st.warning('Ya hay una demostración activa. Inténtalo cuando termine.')
            else:
                try:
                    with st.spinner('Ejecutando demostración aislada…'),tempfile.TemporaryDirectory(prefix='setcover_demo_') as tmp:
                        output=Path(tmp)/'demo.json'
                        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
                        result=subprocess.run([sys.executable,'-B','-m','setcover.demo',method,str(seconds),str(output)],
                            cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',timeout=seconds+12)
                        if result.returncode!=0 or not output.is_file():
                            st.error('La demostración no terminó correctamente. Los resultados históricos permanecen intactos.')
                        else:
                            payload=json.loads(output.read_text(encoding='utf-8'))
                            st.session_state['demo_result']=payload
                except subprocess.TimeoutExpired:
                    st.warning('Se alcanzó el límite duro del proceso. No hay un resultado final verificable.')
                except (OSError,ValueError) as exc:
                    st.error('No se pudo ejecutar: '+str(exc))
                finally:
                    demo_lock().release()
        if 'demo_result' in st.session_state:
            payload=st.session_state['demo_result'];audit=payload['auditoria']
            if audit:
                st.success('Demostración nueva: costo '+audit['costo_recalculado_decimal']+'; 500/500 clientes. No sustituye resultados del informe.')
            else:
                st.warning('No hubo una solución factible verificable dentro del límite.')
            st.json({k:v for k,v in payload['resultado'].items() if k not in ['seleccion','historial']})
            st.download_button('Descargar demostración JSON',json.dumps(payload,ensure_ascii=False,indent=2),file_name='demostracion_nueva.json')