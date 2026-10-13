"""Candidate resource budgets; pure post-return arithmetic, never changes a model."""
import math
import numpy as np

RULE_ID='FIXED_RESOURCE_1PPM_CAP_AND_GROSS_LEAKAGE_V1'

def energy_budget(q):
 q=float(q)
 if not math.isfinite(q) or q<0:raise ValueError('invalid frozen annual quantity')
 return min(1e-3+1e-7*q,1e-6*q) if q else 0.

def prefixes(x):
 total=corr=0.;out=[]
 for value in x:
  y=float(value)-corr;t=total+y;corr=(t-total)-y;total=t;out.append(t)
 return np.array(out)

def absolute_energy(x):return math.fsum(abs(float(v)) for v in x)

def inventory(power,energy,initial,hours,approved=False):
 if not approved:raise ValueError('reviewed contract required')
 p,e,h=map(lambda x:np.asarray(x,dtype=float),(power,energy,hours));q=float(initial)
 if p.ndim!=1 or not len(p) or p.shape!=e.shape or p.shape!=h.shape:raise ValueError('incomplete coverage')
 if not all(np.isfinite(v).all() for v in (p,e,h)) or np.any(h<=0):raise ValueError('nonfinite/invalid hours')
 b=energy_budget(q);release=p*h;acc=prefixes(release);res=e+acc-q
 step=e-np.r_[q,e[:-1]]+release;annual=math.fsum(release.tolist());negative=math.fsum(np.maximum(-release,0).tolist())
 checks={'all_prefixes':bool(np.all(abs(res)<=b)),'all_steps':bool(np.all(abs(step)<=b)),
  'gross_state_error':absolute_energy(step)<=b,'annual':abs(annual-q)<=b,'terminal':abs(e[-1])<=b,
  'stock_lower':bool(np.all(e>=-b)),'stock_upper':bool(np.all(e<=q+b)),
  'release_direction':negative<=b,'cumulative_resource_cap':bool(np.all(acc<=q+b)),
  'zero_Q_exact_zero':bool(q!=0 or (np.all(p==0) and np.all(e==0)))}
 return {'rule_id':RULE_ID,'draft_checks':checks,'passed':all(checks.values()),'prefix_count':len(p),
  'energy_budget_mwh':b,'budget_fraction_of_Q':b/q if q else None,
  'max_prefix_error_mwh':float(abs(res).max()),'gross_state_error_mwh':absolute_energy(step),
  'annual_release_mwh':annual,'gross_negative_release_mwh':negative,'full_acceptance':False}

def meter_checks(power,meter,hours,capacity,pmax,q):
 p,m,h=map(lambda x:np.asarray(x,dtype=float),(power,meter,hours));b=energy_budget(q)
 if not all(np.isfinite(v).all() for v in (p,m,h)):raise ValueError('nonfinite meter')
 if not math.isfinite(capacity) or capacity<0 or not np.isfinite(pmax).all():raise ValueError('invalid returned capacity')
 errors=(m-p)*h;overflow=np.maximum(m-float(capacity)*pmax,0)*h
 return {'meter_equal_release':absolute_energy(errors)<=b,'meter_direction':math.fsum(np.maximum(-m*h,0).tolist())<=b,
  'meter_capacity':math.fsum(overflow.tolist())<=b,'zero_Q_meter_zero':bool(q!=0 or np.all(m==0)),
  'meter_difference_l1_mwh':absolute_energy(errors),'meter_capacity_excess_mwh':math.fsum(overflow.tolist())}

def obligation(supply,demand,hours,quantities):
 """Shared destination: no per-account schedule imposed; gross errors cannot cancel."""
 supply,demand,h=map(lambda x:np.asarray(x,dtype=float),(supply,demand,hours))
 if supply.shape!=demand.shape or demand.shape!=h.shape or not all(np.isfinite(v).all() for v in (supply,demand,h)):raise ValueError('group coverage/nonfinite')
 budgets=[energy_budget(q) for q in quantities];b=math.fsum(budgets);diff=(supply-demand)*h
 over=math.fsum(np.maximum(diff,0).tolist());under=math.fsum(np.maximum(-diff,0).tolist())
 per_step=np.minimum(b,1e-3+1e-7*np.abs(demand*h))
 checks={'each_period':bool(np.all(abs(diff)<=per_step)),'gross_oversupply':over<=b,'gross_undersupply':under<=b,
  'all_delivery_prefixes':bool(np.all(abs(prefixes(diff))<=b)),'zero_total_Q_exact_supply_zero':bool(sum(quantities)!=0 or np.all(supply==0))}
 return {'checks':checks,'passed':all(checks.values()),'group_budget_mwh':b,'gross_oversupply_mwh':over,'gross_undersupply_mwh':under,
  'max_delivery_prefix_error_mwh':float(abs(prefixes(diff)).max()),'periods':len(h),
  'zero_demand_periods':int(np.count_nonzero(demand==0)),'source_demand_integral_mwh':math.fsum((demand*h).tolist()),
  'source_integral_minus_stocks_mwh':math.fsum((demand*h).tolist())-math.fsum(quantities),
  'source_roundoff_added_to_solver_budget':False}
