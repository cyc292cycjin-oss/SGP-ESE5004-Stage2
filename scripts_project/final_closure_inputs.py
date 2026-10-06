"""Frozen human Assembly V1 boundaries; source records are never rewritten."""
from pathlib import Path
from decimal import Decimal as D,localcontext
from copy import deepcopy
import json,hashlib,argparse
DECISION='GATE4-20261006-FINAL-CLOSURE'
LOW='ASSEMBLY_V1_BLEND_MAXIMUM_OVERLAP_BASELINE'
HIGH='ASSEMBLY_V1_BLEND_NO_OVERLAP_UPPER'
OUTSIDE='UNREPORTED_OUTSIDE_ASSEMBLY_V1_FIXED_DEMAND'
STOCK='SOURCE_QUALIFIED_SURVIVING_EXISTING_STOCK_ONLY'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def record_fingerprint(r):
    # Exact scientific record, excluding new representation-only closure labels.
    x={k:v for k,v in r.items() if k not in ['CoverageStatus','RequiredPhysical','Posting']}
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def eligible_unreported(r,e):
    if r.get('Year')!=2050 or r.get('Kind')!='DEMAND':return None
    if r.get('Account')=='InternationalShippingBunker' and r.get('Carrier')=='oil':
        return next((x for x in e['MarineBunkerFindings'] if x['Country']==r['Country'] and x['SourceSymbol']=='..'),None)
    fuels={('KH','gas'):'Natural Gas',('LA','gas'):'Natural Gas',('TL','coal'):'All Coal'}
    if (r.get('Country'),r.get('Carrier')) not in fuels:return None
    if r.get('Account') not in ['ResidentialFuel','ServicesFuel','IndustryFinalEnergy','AgricultureFinalEnergy','RoadResidualFuel']:return None
    return next((x for x in e['Findings'] if x['Country']==r['Country'] and x['FuelColumn']==fuels[r['Country'],r['Carrier']] and x['SourceSymbols']=='..'),None)
def derive_blends(prior,base,envelopes,mode):
    if mode not in [LOW,HIGH]:raise ValueError('Unapproved overlap parameter')
    rows={r['RowID']:deepcopy(r) for r in base['selected_rows']};adjustments=[];seen=set()
    for e in envelopes['records']:
        if e['Status']!='DERIVED_ACCOUNTING_ENVELOPE_ANALYSIS_ONLY' or not e['Proof']['InclusionVerified'] or not e['Proof']['VersionReconciled'] or e['CompatibilityProblems']:raise ValueError('Unqualified overlap envelope')
        p,b=rows[e['PSourceRow']],rows[e['BSourceRow']]
        if e['PSourceRow'] in seen:raise ValueError('Petroleum row adjusted twice')
        seen.add(e['PSourceRow'])
        if any(x['Country']!=e['Country'] for x in [p,b]) or p['Account']!=b['Account'] or p['RawUnit']!=b['RawUnit'] or p['RawUnit']!=e['RawUnit'] or D(p['RawValue'])!=D(e['P']) or D(b['RawValue'])!=D(e['B']):raise ValueError('Envelope/source mismatch')
        P,B=D(e['P']),D(e['B']);Z=min(P,B) if mode==LOW else D(0)
        hp,hb=D(e['PetroleumNCVMWhPerKton']),D(e['BioNCVMWhPerKton'])
        if D(p['MWh'])!=P*hp or D(b['MWh'])!=B*hb:raise ValueError('Frozen heat conversion mismatch')
        p['MWh']=str((P-Z)*hp)
        adjustments.append(dict(UncertaintyID=e['UncertaintyID'],Country=e['Country'],TransactionCode=e['TransactionCode'],P=str(P),B=str(B),Z=str(Z),UniqueQuantity=str(P+B-Z),FossilRemainder=str(P-Z),FossilMWh=p['MWh'],BioMWh=str(B*hb),UniqueEnergyMWh=str((P-Z)*hp+B*hb),RawUnit=e['RawUnit'],PSourceRow=e['PSourceRow'],BSourceRow=e['BSourceRow'],PVersion=e['PVersion'],BVersion=e['BVersion'],CompatibleCachedVersion=e['CompatibleCachedVersion'],SourceReportedZ=None,MethodID=mode,DecisionReference=DECISION+'#A',Affected2050Accounts=e['Affected2050Accounts']))
    output={};lookup={r['InputID']:r for r in prior['records']}
    base_lookup={r['AccountID']:r for r in base['accounts']}
    methods={t['InputID']:t for e in envelopes['records'] for t in e['TargetMethods']}
    with localcontext() as ctx:
        ctx.prec=40
        for ident in envelopes['account_to_uncertainty_ids']:
            r=lookup[ident];a=base_lookup[r['Locator']]
            if a['Status']!='UNRESOLVED_BIOFUEL_OVERLAP':raise ValueError('Unrelated unresolved base')
            selected=[rows[k] for k in a['SourceRows']]
            if any(z['Country']!=r['Country'] or z['Account']!=r['Account'] or z['Carrier']!=r['Carrier'] for z in selected):raise ValueError('Account ownership mismatch')
            value=sum((D(z['MWh']) for z in selected),D(0));m=methods[ident]
            if r['Account']=='RailNonElectric':num,den=D(1),D(1)
            else:num,den=D(m['GrowthNumerator']),D(m['GrowthDenominator'])
            if den<=0 or num<=0:raise ValueError('Invalid approved ratio')
            output[ident]=dict(InputID=ident,BaseAccountID=a['AccountID'],BaseMWh=str(value),Value=str(value*num/den),GrowthNumerator=str(num),GrowthDenominator=str(den),TargetMethodID=r['MethodID'],BlendMethodID=mode,SourceRows=a['SourceRows'],UncertaintyIDs=envelopes['account_to_uncertainty_ids'][ident],SourceReportedOverlap=False)
    return dict(method=mode,DecisionReference=DECISION+'#A',records=output,parameters=adjustments)
