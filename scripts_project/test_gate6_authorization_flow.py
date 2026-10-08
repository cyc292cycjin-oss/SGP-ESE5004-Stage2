"""TEST_ONLY: real authorization/claim/build/hooks, bounded four-step network."""
import copy,hashlib,json,os,shutil,subprocess,sys,weakref
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import highspy,numpy as np,pandas as pd,pypsa,netCDF4
from gate6_execution_context import validate_authorization,claim_execution,checked
from assembly_components import install_research_constraint_hooks,validate_hooks
from gate5_resources import sha

BUDGET=dict(start_available_gib=83,tree_rss_limit_gib=75,headroom_guard_gib=8,start_disk_free_gib=30,solver_seconds=86400,wall_seconds=108000)
OBS=dict(effective_available_bytes=84*1024**3,effective_cpu_cores=2,disk=dict(free_bytes=40*1024**3))
HOOKS={'ResearchImportAnnual-supply','ResearchStoreDirection-inventory','ResearchBatteryNominal-0'}
def write(p,obj):Path(p).write_text(json.dumps(obj,indent=2)+'\n')
def reject(call):
    try:call()
    except (ValueError,FileExistsError):return
    raise AssertionError('Invalid TEST_ONLY authorization was accepted')
def validate_fixture(n):
    assert n.meta.get('fixture')=='TEST_ONLY' and len(n.snapshots)==4 and len(n.buses)==2
    assert n.meta.get('scientific_results_allowed') is False
    assert n.meta.get('formal_phase5_allowed') is False
    assert n.snapshot_weightings.to_numpy().dtype==np.float64
    np.testing.assert_array_equal(n.snapshot_weightings.to_numpy(),3.)
    validate_hooks(n)
def fixture(path,stage='solve',metadata_override=None):
    path=Path(path);path.mkdir(parents=True,exist_ok=False);root=path/'repo';root.mkdir();runs=path/'runs';runs.mkdir();(path/'evidence').mkdir()
    n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=4,freq='3h'));n.snapshot_weightings[:]=3.
    for c in ('AC','battery'):n.add('Carrier',c)
    n.add('Bus','ac',carrier='AC');n.add('Bus','battery',carrier='battery')
    n.add('Generator','supply',bus='ac',carrier='AC',p_nom=3.,marginal_cost=2.)
    n.add('Load','demand',bus='ac',p_set=0.)
    n.add('Store','inventory',bus='battery',e_nom=12.,e_initial=0.,e_cyclic=False)
    n.add('Link','charge',bus0='ac',bus1='battery',efficiency=.9,p_nom_extendable=True,capital_cost=1.)
    n.add('Link','discharge',bus0='battery',bus1='ac',efficiency=.8,p_nom_extendable=True,capital_cost=1.)
    n.meta=dict(fixture='TEST_ONLY',artifact_role='GATE6_TEST_ONLY_FROZEN_INPUT',solver_allowed=False,scientific_results_allowed=False,formal_phase5_allowed=False,
        required_constraint_hooks=['install_fragment_constraints','research_battery_inverter_capacity_equality'],external_annual_caps={'supply':10.},store_power_rules={'inventory':'discharge_only'},battery_inverter_pairs=[dict(charger='charge',discharger='discharge')])
    n.meta.update(metadata_override or {})
    source=root/'TEST_ONLY_input.nc';n.export_to_netcdf(source);del n
    shutil.copyfile(Path(__file__).with_name('gate6_execution_context.py'),root/'tested_execution_code.py')
    cfg=dict(fixture='TEST_ONLY',input='TEST_ONLY_input.nc',input_sha256=sha(source),lock='lock.json',tests='tests.json',proposed_budget=BUDGET)
    write(root/'config.json',cfg)
    entries=[dict(path=p,size_bytes=(root/p).stat().st_size,sha256=sha(root/p)) for p in ['TEST_ONLY_input.nc','tested_execution_code.py','config.json']]
    write(root/'lock.json',dict(gate='GATE6',input_sha256=sha(source),files=entries,fixture='TEST_ONLY'))
    write(root/'tests.json',dict(status='PASS',fixture='TEST_ONLY',solver_calls=0,presolve_calls=0,getSolution_calls=0,input_lock_sha256=sha(root/'lock.json'),tested_code_sha256={'tested_execution_code.py':sha(root/'tested_execution_code.py')}))
    def git(*args):return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.DEVNULL,text=True).strip()
    git('init','-q');git('config','user.name','TEST_ONLY');git('config','user.email','test-only@example.invalid');git('add','.');git('commit','-qm','TEST_ONLY isolated fixture identity')
    run_id='cloud_gate6_TEST_ONLY_'+stage;out=runs/run_id
    a=dict(gate='GATE6',scenario='BASELINE',stage=stage,human_authorized=True,human_decision_reference='TEST_ONLY synthetic authorization, not a production grant',max_attempts=1,budget_approved=True,budget=BUDGET,
        input_sha256=sha(source),code_sha=git('rev-parse','HEAD'),input_lock_sha256=sha(root/'lock.json'),tests_sha256=sha(root/'tests.json'),run_id=run_id,authorization_id=hashlib.sha256(str(path).encode()).hexdigest(),fixture='TEST_ONLY')
    auth=path/'TEST_ONLY_authorization.json';write(auth,a)
    return NS(root=root,cfg=cfg,runs=runs,out=out,auth=auth,a=a,source=source,stage=stage)
