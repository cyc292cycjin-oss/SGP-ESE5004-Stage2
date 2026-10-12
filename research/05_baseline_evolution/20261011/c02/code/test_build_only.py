"""Small arithmetic/serialization tests only; no PyPSA network, no solver."""
from pathlib import Path
import sys,ast,json,time,hashlib,uuid,subprocess
ROOT=Path(__file__).parent;P=ROOT/'payload';sys.path[:0]=[str(P),str(P/'helpers')]
# Install the same import firewall before importing Linopy/any optional solver.
import c02_worker
import numpy as np
from c02_common import write,sha,resource_gate,GIB,identity,same_identity
from c02_model import average,canonical_rows,bits
from c02_binding import synthetic_tests
from fractions import Fraction as F

def main():
    out=ROOT/('local_checks_'+uuid.uuid4().hex[:8]);out.mkdir()
    checks=[]
    a=np.full(2920,1.25);bits(average(a),np.full(365,1.25));checks.append('flat_binary64_identity')
    a=np.tile(np.array([1.,1.+2**-52,1.,1.,1.,1.,1.,1.]),365)
    d=average(a);bits(d,np.ones(365));checks.append('exact_Fraction_mean_nearest_no_compensation')
    exact=sum((F(float(x)) for x in a[:8]),F(0))/8
    assert F(float(d[0]))!=exact;checks.append('rounding_not_mislabeled_exact')
    synthetic=synthetic_tests(P,out/'v4')
    import linopy,pandas as pd
    assert not any(k in sys.modules for k in c02_worker.NoSolver.forbidden)
    m=linopy.Model();x=m.add_variables(lower=[-np.inf,0.,-2.],upper=[np.inf,3.,4.],coords=[pd.Index(['a','b','c'],name='asset')],name='x')
    m.add_constraints(x.sum()==2.,name='sum');m.add_constraints(2*x>=-1.,name='lower');m.add_objective(x.sum())
    vl=m.variables.flat.labels.to_numpy(dtype=int);vm=np.full(m.shape[1],-1,dtype=np.int32);vm[vl]=np.arange(len(vl))
    rows=list(canonical_rows(m,vm,lambda s:None));assert sum(len(x[1]) for x in rows)==4 and sum(x[2].nnz for x in rows)==6
    for i,(name,labels,a,lower,upper) in enumerate(rows):
        for k,v in [('labels',labels),('start',a.indptr),('indices',a.indices),('value',a.data),('lo',lower),('hi',upper)]:
            path=out/(str(i)+'_'+k+'.npy');np.save(path,v);bits(np.load(path),v)
    checks.append('tiny_Linopy_continuous_free_bounds_mixed_rows_canonical_export_roundtrip')
    # No call expression may enter a solver. The one create_model is explicitly allowed.
    forbidden={'solve','solve_model','presolve','optimize','IIS','feasRelax','GRBoptimize','GRBloadenv','GRBstartenv'}
    for path in P.glob('c02_*.py'):
        tree=ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Call):
                name=node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id if isinstance(node.func,ast.Name) else ''
                assert name not in forbidden,(path.name,name,node.lineno)
    checks.append('no_solver_call_AST_and_optional_solver_import_firewall')
    valid={'effective_memory_limit':90*GIB,'effective_cpu_cores':4,'memory_headroom':13*GIB,'host_available':20*GIB,'disk_free':25*GIB}
    resource_gate(valid,True)
    for key,value in [('effective_memory_limit',89*GIB),('effective_cpu_cores',3.9),('memory_headroom',11*GIB),('disk_free',19*GIB)]:
        try:resource_gate(dict(valid,**{key:value}),True)
        except RuntimeError:checks.append('admission_reject_'+key)
        else:raise AssertionError(key+' boundary bypassed')
    from c02_supervise import stop_target
    dummy=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],start_new_session=True)
    try:
        i=identity(dummy.pid);assert same_identity(i);bad=dict(i,ctime=i['ctime']-1)
        assert not same_identity(bad) and stop_target(bad,time.time()+1)['signals']==[]
        result_stop=stop_target(i,time.time()+4);dummy.wait(timeout=5);assert result_stop['identity_confirmed'] and dummy.returncode!=0
        checks.append('owned_dummy_identity_mismatch_rejected_and_verified_TERM_exit')
    finally:
        if dummy.poll() is None:dummy.terminate();dummy.wait(timeout=5)
    result={'status':'PASS_LOCAL_NO_SOLVE_TESTS','checks':checks,'V4_synthetic':synthetic,'full_network_builds':0,'full_LP_builds':0,'tiny_linopy_fixture_builds':1,'solver_calls':0,'native_model_calls':0,
      'cloud_execution':False,'code_sha256':{p.name:sha(p) for p in P.glob('c02_*.py')},'output':str(out)}
    write(ROOT/'LOCAL_NO_SOLVE_TESTS.json',result);print(json.dumps(result))
if __name__=='__main__':main()
