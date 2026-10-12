"""Author noisy_costs equations; immutable asset registry; pure numeric functions.

No optimizer import/call. A numerical term never qualifies a missing scientific price.
"""
import hashlib,json,math
import numpy as np

AUTHOR_PARAMETERS={'Method':2,'Crossover':0,'BarConvTol':1e-6,'Threads':4,'Seed':123,'AggFill':0,'PreDual':0,'GURO_PAR_BARDENSETHRESH':200}

def author_draws(count,kind):
    seed=174 if kind=='marginal_cost' else 123
    if kind not in ('marginal_cost','capital_cost'):raise ValueError('unsupported perturbation')
    # Same legacy MT19937 stream as np.random.seed/random, without global side effects.
    u=np.random.RandomState(seed).random_sample(count)
    return (1e-2+2e-3*(u-0.5)) if kind=='marginal_cost' else (1e-1+2e-2*(u-0.5))

def stable_key(component,name):
    return json.dumps([component,str(name)],ensure_ascii=False,separators=(',',':'))

def registry_for(component,names,signatures):
    if len(set(map(str,names)))!=len(names):raise ValueError('duplicate asset')
    mc=author_draws(len(names),'marginal_cost');cap=author_draws(len(names),'capital_cost')
    return {stable_key(component,name):{'component':component,'asset':str(name),'frozen_ordinal':i,
      'marginal_draw':float(mc[i]),'capital_draw_per_km':float(cap[i]),'signature':signatures[i]}
      for i,name in enumerate(names)}

def lookup(registry,component,names,signatures):
    result=[]
    for name,sig in zip(names,signatures):
        key=stable_key(component,name)
        if key not in registry:raise ValueError('new asset requires registry revision: '+key)
        row=registry[key]
        if row['signature']!=sig:raise ValueError('asset identity/unit/orientation changed: '+key)
        result.append(row)
    if len(result)!=len(names) or len(names)!=len(signatures):raise ValueError('incomplete signatures')
    return result

def reconcile_objectives(original_cost,adapted_cost,z,original_offset,adapted_offset,chunk=200000):
    if len(original_cost)!=len(adapted_cost) or len(z)!=len(original_cost):raise ValueError('length')
    p0=[];pa=[];pd=[]
    for s in range(0,len(z),chunk):
        sl=slice(s,min(len(z),s+chunk));v=z[sl]
        if not np.isfinite(v).all():raise ValueError('nonfinite primal')
        p0.append(float(np.sum(original_cost[sl]*v)));pa.append(float(np.sum(adapted_cost[sl]*v)))
        pd.append(float(np.sum((adapted_cost[sl]-original_cost[sl])*v)))
    a=original_offset+math.fsum(p0);b=adapted_offset+math.fsum(pa);delta=adapted_offset-original_offset+math.fsum(pd)
    return {'original_scientific_objective_known_scope':a,'adapted_objective':b,'numerical_perturbation_contribution':delta,
            'reconciliation_residual':b-a-delta,'original_objective_optimality':'NOT_PROVEN','FullSystemCostComplete':False}
