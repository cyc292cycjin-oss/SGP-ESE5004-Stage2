"""Deterministic Phase3A6 research-only extraction and accounting candidates.

Never writes model inputs. CSV publication is performed by export_tables.mjs.
Decimal arithmetic preserves source precision; unknowns stay empty, not zero.
"""
from pathlib import Path
from decimal import Decimal as D
import json,re,hashlib,ast
from pypdf import PdfReader
R=Path(__file__).resolve().parent;P=R.parent/'phase3a5';E=R/'evidence';OUT=R/'data/derived';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
num=lambda x:format(D(x).quantize(D('.000000001')),'f').rstrip('0').rstrip('.')
def save(name,rows):
 (OUT/(name+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
def textpdf(p,n):return PdfReader(p).pages[n-1].extract_text()
registry=[]
for file,prefix in [(P/'data/raw/buildings/SOURCE_REGISTRY.json','../phase3a5/'),(R/'data/raw/NEW_SOURCE_REGISTRY.json',''),(R/'data/raw/SUPPLEMENT_REGISTRY.json','')]:
 for row in json.loads(file.read_text(encoding='utf8')):
  if row.get('file'):
   row=dict(row);row['file']=prefix+row['file'];assert sha(R/row['file'])==row['sha256'];row['access_date']='2026-10-02';registry.append(row)
reg={r['source_id']:r for r in registry}
# Keep only sources used in this prototype and sources backing reused MY rows.
used={'MY_NEB2016','MY_NEB2019','AEO8','AEO8_CORRIGENDUM','MY_ENERGY_MAG9','MY_WATER_GUIDELINE2016_RESOLVED','MY_GUIDELINE_LANDING','TOE_CONVENTION_INSEE'}
old=json.loads((P/'data/derived/buildings/BUILDINGS_USEFUL_HEAT_INPUT_CANDIDATES.json').read_text(encoding='utf8'))
my=[r for r in old if r['Country']=='MY' and r['SourceID'].startswith('UNSD_')]
used.update(r['SourceID'] for r in my)
registry=[r for r in registry if r['source_id'] in used]
(R/'data/SOURCE_REGISTRY.json').write_text(json.dumps(registry,indent=2,ensure_ascii=False),encoding='utf8')
def src(sid,loc):
 r=reg[sid];return dict(SourceID=sid,SourceURL=r.get('resolved_url',r['url']),SourceFile=r['file'],SourceSHA256=r['sha256'],SourceLocation=loc,SourceVersion=r.get('version','cached official page; access2026-10-02'),AccessDate='2026-10-02')
def meta():return dict(EvidenceClass='VERIFIED_SOURCE_TRANSCRIPTION',Status='UNVERIFIED',HumanConfirmation='PENDING')
aeo=R/reg['AEO8']['file'];c2=textpdf(aeo,183);c5=textpdf(aeo,186)
def row_numbers(text,label,count):
 line=next(s for s in text.splitlines() if s.startswith(label+' '));return re.findall(r'\d[\d,]*\.\d+',line)[:count]
generation=row_numbers(c5,'Total',8);final=row_numbers(c2,'Electricity',8)
assert generation==['513.1','1,270.3','1,401.4','1,658.8','1,940.2','2,264.6','2,635.0','3,036.3']
assert final==['37.8','93.7','104.0','123.0','143.8','167.9','195.3','225.0']
trajectory=[]
for y,g,f in zip([2025,2030,2035,2040,2045,2050],generation[2:],final[2:]):
 value=D(g.replace(',',''));checks={}
 for layer in ['P','U','V']:
  config=(P/f'evidence/source_snapshot/{layer}/configs/config.asean.yaml').read_text()
  block=config.split('total_elec_demand:',1)[1].split('redistribute_industry:',1)[0]
  current=D(re.search(rf'^\s*{y}:\s*([\de+.]+)',block,re.M)[1]);assert current==value*D(1e6);checks[layer]=str(current)
 trajectory.append(dict(year=y,scenario='BAS',coverage='ASEAN10',generation_TWh=str(value),TFEC_electricity_Mtoe=f,conditional_TFEC_TWh=num(D(f)*D('11.63')),conversion_status='EXTERNAL_CONVENTION_11.63_NOT_AEO_SPECIFIC_ACCEPTANCE',config_MWh=checks,match=True))
save('AEO8_TRAJECTORY_CHECK',trajectory)
# Capture targeted device and geography observations for later review.
extra=[]
for sid,pages in [('MY_WATER_GUIDELINE2016_RESOLVED',[8,10]),('MY_ENERGY_MAG9',[29,30,31])]:
 for p in pages:
  t=textpdf(R/reg[sid]['file'],p);file=E/f'{sid}_p{p}.txt';file.write_text(t,encoding='utf8');extra.append(dict(source=sid,pdf_page=p,file=str(file.relative_to(R))))
d=PdfReader(aeo)
country_hits=[]
for i,p in enumerate(d.pages):
 t=p.extract_text()
 if re.search(r'10\s+ASEAN|ten\s+ASEAN|10\s+AMS|ten\s+AMS',t,re.I):
  for m in re.finditer(r'10\s+ASEAN|ten\s+ASEAN|10\s+AMS|ten\s+AMS',t,re.I):country_hits.append(dict(pdf_page=i+1,excerpt=t[max(0,m.start()-70):m.end()+140]))
(E/'TARGETED_SOURCE_CHECKS.json').write_text(json.dumps(dict(geography_hits=country_hits,device_excerpt_files=extra,visual_review=['AEO8 PDF183 C.2','AEO8 PDF186 C.5','MY NEB2016 PDF95 Table42','MY NEB2016 PDF103 Table47','MY NEB2019 PDF57 Table17','MY NEB2019 PDF73 Table29 electricity column']),ensure_ascii=False,indent=2),encoding='utf8')
# All ledger rows are alternatives or nested children, never an additive national input.
ledger=[]
def add(sid,year,geo,sector,fuel,enduse,value,unit,loc,role='ENDUSE_CHILD',note='',destination=''):
 ledger.append(dict(RecordID=f'MYL{len(ledger)+1:03}',Year=year,Geography=geo,Sector=sector,Fuel=fuel,EndUse=enduse,RawValue=str(value),RawUnit=unit,EnergyBasis='final input; NCV for combustible fuels' if sid.startswith('MY_NEB') else 'reported raw source basis',RowRole=role,RetainedDestination=destination or 'pending mapping',Transformation='identity; no national scaling or year bridge',Comment=note,**src(sid,loc),**meta()))
for end,v in [('cooling',327),('water heating',70),('lighting',233),('cooking',117),('appliances',1586),('ALL',2333)]:
 add('MY_NEB2016',2016,'Peninsular Malaysia','Residential','electricity',end,v,'ktoe','PDF95/printed95 Table42',role='PARENT_TOTAL' if end=='ALL' else 'ENDUSE_CHILD',destination='candidate historical electric water-heating account' if end=='water heating' else 'direct electricity subaccount; no extra Load')
for f,e,v in [('natural gas','cooking',1),('LPG','cooking',538),('kerosene','lighting',3)]:add('MY_NEB2016',2016,'Peninsular Malaysia','Residential',f,e,v,'ktoe','PDF95 Table42',destination='direct fuel; cooking NON-EXPLICIT + ACCOUNTING REQUIRED')
add('MY_NEB2016',2016,'Peninsular Malaysia','Residential','all fuels','cooking',655,'ktoe','PDF95 Table42','REPORTED_PARENT_TOTAL','fuel children sum656; printed total655; preserve discrepancy')
for end,v in [('cooling','16440.66'),('water heating','1034.62'),('lighting','8516.23'),('other/unclassified','13114.06'),('ALL','39106.00')]:
 add('MY_NEB2016',2016,'Peninsular Malaysia','Commercial','electricity',end,v,'GWh','PDF103 Table47',role='PARENT_TOTAL' if end=='ALL' else 'ENDUSE_CHILD',note='12 activity categories; Services mapping pending; child sum39105.57 versus parent39106.00',destination='candidate historical electric water-heating account' if end=='water heating' else 'direct electricity subaccount; no extra Load')
add('MY_NEB2016',2016,'Peninsular Malaysia','Commercial','LPG','other use',679,'ktoe','PDF104 Table48','FUEL_PARENT_TOTAL','not allocated to cooking or heat; preserve direct fuel unclassified')
for sector in ['Residential','Commercial']:
 for fuel,end,why in [('electricity','space heating','not separately reported; unknown, not zero'),('biomass','unclassified','non-commercial firewood/biomass excluded from NEB balance; not zero'),('other fuels','unclassified','not fully classified in end-use table; no filled zero')]:
  add('MY_NEB2016',2016,'Peninsular Malaysia',sector,fuel,end,'','','PDF95/103/105','MISSING_EVIDENCE',why)
for sid,year,geo,vals,loc in [('MY_NEB2016',2016,'National',[31128,44349,67664,340,543,144024],'PDF59 Table17'),('MY_NEB2016',2016,'Peninsular Malaysia',[27119,39484,49043,340,'543.3',116529],'PDF59 Table17'),('MY_NEB2019',2019,'National',[33322,45713,78427,477,663,158603],'PDF57 Table17'),('MY_NEB2019',2019,'Peninsular Malaysia',[28877,40471,54749,477,'663.5',125238],'PDF57 Table17')]:
 for sec,v in zip(['Residential','Commercial','Industry','Transport','Agriculture','ALL'],vals):add(sid,year,geo,sec,'electricity','ALL',v,'GWh',loc,'ALTERNATIVE_SECTOR_TOTAL','Table17 supplier-statistics family; do not mix with end-use survey or Table29')
balance2016={'Residential':{'electricity':2678,'natural gas':1,'LPG':602,'kerosene':3,'ALL':3284},'Commercial':{'electricity':3816,'natural gas':24,'diesel':151,'fuel oil':14,'LPG':760,'ALL':4765}}
balance2019={'Residential':{'electricity':2715,'natural gas':1,'LPG':615,'kerosene':8,'ALL':3339},'Commercial':{'electricity':4086,'natural gas':23,'diesel':340,'fuel oil':50,'LPG':163,'ALL':4662}}
for year,balances,sid,loc in [(2016,balance2016,'MY_NEB2016','PDF74-75 national energy balance'),(2019,balance2019,'MY_NEB2019','PDF72-73 Table29')]:
 for sec,fuels in balances.items():
  for f,v in fuels.items():add(sid,year,'National',sec,f,'unclassified',v,'ktoe',loc,'ALTERNATIVE_FUEL_TOTAL','NEB balance family; excludes non-commercial biomass; sector allocation differs from Table17 in2019')
for r in my:
 sid=r['SourceID'];add(sid,2019,'National',r['Sector'],r['Fuel'],'unclassified',r['FinalEnergy'],r['FinalEnergyUnit'],r['SourceLocation'],'ALTERNATIVE_FUEL_TOTAL','Reused exact raw2019 UNdata row from2025-05-02 export; does not establish same population/partition as NEB')
for y,rst,e in [(2016,8051,12394),(2017,7796,12607),(2018,7773,13153),(2019,8000,13647)]:
 add('MY_NEB2019',y,'National','Residential + Commercial','ALL','ALL',rst,'ktoe','PDF67 Table25','TIME_SERIES_PARENT','2019 edition; not independent end-use-share evidence')
 add('MY_NEB2019',y,'National','ALL','electricity','ALL',e,'ktoe','PDF68 Table26','TIME_SERIES_PARENT','2019 edition historical series;2016 edition finalelectric12392 differs slightly')
save('MALAYSIA_BUILDINGS_SOURCE_LEDGER',ledger)
factor=D('41.84')/D('3.6');rw=D(70)*factor;rt=D(2333)*factor;sw=D('1034.62');st=D(39106)
heating=[]
for sec,end,raw,unit,gwh,loc in [('Residential','water',70,'ktoe',rw,'PDF95 Table42; PDF108 conversion'),('Commercial/Services candidate','water','1034.62','GWh',sw,'PDF103 Table47'),('Residential','space','','','','PDF95 Table42'),('Commercial/Services candidate','space','','','','PDF103 Table47')]:
 heating.append(dict(Sector=sec,EndUse=end,RawElectricity=str(raw),RawUnit=unit,FinalElectricityGWh=num(gwh) if gwh!='' else '',Year=2016,Geography='Peninsular Malaysia',Device='electric water-heater mix not identified' if end=='water' else '',Transformation='ktoe *41.84TJ/ktoe /3.6TJ/GWh' if unit=='ktoe' else ('identity' if unit else 'none'),Classification='OBSERVED_REPORTED_FINAL_INPUT' if end=='water' else 'NOT_SEPARATELY_REPORTED_UNKNOWN',E3Role='h_'+('R' if sec=='Residential' else 'S')+'_water partial only; national/year bridge pending',**src('MY_NEB2016',loc),**meta()))
save('MALAYSIA_ELECTRIC_HEATING_EVIDENCE',heating)
useful=[]
for row in heating:
 has=row['FinalElectricityGWh']!='';e=D(row['FinalElectricityGWh'])*1000 if has else ''
 useful.append(dict(CandidateID='MYQ'+str(len(useful)+1),Sector=row['Sector'],EndUse=row['EndUse'],Year=2016,Geography=row['Geography'],FinalEnergyMWh=num(e) if has else '',EndUseShare=1 if has else '',DeviceInputShare='',HistoricalEfficiency_or_COP='',UsefulServiceMWh='',Formula='FinalEnergyMWh * 1 * sum_j(input_energy_share_j * historical_eta_or_COP_j)' if has else 'unknown final input * unknown device mix/performance',UsefulBoundary='proposed heat delivered at building service point; device vs system boundary requires acceptance',Status='CANDIDATE_INPUT_ONLY_USEFUL_VALUE_BLOCKED',HumanConfirmation='PENDING',Blocker='2016 device input-energy shares and historical service-boundary performance; national/year transfer not accepted',**src('MY_NEB2016',row['SourceLocation'])))
save('MALAYSIA_USEFUL_HEAT_CANDIDATES',useful)
devices=[]
for sid,loc,technology,observed,limitation in [
 ('MY_WATER_GUIDELINE2016_RESOLVED','PDF8/printed7 scope; PDF10/printed9 definitions','instantaneous / storage / solar','Official definitions, residential and commercial applications; storage/solar up to300L','No sector input-energy shares or calibrated historical efficiency/COP'),
 ('MY_WATER_GUIDELINE2016_RESOLVED','PDF8/printed7 cited standards','MS IEC60335 and MS1597 series','Appliance safety standards identified by edition','Safety standards are not stock-weighted seasonal device performance'),
 ('MY_ENERGY_MAG9','PDF29-31/printed27-29 water-heater feature','instantaneous / storage','Device approvals discussed for imported/local products','Certificate-of-Approval counts are not installed stock or energy shares'),
 ('MY_NEB2016','PDF105 notes','all historical end-use equipment','Balance explicitly excludes useful energy because equipment efficiencies vary','Cannot reinterpret final-energy water-heating cells as useful heat'),
 ('MY_NEB2016','PDF92/98 survey introductions','household / commercial survey','2000 households and5000 commercial premises; no device-input weighting in published end-use tables','Survey microdata, wave and extrapolation method still needed')]:
 devices.append(dict(RecordID=f'MYD{len(devices)+1:02}',Technology=technology,Observation=observed,HistoricalYear='2016 reference; guideline2017',Country='MY',Efficiency_or_COP='',DeviceInputShare='',PerformanceBoundary='',EvidenceFit=limitation,Adoption='NOT_ADOPTED',**src(sid,loc),**meta()))
save('MALAYSIA_HISTORICAL_DEVICE_EVIDENCE',devices)
tests=[]
def check(id,expr,lhs,rhs,unit,result,note):
 tests.append(dict(TestID=id,Scope='RESEARCH_SOURCE_ACCOUNTING_ONLY',Expression=expr,LHS=str(lhs),RHS=str(rhs),Difference=num(D(lhs)-D(rhs)) if lhs!='' and rhs!='' else '',Unit=unit,Result=result,Interpretation=note,HumanConfirmation='PENDING'))
check('MYC01','R electricity children sum versus Table42 parent',sum([327,70,233,117,1586]),2333,'ktoe','PASS_SOURCE_ARITHMETIC','Same table; not proof of space-heating absence or national coverage')
check('MYC02','R cooking fuel children versus printed cooking parent',1+538+117,655,'ktoe','DISCREPANCY_RETAINED','No corrected cell or hidden residual')
check('MYC03','S end-use children versus printed Table47 parent',D('16440.66')+sw+D('8516.23')+D('13114.06'),st,'GWh','DISCREPANCY_RETAINED','0.43GWh gap; greater than simple four-cell0.01 rounding envelope; no repair')
check('MYC04','R end-use total converted versus Peninsular Table17',num(rt),27119,'GWh','ROUNDING_COMPATIBLE_INFERENCE','Difference4.355556GWh <half-ktoe5.811111GWh; does not prove same sample/upscaling')
check('MYC05','S end-use total versus Peninsular Table17',st,39484,'GWh','SOURCE_RECONCILIATION_REQUIRED','378GWh gap; source mismatch remains')
check('MYC06','2019 R Table29 converted versus Table17',num(D(2715)*factor),33322,'GWh','SOURCE_RECONCILIATION_REQUIRED','Large sector partition disagreement; do not choose silently')
check('MYC07','2019 S Table29 converted versus Table17',num(D(4086)*factor),45713,'GWh','SOURCE_RECONCILIATION_REQUIRED','Large opposite sector partition disagreement')
check('MYC08','2019 Table29 R+S converted versus Table17 R+S',num(D(6801)*factor),33322+45713,'GWh','AGGREGATE_CLOSE_NOT_SECTOR_EQUIVALENCE','Small aggregate gap does not license R/S mixing')
check('MYC09','R2016 water-only transfer (T_R-h_Rwater)+h_Rwater',2333-70+70,2333,'ktoe','PASS_PARTIAL_TRANSFER_IDENTITY','B_no_water2263ktoe; NOT accepted B because space is unknown')
check('MYC10','S2016 water-only transfer (T_S-h_Swater)+h_Swater',st-sw+sw,st,'GWh','PASS_PARTIAL_TRANSFER_IDENTITY','Arithmetic parent identity only; end-use-table discrepancy remains; space unknown')
check('MYC11','NEB2019 electricity secondary+netimports versus final',13789+3-146,13647,'ktoe','REPORTED_ROUNDING_GAP','-1ktoe retained; statistical discrepancy is raw -277 not invented correction')
check('MYC12','2019 Table17 five sectors versus national total',78427+45713+33322+477+663,158603,'GWh','REPORTED_ROUNDING_GAP','-1GWh retained; no residual correction')
check('MYC13','A*_MY = O_MY + T_R_MY + T_S_MY','','','MWh','BLOCKED_BOUNDARY','A* not accepted; incompatible year/region/source families; O not manufactured')
check('MYC14','D_accepted_MY+h_R_MY+h_S_MY=A*_MY','','','MWh','BLOCKED_ANNUAL','National historical space/water heating not complete; partial water transfer is not annual E3 closure')
check('MYC15','min_t(A*_t-h_Rt-h_St)>=0','','','MW','NOT_RUN_ANNUAL_GATE_FAILED','No hours fabricated, clipped, smoothed, capped or rescaled')
check('MYC16','Q useful from observed water electricity','','','MWh useful','BLOCKED_DEVICE_EVIDENCE','No eta1/COP or uniform device mix assumed')
check('MYC17','2016 share-preserving2019 year bridge','','','share','YEAR_BRIDGE_PENDING','National totals trend exists; compatible2017-19 water shares do not')
save('MALAYSIA_E3_CLOSURE_TEST',tests)
# Glossary records separate conventions from inspected implementation.
concepts=[
 ('Gross electricity generation','Generator-terminal output before station auxiliaries','Generator output needs gross/net convention; AEO C.5 only says generation','source exogenous; dispatch endogenous','not necessarily final delivered energy','risk if used as final Load and own use/loss added again','MY NEB2016 PDF106; AEO C.5'),
 ('Net electricity generation','Gross generation less plant auxiliary electricity','Generator/Link bus output if convention is net','endogenous dispatch','station auxiliaries already removed; T&D not removed','gross/net generator inputs must align','MY NEB2016 PDF106'),
 ('Electricity available for supply','Defined-stage supply after specified generation, trade, own-use adjustments','No common A* mapping established','source exogenous','definition-dependent','label alone insufficient','MY NEB2019 Table29 PDF72-73'),
 ('Own use / auxiliary consumption','Energy sector use including power station auxiliaries, excluding final users','No separately verified common ASEAN electricity own-use account','source exogenous; explicit plant account could be endogenous','MY combines with external losses','double deduction/addition possible','MY NEB2016 PDF105'),
 ('Transmission losses','Energy dissipated transporting electricity over transmission network','AC Line losses not enabled by inspected solver call; Link efficiency separate','flow endogenous if explicitly modelled','not part of final-meter demand','risk only if preloaded and modelled again','U solve_network; PyPSA0.30.3 transmission_losses default0'),
 ('Distribution losses','Energy lost between distribution input and consumer meter','Distribution Link efficiency1;0.97 multiplies AC Load','current load transform exogenous','not verified physical3% ASEAN loss','gross target plus future lossy Link would risk duplication','U prepare_sector_network:3402-3469'),
 ('Net imports / exports','Electricity imports minus exports over chosen border','Cross-border Lines/Links; external exchanges require explicit boundary','optimized flows endogenous','not a loss term','do not allocate as losses or direct demand','MY NEB2019 Table29'),
 ('Final electricity consumption','Electricity delivered to final users, before their devices convert it to service','Best-aligned candidate statistical parent A* before E3 heating transfer','base measurement exogenous','normally excludes upstream T&D/own use','future aggregate may already contain electrification later modelled','MY NEB2016 PDF105; AEO C.2'),
 ('Residential electricity','All residential final electricity including cooking/cooling/heating','UNSD electricity residential; overwrites AC shape total','input exogenous','final-meter candidate; exact source alignment pending','water/space electricity must be transferred exactly once','U add_residential; MY Table42'),
 ('Services electricity','Service-activity final electricity under accepted activity crosswalk','services electricity Load, separate from AC','input exogenous','mapping to MY Commercial pending','do not add parent and end-use child as separate Loads','U add_services; MY Table47'),
 ('Industry electricity','Industrial final direct electricity under chosen conversion boundary','industry electricity Load and conversion components','direct input exogenous; some conversion dispatch endogenous','source-dependent','generic target plus explicit processes may duplicate','U redistribute_industrial_load; AEO BAS assumptions'),
 ('Transport electricity','Final traction/charging input according to source boundary','framework capability only; no new Transport work','shares configured; charging dispatch potentially endogenous','charger losses depend on measuring point','existing electrified use versus explicit charging overlap','U prepare_sector_network; AEO PDF65'),
 ('Other final electricity','Retained final users outside accepted R/S; must have an auditable partition','Proposed O; not a manufactured balancing correction','input exogenous','same meter as A* required','unclassified is not deleted or set to zero','Accepted E3 structure; MY Table17'),
 ('Endogenous conversion electricity','Electricity consumed to produce another modelled carrier or useful service','Link input flows','endogenous','includes conversion requirements according to efficiencies','exclude same converted service from fixed direct demand','U prepare_sector_network'),
 ('Storage charging','Electricity moving into storage before later discharge','Store/StorageUnit charging and converter Links','endogenous','charging losses handled once by storage model','not an extra fixed final-consumption Load','U battery storage Links'),
 ('Electrolysis electricity','Link input producing hydrogen with specified input-output efficiency','electrolysis Link bus0','endogenous when retained in FullSC','conversion efficiency is distinct from T&D loss','supply generation may already include H2 transformation','U prepare_sector_network; AEO PDF56/C.2'),
 ('Heat-pump electricity','Electrical input needed for delivered heat at accepted COP boundary','heat pump Link bus0','endogenous dispatch/capacity within configuration','COP converts electrical input to useful thermal output','do not preload future HP electricity plus heat service','U add_heat'),
 ('Resistive-heating electricity','Electric input to modelled resistance heater','resistive heater Link bus0','endogenous dispatch/capacity within configuration','device/system efficiency not necessarily1','historical heating removed once then service regenerated','U add_heat'),
 ('System bus demand','Balance at a specified model bus including attached fixed loads and converter inputs','Bus balance constraints','fixed+endogenous','depends on bus placement and losses between buses','bus name cannot establish original statistic','Inspected U network construction'),
 ('Direct electricity after E3','A* minus accepted historical residential/services electric space/water heating','proposed D_accepted','exogenous future direct-service evolution requires separate contract','same meter/time basis as h_R/h_S','do not use AEO total unchanged and add all conversion demand','Accepted E3 structure'),
 ('Statistical discrepancy','Published supply-use mismatch under source accounting conventions','No invented balancing Load permitted','reported diagnostic exogenous','not a physical T&D loss','cannot fill model residual by silently adding it','MY NEB2019 Table29 row13'),
]
gloss=[]
for concept,definition,model,endo,loss,dup,evidence in concepts:gloss.append(dict(Concept=concept,Definition=definition,Source=evidence,Unit='annual MWh/GWh/TWh; power MW at snapshots',LocationInModel=model,Exogenous='source/input only where stated',Endogenous=endo,LossInclusion=loss,PotentialSectorCouplingDuplicate=dup,EvidenceClass='SOURCE_DEFINITION_AND_CODE_OBSERVATION; mapping proposed',Status='PENDING_MAPPING',HumanConfirmation='PENDING'))
save('ELECTRICITY_ACCOUNTING_GLOSSARY',gloss)
scope=[]
for sector,aeo_repr,current,endogenous,risk,evidence in [
 ('Buildings overall','BAS fixed latest appliance efficiency; clean-cooking/electrification country2005-2022 growth','R/S UNSD totals plus explicit heat framework','heat conversion dispatch/capacity; future service contract pending','YES conditional: forecast fixed total plus new heat electricity','AEO PDF48/printed46; U add_residential/add_services/add_heat'),
 ('Water heat','BAS residential Other includes water heating; no separate regional electricity input recovered','water/space thermal loads with conversion Links','yes if heat branch retained','historical electric water input and future conversions can overlap','AEO PDF69/printed67; U prepare_heat_data/add_heat'),
 ('Space heat','No separately recovered BAS electric-space-heating quantity','framework thermal heat construction','yes if heat branch retained','UNKNOWN magnitude; absent column is not zero','AEO residential end-use chapter; MY Table42/47; U add_heat'),
 ('Road electricity boundary only','BAS fuel-specific vehicle shares fixed;2050 transport electricity0.2%; ATS/CNS stronger shifts distinct','framework EV fractions configured; no implementation in this phase','charging flows can be endogenous; uptake fractions configured','existing/forecast electric traction included twice if not reconciled','AEO PDF48/65; frozen U land-transport constructor'),
 ('Industry electricity boundary only','BAS constant sector intensity and subsector shares; industrial GDP growth','direct industry Load plus process conversion capability','only conversions/dispatch retained by chosen boundary','generic growing electricity parent plus process electricity','AEO PDF48; U final adjustment industry redistribution'),
 ('Hydrogen electricity boundary only','AEO non-power transformation has H2/ammonia; BAS finalH2 printed0.0Mtoe; not proof of zero process input','electrolysis Link framework; power-only final config strips SC','electrolyser input endogenous if retained','DO NOT infer quantified BAS H2 duplication from rounded finalH2 row','AEO PDF56 and C.2 PDF183; U electrolysis'),
 ('Cooling','BAS appliance growth and commercial AC12.9Mtoe2025 to29.7Mtoe2050','retain cooling in R/S direct electricity','not separately endogenised this phase','none if subaccount only; yes if another cooling Load is added','AEO PDF70-71/printed68-69; MY Table42/47'),
 ('Efficiency and fuel switching','BAS latest appliance efficiency fixed; ATS/RAS/CNS policy and technology gains are separate scenarios','device costs/efficiencies config; no new adoption','tech dispatch conditional on framework','do not import CNS gains into BAS interpretation; device service boundary matters','AEO PDF48/53/56'),
 ('Cooking','BAS clean-cooking access/electrification evolves; R cooking end-use reported','NON-EXPLICIT + ACCOUNTING REQUIRED','no cooking conversion added in this phase','retain electric cooking direct and non-electric cooking fuel; not heat','AEO PDF48/69; MY Table42'),
]:scope.append(dict(Sector=sector,AEO8Representation=aeo_repr,CurrentPyPSARepresentation=current,ExogenousInAEO8='scenario-specific fixed inputs/assumptions; LEAP demand construction',EndogenousInFullSC=endogenous,PotentialDoubleCount=risk,Evidence=evidence,Status='VERIFIED_SOURCE_SCOPE; MAGNITUDE_AND_MAPPING_PENDING',HumanConfirmation='PENDING'))
save('AEO8_ELECTRIFICATION_SCOPE_MATRIX',scope)
metrics=dict(MY_conversion_GWh_per_ktoe=num(factor),R_water_GWh=num(rw),R_total_GWh=num(rt),R_without_water_GWh=num(rt-rw),S_water_GWh=num(sw),S_without_water_GWh=num(st-sw),R2016_water_input_share=num(D(70)/D(2333)),S2016_water_input_share=num(sw/st),R2019_balance_GWh=num(D(2715)*factor),S2019_balance_GWh=num(D(4086)*factor),annual_E3_closed=False,snapshot_test_run=False,useful_heat_numeric_ready=False,production_patch=False,solver_runs=0)
save('PROTOTYPE_METRICS',metrics)
print(json.dumps(dict(ledger_rows=len(ledger),source_records=len(registry),glossary=len(gloss),scope_matrix=len(scope),closure_checks=len(tests),metrics=metrics),indent=2))
