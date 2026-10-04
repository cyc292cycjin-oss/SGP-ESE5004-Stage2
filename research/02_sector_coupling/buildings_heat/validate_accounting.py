"""Execute isolated frozen functions on explicitly SYNTHETIC audit fixtures. No optimization.
Also reconcile retained tutorial intermediates; never regenerate or modify them.
"""
from pathlib import Path
from types import SimpleNamespace
import ast, json, logging, warnings
import numpy as np
import pandas as pd
import pypsa

R=Path(__file__).resolve().parent; U=R/'source_snapshot/upstream'; E=R/'evidence'
def load_functions(path,names,env):
    tree=ast.parse(path.read_text()); chosen=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names]
    assert set(x.name for x in chosen)==set(names)
    exec(compile(ast.Module(body=chosen,type_ignores=[]),str(path),'exec'),env)
env=dict(pd=pd,np=np,pypsa=pypsa,logger=logging.getLogger('audit'))
load_functions(U/'scripts/_helpers.py',['safe_divide','get_conv_factors','aggregate_fuels'],env)
load_functions(U/'scripts/prepare_sector_network.py',['normalize_by_country','p_set_from_scaling','add_residential','add_services','create_nodes_for_heat_sector'],env)
# Fixture values are labels for conservation tests, NOT proposed ASEAN inputs.
n=pypsa.Network(); n.set_snapshots(pd.date_range('2013-01-01',periods=2,freq='h'))
for name,carrier in [('SG0','AC'),('SG0 oil','oil'),('SG0 gas','gas'),('SG0 biomass','solid biomass'),('co2 atmosphere','co2'),('SG0 residential rural heat','residential rural heat'),('SG0 services rural heat','services rural heat'),('SG0 urban central heat','urban central heat')]:
    n.add('Bus',name,carrier=carrier)
n.buses['location']='SG0'; n.buses['country']='SG'
for name,value in [('SG0',20),('SG0 residential rural heat',6),('SG0 services rural heat',4),('SG0 urban central heat',2)]:
    n.add('Load',name,bus=name,carrier=n.buses.at[name,'carrier'],p_set=[value*1e6/2]*2)
sp=SimpleNamespace(nodes=pd.Index(['SG0']),**{f:SimpleNamespace(nodes=pd.Index([f'SG0 {f}'])) for f in ['gas','oil','biomass']})
et=pd.DataFrame({'total residential space':[3.6],'total residential water':[2.4],'residential heat oil':[4.],'residential heat gas':[0.],'residential heat biomass':[0.],'residential oil':[1.],'residential gas':[0.],'residential biomass':[0.],'electricity residential':[7.],'services electricity':[3.],'services oil':[0.],'services gas':[0.],'services biomass':[0.]},index=['SG'])
costs=pd.DataFrame({'CO2 intensity':[.2,.2]},index=['oil','gas'])
env.update(spatial=sp,countries=['SG'])
def amounts():return n.loads_t.p_set.sum().div(1e6).to_dict()
before=amounts();env['add_residential'](n,costs,et);after=amounts();env['add_services'](n,costs,et);after_services=amounts()
assert abs(sum(v for k,v in after.items() if 'heat' in k)-2)<1e-10
assert abs(after['SG0']-7)<1e-10
assert abs(after_services['SG0 services electricity']-3)<1e-10
env.update(pop_layout=pd.DataFrame({'urban':[.6],'rural':[.4],'fraction':[1.],'ct':['SG']},index=['SG0']),options={'district_heating':{'potential':.3,'progress':1}},investment_year=2030,get=lambda x,y:x)
_,dh,urban=env['create_nodes_for_heat_sector'](pd.DataFrame({'district heat share':[0.]},index=['SG0']))
assert abs(dh.iloc[0]-.18)<1e-10
out={'synthetic_fixture':True,'no_solver_used':True,'before_TWh':before,'after_add_residential_TWh':after,'after_add_services_TWh':after_services,'residential_remaining_heat_target_TWh':2,'combined_heat_after_TWh':sum(v for k,v in after.items() if 'heat' in k),'district_fixture':{'current':0,'urban':.6,'potential':.3,'progress':1,'computed_share':float(dh.iloc[0])}}
# Re-run ONLY the annual raw household/services aggregation on retained raw rows.
raw=pd.read_json(E/'UNSD_2019_BUILDINGS_ROWS.json');raw['country']=raw.ISO2
split=raw['Commodity - Transaction'].str.split(' - ',expand=True)
raw['Commodity']=split[0];raw['Transaction']=split[1]
countries=sorted(raw.country.unique()); base=pd.DataFrame(index=countries)
gas,oil,bio,coal,heat,elec=env['aggregate_fuels']('industry')
env.update(df_yr=raw,countries=countries,energy_totals_base=base,fuels_conv_toTWh=env['get_conv_factors']('industry'),gas_fuels=gas,oil_fuels=oil,biomass_fuels=bio,coal_fuels=coal,heat=heat,electricity=elec,sectors_dfs={},_logger=logging.getLogger('audit'),snakemake=SimpleNamespace(params=SimpleNamespace(shift_coal_to_elec=True,space_heat_share=.6)))
load_functions(U/'scripts/build_base_energy_totals.py',['calc_sector'],env)
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    for sector in ['consumption by households','services']:env['calc_sector'](sector)
stored=pd.DataFrame(json.loads((E/'TUTORIAL_BUILDINGS_ANNUAL.json').read_text())['base']).T
diff=(base.astype(float)-stored.reindex(index=base.index,columns=base.columns).astype(float)).abs()
out['raw_aggregation_reconciliation']={'max_abs_TWh':float(diff.max().max()),'countries':len(base),'fields':len(base.columns),'exact_at_stored_precision':bool((diff.fillna(0)<1e-8).all().all()),'heat_commodities':heat}
# Which actual tutorial nodes lost assigned annual space service to zero weather shape?
M=Path('/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources/baseline-aims-3H-tutorial')
diagnostic={}
for year in ['2030','2040','2050']:
    pop=pd.read_csv(M/f'population_shares/pop_layout_elec_s_50_{year}.csv',index_col=0)
    ann=pd.read_csv(M/f'energy_totals_{year}.csv',index_col=0)
    df=pd.read_csv(M/f'demand/heat/heat_demand_s_50_{year}.csv',index_col=0,header=[0,1])
    items={}
    for sec in ['residential','services']:
        col='total '+sec+' space'; assigned=pop.ct.map(ann[col])*pop.fraction
        missing=df[sec+' space'].isna().all(); relevant=missing&assigned.reindex(missing.index).gt(0)
        items[sec]={'all_nan_nodes':int(missing.sum()),'positive_annual_but_nan_nodes':int(relevant.sum()),'assigned_annual_TWh':float(assigned.sum()),'lost_assigned_TWh':float(assigned.reindex(missing.index)[relevant].sum()),'remaining_profile_sum_TWh':float(df[sec+' space'].sum().sum()/1e6)}
    diagnostic[year]=items
out['tutorial_profile_conservation']=diagnostic
(E/'ACCOUNTING_VALIDATION.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
