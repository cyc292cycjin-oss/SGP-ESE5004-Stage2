"""Daily native worker. Sole optimize call site, only after full same-model readback."""
from pathlib import Path
import ctypes as C,os,sys,time,threading,traceback,math
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'helpers'))
from c02_common import read,write,sha
from adapter import CBackend,open_problem,load_candidate,exact_readback,ranges
from license_binding import bind_license,safe_error_category

def stage(run,phase):write(run/'PHASE.json',{'phase':phase,'entered_epoch':time.time()})
def bind(lib):
    p,i,d,s=C.c_void_p,C.c_int,C.c_double,C.c_char_p
    for name,args,ret in [('GRBemptyenv',[C.POINTER(p)],i),('GRBstartenv',[p],i),('GRBfreeenv',[p],None),('GRBgetenv',[p],p),('GRBsetintparam',[p,s,i],i),('GRBsetdblparam',[p,s,d],i),('GRBgetintparam',[p,s,C.POINTER(i)],i),('GRBgetdblparam',[p,s,C.POINTER(d)],i),('GRBsetstrparam',[p,s,s],i),('GRBgeterrormsg',[p],s),('GRBoptimize',[p],i),('GRBterminate',[p],None)]:
        f=getattr(lib,name);f.argtypes=args;f.restype=ret
def ok(v):
    if v:raise RuntimeError('NATIVE_API_RETURN_CODE_'+str(v))
def parameters(lib,env,expected,types,limit,apply=False):
    explicit=['Method','Crossover','Threads','BarConvTol','Seed','AggFill','PreDual','GURO_PAR_BARDENSETHRESH','NumericFocus','FeasibilityTol','OptimalityTol','Presolve','Aggregate','ScaleFlag','ObjScale','DualReductions','BarHomogeneous','InfUnbdInfo','SoftMemLimit','TimeLimit','LogToConsole','OutputFlag']
    target=dict(expected,TimeLimit=limit,SoftMemLimit=65.,LogToConsole=0,OutputFlag=1)
    def typ(k):return 'int' if k=='GURO_PAR_BARDENSETHRESH' else types[k]['type']
    if apply:
        for k in explicit:ok((lib.GRBsetdblparam if typ(k)=='double' else lib.GRBsetintparam)(env,k.encode(),target[k]))
    actual={}
    for k,want in target.items():
        value=C.c_double() if typ(k)=='double' else C.c_int()
        ok((lib.GRBgetdblparam if typ(k)=='double' else lib.GRBgetintparam)(env,k.encode(),C.byref(value)))
        actual[k]=value.value
        if k!='TSPort' and value.value!=want:raise ValueError('PARAMETER_MISMATCH_'+k)
    return actual

def raw_save(b,meta,run,authorization,call):
    root=run/'raw';root.mkdir(exist_ok=False);folder=root/'vectors';folder.mkdir()
    status=b.scalar('Status',int)
    receipt={'run_id':authorization['run_id'],'source_model_manifest_sha256':sha(run/'bridge/math_problem/MATH_PROBLEM.json'),'expression_sha256':authorization['expression_sha256'],'native_coordinate_space':'C07_NEW_D_R','native_status':status,'qualification':'UNQUALIFIED','native_returned':True,'collected_epoch':time.time(),'GRBoptimize_return_code':call['native_return_code']}
    write(root/'NATIVE_RETURN.json',receipt)
    result=dict(receipt,native_info={},vectors={})
    for k,kind in [('SolCount',int),('BarIterCount',int),('IterCount',float),('Runtime',float),('ObjVal',float),('BoundVio',float),('ConstrVio',float),('DualVio',float),('MaxVio',float),('ComplVio',float)]:
        try:
            v=b.scalar(k,kind);result['native_info'][k]=v if math.isfinite(v) else {'status':'NONFINITE'}
        except Exception as e:result['native_info'][k]={'status':'NOT_AVAILABLE','error':str(e)}
    write(folder/'RAW_RECEIPT.json',result)
    if not isinstance(result['native_info'].get('SolCount'),int) or result['native_info']['SolCount']<=0:
        result['vectors']={k:{'status':'NOT_AVAILABLE','reason':'NO_LEGAL_SOLUTION_COUNT'} for k in ('X','Pi','RC')}
        write(folder/'RAW_RECEIPT.json',result)
        write(root/'RAW_DURABLE.json',{'run_id':authorization['run_id'],'receipt_sha256':sha(folder/'RAW_RECEIPT.json'),'complete':False,'native_state_preserved':True,'qualification':'UNQUALIFIED'})
        return result
    for name,count in [('X',meta['num_col']),('Pi',meta['num_row']),('RC',meta['num_col'])]:
        try:
            # Query availability before allocating a complete output vector.
            first=b.array(name,0,min(1,count));assert np.isfinite(first).all()
            p=folder/(name+'.partial.npy');out=np.lib.format.open_memmap(p,mode='w+',dtype='<f8',shape=(count,))
            for s,e in ranges(count):
                if time.time()>=authorization['raw_absolute_deadline_epoch']:raise TimeoutError('RAW_ABSOLUTE_DEADLINE')
                got=b.array(name,s,e-s)
                if not np.isfinite(got).all():raise ValueError('NONFINITE_RETURNED_VECTOR')
                out[s:e]=got
            out.flush();del out
            with p.open('rb') as f:os.fsync(f.fileno())
            final=folder/(name+'.npy');os.rename(p,final)
            result['vectors'][name]={'status':'SAVED_UNQUALIFIED','count':count,'bytes':final.stat().st_size,'sha256':sha(final)}
        except Exception as e:result['vectors'][name]={'status':'NOT_AVAILABLE_OR_INCOMPLETE','error':str(e),'partial_not_valid':True}
        write(folder/'RAW_RECEIPT.json',result)
    write(root/'RAW_DURABLE.json',{'run_id':authorization['run_id'],'receipt_sha256':sha(folder/'RAW_RECEIPT.json'),'complete':all(x['status']=='SAVED_UNQUALIFIED' for x in result['vectors'].values()),'native_state_preserved':True,'qualification':'UNQUALIFIED'})
    return result

