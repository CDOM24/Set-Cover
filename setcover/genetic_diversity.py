"""Variante Fase 4: inmigrantes sin alterar el algoritmo original de Fase 3.
El ciclo base se conserva explicitamente y solo se inserta renovacion de no elites.
"""
from dataclasses import asdict
from time import perf_counter
import numpy as np
from .data_io import DataError
from .verification import verify_solution
from .genetic import GAConfig,SetCoverOperators,tournament,uniform_crossover,mutate

def run_with_immigrants(matrix,costs,seed=11,config=None,immigrant_fraction=0.10):
    if not 0 < immigrant_fraction < 1:
        raise DataError("Fraccion de inmigrantes debe estar entre 0 y 1.")
    config=config or GAConfig()
    config.validate()
    if isinstance(seed,bool) or not isinstance(seed,int) or seed < 0:
        raise DataError('La semilla debe ser un entero no negativo.')
    started=perf_counter()
    deadline=started+config.time_limit
    op=SetCoverOperators(matrix,costs)
    rng=np.random.default_rng(seed)
    population=[]
    greedy_count=int(config.population_size*config.greedy_fraction)
    for i in range(config.population_size):
        # Se produce al menos un individuo valido aun con un limite minimo.
        if population and perf_counter() >= deadline:
            break
        initial=np.zeros(op.n,dtype=np.int64) if i<greedy_count else (rng.random(op.n)<config.initial_probability).astype(np.int64)
        population.append(op.repair(initial,rng,config.repair_candidates))
    population=np.array(population)
    scores=np.array([op.evaluate(x)['fitness_minimizar'] for x in population])
    best=population[int(np.argmin(scores))].copy()
    best_cost=float(op.c@best)
    best_time=perf_counter()-started
    history=[]

    def record(generation,complete):
        evaluations=[op.evaluate(x) for x in population]
        if not all(e['factible'] for e in evaluations):
            raise DataError('Una poblacion reparada contiene individuos infactibles.')
        history.append({'generacion':generation,'mejor_costo':best_cost,
                        'costo_medio':float(np.mean([e['costo'] for e in evaluations])),
                        'diversidad_proporcion':len(np.unique(population,axis=0))/len(population),
                        'clientes_cubiertos_minimo':op.m,'poblacion_real':len(population),
                        'generacion_completa':bool(complete),'tiempo_segundos':perf_counter()-started})

    record(0,len(population)==config.population_size)
    initialization_time=perf_counter()-started
    initial_best=best_cost
    stopped='generaciones'
    stagnation=0
    completed=0
    for generation in range(1,config.generations+1):
        if perf_counter()>=deadline:
            stopped='tiempo'
            break
        previous_best=best_cost
        elite_size=min(config.elite_count,len(population))
        new=[population[j].copy() for j in np.argsort(scores,kind='stable')[:elite_size]]
        timed_out=False
        immigrants=min(config.population_size-elite_size,max(1,round(immigrant_fraction*config.population_size)))
        for k in range(immigrants):
            if perf_counter()>=deadline:
                timed_out=True
                break
            fresh=np.zeros(op.n,dtype=np.int64) if k%2==0 else (rng.random(op.n)<config.initial_probability).astype(np.int64)
            fresh=op.repair(fresh,rng,config.repair_candidates)
            new.append(fresh)
            value=float(op.c@fresh)
            if value<best_cost:
                best,best_cost=fresh.copy(),value
                best_time=perf_counter()-started
        while len(new)<config.population_size:
            if perf_counter()>=deadline:
                timed_out=True
                break
            p=tournament(population,scores,config.tournament_size,rng)
            q=tournament(population,scores,config.tournament_size,rng)
            for child in uniform_crossover(p,q,config.crossover_probability,rng):
                if len(new)>=config.population_size:
                    break
                if perf_counter()>=deadline:
                    timed_out=True
                    break
                child=op.repair(mutate(child,config.mutation_probability,rng),rng,config.repair_candidates)
                new.append(child)
                value=float(op.c@child)
                if value<best_cost:
                    best,best_cost=child.copy(),value
                    best_time=perf_counter()-started
            if timed_out:
                break
        population=np.array(new)
        scores=np.array([op.evaluate(x)['fitness_minimizar'] for x in population])
        complete=len(population)==config.population_size
        if complete:
            completed+=1
        record(generation,complete)
        stagnation=0 if best_cost<previous_best else stagnation+1
        if timed_out or perf_counter()>=deadline:
            stopped='tiempo'
            break
        if config.stagnation_generations and stagnation>=config.stagnation_generations:
            stopped='estancamiento'
            break
    if config.generations==0 and perf_counter()>=deadline:
        stopped='tiempo'
    verified=verify_solution(op.a,op.c,best,best_cost)
    if not verified['valida']:
        raise DataError('El mejor individuo no paso el verificador independiente.')
    return {'schema_version':1,'metodo':'AG_con_inmigrantes_reparacion_y_poda','parametros_diversidad':{'fraccion':immigrant_fraction,'inmigrantes_por_generacion':min(config.population_size-config.elite_count,max(1,round(immigrant_fraction*config.population_size)))},'semilla':seed,
            'parametros':asdict(config),'seleccion':best.tolist(),'costo_total':best_cost,
            'numero_antenas':verified['antenas_seleccionadas'],'clientes_cubiertos':verified['clientes_cubiertos'],
            'factible_verificada':True,'optimalidad_demostrada':False,'motivo_parada':stopped,
            'generaciones':history[-1]['generacion'],'generaciones_completas':completed,
            'tiempo_ag_segundos':perf_counter()-started,'tiempo_inicializacion_segundos':initialization_time,
            'tiempo_mejor_solucion_segundos':best_time,'mejor_costo_inicial':initial_best,
            'mejora_desde_inicializacion':initial_best-best_cost,'historial':history,'verificacion':verified,
            'origen_inicializacion':'voraz aleatoria + Bernoulli reparada; sin seleccion ni resultados HiGHS'}
