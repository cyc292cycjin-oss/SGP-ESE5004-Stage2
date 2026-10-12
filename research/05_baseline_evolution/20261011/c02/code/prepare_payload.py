"""Assemble pinned build-only sources, never assemble a network or LP."""
from pathlib import Path
import subprocess, hashlib, json, ast, shutil, importlib.metadata as md

W=Path('/mnt/d/ResearchWorkspaces/ASEAN')
REPO=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
OUT=W/'work/c02_daily_build_20261012'
P=OUT/'payload'
P.mkdir(parents=True,exist_ok=True)
records={}
def sha(b): return hashlib.sha256(b).hexdigest()
def save(name,b,source,expected=None):
    if expected: assert sha(b)==expected,(name,sha(b),expected)
    p=P/name;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists(): assert p.read_bytes()==b,name
    else:p.write_bytes(b)
    records[name]={'bytes':len(b),'sha256':sha(b),'source':source}
def git(name,commit,path,expected=None):
    b=subprocess.check_output(['git','show',commit+':'+path],cwd=REPO)
    save(name,b,commit+':'+path,expected)
def local(name,path,expected=None):
    save(name,Path(path).read_bytes(),str(path),expected)

A='8883de6fb3e15767c632ac92f535e8a423e90b69'; C='68ebb96b7d48318654e9ca3f2b2780a0133bc889'
SCI='b9be7d0ab788a4151346c098d2e657c7e94a22da'
BASE='research/05_baseline_evolution/20261011/'
for f in ['EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json','carrier_fragment.json','external_pending_fixed_accounts.json','LOADS_AND_WEIGHTS_REFERENCE.json','EXACT_SOURCE_CLOSURE_A_CHANGESET.json']:
    git('scheme_a/'+f,A,'research_inputs/derived/exact_source_closure_a_max_account_v1_20261011/'+f,
        'a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720' if f=='EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json' else None)
for f in ['C00_DAILY_365_PROTOCOL_C01R_V1.md','evidence/C01R_RULE.json','evidence/C01R_LOAD_ROUNDING_LEDGER.json','evidence/C01R_INDEPENDENT_CHECK.json']:
    git('c01r/'+Path(f).name,C,BASE+'c01r/'+f)
assert records['c01r/C00_DAILY_365_PROTOCOL_C01R_V1.md']['sha256']=='661a81e532184003938213a3e81ad35bd4a687108332d14b3582bf7a8eac2856'
assert records['c01r/C01R_RULE.json']['sha256']=='49d85c8449b32bb1fbf972b564dacb70a12e918dee58e4678efc36f0c736b140'
git('c01r/C01_CF_INFLOW_ROUNDING_CHECK.json',C,BASE+'c01/evidence/C01_CF_INFLOW_ROUNDING_CHECK.json')
git('c01r/C01_DYNAMIC_ATTRIBUTE_INVENTORY.json',C,BASE+'c01/evidence/C01_DYNAMIC_ATTRIBUTE_INVENTORY.json')
for f in ['assembly_components.py','carrier_architecture.py','fixed_accounts.py','fixed_account_scope.py','integrate_surviving_assets.py','lossless_gate5_lifecycle.py']:
    # Full source retained for attribution; only explicitly extracted functions execute.
    git('source/'+f,SCI,'scripts_project/'+f)
for f in ['assembly_components.py','carrier_architecture.py','fixed_accounts.py','fixed_account_scope.py']:
    save('helpers/'+f,(P/'source'/f).read_bytes(),'pinned source copy')
