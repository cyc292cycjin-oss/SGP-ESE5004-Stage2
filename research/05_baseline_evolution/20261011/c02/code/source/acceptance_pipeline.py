"""Basis-free post-return checks. Reuses prior algebra and frozen engineering equations."""
from common import *
import os,math,types,importlib.util
import numpy as np,pandas as pd
from adapter import save_returned,save_original_vectors,ranges
from basis_free import diagnose,acceptance_draft
from result_bridge import restore_tables,mathematical_gap_decision
from author_objective import reconcile_objectives
from physical_draft import fixed_inventory_prefix_draft
from execution_safety import atomic_json as _atomic_json

def atomic_json(path,value):
 def convert(obj):
  if isinstance(obj,np.generic):return obj.item()
  raise TypeError('unsupported receipt value '+type(obj).__name__)
 normalized=json.loads(json.dumps(value,default=convert,allow_nan=False))
 _atomic_json(path,normalized)

def bounded_columns(a,n,columns=20000,max_nnz=4_000_000):
 s=0
 while s<n:
  e=min(n,s+columns)
  if int(a['start'][e])-int(a['start'][s])>max_nnz:
   e=min(e,int(np.searchsorted(a['start'],int(a['start'][s])+max_nnz,side='right'))-1)
   if e<=s:raise ValueError('single column exceeds scratch budget')
  yield s,e;s=e

def require_contract(contract):
 required={'approved_by_user','physical_budget_approved','perturbation_scope_approved','basis_free_kkt_approved'}
 if any(contract.get(k) is not True for k in required):raise ValueError('Pending scientific decisions; acceptance disabled')
 if contract.get('contract_id')!='AUTHOR_PREFLIGHT_PHYSICS_V3':raise ValueError('unknown contract')

def fsync_file(p):
 with open(p,'rb') as f:os.fsync(f.fileno())

def durable_raw(backend,meta,root,native_returned):
 if not native_returned:raise ValueError('No reads from an active native solve')
 root=Path(root);root.mkdir(exist_ok=False,parents=True)
 atomic_json(root/'NATIVE_RETURN.json',{'native_status':backend.scalar('Status',int),'qualification':'UNQUALIFIED','native_returned':True})
 try:
  receipt=save_returned(backend,meta,root/'vectors',native_returned=True)
  for p in (root/'vectors').iterdir():
   if p.is_file():fsync_file(p)
  atomic_json(root/'RAW_DURABLE.json',{'receipt_sha256':sha(root/'vectors/RAW_RECEIPT.json'),'qualification':'UNQUALIFIED','complete':all(receipt['vectors'].get(a,{}).get('status')=='SAVED_UNQUALIFIED' for a in ('X','Pi','RC'))})
  return receipt
 except Exception as exc:
  try:atomic_json(root/'RAW_CAPTURE_ERROR.json',{'error':type(exc).__name__,'qualification':'NOT_AVAILABLE_OR_INCOMPLETE','retry_solve':False})
  except OSError:pass # A failed disk cannot be repaired by inventing a saved receipt.
  raise

def budget_arrays(meta,a,z,D,R,directory,contract):
 require_contract(contract)
 directory=Path(directory);directory.mkdir(exist_ok=False,parents=True)
 n,m=meta['num_col'],meta['num_row']
 magnitude=np.lib.format.open_memmap(directory/'row_magnitude.npy',mode='w+',dtype='<f8',shape=(m,));magnitude[:]=0
 for s,e in bounded_columns(a,n):
  p,q=int(a['start'][s]),int(a['start'][e]);np.add.at(magnitude,a['index'][p:q],np.abs(a['value'][p:q]*np.repeat(z[s:e],np.diff(a['start'][s:e+1]))))
 rt=np.lib.format.open_memmap(directory/'row_tolerance.npy',mode='w+',dtype='<f8',shape=(m,))
 ct=np.lib.format.open_memmap(directory/'col_tolerance.npy',mode='w+',dtype='<f8',shape=(n,))
 for s,e in ranges(m):
  l=a['row_lower'][s:e]/R[s:e];u=a['row_upper'][s:e]/R[s:e]
  reference=np.maximum(np.where(np.isfinite(l),np.abs(l),0),np.where(np.isfinite(u),np.abs(u),0))
  rt[s:e]=1e-3+1e-7*np.maximum(reference,magnitude[s:e]/R[s:e])
 for s,e in ranges(n):
  l=a['col_lower'][s:e]*D[s:e];u=a['col_upper'][s:e]*D[s:e]
  ct[s:e]=1e-3+1e-7*np.maximum(np.abs(z[s:e]*D[s:e]),np.maximum(np.where(np.isfinite(l),np.abs(l),0),np.where(np.isfinite(u),np.abs(u),0)))
 rt.flush();ct.flush();magnitude.flush();return rt,ct