def classify_coverage(r):
    if r.get('Year')!=2050:return None
    if r.get('Kind')=='DEMAND' and r.get('AssemblyStatus')=='ASSEMBLY_V1_ACCEPTED':return 'PHYSICAL_ACCEPTED_AND_POSTED'
    if r.get('Representation')=='EMBEDDED_IN_ASTAR' or r.get('ParentAccount') and r.get('Representation','').startswith('EMBEDDED'):return 'EMBEDDED_IN_ACCEPTED_PARENT'
    if r.get('Classification')==OUTSIDE:return OUTSIDE
    if r.get('Classification')=='SOURCE_SCOPE_NO_ADDITIONAL_FINAL_LOAD':return 'SOURCE_SCOPE_NO_ADDITIONAL_FINAL_LOAD'
    if r.get('Classification')=='SOURCE_SUPPORTED_NOT_APPLICABLE':return 'DEFERRED_BY_FROZEN_RESEARCH_BOUNDARY' if r.get('BaseStatus')=='BOUNDARY_EXCLUSION' else 'SOURCE_SCOPE_NO_ADDITIONAL_FINAL_LOAD'
    if r.get('Kind') in ['ACCOUNTING','BOUNDARY']:return 'DEFERRED_BY_FROZEN_RESEARCH_BOUNDARY'
    return None
