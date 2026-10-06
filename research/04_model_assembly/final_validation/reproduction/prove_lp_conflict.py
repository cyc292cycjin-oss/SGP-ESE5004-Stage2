from pathlib import Path
from decimal import Decimal as D
import json,sys,re,pypsa
from collections import defaultdict
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');E=Path('/mnt/c/Users/20122/Documents/ChatGPT/ASEAN/work/phase4_final_validation/evidence');run=R/'results_project/validation/gate5_20261006_01'
n=pypsa.Network(run/'research_2050_gate5_24h_validation_input.nc');n.optimize.create_model();m=n.model
candidate=json.loads((E/'LP_PRECISION_ENERGY_SCREEN.json').read_text())[0];bus=candidate['bus'];stocks=candidate['resources']
target={};native={}
def include(name,selector,factor):
 c=m.constraints[name].sel(selector)
 for i,label in enumerate(c.labels.values.ravel()):
  label=int(label);target[label]=factor
  ids=c.vars.values.reshape(-1,c.vars.shape[-1])[i];coef=c.coeffs.values.reshape(-1,c.coeffs.shape[-1])[i]
  native[label]={'name':name,'rhs':D(format(float(c.rhs.values.ravel()[i]),'.12g')),'terms':{int(k):D(format(float(a),'.12g')) for k,a in zip(ids,coef) if k>=0 and a},'sign':str(c.sign.values.ravel()[i])}
include('Bus-nodal_balance',{'Bus':bus},D(24))
for stock in stocks:
 include('Bus-nodal_balance',{'Bus':n.stores.at[stock,'bus']},D(24))
 include('Store-energy_balance',{'Store':stock},D(1))
parsed={};current=None
with (run/'gate5_problem.lp').open() as f:
 for line in f:
  match=re.fullmatch(r'c(\d+):\s*',line)
  if match:
   k=int(match[1]);current=k if k in target else None
   if current is not None:parsed[k]={'terms':{},'text':[line.strip()]}
  elif current is not None:
   s=line.strip();parsed[current]['text'].append(s)
   term=re.fullmatch(r'([+-]?[\d.eE+-]+) x(\d+)',s)
   if term:parsed[current]['terms'][int(term[2])]=D(term[1])
   elif s.startswith(('=','<=','>=')):
    sign,rhs=s.split();parsed[current].update(sign=sign,rhs=D(rhs));current=None
assert set(parsed)==set(target)
lhs=defaultdict(D);rhs=D(0)
for k,row in parsed.items():
 expected=native[k]
 assert row['sign']==expected['sign']=='=' and row['rhs']==expected['rhs'] and row['terms']==expected['terms'],('label mapping mismatch',k)
 rhs+=target[k]*row['rhs']
 for var,a in row['terms'].items():lhs[var]+=target[k]*a
lhs={k:v for k,v in lhs.items() if v}
resolved=[]
for k,a in lhs.items():
 name,coord=m.variables.get_label_position(k);assert name=='Store-e'
 assert coord['snapshot']==n.snapshots[-1] and coord['Store'] in stocks
 assert a==D(-1) and n.stores.at[coord['Store'],'e_min_pu']==0
 resolved.append(dict(variable_label=k,variable=name,coordinate={k:str(v) for k,v in coord.items()},coefficient=str(a),lower_bound=0))
assert rhs>D(0)
proof=dict(status='VERIFIED_EXACT_DECIMAL_LP_CONTRADICTION',bus=bus,resources=stocks,equation_count=len(target),method='Sum365final-bus balances*24 +365resource-bus balances*24 perStore +365Store state equations perStore; compare everyselectedLProw to rebuilt unmodified native equations',remaining_lhs=resolved,rhs=str(rhs),conclusion='Negative sum of nonnegative year-end inventories equals a strictly positive value. This saved LP has no exact feasible solution.',scope='Sufficient independent infeasibility certificate; not a claim that it is the only failure or that a precision correction guarantees an optimal solve',original_floating_difference_mwh=candidate['OriginalFloatingDifferenceMWh'],linopy_export_precision='12 significant decimal digits',source_stock_total=candidate['LPAvailableMWh'],lp_annual_demand=candidate['LPRequiredMWh'])
(E/'EXACT_LP_CONTRADICTION.json').write_text(json.dumps(proof,indent=2)+'\n')
with (E/'EXACT_LP_CONTRADICTION_ROWS.json').open('w') as f:json.dump({str(k):dict(factor=str(target[k]),name=native[k]['name'],raw_lines=v['text']) for k,v in parsed.items()},f,indent=2)
print(json.dumps(proof,indent=2))
