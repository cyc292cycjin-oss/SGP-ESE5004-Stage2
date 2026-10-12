"""Tiny no-solve fixtures for new storage/label/semantic handoff only."""
from pathlib import Path
import sys,json,hashlib,tempfile,ast,shutil
import numpy as np
from scipy.sparse import csr_matrix
W=Path(__file__).resolve().parent;R=W/'release';sys.path[:0]=[str(R),str(R/'helpers')]
from c02_common import read,write,sha
from c02_zero_rows import APPROVED,certify_values
from c02_semantics import rhs_exact,bounds_exact,SemanticCheckError
from daily_bridge import bridge
from adapter import open_problem,load_candidate,exact_readback,native_bounds
from scatter import scatter_active
from c02_binding import synthetic_tests
from daily_acceptance import require_contract
from production_control import phase_deadline
out=Path(tempfile.mkdtemp(prefix='interface_tests_',dir=W));passed=[]
def check(name,f,exception=None):
    try:f()
    except Exception as e:
        if exception is None or not isinstance(e,exception):raise
    else:
        if exception:raise AssertionError('negative test accepted '+name)
    passed.append(name)
for fam,(_,_,_,h,n) in APPROVED.items():
    ids=[str(k) for k in range(n)];a=np.full(n,np.inf);l=np.full(n,-1);s=np.full(n,'<=')
    def call(a=a,l=l,s=s):return certify_values(fam,a,l,s,np.inf,h,ids,ids)
    check(fam+'_positive',call)
    for v in [0.,1.,np.nan,-np.inf]:
        bad=a.copy();bad[0]=v;check(fam+'_reject_'+str(v),lambda:call(a=bad),ValueError)
    bad=l.copy();bad[0]=0;check(fam+'_active_label_rejected',lambda:call(l=bad),ValueError)
check('unknown_zero_family_rejected',lambda:certify_values('Store-fix-e-lower',a,l,s,np.inf,h,ids,ids),ValueError)
ctx=dict(actual_signs=np.array(['=']),expected_sign='=',asset_id='SYNTHETIC',family='Store-energy_balance',row_labels=np.array([3]),report_path=None)
check('signed_zero_semantics_pass',lambda:rhs_exact(np.array([-0.]),np.array([0.]),**ctx))
check('nonzero_ULP_rejected',lambda:rhs_exact(np.array([np.nextafter(1.,2.)]),np.array([1.]),**ctx),SemanticCheckError)
for bad in [np.nan,np.inf,-np.inf]:check('nonfinite_rhs_rejected_'+str(bad),lambda:rhs_exact(np.array([bad]),np.array([0.]),**ctx),SemanticCheckError)
check('wrong_shape_rejected',lambda:rhs_exact(np.array([0.,0.]),np.array([0.]),**ctx),SemanticCheckError)
check('wrong_direction_rejected',lambda:rhs_exact(np.array([0.]),np.array([0.]),**dict(ctx,actual_signs=np.array(['<=']))),SemanticCheckError)
src=out/'source';(src/'lp').mkdir(parents=True);(src/'mapping').mkdir()
write(src/'mapping/LABELS.json',{'variables':[],'constraints':[]})
A=csr_matrix(np.array([[2.,-4.,0.],[0.,.5,1.],[3.,0.,-2.]]));D=np.array([2.,1.,4.]);rr=np.array([.5,2.,1.])
files={}
for key,a in {'D':D,'vlabels':np.array([2,4,8],dtype=np.int64),'cost_V3_scaled':np.array([2.,-3.,0.]),'cost_scientific_scaled':np.array([1.,-2.,0.]),'col_lower_scaled':np.array([-np.inf,0.,2.]),'col_upper_scaled':np.array([np.inf,np.inf,2.])}.items():
    p=src/'lp'/(key+'.npy');np.save(p,a);files[key]={'file':p.name,'sha256':sha(p)}
chunks=[]
for idx,(s,e) in enumerate([(0,2),(2,3)]):
    p=src/'lp'/('chunk_%05d'%idx);p.mkdir();M=A[s:e];entries={}
    vals={'clabels':np.array([12,10,15])[s:e],'indptr':M.indptr,'indices':M.indices,'value_scaled':M.data,'R':rr[s:e],'row_lower_scaled':np.array([1.,-np.inf,0.])[s:e],'row_upper_scaled':np.array([1.,3.,np.inf])[s:e]}
    for k,v in vals.items():np.save(p/(k+'.npy'),v);entries[k]={'sha256':sha(p/(k+'.npy'))}
    chunks.append({'dir':p.name,'rows':e-s,'nnz':M.nnz,'family':'TEST','arrays':entries})
