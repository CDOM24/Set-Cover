"""Proceso opcional con tiempo duro del padre; resultados nuevos y efímeros."""
from dataclasses import replace
import json
from pathlib import Path
import sys
from .catalog import load_inputs, ROOT
from .genetic import GAConfig, run_genetic
from .solver import solve_exact
from .audit import audit_originals


def run(method,seconds):
    if method not in ('AG','MILP') or isinstance(seconds,bool) or not isinstance(seconds,int) or not 1<=seconds<=3:
        raise ValueError('Demostración: método válido y límite entero de 1 a 3 segundos.')
    data=load_inputs()
    if method=='AG':
        result=run_genetic(data['A'],data['c'],44,GAConfig(population_size=20,generations=30,mutation_probability=.01,time_limit=float(seconds)))
    else:
        result=solve_exact(data['A'],data['c'],time_limit=seconds)
    audit=None
    if result.get('seleccion') is not None:
        audit=audit_originals(ROOT/'datos/set_cover_500x500.csv',ROOT/'datos/Costo_S.xlsx',result['seleccion'],result['costo_total'],data['hashes'])
        if not audit['valida']:
            raise ValueError('Auditoría fallida.')
    return {'tipo':'demostracion_nueva_fuera_del_estudio','resultado':result,'auditoria':audit}


if __name__=='__main__':
    if len(sys.argv)!=4:
        raise SystemExit('Uso: python -m setcover.demo AG|MILP segundos salida.json')
    payload=run(sys.argv[1],int(sys.argv[2]))
    # El padre suministra una carpeta temporal; nunca se escribe en resultados históricos.
    Path(sys.argv[3]).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')