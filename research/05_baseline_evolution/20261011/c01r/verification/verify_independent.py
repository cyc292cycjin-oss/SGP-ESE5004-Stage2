"""Independent C01R verifier: integer dyadic sums + integer IEEE754 rounding.

Does not import the generator. Reads frozen NetCDF again and pinned Scheme A
Git objects; no model/solver import. Only its new audit receipt is written.
"""
from pathlib import Path
from fractions import Fraction as Q
import datetime, hashlib, json, struct, subprocess, time, resource, sys
import numpy as np
import netCDF4

R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
D=Path('/mnt/d/ResearchWorkspaces/ASEAN')
B=R/'research/05_baseline_evolution/20261011'
E=B/'c01r/evidence'
N=D/'outputs/phase4_gate4_final_closure_20261006/complete_network/research_fullsc_2050_assembly_v1_unsolved.nc'
V=D/'work/gate6_wls_native_preflight_379_20261010/gate6_preflight379_wls_20261009T224539Z_b9665098/V4_APPROVED.json'
S='8883de6fb3e15767c632ac92f535e8a423e90b69'
P='research_inputs/derived/exact_source_closure_a_max_account_v1_20261011/'
ABS=Q(1,500000000);REL=Q(1,1000000000000000)
context={};start=time.monotonic();source_stats={};boundary_tests=[]

class Rejected(Exception):pass
def check(ok,reason,actual=None,expected=None):
    if not ok:
        context.update(reason=reason,actual=actual,expected=expected)
        raise Rejected(reason)
def digest(data):return hashlib.sha256(data).hexdigest()
def check_source(path,expected):
    st=path.stat();h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    check(h.hexdigest()==expected,'SOURCE_SHA_MISMATCH',h.hexdigest(),expected)
    source_stats[str(path)]=(st.st_size,st.st_mtime_ns)
def obj(path,sha):
    b=subprocess.check_output(['git','-C',str(R),'show',S+':'+P+path])
    check(digest(b)==sha,'SCHEME_A_SHA_MISMATCH',digest(b),sha);return json.loads(b)
def dyadic_sum(values):
    ratios=[float(v).as_integer_ratio() for v in values]
    exp=max((d.bit_length()-1 for n,d in ratios),default=0)
    numerator=sum(n << (exp-(d.bit_length()-1)) for n,d in ratios)
    return Q(numerator,1 << exp)
def pow2(e):return Q(1<<e) if e>=0 else Q(1,1<<-e)
def encoded_value(b):
    exponent=(b>>52)&2047;mantissa=b&((1<<52)-1)
    check(exponent<2047 and b>>63==0,'BAD_BINARY64_BITS')
    return Q(mantissa)*pow2(-1074) if exponent==0 else Q((1<<52)+mantissa)*pow2(exponent-1023-52)
def nearest_integer(mean):
    check(mean>=0 and (mean.denominator & (mean.denominator-1))==0,'NOT_NONNEGATIVE_DYADIC')
    if mean==0:return 0
    exponent=mean.numerator.bit_length()-mean.denominator.bit_length()
    quantum=max(exponent-52,-1074)
    scaled=mean/pow2(quantum);k,r=divmod(scaled.numerator,scaled.denominator)
    if 2*r>scaled.denominator or (2*r==scaled.denominator and k%2):k+=1
    exact=Q(k)*pow2(quantum)
    # Conversion here is of a proved representable value, never the exact mean.
    value=float(exact);b=struct.unpack('>Q',struct.pack('>d',value))[0]
    check(encoded_value(b)==exact,'INTEGER_ROUNDING_ENCODING_ERROR')
    return b
def audit_mean(mean,b):
    expected=nearest_integer(mean);check(b==expected,'NEAREST_OR_TIE_PARITY_FAILURE',b,expected)
    actual=encoded_value(b)
    if actual==mean:
        lower=encoded_value(b-1) if b else -pow2(-1074)
        upper=encoded_value(b+1);bound=min(actual-lower,upper-actual)/2;tie=False
    else:
        lo=b if actual<mean else b-1
        lower=encoded_value(lo);upper=encoded_value(lo+1)
        bound=(upper-lower)/2;tie=(mean-lower)==(upper-mean)
        check(lower<mean<upper,'INDEPENDENT_BRACKET_ERROR')
        check(abs(actual-mean)<=bound,'DAILY_ERROR_EXCEEDS_HALF_GAP')
    return actual-mean,bound,tie
