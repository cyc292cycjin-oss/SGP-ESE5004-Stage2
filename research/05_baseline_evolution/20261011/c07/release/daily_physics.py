from pathlib import Path
import numpy as np,pandas as pd,json,types,importlib.util,os,collections
from c02_common import sha
from fixed_resource_acceptance import RULE_ID,inventory,meter_checks,obligation
fixed_inventory_prefix_draft=inventory
def fsync_file(p):
    with open(p,'rb') as f:os.fsync(f.fileno())

def _base_engineering(n,scalar_values,original_objective,contract):
 require_contract(contract)
 from fixed_accounts import validate_fixed_accounts,validate_exported_accounting
 # Original scientific fields stay unchanged; author objective lives in a separate ledger.
 fixed=validate_fixed_accounts(n)
 validate_exported_accounting(n)
 fom_names=[k for k in scalar_values if k.startswith('Research-')]
 if len(fom_names)!=1 or abs(scalar_values[fom_names[0]]-1)>1e-10:raise ValueError('FOM fixed-column identity')
 expected_const=n.meta.get('existing_annual_fixed_om_eur');assert expected_const is not None
 def accounting_no_model(net,priced_objective=None,**kwargs):
  validate_exported_accounting(net)
  return {'PricedObjective':priced_objective,'KnownFixedCost':float(expected_const),'KnownFixedCostIncludedInPricedObjective':True,
   'FOMProof':'frozen single fixed column plus independent component objective reconciliation',
   'FullSystemCostComplete':False,'FullSystemEmissionsComplete':False,'PendingFixedCostTerms':fixed}
 source=Path(__file__).parent/'validation_dynamics.py'
 spec=importlib.util.spec_from_file_location('frozen_dynamic_checks',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 globals_=dict(module.dynamic_checks.__globals__,accounting_report=accounting_no_model)
 check_function=types.FunctionType(module.dynamic_checks.__code__,globals_)
 n.objective=float(original_objective)
 rows,details=check_function(n)
 h=n.snapshot_weightings.stores.to_numpy();prefix=[]
 for x in fixed:
  k=x['FixedAccountID'];p=n.stores_t.p[k].to_numpy();e=n.stores_t.e[k].to_numpy()
  record=fixed_inventory_prefix_draft(p,e,float(x['QuantityMWh']),h,approved=True)
  meter=n.links_t.p0[x['Meter']].to_numpy();limit=1e-3+1e-7*np.maximum(np.abs(p),np.abs(meter))
  record['meter_equal_release']=bool(np.all(np.abs(meter-p)<=limit))
  record['passed']=record['passed'] and record['meter_equal_release'];record['asset']=k;prefix.append(record)
 # Explicit lower bounds on charge, discharge and spill (not just upper bounds).
 for attr in ('p_dispatch','p_store','spill'):
  v=n.storage_units_t[attr].to_numpy();rows.append({'Check':'SU_NONNEGATIVE_'+attr,'Status':'PASS' if np.isfinite(v).all() and np.all(v>=-(1e-3+1e-7*np.abs(v))) else 'FAIL'})
 details['fixed_prefix_checks']=prefix;details['source_sha256']=sha(source)
 return {'checks':rows,'details':details,'all_physics_pass':all(r['Status']=='PASS' for r in rows) and all(r['passed'] for r in prefix),
  'all_frozen_matrix_rows_still_required':True,'basis_required':False}

def frame_equal(left,right):
 if not left.index.equals(right.index) or set(left.columns)!=set(right.columns):return False
 right=right.reindex(columns=left.columns) # NetCDF schema may reorder attributes, never assets.
 for col in left:
  a,b=left[col],right[col]
  if pd.api.types.is_numeric_dtype(a):
   if not np.array_equal(a.to_numpy(),b.to_numpy(),equal_nan=True):return False
  elif not a.fillna('').astype(str).equals(b.fillna('').astype(str)):return False
 return True

def netcdf_roundtrip(n,path,qualification):
 import pypsa
 path=Path(path)
 n.meta['author_method_result']={'qualification':qualification,'basis_required':False,'scientific_cost_fields':'ORIGINAL_UNMODIFIED','original_objective_optimality':'NOT_PROVEN'}
 n.export_to_netcdf(path)
 fsync_file(path);back=pypsa.Network(path)
 if not n.snapshots.equals(back.snapshots) or n.meta!=back.meta:raise ValueError('NetCDF snapshot/metadata mismatch')
 count=0;restored_defaults=[]
 for c in ('Bus','Generator','Load','Link','Line','Store','StorageUnit','GlobalConstraint','Transformer'):
  if not frame_equal(n.df(c),back.df(c)):raise ValueError('NetCDF static mismatch '+c)
  for key,frame in n.pnl(c).items():
   if not frame.empty:
    got=back.pnl(c)[key]
    missing=frame.columns.difference(got.columns)
    if len(missing):
     default=n.component_attrs[c].at[key,'default']
     original=frame[missing].to_numpy()
     if not np.isscalar(default) or not np.isfinite(default) or not np.all(original==default):raise ValueError('NetCDF nondefault values missing '+c+':'+key)
     got=got.reindex(index=frame.index,columns=frame.columns,fill_value=default)
     back.pnl(c)[key]=got;restored_defaults.append({'component':c,'attribute':key,'columns':len(missing),'declared_default':float(default)})
    if not frame_equal(frame,got):raise ValueError('NetCDF dynamic mismatch '+c+':'+key)
    count+=1
 return back,{'status':'EXACT_SEMANTIC_ROUNDTRIP','sha256':sha(path),'dynamic_tables':count,'qualification':qualification,'pypsa_omitted_declared_default_columns_restored':restored_defaults}
def require_contract(c):
 for key in ('approved_by_user','physical_budget_approved','perturbation_scope_approved','basis_free_kkt_approved'):
  if c.get(key) is not True:raise ValueError('Final scientific contract not explicitly approved')
 if c.get('contract_id')!='AUTHOR_SCIENTIFIC_ACCEPTANCE_V4' or c.get('fixed_resource_rule_id')!=RULE_ID:raise ValueError('wrong contract')
 expected={'physical_absolute_floor_in_each_equation_native_unit':1e-3,'physical_relative_budget':1e-7,'kkt_normalized_budget':1e-6}
 if any(c.get(k)!=v for k,v in expected.items()):raise ValueError('unimplemented numerical budget')

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
