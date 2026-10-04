"""Verify delivery contents and commit Gate3 audit only. Does not push/solve."""
from integrate import *
import csv,decimal,shutil,difflib
G=S/'research/04_model_assembly/gate3';GE=G/'evidence'
head=json.loads((E/'IMPLEMENTATION_COMMITS.json').read_text())[-1]['sha']
assert git('rev-parse','HEAD')==head and not git('status','--porcelain')
start=json.loads((E/'START.json').read_text())
def refs(text):return {line.split('\t')[1]:line.split('\t')[0] for line in text.splitlines()}
before=refs(start['remote_refs']);now=refs(git('ls-remote','origin'))
protected={k:v for k,v in before.items() if k=='refs/heads/main' or k.startswith(('refs/heads/archive/','refs/heads/reference/','refs/tags/reference/'))}
assert all(now.get(k)==v for k,v in protected.items())
assert now['refs/heads/research/full-sc-baseline']==start['head']
tables=json.loads((W/'build/tables.json').read_text());csvchecks=[]
for name,t in tables.items():
 data=list(csv.reader((G/name).open(encoding='utf-8-sig',newline='')));expected=t['export_values']
 assert len(data)==len(expected)
 for ri,(row,src) in enumerate(zip(data,expected)):
  assert len(row)==len(src)
  for ci,(value,old) in enumerate(zip(row,src)):
   if isinstance(old,bool):assert value==str(old).lower(),(name,ri,ci)
   elif isinstance(old,(int,float)):assert decimal.Decimal(value)==decimal.Decimal(str(old)),(name,ri,ci)
   else:assert value==old,(name,ri,ci,value,old)
 csvchecks.append(dict(file=name,rows=len(data)-1,exact_source_values=True,sha256=sha(G/name)))
(E/'CSV_VALUE_CHECK.json').write_text(json.dumps(csvchecks,indent=2))
allow=list(json.loads((E/'INTEGRATION_ALLOWLIST.json').read_text()))
current={rel:sha(R/rel) for rel in allow}
for rel in allow:assert current[rel]==sha(S/rel)
(E/'FINAL_IMPLEMENTATION_HASHES.json').write_text(json.dumps(current,indent=2))
(E/'FINAL_IMPLEMENTATION.diff').write_bytes(sp.check_output(['git','diff',start['head'],head,'--',*allow],cwd=R))
changes=git('diff','--name-only',start['head'],head).splitlines();assert set(changes)==set(allow)
guards={rel:sha(R/rel)==h for rel,h in start['gate2_hashes'].items()};assert all(guards.values())
for p in (E/'source').rglob('*.py'):assert sha(p)==sha(R/p.relative_to(E/'source'))
import yaml
oldconfig=yaml.safe_load(sp.check_output(['git','show',start['head']+':configs/research/baseline.yaml'],cwd=R))
newconfig=yaml.safe_load((R/'configs/research/baseline.yaml').read_text())
assert oldconfig['research_demand']==newconfig['research_demand']
provenance=[];pd=GE/'prior_gate_design';pd.mkdir(exist_ok=True)
for rel in ['research/04_model_assembly/gate1/PHASE4_STATIC_VALIDATION_FRAMEWORK.md','research/04_model_assembly/gate1/PHASE4_SHARED_CARRIER_PREFLIGHT.csv','research/04_model_assembly/gate2/RESEARCH_DEMAND_ACCOUNTING_SPEC.md','research/04_model_assembly/gate2/RESEARCH_ELECTRICITY_PARENT_ASTAR.md','research/04_model_assembly/gate2/SHIPPING_COMPATIBILITY_PROVENANCE.json','research/04_model_assembly/gate2/PHASE4_GATE2_READINESS.md']:
 src=R/rel;shutil.copyfile(src,pd/src.name)
 provenance.append(dict(file=rel,sha256=sha(src),commit=git('log','-1','--format=%H','--',rel)))
for p in (GE/'phase3_design').iterdir():
 rel='research/02_sector_coupling/phase3c/'+p.name
 frozen='f7710800b495b60767ab6b7a5963f38b41aa03b4'
 archived=sp.check_output(['git','show',frozen+':'+rel],cwd=R)
 assert hashlib.sha256(archived).hexdigest()==sha(p),(rel,'archive hash mismatch')
 provenance.append(dict(file=rel,sha256=sha(p),repository_layer='frozen archive, not Research checkout',archive_commit=frozen,commit=git('log','-1','--format=%H',frozen,'--',rel)))
(E/'DESIGN_PROVENANCE.json').write_text(json.dumps(provenance,indent=2))
review=dict(base=start['head'],tested_implementation=head,changed_files=changes,only_allowlisted_files=True,upstream_unchanged=True,gate2_hashes_preserved=guards,demand_config_semantically_unchanged=True,protected_refs=protected,csv_values_pass=True,solver_runs=0,full_network_assemblies=0)
(E/'FINAL_DIFF_REVIEW.json').write_text(json.dumps(review,indent=2))
for name in ['CSV_VALUE_CHECK.json','CSV_EXPORT_RECEIPT.json','FINAL_IMPLEMENTATION_HASHES.json','FINAL_IMPLEMENTATION.diff','DESIGN_PROVENANCE.json','FINAL_DIFF_REVIEW.json']:
 shutil.copyfile(E/name,GE/name)
for name in ['export_tables.mjs','finalize_audit.py']:shutil.copyfile(W/name,GE/'tools'/name)
(GE/'EVIDENCE_HASHES.json').write_text(json.dumps({p.relative_to(GE).as_posix():sha(p) for p in sorted(GE.rglob('*')) if p.is_file() and p.name!='EVIDENCE_HASHES.json'},indent=2))
for p in G.rglob('*'):
 if p.is_file():cp(p.relative_to(S).as_posix())
result=commit('audit: deliver Gate3 carrier isolation and carbon scope evidence\n\nResume from verified Gate2; reuse pinned tutorial/source evidence. Distinguish\nreference shared-resource paths from tested isolated fragments and preserve\nall pending inputs. Include 16 deliverables, exact draft review, 60 new tests\nand Buildings 1062, Shipping 17, Gate2 70, Gate1 20, manifest 7 regressions.\nGate4 remains blocked by accepted inputs, attribution and deferred topology.', ['research/04_model_assembly/gate3'])
assert not git('status','--porcelain')
for p in G.rglob('*'):
 if p.is_file():
  rel=p.relative_to(S).as_posix();tracked=sp.check_output(['git','show','HEAD:'+rel],cwd=R)
  assert hashlib.sha256(tracked).hexdigest()==sha(p),(rel,'Git byte mismatch')
(E/'AUDIT_COMMIT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
