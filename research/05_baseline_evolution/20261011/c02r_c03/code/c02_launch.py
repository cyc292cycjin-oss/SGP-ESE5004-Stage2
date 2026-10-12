"""One build-only window. Run only in the user-confirmed 122 Jupyter terminal."""
from pathlib import Path
import argparse,os,sys,time,uuid,subprocess,platform
from c02_common import *

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--instance-id',type=int,required=True)
    ap.add_argument('--confirmed-hostname',required=True);ap.add_argument('--network',type=Path)
    a=ap.parse_args();root=Path(__file__).resolve().parent;manifest=verify_payload(root);c=read(root/'INPUT_MANIFEST.json')
    assert a.instance_id==122 and a.confirmed_hostname==platform.node(),'not confirmed 122 host'
    project=Path('/root/autodl-tmp/SGP').resolve(strict=True)
    assert root.resolve().is_relative_to(project/'incoming'),'entry must be in independent incoming directory'
    assert platform.python_version()==c['python_version'] and versions()==c['runtime_versions'],'dependency drift; do not install'
    assert Path(sys.executable).resolve()==Path(c['python']).resolve(),'Python path mismatch'
    source=(a.network or Path(c['default_network'])).resolve(strict=True)
    assert source.is_relative_to(project) and source.is_file(),'source outside SGP or not regular'
    assert sha(source)==c['network_sha256'],'frozen network SHA mismatch'
    r=resources(project);resource_gate(r,True)
    # Persistent one-shot claim is outside incoming, so copying the upload cannot clear it.
    claimdir=project/'c02_claims';claimdir.mkdir(exist_ok=True)
    claim=claimdir/('C02_'+manifest['build_id']+'.json')
    t0=time.time();run=project/'runs'/('c02_daily_build_'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime(t0))+'_'+uuid.uuid4().hex[:8])
    with claim.open('x') as f:
        json.dump({'run':str(run),'t0':t0,'deadline':t0+1800,'build_only':True,'optimize_authorized':False},f);f.flush();os.fsync(f.fileno())
    run.mkdir(parents=True,exist_ok=False)
    auth=dict(run=str(run),source=str(source),t0=t0,deadline=t0+1800,root=str(root),instance_id=122,hostname=platform.node(),
       payload_manifest_sha256=sha(root/'PAYLOAD_MANIFEST.json'),input_manifest_sha256=sha(root/'INPUT_MANIFEST.json'),claim=str(claim),initial_resources=r,
       phases='INPUT -> DAILY_NETWORK -> ONE_LINOPY_BUILD -> STREAM_EXPORT -> STATIC_READBACK; no optimizer',full_build_calls_max=1,solver_calls_allowed=0)
    write(run/'BUILD_AUTHORIZATION.json',auth)
    log=(run/'supervisor.log').open('xb')
    p=subprocess.Popen([sys.executable,'-B',str(root/'c02_supervise.py'),str(run)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
    write(run/'DETACHED_LAUNCH.json',{'supervisor':identity(p.pid),'run':str(run),'deadline':auth['deadline'],'browser_independent':True})
    print(str(run));print('No solve. Read STATUS.json, BUILD_RESULT.json and guard/supervisor receipts in this run.')
if __name__=='__main__':main()
