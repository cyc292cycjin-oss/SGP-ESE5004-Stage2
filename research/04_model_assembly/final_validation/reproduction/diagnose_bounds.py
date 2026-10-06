"""Analytical interval propagation, no optimization/relaxation solve."""
from pathlib import Path
import sys,json,time
import numpy as np
import pypsa
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');sys.path.insert(0,str(R/'scripts_project'))
from assembly_components import install_research_constraint_hooks
E=Path('/mnt/c/Users/20122/Documents/ChatGPT/ASEAN/work/phase4_final_validation/evidence')
n=pypsa.Network(R/'results_project/validation/gate5_20261006_01/research_2050_gate5_24h_validation_input.nc');n.optimize.create_model();install_research_constraint_hooks(n);m=n.model
size=max(int(v.labels.max()) for _,v in m.variables.items())+1
lo=np.full(size,-np.inf);hi=np.full(size,np.inf);lop=np.full(size,-1,dtype=np.int64);hip=lop.copy();row_names={}
for name,v in m.variables.items():
 ids=v.labels.values.ravel();valid=ids>=0;lo[ids[valid]]=v.lower.values.ravel()[valid];hi[ids[valid]]=v.upper.values.ravel()[valid]
prepared=[]
for name,c in m.constraints.items():
 ids=c.vars.values;coef=c.coeffs.values;lab=c.labels.values;active=lab>=0
 ids=np.where(ids>=0,ids,size);coef=np.where(np.isfinite(coef)&(ids<size),coef,0)
 prepared.append((name,c,ids,coef,active))
lo=np.r_[lo,0.];hi=np.r_[hi,0.]
history=[];found=[];start=time.monotonic()
for iteration in range(20):
 changed=0
 for name,c,ids,a,active in prepared:
  lower=lo[ids];upper=hi[ids];vmin=np.where(a==0,0,a*np.where(a>0,lower,upper));vmax=np.where(a==0,0,a*np.where(a>0,upper,lower))
  minimum=vmin.sum(axis=-1);maximum=vmax.sum(axis=-1);rhs=c.rhs.values;sign=c.sign.values
  bad=active&(((sign!='>=')&(minimum>rhs+1e-5))|((sign!='<=')&(maximum<rhs-1e-5)))
  if bad.any():
   for flat in np.flatnonzero(bad.ravel())[:5]:
    idx=np.unravel_index(flat,bad.shape);row=c.labels.values[idx];vs=ids[idx];aa=a[idx]
    terms=[dict(variable=int(k),coefficient=float(b),lower=float(lo[k]),upper=float(hi[k]),lower_from_row=int(lop[k]),upper_from_row=int(hip[k])) for k,b in zip(vs,aa) if b and k<size]
    found.append(dict(constraint=name,label=int(row),coordinates={dim:str(c.labels.coords[dim].values[z]) for dim,z in zip(c.labels.dims,idx)},minimum=float(minimum[idx]),maximum=float(maximum[idx]),rhs=float(rhs[idx]),sign=str(sign[idx]),terms=terms))
   break
  # Derive variable bounds using the other terms' tightest known intervals.
  for sense,values in [('upper',vmin),('lower',vmax)]:
   eligible=(sign!='>=') if sense=='upper' else (sign!='<=')
   infin=~np.isfinite(values);count=infin.sum(axis=-1,keepdims=True);finite=np.where(infin,0,values);other=finite.sum(axis=-1,keepdims=True)-finite
   ok=active[...,None]&eligible[...,None]&(a!=0)&((count-infin)==0)
   bound=np.divide(rhs[...,None]-other,a,out=np.zeros_like(a),where=a!=0)
   target_lower=ok&((a<0) if sense=='upper' else (a>0));target_upper=ok&~target_lower
   row_labels=np.broadcast_to(c.labels.values[...,None],a.shape)
   for lower_side,mask in [(True,target_lower),(False,target_upper)]:
    kk=ids[mask];bb=bound[mask];rr=row_labels[mask]
    old=lo[kk] if lower_side else hi[kk];improved=(bb>old+1e-8) if lower_side else (bb<old-1e-8)
    if not improved.any():continue
    kk,bb,rr=kk[improved],bb[improved],rr[improved];changed+=len(kk)
    if lower_side:np.maximum.at(lo,kk,bb);same=bb==lo[kk];lop[kk[same]]=rr[same]
    else:np.minimum.at(hi,kk,bb);same=bb==hi[kk];hip[kk[same]]=rr[same]
  conflict=np.flatnonzero(lo[:size]>hi[:size]+1e-5)
  if len(conflict):
   found=[dict(variable=int(k),lower=float(lo[k]),upper=float(hi[k]),lower_from_row=int(lop[k]),upper_from_row=int(hip[k])) for k in conflict[:5]];break
 history.append(dict(iteration=iteration,updates=changed,elapsed_seconds=time.monotonic()-start));print(history[-1],flush=True)
 if found or changed==0 or time.monotonic()-start>180:break
# Resolve all referenced bound rows to source expressions without another model.
proofs={};needed=set()
for f in found:
 for t in f.get('terms',[f]):needed.update(t.get(k,-1) for k in ['lower_from_row','upper_from_row'])
needed.discard(-1)
for name,c,_,_,_ in prepared:
 for row in needed:
  where=np.argwhere(c.labels.values==row)
  if len(where):
   idx=tuple(where[0]);sel={dim:c.labels.coords[dim].values[z] for dim,z in zip(c.labels.dims,idx)};proofs[str(row)]=str(c.sel(sel))
result=dict(method='Analytical interval propagation on unchanged model; no solve and no modified constraints',found=found,bound_source_expressions=proofs,history=history)
(E/'BOUND_PROPAGATION_DIAGNOSIS.json').write_text(json.dumps(result,indent=2,default=str)+'\n');print(json.dumps(result,indent=2,default=str)[-20000:])