local('V4_APPROVED.json',W/'work/gate6_wls_native_preflight_379_20261010/gate6_preflight379_wls_20261009T224539Z_b9665098/V4_APPROVED.json','955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f')
local('EFFECTIVE_PERTURBATION_LEDGER.csv',W/'work/final_local_closeout_20261010/AUTHOR_METHOD_ADAPTED_SCOPE_V3/EFFECTIVE_PERTURBATION_LEDGER.csv','0450345f1c6a89d89309c920c66d8f7286b84aac76597fa7bd9db19a5a988856')
local('GATE6_3H_ROUNDING_AUDIT.json',W/'outputs/cloud_gate6/cloud_gate6_hipo_capture_20261008T200734Z/completed_backup/runs/cloud_gate6_hipo_capture_20261008T200734Z/GATE6_3H_ROUNDING_AUDIT.json')
local('helpers/fixed_resource_acceptance.py',W/'work/final_scientific_approval_20261010/fixed_resource_acceptance.py')
# Extract two no-solve functions verbatim, including source-line/AST hashes.
selected=[]; origins=[]
for file,fn in [('integrate_surviving_assets.py','install_existing_asset_constraints'),('lossless_gate5_lifecycle.py','bounded_build_allocator')]:
    text=(P/'source'/file).read_text(); node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==fn)
    start=min([node.lineno]+[x.lineno for x in node.decorator_list]); segment='\n'.join(text.splitlines()[start-1:node.end_lineno])
    selected.append(segment);origins.append({'source':file,'function':fn,'first_line':start,'last_line':node.end_lineno,'ast_sha256':sha(ast.dump(node,include_attributes=False).encode())})
save('helpers/build_only_extracted.py',('from contextlib import contextmanager\nimport gc,ctypes\n\n'+'\n\n'.join(selected)+'\n').encode(),'verbatim AST-selected frozen no-solve functions')
kkt=[]
extracts=[('work/gurobi_barrier_preparation_20261009/adapter.py',['ranges']),
 ('work/gurobi_barrier_preparation_20261009/basis_free.py',['mapped_primal_dual','endpoint_metrics','diagnose']),
 ('work/author_method_adapted_20261010/result_bridge.py',['mathematical_gap_decision']),
 ('work/author_method_preflight_20261010/acceptance_pipeline.py',['bounded_columns','budget_arrays','complete_kkt']),
 ('work/final_scientific_approval_20261010/acceptance_revision.py',['require_contract'])]
for rel,names in extracts:
    text=(W/rel).read_text();local('source/'+Path(rel).name,W/rel)
    for name in names:
        node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
        segment='\n'.join(text.splitlines()[node.lineno-1:node.end_lineno]);kkt.append(segment)
        origins.append({'source':rel,'function':name,'first_line':node.lineno,'last_line':node.end_lineno,'ast_sha256':sha(ast.dump(node,include_attributes=False).encode())})
save('helpers/v4_algebra_extracted.py',('from pathlib import Path\nimport math,types\nimport numpy as np\nfrom fixed_resource_acceptance import RULE_ID\nCHUNK = 200_000  # frozen adapter.py:13\n\n'+'\n\n'.join(kkt)+'\n').encode(),'verbatim AST-selected prior V4 formulas, no solver imports')
config={'schema':'C02_BUILD_ONLY_V1','instance_id':122,'project_root':'/root/autodl-tmp/SGP','python':'/root/autodl-tmp/SGP/env/gate5/bin/python3.11',
 'parent_commit':C,'scheme_a_commit':A,'science_commit':SCI,'network_sha256':'238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d',
 'default_network':'/root/autodl-tmp/SGP/worktrees/gate6_capture_20261008T200734Z/results_project/assembly_v1/research_fullsc_2050_assembly_v1_unsolved.nc',
 'runtime_versions':{x:md.version(x) for x in ['pypsa','linopy','numpy','scipy','pandas','xarray','netCDF4','psutil']},
 'python_version':'3.11.13','runtime_versions_source':'local frozen model environment metadata; cloud equality mandatory, no install',
 'deadline_seconds':1800,'rss_limit_GiB':75,'cgroup_min_limit_GiB':90,'cgroup_headroom_GiB':12,'min_cpu_cores':4,
 'disk_start_GiB':20,'disk_floor_GiB':8,'output_reserve_GiB':6,'guard_poll_seconds':0.5,
 'authorization':'User C-02 Controlled Daily Network & LP Build — NO SOLVE','build_authorized':True,'solver_authorized':False,
 'extracted_functions':origins,'files':records}
(P/'INPUT_MANIFEST.json').write_text(json.dumps(config,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'files':len(records),'bytes':sum(v['bytes'] for v in records.values()),'versions':config['runtime_versions'],'manifest_sha256':sha((P/'INPUT_MANIFEST.json').read_bytes())}))