def main(run):
    a=read(run/'AUTHORIZATION.json');lib=None;env=C.c_void_p();backend=None;entered=False
    try:
        assert a['scope']=='C07_V4_RELIABILITY_SINGLE_DAILY_DIAGNOSTIC' and a['maximum_native_seconds']==3600
        assert read(run/'BUILD_RESULT.json')['status']=='C02_BUILD_STATIC_ACCEPTED_NO_SOLVE'
        assert read(run/'bridge/BRIDGE_RECEIPT.json')['status']=='EXACT_CSR_CSC_REVERSE_PERMUTATION_PASS'
        assert read(HERE/'LOCAL_INTERFACE_TESTS.json')['status']=='PASS'
        dll=Path(a['library_path']);assert sha(dll)==a['library_sha256']
        bind_license();lib=C.CDLL(str(dll));bind(lib)
        lib.GRBversion.argtypes=[C.POINTER(C.c_int)]*3;lib.GRBversion.restype=None
        vv=[C.c_int() for _ in range(3)];lib.GRBversion(*[C.byref(x) for x in vv]);assert [x.value for x in vv]==[12,0,3]
        write(run/'NATIVE_VERSION.json',{'version':[x.value for x in vv],'library_sha256':sha(dll)})
        ok(lib.GRBemptyenv(C.byref(env)))
        ok(lib.GRBsetintparam(env,b'OutputFlag',0));rc=int(lib.GRBstartenv(env))
        license_receipt={'path_bound':True,'native_return_code':rc,'started':rc==0,'run_id':a['run_id']}
        if rc:license_receipt['safe_categories']=safe_error_category(lib.GRBgeterrormsg(env))
        write(run/'WLS_ENVIRONMENT.json',license_receipt);ok(rc)
        expected=dict(read(HERE/'C06_EFFECTIVE_MODEL_PARAMETERS.json'),Crossover=0 if a['variant']=='A' else -1);types=read(HERE/'NATIVE_PARAMETER_EVIDENCE.json')['parameters']
        # Bind memory before loading any matrix; console disabled before enabling log.
        ok(lib.GRBsetintparam(env,b'LogToConsole',0));parameters(lib,env,expected,types,3600.,apply=True)
        meta,arrays=open_problem(run/'bridge/math_problem',verify=True)
        from c07_expression_runtime import expression_arrays
        meta,arrays=expression_arrays(run,meta,arrays)
        backend=CBackend(lib,env);loadstart=time.time();load_candidate(backend,meta,arrays)
        transfer=exact_readback(backend,meta,arrays);modelenv=lib.GRBgetenv(backend.model)
        current=read(run/'PHASE.json');assert current['phase']=='BRIDGE'
        if time.time()>=min(current['entered_epoch']+900,a['load_absolute_deadline_epoch']):raise TimeoutError('NATIVE_HANDOFF_DEADLINE')
        limit=min(3600.,a['native_absolute_deadline_epoch']-time.time());assert limit>0
        effective=parameters(lib,modelenv,expected,types,limit,apply=True)
        ok(lib.GRBsetstrparam(modelenv,b'LogFile',str(run/'gurobi.log').encode()))
        transfer.update(expression_sha256=a['expression_sha256'],input_space='C07_NEW_D_R',run_id=a['run_id'],load_and_readback_seconds=time.time()-loadstart,model_manifest_sha256=sha(run/'bridge/math_problem/MATH_PROBLEM.json'),native_model_handle=str(backend.model.value),optimizer_calls_so_far=0)
        write(run/'NATIVE_TRANSFER.json',transfer);write(run/'EFFECTIVE_MODEL_PARAMETERS.json',effective)
        from c07_checks import parameter_diff
        diff=parameter_diff(read(HERE/'C06_EFFECTIVE_MODEL_PARAMETERS.json'),effective,a['variant'])
        write(run/'C07_PARAMETER_DIFF.json',diff);assert diff['status']=='PASS'
        write(run/'C07_EXECUTION_METADATA.json',{'run_id':a['run_id'],'variant':a['variant'],'source_model_manifest_sha256':transfer['model_manifest_sha256'],'expression_sha256':a['expression_sha256'],'model_handle':str(backend.model.value),'ModelSense':backend.scalar('ModelSense',int),'ObjCon':backend.scalar('ObjCon',float),'old_candidate_warm_start':False})
        from c02_common import resource_gate,resources
        resource_gate(resources(run))
        if (run/'STOP_REQUEST.json').exists():raise RuntimeError('PROTECTION_STOP_BEFORE_OPTIMIZE')
        from production_control import alive
        assert alive(read(run/'GUARD_READY.json')) and time.time()-read(run/'GUARD_HEARTBEAT.json')['epoch']<8
        claim=Path(a['optimize_claim']);claim.parent.mkdir(exist_ok=True)
        marker={'run_id':a['run_id'],'authorization_sha256':sha(run/'AUTHORIZATION.json'),'model_manifest_sha256':transfer['model_manifest_sha256'],'parameters_sha256':sha(run/'EFFECTIVE_MODEL_PARAMETERS.json'),'epoch':time.time(),'attempt_limit':1}
        with claim.open('x') as f:
            import json;json.dump(marker,f);f.flush();os.fsync(f.fileno())
        stage(run,'NATIVE');native_start=time.time();native_deadline=min(native_start+limit,a['native_absolute_deadline_epoch']);done=threading.Event()
        def terminate_monitor():
            while not done.wait(.1):
                if (run/'STOP_REQUEST.json').exists() or time.time()>=native_deadline:
                    lib.GRBterminate(backend.model);return
        t=threading.Thread(target=terminate_monitor);t.start()
        write(run/'C07_NATIVE_OPTIMIZE_ENTERED.json',dict(marker,native_deadline=native_deadline,actual_time_limit=limit,model_handle=str(backend.model.value),call_site='c07_native.main:lib.GRBoptimize(backend.model)'))
        entered=True
        try:code=int(lib.GRBoptimize(backend.model)) # THE ONLY OPTIMIZE CALL SITE
        finally:done.set();t.join(timeout=5)
        call={'run_id':a['run_id'],'native_return_code':code,'optimization_calls':1,'returned_utc_epoch':time.time(),'wall_seconds':time.time()-native_start,'model_manifest_sha256':transfer['model_manifest_sha256']}
        write(run/'NATIVE_CALL_EXIT.json',call);stage(run,'RAW_SAVE');raw_save(backend,meta,run,a,call)
        write(run/'NATIVE_WORKER_EXIT.json',{'run_id':a['run_id'],'status':'RETURNED_RAW_CAPTURE_ATTEMPTED','optimize_calls':1,'epoch':time.time()})
    except BaseException as e:
        write(run/'NATIVE_WORKER_FAILURE.json',{'run_id':a['run_id'],'error_type':type(e).__name__,'detail':str(e),'traceback':traceback.format_exc(),'optimize_entered':entered,'retry':False});raise
    finally:
        if backend is not None:backend.close()
        if env.value and lib is not None:lib.GRBfreeenv(env)
if __name__=='__main__':main(Path(sys.argv[1]))
