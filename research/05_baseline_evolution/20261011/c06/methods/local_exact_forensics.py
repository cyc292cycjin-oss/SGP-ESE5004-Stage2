"""Independent exact arithmetic on selected frozen daily CSR rows/CSC columns.
No solver import; no model creation; no full coefficient scan.
"""
from pathlib import Path
from fractions import Fraction as F
import json,math,hashlib,collections,time,numpy as np,xarray as xr
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c06_barconvtol_20261012');N=W/'analysis_view'
B=Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run')
C4=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c04_daily_pattern_20261012')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
arr=lambda p:np.load(p,mmap_mode='r',allow_pickle=False)
ff=lambda x:F(float(x))
def dump(name,v):(W/name).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
t0=time.time();ap=read(W/'C06_ALL_ACCOUNT_AND_GROUP_COMPARISON.json');ks=read(W/'C06_KKT_FAILURE_SET_COMPARISON.json');mf=read(W/'C06_MATRIX_ROW_FAMILY_COMPARISON.json')
M=read(B/'artifacts/lp/MATH_PROBLEM.json');MM=read(B/'bridge/math_problem/MATH_PROBLEM.json');MAP=read(B/'bridge/mapping/MAPPING_MANIFEST.json');L=read(B/'artifacts/mapping/LABELS.json')
A={k:arr(B/'bridge/math_problem'/v['file']) for k,v in MM['arrays'].items()};D=arr(B/'bridge/mapping/D.npy');R=arr(B/'bridge/mapping/R.npy')
vv={k:{v:arr(p/'raw/vectors'/f'{v}.npy') for v in ('X','Pi','RC')} for k,p in [('C03',B),('C06',N)]}
for k,p in [('C03',B),('C06',N)]:vv[k]['original']=arr(p/'postprocess/original_vectors/X_original.npy')
cl=arr(B/'bridge/mapping/clabels.npy');vl=arr(B/'bridge/mapping/vlabels.npy');ends=np.array([r['end'] for r in MAP['row_ranges']]);starts=np.array([r['start'] for r in MAP['row_ranges']])
old=read(C4/'C04_SELECTED_PHYSICAL_RECOMPUTATION.json');oldk=read(C4/'C04_KKT_COLUMN_CLASSIFICATION.json')
selected_rows={r['row'] for r in old['representative_rows']}
for family in {r['family'] for r in mf['families']}:
 item=max((r for r in mf['families'] if r['family']==family),key=lambda r:r['max_violation_original'])
 if family in ('Store-fix-e-lower','Store-energy_balance','Bus-nodal_balance','Bus-meshed-nodal_balance') or item['fail_count']:selected_rows.add(item['worst_row'])
checks=[];touched=set()
for row in sorted(selected_rows):
 j=int(np.searchsorted(ends,row,side='right'));chunk=M['chunks'][j];d=B/'artifacts/lp'/chunk['dir'];i=int(row-starts[j]);ptr=arr(d/'indptr.npy');s,e=map(int,ptr[i:i+2]);ix=arr(d/'indices.npy')[s:e];a=arr(d/'value_original.npy')[s:e];asc=arr(d/'value_scaled.npy')[s:e]
 touched.add(chunk['dir']);lo=arr(d/'row_lower_original.npy')[i];hi=arr(d/'row_upper_original.npy')[i]
 rec={'row':row,'label':int(cl[row]),'family':chunk['family'],'source_chunk':chunk['dir'],'R':float(R[row]),'support':[], 'lower':str(float(lo)),'upper':str(float(hi))}
 for c,v,vs in zip(ix,a,asc):
  assert ff(vs)==ff(R[row])*ff(v)*ff(D[c])
  rec['support'].append({'column':int(c),'label':int(vl[c]),'a_original_hex':float(v).hex(),'a_solver_hex':float(vs).hex(),'D':float(D[c])})
 for k in ('C03','C06'):
  x=vv[k]['original'];z=vv[k]['X'];pi=vv[k]['Pi'];act=sum((ff(v)*ff(x[c]) for c,v in zip(ix,a)),F(0));sc=sum((ff(v)*ff(z[c]) for c,v in zip(ix,asc)),F(0));assert act==sc/ff(R[row])
  violation=max(F(0),ff(lo)-act if math.isfinite(lo) else F(0),act-ff(hi) if math.isfinite(hi) else F(0))
  mult=ff(pi[row])*ff(R[row]);comp=abs(mult*(act-ff(lo))) if mult>0 and math.isfinite(lo) else abs(mult*(ff(hi)-act)) if mult<0 and math.isfinite(hi) else F(0)
  rec[k]={'activity_original_exact':str(act),'activity_solver_exact':str(sc),'violation_original_exact':str(violation),'violation_original':float(violation),'violation_solver':float(violation*ff(R[row])),
   'complementarity_EUR_exact':str(comp),'complementarity_EUR':float(comp),'coordinate_identity_exact':True}
 checks.append(rec)
