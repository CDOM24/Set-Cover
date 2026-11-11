"""AG de SET COVER: operadores explicitos, reparacion y poda. Sin acceso a HiGHS."""
from dataclasses import asdict, dataclass
import math
from time import perf_counter
import numpy as np
from .data_io import DataError
from .validation import validate_arrays
from .verification import verify_solution

@dataclass(frozen=True)
class GAConfig:
    population_size: int = 80
    generations: int = 300
    crossover_probability: float = 0.85
    mutation_probability: float = 0.004
    elite_count: int = 4
    tournament_size: int = 3
    stagnation_generations: int = 100
    time_limit: float = 60.0
    greedy_fraction: float = 0.5
    initial_probability: float = 0.03
    repair_candidates: int = 3

    def validate(self):
        for field in ['population_size','generations','elite_count','tournament_size','stagnation_generations','repair_candidates']:
            value=getattr(self,field)
            if isinstance(value,bool) or not isinstance(value,int):
                raise DataError(field+': se requiere entero.')
        if self.population_size < 2 or self.generations < 0 or not 1 <= self.elite_count < self.population_size:
            raise DataError('Poblacion >=2, generaciones >=0 y 1<=elitismo<poblacion requeridos.')
        if not 1 <= self.tournament_size <= self.population_size or self.stagnation_generations < 0 or self.repair_candidates < 1:
            raise DataError('Torneo, estancamiento o candidatos de reparacion invalidos.')
        for field in ['crossover_probability','mutation_probability','greedy_fraction','initial_probability']:
            value=getattr(self,field)
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise DataError(field+': probabilidad debe estar entre 0 y 1.')
        if not math.isfinite(self.time_limit) or self.time_limit <= 0:
            raise DataError('El limite de tiempo debe ser positivo y finito.')


def chromosome(selection,n):
    x=np.asarray(selection)
    if x.shape != (n,) or not np.isin(x,[0,1]).all():
        raise DataError('Cromosoma binario de longitud igual al numero de antenas requerido.')
    return x.astype(np.int64,copy=True)


def mutate(selection,probability,rng):
    if not math.isfinite(probability) or not 0 <= probability <= 1:
        raise DataError('Probabilidad de mutacion invalida.')
    x=chromosome(selection,len(selection))
    return np.bitwise_xor(x,(rng.random(len(x)) < probability).astype(np.int64))


def uniform_crossover(parent_a,parent_b,probability,rng):
    if not math.isfinite(probability) or not 0 <= probability <= 1:
        raise DataError('Probabilidad de cruce invalida.')
    a,b=chromosome(parent_a,len(parent_a)),chromosome(parent_b,len(parent_a))
    if rng.random() >= probability:
        return a,b
    mask=rng.random(len(a)) < 0.5
    return np.where(mask,a,b),np.where(mask,b,a)


def tournament(population,scores,size,rng):
    if size < 1 or len(population) != len(scores):
        raise DataError('Torneo invalido.')
    indices=rng.integers(0,len(population),size=size)
    winner=indices[np.argmin(np.asarray(scores)[indices])]
    return population[winner].copy()


class SetCoverOperators:
    def __init__(self,matrix,costs):
        self.a=validate_arrays(matrix,costs)
        self.c=np.asarray(costs,dtype=float).copy()
        self.m,self.n=self.a.shape
        if not (self.a.sum(axis=1)>0).all():
            raise DataError('Instancia inviable: existen clientes sin ninguna cobertura.')
        if not math.isfinite(float(self.c.sum()+1)):
            raise DataError('Suma de costos demasiado grande para una penalizacion finita.')
        self.penalty=float(self.c.sum()+1)
        self.covered=[np.flatnonzero(self.a[:,j]) for j in range(self.n)]

    def counts(self,x):
        chosen=np.flatnonzero(x)
        return self.a[:,chosen].sum(axis=1) if len(chosen) else np.zeros(self.m,dtype=np.int64)

    def evaluate(self,selection):
        x=chromosome(selection,self.n)
        missing=int((self.counts(x)==0).sum())
        cost=float(self.c@x)
        return {'costo':cost,'clientes_sin_cubrir':missing,'factible':missing==0,
                'fitness_minimizar':cost+self.penalty*missing}

    def prune(self,selection,rng):
        x=chromosome(selection,self.n)
        counts=self.counts(x)
        if not (counts>=1).all():
            raise DataError('La poda requiere una seleccion factible.')
        selected=np.flatnonzero(x)
        # Costos descendentes; desempate aleatorio reproducible.
        order=selected[np.lexsort((rng.random(len(selected)),-self.c[selected]))]
        for j in order:
            clients=self.covered[j]
            if (counts[clients]>=2).all():
                x[j]=0
                counts[clients]-=1
        return x

    def repair(self,selection,rng,candidates=3):
        if candidates < 1:
            raise DataError('Se necesita al menos un candidato de reparacion.')
        x=chromosome(selection,self.n)
        counts=self.counts(x)
        while (counts==0).any():
            gains=self.a[counts==0].sum(axis=0)
            valid=np.flatnonzero((gains>0)&(x==0))
            if not len(valid):
                raise DataError('No es posible reparar la cobertura.')
            free=valid[self.c[valid]==0]
            if len(free):
                # Antenas gratuitas primero, mayor ganancia preferida.
                pool=free[np.argsort(-gains[free],kind='stable')[:candidates]]
            else:
                ratios=self.c[valid]/gains[valid]
                pool=valid[np.argsort(ratios,kind='stable')[:candidates]]
            j=int(rng.choice(pool))
            x[j]=1
            counts[self.covered[j]]+=1
        return self.prune(x,rng)


def run_genetic(matrix,costs,seed=11,config=None):
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
    return {'schema_version':1,'metodo':'AG_con_reparacion_y_poda','semilla':seed,
            'parametros':asdict(config),'seleccion':best.tolist(),'costo_total':best_cost,
            'numero_antenas':verified['antenas_seleccionadas'],'clientes_cubiertos':verified['clientes_cubiertos'],
            'factible_verificada':True,'optimalidad_demostrada':False,'motivo_parada':stopped,
            'generaciones':history[-1]['generacion'],'generaciones_completas':completed,
            'tiempo_ag_segundos':perf_counter()-started,'tiempo_inicializacion_segundos':initialization_time,
            'tiempo_mejor_solucion_segundos':best_time,'mejor_costo_inicial':initial_best,
            'mejora_desde_inicializacion':initial_best-best_cost,'historial':history,'verificacion':verified,
            'origen_inicializacion':'voraz aleatoria + Bernoulli reparada; sin seleccion ni resultados HiGHS'}
