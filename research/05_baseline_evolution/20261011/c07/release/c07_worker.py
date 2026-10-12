"""Frozen-CSC-only dispatch. No PyPSA/Linopy construction or matrix conversion."""
from pathlib import Path
import sys,os,time,subprocess,traceback
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'helpers'))
from c02_common import read,write,resources,resource_gate
from production_control import alive,phase_deadline,stop_blocks_stage
from c07_checks import verify_release,verify_inputs

def main(run):
    a=read(run/'AUTHORIZATION.json');write(run/'PHASE.json',{'phase':'BRIDGE','entered_epoch':time.time()});write(run/'WORKER_READY.json',{'pid':os.getpid(),'run_id':a['run_id']})
    start=time.time()
    while not (run/'PROCESS_IDENTITY.json').exists():
        if time.time()-start>10:raise RuntimeError('GUARD_STARTUP_FAILED')
        time.sleep(.05)
    def progress(label):
        if stop_blocks_stage(run,read(run/'PHASE.json')['phase']):raise RuntimeError('PROTECTION_STOP_'+label)
        if not alive(read(run/'GUARD_READY.json')) or time.time()-read(run/'GUARD_HEARTBEAT.json')['epoch']>8:raise RuntimeError('GUARD_NOT_FRESH')
        if time.time()>=phase_deadline(read(run/'PHASE.json'),a):raise TimeoutError('PHASE_DEADLINE_'+label)
        resource_gate(resources(run))
    try:
        verify_release(a['release_manifest_sha256']);verify_inputs(run,progress);progress('NATIVE_HANDOFF')
        subprocess.run([sys.executable,'-B',str(HERE/'c07_native.py'),str(run)],check=True)
        raw=read(run/'raw/vectors/RAW_RECEIPT.json')
        if all(raw['vectors'].get(k,{}).get('status')=='SAVED_UNQUALIFIED' for k in ('X','Pi','RC')):
            write(run/'PHASE.json',{'phase':'POSTPROCESS','entered_epoch':time.time()});progress('POSTPROCESS')
            from daily_acceptance import postprocess
            from c07_expression_runtime import canonicalize
            canonical=canonicalize(run,a,progress)
            postprocess(run,HERE,progress,raw_directory=canonical/'vectors')
        else:write(run/'POSTPROCESS_NOT_RUN.json',{'reason':'NO_COMPLETE_LEGAL_PRIMAL_DUAL','native_status':raw['native_status'],'V4':'NOT_AVAILABLE_NO_SOLUTION','retry':False})
        write(run/'WORKER_EXIT.json',{'run_id':a['run_id'],'status':'NATIVE_RETURNED_RAW_SAVED_AND_POSTPROCESS_DECIDED','epoch':time.time(),'retry':False})
        write(run/'PHASE.json',{'phase':'DONE','entered_epoch':time.time()})
    except BaseException as e:
        write(run/'WORKER_FAILURE.json',{'run_id':a['run_id'],'error':type(e).__name__,'detail':str(e),'traceback':traceback.format_exc(),'epoch':time.time(),'raw_preserved':(run/'raw/RAW_DURABLE.json').exists(),'retry':False})
        write(run/'PHASE.json',{'phase':'FAILED','entered_epoch':time.time()});raise
if __name__=='__main__':main(Path(sys.argv[1]))
