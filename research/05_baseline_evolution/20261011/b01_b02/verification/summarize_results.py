from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
import json
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/research/05_baseline_evolution/20261011/b01_b02/evidence')
def read(n):return json.loads((R/n).read_text())
c=read('B01_CAPACITY_AND_PROFILE_CHECK.json');b=read('B02_MULTIPORT_AND_CARBON_BALANCE.json');s=read('B01_SCHEME_A_SOURCE_BRIDGE.json');sh=read('B_SHARED_CAPACITY_AND_STORAGE_NECESSARY_CHECKS.json')
caps=defaultdict(lambda:Counter()); details=defaultdict(list)
for r in c['capacity_records']:
 key=r['component']+':'+r['carrier'];z=r['bounds'];nom=next(k for k in z if k.endswith('_extendable'));ext=bool(z[nom]);caps[key]['count']+=1;caps[key]['extendable']+=ext;caps[key]['unlimited_effective_upper']+=r['effective_nominal_upper']=='Infinity';caps[key]['fixed']+=not ext
 details[key].append(r)
paths={}
for carrier in ['co2 captured','H2','oil']:
 bs=[v for v in b['buses'] if v['carrier']==carrier];inc=Counter((l['carrier'],'consumes' if l['coefficient_on_this_bus']<0 else 'produces') for v in bs for l in v['links']);paths[carrier]={'bus_count':len(bs),'incident_role_counts':{k+':'+d:v for (k,d),v in inc.items()},'example':bs[0]}
gaps=[F(g['Q_prime_minus_D_MWh']['exact']) for g in s['groups']]
hydro=sh['storage_units']
out={'capacity_by_family':dict(caps),'profiles_zero_max_count':sum(p['maximum']==0 for p in c['profiles']),'profiles_max_above_one_count':sum(p['field']=='generators_t_p_max_pu' and p['maximum']>1 for p in c['profiles']),'joint_conversion_paths':paths,'source_gap_MWh':{'minimum':float(min(gaps)),'maximum':float(max(gaps)),'total':float(sum(gaps,F()))},'storage_unit_summary':dict(Counter((r['carrier'],str(bool(r['cyclic_state_of_charge']))) for r in hydro)),'external_annual_caps':c['selected_physical_hooks'].get('external_annual_caps'),'atmo_store':b['atmosphere']['stores'],'atmo_links':len(b['atmosphere']['all_incident_links']),'weak_electric_component_sizes':sorted(map(len,sh['transmission']['weak_electric_components']))}
out['storage_unit_summary']={str(k):v for k,v in out['storage_unit_summary'].items()}
(R/'B_RESULTS_DIGEST.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='joint_conversion_paths'},ensure_ascii=False,indent=2))
print('FILES',[(p.name,p.stat().st_size) for p in R.glob('*.json')])
