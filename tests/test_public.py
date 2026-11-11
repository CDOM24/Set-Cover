"""Regresiones de entrega pública; las búsquedas probadas usan instancias sintéticas."""
import hashlib
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pytest
from pypdf import PdfReader
from streamlit.testing.v1 import AppTest
from setcover.catalog import ROOT,load_catalog,load_inputs,inside,verify_manifest,additional_progress,normalize,read_json
from setcover.demo import run

@pytest.fixture(scope='module')
def catalog():
    return load_catalog()

def test_three_different_scientific_roles(catalog):
    assert len(catalog['corridas'])==26
    assert len([r for r in catalog['corridas'] if r['metodo']=='AG'])==20
    assert catalog['mejor_ag']['costo']==49051
    assert catalog['mejor_ag']['tiempo_s']==pytest.approx(5.717906599998969)
    assert catalog['mejor_global']['costo']==48878
    assert catalog['mejor_global']['esquema']=='highs_adicional'
    assert catalog['mejor_cota']['esquema']=='scip_adicional'
    assert catalog['cota']==pytest.approx(34532.73615154492)
    assert catalog['separacion']==pytest.approx(29.34912199446597)
    assert not any(r['optimo_certificado'] for r in catalog['corridas'])
    assert all(r['auditoria']['valida'] and r['clientes']==500 for r in catalog['corridas'])

def test_same_best_selection_different_solver_contributions(catalog):
    highs=next(r for r in catalog['corridas'] if r['esquema']=='highs_adicional')
    scip=next(r for r in catalog['corridas'] if r['esquema']=='scip_adicional')
    assert highs['seleccion']==scip['seleccion']
    assert highs['cota']==33433
    assert scip['tiempo_s']==pytest.approx(7160.922999999995)
    assert sum(highs['seleccion'])==22
    assert sum(float(x['costo_original']) for x in highs['auditoria']['costos_seleccionados'])==48878

def test_persisted_files_and_final_pdf(catalog):
    assert verify_manifest()>100
    report=ROOT/'docs/Informe_Proyecto_Oliva_Moreno.pdf'
    assert len(PdfReader(report).pages)==20
    assert hashlib.sha256(report.read_bytes()).hexdigest()=='e4bfc2b9c7f0c5e69c72c0e24522b8a195bac5d2870584e0a208b15fddfaca55'

def test_new_adapter_rejects_unknown_schema():
    entry=read_json(ROOT/'resultados/indice.json')[0]
    with pytest.raises(ValueError,match='Esquema'):
        normalize(dict(entry,esquema='desconocido'))

def test_paths_independent_of_working_directory(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_inputs()['A'].shape==(500,500)
    with pytest.raises(ValueError):
        inside(ROOT,'../otro_proyecto/archivo.json')

def test_log_trajectories_have_final_bounds(catalog):
    p=additional_progress(catalog)
    assert max(r['cota'] for r in p if r['solver']=='HiGHS')==33433
    assert max(r['cota'] for r in p if r['solver']=='SCIP')==pytest.approx(34532.73615154492)

@pytest.mark.parametrize('method,seconds',[('AG',0),('MILP',4),('otro',1),('AG',True)])
def test_demos_reject_out_of_bounds_before_loading(method,seconds):
    with patch('setcover.demo.load_inputs',side_effect=AssertionError('No cargar')):
        with pytest.raises(ValueError):run(method,seconds)

def test_ui_all_pages_do_not_start_optimizers(monkeypatch):
    monkeypatch.setenv('SETCOVER_ENABLE_DEMOS','1')
    with (patch('setcover.solver.solve_exact',side_effect=AssertionError('No optimizar')),
          patch('setcover.genetic.run_genetic',side_effect=AssertionError('No optimizar'))):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=45).run()
        assert not app.exception
        assert any(m.value=='48.878' for m in app.metric)
        assert any(m.value=='49.051' for m in app.metric)
        assert any(m.value=='34.532,74' for m in app.metric)
        assert list(app.sidebar.radio[0].options)==['Inicio','Problema y datos','Método exacto','Algoritmo genético','Comparación','Metodología']
        assert any('<h1>SET COVER</h1>' in m.value for m in app.markdown)
        for page in ['Problema y datos','Método exacto','Algoritmo genético','Comparación','Metodología']:
            app.sidebar.radio[0].set_value(page).run()
            assert not app.exception
            assert not app.get('file_uploader')
            assert not app.get('form')
            assert not any('SETCOVER_ENABLE_DEMOS' in m.value for m in app.markdown)
        assert not any(b.label=='Ejecutar demostración' for b in app.button)

def test_genetic_page_defaults_to_ag_not_global():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=45).run()
    app.sidebar.radio[0].set_value('Algoritmo genético').run()
    assert not app.exception
    assert any(m.value=='49.051' for m in app.metric)
def test_historical_rational_dual_without_optimization(catalog):
    from fractions import Fraction
    import math
    certificate=read_json(ROOT/'resultados/fase4/estudio_20261107T020734Z_cbfda0ea/certificado_dual_lp.json')
    decode=lambda d:Fraction(int(d['numerador']),int(d['denominador']))
    y=[decode(d) for d in certificate['y']]
    assert len(y)==500 and all(v>=0 for v in y)
    a=catalog['entradas']['A'];costs=catalog['entradas']['c']
    for j in range(500):
        activity=sum((y[i] for i in range(500) if a[i,j]),Fraction(0))
        assert activity<=Fraction(str(costs[j]))
    assert sum(y,Fraction(0))==decode(certificate['cota_racional'])
    assert math.ceil(sum(y,Fraction(0)))==27860
    assert certificate['no_certifica_optimo_entero']

def test_exact_page_presents_four_latex_equations():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=45).run()
    app.sidebar.radio[0].set_value('Método exacto').run()
    assert not app.exception
    equations=[item.value for item in app.latex]
    assert len(equations)==4
    assert all('\\' in eq for eq in equations)
    assert any('sum' in eq and 'c_j' in eq for eq in equations)
    assert any('A_{ij}' in eq and 'geq' in eq for eq in equations)
    assert any('x_j' in eq and '0,1' in eq and r'\in' in eq for eq in equations)
    assert any('mathsf T' in eq and 'mathbf{1}' in eq for eq in equations)


def test_public_documentation_links_and_no_obsolete_ui():
    import re
    for relative in ['README.md','docs/modelo_matematico.md','docs/GUIA_USO.md']:
        doc=ROOT/relative
        for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
            if not link.startswith(('https://','http://','#')):
                assert (doc.parent/link.split('#')[0]).exists(),link
    text=(ROOT/'docs/modelo_matematico.md').read_text(encoding='utf-8')
    assert all(old not in text for old in ['resultados/fase1/mapeo_antenas.csv','revision_mapeo.json','supuesto_correspondencia.md'])
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    assert all(old not in app for old in ['file_uploader','SETCOVER_ENABLE_DEMOS','subprocess','st.form('])
    assert app.count('Carlos Daniel Oliva Moreno')==1
    assert app.count('Camilo Andrés Oliva Moreno')==1
