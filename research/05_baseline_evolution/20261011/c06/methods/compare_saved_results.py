"""Post-return comparison only. Existing frozen daily data; no model/solver imports.
One bounded C06 stationarity traversal; reuse C04 baseline classification.
Source files are read-only. All outputs are separate diagnostic evidence.
"""
from pathlib import Path
import json, math, hashlib, time, resource, collections
import numpy as np
import xarray as xr

W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c06_barconvtol_20261012')
ROOT=Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
load=lambda p:np.load(p,mmap_mode='r',allow_pickle=False)
RID=read(W/'LAUNCH_RECEIPT.json')['run_id']
N=W/'analysis_view'
B=ROOT/'c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run'
C4=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c04_daily_pattern_20261012')
def write(name,v):
    (W/name).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ratio(a,b):return a/b if b else (0. if a==0 else None)
def transitions(old,new):return dict(resolved=sorted(old-new),retained=sorted(old&new),new=sorted(new-old),old_count=len(old),current_count=len(new))
t0=time.time()
assert read(W/'C06_ANALYSIS_PROVENANCE.json')['status']=='LOCAL_ANALYSIS_INPUTS_AUTHENTICATED_BACKUP_STILL_PENDING'
raw=read(N/'raw/vectors/RAW_RECEIPT.json')
assert raw['native_info']['SolCount']>0 and all(v['status']=='SAVED_UNQUALIFIED' for v in raw['vectors'].values())
M=read(B/'bridge/math_problem/MATH_PROBLEM.json')
MAP=read(B/'bridge/mapping/MAPPING_MANIFEST.json')
labels=read(B/'artifacts/mapping/LABELS.json')
VM={r['name']:r for r in labels['variables']}
vlabels=load(B/'bridge/mapping/vlabels.npy')
D,R=[load(B/'bridge/mapping'/f'{k}.npy') for k in ('D','R')]
A={k:load(B/'bridge/math_problem'/v['file']) for k,v in M['arrays'].items()}
z,pi,rc=[load(N/'raw/vectors'/f'{k}.npy') for k in ('X','Pi','RC')]
net=xr.open_dataset(B/'artifacts/daily_365_unsolved.nc')
meta=json.loads(net.attrs['meta'])
external={r['FixedAccountID']:r for r in meta['external_pending_fixed_accounts']}
pattern=read(C4/'C04_RECEIPT_PATTERN.json')
old_class=read(C4/'C04_KKT_COLUMN_CLASSIFICATION.json')
phys={k:read(p/'postprocess/PHYSICAL_CHECKS.json') for k,p in [('C03',B),('C06',N)]}
kkt={k:read(p/'postprocess/KKT.json') for k,p in [('C03',B),('C06',N)]}
xs={k:load(p/'postprocess/original_vectors/X_original.npy') for k,p in [('C03',B),('C06',N)]}
def cols(name,asset):
    b=VM[name];lab=load(B/'artifacts/mapping'/b['labels_file'])
    dim=next(d for d in b['dims'] if d!='snapshot')
    labs=np.take(lab,b['coordinates'][dim].index(asset),axis=b['dims'].index(dim)).ravel()
    ix=np.searchsorted(vlabels,labs);assert np.array_equal(vlabels[ix],labs)
    return ix
