"""Install the exact reviewed Research-layer files and run bounded regressions; no solver."""
from pathlib import Path
import json,hashlib,subprocess as sp,os
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
P='/home/jin/miniforge3/envs/pypsa-earth/bin/python'
W=Path(__file__).resolve().parent; S=W/'stage'; E=W/'evidence'
def git(*args):return sp.check_output(['git',*args],cwd=R,text=True).rstrip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
start=json.loads((E/'START.json').read_text())
assert git('rev-parse','HEAD')==start['head'] and git('branch','--show-current')==start['branch']
paths=[p.relative_to(S).as_posix() for p in (S/'research_inputs/assembly_v1').rglob('*') if p.is_file()]
paths+=['scripts_project/check_assembly_inputs.py','tests/research/test_assembly_input_freeze.py','configs/research/baseline.yaml']
dirty=git('status','--porcelain').splitlines()
assert all(line[3:] in paths or line[3:].startswith('research_inputs/assembly_v1/') for line in dirty),dirty
for rel in paths:
 target=R/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((S/rel).read_bytes());target.chmod(0o644)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
receipts=[]
def run(name,args,expected=0):
 p=sp.run([P,*map(str,args)],cwd=R,env=env,stdout=sp.PIPE,stderr=sp.STDOUT)
 (E/(name+'.log')).write_bytes(p.stdout)
 receipts.append(dict(name=name,command=[P,*map(str,args)],exit_code=p.returncode,expected_exit=expected,passed=p.returncode==expected,log_sha256=sha(E/(name+'.log'))))
 (E/'TEST_RECEIPTS.json').write_text(json.dumps(receipts,indent=2)+'\n')
 print(name+': '+str(p.returncode),flush=True)
 if p.returncode!=expected:raise RuntimeError(p.stdout.decode())
run('ASSEMBLY_INPUT_TESTS',['tests/research/test_assembly_input_freeze.py'])
run('ASSEMBLY_PREFLIGHT',['scripts_project/check_assembly_inputs.py','--year',2050,'--output',E/'ASSEMBLY_PREFLIGHT.json'],2)
run('GATE1_STATIC_REGRESSION',['tests/research/test_phase4_static.py'])
run('GATE2_REGRESSION',['tests/research/test_demand_accounting.py'])
run('GATE3_REGRESSION',['scripts_project/run_gate3_validation.py','--output',E/'gate3_regression'])
run('GATE3_CONFIG_REGRESSION',['scripts_project/check_research_carriers.py','--output',E/'GATE3_CONFIG_REGRESSION.json'])
run('TOPOLOGY_REGRESSION',['tests/research/test_topology_integrity.py'])
changed=set(paths)
guards={p:sha(R/p)==h for p,h in start['preservation_hashes'].items() if p not in changed}
assert all(guards.values()),guards
(E/'PRESERVATION_GUARD.json').write_text(json.dumps(dict(files=guards,gate2_original_contract_preserved=True,upstream_prepare_sector_network_unchanged=True,solver_runs=0),indent=2)+'\n')
(E/'IMPLEMENTATION_PATHS.json').write_text(json.dumps(sorted(paths),indent=2)+'\n')
print('All required bounded regressions passed; preflight remains fail-closed; no network or solve.')