def apply(repo):
    f=repo/'research_inputs/assembly_v1';s=f/'sources';g=repo/'research/04_model_assembly/gate4';d=read(s/'ASSEMBLY_V1_FINAL_DECISIONS.json')
    if d['ApprovalStatus']!='HUMAN_ACCEPTED' or d['DecisionReference']!=DECISION:raise ValueError('Final boundary authorization absent')
    for rel,h in d['SourcePins'].items():
        if sha(repo/rel)!=h:raise ValueError('Final source pin changed '+rel)
    prior=read(s/'PRE_FINAL_REGISTRY.json');base=read(s/'BASE_RECONSTRUCTION.json');env=read(g/'evidence/uncertainty/BLEND_UNCERTAINTY_ENVELOPES.json');e=read(g/'evidence/uncertainty/SOURCE_REPORTING_STATUS.json')
    if sha(s/'PRE_FINAL_REGISTRY.json')!=env['source_pins']['research_inputs/assembly_v1/registry.json']:raise ValueError('Prior registry differs from accepted envelope')
    variants={};reports={}
    for mode in [LOW,HIGH]:
        result=derive_blends(prior,base,env,mode);name='ASSEMBLY_V1_BLEND_BASELINE.json' if mode==LOW else 'ASSEMBLY_V1_BLEND_UPPER.json';save(s/name,result);data=deepcopy(prior)
        changes=[];exclusions=[]
        for r in data['records']:
            if r['InputID'] in result['records']:
                z=result['records'][r['InputID']]
                r.update(Value=float(D(z['Value'])),RawValue=z['BaseMWh'],RawUnit='MWh/year derived under explicit overlap assumption',BaseValueMWh=z['BaseMWh'],BaseStatus='ASSEMBLY_V1_EXPLICIT_OVERLAP_ASSUMPTION',Source='sources/'+name,SourceSHA256=sha(s/name),Locator=r['InputID'],Transformation='Separate fossil remainder and biofuel, plus other unique source rows; BaseMWh * ('+z['GrowthNumerator']+'/'+z['GrowthDenominator']+')',AssemblyStatus='ASSEMBLY_V1_ACCEPTED',HumanAcceptance='CURRENT_EXPLICIT_BASELINE_ASSUMPTION',SourceQualified=True,TargetReady=True,NumericStatus='NUMERIC_INPUT_READY',Classification='REQUIRED_PHYSICAL',Gate2Status='READY_FOR_ACTUAL_ALLOCATION',CandidateValue=z['Value'],CandidateUnit='MWh/year',GrowthNumerator=z['GrowthNumerator'],GrowthDenominator=z['GrowthDenominator'],BlendMethodID=mode,BlendDecisionReference=DECISION+'#A',SourceReportedZ=None,Reason='Current explicit uncertainty parameter, not recovered memo',CarrierBreakdownMWh={r['Carrier']:z['BaseMWh']})
                changes.append(r['InputID'])
            elif r.get('Year')==2050 and r.get('Kind')=='DEMAND' and r.get('Classification')=='UNRESOLVED':
                proof=eligible_unreported(r,e)
                if proof is None or r['Value'] is not None or r.get('BaseSourceRows'):raise ValueError('Unapproved coverage exclusion '+r['InputID'])
                r.update(Classification=OUTSIDE,RequiredPhysical=False,Posting=False,RawValue=None,Value=None,AssemblyStatus='HUMAN_COVERAGE_BOUNDARY_APPLIED',NumericStatus='REPRESENTATION_RESOLVED_NON_NUMERIC',CoverageDecisionReference=DECISION+'#B',CoverageSourceSymbol='..',CoverageEvidence=proof,CoverageSourceSHA256=e['SHA256'],CoverageSourceFile='research/04_model_assembly/gate4/evidence/source_scope/UN_2019_balance_official.pdf',CoverageReason='Source-unreported fixed obligation outside Assembly V1; neither reported zero nor ban on future carrier use',Sensitivity='PHASE5_OR_LATER_COVERAGE_SENSITIVITY',LimitationFlag='UNKNOWN_REAL_CONSUMPTION_NOT_ZERO')
                exclusions.append(r['InputID'])
            if r.get('Year')==2050:
                coverage=classify_coverage(r)
                if r.get('Kind')=='DEMAND' and coverage is None:raise ValueError('Unclosed target '+r['InputID'])
                if coverage:r.update(CoverageStatus=coverage,RequiredPhysical=coverage=='PHYSICAL_ACCEPTED_AND_POSTED',Posting=coverage=='PHYSICAL_ACCEPTED_AND_POSTED')
        data.update(status='ASSEMBLY_V1_INPUT_COVERAGE_COMPLETE',assembly_variant='BASELINE_MAXIMUM_OVERLAP' if mode==LOW else 'FUTURE_SENSITIVITY_NO_OVERLAP',final_decision_reference=DECISION,final_decision_sha256=sha(s/'ASSEMBLY_V1_FINAL_DECISIONS.json'))
        variants[mode]=data;reports[mode]=dict(changed_accounts=changes,coverage_boundary_accounts=exclusions,physical_count=sum(r.get('CoverageStatus')=='PHYSICAL_ACCEPTED_AND_POSTED' for r in data['records']))
    save(f/'registry.json',variants[LOW]);upper=f/'variants/blend_no_overlap_upper/registry.json';save(upper,variants[HIGH])
    pins=read(f/'manifest.json')
    for name in ['registry.json','sources/PRE_FINAL_REGISTRY.json','sources/ASSEMBLY_V1_FINAL_DECISIONS.json','sources/ASSEMBLY_V1_BLEND_BASELINE.json','sources/ASSEMBLY_V1_BLEND_UPPER.json']:pins['files'][name]=sha(f/name)
    pins.update(assembly_variant='BASELINE_MAXIMUM_OVERLAP',method_id=LOW,DecisionReference=DECISION);save(f/'manifest.json',pins)
    save(upper.parent/'manifest.json',dict(assembly_variant='FUTURE_SENSITIVITY_NO_OVERLAP',method_id=HIGH,registry_sha256=sha(upper),baseline_registry_sha256=sha(f/'registry.json'),shared_source_root='../../',source_files={k:v for k,v in pins['files'].items() if k!='registry.json'},PostingToGate4Network=False,solver_allowed=False))
    save(g/'evidence/final/INPUT_DECISIONS_APPLIED.json',dict(DecisionReference=DECISION,variants=reports,baseline_registry_sha256=sha(f/'registry.json'),upper_registry_sha256=sha(upper),raw_sources_modified=False,previous_accepted_records_fingerprints={r['InputID']:record_fingerprint(r) for r in prior['records'] if r['Year']==2050 and r['Kind']=='DEMAND' and r['AssemblyStatus']=='ASSEMBLY_V1_ACCEPTED'}))
    validate_final_registry(f,variants[LOW]['records']);return reports
