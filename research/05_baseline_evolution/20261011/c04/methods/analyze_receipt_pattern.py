"""Reuse A03 identity tables and actual C03 receipts. No raw matrix scan."""
from pathlib import Path
import json,hashlib,math,collections
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c04_daily_pattern_20261012')
REPO=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
A=REPO/'research/05_baseline_evolution/20261011/evidence'
L=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c02r_c03_combined_20261012/cloud_light')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
oldg=read(A/'A03_GROUP_CROSSWALK.json');olda=read(A/'A03_ACCOUNT_CROSSWALK.json')
p=read(L/'postprocess/PHYSICAL_CHECKS.json');d=p['details']
newg={r['buses'][0]:r for r in d['fixed_group_obligations_v4']}
newa={r['asset']:r for r in d['fixed_prefix_checks']}
assert set(newg)=={r['bus'] for r in oldg} and set(newa)=={r['asset'] for r in olda}
foa={r['asset'] for r in olda if not r['passed']};fna={a for a,r in newa.items() if not r['passed']}
fog={r['bus'] for r in oldg if not r['group_passed']};fng={a for a,r in newg.items() if not r['passed']}
rows=[]
for r in oldg:
    b=r['bus'];n=newg[b];parts=r['source_account'].split(':')
    rows.append(dict(bus=b,country=parts[0],sector=parts[2],account_count=r['account_count'],source_D_MWh=n['source_demand_integral_mwh'],old_pass=r['group_passed'],daily_pass=n['passed'],daily_gross_oversupply_MWh=n['gross_oversupply_mwh'],accounts=[a['asset'] for a in olda if b in a['FinalBuses']]))
def tab(keys):
    t={}
    for r in rows:
        k=tuple(r[x] for x in keys);v=t.setdefault(k,dict(groups=0,failed=0,min_D_MWh=math.inf,max_D_MWh=0))
        v['groups']+=1;v['failed']+=not r['daily_pass'];v['min_D_MWh']=min(v['min_D_MWh'],r['source_D_MWh']);v['max_D_MWh']=max(v['max_D_MWh'],r['source_D_MWh'])
    return [{**dict(zip(keys,k)),**v} for k,v in sorted(t.items())]
pairs=[]
for low,high in [(1,3),(2,4),(2,3),(1,4)]:
    candidates=[]
    for x in rows:
        if x['account_count']!=low:continue
        for y in rows:
            if y['account_count']!=high:continue
            same=x['country']==y['country'] and x['sector']==y['sector']
            candidates.append((not same,abs(math.log(x['source_D_MWh']/y['source_D_MWh'])),x['bus'],y['bus']))
    v=min(candidates);pairs.append(dict(count_pair=[low,high],same_country_and_sector=not v[0],absolute_log_D_ratio=v[1],passing_bus=v[2],failing_bus=v[3]))
selected=sorted({b for p in pairs[:2] for b in (p['passing_bus'],p['failing_bus'])})
maxbus=max(rows,key=lambda x:x['daily_gross_oversupply_MWh'])['bus']
if maxbus not in selected:selected.append(maxbus)
k=read(L/'postprocess/KKT.json');Z=max(1,abs(k['primal_objective']),abs(k['dual_objective_numeric']))
result=dict(evidence_class='RECEIPT_ASSET_ID_RECONCILIATION_NOT_CAUSAL',sources=[dict(path=str(x),sha256=sha(x)) for x in [A/'A03_GROUP_CROSSWALK.json',A/'A03_ACCOUNT_CROSSWALK.json',L/'postprocess/PHYSICAL_CHECKS.json',L/'postprocess/KKT.json']],old_failed_accounts=len(foa),daily_failed_accounts=len(fna),account_symmetric_difference=sorted(foa^fna),old_failed_groups=len(fog),daily_failed_groups=len(fng),group_symmetric_difference=sorted(fog^fng),cardinality_table=tab(['account_count']),country_sector_cardinality=tab(['country','sector','account_count']),selected_pairs=pairs,selected_buses=selected,selection_rule='closest log annual demand, prefer same country AND sector, deterministic Unicode tie break; 1 vs3 and2 vs4 plus max oversupply',global_KKT=dict(Z=Z,complementarity_L1_over_Z=k['complementarity_l1']/Z,weighted_stationarity_L1_over_Z=k['stationarity_weighted_l1']/Z,relative_gap=k['relative_gap']),groups=rows)
(W/'C04_RECEIPT_PATTERN.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['groups','sources']},ensure_ascii=False,indent=2))
