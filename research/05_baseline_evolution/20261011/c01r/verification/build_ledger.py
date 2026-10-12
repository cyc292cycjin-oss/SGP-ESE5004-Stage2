"""C01R exact representation audit only; never imports a model/solver library."""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import datetime, hashlib, json, math, struct, subprocess, sys, time, resource
import numpy as np
import netCDF4

REPO=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
WORKSPACE=Path('/mnt/d/ResearchWorkspaces/ASEAN')
BASE=REPO/'research/05_baseline_evolution/20261011'
OUT=BASE/'c01r'; E=OUT/'evidence'
PRIOR='efb0ddb5b66c0305715d285c9d622ed65228b728'
C00='5d757c5a4a9dad965d9c7cbe6e55d486d167ff93'
SCHEME='8883de6fb3e15767c632ac92f535e8a423e90b69'
SCI='b9be7d0ab788a4151346c098d2e657c7e94a22da'
SP='research_inputs/derived/exact_source_closure_a_max_account_v1_20261011/'
NET=WORKSPACE/'outputs/phase4_gate4_final_closure_20261006/complete_network/research_fullsc_2050_assembly_v1_unsolved.nc'
V4=WORKSPACE/'work/gate6_wls_native_preflight_379_20261010/gate6_preflight379_wls_20261009T224539Z_b9665098/V4_APPROVED.json'
started=time.monotonic(); context={}; bindings={}; file_stats={}

class AuditStop(Exception):pass
def need(ok, reason):
    if not ok:raise AuditStop(reason)
