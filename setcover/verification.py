"""Verificador independiente de futuras soluciones exactas y geneticas."""
import math
import numpy as np
from .data_io import DataError
from .validation import validate_arrays

def verify_solution(matrix, costs, selection, reported_cost=None):
    a = validate_arrays(matrix, costs)
    c, x = np.asarray(costs, dtype=float), np.asarray(selection)
    if x.shape != (a.shape[1],) or not np.isin(x, [0, 1]).all():
        raise DataError('Seleccion: vector binario de longitud igual al numero de antenas requerido.')
    counts = a @ x.astype(np.int64)
    value = float(c @ x)
    consistent = reported_cost is None or math.isclose(value, reported_cost, rel_tol=1e-9, abs_tol=1e-8)
    return {'valida': bool((counts >= 1).all() and consistent), 'costo_recalculado': value,
            'costo_coincide': consistent, 'clientes_cubiertos': int((counts >= 1).sum()),
            'clientes_sin_cubrir_posiciones': np.flatnonzero(counts == 0).tolist(),
            'antenas_seleccionadas': int(x.sum())}
