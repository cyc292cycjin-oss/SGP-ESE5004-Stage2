"""Detached integration, called ONLY after the existing real-run authorization.

No CLI and no implicit authorization. All mathematical operations are the same
ones measured by profile_gate5_lossless.py; run/presolve remain banned there.
"""
import gc,json,weakref
from pathlib import Path
import linopy
from precision_handoff import transfer,ok
from lossless_gate5_lifecycle import save_mapping,trim
from finish_gate5_lossless import consume_native


def prepare_detached(network_owner,scale_owner,source,input_sha,out,labels,factors,progress,result_directory=None):
    """Consume caller's sole owners, return exact native problem and disk mapping."""
    n=network_owner[0];scaling=scale_owner[0]
    native,mapping,fidelity=transfer(n.model,progress=progress,certificate_labels=labels,
                                    certificate_factors=factors,transformation=scaling)
    if fidelity['status']!='PASS':raise ValueError('Incomplete native transfer')
    out=Path(out)
    (out/'SOLVER_TRANSFER_FIDELITY.json').write_text(json.dumps(fidelity,indent=2)+'\n')
    result_dir=Path(result_directory).resolve() if result_directory is not None else (out if str(out.resolve()).startswith('/mnt/d/ResearchWorkspaces/ASEAN/') else Path('/mnt/d/ResearchWorkspaces/ASEAN/work/gate5_native_results')/out.name)
    record=save_mapping(result_dir/'mapping',n,mapping,scaling,source,input_sha)
    record['result_directory']=str(result_dir)
    (result_dir/'mapping/MAPPING_MANIFEST.json').write_text(json.dumps(record,indent=2)+'\n')
    network_ref,scale_ref=weakref.ref(n),weakref.ref(scaling)
    model_id=id(n.model)
    assert gc.is_tracked(n.model)
    dims=(native.getNumCol(),native.getNumRow(),native.getNumNz())
    network_owner[0]=None;scale_owner[0]=None
    del n,scaling,mapping
    trim()
    if network_ref() is not None or scale_ref() is not None or any(id(x)==model_id and isinstance(x,linopy.Model) for x in gc.get_objects()):
        raise ValueError('Source objects still owned before native run')
    if dims!=(native.getNumCol(),native.getNumRow(),native.getNumNz()):raise ValueError('Native dimensions changed')
    progress('source_released_before_run')
    return native,record,fidelity


def execute_prepared(native_owner,record,fidelity,identity,out,options,progress,before_run):
    """Existing guarded runner is the only production caller of this function."""
    out=Path(out)
    if options!={'threads':2,'time_limit':10800,'solver':'ipm','run_crossover':'on'}:
        raise ValueError('Frozen solver options changed')
    h=native_owner[0]
    ok(h.setOptionValue('output_flag',True));ok(h.setOptionValue('log_file',str(out/'gate5_solver.log')))
    for key,value in options.items():ok(h.setOptionValue(key,value))
    before_run(h,fidelity)
    fidelity['solver_run_started']=True
    (out/'SOLVER_TRANSFER_FIDELITY.json').write_text(json.dumps(fidelity,indent=2)+'\n')
    h.run()  # Reachable only from the separately authorized real-run entrypoint.
    del h
    try:
        result_dir=Path(record['result_directory'])
        result=consume_native(native_owner,result_dir,result_dir/'mapping',record,identity,progress)
        result['result_directory']=str(result_dir)
    finally:
        # Preserve qualification even if later mapping or validation raises.
        qp=Path(record['result_directory'])/'native_result/NATIVE_QUALIFICATION.json'
        if qp.exists():
            q=json.loads(qp.read_text())
            fidelity['native_solution_qualification']=q
            fidelity['network_writeback_qualified']=q['network_writeback_qualified']
            fidelity['original_scale_mapping_status']='SEE_NATIVE_RESULT_AND_DYNAMIC_RECEIPTS'
            (out/'SOLVER_TRANSFER_FIDELITY.json').write_text(json.dumps(fidelity,indent=2)+'\n')
    return result
