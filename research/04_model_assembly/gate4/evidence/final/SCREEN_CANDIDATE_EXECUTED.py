"""Independent checks that do not accept the pending Animal-waste boundary."""
from pathlib import Path
import sys,json
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');W=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'scripts_project'))
import pypsa,numpy as np
from carrier_architecture import Fragment,to_pypsa_fragment
from assembly_components import merge_input_components,bind_loads,validate_hooks
from build_research_network import load_unbound_recipe
from build_research_network import static_validate
from validate_fullsc_final import numeric_inputs,coupling,controls
from build_diagnostic_network import check_physical_reachability
from final_closure_inputs import read,save
A=R/'results_project/assembly_v1/final_assets';L=R/'results_project/assembly_v1/final_allocation'
n=pypsa.Network(A/'electric_base_2050_unsolved.nc');raw=load_unbound_recipe(A/'carrier_fragment.json');f=Fragment();f.buses=raw['buses'];f.components=raw['components'];f.markets=raw['markets']
sub=to_pypsa_fragment(f,list(n.snapshots),list(n.snapshot_weightings.generators),component_ids=list(f.components));merge_input_components(n,sub)
n.meta.update(artifact_role='DIAGNOSTIC_PARTIAL_UNSOLVED',fullsc_network_complete=False,input_coverage_complete=False,solver_allowed=False,scientific_results_allowed=False,required_constraint_hooks=sorted(set(n.meta['required_constraint_hooks'])|{'install_fragment_constraints'}))
n.meta.update(approved_coupling_paths=raw['approved_coupling_paths'],biomass_obligation_routes=raw['biomass_obligation_routes'])
m=read(L/'allocation_manifest.json');records=read(R/'research_inputs/assembly_v1/registry.json')['records']
with np.load(L/m['arrays_file'],allow_pickle=False) as z:bind_loads(n,records,m,z,raw['demand_destinations'])
validate_hooks(n);native=numeric_inputs(n);paths=coupling(n);transfer=controls(n);reach=check_physical_reachability(n)
expected={r['InputID']:float(r['Value']) for r in records if r.get('RequiredPhysical') and r['Year']==2050};totals={k:0. for k in expected}
for load,account in n.meta['demand_owners'].items():totals[account]+=float((n.loads_t.p_set[load]*n.snapshot_weightings.generators).sum())
assert set(totals)==set(n.loads.source_account_id)
assert all(np.isclose(v,totals[k],rtol=1e-10,atol=1e-6) for k,v in expected.items())
physical=static_validate(n,records,L,read(A/'carbon_component_map.json'))
save(W/'evidence/INDEPENDENT_CANDIDATE_SCREEN.json',dict(role='DIAGNOSTIC_ONLY_NO_EXPORT',accounts=len(expected),loads=len(n.loads),annual_conservation=True,exactly_once_accounts=True,native_schema_sentinels=native,coupling=paths,interconnect=transfer,reachability=reach,physical_validation=physical,full_fixed_account_qualification=False,reason='Animal waste boundary pending; no qualification flags promoted',solver_runs=0,optimization_variables_created=False))
print(json.dumps(dict(accounts=len(expected),loads=len(n.loads),coupling_paths=len(paths),electricity_components=len(transfer),cross_border=sum(r['Classification']=='CROSS_BORDER' for r in transfer),full_network_exported=False)))
