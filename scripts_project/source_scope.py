"""Apply the two human-approved, bounded statistical-scope interpretations.

No raw quantity, physical demand, plant, future supply interface or price is
changed. A missing final-consumption field remains missing. Source scope cannot
be reused as a nationwide zero, a bunker exemption, or a different fuel rule.
"""
from pathlib import Path
from decimal import Decimal as D
import argparse,copy,hashlib,json
from reconstruct_base_accounts import Reconstruction,commodity,norm,row_id,account_for_transaction

STATUS='SOURCE_SCOPE_NO_ADDITIONAL_FINAL_LOAD'
DECISION='GATE4-20261006-BOUNDED-SOURCE-SCOPE'
METHODS={('BN','coal'):'ASSEMBLY_V1_BN_REPORTED_COAL_TRANSFORMATION_SCOPE',('TL','gas'):'ASSEMBLY_V1_TL_REPORTED_GAS_BALANCE_SCOPE'}
ACCOUNTS={('BN','coal'):{'ResidentialFuel','ServicesFuel','IndustryFinalEnergy','AgricultureFinalEnergy'},('TL','gas'):{'ResidentialFuel','ServicesFuel','RoadResidualFuel'}}

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def derive_proofs(folder):
    s=Path(folder)/'sources';d=read(s/'BOUNDED_SOURCE_SCOPE_DECISIONS.json')
    if d['DecisionReference']!=DECISION or d['ApprovalStatus']!='HUMAN_ACCEPTED':raise ValueError('Missing current scope authorization')
    for rel,h in d['SourcePins'].items():
        if sha(s/rel)!=h:raise ValueError('Scope source revision requires review')
    b=Reconstruction(read(s/'UNSD_2019_SOURCE_CAPSULE.json'),read(s/'FROZEN_UPSTREAM_CONVERSIONS.json'))
    proofs={}
    for (country,fuel),method in METHODS.items():
        rule=d['Scopes'][country+':'+fuel]
        if rule['MethodID']!=method or rule['Year']!=2019:raise ValueError('Scope method/year changed')
        rows=[r for r in b.rows if r['Country']==country and b.fuels.get(commodity(r['Commodity']))==fuel]
        if not rows or any(r['Year']!='2019' or r['Quantity Footnotes'] for r in rows):raise ValueError('Year/footnote requires scope review')
        if any(account_for_transaction(r['Transaction']) is not None or 'consumption' in norm(r['Transaction']) for r in rows):raise ValueError('Final-use/bunker record cannot be discarded by scope decision')
        allowed_products=set(rule['CanonicalCommodities'])
        outside=[r for r in rows if commodity(r['Commodity']) not in allowed_products]
        if outside:raise ValueError('Additional reported commodity outside authorized scope remains unresolved')
        observed=[]
        for r in rows:
            q=D(r['Quantity'])
            if not q.is_finite() or q<0:raise ValueError('Raw quantity invalid')
            observed.append(dict(RowID=row_id(r),Raw=copy.deepcopy(r),QuantityState='REPORTED_ZERO' if q==0 else 'OBSERVED_QUANTITY'))
        def q(product,transaction,unit):
            found=[r for r in rows if commodity(r['Commodity'])==product and norm(r['Transaction'])==transaction]
            if len(found)!=1 or found[0]['Unit']!=unit:raise ValueError('Missing/duplicate/incompatible statistical level '+transaction)
            return D(found[0]['Quantity'])
        if country=='BN':
            transactions={'imports','transformation','transformation in electricity, chp and heat plants','transformation in autoproducer electricity plants','total energy supply'}
            if {norm(r['Transaction']) for r in rows}!=transactions:raise ValueError('Unreviewed BN transaction')
            levels={p:{t:q(p,t,'Metric tons,  thousand') for t in sorted(transactions)} for p in sorted(allowed_products)}
            qty=levels['brown coal']['imports']
            if qty!=D(rule['ObservedParentQuantity']) or any(v!=qty for z in levels.values() for v in z.values()):raise ValueError('Reported coal hierarchy not wholly reconciled')
            accounting=dict(ObservedParentQuantity=str(qty),Unit='Metric tons, thousand',CommodityHierarchy='Brown coal includes Lignite; do not sum',TransactionHierarchy='imports / TES / transformation / electricity-CHP-heat / autoproducer-electricity are successive or nested levels; do not sum',Posting=False,FinalConsumptionField=None)
        else:
            product='natural gas (including lng)';unit='Terajoules'
            if {norm(r['Transaction']) for r in rows}!={'production','gross production','exports','re-injected','flared and vented','flared','total energy supply'}:raise ValueError('Unreviewed TL transaction')
            z={t:q(product,t,unit) for t in ['production','gross production','exports','re-injected','flared and vented','flared','total energy supply']}
            if z['production']!=D(rule['ObservedNetProduction']) or z['production']!=z['exports'] or z['total energy supply']!=0:raise ValueError('TL net supply balance differs')
            if z['gross production']-z['re-injected']-z['flared and vented']!=z['production'] or z['flared']!=z['flared and vented']:raise ValueError('TL upstream hierarchy differs')
            accounting=dict(Quantities={k:str(v) for k,v in z.items()},Unit=unit,UpstreamHierarchy='gross minus reinjection minus flared-and-vented equals net production; Flared is a child, not another loss',Posting=False,FinalConsumptionField=None,UpstreamPhysicalEmissionsKnown=False,FutureExternalGasInterfaceUnchanged=True)
        proofs[country+':'+fuel]=dict(Country=country,Carrier=fuel,SourceYear=2019,MethodID=method,DecisionReference=DECISION,ScopeStatus=STATUS,CanonicalCommodities=sorted(allowed_products),ObservedRows=observed,Accounting=accounting,OutsideCoverageStatus='UNKNOWN_OUTSIDE_COVERAGE',OutsideCoverageMeaning='Other source vintages, unreported commodities or nationwide unobserved final uses are not proven zero; no outside physical quantity fabricated',OriginalFEC=None,ScopeSourceSHA256=sha(s/'UNSD_2019_SOURCE_CAPSULE.json'),DecisionSHA256=sha(s/'BOUNDED_SOURCE_SCOPE_DECISIONS.json'))
    return proofs

