"""Assemble only new controlled code; retain every original byte and source SHA."""
from pathlib import Path
import hashlib,json,shutil,ast,subprocess
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work');OUT=W/'c02r_c03_combined_20261012';R=OUT/'release'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
R.mkdir(exist_ok=False)
old=W/'c02_daily_build_20261012/upload_stage'
for p in old.rglob('*'):
    if p.is_file():
        q=R/p.relative_to(old);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
# Old launchers/manifest are evidence only; new manifest will enumerate active code.
for name in ['c02_model.py','c02_semantics.py']:
    shutil.copyfile(W/'c02r_checker_20261012/candidate'/name,R/name)
provenance=[]
items={
 'adapter.py':W/'gurobi_barrier_preparation_20261009/adapter.py',
 'basis_free.py':W/'gurobi_barrier_preparation_20261009/basis_free.py',
 'author_objective.py':W/'author_method_adapted_20261010/author_objective.py',
 'validation_dynamics.py':W/'gate6_refinement_restart_20261009/source/scripts_project/validation_dynamics.py',
 'license_binding.py':W/'gate6_wls_native_preflight_379_20261010/license_binding.py',
 'NATIVE_PARAMETER_EVIDENCE.json':W/'author_method_adapted_20261010/NATIVE_PARAMETER_EVIDENCE.json',
 'production_control_original.py':W/'final_local_closeout_20261010/production_control.py',
}
for name,p in items.items():
    shutil.copyfile(p,R/name);provenance.append({'source':str(p),'sha256':sha(p),'copy':name})
def functions(p,names):
    src=p.read_text();tree=ast.parse(src);out=[]
    for name in names:
        f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
        out.append(ast.get_source_segment(src,f))
    provenance.append({'source':str(p),'sha256':sha(p),'extracted_functions':names})
    return '\n\n'.join(out)
prior=W/'author_method_preflight_20261010/acceptance_pipeline.py'
v4=W/'final_scientific_approval_20261010/acceptance_revision.py'
base=functions(prior,['engineering_checks','frame_equal','netcdf_roundtrip'])
base=base.replace('def engineering_checks(', 'def _base_engineering(').replace("ROOT/'work/gate6_refinement_restart_20261009/source/scripts_project/validation_dynamics.py'", "Path(__file__).parent/'validation_dynamics.py'")
v=functions(v4,['require_contract','engineering_checks'])
header='''from pathlib import Path
import numpy as np,pandas as pd,json,types,importlib.util,os,collections
from c02_common import sha
from fixed_resource_acceptance import RULE_ID,inventory,meter_checks,obligation
fixed_inventory_prefix_draft=inventory
def fsync_file(p):
    with open(p,'rb') as f:os.fsync(f.fileno())
'''
(R/'daily_physics.py').write_text(header+'\n'+base+'\n'+v+'\n')
bridge=W/'author_method_adapted_20261010/result_bridge.py'
(R/'scatter.py').write_text('import numpy as np\n'+functions(bridge,['scatter_active'])+'\n')
put(OUT/'REUSE_PROVENANCE.json',{'sources':provenance,'formula_changes':False,'source_path_changes_only_in_engineering':True})
shutil.copyfile(OUT/'REUSE_PROVENANCE.json',R/'REUSE_PROVENANCE.json')