def sha(b):return hashlib.sha256(b).hexdigest()
def arrsha(a):return sha(np.asarray(a,dtype='<f8',order='C').tobytes(order='C'))
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args])
def save(path,data,compact=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(data,f,ensure_ascii=False,indent=None if compact else 2,separators=(',',':') if compact else None,allow_nan=False);f.write('\n')
def object_at(commit,rel,expected=None):
    data=git('show',commit+':'+rel)
    if expected:need(sha(data)==expected,'GIT_OBJECT_SHA_MISMATCH:'+rel)
    bindings[commit+':'+rel]={'sha256':sha(data),'bytes':len(data)}
    return json.loads(data) if rel.endswith('.json') else data
def check_file(path,expected):
    before=path.stat();h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    need(h.hexdigest()==expected,'FILE_SHA_MISMATCH:'+str(path))
    file_stats[str(path)]=(before.st_size,before.st_mtime_ns)
    bindings[str(path).replace('/mnt/d/','D:/')]={'sha256':h.hexdigest(),'bytes':before.st_size,'mtime_ns':before.st_mtime_ns}
def bits(x):return struct.unpack('>Q',struct.pack('>d',x))[0]
def unbits(b):return struct.unpack('>d',struct.pack('>Q',b))[0]
def nearest_record(mean):
    rounded=struct.unpack('<d',struct.pack('<d',float(mean)))[0]
    need(math.isfinite(rounded) and rounded>=0,'NONFINITE_OR_NEGATIVE_DAILY_MEAN')
    q=F(rounded);b=bits(rounded)
    if mean==q:
        lower=F(unbits(b-1)) if b else -F(1,2**1074)
        upper=F(unbits(b+1))
        budget=min(q-lower,upper-q)/2;tie=False;ok=True
    else:
        lower,upper=(F(unbits(b-1)),q) if mean<q else (q,F(unbits(b+1)))
        need(lower<mean<upper,'BAD_ADJACENT_BRACKET')
        dl=mean-lower;du=upper-mean;tie=dl==du
        ok=abs(q-mean)==min(dl,du) and (not tie or b%2==0)
        budget=(upper-lower)/2
    need(ok and abs(q-mean)<=budget,'NOT_NEAREST_TIES_EVEN')
    return [str(mean),rounded.hex(),str(q-mean),str(budget),tie,True]

def execute():
    need(git('branch','--show-current').decode().strip()=='audit/stage2-c01r-bounded-binary64-20261012','WRONG_BRANCH')
    prior_index=json.loads((BASE/'c01/evidence/C01_EVIDENCE_INDEX.json').read_text())
    for rel,row in prior_index['files'].items():
        data=(REPO/rel).read_bytes()
        need(data==git('show',PRIOR+':'+rel) and len(data)==row['bytes'] and sha(data)==row['sha256'],'PRIOR_EVIDENCE_CHANGED:'+rel)
        bindings[PRIOR+':'+rel]=row
    original=object_at(C00,'research/05_baseline_evolution/20261011/b03_c00/C00_DAILY_365_DIAGNOSTIC_PROTOCOL.md','8530ea85ac087c89adafa594f885d3fa83d54d5f0a4fdd87e643f4b2d8e9ec86')
    manifest=object_at(SCHEME,SP+'EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json','a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720')
    ref=object_at(SCHEME,SP+'LOADS_AND_WEIGHTS_REFERENCE.json',manifest['files']['LOADS_AND_WEIGHTS_REFERENCE.json']['sha256'])
    accounts=object_at(SCHEME,SP+'external_pending_fixed_accounts.json',manifest['files']['external_pending_fixed_accounts.json']['sha256'])
    recipe=object_at(SCHEME,SP+'carrier_fragment.json',manifest['files']['carrier_fragment.json']['sha256'])
    registry=object_at(SCI,'research_inputs/assembly_v1/registry.json','2e5963b7e8a89cbd6369258ead0ce4e7d807f90d0a38b40013b91ed91fbfc518')
    check_file(NET,'238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d')
    check_file(V4,'955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f')
    previous=json.loads((BASE/'c01/evidence/C01_LOAD_ANNUAL_EXACT_CHECK.json').read_text())
    old={r['asset']:r for r in previous['records']}
    inventory=json.loads((BASE/'c01/evidence/C01_DYNAMIC_ATTRIBUTE_INVENTORY.json').read_text())
    owner={r['InputID']:r for r in registry['records']}
    refs={r['LoadID']:r for r in ref['loads']}
    rule={
      'version':'C00_DAILY_365_PROTOCOL_C01R_V1','rounding_rule':'C01R_BOUNDED_BINARY64_V1',
      'approval':'USER_AND_CHATGPT_EXPLICIT_APPROVAL_20261012','scope':'365_DAY_DIAGNOSTIC_INPUT_REPRESENTATION_ONLY',
      'applicability':'Only actual nonconstant Electricity/Astar/electricity Load profiles in the pinned 2920-slot input',
      'mean':'sum(Fraction(binary64_source_value)*Fraction(3))/Fraction(24)',
      'serialization':'IEEE754 binary64 round-to-nearest ties-to-even; no bias or corrections',
      'A':'Exact nearest adjacent-value comparison; tie selects even significand; error <= bracket gap/2',
      'half_ULP_definition':'For an inexact mean use half of its two adjacent binary64 bracketing values distance. For an exactly representable mean use half the smaller neighboring distance (including subnormals).',
      'B':'abs(E_daily-E_original) <= sum(24*per_day_half_ULP), all quantities exact rational',
      'C_absolute_MWh':{'decimal':'2e-9','exact':str(F('2e-9'))},
      'C_relative':{'decimal':'1e-15','exact':str(F('1e-15'))},
      'zero_annual_case':'E_original=0 requires DeltaE=0 AND finite nonnegative source values',
      'logic':'A AND B AND C_absolute AND C_relative_or_zero_rule, per asset; no cancellation across assets',
      'flat_Load':'Preserve source binary64 exactly; no new drift in formerly exact assets',
      'Scheme_A':'385 exact D<=Q_prime; 807 accounts and 180 approved repairs unchanged; no rounding exception',
      'CF_inflow':'Retain C00/C01 budget and physical-range evidence, no clipping or electricity C caps',
      'V4_sha256':'955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f',
      'V4_unchanged':True,'subtract_representation_error_from_future_V4_residual':False,
      'scientific_annual_demand_authority':'Original exact integral of pinned 2920 binary64 values; installed daily input is a separately recorded approximation',
      'mathematically_equivalent_to_original_LP':False,'network_or_LP_build_authorized':False,'solver_authorized':False,
      'previous_two_term_candidate':'NOT_SELECTED_NOT_IMPLEMENTED',
      'C00_parent_commit':C00,'C00_parent_document_sha256':sha(original),
      'Scheme_A_commit':SCHEME,'Scheme_A_manifest_sha256':sha(git('show',SCHEME+':'+SP+'EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json'))}
    save(E/'C01R_RULE.json',rule)
    rule_sha=sha((E/'C01R_RULE.json').read_bytes())
    print('SOURCE_IDENTITIES_PASS',flush=True)
    records=[];days=[]
    with netCDF4.Dataset(NET,'r') as n:
        n.set_auto_mask(False)
        actual={k:list(v.shape) for k,v in n.variables.items() if 'snapshots' in v.dimensions and not k.startswith('snapshots') and v.size}
        expected={r['netcdf_variable']:r['shape'] for r in inventory['dynamic_attributes']}
        need(actual==expected,'BLOCKED_PROTOCOL_EXTENSION_OR_DYNAMIC_IDENTITY')
        dates=netCDF4.num2date(n['snapshots_snapshot'][:],units=n['snapshots_snapshot'].units,calendar=n['snapshots_snapshot'].calendar)
        need(len(dates)==2920 and len(set(str(d) for d in dates))==2920,'TIME_AXIS_ERROR')
        need(np.array_equal(n['snapshots_snapshot'][:],np.arange(2920)*3),'TIME_STEP_ERROR')
        for name in ['objective','generators','stores']:
            weights=np.asarray(n['snapshots_'+name][:]);need(all(F(float(v))==3 for v in weights),'WEIGHT_ERROR')
            need(arrsha(weights)==ref['weights_sha256'],'WEIGHTS_SHA_ERROR')
        for d in range(365):
            ix=list(range(d*8,d*8+8));need(len(set(str(dates[i])[:10] for i in ix))==1,'INCOMPLETE_DAY')
            days.append({'day_index':d,'date':str(dates[ix[0]])[:10],'original_snapshot_indices':ix,'source_hours_exact':'24','daily_weight_exact':'24'})
        variable=n['loads_t_p_set'];ids=[str(x) for x in n[variable.dimensions[1]][:]]
        a=np.asarray(variable[:]);need(a.shape==(2920,1737) and a.dtype==np.dtype('float64'),'LOAD_SHAPE_OR_DTYPE')
        need(np.isfinite(a).all() and (a>=0).all(),'INVALID_LOAD_VALUES')
        need(set(ids)==set(old)==set(refs),'LOAD_IDENTITY_SET_CHANGED')
        need(arrsha(a)==next(r for r in inventory['dynamic_attributes'] if r['netcdf_variable']=='loads_t_p_set')['canonical_data_SHA256_float64_LE_C_order'],'LOAD_TABLE_SHA_CHANGED')
        for j,asset in enumerate(ids):
            context.clear();context.update(asset=asset)
            col=a[:,j];prior=old[asset];reference=refs[asset];o=owner[reference['InputID']]
            need(arrsha(col)==reference['binary64_sha256']==prior['source_SHA256_float64_LE'],'LOAD_SOURCE_SHA_CHANGED')
            flat=bool(np.all(col.view('u8')==col.view('u8')[0]))
            need(flat==prior['constant_source_binary64'],'NEW_ANOMALOUS_LOAD')
            eligible=not flat
            if eligible:need(o['Sector']=='Electricity' and o['Account']=='Astar' and o['Carrier']=='electricity','EXCEPTION_SCOPE_VIOLATION')
            entry={'component':'Load','LoadID':asset,'bus':prior['bus'],'carrier':prior['carrier'],
                   'DemandOwner':{'InputID':o['InputID'],'Country':o['Country'],'Sector':o['Sector'],'Account':o['Account'],'Carrier':o['Carrier'],'Year':o['Year']},
                   'DemandOwner_semantics':'Audit crosswalk of frozen registry InputID ownership; no new model attribute or ownership change',
                   'source_array_key':reference['ArrayKey'],'source_array_column':reference['column'],'source_values_sha256':arrsha(col),
                   'constant_source_binary64':flat,'C01R_electric_rounding_exception_applicable':eligible,
                   'rule_SHA256':rule_sha,'source_version_ref':'source_identity','day_buckets_ref':'day_buckets'}
            if flat:
                m=F(float(col[0])); row=nearest_record(m)
                original_annual=m*8760; daily_annual=m*8760;bound=F(row[3])*8760;series=[float(col[0])]*365
                entry['daily_records_RLE']={'first_day':0,'last_day_inclusive':364,'record_without_day_index':row,'semantics':'Exact same source binary64 and error=0 for each of 365 days'}
                tiecount=0;inexact=0
            else:
                source_fracs=[F(float(v)) for v in col]
                original_annual=sum(source_fracs,F(0))*3
                daily_annual=F(0);bound=F(0);daily=[];series=[];tiecount=0;inexact=0
                for d in range(365):
                    context['day_index']=d; m=sum(source_fracs[d*8:d*8+8],F(0))/8
                    row=nearest_record(m);daily.append([d]+row)
                    p=float.fromhex(row[1]);series.append(p);daily_annual+=F(p)*24;bound+=F(row[3])*24
                    tiecount+=int(row[4]);inexact+=int(F(row[2])!=0)
                entry['daily_records']=daily
            delta=daily_annual-original_annual;relative=abs(delta)/abs(original_annual) if original_annual else None
            need(original_annual==F(prior['annual_original']['exact']) and daily_annual==F(prior['annual_daily']['exact']),'C01_ANNUAL_BASELINE_MISMATCH')
            need(arrsha(series)==prior['daily_simulation_SHA256_float64_LE'],'C01_DAILY_REPRESENTATION_CHANGED')
            need(not(F(prior['annual_delta_daily_minus_original']['exact'])==0 and delta!=0),'EXACT_ASSET_NEW_DRIFT')
            checks={'A_daily_nearest_ties_even':True,'B_annual_half_ULP':abs(delta)<=bound,
                    'C_absolute':abs(delta)<=F('2e-9') if eligible else 'NOT_APPLICABLE_FLAT_EXACT_REQUIRED',
                    'C_relative':relative<=F('1e-15') if eligible and original_annual else (delta==0 if eligible else 'NOT_APPLICABLE_FLAT_EXACT_REQUIRED'),
                    'flat_bitwise_and_annual_identity':(delta==0 and all(bits(p)==bits(float(col[0])) for p in series)) if flat else 'NOT_APPLICABLE'}
            accepted=checks['A_daily_nearest_ties_even'] and checks['B_annual_half_ULP'] and ((checks['C_absolute'] and checks['C_relative']) if eligible else checks['flat_bitwise_and_annual_identity'])
            entry.update(E_original_MWh=str(original_annual),E_daily_MWh=str(daily_annual),DeltaE_MWh=str(delta),abs_DeltaE_MWh=str(abs(delta)),relative_abs_DeltaE=str(relative) if relative is not None else None,
                         annual_half_ULP_MWh=str(bound),annual_absolute_cap_MWh=str(F('2e-9')) if eligible else None,annual_relative_cap=str(F('1e-15')) if eligible else None,
                         zero_annual_special_case=original_annual==0,rounding_ties=tiecount,inexact_daily_means=inexact,
                         daily_audit_value_SHA256=arrsha(series),checks=checks,AND_pass=bool(accepted))
            records.append(entry);need(accepted,'C01R_NO_GO_HARD_GATE_FAILED')
        del a
    byload={r['LoadID']:r for r in records}; acc={a['FixedAccountID']:a for a in accounts};groups=[];seen=set()
    for g in previous['biomass_groups']:
        r=byload[g['load']];Q=sum((F(acc[i]['QuantityMWh']) for i in g['account_ids']),F(0));D=F(r['E_original_MWh'])
        need(r['constant_source_binary64'] and F(r['E_daily_MWh'])==D<=Q,'SCHEME_A_CLOSURE_FAILURE')
        need(str(D)==g['original_D_MWh'] and str(Q)==g['approved_Q_prime_MWh'],'SCHEME_A_SOURCE_RELATION_CHANGED')
        for i in g['account_ids']:
            q=acc[i]['QuantityMWh'];p=recipe['components']['Store:'+i]['params'];cap=recipe['biomass_obligation_routes'][i]['annual_cap_mwh']
            need(q>0 and all(struct.pack('<d',q)==struct.pack('<d',x) for x in [p['e_nom'],p['e_initial'],cap]),'SCHEME_A_FOUR_FIELDS_CHANGED')
            seen.add(i)
        groups.append({'LoadID':g['load'],'account_ids':g['account_ids'],'D_original_MWh':str(D),'D_daily_MWh':r['E_daily_MWh'],'Q_prime_MWh':str(Q),'exact_slack_MWh':str(Q-D),'PASS':True})
    need(len(groups)==385 and len(seen)==len(acc)==807,'SCHEME_A_COUNTS_ERROR')
    deltas=[F(r['DeltaE_MWh']) for r in records];drift=[r for r in records if F(r['DeltaE_MWh'])];eligible=[r for r in records if r['C01R_electric_rounding_exception_applicable']]
    maxima=max(records,key=lambda r:F(r['abs_DeltaE_MWh']));relative_max=max(records,key=lambda r:F(r['relative_abs_DeltaE'] or '0'))
    summary={'Load_assets':len(records),'constant_assets':sum(r['constant_source_binary64'] for r in records),'varying_electric_assets':len(eligible),
             'exact_annual_assets':sum(v==0 for v in deltas),'drift_assets':len(drift),'positive_drift':sum(v>0 for v in deltas),'negative_drift':sum(v<0 for v in deltas),
             'signed_annual_error_MWh':str(sum(deltas,F(0))),'absolute_annual_error_sum_MWh':str(sum(map(abs,deltas),F(0))),
             'max_absolute':{'LoadID':maxima['LoadID'],'MWh':maxima['abs_DeltaE_MWh']},'max_relative':{'LoadID':relative_max['LoadID'],'value':relative_max['relative_abs_DeltaE']},
             'inexact_daily_means':sum(r['inexact_daily_means'] for r in records),'ties':sum(r['rounding_ties'] for r in records),'blocked_assets':0,
             'all_95_drift_assets_pass':all(r['AND_pass'] for r in drift),'Scheme_A_groups':385,'Scheme_A_accounts':807,'Scheme_A_exact_D_le_Q_prime':385}
    need((summary['Load_assets'],summary['varying_electric_assets'],summary['exact_annual_assets'],summary['drift_assets'],summary['positive_drift'],summary['negative_drift'])==(1737,96,1642,95,52,43),'C01_COUNTS_CHANGED')
    need(summary['max_absolute']['MWh']=='159/137438953472' and summary['absolute_annual_error_sum_MWh']=='1442325/281474976710656','C01_REFERENCE_TOTAL_CHANGED')
    for path,st in file_stats.items():need((Path(path).stat().st_size,Path(path).stat().st_mtime_ns)==st,'SOURCE_MODIFIED_DURING_AUDIT')
    save(E/'C01R_LOAD_ROUNDING_LEDGER.json',{
      'schema':'C01R_LOAD_ROUNDING_LEDGER_V1','generator_status':'ALL_STATIC_GATES_PASS_PENDING_INDEPENDENT_VERIFIER',
      'source_identity':{'SourceVersion':'assembly_v1_2050_frozen_2920_3h','SourceRun':'phase4_gate4_final_closure_20261006_UNSOLVED_SOURCE_NOT_SOLVER_RUN',
      'NetCDF_sha256':bindings[str(NET).replace('/mnt/d/','D:/')]['sha256'],'original_Load_table_sha256':next(r['canonical_data_SHA256_float64_LE_C_order'] for r in inventory['dynamic_attributes'] if r['netcdf_variable']=='loads_t_p_set'),
      'scientific_commit':SCI,'Scheme_A_commit':SCHEME,'Scheme_A_manifest_sha256':rule['Scheme_A_manifest_sha256'],'previous_C01_commit':PRIOR},
      'rule_version':rule['rounding_rule'],'rule_sha256':rule_sha,'daily_record_columns':['day_index','exact_mean_MW','binary64_hex_MW','signed_error_MW','half_ULP_budget_MW','is_midpoint_tie','A_PASS'],
      'daily_flat_RLE_columns':['exact_mean_MW','binary64_hex_MW','signed_error_MW','half_ULP_budget_MW','is_midpoint_tie','A_PASS'],
      'day_buckets':days,'records':records,'summary':summary,'Scheme_A_groups':groups,'no_new_input_files':True,
      'units':{'daily':'MW','annual':'MWh','relative':'dimensionless'},'error_not_future_physical_tolerance':True},compact=True)
    save(E/'C01R_SOURCE_IDENTITY.json',{'status':'PASS','bindings':bindings,'new_dynamic_attributes':[],
      'dynamic_inventory':actual,'all_sources_unchanged':True,'V4_original_unchanged':True,
      'CF_inflow':'Reuse hash-verified C01 evidence on identical NetCDF; no new CF/inflow aggregation or clipping',
      'scope':'New electricity-load hard caps and exact adjacent rounding audit; no new network/LP/input recipe',
      'wall_seconds':time.monotonic()-started,'peak_RSS_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
      'python':sys.version.split()[0],'numpy':np.__version__,'netCDF4':netCDF4.__version__,
      'AutoDL_operations':0,'solver_calls':0,'source_write_operations':0,'G6_05':'PAUSED_BY_USER'})
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    try:execute()
    except Exception as exc:
        E.mkdir(parents=True,exist_ok=True)
        stop={'status':'C01R_NO_GO','final_status':'C01R_BLOCKED_WITH_EVIDENCE' if not isinstance(exc,AuditStop) else 'C01R_REPRESENTATION_REJECTED',
              'failure_context':context,'exception':type(exc).__name__,'reason':str(exc),'solver_calls':0,'AutoDL_operations':0}
        save(E/('C01R_STOP_'+datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S%f')+'.json'),stop)
        print(json.dumps(stop,ensure_ascii=False),file=sys.stderr);raise
