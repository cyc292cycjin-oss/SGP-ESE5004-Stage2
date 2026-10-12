"""Read-only daily representation preflight. No PyPSA or solver import.

Only original NetCDF/NPZ and pinned small Git evidence are read. Daily float64
values exist transiently for SHA/round-trip simulation; no derived input is saved.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
from functools import lru_cache
import json,hashlib,math,struct,subprocess,time,datetime,zipfile,resource
import numpy as np
import netCDF4
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
D=Path('/mnt/d/ResearchWorkspaces/ASEAN');BASE=R/'research/05_baseline_evolution/20261011'
OUT=BASE/'c01';E=OUT/'evidence';E.mkdir(parents=True,exist_ok=True)
S='8883de6fb3e15767c632ac92f535e8a423e90b69';P='research_inputs/derived/exact_source_closure_a_max_account_v1_20261011/'
C00='5d757c5a4a9dad965d9c7cbe6e55d486d167ff93';SCI='b9be7d0ab788a4151346c098d2e657c7e94a22da'
SOURCE=D/'outputs/phase4_gate4_final_closure_20261006'
NET=SOURCE/'complete_network/research_fullsc_2050_assembly_v1_unsolved.nc'
started=time.monotonic();bindings={};files_before={};blockers=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def digest_file(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(n,j):(E/n).write_text(json.dumps(j,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def frac(q):return {'exact':str(q),'approx':float(q)}
def git(*a):return subprocess.check_output(['git','-C',str(R),*a])
def obj(commit,rel,expected=None):
 b=git('show',commit+':'+rel);h=sha(b)
 if expected:assert h==expected,(rel,h)
 bindings[commit+':'+rel]={'sha256':h,'bytes':len(b)}
 return json.loads(b) if rel.endswith('.json') else b.decode()
def filecheck(p,expected):
 stat=p.stat();h=digest_file(p);assert h==expected,(str(p),h)
 files_before[str(p)]=(stat.st_size,stat.st_mtime_ns)
 bindings[str(p).replace('/mnt/d/','D:/')]={'sha256':h,'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns}
def arrsha(a):return sha(np.asarray(a,dtype='<f8',order='C').tobytes(order='C'))
def exact_sum_integer(vals):
 ratios=[float(v).as_integer_ratio() for v in vals]; k=max((q.bit_length()-1 for _,q in ratios),default=0)
 return F(sum(n<<(k-(q.bit_length()-1)) for n,q in ratios),1<<k)
assert subprocess.run(['git','-C',str(R),'merge-base','--is-ancestor',C00,'HEAD']).returncode==0
assert git('branch','--show-current').decode().strip()=='audit/stage2-c01-daily-representation-20261012'
mf=obj(S,P+'EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json','a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720')
ref=obj(S,P+'LOADS_AND_WEIGHTS_REFERENCE.json',mf['files']['LOADS_AND_WEIGHTS_REFERENCE.json']['sha256'])
accounts=obj(S,P+'external_pending_fixed_accounts.json',mf['files']['external_pending_fixed_accounts.json']['sha256'])
recipe=obj(S,P+'carrier_fragment.json',mf['files']['carrier_fragment.json']['sha256'])
bridge=obj(C00,'research/05_baseline_evolution/20261011/b01_b02/evidence/B01_SCHEME_A_SOURCE_BRIDGE.json')
protocol=obj(C00,'research/05_baseline_evolution/20261011/b03_c00/evidence/C00_PROTOCOL_DESIGN.json')
obj(C00,'research/05_baseline_evolution/20261011/b03_c00/C00_DAILY_365_DIAGNOSTIC_PROTOCOL.md')
for k,v in mf['inputs'].items():
 if v['scope']=='git_science':obj(v['commit'],v['path'],v['sha256'])
for key in ['network','allocation','allocation_manifest']:
 rec=mf['inputs'][key];filecheck(SOURCE/rec['path'],rec['sha256'])
zip_path=D/'outputs/B03_C00_DAILY_DIAGNOSTIC_DESIGN_REVIEW.zip'
filecheck(zip_path,'4aee43d3cb4a0cc908848a965c9ba0f50fec9be3159461cea27ea20df7244796')
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 package=json.loads(z.read('PACKAGE_MANIFEST.json'));assert package['commit']==C00
 for q in package['files']:
  b=z.read(q['path']);assert len(b)==q['bytes'] and sha(b)==q['sha256']
print('IDENTITIES_PASS',flush=True)
allocation=json.loads((SOURCE/'actual_allocation/allocation_manifest.json').read_text())
with np.load(SOURCE/'actual_allocation/allocations.npz',allow_pickle=False) as npz:
 source_arrays=[];load_source_sha={};ref_load={x['LoadID']:x for x in ref['loads']}
 records={q['ArrayKey']:q for q in allocation['records']}
 assert set(npz.files)==set(records)|{'weights','snapshots'}
 for k in npz.files:
  a=npz[k];raw=a.tobytes(order='C');source_arrays.append({'key':k,'shape':list(a.shape),'dtype':str(a.dtype),'canonical_SHA256':arrsha(a) if a.dtype.kind=='f' else sha(raw),'bytes':a.nbytes,'role':'Load.p_set source' if k in records else 'time coordinate/weight'})
  if k in records:
   assert arrsha(a)==records[k]['ArraySHA256'],k
 for key,q in ref_load.items():
  v=npz[q['ArrayKey']][:,q['column']];h=arrsha(v);assert h==q['binary64_sha256'];load_source_sha[key]=h
 zero_refs=ref['preexisting_zero_allocation_columns_without_Load']
 source_weights=npz['weights'].copy();source_dates=npz['snapshots'].copy()
 assert np.all(source_weights==3) and arrsha(source_weights)==ref['weights_sha256']
print('SOURCE_ALLOCATION_PASS',len(load_source_sha),flush=True)
def profile(values,asset):
 vals=np.asarray(values,dtype=np.float64);assert vals.shape==(2920,) and np.isfinite(vals).all()
 flat=bool(np.all(vals.view(np.uint64)==vals.view(np.uint64)[0]))
 daily=[];daily_exact=[];mean_error=[];half_bounds=[];bad_days=[];ties=0;max_bits=0;nearest_verified=True
 # Equal 8-value tuples reuse their exact Fraction result. All buckets are still checked.
 cache={}
 for d in range(365):
  block=vals[8*d:8*d+8];key=block.tobytes()
  if key not in cache:
   target=sum((F(float(v))*F(3) for v in block),F(0))/F(24)
   stored=struct.unpack('<d',struct.pack('<d',float(target)))[0]
   err=F(stored)-target;half=F(math.ulp(stored))/2
   assert abs(err)<=half,(asset,d)
   # Exact distance to the nearest neighbor in the direction of the target.
   bits=struct.unpack('<Q',struct.pack('<d',stored))[0]
   if target!=F(stored):
    neighbor_bits=bits+(1 if target>F(stored) else -1)
    neighbor=struct.unpack('<d',struct.pack('<Q',neighbor_bits))[0]
    distance=abs(target-F(stored));other=abs(target-F(neighbor))
    assert distance<=other and (distance!=other or bits%2==0)
   cache[key]=(target,stored,err,half)
  target,stored,err,half=cache[key]
  daily_exact.append(target);daily.append(stored);mean_error.append(err);half_bounds.append(half)
  max_bits=max(max_bits,abs(target.numerator).bit_length())
  if err:bad_days.append(d)
  if err and abs(err)==half:ties+=1
 old=3*exact_sum_integer(vals);new=24*sum((F(v) for v in daily),F(0));expected=24*sum(daily_exact,F(0))
 assert old==expected
 drift=new-old;bound=24*sum(half_bounds,F(0));assert abs(drift)<=bound
 if flat:assert not bad_days and drift==0
 nonzero=[F(math.ulp(v)) for v in daily if v>0]
 umin=min(nonzero) if nonzero else F(math.ulp(0.0));units=(-drift/24)/umin
 annualulp=F(math.ulp(float(old)))
 worst=max(range(365),key=lambda d:abs(mean_error[d]))
 example={'day_index':worst,'date':str(source_dates[8*worst])[:10],'source_8_hex':[float(x).hex() for x in vals[8*worst:8*worst+8]],'exact_mean':str(daily_exact[worst]),'nearest_hex':daily[worst].hex(),'signed_error':str(mean_error[worst]),'half_ulp_bound':str(half_bounds[worst])}
 record={'asset':asset,'source_SHA256_float64_LE':arrsha(vals),'daily_simulation_SHA256_float64_LE':arrsha(daily),'constant_source_binary64':flat,'annual_original':frac(old),'annual_daily':frac(new),'annual_delta_daily_minus_original':frac(drift),'annual_relative_signed_delta':frac(drift/abs(old)) if old else {'exact':'0','approx':0.0},'classification':'EXACT_ANNUAL_PRESERVED' if drift==0 else 'POSITIVE_ANNUAL_DRIFT' if drift>0 else 'NEGATIVE_ANNUAL_DRIFT','not_exactly_representable_daily_means':len(bad_days),'nonrepresentable_day_bitmap_hex':hex(sum(1<<d for d in bad_days)),'rounding_ties':ties,'maximum_exact_mean_significant_bits':max_bits,'annual_half_ULP_bound':frac(bound),'half_ULP_budget_pass':True,'maximum_daily_abs_error':frac(abs(mean_error[worst])),'annual_delta_in_annual_float_ULPs':frac(drift/annualulp),'minimum_positive_daily_ULP':frac(umin),'required_correction_in_minimum_daily_ULPs':frac(units),'local_same_binade_ULP_lattice_necessary_condition':units.denominator==1,'source_minimum':float(vals.min()),'source_maximum':float(vals.max()),'source_negative_count':int(np.count_nonzero(vals<0)),'source_zero_count':int(np.count_nonzero(vals==0)),'source_above_one_count':int(np.count_nonzero(vals>1)),'daily_minimum':min(daily),'daily_maximum':max(daily),'daily_above_one_count':sum(v>1 for v in daily),'worst_mean_example':example}
 # Return only summaries; no proposed correction or derived input arrays are saved.
 return record
inventory=[];coordinate=[];results={};scope_extensions=[];series_before=[]
with netCDF4.Dataset(NET,'r') as n:
 n.set_auto_mask(False)
 times=np.asarray(n['snapshots_snapshot'][:]);vtime=n['snapshots_snapshot'];dates=netCDF4.num2date(times,units=vtime.units,calendar=vtime.calendar)
 assert len(dates)==2920 and len(set(str(x) for x in dates))==2920
 assert np.array_equal(times,np.arange(2920)*3)
 assert [str(x) for x in dates]==[str(x).replace('T',' ') for x in source_dates]
 assert str(dates[0])=='2013-01-01 00:00:00' and str(dates[-1])=='2013-12-31 21:00:00'
 for d in range(365):assert len(set(str(x)[:10] for x in dates[d*8:d*8+8]))==1
 for key in ['objective','generators','stores']:
  a=np.asarray(n['snapshots_'+key][:]);assert np.array_equal(a,source_weights)
  coordinate.append({'field':'snapshots_'+key,'shape':list(a.shape),'SHA256_float64_LE':arrsha(a),'exact_sum':str(3*len(a))})
 coordinate.append({'field':'snapshots_snapshot','shape':list(times.shape),'raw_SHA256_int64_LE':sha(times.astype('<i8').tobytes()),'units':vtime.units,'calendar':vtime.calendar,'first':str(dates[0]),'last':str(dates[-1]),'complete_days':365,'slots_per_day':8,'missing_days':0,'duplicate_slots':0})
 meta=json.loads(n.getncattr('meta'))
 types=['loads','generators','storage_units'];tables={}
 for typ in types:
  ids=[str(x) for x in n[typ+'_i'][:]];tables[typ]={key:{'id':key} for key in ids}
  for attr in ['bus','carrier','source_account_id']:
   if typ+'_'+attr in n.variables:
    for key,v in zip(ids,n[typ+'_'+attr][:]):tables[typ][key][attr]=str(v)
 busids=[str(x) for x in n['buses_i'][:]];countries=dict(zip(busids,[str(x) for x in n['buses_country'][:]]));locations=dict(zip(busids,[str(x) for x in n['buses_location'][:]]))
 def country(bus):return countries.get(bus) or countries.get(locations.get(bus,'')) or 'UNKNOWN'
 dynamic=[(k,v) for k,v in n.variables.items() if 'snapshots' in v.dimensions and not k.startswith('snapshots')]
 for name,var in dynamic:
  typ,attribute=name.split('_t_',1) if '_t_' in name else ('UNKNOWN',name)
  recognized=name in {'loads_t_p_set','generators_t_p_max_pu','storage_units_t_inflow'}
  a=np.asarray(var[:]);assert a.nbytes<=64*1024*1024
  ids=[str(x) for x in n[var.dimensions[1]][:]] if a.ndim==2 else []
  invalid={'NaN':int(np.isnan(a).sum()),'positive_inf':int(np.isposinf(a).sum()),'negative_inf':int(np.isneginf(a).sum()),'negative_values':int((a<0).sum())}
  row={'component':typ,'attribute':attribute,'netcdf_variable':name,'assets':len(ids),'time_slots':a.shape[0],'shape':list(a.shape),'dtype':str(a.dtype),'canonical_data_SHA256_float64_LE_C_order':arrsha(a),'ordered_asset_ids_SHA256_UTF8_JSON':sha(json.dumps(ids,ensure_ascii=False,separators=(',',':')).encode()),'data_bytes':a.nbytes,'asset_ids':ids,'invalid_values':invalid,'fill_value_metadata_present':'_FillValue' in var.ncattrs(),'fill_value_is_actual_NULL':False,'C00_protocol_covered':recognized}
  inventory.append(row)
  if not recognized:scope_extensions.append(name);continue
  if any(invalid[k] for k in ['NaN','positive_inf','negative_inf']):blockers.append('NONFINITE:'+name);continue
  recs=[]
  print('ANALYZE',name,len(ids),flush=True)
  for j,key in enumerate(ids):
   col=a[:,j]
   if typ=='loads':assert key in load_source_sha and arrsha(col)==load_source_sha[key]
   rec=profile(col,key);rec.update(tables[typ][key]);rec['country']=country(rec['bus'])
   rec['quantity_unit']='MWh' if typ!='generators' else 'equivalent_full_load_hours'
   if typ=='loads' and rec['source_negative_count']:blockers.append('NEGATIVE_LOAD:'+key)
   if typ=='storage_units' and rec['source_negative_count']:blockers.append('NEGATIVE_INFLOW:'+key)
   recs.append(rec)
  results[name]=recs
  print('DONE',name,Counter(x['classification'] for x in recs),flush=True)
  del a
 assert set(tables['loads'])==set(load_source_sha)
 source_meta={k:meta.get(k) for k in ['target_year','weather_year','assembly_version','policy_enabled','policy_cap_actually_enabled','no_cap_assembly_v1','full_system_cost_complete','full_system_emissions_complete']}
load=results.get('loads_t_p_set',[]);cf=results.get('generators_t_p_max_pu',[]);inflow=results.get('storage_units_t_inflow',[])
def summary(rows):
 ds=[F(x['annual_delta_daily_minus_original']['exact']) for x in rows]
 maxrow=max(rows,key=lambda x:abs(F(x['annual_delta_daily_minus_original']['exact']))) if rows else None
 relrow=max(rows,key=lambda x:abs(F(x['annual_relative_signed_delta']['exact']))) if rows else None
 return {'assets':len(rows),'constant_source':sum(x['constant_source_binary64'] for x in rows),'varying_source':sum(not x['constant_source_binary64'] for x in rows),'exact_annual':sum(x==0 for x in ds),'positive_drift':sum(x>0 for x in ds),'negative_drift':sum(x<0 for x in ds),'sum_signed_delta':frac(sum(ds,F(0))),'sum_absolute_delta':frac(sum(map(abs,ds),F(0))),'max_abs_delta':{'asset':maxrow['asset'],'bus':maxrow['bus'],'value':frac(abs(F(maxrow['annual_delta_daily_minus_original']['exact'])))} if maxrow else None,'max_relative_delta':{'asset':relrow['asset'],'value':frac(abs(F(relrow['annual_relative_signed_delta']['exact'])))} if relrow else None,'nonrepresentable_daily_means':sum(x['not_exactly_representable_daily_means'] for x in rows),'daily_mean_count':365*len(rows),'max_significant_bits':max((x['maximum_exact_mean_significant_bits'] for x in rows),default=0),'half_ULP_bound_pass':all(x['half_ULP_budget_pass'] for x in rows),'positive_source_min':min((x['source_minimum'] for x in rows if x['source_minimum']>0),default=None),'drift_loads_local_ULP_lattice_obstruction':sum(x['classification']!='EXACT_ANNUAL_PRESERVED' and not x['local_same_binade_ULP_lattice_necessary_condition'] for x in rows),'source_above_one_assets':sum(x['source_above_one_count']>0 for x in rows),'source_above_one_values':sum(x['source_above_one_count'] for x in rows),'daily_above_one_values':sum(x['daily_above_one_count'] for x in rows)}
byload={x['asset']:x for x in load};acc={x['FixedAccountID']:x for x in accounts};groups=[]
for g in bridge['groups']:
 rec=byload[g['load']];qsum=sum((F(acc[i]['QuantityMWh']) for i in g['account_ids']),F(0));old=F(rec['annual_original']['exact']);daily=F(rec['annual_daily']['exact'])
 assert old==F(g['D_MWh']['exact']) and daily==old and qsum==F(g['Q_prime_MWh']['exact']) and daily<=qsum
 for key in g['account_ids']:
  q=acc[key]['QuantityMWh'];p=recipe['components']['Store:'+key]['params'];route=recipe['biomass_obligation_routes'][key]
  assert q==p['e_nom']==p['e_initial']==route['annual_cap_mwh']
 groups.append({'load':g['load'],'bus':g['bus'],'account_ids':g['account_ids'],'original_D_MWh':str(old),'daily_D_MWh':str(daily),'approved_Q_prime_MWh':str(qsum),'Q_prime_minus_daily_D_MWh':str(qsum-daily),'exact_annual_preserved':True,'D_le_Q_prime':True})
assert len(groups)==385 and len(acc)==807
if scope_extensions:blockers.append('BLOCKED_PROTOCOL_EXTENSION:'+','.join(scope_extensions))
status='C01_BLOCKED_WITH_EVIDENCE' if blockers else 'C01_REPRESENTATION_DECISION_REQUIRED' if any(F(x['annual_delta_daily_minus_original']['exact']) for x in load) else 'C01_REPRESENTATION_PASS'
save('C01_LOAD_ANNUAL_EXACT_CHECK.json',{'status':status,'method':'Exact Fraction(float)*Fraction(3) per source, /Fraction(24) per full bucket, round-to-nearest ties-even binary64 byte serialization simulated, no mean/isclose or corrections','units':'MW inputs / MWh annual totals','source_network_SHA256':mf['inputs']['network']['sha256'],'summary':summary(load),'records':load,'biomass_groups':groups,'Q_modified_this_task':0,'new_input_arrays_saved':False})
save('C01_CF_INFLOW_ROUNDING_CHECK.json',{'method':'Same exact weighted rational daily mean; actual nearest serialization versus sum of 24*half-ULP bounds. Source value outside [0,1] is recorded, not clipped.','CF':{'summary':summary(cf),'records':cf},'inflow':{'summary':summary(inflow),'records':inflow},'scientific_changes':0})
save('C01_DYNAMIC_ATTRIBUTE_INVENTORY.json',{'source_network_sha256':mf['inputs']['network']['sha256'],'scope':'Every NetCDF variable with snapshots dimension; coordinate variables and weight columns separately enumerated. Source NPZ keys exactly allocation records plus weights/snapshots. No PyPSA model instantiated.','dynamic_attributes':inventory,'coordinates_and_weights':coordinate,'allocation_source_arrays':source_arrays,'source_array_count':len(source_arrays),'source_Load_sha_matches':len(load_source_sha),'preexisting_zero_allocation_columns_without_Load':len(zero_refs),'additional_dynamic_attributes':scope_extensions,'source_meta':source_meta,'protocol_extension_required':bool(scope_extensions),'NULL_interpretation':'NetCDF NaN _FillValue attribute is metadata, not an actual missing observation. All values explicitly counted.'})
for path,stat in files_before.items():
 p=Path(path);assert (p.stat().st_size,p.stat().st_mtime_ns)==stat
save('C01_SOURCE_IDENTITY_AND_SCOPE.json',{'status':'PASS','C00_commit':C00,'Scheme_A_commit':S,'Scheme_A_manifest_SHA256':'a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720','scientific_commit':SCI,'bindings':bindings,'read_only_file_stat_unchanged':True,'source_hash_scope':'NetCDF, NPZ, allocation manifest streamed/read once for SHA; fixed Git object SHA checked. No CSC, solution vectors or new network.','original_network_open_mode':'r','python':__import__('sys').version.split()[0],'numpy':np.__version__,'netCDF4':netCDF4.__version__,'max_RSS_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'wall_seconds':time.monotonic()-started,'model_builds':0,'solver_calls':0,'AutoDL_operations':0,'source_write_operations':0,'G6_05':'PAUSED_BY_USER'})
save('C01_RESULT_SUMMARY.json',{'status':status,'blockers':blockers,'loads':summary(load),'CF':summary(cf),'inflow':summary(inflow),'Scheme_A':{'groups':385,'accounts':807,'exact_annual_preserved':385,'exact_D_le_Q_prime':385,'Q_rederived':False,'Q_modified':0},'dynamic_attribute_count':len(inventory),'protocol_extensions':scope_extensions,'new_network_or_LP':False,'candidate_rule_applied':False,'finished_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()})
print(json.dumps({'status':status,'loads':summary(load),'CF':summary(cf),'inflow':summary(inflow),'seconds':time.monotonic()-started},ensure_ascii=False,indent=2),flush=True)
