"""SYNTHETIC engineering fixtures only. Never a production solution/witness."""
import copy,json,tempfile,sys
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import numpy as np,pandas as pd,pypsa,highspy
import run_gate6_baseline as entry
import gate6_result as result
from inventory_audit_3h import source_bound,prefix_check
from gate6_fixed_term_contract import compare
from test_gate5_lossless_integration import IdentityScaling
from test_lossless_export import edge_network
from execute_gate5_lossless import prepare_detached
from test_gate6_authorization_flow import ready_context

def run(root,out):
    checks=[];out=Path(out)
    def yes(name):checks.append(dict(test=name,status='PASS',fixture='SYNTHETIC_NOT_SCIENTIFIC_RESULT'))
    def reject(action):
        try:action()
        except (ValueError,TypeError,OverflowError,FileNotFoundError):return
        raise AssertionError('Negative case accepted')
    with patch.object(highspy.Highs,'run',side_effect=AssertionError('REAL RUN FORBIDDEN')) as native_run,patch.object(highspy.Highs,'presolve',side_effect=AssertionError('PRESOLVE FORBIDDEN')) as presolve,patch.object(highspy.Highs,'getSolution',side_effect=AssertionError('NATIVE GETSOLUTION FORBIDDEN')) as get_solution:
        n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=2920,freq='3h'));n.snapshot_weightings[:]=3.
        entry.validate_temporal(n);yes('2920_3h_8760_hours')
        n.snapshot_weightings.iloc[0,0]=2.;reject(lambda:entry.validate_temporal(n));n.snapshot_weightings[:]=3.
        n.set_snapshots(n.snapshots[:-1]);reject(lambda:entry.validate_temporal(n))
        n.set_snapshots(pd.date_range('2013-01-01',periods=365,freq='24h'));n.snapshot_weightings[:]=24.;reject(lambda:entry.validate_temporal(n));yes('wrong_weights_missing_step_daily_input_rejected')
        wrong=out/'wrong_input.nc';wrong.write_bytes(b'SYNTHETIC WRONG SHA')
        with patch('run_gate6_baseline.pypsa.Network',side_effect=AssertionError('Wrong SHA must reject before load')):
            reject(lambda:entry.dispatch(root,out/'wrong_sha_preflight','preflight',source=wrong))
        yes('actual_entry_wrong_SHA_rejected_before_network_load')
        for mode in ['build','solve']:
            with patch('run_gate6_baseline.preflight',side_effect=AssertionError('No auth must stop before preflight/full build')):
                reject(lambda:entry.dispatch(root,out/'unauthorized',mode))
                old=out/('old_gate5_'+mode+'.json');old.write_text(json.dumps(dict(gate='GATE5',real_gate5_authorized=True,max_attempts=1)))
                reject(lambda:entry.dispatch(root,out/'old_gate5',mode,old))
        yes('actual_entry_rejects_no_authorization_and_old_gate5_for_build_and_solve')
        p=np.ones(2920,dtype=np.float64);w=np.full(2920,3.,dtype=np.float64);initial=8760.;e=initial-np.cumsum(p*w)
        bound=source_bound(p,w,[initial],1)
        assert bound['exact_binary64_annual_equality'] and bound['daily_mean_operations']==0
        assert prefix_check(initial,p,e,w,bound['original_energy_error_bound_mwh'])['status']=='PASS'
        damaged=e.copy();damaged[1200]+=1.;assert prefix_check(initial,p,damaged,w,bound['original_energy_error_bound_mwh'])['status']=='FAIL'
        reject(lambda:source_bound(p,w,[8759.],1));reject(lambda:source_bound(p,w,[8761.],1))
        reject(lambda:source_bound(p.astype(np.float32),w,[initial],1));bad=w.copy();bad[0]=np.nan;reject(lambda:source_bound(p,bad,[initial],1))
        assert prefix_check(8759.,p,8759.-np.cumsum(p*w),w,bound['original_energy_error_bound_mwh'])['status']=='FAIL'
        yes('hand_feasible_2920_prefix_terminal_witness_and_true_shortage_surplus_float32_nonfinite_rejection')
        # Explicit physical port equation; this is the same check function used postsolve.
        from fixed_inventory_scaling import physical_checks
        tiny=pypsa.Network();tiny.set_snapshots(pd.date_range('2013-01-01',periods=2920,freq='3h'));tiny.snapshot_weightings[:]=3.
        tiny.add('Bus','源');tiny.add('Bus','用')
        tiny.add('Store','stock',bus='源',e_nom=initial,e_initial=initial,e_cyclic=False)
        tiny.add('Link','meter',bus0='源',bus1='用',efficiency=1.,p_nom=2.)
        tiny.stores_t.p=pd.DataFrame({'stock':p},index=tiny.snapshots);tiny.stores_t.e=pd.DataFrame({'stock':e},index=tiny.snapshots)
        tiny.links_t.p0=pd.DataFrame({'meter':p},index=tiny.snapshots);tiny.links_t.p1=pd.DataFrame({'meter':-p},index=tiny.snapshots)
        tiny.add('Load','load',bus='用',p_set=p);tiny.meta={'biomass_obligation_routes':{'stock':{'meter':'meter','buses':['用']}}}
        ident={'groups':[dict(group=0,source_account_id='SYNTHETIC_ONLY',load='load',stores=['stock'],**bound)]}
        tiny.links.at['meter','p_nom_opt']=2.
        with patch('fixed_accounts.validate_exported_accounting'):
            assert all(r['Status']=='PASS' for r in physical_checks(tiny,ident))
            tiny.links.at['meter','efficiency']=0.9;tiny.links_t.p1['meter']=-0.9*p
            assert any(r['Status']=='FAIL' for r in physical_checks(tiny,ident))
        yes('real_physical_validator_rejects_wrong_efficiency_2920_steps')
        # A few components but the full 2920-step temporal axis; no solve.
        tiny.links.at['meter','efficiency']=1.;tiny.links_t.p1['meter']=-p;tiny.stores.at['stock','marginal_cost']=1.
        tiny.optimize.create_model();no=[tiny];so=[IdentityScaling()];del tiny
        target=out/'tiny2920';target.mkdir()
        h,record,fidelity=prepare_detached(no,so,'SYNTHETIC_ONLY','SYNTHETIC_ONLY',target,[],{},lambda *x:None,result_directory=target)
        assert no[0] is None and so[0] is None and fidelity['status']=='PASS'
        assert h.getNumCol()<20000;h.clear();del h
        yes('few_component_2920_native_float64_transfer_and_source_release')
        events=[]
        class Fake:
            def setOptionValue(self,k,v):events.append((k,v));return highspy.HighsStatus.kOk
            def run(self):events.append('MOCK_RUN')
        def consume(owner,*args):events.append('CONSUME');owner[0]=None;return {'status':'SYNTHETIC_TEST_ONLY'}
        owner=[Fake()];context=ready_context(out/'native_boundary_context')
        with patch('run_gate6_baseline.consume',consume):
            entry.execute_native(owner,target,record,fidelity,ident,entry.read(Path(root)/entry.CONFIG),lambda *x:None,lambda:events.append('AUTHORIZED_BOUNDARY'),context)
        context.close()
        assert events.index('AUTHORIZED_BOUNDARY')<events.index('MOCK_RUN')<events.index('CONSUME') and events.count('MOCK_RUN')==1 and owner[0] is None
        for option in [('threads',2),('solver','ipm'),('run_crossover','on'),('presolve','on'),('time_limit',86400)]:assert option in events
        yes('new_execution_boundary_mock_once_keeps_IPM_crossover_presolve_two_threads')
        # Gate6 result consumer qualifies once and refuses any mapping on failure.
        from lossless_gate5_lifecycle import write_array
        mf=out/'qual_map';mf.mkdir();arrays={}
        for key,v,dtype in [('vlabels',[0],np.int32),('clabels',[0],np.int32),('D',[1.],np.float64),('R',[1.],np.float64)]:arrays[key]=write_array(mf/(key+'.npy'),v,dtype)
        rec=dict(arrays=arrays,model_shape=[1,1],research_scalars=[])
        for label,valid,value,info,expected in [('placeholder',False,0.,True,False),('nan',True,np.nan,True,False),('inf',True,np.inf,True,False),('invalid_info',True,1.,False,False)]:
            folder=out/label;folder.mkdir();import shutil;shutil.copytree(mf,folder/'mapping')
            calls=[]
            def get():calls.append(1);return NS(value_valid=valid,dual_valid=False,col_value=[value],col_dual=[0.],row_value=[0.],row_dual=[0.])
            native=NS(getSolution=get,getInfo=lambda:NS(valid=info,primal_solution_status=2,dual_solution_status=0),getModelStatus=lambda:highspy.HighsModelStatus.kOptimal,modelStatusToString=lambda x:'Optimal',getObjectiveValue=lambda:1.,clear=lambda:None)
            context=ready_context(out/(label+'_context'),solved=True)
            with patch('gate6_result.reload_map_validate',side_effect=AssertionError('Unqualified solution must never map')):
                returned=result.consume([native],folder,rec,{},lambda *x:None,context)
            context.close()
            assert returned['status']=='FAILED_NATIVE_QUALIFICATION' and len(calls)==1
        yes('new_consumer_once_getSolution_no_invalid_placeholder_or_nonfinite_writeback')
        # Metadata finalization tests use synthetic values, not Gate5 dispatch.
        account=dict(PricedObjective=None,KnownFixedCost=2.,KnownFixedCostIncludedInPricedObjective=None,KnownFixedCostToAddToPricedObjective=None)
        old=dict(accounting_report=account,external_pending_fixed_accounts=[dict(UnitPriceEUR2020PerMWh=None,PhysicalCO2_tPerMWh=None) for _ in range(807)],physical_carbon_map=[dict(policy_weight=None) for _ in range(200)])
        for k in ['scientific_results_allowed','policy_enabled','FullSystemCostComplete','FullSystemEmissionsComplete','full_system_cost_complete','full_system_emissions_complete']:old[k]=False
        q=dict(network_writeback_qualified=True,linopy_termination_condition='optimal',native_getSolution_calls=1,objective=12.,model_status='Optimal')
        checks_mock=[dict(Check='OBJECTIVE_RECONCILIATION',Status='PASS')]
        detail=dict(accounting_report={**account,'PricedObjective':12.,'KnownFixedCostIncludedInPricedObjective':True,'KnownFixedCostToAddToPricedObjective':0.},objective_reconciliation=dict(actual=12.,known_fixed_once=2.))
        for ck,ex in [([],dict(status='PASS',sha256='test')),([dict(Check='OBJECTIVE_RECONCILIATION',Status='FAIL')],dict(status='PASS',sha256='test')),(checks_mock,dict(status='FAIL',sha256='test'))]:reject(lambda:result.accepted_metadata(old,q,ck,detail,ex,{},'test'))
        bad_detail=copy.deepcopy(detail);bad_detail['accounting_report']['KnownFixedCostToAddToPricedObjective']=2.;reject(lambda:result.accepted_metadata(old,q,checks_mock,bad_detail,dict(status='PASS',sha256='test'),{},'test'))
        n=edge_network();n.meta=old;n.objective=12.;parent=out/'synthetic_pending.nc'
        from finish_gate5_lossless import export_complete_timeseries
        export_complete_timeseries(n,parent);ex=dict(status='PASS',sha256=entry.sha(parent))
        final=result.finalize(parent,out/'synthetic_final.nc',q,checks_mock,detail,ex,dict(test_only=True))
        assert final['scientific_data_unchanged'];reread=pypsa.Network(final['result_network'])
        assert reread.meta['accounting_report']['PricedObjective']==12. and reread.meta['current_result_qualification']['status']=='PASS'
        assert reread.meta['policy_enabled'] is False and old['accounting_report']['PricedObjective'] is None
        yes('new_metadata_requires_dynamic_export_pass_FOM_once_exact_signed_zero_Unicode_NaN_roundtrip')
        # Exercise Gate6's complete positive postsolve sequence with a labelled mock primal.
        positive=out/'positive_consumer';positive.mkdir();shutil.copytree(mf,positive/'mapping')
        (positive/'GATE6_INPUT_LOCK.json').write_text('{"fixture":"SYNTHETIC_ONLY"}')
        context=ready_context(out/'positive_consumer_context',solved=True)
        def synthetic_mapping(*args,execution_context=None):
            assert execution_context is context
            mapped,_=context.build_network('reconstruction')
            mapped.meta.update(copy.deepcopy(old));mapped.objective=12.
            return mapped,checks_mock,detail
        calls=[]
        def positive_get():calls.append(1);return NS(value_valid=True,dual_valid=False,col_value=[1.],col_dual=[0.],row_value=[0.],row_dual=[0.])
        native=NS(getSolution=positive_get,getInfo=lambda:NS(valid=True,primal_solution_status=2,dual_solution_status=0),getModelStatus=lambda:highspy.HighsModelStatus.kOptimal,modelStatusToString=lambda x:'Optimal',getObjectiveValue=lambda:12.,clear=lambda:None)
        phases=[]
        with patch('gate6_result.reload_map_validate',side_effect=synthetic_mapping),patch('finish_gate5_lossless.physical_checks',return_value=[{'Status':'PASS'}]):
            accepted=result.consume([native],positive,{**rec,'input_path':'SYNTHETIC_ONLY','input_sha256':'SYNTHETIC_ONLY'},{'groups':[]},lambda stage:phases.append(stage),context)
        assert accepted['status']=='PASS' and len(calls)==1
        assert phases.index('native_released')<phases.index('postsolve_rebuild_mapping')<phases.index('export_readback')<phases.index('metadata_finalization')
        yes('new_consumer_positive_mock_one_read_durable_vectors_release_map_validate_export_then_finalize')
        original_signature=result.netcdf_science_signature
        def corrupt(path):
            if str(path).endswith('.partial.nc'):
                import netCDF4
                with netCDF4.Dataset(path,'r+') as ds:ds.variables['generators_t_p'][0,0]=np.nextafter(ds.variables['generators_t_p'][0,0],np.inf)
            return original_signature(path)
        bad_output=out/'bad_gate6_final.nc'
        with patch('gate6_result.netcdf_science_signature',corrupt):reject(lambda:result.finalize(parent,bad_output,q,checks_mock,detail,ex,{}))
        assert not bad_output.exists() and not bad_output.with_suffix('.partial.nc').exists()
        yes('new_finalizer_one_ULP_rejected_partial_never_valid_result')
        from carbon_architecture import install_power_policy
        reject(lambda:install_power_policy(NS(),[dict(policy_weight=None,accepted=False)],2050,enabled=True,scope_complete=False,expected_hours=8760))
        yes('DEC_pending_enabled_rejected')
        a=dict(terms=[dict(source_id='source',commodity='wood',quantity_mwh='0x1.0p+0',time_weights='3h',exclusive_final_buses=['use'],price_boundary=None,store_direction='discharge_only')])
        assert compare(a,copy.deepcopy(a))['cost_cancellation_proven'] is False
        for key in a['terms'][0]:
            b=copy.deepcopy(a);b['terms'][0][key]='CHANGED';reject(lambda:compare(a,b))
        yes('fixed_term_contract_rejects_each_boundary_change_no_cancellation_claim')
        budget=entry.read(Path(root)/entry.CONFIG)['proposed_budget'];obs=dict(effective_available_bytes=84*entry.GIB,effective_cpu_cores=2,disk=dict(free_bytes=40*entry.GIB))
        assert entry.resource_admission(obs,budget)['status']=='PASS'
        for key,value in [('effective_available_bytes',82*entry.GIB),('effective_cpu_cores',1)]:
            bad={**obs,key:value};assert entry.resource_admission(bad,budget)['status']=='NOT_READY'
        assert entry.guard_reason(obs,76*entry.GIB,0,budget)=='PROCESS_TREE_RSS_GUARD'
        assert entry.guard_reason(None,0,0,budget)=='RESOURCE_MONITOR_UNAVAILABLE'
        assert entry.guard_reason(obs,0,108001,budget)=='WALL_GUARD'
        yes('Gate6_resource_budgets_fail_closed_for_all_lifecycle_phases')
        assert native_run.call_count==presolve.call_count==get_solution.call_count==0
    return dict(status='PASS',solver_calls=0,presolve_calls=0,getSolution_calls=0,checks=checks,full_gate6_model_built=False)

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];p=Path(sys.argv[1]);p.write_text(json.dumps(run(root,p.parent),indent=2)+'\n')