def complete_kkt(meta,a,z,pi,rc,D,R,directory,contract):
 rt,ct=budget_arrays(meta,a,z,D,R,Path(directory)/'budgets',contract)
 def adaptive_ranges(length,chunk=None):
  return bounded_columns(a,length) if length==meta['num_col'] and chunk==20000 else ranges(length,chunk)
 # Preserve the verified formulas; replace only fixed-width batching that can exceed
 # scratch memory for dense capacity columns in the actual frozen CSC.
 bounded_diagnose=types.FunctionType(diagnose.__code__,dict(diagnose.__globals__,ranges=adaptive_ranges))
 out=bounded_diagnose(meta,a,z,pi,rc,D,R,Path(directory)/'algebra',rt,ct,0.,1e-6)
 # Existing algebra reports raw sign error. Add an explicit normalized sign gate,
 # including forbidden multipliers on free columns and nonexistent endpoints.
 maxerr=0.;count=0
 for length,mult,scale,lo,hi in [(meta['num_col'],rc,D,a['col_lower'],a['col_upper']),(meta['num_row'],pi,R,a['row_lower'],a['row_upper'])]:
  iscol=mult is rc
  for s,e in ranges(length):
   v=mult[s:e]/scale[s:e] if iscol else mult[s:e]*scale[s:e]
   error=np.where(~np.isfinite(lo[s:e]),np.maximum(v,0),0)+np.where(~np.isfinite(hi[s:e]),np.maximum(-v,0),0)
   norm=error/np.maximum(1,np.abs(v));maxerr=max(maxerr,float(norm.max(initial=0)));count+=int(np.count_nonzero(norm>1e-6))
 out.update(dual_sign_normalized_max=maxerr,dual_sign_fail_count=count)
 decision=mathematical_gap_decision(out)
 out['independent_kkt_pass']=bool(decision['numeric_draft_pass'] and not count and out['row_fail_count']==out['column_fail_count']==out['stationarity_fail_count']==0)
 return out

def engineering_checks(n,scalar_values,original_objective,contract):
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
 source=ROOT/'work/gate6_refinement_restart_20261009/source/scripts_project/validation_dynamics.py'
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

def postprocess_raw(raw,meta,arrays,mapping_dir,frozen_network,original_cost,original_offset,output,contract,transfer_receipt):
 """Callable only after raw persistence. No native model or solve exists in this path."""
 import pypsa
 require_contract(contract)
 if transfer_receipt.get('status')!='EXACT_READBACK_PASS':raise ValueError('native transfer not verified')
 output=Path(output);output.mkdir(exist_ok=False)
 raw=Path(raw);receipt=json.loads((raw/'vectors/RAW_RECEIPT.json').read_text())
 save_original_vectors(raw/'vectors',mapping_dir,output/'original_vectors')
 z,pi,rc=[np.load(raw/'vectors'/(k+'.npy'),mmap_mode='r') for k in ('X','Pi','RC')]
 D=np.load(Path(mapping_dir)/'D.npy',mmap_mode='r');R=np.load(Path(mapping_dir)/'R.npy',mmap_mode='r')
 kkt=complete_kkt(meta,arrays,z,pi,rc,D,R,output/'kkt',contract)
 costs=reconcile_objectives(original_cost,arrays['cost'],z,original_offset,meta['offset'])
 n=pypsa.Network(frozen_network);mm=json.loads((Path(mapping_dir)/'MAPPING_MANIFEST.json').read_text())
 scalars=restore_tables(n,mm,np.load(Path(mapping_dir)/'vlabels.npy',mmap_mode='r'),np.load(output/'original_vectors/X_original.npy',mmap_mode='r'))
 physics=engineering_checks(n,scalars,costs['original_scientific_objective_known_scope'],contract)
 back,export=netcdf_roundtrip(n,output/'candidate_UNQUALIFIED.nc','UNQUALIFIED_PENDING_ALL_GATES')
 physics_after=engineering_checks(back,scalars,costs['original_scientific_objective_known_scope'],contract)
 gates={'transfer':True,'complete_primal_dual':True,'all_rows_original_units':kkt['row_fail_count']==kkt['column_fail_count']==0,
  'physical_dynamics':physics['all_physics_pass'] and physics_after['all_physics_pass'],'fixed_inventory_original_bounds':all(r['passed'] for r in physics['details']['fixed_prefix_checks']),
  'all_prefixes_and_annual':all(r['passed'] for r in physics['details']['fixed_prefix_checks']),'objective_fom_once':any(r['Check']=='OBJECTIVE_RECONCILIATION_KNOWN_FOM_ONCE' and r['Status']=='PASS' for r in physics['checks']),
  'dual_kkt_gap':kkt['independent_kkt_pass'],'export_reload':True,'durable_sha_backup':False,'approved_contract':True}
 result={'native_status':receipt['native_status'],'costs':costs,'kkt':kkt,'engineering':physics,'export':export,'gates':gates,'acceptance':acceptance_draft(receipt['native_status'],gates),'next':'Complete verified backup before final qualification'}
 atomic_json(output/'POSTPROCESS_RECEIPT.json',result);return result

def finalize_verified_acceptance(postprocess_receipt,backup_directory,native_status):
 """Recompute transferred-file hashes before closing the final gate; never Gate6 PASS."""
 backup=Path(backup_directory);index=json.loads((backup/'BACKUP_INDEX.json').read_text())
 for row in index['files']:
  target=(backup/row['relative']).resolve()
  if not target.is_relative_to(backup.resolve()) or sha(target)!=row['sha256']:raise ValueError('backup bytes mismatch')
 for row in index['reused_by_reference']:
  if sha(row['path'])!=row['sha256']:raise ValueError('referenced original mismatch')
 source=Path(postprocess_receipt)
 if not any(row['sha256']==sha(source) for row in index['files']):raise ValueError('postprocess receipt absent from verified backup')
 result=json.loads(source.read_text())
 if native_status!=result['native_status']:raise ValueError('native final status mismatch')
 gates=dict(result['gates'],durable_sha_backup=True)
 decision=acceptance_draft(native_status,gates)
 accepted=decision['status']=='DRAFT_ACCEPTANCE_CHECKS_SATISFIED'
 return {'status':'AUTHOR_METHOD_NUMERICALLY_CERTIFIED_KNOWN_COST_SCOPE' if accepted else 'NOT_ACCEPTED',
  'details':decision,'original_objective_optimality':'NOT_PROVEN','historical_gate6_pass':False,'basis_required':False}
