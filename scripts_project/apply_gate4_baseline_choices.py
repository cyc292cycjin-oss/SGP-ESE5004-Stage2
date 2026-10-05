"""Deterministically apply the current Thailand and rail/NEC human choices.

Raw capsules/XML remain immutable; the local-vintage overlay and accounting
parent replacements retain old identities and explicit new decision references.
"""
from pathlib import Path
from decimal import Decimal as D,localcontext
import argparse,json,hashlib,copy,subprocess
from reconstruct_base_accounts import reconstruct,row_id,commodity,account_for_transaction
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def apply(repo,report):
 f=repo/'research_inputs/assembly_v1';s=f/'sources';d=read(s/'GATE4_CONSOLIDATED_BASELINE_DECISIONS.json');ref=d['DecisionReference'];registry=read(f/'registry.json')
 original=json.loads(subprocess.check_output(['git','show',d['PriorHead']+':research_inputs/assembly_v1/registry.json'],cwd=repo))
 if d['ApprovalStatus']!='HUMAN_ACCEPTED':raise ValueError('Missing current decision')
 old=read(s/'UNSD_2019_SOURCE_CAPSULE.json')['records'];obs=read(s/'unsd_targeted/observations.json')
 names={'MO':('4652','Motor Gasoline'),'DL':('4670','Gas Oil/ Diesel Oil'),'AL':('5210','Biogasoline'),'BD':('5220','Biodiesel'),'ZG':('5212','Of which: biogasoline'),'ZD':('5222','Of which: biodiesel')}
 new={k:next(r for r in obs if r['Country']=='TH' and r['TRANSACTION']=='1221' and r['COMMODITY']==code) for k,(code,_) in names.items()}
 assert len({r['SourceSHA256'] for r in new.values()})==1
 replacements=[];ids={}
 for code in ['MO','DL','AL','BD']:
  name=names[code][1];before=[r for r in old if r['Country']=='TH' and commodity(r['Commodity'])==commodity(name) and account_for_transaction(r['Transaction'])=='RoadResidualFuel']
  assert len(before)==1
  prior=before[0];o=new[code];raw=dict(prior,Quantity=o['Quantity'],SourceFile=o['SourceFile'],SourceSHA256=o['SourceSHA256'],PhysicalLine=o['COMMODITY']+':'+o['TRANSACTION'])
  raw['Quantity Footnotes']=o['OBS_STATUS'];ids[code]=row_id(raw)
  replacements.append(dict(OldRowID=row_id(prior),OldRawRow=prior,NewRawRow=raw,OfficialObservation=o))
 save(s/'TH_ROAD_LOCAL_VINTAGE_APPLIED.json',dict(ApprovalStatus='HUMAN_ACCEPTED',DecisionReference=ref+'#C',MethodID=d['Methods']['thailand'],replacements=replacements,memo={k:new[k] for k in ['ZG','ZD']},original_files_preserved=True))
 blends=read(s/'COMPATIBLE_BLEND_EVIDENCE.json');blends['records']=[r for r in blends['records'] if r['parent']['Country']!='TH']
 for parent,bio,memo in [('MO','AL','ZG'),('DL','BD','ZD')]:
  def part(code):
   o=new[code];return dict(Country='TH',Year=2019,Transaction='1221',Unit='Metric tons,  thousand',Vintage=o['SourceSHA256'],CommodityCode=code,Quantity=o['Quantity'],SourceRow=o['SourceSHA256']+':'+o['COMMODITY']+':1221',Footnote=o['OBS_STATUS'],InclusionVerified=True,InclusionSource='Cached official questionnaire and verified DSD commodity memo relationship; whole coherent bundle accepted this round')
  blends['records'].append(dict(Status='COMPATIBLE_VERIFIED',parent=part(parent),bio=part(bio),memo=part(memo),CachedParentRow=ids[parent],CachedBioRow=ids[bio],Qualification=d['Methods']['thailand'],DecisionReference=ref+'#C'))
 save(s/'COMPATIBLE_BLEND_EVIDENCE.json',blends)
 base=reconstruct(s);save(s/'BASE_RECONSTRUCTION.json',base);bs=sha(s/'BASE_RECONSTRUCTION.json');bm={r['AccountID']:r for r in base['accounts']};records=registry['records']
 def link(r,b):
  r.update(Source='sources/BASE_RECONSTRUCTION.json',SourceSHA256=bs,Locator=b['AccountID'],BaseValueMWh=b['ValueMWh'],BaseStatus=b['Status'],BaseSourceRows=b['SourceRows'],CarrierBreakdownMWh=b['CarrierBreakdownMWh'],EnergyBasis=b['EnergyBasis'])
  if r.get('Classification')=='SOURCE_SUPPORTED_NOT_APPLICABLE':
   if set(filter(None,r.get('ZeroEvidence','').split(';')))!=set(b['ZeroEvidence']):raise ValueError('Prior source exclusion evidence changed: '+r['InputID'])
   r['ZeroEvidence']=';'.join(b['ZeroEvidence'])
 def accept(r,b,method,value,reference):
  link(r,b);r.update(Value=str(value),RawValue=b['ValueMWh'],RawUnit='MWh/year derived from pinned raw rows',Unit='MWh/year',SourceYear=2019,AssemblyStatus='ASSEMBLY_V1_ACCEPTED',HumanAcceptance='CURRENT_EXPLICIT_BASELINE_METHOD_SOURCE_QUALIFIED',SourceQualified=True,NumericStatus='NUMERIC_INPUT_READY',Classification='REQUIRED_PHYSICAL',MethodID=method,DecisionReference=reference,ProjectionEvidence='sources/GATE4_CONSOLIDATED_BASELINE_DECISIONS.json',Transformation='Qualified2019 * (374.9/145.2)' if method==d['Methods']['thailand'] else 'Qualified exclusive2019 source account held constant in2050',Reason='New human baseline assumption; not forecast or observed2050 fact',Required=True,TargetReady=False,CandidateValue=None,CandidateUnit='',SensitivityRequired=True)
 # Rebind all source hashes, without changing previously accepted quantities.
 for r in records:
  if r['Year']==2050 and r['Kind']=='DEMAND' and r.get('Source')=='sources/BASE_RECONSTRUCTION.json':link(r,bm[r['Locator']])
  if r['Year']==2050 and r['Country']=='TH' and r['Account']=='RoadResidualFuel' and r['Carrier'] in ['oil','biomass']:
   b=bm[r['Locator']];assert b['Status']=='NUMERIC_INPUT_READY'
   with localcontext() as ctx:ctx.prec=40;value=D(b['ValueMWh'])*D('374.9')/D('145.2')
   # Quantity growth method remains the existing road method; local vintage decision is separate.
   accept(r,b,d['Methods']['thailand'],value,ref+'#C');r['VintageMethodID']=r['MethodID'];r['MethodID']='ASSEMBLY_V1_ROAD_NON_ELECTRIC_TRANSPORT_GROWTH_PROXY'
 template=next(r for r in records if r['Year']==2050 and r['Account']=='RoadResidualFuel' and r['AssemblyStatus']=='ASSEMBLY_V1_ACCEPTED')
 existing={r['InputID']:r for r in records};new_ids=[]
 for b in base['accounts']:
  if b['Account'] not in ['RailNonElectric','TransportNEC','OtherNEC']:continue
  group=b['Account'];country=b['Country'];sector='OtherNEC' if group=='OtherNEC' else 'Transport';rid=f"{country}:2050:{sector}:{group}:{b['Carrier']}"
  parent=next((r for r in records if r['Year']==2050 and r['Country']==country and r['Account']=='TransportEmbeddedFuelParent'),None) if group=='RailNonElectric' else None
  r=existing.get(rid,dict(template,InputID=rid,Country=country,Sector=sector,Account=group,Carrier=b['Carrier'],CountryScope=country,ParentAccount=parent['InputID'] if parent else '',Value=None,Representation='EXPLICIT',HumanAcceptance='METHOD_ACCEPTED_BASE_QUALIFICATION_PENDING'))
  for key in ['GrowthNumerator','GrowthDenominator','GrowthRatioBaseYear','VintageMethodID']:r.pop(key,None)
  key='TransportEmbeddedFuelParent' if group=='RailNonElectric' else group;method=d['Methods'][key]
  link(r,b);r.update(MethodID=method,DecisionReference=ref+'#D',ProjectionEvidence='sources/GATE4_CONSOLIDATED_BASELINE_DECISIONS.json',SourceUseGroup=group,Required=True)
  if b['Status']=='NUMERIC_INPUT_READY':accept(r,b,method,D(b['ValueMWh']),ref+'#D')
  else:r.update(Value=None,AssemblyStatus='PENDING',SourceQualified=False,NumericStatus='UNRESOLVED',Classification='UNRESOLVED',Reason=b['Reason'],BaseStatus=b['Status'])
  if rid not in existing:records.append(r);existing[rid]=r;new_ids.append(rid)
  if parent:
   parent.update(Kind='ACCOUNTING',Required=False,Value=None,Representation='APPROVED_CARRIER_SPLIT',MethodID=method,DecisionReference=ref+'#D',Reason='Source rail parent retained as accounting only; exclusive carrier children are the physical obligations',AssemblyStatus='PENDING')
   parent.setdefault('PhysicalChildren',[])
   if rid not in parent['PhysicalChildren']:parent['PhysicalChildren'].append(rid)
 # Each known NEC source row is represented once, never also posted as a parent.
 for oldrow in registry.get('known_unallocated_base_accounts',[]):
  owners=[r for r in records if r['Year']==2050 and r['Kind']=='DEMAND' and oldrow['SourceRow'] in r.get('BaseSourceRows',[]) and r['AssemblyStatus']=='ASSEMBLY_V1_ACCEPTED']
  if len(owners)>1:raise ValueError('Duplicate known NEC source ownership')
  if owners:oldrow.update(Target2050Status='MATERIALISED_EXCLUSIVE_SOURCE_USE',TargetInputID=owners[0]['InputID'],DecisionReference=ref+'#D')
 save(f/'registry.json',registry)
 pin=read(f/'manifest.json')
 for rel in ['registry.json','sources/BASE_RECONSTRUCTION.json','sources/COMPATIBLE_BLEND_EVIDENCE.json','sources/TH_ROAD_LOCAL_VINTAGE_APPLIED.json','sources/GATE4_CONSOLIDATED_BASELINE_DECISIONS.json']:pin['files'][rel]=sha(f/rel)
 save(f/'manifest.json',pin)
 oldaccepted={r['InputID']:r['Value'] for r in original['records'] if r['Year']==2050 and r['Kind']=='DEMAND' and r['AssemblyStatus']=='ASSEMBLY_V1_ACCEPTED'}
 for rid,value in oldaccepted.items():assert existing[rid]['Value']==value,rid
 out=dict(DecisionReference=ref,prior_accepted_values_preserved=len(oldaccepted),accepted_count=sum(r['Year']==2050 and r['Kind']=='DEMAND' and r['AssemblyStatus']=='ASSEMBLY_V1_ACCEPTED' for r in records),new_account_ids=new_ids,rail_nec=[dict(InputID=r['InputID'],Value=r['Value'],Status=r['AssemblyStatus'],BaseSourceRows=r['BaseSourceRows']) for r in records if r['Year']==2050 and r['Account'] in ['RailNonElectric','TransportNEC','OtherNEC']],thailand=[r for r in records if r['Year']==2050 and r['Country']=='TH' and r['Account']=='RoadResidualFuel'],solver_runs=0)
 report.parent.mkdir(parents=True,exist_ok=True);save(report,out);return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--report',type=Path,required=True);a=p.parse_args();x=apply(a.repo,a.report);print(json.dumps({k:v for k,v in x.items() if k not in ['thailand','rail_nec','new_account_ids']}))
