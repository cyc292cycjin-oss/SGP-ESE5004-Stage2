"""Deterministic Gate4 closure evidence. JSON is canonical; CSV export is separate."""
from pathlib import Path
from decimal import Decimal as D, getcontext
import json,hashlib,shutil,collections,csv,io
getcontext().prec=40
W=Path(__file__).resolve().parent; N=W.parents[1]; S=W/'stage'; E=W/'evidence'
F=S/'research_inputs/assembly_v1'; G=S/'research/04_model_assembly/gate4'; GE=G/'evidence/resume'
GE.mkdir(parents=True,exist_ok=True); (W/'build').mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def text(p,x):p.write_text(x.strip()+'\n',encoding='utf-8')
def fmt(x):return format(x,'f')
old=json.loads((N/'work/phase4_gate4/stage/research_inputs/assembly_v1/registry.json').read_text())
records=old['records']; decisions=json.loads((W/'resume_decisions.json').read_text())
shutil.copyfile(W/'resume_decisions.json',F/'sources/GATE4_RESUME_DECISIONS.json')
req=Path('C:/Users/20122/.codex/attachments/43ba193e-5db6-4d26-b87e-e68be6b98cf0/已粘贴的文本.txt')
shutil.copyfile(req,F/'sources/GATE4_RESUME_REQUEST.txt')
decision_sha=sha(F/'sources/GATE4_RESUME_DECISIONS.json')
request_sha=sha(F/'sources/GATE4_RESUME_REQUEST.txt')
aeo=N/'research/02_sector_coupling/buildings_heat_alignment/data/raw/buildings/aeo8.pdf'
aeo_sha=sha(aeo)
url='https://www.aseanenergy.org/publications/the-8th-asean-energy-outlook/'
sources=dict(scenario='BAS',coverage='ASEAN10; TL excluded from regional totals',pdf_sha256=aeo_sha,official_landing=url,source_file=str(aeo),values=[
 dict(id='Astar2050',value='225.0',unit='Mtoe',year=2050,source='Appendix C.2, printed181/PDF183; Electricity, BAS2050',definition='Final electricity; never generation'),
 dict(id='ResidentialGrowth',base='63.0',target='68.2',base_year=2022,year=2050,unit='Mtoe',source='Appendix C.3 printed182/PDF184'),
 dict(id='ServicesGrowth',base='29.5',target='75.9',base_year=2022,year=2050,unit='Mtoe',source='Appendix C.3 Commercial printed182/PDF184'),
 dict(id='IndustryGrowth',base='185.6',target='561.0',base_year=2022,year=2050,unit='Mtoe',source='Appendix C.3 printed182/PDF184'),
 dict(id='AgricultureOtherGrowth',base='8.8',target='27.8',base_year=2022,year=2050,unit='Mtoe',source='Appendix C.3 printed182/PDF184',scope_warning='Agriculture and Others, not pure Agriculture; non-energy uses in source boundary'),
 dict(id='Transport2050',value='374.9',year=2050,unit='Mtoe',source='3.1.2 printed63/PDF65; Appendix C.3 printed182/PDF184'),
 dict(id='RoadProportionApprox',value='0.935',unit='fraction',year=None,source='3.1.2 printed64/PDF66 text adjacent ATS Figure3.8',scope_warning='Human approximation applied to BAS, not an independently resolved BAS road table')])
