"""Read fixed Git objects and targeted history; no workflow execution or input edits."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parent
REPO=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/upstream_sc_baseline')
PAPER='5bacad702ccfed17ad19ab510fa710651e966f2c'
UPSTREAM='a3616a68ee44592af6527ca9024a90f1956646ae'
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args])
assert git('rev-parse','HEAD').decode().strip()==UPSTREAM
assert not git('status','--porcelain').strip()
files=['Snakefile','config.default.yaml','configs/config.asean.yaml',
 'scripts/build_base_energy_totals.py','scripts/prepare_energy_totals.py','scripts/prepare_heat_data.py',
 'scripts/build_heat_demand.py','scripts/build_cop_profiles.py','scripts/build_temperature_profiles.py',
 'scripts/build_existing_heating_distribution.py','scripts/prepare_sector_network.py',
 'scripts/build_population_layouts.py','scripts/build_clustered_population_layouts.py',
 'scripts/add_existing_baseyear.py','scripts/add_brownfield.py','scripts/final_asean_adjustment.py',
 'scripts/build_demand_profiles.py','scripts/add_electricity.py',
 'data/heat_load_profile_BDEW.csv','data/existing_infrastructure/existing_heating_raw.csv',
 'data/demand/district_heating.csv','data/demand/fuel_shares.csv','data/demand/growth_factors_cagr.csv',
 'data/demand/efficiency_gains_cagr.csv','data/unsd_transactions.csv',
 'scripts/_helpers.py','scripts/prepare_urban_percent.py','scripts/build_shapes.py',
 'data/demand/unsd/paths/Energy_Statistics_Database.xlsx']
manifest=[]
for layer,sha in [('upstream',UPSTREAM),('paper',PAPER)]:
    tracked=set(git('ls-tree','-r','--name-only',sha).decode().splitlines())
    for rel in files:
        if rel not in tracked:continue
        data=git('show',f'{sha}:{rel}');p=R/'source_snapshot'/layer/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        manifest.append({'layer':layer,'sha':sha,'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
hist=R/'history';hist.mkdir(exist_ok=True)
for filename,args in [
 ('heat_parameters.log',['log',UPSTREAM,'--format=fuller','--date=iso','--max-count=20','-G','space_heat_share|district_heating_potential|district_heating_loss|district_heating:','--','config.default.yaml','configs/config.asean.yaml']),
 ('heat_profile.log',['log',UPSTREAM,'--follow','--format=fuller','--max-count=15','--','data/heat_load_profile_BDEW.csv']),
 ('heating_assets.log',['log',UPSTREAM,'--format=fuller','--max-count=15','--','data/existing_infrastructure/existing_heating_raw.csv','scripts/build_existing_heating_distribution.py']),
 ('heat_code.log',['log',UPSTREAM,'--format=fuller','--max-count=20','--','scripts/prepare_heat_data.py','scripts/build_base_energy_totals.py','scripts/prepare_energy_totals.py']),
 ('fuel_shares.log',['log',UPSTREAM,'--follow','--format=fuller','--max-count=12','--','data/demand/fuel_shares.csv']),
 ('district_file.log',['log',UPSTREAM,'--follow','--format=fuller','--max-count=12','--','data/demand/district_heating.csv'])]:
    (hist/filename).write_bytes(git(*args))
for filename,args in [
 ('compact_history.txt',['log',UPSTREAM,'--format=%H %ad %s','--date=short','--max-count=35','--','data/heat_load_profile_BDEW.csv','data/demand/fuel_shares.csv','data/demand/district_heating.csv','scripts/prepare_energy_totals.py']),
 ('split_origin.txt',['log',UPSTREAM,'--format=%H %ad %s','--date=short','-S','space_heat_share','--','config.default.yaml','scripts/build_base_energy_totals.py']),
 ('heat_blame.txt',['blame',UPSTREAM,'-L','825,868','--','config.default.yaml']),
 ('profile_blame.txt',['blame',UPSTREAM,'--','data/heat_load_profile_BDEW.csv']),
 ('fuel_blame.txt',['blame',UPSTREAM,'--','data/demand/fuel_shares.csv'])]:
    (hist/filename).write_bytes(git(*args))
(R/'SOURCE_MANIFEST.json').write_text(json.dumps({'paper_sha':PAPER,'upstream_sha':UPSTREAM,'source_files':manifest,'upstream_status':git('status','--porcelain').decode()},indent=2))
print(json.dumps({'files':len(manifest),'bytes':sum(x['bytes'] for x in manifest)},indent=2))