def annual_gates(delta,old,budget,A=True):
    return {'A':bool(A),'B':abs(delta)<=budget,'C_absolute':abs(delta)<=ABS,
            'C_relative_or_zero':(abs(delta)<=REL*abs(old)) if old else delta==0}
def boundary_checks():
    samples=[('zero',Q(0)),('exact_one',Q(1)),('midpoint_below_power_two',Q(1)-pow2(-54)),
             ('tie_even_lower',Q(1)+pow2(-53)),('tie_even_upper',Q(1)+3*pow2(-53)),
             ('subnormal_half_to_zero',pow2(-1075)),('subnormal_tie_up_even',3*pow2(-1075)),
             ('smallest_normal_left_boundary',pow2(-1022)-pow2(-1075))]
    expected=[0,0x3ff0000000000000,0x3ff0000000000000,0x3ff0000000000000,0x3ff0000000000002,0,2,0x0010000000000000]
    for (name,mean),b in zip(samples,expected):
        check(nearest_integer(mean)==b,'BOUNDARY_TEST_FAILED:'+name)
        audit_mean(mean,b);boundary_tests.append({'case':name,'status':'PASS'})
    check(all(annual_gates(ABS,Q(10**7),ABS).values()),'EXACT_DECIMAL_BOUNDARY_REJECTED')
    check(not annual_gates(ABS+Q(1,10**30),Q(10**7),Q(1))['C_absolute'],'ABOVE_ABSOLUTE_NOT_REJECTED')
    check(not annual_gates(Q(1,10**15)+Q(1,10**30),Q(1),Q(1))['C_relative_or_zero'],'ABOVE_RELATIVE_NOT_REJECTED')
    check(all(annual_gates(Q(0),Q(0),Q(0)).values()),'ZERO_RULE_FALSE_NEGATIVE')
    check(not annual_gates(Q(1,10**30),Q(0),Q(1))['C_relative_or_zero'],'ZERO_NONZERO_DRIFT_ACCEPTED')
    check(not all(annual_gates(Q(0),Q(1),Q(1),A=False).values()),'AND_IGNORES_A')
    check(not all(annual_gates(Q(1,10**16),Q(1),Q(0)).values()),'AND_IGNORES_B')
    boundary_tests.append({'case':'exact_caps_zero_case_AND_failure_paths','status':'PASS'})