write(src/'lp/MATH_PROBLEM.json',{'version':'C02_DAILY_CHUNKED_CSR_LP','status':'EXACT_NUMPY_EXPORT_READBACK_PASS','sense':'min','rows':3,'columns':3,'nnz':A.nnz,'arrays':files,'chunks':chunks,'V3_offset':-7.25,'scientific_offset':-3.,'label_manifest_sha256':sha(src/'mapping/LABELS.json'),'network_sha256':'SYNTHETIC'})
rec=bridge(src,out/'bridge');assert rec['status']=='EXACT_CSR_CSC_REVERSE_PERMUTATION_PASS';passed.append('CSR_CSC_exact_inverse_nonmonotonic_row_labels')
meta,arrays=open_problem(out/'bridge/math_problem')
assert np.array_equal(np.load(out/'bridge/mapping/clabels.npy'),[12,10,15]);passed.append('row_permutation_and_dual_scale_identity')
assert np.array_equal(np.load(out/'bridge/mapping/R.npy'),rr) and np.array_equal(np.load(out/'bridge/mapping/D.npy'),D)
class Fake:
    def create(self,offset):self.offset=offset;self.cols=[];self.s=[];self.r=[]
    def rows(self,s,r):self.s.extend(s);self.r.extend(r)
    def update(self):pass
    def columns(self,beg,ids,vals,obj,lb,ub):
        for j in range(len(beg)):
            p=beg[j];q=beg[j+1] if j+1<len(beg) else len(vals)
            self.cols.append((ids[p:q].copy(),vals[p:q].copy(),obj[j],lb[j],ub[j]))
    def scalar(self,k,t):return {'NumVars':len(self.cols),'NumConstrs':len(self.r),'ModelSense':1,'ObjCon':self.offset,'NumNZs':sum(len(x[0]) for x in self.cols)}[k]
    def array(self,k,s,n,dtype='<f8'):
        if k=='Sense':return np.array(self.s[s:s+n],dtype='S1')
        if k=='RHS':return np.array(self.r[s:s+n])
        if k=='VType':return np.full(n,b'C',dtype='S1')
        return np.array([c[{'Obj':2,'LB':3,'UB':4}[k]] for c in self.cols[s:s+n]])
    def matrix_columns(self,s,n):
        c=self.cols[s:s+n];beg=np.cumsum([0]+[len(x[0]) for x in c[:-1]])
        return beg,np.concatenate([x[0] for x in c]),np.concatenate([x[1] for x in c])
b=Fake();load_candidate(b,meta,arrays);exact_readback(b,meta,arrays);passed.append('legacy_native_adapter_full_readback_with_mock_no_Gurobi')
check('native_readback_wrong_offset_rejected',lambda:exact_readback(b,dict(meta,offset=-7.),arrays),ValueError)
check('finite_infinity_sentinel_rejected',lambda:native_bounds(np.array([1e20])),ValueError)
labels=np.array([[8,2,-1],[4,8,2]]);values=np.array([10.,20.,30.]);result=scatter_active(labels,np.array([2,4,8]),values)
assert np.array_equal(result,[[30.,10.,0.],[20.,30.,10.]]);passed.append('actual_label_scatter_mask_and_order')
check('unknown_variable_label_rejected',lambda:scatter_active(np.array([3]),np.array([2,4,8]),values),ValueError)
syn=synthetic_tests(R,out/'V4');passed.extend(syn['checks']);require_contract(read(R/'V4_APPROVED.json'))
a={'build_absolute_deadline_epoch':1800,'load_absolute_deadline_epoch':2700,'native_absolute_deadline_epoch':6300,'raw_absolute_deadline_epoch':6750,'post_absolute_deadline_epoch':7950}
for ph,entry,wanted in [('BUILD',0,1800),('BRIDGE',100,1000),('NATIVE',200,3800),('RAW_SAVE',450,750),('POSTPROCESS',600,1800)]:assert phase_deadline({'phase':ph,'entered_epoch':entry},a)==wanted
passed.append('each_stage_cannot_borrow_early_time_or_exceed_cumulative_deadline')
for p in R.rglob('*.py'):ast.parse(p.read_text())
assert (R/'c03_native.py').read_text().count('code=int(lib.GRBoptimize(backend.model))')==1
assert 'NoSolver' in (R/'c02r_build.py').read_text();passed.append('separate_build_firewall_single_native_call_site')
receipt={'status':'PASS','checks':passed,'count':len(passed),'synthetic_only':True,'PyPSA_model_builds':0,'native_model_creations':0,'optimizer_calls':0,'real_daily_V4_pass':False,'fixture_directory':str(out)}
write(W/'LOCAL_INTERFACE_TESTS.json',receipt);shutil.copyfile(W/'LOCAL_INTERFACE_TESTS.json',R/'LOCAL_INTERFACE_TESTS.json');print(json.dumps(receipt,indent=2))