dump(F/'sources/AEO8_BAS_SOURCE_VALUES.json',sources)
shutil.copyfile(E/'BUNKER_BASE_VERIFICATION.json',F/'sources/BUNKER_BASE_VERIFICATION.json')
aeo_capsule_sha=sha(F/'sources/AEO8_BAS_SOURCE_VALUES.json')
proof=json.loads((E/'BUNKER_BASE_VERIFICATION.json').read_text())
bproof={(x['country'],x['account']):x for x in proof['records']}
energy=json.loads((F/'sources/energy_cache.json').read_text())
energy_by={x['Country']:x for x in energy['records']}
base={(x['Country'],x['Account'],x['Carrier']):x for x in records if x['Kind']=='DEMAND' and x['Year']==2019}
countries=sorted({x['Country'] for x in records if x['Kind']=='DEMAND'})
c10=[c for c in countries if c!='TL']
astar_base={c:D(base[c,'Astar','electricity']['Value']) for c in countries}
astar_sum=sum(astar_base[c] for c in c10)
road_base={c:D(energy_by[c]['total road']) for c in countries}
road_sum=sum(road_base[c] for c in c10)
road_parent=D('374.9')*D('0.935'); assert road_parent==D('350.5315')
unit=decisions['Mtoe_to_TWh']['value']
factor=D(unit)*1000000 if unit is not None else None
growth={'ResidentialFuel':('ResidentialGrowth','63.0','68.2'),'ServicesFuel':('ServicesGrowth','29.5','75.9'),'IndustryFinalEnergy':('IndustryGrowth','185.6','561.0'),'AgricultureFinalEnergy':('AgricultureOtherGrowth','8.8','27.8')}
methods=[]
def method(mid,sector,carrier,source2050,basesource,formula,cs,fallback,materiality,status,loc):
 methods.append(dict(MethodID=mid,Sector=sector,Carrier=carrier,Source2050=source2050,BaseSource2019=basesource,Formula=formula,Countries=cs,Fallback=fallback,Materiality=materiality,Status=status,SourceLocation=loc))
method('AEO8_BAS_ASTAR_2050','Electricity','electricity','225.0 Mtoe AEO8 BAS','Verified UNSD2019 Astar','225.0 * Astar_c2019 / sum_ASEAN10 Astar2019','ASEAN10','NO','MATERIAL','METHOD_ACCEPTED; '+decisions['Mtoe_to_TWh']['status'],'Appendix C.2 printed181/PDF183')
method('ASSEMBLY_V1_TL_REGIONAL_GROWTH_FALLBACK','Electricity','electricity','ASEAN10 Astar growth','Verified TL2019 Astar','TL2019 * (225.0 Mtoe in MWh / sum_ASEAN10 Astar2019)','TL','Human authorized regional-growth assumption','MATERIAL','METHOD_ACCEPTED; '+decisions['Mtoe_to_TWh']['status'],'Resume section5; AEO8 C.2')
method(decisions['road']['method'],'Road','aggregate final energy','374.9 Mtoe * 0.935','2019 country road ownership','350.5315 Mtoe * road_c2019 / sum_ASEAN10 road2019','ASEAN10','Human-approved BAS approximation; not exact BAS road table','MATERIAL','PARENT_METHOD_ACCEPTED; CARRIER_AND_UNIT_CLOSURE_PENDING','AEO8 printed63-64/PDF65-66; C.3 printed182/PDF184; human Road BAS Decision')
method('ROAD_EV_EMBEDDED','Road','electricity','HUMAN_REPRESENTATION_DECISION','No separate BAS road EV split','Included once in Astar; EV value unknown, not zero','ASEAN11','Explicit EV pathway deferred','Small whole-transport electricity motivates human decision; not a road share','EMBEDDED_IN_ASTAR; NOT_SEPARATELY_MATERIALISED; DEFERRED_TO_EV_SENSITIVITY','Human Road BAS Decision items3-9')
method('ROAD_CARRIER_2019_CANDIDATE','Road','oil/gas/biomass/unclassified','No exclusive BAS road carrier vector recovered','2019 country road fuel observations','RoadParent_c * observed2019_carrier / totalroad_c2019; no renormalisation of missing shares','ASEAN10; TL projection pending','Candidate carrier preservation only; unknown residual UNCLASSIFIED','MATERIAL','CANDIDATE_NOT_ACCEPTED; no transport-wide shares or ATS fuel mix','energy_cache.json; original raw/calorific closure required')
for account,(mid,b,t) in growth.items():
 method(mid,account,'non-electric carriers','AEO8 BAS sector totals', '2019 fixed final-fuel core',f'D_c,k,2019 * ({t}/{b}); source ratio is 2022→2050, rebase to 2019 must be explicit','ASEAN11','2022 ratio applied to 2019 is a candidate rebase, not an observed 2019 ratio','MATERIAL','CANDIDATE_REBASE_AND_BASE_SOURCE_PENDING','Appendix C.3 printed182/PDF184; Agriculture includes Others')
