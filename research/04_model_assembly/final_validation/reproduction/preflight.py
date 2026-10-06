import sys, json, hashlib, subprocess, platform, os, shutil, inspect
from pathlib import Path
import pypsa, linopy, pandas as pd, psutil
ROOT=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
os.chdir(ROOT)
OUT=Path('/mnt/c/Users/20122/Documents/ChatGPT/ASEAN/work/phase4_final_validation/evidence');OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cmd(args):return subprocess.check_output(args,text=True).strip()
report=dict(python=sys.version,executable=sys.executable,pypsa=pypsa.__version__,linopy=linopy.__version__,platform=platform.platform(),cpu_count=os.cpu_count(),ram_bytes=psutil.virtual_memory().total,available_ram_bytes=psutil.virtual_memory().available,disk_free_bytes=shutil.disk_usage(ROOT).free,solvers=linopy.available_solvers,git_sha=cmd(['git','rev-parse','HEAD']),git_status=cmd(['git','status','--porcelain']),lock_sha256=sha('envs/linux-64.lock.yaml'))
packages=cmd([sys.executable,'-m','pip','list','--format=json']);(OUT/'ENVIRONMENT_PACKAGES.json').write_text(packages+'\n')
report['package_snapshot_sha256']=sha(OUT/'ENVIRONMENT_PACKAGES.json')
for mod in ['highspy','gurobipy']:
 try:
  m=__import__(mod)
  report[mod]={'version':m.Highs().version() if mod=='highspy' else list(m.gurobi.version())}
 except Exception as e:report[mod]={'unavailable':str(e)}
n=pypsa.Network('results_project/assembly_v1/research_fullsc_2050_assembly_v1_unsolved.nc')
report['input_sha256']=sha('results_project/assembly_v1/research_fullsc_2050_assembly_v1_unsolved.nc')
report['components']={c.name:len(c.df) for c in n.iterate_components()}
report['snapshot_count']=len(n.snapshots)
report['global_constraints']=n.global_constraints.reset_index().to_dict('records')
report['hooks']={k:n.meta.get(k) for k in ['required_constraint_hooks','approved_global_constraints','existing_annual_fixed_om_eur','external_annual_caps','lv_limit','policy_enabled']}
report['meta_keys']=sorted(n.meta)
report['series']={c.name:{a:list(f.shape) for a,f in c.pnl.items() if len(f.columns)} for c in n.iterate_components()}
report['create_model_signature']=str(inspect.signature(n.optimize.create_model));report['solve_model_signature']=str(inspect.signature(n.optimize.solve_model))
(OUT/'ENVIRONMENT_PREFLIGHT.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
for method in [n.optimize.create_model,n.optimize.solve_model]:
 (OUT/(method.__name__+'_source.py')).write_text(inspect.getsource(method))
print(json.dumps(report,indent=2,default=str))
