"""Read-only post-return comparison. One daily CSC traversal, local Fraction checks.
No solver imports, no model builds, no changes to any result or contract.
"""
from pathlib import Path
from fractions import Fraction as F
import json,math,time,hashlib,collections,resource
import numpy as np
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c07_v4_reliability_20261013')
W6=W.parent/'c06_barconvtol_20261012';ROOT=W.parents[1]/'outputs'
B=ROOT/'c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
load=lambda p:np.load(p,mmap_mode='r',allow_pickle=False)
ff=lambda x:F(float(x))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
def write(n,x):
 with (W/n).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def transitions(a,b):return dict(old_count=len(a),current_count=len(b),resolved=sorted(a-b),retained=sorted(a&b),new=sorted(b-a))
t0=time.time();M=read(B/'bridge/math_problem/MATH_PROBLEM.json');MAP=read(B/'bridge/mapping/MAPPING_MANIFEST.json');LAB=read(B/'artifacts/mapping/LABELS.json')
A={k:load(B/'bridge/math_problem'/v['file']) for k,v in M['arrays'].items()};D=load(B/'bridge/mapping/D.npy');R=load(B/'bridge/mapping/R.npy');vl=load(B/'bridge/mapping/vlabels.npy');cl=load(B/'bridge/mapping/clabels.npy')
VM={b['name']:b for b in LAB['variables']};oldac=read(W6/'C06_ALL_ACCOUNT_AND_GROUP_COMPARISON.json');oldks=read(W6/'C06_KKT_FAILURE_SET_COMPARISON.json');oldrows=read(W6/'C06_MATRIX_ROW_FAMILY_COMPARISON.json')
def cols(name,asset):
 b=VM[name];la=load(B/'artifacts/mapping'/b['labels_file']);dim=next(d for d in b['dims'] if d!='snapshot');labs=np.take(la,b['coordinates'][dim].index(asset),axis=b['dims'].index(dim)).ravel();ix=np.searchsorted(vl,labs);assert np.array_equal(vl[ix],labs);return ix
def describe(indices):
 out={};q=np.asarray(sorted(set(indices)),dtype=int);labs=vl[q]
 for b in LAB['variables']:
  la=load(B/'artifacts/mapping'/b['labels_file']);flat=la.ravel();valid=flat[flat>=0]
  if not len(valid):continue
  mask=(labs>=valid.min())&(labs<=valid.max())
  if not mask.any():continue
  p=np.searchsorted(valid,labs[mask]);assert np.array_equal(valid[p],labs[mask])
  for c,pos in zip(q[mask],np.flatnonzero(flat>=0)[p]):
   loc=np.unravel_index(pos,la.shape) if la.shape else ();out[int(c)]=dict(family=b['name'],label=int(vl[c]),coordinates={d:b['coordinates'][d][i] for d,i in zip(b['dims'],loc)})
 assert len(out)==len(q);return out
