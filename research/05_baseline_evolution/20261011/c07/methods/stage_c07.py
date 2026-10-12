"""Stage only explicit C07 light evidence / code, no large arrays or credentials."""
from pathlib import Path
import shutil,json,hashlib,ast
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c07_v4_reliability_20261013')
REPO=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
DEST=REPO/'research/05_baseline_evolution/20261011/c07';DEST.mkdir(exist_ok=True)
def cp(src,rel):
 dst=DEST/rel;dst.parent.mkdir(exist_ok=True,parents=True)
 if dst.exists():assert dst.read_bytes()==src.read_bytes(),str(dst)
 else:shutil.copyfile(src,dst)
for p in (W/'release').rglob('*'):
 if p.is_file() and p.suffix in ('.py','.json') and '__pycache__' not in p.parts:cp(p,'release/'+str(p.relative_to(W/'release')))
for n in ['C07_V4_APPLICABILITY.json','C07_RESOURCE_SCALE_PLAN.json','C07_EXPRESSION_STATIC_CHECK.json','C07_MAPPING_INTERFACE_TESTS.json','C07_AFFINE_NORMALIZATION_DIAGNOSTIC.json','C07_INITIAL_INVENTORY.json','RELEASE_DELIVERY.json','DEPLOYMENT_RECEIPT.json','A_LAUNCH_RECEIPT.json','B_LAUNCH_RECEIPT.json','A_TERMINAL_REVIEW.json','B_TERMINAL_REVIEW.json','C06_NEW_WINDOW_SOURCE_PREFIX_VERIFIED.json','C06_NEW_TRANSFER_WINDOW.json','C06_NEW_TRANSFER_COMPLETE.json']:
 cp(W/n,'evidence/'+n)
cp(W/'LITERATURE_AND_V4_INTERPRETATION.md','LITERATURE_AND_VERSION_EVIDENCE.md')
cp(W.parent/'c06_barconvtol_20261012/C06_LOCAL_BACKUP_RECEIPT.json','evidence/C06_LOCAL_BACKUP_RECEIPT.json')
for n in ['audit_v4.py','prepare_expression.py','test_mapping.py','prepare_release.py','compare_c07.py','stage_c07.py']:
 ast.parse((W/n).read_text());cp(W/n,'methods/'+n)
e=json.loads((W/'expression/C07_EXPRESSION_BINDING.json').read_text())
record={'omitted_payload_arrays':e['files'],'reason':'Large native numerical arrays are preserved in run evidence; review/Git contain identities and reproduction code only','local_expression':str(W/'expression'),'release_manifest_sha256':json.loads((W/'RELEASE_DELIVERY.json').read_text())['release_manifest_sha256'],'scientific_source_or_formal_V4_changes':False,'optimization_calls_completed':2,'A':'OPTIMAL_BUT_NOT_ACCEPTED','B':'INFEASIBLE_NO_LEGAL_SOLUTION','C07_archive_reception':'IN_PROGRESS_NOT_YET_COMPLETE'}
(DEST/'IMPLEMENTATION_AND_PAYLOAD_REFERENCES.json').write_text(json.dumps(record,indent=2)+'\n')
print(str(DEST))
