"""Read preserved C02 evidence only. No PyPSA/Linopy model or solver is created."""
from pathlib import Path
import json, hashlib, zipfile, collections, struct
import numpy as np
import xarray as xr

W = Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c02_daily_build_20261012')
E = W/'cloud_evidence'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

idx=read(W/'READ_ONLY_CLOUD_ARTIFACT_INDEX.json')
by={v['path']:v for v in idx['files']}
zipfile_path=E/'C02_CLOUD_REVIEW.zip'
assert sha(zipfile_path)==by['C02_CLOUD_REVIEW.zip']['sha256']
out=E/'original_run_receipts'
out.mkdir(exist_ok=True)
with zipfile.ZipFile(zipfile_path) as z:
    assert z.testzip() is None
    assert len(set(z.namelist()))==len(z.namelist())
    manifest=json.loads(z.read('CLOUD_REVIEW_INDEX.json'))
    assert set(z.namelist())=={x['path'] for x in manifest['files']}|{'CLOUD_REVIEW_INDEX.json'}
    for n in z.namelist():
        assert not Path(n).is_absolute() and '..' not in Path(n).parts
        data=z.read(n); ref=by[n]
        assert len(data)==ref['bytes'] and hashlib.sha256(data).hexdigest()==ref['sha256']
        p=out/n;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists():assert p.read_bytes()==data
        else:p.write_bytes(data)
assert sha(E/'CLOUD_SEAL_COMPLETE.json')==by['CLOUD_SEAL_COMPLETE.json']['sha256']
net=E/'daily_365_unsolved.nc'
assert sha(net)==by['artifacts/daily_365_unsolved.nc']['sha256']
ds=xr.open_dataset(net)
assert len(ds['snapshots'])==365
names=list(ds.variables)
print('NetCDF static Store keys:',[x for x in names if x.startswith('stores_') and not x.startswith('stores_t_')][:30])

families=collections.defaultdict(lambda:{'blocks':0,'active_rows':0})
for b in idx['families']:
    if b['kind']!='constraints':continue
    name=b['name']
    for prefix in ['ResearchStoreDirection','ResearchBatteryNominal','ResearchImportAnnual','ResearchExistingResource']:
        if name.startswith(prefix+'-'):name=prefix;break
    families[name]['blocks']+=1;families[name]['active_rows']+=b['active_labels']
coverage={'status':'LABEL_PRESENCE_AND_COUNTS_VERIFIED_COEFFICIENT_READBACK_NOT_COMPLETED',
 'source':'READ_ONLY_CLOUD_ARTIFACT_INDEX.json; persisted mapping/*.npy hashes',
 'total_active_variables':sum(x['active_labels'] for x in idx['families'] if x['kind']=='variables'),
 'total_active_rows':sum(x['active_labels'] for x in idx['families'] if x['kind']=='constraints'),
 'families':dict(families),'nnz':None,'nnz_status':'NOT_PERSISTED_BEFORE_FAILURE',
 'constraint_coefficients_complete_verified':False,
 'all_807_Scheme_A_actual_initial_RHS_check':'BLOCKED_AT_FIRST_ASSET_NO_RHS_SNAPSHOT',
 'all_final_Bus_RHS_check':'NOT_REACHED','static_full_LP_acceptance':False}
write(W/'C02_CONSTRAINT_COVERAGE.json',coverage)

source=idx['pypsa_constraints_source']
assert any(x['line']==927 and x['text'].strip()=='rhs = -e_init.where(~include_previous_e, 0)' for x in source['lines'])
# Evaluate only the scalar/array RHS expression, not define_store_constraints or a model.
q=1.0
rhs=(-xr.DataArray(q).where(~xr.DataArray([False,True,True],dims=['snapshot']),0)).values
expected=np.r_[-q,np.zeros(2)]
zero={'status':'CHECKER_SIGNED_ZERO_DEFECT_REPRODUCED_SOURCE_EXPRESSION_ONLY',
 'evidence_grade':'VERIFIED_SOURCE_AND_TINY_ARITHMETIC; ACTUAL_FAILED_RHS_ARRAY_NOT_SAVED',
 'cloud_PyPSA_source':{'path':source['path'],'sha256':source['sha256'],'line':927},
 'checker':{'file':'c02_model.py','sha256':sha(W/'upload_stage/c02_model.py'),'line':210,'expected':'[-q, +0.0, ...]','comparison':'uint64 binary64 bits'},
 'scalar_test_q':q,'source_expression_rhs_hex':[float(x).hex() for x in rhs],
 'checker_expected_hex':[float(x).hex() for x in expected],
 'numeric_exact_equal':bool(np.array_equal(rhs,expected)),
 'bits_equal':bool(np.array_equal(rhs.view('u8'),expected.view('u8'))),
 'interpretation':'The checker can reject exact real equality solely for zero sign. Source derives -0 for later noncyclic Store rows. The production exception has no per-element dump, so absence of any additional mismatch is NOT_PROVEN.',
 'full_model_rebuilt':False,'solver_calls':0,'failed_code_modified':False,
 'proposed_fix_not_applied':'Compare exact finite numeric equality for row semantics, explicitly retain/report signed-zero differences; retain bit-exact checks for immutable inputs and file roundtrips. Record first mismatching asset/row/hex before abort. A new full build is not executed.'}
