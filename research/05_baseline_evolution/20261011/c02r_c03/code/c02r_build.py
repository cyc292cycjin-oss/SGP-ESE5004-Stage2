"""Single daily build from sealed daily NetCDF. Firewall is retained."""
import sys,importlib.abc
class NoSolver(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in {'gurobipy','highspy','mosek','cplex','xpress','pyscipopt','mindoptpy','coptpy'}:raise ModuleNotFoundError('C02_NO_SOLVER_IMPORT:'+fullname)
sys.meta_path.insert(0,NoSolver())
from pathlib import Path
import time,os,traceback,signal,resource,gc,shutil
from c02_common import *
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'helpers'))
def main(run):
    a=read(run/'AUTHORIZATION.json');started=time.time();stage='START'
    def progress(s):
        nonlocal stage;stage=s
        if time.time()>=min(started+1800,a['build_absolute_deadline_epoch'])-5:raise TimeoutError('BUILD_FIXED_DEADLINE')
        if (run/'STOP_REQUEST.json').exists():raise RuntimeError('BUILD_STOP_REQUEST')
        if time.time()-read(run/'GUARD_HEARTBEAT.json')['epoch']>8:raise RuntimeError('GUARD_NOT_FRESH')
        resource_gate(resources(run));write(run/'BUILD_STATUS.json',{'phase':s,'epoch':time.time(),'solver_calls':0})
    def stop(s,f):raise RuntimeError('BUILD_NORMAL_TERMINATION')
    signal.signal(signal.SIGTERM,stop)
    try:
        source=Path(a['daily_source']);assert sha(source)==a['daily_source_sha256']
        out=run/'artifacts';out.mkdir(exist_ok=False);os.link(source,out/'daily_365_unsolved.nc')
        for name,expected in a['reused_build_evidence'].items():
            p=source.parent/name;assert sha(p)==expected;shutil.copyfile(p,out/name)
        import pypsa,linopy
        from pypsa.optimization.optimize import OptimizationAccessor
        def no(*args,**kwargs):raise RuntimeError('C02_NO_SOLVE_API')
        OptimizationAccessor.__call__=no;OptimizationAccessor.solve_model=no;linopy.Model.solve=no
        for name in ['to_gurobipy','to_highspy']:
            if hasattr(linopy.Model,name):setattr(linopy.Model,name,no)
        from c02_model import add_hooks,export_model
        from c02_binding import make_binding
        from build_only_extracted import bounded_build_allocator
        n=pypsa.Network(out/'daily_365_unsolved.nc');assert len(n.snapshots)==365 and n.meta['solver_allowed'] is False
        for k in ('objective','generators','stores'):assert (n.snapshot_weightings[k]==24).all()
        progress('ONE_LINOPY_BUILD');begin=time.time()
        with bounded_build_allocator():n.optimize.create_model();add_hooks(n)
        built=time.time();progress('MODEL_BUILT');record=export_model(n,HERE,out,progress);del n;gc.collect()
        make_binding(HERE,out,record);progress('STATIC_READBACK_COMPLETE')
        write(run/'BUILD_RESULT.json',{'status':'C02_BUILD_STATIC_ACCEPTED_NO_SOLVE','run_id':a['run_id'],'rows':record['rows'],'columns':record['columns'],'nnz':record['nnz'],'builds':1,'build_seconds':built-begin,'worker_seconds':time.time()-started,'solver_calls':0,'reaggregations':0,'daily_source_reused':True,'peak_worker_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'G6_05':'PAUSED_BY_USER'})
    except BaseException as e:
        write(run/'BUILD_RESULT.json',{'status':'C02_BLOCKED_WITH_SPECIFIC_EVIDENCE','run_id':a['run_id'],'stage':stage,'error':type(e).__name__,'detail':str(e),'traceback':traceback.format_exc(),'solver_calls':0,'automatic_retry':False,'epoch':time.time()});raise
if __name__=='__main__':main(Path(sys.argv[1]))
