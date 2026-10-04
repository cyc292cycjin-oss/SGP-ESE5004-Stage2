"""Verify source audit Git vs actual project Git, including ignored data extensions."""
from engineering_review import *
workspace=HERE.parent.parent;project=BASE/'research_audit'
subprocess.run([sys.executable,str(HERE/'validate_delivery.py')],check=True)
subprocess.run(['git','-C',str(workspace),'add','--','research/01_baseline_construction'],check=True)
subprocess.run(['git','-C',str(workspace),'commit','-m','docs: preserve complete audit artifacts despite upstream ignore rules'],check=True)
entries=subprocess.check_output(['git','-C',str(workspace),'ls-files','--stage','-z','--','research/00_model_audit','research/00_source_provenance','research/01_baseline_construction']).decode().split('\0')
expected=[]
for entry in entries:
    if not entry:continue
    meta,rel=entry.split('\t',1);mode,blob,stage=meta.split();assert stage=='0'
    source=workspace/rel;target=project/rel;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(source.read_bytes());target.chmod(0o755 if mode=='100755' else 0o644)
    expected.append((rel,blob,mode))
subprocess.run(['git','-C',str(project),'add','-f','--','research/00_model_audit','research/00_source_provenance','research/01_baseline_construction'],check=True)
subprocess.run(['git','-C',str(project),'diff','--cached','--check','--','research/01_baseline_construction'],check=True)
subprocess.run(['git','-C',str(project),'commit','-m','docs: preserve all evidence files and portable artifact modes'],check=True)
actual={}
for entry in subprocess.check_output(['git','-C',str(project),'ls-files','--stage','-z','--','research']).decode().split('\0'):
    if entry:
        meta,rel=entry.split('\t',1);mode,blob,stage=meta.split();actual[rel]=(blob,mode)
for rel,blob,mode in expected:assert actual.get(rel)==(blob,mode),(rel,actual.get(rel),(blob,mode))
receipt_path=workspace/'outputs/phase2_delivery_receipt.json';receipt=json.loads(receipt_path.read_text())
receipt['local_audit_sha']=subprocess.check_output(['git','-C',str(workspace),'rev-parse','HEAD'],text=True).strip()
receipt['project_review_sha']=subprocess.check_output(['git','-C',str(project),'rev-parse','HEAD'],text=True).strip()
receipt['exact_git_blob_and_mode_matches']=len(expected)
receipt['worktree_statuses']['research_audit']={'sha':receipt['project_review_sha'],'status':subprocess.check_output(['git','-C',str(project),'status','--porcelain'],text=True)}
assert receipt['worktree_statuses']['research_audit']['status']==''
receipt_path.write_text(json.dumps(receipt,indent=2))
archive=workspace/'outputs/phase2_baseline_review_20261001.zip'
subprocess.run(['git','-C',str(project),'archive','--format=zip','--output',str(archive),'HEAD','research'],check=True)
receipt['zip']={'path':str(archive),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
receipt_path.write_text(json.dumps(receipt,indent=2));print(json.dumps({k:receipt[k] for k in ['local_audit_sha','project_review_sha','exact_git_blob_and_mode_matches','remote_publication','zip']},indent=2))
