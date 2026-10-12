"""Small post-return cloud slice, while the separate full archive reception proceeds."""
import json
from local_control import W,remote,save
run=json.loads((W/'A_LAUNCH_RECEIPT.json').read_text())['run']
code=r'''from pathlib import Path
from fractions import Fraction as F
import json,math,hashlib,numpy as np
p=Path(RUN);base=p/'bridge';read=lambda q:json.loads(q.read_text());load=lambda q:np.load(q,mmap_mode='r')
M=read(base/'math_problem/MATH_PROBLEM.json');MAP=read(base/'mapping/MAPPING_MANIFEST.json');L=read(p/'artifacts/mapping/LABELS.json');LP=read(p/'artifacts/lp/MATH_PROBLEM.json')
A={k:load(base/'math_problem'/r['file']) for k,r in M['arrays'].items()};D=load(base/'mapping/D.npy');R=load(base/'mapping/R.npy');vl=load(base/'mapping/vlabels.npy');rn=load(p/'expression/R_exponent.npy');dn=load(p/'expression/D_exponent.npy')
X=load(p/'postprocess/original_vectors/X_original.npy');z=load(p/'raw/vectors/X.npy');pi=load(p/'raw/vectors/Pi.npy');rc=load(p/'raw/vectors/RC.npy')
def desc(c):
 label=int(vl[c])
 for b in L['variables']:
  lab=load(p/'artifacts/mapping'/b['labels_file']);where=np.argwhere(lab==label)
  if len(where):return {'family':b['name'],'label':label,'coordinates':{d:b['coordinates'][d][int(i)] for d,i in zip(b['dims'],where[0])}}
 raise ValueError('no label')
activity=load(p/'postprocess/kkt/algebra/activity_solver.npy');tol=load(p/'postprocess/kkt/budgets/row_tolerance.npy');records=[]
for j,b in enumerate(MAP['row_ranges']):
 if b['family'] not in ('Store-fix-e-lower','Store-ext-e-lower'):continue
 s,e=b['start'],b['end'];v=activity[s:e]/R[s:e];lo=A['row_lower'][s:e]/R[s:e];bad=np.flatnonzero(lo-v>tol[s:e])
 for off in bad:
  row=int(s+off);ch=LP['chunks'][j];fold=p/'artifacts/lp'/ch['dir'];ptr=load(fold/'indptr.npy');u,w=map(int,ptr[off:off+2]);ix=load(fold/'indices.npy')[u:w];coef=load(fold/'value_original.npy')[u:w]
  exact=sum((F(float(a))*F(float(X[c])) for c,a in zip(ix,coef)),F(0));records.append({'row':row,'family':b['family'],'bound_original':float(lo[off]),'activity_exact':str(exact),'violation':float(F(float(lo[off]))-exact),'budget':float(tol[row]),'R_old':float(R[row]),'R_new':math.ldexp(1,int(rn[row])),'support':[dict(column=int(c),coefficient_hex=float(a).hex(),**desc(c)) for c,a in zip(ix,coef)]})
free=~np.isfinite(A['col_lower'])&~np.isfinite(A['col_upper']);origrc=np.ldexp(rc,-dn.astype(np.int32));badfree=free&(abs(origrc)/np.maximum(1,abs(origrc))>1e-6);col=int(np.argmax(np.where(free,abs(origrc),-1)))
sample={'column':col,**desc(col),'D_old':float(D[col]),'D_new':math.ldexp(1,int(dn[col])),'native_RC':float(rc[col]),'original_RC':float(origrc[col]),'free_RC_fail_count':int(badfree.sum()),'exact_mapping':str(F(float(rc[col]))/F(math.ldexp(1,int(dn[col]))))}
out={'run_id':p.name,'failed_Store_rows':records,'worst_free_RC':sample,'full_archive_status':'TRANSFER_IN_PROGRESS_NOT_COMPLETE','read_only':True,'solver_calls':0,'matrix_rebuilds':0,'historical_annual_matrix_reads':0}
print(json.dumps(out))'''.replace('RUN',repr(run))
x=remote(code,90);save('A_TARGETED_EARLY_CHECK.json',x);print(json.dumps(x,indent=2))
