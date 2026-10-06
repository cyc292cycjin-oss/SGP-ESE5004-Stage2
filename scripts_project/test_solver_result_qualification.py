"""Mocked frozen-interface result states. NO SOLVER CALLS."""
from types import SimpleNamespace as NS
from pathlib import Path
import json,sys
import pandas as pd
from linopy.constants import Result,Solution,Status
from precision_handoff import qualify_native_solution
from run_gate5_stable_inventory import result_route,monitor_phase

def run():
    checks=[]
    for label,value_valid,info_valid,pstatus,condition,expected in [
        ('time_limit_with_zero_placeholder_arrays',False,False,0,'time_limit',False),
        ('infeasible_candidate',True,True,1,'time_limit',False),
        ('feasible_limited_candidate_preserved',True,True,2,'time_limit',True),
        ('optimal_primal_preserved',True,True,2,'optimal',True)]:
        h=NS(getSolution=lambda:NS(value_valid=value_valid,dual_valid=value_valid),getInfo=lambda:NS(valid=info_valid,primal_solution_status=pstatus,dual_solution_status=pstatus),getModelStatus=lambda:condition,modelStatusToString=lambda z:z)
        r=Result(Status.from_termination_condition(condition),Solution(pd.Series([0.] if not expected else [1.]),pd.Series([0.]),0.),h)
        r,q=qualify_native_solution(r,h)
        assert q['native_feasible_primal']==expected
        assert bool(len(r.solution.primal))==expected
        assert r.status.termination_condition.value==condition
        assert r.status.status.value==('ok' if expected else 'warning')
        checks.append(dict(test=label,status='PASS',native_receipt=q))
    assert not result_route('warning','time_limit')['run_dynamic_checks']
    candidate=result_route('ok','time_limit')
    assert candidate['run_dynamic_checks'] and not candidate['optimal'] and candidate['failure_status']=='FAILED_TIME_LIMIT'
    assert result_route('ok','optimal')['optimal']
    phase,seen=monitor_phase('Presolving model',False);assert phase=='presolve' and not seen
    phase,seen=monitor_phase('IPX',seen);assert phase=='solve' and seen
    phase,seen=monitor_phase('73 1.30e-08',seen);assert phase=='solve' and seen
    checks += [dict(test='qualified_limited_primal_routes_to_dynamic_checks_without_gate_pass',status='PASS'),dict(test='solve_stage_does_not_revert_when_header_rolls_off',status='PASS')]
    return dict(status='PASS',role='MOCK_INTERFACE_TEST_ONLY',solver_runs=0,checks=checks)
if __name__=='__main__':Path(sys.argv[1]).write_text(json.dumps(run(),indent=2)+'\n')
