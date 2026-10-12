"""Bounded independent C04 calculations on backed-up daily data only. No solver imports.
One CSC traversal classifies stationarity; physical calculations use selected CSR rows.
No production acceptance functions are called. All output is new local diagnostic evidence.
"""
from pathlib import Path
from fractions import Fraction as F
import numpy as np, json, math, hashlib, time, resource, collections
import xarray as xr
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c04_daily_pattern_20261012')
B=Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run')
def read(p):return json.loads(p.read_text())
def load(p):return np.load(p,mmap_mode='r',allow_pickle=False)
def write(name,obj):
    (W/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n')
def hashbytes(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def exact(x):return F(float(x))
def numeric(x):return float(x) if np.isfinite(x) else str(float(x))
t0=time.time();assert read(W/'C04_BACKUP_RECEIPT.json')['status']=='LOCAL_BACKUP_SHA_VERIFIED'
M=read(B/'artifacts/lp/MATH_PROBLEM.json');MM=read(B/'bridge/math_problem/MATH_PROBLEM.json');MAP=read(B/'bridge/mapping/MAPPING_MANIFEST.json')
labels=read(B/'artifacts/mapping/LABELS.json');VM={x['name']:x for x in labels['variables']};CM={x['name']:x for x in labels['constraints']}
vlabels=load(B/'bridge/mapping/vlabels.npy');clabels=load(B/'bridge/mapping/clabels.npy')
# Native row order follows exported chunks, not numerical Linopy label order.
row_inverse=np.full(int(np.max(clabels))+1,-1,dtype=np.int32)
row_inverse[clabels]=np.arange(len(clabels),dtype=np.int32)
assert np.count_nonzero(row_inverse>=0)==len(clabels)
D=load(B/'bridge/mapping/D.npy');R=load(B/'bridge/mapping/R.npy')
z,pi,rc=[load(B/'raw/vectors'/f'{k}.npy') for k in ('X','Pi','RC')]
xo=load(B/'postprocess/original_vectors/X_original.npy')
A={k:load(B/'bridge/math_problem'/v['file']) for k,v in MM['arrays'].items()}
savedact=load(B/'postprocess/kkt/algebra/activity_solver.npy');savedrt=load(B/'postprocess/kkt/budgets/row_tolerance.npy')
net=xr.open_dataset(B/'artifacts/daily_365_unsolved.nc');candidate=xr.open_dataset(B/'postprocess/daily_candidate_UNQUALIFIED.nc')
meta=json.loads(net.attrs['meta']);routes=meta['biomass_obligation_routes'];external={x['FixedAccountID']:x for x in meta['external_pending_fixed_accounts']}
pattern=read(W/'C04_RECEIPT_PATTERN.json');groups={g['bus']:g for g in pattern['groups']}
starts=np.array([r['start'] for r in MAP['row_ranges']]);ends=np.array([r['end'] for r in MAP['row_ranges']])
cache={};touched=set();row_details=[]
def series(kind,name,asset=None):
    b=(VM if kind=='variables' else CM)[name];lab=load(B/'artifacts/mapping'/b['labels_file'])
    if asset is not None:
        dim=next(d for d in b['dims'] if d!='snapshot');i=b['coordinates'][dim].index(asset);lab=np.take(lab,i,axis=b['dims'].index(dim))
    return np.asarray(lab).ravel()
def cols(name,asset):
    ls=series('variables',name,asset);ix=np.searchsorted(vlabels,ls);assert np.array_equal(vlabels[ix],ls);return ix
def rows(name,asset=None):
    ls=series('constraints',name,asset);ls=ls[ls>=0];ix=row_inverse[ls];assert np.all(ix>=0) and np.array_equal(clabels[ix],ls);return ix
def desc_cols(indices):
    out={};query=np.asarray(indices,dtype=int);labs=vlabels[query]
    for b in labels['variables']:
        lab=load(B/'artifacts/mapping'/b['labels_file']);flat=lab.ravel();mask=flat>=0;valid=flat[mask]
        if not len(valid):continue
        use=(labs>=valid.min())&(labs<=valid.max())
        if not use.any():continue
        positions=np.searchsorted(valid,labs[use]);assert np.array_equal(valid[positions],labs[use]);ravel=np.flatnonzero(mask)[positions]
        for c,l,pos in zip(query[use],labs[use],ravel):
            loc=np.unravel_index(pos,lab.shape) if lab.shape else ()
            out[int(c)]=dict(column=int(c),label=int(l),family=b['name'],coordinates={d:b['coordinates'][d][i] for d,i in zip(b['dims'],loc)})
    assert len(out)==len(set(indices));return out
def rowdata(row):
    k=int(np.searchsorted(ends,row,side='right'));c=M['chunks'][k];folder=B/'artifacts/lp'/c['dir'];touched.add(c['dir'])
    if k not in cache:cache[k]={s:load(folder/(s+'.npy')) for s in ('indptr','indices','value_original','value_scaled','row_lower_original','row_upper_original','clabels')}
    q=cache[k];i=int(row-starts[k]);assert int(q['clabels'][i])==int(clabels[row]);p,e=map(int,q['indptr'][i:i+2]);ix=q['indices'][p:e]
    return c,q,i,ix,q['value_original'][p:e],q['value_scaled'][p:e]
def rowcalc(row,detailed=False):
    c,q,i,ix,vo,vs=rowdata(row);lo=float(q['row_lower_original'][i]);hi=float(q['row_upper_original'][i])
    act=math.fsum(float(a)*float(x) for a,x in zip(vo,xo[ix]));scaled=math.fsum(float(a)*float(x) for a,x in zip(vs,z[ix]));mag=math.fsum(abs(float(a)*float(x)) for a,x in zip(vo,xo[ix]))
    viol=max(0,lo-act if math.isfinite(lo) else 0,act-hi if math.isfinite(hi) else 0);budget=.001+1e-7*max(abs(lo) if math.isfinite(lo) else 0,abs(hi) if math.isfinite(hi) else 0,mag)
    assert np.array_equal(vs/(R[row]*D[ix]),vo) and np.array_equal(z[ix]*D[ix],xo[ix])
    result=dict(row=int(row),label=int(clabels[row]),family=c['family'],R=float(R[row]),support_count=len(ix),activity_original=act,activity_solver=scaled,lower_original=numeric(lo),upper_original=numeric(hi),violation_original=viol,V4_row_budget=budget,violation_over_budget=viol/budget,scaled_to_original_delta=scaled/R[row]-act,saved_activity_delta=scaled-float(savedact[row]),source_chunk=c['dir'])
    if detailed:
        er=sum((exact(a)*exact(x) for a,x in zip(vo,xo[ix])),F(0));es=sum((exact(a)*exact(x) for a,x in zip(vs,z[ix])),F(0));assert er==es/exact(R[row])
        descriptions=desc_cols(ix.tolist());result.update(exact_activity_original=str(er),exact_activity_solver=str(es),exact_coordinate_identity=True,exact_residual_to_finite_bound=str(er-exact(lo if math.isfinite(lo) else hi)),support=[dict(**descriptions[int(j)],coefficient_original_hex=float(a).hex(),coefficient_scaled_hex=float(b).hex(),D=float(D[j]),z_hex=float(z[j]).hex(),x_original_hex=float(xo[j]).hex(),cost_original=float(A['cost'][j]/D[j]),column_lower=numeric(A['col_lower'][j]*D[j]),column_upper=numeric(A['col_upper'][j]*D[j])) for j,a,b in zip(ix,vo,vs)])
        row_details.append(result)
    return result
def busrows(bus):
    candidates=[]
    for nm in ('Bus-nodal_balance','Bus-meshed-nodal_balance'):
        b=CM[nm];dim=next(d for d in b['dims'] if d!='snapshot')
        if bus in b['coordinates'][dim]:candidates.append(rows(nm,bus))
    assert len(candidates)==1;return candidates[0]

# Scale confounding uses only labels and diagonal arrays, not matrix coefficients.
scale_summary=[]
for bus,g in groups.items():
    br=busrows(bus);eix=cols('Store-e',g['accounts'][0]);vals=np.unique(D[eix]);assert len(vals)==1
    scale_summary.append(dict(bus=bus,country=g['country'],sector=g['sector'],count=g['account_count'],D=float(vals[0]),R_final=float(R[br[0]]),source_D_MWh=g['source_D_MWh'],passed=g['daily_pass']))
strata=collections.defaultdict(lambda:collections.Counter())
for r in scale_summary:strata[(r['D'],r['count'])]['pass' if r['passed'] else 'fail']+=1
write('C04_SCALE_CONFOUNDING.json',dict(groups=scale_summary,D_count_strata=[dict(D=k[0],count=k[1],**v) for k,v in sorted(strata.items())],causation='NOT_IDENTIFIED; no randomization and commodity/subsector differences remain'))
selected=pattern['selected_buses']
# Include the stronger same-country/sector 2-vs3 matched pair as a sensitivity check.
for pair in pattern['selected_pairs'][2:3]:
    selected+= [b for b in [pair['passing_bus'],pair['failing_bus']] if b not in selected]
group_results=[];all_local_rows=set()
for bus in selected:
    g=groups[bus];accounts=[];supply=np.zeros(365);stock=np.zeros(365)
    for asset in g['accounts']:
        rt=routes[asset];meter=external[asset]['Meter'];rb=external[asset]['ResourceBus'];q=float(external[asset]['QuantityMWh'])
        ei,sp,mp=cols('Store-e',asset),cols('Store-p',asset),cols('Link-p',meter)
        e,p,l=xo[ei],xo[sp],xo[mp];assert np.array_equal(z[ei]*D[ei],e)
        for name,vals in [('stores_t_e',e),('stores_t_p',p),('links_t_p0',l)]:
            dim=next(d for d in candidate[name].dims if d!='snapshots');name_asset=asset if name.startswith('stores') else meter
            assert np.array_equal(candidate[name].sel({dim:name_asset}).values,vals)
        supply+=l;stock+=e;rel=math.fsum(float(v)*24 for v in p);step=e-np.r_[q,e[:-1]]+24*p
        families=[('Store-energy_balance',asset),('Store-fix-e-lower',asset),('Store-fix-e-upper',asset),('ResearchStoreDirection-'+asset,None),('Link-ext-p-lower',meter),('Link-ext-p-upper',meter)]
        selected_rows=[]
        for fam,a in families:selected_rows+=rows(fam,a).tolist()
        selected_rows+=busrows(rb).tolist();all_local_rows.update(selected_rows)
        summary=[]
        for fam in sorted({rowdata(r)[0]['family'] for r in selected_rows}):
            candidates=[rowcalc(r) for r in selected_rows if rowdata(r)[0]['family']==fam]
            worst=max(candidates,key=lambda r:r['violation_over_budget']);summary.append(dict(family=fam,rows=len(candidates),failed=sum(r['violation_over_budget']>1 for r in candidates),max_violation=worst['violation_original'],max_budget_ratio=worst['violation_over_budget'],worst_row=worst['row']))
            rowcalc(worst['row'],True)
        rowcalc(rows('Store-energy_balance',asset)[0],True)
        eb=min(.001+1e-7*q,1e-6*q)
        accounts.append(dict(asset=asset,meter=meter,resource_bus=rb,Q=q,D=float(D[ei[0]]),stock_min=float(min(e)),stock_final=float(e[-1]),annual_release=rel,annual_excess=rel-q,account_budget=eb,stock_violation_budget_ratio=max(0,-min(e))/eb,annual_plus_final_minus_Q=math.fsum([rel,float(e[-1]),-q]),max_step_residual=float(max(abs(step))),meter_store_max_difference=float(max(abs(l-p))),row_families=summary))
    br=busrows(bus);all_local_rows.update(br.tolist());bc=[rowcalc(r) for r in br];worst=max(bc,key=lambda r:r['violation_original']);rowcalc(worst['row'],True)
    loadid=next(x['load'] for x in read(B/'artifacts/SCHEME_A_DAILY_EXACT_GROUPS.json')['groups'] if x['load']+' :: final obligation'==bus)
    demand=net['loads_t_p_set'].sel(loads_t_p_set_i=loadid).values
    oversupply=math.fsum(max(0,float(s)-float(d))*24 for s,d in zip(supply,demand));Q=math.fsum(a['Q'] for a in accounts);dd=math.fsum(float(d)*24 for d in demand)
    group_results.append(dict(bus=bus,count=len(accounts),country=g['country'],sector=g['sector'],D_annual=dd,Q_sum=Q,initial_source_slack_exact=str(sum((exact(a['Q']) for a in accounts),F(0))-sum((exact(x)*24 for x in demand),F(0))),gross_oversupply=oversupply,gross_undersupply=math.fsum(max(0,float(d)-float(s))*24 for s,d in zip(supply,demand)),final_stock_sum=float(stock[-1]),oversupply_plus_final_minus_source_slack=math.fsum([oversupply,float(stock[-1]),dd,-Q]),bus_max_original=worst['violation_original'],bus_max_solver=worst['violation_original']*worst['R'],bus_R=worst['R'],bus_budget=worst['V4_row_budget'],accounts=accounts))
write('C04_SELECTED_PHYSICAL_RECOMPUTATION.json',dict(method='independent CSR row support; math.fsum and selected Fraction exact binary64 dot products; xarray direct readback',selected_groups=group_results,rows_read=len(all_local_rows),chunks_touched=len(touched),representative_rows=row_details,full_V4_rerun=False))
print('PHYSICAL_DONE',len(all_local_rows),flush=True)

# The sole streaming traversal of daily CSC coefficients; no old annual matrix read.
fail=[];family_meta=None;normmax=0.;resmax=0.;nnzread=0;comp_samples=[]
n=MM['num_col'];pointers=A['start'];size=20000
def bounded():
    s=0
    while s<n:
        end=min(n,s+size)
        if int(pointers[end])-int(pointers[s])>4_000_000:
            end=min(end,int(np.searchsorted(pointers,int(pointers[s])+4_000_000,side='right'))-1)
        assert end>s
        yield s,end
        s=end
for s,end in bounded():
    p0,p1=int(pointers[s]),int(pointers[end]);counts=np.diff(pointers[s:end+1]);rr=A['index'][p0:p1];aa=A['value'][p0:p1];nnzread+=p1-p0
    assert p1-p0<=4_000_000
    ci=np.repeat(np.arange(end-s),counts);at=np.bincount(ci,weights=aa*pi[rr],minlength=end-s);ab=np.bincount(ci,weights=np.abs(aa*pi[rr]),minlength=end-s)
    residual=(A['cost'][s:end]-at-rc[s:end])/D[s:end];scale=np.maximum(1,(np.abs(A['cost'][s:end])+ab+np.abs(rc[s:end]))/D[s:end]);norm=np.abs(residual)/scale
    for j in np.flatnonzero(norm>1e-6):fail.append(dict(column=int(s+j),residual_original=float(residual[j]),normalization=float(scale[j]),normalized=float(norm[j]),D=float(D[s+j])))
    normmax=max(normmax,float(max(norm)));resmax=max(resmax,float(max(abs(residual))))
assert nnzread==11403496
write('C04_KKT_STREAM_CACHE.json',dict(failed_columns=fail,nnz_streamed=nnzread,stationarity_normalized_max=normmax,stationarity_max_original=resmax))
descriptions=desc_cols([x['column'] for x in fail])
for f in fail:f.update(descriptions[f['column']])
families=collections.Counter(f['family'] for f in fail)
signfail=[]
for kind,length,vec,sc,lo,hi in [('column',n,rc,D,A['col_lower'],A['col_upper']),('row',MM['num_row'],pi,R,A['row_lower'],A['row_upper'])]:
    for s in range(0,length,100000):
        e=min(length,s+100000);v=vec[s:e]/sc[s:e] if kind=='column' else vec[s:e]*sc[s:e]
        err=np.where(~np.isfinite(lo[s:e]),np.maximum(v,0),0)+np.where(~np.isfinite(hi[s:e]),np.maximum(-v,0),0);norm=err/np.maximum(1,abs(v))
        for j in np.flatnonzero(norm>1e-6):signfail.append(dict(kind=kind,index=int(s+j),multiplier_original=float(v[j]),normalized_error=float(norm[j]),scale=float(sc[s+j]),lower=numeric(lo[s+j]),upper=numeric(hi[s+j])))
ds=desc_cols([x['index'] for x in signfail if x['kind']=='column'])
for f in signfail:
    if f['kind']=='column':f.update(ds[f['index']])
    else:f['family']=MAP['row_ranges'][int(np.searchsorted(ends,f['index'],side='right'))]['family']
representatives={max([f for f in fail if f['family']==fam],key=lambda x:x['normalized'])['column'] for fam in families}
for fam in set(f['family'] for f in signfail if f['kind']=='column'):representatives.add(max([f for f in signfail if f['kind']=='column' and f['family']==fam],key=lambda x:x['normalized_error'])['index'])
details=[]
for j in sorted(representatives):
    p,e=map(int,pointers[j:j+2]);rr=A['index'][p:e];aa=A['value'][p:e]
    scaled=exact(A['cost'][j])-sum((exact(a)*exact(pi[r]) for a,r in zip(aa,rr)),F(0))-exact(rc[j]);original=scaled/exact(D[j])
    independent=exact(A['cost'][j])/exact(D[j])-sum((exact(a)/(exact(R[r])*exact(D[j]))*(exact(pi[r])*exact(R[r])) for a,r in zip(aa,rr)),F(0))-exact(rc[j])/exact(D[j]);assert independent==original
    rowterms=[]
    for r,a in zip(rr,aa):
        k=int(np.searchsorted(ends,r,side='right'));lo=A['row_lower'][r];hi=A['row_upper'][r];v=savedact[r];mult=pi[r]
        comp=(abs(float(mult)*float(v-lo)) if mult>0 and np.isfinite(lo) else abs(float(mult)*float(hi-v)) if mult<0 and np.isfinite(hi) else 0)
        rowterms.append(dict(row=int(r),label=int(clabels[r]),family=MAP['row_ranges'][k]['family'],R=float(R[r]),a_solver_hex=float(a).hex(),pi_solver_hex=float(pi[r]).hex(),pi_original=float(pi[r]*R[r]),row_complementarity_EUR=comp))
    details.append(dict(**desc_cols([j])[j],D=float(D[j]),cost_solver=float(A['cost'][j]),RC_solver=float(rc[j]),RC_original=float(rc[j]/D[j]),column_lower=numeric(A['col_lower'][j]),column_upper=numeric(A['col_upper'][j]),exact_stationarity_solver=str(scaled),exact_stationarity_original=str(original),stationarity_original=float(original),coordinate_identity_exact=True,terms=rowterms))
write('C04_KKT_COLUMN_CLASSIFICATION.json',dict(source='one daily CSC stream; no acceptance module called',nnz_streamed=nnzread,stationarity_fail_count=len(fail),stationarity_families=dict(families),stationarity_max_original=resmax,stationarity_normalized_max=normmax,sign_fail_count=len(signfail),sign_families=dict(collections.Counter((f['kind']+':'+f['family']) for f in signfail)),failed_columns=fail,dual_sign_failures=signfail,exact_representative_columns=details))
write('C04_INDEPENDENT_METHOD_RECEIPT.json',dict(finished_epoch=time.time(),seconds=time.time()-t0,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,physical_rows_read=len(all_local_rows),daily_CSC_full_traversals=1,daily_CSC_nnz=nnzread,annual_matrix_reads=0,solver_imports=0,new_model_builds=0,production_acceptance_rerun=False,original_files_modified=False))
print('KKT_DONE',dict(families),len(signfail),flush=True)
