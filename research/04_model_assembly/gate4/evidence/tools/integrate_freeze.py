from pathlib import Path
import subprocess as sp,json,hashlib,os,yaml
W=Path(__file__).resolve().parent;S=W/'stage';E=W/'evidence';R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');P='/home/jin/miniforge3/envs/pypsa-earth/bin/python'
def git(*a):return sp.check_output(['git',*a],cwd=R,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert git('rev-parse','HEAD')==json.loads((E/'TOPOLOGY_COMMIT.json').read_text())['head'] and not git('status','--porcelain')
for folder in ['research_inputs/assembly_v1','scripts_project','tests/research']:
 for p in (S/folder).rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(S);q=R/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());q.chmod(0o644)
baseline=R/'configs/research/baseline.yaml';previous=baseline.read_text()
addition='''

# Gate4 input gate only. A runnable Full-SC assembly is blocked until the
# target-year source, supply, allocation and carbon attribution gates close.
demand_data:
  update_data: false
final_adjustment:
  only_elec_network: false
research_assembly:
  schema: phase4-gate4-v1
  input_registry: research_inputs/assembly_v1/registry.json
  target_year: 2050
  base_year: 2019
  accepted_status: ASSEMBLY_V1_ACCEPTED
  preflight: scripts_project/check_assembly_inputs.py
  legacy_final_adjustment: forbidden
  legacy_sector_demand_builders: forbidden
  target_year_fallback: forbidden
  network_export_enabled: false
  blocked_reason: target_year_input_freeze_incomplete
  scenario_switching: false
  solver_allowed: false
'''
baseline.write_text(previous.rstrip()+addition)
recipe=R/'configs/research/composition.json';c=json.loads(recipe.read_text());assert c['runnable_workflow'] is False
c['reason']='Gate4 input freeze remains incomplete. Run the explicit assembly preflight only; no full-network entry point is falsely advertised.'
c['assembly_preflight']='scripts_project/check_assembly_inputs.py';recipe.write_text(json.dumps(c,indent=2)+'\n')
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
def run(name,args,expected=0):
 p=sp.run([P,*map(str,args)],cwd=R,stdout=sp.PIPE,stderr=sp.STDOUT,env=env);(E/(name+'.log')).write_bytes(p.stdout)
 if p.returncode!=expected:raise RuntimeError(name+'\n'+p.stdout.decode())
run('ASSEMBLY_INPUT_TESTS',['tests/research/test_assembly_input_freeze.py'])
run('ASSEMBLY_PREFLIGHT',['scripts_project/check_assembly_inputs.py','--year',2050,'--output',E/'ASSEMBLY_PREFLIGHT.json'],2)
run('GATE1_STATIC_REGRESSION',['tests/research/test_phase4_static.py'])
run('GATE2_REGRESSION',['tests/research/test_demand_accounting.py'])
run('GATE3_REGRESSION',['scripts_project/run_gate3_validation.py','--output',E/'gate3_regression'])
run('GATE3_CONFIG_REGRESSION',['scripts_project/check_research_carriers.py','--output',E/'GATE3_CONFIG_REGRESSION.json'])
start=json.loads((E/'START.json').read_text());guard={rel:sha(R/rel)==h for rel,h in start['gate2_hashes'].items()};assert all(guard.values())
old=yaml.safe_load(sp.check_output(['git','show',start['head']+':configs/research/baseline.yaml'],cwd=R))
new=yaml.safe_load(baseline.read_text());assert all(new[k]==v for k,v in old.items())
(E/'PRESERVATION_GUARD.json').write_text(json.dumps(dict(gate2_input_hashes=guard,gate2_and_gate3_contracts_unchanged=True),indent=2))
commits=[]
for message,paths in [
 ('data: freeze source-qualified Assembly V1 anchors and controls\n\nAccept 11 UNSD 2019 final-electricity parents, four frozen upstream electrolyser\nparameters, six existing power budgets and explicit boundary controls under\nASSEMBLY_V1_ACCEPTED, never HUMAN_ACCEPTED. Keep 2050 demand pending and\nnever reuse DEFAULT growth, missing zero, or vehicle shares as energy shares.', ['research_inputs/assembly_v1']),
 ('test: gate assembly on source-qualified target-year inputs\n\nAdd hash-pinned input checks and explicit blocked 2050 preflight. Disable\nupstream electricity-only crop and data refresh in Research overrides, but\nkeep full workflow non-runnable until material inputs close. Preserve Gate2\nand Gate3 contracts; no model construction, scenario switch or optimizer.', ['scripts_project/check_assembly_inputs.py','tests/research/test_assembly_input_freeze.py','configs/research/baseline.yaml','configs/research/composition.json'])]:
  sp.run(['git','add','--',*paths],cwd=R,check=True)
  sp.run(['git','-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','commit','-m',message],cwd=R,check=True)
  commits.append(dict(head=git('rev-parse','HEAD'),message=message,paths=paths))
assert not git('status','--porcelain');(E/'INPUT_COMMITS.json').write_text(json.dumps(commits,indent=2));print(json.dumps(commits,indent=2))