method('AEO8_BAS_DOMESTIC_CONSTANT_CANDIDATE','DomesticShipping/DomesticAviation','oil','AEO8 BAS constant latest historical consumption','2019 domestic fuel raw/cached observations','Candidate D2050=D2019; AEO8 latest year is2022; 2019 rebase is separate modelling assumption','Countries with compatible base records','Not invoked as low-materiality Tier4','MATERIAL','METHOD_RECOVERED; REBASE_AND_BASE_ACCOUNT_CLOSURE_PENDING','2.1.1 printed46/PDF48')
method(decisions['bunker']['method'],'InternationalShippingBunker/InternationalAviationBunker','accepted liquid-fuel obligation','HUMAN_BASELINE_ASSUMPTION','Verified2019 bunker statistics','D_c2050 = verified D_c2019','Verified country records only; no redistribution','Explicit NEW HUMAN ASSUMPTION, not Tier4','MATERIAL_EXOGENOUS_ASSUMPTION; PHASE5_SENSITIVITY_REQUIRED=YES','2050_GROWTH_ISSUE_CLOSED; missing/omitted2019 accounts stay PENDING','Human International Bunker Decision; bunker_review.json; BUNKER_BASE_VERIFICATION.json')
method('RAIL_EMBEDDED_ACCOUNTING','Rail','electricity / fuel','AEO8 BAS latest-history constant; existing frozen representation','Rail raw transaction evidence','Electricity once in Astar; fuel once in TransportEmbeddedFuelParent','ASEAN11','No rail-specific Load','UNRESOLVED_BASE_ACCOUNT','ELECTRICITY_EMBEDDED; FUEL_SOURCE_CLOSURE_PENDING','AEO8 printed46/PDF48; Phase3b2 rail contract')
method('FROZEN_FOSSIL_PRICE','Supply','coal/gas/oil','Frozen pre_costs2050 v0.13.2','Not applicable','Use final processed EUR2020/MWh_th unchanged','ASEAN11 independent interfaces','No reinflation or second HHV/LHV conversion','MATERIAL','PRICE_AND_QUANTITY_BOUNDARY_ACCEPTED; thermal-basis compatibility remains documented','Resume10-11; COST_CANDIDATES_2050.json')
method('LOCAL_BIOMASS_OBLIGATION_CAP','Supply','biomass','HUMAN_BASELINE_BOUNDARY','Accepted country biomass final demand','Local annual supply cap = accepted fixed biomass obligation','Accepted country obligations only','No surplus expansion resource / no regional pool','MATERIAL','BOUNDARY_ACCEPTED; numerical obligations pending','Resume12')
astar_rows=[]; road_rows=[]; accepted_bunkers=[]
for r in records:
 if r['Kind']=='DEMAND' and r['Year']==2050:
  account=r['Account']; c=r['Country']; k=r['Carrier']
  r.update(MethodID='',CandidateValue=None,CandidateUnit='',ProjectionEvidence='',SpatialEvidence='',TemporalEvidence='',NumericStatus='PENDING')
  if account=='RoadEVFinalElectricity':
   r.update(Kind='BOUNDARY',Required=False,Value=None,RawValue=None,RawUnit='',Unit='',SourceYear=2026,Source='sources/GATE4_RESUME_DECISIONS.json',SourceSHA256=decision_sha,Locator='road',Transformation='Human-approved representation override for Assembly V1 only; no subtraction from Astar',AssemblyStatus='ASSEMBLY_V1_ACCEPTED',HumanAcceptance='EXPLICIT_HUMAN_ROAD_BAS_REPRESENTATION_DECISION',SourceQualified=True,TargetReady=True,ParentAccount=c+':2050:Electricity:Astar:electricity',Representation='EMBEDDED_IN_ASTAR',Availability=None,MethodID='ROAD_EV_EMBEDDED',Materialisation='NOT_SEPARATELY_MATERIALISED',Sensitivity='DEFERRED_TO_EV_SENSITIVITY',NumericStatus='NOT_SEPARATELY_MATERIALISED',Reason='Road EV remains inside Astar; unknown exclusive amount is not zero; no fixed EV Load. Supersedes resume section7 for Assembly V1, preserves historical Gate2 contract.')
  elif account=='Astar':
   val=D('225.0')*astar_base[c]/astar_sum
   r.update(MethodID='AEO8_BAS_ASTAR_2050' if c!='TL' else 'ASSEMBLY_V1_TL_REGIONAL_GROWTH_FALLBACK',CandidateValue=fmt(val),CandidateUnit='Mtoe/year',Source='sources/AEO8_BAS_SOURCE_VALUES.json',SourceSHA256=aeo_capsule_sha,SourceYear=2050,RawValue='225.0',RawUnit='Mtoe',Locator='Appendix C.2 printed181/PDF183',Transformation='225.0 Mtoe * country2019Astar/sumASEAN10_2019Astar; TL outside regional total',ProjectionEvidence='Gate4 Resume5; pinned AEO8 C.2; verified UNSD2019 national parents',Reason='National candidate in Mtoe; conversion pending human convention; no generation calibration or child subtraction',BaseInputID=base[c,'Astar','electricity']['InputID'])
   if factor is not None:r.update(Value=fmt(val*factor),Unit='MWh/year',AssemblyStatus='ASSEMBLY_V1_ACCEPTED',SourceQualified=True,NumericStatus='NUMERIC_ACCEPTED',Reason='Human unit convention and regional allocation accepted; spatial/time validation still required')
   astar_rows.append(dict(Country=c,Base2019MWh=fmt(astar_base[c]),ShareASEAN10=fmt(astar_base[c]/astar_sum),Candidate2050Mtoe=fmt(val),Value2050MWh=r['Value'],Status=r['AssemblyStatus'],MethodID=r['MethodID']))
  elif account in growth:
   mid,b,t=growth[account]; ba='IndustryFuel' if account=='IndustryFinalEnergy' else account
   oldr=base.get((c,ba,k)); oldval=oldr.get('Value') if oldr else None
   candidate=D(oldval)*D(t)/D(b) if oldval is not None else None
   r.update(MethodID=mid,CandidateValue=fmt(candidate) if candidate is not None else None,CandidateUnit='MWh/year',Source='sources/AEO8_BAS_SOURCE_VALUES.json',SourceSHA256=aeo_capsule_sha,SourceYear=2022,RawValue=t,RawUnit='Mtoe',Locator='C.3 printed182/PDF184',Transformation=f'candidate base2019 * {t}/{b}; AEO8 ratio is2022→2050',ProjectionEvidence='Ratio source recovered; applying it to2019 is an explicit candidate rebase',BaseInputID=oldr['InputID'] if oldr else '',Reason='PENDING_BASE_FUEL_QUALIFICATION_AND_2022_TO_2019_REBASE; numeric candidate is not an accepted forecast')
  elif account in ['InternationalShippingBunker','InternationalAviationBunker']:
   p=bproof[c,account+'Fuel']; oldr=base[c,account,k]
   r.update(MethodID=decisions['bunker']['method'],Source=oldr['Source'],SourceSHA256=oldr['SourceSHA256'],SourceYear=2019,Source2050='HUMAN_BASELINE_ASSUMPTION',DecisionSHA256=decision_sha,BaseInputID=oldr['InputID'],RawValue=p['base_text'] or None,RawUnit='TWh/year',Locator=oldr['Locator'],Transformation='2019 frozen TWh * 1e6 MWh/TWh; 2050 identical energy obligation per human assumption',ProjectionEvidence='sources/GATE4_RESUME_DECISIONS.json bunker; '+decision_sha,Materiality='MATERIAL_EXOGENOUS_ASSUMPTION',Phase5SensitivityRequired=True,Reason='Future-growth method CLOSED; '+p['source_status'],EnergyBasis=p['heat_basis'])
   if p['eligible_verified_2019_obligation']:
    val=D(p['base_text'])*1000000
    r.update(Value=fmt(val),Unit='MWh/year',AssemblyStatus='ASSEMBLY_V1_ACCEPTED',SourceQualified=True,HumanAcceptance='EXPLICIT_HUMAN_CONSTANT2019_BOUNDARY_PLUS_VERIFIED_BASE_CHAIN',NumericStatus='NUMERIC_ACCEPTED',Reason='2019 raw hashes, selected rows and rounding verified; constant2019 human2050 boundary. Supply pathway remains endogenous; actual allocation not yet validated.')
    accepted_bunkers.append(dict(Country=c,Account=account,Value2050MWh=fmt(val),MethodID=r['MethodID']))
   else:r.update(Value=None,CandidateValue=fmt(D(p['base_text'])*1000000) if p['base_text'] and D(p['base_text'])>0 else None,CandidateUnit='MWh/year',Reason='2050 growth assumption CLOSED, but base-account '+p['source_status']+'; do not turn missing/empty-set zero into a verified obligation')
  elif account in ['DomesticShippingFuel','DomesticAviationFuel']:
   oldr=base[c,account,k]
   r.update(MethodID='AEO8_BAS_DOMESTIC_CONSTANT_CANDIDATE',CandidateValue=oldr['Value'],CandidateUnit='MWh/year',ProjectionEvidence='AEO8 2.1.1 printed46/PDF48 keeps latest historical mode use constant; 2019 rebasing not silently equated with2022',BaseInputID=oldr['InputID'],Reason='DOMESTIC_BASE_ACCOUNT_AND_2019_REBASE_PENDING; international human assumption does not apply')
  elif account=='RoadResidualFuel':
   parent=road_parent*road_base[c]/road_sum if c!='TL' else None
   raw=energy_by[c]['road '+k]
   amount=parent*D(raw)/road_base[c] if parent is not None and raw and D(raw)>0 else None
   r.update(MethodID='ROAD_CARRIER_2019_CANDIDATE',CandidateValue=fmt(amount) if amount is not None else None,CandidateUnit='Mtoe/year',ProjectionEvidence='Human Road BAS approximation; base carrier composition candidate only',Reason='Road EV split is no longer a blocker. Compatible residual carrier vector and heat-basis closure remain; no fabricated zero, no all-transport fuel-share substitution.',RawValue=raw or None,RawUnit='TWh/year',Source=energy['source'],SourceSHA256=energy['source_sha256'],Locator=c+'/road '+k,Transformation='candidate regionalroadMtoe * basecountry_carrierTWh/sumASEAN10roadTWh; no missing-share renormalisation')
  elif account=='TransportEmbeddedFuelParent':r.update(MethodID='RAIL_EMBEDDED_ACCOUNTING',Reason='Rail electricity remains inside Astar. Non-electric rail parent source/coverage remains unresolved; no second rail Load or invented amount.')
 if r['Kind']=='EXTERNAL_SUPPLY' and r['Year']==2050:
  r.update(AssemblyStatus='ASSEMBLY_V1_ACCEPTED',SourceQualified=True,TargetReady=True,HumanAcceptance='EXPLICIT_GATE4_RESUME_FROZEN_PROCESSED_PRICE',Availability='ASSEMBLY_V1_EXTERNAL_MARKET_UNCONSTRAINED',EnergyBasis='FROZEN_UPSTREAM_THERMAL_PRICE_BASIS_NO_SECOND_CONVERSION',MethodID='FROZEN_FOSSIL_PRICE',ProjectionEvidence='Gate4 Resume10-11',Reason='Final processed EUR2020/MWh_th retained unchanged. Independent country quantity-unconstrained market is a human model boundary; no physical regional fossil network. Underlying calorific documentation not strengthened by this acceptance.')