assert zero['numeric_exact_equal'] and not zero['bits_equal']
write(W/'C02_SIGNED_ZERO_FORENSICS.json',zero)
write(W/'PYPSA_STORE_SOURCE_EVIDENCE.json',source)

auth=read(out/'BUILD_AUTHORIZATION.json');result=read(out/'BUILD_RESULT.json');seal=read(E/'CLOUD_SEAL_COMPLETE.json')
samples=[json.loads(s) for s in (out/'RESOURCE_SAMPLES.jsonl').read_text().splitlines()]
rss=read(out/'STATUS.json')['peak_rss_bytes']
resource={'t0_epoch':auth['t0'],'absolute_deadline_epoch':auth['deadline'],'window_seconds':auth['deadline']-auth['t0'],
 'failure_epoch':result['time'],'seal_epoch':seal['at'],'seconds_to_failure':result['time']-auth['t0'],
 'seconds_to_cloud_seal':seal['at']-auth['t0'],'peak_worker_ru_maxrss_bytes':rss,
 'peak_worker_tree_sampled_bytes':idx['resources']['max_worker_tree_rss'],
 'peak_cgroup_memory_bytes':max(a['memory_peak'] for x in samples for a in x['ancestors']),
 'min_disk_free_bytes':idx['resources']['min_disk_free'],'initial':auth['initial_resources'],
 'last':samples[-1],'samples':len(samples),'processes_after_exit':idx['processes'],
 'supervisor_exit':read(out/'SUPERVISOR_EXIT.json'),'guard_exit':read(out/'GUARD_EXIT.json'),
 'build_attempts':1,'optimizer_calls':0,'no_automatic_retry':True,'instance_power_not_changed':True}
write(W/'C02_RESOURCE_AND_EXIT_SUMMARY.json',resource)

local=[];pending=[]
for rec in idx['files']:
    p=out/rec['path']
    if rec['path']=='artifacts/daily_365_unsolved.nc':p=net
    elif rec['path'] in ['CLOUD_SEAL_COMPLETE.json','C02_CLOUD_REVIEW.zip']:p=E/rec['path']
    if p.exists():
        assert sha(p)==rec['sha256']; local.append({**rec,'local_path':str(p).replace('/mnt/d/','D:/')})
    else:pending.append(rec)
sync={'status':'NETWORK_AND_LIGHT_RECEIPTS_LOCAL_SHA_VERIFIED_PARTIAL_LP_CLOUD_ONLY',
 'run':idx['run'],'originals_retained':True,'local_verified':local,'cloud_only':pending,
 'cloud_only_bytes':sum(r['bytes'] for r in pending),'zip_crc':'PASS','zip_member_identity':'PASS',
 'old_cloud_index_caveat':'CLOUD_REVIEW_INDEX names ARTIFACT_SHA_INDEX.json, but it was not generated before failure. This independently collected post-exit index fills preservation metadata only; it does not certify a complete LP.',
 'full_LP_exists':False}
write(W/'C02_LOCAL_SYNC_AND_PARTIAL_ARTIFACTS.json',sync)
ds.close()
print(json.dumps({'coverage_variables':coverage['total_active_variables'],'coverage_rows':coverage['total_active_rows'],
 'families':len(families),'partial_cloud_only_bytes':sync['cloud_only_bytes'],'resource':{k:resource[k] for k in ['seconds_to_failure','seconds_to_cloud_seal','peak_worker_ru_maxrss_bytes','peak_cgroup_memory_bytes','min_disk_free_bytes']}},indent=2))
