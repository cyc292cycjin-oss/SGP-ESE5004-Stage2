"""Validate new publication against actual receipts, without rerunning science."""
from pathlib import Path
import json,hashlib,re
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
O=R/'research/05_baseline_evolution/20261011/c06'
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c06_barconvtol_20261012')
j=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
index=j(O/'C06_EVIDENCE_INDEX.json')
for x in index['files']:
 p=O/x['relative'];assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256'],x['relative']
run=O/'evidence/current_run';raw=j(run/'raw/vectors/RAW_RECEIPT.json')
assert raw['native_status']==2 and raw['native_info']['SolCount']==1 and raw['native_info']['BarIterCount']==143
assert all(v['status']=='SAVED_UNQUALIFIED' for v in raw['vectors'].values())
assert j(run/'raw/RAW_DURABLE.json')['complete']
assert j(run/'NATIVE_CALL_EXIT.json')['optimization_calls']==1 and j(run/'NATIVE_CALL_EXIT.json')['native_return_code']==0
assert j(run/'NATIVE_TRANSFER.json')['native_model_handle']==j(run/'C06_NATIVE_OPTIMIZE_ENTERED.json')['model_handle']
pp=j(run/'postprocess/POSTPROCESS_RECEIPT.json');assert pp['status']=='OPTIMAL_BUT_NOT_ACCEPTED' and pp['gates']['385_obligations'] and not pp['gates']['807_inventory']
actual=j(run/'EFFECTIVE_MODEL_PARAMETERS.json');c3=j(O/'release/C03_EFFECTIVE_MODEL_PARAMETERS.json');c5=j(O/'release/C05_EFFECTIVE_MODEL_PARAMETERS.json')
assert len(actual)==len(c3)==len(c5)==154
assert [k for k in actual if actual[k]!=c3[k]]==['BarConvTol']
assert sorted(k for k in actual if actual[k]!=c5[k])==['Aggregate','BarConvTol']
assert actual['Aggregate']==1 and actual['BarConvTol']==1e-9
assert j(O/'C06_C03_C05_PARAMETER_COMPARISON.json')['status']=='PASS'
snap=j(O/'evidence/C06_TERMINAL_OBSERVATION.json');assert all(not v['live'] for v in snap['live_identities'].values())
assert snap['_SEAL_GUARD_RECEIPT.json']['exit_code']==0
backup=j(O/'C06_FINAL_BACKUP_STATUS.json');assert backup['status']=='LOCAL_SYNC_PENDING'
assert backup['missing_bytes']==13075703 and backup['window_expired'] and not backup['new_window_opened']
assert j(O/'evidence/C06_ANALYSIS_PROVENANCE.json')['status']=='LOCAL_ANALYSIS_INPUTS_AUTHENTICATED_BACKUP_STILL_PENDING'
assert all(v['matches_cloud_native_SHA_exactly'] for v in j(O/'evidence/C06_ANALYSIS_PROVENANCE.json')['vectors'])
comparison=j(O/'C03_C05_C06_METRIC_COMPARISON.json')
assert comparison['classification']=='C06_EXECUTION_ACCEPTED_SCIENCE_NOT_ACCEPTED'
assert comparison['stationarity_asset_sets']['new']==['Line-s:49','Line-s:59']
assert j(O/'evidence/C06_EXACT_LOCAL_FORENSICS.json')['all_coordinate_identities_exact']
for x in j(O/'evidence/C06_PUBLIC_EVIDENCE_PROVENANCE.json')['files']:assert sha(O/x['published_relative'])==x['published_sha256']
secrets=[]
for p in O.rglob('*'):
 if not p.is_file():continue
 assert p.suffix not in ('.npy','.npz','.nc','.lic','.so','.zip','.gz','.pyc')
 assert p.stat().st_size<4_000_000,p
 text=p.read_text()
 for rx in [r'-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----',r'Academic license \d+',r'\b(?:WLSSECRET|WLSACCESSID)\s*=\s*[^\s\n]{8,}',r'\bgh[pousr]_[A-Za-z0-9]{20,}',r'\bgithub_pat_[A-Za-z0-9_]+']:
  if re.search(rx,text):secrets.append(str(p.relative_to(O)))
assert not secrets,secrets
rec=dict(status='PASS_WITH_EXPLICIT_BACKUP_PENDING',evidence_files=len(index['files']),checks=['file sizes and SHA','actual 154 parameter comparisons C03/C05','one optimize; saved raw complete X/Pi/RC','same transferred native model handle','complete V4 failure honestly retained','last observation processes exited and seal success','local archive remains incomplete; expired window unchanged','three inverse-coordinate files match recorded native SHA','selected exact rows and columns agree','public redaction provenance','no bulk data or credential values'],scope='publication consistency, no scientific rerun')
(W/'C06_PUBLICATION_CONSISTENCY.json').write_text(json.dumps(rec,indent=2)+'\n')
print(json.dumps(rec,indent=2))
