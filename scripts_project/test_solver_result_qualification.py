"""Mocked frozen-interface result states. NO SOLVER CALLS."""
from types import SimpleNamespace as NS
from pathlib import Path
import json,sys,hashlib,tempfile,importlib
import pandas as pd
import numpy as np
import xarray as xr
import linopy,highspy
from unittest.mock import patch
from linopy.constants import Result,Solution,Status
from precision_handoff import qualify_native_solution,research_scalar_assignment,scalar_value_diagnostic,audited_direct_backend
from run_gate5_stable_inventory import result_route
from gate5_resources import LogPhases

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
    phase=LogPhases()
    assert phase.feed('Presolving model')=='presolve'
    assert phase.feed('IPX')=='IPM'
    assert phase.feed('73 1.30e-08')=='IPM'
    checks += [dict(test='qualified_limited_primal_routes_to_dynamic_checks_without_gate_pass',status='PASS'),dict(test='solve_stage_does_not_revert_when_header_rolls_off',status='PASS')]
    h=NS(getSolution=lambda:NS(value_valid=True,dual_valid=True),getInfo=lambda:NS(valid=True,primal_solution_status=2,dual_solution_status=2),getModelStatus=lambda:'optimal',modelStatusToString=lambda z:z)
    for value in [np.nan,np.inf]:
        result=Result(Status.from_termination_condition('optimal'),Solution(pd.Series([value]),pd.Series([0.]),0.),h)
        result,q=qualify_native_solution(result,h)
        assert not q['native_feasible_primal'] and q['nonfinite_primal_count']==1 and not len(result.solution.primal)
    checks.append(dict(test='nonfinite_native_primal_rejected_without_changing_termination',status='PASS'))
    module=importlib.import_module('pypsa.optimization.optimize');original=module.assign_solution
    try:
        with tempfile.TemporaryDirectory() as temp:
            for value,expected in [(0.,False),(np.nan,False),(1.,True)]:
                called=[];dest=Path(temp)/'scalar.json'
                def record_assignment(n):
                    assert dest.exists() # Diagnostics must be durable before mapper call.
                    called.append(True)
                    assert 'Research_existing_FOM_constant' in n.model.variables.data
                module.assign_solution=record_assignment
                variable=NS(solution=xr.DataArray([value]),labels=xr.DataArray([4]))
                n=NS(model=NS(variables=NS(data={'Research-existing-FOM-constant':variable})),all_components={'Generator'})
                try:
                    with research_scalar_assignment(dest):module.assign_solution(n)
                    assert expected
                except ValueError:assert not expected
                d=json.loads(dest.read_text());assert d['all_qualified']==expected and bool(called)==expected
                assert 'Research-existing-FOM-constant' in n.model.variables.data
                assert np.array_equal(variable.solution.values,[value],equal_nan=True)
                checks.append(dict(test='FOM_scalar_'+repr(value),status='PASS',diagnostic=d))
    finally:module.assign_solution=original
    with tempfile.TemporaryDirectory() as temp:
        for value,expected in [(0.,False),(1.,True)]:
            m=linopy.Model();v=m.add_variables(lower=1,upper=1,name='Research-existing-FOM-constant');m.add_objective(1*v)
            label=int(v.labels);dest=Path(temp)/'transfer.json'
            h=NS(getSolution=lambda:NS(value_valid=True,dual_valid=True),getInfo=lambda:NS(valid=True,primal_solution_status=2,dual_solution_status=2),getModelStatus=lambda:'Time limit reached',modelStatusToString=lambda z:z,setOptionValue=lambda *a:highspy.HighsStatus.kOk)
            def mock_solve(self,*args,**kwargs):
                return Result(Status.from_termination_condition('time_limit'),Solution(pd.Series([value],index=[label]),pd.Series(dtype=float),0.),h)
            with patch('precision_handoff.transfer',return_value=(h,NS(),{'status':'PASS'})),patch.object(linopy.solvers.Highs,'_solve',mock_solve):
                with audited_direct_backend(dest):result=linopy.solvers.Highs().solve_problem_from_model(m)
            d=json.loads(dest.read_text());assert d['network_writeback_qualified']==expected
            assert bool(len(result.solution.primal))==expected and result.status.termination_condition.value=='time_limit'
            assert d['custom_scalar_diagnostics_before_mapping'][0]['original_values']==[value]
            checks.append(dict(test='backend_before_writeback_scalar_'+str(value),status='PASS',network_writeback_qualified=expected))
    here=Path(__file__).resolve().parent
    hashes={name:hashlib.sha256((here/name).read_bytes()).hexdigest() for name in ['precision_handoff.py','run_gate5_stable_inventory.py','test_solver_result_qualification.py','fixed_inventory_scaling.py','gate5_resources.py','gate5_memory_preflight.py']}
    return dict(status='PASS',role='MOCK_INTERFACE_TEST_ONLY',solver_runs=0,checks=checks,tested_code_sha256=hashes)
if __name__=='__main__':Path(sys.argv[1]).write_text(json.dumps(run(),indent=2)+'\n')
