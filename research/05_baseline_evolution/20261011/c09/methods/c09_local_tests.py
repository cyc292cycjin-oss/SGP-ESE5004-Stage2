"""Local (no solver) tests of the C09 release against the real frozen C03 CSC copy."""
import sys, json, copy, numpy as np, tempfile, shutil, time
REL='/tmp/claude-0/-home-claude/44092b67-2a1c-5b05-b74b-55808728284f/scratchpad/c08/c09/release'
sys.path.insert(0,REL); sys.path.insert(0,REL+'/helpers')
from adapter import open_problem, validate, load_candidate, exact_readback
from c09_decompose import load_block, verify_block, main_problem, merge
from c09_checks import parameter_diff
from v4_algebra_extracted import complete_kkt
B='/mnt/user-data/uploads/ResearchWorkspaces/ASEAN/outputs/'
MP=B+'c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run/bridge/'
V=B+'c07_daily_diagnostic/c07a_daily122_20261012T162928Z_0d9301f2/cloud_run/canonical_raw_for_V4/vectors/'
T={}
def check(name,fn):
    t=time.time()
    try: r=fn(); T[name]={'status':'PASS','detail':r,'seconds':round(time.time()-t,2)}
    except Exception as e: T[name]={'status':'FAIL','error':f'{type(e).__name__}: {e}'}
    print(name,T[name]['status'],T[name].get('detail',T[name].get('error')))
meta,a=open_problem(MP+'math_problem',verify=True)
rec,cols,rows,xb=load_block()
check('T01_block_verify_real_csc',lambda: verify_block(meta,a,cols,rows,xb))
def neg(mut):
    a2=dict(a); cols2,rows2,xb2=cols,rows,xb
    a2,cols2,rows2,xb2=mut(a2,cols2,rows2,xb2)
    try: verify_block(meta,a2,cols2,rows2,xb2)
    except ValueError as e: return 'REJECTED: '+str(e)[:80]
    raise AssertionError('tampering not detected')
def t_cost(a2,c,r,x):
    cc=np.array(a2['cost']); cc[c[5]]=1.0; a2['cost']=cc; return a2,c,r,x
def t_primal(a2,c,r,x):
    x=x.copy(); x[1000]+=1e-3; return a2,c,r,x
def t_cross(a2,c,r,x):
    idx=np.array(a2['index']); j=c[0]; idx[int(a2['start'][j])]=0 if 0 not in set(r[:5]) else 1; a2['index']=idx; return a2,c,r,x
def t_rowset(a2,c,r,x):
    return a2,c,r[1:],x
check('T02_negative_nonzero_block_cost',lambda: neg(t_cost))
check('T03_negative_perturbed_block_primal',lambda: neg(t_primal))
check('T04_negative_cross_entry',lambda: neg(t_cross))
def t04b():
    try: verify_block(meta,a,cols,rows[1:],xb)
    except (ValueError,Exception) as e: return 'REJECTED: '+type(e).__name__
    raise AssertionError('row set tamper not detected')
check('T05_negative_row_set',t04b)
mmeta,marr,mc,mr,ident=main_problem(meta,a,cols,rows)
def t06():
    v=validate(mmeta,marr); assert (mmeta['num_col'],mmeta['num_row'],mmeta['nnz'])==(1565533,3839021,7868836); return v
check('T06_main_problem_validate_dims',t06)
def t07():
    # every main entry equals the source entry bitwise (restriction only)
    st=np.asarray(a['start']); idx=np.asarray(a['index']); val=np.asarray(a['value'])
    rowmap=np.full(meta['num_row'],-1); rowmap[mr]=np.arange(len(mr))
    for j_new in np.random.default_rng(0).choice(len(mc),20000,replace=False):
        j=mc[j_new]; p,q=st[j],st[j+1]; P,Q=marr['start'][j_new],marr['start'][j_new+1]
        assert np.array_equal(rowmap[idx[p:q]],marr['index'][P:Q]) and np.array_equal(val[p:q].view('u8'),marr['value'][P:Q].view('u8'))
    for k,src,sel in [('cost','cost',mc),('col_lower','col_lower',mc),('col_upper','col_upper',mc),('row_lower','row_lower',mr),('row_upper','row_upper',mr)]:
        assert np.array_equal(np.asarray(a[src])[sel].view('u8'),marr[k].view('u8'))
    assert mmeta['offset']==meta['offset']; return 'bitwise restriction on 20000 sampled columns + all cost/bounds'