def run():
    boundary_checks()
    ledger=json.loads((E/'C01R_LOAD_ROUNDING_LEDGER.json').read_text())
    rawrule=(E/'C01R_RULE.json').read_bytes();rule=json.loads(rawrule)
    check(ledger['rule_sha256']==digest(rawrule),'RULE_HASH_FAILURE')
    check(Q(rule['C_absolute_MWh']['decimal'])==ABS==Q(rule['C_absolute_MWh']['exact']),'ABS_CAP_CHANGED')
    check(Q(rule['C_relative']['decimal'])==REL==Q(rule['C_relative']['exact']),'REL_CAP_CHANGED')
    check_source(N,'238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d')
    check_source(V,'955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f')
    manifest=obj('EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json','a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720')
    ref=obj('LOADS_AND_WEIGHTS_REFERENCE.json',manifest['files']['LOADS_AND_WEIGHTS_REFERENCE.json']['sha256'])
    accounts=obj('external_pending_fixed_accounts.json',manifest['files']['external_pending_fixed_accounts.json']['sha256'])
    recipe=obj('carrier_fragment.json',manifest['files']['carrier_fragment.json']['sha256'])
    registry_bytes=subprocess.check_output(['git','-C',str(R),'show','b9be7d0ab788a4151346c098d2e657c7e94a22da:research_inputs/assembly_v1/registry.json'])
    check(digest(registry_bytes)=='2e5963b7e8a89cbd6369258ead0ce4e7d807f90d0a38b40013b91ed91fbfc518','REGISTRY_CHANGED')
    reg={r['InputID']:r for r in json.loads(registry_bytes)['records']}
    refs={r['LoadID']:r for r in ref['loads']};rows={r['LoadID']:r for r in ledger['records']}
    previous=json.loads((B/'c01/evidence/C01_LOAD_ANNUAL_EXACT_CHECK.json').read_text());prior={r['asset']:r for r in previous['records']}
    measured={};deltas=[];bounds={};ties=0;inexact=0;flat_count=0;vary=0;days_checked=0;zero_annual=0
    with netCDF4.Dataset(N,'r') as ds:
        ds.set_auto_mask(False)
        actual={k:list(v.shape) for k,v in ds.variables.items() if 'snapshots' in v.dimensions and not k.startswith('snapshots') and v.size}
        check(actual=={'loads_t_p_set':[2920,1737],'generators_t_p_max_pu':[2920,460],'storage_units_t_inflow':[2920,40]},'BLOCKED_PROTOCOL_EXTENSION')
        for k in ['objective','generators','stores']:
            w=np.asarray(ds['snapshots_'+k][:]);check(dyadic_sum(w)==8760 and np.all(w==3),'WEIGHTS_CHANGED')
            check(digest(w.astype('<f8').tobytes())==ref['weights_sha256'],'WEIGHTS_SOURCE_SHA')
        t=ds['snapshots_snapshot'][:];check(np.array_equal(t,np.arange(2920)*3),'SOURCE_SNAPSHOTS_CHANGED')
        dates=netCDF4.num2date(t,units=ds['snapshots_snapshot'].units,calendar=ds['snapshots_snapshot'].calendar)
        for d,bucket in enumerate(ledger['day_buckets']):
            check(bucket=={'day_index':d,'date':str(dates[d*8])[:10],'original_snapshot_indices':list(range(8*d,8*d+8)),'source_hours_exact':'24','daily_weight_exact':'24'},'BUCKET_IDENTITY_CHANGED')
        check(len(ledger['day_buckets'])==365,'BUCKET_COUNT')
        variable=ds['loads_t_p_set'];ids=[str(x) for x in ds[variable.dimensions[1]][:]]
        table=np.asarray(variable[:]);check(table.shape==(2920,1737),'SOURCE_LOAD_SHAPE')
        check(set(ids)==set(rows)==set(refs)==set(prior),'LOAD_ID_SET_CHANGED')
        for col,asset in enumerate(ids):
            context.clear();context.update(LoadID=asset)
            values=table[:,col];r=rows[asset];rf=refs[asset];o=reg[rf['InputID']]
            check(np.isfinite(values).all() and (values>=0).all(),'INVALID_OR_NEGATIVE_SOURCE')
            h=digest(values.astype('<f8').tobytes());check(h==rf['binary64_sha256']==r['source_values_sha256']==prior[asset]['source_SHA256_float64_LE'],'ASSET_SOURCE_HASH')
            owner={k:o[k] for k in ['InputID','Country','Sector','Account','Carrier','Year']}
            check(r['DemandOwner']==owner and r['rule_SHA256']==digest(rawrule),'OWNER_OR_RULE_CHANGED')
            flat=len(set(struct.pack('<d',float(v)) for v in values))==1
            check(flat==r['constant_source_binary64']==prior[asset]['constant_source_binary64'],'FLAT_FLAG_ERROR')
            check(r['C01R_electric_rounding_exception_applicable']==(not flat),'WRONG_EXCEPTION_APPLICABILITY')
            if not flat:check(o['Sector']=='Electricity' and o['Account']=='Astar' and o['Carrier']=='electricity','INELIGIBLE_ROUNDING')
            old=dyadic_sum(values)*3;new=Q(0);budget=Q(0);stored=[];asset_ties=0;asset_inexact=0
            if flat:
                flat_count+=1
                check(r['daily_records_RLE']['first_day']==0 and r['daily_records_RLE']['last_day_inclusive']==364,'BAD_FLAT_RLE_SPAN')
                record=r['daily_records_RLE']['record_without_day_index'];mean=dyadic_sum(values[:8])/8
                b=nearest_integer(mean);error,bound,tie=audit_mean(mean,b)
                p=struct.unpack('>d',struct.pack('>Q',b))[0]
                check(record==[str(mean),p.hex(),str(error),str(bound),tie,True],'FLAT_DAILY_RECORD_ERROR')
                check(struct.pack('<d',p)==struct.pack('<d',float(values[0])),'FLAT_VALUE_CHANGED')
                new=encoded_value(b)*8760;budget=bound*8760;stored=[p]*365
                days_checked+=365
            else:
                vary+=1;check(len(r['daily_records'])==365,'DAILY_RECORD_COUNT')
                for day in range(365):
                    context.update(day_index=day,date=str(dates[8*day])[:10])
                    mean=dyadic_sum(values[8*day:8*day+8])/8;b=nearest_integer(mean)
                    error,bound,tie=audit_mean(mean,b);p=struct.unpack('>d',struct.pack('>Q',b))[0]
                    expected=[day,str(mean),p.hex(),str(error),str(bound),tie,True]
                    check(r['daily_records'][day]==expected,'DAILY_LEDGER_MISMATCH',r['daily_records'][day],expected)
                    new+=encoded_value(b)*24;budget+=bound*24;stored.append(p)
                    asset_ties+=int(tie);asset_inexact+=int(error!=0);days_checked+=1
            delta=new-old;rel=abs(delta)/abs(old) if old else None
            for field,val in [('E_original_MWh',old),('E_daily_MWh',new),('DeltaE_MWh',delta),('abs_DeltaE_MWh',abs(delta)),('annual_half_ULP_MWh',budget)]:
                check(Q(r[field])==val,'ANNUAL_FIELD_MISMATCH:'+field,r[field],str(val))
            check(r['relative_abs_DeltaE']==(str(rel) if rel is not None else None),'RELATIVE_FIELD_MISMATCH')
            check(new==Q(prior[asset]['annual_daily']['exact']) and old==Q(prior[asset]['annual_original']['exact']),'PRIOR_C01_ANNUAL_CHANGED')
            check(digest(np.array(stored,dtype='<f8').tobytes())==r['daily_audit_value_SHA256']==prior[asset]['daily_simulation_SHA256_float64_LE'],'SERIALIZED_DAILY_HASH_CHANGED')
            check(not(Q(prior[asset]['annual_delta_daily_minus_original']['exact'])==0 and delta!=0),'NEW_DRIFT_IN_EXACT_ASSET')
            gates=annual_gates(delta,old,budget)
            if flat:
                expected_checks={'A_daily_nearest_ties_even':True,'B_annual_half_ULP':gates['B'],'C_absolute':'NOT_APPLICABLE_FLAT_EXACT_REQUIRED','C_relative':'NOT_APPLICABLE_FLAT_EXACT_REQUIRED','flat_bitwise_and_annual_identity':delta==0}
                check(delta==0,'FLAT_ANNUAL_CHANGE')
            else:
                check(Q(r['annual_absolute_cap_MWh'])==ABS and Q(r['annual_relative_cap'])==REL,'PER_ASSET_CAP_CHANGED')
                expected_checks={'A_daily_nearest_ties_even':True,'B_annual_half_ULP':gates['B'],'C_absolute':gates['C_absolute'],'C_relative':gates['C_relative_or_zero'],'flat_bitwise_and_annual_identity':'NOT_APPLICABLE'}
                check(all(gates.values()),'HARD_GATE_FAILED',gates)
            check(r['checks']==expected_checks and r['AND_pass'] is True,'REPORTED_GATE_MISMATCH')
            check(r['rounding_ties']==asset_ties and r['inexact_daily_means']==asset_inexact,'DAILY_COUNTS_MISMATCH')
            measured[asset]=(old,new,delta);bounds[asset]=budget;deltas.append(delta)
            ties+=asset_ties;inexact+=asset_inexact;zero_annual+=int(old==0)
    acc={a['FixedAccountID']:a for a in accounts};all_accounts=set()
    group_rows={g['LoadID']:g for g in ledger['Scheme_A_groups']}
    for oldg in previous['biomass_groups']:
        asset=oldg['load'];context.clear();context.update(LoadID=asset,scope='Scheme_A')
        g=group_rows[asset];aids=oldg['account_ids'];total=dyadic_sum([acc[k]['QuantityMWh'] for k in aids]);annual,daily,_=measured[asset]
        check(rows[asset]['constant_source_binary64'] and annual==daily<=total,'SCHEME_A_EXACT_CLOSURE')
        check(g=={'LoadID':asset,'account_ids':aids,'D_original_MWh':str(annual),'D_daily_MWh':str(daily),'Q_prime_MWh':str(total),'exact_slack_MWh':str(total-daily),'PASS':True},'SCHEME_A_LEDGER_MISMATCH')
        for k in aids:
            q=acc[k]['QuantityMWh'];p=recipe['components']['Store:'+k]['params'];cap=recipe['biomass_obligation_routes'][k]['annual_cap_mwh']
            check(q>0 and len({struct.pack('<d',float(v)) for v in [q,p['e_nom'],p['e_initial'],cap]})==1,'SCHEME_A_FOUR_FIELD_MISMATCH')
            all_accounts.add(k)
    check(len(group_rows)==385 and len(all_accounts)==len(acc)==807,'SCHEME_A_COUNTS')
    cf=json.loads((B/'c01/evidence/C01_CF_INFLOW_ROUNDING_CHECK.json').read_text())
    for family,count in [('CF',460),('inflow',40)]:
        check(len(cf[family]['records'])==count,'CF_INFLOW_COUNT_CHANGED')
        for p in cf[family]['records']:
            check(abs(Q(p['annual_delta_daily_minus_original']['exact']))<=Q(p['annual_half_ULP_bound']['exact']),'EXISTING_CF_INFLOW_BUDGET_FAIL',p['asset'])
    total=sum(deltas,Q(0));abstotal=sum(map(abs,deltas),Q(0))
    max_asset=max(measured,key=lambda a:abs(measured[a][2]));rel_asset=max(measured,key=lambda a:abs(measured[a][2]/measured[a][0]) if measured[a][0] else Q(0))
    independent_summary={'Load_assets':len(measured),'constant_assets':flat_count,'varying_electric_assets':vary,'exact_annual_assets':sum(x==0 for x in deltas),
        'drift_assets':sum(x!=0 for x in deltas),'positive_drift':sum(x>0 for x in deltas),'negative_drift':sum(x<0 for x in deltas),
        'signed_annual_error_MWh':str(total),'absolute_annual_error_sum_MWh':str(abstotal),
        'max_absolute':{'LoadID':max_asset,'MWh':str(abs(measured[max_asset][2]))},
        'max_relative':{'LoadID':rel_asset,'value':str(abs(measured[rel_asset][2]/measured[rel_asset][0]))},
        'inexact_daily_means':inexact,'ties':ties,'blocked_assets':0,'all_95_drift_assets_pass':True,
        'Scheme_A_groups':385,'Scheme_A_accounts':807,'Scheme_A_exact_D_le_Q_prime':385}
    check(independent_summary==ledger['summary'],'SUMMARY_MISMATCH',independent_summary,ledger['summary'])
    check((vary,flat_count,independent_summary['exact_annual_assets'],independent_summary['drift_assets'])==(96,1641,1642,95),'C01_REFERENCE_COUNTS')
    check(total==Q(293007,281474976710656) and abstotal==Q(1442325,281474976710656),'C01_REFERENCE_TOTALS')
    for path,st in source_stats.items():check((Path(path).stat().st_size,Path(path).stat().st_mtime_ns)==st,'SOURCE_STAT_CHANGED')
    return {'status':'C01R_REPRESENTATION_ACCEPTED','verification':'INDEPENDENT_SOURCE_READ_AND_INTEGER_DYADIC_IEEE754_ROUNDING',
      'generator_imported':False,'mean_rounding_uses_float_of_exact_mean':False,
      'all_day_buckets_verified':days_checked,'varying_day_buckets_individually_recomputed':96*365,
      'flat_buckets_verified_by_bitwise_constant_proof':1641*365,'midpoint_ties_checked':ties,
      'boundary_tests':boundary_tests,'zero_annual_assets_actual':zero_annual,'summary':independent_summary,
      'CF_inflow_reused_budget_check_assets':500,'CF_above_one_values_retained_from_C01':44,
      'representation_error_separate_from_V4':True,'V4_original_SHA256':'955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f',
      'ledger_SHA256':digest((E/'C01R_LOAD_ROUNDING_LEDGER.json').read_bytes()),'rule_SHA256':digest(rawrule),
      'source_NetCDF_SHA256':'238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d',
      'Scheme_A_manifest_SHA256':'a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720',
      'source_unchanged':True,'failed_assets':[],'C02_authorized':False,'new_model_or_LP':False,
      'solver_calls':0,'AutoDL_operations':0,'G6_05':'PAUSED_BY_USER'}

if __name__=='__main__':
    try:result=run()
    except Exception as exc:
        result={'status':'C01R_REPRESENTATION_REJECTED' if isinstance(exc,Rejected) else 'C01R_BLOCKED_WITH_EVIDENCE',
                'failure_context':context,'reason':str(exc),'exception_type':type(exc).__name__,'C02_authorized':False,'solver_calls':0}
    result.update(wall_seconds=time.monotonic()-start,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                  verifier_SHA256=digest(Path(__file__).read_bytes()),Python=sys.version.split()[0],checked_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat())
    with (E/'C01R_INDEPENDENT_CHECK.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(0 if result['status']=='C01R_REPRESENTATION_ACCEPTED' else 1)
