"""Design-only exact arithmetic on small, previously audited JSON constants.

Reads no CSC, NetCDF, solution vector or solver. Never writes model inputs.
Run: python verification/analyze_exact_closure_options.py --output NEW_DIRECTORY
Only a new, empty output directory is accepted. Ratios are exact; decimal fields
are display aids. A is minimal in the explicitly selected one-account class,
not a global minimum across arbitrary changes to several accounts.
"""
from collections import Counter, defaultdict
from fractions import Fraction as F
from pathlib import Path
import argparse, hashlib, json, math

ROOT = Path(__file__).resolve().parents[1]
CERT_BUS = 'ID:2050:Industry:IndustryFinalEnergy:biomass@ID_Java-Bali1 2 :: final obligation'
H = 8760
Z = F(0)

def exact(v): return F(v)
def rat(v): return str(v.numerator) + '/' + str(v.denominator)
def num(v): return {'exact': rat(v), 'approx': float(v)}
def sha(b): return hashlib.sha256(b).hexdigest()
def ceil_float(q):
    x = float(q)
    if F(x) < q: x = math.nextafter(x, math.inf)
    assert math.isfinite(x) and F(x) >= q and F(math.nextafter(x,-math.inf)) < q
    return x
def floor_float(q):
    x = float(q)
    if F(x) > q: x = math.nextafter(x,-math.inf)
    assert math.isfinite(x) and F(x) <= q and F(math.nextafter(x,math.inf)) > q
    return x
def round_even(q):
    n, r = divmod(q.numerator,q.denominator)
    return n + int(2*r > q.denominator or (2*r == q.denominator and n%2==1))
def exact_binary(v):
    x = float(v)
    assert math.isfinite(x) and F(x)==v
    return x
def write(path,obj):
    # Compact one record per line keeps the full 385-group evidence lightweight.
    with path.open('x',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,separators=(',',':')); f.write('\n')

