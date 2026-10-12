"""C07 immutable input overlay and post-RAW reversible coordinate mapping."""
from pathlib import Path
import sys,hashlib,time,numpy as np
from c02_common import read,write,sha
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'expression'))
from c07_expression import overlay,PowerView,canonicalize_saved_raw

def expression_arrays(run,meta,arrays):
    run=Path(run);a=read(run/'AUTHORIZATION.json');folder=run/'expression';p=folder/'C07_EXPRESSION_BINDING.json'
    assert sha(p)==a['expression_sha256'];e=read(p)
    assert e['expression_id']=='C07_DAILY_RESOURCE_BUDGET_POW2_V1' and e['alpha']==1
    assert sha(run/'bridge/math_problem/MATH_PROBLEM.json')==e['source_math_manifest_sha256']
    assert sha(run/'bridge/mapping/MAPPING_MANIFEST.json')==e['source_mapping_manifest_sha256']
    assert sha(run/'artifacts/DAILY_V4_BINDING.json')==e['source_daily_V4_sha256']
    assert sha(HERE/'V4_APPROVED.json')==e['parent_V4_sha256']
    for name,info in e['files'].items():assert (folder/name).stat().st_size==info['bytes'] and sha(folder/name)==info['sha256']
    D=np.load(run/'bridge/mapping/D.npy',mmap_mode='r');R=np.load(run/'bridge/mapping/R.npy',mmap_mode='r')
    dn=np.load(folder/'D_exponent.npy',mmap_mode='r');rn=np.load(folder/'R_exponent.npy',mmap_mode='r')
    nm,na,delta=overlay(meta,arrays,D,R,dn,rn)
    na['cost_scientific']=PowerView(arrays['cost_scientific'],lambda key:delta['delta_D_exponent'][key])
    hashes={}
    for key,vec in na.items():
        h=hashlib.sha256()
        for s in range(0,len(vec),200000):
            if time.time()>=a['load_absolute_deadline_epoch'] or (run/'STOP_REQUEST.json').exists():raise TimeoutError('EXPRESSION_HASH_PROTECTION_STOP')
            v=np.ascontiguousarray(vec[s:s+200000]);assert not np.isnan(v).any();h.update(v.tobytes())
        hashes[key]=h.hexdigest();assert hashes[key]==e['transformed_array_payload_sha256'][key],key
    write(run/'EXPRESSION_HASH_VERIFICATION.json',{'status':'PASS','expression_sha256':sha(p),'source_math_manifest_sha256':e['source_math_manifest_sha256'],'transformed_array_payload_sha256':hashes,'native_loads_so_far':0,'source_arrays_read_only':True,'numeric_arrays_materialized':False,'reversible_binary64_scaling':True,'alpha':1})
    return nm,na

def canonicalize(run,a,progress):
    run=Path(run);folder=run/'expression';e=read(folder/'C07_EXPRESSION_BINDING.json');assert sha(folder/'C07_EXPRESSION_BINDING.json')==a['expression_sha256']
    oldD=np.load(run/'bridge/mapping/D.npy',mmap_mode='r');oldR=np.load(run/'bridge/mapping/R.npy',mmap_mode='r')
    dn=np.load(folder/'D_exponent.npy',mmap_mode='r');rn=np.load(folder/'R_exponent.npy',mmap_mode='r')
    dd=dn-np.rint(np.log2(oldD)).astype('<i2');rr=rn-np.rint(np.log2(oldR)).astype('<i2')
    progress('CANONICAL_MAPPING_START')
    dest=run/'canonical_raw_for_V4'
    receipt=canonicalize_saved_raw(run/'raw',dest,dd,rr,a['expression_sha256'],min(a['post_absolute_deadline_epoch'],read(run/'PHASE.json')['entered_epoch']+1200),lambda:(run/'STOP_REQUEST.json').exists())
    assert len(receipt['vectors'])==3
    write(run/'C07_CANONICAL_MAPPING.json',{'status':'PASS','expression_sha256':a['expression_sha256'],'native_raw_receipt_sha256':sha(run/'raw/vectors/RAW_RECEIPT.json'),'canonical_receipt_sha256':sha(dest/'vectors/RAW_RECEIPT.json'),'native_quality_attributes_relabelled':False,'native_vectors_preserved':True,'no_solution_repair':True,'formula':e['mapping'],'old_V4_binding_sha256':e['source_daily_V4_sha256']})
    progress('CANONICAL_MAPPING_COMPLETE');return dest
