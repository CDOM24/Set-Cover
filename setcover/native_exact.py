"""Modelos identicos de SET COVER con HiGHS nativo y SCIP, sin alterar Fases 2/3."""
import math
from pathlib import Path
from time import perf_counter
import numpy as np
from scipy.sparse import csr_matrix
from .validation import validate_arrays
from .verification import verify_solution
from .data_io import DataError

def finite(value):
    if value is None:
        return None
    value=float(value)
    return value if math.isfinite(value) and abs(value)<1e19 else None

def solve_native(a,c,solver='highs',limit=30,start=None,log=None,relaxation=False,effort=0.05):
    a=validate_arrays(a,c); c=np.asarray(c,dtype=float)
    if not math.isfinite(limit) or limit<=0:
        raise DataError('Tiempo positivo requerido.')
    if solver not in ('highs','scip'):
        raise DataError('Solver desconocido.')
    if start is not None:
        verification=verify_solution(a,c,start)
        if not verification['valida']:
            raise DataError('Inicio no factible.')
        start=np.asarray(start,dtype=float)
    built=perf_counter(); m,n=a.shape
    result={'solver':solver,'limite_segundos':limit,'relajacion_lineal':relaxation,
            'inicio_suministrado':start is not None,'costo_inicio':float(c@start) if start is not None else None,
            'parametros':{'hilos':1,'semilla':0,'brecha_relativa':0,'brecha_absoluta':0},
            'seleccion':None,'costo_total':None,'factible_verificada':False,'optimalidad_certificada_solver':False}
    if solver=='highs':
        import highspy
        h=highspy.Highs()
        for key,value in {'threads':1,'random_seed':0,'time_limit':float(limit),'mip_rel_gap':0.0,
                          'mip_abs_gap':0.0,'presolve':'on','log_to_console':False,'mip_heuristic_effort':effort}.items():
            if h.setOptionValue(key,value)!=highspy.HighsStatus.kOk:
                raise DataError('Opcion HiGHS rechazada: '+key)
        if log:
            h.setOptionValue('log_file',str(log))
        result['version_solver']=h.version(); result['parametros']['mip_heuristic_effort']=effort
        assert h.addCols(n,c,np.zeros(n),np.ones(n),0,np.zeros(n+1,dtype=np.int32),np.array([],dtype=np.int32),np.array([],dtype=float))==highspy.HighsStatus.kOk
        matrix=csr_matrix(a,dtype=float)
        assert h.addRows(m,np.ones(m),np.full(m,highspy.kHighsInf),matrix.nnz,matrix.indptr.astype(np.int32),matrix.indices.astype(np.int32),matrix.data)==highspy.HighsStatus.kOk
        if not relaxation:
            assert h.changeColsIntegrality(n,np.arange(n,dtype=np.int32),np.full(n,int(highspy.HighsVarType.kInteger),dtype=np.uint8))==highspy.HighsStatus.kOk
        if start is not None:
            accepted=h.setSolution(n,np.arange(n,dtype=np.int32),start)
            result['inicio_aceptado_api']=accepted==highspy.HighsStatus.kOk
        if log:
            h.writeModel(str(Path(log).with_suffix('.mps')))
        began=perf_counter(); status_run=h.run(); elapsed=perf_counter()-began
        info=h.getInfo(); solution=h.getSolution(); model_status=h.getModelStatus()
        raw=np.array(solution.col_value) if solution.value_valid else None
        objective=finite(info.objective_function_value) if solution.value_valid else None
        result.update({'estado_solver':h.modelStatusToString(model_status),'codigo_estado_solver':int(model_status),
                       'codigo_api':str(status_run),'mejor_cota':finite(info.mip_dual_bound) if not relaxation else objective,
                       'brecha_relativa_solver':finite(info.mip_gap) if not relaxation else None,
                       'nodos':int(info.mip_node_count) if not relaxation else 0})
        reported_optimal=model_status==highspy.HighsModelStatus.kOptimal
        if log and raw is not None:
            h.writeSolution(str(Path(log).with_suffix('.sol')),0)
    else:
        from pyscipopt import Model,quicksum
        model=Model('set_cover_mismo_modelo')
        model.hideOutput()
        model.setRealParam('limits/time',float(limit)); model.setRealParam('limits/gap',0.0)
        model.setRealParam('limits/absgap',0.0); model.setIntParam('parallel/maxnthreads',1)
        model.setIntParam('randomization/randomseedshift',0)
        if log:
            model.setLogfile(str(log))
        variables=[model.addVar(name=f'x_{j}',vtype='C' if relaxation else 'B',lb=0,ub=1,obj=float(c[j])) for j in range(n)]
        for i in range(m):
            model.addCons(quicksum(variables[j] for j in np.flatnonzero(a[i]))>=1,name=f'cubre_{i}')
        model.setMinimize()
        if start is not None:
            solution=model.createSol()
            for var,value in zip(variables,start):
                model.setSolVal(solution,var,float(value))
            result['inicio_aceptado_api']=bool(model.addSol(solution))
        if log:
            model.writeProblem(str(Path(log).with_suffix('.cip')),verbose=False)
        result['version_solver']=f'{model.getMajorVersion()}.{model.getMinorVersion()}.{model.getTechVersion()}'
        began=perf_counter(); model.optimize(); elapsed=perf_counter()-began
        best=model.getBestSol() if model.getNSols()>0 else None
        raw=np.array([model.getSolVal(best,v) for v in variables]) if best is not None else None
        objective=finite(model.getObjVal()) if best is not None else None
        state=str(model.getStatus())
        result.update({'estado_solver':state,'mejor_cota':finite(model.getDualbound()),
                       'brecha_relativa_solver':finite(model.getGap()),'nodos':int(model.getNNodes())})
        reported_optimal=state=='optimal'
        if log and best is not None:
            model.writeSol(best,str(Path(log).with_suffix('.sol')))
    result.update({'tiempo_optimizacion_segundos':elapsed,'tiempo_construccion_y_solver_segundos':perf_counter()-built,
                   'objetivo_reportado_solver':objective})
    if raw is not None:
        result['vector_crudo_solver']=raw.tolist()
        if relaxation:
            result['optimo_relajacion_reportado']=reported_optimal
            result['costo_relajacion']=objective
        elif np.isclose(raw,np.rint(raw),rtol=0,atol=1e-6).all():
            x=np.rint(raw).astype(np.int64)
            check=verify_solution(a,c,x,objective)
            if not check['valida']:
                raise DataError('Solver devolvio seleccion/costo no verificable.')
            result.update({'seleccion':x.tolist(),'costo_total':check['costo_recalculado'],
                           'numero_antenas':check['antenas_seleccionadas'],'clientes_cubiertos':check['clientes_cubiertos'],
                           'factible_verificada':True,'verificacion':check})
            bound=result['mejor_cota']; gap=result['brecha_relativa_solver']
            result['optimalidad_certificada_solver']=bool(reported_optimal and bound is not None and objective is not None
                and math.isclose(bound,objective,rel_tol=1e-9,abs_tol=1e-6) and gap is not None and gap<=1e-9)
        else:
            raise DataError('La solucion MILP no es binaria dentro de tolerancia.')
    return result
