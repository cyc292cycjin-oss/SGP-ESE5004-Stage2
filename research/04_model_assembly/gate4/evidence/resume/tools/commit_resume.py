"""Commit only the reviewed resume scope; pin tested implementation in reports."""
from pathlib import Path
import subprocess as sp,json,hashlib,csv,shutil,sys
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
W=Path(__file__).resolve().parent; S=W/'stage'; E=W/'evidence'; G=S/'research/04_model_assembly/gate4'; GE=G/'evidence/resume'
def git(*args):return sp.check_output(['git',*args],cwd=R,text=True).rstrip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def refs(s):return {l.split('\t')[1]:l.split('\t')[0] for l in s.splitlines()}
start=json.loads((E/'START.json').read_text()); impl=json.loads((E/'IMPLEMENTATION_PATHS.json').read_text())
assert git('rev-parse','HEAD')==start['head'] and git('branch','--show-current')==start['branch']
before=refs(start['remote_refs']); current=refs(git('ls-remote','origin'))
assert current==before,'Remote changed; do not push over concurrent work'
for rel in impl:assert sha(R/rel)==sha(S/rel),rel
dirty=git('status','--porcelain').splitlines()
assert all(l[3:] in impl or l[3:].startswith('research_inputs/assembly_v1/') for l in dirty),dirty
# CSV roundtrips and exact registry view before any commit.
tables=json.loads((W/'build/tables.json').read_text())
for name,t in tables.items():
 with (G/name).open(encoding='utf-8-sig',newline='') as f: actual=list(csv.reader(f))
 assert actual==t['export_values'],name
validation=json.loads((E/'TEST_RECEIPTS.json').read_text());assert all(x['passed'] for x in validation)
commits=[]
def commit(message,paths):
 sp.run(['git','add','--',*paths],cwd=R,check=True)
 staged=git('diff','--cached','--name-only').splitlines(); assert staged
 assert all(any(p==root or p.startswith(root.rstrip('/')+'/') for root in paths) for p in staged),staged
 sp.run(['git','-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','commit','-m',message],cwd=R,check=True)
 commits.append(dict(head=git('rev-parse','HEAD'),message=message,paths=staged))
commit('data: record BAS road and constant-bunker Assembly V1 decisions\n\nRetain approximate road parent350.5315Mtoe and keep Road EV embedded in Astar.\nFreeze17 verified international bunker obligations at2019 values under the\nexplicit human2050 boundary. Preserve missing accounts and candidate rebases;\nno AEO8 generation, ATS EV share, DEFAULT growth or new forecast is inserted.', ['research_inputs/assembly_v1'])
commit('test: enforce Assembly V1 embedded road ownership at preflight\n\nReject explicit/zero EV, duplicate road parents and dropped required fuel\naccounts. Record the human market/biomass/geology boundary, keep export and\nsolver disabled, and move actual carbon attribution to post-build validation.\n17 input tests and Gate1/Gate2/Gate3/topology regressions pass; input readiness\nremains blocked rather than fabricating an assembled network.', ['scripts_project/check_assembly_inputs.py','tests/research/test_assembly_input_freeze.py','configs/research/baseline.yaml'])
tested=git('rev-parse','HEAD')
sys.path.insert(0,str(R/'scripts_project'))
from phase4_static import config,json_evidence
dump(GE/'EFFECTIVE_CONFIG_AFTER.json',json_evidence(config(R)))
manifest=json.loads((G/'PHASE4_FIRST_FULLSC_NETWORK_MANIFEST.json').read_text())
manifest.update(git_commit=tested,git_commit_role='Tested resume input/preflight commit; no network build commit',config_sha256={p:sha(R/p) for p in manifest['config']},effective_config_after_sha256=sha(GE/'EFFECTIVE_CONFIG_AFTER.json'))
assert manifest['network_sha256'] is None and manifest['network_file'] is None and manifest['solver_runs']==0
dump(G/'PHASE4_FIRST_FULLSC_NETWORK_MANIFEST.json',manifest)
dump(GE/'IMPLEMENTATION_COMMITS.json',commits)
dump(GE/'IMPLEMENTATION_HASHES.json',{p:sha(R/p) for p in impl})
(GE/'IMPLEMENTATION.diff').write_bytes(sp.check_output(['git','diff',start['head'],tested,'--',*impl],cwd=R))
tool_dir=GE/'tools';tool_dir.mkdir(exist_ok=True)
for name in ['prepare_resume.py','verify_bunker_sources.py','build_resume.py','export_tables.mjs','resume_decisions.json','write_reports.py','integrate_and_test.py','commit_resume.py']:
 shutil.copyfile(W/name,tool_dir/name)
(tool_dir/'README.md').write_text('These are the exact audit builders and integration helpers used in the recorded workspace. They retain explicit original paths and start-SHA guards; do not run integration/commit helpers on a different branch. Canonical replay inputs are hash-pinned in research_inputs/assembly_v1. TARGET_CONSTRUCTION.json and the method register expose all formulas independently of the helper environment. CSV export uses the bundled @oai/artifact-tool; no solver is called.\n')
for p in G.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(S);dest=R/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());dest.chmod(0o644)
commit('audit: document Gate4 resume decisions and remaining input evidence\n\nPin the AEO8 table/page/hash trace, target method register and raw bunker\nverification. Distinguish closed Road EV/bunker growth questions from pending\nunit/rebase and base-fuel reconciliation. Record bounded regression evidence\nand leave all actual-network metrics unavailable: no network and zero solves.', ['research/04_model_assembly/gate4'])
assert not git('status','--porcelain'),git('status','--porcelain')
dump(E/'COMMITS.json',commits)
print(json.dumps(dict(commits=[c['head'] for c in commits],working_tree_clean=True,solver_runs=0),indent=2))
