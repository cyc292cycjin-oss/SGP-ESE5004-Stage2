"""SYNTHETIC_TEST_ONLY: nonzero dual, same-model hooks, physical export mapping."""
import json,sys,copy
from pathlib import Path
import numpy as np,pypsa,linopy
from precision_handoff import audited_direct_backend,research_scalar_assignment,exact,transfer
from fixed_inventory_scaling import FixedInventoryScaling,physical_checks
from fixed_accounts import qualify_fixed_accounts,validate_exported_accounting
from assembly_components import install_research_constraint_hooks

def run(root,out):
    out.mkdir(parents=True,exist_ok=False)
    result=dict(role='SYNTHETIC_TEST_ONLY',synthetic_solver_runs=0,local_solver_runs=0,real_gate5_runs=0,tests=[])
    def save(): (out/'MAPPING_REGRESSION_RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    save()
    class ScalarMap:
        def columns(self,vl,lo,up,c): return lo/4,up/4,c*4
        def rows(self,cl,a,lo,up):return a,lo/4,up/4
        def finish(self):return dict(role='SYNTHETIC_NONZERO_OBJECTIVE_MAP',D=4,R=.25)
        def restore(self,r):r.solution.primal*=4;r.solution.dual*=.25;return r
    m=linopy.Model();x=m.add_variables(lower=0,name='x');m.add_constraints(x>=3,name='minimum');m.add_objective(2*x)
    with audited_direct_backend(out/'scalar_transfer.json',transformation=ScalarMap()):
        result['synthetic_solver_runs']+=1;save()
        status=m.solve(solver_name='highs',io_api='direct',threads=2,solver='ipm',run_crossover='on',log_fn=out/'scalar.log')
    assert status==('ok','optimal') and float(x.solution)==3 and float(m.constraints['minimum'].dual)==2 and m.objective.value==6
    result['tests'].append(dict(test='nonzero_objective_primal_dual_mapping',status='PASS',objective=6,primal=3,dual=2));save()
    source=pypsa.Network(root/'results_project/validation/gate5_20261006_01/research_2050_gate5_24h_validation_input.nc')
    audit=json.loads((root/'results_project/validation/inventory_local_20261006_02/FORMULATION_MAPPING_AND_ROUNDING_AUDIT.json').read_text())
    g=audit['groups'][0];audit={**audit,'groups':[g],'store_count':len(g['stores']),'group_count':1}
    n=pypsa.Network();n.set_snapshots(source.snapshots);n.snapshot_weightings=source.snapshot_weightings.copy()
    stores=g['stores'];links=source.links.index[source.links.bus0.isin(source.stores.loc[stores,'bus'])];buses=list(g['final_buses'])+source.stores.loc[stores,'bus'].tolist()
    for typ,ids in [('Carrier',source.carriers.index),('Bus',buses),('Store',stores),('Link',links),('Load',[g['load']])]:
        n.import_components_from_dataframe(source.df(typ).loc[ids].copy(),typ)
    n.loads_t.p_set=source.loads_t.p_set[[g['load']]].copy()
    n.add('Bus','synthetic_electric',carrier='AC');n.add('Generator','synthetic_supply',bus='synthetic_electric',p_nom=2,marginal_cost=1)
    n.add('Load','synthetic_load',bus='synthetic_electric',p_set=1)
    n.meta=dict(artifact_role='SYNTHETIC_TEST_ONLY',required_constraint_hooks=['install_fragment_constraints'],policy_enabled=False,
        biomass_obligation_routes={s:copy.deepcopy(source.meta['biomass_obligation_routes'][s]) for s in stores},store_power_rules={s:'discharge_only' for s in stores})
    qualify_fixed_accounts(n);n.optimize.create_model();model=n.model;install_research_constraint_hooks(n)
    scalar=model.add_variables(lower=1,upper=1,name='Research-synthetic-FOM');model.objective+=17*scalar
    hooks=[k for k in model.constraints if k.startswith('ResearchStoreDirection-')];assert len(hooks)==len(stores)
    plan=FixedInventoryScaling(n,audit)
    with audited_direct_backend(out/'fragment_transfer.json',transformation=plan),research_scalar_assignment():
        result['synthetic_solver_runs']+=1;save()
        status=n.optimize.solve_model(solver_name='highs',io_api='direct',solver_options=dict(threads=2,solver='ipm',run_crossover='on'),log_fn=out/'fragment.log')
    assert status==('ok','optimal') and n.model is model and all(k in model.constraints for k in hooks)
    assert abs(n.objective-(8760+17))<1e-8 and float(scalar.solution)==1
    checks=physical_checks(n,audit);assert all(r['Status']=='PASS' for r in checks),checks
    n.meta['constraint_hook_state']='INSTALLED_AND_SOLVED_ON_SAME_MODEL'
    path=out/'synthetic_mapping_solved.nc';n.export_to_netcdf(path);r=pypsa.Network(path)
    validate_exported_accounting(r);assert r.meta==n.meta
    for typ,attr,ids in [('Store','e',stores),('Store','p',stores),('Link','p0',links),('Link','p1',links)]:exact(n.pnl(typ)[attr][ids],r.pnl(typ)[attr][ids],typ+'-'+attr)
    assert all(z['Status']=='PASS' for z in physical_checks(r,audit))
    result['tests'].append(dict(test='same_model_hooks_fom_once_primal_export_readback',status='PASS',fixed_original_unit_checks=checks));save()
    # One external coupling invalidates the isolation proof; rejection before solve.
    model.add_constraints(model['Store-p'].isel(snapshot=0,Store=0)+model['Generator-p'].isel(snapshot=0,Generator=0)>=0,name='SYNTHETIC_FORBIDDEN_EXTERNAL_COUPLING')
    try:transfer(model,transformation=FixedInventoryScaling(n,audit))
    except ValueError as e:
        assert 'external/cross-group' in str(e);result['tests'].append(dict(test='external_coupling_revokes_scaling',status='PASS_REJECTED',detail=str(e)))
    else:raise AssertionError('External coupling not rejected')
    result['status']='PASS';save()

if __name__=='__main__':run(Path(__file__).resolve().parents[1],Path(sys.argv[1]).resolve())
