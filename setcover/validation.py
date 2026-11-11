"""Diagnostico de datos; no ejecuta optimizacion."""
import numpy as np
from .data_io import DataError

def validate_arrays(matrix, costs=None):
    a = np.asarray(matrix)
    if a.ndim != 2 or min(a.shape) == 0 or not np.isfinite(a).all() or not np.isin(a, [0, 1]).all():
        raise DataError('Cobertura: matriz no vacia, finita y binaria requerida.')
    if costs is not None:
        c = np.asarray(costs)
        if c.shape != (a.shape[1],) or not np.isfinite(c).all() or (c < 0).any():
            raise DataError('Costos: vector finito, no negativo y alineado en longitud requerido.')
    return a.astype(np.int64)

def duplicate_groups(a, labels):
    groups = {}
    for row, label in zip(a, labels):
        groups.setdefault(tuple(row.tolist()), []).append(label)
    return [group for group in groups.values() if len(group) > 1]

def diagnose(coverage, costs):
    a = validate_arrays(coverage.matrix)
    rs, cs = a.sum(axis=1), a.sum(axis=0)
    missing = [coverage.client_ids[i] for i in np.flatnonzero(rs == 0)]
    return {
        'clientes': a.shape[0], 'antenas': a.shape[1], 'unos': int(a.sum()),
        'densidad': float(a.mean()),
        'clientes_cubribles_proporcion': float((rs > 0).mean()),
        'clientes_sin_cobertura': missing,
        'antenas_sin_cobertura': [coverage.antenna_ids[j] for j in np.flatnonzero(cs == 0)],
        'filas_duplicadas': duplicate_groups(a, coverage.client_ids),
        'columnas_duplicadas': duplicate_groups(a.T, coverage.antenna_ids),
        'cobertura_por_cliente': {'min': int(rs.min()), 'max': int(rs.max()), 'media': float(rs.mean())},
        'clientes_por_antena': {'min': int(cs.min()), 'max': int(cs.max()), 'media': float(cs.mean())},
        'costos': {'cantidad': len(costs.costs), 'min': float(costs.costs.min()),
                   'max': float(costs.costs.max()), 'media': float(costs.costs.mean()),
                   'suma': float(costs.costs.sum()),
                   'valores_distintos': len(set(costs.costs.tolist()))},
        'factibilidad_cobertura': not missing,
        'interpretacion_factibilidad': 'Sin otras restricciones, instalar todas las antenas cubre a todos si y solo si no hay filas nulas. No constituye optimizacion.',
    }
