"""Archive the review in local audit Git and an actual project review worktree.

No push, force-push, baseline merge, or deletion. Only explicit research paths
are staged. The receipt is outside the versioned payload to avoid self-hash cycles.
"""
from engineering_review import *
from datetime import datetime,timezone
workspace=HERE.parent.parent
subprocess.run([sys.executable,str(HERE/'validate_delivery.py')],check=True)
subprocess.run(['git','-C',str(workspace),'add','--','research/01_baseline_construction'],check=True)
subprocess.run(['git','-C',str(workspace),'diff','--cached','--check'],check=True)
subprocess.run(['git','-C',str(workspace),'commit','-m','audit: freeze baseline layers and validate industrial and carbon fixes'],check=True)
audit_sha=subprocess.check_output(['git','-C',str(workspace),'rev-parse','HEAD'],text=True).strip()
project=BASE/'research_audit';pool=BASE/'model-source'
if project.exists():raise FileExistsError('Review worktree exists; inspect and reuse it rather than overwrite')
subprocess.run(['git','-C',str(pool),'worktree','add','-b','codex/phase2-baseline-review',str(project),'a3616a68ee44592af6527ca9024a90f1956646ae'],check=True)
paths=subprocess.check_output(['git','-C',str(workspace),'ls-files','-z','--','research/00_model_audit','research/00_source_provenance','research/01_baseline_construction']).decode().split('\0')
copied=[]
for rel in paths:
    if not rel:continue
    source=workspace/rel;target=project/rel
    if source.is_symlink() or not source.is_file():raise ValueError(f'Unexpected tracked non-file: {rel}')
    if target.exists():raise FileExistsError(f'Project file already exists: {rel}')
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);target.chmod(0o644);copied.append(rel)
# These directories contain only the explicit audit Git file list copied above.
# Upstream ignores CSV/log/workbook extensions globally, so ordinary add is incomplete.
subprocess.run(['git','-C',str(project),'add','-f','--','research/00_model_audit','research/00_source_provenance','research/01_baseline_construction'],check=True)
subprocess.run(['git','-C',str(project),'diff','--cached','--check','--','research/01_baseline_construction'],check=True)
subprocess.run(['git','-C',str(project),'commit','-m','audit: attach baseline review with reproducible source and fix evidence'],check=True)
project_sha=subprocess.check_output(['git','-C',str(project),'rev-parse','HEAD'],text=True).strip()
statuses={}
for name in ['paper_reference','upstream_sc_baseline','research_model','fix_industrial_gdp','fix_carbon_config','fix_topology','research_audit']:
    p=BASE/name;statuses[name]={'sha':subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip(),'status':subprocess.check_output(['git','-C',str(p),'status','--porcelain'],text=True)}
assert all(not x['status'] for x in statuses.values())
receipt={'date_utc':datetime.now(timezone.utc).isoformat(),'local_audit_sha':audit_sha,'project_review_branch':'codex/phase2-baseline-review','project_review_sha':project_sha,'project_review_directory':str(project),'origin':'https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2.git','remote_publication':'NOT_PUSHED','inherited_evidence_files_included':True,'copied_files':len(copied),'worktree_statuses':statuses,'original_tutorial_status':subprocess.check_output(['git','-C',str(OLD),'status','--porcelain'],text=True),'audit_workspace_status':subprocess.check_output(['git','-C',str(workspace),'status','--porcelain'],text=True)}
out=workspace/'outputs';out.mkdir(exist_ok=True)
(out/'phase2_delivery_receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
