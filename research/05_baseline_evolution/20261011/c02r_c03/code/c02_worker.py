"""Single authorized daily network + Linopy LP build. No solver may be imported."""
import sys,importlib.abc
class NoSolver(importlib.abc.MetaPathFinder):
    forbidden={'gurobipy','highspy','mosek','cplex','xpress','pyscipopt','mindoptpy','coptpy'}
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in self.forbidden:raise ModuleNotFoundError('C02_NO_SOLVER_IMPORT: '+fullname)
sys.meta_path.insert(0,NoSolver())
from pathlib import Path
import time,os,traceback,signal,resource,gc
from c02_common import *

def main(run):
    root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'helpers'));verify_payload(root)
    a=read(run/'BUILD_AUTHORIZATION.json');source=Path(a['source']);stage='START';started=time.time()
    def progress(s):
        nonlocal stage
        stage=s
        if time.time()>a['deadline']-10:raise TimeoutError('fixed deadline closeout margin')
        h=run/'GUARD_ALIVE.json'
        if not h.exists() or time.time()-read(h)['timestamp']>8:raise RuntimeError('guard not fresh')
        resource_gate(resources(run))
        write(run/'STATUS.json',{'phase':s,'timestamp':time.time(),'deadline':a['deadline'],'solver_calls':0,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024})
    def stopped(signum,frame):raise RuntimeError('Controlled termination signal '+str(signum))
    signal.signal(signal.SIGTERM,stopped)
    try:
        while not (run/'GUARD_ALIVE.json').exists():
            if time.time()-started>10:raise RuntimeError('guard startup failed')
            time.sleep(.1)
        progress('INPUT_IDENTITY')
        assert sha(source)==read(root/'INPUT_MANIFEST.json')['network_sha256']
        import pypsa,linopy
        from pypsa.optimization.optimize import OptimizationAccessor
        def forbidden(*args,**kwargs):raise RuntimeError('C02_NO_SOLVE_API')
        OptimizationAccessor.__call__=forbidden;OptimizationAccessor.solve_model=forbidden;linopy.Model.solve=forbidden
        for name in ['to_gurobipy','to_highspy']:
            if hasattr(linopy.Model,name):setattr(linopy.Model,name,forbidden)
        from c02_model import assemble_daily,add_hooks,export_model
        from c02_binding import synthetic_tests,make_binding
        from build_only_extracted import bounded_build_allocator
        out=run/'artifacts';out.mkdir(exist_ok=False)
        n,ledger=assemble_daily(source,root,out,progress)
        progress('ONE_LINOPY_BUILD')
        build_start=time.time()
        # Default frozen create_model call, same no-solve graph; allocator wrapper changes no equations.
        with bounded_build_allocator():n.optimize.create_model();add_hooks(n)
        progress('MODEL_BUILT')
        built=time.time();record=export_model(n,root,out,progress);del n;gc.collect()
        binding=make_binding(root,out,record);syn=synthetic_tests(root,out/'synthetic_checks')
        progress('STATIC_READBACK_COMPLETE')
        files=[]
        for p in sorted(out.rglob('*')):
            if p.is_file():
                with p.open('rb') as f:os.fsync(f.fileno())
                files.append({'path':str(p.relative_to(run)),'bytes':p.stat().st_size,'sha256':sha(p)})
        write(run/'ARTIFACT_SHA_INDEX.json',{'files':files,'cloud_originals_preserved':True,'local_sync':'PENDING','solution_vectors':'NOT_AVAILABLE_NO_SOLVE'})
        write(run/'BUILD_RESULT.json',{'status':'C02_BUILD_STATIC_ACCEPTED_NO_SOLVE','run':run.name,'actual_complete_builds':1,'rows':record['rows'],'columns':record['columns'],'nnz':record['nnz'],
           'network_and_LP_readback':'PASS','build_seconds':built-build_start,'worker_seconds':time.time()-started,'peak_worker_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
           'final_resources':resources(run),'solver_calls':0,'Gurobi_WLS_environment_started':False,'real_V4_acceptance':'NOT_RUN_NO_SOLUTION','C03_authorized':False,
           'deadline':a['deadline'],'artifact_index_sha256':sha(run/'ARTIFACT_SHA_INDEX.json'),'G6_05':'PAUSED_BY_USER'})
    except BaseException as e:
        write(run/'BUILD_RESULT.json',{'status':'C02_BLOCKED_WITH_SPECIFIC_EVIDENCE','stage':stage,'error':type(e).__name__,'detail':str(e),'traceback':traceback.format_exc(),
          'time':time.time(),'deadline':a['deadline'],'solver_calls':0,'automatic_retry':False,'partial_files_preserved':True});raise
if __name__=='__main__':main(Path(sys.argv[1]))
