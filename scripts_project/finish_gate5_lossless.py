"""Postsolve consumer for later separately authorized Gate5 execution.

No solver invocation exists here. Consume the only owned native solver, record
one native result, destroy it, then rebuild and map the unchanged frozen input.
Real full-scale postsolve remains unmeasured until a separately authorized solve.
"""
import gc
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pypsa
from gate5_resources import sha
from lossless_gate5_lifecycle import qualify_and_store, release_native, reload_map_validate, trim, sha_index
from fixed_inventory_scaling import physical_checks


def frame_signature(frame):
    # Hash a frame in bounded rows, retaining exact column/index order. Pandas
    # equality considers NaNs equal, so normalize NaN payloads within each chunk.
    h=hashlib.sha256()
    # Index.freq and memoization caches are not part of DataFrame.equals.
    for index in [frame.index,frame.columns]:
        h.update(str(index.dtype).encode())
        h.update(pd.util.hash_pandas_object(index,index=False).to_numpy().tobytes())
    h.update(str(list(frame.dtypes.astype(str))).encode())
    for i in range(0,len(frame),32):
        block=frame.iloc[i:i+32].to_numpy(copy=True)
        if block.dtype.kind=='f':block[np.isnan(block)]=np.nan
        h.update(np.ascontiguousarray(block).tobytes())
    return h.hexdigest()


def export_sequential(owner, output, identity):
    """No simultaneous original and reread PyPSA networks."""
    n=owner[0]
    signatures={(typ,attr):frame_signature(frame)
        for typ in ['Generator','Link','Line','Transformer','Store','StorageUnit','Load']
        for attr,frame in n.pnl(typ).items() if not frame.empty}
    meta=json.dumps(n.meta,sort_keys=True)
    n.export_to_netcdf(output)
    owner[0]=None
    del n
    trim()
    reread=pypsa.Network(output)
    if json.dumps(reread.meta,sort_keys=True)!=meta:raise ValueError('Export metadata changed')
    for (typ,attr),signature in signatures.items():
        if frame_signature(reread.pnl(typ)[attr])!=signature:raise ValueError('Export time series changed: '+typ+'.'+attr)
    strict=physical_checks(reread,identity)
    if not all(x['Status']=='PASS' for x in strict):raise ValueError('Export original-unit checks failed')
    return dict(status='PASS',sha256=sha(output),compared_nonempty_frames=len(signatures),
                method='Exact dtype/order/value signatures with normalized NaN payloads; sequential network lifetimes')


def consume_native(owner, out, mapping_folder, record, identity, progress=lambda phase:None):
    """owner must be the sole [Highs] owner after a separately authorized run."""
    out=Path(out)
    progress('solution_retrieval')
    q=qualify_and_store(owner[0],out/'native_result',mapping_folder,record)
    release_native(owner)
    progress('solver_released_before_mapping')
    if not q['network_writeback_qualified']:
        return dict(status='FAILED_NATIVE_QUALIFICATION',qualification=q,result_network=None,dynamic_checks='NOT_RUN')
    progress('frozen_network_reload_and_original_unit_mapping')
    n,checks,detail=reload_map_validate(record['input_path'],record['input_sha256'],mapping_folder,out/'native_result',record,q,identity)
    # FOM diagnostics and every raw native vector are durable before source-model
    # release. All original-unit checks were run by the unchanged project code.
    model=n.model
    for key,value in list(vars(n).items()):
        if value is model:setattr(n,key,None)
    del model,value
    trim()
    progress('validation_completed')
    (out/'GATE5_DYNAMIC_CHECKS.json').write_text(json.dumps(checks,indent=2)+'\n')
    (out/'GATE5_DYNAMIC_DETAIL.json').write_text(json.dumps(detail,indent=2)+'\n')
    n.meta.update(artifact_role='GATE5_VALIDATION_SOLVED_DYNAMIC_PENDING',scientific_results_allowed=False,
                  formal_phase5_allowed=False,solver_allowed=False,
                  constraint_hook_state='IDENTICAL_FROZEN_REBUILD_MAPPED_FROM_HASHED_NATIVE_SOLUTION')
    progress('export')
    netowner=[n];del n
    exported=export_sequential(netowner,out/'research_2050_gate5_24h_validation_solved.nc',identity)
    dynamic=all(x['Status']=='PASS' for x in checks)
    return dict(status='PASS_PENDING_HUMAN_REVIEW' if dynamic and q['linopy_termination_condition']=='optimal'
                else 'FAILED_DYNAMIC_CHECKS' if not dynamic else 'VALIDATION_FEASIBLE_NOT_OPTIMAL',
                qualification=q,dynamic_checks='PASS' if dynamic else 'FAIL',export=exported,
                gate6_runs=0,phase5_runs=0,formal_scientific_results_allowed=False)
