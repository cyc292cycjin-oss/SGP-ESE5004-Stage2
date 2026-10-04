"""Pinned observation capsule reader and ledger row constructors."""
from pathlib import Path
import hashlib,json
from demand_accounting import FIELDS, convert


def load_sources(repo, verify_originals=False):
    root=Path(repo)/'research_inputs/demand/sources'
    manifest=json.loads((root/'manifest.json').read_text())
    result={}
    for s in manifest['sources']:
        p=root/s['capsule']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=s['sha256']:raise ValueError('Capsule hash mismatch')
        if verify_originals:
            original=Path(s['source'])
            if not original.exists() or hashlib.sha256(original.read_bytes()).hexdigest()!=s['source_sha256']:
                raise ValueError('Original source missing/changed: '+str(original))
        data=json.loads(p.read_text())
        if data['source_sha256']!=s['source_sha256']:raise ValueError('Source manifest mismatch')
        result[p.stem]=data
    return result


def row(country,year,sector,account,carrier,**kwargs):
    r={k:'' for k in FIELDS}
    r.update(Country=country,Year=year,Sector=sector,Subsector=account,Carrier=carrier,
             DemandType='DIRECT_FUEL',RawValue=None,RawUnit='',ConvertedMWh=None,
             ParentAccount='',ChildAccount=account,Representation='EXPLICIT',SourceYear=2019,
             SpatialRule='PENDING_ACCEPTED_COUNTRY_NODE_WEIGHTS',TemporalRule='PENDING_ACCEPTED_SHAPE_AND_PHYSICAL_WEIGHTS',
             IncludedInAstar=False,TransferredFromAstar=False,FixedOrEndogenous='FIXED',
             Status='PENDING',HumanAcceptance='REPRESENTATION_ACCEPTED_NUMERIC_PENDING',
             RowID=f'{country}:{year}:{sector}:{account}:{carrier}',OwnerAccount=account,
             Posting=True,Required=True,NumericAccepted=False,ZeroEvidence='MISSING',
             LogicalDestination=f'{country}:{carrier}',ExistingEnergyLoad=False,EmissionsPresent=False,Group=sector,
             ParentBefore=None,TransferredChild=None,ParentAfter=None,IndependentReference=None)
    r.update(kwargs);return r


def cached(r,source,raw,locator,*,unit='TWh/year'):
    """Cache positives retained, unsupported cache zeros are not observations."""
    r.update(RawValue=raw if raw not in ('',None) else None,RawUnit=unit,Source=source['source'],
             SourceSHA256=source['source_sha256'],SourceLocator=locator,
             Transformation='Frozen derived cache; '+unit+' -> MWh; raw/calorific provenance still pending')
    if raw in ('',None): r.update(Status='MISSING',ZeroEvidence='MISSING')
    elif float(raw)==0:r.update(Status='MISSING',ZeroEvidence='CACHE_ZERO_UNVERIFIED',Notes=r['Notes']+'; cache zero has no certified raw-zero evidence')
    else:r.update(ConvertedMWh=convert(raw,unit),Status='FROZEN_UPSTREAM',ZeroEvidence='POSITIVE_CACHE_VALUE')
    return r


def electricity(r,source,label):
    matches=[x for x in source['records'] if x['Country']==r['Country'] and x['Commodity - Transaction']=='Electricity - '+label]
    if len(matches)>1:raise ValueError('Duplicate raw final-electricity transaction')
    r.update(Source=source['source'],SourceSHA256=source['source_sha256'],SourceLocator=label,
             RawUnit='Kilowatt-hours, million',Transformation='Exact raw transaction; million kWh * 1000 = MWh; no losses or AEO scaling')
    if not matches:r.update(Status='MISSING');return r
    x=matches[0];v=convert(x['Quantity'],x['Unit'])
    r.update(RawValue=x['Quantity'],RawUnit=x['Unit'],ConvertedMWh=v,Status='PENDING',
             ZeroEvidence='REPORTED_ZERO' if v==0 else 'REPORTED_VALUE',
             SourceLocator=label+'; physical line end '+str(x['SourceLineEnd']))
    return r
