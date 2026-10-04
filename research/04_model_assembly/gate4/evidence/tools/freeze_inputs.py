"""Freeze only source-qualified values. Never reinterpret base year as 2050."""
from pathlib import Path
import sys,csv,json,hashlib,io,decimal,collections,shutil
W=Path(__file__).resolve().parent;E=W/'evidence';S=W/'stage';R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');N=W.parents[1]
sys.path.insert(0,str(R/'scripts_project'))
from demand_sources import load_sources
from carbon_architecture import TRAJECTORY
sources=load_sources(R,verify_originals=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return list(csv.DictReader(io.StringIO(p.read_text(encoding='utf-8-sig'))))
original=read(R/'research/04_model_assembly/gate2/RESEARCH_DEMAND_LEDGER.csv')
records=[];accepted=[]
for r in original:
 if r['Year'] not in ('2019','2050') or r['Posting']!='true':continue
 q=dict(InputID=r['RowID'],Kind='DEMAND',Country=r['Country'],Year=int(r['Year']),Sector=r['Sector'],Account=r['Subsector'],Carrier=r['Carrier'],RawValue=r['RawValue'] or None,RawUnit=r['RawUnit'],Value=r['ConvertedMWh'] or None,Unit='MWh/year',SourceYear=int(r['SourceYear']),Source=r['Source'],SourceSHA256=r['SourceSHA256'],Locator=r['SourceLocator'],Transformation=r['Transformation'],AssemblyStatus='PENDING',HumanAcceptance=r['HumanAcceptance'],Gate2Status=r['Status'],SourceQualified=False,TargetReady=False,Required=True,Reason=r['Notes'],ParentAccount=r['ParentAccount'],Representation=r['Representation'],CurrencyYear=None,EnergyBasis='FINAL_ENERGY_AS_REPORTED' if r['Carrier']=='electricity' else 'PENDING_CALORIFIC_BASIS',Availability=None,CountryScope=r['Country'])
 if r['Year']=='2019' and r['Subsector']=='Astar':
  source=[x for x in sources['electricity']['records'] if x['Country']==r['Country'] and x['Commodity - Transaction']=='Electricity - Final energy consumption']
  assert len(source)==1;raw=source[0];assert raw['Year']=='2019' and raw['Unit']=='Kilowatt-hours, million'
  val=decimal.Decimal(raw['Quantity'])*1000
  # Gate2 wrote decimal MWh through float formatting. Keep the exact raw
  # decimal conversion and verify the established 1e-6 MWh tolerance.
  delta=val-decimal.Decimal(r['ConvertedMWh']);assert abs(delta)<=decimal.Decimal('0.000001'),(r['Country'],val,r['ConvertedMWh'])
  q['Gate2ConversionDeltaMWh']=str(delta)
  q.update(AssemblyStatus='ASSEMBLY_V1_ACCEPTED',SourceQualified=True,Value=str(val),Reason='2019 national end-user final electricity parent; no loss/generation adjustment or uncertified child subtraction; base-year anchor only, NOT a 2050 forecast',HumanAcceptance='GATE4_RULE_BASED_ASSEMBLY_ACCEPTANCE_NOT_HUMAN_ACCEPTED')
  accepted.append(q)
 if r['Year']=='2050':q['Reason']='TARGET_YEAR_UNRESOLVED; '+q['Reason']
 records.append(q)
assert len(accepted)==11,[(r['Account'],r['Year']) for r in records[:12]]
# The user's attachment identity is pinned; no numeric inference from its title.
request=Path('/mnt/c/Users/20122/.codex/attachments/b702ba33-d97f-49d7-8717-51bd1ed0c386/已粘贴的文本.txt')
request_sha=sha(request)
common=dict(Country='ASEAN',Year=2050,RawValue=None,RawUnit='',Value=None,Unit='',SourceYear=2026,Source=str(request),SourceSHA256=request_sha,Locator='Gate4 user instruction',Transformation='Explicit instruction applied to existing architecture',AssemblyStatus='ASSEMBLY_V1_ACCEPTED',HumanAcceptance='EXPLICIT_GATE4_SCOPE',Gate2Status='NOT_APPLICABLE',SourceQualified=True,TargetReady=True,Required=False,Reason='',ParentAccount='',Representation='CONTROL',CurrencyYear=None,EnergyBasis='NOT_APPLICABLE',Availability=None,CountryScope='ASEAN')
for year,value in TRAJECTORY.items():
 records.append(dict(common,InputID=f'PowerPolicyBudget:{year}',Kind='POLICY',Year=year,Sector='Power',Account='PolicyCO2_Power',Carrier='co2',RawValue=str(value/1e6),RawUnit='MtCO2/year',Value=str(int(value)),Unit='tCO2/year',SourceYear=year,Locator='Gate4 section31; Phase3 CARBON_SCOPE_FREEZE; Gate3 TRAJECTORY',Transformation='Mt * 1e6; baseline enable remains false',TargetReady=year==2050,Reason='Existing accepted trajectory; no full-system cap'))
for carrier,account,availability,reason in [('co2','GeologicalStorageAvailability','OFF_NO_ACCEPTED_CAPACITY','No geological asset; physical capacity remains UNKNOWN, never infinite and not a claim that natural potential is zero'),('solid biomass','UnallocatedBiomassResource','UNAVAILABLE_UNSUPPORTED','No 360 TWh regional pool replicated or free biomass imports; positive fuel obligations remain separately required')]:
 records.append(dict(common,InputID=account,Kind='BOUNDARY',Sector='Supply',Account=account,Carrier=carrier,Availability=availability,Locator='Gate4 sections16–17',Reason=reason))
for c in sorted({r['Country'] for r in accepted}):
 for sector in ['Residential','Services']:
  records.append(dict(common,InputID=f'{c}:2050:{sector}:representation',Kind='BOUNDARY',Country=c,CountryScope=c,Sector='Buildings',Account=sector,Carrier='mixed',Representation='EMBEDDED_ELECTRICITY_FIXED_FUEL',Locator='Gate4 section8 + Phase3 Buildings freeze',Reason='Cooling embedded; cooking accounting-only; no accepted explicit heat service, no BDEW/default district-heat/stock Load; fuel quantities remain required'))
cost=json.loads((E/'COST_CANDIDATES_2050.json').read_text())
for r in cost['records']:
 if not (r['technology']=='electrolysis' or r['parameter']=='fuel'):continue
 q=dict(common,InputID='Cost2050:'+r['technology']+':'+r['parameter'],Kind='TECHNOLOGY' if r['parameter']!='fuel' else 'EXTERNAL_SUPPLY',Sector='Supply',Account=r['parameter'],Carrier=r['technology'],RawValue=r['value'],RawUnit=r['unit'],Value=r['value'],Unit=r['unit'],SourceYear=2050,Source=cost['source'],SourceSHA256=cost['sha256'],Locator=r['technology']+'/'+r['parameter']+'; upstream v0.13.2 SHA '+cost['git_version'],Transformation='Frozen output identity; no re-inflation or unit change',CurrencyYear=2020 if r['parameter'] in ('fuel','investment') else None,EnergyBasis='LHV_H2_OUTPUT_PER_ELECTRIC_INPUT' if r['parameter']=='efficiency' else 'PENDING' if r['parameter']=='fuel' else 'NOT_APPLICABLE',AssemblyStatus='PENDING',SourceQualified=False,TargetReady=False,Required=True,HumanAcceptance='NOT_HUMAN_ACCEPTED',Reason='Public/private source/basis or country supply availability unresolved',Availability='PENDING_COUNTRY_CAPACITY_AND_ANNUAL_CAP' if r['parameter']=='fuel' else None)
 if r['technology']=='electrolysis':
  reason='DEA sheet86 lineage previously recovered, same frozen cost output, compatible existing electrolyser; no new technology or numeric replacement'
  if r['parameter']=='investment':reason='Gate4 priority3 frozen upstream technology-cost assumption, 1000 EUR2020/kW_e from public v0.13.2 output/manual override; private-communication origin not independently validated, retained as disclosed upstream assumption, not empirical confirmation'
  q.update(AssemblyStatus='ASSEMBLY_V1_ACCEPTED',SourceQualified=True,TargetReady=True,HumanAcceptance='GATE4_RULE_BASED_ASSEMBLY_ACCEPTANCE_NOT_HUMAN_ACCEPTED',Reason=reason)
 records.append(q)
folder=S/'research_inputs/assembly_v1';folder.mkdir(parents=True,exist_ok=True)
body=dict(schema='assembly-v1-freeze-1',base_year=2019,target_year=2050,status='PARTIAL',acceptance_kind='ASSEMBLY_V1_ACCEPTED_NOT_HUMAN_ACCEPTED',gate2_ledger_sha256=sha(R/'research/04_model_assembly/gate2/RESEARCH_DEMAND_LEDGER.csv'),records=records)
(folder/'registry.json').write_text(json.dumps(body,ensure_ascii=False,indent=2))
sources_out=folder/'sources';sources_out.mkdir(exist_ok=True)
for name in ['electricity.json','energy_cache.json','industry_cache.json','bunker_review.json']:
 shutil.copyfile(R/'research_inputs/demand/sources'/name,sources_out/name)
shutil.copyfile(request,sources_out/'GATE4_REQUEST.txt')
shutil.copyfile(E/'COST_CANDIDATES_2050.json',sources_out/'COST_CANDIDATES_2050.json')
(folder/'README.md').write_text('''# Assembly V1 partial input freeze\n\nASSEMBLY_V1_ACCEPTED is the Gate4 rule-based status, not HUMAN_ACCEPTED. Gate2 tables are unchanged. Eleven 2019 A* anchors are accepted for 2019 only; they are not copied/grown to 2050. 2050 demand remains blocked. The six Power budgets and no-geological-storage/unsupported-biomass availability controls preserve user instructions, not evidence of zero physical potential. Four existing electrolyser parameters retain the frozen upstream values; its investment is a disclosed upstream assumption with an unverified private-communication origin. External fuel basis/availability remain pending.\n\nregistry.json is canonical. manifest.json pins its bytes and source capsules. No data loader may infer missing numeric values as zero or future growth as one. check_assembly_inputs.py evaluates the requested year and returns BLOCKED before network construction.\n''')
(folder/'.gitignore').write_text('!*.json\n!*.txt\n')
(folder/'.gitattributes').write_text('* -text\n')
manifest=dict(schema='assembly-v1-sources-1',files={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'})
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2))
(E/'ASSEMBLY_FREEZE_COUNTS.json').write_text(json.dumps(dict(records=len(records),by_status=dict(collections.Counter(r['AssemblyStatus'] for r in records)),accepted_baseyear_parents=len(accepted),target_demand_accepted=sum(r['Kind']=='DEMAND' and r['Year']==2050 and r['AssemblyStatus']=='ASSEMBLY_V1_ACCEPTED' for r in records)),indent=2))
print((E/'ASSEMBLY_FREEZE_COUNTS.json').read_text())
