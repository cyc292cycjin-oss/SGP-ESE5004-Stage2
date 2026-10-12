"""No coefficient stream: reuse saved row activities and at most selected CSR rows."""
from pathlib import Path
from fractions import Fraction as F
import numpy as np,xarray as xr,json,collections,math,hashlib
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c04_daily_pattern_20261012')
B=Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run')
def read(p):return json.loads(p.read_text())
def arr(p):return np.load(p,mmap_mode='r')
def ff(x):return F(float(x))
def dump(name,obj):(W/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n')
k=read(W/'C04_KKT_COLUMN_CLASSIFICATION.json');m=read(B/'artifacts/lp/MATH_PROBLEM.json');mapping=read(B/'bridge/mapping/MAPPING_MANIFEST.json');labels=read(B/'artifacts/mapping/LABELS.json')
ends=np.array([r['end'] for r in mapping['row_ranges']]);starts=np.array([r['start'] for r in mapping['row_ranges']])
z=arr(B/'raw/vectors/X.npy');pi=arr(B/'raw/vectors/Pi.npy');D=arr(B/'bridge/mapping/D.npy');R=arr(B/'bridge/mapping/R.npy');xo=arr(B/'postprocess/original_vectors/X_original.npy')
exact=[]
for r in sorted({t['row'] for c in k['exact_representative_columns'] for t in c['terms']}):
    j=int(np.searchsorted(ends,r,side='right'));d=B/'artifacts/lp'/m['chunks'][j]['dir'];i=int(r-starts[j]);ptr=arr(d/'indptr.npy');p,e=map(int,ptr[i:i+2]);ix=arr(d/'indices.npy')[p:e];vs=arr(d/'value_scaled.npy')[p:e];vo=arr(d/'value_original.npy')[p:e]
    act=sum((ff(a)*ff(x) for a,x in zip(vs,z[ix])),F(0));orig=sum((ff(a)*ff(x) for a,x in zip(vo,xo[ix])),F(0));assert act/ff(R[r])==orig
    lo=arr(d/'row_lower_original.npy')[i];hi=arr(d/'row_upper_original.npy')[i];mul=ff(pi[r])*ff(R[r])
    comp=abs(mul*(orig-ff(lo))) if mul>0 and np.isfinite(lo) else abs(mul*(ff(hi)-orig)) if mul<0 and np.isfinite(hi) else F(0)
    exact.append(dict(row=r,family=m['chunks'][j]['family'],support_count=e-p,exact_activity_original=str(orig),exact_multiplier_original=str(mul),exact_complementarity_EUR=str(comp),complementarity_EUR=float(comp),scaled_original_identity=True))
net=xr.open_dataset(B/'artifacts/daily_365_unsolved.nc');byasset=collections.Counter((f['family'],f['coordinates'][f['family'].split('-')[0]]) for f in k['failed_columns'])
assets=[]
for (family,asset),count in sorted(byasset.items()):
    c=family.split('-')[0].lower()+'s';dim=c+'_i'
    item=dict(family=family,asset=asset,failed_columns=count,carrier=str(net[c+'_carrier'].sel({dim:asset}).item()))
    item['ports']={v[len(c)+1:]:str(net[v].sel({dim:asset}).item()) for v in net if v.startswith(c+'_bus')}
    assets.append(item)
cl=arr(B/'bridge/mapping/clabels.npy');rev=np.full(int(max(cl))+1,-1,dtype=np.int32);rev[cl]=np.arange(len(cl),dtype=np.int32)
activity=arr(B/'postprocess/kkt/algebra/activity_solver.npy');lower=arr(B/'bridge/math_problem/row_lower.npy')
bs={}
for b in labels['constraints']:
    if b['name'] in ['Bus-nodal_balance','Bus-meshed-nodal_balance']:
        dim=next(d for d in b['dims'] if d!='snapshot');labs=arr(B/'artifacts/mapping'/b['labels_file'])
        for bus in b['coordinates'][dim]:
            if ' :: final obligation' in bus:
                i=b['coordinates'][dim].index(bus);ls=np.take(labs,i,axis=b['dims'].index(dim)).ravel();bs[bus]=rev[ls]
patterns=[]
for g in read(W/'C04_RECEIPT_PATTERN.json')['groups']:
    ids=bs[g['bus']];res=activity[ids]-lower[ids]
    patterns.append(dict(bus=g['bus'],account_count=g['account_count'],daily_pass=g['daily_pass'],R=float(R[ids[0]]),scaled_residual_min=float(min(res)),scaled_residual_max=float(max(res)),mean_scaled_residual_per_account=float(np.mean(res)/g['account_count'])))
summ=[]
for count in [1,2,3,4]:
    data=[g for g in patterns if g['account_count']==count];v=[g['mean_scaled_residual_per_account'] for g in data]
    summ.append(dict(account_count=count,groups=len(data),min_mean_scaled_residual_per_account=min(v),max_mean_scaled_residual_per_account=max(v)))
dump('C04_TARGETED_CROSSCHECKS.json',dict(exact_complementarity_rows=exact,failed_stationarity_assets=assets,failed_column_D_values=sorted({r['D'] for r in k['failed_columns']}),saved_activity_pattern=summ,groups_saved_activity=patterns,scope='row-activity pattern uses saved V4 intermediate (not independent full matvec); exact complementary rows independently recomputed from CSR',additional_CSC_streams=0))
print(json.dumps(dict(assets=assets,pattern=summ,exact_complementarity_rows=len(exact)),ensure_ascii=False,indent=2))
