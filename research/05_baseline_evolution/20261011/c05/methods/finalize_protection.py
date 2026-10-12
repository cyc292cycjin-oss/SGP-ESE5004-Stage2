"""Keep a consumed native deadline from suppressing the separately approved V4 budget."""
from pathlib import Path
import json,hashlib
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c05_aggregate0_20261012');R=W/'release'
p=R/'production_control.py';s=p.read_text()
insert='''def stop_blocks_stage(root,phase):
 p=Path(root)/'STOP_REQUEST.json'
 if not p.exists():return False
 # Preserve the old stop receipt. Only a completed native-only timeout may
 # transition to the separately bounded postprocess budget. Resources, loss of
 # supervision and every other stop still block immediately.
 if phase=='POSTPROCESS' and read(p).get('reason')=='PHASE_DEADLINE_NATIVE':
  durable=Path(root)/'raw/RAW_DURABLE.json'
  if (Path(root)/'NATIVE_CALL_EXIT.json').exists() and durable.exists() and read(durable).get('complete') is True:return False
 return True

'''
assert s.count('def guardian(config):')==1
s=s.replace('def guardian(config):',insert+'def guardian(config):')
assert s.count("requested=(root/'STOP_REQUEST.json').exists()") == 1
s=s.replace("requested=(root/'STOP_REQUEST.json').exists()","requested=stop_blocks_stage(root,stage['phase'])\n   if not requested:stop_at=None")
p.write_text(s)
p=R/'c05_worker.py';s=p.read_text().replace('from production_control import alive,phase_deadline','from production_control import alive,phase_deadline,stop_blocks_stage')
s=s.replace("if (run/'STOP_REQUEST.json').exists():raise RuntimeError('PROTECTION_STOP_'+label)","if stop_blocks_stage(run,read(run/'PHASE.json')['phase']):raise RuntimeError('PROTECTION_STOP_'+label)")
p.write_text(s)
p=R/'C03_MODULE_REUSE.json';m=json.loads(p.read_text())
for r in m['files']:
 if r['relative']=='production_control.py':r.update(role='ADAPTED_NATIVE_TIMEOUT_TO_POSTPROCESS_TRANSITION_ONLY',derived_sha256=hashlib.sha256((R/r['relative']).read_bytes()).hexdigest())
p.write_text(json.dumps(m,indent=2)+'\n')
(W/'C05_RELEASE.tar.gz').rename(W/'C05_RELEASE_prelaunch_v1.tar.gz')
(W/'RELEASE_DELIVERY.json').rename(W/'RELEASE_DELIVERY_prelaunch_v1.json')