def run(out):
    out.mkdir(parents=True,exist_ok=False)
    inputs = {}
    def read(rel, expected=None):
        p=ROOT/rel; b=p.read_bytes()
        if expected: assert sha(b)==expected
        inputs[rel]={'bytes':len(b),'sha256':sha(b)}
        return json.loads(b)
    groups=read('evidence/A03_GROUP_CROSSWALK.json','f375c37a791e3e346c7f130845ab3e099d01cc1ba65636420960b31aedd5a85b')
    accounts=read('evidence/A03_ACCOUNT_CROSSWALK.json','1fac8b56bf52239f12ae7bdfc55f82869d33f8716a0f1ad728f01c3cbfe8eb36')
    topology=read('evidence/A03_OBLIGATION_AUDIT_SUMMARY.json','a05a80100ad1ef8fded270ab46677867986611610b21716a8fa9e80708fe53ad')
    source=read('evidence/closure_repair/SOURCE_BINDINGS.json')
    certificate=read('evidence/a03_full_lp/EXACT_CERTIFICATE.json','85b895aca9da35032517fa3a99d2b22e069310cb87d66747fbec26f33621504b')
    assert not topology['topology_issues'] and topology['all_final_loads_flat'] and topology['total_weight_hours']==H
    assert certificate['status']=='FULL_LP_EXACT_INFEASIBILITY_CERTIFIED'
    group_accounts=defaultdict(list)
    for a in accounts:
        assert len(a['FinalBuses'])==1
        group_accounts[a['FinalBuses'][0]].append(a)
    src={r['InputID']:r for r in source['source_accounts']}
    ledger=[]; schemes={k:[] for k in 'ABC'}
    metrics={k:[] for k in 'ABC'}; cases=Counter(); tests=Counter()
    for g in sorted(groups,key=lambda g:g['bus']):
        bus=g['bus']; aa=sorted(group_accounts[bus],key=lambda a:a['asset'])
        assert len(aa)==g['account_count']
        q=[F(a['Q_mwh']) for a in aa]; load=F(g['flat_load_mw']); D=H*load; Q=sum(q,Z); delta=D-Q
        assert all(x>0 for x in q) and load>0
        assert delta==F(g['exact_difference_numerator'],g['exact_difference_denominator'])
        s=src[g['source_account']]
        raw=[r for r in source['commodity_rows'] if r['Country']==s['Country'] and r['Account']==s['Account']]
        raw_map={r['Commodity']:r for r in raw}; assert len(raw_map)==len(raw)==len(aa)
        raw_q=[F(float(raw_map[a['commodity']]['MWh'])) for a in aa]
        raw_sum=sum(raw_q,Z); raw_share=[v/raw_sum for v in raw_q]
        current_share=[v/Q for v in q]
        old_budget=[min(F('0.001')+F('1e-7')*v,F('1e-6')*v) for v in q]
        q_ulps=[F(math.ulp(float(v))) for v in q]; min_ulp=min(q_ulps)
        category=('FULL_LP_CERTIFIED_ONE_GROUP' if bus==CERT_BUS else
                  'POSITIVE_GAP_SIMILAR_TOPOLOGY_NOT_INDIVIDUALLY_CERTIFIED' if delta>0 else
                  'NO_POSITIVE_ANNUAL_GAP_NOT_A_GLOBAL_FEASIBILITY_PROOF')
        cases[category]+=1
        if bus==CERT_BUS: assert delta==F(513,34359738368)
        record={'bus':bus,'load':g['load'],'source_account':g['source_account'],
          'annual_D_mwh':num(D),'Q_sum_mwh':num(Q),'D_minus_Q_mwh':num(delta),
          'relative_gap_to_D':num(delta/D),'flat_load_mw_hex':float(load).hex(),
          'ulp_D_rounded_mwh':math.ulp(float(D)),'ulp_load_mw':math.ulp(float(load)),
          'gap_in_annual_D_ulps':num(delta/F(math.ulp(float(D)))),
          'gap_in_8760_load_ulps':num(delta/(H*F(math.ulp(float(load))))),
          'minimum_account_ulp_mwh':num(min_ulp),
          'D_on_unchanged_account_binade_lattice':(D/min_ulp).denominator==1,
          'classification':category,'complete_LP_certificate_available':bus==CERT_BUS,
          'topology_evidence':'A03_OBLIGATION_AUDIT_SUMMARY.json: exclusive Store/resource Bus/meter/final Bus; no time override, loss or terminal e_set; same 3h weights',
          'scope_limit':'Other LP mechanisms and global feasibility are not reverified; positive-gap groups other than the selected certificate remain conditional.',
          'responsible_code':'build_research_assets.py:226,237-248; allocation:49-78; bind_loads:49-67',
          'accounts':[]}
        for a, v, ulp, raw_s in zip(aa,q,q_ulps,raw_share):
            r=raw_map[a['commodity']]
            record['accounts'].append({'asset':a['asset'],'meter':a['Meter'],'commodity':a['commodity'],
              'Q_mwh_hex':float(v).hex(),'Q_mwh_exact':rat(v),'ulp_Q_mwh':num(ulp),
              'source_row':r['RowID'],'source_file':r['SourceFile'],'source_sha256':r['SourceSHA256'],
              'source_share_binary64_rational':rat(raw_s),'frozen_Q_share':rat(v/Q)})
        ledger.append(record)

        # A: keep every Load bit; repair only a positive gap in the largest Q.
        # Stable tie: full asset ID, independently of component enumeration.
        j=min(range(len(q)),key=lambda i:(-q[i],aa[i]['asset']))
        qa=list(q)
        if delta>0:
            qa[j]=F(ceil_float(q[j]+delta))
            assert sum(qa,Z)>=D
            assert sum(qa,Z)-qa[j]+F(math.nextafter(float(qa[j]),-math.inf))<D
            tests['A_minimal_for_selected_one_account']+=1
        # B: preserve every Q bit; uniformly reduce flat Load only if needed.
        lb=F(floor_float(Q/H)) if delta>0 else load
        if delta>0:
            assert H*F(math.nextafter(float(lb),math.inf))>Q
            tests['B_largest_admissible_constant_load']+=1
        # C: common annual authority is the approved node Load integral D.
        # q0=ULP(round64(D)); 8760=1095*2^3. N is a multiple of 1095,
        # making d*=N*q0/8760 exactly binary64; Hamilton allocates N quanta.
        quantum=F(math.ulp(float(D)))
        m=round_even(D/(1095*quantum)); N=1095*m
        C=N*quantum; lc=F(exact_binary(m*quantum/8))
        assert H*lc==C and 0<N<=2**53
        quotas=[N*r for r in raw_share]
        units=[v.numerator//v.denominator for v in quotas]
        leftover=N-sum(units)
        order=sorted(range(len(q)),key=lambda i:(-(quotas[i]-units[i]),aa[i]['asset']))
        assert 0<=leftover<len(q)
        for i in order[:leftover]: units[i]+=1
        qc=[F(exact_binary(v*quantum)) for v in units]
        assert sum(qc,Z)==C and all(v>0 for v in qc)
        tests['C_exact_binary64_common_annual_and_allocation']+=1

        for name, lnew, qnew in [('A',load,qa),('B',lb,q),('C',lc,qc)]:
            Dnew=H*lnew; Qnew=sum(qnew,Z); slack=Qnew-Dnew
            assert slack>=0 and all(v>0 for v in qnew) and lnew>0
            assert Dnew==365*24*lnew # analytic flat annual daily consistency, no model built
            diffs=[v-u for v,u in zip(qnew,q)]
            shares=[v/Qnew for v in qnew]
            shares_delta=[v-u for v,u in zip(shares,current_share)]
            share_source=[v-u for v,u in zip(shares,raw_share)]
            changes=[]
            for a, before, after, change, sdiff, ssrc, ulp in zip(aa,q,qnew,diffs,shares_delta,share_source,q_ulps):
                if change or sdiff:
                    changes.append({'asset':a['asset'],'commodity':a['commodity'],'before_hex':float(before).hex(),
                      'after_hex':float(after).hex(),'delta_mwh':num(change),'delta_in_original_Q_ulp':num(change/ulp),
                      'relative_delta_Q':num(change/before),'share_delta_absolute':num(sdiff),'share_minus_source_absolute':num(ssrc)})
            one={'bus':bus,'status':'SIMULATED_PROPOSED_NOT_APPLIED','load_before_hex':float(load).hex(),
              'load_after_hex':float(lnew).hex(),'annual_D_after_mwh':num(Dnew),'annual_D_delta_mwh':num(Dnew-D),
              'Q_sum_after_mwh':num(Qnew),'Q_sum_delta_mwh':num(Qnew-Q),'sum_abs_account_Q_delta_mwh':num(sum(map(abs,diffs),Z)),
              'remaining_inventory_sum_mwh':num(slack),'D_le_Q_exact':True,'D_eq_Q_exact':slack==0,
              'min_old_V4_account_budget_mwh':num(min(old_budget)),
              'slack_over_min_old_V4_budget':num(slack/min(old_budget)),
              'max_absolute_share_change':num(max(map(abs,shares_delta))),
              'account_differences':changes}
            if name=='A':
                one.update(selected_residual_asset=aa[j]['asset'],rule='minimal upward binary64 adjustment in largest-Q account, only if D>Q; stable asset-ID tie')
            if name=='C':
                one.update(annual_quantum_mwh=rat(quantum),annual_integer_quanta=N,common_scalar_rounding='nearest multiple of 1095 quanta; ties to even',
                           allocation='Hamilton exact source-binary64 shares; stable asset-ID tie',source_share_basis='Fraction(float(source MWh))/sum exact binary64 MWh')
            schemes[name].append(one)
            metrics[name].append({'bus':bus,'delta_D':Dnew-D,'delta_Q':Qnew-Q,'account_deltas':diffs,
              'original_q':q,'slack':slack,'share_changes':shares_delta,'share_source':share_source,
              'd_changed':lnew!=load,'q_changed':sum(a!=b for a,b in zip(q,qnew)),
              'max_slack_budget_ratio':slack/min(old_budget),'max_q_change_budget_ratio':max(abs(v)/b for v,b in zip(diffs,old_budget)),
              'commodities':[a['commodity'] for a in aa],'source_account':g['source_account'],
              'load_ulp_delta':(lnew-load)/F(math.ulp(float(load)))})

    assert len(ledger)==385 and sum(len(g['accounts']) for g in ledger)==807
    assert sum(F(g['D_minus_Q_mwh']['exact'])>0 for g in ledger)==180
    assert cases['FULL_LP_CERTIFIED_ONE_GROUP']==1 and cases['POSITIVE_GAP_SIMILAR_TOPOLOGY_NOT_INDIVIDUALLY_CERTIFIED']==179
    summaries={}
    for name, mm in metrics.items():
        ds=[m['delta_D'] for m in mm]; qs=[m['delta_Q'] for m in mm]; ads=[v for m in mm for v in m['account_deltas']]
        bycommodity=defaultdict(lambda:Z); bysource=defaultdict(lambda:Z)
        for m in mm:
            bysource[m['source_account']]+=m['delta_D']
            for c,v in zip(m['commodities'],m['account_deltas']): bycommodity[c]+=v
        summaries[name]={
          'status':'SIMULATED_PROPOSED_NOT_APPLIED','groups':385,'accounts':807,
          'load_groups_changed':sum(m['d_changed'] for m in mm),'Q_groups_changed':sum(bool(m['delta_Q']) or any(m['account_deltas']) for m in mm),
          'Q_accounts_changed':sum(m['q_changed'] for m in mm),'exact_D_le_Q_groups':385,
          'exact_D_eq_Q_groups':sum(m['slack']==0 for m in mm),
          'annual_D_max_abs_delta_mwh':num(max(map(abs,ds))),'annual_D_sum_abs_delta_mwh':num(sum(map(abs,ds),Z)),
          'annual_D_net_delta_mwh':num(sum(ds,Z)),'Q_group_max_abs_delta_mwh':num(max(map(abs,qs))),
          'Q_group_sum_abs_delta_mwh':num(sum(map(abs,qs),Z)),'Q_net_delta_mwh':num(sum(qs,Z)),
          'Q_account_max_abs_delta_mwh':num(max(map(abs,ads))),'Q_account_sum_abs_delta_mwh':num(sum(map(abs,ads),Z)),
          'max_relative_account_Q_change':num(max(abs(d)/q for m in mm for d,q in zip(m['account_deltas'],m['original_q']))),
          'max_absolute_commodity_share_change':num(max(abs(d) for m in mm for d in m['share_changes'])),
          'max_absolute_commodity_share_minus_raw_source':num(max(abs(d) for m in mm for d in m['share_source'])),
          'remaining_stock_max_mwh':num(max(m['slack'] for m in mm)),
          'remaining_stock_total_mwh':num(sum((m['slack'] for m in mm),Z)),
          'max_slack_over_smallest_group_account_old_budget':num(max(m['max_slack_budget_ratio'] for m in mm)),
          'max_Q_change_over_account_old_budget':num(max(m['max_q_change_budget_ratio'] for m in mm)),
          'max_abs_flat_load_change_in_original_ULPs':num(max(abs(m['load_ulp_delta']) for m in mm)),
          'commodity_net_Q_change_mwh':{k:num(v) for k,v in sorted(bycommodity.items())},
          'source_account_net_D_change_mwh':{k:num(v) for k,v in sorted(bysource.items())},
          'max_D_change_group':max(mm,key=lambda m:abs(m['delta_D']))['bus'],
          'max_account_Q_change_group':max(mm,key=lambda m:max(map(abs,m['account_deltas'])))['bus'],
          'no_zeroed_positive_load_or_Q':True,'flat_daily_annual_identity_365x24_vs2920x3':'EXACT_DERIVATION_ONLY_NO_DAILY_MODEL'}
    summary={'schema':'exact-source-closure-design-v1','status':'PROPOSED_NOT_APPROVED_NOT_APPLIED',
      'counts':dict(cases),'positive_gap_groups':180,'negative_gap_groups':205,'zero_gap_groups':0,
      'exact_annual_D_total_mwh':num(sum((F(g['annual_D_mwh']['exact']) for g in ledger),Z)),
      'exact_Q_total_mwh':num(sum((F(g['Q_sum_mwh']['exact']) for g in ledger),Z)),
      'sum_abs_original_gap_mwh':num(sum((abs(F(g['D_minus_Q_mwh']['exact'])) for g in ledger),Z)),
      'maximum_abs_original_gap_mwh':num(max(abs(F(g['D_minus_Q_mwh']['exact'])) for g in ledger)),
      'maximum_absolute_relative_gap':num(max(abs(F(g['relative_gap_to_D']['exact'])) for g in ledger)),
      'min_Q_mwh':min(a['Q_mwh'] for a in accounts),'max_Q_mwh':max(a['Q_mwh'] for a in accounts),
      'groups_D_not_on_current_Q_ulp_lattice':sum(not g['D_on_unchanged_account_binade_lattice'] for g in ledger),
      'source_price_CO2_policy':'Keep unknown source price and physical CO2 factor NULL; no new price or objective assumption.',
      'options':summaries,'recommended_option':'A_LARGEST_ACCOUNT_MINIMAL_UPWARD_BINARY64',
      'recommendation_boundary':'D<=Q certified for simulated constants, not exact D=Q or full-LP feasibility. Local finite remaining stock explicitly reported; no slack variable.',
      'tests':dict(tests),'matrix_scans':0,'model_builds':0,'solver_calls':0,'remote_operations':0,
      'source_inputs':inputs,'analysis_method_sha256':sha(Path(__file__).read_bytes())}
    write(out/'ALL_385_GROUPS_CLOSURE_LEDGER.json',{'schema':'385-group-exact-source-ledger-v1','counts':dict(cases),'groups':ledger})
    for name,rows in schemes.items(): write(out/('OPTION_'+name+'_SIMULATION.json'),{'option':name,'status':'PROPOSED_NOT_APPLIED','groups':rows})
    write(out/'CLOSURE_REPAIR_SUMMARY.json',summary)
    output_index=[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(out.glob('*.json'))]
    write(out/'ANALYSIS_VALIDATION.json',{'status':'EXACT_SIMULATION_ASSERTIONS_PASS','input_hashes':inputs,'outputs':output_index,
      'verified_exact_source_gaps':385,'matched_accounts':807,'full_LP_certified_groups_reused':1,
      'new_full_LP_certificates':0,'all_candidate_D_le_Q':True,'C_all_candidate_D_eq_Q':True,
      'A_positive_only_one_account_minimal':tests['A_minimal_for_selected_one_account']==180,
      'B_maximum_flat_feasible_load':tests['B_largest_admissible_constant_load']==180,
      'science_file_writes':0,'source_matrix_reads':0,'solver_calls':0})
    print(json.dumps({'counts':dict(cases),'outputs':output_index,'summary':str(out/'CLOSURE_REPAIR_SUMMARY.json')},ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True,type=Path)
    run(ap.parse_args().output)
