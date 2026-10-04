"""Re-observe unresolved E3 on the integration branch, without editing the model."""
from pathlib import Path
import ast,hashlib,json,sys
HERE=Path(__file__).resolve().parent
repo=Path('/home/jin/research/SGP_ESE5004_Stage2/phase3a4/buildings_accounting_validation')
sys.path.insert(0,str(repo/'research/02_sector_coupling/buildings_engineering_tests'))
from check_E1 import fixture,load,amounts,pd
n,env,_,_,_=fixture(repo)
n.add('Load','SG0 services electricity',bus='SG0',carrier='services electricity',p_set=[3e6/5]*2)
load(repo/'scripts/final_asean_adjustment.py',['include_electricity_growth','elec_carrier'],env)
env['retrieve_population_forcast']=lambda path:pd.DataFrame({2030:[1000.]},index=['SG'])
before=amounts(n).to_dict()
env['include_electricity_growth'](n,{'pop_forecast_path':'SYNTHETIC_NO_FILE','elec_per_capita':{'SG':1.},'total_elec_demand':False},2030)
after=amounts(n).to_dict()
assert abs(after['SG0']-1)<1e-9 and abs(after['SG0 services electricity']-3)<1e-9
trace={}
for f in ['prepare_sector_network.py','final_asean_adjustment.py','prepare_heat_data.py']:
    p=repo/'scripts'/f;lines=p.read_text().splitlines()
    trace[f]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),matches=[dict(line=i+1,text=l.strip()) for i,l in enumerate(lines)
        if any(s in l for s in ['service electricity','services electricity','elec_carrier','electric_heat_supply','add_residential(n,','add_services(n,'])])
result=dict(synthetic_only=True,optimizer_called=False,expected_national_target_TWh=1.,before_TWh=before,
            after_TWh=after,total_after_TWh=sum(after.values()),regression_result='KNOWN_E3_BLOCKER_REPRODUCED',
            scientific_ASEAN_overestimate_quantified=False,E3_patch=False,trace=trace)
(HERE/'evidence/INTEGRATED_E3_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='trace'}))