# Informational parent accounts never materialise as duplicate Loads.
common=next(x for x in records if x['Kind']=='BOUNDARY' and x['Account']=='RoadEVFinalElectricity').copy()
for c in ['ASEAN10',*countries]:
 val=road_parent if c=='ASEAN10' else road_parent*road_base[c]/road_sum if c!='TL' else None
 q=dict(common,InputID=c+':2050:RoadParent:aggregate',Kind='ACCOUNTING',Country=c,CountryScope=c,Account='RoadParent',Carrier='aggregate_final_energy',Value=fmt(val) if val is not None else None,Unit='Mtoe/year',RawValue='374.9*0.935',RawUnit='Mtoe',SourceYear=2050,Source='sources/AEO8_BAS_SOURCE_VALUES.json',SourceSHA256=aeo_capsule_sha,AssemblyStatus='ASSEMBLY_V1_ACCEPTED' if val is not None else 'PENDING',SourceQualified=val is not None,TargetReady=False,Required=False,Representation='ACCOUNTING_ONLY_NO_LOAD',ParentAccount='',MethodID=decisions['road']['method'],Materialisation='ACCOUNTING_ONLY_NO_LOAD',Transformation='350.5315 Mtoe * country2019road / sumASEAN10road; ASEAN10 excludes TL',Locator='AEO8 printed63-64/PDF65-66 and C.3 printed182/PDF184; human Road BAS decision',Reason='Approximate road parent. Embedded EV is not zero, so exact non-electric residual identity is not claimed. TL needs separate compatible growth boundary.',Sensitivity='DEFERRED_TO_EV_SENSITIVITY',HumanAcceptance='EXPLICIT_HUMAN_APPROXIMATE_BAS_ROAD_PARENT')
 records.append(q);road_rows.append(dict(Country=c,Base2019TWh=fmt(road_base[c]) if c in road_base else fmt(road_sum),RoadParent2050Mtoe=q['Value'],MethodID=q['MethodID'],Status=q['AssemblyStatus']))
