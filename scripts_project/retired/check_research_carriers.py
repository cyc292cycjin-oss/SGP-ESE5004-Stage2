"""Validate Gate3 contract + 11-country structural template; no full network."""
from pathlib import Path
import argparse,json,hashlib
import yaml
from carrier_architecture import local_blueprint,validate,reachability,COUNTRIES
from carbon_architecture import TRAJECTORY
from check_research_demand import check as check_demand
from phase4_static import config


def check(repo):
    repo=Path(repo);full=config(repo);baseline=yaml.safe_load((repo/'configs/research/baseline.yaml').read_text())
    a=baseline['research_carrier_architecture'];co=baseline['research_carbon']
    for field in ['cross_border_h2','cross_border_gas','cross_border_co2','cross_border_biomass','cross_border_synthetic_fuels','solver_allowed']:
        if a[field] is not False:raise ValueError('Prohibited physical network/solve: '+field)
    if a['mode']!='static_fragments_only' or a['external_market']!='independent_source_generators_shared_price_metadata_only':raise ValueError('Wrong carrier assembly contract')
    if co['budget_tco2_per_year']!=TRAJECTORY or co['reporting_creates_cap'] is not False or co['full_system_cap']!='forbidden':raise ValueError('Carbon trajectory/scope changed')
    if co['policy_enabled']!=full['co2']['budget']['enable']:raise ValueError('Unrequested baseline budget activation')
    original=full['co2']['budget']
    for year,amount in TRAJECTORY.items():
        if original['base_value']*original['year'][year]!=amount:raise ValueError('Trajectory not equivalent to frozen config')
    # Run Gate2 entry point: pending numeric demand remains blocked and table
    # content is unchanged, rather than trusting config text alone.
    demand=check_demand(repo)
    if demand['build']['numeric_accepted_rows']!=0 or demand['build']['guarded_country_years']!=44:raise ValueError('Gate2 acceptance state changed')
    f=local_blueprint({c+'::template':c for c in sorted(COUNTRIES)},options=full['sector']);validate(f)
    for scenario in ['integrated','disconnected']:
        other=config(repo,scenario)
        for key in ['research_carrier_architecture','research_carbon','research_demand']:
            if full[key]!=other[key]:raise ValueError('Premature scenario difference')
    return dict(config='PASS',Gate2Guards='PASS',template_buses=len(f.buses),template_components=len(f.components),
        pending_numeric_components=sum(not r['accepted'] for r in f.components.values()),hidden_template_paths=reachability(f),
        trajectory=TRAJECTORY,policy_enabled=co['policy_enabled'],full_network_assembled=False,solver_status='NOT_RUN',
        real_scope_complete=False,real_demand_materialised=False,topology_fix_required=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=check(a.repo);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2));print(json.dumps(result))
