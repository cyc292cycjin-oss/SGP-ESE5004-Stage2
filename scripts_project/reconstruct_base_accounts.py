"""Reconstruct 2019 final-fuel accounts from pinned UNSD rows, not cache labels.

No network, optimisation, growth or inferred missing-zero belongs in this layer.
UNSD natural-gas TJ/GCV is distinguished from other gases and already converted
energy. A published parent replaces its overlapping children, never adds to them.
"""
from decimal import Decimal as D
from collections import defaultdict
import hashlib,json,re
from pathlib import Path

COUNTRIES=('BN','ID','KH','LA','MM','MY','PH','SG','TH','TL','VN')
ACCOUNTS={
 'ResidentialFuel':('oil','gas','coal','biomass'),
 'ServicesFuel':('oil','gas','coal','biomass'),
 'IndustryFinalEnergy':('oil','gas','coal','biomass'),
 'AgricultureFinalEnergy':('oil','coal','biomass'),
 'RoadResidualFuel':('oil','gas','biomass'),
 'TransportEmbeddedFuelParent':('unclassified_fuel',),
 'DomesticShippingFuel':('oil',),'DomesticAviationFuel':('oil',),
 'InternationalShippingBunker':('oil',),'InternationalAviationBunker':('oil',),
}
UNSD_CONVERSION='https://unstats.un.org/unsd/energy/balance/2014/05.pdf'
def norm(x):return re.sub(r'\s+',' ',x.strip().lower())
def commodity(x):
 c=norm(x)
 return {'liquified petroleum gas (lpg)':'liquefied petroleum gas (lpg)','hrad coal':'hard coal','coke-oven coke':'coke oven coke','natural gas':'natural gas (including lng)'}.get(c,c)
def row_id(r):return r['SourceSHA256']+':'+str(r['PhysicalLine'])
def decimal(x):
 v=D(str(x))
 if not v.is_finite() or v<0:raise ValueError('Non-finite or negative raw energy')
 return v
def account_for_transaction(t):
 t=norm(t)
 if t in {'consumption by households'}:return 'ResidentialFuel'
 if t in {'consumption by commerce and public services','consumption by commercial and public services'}:return 'ServicesFuel'
 if t in {'consumption by agriculture, forestry and fishing','consumption in agriculture, forestry and fishing'}:return 'AgricultureFinalEnergy'
 if t in {'consumption by road','consumption in road'}:return 'RoadResidualFuel'
 if t in {'consumption by rail','consumption in rail'}:return 'TransportEmbeddedFuelParent'
 if t=='consumption not elsewhere specified (transport)':return 'TransportNEC'
 if t=='consumption not elsewhere specified (other)':return 'OtherNEC'
 if t in {'consumption by domestic navigation','consumption in domestic navigation'}:return 'DomesticShippingFuel'
 if t in {'consumption by domestic aviation','consumption in domestic aviation'}:return 'DomesticAviationFuel'
 if t=='international marine bunkers':return 'InternationalShippingBunker'
 if t=='international aviation bunkers':return 'InternationalAviationBunker'
 if t in {'consumption by manufacturing, construction and non-fuel industry','consumption by manufacturing, construction and non-fuel mining industry'}:return 'IndustryFinalEnergy'
 return None

