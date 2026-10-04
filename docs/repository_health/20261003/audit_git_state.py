"""Run in WSL: record identities, fetch origin without pruning, inspect Git objects.

No checkout/merge/reset or model workflow. Only refs/objects and audit evidence change.
"""
from pathlib import Path
from datetime import datetime,timezone
import collections,hashlib,json,subprocess
import yaml
R=Path(__file__).resolve().parent;E=R/'evidence';S=E/'source';S.mkdir(exist_ok=True)
REPO=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit')
U='a3616a68ee44592af6527ca9024a90f1956646ae'
def call(repo,*args):
    p=subprocess.run(['git','-C',str(repo),*args],capture_output=True)
    return dict(command=['git',*args],exit_code=p.returncode,stdout=p.stdout.decode('utf8',errors='replace').strip(),stderr=p.stderr.decode('utf8',errors='replace').strip())
def git(*args):
    p=call(REPO,*args);assert p['exit_code']==0,p;return p['stdout']
before={name:call(REPO,*args) for name,args in {
 'head':['rev-parse','HEAD'],'branch':['branch','--show-current'],'status':['status','--porcelain'],
 'remotes':['remote','-v'],'refs':['show-ref'],'worktrees':['worktree','list','--porcelain'],
 'fetch_refspec':['config','--get-all','remote.origin.fetch']}.items()}
(E/'WSL_GIT_BEFORE.json').write_text(json.dumps(before,indent=2))
fetch=call(REPO,'fetch','origin');assert fetch['exit_code']==0,fetch
remote=call(REPO,'ls-remote','--heads','--tags','origin');assert remote['exit_code']==0,remote
fsck=call(REPO,'fsck','--full','--no-reflogs')
(E/'GIT_FSCK.txt').write_text(fsck['stdout']+'\n'+fsck['stderr'],encoding='utf8')
assert fsck['exit_code']==0,fsck
assert git('rev-parse','origin/main')==U
assert git('rev-parse','HEAD')==before['head']['stdout'] and git('status','--porcelain')==before['status']['stdout']
raw=subprocess.check_output(['git','-C',str(REPO),'ls-tree','-r','-l','-z',U])
entries=[]
for row in raw.split(b'\0'):
    if not row:continue
    props,name=row.split(b'\t',1);mode,kind,oid,size=props.decode().split()
    entries.append(dict(path=name.decode(),mode=mode,type=kind,oid=oid,bytes=int(size) if size!='-' else None))
workflows=[];snapshots=[]
for x in entries:
    name=x['path']
    if name.startswith('.github/workflows/') or name in ['.gitignore','.gitattributes','.gitmodules','.github/dependabot.yml'] or name.endswith('/.gitattributes') or name=='AGENTS.md':
        snapshot_path={'.gitattributes':'ROOT_GITATTRIBUTES.txt','.gitignore':'ROOT_GITIGNORE.txt'}.get(name,name)
        b=subprocess.check_output(['git','-C',str(REPO),'show',U+':'+name]);p=S/snapshot_path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        snapshots.append(dict(path=name,snapshot_path=snapshot_path,git_sha=U,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
        if name.startswith('.github/workflows/') and name.endswith(('.yml','.yaml')):
            v=yaml.load(b.decode(),Loader=yaml.BaseLoader)
            assert isinstance(v,dict) and 'on' in v and isinstance(v.get('jobs'),dict),name
            workflows.append(dict(path=name,yaml_parsed=True,on=v['on'],jobs=list(v['jobs']),parsed=v))
large=sorted((x for x in entries if x['type']=='blob'),key=lambda x:x['bytes'],reverse=True)
archive_ext={'.zip','.pdf','.nc','.netcdf','.xlsx','.csv','.parquet','.gz','.7z'}
special=[x for x in entries if Path(x['path']).suffix.lower() in archive_ext]
envpaths=[x['path'] for x in entries if set(Path(x['path']).parts)&{'.venv','venv','site-packages','node_modules','__pycache__'}]
lfs=[]
for x in entries:
    if x['type']=='blob' and x['bytes']<=1024:
        b=subprocess.check_output(['git','-C',str(REPO),'cat-file','blob',x['oid']])
        if b.startswith(b'version https://git-lfs.github.com/spec/v1'):lfs.append(x['path'])
identities=[]
worktrees=[line[9:] for line in before['worktrees']['stdout'].splitlines() if line.startswith('worktree ')]
remote_branches=git('for-each-ref','--format=%(refname)','refs/remotes/origin').splitlines()
for path in worktrees:
    sha=call(path,'rev-parse','HEAD')['stdout'];status=call(path,'status','--porcelain')
    containing=[ref for ref in remote_branches if call(REPO,'merge-base','--is-ancestor',sha,ref)['exit_code']==0]
    identities.append(dict(path=path,head=sha,status=status['stdout'],status_exit_code=status['exit_code'],remote_branches_containing_head=containing))
record=dict(checked_utc=datetime.now(timezone.utc).isoformat(),repo=str(REPO),head=git('rev-parse','HEAD'),default_remote_head=U,fetch=fetch,ls_remote=remote,fsck_exit_code=fsck['exit_code'],fsck_dangling_lines=sum('dangling ' in s for s in fsck['stdout'].splitlines()),count_objects=git('count-objects','-vH'),unmerged_index=git('ls-files','-u'),tracked_files=len(entries),tracked_bytes=sum(x['bytes'] or 0 for x in entries),submodules=[x for x in entries if x['mode']=='160000'],lfs_pointers=lfs,environment_paths=envpaths,python_files=[x['path'] for x in entries if x['path'].endswith('.py')],notebooks=[x['path'] for x in entries if x['path'].endswith('.ipynb')],largest_files=large[:20],special_tracked_files=special,worktrees=identities,workflow_yaml=workflows,source_snapshots=snapshots)
(E/'REPOSITORY_GIT_AUDIT.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(fetch_pass=True,fsck_pass=True,tracked_files=len(entries),tracked_bytes=record['tracked_bytes'],workflow_yaml_count=len(workflows),python_files=len(record['python_files']),submodules=len(record['submodules']),lfs_pointers=len(lfs),environments=len(envpaths),worktrees=len(identities))))
