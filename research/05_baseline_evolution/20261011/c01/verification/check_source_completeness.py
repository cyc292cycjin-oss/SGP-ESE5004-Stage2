"""Read-only NPZ invalid-value and omitted-zero-column verification; no aggregation."""
from pathlib import Path
import json,subprocess,hashlib
import numpy as np
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
E=R/'research/05_baseline_evolution/20261011/c01/evidence'
S=Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/phase4_gate4_final_closure_20261006/actual_allocation')
def sha(b):return hashlib.sha256(b).hexdigest()
reference=json.loads(subprocess.check_output(['git','-C',str(R),'show','8883de6fb3e15767c632ac92f535e8a423e90b69:research_inputs/derived/exact_source_closure_a_max_account_v1_20261011/LOADS_AND_WEIGHTS_REFERENCE.json']))
manifest=json.loads((S/'allocation_manifest.json').read_text())
assert sha((S/'allocations.npz').read_bytes())==manifest['arrays_sha256']=='931c24aac84be29eda6b2a1906a8e85ca0f3876b90c26cdb3b40e84ad8d3b2b9'
mapped={r['LoadID'] for r in reference['loads']};zero={r['LoadID']:r for r in reference['preexisting_zero_allocation_columns_without_Load']}
counts=[];zero_verified=[];seen=set()
with np.load(S/'allocations.npz',allow_pickle=False) as z:
 for rec in manifest['records']:
  a=z[rec['ArrayKey']];stats={'NaN':int(np.isnan(a).sum()),'Inf':int(np.isinf(a).sum()),'negative':int((a<0).sum())}
  assert not any(stats.values())
  counts.append({'ArrayKey':rec['ArrayKey'],'InputID':rec['InputID'],'shape':list(a.shape),'invalid_counts':stats})
  for j,node in enumerate(rec['Nodes']):
   key=rec['InputID']+'@'+node;seen.add(key)
   assert key in mapped or key in zero
   if key in zero:
    assert np.all(a[:,j]==0) and sha(np.asarray(a[:,j],dtype='<f8').tobytes())==zero[key]['binary64_sha256']
    zero_verified.append(key)
assert seen==mapped|set(zero) and len(zero_verified)==161
out={'status':'PASS','allocation_arrays':counts,'total_source_columns':len(seen),'actual_Load_columns':len(mapped),'preexisting_zero_columns_not_new_Loads':zero_verified,'nonfinite_or_negative_values':0,'note':'No missing positive column or newly removed Load. These 161 zero allocation columns predate C01 and were already recorded by Scheme A; original source file unchanged.','source_write_operations':0,'aggregations_repeated':0}
(E/'C01_SOURCE_ARRAY_COMPLETENESS.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['allocation_arrays','preexisting_zero_columns_not_new_Loads']}))
