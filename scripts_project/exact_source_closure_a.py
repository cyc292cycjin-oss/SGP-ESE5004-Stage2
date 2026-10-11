"""Approved, bounded source-recipe derivation. No model construction or solver imports.

This is an explicit opt-in source materializer, not a production model launcher.
Original data remain read-only. Only the four approved Q fields may change.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from fractions import Fraction as F
from pathlib import Path
import subprocess
import numpy as np

RULE = 'EXACT_SOURCE_CLOSURE_A_MAX_ACCOUNT_V1'
VERSION = RULE + '_20261011'
PARENT = '53c2b28632cb577136d48ebb843823967f0b1c25'
SCIENCE = 'b9be7d0ab788a4151346c098d2e657c7e94a22da'
AUDIT = Path('research/05_baseline_evolution/20261011')
DERIVED = Path('research_inputs/derived/exact_source_closure_a_max_account_v1_20261011')
APPROVED = {
 'ledger': ('evidence/closure_repair/ALL_385_GROUPS_CLOSURE_LEDGER.json','65ba124368e93ea9ba08e184eaee25fc2e4f81946a310db06d3f8c6888e51117'),
 'option_a': ('evidence/closure_repair/OPTION_A_SIMULATION.json','5c4d913760b3de0d73c5433e72757d8bd11a3c5efce69aadd38858ece5ec7864'),
 'summary': ('evidence/closure_repair/CLOSURE_REPAIR_SUMMARY.json','f700423d41e65e376f2460b1bf46ade61efb239cce988de65b4e34a08837d740'),
}
SOURCE = {
 'recipe': ('production_assets/carrier_fragment.json','01f64727d3baf956496a01099b985b085caa1966ef80d342dd7ed973004bd7a3'),
 'accounts': ('production_assets/external_pending_fixed_accounts.json','193741d46f4a126c680b7ac7251f527a1d789c397d5e2cd61a9ffea7408b0521'),
 'allocation_manifest': ('actual_allocation/allocation_manifest.json','4e2cc08c6671635ccd1cc472ccabf06bad630650cd948678c042205607703d06'),
 'allocation': ('actual_allocation/allocations.npz','931c24aac84be29eda6b2a1906a8e85ca0f3876b90c26cdb3b40e84ad8d3b2b9'),
 'network': ('complete_network/research_fullsc_2050_assembly_v1_unsolved.nc','238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d'),
 'demand_destinations': ('production_assets/demand_destinations.json','1b68de43ba71a1f80197140d257a490dd5651841b11a734468e808b99340f1bb'),
 'carbon_map': ('production_assets/carbon_component_map.json','719c0dc42ab67894ba2ae9ed9b047b7572139d8d202b2cfd9af68879956f21d5'),
}

def need(ok, message):
    if not ok: raise ValueError('STOP: ' + message)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def write(path, data, *, legacy_infinity=False):
    # The frozen unbound recipe uses Python JSON Infinity for unbounded capacity.
    # Preserve that existing serialization; never replace a physical bound.
    payload=json.dumps(data,ensure_ascii=False,indent=2,allow_nan=legacy_infinity)+'\n'
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:
        f.write(payload)

def rat(x): return {'exact':f'{x.numerator}/{x.denominator}','approx':float(x)}

def bits_sha(a): return hashlib.sha256(np.asarray(a,dtype='<f8').tobytes(order='C')).hexdigest()

def ceil_binary64(y):
    """Nearest conversion followed by at most one successor, not iterative repair."""
    q=float(y)
    need(math.isfinite(q),'nonfinite target')
    if F(q)<y: q=math.nextafter(q, math.inf)
    need(math.isfinite(q) and F(math.nextafter(q,-math.inf))<y<=F(q),'ceil minimality')
    return q

def bound_inputs(repo, root):
    records={}
    for key,(rel,expected) in SOURCE.items():
        path=root/rel
        need(sha(path)==expected,'source SHA mismatch: '+key)
        records[key]={'scope':'frozen_source','path':rel,'sha256':expected,'bytes':path.stat().st_size}
    more=['EXACT_SOURCE_CLOSURE_REPAIR_OPTIONS.md','PROPOSED_MINIMAL_REPAIR_SPEC.md',
          'A03_EXACT_ANNUAL_CLOSURE_PROOF.md','BASELINE_EVOLUTION_LEDGER.md',
          'evidence/closure_repair/SOURCE_BINDINGS.json']
    for rel in [r for r,_ in APPROVED.values()]+more:
        path=AUDIT/rel
        blob=subprocess.check_output(['git','show',f'{PARENT}:{path.as_posix()}'],cwd=repo)
        expected=hashlib.sha256(blob).hexdigest()
        # The ledger will subsequently be updated; its approved parent blob stays bound.
        need(sha(repo/path)==expected,'approved parent file changed: '+rel)
        if rel in [x[0] for x in APPROVED.values()]:
            need(expected==next(s for r,s in APPROVED.values() if r==rel),'approval hash differs')
        records['approval:'+rel]={'scope':'git_parent','path':path.as_posix(),'commit':PARENT,'sha256':expected,'bytes':len(blob)}
    bindings=load(repo/AUDIT/'evidence/closure_repair/SOURCE_BINDINGS.json')
    for rec in bindings['sources']:
        blob=subprocess.check_output(['git','show',f"{SCIENCE}:{rec['path']}"],cwd=repo)
        need(hashlib.sha256(blob).hexdigest()==rec['sha256']==sha(repo/rec['path']),'science source binding: '+rec['path'])
        records['science:'+rec['path']]={'scope':'git_science','path':rec['path'],'commit':SCIENCE,'sha256':rec['sha256'],'bytes':len(blob)}
    return records

def derive(repo, root, out):
    need(not out.exists(),'output exists; refuse overwrite or repeat derivation')
    records=bound_inputs(repo,root)
    ledger=load(repo/AUDIT/APPROVED['ledger'][0])['groups']
    approved={g['bus']:g for g in load(repo/AUDIT/APPROVED['option_a'][0])['groups']}
    old_recipe=load(root/SOURCE['recipe'][0]);old_accounts=load(root/SOURCE['accounts'][0])
    recipe=copy.deepcopy(old_recipe);accounts=copy.deepcopy(old_accounts)
    by_id={a['FixedAccountID']:a for a in accounts}
    routes=recipe['biomass_obligation_routes'];components=recipe['components']
    allocation=load(root/SOURCE['allocation_manifest'][0])
    ar={r['InputID']:r for r in allocation['records']}
    need(len(ledger)==385 and len(by_id)==len(accounts)==807,'scope count')
    need(recipe['artifact_role']=='UNBOUND_CARRIER_RECIPE','recipe role')
    need(not any(c['type']=='Load' for c in components.values()),'unbound recipe contains Load')
    changes=[];group_checks=[];load_refs=[];zero_refs=[]
    with np.load(root/SOURCE['allocation'][0],allow_pickle=False) as z:
        weights=np.asarray(z['weights'],dtype=np.float64)
        need(weights.shape==(2920,) and all(float(w).hex()==float(3).hex() for w in weights),'weights changed')
        # Fingerprint every approved allocation Load, including non-biomass; no copy of time series.
        for r in allocation['records']:
            a=z[r['ArrayKey']]
            need(a.shape==(2920,len(r['Nodes'])),'allocation shape')
            need(bits_sha(a)==r['ArraySHA256'],'allocation array hash')
            for j,node in enumerate(r['Nodes']):
                if not np.any(a[:,j]):
                    zero_refs.append({'LoadID':r['InputID']+'@'+node,'binary64_sha256':bits_sha(a[:,j])})
                    continue  # Inherit bind_loads: exact zero allocation creates no Load.
                load_refs.append({'LoadID':r['InputID']+'@'+node,'InputID':r['InputID'],
                    'ArrayKey':r['ArrayKey'],'column':j,'node':node,'binary64_sha256':bits_sha(a[:,j])})
        need(len(load_refs)==len({r['LoadID'] for r in load_refs})==1737,'Load identity scope')
        for g in ledger:
            r=ar[g['source_account']];node=g['load'][len(g['source_account'])+1:]
            d=z[r['ArrayKey']][:,r['Nodes'].index(node)]
            need(all(float(v).hex()==g['flat_load_mw_hex'] for v in d),'Load changed: '+g['load'])
            D=sum((F(float(w))*F(float(v)) for w,v in zip(weights,d)),F(0))
            need(D==F(g['annual_D_mwh']['exact']),'D binding')
            q={a['asset']:float.fromhex(a['Q_mwh_hex']) for a in g['accounts']}
            for a in g['accounts']:
                name=a['asset'];c=components['Store:'+name];e=by_id[name];route=routes[name]
                need(all(float(v).hex()==a['Q_mwh_hex'] for v in [c['params']['e_nom'],c['params']['e_initial'],route['annual_cap_mwh'],e['QuantityMWh']]),'Q source mismatch '+name)
                need(e['SourceRow']==a['source_row']==route['source_row']==c['source'],'SourceRow')
                need(e['Commodity']==a['commodity']==route['commodity'] and e['SourceAccountID']==g['source_account']==route['input_id'],'ownership')
            Q=sum(map(F,q.values()),F(0));need(Q==F(g['Q_sum_mwh']['exact']),'Q binding')
            selected=min(q,key=lambda k:(-F(q[k]),k))
            expected={a['asset']:a for a in approved[g['bus']]['account_differences'] if a['before_hex']!=a['after_hex']}
            if D>Q:
                before=q[selected];after=ceil_binary64(F(before)+D-Q)
                need(set(expected)=={selected} and expected[selected]['before_hex']==before.hex() and expected[selected]['after_hex']==after.hex(),'approved delta mismatch')
                need(F(after)-F(before)==F(expected[selected]['delta_mwh']['exact']),'approved exact delta')
                components['Store:'+selected]['params']['e_nom']=after
                components['Store:'+selected]['params']['e_initial']=after
                routes[selected]['annual_cap_mwh']=after;by_id[selected]['QuantityMWh']=after
                q[selected]=after
                changes.append({'asset':selected,'bus':g['bus'],'before_hex':before.hex(),'after_hex':after.hex(),
                    'delta_mwh':rat(F(after)-F(before)),'commodity':by_id[selected]['Commodity'],
                    'SourceRow':by_id[selected]['SourceRow'],'InputID':by_id[selected]['SourceAccountID'],
                    'synchronized_fields':['Store.e_nom','Store.e_initial','route.annual_cap_mwh','external_pending_fixed_accounts.QuantityMWh'],
                    'previous_binary64_insufficient':Q-F(before)+F(math.nextafter(after,-math.inf))<D})
            else: need(not expected,'unexpected approved change')
            Qnew=sum(map(F,q.values()),F(0));need(D<=Qnew,'closure failed')
            need(Qnew==F(approved[g['bus']]['Q_sum_after_mwh']['exact']),'approved total differs')
            group_checks.append({'bus':g['bus'],'D':rat(D),'Q_old':rat(Q),'Q_new':rat(Qnew),'Q_new_minus_D':rat(Qnew-D),'D_le_Q_new':True,'D_eq_Q_new':D==Qnew})
    need(len(changes)==180,'change count')
    need(not any(c['commodity']=='Animal waste' for c in changes),'Animal waste change')
    # All fail-closed scientific calculations finish before creating the new version.
    out.mkdir(parents=True,exist_ok=False)
    write(out/'carrier_fragment.json',recipe,legacy_infinity=True)
    write(out/'external_pending_fixed_accounts.json',accounts)
    write(out/'LOADS_AND_WEIGHTS_REFERENCE.json',{'schema':'immutable-allocation-reference-v1','loads':load_refs,
        'weights_sha256':bits_sha(weights),'snapshots':2920,'hours_exact':'8760/1',
        'allocation_reference':records['allocation'],'network_reference':records['network'],
        'load_write_operations':0,'weight_write_operations':0,'preexisting_zero_allocation_columns_without_Load':zero_refs})
    write(out/'EXACT_SOURCE_CLOSURE_A_CHANGESET.json',{'rule':RULE,'version':VERSION,'changed_accounts':180,'unchanged_accounts':627,
        'sum_delta_mwh':rat(sum((F(c['delta_mwh']['exact']) for c in changes),F(0))),'changes':changes})
    write(out/'SOURCE_DERIVATION_CHECK.json',{'status':'GENERATED_PENDING_INDEPENDENT_ACCEPTANCE','groups':group_checks,'solver_calls':0,'model_builds':0})
    files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir())}
    write(out/'EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json',{'schema':'controlled-source-version-v1','version_id':VERSION,
        'repair_rule':RULE,'approval':'USER_AND_CHATGPT_APPROVED_SCHEME_A_CONTROLLED_IMPLEMENTATION',
        'parent_git_sha':PARENT,'science_parent_git_sha':SCIENCE,'audit_pr':3,
        'parent_recipe_sha256':SOURCE['recipe'][1],'inputs':records,'files':files,
        'generator_sha256':sha(Path(__file__)),'source_root_hint':str(root),
        'activation':'EXPLICIT_SOURCE_DERIVATIVE_ONLY_NOT_ASSEMBLED_OR_SOLVED',
        'future_assembly':'Use new carrier_fragment and external account ledger together; retain immutable allocation. Old asset manifest is not a manifest for this new version.',
        'old_network_and_lp':'RETAINED_UNMODIFIED_NOT_REBUILT','G6_05':'PAUSED_BY_USER'})
    # Reconfirm no source changed while deriving (read-only, no full matrix access).
    for key,(rel,expected) in SOURCE.items(): need(sha(root/rel)==expected,'source changed during derivation: '+key)
    print(json.dumps({'version':VERSION,'output':str(out),'changes':len(changes),'groups':len(group_checks),'manifest_sha256':sha(out/'EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json')}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--frozen-source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();derive(a.repo.resolve(),a.frozen_source.resolve(),a.out.resolve())
