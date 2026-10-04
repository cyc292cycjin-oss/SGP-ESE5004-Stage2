"""Deterministic, source-bounded candidate tables. Never produces accepted model input.

Raw quantities retain source units; unknown shares/performance remain blank.
PDF values are transcriptions at the cited table/page, not pixel estimates.
"""
from pathlib import Path
from decimal import Decimal
import csv,hashlib,json,collections
R=Path(__file__).resolve().parent
ROOT=R.parents[3]
raw=R/'data/raw/buildings'; out=R/'data/derived/buildings';out.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((raw/'SOURCE_REGISTRY.json').read_text(encoding='utf8'))
sources={x['source_id']:x for x in reg}
versions={'ERIA_PILOT2013':('ERIA RPR FY2012 No.19 chapter1; 2013','2011-09 to 2012-02'),
 'MY_NEB2016':('National Energy Balance2016; released2018','2013-2016 table years; survey wave unresolved'),
 'BELDA2017':('ECEEE2017 paper','2014-10 to 2015-09'),
 'VN_WATER2018':('Toyosada et al.2018; paper82791','December observation; exact campaign year requires verification'),
 'AEO8':('8th ASEAN Energy Outlook2023-2050; 2024','base2022; forecasts2023-2050'),
 'AEO8_CORRIGENDUM':('November2024 corrigendum','2024'),
 'ESDM2019':('Handbook of Energy & Economic Statistics2019','2019'),
 'KH2019':('Cambodia Energy Statistics2019-2020; RPR2022-08','2019-2020'),
 'NEA2017':('NEA official news2018-05-05; Household Energy Consumption Study2017','2017'),
 'DEMANDCAST_PAPER':('arXiv2510.08000v1; 2025-10-09','2025'),
 'DEMANDCAST_RELEASE':('Zenodo18374352 version1.0.0; published2026-01-26','historical forecasts2000-2024'),
 'DEMANDCAST_TAG':('paper-cited v0.9.0; tree fe8454093c776138df78ae59b30db8e3c89ec7fa','2025'),
 'EMBER_METHOD':('Electricity data methodology v1.6; downloaded2026-10-02; not historical input vintage proof','current reference'),
 'PH_DOE_LEGACY':('Compendium Energy Statistics1990-2021; original PDF not retrieved','2011 HECS six-month period: index evidence only'),
 'PH_DOE_CURRENT':('Compendium Energy Statistics1990-2021; URL returned HTML','2011'),
 'PH_HECS2023_NOTES':('2023 HECS technical notes; native download403; browser text available','2023')}
for sid,(v,y) in versions.items():sources[sid].update(version=v,year=y)
sources['DEMANDCAST_RELEASE']['license']='CC BY4.0 per Zenodo metadata'
sources['MY_NEB2016']['purpose']='R/S end-use electricity, cooking by fuel and coverage evidence; not accepted national heat input'
for sid,url in [('GEGIS_AUTHOR_METHOD','https://github.com/niclasmattsson/GlobalEnergyGIS'),('PYPSA_EARTH_CURRENT_DEMAND_DOC','https://pypsa-earth.readthedocs.io/en/latest/tutorials/use-cases/3-demand-data/')]:
    if sid not in sources:
        item=dict(source_id=sid,url=url,resolved_url=url,file='',sha256='',version='Current web documentation read2026-10-02; not fixed input vintage',year='2026 access',
          license='Author repository/documentation terms; source description only',purpose='Auxiliary GEGIS annual/profile method description; no numeric input',access='WEB_READ_ONLY_NOT_ARCHIVED',status='UNVERIFIED')
        reg.append(item);sources[sid]=item
