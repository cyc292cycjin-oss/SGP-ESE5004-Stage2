"""Read only static NetCDF attributes/selected small vectors; never imports PyPSA or solvers."""
from pathlib import Path
import json,hashlib,csv,math
import numpy as np
from netCDF4 import Dataset
D=Path('/mnt/d/ResearchWorkspaces/ASEAN');R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');O=D/'work/a06_policy_cost_resource_audit_20261012'
def norm(v):
 if isinstance(v,dict):return {str(k):norm(x) for k,x in v.items()}
 if isinstance(v,(list,tuple,np.ndarray)):return [norm(x) for x in v]
 if isinstance(v,np.generic):return norm(v.item())
 if isinstance(v,float) and not math.isfinite(v):return str(v)
 return v
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
idx=json.loads((D/'research/00_source_provenance/RESULTS_MEMBER_HASHES.json').read_text())
models=[('author2025',D/'research/00_source_provenance'/r['path'].replace('\\','/'),r['sha256']) for r in idx if '_2025_' in r['path']]+[('author2050',D/'research/00_source_provenance'/r['path'].replace('\\','/'),r['sha256']) for r in idx if '_2050_' in r['path']]+[('frozen2050',D/'outputs/phase4_gate4_final_closure_20261006/complete_network/research_fullsc_2050_assembly_v1_unsolved.nc','238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d')]
out={'method':'Read-only netCDF4; no dynamic dispatch, full CSC or raw solution vectors read. Big-file identity reuses verified A05 hash index, not a new full-file hash scan.','models':{}}
ids25={}
for name,p,expected in models:
 with Dataset(p,'r') as ds:
  def arr(key):return norm(ds.variables[key][:].tolist())
  def rows(comp):
   keys=[k for k in ds.variables if k.startswith(comp+'_') and ds.variables[k].ndim==1 and ds.variables[k].dimensions==(comp+'_i',)]
   keys=[k for k in keys if k!=comp+'_i']
   data={k:arr(k) for k in keys}
   return [{**{'id':str(id)},**{k[len(comp)+1:]:data[k][i] for k in keys}} for i,id in enumerate(arr(comp+'_i'))]
  glob=rows('global_constraints')
  weights={k:{'count':len(arr(k)),'sum':float(np.sum(ds.variables[k][:])),'min':float(np.min(ds.variables[k][:])),'max':float(np.max(ds.variables[k][:]))} for k in ['snapshots_objective','snapshots_generators','snapshots_stores'] if k in ds.variables}
  costs={};extra=[]
  for comp in ['generators','links','lines','stores','storage_units']:
   data=rows(comp);cs={}
   if name=='author2025' and comp in ['links','lines']:ids25[comp]={r['id'] for r in data}
   for r in data:
    car=r.get('carrier','AC' if comp=='lines' else 'DEFAULT_UNSET')
    cs.setdefault(car,[]).append(r)
    if name=='author2050' and comp in ['links','lines'] and r['id'] not in ids25[comp] and (comp=='lines' or car in ['DC','B2B']):extra.append({'component':comp,**r})
   costs[comp]={car:{'count':len(rs),**{f:{'min':min(float(r[f]) for r in rs if r.get(f) is not None),'max':max(float(r[f]) for r in rs if r.get(f) is not None),'nonzero':sum(float(r.get(f,0))!=0 for r in rs),'stored_count':sum(f in r for r in rs)} for f in ['capital_cost','marginal_cost','efficiency'] if any(r.get(f) is not None for r in rs)}} for car,rs in cs.items()}
  meta=json.loads(ds.getncattr('meta')) if 'meta' in ds.ncattrs() else {}
  safe={k:v for k,v in meta.items() if k in ['policy_enabled','policy_cap_actually_enabled','no_cap_assembly_v1','existing_annual_fixed_om_eur','FullSystemCostComplete','FullSystemEmissionsComplete','external_pending_fixed_accounts','price_basis','accounting_qualification','reporting_contract','carbon_policy','source_years']}
  out['models'][name]={'path':str(p),'bytes':p.stat().st_size,'sha256_from_reused_verified_index':expected,'global_constraints':glob,'weights':weights,'cost_summary_stored_fields_only':costs,'safe_meta':safe,'author2050_additional_electric_assets':extra,'carriers':rows('carriers')}
  if extra:print('EXTRA',json.dumps([{k:r[k] for k in ['component','id','build_year','p_nom','p_nom_opt','s_nom','s_nom_opt','p_nom_extendable','s_nom_extendable'] if k in r} for r in extra]))
out=norm(out);(O/'NETWORK_STATIC_READOUT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
for label,rel in [('v3','work/final_local_closeout_20261010/AUTHOR_METHOD_ADAPTED_SCOPE_V3/OBJECTIVE_DERIVATION.json'),('scope','work/final_local_closeout_20261010/AUTHOR_METHOD_ADAPTED_SCOPE_V3/SCOPE_V3_LOCAL_AUDIT.json')]:
 j=json.loads((D/rel).read_text());print(label,json.dumps({k:v for k,v in j.items() if k not in ['math_arrays_reused_by_reference','blocks','exceptions','component_summary']},ensure_ascii=False)[:12000])
with (D/'work/final_local_closeout_20261010/AUTHOR_METHOD_ADAPTED_SCOPE_V3/EFFECTIVE_PERTURBATION_LEDGER.csv').open() as f:
 reader=csv.DictReader(f);print('LEDGER HEAD',reader.fieldnames);print('LEDGER FIRST',next(reader))
