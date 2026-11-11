"""Formulacion en casos SINTETICOS; estados limites simulados se identifican como mocks."""
from itertools import product
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from setcover import solver
from setcover.audit import audit_originals
from setcover.data_io import DataError


def test_known_small_optimum():
    a = [[1,0,1],[1,1,0],[0,1,1]]
    result = solver.solve_exact(a, [2,3,2], time_limit=10)
    assert result['optimalidad_certificada_solver']
    assert result['solver_status_code'] == 0
    assert result['seleccion'] == [1,0,1]
    assert result['costo_total'] == 4
    assert result['mejor_cota'] == 4
    assert result['brecha_relativa_solver'] == 0


def test_weighted_cost_not_number_of_antennas():
    result = solver.solve_exact([[1,1,0],[1,0,1]], [9,2,3], time_limit=10)
    assert result['seleccion'] == [0,1,1]
    assert result['costo_total'] == 5
    assert result['optimalidad_certificada_solver']


def test_real_solver_infeasible_small():
    result = solver.solve_exact([[1,0],[0,0]], [1,2], time_limit=10)
    assert result['solver_status_code'] == 2
    assert result['seleccion'] is None
    assert not result['optimalidad_certificada_solver']


def test_zero_costs():
    result = solver.solve_exact(np.eye(3), [0,0,0], time_limit=10)
    assert result['costo_total'] == 0
    assert result['optimalidad_certificada_solver']


@pytest.mark.parametrize('seed', range(5))
def test_small_matches_exhaustive_enumeration(seed):
    rng = np.random.default_rng(seed)
    a = rng.integers(0,2,size=(5,7))
    a[:,0] = 1
    c = rng.integers(1,12,size=7)
    reference = min(float(c@x) for x in product([0,1],repeat=7) if (a@x>=1).all())
    result = solver.solve_exact(a,c,time_limit=10)
    assert result['optimalidad_certificada_solver']
    assert result['costo_total'] == reference


def fake_result(**kwargs):
    defaults = dict(status=1, success=False, message='MOCK Time limit reached',
                    x=np.array([1.,0.]), fun=5., mip_dual_bound=3., mip_gap=0.4, mip_node_count=10)
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_time_limit_incumbent_is_not_optimal(monkeypatch):
    monkeypatch.setattr(solver,'milp',lambda **kwargs:fake_result())
    r = solver.solve_exact([[1,1]], [5,9], 600)
    assert r['estado'] == 'factible_limite'
    assert r['factible_verificada']
    assert not r['optimalidad_certificada_solver']
    assert r['brecha_porcentaje_solver'] == 40
    assert r['mejor_cota'] == 3


def test_limit_without_incumbent(monkeypatch):
    monkeypatch.setattr(solver,'milp',lambda **kwargs:fake_result(x=None,fun=None,mip_gap=None,mip_dual_bound=None))
    r = solver.solve_exact([[1,1]], [5,9])
    assert r['seleccion'] is None and r['costo_total'] is None
    assert not r['optimalidad_certificada_solver']
    assert r['brecha_relativa_solver'] is None


@pytest.mark.parametrize('changes', [
    {'x':np.array([0.5,0.5])}, {'x':np.array([0.,0.]),'fun':0.},
    {'fun':99.}, {'fun':None}, {'x':np.array([2.,0.]),'fun':10.},
    {'x':np.array([float('nan'),0.])},
])
def test_invalid_incumbent_rejected(monkeypatch,changes):
    monkeypatch.setattr(solver,'milp',lambda **kwargs:fake_result(**changes))
    r = solver.solve_exact([[1,1]], [5,9])
    assert r['estado'] == 'error_verificacion'
    assert r['seleccion'] is None
    assert not r['optimalidad_certificada_solver']


def test_nonzero_gap_never_claims_proven_optimum(monkeypatch):
    monkeypatch.setattr(solver,'milp',lambda **kwargs:fake_result(status=0,success=True))
    assert not solver.solve_exact([[1,1]],[5,9])['optimalidad_certificada_solver']


def test_formulation_and_default_limit(monkeypatch):
    def inspect(**kw):
        np.testing.assert_array_equal(kw['integrality'],[1,1])
        np.testing.assert_array_equal(kw['bounds'].lb,[0,0])
        np.testing.assert_array_equal(kw['bounds'].ub,[1,1])
        np.testing.assert_array_equal(kw['constraints'].lb,[1])
        assert np.isposinf(kw['constraints'].ub).all()
        np.testing.assert_array_equal(kw['constraints'].A.toarray(),[[1,1]])
        assert kw['options']['time_limit'] == 600
        assert kw['options']['mip_rel_gap'] == 0
        return fake_result()
    monkeypatch.setattr(solver,'milp',inspect)
    solver.solve_exact([[1,1]],[5,9])


@pytest.mark.parametrize('seconds',[0,-1,float('nan'),float('inf')])
def test_invalid_time_limits(seconds):
    with pytest.raises(DataError):
        solver.solve_exact([[1]], [2], seconds)


def test_solver_exception_recorded(monkeypatch):
    def failure(**kwargs):
        raise RuntimeError('MOCK solver unavailable')
    monkeypatch.setattr(solver,'milp',failure)
    r = solver.solve_exact([[1]],[2])
    assert r['estado'] == 'error_solver'
    assert not r['optimalidad_certificada_solver']


def test_audit_reopens_originals_and_rejects_wrong_cost_or_selection():
    from openpyxl import load_workbook
    root = Path(__file__).resolve().parents[1]
    csv, excel = root/'datos/set_cover_500x500.csv', root/'datos/Costo_S.xlsx'
    book = load_workbook(excel,read_only=True,data_only=True)
    try:
        total = sum(list(book['Hoja1'].values)[1][1:])
    finally:
        book.close()
    assert audit_originals(csv,excel,[1]*500,total)['valida']
    assert not audit_originals(csv,excel,[1]*500,total+1)['valida']
    assert not audit_originals(csv,excel,[0]*500,0)['valida']
    assert not audit_originals(csv,excel,[1]*500,total,{'csv':'incorrecto','excel':'incorrecto'})['valida']