def validate_final_registry(folder,records):
    path=Path(folder)/'sources/ASSEMBLY_V1_FINAL_DECISIONS.json'
    if not path.exists():
        if any(r.get('Classification')==OUTSIDE or r.get('BlendMethodID') for r in records):raise ValueError('Missing final human decisions')
        return
    d=read(path)
    if d['ApprovalStatus']!='HUMAN_ACCEPTED' or d['DecisionReference']!=DECISION:raise ValueError('Wrong human boundary')
    baseline_data=read(Path(folder)/'sources/ASSEMBLY_V1_BLEND_BASELINE.json')
    if (Path(folder)/'sources/FINAL_ACCEPTED_BLEND_ENVELOPES.json').exists():
        derived=derive_blends(read(Path(folder)/'sources/PRE_FINAL_REGISTRY.json'),read(Path(folder)/'sources/BASE_RECONSTRUCTION.json'),read(Path(folder)/'sources/FINAL_ACCEPTED_BLEND_ENVELOPES.json'),LOW)
        if baseline_data!=derived:raise ValueError('Accepted blend file differs from independent source derivation')
    baseline=baseline_data['records'];e=read(Path(folder)/'sources/FINAL_UN_REPORTING_EVIDENCE.json')
    found=set()
    for r in records:
        if r.get('BlendMethodID'):
            z=baseline.get(r['InputID'])
            if z is None or r['BlendMethodID']!=LOW or D(str(r['Value']))!=D(str(float(D(z['Value'])))) or r['BaseValueMWh']!=z['BaseMWh'] or r['MethodID']!=z['TargetMethodID'] or r['SourceSHA256']!=sha(Path(folder)/r['Source']):raise ValueError('Blend accepted input differs from approved baseline')
            found.add(r['InputID'])
        if r.get('Classification')==OUTSIDE:
            if eligible_unreported(r,e) is None or r.get('CoverageDecisionReference')!=DECISION+'#B' or r.get('CoverageEvidence')!=eligible_unreported(r,e) or r.get('CoverageSourceSHA256')!=e['SHA256']:raise ValueError('Coverage escaped authorized evidence')
            if any(r.get(k) is not None for k in ['Value','RawValue','BaseValueMWh']) or r.get('BaseSourceRows') or r.get('Posting') is not False or r.get('RequiredPhysical') is not False:raise ValueError('Unreported account cannot be zeroed or posted')
    if found!=set(baseline):raise ValueError('Incomplete blend application')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);a=p.parse_args();print(json.dumps(apply(a.repo),indent=2))
