"""Non-posting accounting envelopes for compatible, cached UNSD blend pairs.

No midpoint, endpoint or inferred blend quantity is a production input.
"""
from pathlib import Path
from decimal import Decimal as D
import argparse,json,hashlib,xml.etree.ElementTree as ET
from collections import defaultdict
from reconstruct_base_accounts import reconstruct,Reconstruction,commodity,row_id
from residual_account_mapping import build_crosswalk,transaction_name,official_codes

PAIRS={'ZD':('gas oil/ diesel oil','biodiesel','4670','5220','5222'), 'ZG':('motor gasoline','biogasoline','4652','5210','5212')}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def number(v):
 q=D(str(v))
 if not q.is_finite() or q<0:raise ValueError('Quantity/factor missing, negative or nonfinite')
 return q
def bounds(parent,bio,proof,petroleum_factor=None,bio_factor=None):
 out=dict(Status='BOUND_NOT_DERIVABLE_FROM_CURRENT_SOURCE',Posting=False,SourceQualificationChanged=False,ZLower=None,ZUpper=None,LowerUniqueQuantity=None,UpperUniqueQuantity=None,LowerEnergyMWh=None,UpperEnergyMWh=None,NoPointEstimate=True)
 try:
  for field in ['Country','Year','Transaction','Unit','Vintage']:
   if parent.get(field) is None or parent[field]!=bio.get(field):raise ValueError('Incompatible '+field)
  pair=PAIRS.get(proof.get('Memo'))
  if not pair or (parent['CommodityCode'],bio['CommodityCode'])!=pair[2:4]:raise ValueError('Unqualified commodity pair')
  if parent['Unit']!='Metric tons, thousand':raise ValueError('Mass basis not compatible')
  if not proof.get('InclusionVerified') or not proof.get('VersionReconciled'):raise ValueError('Inclusion/version not verified')
  if not parent.get('SourceRow') or not bio.get('SourceRow') or parent['SourceRow']==bio['SourceRow']:raise ValueError('Source identities missing/duplicated')
  p,b=number(parent['Quantity']),number(bio['Quantity']);z=min(p,b)
  out.update(Status='DERIVED_ACCOUNTING_ENVELOPE_ANALYSIS_ONLY',ZLower='0',ZUpper=str(z),LowerUniqueQuantity=str(max(p,b)),UpperUniqueQuantity=str(p+b),Formula='Unique=P+B-Z; 0<=Z<=min(P,B)',EnergyStatus='ENERGY_BOUND_NOT_DERIVABLE_FROM_CURRENT_SOURCE')
 except (ValueError,KeyError,ArithmeticError) as e:out['CannotDerive']=str(e);return out
 try:
  hp,hb=number(petroleum_factor),number(bio_factor)
  if hp<=0 or hb<=0:raise ValueError('Heating factor must be qualified positive')
  out.update(LowerEnergyMWh=str((p-z)*hp+b*hb),UpperEnergyMWh=str(p*hp+b*hb),EnergyStatus='DERIVED_WITH_FROZEN_COMMODITY_NCV',EnergyFormula='E(Z)=(P-Z)*h_petroleum+B*h_bio; bio total counted once, mixed parent never receives a second full-energy posting')
 except (ValueError,ArithmeticError) as e:out['CannotDeriveEnergy']=str(e)
 return out
def observations(path):
 rows=[]
 for s in ET.parse(path).getroot().iter():
  if s.tag.split('}')[-1]!='Series':continue
  attrs={}
  for child in s:
   if child.tag.split('}')[-1] in ['SeriesKey','Attributes']:
    attrs.update({v.attrib['id']:v.attrib['value'] for v in child})
  for o in s:
   if o.tag.split('}')[-1]!='Obs':continue
   r=dict(attrs)
   for v in o:
    tag=v.tag.split('}')[-1]
    if tag=='ObsDimension':r['Year']=v.attrib['value']
    elif tag=='ObsValue':r['Quantity']=v.attrib['value']
    elif tag=='Attributes':r.update({x.attrib['id']:x.attrib['value'] for x in v})
   rows.append(r)
 return rows
