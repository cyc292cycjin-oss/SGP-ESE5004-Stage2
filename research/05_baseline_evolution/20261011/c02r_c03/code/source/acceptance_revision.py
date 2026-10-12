"""Narrow V4 binding: preserve verified algebra/export; tighten only fixed resources."""
from pathlib import Path
import sys,types,collections
PACK=Path(__file__).resolve().parent
sys.path.insert(0,str(PACK.parent/'author_method_preflight_20261010'))
import acceptance_pipeline as prior
from fixed_resource_acceptance import RULE_ID,inventory,meter_checks,obligation

def require_contract(c):
 for key in ('approved_by_user','physical_budget_approved','perturbation_scope_approved','basis_free_kkt_approved'):
  if c.get(key) is not True:raise ValueError('Final scientific contract not explicitly approved')
 if c.get('contract_id')!='AUTHOR_SCIENTIFIC_ACCEPTANCE_V4' or c.get('fixed_resource_rule_id')!=RULE_ID:raise ValueError('wrong contract')
 expected={'physical_absolute_floor_in_each_equation_native_unit':1e-3,'physical_relative_budget':1e-7,'kkt_normalized_budget':1e-6}
 if any(c.get(k)!=v for k,v in expected.items()):raise ValueError('unimplemented numerical budget')

def bind(f,**g):return types.FunctionType(f.__code__,dict(f.__globals__,**g),f.__name__,f.__defaults__,f.__closure__)
budget_arrays=bind(prior.budget_arrays,require_contract=require_contract)
complete_kkt=bind(prior.complete_kkt,budget_arrays=budget_arrays)
_base_engineering=bind(prior.engineering_checks,require_contract=require_contract,fixed_inventory_prefix_draft=inventory)

def engineering_checks(n,scalars,original_objective,contract):
 result=_base_engineering(n,scalars,original_objective,contract)
 from fixed_accounts import validate_fixed_accounts
 accounts=validate_fixed_accounts(n);lookup={a['FixedAccountID']:a for a in accounts};h=n.snapshot_weightings.stores.to_numpy();groups=collections.defaultdict(list);pmax=n.get_switchable_as_dense('Link','p_max_pu')
 for record in result['details']['fixed_prefix_checks']:
  a=lookup[record['asset']];k=a['FixedAccountID'];q=float(a['QuantityMWh']);meter=a['Meter']
  if float(n.stores.at[k,'e_initial'])!=q or float(n.stores.at[k,'e_nom'])!=q:raise ValueError('fixed source bound changed')
  checks=meter_checks(n.stores_t.p[k].to_numpy(),n.links_t.p0[meter].to_numpy(),h,float(n.links.at[meter,'p_nom_opt']),pmax[meter].to_numpy(),q)
  record.update(checks);record['passed']=record['passed'] and all(checks[x] for x in ('meter_equal_release','meter_direction','meter_capacity','zero_Q_meter_zero'))
  groups[tuple(a['FinalBuses'])].append(a)
 demand=n.get_switchable_as_dense('Load','p_set');groupchecks=[]
 for buses,aa in groups.items():
  loads=n.loads.index[n.loads.bus.isin(buses)];supply=-n.links_t.p1[[a['Meter'] for a in aa]].sum(axis=1).to_numpy()
  check=obligation(supply,demand[loads].sum(axis=1).to_numpy(),h,[a['QuantityMWh'] for a in aa]);check['buses']=list(buses);groupchecks.append(check)
 result['details']['fixed_group_obligations_v4']=groupchecks
 result['all_physics_pass']=result['all_physics_pass'] and all(r['passed'] for r in result['details']['fixed_prefix_checks']) and all(r['passed'] for r in groupchecks)
 return result

postprocess_raw=bind(prior.postprocess_raw,require_contract=require_contract,complete_kkt=complete_kkt,engineering_checks=engineering_checks)

def run_future_authorized_worker(authorization_path):
 """Not a preparation entry point. Prior worker still requires separate solve authority."""
 import solve_worker
 solve_worker.require_contract=require_contract;solve_worker.postprocess_raw=postprocess_raw
 return solve_worker.run(authorization_path)
