"""Read Git history and newly reachable objects before any remote publication.

Run in WSL. Fetch updates remote-tracking refs only. No model or source edits.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, subprocess, re

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'evidence'
OUT.mkdir(exist_ok=True)
REPO = '/home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit'
MILESTONES = {
 'tutorial':'ce327bfae2abe5526d4c1976173f0f8d08366ba5',
 'paper_run':'5bacad702ccfed17ad19ab510fa710651e966f2c',
 'paper_publication':'99159edb7298b847fea517bf05c3f388493501c9',
 'upstream':'a3616a68ee44592af6527ca9024a90f1956646ae',
 'industrial_gdp':'a7a8f06b43f0dcce0dbd7005b989d8f73d142b81',
 'carbon_key':'753ac81c23f8b9a1ca8ceed531d0630b56f6953d',
 'buildings_e1_source':'92e9118be20f0b3802f385adac2f56650d57299d',
 'buildings_e2_source':'31037d60d69fa762c9ed8ec9ce8289d95bd6a181',
 'buildings_e4_source':'5d761eceeeb0d0519208d760224a41ff50ec1e30',
 'buildings_validation':'50a73d8f531132c5459174a55cac412d5f684462',
 'buildings_tested_source':'353dec3c83b859eab39bcf2dff79fe30d88a2ec0',
 'shipping_allocation':'512c6cc2e53c579976d269486a7e328a0f372017',
 'shipping_target_guard':'cf4b0f816086470dce40ec950e20c045044eec0c',
 'shipping_final':'85a32dc231458fd753445df38d422b78435b8aad',
}
def run(*args, repo=REPO, data=None):
 p=subprocess.run(['git','-C',repo,*args],input=data,capture_output=True)
 return {'args':list(args),'exit_code':p.returncode,'stdout':p.stdout.decode('utf8','replace').strip(),'stderr':p.stderr.decode('utf8','replace').strip()}
def git(*args, **kwargs):
 p=run(*args,**kwargs); assert p['exit_code']==0,p; return p['stdout']
def save(name,x):
 (OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def worktrees():
 result=[]
 for block in git('worktree','list','--porcelain').split('\n\n'):
  lines=block.splitlines(); path=lines[0][9:]
  result.append(dict(path=path,head=git('rev-parse','HEAD',repo=path),branch=git('branch','--show-current',repo=path),status=git('status','--porcelain',repo=path)))
 return result

before=dict(utc=datetime.now(timezone.utc).isoformat(),repo=REPO,remotes=git('remote','-v'),refs=git('show-ref'),worktrees=worktrees(),symbolic_origin_head=run('symbolic-ref','refs/remotes/origin/HEAD'))
save('WSL_BEFORE.json',before)
fetch=run('fetch','origin');assert fetch['exit_code']==0,fetch
remote=git('ls-remote','--symref','origin')
fsck=run('fsck','--full')
save('INTEGRITY.json',dict(fetch=fetch,ls_remote=remote,fsck=fsck,count_objects=run('count-objects','-vH')))
assert fsck['exit_code']==0,fsck
refs={row.split('\t')[0]:row.split('\t')[1] for row in git('for-each-ref','--format=%(refname)\t%(objectname)').splitlines()}
local={k:v for k,v in refs.items() if k.startswith('refs/heads/')}
origin={k:v for k,v in refs.items() if k.startswith('refs/remotes/origin/')}
milestones=[]
for name,sha in MILESTONES.items():
 milestones.append(dict(name=name,sha=sha,type=git('cat-file','-t',sha),subject=git('show','-s','--format=%s',sha),parents=git('show','-s','--format=%P',sha),local_containing=git('for-each-ref','--contains',sha,'--format=%(refname)','refs/heads').splitlines(),remote_containing=git('for-each-ref','--contains',sha,'--format=%(refname)','refs/remotes/origin').splitlines()))
save('MILESTONES.json',milestones)
unpushed={k:int(git('rev-list','--count',v,'--not',*origin.values())) for k,v in local.items()}
save('REFS_BEFORE.json',dict(local=local,origin=origin,tags={k:v for k,v in refs.items() if k.startswith('refs/tags/')},unpushed=unpushed))
candidates={k:v for k,v in local.items() if k in ['refs/heads/codex/github-health-audit','refs/heads/codex/fix-industrial-gdp','refs/heads/codex/fix-carbon-config','refs/heads/codex/buildings-e1','refs/heads/codex/buildings-e2','refs/heads/codex/buildings-e4','refs/heads/codex/buildings-accounting-validation','refs/heads/codex/transport-shipping-reviewable-patch']}
candidates.update({'milestone/'+k:v for k,v in MILESTONES.items()})
by_oid={};by_ref={}
for name,sha in candidates.items():
 objects=git('rev-list','--objects',sha,'--not',*origin.values()).splitlines()
 ids=[]
 for line in objects:
  oid,_,path=line.partition(' '); ids.append(oid)
  entry=by_oid.setdefault(oid,dict(oid=oid,paths=[],refs=[]))
  if path and path not in entry['paths']:entry['paths'].append(path)
  entry['refs'].append(name)
 by_ref[name]=dict(sha=sha,new_object_count=len(ids),oids=ids)
batch=git('cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)',data=('\n'.join(by_oid)+'\n').encode())
for line in batch.splitlines():
 oid,kind,size=line.split();by_oid[oid].update(type=kind,bytes=int(size))
save('NEW_REACHABLE_OBJECTS.json',list(by_oid.values()))
save('CANDIDATE_REFS.json',by_ref)
blobs=[x for x in by_oid.values() if x['type']=='blob']
flags=[]
secret_patterns={
 'github_token':rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})',
 'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
 'aws_access_key':rb'\bAKIA[A-Z0-9]{16}\b',
 'credential_assignment':rb'(?i)(?:password|api_key|access_token)\s*[=:]\s*[\x22\x27][A-Za-z0-9_/+.-]{12,}[\x22\x27]',
 'communication':rb'(?im)^(?:From:|To:|Subject:|Dear (?:Professor|Prof|Dr)|Best regards|Sent from my)',
}
for x in blobs:
 reasons=[];paths=' '.join(x['paths']);suffixes={Path(p).suffix.lower() for p in x['paths']}
 if x['bytes']>10_000_000:reasons.append('over_10_MB_review')
 if suffixes & {'.nc','.netcdf','.zip','.7z','.pdf','.xlsx','.xls','.parquet','.gz','.png','.jpg','.jpeg'}:reasons.append('binary_or_raw_review')
 if re.search(r'(?i)(node_modules|site-packages|__pycache__|cutouts/|results-asean-paper|\.env$|\.pem$|id_rsa|email|correspondence|whatsapp|wechat)',paths):reasons.append('path_review')
 b=subprocess.check_output(['git','-C',REPO,'cat-file','blob',x['oid']])
 if b'\x00' not in b[:10000]:
  for label,pat in secret_patterns.items():
   if re.search(pat,b): reasons.append(label)
 if reasons:flags.append({**x,'flags':reasons})
save('SAFETY_REVIEW_FLAGS.json',flags)
save('AUDIT_SUMMARY.json',dict(utc=datetime.now(timezone.utc).isoformat(),branches=len(local),worktrees=len(before['worktrees']),milestones=len(milestones),new_blobs=len(blobs),new_blob_bytes=sum(x['bytes'] for x in blobs),flags=len(flags),largest=sorted(blobs,key=lambda x:x['bytes'],reverse=True)[:15]))
print(json.dumps(dict(branches=len(local),milestones=len(milestones),new_blobs=len(blobs),flags=len(flags),fsck='PASS')))
