"""Run an explicit argv command with an immutable run identity and failure receipt.

Usage: python run_manifest.py SPEC.json -- executable arg ...
This tool does not choose scenarios, confirm datasets, or infer solver success.
The solver adapter must write the specified metrics JSON after solving.
"""
from pathlib import Path
import datetime as dt
import hashlib, json, math, os, subprocess, sys

def digest(path):
    with open(path,'rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def utc():return dt.datetime.now(dt.timezone.utc).isoformat()

def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()

def run(spec,command):
    directory=Path(spec['run_directory']).resolve()
    directory.mkdir(parents=True,exist_ok=False)  # Never overwrite a prior receipt.
    receipt=directory/'manifest.json'
    m=dict(spec,command=command,start_time=utc(),end_time=None,objective=None,
           solver_status='NOT_STARTED',constraint_residual=None,output_hash=None,status='PREFLIGHT')
    def save():
        tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(m,indent=2),encoding='utf-8');os.replace(tmp,receipt)
    save();rc=1
    try:
        repo=Path(spec['repository']).resolve()
        m['git_commit']=git(repo,'rev-parse','HEAD')
        m['dirty_status']=git(repo,'status','--porcelain')
        if m['dirty_status']:raise ValueError('Model checkout is dirty; commit the reviewed change before a formal run')
        if m['git_commit'] != spec['expected_git_commit']:raise ValueError('Unexpected model SHA')
        if not command:raise ValueError('Missing explicit command argv')
        m['config_files']=[{'path':str(Path(p).resolve()),'sha256':digest(p)} for p in spec['config_files']]
        m['config_hash']=hashlib.sha256(json.dumps(m['config_files'],sort_keys=True).encode()).hexdigest()
        m['input_files']=[{'path':str(Path(p).resolve()),'sha256':digest(p)} for p in spec['input_files']]
        m['input_hashes']={r['path']:r['sha256'] for r in m['input_files']}
        m['environment_file']={'path':spec['environment_file'],'sha256':digest(spec['environment_file'])}
        for p in [*spec['output_files'],spec['metrics_file']]:
            if Path(p).exists():raise ValueError(f'Refusing stale output or metrics file: {p}')
        m['status']='RUNNING';m['solver_status']='UNREPORTED';save()
        with (directory/'command.log').open('w',encoding='utf-8') as log:
            process=subprocess.run(command,cwd=repo,stdout=log,stderr=subprocess.STDOUT,check=False)
        m['returncode']=process.returncode
        for r in m['config_files']+m['input_files']:
            if digest(r['path'])!=r['sha256']:raise ValueError(f'Run changed an input/config: {r["path"]}')
        m['outputs']=[{'path':p,'sha256':digest(p)} for p in spec['output_files'] if Path(p).exists()]
        m['output_hash']={r['path']:r['sha256'] for r in m['outputs']}
        m['dirty_status_end']=git(repo,'status','--porcelain')
        if process.returncode:raise RuntimeError(f'Command returned {process.returncode}')
        if len(m['outputs'])!=len(spec['output_files']):raise RuntimeError('Declared output is missing')
        metrics=json.loads(Path(spec['metrics_file']).read_text(encoding='utf-8'))
        m['metrics_sha256']=digest(spec['metrics_file'])
        for key in ['objective','constraint_residual']:
            if metrics.get(key) is not None and not math.isfinite(float(metrics[key])):
                raise ValueError(f'{key} must be a finite measurement')
        for k in ['objective','solver_status','constraint_residual']:m[k]=metrics.get(k)
        if m['objective'] is None or m['solver_status'] not in ['optimal','ok/optimal']:
            raise ValueError('Command exit is not evidence of an optimal solve; solver metrics missing or nonoptimal')
        if m['constraint_residual'] is None:raise ValueError('Constraint residual has not been measured')
        if not math.isfinite(float(m['objective'])) or not math.isfinite(float(m['constraint_residual'])):
            raise ValueError('Objective/residual must be finite measurements')
        if float(m['constraint_residual']) < 0:raise ValueError('Maximum absolute constraint violation must be nonnegative')
        m['residual_acceptance']='NOT_EVALUATED: apply the documented units and study tolerance'
        if m['dirty_status_end']:raise ValueError('Run changed tracked or unignored model files')
        m['status']='COMPLETED';rc=0
    except BaseException as ex:
        m['status']='FAILED';m['error']=f'{type(ex).__name__}: {ex}'
    finally:
        m['end_time']=utc();save()
    return rc,m

if __name__=='__main__':
    spec=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    command=sys.argv[2:];command=command[1:] if command[:1]==['--'] else command
    rc,result=run(spec,command);print(json.dumps(result,indent=2));sys.exit(rc)
