"""Exact UNSD overlap/request identities derived from raw rows and official DSD."""
from pathlib import Path
from decimal import Decimal
import json,xml.etree.ElementTree as ET
from reconstruct_base_accounts import norm,commodity,account_for_transaction

def transaction_name(value):
    # Frozen UNdata display alias, same manufacturing/construction/non-fuel
    # mining industry account; not a mapping to an industry child or mining fuel use.
    return norm(value).replace('non-fuel mining industry','non-fuel industry').replace('consumption in road','consumption by road').replace('consumption in rail','consumption by rail').replace('consumption in agriculture, forestry and fishing','consumption by agriculture, forestry and fishing')

def official_codes(path):
    result={}
    for cl in ET.parse(path).getroot().iter():
        if cl.tag.endswith('Codelist'):
            result[cl.attrib['id']]={c.attrib['id']:next((n.text for n in c if n.tag.endswith('Name')),None) for c in cl if c.tag.endswith('Code')}
    return result

def build_crosswalk(result,sources,registry,receipt):
    codes=official_codes(sources/'unsd_targeted/DSD_Energy.xml')
    flows={transaction_name(v):k for k,v in codes['CL_TRANSACTION_NRG'].items()}
    raw={r['RowID']:r for r in result['selected_rows']};out=[]
    observations=json.loads((sources/'unsd_targeted/observations.json').read_text())
    plan=receipt['plan'];downloads={r['file']:r for r in receipt['downloads']}
    for overlap in result['biofuel_overlap']:
        bio=raw[overlap['BioSourceRow']];flow=flows.get(transaction_name(bio['Transaction']))
        if flow is None:raise ValueError('No official transaction identity: '+bio['Transaction'])
        memo,code,parent=('ZD','5222','gas oil/ diesel oil') if bio['Commodity']=='Biodiesel' else ('ZG','5212','motor gasoline')
        parents=[raw[k] for k in overlap['OilSourceRows'] if commodity(raw[k]['Commodity'])==parent]
        if not parents:raise ValueError('No compatible petroleum parent for '+bio['RowID'])
        account=bio['Account']; country=bio['Country'];year=result['year']
        if any(p['Country']!=country or transaction_name(p['Transaction'])!=transaction_name(bio['Transaction']) or p['RawUnit']!=bio['RawUnit'] for p in parents):raise ValueError('Parent/bio transaction, country or unit mismatch: '+str((country,bio['Transaction'],bio['RawUnit'],[(p['Transaction'],p['RawUnit']) for p in parents])))
        targets=[r['InputID'] for r in registry['records'] if r['Country']==country and r['Year']==2050 and r['Account']==account and r['Carrier'] in ['oil','biomass','unclassified_fuel']]
        if not targets:raise ValueError('No affected target account for '+country+':'+account)
        queried=flow in plan['transactions'].get(country,[])
        file=country+'_2019.xml';d=downloads.get(file,{})
        wildcard=downloads.get(country+'_blend_all_transactions.xml',{})
        matches=[r for r in observations if r['Country']==country and str(r['Year'])==str(year) and r['COMMODITY']==code and r['TRANSACTION']==flow]
        row=dict(RequestID=f'{country}:{year}:{code}:{flow}',Country=country,Year=year,Account=account,Transaction=flow,OfficialTransaction=codes['CL_TRANSACTION_NRG'][flow],BioCommodity=bio['Commodity'],MemoCommodity=memo,MemoSDMXCode=code,MemoName=codes['CL_COMMODITY_NRG'][code],ParentCommodity=parents[0]['Commodity'],ParentRows=[p['RowID'] for p in parents],ParentValues=[p['RawValue'] for p in parents],ParentSourceFiles=[p['SourceFile'] for p in parents],ParentSourceVersions=[p['SourceSHA256'] for p in parents],ParentFootnotes=[p['Footnotes'] for p in parents],BioSourceRow=bio['RowID'],BioRawValue=bio['RawValue'],RawUnit=bio['RawUnit'],AffectedTargetAccounts=targets,PriorTargetedQueryCovered=queried,PriorReceiptFile=file if queried else None,PriorReceiptSHA256=d.get('sha256') if queried else None,PriorWildcardReceipt=wildcard.get('file'),PriorWildcardStatus=wildcard.get('status'),ReturnedMemoRows=len(matches),RequestStatus='NO_MATCHING_TRANSACTION_RETURNED' if queried and not matches else 'NEW_QUERY_REQUIRED' if not queried else 'RETRIEVED_NEEDS_VINTAGE_CHECK',MappingStatus='REQUEST_MAPPING_VERIFIED_FROM_DSD',SourceOverlapResolved=False,OfficialEntry=receipt['official_entry'],ExactRequestURL=f"https://data.un.org/WS/rest/data/UNSD,DF_UNDATA_ENERGY,/A.{plan['countries'][country]}.{code}.{flow}/?startPeriod={year}&endPeriod={year}",RequiredFields='2019 quantity, unit/multiplier, transaction, revision/version, flags/footnotes, inclusion relationship; compatible petroleum and bio total vintage. Cached parents need not be supplied again.')
        out.append(row)
    validate_crosswalk(result,out,sources)
    return sorted(out,key=lambda r:r['RequestID'])

def validate_crosswalk(result,rows,sources):
    flows=official_codes(sources/'unsd_targeted/DSD_Energy.xml')['CL_TRANSACTION_NRG'];bybio={r['BioSourceRow']:r for r in rows}
    if len(bybio)!=len(rows):raise ValueError('Duplicate overlap mapping')
    raw={r['RowID']:r for r in result['selected_rows']}
    for o in result['biofuel_overlap']:
        if o['BioSourceRow'] not in bybio:raise ValueError('Overlap has no exact memo request or metadata route')
        r=bybio[o['BioSourceRow']];b=raw[o['BioSourceRow']]
        if r['Country']!=b['Country'] or r['Year']!=result['year'] or transaction_name(flows[r['Transaction']])!=transaction_name(b['Transaction']):raise ValueError('Request country/year/transaction mismatch')
        if r['MemoSDMXCode']!=('5222' if b['Commodity']=='Biodiesel' else '5212'):raise ValueError('Wrong memo commodity')
    return True

def reconcile_commodity_scope(parent,parts):
    """Compare mutually exclusive raw-use leaves with one FEC source parent."""
    if parent is None:return dict(Status='PARENT_NOT_REPORTED',Difference=None)
    if any(account_for_transaction(r['Transaction']) in [None,'InternationalShippingBunker','InternationalAviationBunker'] for r in parts):raise ValueError('Non-leaf or out-of-scope use in final-energy balance')
    if any(any(r[k]!=parent[k] for k in ['Country','Year','Commodity','Unit','SourceSHA256']) for r in parts):raise ValueError('Incompatible commodity source scope')
    if len({norm(r['Transaction']) for r in parts})!=len(parts):raise ValueError('Overlapping duplicate use')
    p=Decimal(str(parent['Quantity']));q=sum((Decimal(str(r['Quantity'])) for r in parts),Decimal(0))
    return dict(Status='SOURCE_TOTAL_CLOSED' if p==q else 'SOURCE_TOTAL_NOT_CLOSED',ParentRawValue=str(p),ExclusiveUsesRawValue=str(q),Difference=str(p-q))
