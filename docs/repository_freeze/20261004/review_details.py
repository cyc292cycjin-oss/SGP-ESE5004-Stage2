"""Bounded follow-up evidence for publication decision; no mutations to Git."""
from pathlib import Path
import subprocess,json,zipfile,io,hashlib,re
ROOT=Path(__file__).resolve().parent;E=ROOT/'evidence'
REPO='/home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit'
def git(*args):return subprocess.check_output(['git','-C',REPO,*args]).decode('utf8','replace').strip()
def blob(oid):return subprocess.check_output(['git','-C',REPO,'cat-file','blob',oid])
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
objects=json.loads((E/'NEW_REACHABLE_OBJECTS.json').read_text());refs=json.loads((E/'REFS_BEFORE.json').read_text())
small_refs={k:dict(sha=v['sha'],files=[]) for k,v in json.loads((E/'CANDIDATE_REFS.json').read_text()).items() if 'github-health-audit' not in k}
communication=[];binary=[]
for x in objects:
 if x['type']!='blob':continue
 for k in x['refs']:
  if k in small_refs:small_refs[k]['files'].append({a:x[a] for a in ['oid','paths','bytes']})
 if any(p.endswith('.xlsx') for p in x['paths']):
  z=zipfile.ZipFile(io.BytesIO(blob(x['oid'])))
  binary.append(dict(paths=x['paths'],sha256=hashlib.sha256(blob(x['oid'])).hexdigest(),embedded_media=[p for p in z.namelist() if p.startswith('xl/media/')],external_links=[p for p in z.namelist() if 'externalLinks/' in p],vba=[p for p in z.namelist() if 'vba' in p.lower()]))
 if any('REQUEST' in p or 'TASK_SCOPE' in p or p.endswith('.patch') for p in x['paths']):
  txt=blob(x['oid']).decode('utf8','replace')
  communication.append(dict(paths=x['paths'],header_labels=[line for line in txt.splitlines() if re.match(r'^(From:|To:|Subject:|Dear |Best regards|Purpose:)',line)],bytes=x['bytes']))
save('SMALL_REF_CONTENTS.json',small_refs);save('WORKBOOK_CONTAINER_REVIEW.json',binary);save('COMMUNICATION_FLAG_CONTEXT.json',communication)
families={
 'model_audit':'research/00_model_audit',
 'source_provenance':'research/00_source_provenance',
 'phase2_baseline':'research/01_baseline_construction',
 'buildings_3a1':'research/02_sector_coupling/buildings_heat',
 'buildings_3a2':'research/02_sector_coupling/buildings_heat_alignment',
 'buildings_3a3':'research/02_sector_coupling/buildings_phase3a3',
 'buildings_3a4':'research/02_sector_coupling/buildings_heat/phase3a4',
 'buildings_3a5':'research/02_sector_coupling/buildings_heat/phase3a5',
 'buildings_3a6':'research/02_sector_coupling/buildings_heat/phase3a6',
 'buildings_3a7':'research/02_sector_coupling/buildings_heat/phase3a7',
 'transport_3b1':'research/02_sector_coupling/transport/phase3b1',
 'transport_3b2':'research/02_sector_coupling/transport/phase3b2',
 'phase3c':'research/02_sector_coupling/phase3c',
 'github_health':'docs/repository_health/20261003',
 'data_registries':'research/01_baseline_construction/data_registry',
}
sha=refs['local']['refs/heads/codex/github-health-audit']
coverage=[]
for name,path in families.items():
 paths=git('ls-tree','-r','--name-only',sha,'--',path).splitlines()
 coverage.append(dict(family=name,path=path,head=sha,file_count=len(paths),files=paths,latest_commit=git('log','-1','--format=%H',sha,'--',path)))
save('ARCHIVE_FAMILIES.json',coverage)
save('ARCHIVE_CHAIN.json',dict(head=sha,commits=git('log','--format=%H%x09%P%x09%s','origin/main..'+sha).splitlines()))
dangling=[]
for line in json.loads((E/'INTEGRITY.json').read_text())['fsck']['stdout'].splitlines():
 if line.startswith('dangling commit '):
  oid=line.split()[-1];dangling.append(dict(sha=oid,subject=git('show','-s','--format=%s',oid),files=git('diff-tree','--root','--no-commit-id','--name-only','-r',oid).splitlines()))
save('DANGLING_REVIEW.json',dangling)
workflows=[]
for sha in sorted(set(v['sha'] for v in small_refs.values())):
 for p in git('ls-tree','-r','--name-only',sha,'--','.github/workflows').splitlines():
  txt=git('show',sha+':'+p)
  workflows.append(dict(sha=sha,path=p,text=txt))
save('CANDIDATE_WORKFLOWS.json',workflows)
print(json.dumps(dict(families=len(coverage),small_refs=len(small_refs),workbooks=binary,dangling=len(dangling))))
