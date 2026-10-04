"""Read frozen Git blobs only; preserve targeted Transport source evidence."""
from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parent
base=Path('/home/jin/research/SGP_ESE5004_Stage2')
layers={'P':(base/'phase2/paper_reference','5bacad702ccfed17ad19ab510fa710651e966f2c'),'U':(base/'phase2/upstream_sc_baseline','a3616a68ee44592af6527ca9024a90f1956646ae'),'V':(base/'phase3a4/buildings_accounting_validation','50a73d8f531132c5459174a55cac412d5f684462'),'R':(base/'phase2/research_model','a3616a68ee44592af6527ca9024a90f1956646ae')}
names=['Snakefile','config.default.yaml','configs/config.asean.yaml','configs/scenarios.asean.yaml','configs/tutorials/config.asean.yaml','scripts/prepare_sector_network.py','scripts/final_asean_adjustment.py','scripts/build_base_energy_totals.py','scripts/prepare_energy_totals.py','scripts/prepare_transport_data.py','scripts/prepare_transport_data_input.py','scripts/prepare_airports.py','scripts/prepare_ports.py','scripts/build_demand_profiles.py','scripts/_helpers.py','scripts/prepare_network.py','scripts/add_brownfield.py','scripts/add_existing_baseyear.py','data/emobility/traffic.tex','data/emobility/European_countries_car_ownership.csv','data/emobility/Pkw__count','data/emobility/KFZ__count','data/temp_hard_coded/transport_data.csv','data/temp_hard_coded/energy_totals.csv','data/energy_totals_DF_2030.csv','doc/configtables/sector_land_transport.csv','doc/configtables/sector_shipping_aviation.csv']
names += ['scripts/prepare_heat_data.py','scripts/build_clustered_population_layouts.py','scripts/prepare_cost_data.py','scripts/prepare_costs.py','scripts/build_costs.py','data/demand/fuel_shares.csv']
records=[];identities=[]
for layer,(repo,expected) in layers.items():
    def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
    commit=git('rev-parse','HEAD').decode().strip();status=git('status','--porcelain').decode().strip()
    assert commit==expected and not status,(layer,commit,status)
    identities.append(dict(layer=layer,path=str(repo),commit=commit,clean=True))
    if layer not in ['P','U']:continue
    tracked=set(git('ls-files').decode().splitlines())
    extra=[p for p in tracked if p.startswith('data/') and any(t in p.lower() for t in ['cagr','efficiency','transport','energy_totals','growth']) and Path(p).suffix in ['.csv','.yaml']]
    for name in sorted(set(names+extra)&tracked):
        b=git('show','HEAD:'+name);out=R/'evidence/source'/layer/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(b)
        records.append(dict(layer=layer,commit=commit,path=name,local_path=out.relative_to(R).as_posix(),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),source_url=f'https://github.com/pypsa-meets-earth/pypsa-asean/blob/{commit}/{name}'))
e=R/'evidence';e.mkdir(exist_ok=True)
(e/'SOURCE_MANIFEST.json').write_text(json.dumps(records,indent=2))
(e/'MODEL_IDENTITY.json').write_text(json.dumps(identities,indent=2))
print(json.dumps(dict(files=len(records),protected_models=len(identities))))
