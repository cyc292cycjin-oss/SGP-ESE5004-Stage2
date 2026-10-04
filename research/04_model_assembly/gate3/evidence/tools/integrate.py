from pathlib import Path
import sys,subprocess as sp,json,hashlib,os,difflib
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');W=Path(__file__).resolve().parent;S=W/'stage';E=W/'evidence'
P='/home/jin/miniforge3/envs/pypsa-earth/bin/python';env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
def git(*a):return sp.check_output(['git',*a],cwd=R,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cp(rel):
    q=R/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((S/rel).read_bytes());q.chmod(0o644)
def command(name,args):
    res=sp.run(list(map(str,args)),cwd=R,env=env,stdout=sp.PIPE,stderr=sp.STDOUT);(E/(name+'.log')).write_bytes(res.stdout)
    if res.returncode:print(res.stdout.decode());raise RuntimeError(name)
def commit(msg,paths):
    sp.run(['git','add','--',*paths],cwd=R,check=True)
    sp.run(['git','-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','commit','-m',msg],cwd=R,check=True)
    return {'sha':git('rev-parse','HEAD'),'message':msg,'paths':paths}
if __name__=='__main__':
    start=json.loads((E/'START.json').read_text());assert git('rev-parse','HEAD')==start['head'] and not git('status','--porcelain')
    approved=['scripts_project/carrier_architecture.py','scripts_project/carbon_architecture.py','scripts_project/check_research_carriers.py','scripts_project/run_gate3_validation.py','tests/research/test_carrier_carbon.py','configs/research/baseline.yaml']
    assert (W/'reports/GATE3_DRAFT_DIFF_REVIEW.md').exists() and (E/'RESUME_IDENTITY.json').exists()
    finaldiffs=E/'final_diffs';finaldiffs.mkdir(exist_ok=True);hashes={}
    for rel in approved:
        old=sp.run(['git','show',start['head']+':'+rel],cwd=R,stdout=sp.PIPE,stderr=sp.PIPE)
        p=S/rel;hashes[rel]=sha(p)
        (finaldiffs/(p.name+'.patch')).write_text(''.join(difflib.unified_diff(old.stdout.decode().splitlines(True),p.read_text().splitlines(True),fromfile='Gate2/'+rel,tofile='final/'+rel)))
    (E/'INTEGRATION_ALLOWLIST.json').write_text(json.dumps(hashes,indent=2))
    for rel in approved:cp(rel)
    command('gate3_validation',[P,'scripts_project/run_gate3_validation.py','--output',E])
    command('gate3_config',[P,'scripts_project/check_research_carriers.py','--output',E/'RESEARCH_GATE3_CONFIG_CHECK.json'])
    command('gate2_regression_70',[P,'tests/research/test_demand_accounting.py'])
    command('gate1_static_regression',[P,'tests/research/test_phase4_static.py'])
    command('gate1_manifest_regression',[P,'tests/research/test_run_manifest_schema.py'])
    command('shipping_regression',[P,'tests/transport/test_shipping_allocation.py',R,E/'SHIPPING_REGRESSION.json'])
    command('buildings_strict_regression',[P,'tests/research/approved_buildings_regressions.py','--repo',R,'--fix','combined','--output',E/'BUILDINGS_REGRESSION.json'])
    buildings=json.loads((E/'BUILDINGS_REGRESSION.json').read_text())
    assert buildings['all_pass'] and len(buildings['rows'])==1062
    guards={rel:sha(R/rel)==h for rel,h in start['gate2_hashes'].items()};assert all(guards.values())
    (E/'GATE2_HASH_GUARD.json').write_text(json.dumps(guards,indent=2))
    commits=[]
    for msg,paths in [
        ('feat: isolate research carrier ownership and physical carbon stores\n\nImplement the frozen electricity-only intervention contract using country/node\nH2/fuel/biomass/CO2 interfaces. Shared prices are metadata, finite resources\nrequire accepted allocations, and geology has explicit no-withdrawal constraints.\nEvidence: Phase3 cross-border/supply/carbon contracts; Gate3 static fragment tests.', ['scripts_project/carrier_architecture.py']),
        ('feat: separate power policy co2 from system emissions reporting\n\nPreserve all six absolute budgets and baseline disabled semantics. Use explicit\naccepted component coefficients, not the whole-atmosphere Store. Require\nshared SMR/CHP attribution, trace physical carbon once, and never add a full-system cap.\nValidation: synthetic +1 sector events, capture/recycle/storage and unsolved Linopy coefficients.', ['scripts_project/carbon_architecture.py']),
        ('test: add carrier reachability and carbon scope gates\n\nValidate explicit config consumers, no scenario difference, no demand acceptance\nchanges and real PyPSA fragment semantics. Gate2 70 tests and input hashes preserved.\nNo optimisation, final network construction or topology repair.', ['scripts_project/check_research_carriers.py','scripts_project/run_gate3_validation.py','tests/research/test_carrier_carbon.py','configs/research/baseline.yaml'])]:commits.append(commit(msg,paths))
    assert not git('status','--porcelain');(E/'IMPLEMENTATION_COMMITS.json').write_text(json.dumps(commits,indent=2));print(git('rev-parse','HEAD'))