for rec in json.loads((R/'evidence/UNSD_RAW_IDENTITIES.json').read_text()):
    p=raw/'unsd'/rec['filename']; assert sha(p)==rec['sha256']
    sid='UNSD_'+p.stem
    if sid not in sources:
        entry=dict(source_id=sid,url='https://data.un.org/Explorer.aspx?d=EDATA',resolved_url='',
          file=p.relative_to(R).as_posix(),sha256=rec['sha256'],bytes=rec['bytes'],
          access='REUSED_LOCAL_RAW_EXPORT',version='UNdata export2025-05-02; original query URL not retained',year='candidate rows2019',
          license='UNdata original terms; no additional redistribution license inferred',
          purpose='R/S final-energy calibration candidates; original units; no end-use inference',status='UNVERIFIED')
        reg.append(entry);sources[sid]=entry
meta=json.loads((R/'evidence/LOCAL_DEMANDCAST_METADATA.json').read_text())
if 'LOCAL_DEMANDCAST_TUTORIAL' not in sources:
    p=raw/'local-tutorial-demandcast.parquet';assert sha(p)==meta['sha256']
    reg.append(dict(source_id='LOCAL_DEMANDCAST_TUTORIAL',url='https://sandbox.zenodo.org/records/493116',
      file=p.relative_to(R).as_posix(),sha256=meta['sha256'],bytes=meta['bytes'],version='retained tutorial artifact; relationship to full archive unverified',
      year='2013 hourly',license='upstream tutorial bundle terms; exact redistribution terms unverified',purpose='verify actual local profile identity',
      access='REUSED_LOCAL_RAW',status='UNVERIFIED'))
(raw/'SOURCE_REGISTRY.json').write_text(json.dumps(reg,indent=2,ensure_ascii=False),encoding='utf8')
fields=next(csv.reader((ROOT/'data_registry/buildings_phase3a4/BUILDINGS_USEFUL_HEAT_INPUT_TEMPLATE.csv').open(encoding='utf-8-sig')))
extra=['CandidateID','SourceID','Coverage','RowRole','CookingDestination','Blocker']
rows=[]
def add(sid,**kw):
    s=sources[sid];r={f:'' for f in fields+extra}
    r.update(SourceID=sid,Source=sid,SourceURL=s.get('resolved_url') or s['url'],SourceFile=s['file'],SourceSHA256=s['sha256'],
      PublicationVersion=s['version'],TargetYear=2019,Status='UNVERIFIED',HumanConfirmationRecord='PENDING',
      RowRole='NON_ADDITIVE_CANDIDATE',UsefulServiceBoundary='space/water service at building delivery point; not yet quantified')
    r.update(kw);r['CandidateID']=f'E3C{len(rows)+1:04d}';rows.append(r);return r
classified=json.loads((R.parent.parent/'buildings_heat_alignment/data/processed/buildings/UNSD_2019_BUILDINGS_CLASSIFIED.json').read_text())
byfile=collections.defaultdict(list)
for r in classified:byfile[r['source_file']].append(r)
matched=[]
for name,targets in sorted(byfile.items()):
    with (raw/'unsd'/name).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f,delimiter=';');found=collections.defaultdict(list)
        for ix,v in enumerate(reader,start=2):
            if v.get('Year') not in ['2019','2019.0']:continue
            for j,t in enumerate(targets):
                if v['Country or Area']==t['Country or Area'] and v['Commodity - Transaction']==t['Commodity - Transaction'] and v['Unit']==t['Unit']:
                    found[j].append((ix,reader.line_num,v))
    for j,t in enumerate(targets):
        assert len(found[j])==1,(name,t,found[j])
        record,line,v=found[j][0];elec=t['fuel']=='Electricity'
        delta=abs(Decimal(v['Quantity'])-Decimal(str(t['Quantity'])))
        assert delta<=max(Decimal('0.000000001'),abs(Decimal(v['Quantity']))*Decimal('1e-12')),(t,v,delta)
        r=add('UNSD_'+Path(name).stem,Country=t['ISO2'],Sector=t['sector'].title(),Region='National',Fuel=t['fuel'],
          FinalEnergy=v['Quantity'],FinalEnergyUnit=v['Unit'],FinalEnergyScope='fuel_total',EnergyBasis='reported final energy / fuel quantity',
          EndUse='unclassified',AccountID='B/C/F/G/D/E unpartitioned' if elec else 'M or H/I or other unclassified',
          SourceRowID=f'{name}:record{record}',SourceLocation=f'CSV record {record} (header=1), physical end line {line}; {v["Commodity - Transaction"]}',
          SourceYear=2019,YearBridge='same year; boundary harmonisation pending',Coverage='National R/S transaction; not end-use/device split',
          RetainedDestination='DirectElectricity_unpartitioned' if elec else 'DirectFuel_unclassified_pending_mapping',
          CookingDestination='Unclassified',Transformation='Exact raw row match; no model conversion-factor adoption; no share/efficiency invented',
          Blocker='End-use split; historical electric heat; device input share/performance; meter boundary; human acceptance'+('' if elec else '; calorific/unit basis'))
        matched.append(dict(candidate=r['CandidateID'],source_file=name,record=record,physical_end_line=line,quantity=v['Quantity'],unit=v['Unit'],prior_JSON_quantity=t['Quantity'],prior_precision_difference=str(delta)))
