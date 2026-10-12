"""Verify only the newly prepared, lightweight C05 publication and original receipts."""
from pathlib import Path
import json, hashlib, re
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
O=R/'research/05_baseline_evolution/20261011/c05'
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c05_aggregate0_20261012')
def j(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
index=j(O/'C05_EVIDENCE_INDEX.json')
for e in index['files']:
 p=O/e['relative']; assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'], e['relative']
params=j(O/'evidence/current_run/EFFECTIVE_MODEL_PARAMETERS.json')
old=j(O/'release/C03_EFFECTIVE_MODEL_PARAMETERS.json')
assert len(params)==len(old)==154 and [k for k in old if old[k]!=params[k]]==['Aggregate']
assert params['Aggregate']==0 and old['Aggregate']==1
run=O/'evidence/current_run'
raw=j(run/'raw/vectors/RAW_RECEIPT.json')
assert raw['native_status']==12 and raw['native_info']['SolCount']==0
assert all(x['status']=='NOT_AVAILABLE' for x in raw['vectors'].values())
assert j(run/'NATIVE_CALL_EXIT.json')['optimization_calls']==1
assert j(run/'NATIVE_CALL_EXIT.json')['native_return_code']==0
assert not j(run/'raw/RAW_DURABLE.json')['complete']
assert j(run/'raw/RAW_DURABLE.json')['native_state_preserved']
assert j(run/'POSTPROCESS_NOT_RUN.json')['reason']=='NO_COMPLETE_LEGAL_PRIMAL_DUAL'
assert j(run/'NATIVE_TRANSFER.json')['native_model_handle']==j(run/'C05_NATIVE_OPTIMIZE_ENTERED.json')['model_handle']
snap=j(O/'evidence/C05_TERMINAL_OBSERVATION.json')
assert all(not x['live'] for x in snap['live_identities'].values())
assert snap['_SEAL_GUARD_RECEIPT.json']['exit_code']==0
provenance=j(O/'evidence/C05_PUBLIC_EVIDENCE_PROVENANCE.json')
for f in provenance['files']:
 assert sha(O/f['published_relative'])==f['published_sha256']
secrets=[]
for p in sorted(O.rglob('*')):
 if not p.is_file(): continue
 assert p.suffix not in ('.npy','.nc','.npz','.lic','.so','.zip','.gz','.pyc')
 txt=p.read_text()
 for rx in [r'-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----',r'Academic license \d+',r'\b(?:WLSSECRET|WLSACCESSID)\s*=\s*[^\s\n]{8,}',r'\bgh[pousr]_[A-Za-z0-9]{20,}',r'\bgithub_pat_[A-Za-z0-9_]+']:
  if re.search(rx,txt): secrets.append(str(p.relative_to(O)))
assert not secrets,secrets
rec={'status':'PASS','checks':[f"{len(index['files'])} lightweight evidence members matched size and SHA",'154 actual numeric parameters only Aggregate differs','same native handle after readback','one native optimize returned code0 Status12 SolCount0','no vectors claimed saved','postprocess conditional branch respected','terminal worker/supervisor/guard no longer live; seal guard exit0','public logs preserve numerical contents and redact license-registration metadata','no bulk arrays or credential-value patterns published'],
 'scope':'publication consistency; not a repeat solve, V4, model scan or production test','source_evidence_count':len(index['files'])}
(W/'C05_PUBLICATION_CONSISTENCY.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(rec,ensure_ascii=False))
