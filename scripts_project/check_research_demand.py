"""Consume the Gate2 research config and verify its tables, without a solver.

This is the only Gate2 research demand entry point. The upstream Snakefile and
its demand builders are not called. No inherited heat, rail, AEO8 or industrial
Load creation is permitted here. Future network wiring belongs to later gates.
"""
from pathlib import Path
import argparse,csv,io,json
import yaml
from build_research_demand import build,csv_bytes,TABLES


def check(repo):
    repo=Path(repo)
    cfg=yaml.safe_load((repo/'configs/research/baseline.yaml').read_text())['research_demand']
    controls={'mode':'static_demand_only','numeric_acceptance_required':True,
        'legacy_demand_builders':'forbidden','astar_boundary':'end_user_final_electricity',
        'aeo8_generation_target':False,'heat_without_accepted_service':'embedded',
        'future_growth_fallback':'forbidden','solver_allowed':False}
    for key,value in controls.items():
        if cfg.get(key)!=value:raise ValueError('Invalid research demand control: '+key)
    if set(cfg['tables'])!=set(TABLES):raise ValueError('Missing/duplicate demand tables')
    if len(cfg['tables'])!=len(TABLES):raise ValueError('Duplicate demand table')
    path=repo/cfg['input_directory']
    if path.resolve()!= (repo/'research_inputs/demand').resolve():raise ValueError('Unregistered demand directory')
    tables,report=build(repo)
    for name in TABLES:
        disk=list(csv.reader(io.StringIO((path/name).read_text(encoding='utf-8-sig'))))
        expected=list(csv.reader(io.StringIO(csv_bytes(tables[name]).decode('utf-8-sig'))))
        if disk!=expected:raise ValueError('Stale or edited derived demand table: '+name)
    return dict(config_contract='PASS',derived_tables_match='PASS',legacy_builders_called=False,
                static_only=True,full_network_assembled=False,solver_status='NOT_RUN',build=report)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    result=check(args.repo);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='build'}))
