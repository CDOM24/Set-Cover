"""Verificación sin optimización y búsquedas locales explícitas en salidas nuevas."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import platform
from .catalog import load_catalog, load_inputs
from .genetic import GAConfig, run_genetic
from .genetic_diversity import run_with_immigrants
from .native_exact import solve_native
from .solver import solve_exact
from .verification import verify_solution


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('verificar')
    run=sub.add_parser('resolver')
    run.add_argument('--metodo',choices=['ag','inmigrantes','scipy','highs','scip'],required=True)
    run.add_argument('--segundos',type=float,required=True)
    run.add_argument('--semilla',type=int,default=44)
    run.add_argument('--mutacion',type=float,default=.01)
    run.add_argument('--inicio',choices=['ninguno','mejor-ag','mejor-global'],default='ninguno')
    run.add_argument('--salida',type=Path,required=True,help='Carpeta NUEVA, fuera de resultados históricos.')
    args=p.parse_args()
    if args.command=='verificar':
        c=load_catalog()
        print(json.dumps({'corridas':len(c['corridas']),'mejor_ag':c['mejor_ag']['costo'],
          'mejor_global':c['mejor_global']['costo'],'cota':c['cota'],'separacion_pct':c['separacion'],
          'certificado':any(r['optimo_certificado'] for r in c['corridas'])},ensure_ascii=False,indent=2))
        return
    if not 0<args.segundos<=7200:
        p.error('El límite explícito debe estar entre 0 y 7200 segundos.')
    inputs=load_inputs(); directory=args.salida.resolve()
    from .catalog import ROOT
    protected=[ROOT/'resultados',ROOT/'datos',ROOT/'setcover',ROOT/'docs',ROOT/'tests',ROOT/'.git']
    if directory==ROOT or any(directory.is_relative_to(d) for d in protected):
        p.error('Usar una carpeta nueva fuera de las fuentes y resultados históricos.')
    if args.inicio!='ninguno' and args.metodo not in ('highs','scip'):
        p.error('El inicio persistido solo está implementado en las interfaces nativas highs/scip.')
    directory.mkdir(parents=True,exist_ok=False)
    start=None
    if args.inicio!='ninguno':
        c=load_catalog();start=c['mejor_ag' if args.inicio=='mejor-ag' else 'mejor_global']['seleccion']
    if args.metodo in ('ag','inmigrantes'):
        cfg=GAConfig(time_limit=args.segundos,mutation_probability=args.mutacion)
        result=(run_genetic if args.metodo=='ag' else run_with_immigrants)(inputs['A'],inputs['c'],args.semilla,cfg)
    elif args.metodo=='scipy':
        result=solve_exact(inputs['A'],inputs['c'],time_limit=args.segundos)
    else:
        result=solve_native(inputs['A'],inputs['c'],args.metodo,args.segundos,start,log=directory/'solver.log')
    audit=None
    if result.get('seleccion') is not None:
        audit=verify_solution(inputs['A'],inputs['c'],result['seleccion'],result['costo_total'])
    payload={'resultado':result,'verificacion':audit,'entrada':inputs['hashes'],'python':platform.python_version(),
      'nota':'Ejecución nueva; no sobrescribe ni reproduce automáticamente los tiempos o el árbol de los experimentos publicados.'}
    (directory/'resultado.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print(directory/'resultado.json')


if __name__=='__main__':
    main()