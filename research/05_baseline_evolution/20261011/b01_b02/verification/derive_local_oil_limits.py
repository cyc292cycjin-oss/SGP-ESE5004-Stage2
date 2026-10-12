"""Small exact static calculation on B audit JSON, no source-array reread."""
from pathlib import Path
from fractions import Fraction as F
import json
O=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/research/05_baseline_evolution/20261011/b01_b02/evidence')
def read(p):return json.loads((O/p).read_text())
c=read('B01_CAPACITY_AND_PROFILE_CHECK.json');z=read('B02_MULTIPORT_AND_CARBON_BALANCE.json');loads=read('B01_LOAD_SUPPLY_PATHS.json')['records'];lookup={x['supply_path'][-1]:x for x in loads if x['carrier']=='oil'}
limits=[]
for b in [x for x in z['buses'] if x['carrier']=='oil']:
 meter=[];power=[];unknown=[]
 for link in b['links']:
  if link['coefficient_on_this_bus']>=0:continue
  if link['carrier']=='oil final-energy accounting':
   l=lookup[link['id']];assert l['minimum_MW']==l['peak_MW'];meter.append({'load':l['load'],'meter':link['id'],'flat_MW_exact':str(F(l['peak_MW']))})
  elif link['carrier']=='oil existing':
   p=link['bounds'];assert not p['p_nom_extendable'];power.append({'asset':link['id'],'maximum_fuel_input_MW_exact':str(F(p['p_nom'])*F(p['p_max_pu']))})
  else:unknown.append(link['id'])
 assert not unknown
 limit=sum((F(v['flat_MW_exact']) for v in meter),F())+sum((F(v['maximum_fuel_input_MW_exact']) for v in power),F())
 ft=next(l for l in b['links'] if l['carrier']=='Fischer-Tropsch');eta=F(ft['coefficient_on_this_bus']);assert eta>0
 cb=next(p['bus'] for p in ft['ports'] if p['carrier']=='co2 captured');ratio=F(next(r['FT_input_per_CC_gas']['exact'] for r in z['captured_balance_exact_arithmetic'] if r['captured_bus']==cb))
 limits.append({'oil_bus':b['bus'],'country':b['country'],'FT':ft['id'],'captured_CO2_bus':cb,'oil_loads':meter,'oil_power':power,'maximum_oil_sink_MW_exact':str(limit),'FT_input_necessary_upper_MW_exact':str(limit/eta),'SMRCC_input_necessary_upper_MW_exact':str(limit/eta/ratio),'forced_zero_FT_and_SMRCC':limit==0,'bound_scope':'Necessary local oil-balance upper bound; all oil demand flat; existing oil power allowed up to input capacity. Not a dispatch solution.'})
anomalies={'zero_profile_assets':[p for p in c['profiles'] if p['maximum']==0],'p_max_above_one':[p for p in c['profiles'] if p['field']=='generators_t_p_max_pu' and p['maximum']>1]}
out={'local_oil_limits':limits,'forced_zero_nodes':[r['oil_bus'] for r in limits if r['forced_zero_FT_and_SMRCC']],'profile_exceptions':anomalies,'formula':'eta_oil*f + external_oil = final_oil_meter_sum + existing_oil_power_input. Nonnegative external_oil implies eta_oil*f <= finite sink bound. a*s=b*f ties SMR CC to FT.'}
(O/'B02_LOCAL_OIL_SINK_LIMITS.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'forced_zero_nodes':out['forced_zero_nodes'],'profile_exceptions':anomalies},ensure_ascii=False,indent=2))