cols={r['column'] for r in oldk['exact_representative_columns']}
for fam in {r['family'] for r in ks['failed_columns']}:
 cols.add(max((r for r in ks['failed_columns'] if r['family']==fam),key=lambda r:r['normalized'])['column'])
exactcols=[]
for c in sorted(cols):
 s,e=map(int,A['start'][c:c+2]);rr=A['index'][s:e];coef=A['value'][s:e]
 rec={'column':c,'label':int(vl[c]),'D':float(D[c]),'row_support':[{'row':int(r),'family':MAP['row_ranges'][int(np.searchsorted(ends,r,side='right'))]['family'],'a_solver_hex':float(a).hex(),'R':float(R[r])} for r,a in zip(rr,coef)]}
 for k in ('C03','C06'):
  v=vv[k];sp=ff(A['cost'][c])-sum((ff(a)*ff(v['Pi'][r]) for r,a in zip(rr,coef)),F(0))-ff(v['RC'][c]);op=sp/ff(D[c])
  independently=ff(A['cost'][c])/ff(D[c])-sum((ff(a)/(ff(R[r])*ff(D[c]))*(ff(v['Pi'][r])*ff(R[r])) for r,a in zip(rr,coef)),F(0))-ff(v['RC'][c])/ff(D[c]);assert op==independently
  scale=max(F(1),(abs(ff(A['cost'][c]))+sum((abs(ff(a)*ff(v['Pi'][r])) for r,a in zip(rr,coef)),F(0))+abs(ff(v['RC'][c])))/ff(D[c]))
  rec[k]={'stationarity_original_exact':str(op),'stationarity_original':float(op),'normalized_exact':str(abs(op)/scale),'normalized':float(abs(op)/scale),'RC_original':float(v['RC'][c]/D[c]),'coordinate_identity_exact':True}
 exactcols.append(rec)
# Per-group signed resource allocation and within-group cancellation, not just net demand.
accounts={r['asset']:r for r in ap['accounts']};grows=[]
scale={r['bus']:r for r in read(C4/'C04_SCALE_CONFOUNDING.json')['groups']}
strata=collections.defaultdict(lambda:dict(groups=0,accounts=0,C03_failed_accounts=0,C06_failed_accounts=0,C03_failed_groups=0,C06_failed_groups=0))
for g in ap['groups']:
 rec={k:g[k] for k in ('bus','country','sector','account_count','accounts')};rec['D']=scale[g['bus']]['D'];rec['R_final']=scale[g['bus']]['R_final'];rec['demand_MWh']=scale[g['bus']]['source_D_MWh']
 qbin=int(math.floor(math.log10(max(rec['demand_MWh'],1e-300))));key=(rec['country'],rec['sector'],rec['D'],qbin,rec['account_count']);st=strata[key];st['groups']+=1;st['accounts']+=len(g['accounts'])
 for k in ('C03','C06'):
  rows=[accounts[a][k] for a in g['accounts']];signed=[r['metrics']['annual_signed_error_MWh'] for r in rows]
  rec[k]={'failed_accounts':sum(not r['passed'] for r in rows),'failed_group':not g[k]['passed'],
    'positive_account_excess_MWh':math.fsum(max(0,x) for x in signed),'negative_account_shortfall_MWh':math.fsum(max(0,-x) for x in signed),'net_resource_error_MWh':math.fsum(signed),
    'over_and_under_account_cancellation_MWh':min(math.fsum(max(0,x) for x in signed),math.fsum(max(0,-x) for x in signed)),
    'terminal_stock_sum_MWh':math.fsum(r['metrics']['terminal_stock_MWh'] for r in rows)}
  st[k+'_failed_accounts']+=rec[k]['failed_accounts'];st[k+'_failed_groups']+=rec[k]['failed_group']
 grows.append(rec)
