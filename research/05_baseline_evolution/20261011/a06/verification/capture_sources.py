from pathlib import Path
import json,hashlib,subprocess
from netCDF4 import Dataset
D=Path('/mnt/d/ResearchWorkspaces/ASEAN');R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');O=D/'work/a06_policy_cost_resource_audit_20261012'
P='5bacad702ccfed17ad19ab510fa710651e966f2c';U='a3616a68ee44592af6527ca9024a90f1956646ae';F='b9be7d0ab788a4151346c098d2e657c7e94a22da'
def g(*a):return subprocess.check_output(['git','-C',str(R),*a])
spec=[(P,'scripts/prepare_sector_network.py',[(50,180),(1147,1210),(2973,3025),(3120,3180)]),(P,'scripts/solve_network.py',[(138,187),(898,920)]),(P,'scripts/add_electricity.py',[(130,246)]),(P,'scripts/prepare_network.py',[(134,190)]),(F,'scripts_project/build_research_assets.py',[(35,165),(177,216)]),(F,'scripts_project/carbon_architecture.py',[(1,180)]),(F,'configs/research/baseline.yaml',[(1,130)])]
out={'snippets':[],'searches':[],'safe_network_config':{}}
for c,p,ranges in spec:
 b=g('show',c+':'+p);ls=b.decode().splitlines();out['snippets'].append({'commit':c,'path':p,'blob_sha1':g('rev-parse',c+':'+p).decode().strip(),'sha256':hashlib.sha256(b).hexdigest(),'snippets':[{'start':a,'end':min(z,len(ls)),'text':'\n'.join(f'{i+1}: {ls[i]}' for i in range(a-1,min(z,len(ls))))} for a,z in ranges]})
for c,term in [(P,'transmission_projects'),(P,'def prepare_costs'),(P,'def annuity'),(F,'KnownFixedCostToAdd'),(F,'install_existing_asset_constraints'),(F,'2050'),(F,'price_method')]:
 scope=['scripts','scripts_project','rules'] if term!='2050' else ['research_inputs/asset_survival/selected_closure_decisions.json']
 q=subprocess.run(['git','-C',str(R),'grep','-n','-F',term,c,'--',*scope],capture_output=True,text=True);assert q.returncode in (0,1)
 out['searches'].append({'commit':c,'term':term,'matches':q.stdout.splitlines()})
for m in json.loads((O/'NETWORK_STATIC_READOUT.json').read_text())['models'].values():
 with Dataset(m['path'],'r') as n:
  meta=json.loads(n.meta)
  label=Path(m['path']).name
  safe={k:meta[k] for k in ['git_commit','wildcards','co2_budget','costs','policy_config','transmission_projects','final_adjustment'] if k in meta}
  if 'sector' in meta:safe['sector_carbon_resource']={k:v for k,v in meta['sector'].items() if any(t in k.lower() for t in ['co2','biomass','lignite','capture','dac','smr','fischer','potential'])}
  if 'accounting_report' in meta:safe['accounting_report']=meta['accounting_report']
  safe['stored_weight_fields']={k:n[k][:].tolist()[:3] for k in n.variables if 'weight' in k or k.startswith('snapshots_')}
  out['safe_network_config'][label]=safe
(O/'SOURCE_CAPTURE.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
