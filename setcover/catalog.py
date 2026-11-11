"""Catálogo académico: adapters de lectura, auditorías y métricas; no optimiza."""
import csv
import hashlib
import io
import json
from pathlib import Path
import numpy as np
from .audit import audit_originals
from .data_io import DataError, load_coverage, load_costs, align_costs
from .validation import diagnose
ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def inside(root, value):
    root = Path(root).resolve()
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise DataError('Ruta fuera del proyecto.')
    return path


def csv_bytes(rows):
    if not rows:
        return b''
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8-sig')


def load_inputs(root=ROOT):
    root = Path(root)
    a = load_coverage(root/'datos/set_cover_500x500.csv')
    costs = load_costs(root/'datos/Costo_S.xlsx')
    c, mapping, rule = align_costs(a, costs, 'ordinal-0-1')
    identity = hashlib.sha256(a.matrix.astype('<i8').tobytes()+c.astype('<f8').tobytes()).hexdigest()
    return {'A':a.matrix, 'c':c, 'mapeo':mapping, 'regla':rule,
            'identidad':identity, 'diagnostico':diagnose(a,costs),
            'hashes':{'csv':a.metadata['sha256'],'excel':costs.metadata['sha256']}}


def verify_manifest(root=ROOT):
    root = Path(root)
    manifest = read_json(root/'resultados/procedencia.json')
    for entry in manifest:
        path = inside(root, entry['archivo'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise DataError('Archivo diferente del manifiesto: '+entry['archivo'])
    return len(manifest)


def normalize(entry, root=ROOT):
    path = inside(root, entry['archivo'])
    document = read_json(path)
    r = document.get('resultado', document)
    schema = entry['esquema']
    if schema == 'highs_adicional':
        cost=r['mejor_costo_verificado']; lower=r['cota_inferior_corrida']
        elapsed=r['tiempo_solver_segundos']; nodes=r['nodos_explorados']
        gap=r['brecha_relativa_solver']; solver='HiGHS 1.11.0'; certified=r['optimalidad_certificada']
    elif schema == 'scip_adicional':
        cost=r['mejor_costo_verificado']; lower=r['cota_inferior_propia']
        elapsed=r['tiempo_optimizacion_monotonico_segundos']; nodes=r['nodos_total']
        gap=r['brecha_nativa_SCIP']; solver='SCIP 9.2.1'; certified=r['optimalidad_certificada']
    elif schema == 'historico':
        cost=r['costo_total']; lower=r.get('mejor_cota')
        elapsed=r.get('tiempo_ag_segundos',r.get('tiempo_optimizacion_segundos',r.get('tiempo_solver_segundos')))
        nodes=r.get('nodos',r.get('nodos_explorados')); gap=r.get('brecha_relativa_solver')
        solver=r.get('version_solver',r.get('solver','SciPy/HiGHS')) if entry['metodo']=='MILP' else 'AG'
        certified=r.get('optimalidad_certificada_solver',r.get('optimalidad_demostrada',False))
    else:
        raise DataError('Esquema de resultado no reconocido.')
    params=r.get('parametros',{})
    if (path.parent/'configuracion.json').exists():
        params=read_json(path.parent/'configuracion.json')
    return {**entry, 'costo':cost, 'cota':lower, 'tiempo_s':elapsed, 'nodos':nodes,
            'solver':solver, 'antenas':r['numero_antenas'], 'clientes':r['clientes_cubiertos'],
            'estado':r.get('motivo_parada',r.get('estado_solver',r.get('estado'))),
            'semilla':r.get('semilla'), 'configuracion':r.get('configuracion','original'),
            'optimo_certificado':bool(certified), 'brecha_nativa_pct':None if gap is None else 100*gap,
            'seleccion':r['seleccion'], 'historial':r.get('historial',[]),
            'parametros':params, 'documento':document}


def load_catalog(root=ROOT):
    root=Path(root)
    verified_files=verify_manifest(root)
    inputs=load_inputs(root)
    records=[]
    for entry in read_json(root/'resultados/indice.json'):
        record=normalize(entry,root)
        if record['costo'] is None or record['tiempo_s'] is None:
            raise DataError('Resultado incompleto: '+record['archivo'])
        audit=audit_originals(root/'datos/set_cover_500x500.csv',root/'datos/Costo_S.xlsx',
                              record['seleccion'],record['costo'],inputs['hashes'])
        if not audit['valida'] or record['antenas']!=sum(record['seleccion']) or record['clientes']!=audit['clientes_cubiertos']:
            raise DataError('Resultado no verificable: '+record['archivo'])
        if record['cota'] is not None and record['cota']>record['costo']:
            raise DataError('Cota mayor que el incumbente.')
        record['auditoria']=audit
        records.append(record)
    best_ga=min((r for r in records if r['metodo']=='AG'),key=lambda r:r['costo'])
    best_global=min(records,key=lambda r:r['costo'])
    best_bound=max((r for r in records if r['cota'] is not None),key=lambda r:r['cota'])
    lower=best_bound['cota']; upper=best_global['costo']
    if lower>upper:
        raise DataError('Cotas globales contradictorias.')
    return {'entradas':inputs,'corridas':records,'mejor_ag':best_ga,'mejor_global':best_global,
            'mejor_cota':best_bound,'cota':lower,'separacion':100*(upper-lower)/abs(upper),
            'archivos_verificados':verified_files}


def public_rows(catalog):
    keys=['etiqueta','metodo','estudio','costo','antenas','clientes','tiempo_s','cota','estado','semilla','nodos','optimo_certificado']
    return [{k:r[k] for k in keys} for r in catalog['corridas']]


def additional_progress(catalog, root=ROOT):
    """Serie histórica propia de cada ejecución; no interpola ni reanuda árboles."""
    points=[]
    for r in catalog['corridas']:
        if r['esquema'] not in ('highs_adicional','scip_adicional'):
            continue
        highs=r['esquema']=='highs_adicional'
        path=inside(root,r['archivo']).parent/'progreso.jsonl'
        if not path.is_file():
            continue
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            d=json.loads(line)
            t=d['tiempo_solver_segundos'] if highs else d['tiempo_scip_acumulado']
            lower=d.get('cota_inferior_corrida') if highs else d.get('cota_inferior_propia')
            if lower is not None:
                points.append({'solver':'HiGHS' if highs else 'SCIP','minutos':t/60,'cota':lower})
        native=r['documento'].get('tiempo_scip_acumulado',r['tiempo_s'])
        points.append({'solver':'HiGHS' if highs else 'SCIP','minutos':native/60,'cota':r['cota']})
    return points