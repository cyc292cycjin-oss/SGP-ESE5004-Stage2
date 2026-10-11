"""Verify lightweight A06 files only. No solver or network imports."""
from pathlib import Path
import json,hashlib,sys
root=Path(sys.argv[1]).resolve();base=root/'research/05_baseline_evolution/20261011/a06';e=base/'evidence'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
index=read(e/'A06_EVIDENCE_INDEX.json');count=0
for rel,r in index['files'].items():
 p=root/rel;assert p.is_file() and not p.is_symlink(),rel
 b=p.read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],rel
 if p.suffix=='.json':json.loads(b,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
 count+=1
n=read(e/'A06_NETWORK_STATIC_READOUT.json')['models'];c=read(e/'A06_COST_OBJECTIVE_EVIDENCE.json')
assert [r['id'] for r in n['author2025']['global_constraints']]==['lv_limit']
assert n['author2050']['global_constraints'][1]['constant']==1e8
assert [r['id'] for r in n['frozen2050']['global_constraints']]==['lv_limit']
assert all(len(m['weights'])==3 and all(w['sum']==8760 and w['count']==2920 for w in m['weights'].values()) for m in n.values())
assert c['frozen_meta']['fixed_accounts_unknown_price_count']==807
assert c['v3_derivation']['changed_objective_columns']==10628915
assert c['v3_derivation']['adapted_objective']['offset']==-12788967.997821666
assert c['first_run_recorded_dual_costs_and_acceptance']['acceptance']['historical_gate6_pass'] is False
v=read(e/'A06_VALIDATION_RECEIPT.json');assert v['checks_passed']==17 and all(x['status']=='PASS_VERIFIED' for x in v['checks'])
assert v['G6_05']=='PAUSED_BY_USER'
print(json.dumps({'status':'PASS','SHA_files_checked':count,'prior_static_checks':17,'solver_calls':0,'scientific_files_written':0}))
