"""D-1 single 2920 network + Linopy LP build from the frozen Gate6 3h NetCDF (derived from c02r_build.py). Solver firewall retained."""
import sys,importlib.abc
class NoSolver(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in {'gurobipy','highspy','mosek','cplex','xpress','pyscipopt','mindoptpy','coptpy'}:raise ModuleNotFoundError('D1_NO_SOLVER_IMPORT:'+fullname)
sys.meta_path.insert(0,NoSolver())
from pathlib import Path
import time,os,traceback,signal,resource,gc
from c02_common import *
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'helpers'))
def main(run):
    a=read(run/'AUTHORIZATION.json');started=time.time();stage='START';T=a.get('test_snapshots') or 2920
    def progress(s):
        nonlocal stage;stage=s
        if time.time()>=min(started+a['build_phase_seconds'],a['build_absolute_deadline_epoch'])-5:raise TimeoutError('BUILD_FIXED_DEADLINE')
        if (run/'STOP_REQUEST.json').exists():raise RuntimeError('BUILD_STOP_REQUEST')
        if time.time()-read(run/'GUARD_HEARTBEAT.json')['epoch']>8:raise RuntimeError('GUARD_NOT_FRESH')
        resource_gate(resources(run));write(run/'BUILD_STATUS.json',{'phase':s,'epoch':time.time(),'solver_calls':0,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024})
    def stop(s,f):raise RuntimeError('BUILD_NORMAL_TERMINATION')
    signal.signal(signal.SIGTERM,stop)
    try:
        source=Path(a['source_network']);assert sha(source)==a['source_network_sha256']
        out=run/'artifacts';out.mkdir(exist_ok=False)
        import pypsa,linopy
        from pypsa.optimization.optimize import OptimizationAccessor
        def no(*args,**kwargs):raise RuntimeError('D1_NO_SOLVE_API')
        OptimizationAccessor.__call__=no;OptimizationAccessor.solve_model=no;linopy.Model.solve=no
        for name in ['to_gurobipy','to_highspy']:
            if hasattr(linopy.Model,name):setattr(linopy.Model,name,no)
        from d1_model import assemble_2920,add_hooks,export_model
        from d1_binding import make_binding
        from build_only_extracted import bounded_build_allocator
        progress('ASSEMBLE_2920');n=assemble_2920(source,HERE,out,progress)
        # T is 2920 for every cloud authorization; only the local interface harness may wrap assemble_2920 with a shorter horizon.
        assert len(n.snapshots)==T and n.meta['solver_allowed'] is False
        for k in ('objective','generators','stores'):assert (n.snapshot_weightings[k]==3).all()
        progress('ONE_LINOPY_BUILD');begin=time.time()
        with bounded_build_allocator():n.optimize.create_model();add_hooks(n)
        built=time.time();progress('MODEL_BUILT');record=export_model(n,HERE,out,progress);del n;gc.collect()
        make_binding(HERE,out,record,expected_snapshots=T);progress('STATIC_READBACK_COMPLETE')
        write(run/'BUILD_RESULT.json',{'status':'D1_BUILD_STATIC_ACCEPTED_NO_SOLVE','run_id':a['run_id'],'snapshots':T,'rows':record['rows'],'columns':record['columns'],'nnz':record['nnz'],'builds':1,'build_seconds':built-begin,'worker_seconds':time.time()-started,'solver_calls':0,'time_aggregation':'NONE','peak_worker_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'G6_05':'PAUSED_BY_USER'})
    except BaseException as e:
        write(run/'BUILD_RESULT.json',{'status':'D1_BLOCKED_WITH_SPECIFIC_EVIDENCE','run_id':a['run_id'],'stage':stage,'error':type(e).__name__,'detail':str(e)[:20000],'traceback':traceback.format_exc()[-20000:],'solver_calls':0,'automatic_retry':False,'epoch':time.time()});raise
if __name__=='__main__':main(Path(sys.argv[1]))
