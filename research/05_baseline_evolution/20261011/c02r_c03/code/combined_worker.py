"""Sequential dispatch only. Build firewall and native worker live in distinct processes."""
from pathlib import Path
import sys,time,os,subprocess,traceback
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'helpers'))
from c02_common import read,write,resource_gate,resources
from production_control import alive
def main(run):
    a=read(run/'AUTHORIZATION.json');write(run/'PHASE.json',{'phase':'BUILD','entered_epoch':time.time()});write(run/'WORKER_READY.json',{'pid':os.getpid(),'run_id':a['run_id']})
    start=time.time()
    while not (run/'PROCESS_IDENTITY.json').exists():
        if time.time()-start>10:raise RuntimeError('GUARD_STARTUP_FAILED')
        time.sleep(.05)
    assert alive(read(run/'GUARD_READY.json'))
    def progress(s):
        if (run/'STOP_REQUEST.json').exists():raise RuntimeError('STOP_BEFORE_'+s)
        if not alive(read(run/'GUARD_READY.json')) or time.time()-read(run/'GUARD_HEARTBEAT.json')['epoch']>8:raise RuntimeError('GUARD_NOT_FRESH')
        stage=read(run/'PHASE.json')
        from production_control import phase_deadline
        if time.time()>=phase_deadline(stage,a):raise TimeoutError('PHASE_DEADLINE_'+s)
        resource_gate(resources(run))
    try:
        write(run/'PHASE.json',{'phase':'BUILD','entered_epoch':time.time()});progress('BUILD')
        subprocess.run([sys.executable,'-B',str(HERE/'c02r_build.py'),str(run)],check=True)
        assert read(run/'BUILD_RESULT.json')['status']=='C02_BUILD_STATIC_ACCEPTED_NO_SOLVE'
        write(run/'PHASE.json',{'phase':'BRIDGE','entered_epoch':time.time()});progress('BRIDGE')
        from daily_bridge import bridge
        bridge(run/'artifacts',run/'bridge',progress)
        progress('NATIVE_HANDOFF')
        subprocess.run([sys.executable,'-B',str(HERE/'c03_native.py'),str(run)],check=True)
        raw=read(run/'raw/vectors/RAW_RECEIPT.json')
        if all(raw['vectors'][k]['status']=='SAVED_UNQUALIFIED' for k in ('X','Pi','RC')):
            write(run/'PHASE.json',{'phase':'POSTPROCESS','entered_epoch':time.time()});progress('POSTPROCESS')
            from daily_acceptance import postprocess
            postprocess(run,HERE,progress)
        else:write(run/'POSTPROCESS_NOT_RUN.json',{'reason':'NO_COMPLETE_LEGAL_PRIMAL_DUAL','native_status':raw['native_status'],'V4':'NOT_AVAILABLE_NO_SOLUTION','retry':False})
        write(run/'WORKER_EXIT.json',{'run_id':a['run_id'],'status':'NATIVE_RETURNED_RAW_SAVED_AND_POSTPROCESS_DECIDED','epoch':time.time(),'retry':False})
        write(run/'PHASE.json',{'phase':'DONE','entered_epoch':time.time()})
    except BaseException as e:
        write(run/'WORKER_FAILURE.json',{'run_id':a['run_id'],'error':type(e).__name__,'detail':str(e),'traceback':traceback.format_exc(),'epoch':time.time(),'raw_preserved':(run/'raw/RAW_DURABLE.json').exists(),'retry':False})
        write(run/'PHASE.json',{'phase':'FAILED','entered_epoch':time.time()});raise
if __name__=='__main__':main(Path(sys.argv[1]))
