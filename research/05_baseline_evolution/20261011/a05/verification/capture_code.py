from pathlib import Path
import subprocess,hashlib,json
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
O=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/a05_cross_border_audit_20261011')
P='5bacad702ccfed17ad19ab510fa710651e966f2c';U='a3616a68ee44592af6527ca9024a90f1956646ae';C='b9be7d0ab788a4151346c098d2e657c7e94a22da'
def git(*a):return subprocess.check_output(['git','-C',str(R),*a])
records=[]
specs=[(P,'scripts/prepare_sector_network.py',[(805,912),(979,1117)]),(P,'scripts/final_asean_adjustment.py',[(30,100),(300,400)]),
 (U,'scripts/prepare_sector_network.py',[(344,383),(807,912),(981,1117),(1276,1358),(1486,1542),(1683,1788),(2146,2235)]),
 (C,'scripts_project/build_research_assets.py',[(49,84),(115,141),(175,214),(225,265)]),(C,'scripts_project/build_research_network.py',[(53,68)]),(C,'scripts_project/carrier_architecture.py',[(25,55),(90,122)]),
 (C,'configs/research/baseline.yaml',[(24,45),(46,65),(90,105)])]
for commit,path,ranges in specs:
 b=git('show',commit+':'+path);lines=b.decode().splitlines()
 records.append({'commit':commit,'path':path,'blob_sha1':git('rev-parse',commit+':'+path).decode().strip(),'sha256':hashlib.sha256(b).hexdigest(),
 'snippets':[{'start_line':a,'end_line':min(z,len(lines)),'text':'\n'.join(f'{i+1}: {lines[i]}' for i in range(a-1,min(z,len(lines))))} for a,z in ranges]})
searches=[]
for commit in [P,U]:
 for term in ['gas pipeline','methanol','ammonia','h2export','H2 pipeline']:
  p=subprocess.run(['git','-C',str(R),'grep','-n','-i','-F',term,commit,'--','scripts','configs','config.default.yaml','Snakefile','rules'],capture_output=True,text=True)
  assert p.returncode in [0,1]
  searches.append({'commit':commit,'term':term,'bounded_scope':'scripts, configs, config.default.yaml, Snakefile, rules','matches':p.stdout.splitlines()})
history={}
for path in ['configs/research/baseline.yaml','scripts_project/carrier_architecture.py','scripts_project/build_research_assets.py']:
 history[path]=git('log',C,'--format=%H %aI %s','--',path).decode().splitlines()
decisions=git('show',C+':research_inputs/asset_survival/selected_closure_decisions.json').decode()
out={'source_snippets':records,'bounded_capability_searches':searches,'relevant_path_history':history,'selected_closure_decisions':json.loads(decisions)}
(O/'CODE_CAPTURE.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Search counts',[(a['commit'][:8],a['term'],len(a['matches'])) for a in searches])
print('Decisions',decisions[:7500])
for rec in records:
 if rec['path']=='scripts/final_asean_adjustment.py' or rec['path']=='scripts_project/build_research_assets.py' or (rec['commit']==U and rec['path']=='scripts/prepare_sector_network.py'):
  print(rec['commit'],rec['path'])
  for x in rec['snippets']:
   if x['start_line'] in [30,300,49,115,344,807]: print(x['text'])
print('Histories',json.dumps(history))
