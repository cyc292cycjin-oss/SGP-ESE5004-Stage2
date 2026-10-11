"""Independent disk-readback acceptance; does not import the derivation program.

Exact arithmetic uses actual immutable allocation and frozen NetCDF Load values.
No optimization, LP construction, or whole-CSC read occurs here.
"""
from __future__ import annotations
import argparse, hashlib, json, math, struct, subprocess
from pathlib import Path
from fractions import Fraction
import numpy as np
import netCDF4

F=Fraction
PARENT='53c2b28632cb577136d48ebb843823967f0b1c25'
AUDIT=Path('research/05_baseline_evolution/20261011')
LEDGER_SHA='65ba124368e93ea9ba08e184eaee25fc2e4f81946a310db06d3f8c6888e51117'
OPTION_SHA='5c4d913760b3de0d73c5433e72757d8bd11a3c5efce69aadd38858ece5ec7864'

def require(ok,msg):
    if not ok: raise ValueError('STATIC_REJECTED: '+msg)

def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,j):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(j,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def ratio(x):return {'exact':str(x),'approx':float(x)}
def bit(v):return struct.pack('>d',float(v))
def array_digest(a):return hashlib.sha256(np.asarray(a,dtype='<f8').tobytes(order='C')).hexdigest()

def differences(a,b,path=()):
    """All fields, including types, list order and double bit patterns."""
    if type(a) is not type(b):return [(path,a,b)]
    if isinstance(a,dict):
        require(a.keys()==b.keys(),'dictionary membership differs '+str(path))
        return [r for k in a for r in differences(a[k],b[k],path+(k,))]
    if isinstance(a,list):
        require(len(a)==len(b),'list length '+str(path))
        return [r for i,(x,y) in enumerate(zip(a,b)) for r in differences(x,y,path+(i,))]
    same=bit(a)==bit(b) if isinstance(a,float) else a==b
    return [] if same else [(path,a,b)]

def approved_changes(option):
    result={}
    for g in option['groups']:
        for a in g['account_differences']:
            if a['before_hex']!=a['after_hex']:
                require(a['asset'] not in result,'duplicate approval')
                result[a['asset']]=a
    require(len(result)==180,'approval does not contain 180 changes')
    require(all(x['commodity']!='Animal waste' for x in result.values()),'Animal waste whitelist')
    return result

def validate_diff(old_recipe,new_recipe,old_accounts,new_accounts,changes):
    expected_recipe={}
    for asset,c in changes.items():
        for field in ('e_nom','e_initial'):
            expected_recipe[('components','Store:'+asset,'params',field)]=(c['before_hex'],c['after_hex'])
        expected_recipe[('biomass_obligation_routes',asset,'annual_cap_mwh')]=(c['before_hex'],c['after_hex'])
    rd=differences(old_recipe,new_recipe)
    require({p for p,_,_ in rd}==set(expected_recipe),'non-whitelist recipe difference or unsynced Q')
    for p,a,b in rd:require((float(a).hex(),float(b).hex())==expected_recipe[p],'unapproved recipe delta')
    require(len(old_accounts)==len(new_accounts)==807,'external account count')
    require(len({x['FixedAccountID'] for x in new_accounts})==807,'duplicate external ID')
    expected_external={}
    for i,a in enumerate(old_accounts):
        if a['FixedAccountID'] in changes:
            c=changes[a['FixedAccountID']];expected_external[(i,'QuantityMWh')]=(c['before_hex'],c['after_hex'])
    ed=differences(old_accounts,new_accounts)
    require({p for p,_,_ in ed}==set(expected_external),'non-whitelist external difference or unsynced Q')
    for p,a,b in ed:require((float(a).hex(),float(b).hex())==expected_external[p],'unapproved external delta')
    return [{'file':name,'path':list(p),'before_hex':float(a).hex(),'after_hex':float(b).hex()}
            for name,ds in [('carrier_fragment.json',rd),('external_pending_fixed_accounts.json',ed)] for p,a,b in ds]

def validate_manifest(repo,root,out):
    manifest=read(out/'EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json')
    require(manifest['parent_git_sha']==PARENT,'parent commit')
    for key,r in manifest['inputs'].items():
        if r['scope']=='frozen_source':
            p=root/r['path'];require(digest(p)==r['sha256'],'immutable source hash '+key)
        else:
            blob=subprocess.check_output(['git','show',f"{r['commit']}:{r['path']}"],cwd=repo)
            require(hashlib.sha256(blob).hexdigest()==r['sha256'],'Git blob '+key)
            if r['scope']=='git_science': require(digest(repo/r['path'])==r['sha256'],'science code modified '+key)
    for name,r in manifest['files'].items():require(digest(out/name)==r['sha256'] and (out/name).stat().st_size==r['bytes'],'derived file hash '+name)
    return manifest

def verify(repo,root,out,evidence):
    require(not evidence.exists(),'acceptance evidence already exists')
    manifest=validate_manifest(repo,root,out)
    lp=repo/AUDIT/'evidence/closure_repair/ALL_385_GROUPS_CLOSURE_LEDGER.json'
    op=repo/AUDIT/'evidence/closure_repair/OPTION_A_SIMULATION.json'
    require(digest(lp)==LEDGER_SHA and digest(op)==OPTION_SHA,'approved input identity')
    ledger=read(lp)['groups'];option=read(op);approved=approved_changes(option)
    old_recipe=read(root/'production_assets/carrier_fragment.json');new_recipe=read(out/'carrier_fragment.json')
    old_accounts=read(root/'production_assets/external_pending_fixed_accounts.json');new_accounts=read(out/'external_pending_fixed_accounts.json')
    diffs=validate_diff(old_recipe,new_recipe,old_accounts,new_accounts,approved)
    old_by={a['FixedAccountID']:a for a in old_accounts};new_by={a['FixedAccountID']:a for a in new_accounts}
    refs=read(out/'LOADS_AND_WEIGHTS_REFERENCE.json');ref_by={a['LoadID']:a for a in refs['loads']}
    all_group_checks=[];all_account_checks=[];load_checks=[];animal=[]
    allocation=read(root/'actual_allocation/allocation_manifest.json')
    ar={r['InputID']:r for r in allocation['records']}
    with np.load(root/'actual_allocation/allocations.npz',allow_pickle=False) as z, netCDF4.Dataset(root/'complete_network/research_fullsc_2050_assembly_v1_unsolved.nc','r') as n:
        n.set_auto_mask(False)
        names=list(n['loads_t_p_set_i'][:]);static_names=list(n['loads_i'][:]);store_names=list(n['stores_i'][:])
        load_index={v:i for i,v in enumerate(names)};store_index={v:i for i,v in enumerate(store_names)}
        require(len(names)==len(set(names))==1737 and set(names)==set(static_names)==set(ref_by),'all Load identity')
        weights=z['weights'];require(weights.shape==(2920,) and np.all(weights==3.0),'weights scope')
        require(array_digest(weights)==refs['weights_sha256'],'weight fingerprint')
        for kind in ['stores','generators','objective']:
            require(np.asarray(n['snapshots_'+kind][:],dtype='<f8').tobytes()==np.asarray(weights,dtype='<f8').tobytes(),'NC weights '+kind)
        # All 1737 time series checked against their authoritative source, one allocation block at a time.
        for rec in allocation['records']:
            a=z[rec['ArrayKey']]
            require(array_digest(a)==rec['ArraySHA256'],'array identity '+rec['ArrayKey'])
            for j,node in enumerate(rec['Nodes']):
                name=rec['InputID']+'@'+node
                if not np.any(a[:,j]):
                    require(name not in load_index and name not in ref_by,'preexisting zero allocation unexpectedly gained Load')
                    require({'LoadID':name,'binary64_sha256':array_digest(a[:,j])} in refs['preexisting_zero_allocation_columns_without_Load'],'zero allocation reference')
                    continue
                v=np.asarray(n['loads_t_p_set'][:,load_index[name]],dtype='<f8')
                require(v.tobytes()==np.asarray(a[:,j],dtype='<f8').tobytes(),'Load source/NC bit mismatch '+name)
                require(array_digest(v)==ref_by[name]['binary64_sha256'],'Load immutable reference '+name)
                require((ref_by[name]['ArrayKey'],ref_by[name]['column'],ref_by[name]['node'])==(rec['ArrayKey'],j,node),'Load reference mapping')
                load_checks.append({'load':name,'binary64_sha256':array_digest(v),'status':'UNCHANGED_IMMUTABLE_REFERENCE'})
        for g in ledger:
            d=np.asarray(n['loads_t_p_set'][:,load_index[g['load']]],dtype=np.float64)
            require(all(float(v).hex()==g['flat_load_mw_hex'] for v in d),'flat Load identity')
            # Independent exact cumulative integration; every stored prefix, not float cumsum.
            demand_prefix=[];cum=F(0)
            for w,v in zip(weights,d):
                require(math.isfinite(float(v)) and v>=0,'nonnegative finite demand')
                cum+=F(float(w))*F(float(v));demand_prefix.append(cum)
            D=cum;Qold=sum((F(old_by[a['asset']]['QuantityMWh']) for a in g['accounts']),F(0))
            Qnew=sum((F(new_by[a['asset']]['QuantityMWh']) for a in g['accounts']),F(0))
            require(D==F(g['annual_D_mwh']['exact']) and Qold==F(g['Q_sum_mwh']['exact']),'old exact binding')
            require(D<=Qnew and all(p<=Qnew for p in demand_prefix),'annual or prefix closure')
            selected=min(g['accounts'],key=lambda a:(-F(old_by[a['asset']]['QuantityMWh']),a['asset']))['asset']
            changed=[a['asset'] for a in g['accounts'] if bit(old_by[a['asset']]['QuantityMWh'])!=bit(new_by[a['asset']]['QuantityMWh'])]
            require(changed==[selected] if D>Qold else not changed,'selection/unchanged rule')
            if changed:
                qprev=math.nextafter(float(new_by[selected]['QuantityMWh']),-math.inf)
                require(Qnew-F(new_by[selected]['QuantityMWh'])+F(qprev)<D,'previous double suffices: not minimal')
            max_share=F(0)
            for a in g['accounts']:
                asset=a['asset'];old=old_by[asset];new=new_by[asset];q=F(new['QuantityMWh']);qo=F(old['QuantityMWh'])
                c=new_recipe['components']['Store:'+asset];route=new_recipe['biomass_obligation_routes'][asset]
                require(q>0 and math.isfinite(new['QuantityMWh']),'positive Q')
                require(all(bit(v)==bit(new['QuantityMWh']) for v in [c['params']['e_nom'],c['params']['e_initial'],route['annual_cap_mwh']]),'four synchronized fields')
                # Link original recipe to actual frozen assembled Store constants without assembling a new network.
                si=store_index[asset]
                require(bit(n['stores_e_nom'][si])==bit(n['stores_e_initial'][si])==bit(old['QuantityMWh']),'old NC Store identity')
                require(not bool(n['stores_e_cyclic'][si]) and not bool(n['stores_e_nom_extendable'][si]) and float(n['stores_e_min_pu'][si])==0,'old Store boundary')
                require(c['params']['e_cyclic'] is False and c['params']['p_min_pu']==0,'source Store direction/cycle')
                m=new_recipe['components']['Link:'+new['Meter']]
                require(m['inputs']==[new['ResourceBus']] and m['outputs']==[g['bus']] and m['params']['efficiency']==1 and m['params']['p_min_pu']==0,'meter port/direction/efficiency')
                require(new['UnitPriceEUR2020PerMWh'] is None and new['PhysicalCO2_tPerMWh'] is None,'NULL semantics')
                share=q/Qnew-qo/Qold;max_share=max(max_share,abs(share))
                # For this isolated, unchanged, lossless exclusive subsystem: p_i(t)=q_i*d_t/Qnew.
                # e_i(k)=q_i*(1-prefix_D(k)/Qnew). All prefix inequalities above imply bounds.
                ending=q*(1-D/Qnew)
                require(0<=ending<=q,'analytic inventory bounds')
                if new['Commodity']=='Animal waste':
                    require(bit(float(q))==bit(float(qo)),'Animal waste changed');animal.append(asset)
                all_account_checks.append({'asset':asset,'bus':g['bus'],'before_hex':float(qo).hex(),'after_hex':float(q).hex(),
                    'delta_mwh':ratio(q-qo),'share_delta':ratio(share),'source_share_reference':a['source_share_binary64_rational'],
                    'final_inventory_local_analytic_mwh':ratio(ending),'minimum_prefix_inventory_mwh':ratio(ending),
                    'prefixes_covered':2920,'proof':'e_i(k)=q_i*(1-prefix_D(k)/Qnew), 0<=prefix_D(k)<=D<=Qnew; conditional local subsystem only',
                    'fields_synchronized':True,'ownership_and_other_fields':'UNCHANGED_BY_FULL_STRUCTURAL_DIFF'})
            all_group_checks.append({'bus':g['bus'],'load':g['load'],'D_mwh':ratio(D),'Q_old_mwh':ratio(Qold),'Q_new_mwh':ratio(Qnew),
                'old_D_minus_Q':ratio(D-Qold),'new_Q_minus_D':ratio(Qnew-D),'D_le_Q_new':True,'D_eq_Q_new':D==Qnew,
                'changed_assets':changed,'max_abs_share_delta':ratio(max_share),'prefix_demand_checks':len(demand_prefix),
                'max_prefix_D':ratio(max(demand_prefix)),'local_prefix_feasibility':'EXACT_ANALYTIC_CONDITIONAL_NOT_FULL_LP'})
    require(len(animal)==5,'Animal waste scope')
    require(len(all_group_checks)==385 and len(all_account_checks)==807 and len(diffs)==720,'scope counts')
    # Compare all realized group totals and every changed coefficient to the approved simulation.
    ag={g['bus']:g for g in option['groups']}
    for g in all_group_checks:
        require(F(g['Q_new_mwh']['exact'])==F(ag[g['bus']]['Q_sum_after_mwh']['exact']),'approved group total')
        require(F(g['max_abs_share_delta']['exact'])==abs(F(ag[g['bus']]['max_absolute_share_change']['exact'])),'approved share change')
    changed_count=sum(a['before_hex']!=a['after_hex'] for a in all_account_checks)
    require(changed_count==180,'actual changed count')
    # Read writer's advertised change list, rather than trusting it as acceptance authority.
    advertised=read(out/'EXACT_SOURCE_CLOSURE_A_CHANGESET.json')
    require({a['asset']:(a['before_hex'],a['after_hex']) for a in advertised['changes']}=={k:(v['before_hex'],v['after_hex']) for k,v in approved.items()},'advertised change list')
    evidence.mkdir(parents=True,exist_ok=False)
    dump(evidence/'EXACT_SOURCE_CLOSURE_A_ALL_GROUPS_CHECK.json',{'status':'PASS','groups':all_group_checks,'accounts':all_account_checks,'animal_waste_unchanged':animal})
    dump(evidence/'EXACT_SOURCE_CLOSURE_A_WHITELIST_DIFF.json',{'status':'PASS','scientific_Q_changes':180,'synchronized_leaf_changes':720,
        'new_assets':0,'removed_assets':0,'non_whitelist_differences':0,'full_recipe_fields_compared':True,'differences':diffs})
    dump(evidence/'LOAD_WEIGHT_READBACK.json',{'status':'PASS','count':len(load_checks),'snapshots':2920,'weights_sha256':array_digest(weights),
        'all_three_NC_weight_arrays_match':True,'source_and_frozen_NC_bitwise_match':True,'new_version':'IMMUTABLE_REFERENCES_NO_LOAD_COPY_OR_REGENERATION','loads':load_checks})
    witness=next(g for g in all_group_checks if g['bus']=='ID:2050:Industry:IndustryFinalEnergy:biomass@ID_Java-Bali1 2 :: final obligation')
    summary={'status':'SCHEME_A_STATIC_ACCEPTED','layers':{'source_exact':'PASS','derived_component_readback':'PASS','whitelist':'PASS'},
        'version_manifest_sha256':digest(out/'EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json'),'verifier_sha256':digest(Path(__file__)),
        'groups_D_le_Q':385,'groups_D_eq_Q':sum(g['D_eq_Q_new'] for g in all_group_checks),'changed_accounts':180,'unchanged_accounts':627,
        'loads_unchanged':1737,'animal_waste_unchanged':5,'sum_Q_increase_mwh':ratio(sum((F(a['delta_mwh']['exact']) for a in all_account_checks),F(0))),
        'max_account_increase_mwh':ratio(max(F(a['delta_mwh']['exact']) for a in all_account_checks)),
        'sum_remaining_inventory_mwh':ratio(sum((F(g['new_Q_minus_D']['exact']) for g in all_group_checks),F(0))),
        'max_remaining_inventory_mwh':ratio(max(F(g['new_Q_minus_D']['exact']) for g in all_group_checks)),
        'max_share_delta':ratio(max(abs(F(a['share_delta']['exact'])) for a in all_account_checks)),
        'witness':witness,'scalar_changes_by_field':{'Store.e_nom':180,'Store.e_initial':180,'route.annual_cap_mwh':180,'external.QuantityMWh':180},
        'scope_status':{'all_recipe_cost_parameters':'UNCHANGED','recipe_policy_and_carbon_fields':'UNCHANGED','technical_efficiencies_and_ports':'UNCHANGED','all_non_Q_recipe_values':'UNCHANGED','allocation_and_all_Loads':'UNCHANGED',
            'new_full_LP_objective':'NOT_CHECKED_NOT_CONSTRUCTED','new_LP_scaled_bounds':'NOT_CHECKED_NOT_CONSTRUCTED','global_feasibility':'NOT_PROVEN'},
        'solver_calls':0,'full_LP_builds':0,'CSC_reads':0,'G6_05':'PAUSED_BY_USER','old_certificate':'VALID_FOR_OLD_FROZEN_LP_RETAINED'}
    dump(evidence/'STATIC_ACCEPTANCE_RECEIPT.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['witness','scope_status']},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ['repo','frozen-source','version','evidence']:p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();verify(a.repo.resolve(),a.frozen_source.resolve(),a.version.resolve(),a.evidence.resolve())