class Reconstruction:
 def __init__(self,source,conversion):
  self.raw=source['records'];self.conversion=conversion
  c=conversion['constants'];self.factors={commodity(k):D(str(v)) for k,v in c['fuels_conv_toTWh'].items()}
  self.fuels={commodity(v):key for key,name in [('oil','oil_fuels'),('gas','gas_fuels'),('coal','coal_fuels'),('biomass','biomass_fuels'),('electricity','electricity'),('heat','heat')] for v in c[name]}
  self.fuels['natural gas (including lng)']='gas'
  self.selection=[];self.duplicates=[];self.errors=[]
  self.rows=self.deduplicate(self.raw)
 def deduplicate(self,rows):
  out=[];seen={}
  for r in rows:
   if not r['Commodity']:continue # unlabeled 'of which' / generation rows are not end-use totals
   key=(r['Country'],commodity(r['Commodity']),norm(r['Transaction']),r['Unit'])
   if key in seen:
    if decimal(seen[key]['Quantity'])!=decimal(r['Quantity']):raise ValueError('Conflicting duplicate raw records: '+str(key))
    self.duplicates.append(dict(kept=row_id(seen[key]),excluded=row_id(r),reason='EXACT_ALIAS_DUPLICATE'))
   else:out.append(r);seen[key]=r
  return out
 def convert(self,r):
  q=decimal(r['Quantity']); c=commodity(r['Commodity']);unit=r['Unit'];f=self.fuels.get(c)
  if unit=='Kilowatt-hours, million' and f=='electricity':return q*1000,'kWh-million *1000','FINAL_ELECTRICITY'
  if unit=='Terajoules':
   if c=='natural gas (including lng)':
    # This exact UNSD source series is documented as TJ on GCV, not a blanket
    # operation on gas, biogas, refinery gas or pre-existing MWh/TWh values.
    return q*D('0.9')/D('0.0036'),'UNSD raw natural-gas TJ/GCV *0.90 /0.0036; PDF p2','NCV_FROM_SOURCE_GCV'
   if f in {'biomass','coal','heat'}:return q/D('0.0036'),'UNSD net-energy TJ /0.0036; PDF p2-3','NCV_AS_REPORTED'
   raise ValueError('Unqualified TJ basis: '+c)
  if unit=='Metric tons,  thousand' and c in self.factors and c!='fuelwood':
   return q*self.factors[c]*1000000,'kton * frozen commodity-specific TWh/kton *1e6','NCV_FROZEN_UPSTREAM_COMMODITY_FACTOR'
  if unit=='Cubic metres, thousand' and c=='fuelwood':
   return q*self.factors[c]*1000000,'1000m3 * frozen0.00254TWh/1000m3 *1e6; UNSD9.135GJ/m3 rounded by upstream','NCV_FROZEN_VOLUME_FACTOR'
  raise ValueError('Unsupported source unit/basis: '+c+'/'+unit)
 def select_coal_hierarchy(self,rows):
  # UNSD aggregate fuel products. A reported aggregate is a source total,
  # not a fabricated residual and not a total added to its child products.
  out=list(rows);excluded=[]
  for parent,children in [('hard coal',{'anthracite','coking coal','other bituminous coal'}),('brown coal',{'lignite','sub-bituminous coal'})]:
   p=[r for r in out if commodity(r['Commodity'])==parent]
   if not p:continue
   ch=[r for r in out if commodity(r['Commodity']) in children]
   if not ch:continue
   if len(p)!=1 or any(r['Unit']!=p[0]['Unit'] for r in ch):raise ValueError('Ambiguous coal parent units')
   if sum(decimal(r['Quantity']) for r in ch)>decimal(p[0]['Quantity'])+D('0.001'):
    raise ValueError('Coal children exceed reported parent: '+row_id(p[0]))
   for r in ch:out.remove(r);excluded.append(dict(row=row_id(r),kept_parent=row_id(p[0]),reason='COMMODITY_CHILD_ALREADY_IN_REPORTED_PARENT'))
  return out,excluded
 def reported_zero_bound(self,c,account,fuel):
  """Prove a zero only from reported disjoint allocations exhausting FEC.

  No positive unallocated difference is turned into a sector demand. A source
  absent commodity is not asserted to be physically zero. This proof is bounded
  to the recorded commodity inventory and records every supporting raw row.
  """
  if account.startswith('International'):return None # bunkers are outside domestic FEC
  fec=[r for r in self.rows if r['Country']==c and self.fuels.get(commodity(r['Commodity']))==fuel and norm(r['Transaction'])=='final energy consumption']
  if not fec:return None
  fec,excluded=self.select_coal_hierarchy(fec);evidence=[]
  for p in fec:
   q=decimal(p['Quantity']);com=commodity(p['Commodity'])
   if q==0:evidence.append(row_id(p));continue
   parts=[r for r in self.rows if r['Country']==c and commodity(r['Commodity'])==com and r['Unit']==p['Unit'] and account_for_transaction(r['Transaction']) not in {None,account,'InternationalShippingBunker','InternationalAviationBunker'}]
   # Explicit NEC end-use leaves are disjoint from named sectors. Retain their
   # original ownership; use them only to prove exhaustion of this commodity FEC.
   # NEC already has unique account_for_transaction ownership above.
   total=sum(decimal(r['Quantity']) for r in parts)
   if abs(total-q)>D('0.000001'):return None
   evidence.extend([row_id(p),*[row_id(x) for x in parts]])
  return evidence
 def build(self):
  accounts=[];industry_audit=[];nonenergy=[]
  for r in self.rows:
   t=norm(r['Transaction'])
   if t in {'non-energy uses','consumption for non-energy uses'}:
    v,formula,basis=self.convert(r)
    nonenergy.append(dict(Country=r['Country'],Commodity=r['Commodity'],MWh=str(v),RawRow=row_id(r),Purpose='NON_ENERGY_REFERENCE_NOT_COMBUSTION',Formula=formula,EnergyBasis=basis))
  for c in COUNTRIES:
   uses=dict(ACCOUNTS)
   # Only observed NEC carrier accounts are materialised, no fictitious Cartesian obligations.
   for use in ['TransportNEC','OtherNEC']:
    fuels={self.fuels.get(commodity(r['Commodity'])) for r in self.rows if r['Country']==c and account_for_transaction(r['Transaction'])==use}
    fuels.discard(None);fuels.discard('electricity');uses[use]=sorted(fuels)
   for account,fuels in uses.items():
    for fuel in fuels:
     candidates=[r for r in self.rows if r['Country']==c and account_for_transaction(r['Transaction'])==account and self.fuels.get(commodity(r['Commodity']))!='electricity' and (fuel=='unclassified_fuel' or self.fuels.get(commodity(r['Commodity']))==fuel)]
     old_candidates=list(candidates);excluded=[];error=None
     try:candidates,excluded=self.select_coal_hierarchy(candidates)
     except ValueError as exc:error=str(exc)
     quantity=D(0);selected=[];carrier_values=defaultdict(lambda:D(0));bases=[]
     for raw in candidates:
      try:
       v,formula,basis=self.convert(raw);quantity+=v;bases.append(basis)
       carrier_values[self.fuels[commodity(raw['Commodity'])]]+=v
       selected.append(dict(RowID=row_id(raw),Country=c,Account=account,Carrier=self.fuels[commodity(raw['Commodity'])],Commodity=raw['Commodity'],Transaction=raw['Transaction'],RawValue=raw['Quantity'],RawUnit=raw['Unit'],MWh=str(v),Transformation=formula,EnergyBasis=basis,SourceFile=raw['SourceFile'],PhysicalLine=raw['PhysicalLine'],SourceSHA256=raw['SourceSHA256'],Footnotes=raw['Quantity Footnotes']))
      except ValueError as exc:error=str(exc)
     status='NUMERIC_INPUT_READY' if candidates and not error else 'UNRESOLVED'
     classification='REQUIRED_PHYSICAL' if candidates and not error else 'UNRESOLVED'
     zero_evidence=[]
     if not candidates:
      if c=='TL' and account=='IndustryFinalEnergy':
       classification='SOURCE_SUPPORTED_NOT_APPLICABLE';status='BOUNDARY_EXCLUSION';error='Phase3c TL independent industry deferred; unknown fuel is not zero'
      else:
       # A road-only vintage overlay must not be mixed into an older complete
       # FEC balance used as bounded zero evidence for other source accounts.
       zero_evidence=getattr(self,'zero_scope',self).reported_zero_bound(c,account,fuel) or []
       if zero_evidence:classification='SOURCE_SUPPORTED_NOT_APPLICABLE';status='SOURCE_BOUNDED_ZERO';error=None
     if candidates and quantity==0 and not error:classification='SOURCE_SUPPORTED_NOT_APPLICABLE';status='SOURCE_REPORTED_ZERO';zero_evidence=[r['RowID'] for r in selected]
     if error and classification!='SOURCE_SUPPORTED_NOT_APPLICABLE':status='UNRESOLVED'
     for raw in selected:self.selection.append(raw)
     # Record industry detailed children solely as a comparison to the source
     # parent. No parent+children or feedstock sum enters the account.
     if account=='IndustryFinalEnergy' and candidates:
      for parent in candidates:
       same=[r for r in self.rows if r['Country']==c and commodity(r['Commodity'])==commodity(parent['Commodity']) and ('consumption by' in norm(r['Transaction']) or 'consumption not elsewhere specified (industry)'==norm(r['Transaction'])) and account_for_transaction(r['Transaction']) is None]
       industry_audit.append(dict(Country=c,Commodity=parent['Commodity'],ParentRow=row_id(parent),ParentRawQuantity=parent['Quantity'],DetailRows=[row_id(x) for x in same],Rule='REPORTED_INDUSTRY_PARENT_ONLY; details retained for review, never added'))
     accounts.append(dict(AccountID=c+':2019:'+account+':'+fuel,Country=c,Year=2019,Account=account,Carrier=fuel,ValueMWh=str(quantity) if candidates and not error else '0' if zero_evidence else None,Status=status,Classification=classification,SourceRows=[r['RowID'] for r in selected],ZeroEvidence=zero_evidence,ExcludedOverlappingRows=excluded,CarrierBreakdownMWh={k:str(v) for k,v in carrier_values.items()},EnergyBasis=';'.join(sorted(set(bases))),Reason=error or ('Raw account sum; electricity remains in Astar' if candidates else 'Reported final-energy commodity inventory exhausted by disjoint source accounts; bounded exclusion, not absence guessed from empty selection' if zero_evidence else 'No source-qualified2019 row or zero proof'),SelectedRawRows=len(selected),OriginalCandidateRows=len(old_candidates)))
  return dict(schema='research-base-reconciliation-1',year=2019,accounts=accounts,selected_rows=self.selection,industry_parent_audit=industry_audit,nonenergy_reference=nonenergy,exact_alias_duplicates=self.duplicates,unlabelled_rows=[dict(SourceFile=r['SourceFile'],PhysicalLine=r['PhysicalLine'],Label=r['Commodity - Transaction'],Country=r['Country']) for r in self.raw if not r['Commodity']],conversion_provenance=UNSD_CONVERSION)