def claim(f,observation=OBS):return claim_execution(f.root,f.cfg,f.stage,f.out,f.auth,expected_input_sha=f.cfg['input_sha256'],runs_root=f.runs,observation=observation,network_validator=validate_fixture,test_only=True)
def ready_context(path,stage='solve',solved=False):
    f=fixture(path,stage);ctx=claim(f);f.out.mkdir();n,_=ctx.build_network();assert HOOKS<=set(n.model.constraints);del n
    if solved:ctx.begin_solve(NS());ctx.finish_solve()
    return ctx

def run(root,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);checks=[];negative=[]
    def yes(name,**details):checks.append(dict(check=name,status='PASS',fixture='TEST_ONLY',**details))
    with patch.object(highspy.Highs,'run',side_effect=AssertionError('NO REAL RUN')) as nr,patch.object(highspy.Highs,'presolve',side_effect=AssertionError('NO PRESOLVE')) as npresolve,patch.object(highspy.Highs,'getSolution',side_effect=AssertionError('NO NATIVE GETSOLUTION')) as ng:
        f=fixture(out/'positive');source_hash=sha(f.source)
        raw=pypsa.Network(f.source);raw.optimize.create_model()
        reject(lambda:install_research_constraint_hooks(raw));raw.meta['solver_allowed']=True
        reject(lambda:install_research_constraint_hooks(raw));reject(lambda:install_research_constraint_hooks(raw,NS(authorized=True)))
        yes('A_D_frozen_false_and_handwritten_true_or_fake_context_rejected');del raw
        original=f.auth.read_bytes()
        for label,change in [('wrong_run',{'run_id':'cloud_gate6_OTHER'}),('wrong_input',{'input_sha256':'0'*64}),('wrong_code',{'code_sha':'0'*40}),('wrong_stage',{'stage':'build'}),('old_gate5',{'gate':'GATE5'}),('missing_human',{'human_authorized':False}),('unapproved_budget',{'budget_approved':False}),('wrong_lock',{'input_lock_sha256':'0'*64}),('wrong_tests',{'tests_sha256':'0'*64})]:
            write(f.auth,{**f.a,**change})
            reject(lambda:claim(f));negative.append(dict(case=label,status='REJECTED'))
        f.auth.write_bytes(original)
        reject(lambda:validate_authorization(f.root,f.cfg,'test',f.out,f.auth,f.cfg['input_sha256'],f.runs))
        reject(lambda:validate_authorization(f.root,f.cfg,'preflight',f.out,f.auth,f.cfg['input_sha256'],f.runs))
        reject(lambda:claim(f,{**OBS,'effective_available_bytes':82*1024**3}));negative.append(dict(case='insufficient_resources',status='REJECTED'))
        ctx=claim(f);claim_hash=sha(ctx._claim);reject(lambda:claim(f));negative.append(dict(case='duplicate_claim',status='REJECTED'));f.out.mkdir()
        for path,label in [(f.auth,'authorization_mutated_after_claim'),(ctx._claim,'claim_mutated_after_claim'),(f.root/'tested_execution_code.py','code_mutated_after_claim')]:
            frozen=path.read_bytes();path.write_bytes(frozen+b'\n ')
            reject(lambda:ctx.build_network());path.write_bytes(frozen)
            negative.append(dict(case=label,status='REJECTED'))
        n,_=ctx.build_network();assert HOOKS<=set(n.model.constraints)
        assert n.meta['solver_allowed'] is False and n.meta['gate6_parent_input_state']['solver_allowed'] is False
        assert float(n.model.constraints['ResearchImportAnnual-supply'].rhs)==10.
        np.testing.assert_array_equal(n.model.constraints['ResearchStoreDirection-inventory'].rhs,0.)
        yes('B_real_authorized_initial_build_installs_real_hooks',installed_constraints=sorted(HOOKS),variables=int(n.model.nvars),constraints=int(n.model.ncons))
        reject(lambda:ctx.build_network());reject(lambda:install_research_constraint_hooks(n,ctx))
        from precision_handoff import digest
        labels={kind:{name:digest(block.labels.values) for name,block in getattr(n.model,kind).items()} for kind in ['variables','constraints']}
        # Real exact transfer and source-object release; never solve this native LP.
        from execute_gate5_lossless import prepare_detached
        from test_gate5_lossless_integration import IdentityScaling
        ref=weakref.ref(n);owner=[n];scale=[IdentityScaling()];del n
        native,record,fidelity=prepare_detached(owner,scale,f.source,source_hash,f.out,[],{},lambda *args:None,result_directory=f.out)
        assert ref() is None and fidelity['status']=='PASS'
        reject(lambda:ctx.begin_solve(native));native.clear();del native
        yes('E_TEST_ONLY_rejects_real_Highs_and_context_does_not_retain_source_objects')
        ctx.begin_solve(NS());ctx.finish_solve();reject(lambda:ctx.begin_solve(NS()))
        ctx.begin_results(NS());reject(lambda:ctx.begin_results(NS()))
        # Synthetic zero primal/dual witness exercises the actual mmap mapper.
        # It is never a solver-derived optimal scientific result.
        from lossless_gate5_lifecycle import write_array,reload_map_validate
        results=f.out/'TEST_ONLY_native_vectors';results.mkdir();arrays={}
        for key,size in [('col_value',record['model_shape'][1]),('col_dual',record['model_shape'][1]),('row_value',record['model_shape'][0]),('row_dual',record['model_shape'][0])]:arrays[key]=write_array(results/(key+'.npy'),np.zeros(size),np.float64)
        q=dict(network_writeback_qualified=True,arrays=arrays,objective=0.,model_status_code=7,fixture='TEST_ONLY_SYNTHETIC_VECTOR_NOT_SOLVED')
        class AtValidationBoundary(Exception):pass
        def stop_after_actual_mapping(network):
            assert HOOKS<=set(network.model.constraints)
            for kind in labels:
                assert labels[kind]=={name:digest(block.labels.values) for name,block in getattr(network.model,kind).items()}
            np.testing.assert_array_equal(network.generators_t.p,0.)
            np.testing.assert_array_equal(network.links_t.p0,0.)
            raise AtValidationBoundary(network)
        try:
            with patch('validation_dynamics.dynamic_checks',side_effect=stop_after_actual_mapping):
                reload_map_validate(f.source,source_hash,f.out/'mapping',results,record,q,{},execution_context=ctx)
        except AtValidationBoundary as done:rebuilt=done.args[0]
        else:raise AssertionError('Did not reach actual mapping/validation boundary')
        reject(lambda:ctx.begin_solve(NS()));assert sha(ctx._claim)==claim_hash
        yes('F_actual_reload_hooks_labels_and_mmap_mapping_same_claim_no_second_solve',validation_scope='Stops after real mapper, before unrelated full-system physical validator; no mock authorization or hooks')
        ctx.seal_network(rebuilt);assert rebuilt.meta['solver_allowed'] is False and rebuilt.meta['gate6_execution_record']['execution_closed'] is True
        reject(lambda:checked(ctx));reject(lambda:install_research_constraint_hooks(rebuilt))
        from closeout_gate5_metadata import netcdf_science_signature
        before=netcdf_science_signature(f.source);export=f.out/'TEST_ONLY_sealed_metadata.nc';shutil.copyfile(f.source,export)
        with netCDF4.Dataset(export,'r+') as ds:ds.setncattr('meta',json.dumps(rebuilt.meta))
        assert netcdf_science_signature(export)==before and sha(f.source)==source_hash
        reread=pypsa.Network(export);assert reread.meta['solver_allowed'] is False and reread.meta['scientific_results_allowed'] is False and reread.meta['formal_phase5_allowed'] is False
        reread.meta['solver_allowed']=True;reject(lambda:install_research_constraint_hooks(reread))
        yes('G_input_bytes_and_all_science_arrays_unchanged_sealed_export_cannot_reuse_permission',input_sha256=source_hash)
        b=ready_context(out/'build_only','build');h=highspy.Highs();reject(lambda:b.begin_solve(h));reject(lambda:b.begin_results(NS()));h.clear();b.close()
        yes('E_build_only_cannot_enter_solve_or_results')
        for kind,metadata in [('diagnostic',{'artifact_role':'DIAGNOSTIC_PARTIAL_UNSOLVED'}),('preenabled',{'solver_allowed':True})]:
            bad=fixture(out/kind,metadata_override=metadata)
            bad_context=claim(bad);bad.out.mkdir()
            from pypsa.optimization.optimize import OptimizationAccessor
            with patch.object(OptimizationAccessor,'create_model',side_effect=AssertionError('Invalid input must stop before build')):
                reject(lambda:bad_context.build_network())
            bad_context.close();negative.append(dict(case=kind+'_freshly_hashed_input',status='REJECTED'))
        # Direct load validator also refuses diagnostic and pre-enabled metadata;
        # this check is exercised without changing any production input.
        d=pypsa.Network(f.source);d.meta['artifact_role']='DIAGNOSTIC_PARTIAL_UNSOLVED'
        reject(lambda:install_research_constraint_hooks(d));d.meta['solver_allowed']=True;reject(lambda:install_research_constraint_hooks(d))
        yes('C_diagnostic_partial_never_gets_production_hook_permission')
        assert nr.call_count==npresolve.call_count==ng.call_count==0
    return dict(status='PASS',fixture='TEST_ONLY',checks=checks,negative_cases=negative,solver_calls=0,presolve_calls=0,getSolution_calls=0,
        full_gate6_model_built=False,real_claims_consumed_or_removed=0,real_hook_constraints=sorted(HOOKS),complete_scientific_validation_claimed=False)

if __name__=='__main__':
    target=Path(sys.argv[1]);result=run(Path(__file__).resolve().parents[1],target.parent/'authorization_flow_fixtures');write(target,result)