registry=dict(old, schema='assembly-v1-freeze-2',status='PARTIAL',resume_decisions_sha256=decision_sha,records=records)
dump(F/'registry.json',registry)
dump(E/'TARGET_CONSTRUCTION.json',dict(Astar2019ASEAN10MWh=fmt(astar_sum),Road2019ASEAN10TWh=fmt(road_sum),Astar=astar_rows,RoadParent=road_rows,BunkerAccepted=accepted_bunkers,counts=dict(records=len(records),required_target_demands=sum(r['Kind']=='DEMAND' and r['Year']==2050 and r['Required'] for r in records),numeric_accepted_target_demands=sum(r['Kind']=='DEMAND' and r['Year']==2050 and r['AssemblyStatus']=='ASSEMBLY_V1_ACCEPTED' for r in records),embedded_EV_boundaries=sum(r['Year']==2050 and r['Account']=='RoadEVFinalElectricity' and r['Kind']=='BOUNDARY' for r in records))))
text(F/'README.md','''# Assembly V1 Gate4 resume input freeze

`registry.json` is canonical and `manifest.json` pins all source capsules. Existing Gate2 source files and its historical contract remain unchanged. Road EV is an accepted Assembly V1 boundary, not a numeric zero or a standalone fixed Load. The approximate regional road parent is 350.5315 Mtoe; exclusive carrier closure remains separate.

The international bunker growth-method issue is CLOSED by `ASSEMBLY_V1_BUNKER_CONSTANT_2019`. Only verified base obligations become numeric accepted targets. Missing countries and omitted transactions remain PENDING. This is a material human baseline assumption requiring Phase5 sensitivity, not a forecast.

Numeric acceptance is distinct from node/time allocation and actual-network validation. Candidate fields never feed a network. AEO8 generation and upstream DEFAULT future growth are forbidden. No solver is enabled.
''')
dump(F/'manifest.json',dict(schema='assembly-v1-sources-2',files={p.relative_to(F).as_posix():sha(p) for p in F.rglob('*') if p.is_file() and p.name!='manifest.json'}))
tables={}
def table(name,rows,fields=None):
 fields=fields or list(rows[0]); vals=[fields]+[[str(r.get(k,'')) if r.get(k) is not None else '' for k in fields] for r in rows];tables[name]=dict(export_values=vals)