# Old Line 52 free-RC failed points, all days, under unchanged V4 normalization.
free=[]
for oldr in oldk['dual_sign_failures']:
 if oldr['kind']!='column':continue
 c=oldr['index'];assert not np.isfinite(A['col_lower'][c]) and not np.isfinite(A['col_upper'][c])
 free.append({'column':c,'coordinates':oldr['coordinates'],**{k:float(vv[k]['RC'][c]/D[c]) for k in ('C03','C06')}})
# Exact candidate export readback at selected row support variables, all their labeled entries.
indices=sorted({t['column'] for r in checks for t in r['support']});query=np.asarray(indices);labs=vl[query];net=xr.open_dataset(N/'postprocess/daily_candidate_UNQUALIFIED.nc');exportchecks=[];export_not_stored=[]
assert len(net['snapshots_snapshot'])==365 and np.array_equal(net['snapshots'].values,np.arange(365))
net=net.assign_coords(snapshots=net['snapshots_snapshot'].values)
for block in L['variables']:
 la=arr(B/'artifacts/mapping'/block['labels_file']);flat=la.ravel();valid=flat[flat>=0]
 if not len(valid):continue
 mask=(labs>=valid.min())&(labs<=valid.max())
 if not mask.any():continue
 pp=np.searchsorted(valid,labs[mask]);positions=np.flatnonzero(flat>=0)[pp]
 names={'Store-e':'stores_t_e','Store-p':'stores_t_p','Link-p':'links_t_p0','Line-s':'lines_t_p0','Generator-p':'generators_t_p','StorageUnit-p_dispatch':'storage_units_t_p_dispatch','StorageUnit-p_store':'storage_units_t_p_store','StorageUnit-state_of_charge':'storage_units_t_state_of_charge'}
 if block['name'] not in names:continue
 var=names[block['name']]
 if var not in net:continue
 for c,pos in zip(query[mask],positions):
  loc=np.unravel_index(pos,la.shape);co=dict(zip(block['dims'],(block['coordinates'][d][i] for d,i in zip(block['dims'],loc))))
  selectors={d:co['snapshot'] if d=='snapshots' else co[block['name'].split('-')[0]] for d in net[var].dims}
  if any(selectors[d] not in net[d].values for d in net[var].dims if d!='snapshots'):
   export_not_stored.append({'column':int(c),'variable':var,'coordinates':co,'status':'ASSET_NOT_EXPLICITLY_STORED_IN_THIS_TABLE; not tested as direct scalar readback'})
   continue
  got=float(net[var].sel(selectors).item());assert ff(got)==ff(vv['C06']['original'][c])
  exportchecks.append({'column':int(c),'variable':var,'coordinates':co,'value_hex':got.hex()})
dump('C06_EXACT_LOCAL_FORENSICS.json',{'exact_rows':checks,'exact_columns':exactcols,'NetCDF_selected_values':exportchecks,'NetCDF_not_explicitly_stored':export_not_stored,
 'all_coordinate_identities_exact':True,'row_count':len(checks),'column_count':len(exactcols),'CSR_chunks_touched':len(touched),'daily_full_coefficient_scans':0,
 'old_annual_matrix_reads':0,'new_solver_calls':0,'new_models':0,'elapsed_seconds':time.time()-t0,'source_provenance_SHA':sha(W/'C06_ANALYSIS_PROVENANCE.json')})
dump('C06_GROUP_PATTERN_AND_FREE_RC.json',{'groups':grows,'matched_strata':[dict(country=k[0],sector=k[1],D=k[2],demand_log10_bin=k[3],account_count=k[4],**v) for k,v in sorted(strata.items())],
 'Line52_previous_free_RC_failures':free,'interpretation':'observational strata; cardinality/country/commodity/scale confounded; not causal isolation'})
print(json.dumps({'rows':len(checks),'columns':len(exactcols),'NetCDF_values':len(exportchecks),'seconds':time.time()-t0}))