assert len(matched)==92

def my(sector,enduse,fuel,value,unit,loc,year=2016,scope='end_use',role='NON_ADDITIVE_SOURCE_ENDUSE'):
    cooking='DirectElectricity' if enduse=='cooking' and fuel=='electricity' else ('DirectFuel' if enduse=='cooking' else 'Unclassified')
    dest='ThermalEvidence_pending_conversion' if enduse in ['water','space'] else ('DirectElectricity' if fuel=='electricity' else 'DirectFuel')
    account={'water':'E/I','space':'D/H','cooking':'M','cooling':'F','lighting':'G','appliances':'G','other':'G/unclassified'}.get(enduse,'')
    return add('MY_NEB2016',Country='MY',Sector=sector,Region='Peninsular survey basis; table aggregate extent to verify',Fuel=fuel,
      FinalEnergy=value,FinalEnergyUnit=unit,FinalEnergyScope=scope,EndUse=enduse,EndUseShare=1 if scope=='end_use' else '',
      ShareDenominator='already end-use-specific input; identity, not empirical share',EnergyBasis='reported final energy',
      UnitConversion='GWh to MWh: multiply1000 (SI prefix)' if unit=='GWh' else '',HistoricalElectricHeating=value*1000 if unit=='GWh' and fuel=='electricity' and enduse in ['space','water'] else '',
      AccountID=account,SourceRowID=f'MY-{year}-{sector}-{fuel}-{enduse}',SourceLocation=loc,SourceYear=year,
      YearBridge=f'{year} absolute quantity retained; structure-to2019 proposal not applied',Coverage='Official aggregate; survey limited to Peninsular Malaysia; no Sabah/Sarawak representativeness proof',
      RetainedDestination=dest,CookingDestination=cooking,RowRole=role,Transformation='Reported end-use value; no useful-heat calculation',
      Blocker='Coverage/national expansion and source rounding; year bridge; device energy shares and historical seasonal performance; human acceptance'+('; ktoe energy convention/conversion pending' if unit=='ktoe' else ''))