accounts=[]
pa={k:{r['asset']:r for r in p['details']['fixed_prefix_checks']} for k,p in phys.items()}
assert set(pa['C03'])==set(pa['C06'])==set(external) and len(external)==807
for asset,a in sorted(external.items()):
    q=float(a['QuantityMWh']);ei,sp,mp=cols('Store-e',asset),cols('Store-p',asset),cols('Link-p',a['Meter'])
    r={'asset':asset,'Q_MWh':q,'final_buses':a['FinalBuses'],'meter':a['Meter']}
    for k in ('C03','C06'):
        receipt=pa[k][asset];b=receipt['energy_budget_mwh'];e=xs[k][ei];p=xs[k][sp];m=xs[k][mp]
        annual=math.fsum(float(v)*24 for v in p)
        assert annual==receipt['annual_release_mwh']
        metrics=dict(annual_release_MWh=annual,annual_signed_error_MWh=annual-q,
          annual_abs_error_MWh=abs(annual-q),annual_overuse_MWh=max(0,annual-q),
          minimum_stock_MWh=float(e.min()),terminal_stock_MWh=float(e[-1]),
          stock_lower_violation_MWh=max(0,-float(e.min())),terminal_abs_MWh=abs(float(e[-1])),
          prefix_max_MWh=receipt['max_prefix_error_mwh'],state_residual_L1_MWh=receipt['gross_state_error_mwh'],
          meter_difference_L1_MWh=receipt['meter_difference_l1_mwh'],
          meter_capacity_excess_MWh=receipt['meter_capacity_excess_mwh'])
        r[k]={'passed':receipt['passed'],'budget_MWh':b,'checks':receipt['draft_checks'],
          'meter_checks':{x:receipt[x] for x in ('meter_equal_release','meter_direction','meter_capacity','zero_Q_meter_zero')},
          'metrics':metrics,'error_over_own_budget':{key:ratio(value,b) for key,value in metrics.items() if key in ('annual_abs_error_MWh','stock_lower_violation_MWh','terminal_abs_MWh','prefix_max_MWh','state_residual_L1_MWh','meter_difference_L1_MWh','meter_capacity_excess_MWh')}}
    accounts.append(r)
ga={k:{r['buses'][0]:r for r in p['details']['fixed_group_obligations_v4']} for k,p in phys.items()}
assert len(ga['C03'])==len(ga['C06'])==385 and set(ga['C03'])==set(ga['C06'])
groups=[]
for g in pattern['groups']:
    r={k:g[k] for k in ('bus','country','sector','account_count','accounts')}
    for k in ('C03','C06'):
        v=ga[k][g['bus']];r[k]=dict(v)
        r[k]['error_over_group_budget']={x:ratio(v[x],v['group_budget_mwh']) for x in ('gross_oversupply_mwh','gross_undersupply_mwh','max_delivery_prefix_error_mwh')}
    groups.append(r)
card=[]
by_asset={r['asset']:r for r in accounts}
for count in (1,2,3,4):
    rows=[r for r in groups if r['account_count']==count]
    members=[by_asset[a] for r in rows for a in r['accounts']]
    card.append(dict(account_count=count,groups=len(rows),accounts=len(members),**{k:{'failed':sum(not r[k]['passed'] for r in rows),'failed_accounts':sum(not r[k]['passed'] for r in members),'resource_positive_overuse_MWh':math.fsum(r[k]['metrics']['annual_overuse_MWh'] for r in members),'gross_oversupply_MWh':math.fsum(r[k]['gross_oversupply_mwh'] for r in rows),'gross_undersupply_MWh':math.fsum(r[k]['gross_undersupply_mwh'] for r in rows)} for k in ('C03','C06')}))
write('C06_ALL_ACCOUNT_AND_GROUP_COMPARISON.json',dict(accounts=accounts,groups=groups,cardinality=card,
 account_failure_sets=transitions({a for a,r in pa['C03'].items() if not r['passed']},{a for a,r in pa['C06'].items() if not r['passed']}),
 group_failure_sets=transitions({a for a,r in ga['C03'].items() if not r['passed']},{a for a,r in ga['C06'].items() if not r['passed']}),
 totals={k:{'failed_accounts':sum(not r[k]['passed'] for r in accounts),'failed_groups':sum(not r[k]['passed'] for r in groups),
 'annual_positive_resource_excess_MWh':math.fsum(r[k]['metrics']['annual_overuse_MWh'] for r in accounts),
 'gross_positive_group_oversupply_MWh':math.fsum(r[k]['gross_oversupply_mwh'] for r in groups),
 'gross_negative_group_undersupply_MWh':math.fsum(r[k]['gross_undersupply_mwh'] for r in groups),
 'maximum_account_error_budget_ratio':max(v for r in accounts for v in r[k]['error_over_own_budget'].values() if v is not None)} for k in ('C03','C06')}))