def validate_scope_record(r):
    if r.get('Classification')!=STATUS:return
    key=(r['Country'],r['Carrier'])
    if key not in METHODS or r['Account'] not in ACCOUNTS[key] or r['Kind']!='DEMAND' or r['Year']!=2050:raise ValueError('Scope reused outside approved target')
    if r.get('ScopeMethodID')!=METHODS[key] or r.get('ScopeDecisionReference')!=DECISION or not r.get('ScopeProofSHA256'):raise ValueError('Scope proof/decision absent')
    if any(r.get(k) is not None for k in ['Value','RawValue','BaseValueMWh']) or r.get('BaseSourceRows') or r.get('ZeroEvidence'):raise ValueError('Source scope cannot erase positive/zero physical evidence')
    if r.get('RequiredPhysical') is not False or r.get('Posting') is not False or not r.get('Required') or r.get('OutsideCoverageStatus')!='UNKNOWN_OUTSIDE_COVERAGE':raise ValueError('Scope boundary/ownership guard missing')
    if r.get('AssemblyStatus')!='SOURCE_SCOPE_APPLIED' or r.get('NumericStatus')!='REPRESENTATION_RESOLVED_NON_NUMERIC':raise ValueError('Scope interpretation promoted to accepted numeric input')

def validate_scope_registry(folder,records):
    scoped=[r for r in records if r.get('Classification')==STATUS]
    if not scoped:return
    proofs=derive_proofs(folder);p=Path(folder)/'sources/BOUNDED_SOURCE_SCOPE_APPLICATION.json';application=read(p)
    if application['proofs']!=proofs:raise ValueError('Scope application does not match raw-source interpretation')
    expected={r['InputID'] for r in records if (r['Country'],r['Carrier']) in ACCOUNTS and r['Year']==2050 and r['Kind']=='DEMAND' and r['Account'] in ACCOUNTS[(r['Country'],r['Carrier'])]}
    if expected!={r['InputID'] for r in scoped} or sorted(expected)!=application['AppliedInputIDs']:raise ValueError('Incomplete or extended scope application')
    for r in scoped:
        validate_scope_record(r)
        if r['ScopeProofSHA256']!=sha(p) or r['ScopeSourceSHA256']!=proofs[r['Country']+':'+r['Carrier']]['ScopeSourceSHA256']:raise ValueError('Scope proof hash mismatch')

def apply(folder,report):
    folder=Path(folder);proofs=derive_proofs(folder);data=read(folder/'registry.json');before=copy.deepcopy(data);changed=[]
    for r in data['records']:
        key=(r['Country'],r['Carrier'])
        if key not in ACCOUNTS or r['Year']!=2050 or r['Kind']!='DEMAND' or r['Account'] not in ACCOUNTS[key]:continue
        if r.get('Classification') not in ['UNRESOLVED',STATUS]:raise ValueError('Existing classification not eligible for bounded interpretation')
        if r['Value'] is not None or r.get('BaseSourceRows'):raise ValueError('Known source obligation cannot be excluded')
        r.update(Classification=STATUS,AssemblyStatus='SOURCE_SCOPE_APPLIED',NumericStatus='REPRESENTATION_RESOLVED_NON_NUMERIC',RequiredPhysical=False,Posting=False,ScopeMethodID=METHODS[key],ScopeDecisionReference=DECISION,ScopeSourceSHA256=proofs[r['Country']+':'+r['Carrier']]['ScopeSourceSHA256'],OutsideCoverageStatus='UNKNOWN_OUTSIDE_COVERAGE',Reason='Current human-approved reported-source scope only; no additional final Load; original missing FEC/value preserved',ScopeQualification='INTERPRETATION_ACCEPTED_NOT_A_NUMERIC_ZERO')
        changed.append(r['InputID'])
    p=folder/'sources/BOUNDED_SOURCE_SCOPE_APPLICATION.json';save(p,dict(schema='bounded-source-scope-application-v1',proofs=proofs,AppliedInputIDs=sorted(changed),NewDemandMWh=None,NewPhysicalLoads=0))
    for r in data['records']:
        if r.get('Classification')==STATUS:r['ScopeProofSHA256']=sha(p)
    validate_scope_registry(folder,data['records']);save(folder/'registry.json',data)
    pins=read(folder/'manifest.json')
    for rel in ['registry.json','sources/BOUNDED_SOURCE_SCOPE_DECISIONS.json','sources/BOUNDED_SOURCE_SCOPE_APPLICATION.json']:pins['files'][rel]=sha(folder/rel)
    save(folder/'manifest.json',pins)
    save(report,dict(DecisionReference=DECISION,AppliedInputIDs=sorted(changed),Changed=before!=data,SourceRawRecordsUnchanged=True,PhysicalValuesChanged=False,OriginalMissingFECUnchanged=True,ProofSHA256=sha(p),registry_sha256=sha(folder/'registry.json')))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();apply(**vars(a))