V={};summ={};provenance={}
for k in ('A','B'):
 pfile=W/(k+'_LOCAL_BACKUP_RECEIPT.json')
 if not pfile.exists():summ[k]={'status':'LOCAL_SYNC_PENDING'};continue
 rec=read(pfile);p=Path(rec['local_run'].replace('D:\\','/mnt/d/').replace('\\','/'));raw=read(p/'raw/vectors/RAW_RECEIPT.json');info=raw['native_info'];post=read(p/'postprocess/POSTPROCESS_RECEIPT.json') if (p/'postprocess/POSTPROCESS_RECEIPT.json').exists() else None
 summ[k]=dict(run_id=raw['run_id'],native_status=raw['native_status'],info=info,postprocess=post,backup_status=rec['status'])
 provenance[k]={'raw_receipt_sha256':sha(p/'raw/vectors/RAW_RECEIPT.json'),'backup_receipt_sha256':sha(pfile)}
 resources=[json.loads(s) for s in (p/'RESOURCE.jsonl').read_text().splitlines() if s.strip()]
 summ[k]['resources']=dict(sampled_process_RSS_max=max(r['rss_bytes'] for r in resources),cgroup_current_max=max(c['current'] for r in resources for c in r['cgroup']),cgroup_headroom_min=min(r['cgroup_headroom_bytes'] for r in resources),disk_free_min=min(r['disk_free_bytes'] for r in resources),protection_reasons=[r['reason'] for r in resources if r.get('reason')],resource_samples=len(resources),cgroup_peak_scope='shared cgroup lifetime; not run-exclusive')
 if not post:continue
 assert read(p/'C07_CANONICAL_MAPPING.json')['status']=='PASS'
 V[k]={'path':p,'X':load(p/'canonical_raw_for_V4/vectors/X.npy'),'Pi':load(p/'canonical_raw_for_V4/vectors/Pi.npy'),'RC':load(p/'canonical_raw_for_V4/vectors/RC.npy'),'original':load(p/'postprocess/original_vectors/X_original.npy'),'native':{q:load(p/'raw/vectors'/f'{q}.npy') for q in ('X','Pi','RC')},'phys':read(p/'postprocess/PHYSICAL_CHECKS.json'),'kkt':read(p/'postprocess/KKT.json'),'de':load(p/'expression/D_exponent.npy'),'re':load(p/'expression/R_exponent.npy')}
 summ[k]['KKT']=V[k]['kkt'];summ[k]['physical_checks']=V[k]['phys']['checks'];summ[k]['costs']=read(p/'postprocess/DUAL_COST_LEDGER.json')
 resources=[json.loads(s) for s in (p/'RESOURCE.jsonl').read_text().splitlines() if s.strip()]
 summ[k]['resources']=dict(sampled_process_RSS_max=max(r['rss_bytes'] for r in resources),cgroup_current_max=max(c['current'] for r in resources for c in r['cgroup']),cgroup_headroom_min=min(r['cgroup_headroom_bytes'] for r in resources),disk_free_min=min(r['disk_free_bytes'] for r in resources),protection_reasons=[r['reason'] for r in resources if r.get('reason')],resource_samples=len(resources),cgroup_peak_scope='shared cgroup lifetime; not run-exclusive')
 # All resource/group budgets are read from unchanged V4 receipts; stocks independently recovered from X.
 pa={r['asset']:r for r in V[k]['phys']['details']['fixed_prefix_checks']};ga={r['buses'][0]:r for r in V[k]['phys']['details']['fixed_group_obligations_v4']}
 assert len(pa)==807 and len(ga)==385
 accounts=[];groups=[]
 for old in oldac['accounts']:
  a=old['asset'];r=pa[a];e=V[k]['original'][cols('Store-e',a)];flow=V[k]['original'][cols('Store-p',a)];meter=V[k]['original'][cols('Link-p',old['meter'])];annual=math.fsum(float(x)*24 for x in flow);assert annual==r['annual_release_mwh'];q=old['Q_MWh'];budget=r['energy_budget_mwh']
  errors=dict(annual_abs_MWh=abs(annual-q),stock_lower_MWh=max(0,-float(e.min())),terminal_abs_MWh=abs(float(e[-1])),prefix_max_MWh=r['max_prefix_error_mwh'],state_L1_MWh=r['gross_state_error_mwh'],meter_L1_MWh=r['meter_difference_l1_mwh'])
  accounts.append(dict(asset=a,Q_MWh=q,budget_MWh=budget,passed=r['passed'],checks=r['draft_checks'],annual_release_MWh=annual,annual_signed_error_MWh=annual-q,minimum_stock_MWh=float(e.min()),terminal_stock_MWh=float(e[-1]),errors=errors,error_over_budget={n:x/budget for n,x in errors.items()},meter_max_independent_MW=float(np.max(abs(flow-meter)))))
 for old in oldac['groups']:
  r=dict(ga[old['bus']]);r.update({q:old[q] for q in ('bus','country','sector','account_count','accounts')});groups.append(r)
 acmap={r['asset']:r for r in accounts};card=[]
 for n in (1,2,3,4):
  gg=[r for r in groups if r['account_count']==n];aa=[acmap[a] for r in gg for a in r['accounts']];card.append(dict(account_count=n,groups=len(gg),accounts=len(aa),failed_groups=sum(not r['passed'] for r in gg),failed_accounts=sum(not r['passed'] for r in aa)))
 summ[k]['resource_totals']=dict(failed_accounts=sum(not r['passed'] for r in accounts),failed_groups=sum(not r['passed'] for r in groups),positive_annual_overuse_MWh=math.fsum(max(0,r['annual_signed_error_MWh']) for r in accounts),negative_annual_shortfall_MWh=math.fsum(max(0,-r['annual_signed_error_MWh']) for r in accounts),group_gross_over_MWh=math.fsum(r['gross_oversupply_mwh'] for r in groups),group_gross_under_MWh=math.fsum(r['gross_undersupply_mwh'] for r in groups),max_account_error_budget_ratio=max(v for r in accounts for v in r['error_over_budget'].values()),cardinality=card)
 write(k+'_ALL_ACCOUNT_GROUP_COMPARISON.json',dict(accounts=accounts,groups=groups,cardinality=card,C06_accounts=transitions({r['asset'] for r in oldac['accounts'] if not r['C06']['passed']},{r['asset'] for r in accounts if not r['passed']}),C03_accounts=transitions({r['asset'] for r in oldac['accounts'] if not r['C03']['passed']},{r['asset'] for r in accounts if not r['passed']})))
 # Complete row classification from durable activity/budget arrays; no repeated A*x.
 act=load(p/'postprocess/kkt/algebra/activity_solver.npy');tol=load(p/'postprocess/kkt/budgets/row_tolerance.npy');families=[];badrows=[]
 for f in MAP['row_ranges']:
  s,e=f['start'],f['end'];v=act[s:e]/R[s:e];lo=A['row_lower'][s:e]/R[s:e];hi=A['row_upper'][s:e]/R[s:e];viol=np.maximum(0,np.maximum(np.where(np.isfinite(lo),lo-v,0),np.where(np.isfinite(hi),v-hi,0)));js=np.flatnonzero(viol>tol[s:e]);j=int(np.argmax(viol));families.append(dict(family=f['family'],rows=e-s,failures=len(js),max_violation=float(viol[j]),worst_row=s+j))
  for j in js:badrows.append(dict(row=int(s+j),label=int(cl[s+j]),family=f['family'],violation=float(viol[j]),budget=float(tol[s+j]),R_old=float(R[s+j]),R_new=float(np.ldexp(1.,V[k]['re'][s+j]))))
 assert len(badrows)==V[k]['kkt']['row_fail_count'];V[k]['badrows']=badrows;V[k]['families']=families
 write(k+'_ROW_FAMILY_CHECK.json',dict(families=families,failed_rows=badrows,C06_transition=transitions({r['row'] for r in oldrows['failed_rows']},{r['row'] for r in badrows})))
 print(k,'resources and rows classified',flush=True)