for use,val in [('cooling',327),('water',70),('lighting',233),('cooking',117),('appliances',1586)]:my('Residential',use,'electricity',val,'ktoe','PDF95 / printed95 Table42 (2016)')
my('Residential','cooking','gas',1,'ktoe','PDF95 Table42 gas row')
my('Residential','cooking','LPG',538,'ktoe','PDF95 Table42 LPG row')
my('Residential','lighting','kerosene',3,'ktoe','PDF95 Table42 kerosene row')
for use,val in [('cooling',16440.66),('water',1034.62),('lighting',8516.23),('other',13114.06)]:my('Services',use,'electricity',val,'GWh','PDF103 / printed103 Table47 total row (2016)')
for yr,v,p,t in [(2013,59,94,39),(2014,61,94,40),(2015,63.48,95,41)]:my('Residential','water','electricity',v,'ktoe',f'PDF{p} Table{t} electricity water-heating cell',yr,role='YEAR_BRIDGE_COMPARATOR_NOT_ADDITIVE')
add('NEA2017',Country='SG',Sector='Residential',Region='National',Fuel='electricity',FinalEnergy=7295,FinalEnergyUnit='GWh',FinalEnergyScope='fuel_total',
    EnergyBasis='reported household electricity consumption',UnitConversion='GWh to MWh: multiply1000',EndUse='unclassified',SourceRowID='NEA2017-national-electricity',SourceLocation='2018-05-05 release paragraph: households consumed7295GWh in2017',SourceYear=2017,
    YearBridge='2017 retained; 2019 bridge not applied',Coverage='All Singapore households aggregate; separate typical-home shares not assumed energy-weighted',
    RetainedDestination='DirectElectricity_unpartitioned',CookingDestination='Unclassified',AccountID='B/D/E/F/G unpartitioned',
    Transformation='Retain reported aggregate without multiplying by typical-home percentages',Blocker='Typical-home share denominator/weights; historical performance; year bridge')
for use,share,account in [('water',0.11,'E/I'),('cooling',0.24,'F')]:
    add('NEA2017',Country='SG',Sector='Residential',Region='Typical home, not national expansion',Fuel='electricity',FinalEnergyScope='fuel_total',
      EndUse=use,EndUseShare=share,ShareDenominator='typical-home total electricity (not proven national energy-weighted mean)',
      SourceRowID='NEA2017-typical-'+use,SourceLocation='2018-05-05 release typical-home appliance shares',SourceYear=2017,
      YearBridge='2017 share only; no national/year transfer',Coverage='Typical household; weighting methodology not recovered',
      RetainedDestination='ThermalEvidence_pending_conversion' if use=='water' else 'DirectElectricity',AccountID=account,
      Transformation='Percent to fraction only; FinalEnergy and UsefulService intentionally blank',
      RowRole='SHARE_ONLY_NOT_MULTIPLIED_BY_NATIONAL_TOTAL',CookingDestination='Unclassified',Blocker='National representativeness/energy weights; device input shares/performance; year bridge')
water={'rural':dict(KH=134.2,VN=530.7,ID=570.9,PH=667.6,TH=144.0,MY=396.2),'urban':dict(KH=173.0,LA=456.5,VN=52.1,ID=373.7,PH=55.4,TH=10.6,MY=382.9,SG=273.7)}
cooking={'rural':dict(KH=1653.4,VN=1923.2,ID=1768.8,PH=676.1,TH=668.2,MY=678.1),'urban':dict(KH=547.0,LA=979.2,VN=376.3,ID=579.2,PH=238.1,TH=100.7,MY=555.3,SG=410.7)}
for use,values in [('water',water),('cooking',cooking),('space',{'urban':dict(KH=2.1,SG=2.1)})]:
    for region,countries in values.items():
        for c,val in countries.items():
            add('ERIA_PILOT2013',Country=c,Sector='Residential',Region=region+' convenience sample',Fuel='mixed fuels; allocation unavailable',FinalEnergy=val,
              FinalEnergyUnit='Mcal/household',FinalEnergyScope='end_use',EnergyBasis='reported household end-use energy; period/energy convention unresolved',
              EndUse=use,EndUseShare=1,ShareDenominator='already end-use-specific sample quantity; scope identity',SourceRowID=f'ERIA-T11-{region}-{c}-{use}',
              SourceLocation=f'PDF56 / printed55 Table11 {region} {c} {use}',SourceYear='2011-09 to 2012-02',
              YearBridge='No annualisation; no2019 transfer',Coverage='112 convenience households in8countries; regional sample quantity, not country total',
              RetainedDestination='Unclassified' if use=='cooking' else 'ThermalEvidence_pending_fuel_performance_and_coverage',
              CookingDestination='Unclassified',AccountID='M' if use=='cooking' else ('D/H' if use=='space' else 'E/I'),
              RowRole='LOCAL_MIXED_FUEL_SAMPLE_NOT_NATIONAL',Transformation='Transcribed source table only; no fuel split, annualisation, national expansion or efficiency',
              Blocker='Recall/aggregation period and unit convention; fuel split; nonprobability sample; device performance; year/region transfer')

