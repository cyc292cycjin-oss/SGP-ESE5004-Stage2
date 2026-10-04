"""Read-only model identity/source validation; native resume inventory and diffs."""
from pathlib import Path
import math
import subprocess as sp,json,hashlib,difflib,shutil,sys
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
W=Path(__file__).resolve().parent;E=W/'evidence';D=W/'reports';D.mkdir(exist_ok=True)
HEAD='ad5e81e75882704ac9e33a6eac96c5c79717c5e1'
def git(*args):return sp.check_output(['git',*args],cwd=R,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert git('rev-parse','HEAD')==HEAD and not git('status','--porcelain')
refs=git('ls-remote','origin');start=json.loads((E/'START.json').read_text())
assert HEAD+'\trefs/heads/research/full-sc-baseline' in refs
assert 'a3616a68ee44592af6527ca9024a90f1956646ae\trefs/heads/main' in refs
checks={rel:sha(R/rel)==h for rel,h in start['gate2_hashes'].items()}
for p in (E/'source').rglob('*.py'):checks[str(p.relative_to(E))]=sha(p)==sha(R/p.relative_to(E/'source'))
network=json.loads((E/'TUTORIAL_COMPONENTS.json').read_text())
checks['historical_tutorial_network']=sha(Path(network['source']))==network['sha256']
raw=json.loads((E/'RAW_ELECTRICITY_CLASSIFICATION.json').read_text())
for name,h in raw['hashes'].items():checks['raw_topology/'+name]=sha(R/'data/osm-plus-prebuilt/0.1.1'/name)==h
sys.path.insert(0,str(R/'scripts_project'))
from phase4_static import config
def clean(x):
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,list):return [clean(v) for v in x]
 if isinstance(x,float) and not math.isfinite(x):return str(x)
 return x
checks['effective_config']=json.loads(json.dumps(clean(config(R)),default=str))==json.loads((E/'EFFECTIVE_CONFIG.json').read_text())
assert all(checks.values()),checks
worktrees=git('worktree','list','--porcelain');branches=git('branch','--list')
receipt=dict(head=HEAD,branch=git('branch','--show-current'),clean=True,remote_refs=refs,checks=checks,worktrees=worktrees,branches=branches)
(E/'RESUME_IDENTITY.json').write_text(json.dumps(receipt,indent=2))
classes={'carrier_architecture.py':'A','carbon_architecture.py':'B','baseline.yaml':'A+B','test_carrier_carbon.py':'C','check_research_carriers.py':'C','run_gate3_validation.py':'C'}
review=['# Gate3 pre-integration exact diff review','',f'Base: `{HEAD}`. Review completed before integration; no commit created by this inventory.','',
'A carrier isolation; B carbon architecture; C test/validation; D documentation; E unrelated.','', '| Draft | Class | Exact patch |','|---|---|---|']
orig=W/'preserved_drafts';orig.mkdir(exist_ok=True);patchdir=E/'resume_diffs';patchdir.mkdir(exist_ok=True)
for p in sorted((W/'stage').rglob('*')):
 if not p.is_file() or '__pycache__' in str(p):continue
 rel=p.relative_to(W/'stage');assert p.name in classes,rel
 out=orig/rel;out.parent.mkdir(parents=True,exist_ok=True);assert not out.exists();out.write_bytes(p.read_bytes())
 old=sp.run(['git','show',HEAD+':'+rel.as_posix()],cwd=R,stdout=sp.PIPE,stderr=sp.PIPE)
 diff=''.join(difflib.unified_diff(old.stdout.decode().splitlines(True),p.read_text().splitlines(True),fromfile='Gate2/'+rel.as_posix(),tofile='draft/'+rel.as_posix()))
 patch=patchdir/(p.name+'.patch');patch.write_text(diff)
 review.append(f'| {rel.as_posix()} | {classes[p.name]} | evidence/resume_diffs/{patch.name} |')
review += ['', 'E unrelated: NONE in the six implementation drafts. New files are represented as complete additions. baseline.yaml preserves every research_demand value; it adds carrier/carbon contracts only.',
'', 'Review follow-ups before integration: enforce nonnegative directed Link dispatch; retain geological storage investment cost in the objective with an extendable, capped Store; strengthen shared-event transfer guards; add missing Buildings/Shipping/manifest regression invocations. Final draft patches and hashes will be recorded before copying.']
(D/'GATE3_DRAFT_DIFF_REVIEW.md').write_text('\n'.join(review)+'\n')
inv=['# Gate3 resume inventory','',f'Verified base `{HEAD}`; local/remote research match; working tree clean; main unchanged. No model write or commit during inventory.','', '| Artifact | Classification | Basis / action |','|---|---|---|',
'| START.json, EFFECTIVE_CONFIG.json, source/*.py | VALID_REUSE | Current SHA/config content matches saved evidence. |',
'| TUTORIAL_COMPONENTS.json, CARRIER_FACTORS.json | VALID_REUSE | Original historical NetCDF SHA matches; reference only, not Research assembly. |',
'| REFERENCE_GRAPH_AUDIT.json, REFERENCE_POLICY_MAP.json | VALID_REUSE | Inputs and source hashes unchanged; reuse derived reference graph/maps, no rerun. |',
'| RAW_ELECTRICITY_CLASSIFICATION.json | VALID_REUSE | All four pinned raw topology input hashes match. |',
'| Six stage implementation drafts | NEEDS_RECHECK | Preserved byte copies and exact Gate2 diffs; final tests incomplete. |',
'| probe.py, audit_reference.py, complete_source_audit.py | VALID_REUSE | Extraction/replay provenance; do not regenerate validated reference evidence. |',
'| integrate.py | NEEDS_RECHECK | Never ran before interruption; must add Buildings, Shipping, manifest regressions. |',
'| Gate3 final CSVs, reports, package | UNKNOWN | Not yet present; must produce. |',
'| Existing fix_topology worktree | VALID_REUSE | Inventory only; untouched and excluded from Gate3. |',
'| Other historical worktrees/branches | VALID_REUSE | Retained as references; no Gate3-specific worktree or branch found. |',
'', 'OBSOLETE: none proven. No draft/evidence/history deleted. Implementation target is only research/full-sc-baseline. Native workspace is delivery staging, not the model repository.',
'', '## Worktrees at resume','```',worktrees,'```','', '## Branches at resume','```',branches,'```','',
'Identity and hash checks: evidence/RESUME_IDENTITY.json. Draft byte copies: preserved_drafts/ in the working delivery area; exact patches: evidence/resume_diffs/.']
(D/'GATE3_RESUME_INVENTORY.md').write_text('\n'.join(inv)+'\n')
print(json.dumps({'head':HEAD,'checks':len(checks),'all_checks_pass':all(checks.values()),'drafts':len(classes),'inventory':str(D)}))