# One streaming traversal of 11.4M saved daily coefficients; evaluate both returned points together.
assert 'A' in V and summ['B']['native_status']==3 and summ['B']['info']['SolCount']==0
fail={k:[] for k in V};nnz=0
for s in range(0,M['num_col'],20000):
 e=min(M['num_col'],s+20000);p,q=map(int,(A['start'][s],A['start'][e]));assert q-p<=5_000_000;rr=A['index'][p:q];coef=A['value'][p:q];ci=np.repeat(np.arange(e-s),np.diff(A['start'][s:e+1]));nnz+=q-p
 for k,v in V.items():
  aty=np.bincount(ci,weights=coef*v['Pi'][rr],minlength=e-s);ab=np.bincount(ci,weights=abs(coef*v['Pi'][rr]),minlength=e-s);res=(A['cost'][s:e]-aty-v['RC'][s:e])/D[s:e];scale=np.maximum(1.,abs(A['cost'][s:e]/D[s:e])+ab/D[s:e]+abs(v['RC'][s:e]/D[s:e]));norm=abs(res)/scale
  for j in np.flatnonzero(norm>1e-6):fail[k].append(dict(column=int(s+j),residual=float(res[j]),normalized=float(norm[j])))
assert nnz==11403496
for k,v in V.items():
 ds=describe(r['column'] for r in fail[k]);sign=[]
 for r in fail[k]:r.update(ds[r['column']])
 for kind,length,vec,sc,lo,hi in [('column',M['num_col'],v['RC'],D,A['col_lower'],A['col_upper']),('row',M['num_row'],v['Pi'],R,A['row_lower'],A['row_upper'])]:
  for s in range(0,length,100000):
   e=min(length,s+100000);mu=vec[s:e]/sc[s:e] if kind=='column' else vec[s:e]*sc[s:e];er=np.where(~np.isfinite(lo[s:e]),np.maximum(mu,0),0)+np.where(~np.isfinite(hi[s:e]),np.maximum(-mu,0),0);norm=er/np.maximum(1,abs(mu))
   for j in np.flatnonzero(norm>1e-6):sign.append(dict(kind=kind,index=int(s+j),original_multiplier=float(mu[j]),normalized=float(norm[j]),free=bool(not np.isfinite(lo[s+j]) and not np.isfinite(hi[s+j]))))
 assert len(fail[k])==v['kkt']['stationarity_fail_count'] and len(sign)==v['kkt']['dual_sign_fail_count']
 ds=describe(r['index'] for r in sign if r['kind']=='column')
 for r in sign:
  if r['kind']=='column':r.update(ds[r['index']])
 summary=dict(stationarity_families=dict(collections.Counter(r['family'] for r in fail[k])),sign_families=dict(collections.Counter(r.get('family',r['kind']) for r in sign)),free_RC_failures=sum(r['kind']=='column' and r['free'] for r in sign),C06_stationarity=transitions({r['column'] for r in oldks['failed_columns']},{r['column'] for r in fail[k]}))
 summ[k]['KKT_classification']=summary;v['sign']=sign
 grouped={}
 for r in sign:
  coordinates=r.get('coordinates',{});static={n:x for n,x in coordinates.items() if n!='snapshot'};key=json.dumps([r['kind'],r.get('family','row'),static],sort_keys=True)
  g=grouped.setdefault(key,dict(kind=r['kind'],family=r.get('family','row'),asset_coordinates=static,entries=[]))
  g['entries'].append([r['index'],coordinates.get('snapshot'),r['original_multiplier'],r['normalized'],r['free']])
 write(k+'_KKT_CLASSIFICATION.json',dict(**summary,failed_columns=fail[k],dual_sign_failure_groups=list(grouped.values()),dual_sign_entry_schema=['index','snapshot','original_multiplier','normalized','free'],all_dual_sign_failures_included=len(sign),source_receipt_sha256=sha(v['path']/'postprocess/KKT.json')))