print('ACCOUNTS_AND_GROUPS_DONE',flush=True)

# Actual current stationarity failure columns; one new daily traversal, no old annual matrix.
n,m=M['num_col'],M['num_row'];starts=A['start'];failed=[];maxnorm=maxabs=0.;nnz=0;s=0
while s<n:
    e=min(n,s+20000)
    if int(starts[e])-int(starts[s])>4_000_000:e=min(e,int(np.searchsorted(starts,int(starts[s])+4_000_000,side='right'))-1)
    assert e>s
    p,q=int(starts[s]),int(starts[e]);counts=np.diff(starts[s:e+1]);rr=A['index'][p:q];av=A['value'][p:q];nnz+=q-p
    ci=np.repeat(np.arange(e-s),counts)
    aty=np.bincount(ci,weights=av*pi[rr],minlength=e-s);ab=np.bincount(ci,weights=np.abs(av*pi[rr]),minlength=e-s)
    residual=(A['cost'][s:e]-aty-rc[s:e])/D[s:e]
    scale=np.maximum(1.,(np.abs(A['cost'][s:e])+ab+np.abs(rc[s:e]))/D[s:e]);norm=np.abs(residual)/scale
    for j in np.flatnonzero(norm>1e-6):failed.append({'column':int(s+j),'residual_original':float(residual[j]),'normalized':float(norm[j])})
    maxnorm=max(maxnorm,float(norm.max(initial=0)));maxabs=max(maxabs,float(np.abs(residual).max(initial=0)));s=e
assert nnz==11403496 and len(failed)==kkt['C06']['stationarity_fail_count']
def desc(indices):
    out={};query=np.asarray(sorted(set(indices)),dtype=int);labs=vlabels[query]
    for b in labels['variables']:
        lab=load(B/'artifacts/mapping'/b['labels_file']);flat=lab.ravel();mask=flat>=0;valid=flat[mask]
        if not len(valid):continue
        use=(labs>=valid.min())&(labs<=valid.max())
        if not use.any():continue
        pos=np.searchsorted(valid,labs[use]);assert np.array_equal(valid[pos],labs[use])
        for c,l,r in zip(query[use],labs[use],np.flatnonzero(mask)[pos]):
            loc=np.unravel_index(r,lab.shape) if lab.shape else ()
            out[int(c)]=dict(label=int(l),family=b['name'],coordinates={d:b['coordinates'][d][i] for d,i in zip(b['dims'],loc)})
    assert len(out)==len(query);return out
ds=desc([r['column'] for r in failed])
for r in failed:r.update(ds[r['column']])
signfail=[]
for kind,length,vec,sc,lo,hi in [('column',n,rc,D,A['col_lower'],A['col_upper']),('row',m,pi,R,A['row_lower'],A['row_upper'])]:
    for s in range(0,length,100000):
        e=min(length,s+100000);v=vec[s:e]/sc[s:e] if kind=='column' else vec[s:e]*sc[s:e]
        error=np.where(~np.isfinite(lo[s:e]),np.maximum(v,0),0)+np.where(~np.isfinite(hi[s:e]),np.maximum(-v,0),0)
        norm=error/np.maximum(1,abs(v))
        for j in np.flatnonzero(norm>1e-6):signfail.append(dict(kind=kind,index=int(s+j),multiplier_original=float(v[j]),normalized_error=float(norm[j]),free=bool(not np.isfinite(lo[s+j]) and not np.isfinite(hi[s+j]))))