table('ASSEMBLY_V1_2050_METHOD_REGISTER.csv',methods)
fields=list(records[0]); fields += sorted(set().union(*(r.keys() for r in records))-set(fields))
table('PHASE4_ASSEMBLY_INPUT_REGISTRY.csv',records,fields)
blockers=[
 dict(ID='G4-ROAD-EV-2050',Group='INPUT_FREEZE',MaterialImpact='No exclusive road BAS EV share recovered; user defers explicit pathway',Affected='11 Road EV rows',MinimumResolution='None for Assembly V1; no fixed EV Load; preserve unknown within Astar',Status='CLOSED_FOR_ASSEMBLY_V1',Evidence='Human Road BAS Decision; GATE4_RESUME_DECISIONS.json'),
 dict(ID='G4-BUNKER-GROWTH-2050',Group='INPUT_FREEZE',MaterialImpact='International bunker is material, including SG marine535.3418TWh',Affected='InternationalShippingBunker and InternationalAviationBunker',MinimumResolution='Human constant2019 boundary applied only to verified records; future sensitivity required',Status='CLOSED_FOR_ASSEMBLY_V1',Evidence='Human International Bunker Decision; verified17 international base records'),
 dict(ID='G4-INPUT-01',Group='INPUT_FREEZE',MaterialImpact='Unqualified2019 fuel account coverage, calorific basis and rebasing cannot be hidden by a2050 growth rule',Affected='Fixed fuel core, rail parent, road residual vector, missing/omitted domestic and international base accounts',MinimumResolution='Close the existing base-account reconciliation and explicit2019 rebase; no new future bunker/EV search',Status='OPEN_BASE_ACCOUNT_CLOSURE',Evidence='BUNKER_BASE_VERIFICATION.json; preserved Gate2 registry; candidate target methods'),
 dict(ID='G4-UNIT-01',Group='INPUT_FREEZE',MaterialImpact='AEO8 Mtoe needs an explicitly accepted operational conversion before MWh loads',Affected='Astar and Road absolute energy anchors',MinimumResolution='Pending human question: adopt standard1Mtoe=11.63TWh as project convention, or supply source-specific alternative',Status=decisions['Mtoe_to_TWh']['status'],Evidence='INSEE standard41.868GJ/toe; AEO8 conversion metadata not recovered'),
 dict(ID='G4-INPUT-02',Group='INPUT_FREEZE',MaterialImpact='Processed fossil prices and market quantity boundary now accepted; heat-basis compatibility must remain visible',Affected='Fuel demand/technology/cost thermal basis and biomass obligations',MinimumResolution='Reconcile source thermal units without reinflating or converting frozen processed prices twice; local biomass cap equals accepted demand',Status='PRICE_AND_MARKET_BOUNDARY_CLOSED_BASIS_REVIEW_REMAINS',Evidence='Resume10-13; frozen COST_CANDIDATES_2050.json'),
 dict(ID='G4-ALLOCATION-01',Group='BUILD_INPUT',MaterialImpact='Numeric source acceptance does not establish100-node/full-year allocation',Affected='Target obligations; first unsolved network',MinimumResolution='Verify source-to-node-to-time build assets and conservation after numerical freeze',Status='NOT_YET_VALIDATED',Evidence='No first unsolved Research network exists'),
 dict(ID='G4-CARBON-01',Group='CARBON_ATTRIBUTION',MaterialImpact='Actual emitting and shared conversion components need explicit role/origin attribution',Affected='CHP SMR FT captured/recycled CO2 and power H2',MinimumResolution='Validate actual component attribution after build and before Gate5; not an input-preflight requirement',Status='POST_BUILD_STATIC_VALIDATION_BLOCKER',Evidence='Resume15,19; Gate3 architecture preserved')]