# Exact local checks: worst/new physical rows; historically diagnosed resource/Line/Link columns.
LP=read(B/'artifacts/lp/MATH_PROBLEM.json');ends=np.array([r['end'] for r in MAP['row_ranges']]);starts=np.array([r['start'] for r in MAP['row_ranges']]);rows={3357088,3258844}
for v in V.values():
 rows.update(r['row'] for r in v['badrows'][:10]);rows.update(r['worst_row'] for r in v['families'] if r['family'] in ('Store-energy_balance','Bus-nodal_balance','Bus-meshed-nodal_balance'))
cols_set={318846,1407794,356365,2047858}
for k in V:
 for family in set(r['family'] for r in fail[k]):cols_set.add(max((r for r in fail[k] if r['family']==family),key=lambda r:r['normalized'])['column'])
 for r in V[k]['sign'][:2]:
  if r['kind']=='column':cols_set.add(r['index'])
erows=[];ecols=[]
for row in sorted(rows):
 j=int(np.searchsorted(ends,row,side='right'));c=LP['chunks'][j];folder=B/'artifacts/lp'/c['dir'];i=int(row-starts[j]);ptr=load(folder/'indptr.npy');s,e=map(int,ptr[i:i+2]);ix=load(folder/'indices.npy')[s:e];av=load(folder/'value_original.npy')[s:e];asc=load(folder/'value_scaled.npy')[s:e];lo=load(folder/'row_lower_original.npy')[i];hi=load(folder/'row_upper_original.npy')[i]
 descriptions=describe(ix)
 rec=dict(row=row,label=int(cl[row]),family=c['family'],support=[dict(column=int(x),coefficient_hex=float(y).hex(),**descriptions[int(x)]) for x,y in zip(ix,av)],lower=str(float(lo)),upper=str(float(hi)))
 for k,v in V.items():
  dn=np.ldexp(1.,v['de'][ix]);rn=math.ldexp(1.,int(v['re'][row]));newcoef=np.ldexp(asc,v['re'][row]-np.frexp(R[row])[1]+1+v['de'][ix]-np.frexp(D[ix])[1]+1)
  original=sum((ff(y)*ff(v['original'][x]) for x,y in zip(ix,av)),F(0));old=sum((ff(y)*ff(v['X'][x]) for x,y in zip(ix,asc)),F(0));new=sum((ff(y)*ff(v['native']['X'][x]) for x,y in zip(ix,newcoef)),F(0));assert original==old/ff(R[row])==new/ff(rn)
  violation=max(F(0),ff(lo)-original if math.isfinite(lo) else F(0),original-ff(hi) if math.isfinite(hi) else F(0))
  rec[k]=dict(activity_exact=str(original),violation_exact=str(violation),violation_original=float(violation),violation_new=float(violation*ff(rn)),R_new=rn,coordinate_identity_exact=True)
 erows.append(rec)
