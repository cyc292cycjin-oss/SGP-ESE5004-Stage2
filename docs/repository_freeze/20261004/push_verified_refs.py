"""Publish only the reviewed twelve refs. No force, no merge, no model edits.

One-time operation for the 2026-10-04 user-authorized freeze. Collisions abort.
"""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,json
ROOT=Path(__file__).resolve().parent;E=ROOT/'evidence'
REPO='/home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit'
U='a3616a68ee44592af6527ca9024a90f1956646ae'
PLAN=[
 ('refs/tags/reference/tutorial-ce327bfa','ce327bfae2abe5526d4c1976173f0f8d08366ba5','Immutable tutorial reference; not paper reproduction'),
 ('refs/tags/reference/paper-run-5bacad70','5bacad702ccfed17ad19ab510fa710651e966f2c','Immutable author paper actual-run source reference'),
 ('refs/tags/reference/paper-publication-99159edb','99159edb7298b847fea517bf05c3f388493501c9','Immutable later paper publication/cleanup reference'),
 ('refs/tags/reference/upstream-sc-a3616a68',U,'Immutable upstream SC baseline; not assembled Full-SC'),
 ('refs/tags/reference/buildings-validation-50a73d8f','50a73d8f531132c5459174a55cac412d5f684462','Immutable combined validation record; tested source is parent 353dec3c83b859eab39bcf2dff79fe30d88a2ec0'),
 ('refs/heads/codex/fix-industrial-gdp','a7a8f06b43f0dcce0dbd7005b989d8f73d142b81','Isolated industrial GDP candidate; not merged into research model'),
 ('refs/heads/codex/fix-carbon-config','753ac81c23f8b9a1ca8ceed531d0630b56f6953d','Isolated carbon-key engineering candidate; no new policy'),
 ('refs/heads/codex/buildings-e1','30bafa420e5cd639e696cbdd56de0e7df36c0e47','Preserve E1 source fix 92e9118be20f0b3802f385adac2f56650d57299d and validation records'),
 ('refs/heads/codex/buildings-e2','070db2918186829908a02a0b72a7b4426711c653','Preserve E2 source fix 31037d60d69fa762c9ed8ec9ce8289d95bd6a181 and validation records'),
 ('refs/heads/codex/buildings-e4','9342893fcf467eadbbc410f59c3dbe817d123aa9','Preserve E4 source fix 5d761eceeeb0d0519208d760224a41ff50ec1e30 and validation records'),
 ('refs/heads/codex/buildings-accounting-validation','50a73d8f531132c5459174a55cac412d5f684462','Preserve real combined buildings validation history; no new merges'),
 ('refs/heads/codex/transport-shipping-reviewable-patch','85a32dc231458fd753445df38d422b78435b8aad','Preserve two shipping functional candidates and byte-fidelity commit'),
]
def run(*args):
 p=subprocess.run(['git','-C',REPO,*args],capture_output=True)
 return dict(args=list(args),exit_code=p.returncode,stdout=p.stdout.decode('utf8','replace').strip(),stderr=p.stderr.decode('utf8','replace').strip())
def git(*args):
 p=run(*args);assert p['exit_code']==0,p;return p['stdout']
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
assert not (E/'PUSH_RECEIPT.json').exists(),'One-time receipt already exists. Read it; do not repeat blindly.'
assert git('remote','get-url','origin')=='https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2.git'
remote={line.split()[1]:line.split()[0] for line in git('ls-remote','--heads','--tags','origin').splitlines()}
assert remote['refs/heads/main']==U
assert git('status','--porcelain')==''
for ref,sha,purpose in PLAN:
 assert ref not in remote,('Remote collision',ref)
 assert git('cat-file','-t',sha)=='commit'
 if ref.startswith('refs/tags/'):
  assert run('show-ref','--verify',ref)['exit_code']!=0,('Local tag collision',ref)
 else:assert git('rev-parse',ref)==sha
save('PUSH_PLAN.json',[dict(LocalRef=r,RemoteRef=r,ExpectedSHA=s,Purpose=p,category='IMMUTABLE_REFERENCE' if r.startswith('refs/tags/') else 'CANDIDATE_FIX') for r,s,p in PLAN])
created=[]
for ref,sha,purpose in PLAN:
 if ref.startswith('refs/tags/'):
  message=f'{purpose}\nSource SHA: {sha}\nContext: Pre-Phase4 research-history freeze, 2026-10-04.\nImmutable reference: do not retarget. No scientific acceptance implied.\n'
  git('-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','tag','-a',ref[10:],sha,'-m',message)
  created.append(dict(ref=ref,tag_object=git('rev-parse',ref),peeled_sha=git('rev-parse',ref+'^{commit}')))
save('ANNOTATED_TAGS.json',created)
push=run('push','--atomic','origin',*[r+':'+r for r,s,p in PLAN])
save('PUSH_RECEIPT.json',dict(utc=datetime.now(timezone.utc).isoformat(),push=push,created_tags=created))
assert push['exit_code']==0,push
fetch=run('fetch','--prune','--tags','origin');assert fetch['exit_code']==0,fetch
remote={line.split()[1]:line.split()[0] for line in git('ls-remote','--heads','--tags','origin').splitlines()}
rows=[]
for ref,sha,purpose in PLAN:
 fetched_ref=ref if ref.startswith('refs/tags/') else ref.replace('refs/heads/','refs/remotes/origin/',1)
 fetched=git('rev-parse',fetched_ref+'^{commit}')
 remote_sha=remote.get(ref+'^{}',remote.get(ref))
 assert fetched==sha==remote_sha,(ref,sha,fetched,remote_sha)
 rows.append(dict(LocalRef=ref,RemoteRef=ref,ExpectedSHA=sha,FetchedSHA=fetched,Match=True,Purpose=purpose))
assert remote['refs/heads/main']==U and git('rev-parse','origin/main')==U
milestones=json.loads((E/'MILESTONES.json').read_text())
for item in milestones:
 item['remote_after']=[ref for ref,sha,p in PLAN if run('merge-base','--is-ancestor',item['sha'],ref)['exit_code']==0]
 assert item['remote_after'],item
save('REMOTE_VERIFICATION_ROWS.json',rows)
save('MILESTONES_AFTER.json',milestones)
save('REMOTE_AFTER.json',dict(utc=datetime.now(timezone.utc).isoformat(),fetch=fetch,refs=remote,main_unchanged=True,phase4_exists='refs/heads/research/full-sc-baseline' in remote))
print(json.dumps(dict(pushed=len(rows),all_exact_match=True,main=U,phase4_exists=False)))
