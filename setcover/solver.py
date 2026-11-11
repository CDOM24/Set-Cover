"""MILP binario con SciPy/HiGHS; no contiene heuristicas ni AG."""
import math
from time import perf_counter
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csc_matrix
from .data_io import DataError
from .validation import validate_arrays
from .verification import verify_solution

STATUS = {0: 'optimo_reportado', 1: 'limite_alcanzado', 2: 'inviable', 3: 'no_acotado', 4: 'error_solver'}

def finite_or_none(value):
    if value is None:
        return None
    value = float(value)
    return value if math.isfinite(value) else None

def solve_exact(matrix, costs, time_limit=600.0, disp=False):
    """Min c@x, A@x>=1, x entero y 0<=x<=1. Limite en segundos."""
    started = perf_counter()
    if not math.isfinite(time_limit) or time_limit <= 0:
        raise DataError('El limite de tiempo debe ser positivo y finito.')
    a = validate_arrays(matrix, costs)
    c = np.asarray(costs, dtype=float)
    m, n = a.shape
    constraints = LinearConstraint(csc_matrix(a, dtype=float), np.ones(m), np.full(m, np.inf))
    bounds = Bounds(np.zeros(n), np.ones(n))
    integrality = np.ones(n, dtype=np.uint8)
    options = {'time_limit': float(time_limit), 'mip_rel_gap': 0.0, 'presolve': True, 'disp': bool(disp)}
    built = perf_counter()
    try:
        raw = milp(c=c, integrality=integrality, bounds=bounds, constraints=constraints, options=options)
    except Exception as exc:
        return {'estado': 'error_solver', 'solver_status_code': None, 'solver_message': str(exc),
                'solver_success': False, 'parametros': options, 'seleccion': None,
                'factible_verificada': False, 'optimalidad_certificada_solver': False,
                'costo_total': None, 'mejor_cota': None, 'brecha_relativa_solver': None,
                'brecha_porcentaje_solver': None, 'numero_antenas': None, 'clientes_cubiertos': None,
                'tiempo_solver_segundos': perf_counter()-built, 'tiempo_total_segundos': perf_counter()-started}
    ended = perf_counter()
    status = int(raw.status)
    bound = finite_or_none(getattr(raw, 'mip_dual_bound', None))
    gap = finite_or_none(getattr(raw, 'mip_gap', None))
    objective = finite_or_none(getattr(raw, 'fun', None))
    nodes = finite_or_none(getattr(raw, 'mip_node_count', None))
    result = {
        'estado': STATUS.get(status, 'estado_desconocido'), 'solver_status_code': status,
        'solver_message': str(raw.message), 'solver_success': bool(raw.success),
        'parametros': options, 'tiempo_construccion_segundos': built-started,
        'tiempo_solver_segundos': ended-built, 'tiempo_total_segundos': ended-started,
        'objetivo_reportado_solver': objective, 'mejor_cota': bound,
        'brecha_relativa_solver': gap, 'brecha_porcentaje_solver': 100*gap if gap is not None else None,
        'nodos_explorados': int(nodes) if nodes is not None else None,
        'seleccion': None, 'factible_verificada': False, 'optimalidad_certificada_solver': False,
        'costo_total': None, 'numero_antenas': None, 'clientes_cubiertos': None,
        'verificacion': None, 'tolerancia_integralidad_lectura': 1e-6,
    }
    vector = getattr(raw, 'x', None)
    if vector is not None:
        x = np.asarray(vector, dtype=float)
        result['vector_crudo_solver'] = x.tolist() if np.isfinite(x).all() else None
        if x.shape != (n,) or not np.isfinite(x).all() or not np.isclose(x, np.rint(x), rtol=0, atol=1e-6).all():
            result['estado'] = 'error_verificacion'
            result['motivo_rechazo'] = 'El solver no devolvio un vector binario dentro de tolerancia.'
            return result
        selection = np.rint(x).astype(np.int64)
        if not np.isin(selection, [0, 1]).all():
            result['estado'] = 'error_verificacion'
            result['motivo_rechazo'] = 'Seleccion fuera de los limites binarios.'
            return result
        verification = verify_solution(a, c, selection, objective)
        result['verificacion'] = verification
        # Sin objetivo del solver no se certifica la consistencia del incumbente.
        if not verification['valida'] or objective is None:
            result['estado'] = 'error_verificacion'
            result['motivo_rechazo'] = 'Cobertura incompleta o costo inconsistente/ausente.'
            return result
        result.update({'seleccion': selection.tolist(), 'factible_verificada': True,
                       'costo_total': verification['costo_recalculado'],
                       'numero_antenas': verification['antenas_seleccionadas'],
                       'clientes_cubiertos': verification['clientes_cubiertos']})
        zero_gap = gap is None or (0 <= gap <= 1e-9)
        bound_ok = bound is None or math.isclose(bound, objective, rel_tol=1e-9, abs_tol=1e-7)
        certified = status == 0 and bool(raw.success) and zero_gap and bound_ok
        result['optimalidad_certificada_solver'] = certified
        result['estado'] = 'optimo_certificado_solver' if certified else ('factible_limite' if status == 1 else 'factible_sin_certificacion')
    return result
