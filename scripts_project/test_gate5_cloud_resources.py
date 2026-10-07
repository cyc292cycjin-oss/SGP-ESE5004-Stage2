"""No native solve: cgroup, unchanged guards, durable one-call claim and paths."""
import json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
import highspy,pypsa,pandas as pd
from gate5_cloud_resources import *
from gate5_resources import current_evidence,budget
from test_gate5_lossless_integration import IdentityScaling
from execute_gate5_lossless import prepare_detached
from gate5_cloud_preflight import checked_file,environment_identity
from gate5_cloud_worker import collect,validate_dispatch


def run():
    checks=[]
    def passed(name):checks.append(dict(test=name,status='PASS'))
    def rejected(fn):
        try:fn()
        except (ValueError,FileExistsError):return
        raise AssertionError('Invalid case accepted')
    root=Path(__file__).resolve().parents[1];e=current_evidence(root);b=budget(e)
    r=effective_resources([{'memory.max':str(90*GIB),'memory.current':str(GIB),'cpu.max':'2500000 100000'},
                           {'memory.max':str(80*GIB),'memory.current':str(2*GIB),'cpu.max':'200000 100000'}],754*GIB,700*GIB,64)
    assert r==dict(effective_memory_limit_bytes=80*GIB,effective_available_bytes=78*GIB,effective_cpu_cores=2.)
    passed('ancestor_memory_and_cpu_caps_override_host_free_memory')
    rejected(lambda:effective_resources([{'memory.max':'max'}],754*GIB,700*GIB,64))
    rejected(lambda:effective_resources([{'memory.max':'9'}],754*GIB,700*GIB,64))
    passed('missing_finite_limit_or_usage_fails_closed')
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp);base=p/'cgroup';child=base/'a'/'b';child.mkdir(parents=True)
        membership=p/'membership';membership.write_text('0::/a/b\n')
        for folder in [base,base/'a',child]:
            (folder/'memory.max').write_text(str(90*GIB));(folder/'memory.current').write_text('0')
        rows=cgroup_rows(base,membership);assert len(rows)==3
        membership.write_text('0::/../../escape\n');rejected(lambda:cgroup_rows(base,membership))
    passed('cgroup_membership_all_ancestors_and_path_escape')
    obs=dict(scope='CURRENT_LINUX_CGROUP',effective_available_bytes=b['required_guest_available_bytes']+2*GIB,
             effective_memory_limit_bytes=90*GIB,effective_cpu_cores=2.,disk=dict(free_bytes=20*GIB))
    assert admission(e,obs)['status']=='PASS'
    assert admission(e,{**obs,'effective_available_bytes':obs['effective_available_bytes']-1})['status']=='NOT_READY'
    assert admission(e,{**obs,'effective_cpu_cores':1.9})['status']=='NOT_READY'
    assert admission(e,{**obs,'disk':{'free_bytes':20*GIB-1}})['status']=='NOT_READY'
    rejected(lambda:admission(e,{**obs,'scope':'CURRENT_WINDOWS_HOST'}))
    passed('original_physical_requirement_and_two_threads_and_disk_and_scope')
    assert stop_reason(511*MIB,obs,0)=='GUEST_AVAILABLE_BELOW_512_MIB'
    assert stop_reason(GIB,None,0)=='CLOUD_RESOURCE_MONITOR_UNAVAILABLE'
    assert stop_reason(GIB,{**obs,'effective_available_bytes':2*GIB-1},0)=='CLOUD_AVAILABLE_BELOW_2_GIB'
    assert stop_reason(GIB,obs,14401)=='WALL_GUARD'
    assert stop_reason(GIB,obs,0,process_tree_rss=11,process_budget=10)=='PROCESS_TREE_EXCEEDS_DECLARED_BUDGET'
    assert stop_reason(GIB,obs,14400,process_tree_rss=10,process_budget=10) is None
    passed('unchanged_512MiB_2GiB_wall_and_declared_RSS_guards')
    assert validate_run_path('/root/autodl-tmp/SGP/runs/cloud_gate5_test')==Path('/root/autodl-tmp/SGP')
    rejected(lambda:validate_run_path('/root/cloud_gate5_test'))
    rejected(lambda:validate_run_path('/root/autodl-tmp/SGP/runs/old_run'))
    passed('data_disk_and_unique_cloud_run_namespace')
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp);(p/'evidence').mkdir();a=p/'authorization.json'
        a.write_text(json.dumps(dict(authorization_id='a'*64,run_id='cloud_gate5_test',max_attempts=1)))
        claim_once(a,p/'runs/cloud_gate5_test',p)
        rejected(lambda:claim_once(a,p/'runs/cloud_gate5_test',p))
        a.write_text(json.dumps(dict(authorization_id='a'*64,run_id='cloud_gate5_other',max_attempts=1)))
        rejected(lambda:claim_once(a,p/'runs/cloud_gate5_other',p))
    passed('durable_authorization_claim_rejects_replay_and_new_run_id')
    with patch.object(highspy.Highs,'run',side_effect=AssertionError('NO SOLVE')),patch.object(highspy.Highs,'presolve',side_effect=AssertionError('NO PRESOLVE')):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);out=p/'run';out.mkdir();destination=p/'portable-results'
            n=pypsa.Network();n.set_snapshots(pd.date_range('2050',periods=3,freq='h'))
            n.add('Bus','b');n.add('Generator','g',bus='b',p_nom=10.,marginal_cost=2.)
            n.add('Load','l',bus='b',p_set=[1.,2.,3.]);n.optimize.create_model()
            no=[n];so=[IdentityScaling()];del n
            h,record,fidelity=prepare_detached(no,so,'synthetic','synthetic',out,[],{},lambda *args:None,result_directory=destination)
            assert fidelity['status']=='PASS' and not fidelity['solver_run_started']
            assert Path(record['result_directory'])==destination and (destination/'mapping/MAPPING_MANIFEST.json').is_file()
            assert no[0] is None and so[0] is None
            h.clear();del h
    passed('explicit_cloud_result_path_exact_transfer_and_release_without_solve')
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp);(p/'input').write_bytes(b'frozen')
        h=hashlib.sha256(b'frozen').hexdigest()
        assert checked_file(p,'input',h)==p/'input'
        rejected(lambda:checked_file(p,'input','0'*64))
        rejected(lambda:checked_file(p,'missing',h))
        rejected(lambda:checked_file(p,'../input',h))
        rejected(lambda:checked_file(p,'/absolute',h))
    passed('preflight_file_hash_missing_file_and_traversal_fail_closed')
    rejected(lambda:environment_identity({'distributions':[{'name':'pypsa','version':'0.0.0'}]}))
    passed('environment_version_conflict_fails_closed_without_upgrade')
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp);out=p/'run';out.mkdir()
        raw=dict(status='PASS',solver_runs=1,objective=123.,result_network='unqualified.nc',dynamic_checks='PASS',export_roundtrip='PASS',
                 native_solution_qualification=dict(network_writeback_qualified=False,linopy_termination_condition='optimal'))
        (out/'GATE5_VALIDATION_RUN_MANIFEST.json').write_text(json.dumps(raw))
        result=collect(out,0,{})
        assert not result['gate5_pass'] and result['objective'] is None and result['result_network'] is None and result['dynamic_checks']=='NOT_RUN'
        raw['native_solution_qualification']['network_writeback_qualified']=True
        raw['native_solution_qualification']['linopy_termination_condition']='time_limit'
        (out/'GATE5_VALIDATION_RUN_MANIFEST.json').write_text(json.dumps(raw));assert not collect(out,0,{})['gate5_pass']
        raw['native_solution_qualification']['linopy_termination_condition']='optimal'
        (out/'GATE5_VALIDATION_RUN_MANIFEST.json').write_text(json.dumps(raw));assert not collect(out,0,{})['gate5_pass']
        network=out/'test.nc';network.write_bytes(b'fixture-only')
        raw.update(result_network=str(network),result_sha256=hashlib.sha256(network.read_bytes()).hexdigest())
        (out/'GATE5_VALIDATION_RUN_MANIFEST.json').write_text(json.dumps(raw))
        (out/'GATE5_DYNAMIC_CHECKS.json').write_text(json.dumps([dict(Check='OBJECTIVE_RECONCILIATION',Status='PASS')]))
        (out/'GATE5_DYNAMIC_DETAIL.json').write_text(json.dumps(dict(objective_reconciliation=dict(capital=1.,variable=2.,known_fixed_once=3.,actual=6.))))
        assert collect(out,0,{})['gate5_pass']
        assert not collect(out,-9,{})['gate5_pass']
        missing=p/'missing-manifest';assert collect(missing,125,{})['solver_runs']==0
    passed('durable_collector_unqualified_nulls_time_limit_and_crash_never_pass')
    return dict(status='PASS',solver_runs=0,presolve_calls=0,checks=checks)

if __name__=='__main__':Path(sys.argv[1]).write_text(json.dumps(run(),indent=2)+'\n')
