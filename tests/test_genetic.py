"""Instancias SINTETICAS DE PRUEBA de operadores y AG; no son experimentos reales."""
from dataclasses import replace
import numpy as np
import pytest
from setcover.data_io import DataError
from setcover.genetic import GAConfig,SetCoverOperators,chromosome,mutate,uniform_crossover,tournament,run_genetic
from setcover.verification import verify_solution

A=np.array([[1,0,1],[1,1,0],[0,1,1]])
C=np.array([2,3,2])


def test_repair_empty_and_remove_redundancy():
    op=SetCoverOperators(A,C)
    x=op.repair([0,0,0],np.random.default_rng(11))
    assert verify_solution(A,C,x)['valida']
    for j in np.flatnonzero(x):
        y=x.copy(); y[j]=0
        assert not verify_solution(A,C,y)['valida']


def test_prune_expensive_redundant_antenna():
    op=SetCoverOperators([[1,1,0],[1,0,1]],[9,2,3])
    assert op.prune([1,1,1],np.random.default_rng(1)).tolist()==[0,1,1]


def test_zero_cost_repair_no_division_by_zero():
    op=SetCoverOperators(np.eye(3),[0,0,0])
    x=op.repair([0,0,0],np.random.default_rng(1))
    assert x.tolist()==[1,1,1]
    assert op.evaluate(x)['costo']==0


def test_uncoverable_client_rejected():
    with pytest.raises(DataError):
        SetCoverOperators([[1,0],[0,0]],[1,2])


def test_empty_antenna_is_pruned():
    op=SetCoverOperators([[1,0]],[1,0])
    assert op.repair([1,1],np.random.default_rng(1)).tolist()==[1,0]


def test_infeasible_fitness_worse_than_any_feasible():
    op=SetCoverOperators(A,C)
    assert op.evaluate([0,0,0])['fitness_minimizar']>C.sum()
    assert op.evaluate([1,0,1])['fitness_minimizar']==4


@pytest.mark.parametrize('x',[[1,0],[1,0.3,0],[1,2,0],[float('nan'),0,1]])
def test_bad_chromosome(x):
    with pytest.raises(DataError):
        chromosome(x,3)


def test_mutation_extremes_and_parent_preserved():
    parent=np.array([1,0,1])
    assert mutate(parent,0,np.random.default_rng(1)).tolist()==[1,0,1]
    assert mutate(parent,1,np.random.default_rng(1)).tolist()==[0,1,0]
    assert parent.tolist()==[1,0,1]


def test_uniform_crossover_and_parents_preserved():
    a,b=np.zeros(20,dtype=int),np.ones(20,dtype=int)
    x,y=uniform_crossover(a,b,1,np.random.default_rng(4))
    np.testing.assert_array_equal(x+y,np.ones(20))
    assert 0<x.sum()<20
    assert a.sum()==0 and b.sum()==20
    x,y=uniform_crossover(a,b,0,np.random.default_rng(4))
    x[0]=1
    assert a[0]==0 and y.sum()==20


def test_tournament_selects_best_of_drawn_candidates():
    pop=np.eye(3,dtype=int); scores=[10,2,5]
    class FixedRNG:
        def integers(self,*args,**kwargs):
            return np.array([0,2,1])
    np.testing.assert_array_equal(tournament(pop,scores,3,FixedRNG()),pop[1])


@pytest.mark.parametrize('changes',[{'population_size':1},{'elite_count':0},{'elite_count':80},
    {'generations':-1},{'tournament_size':0},{'mutation_probability':1.1},
    {'crossover_probability':-0.1},{'time_limit':0},{'time_limit':float('nan')},
    {'stagnation_generations':-1},{'repair_candidates':0},{'greedy_fraction':2}])
def test_invalid_parameters(changes):
    with pytest.raises(DataError):
        replace(GAConfig(),**changes).validate()


def test_seed_reproducibility_fixed_generations():
    cfg=GAConfig(population_size=12,generations=10,elite_count=2,stagnation_generations=0,time_limit=30)
    first=run_genetic(A,C,11,cfg); second=run_genetic(A,C,11,cfg)
    assert first['seleccion']==second['seleccion']
    assert first['costo_total']==second['costo_total']==4
    for a,b in zip(first['historial'],second['historial']):
        assert {k:v for k,v in a.items() if k!='tiempo_segundos'}=={k:v for k,v in b.items() if k!='tiempo_segundos'}
    assert first['generaciones_completas']==10


def test_elitism_monotone_and_final_feasible():
    rng=np.random.default_rng(4)
    a=rng.integers(0,2,size=(12,15)); a[:,0]=1
    c=rng.integers(1,10,size=15)
    cfg=GAConfig(population_size=16,generations=12,elite_count=2,time_limit=30,stagnation_generations=0)
    r=run_genetic(a,c,4,cfg)
    curve=[h['mejor_costo'] for h in r['historial']]
    assert all(y<=x for x,y in zip(curve,curve[1:]))
    assert verify_solution(a,c,r['seleccion'],r['costo_total'])['valida']
    assert all(h['clientes_cubiertos_minimo']==12 for h in r['historial'])
    assert not r['optimalidad_demostrada']


def test_stagnation_stop():
    cfg=GAConfig(population_size=6,generations=30,elite_count=1,time_limit=30,stagnation_generations=2)
    r=run_genetic(np.eye(3),[1,2,3],1,cfg)
    assert r['motivo_parada']=='estancamiento'
    assert r['generaciones']==2


def test_tiny_time_limit_preserves_verified_best():
    cfg=GAConfig(population_size=6,generations=30,elite_count=1,time_limit=1e-9)
    r=run_genetic(A,C,1,cfg)
    assert r['motivo_parada']=='tiempo'
    assert r['factible_verificada']
    assert r['generaciones']==0


def test_zero_generations_means_initialization_only():
    cfg=GAConfig(population_size=6,generations=0,elite_count=1,time_limit=30)
    r=run_genetic(A,C,1,cfg)
    assert len(r['historial'])==1 and r['factible_verificada']


def test_repair_does_not_modify_input():
    x=np.zeros(3,dtype=int)
    SetCoverOperators(A,C).repair(x,np.random.default_rng(1))
    assert x.sum()==0
