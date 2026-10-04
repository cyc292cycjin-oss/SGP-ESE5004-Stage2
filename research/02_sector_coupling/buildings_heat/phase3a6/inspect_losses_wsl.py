"""Read-only frozen source and installed optimization API inspection. Run in WSL."""
from pathlib import Path
import subprocess,json,hashlib,ast,inspect
import pypsa
from pypsa.optimization.optimize import OptimizationAccessor
R=Path('/mnt/c/Users/20122/Documents/ChatGPT/ASEAN/research/02_sector_coupling/buildings_heat/phase3a6')
E=R/'evidence';E.mkdir(exist_ok=True)
base=Path('/home/jin/research/SGP_ESE5004_Stage2')
ids=[]
for layer,p,expected in [('P','phase2/paper_reference','5bacad702ccfed17ad19ab510fa710651e966f2c'),('U','phase2/upstream_sc_baseline','a3616a68ee44592af6527ca9024a90f1956646ae'),('V','phase3a4/buildings_accounting_validation','50a73d8f531132c5459174a55cac412d5f684462'),('R','phase2/research_model','a3616a68ee44592af6527ca9024a90f1956646ae')]:
 repo=base/p
 def git(*a):return subprocess.check_output(['git','-C',str(repo),*a]).decode().strip()
 commit=git('rev-parse','HEAD');assert commit==expected
 dirty=git('status','--porcelain');assert not dirty,(layer,dirty)
 ids.append(dict(layer=layer,path=str(repo),commit=commit,clean=True))
records=[]
repo=base/'phase2/upstream_sc_baseline'
for f in ['scripts/solve_network.py','scripts/prepare_network.py','scripts/_helpers.py','scripts/add_extra_components.py']:
 b=(repo/f).read_bytes();out=E/'source_snapshot/U'/f;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(b)
 records.append(dict(path=f,sha256=hashlib.sha256(b).hexdigest()))
 for node in ast.walk(ast.parse(b)):
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in ['add_lossy_bidirectional_link_constraints','solve_network','extra_functionality','set_length_based_efficiency']:
   print(f'{f}:{node.lineno}-{node.end_lineno} {node.name}\n'+'\n'.join(b.decode().splitlines()[node.lineno-1:node.end_lineno]))
sig=str(inspect.signature(OptimizationAccessor.__call__))
src=Path(inspect.getsourcefile(OptimizationAccessor));b=src.read_bytes();(E/'installed_pypsa_optimize.py').write_bytes(b)
rec=dict(pypsa_version=pypsa.__version__,optimizer_signature=sig,source_path=str(src),sha256=hashlib.sha256(b).hexdigest(),solver_run=False)
assert 'transmission_losses' in sig
(E/'LOSS_CODE_IDENTITY.json').write_text(json.dumps(dict(protected_models=ids,files=records,installed_api=rec),indent=2))
calls=subprocess.run(['git','-C',str(repo),'grep','-n','-e','transmission_losses','-e','set_length_based_efficiency','-e','lossy_bidirectional_links','--','scripts','config.default.yaml','configs/config.asean.yaml'],capture_output=True,text=True)
assert calls.returncode==0
(E/'LOSS_CALLSITES.txt').write_text(calls.stdout)
print(json.dumps(rec,indent=2))
