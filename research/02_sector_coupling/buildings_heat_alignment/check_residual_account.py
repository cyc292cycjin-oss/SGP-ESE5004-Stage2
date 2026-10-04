"""Demonstrate E3 on a synthetic two-load country, with no policy/data change."""
from pathlib import Path
import json
from check_candidate_fixes import fixture, load, amounts, pd
R=Path(__file__).resolve().parent;U=R.parent/'buildings_heat/source_snapshot/upstream'
n,env,_,_,_=fixture(U)
n.add('Load','SG0 services electricity',bus='SG0',carrier='services electricity',p_set=[3e6/5]*2)
load(U/'scripts/final_asean_adjustment.py',['include_electricity_growth','elec_carrier'],env)
env['retrieve_population_forcast']=lambda path:pd.DataFrame({2030:[1000.]},index=['SG'])
before=amounts(n).to_dict()
env['include_electricity_growth'](n,{'pop_forecast_path':'SYNTHETIC_NO_FILE','elec_per_capita':{'SG':1.},'total_elec_demand':False},2030)
after=amounts(n).to_dict()
assert abs(after['SG0']-1)<1e-9 and abs(after['SG0 services electricity']-3)<1e-9
result=dict(synthetic_only=True,optimizer_called=False,expected_national_target_TWh=1.,before_TWh=before,after_TWh=after,total_after_TWh=sum(after.values()),failure='retained services are outside the aggregate-growth selection, so target + services exceeds target',patch='NOT_IMPLEMENTED; accepted direct electricity and existing electric heat bridge required')
(R/'evidence/E3_ACCOUNTING_DEMONSTRATION.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
