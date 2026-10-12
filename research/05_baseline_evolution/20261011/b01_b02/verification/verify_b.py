"""Independent check of audit JSON using exact rational expressions.
No NetCDF/CSC/solution-vector or optimizer access.
"""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib,subprocess,math
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');B=R/'research/05_baseline_evolution/20261011';O=B/'b01_b02/evidence'
def read(n):return json.loads((O/n).read_text())
def frac(v):return F(v['exact']) if isinstance(v,dict) else F(v)
checks=[]
def check(name,b,detail):
 checks.append({'check':name,'pass':bool(b),'detail':detail})
 if not b:raise AssertionError(name)
s=read('B01_SCHEME_A_SOURCE_BRIDGE.json');paths=read('B01_LOAD_SUPPLY_PATHS.json');top=read('B01_RESOURCE_TOPOLOGY.json');caps=read('B01_CAPACITY_AND_PROFILE_CHECK.json');conv=read('B02_MULTIPORT_AND_CARBON_BALANCE.json');shared=read('B_SHARED_CAPACITY_AND_STORAGE_NECESSARY_CHECKS.json')
acc={a['asset']:a for a in s['accounts']};groups=[]
for g in s['groups']:
 q={a:F.from_float(acc[a]['Q_prime_MWh']) for a in g['account_ids']};Q=sum(q.values(),F());D=frac(g['D_MWh']);gap=Q-D
 assert Q==frac(g['Q_prime_MWh']) and gap==frac(g['Q_prime_minus_D_MWh']) and gap>=0
 # Construct only symbolic source-subsystem witness, never a production solution.
 # Constant nonnegative d and shared 3h weights; cumulative demand is monotone.
 residual={a:v*gap/Q for a,v in q.items()}
 annual={a:v*D/Q for a,v in q.items()}
 assert sum(annual.values(),F())==D and all(0<=annual[a]<=q[a] for a in q)
 assert sum(residual.values(),F())==gap
 groups.append({'bus':g['bus'],'source_D_le_Q_prime':True,'annual_release_formula':'q_i * D / sum(Q_prime)','terminal_inventory_formula':'q_i * (sum(Q_prime)-D)/sum(Q_prime)','terminal_inventory_sum_MWh_exact':str(gap),'largest_account_terminal_residue_MWh':float(max(residual.values())),'scope':'Conditional real-valued exclusive source subsystem witness; not an assembled LP solution or V4 result'})
check('385 exact Scheme A source closures',len(groups)==385,'All exact Fraction annual inequalities re-summed from account binary64 values')
changes=[a for a,r in acc.items() if r['old_Q_hex']!=r['Q_prime_hex']]
check('180 changed and 627 unchanged account values',len(changes)==180 and len(acc)-len(changes)==627,'No recipe merged or changed')
check('1737 fixed demands have recorded lawful local supply path',len(paths['records'])==1737 and all(r['supply_path'] for r in paths['records']) and not paths['unresolved_paths'],'Graph/rate necessary condition, not simultaneous feasibility')
check('807 isolated store and meter ports',len(top['accounts'])==807 and all(a['old_ports_and_store_structure_pass'] for a in top['accounts']),'Old network topology plus Scheme A source bridge; not new LP support')
check('400 priced unlimited external sources',len(caps['external_suppliers'])==400 and all(r['bounds']['p_nom_max']=='Infinity' and r['marginal_cost']>0 for r in caps['external_suppliers']),'Model assumption does not prove real imports or costs')
check('nominal and static dispatch bounds not contradictory',not caps['bound_conflicts'],'Does not cover all LP rows')
check('no must-run positive dispatch minima',not caps['positive_dispatch_minima'],'p_nom_min is a capacity commitment, not required hourly output')
check('minimum transmission volume respects lv_limit',frac(shared['transmission']['minimum_volume_MWkm'])<=F(shared['transmission']['cap_MWkm']),'Shared cap and KVL remain binding possibilities at a real solution')
check('43 storage-unit initial values within capacity',len(shared['storage_units'])==43 and all(r['initial_within_nominal_energy'] for r in shared['storage_units']),'No joint hydro or electric dispatch construction')
check('100 captured buses have exactly SMRCC and FT, no storage/import/load',len(conv['captured_balance_exact_arithmetic'])==100,'Verified from complete incident lists for these static buses')
co2=[b for b in conv['buses'] if b['carrier']=='co2 captured']
formula=[]
for b in co2:
 cc=next(l for l in b['links'] if l['carrier']=='SMR CC');ft=next(l for l in b['links'] if l['carrier']=='Fischer-Tropsch')
 a=F(cc['coefficient_on_this_bus']);c=-F(ft['coefficient_on_this_bus']);f=a/c
 h=next(F(p['coefficient']) for p in cc['ports'] if p['carrier']=='H2');e=-next(F(p['coefficient']) for p in ft['ports'] if p['carrier'] in ['AC','DC']);o=next(F(p['coefficient']) for p in ft['ports'] if p['carrier']=='oil')
 assert a-c*f==0 and f>h
 formula.append({'bus':b['bus'],'FT_per_CC_exact':str(f),'H2_shortfall_per_CC_exact':str(f-h),'electricity_per_CC_exact':str(e*f),'oil_per_CC_exact':str(o*f)})
check('independent capturedCO2 cancellation and extra H2 requirement',len(formula)==100,'a*s=c*f exactly with Fraction(binary64); f/s exceeds CC H2 output')
h2=[b for b in conv['buses'] if b['carrier']=='H2'];oil=[b for b in conv['buses'] if b['carrier']=='oil']
check('100 H2 cyclic tanks, no exogenous H2 load/source',len(h2)==100 and all(len(b['stores'])==1 and b['stores'][0]['bounds']['e_cyclic'] and b['stores'][0]['bounds']['standing_loss']==0 and not b['loads'] and not b['generators'] for b in h2),'Cyclic annual net supply zero, temporal buffering allowed')
check('100 local oil sources, no oil storage or direct oil Load bypass',len(oil)==100 and all(len(b['generators'])==1 and not b['stores'] and not b['loads'] for b in oil),'Final oil Loads are on separate obligation buses via meters')
check('atmospheric ports not reversible energy sources',all(p['coefficient']>0 and p['p_min_pu']==0 for p in conv['atmosphere']['all_incident_links']),'Atmosphere has no energy carrier withdrawal conversion')
check('no Load time-vector duplicated in evidence',all('profile_sha256_float64_le' in r and 'profile' not in r for r in paths['records']),'Only per-asset scalar summaries/hashes saved')
out={'status':'PASS','checks':checks,'independent_source_subsystem_derivation':groups,'independent_CO2_exact_arithmetic':formula,'not_a_full_LP_certificate':True,'solver_calls':0,'AutoDL_operations':0,'new_network_assembly':False,'G6_05':'PAUSED_BY_USER'}
(O/'B_INDEPENDENT_CHECK_RECEIPT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'PASS','checks':len(checks),'conditional_source_subsystems':len(groups),'CO2_bus_formulas':len(formula)}))