table('PHASE4_GATE4_BLOCKERS.csv',blockers)
with (G/'PHASE4_ACTIVE_SECTOR_COUPLING_PATHWAYS.csv').open(encoding='utf-8-sig',newline='') as f: pathways=list(csv.DictReader(f))
for r in pathways:
 if any('EV' in str(v) for v in r.values()):
  r.update(CapacityStatus='NO_SEPARATE_EV_COMPONENT_IN_ASSEMBLY_V1',DemandStatus='EMBEDDED_IN_ASTAR_NOT_SEPARATELY_MATERIALISED',CanCarryNonzeroFlow='NOT_SEPARATE_PATHWAY_IN_V1',ScientificRole='Human decision defers explicit EV pathway; electricity remains once in Astar',ActualStatus='DEFERRED_TO_EV_SENSITIVITY')
  # Preserve the existing schema; append scope evidence without claiming a pathway exists.
  r['AssemblyV1Note']='Road EV embedded in Astar; no separate fixed EV Load or active explicit EV pathway required'
if pathways:table('PHASE4_ACTIVE_SECTOR_COUPLING_PATHWAYS.csv',pathways,list(dict.fromkeys(k for r in pathways for k in r)))
dump(W/'build/tables.json',tables)
for p in E.glob('aeo8*.txt'):shutil.copyfile(p,GE/p.name)
for name in ['BUNKER_BASE_VERIFICATION.json','TARGET_CONSTRUCTION.json','START.json']:shutil.copyfile(E/name,GE/name)
for name in ['AEO8_BAS_SOURCE_VALUES.json','GATE4_RESUME_DECISIONS.json']:shutil.copyfile(F/'sources'/name,GE/name)
print(json.dumps(json.loads((E/'TARGET_CONSTRUCTION.json').read_text())['counts'],indent=2))