assert len(signfail)==kkt['C06']['dual_sign_fail_count']
ds=desc([r['index'] for r in signfail if r['kind']=='column'])
for r in signfail:
    if r['kind']=='column':r.update(ds[r['index']])
stattrans=transitions({r['column'] for r in old_class['failed_columns']},{r['column'] for r in failed})
signtrans=transitions({f"{r['kind']}:{r['index']}" for r in old_class['dual_sign_failures']},{f"{r['kind']}:{r['index']}" for r in signfail})
write('C06_KKT_FAILURE_SET_COMPARISON.json',dict(C03_source_sha256=sha(C4/'C04_KKT_COLUMN_CLASSIFICATION.json'),C06_KKT_source_sha256=sha(N/'postprocess/KKT.json'),
 stationarity_transition=stattrans,sign_transition=signtrans,stationarity_fail_count=len(failed),stationarity_families=dict(collections.Counter(r['family'] for r in failed)),
 failed_columns=failed,dual_sign_failures=signfail,stationarity_normalized_max=maxnorm,stationarity_max_original=maxabs,
 one_daily_CSC_traversal_nnz=nnz,old_annual_matrix_reads=0,production_V4_counts_independently_matched=True))
# Existing complete activity / per-row budget arrays, not another matrix traversal.
act=load(N/'postprocess/kkt/algebra/activity_solver.npy');tol=load(N/'postprocess/kkt/budgets/row_tolerance.npy')
oldact=load(B/'postprocess/kkt/algebra/activity_solver.npy');oldtol=load(B/'postprocess/kkt/budgets/row_tolerance.npy')
clabels=load(B/'bridge/mapping/clabels.npy')
families=[];current_rows=[];old_rows=set()
for f in MAP['row_ranges']:
    s,e=f['start'],f['end'];v=act[s:e]/R[s:e];lo=A['row_lower'][s:e]/R[s:e];hi=A['row_upper'][s:e]/R[s:e]
    viol=np.maximum(0,np.maximum(np.where(np.isfinite(lo),lo-v,0),np.where(np.isfinite(hi),v-hi,0)))
    count=int(np.count_nonzero(viol>tol[s:e]));j=int(np.argmax(viol))
    families.append(dict(family=f['family'],rows=e-s,fail_count=count,max_violation_original=float(viol[j]),max_budget_ratio=float(np.max(viol/tol[s:e],initial=0)),worst_row=s+j))
    for u in np.flatnonzero(viol>tol[s:e]):current_rows.append(dict(row=int(s+u),label=int(clabels[s+u]),family=f['family'],violation_original=float(viol[u]),budget=float(tol[s+u]),budget_ratio=float(viol[u]/tol[s+u]),R=float(R[s+u])))
    oldv=oldact[s:e]/R[s:e]
    oldviol=np.maximum(0,np.maximum(np.where(np.isfinite(lo),lo-oldv,0),np.where(np.isfinite(hi),oldv-hi,0)))
    old_rows.update(int(s+u) for u in np.flatnonzero(oldviol>oldtol[s:e]))
assert sum(f['fail_count'] for f in families)==kkt['C06']['row_fail_count']
assert len(old_rows)==kkt['C03']['row_fail_count']
write('C06_MATRIX_ROW_FAMILY_COMPARISON.json',dict(families=families,all_rows=m,fail_count=len(current_rows),failed_rows=current_rows,
 failure_sets=transitions(old_rows,{r['row'] for r in current_rows}),method='read stored complete C03/C06 activity and unchanged V4 budgets; no repeated A*x',source_sha256=sha(N/'postprocess/KKT.json')))
write('C06_COMPARISON_METHOD_RECEIPT.json',dict(seconds=time.time()-t0,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,account_count=807,group_count=385,
 new_daily_CSC_full_traversals=1,old_annual_matrix_reads=0,solver_imports=0,solver_calls=0,new_model_builds=0,original_files_modified=False))
print('C06_COMPARISON_COMPLETE',len(failed),len(signfail),flush=True)