check('T07_main_restriction_bitwise',t07)
class Fake:
    def create(self,off): self.off=off; self.rs=[];self.rh=[];self.cols=[]
    def rows(self,s,r): self.rs.append(s.copy()); self.rh.append(r.copy())
    def update(self): pass
    def columns(self,beg,ids,vals,obj,lb,ub): self.cols.append((beg.copy(),ids.copy(),vals.copy(),obj.copy(),lb.copy(),ub.copy()))
    def _cat(self):
        if not hasattr(self,'S'):
            self.S=np.concatenate(self.rs);self.H=np.concatenate(self.rh)
            self.O=np.concatenate([c[3] for c in self.cols]);self.L=np.concatenate([c[4] for c in self.cols]);self.U=np.concatenate([c[5] for c in self.cols])
            st=[0];ids=[];vals=[]
            for beg,i,v,*_ in self.cols:
                base=st[-1]; st.extend((base+np.append(beg[1:],len(i))).tolist()); ids.append(i); vals.append(v)
            self.ST=np.array(st);self.I=np.concatenate(ids);self.V=np.concatenate(vals)
    def scalar(self,attr,kind):
        self._cat(); return {'NumVars':len(self.O),'NumConstrs':len(self.H),'ModelSense':1,'ObjCon':self.off}[attr]
    def array(self,attr,s,n,dtype='<f8'):
        self._cat()
        if attr=='VType': return np.full(n,b'C',dtype='S1')
        return {'Obj':self.O,'LB':self.L,'UB':self.U,'Sense':self.S,'RHS':self.H}[attr][s:s+n]
    def matrix_columns(self,s,n):
        self._cat(); p,q=self.ST[s],self.ST[s+n]; return (self.ST[s:s+n]-p).astype(np.int32),self.I[p:q],self.V[p:q]
def t08():
    f=Fake(); load_candidate(f,mmeta,marr); return exact_readback(f,mmeta,marr)
check('T08_load_and_exact_readback_fake_backend',t08)
def t09():
    base=json.load(open(REL+'/C06_EFFECTIVE_MODEL_PARAMETERS.json'))
    ok=parameter_diff(base,dict(base,Crossover=-1)); assert ok['status']=='PASS'
    bad=parameter_diff(base,dict(base,Crossover=-1,NumericFocus=3)); assert bad['status']=='FAIL'
    bad2=parameter_diff(base,dict(base)); assert bad2['status']=='FAIL'
    return {'authorized':ok['differences'],'rejects_extra_change':bad['unauthorized'],'rejects_missing_crossover':bad2['unauthorized']}
check('T09_parameter_gate',t09)
def t10():
    # merge with C07A main-part vectors (dry run) -> unchanged V4 algebra
    z0,p0,r0=[np.load(V+k+'.npy') for k in ('X','Pi','RC')]
    d=tempfile.mkdtemp(); raw=d+'/raw'; import os; os.makedirs(raw)
    import hashlib
    rec={'vectors':{}}
    for k,v in [('X',z0[mc]),('Pi',p0[mr]),('RC',r0[mc])]:
        np.save(raw+f'/{k}.npy',v); rec['vectors'][k]={'status':'SAVED_UNQUALIFIED','sha256':hashlib.sha256(open(raw+f'/{k}.npy','rb').read()).hexdigest()}
    json.dump(rec,open(raw+'/RAW_RECEIPT.json','w'))
    out=merge(raw,d+'/merged',meta,cols,rows,xb,mc,mr,2)
    z,pi,rc=[np.load(d+f'/merged/vectors/{k}.npy') for k in ('X','Pi','RC')]
    D=np.load(MP+'mapping/D.npy');R=np.load(MP+'mapping/R.npy')
    k=complete_kkt(meta,a,z,pi,rc,D,R,d+'/kkt',json.load(open(REL+'/V4_APPROVED.json')))
    shutil.rmtree(d)
    r={x:k[x] for x in ['row_fail_count','column_fail_count','stationarity_fail_count','dual_sign_fail_count','relative_gap','independent_kkt_pass']}
    assert r['row_fail_count']==0 and r['dual_sign_fail_count']==0 and r['stationarity_fail_count']==3353
    return r
check('T10_merge_plus_unchanged_V4_dryrun',t10)
status='PASS' if all(v['status']=='PASS' for v in T.values()) else 'FAIL'
json.dump({'status':status,'tests':T,'solver_calls':0,'note':'run in Claude cloud workspace on SHA-verified read-only copies of the frozen C03 CSC'},open(REL+'/C09_LOCAL_TESTS.json','w'),indent=1,default=str)
print('OVERALL',status)
