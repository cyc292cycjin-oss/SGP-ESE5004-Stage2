"""Authenticate recoverable evidence and derive coordinates for local analysis only.
No downloaded-original replacement and no declaration of a complete archive.
"""
from pathlib import Path
import json,hashlib,os,numpy as np
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c06_barconvtol_20261012')
B=Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rec=read(W/'C06_PARTIAL_EVIDENCE_RECOVERY.json');src=W/'recovered_partial_evidence';dst=W/'analysis_view'
dst.mkdir(exist_ok=True)
snap=read(W/'monitor_snapshots/20261012T100539Z.json');receipts=snap['receipts'];ver=[]
for v in rec['member_records']:
 p=src/v['relative'];assert sha(p)==v['sha256'];q=dst/v['relative'];q.parent.mkdir(parents=True,exist_ok=True)
 if not q.exists():os.link(p,q)
 else:assert sha(q)==v['sha256']
 if v['relative'] in receipts and p.suffix=='.json':
  actual=read(p);remote=receipts[v['relative']]
  # Observer deliberately compacts parameter-diff and postprocessing receipts.
  if v['relative']=='C06_C03_C05_PARAMETER_COMPARISON.json':
   actual={'status':actual['status'],'count':actual['count'],'C03_differences':actual['C03_vs_C06']['differences'],'C05_differences':actual['C05_vs_C06']['differences']}
  same=all(k in actual and actual[k]==x for k,x in remote.items())
  ver.append({'relative':v['relative'],'monitor_exact_object_or_subset':same})
  assert same,v['relative']
raw=receipts['raw/vectors/RAW_RECEIPT.json'];p=dst/'raw/vectors/RAW_RECEIPT.json';p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(raw,indent=2)+'\n',encoding='utf-8')
assert sha(p)==read(dst/'raw/RAW_DURABLE.json')['receipt_sha256']
index=read(dst/'postprocess/original_vectors/ORIGINAL_VECTOR_INDEX.json');vectors=[]
for name in ('X','Pi','RC'):
 orig=dst/'postprocess/original_vectors'/f'{name}_original.npy'
 assert sha(orig)==index['vectors'][name]['sha256']
 x=np.load(orig,mmap_mode='r',allow_pickle=False)
 factor=np.load(B/'bridge/mapping'/('R.npy' if name=='Pi' else 'D.npy'),mmap_mode='r',allow_pickle=False)
 assert np.all(np.isfinite(x)) and np.all(np.isfinite(factor)) and np.all(factor>0)
 native=x*factor if name=='RC' else x/factor
 p=dst/'raw/vectors'/f'{name}.npy';np.save(p,native,allow_pickle=False)
 assert sha(p)==raw['vectors'][name]['sha256'],name
 vectors.append({'name':name,'original_unit_path':str(orig),'original_unit_sha256':sha(orig),
  'derived_for_analysis_path':str(p),'derived_native_sha256':sha(p),'matches_cloud_native_SHA_exactly':True,
  'method':'rc=RC_original*D' if name=='RC' else ('pi=Pi_original/R' if name=='Pi' else 'z=X_original/D'),
  'qualification':'BIT_IDENTICAL_TO_RECORDED_NATIVE_FILE_BY_SHA256; coordinate inverse, not new solution or completed download'})
assert sha(dst/'EFFECTIVE_MODEL_PARAMETERS.json')==read(dst/'C06_NATIVE_OPTIMIZE_ENTERED.json')['parameters_sha256']
for rel,h in read(dst/'IMMUTABLE_INPUTS.json')['core'].items():assert sha(B/rel)==h,rel
out={'status':'LOCAL_ANALYSIS_INPUTS_AUTHENTICATED_BACKUP_STILL_PENDING','run_id':snap['run_id'],
 'analysis_view':str(dst),'source_recovery_receipt_sha256':sha(W/'C06_PARTIAL_EVIDENCE_RECOVERY.json'),
 'native_receipt_recovered_from_monitor_SHA_verified':sha(dst/'raw/vectors/RAW_RECEIPT.json'),
 'vectors':vectors,'monitor_comparisons':ver,'immutable_core_files_SHA_verified':len(read(dst/'IMMUTABLE_INPUTS.json')['core']),
 'complete_archive_SHA_and_CRC':'NOT_VERIFIED_INCOMPLETE','BACKUP_INDEX_file':'NOT_RECEIVED',
 'all_53_files_against_BACKUP_INDEX':'NOT_VERIFIED','remote_operations':0,'new_solution_or_raw_edit':False}
(W/'C06_ANALYSIS_PROVENANCE.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2))