for c in sorted(cols_set):
 p,q=map(int,A['start'][c:c+2]);rr=A['index'][p:q];av=A['value'][p:q];rec=dict(column=c,description=describe([c])[c],support_rows=[int(r) for r in rr],terms=len(rr))
 for k,v in V.items():
  ro=ff(A['cost'][c])/ff(D[c])-sum((ff(a)*ff(v['Pi'][r])/ff(D[c]) for r,a in zip(rr,av)),F(0))-ff(v['RC'][c])/ff(D[c]);dn=math.ldexp(1.,int(v['de'][c]));cn=math.ldexp(float(A['cost'][c]),int(v['de'][c]-np.frexp(D[c])[1]+1));an=np.ldexp(av,v['re'][rr]-np.frexp(R[rr])[1]+1+v['de'][c]-np.frexp(D[c])[1]+1);rn=(ff(cn)-sum((ff(a)*ff(v['native']['Pi'][r]) for r,a in zip(rr,an)),F(0))-ff(v['native']['RC'][c]))/ff(dn);assert ro==rn
  magnitude=(abs(ff(A['cost'][c]))+sum((abs(ff(a)*ff(v['Pi'][r])) for r,a in zip(rr,av)),F(0))+abs(ff(v['RC'][c])))/ff(D[c]);scale=max(F(1),magnitude);n=2*len(rr)+4;u=F(1,2**53);bound=n*u/(1-n*u)*magnitude
  rec[k]=dict(stationarity_original_exact=str(ro),normalized_exact=str(abs(ro)/scale),normalized=float(abs(ro)/scale),RC_original=float(v['RC'][c]/D[c]),R_D_identity_exact=True,standard_dot_subtraction_roundoff_bound_EUR_per_unit=float(bound),absolute_residual_over_arithmetic_bound=float(abs(ro)/bound) if bound else None,bound_assumptions='binary64 products/additions, no overflow/subnormal, n=2k+4; not model condition or solver error bound')
 ecols.append(rec)
write('C07_EXACT_LOCAL_CROSS_COORDINATE_CHECK.json',dict(rows=erows,columns=ecols,all_identities_exact=True,old_annual_matrix_reads=0,full_daily_scans_for_exact_checks=0))
write('C07_C06_A_B_COMPARISON.json',dict(results=summ,source_provenance=provenance,method=dict(one_daily_CSC_traversal_nnz=nnz,exact_rows=len(erows),exact_columns=len(ecols),seconds=time.time()-t0,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,solver_imports=0,solver_calls=0,models_built=0)))
print(json.dumps({k:dict(status=s.get('native_status'),gates=(s.get('postprocess') or {}).get('gates'),resource=s.get('resource_totals'),KKT=s.get('KKT')) for k,s in summ.items()},indent=2),flush=True)