def analyse(repo,output):
 s=repo/'research_inputs/assembly_v1/sources';regpath=s.parent/'registry.json';reg=read(regpath);capsule=read(s/'UNSD_2019_SOURCE_CAPSULE.json');conversion=read(s/'FROZEN_UPSTREAM_CONVERSIONS.json');b=Reconstruction(capsule,conversion);raw={row_id(r):r for r in b.rows}
 receipt=read(repo/'research/04_model_assembly/gate4/UNSD_TARGETED_RETRIEVAL_RECEIPT.json');result=reconstruct(s);cross=build_crosswalk(result,s,reg,receipt);lookup={r['InputID']:r for r in reg['records']}
 definitions=s/'unsd_targeted/questionnaire_guidelines.pdf';assert sha(definitions)==read(str(definitions)+'.receipt.json')['sha256']
 codes=official_codes(s/'unsd_targeted/DSD_Energy.xml');rows=[];cache={};seen=set();dependencies=defaultdict(list)
 for q in cross:
  key=q['RequestID'];assert key not in seen;seen.add(key)
  product,bproduct,pc,bc,mc=PAIRS[q['MemoCommodity']];p=raw[q['ParentRows'][0]];bio=raw[q['BioSourceRow']];xml=s/'unsd_targeted'/q['PriorReceiptFile'];h=sha(xml);assert h==q['PriorReceiptSHA256']==read(str(xml)+'.receipt.json')['sha256']
  if xml not in cache:cache[xml]=observations(xml)
  current=[];reason=[]
  for code,r in [(pc,p),(bc,bio)]:
   found=[x for x in cache[xml] if x['REF_AREA']==receipt['plan']['countries'][q['Country']] and x['Year']=='2019' and x['TRANSACTION']==q['Transaction'] and x['COMMODITY']==code]
   if len(found)!=1:reason.append('Cached coherent response missing/duplicates '+code);continue
   z=found[0];current.append(z)
   if z['UNIT_MEASURE']!='TN' or z.get('UNIT_MULT')!='3' or r['Unit']!='Metric tons,  thousand':reason.append('Unit conflict '+code)
   if number(z['Quantity'])!=number(r['Quantity']):reason.append('Version quantity conflict '+code)
   if z.get('OBS_STATUS')!='A' or r['Quantity Footnotes']:reason.append('Unresolved status/footnotes '+code)
   if r['Country']!=q['Country'] or r['Year']!='2019' or transaction_name(r['Transaction'])!=transaction_name(codes['CL_TRANSACTION_NRG'][q['Transaction']]):reason.append('Source country/year/transaction conflict '+code)
  if len(q['ParentRows'])!=1 or commodity(p['Commodity'])!=product or commodity(bio['Commodity'])!=bproduct:reason.append('Wrong pair or nonunique parent')
  prep=lambda r,code:dict(Country=r['Country'],Year=int(r['Year']),Transaction=q['Transaction'],Unit='Metric tons, thousand',Vintage=h,CommodityCode=code,Quantity=r['Quantity'],SourceRow=row_id(r))
  proof=dict(Memo=q['MemoCommodity'],InclusionVerified=True,VersionReconciled=not reason,DefinitionSource=str(definitions.relative_to(repo)),DefinitionSHA256=sha(definitions),DefinitionPages=[10,16] if mc=='5212' else [11,16,17],DefinitionMeaning='ZG/ZD is the blended subset included in MO/DL and in AL/BD totals; no assumption about its realised share',DSDSHA256=sha(s/'unsd_targeted/DSD_Energy.xml'),OfficialMemoName=codes['CL_COMMODITY_NRG'][mc],SameResponseSHA256=h,SameResponseRows=current,OldParentAndBioMatchedIndividually=not reason,RevisionRule='Separate frozen source files match the same already-cached official response at exact values/scope/units/status; download date equality not assumed')
  hp=b.factors[product]*1000000;hb=b.factors[bproduct]*1000000
  envelope=bounds(prep(p,pc),prep(bio,bc),proof,hp,hb)
  methods=[]
  for ident in q['AffectedTargetAccounts']:
   r=lookup[ident];m=dict(InputID=ident,MethodID=r['MethodID'],DecisionReference=r.get('DecisionReference'),GrowthNumerator=r.get('GrowthNumerator'),GrowthDenominator=r.get('GrowthDenominator'),RegistryTransformationText=r.get('Transformation'))
   if r['MethodID']=='ASSEMBLY_V1_RAIL_CONSTANT_2019':
    d=read(s/'GATE4_CONSOLIDATED_BASELINE_DECISIONS.json');assert d['ApprovalStatus']=='HUMAN_ACCEPTED' and d['Methods']['TransportEmbeddedFuelParent']==r['MethodID']
    m.update(ApprovedRatio='1',AuthoritativeSource='sources/GATE4_CONSOLIDATED_BASELINE_DECISIONS.json',RegistryTextConflict='Old transport-growth Transformation/Candidate fields remain in this PENDING account; not used by this analysis or production; approved method is constant2019')
   elif m['GrowthNumerator'] is not None and m['GrowthDenominator'] is not None:m['ApprovedRatio']=str(number(m['GrowthNumerator'])/number(m['GrowthDenominator']))
   else:m['ApprovedRatio']=None
   methods.append(m);dependencies[ident].append(key)
  rows.append(dict(UncertaintyID=key,Country=q['Country'],Year=2019,TransactionCode=q['Transaction'],TransactionName=q['OfficialTransaction'],Memo=q['MemoCommodity'],ParentCommodity=p['Commodity'],BioCommodity=bio['Commodity'],P=p['Quantity'],B=bio['Quantity'],RawUnit=p['Unit'],PSourceRow=row_id(p),BSourceRow=row_id(bio),PSourceFile=p['SourceFile'],BSourceFile=bio['SourceFile'],PVersion=p['SourceSHA256'],BVersion=bio['SourceSHA256'],CompatibleCachedVersion=h,CompatibilityProblems=reason,Proof=proof,PetroleumNCVMWhPerKton=str(hp),BioNCVMWhPerKton=str(hb),ConversionSource='research_inputs/assembly_v1/sources/FROZEN_UPSTREAM_CONVERSIONS.json',ConversionSHA256=sha(s/'FROZEN_UPSTREAM_CONVERSIONS.json'),EnergyScope='This2019 commodity pair only, using accepted rounded frozen NCV; no heat-value uncertainty envelope or complete country/sector total',TargetMethods=methods,Affected2050Accounts=q['AffectedTargetAccounts'],ProductionInputsChanged=False,ApprovalStatus='ANALYSIS_ONLY_NO_BASELINE_POINT_ACCEPTED',**envelope))
 assert set(dependencies)=={r['InputID'] for r in reg['records'] if r['Year']==2050 and r.get('BaseStatus')=='UNRESOLVED_BIOFUEL_OVERLAP' and r['InputID'] in {i for x in cross for i in x['AffectedTargetAccounts']}}
 pins=[regpath,s/'UNSD_2019_SOURCE_CAPSULE.json',s/'FROZEN_UPSTREAM_CONVERSIONS.json',definitions,s/'unsd_targeted/DSD_Energy.xml',s/'GATE4_CONSOLIDATED_BASELINE_DECISIONS.json',*cache]
 save(output,dict(schema='nonposting-blend-uncertainty-envelope-v1',Method='Inclusion-relationship accounting interval, not confidence interval, reported range or scenario forecast',records=rows,source_pins={str(p.relative_to(repo)):sha(p) for p in pins},account_to_uncertainty_ids=dict(dependencies),independent_source_variables=len(rows),affected_target_accounts=len(dependencies),reported_ranges=False,midpoints_or_endpoints_accepted=False,production_changed=False,new_queries_executed=0,solver_runs=0,range_status_counts={k:sum(r['Status']==k for r in rows) for k in {r['Status'] for r in rows}},DependencyRule='One Z per exact country/year/transaction/commodity memo. Repeat account references do not create independent errors. PH road gasoline and diesel are separate pairs sharing the same two target accounts; no stochastic independence assumed.'))
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=analyse(**vars(a));print(json.dumps({r['UncertaintyID']:[r['Status'],r['LowerUniqueQuantity'],r['UpperUniqueQuantity']] for r in rows},indent=2))