countries=['BN','KH','ID','LA','MY','MM','PH','SG','TH','TL','VN']
matrix=[]
mf='Country Sector EndUse SourceYear TargetYear RawElectricity Unit Coverage Geography DeviceType Observed_or_Derived Source SourceURL SourceFile SourceSHA256 SourceLocation YearBridge TemporalEvidence SpatialEvidence Status HumanConfirmation'.split()
for c in countries:
 for sec in ['Residential','Services']:
  for use in ['space','water']:
    r={k:'' for k in mf};r.update(Country=c,Sector=sec,EndUse=use,TargetYear=2019,Status='PENDING',HumanConfirmation='PENDING',Coverage='No adequate national electricity/end-use observation recovered in bounded source set',YearBridge='NOT_ESTABLISHED',TemporalEvidence='NOT_ESTABLISHED',SpatialEvidence='NOT_ESTABLISHED',Observed_or_Derived='UNKNOWN',EvidenceNote='Missing is not zero')
    sid=None
    if c=='MY':
      sid='MY_NEB2016';r.update(SourceYear=2016,Geography='Peninsular survey; table expansion needs confirmation',Coverage='R2000households / S5000premises survey; not proven nationwide end-use coverage',SourceLocation='PDF95 Table42' if sec=='Residential' else 'PDF103 Table47',EvidenceNote='No space column is not measured zero')
      if use=='water':r.update(RawElectricity=70 if sec=='Residential' else 1034.62,Unit='ktoe' if sec=='Residential' else 'GWh',Observed_or_Derived='REPORTED_AGGREGATE',Status='UNVERIFIED',EvidenceNote='Historical final electricity reported; device/performance unknown; no2019 substitution')
    elif c=='SG' and sec=='Residential':
      sid='NEA2017';r.update(SourceYear=2017,Geography='Singapore typical home',SourceLocation='2018-05-05 NEA release appliance shares',EvidenceNote='11% water-heater share of typical-home electricity; no national heat quantity; space unknown',Observed_or_Derived='SHARE_ONLY' if use=='water' else 'UNKNOWN')
    elif c=='PH' and sec=='Residential' and use=='water':
      sid='PH_DOE_LEGACY';r.update(SourceYear=2011,Geography='Philippines national survey',SourceLocation='Compendium1990-2021 Table2; indexed text only',Observed_or_Derived='INDEX_ONLY',EvidenceNote='2011 period six months; 3.4%/484kWh per user indexed; original PDF missing, no annualisation')
    elif sec=='Residential' and c in ['VN','TH','KH','ID','LA']:
      sid='BELDA2017' if c in ['VN','TH'] else 'ERIA_PILOT2013';r.update(SourceYear='2014-2015' if sid=='BELDA2017' else '2011-2012',Geography='Selected local urban/rural samples',SourceLocation='PDF6 heating discussion' if sid=='BELDA2017' else 'PDF56 Table11',Observed_or_Derived='LOCAL_MIXED_FUEL_OR_QUALITATIVE',EvidenceNote='End-use evidence does not identify national electric heat; VN Hanoi/HoaBinh local space heat; no country zero')
    if sid:
      s=sources[sid];r.update(Source=sid,SourceURL=s.get('resolved_url') or s['url'],SourceFile=s['file'],SourceSHA256=s['sha256'])
    matrix.append(r)
