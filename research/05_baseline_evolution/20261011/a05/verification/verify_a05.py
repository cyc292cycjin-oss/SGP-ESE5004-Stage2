"""Checks A05 artifact/source consistency only; no model/solver/network access."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from collections import Counter

def verify(folder,repo):
    e=folder/'evidence' if (folder/'evidence').is_dir() else folder
    load=lambda n:json.loads((e/n).read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
    a=load('A05_CROSS_BORDER_ASSET_INVENTORY.json');s=load('A05_SOURCE_AND_DECISION_EVIDENCE.json');b=load('A05_REACHABILITY_AND_BOUNDARIES.json');d=load('A05_ELECTRICITY_INPUT_DIFF.json')
    checks=[]
    def ok(label,condition):
        if not condition:raise AssertionError(label)
        checks.append({'check':label,'status':'PASS'})
    m=a['models'][0]
    ok('current exact component counts',m['component_counts']==dict(buses=3443,links=3358,lines=105,generators=860,stores=1104,loads=1737,storage_units=43,transformers=0))
    ok('current classification covers every branch',sum(m['classification_counts'].values())==3463)
    ok('actual cross-border 19 Line + 5 DC',Counter(x['component'] for x in m['cross_border_assets'])=={'lines':19,'links':5} and all(x['carrier']=='DC' for x in m['cross_border_assets'] if x['component']=='links'))
    old=s['frozen_network_manifest']['selected_fields']['actual_network_validation']['interconnect']
    prior={(x['ComponentType'].lower()+'s',x['Component'],x['Bus0'],x['Bus1']) for x in old if x['Classification']=='CROSS_BORDER'}
    actual={(x['component'],x['id'],x['ports'][0]['bus'],x['ports'][1]['bus']) for x in m['cross_border_assets']}
    ok('independent old assembly interconnect receipt agrees',prior==actual and len(prior)==24)
    ok('no hidden non-electric cross-country component',m['non_electric_graph']['multi_country_components']==[] and m['global_pool_interfaces']==[])
    ok('only unassigned current Bus is reporting atmosphere',len(m['unresolved_buses'])==1 and m['unresolved_buses'][0]['bus'] in m['atmosphere_reporting_buses'])
    ok('atmosphere is not a withdrawable Link supply',b['atmosphere_interface_direction_check']=={'nonzero_interfaces':1748,'negative_or_reversible':[],'interpretation':'Atmosphere is not a withdrawable input port for any installed Link.'})
    ok('400 independent external priced sources',Counter(x['carrier'] for x in m['external_or_fuel_generators'])==dict(coal=100,gas=100,lignite=100,oil=100) and all(x['research_role']=='EXTERNAL_SUPPLY' and x['p_min_pu']==0 and x['p_nom_extendable'] and x['p_nom_max']=='Infinity' and x['marginal_cost']>0 for x in m['external_or_fuel_generators']))
    ok('all 100 H2 nodes have FT-oil endpoint plus fuel cell',all(x['FT_ids'] and x['fuel_cell_ids'] and x['oil_final_load_count']>0 for x in b['hydrogen_local_end_use_coverage']) and len(b['hydrogen_local_end_use_coverage'])==100 and not m['direct_h2_nh3_methanol_loads'])
    ok('2025 electrical IDs and ports preserved',d['common_count']==118 and not d['current_only'] and not d['paper2025_only'] and not d['port_changes'])
    ok('compared electric changes limited to costs and inactive efficiency3',set(f for v in d['parameter_changes'].values() for f in v)<={'capital_cost','marginal_cost','efficiency3'})
    ok('no unexamined dynamic cross-border bound',all(not z['cross_border_affected_ids'] for x in a['models'] for z in x['branch_dynamic_bound_fields']))
    ok('baseline policy disabled and lv_limit alone',s['frozen_network_manifest']['selected_fields']['policy_cap_enabled'] is False and m['global_constraints']['global_constraints_i']==['lv_limit'])
    receipts=s['scheme_a_reused_evidence'];v=next(x['receipt'] for x in receipts if x['path'].endswith('STATIC_ACCEPTANCE_RECEIPT.json'))
    ok('Scheme A remains source-only accepted reference',v['status']=='SCHEME_A_STATIC_ACCEPTED' and v['changed_accounts']==180 and v['groups_D_le_Q']==385 and v['solver_calls']==0 and v['full_LP_builds']==0)
    sources=s['source_snippets']+s['supplementary_sources']
    for x in sources:
        raw=subprocess.check_output(['git','-C',str(repo),'show',x['commit']+':'+x['path']]);assert hashlib.sha256(raw).hexdigest()==x['sha256']
        text=raw.decode().splitlines()
        for part in x['snippets']:
            assert part['text']=='\n'.join(f'{i+1}: {text[i]}' for i in range(part['start_line']-1,part['end_line']))
    for x in receipts:
        raw=subprocess.check_output(['git','-C',str(repo),'show',x['commit']+':'+x['path']]);assert hashlib.sha256(raw).hexdigest()==x['sha256'] and json.loads(raw)==x['receipt']
    ok('all cited fixed-commit source and Scheme A SHA match',True)
    for p in e.glob('A05_*.json'):
        json.loads(p.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
    ok('strict JSON, no NaN/Infinity tokens',True)
    result={'status':'A05_STATIC_EVIDENCE_CHECK_PASS','checks':checks,'count':len(checks),'scientific_scope':'Static lineage/port identity only; no full-LP or real-world supply feasibility assertion','reused_history_not_rerun':True,'solver_calls':0,'AutoDL_operations':0,'G6_05':'PAUSED_BY_USER'}
    (e/'A05_VALIDATION_RECEIPT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'checks':len(checks)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--repo',type=Path,required=True);a=p.parse_args();verify(a.folder,a.repo)
