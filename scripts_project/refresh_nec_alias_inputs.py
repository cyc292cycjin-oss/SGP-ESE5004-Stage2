"""Mechanical UNSD1234 leaf recovery under the already accepted OtherNEC rule.

Raw sources and numerical methods are immutable. Existing positive accounts may
only gain the two pinned, previously unmapped LPG rows, never a balance residual.
"""
from pathlib import Path
from copy import deepcopy
from decimal import Decimal
import json,hashlib,argparse
from reconstruct_base_accounts import reconstruct

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def refresh(folder,output):
    s=folder/'sources';old=read(s/'BASE_RECONSTRUCTION.json');new=reconstruct(s)
    previous={r['AccountID']:r for r in old['accounts']};current={r['AccountID']:r for r in new['accounts']}
    decisions=read(s/'GATE4_CONSOLIDATED_BASELINE_DECISIONS.json')
    if decisions['ApprovalStatus']!='HUMAN_ACCEPTED' or decisions['Methods']['OtherNEC']!='ASSEMBLY_V1_OTHER_NEC_CONSTANT_2019':raise ValueError('Existing NEC decision missing')
    changes=[]
    for ident,b in current.items():
        a=previous.get(ident)
        if a and all(a[k]==b[k] for k in ['Status','ValueMWh','SourceRows','ZeroEvidence']):continue
        if b['Status']=='SOURCE_BOUNDED_ZERO' and a and a['Status']=='UNRESOLVED' and not a['SourceRows'] and b['ZeroEvidence']:
            changes.append(dict(AccountID=ident,Type='EXISTING_BOUNDED_FEC_RULE',Before=a,After=b));continue
        if b['Country'] not in ['MM','TL'] or b['Account']!='OtherNEC' or b['Carrier']!='oil' or b['Status']!='NUMERIC_INPUT_READY':raise ValueError('Unexpected alias change '+ident)
        added=set(b['SourceRows'])-set(a['SourceRows'] if a else [])
        rows=[r for r in new['selected_rows'] if r['RowID'] in added]
        if len(rows)!=1 or rows[0]['Transaction']!='Consumption by other consumers not elsewhere specified' or rows[0]['Commodity']!='Liquefied petroleum gas (LPG)':raise ValueError('Not the qualified1234 LPG alias')
        delta=Decimal(b['ValueMWh'])-Decimal(a['ValueMWh'] if a else '0')
        if delta!=Decimal(rows[0]['MWh']):raise ValueError('Positive change not accounted by raw row')
        changes.append(dict(AccountID=ident,Type='RECOVERED_EXISTING_SOURCE_LEAF',Before=a,After=b,AddedSourceRows=rows,AddedMWh=str(delta)))
    if not changes:save(output,dict(status='IDEMPOTENT_NO_CHANGE',changes=[]));return
    data=read(folder/'registry.json');prior_records=deepcopy(data['records']);byloc={r.get('Locator'):r for r in data['records'] if r['Year']==2050 and r['Kind']=='DEMAND'}
    save(s/'BASE_RECONSTRUCTION.json',new);digest=sha(s/'BASE_RECONSTRUCTION.json')
    for change in changes:
        b=change['After'];r=byloc.get(b['AccountID'])
        if change['Type']=='EXISTING_BOUNDED_FEC_RULE':
            if r is None or r['Value'] is not None:raise ValueError('Cannot remove positive obligation')
            r.update(BaseValueMWh=b['ValueMWh'],BaseStatus=b['Status'],Classification='SOURCE_SUPPORTED_NOT_APPLICABLE',NumericStatus='SOURCE_BOUNDED_ZERO',ZeroEvidence=';'.join(b['ZeroEvidence']),ExclusionEvidence='Existing frozen-commodity FEC exhaustion rule after official1234 alias recovery; not an absence=zero assumption',Reason=b['Reason'],SourceQualified=True)
        else:
            if r is None:
                template=next(x for x in prior_records if x['Year']==2050 and x['Account']=='OtherNEC' and x['Carrier']=='oil' and x['AssemblyStatus']=='ASSEMBLY_V1_ACCEPTED')
                r=deepcopy(template);r.update(InputID=b['Country']+':2050:'+template['Sector']+':OtherNEC:oil',Country=b['Country'],CountryScope=b['Country'],Locator=b['AccountID'],ParentAccount='');data['records'].append(r)
            if r['MethodID']!=decisions['Methods']['OtherNEC']:raise ValueError('Quantity method changed')
            r.update(Value=str(b['ValueMWh']),RawValue=str(b['ValueMWh']),RawUnit='MWh/year',Unit='MWh/year',SourceYear=2019,Source='sources/BASE_RECONSTRUCTION.json',BaseValueMWh=b['ValueMWh'],BaseStatus=b['Status'],BaseSourceRows=b['SourceRows'],Classification='REQUIRED_PHYSICAL',AssemblyStatus='ASSEMBLY_V1_ACCEPTED',NumericStatus='NUMERIC_INPUT_READY',SourceQualified=True,TargetReady=True,Required=True,EnergyBasis=b['EnergyBasis'],Transformation='Source-qualified exclusive2019 OtherNEC fuel account; constant2019 under existing human decision; recovered official1234 legacy label',ProjectionEvidence=r['DecisionReference'],SourceRepair='OFFICIAL_1234_LEGACY_TRANSACTION_ALIAS',Reason='Original LPG quantity and use restored; no balancing residual')
            # Remove copied optional values that could refer to a different source/account.
            for k in ['CandidateValue','ZeroEvidence','ExclusionEvidence','PhysicalChildren']:r.pop(k,None)
    for r in data['records']:
        if r.get('Source')=='sources/BASE_RECONSTRUCTION.json':r['SourceSHA256']=digest
    # The original known-positive ownership list remains intact; the new leaf is
    # directly owned by its explicit OtherNEC target, never an unallocated residual.
    save(folder/'registry.json',data);pins=read(folder/'manifest.json')
    for rel in ['sources/BASE_RECONSTRUCTION.json','registry.json']:pins['files'][rel]=sha(folder/rel)
    save(folder/'manifest.json',pins)
    from check_assembly_inputs import load_registry,validate_records
    validate_records(load_registry(folder)['records'])
    save(output,dict(status='MECHANICAL_SOURCE_RECOVERY',new_scientific_assumption=False,changes=changes,registry_sha256=sha(folder/'registry.json'),base_sha256=digest))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();refresh(a.folder,a.output)