assert len(matrix)==44

groups=['electricity','gas','LPG/oil','biomass','coal','heat commodity','others']
def fuelgroup(f):
 f=f.lower()
 if f=='electricity':return 'electricity'
 if f in ['gas'] or 'natural gas' in f:return 'gas'
 if any(t in f for t in ['lpg','petroleum','oil','gasoline','kerosene']):return 'LPG/oil'
 if f in ['biodiesel','biogases','charcoal','fuelwood']:return 'biomass'
 if 'coal' in f:return 'coal'
 if f=='heat':return 'heat commodity'
 return 'others'
end=[]
for c in countries:
 for sec in ['Residential','Services']:
  for g in groups:
    rr=[r for r in rows if r['Country']==c and r['Sector']==sec and fuelgroup(r['Fuel'])==g]
    e=dict(Country=c,Sector=sec,FuelGroup=g)
    for use in ['space','water','cooking','cooling','other','unclassified']:
      usable=[r for r in rr if r['EndUse']==use or (use=='other' and r['EndUse'] in ['lighting','appliances'])]
      e[use+'_evidence']='; '.join(r['CandidateID'] for r in usable) or 'UNKNOWN'
    e.update(FinalEnergyCandidateRows='; '.join(r['CandidateID'] for r in rr if r['FinalEnergyScope']=='fuel_total'),
      CookingDestination='; '.join(sorted({r['CookingDestination'] for r in rr if r['EndUse']=='cooking'})) or 'Unclassified',
      SourceIDs='; '.join(sorted({r['SourceID'] for r in rr})),
      Coverage='See row-specific geography; local samples and national totals must not be added',
      Blocker='Fuel totals do not imply end-use shares; missing cells are unknown, not zero',Status='UNVERIFIED',HumanConfirmation='PENDING')
    end.append(e)
assert len(end)==154
for name,data in [('ASEAN_BUILDINGS_HISTORICAL_ELECTRIC_HEATING_MATRIX',matrix),('ASEAN_BUILDINGS_ENDUSE_EVIDENCE_MATRIX',end),('BUILDINGS_USEFUL_HEAT_INPUT_CANDIDATES',rows)]:
    (out/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
checks=dict(raw_UNSD_rows_matched=len(matched),raw_matches=matched,candidate_rows=len(rows),historical_matrix_rows=len(matrix),enduse_matrix_rows=len(end),
  candidates_by_source=dict(collections.Counter(r['SourceID'] for r in rows)),
  source_arithmetic_checks={'MY_R2016_electric_enduses_sum_ktoe':sum([327,70,233,117,1586]),'MY_R2016_printed_electric_total_ktoe':2333,
    'MY_R2016_cooking_cells_ktoe':656,'MY_R2016_printed_cooking_total_ktoe':655,
    'MY_S2016_enduses_sum_GWh':str(sum(map(Decimal,['16440.66','1034.62','8516.23','13114.06']))),
    'MY_S2016_printed_total_GWh':'39106.00','MY_S2016_unreconciled_residual_GWh':'0.43',
    'action':'Preserve source values; no residual allocation or renormalisation'},
  MY_R_electric_water_shares={str(y):{'water_ktoe':v,'total_ktoe':t,'ratio':v/t} for y,v,t in [(2013,59,1971),(2014,61,2041),(2015,63.48,2116),(2016,70,2333)]},
  MY_S2016_electric_water_share=1034.62/39106.00,
  useful_service_values_filled=sum(r['UsefulService']!='' for r in rows),historical_performance_values_filled=sum(r['Efficiency_or_COP']!='' for r in rows),human_accepted_rows=0)
(R/'data/processed/buildings/CANDIDATE_SOURCE_CHECKS.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in checks.items() if k not in ['raw_matches','candidates_by_source']},indent=2))
