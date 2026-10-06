"""No optimization or presolve. Small matrices, mocked guards, bounded buffers."""
from pathlib import Path
from types import SimpleNamespace as NS
import json,sys,tempfile,hashlib,tracemalloc,datetime,gc
from unittest.mock import patch
import numpy as np,pandas as pd,linopy,highspy
from gate5_resources import *
from gate5_memory_preflight import authorize
from precision_handoff import digest,transfer
from fixed_inventory_scaling import restore_series_chunks,FixedInventoryScaling

def main(output):
    root=Path(__file__).resolve().parents[1];tests=[]
    def passed(name,**kw):tests.append(dict(test=name,status='PASS',**kw))
    phases=LogPhases()
    for text,expected in [('unrecognised banner','UNKNOWN'),('Presolving model','presolve'),('IPX','IPM'),('108* 1.86e-09 3.99e-04 4.27e11 4.27e11 4.45e-05 4533s','IPM'),('Running crossover as requested','crossover'),('IPX solution is imprecise, so clean up with simplex','simplex_cleanup'),('Solving the original LP from the solution after postsolve','original_model_postsolve'),('Presolving model','original_model_postsolve')]:
        assert phases.feed(text)==expected
    with tempfile.TemporaryDirectory() as d:
        log=Path(d)/'log';log.write_text('Presolving model\nIPX\nRunning cross')
        p=LogPhases();assert p.read(log)=='IPM'
        with log.open('a') as f:f.write('over as requested\n')
        assert p.read(log)=='crossover' and p.read(log)=='crossover'
    passed('incremental_phase_unknown_starred_iteration_no_backward_transition')
    host=dict(physical_available_bytes=20*GIB,commit_available_bytes=20*GIB)
    assert stop_reason(511*MIB,host,10)=='GUEST_AVAILABLE_BELOW_512_MIB'
    assert stop_reason(512*MIB,host,10) is None
    assert stop_reason(4*GIB,dict(host,physical_available_bytes=GIB),10)=='HOST_AVAILABLE_BELOW_2_GIB'
    assert stop_reason(4*GIB,None,10)=='HOST_MONITOR_UNAVAILABLE_OR_STALE'
    assert stop_reason(4*GIB,host,14401)=='WALL_GUARD'
    assert stop_reason(4*GIB,host,10,process_tree_rss=11,process_budget=10)=='PROCESS_TREE_EXCEEDS_DECLARED_BUDGET'
    with tempfile.TemporaryDirectory() as d:
        r={};events=[]
        def save():events.append('save');(Path(d)/'manifest.json').write_text(json.dumps(r))
        def fake_exit(code):
            assert code==3 and json.loads((Path(d)/'manifest.json').read_text())['status']=='STOPPED_RESOURCE_GUARD'
            assert (Path(d)/'RESOURCE_STOP_RECEIPT.json').exists();events.append('exit')
        persist_resource_stop(d,r,dict(available_bytes=511*MIB),'GUEST_AVAILABLE_BELOW_512_MIB',save,fake_exit)
        assert events==['save','exit']
        path=Path(d)/'stale.json';path.write_text(json.dumps(dict(observed_at='2000-01-01T00:00:00+00:00',scope='CURRENT_WINDOWS_HOST')))
        try:host_read(path);raise AssertionError('Stale host accepted')
        except ValueError:pass
    passed('all_guards_and_small_receipt_persist_before_mock_exit')
    child=NS(pid=2,memory_info=lambda:NS(rss=30),memory_full_info=lambda:NS(pss=20))
    parent=NS(pid=1,memory_info=lambda:NS(rss=50),memory_full_info=lambda:NS(pss=40),children=lambda recursive:[child])
    tree=process_tree_sample(parent,include_pss=True)
    assert tree['process_tree_rss_bytes']==80 and [x['pss_bytes'] for x in tree['processes']]==[40,20]
    passed('parent_and_children_RSS_PSS_no_command_line_collection')
    e=current_evidence(root);b=budget(e)
    assert e['run_id']=='gate5_20261006_04' and e['status']=='STOPPED_RESOURCE_GUARD'
    assert b['required_guest_available_bytes']>e['observed_peak_bytes']+512*MIB
    assert admission(e,host,b['required_guest_available_bytes'])['status']=='PASS'
    assert admission(e,host,7*GIB)['status']=='NOT_READY'
    assert admission(e,dict(host,physical_available_bytes=5*GIB),20*GIB)['status']=='NOT_READY'
    assert admission(e,host,20*GIB,cgroups=[{'memory.max':str(8*GIB),'memory.current':'0'}])['status']=='NOT_READY'
    try:authorize(None,root,'gate5_20261006_05');raise AssertionError('Unauthorized run accepted')
    except ValueError:pass
    passed('latest_run_identity_budget_guest_host_cgroup_and_authorization_guards',budget=b)
    def old_digest(*arrays):
        h=hashlib.sha256()
        for a in arrays:
            a=np.ascontiguousarray(a);h.update(str(a.dtype).encode());h.update(str(a.shape).encode());h.update(a.tobytes())
        return h.hexdigest()
    for a in [np.array([0.,-0.,np.inf,-np.inf,np.nan]),np.arange(30,dtype=np.int64).reshape(5,6)[:,::2],np.empty((0,2)),np.array(3.5)]:assert digest(a)==old_digest(a)
    passed('streaming_digest_exact_bytes_contiguous_strided_empty_scalar')
    index=pd.Index([99,4,205,3]);x=np.array([1.234567890123456,-3.,2.**-90,0.]);f=np.array([2.**5,2.**-2,2.**12,1.])
    primal=pd.Series(x.copy(),index=index);dual=pd.Series(x[::-1].copy(),index=index[::-1]);result=NS(solution=NS(primal=primal,dual=dual))
    t=FixedInventoryScaling.__new__(FixedInventoryScaling);t.d=f;t.r=f[::-1]
    t.restore(result)
    assert result.solution.primal is primal and result.solution.dual is dual
    assert np.array_equal(primal.to_numpy(),x*f) and np.array_equal(dual.to_numpy(),x[::-1]*f[::-1])
    assert primal.index.equals(index) and dual.index.equals(index[::-1])
    try:restore_series_chunks(primal,[1.],'bad');raise AssertionError('Length mismatch accepted')
    except ValueError:pass
    passed('chunked_primal_dual_inverse_values_labels_and_series_identity')
    n=600_000;a=np.arange(n,dtype=float)/7;f=np.full(n,2.**8)
    def measure(fn):
        gc.collect();tracemalloc.start();fn();peak=tracemalloc.get_traced_memory()[1];tracemalloc.stop();return peak
    p=pd.Series(a.copy());old=measure(lambda:old_digest(a));new=measure(lambda:digest(a));assert new<old
    def old_restore():
        raw=p.to_numpy(copy=True);p[:]*=f;assert np.array_equal(p.to_numpy()/f,raw)
    base=measure(old_restore);p=pd.Series(a.copy());chunk=measure(lambda:restore_series_chunks(p,f,'synthetic'));assert chunk<base
    assert np.array_equal(p.to_numpy(),a*f)
    passed('small_data_live_allocation_comparison_not_full_model_RSS',entries=n,production_chunk_size=200_000,hash_old_peak_bytes=old,hash_new_peak_bytes=new,restore_old_peak_bytes=base,restore_new_peak_bytes=chunk)
    # Real frozen addRows/getRows exchange, explicitly trap optimizer calls.
    with patch.object(highspy.Highs,'run',side_effect=AssertionError('SOLVER_FORBIDDEN_THIS_ROUND')):
        m=linopy.Model();v=m.add_variables(lower=0,upper=9,coords=[pd.Index(range(4),name='v')],name='x')
        m.add_constraints(1.123456789012345*v>=np.arange(4)+.123456789012345,name='precision')
        m.add_objective((v*2.123456789012345).sum())
        h,mapping,r=transfer(m,slice_size=2)
        assert r['status']=='PASS' and r['max_absolute_transfer_difference']==0 and not r['solver_run_started']
        assert np.array_equal(mapping.matrices.vlabels,v.labels.values)
    passed('small_frozen_float64_transfer_no_Highs_run',variables=r['variables'],constraints=r['constraints'],nnz=r['nnz'])
    output=Path(output);output.write_text(json.dumps(dict(status='PASS',role='MOCK_AND_SMALL_DATA_NO_SOLVER',real_gate5_runs=0,synthetic_solves=0,presolve_calls=0,checks=tests,tested_code_sha256={n:sha(Path(__file__).parent/n) for n in ['gate5_resources.py','gate5_memory_preflight.py','precision_handoff.py','fixed_inventory_scaling.py','run_gate5_stable_inventory.py','test_gate5_resources.py']}),indent=2)+'\n')
if __name__=='__main__':main(sys.argv[1])