def reconstruct(folder, *, allow_blend_evidence=True):
 folder=Path(folder)
 s=json.loads((folder/'UNSD_2019_SOURCE_CAPSULE.json').read_text())
 frozen_scope=json.loads((folder/'UNSD_2019_SOURCE_CAPSULE.json').read_text())
 overlay=folder/'TH_ROAD_LOCAL_VINTAGE_APPLIED.json'
 if overlay.exists():
  replacement=json.loads(overlay.read_text())
  if replacement.get('ApprovalStatus')!='HUMAN_ACCEPTED' or not replacement.get('DecisionReference'):raise ValueError('Unapproved local vintage update')
  byid={row_id(r):i for i,r in enumerate(s['records'])}
  for entry in replacement['replacements']:
   idx=byid[entry['OldRowID']];prior=s['records'][idx];new=entry['NewRawRow']
   if any(prior[k]!=new[k] for k in ['Country','Year','Commodity','Transaction','Unit']):raise ValueError('Local vintage scope drift')
   if new['Country']!='TH' or account_for_transaction(new['Transaction'])!='RoadResidualFuel':raise ValueError('Unapproved vintage replacement scope')
   s['records'][idx]=new
 c=json.loads((folder/'FROZEN_UPSTREAM_CONVERSIONS.json').read_text())
 builder=Reconstruction(s,c);builder.zero_scope=Reconstruction(frozen_scope,c)
 result=builder.build()
 result['zero_proof_vintage_scope']='Original immutable UNSD capsule only; never mix the local TH Road overlay into old FEC closures. Evidence remains bounded to that source version.'
 # New official memo files supplement, never overwrite, the frozen capsule.
 # Evidence must compare parent and bio totals with the cached version first.
 resolved={}
 evidence_path=folder/'COMPATIBLE_BLEND_EVIDENCE.json'
 if allow_blend_evidence and evidence_path.exists():
  from reconcile_unsd_blends import reconcile
  factors=Reconstruction(s,c).factors
  for entry in json.loads(evidence_path.read_text())['records']:
   if entry['Status']!='COMPATIBLE_VERIFIED':continue
   dedup=reconcile(entry['parent'],entry['bio'],entry['memo'])
   parent=next(z for z in result['selected_rows'] if z['RowID']==entry['CachedParentRow'])
   bio=next(z for z in result['selected_rows'] if z['RowID']==entry['CachedBioRow'])
   if D(parent['RawValue'])!=D(entry['parent']['Quantity']) or D(bio['RawValue'])!=D(entry['bio']['Quantity']):raise ValueError('New/old parent or bio version conflict')
   old=D(parent['MWh']);new=D(dedup['FossilMass'])*factors[commodity(parent['Commodity'])]*1000000
   parent.update(OriginalMWh=parent['MWh'],MWh=str(new),FossilMass=dedup['FossilMass'],BlendEvidence=dedup,Transformation=dedup['Rule'])
   for a in result['accounts']:
    if parent['RowID'] in a['SourceRows']:
     a['ValueMWh']=str(D(a['ValueMWh'])-old+new)
     a['CarrierBreakdownMWh']['oil']=str(D(a['CarrierBreakdownMWh']['oil'])-old+new)
     a['BlendEvidence']=dedup
   resolved[bio['RowID']]=dedup
 overlap=[]
 for z in result['selected_rows']:
  if z['Commodity'] not in ['Biodiesel','Biogasoline'] or D(z['MWh'])<=0:continue
  if z['RowID'] in resolved:continue
  peers=[p for p in result['selected_rows'] if p['Country']==z['Country'] and p['Account']==z['Account'] and p['Carrier']=='oil' and p['Commodity'].lower() in ['motor gasoline','gas oil/ diesel oil']]
  # Rail uses an aggregate account but selected_rows retain carrier identity.
  if not peers:continue
  overlap.append(dict(Country=z['Country'],Account=z['Account'],BioCommodity=z['Commodity'],BioMWh=z['MWh'],BioSourceRow=z['RowID'],OilSourceRows=[p['RowID'] for p in peers],Need='Same-vintage2019 blended-memo quantities or explicit metadata that petroleum series exclude biofuels',Source='https://unstats.un.org/unsd/energy/meetings/2017a/8.1renewables.pdf'))
  for a in result['accounts']:
   if a['Country']==z['Country'] and a['Account']==z['Account'] and a['Carrier'] in ['oil','biomass','unclassified_fuel']:
    a.update(Status='UNRESOLVED_BIOFUEL_OVERLAP',Classification='UNRESOLVED',Reason='Petroleum/biofuel commodity-series overlap not resolved; memo blended rows missing; raw sum is a candidate, not a qualified disjoint obligation')
 result['biofuel_overlap']=overlap
 result['resolved_blends']=resolved
 # Preserve the source rail parent as accounting; its disjoint carrier children
 # are the only possible physical destinations after an explicit target decision.
 for a in list(result['accounts']):
  if a['Account']!='TransportEmbeddedFuelParent' or not a['SourceRows']:continue
  for fuel,value in a['CarrierBreakdownMWh'].items():
   selected=[r for r in result['selected_rows'] if r['RowID'] in a['SourceRows'] and r['Carrier']==fuel]
   child=dict(a,Account='RailNonElectric',Carrier=fuel,AccountID=a['Country']+':2019:RailNonElectric:'+fuel,ValueMWh=value,CarrierBreakdownMWh={fuel:value},SourceRows=[r['RowID'] for r in selected],ParentAccountID=a['AccountID'])
   result['accounts'].append(child)
  for r in result['selected_rows']:
   if r['RowID'] in a['SourceRows']:r['Account']='RailNonElectric';r['OriginalParentAccount']='TransportEmbeddedFuelParent'
 return result

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--sources',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 result=reconstruct(a.sources);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
 from collections import Counter
 print(json.dumps(dict(accounts=len(result['accounts']),statuses=dict(Counter(r['Status'] for r in result['accounts'])),selected_raw_rows=len(result['selected_rows'])),indent=2))
