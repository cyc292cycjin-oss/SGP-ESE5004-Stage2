"""Rebuild audit records from immutable local source files and test receipts."""
from pathlib import Path
import ast, csv, hashlib, json, re
R=Path(__file__).resolve().parent
D=R/'data/derived/buildings';D.mkdir(parents=True,exist_ok=True)
OLD=R.parent/'buildings_heat_alignment'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
summaries=[]; matrix=[]
key=lambda r:(r['case'],r['country'],r['sector'],r['metric'])
for fix in ['E1','E2','E4']:
    before=json.loads((R/f'evidence/{fix}_before.json').read_text())
    after=json.loads((R/f'evidence/{fix}_after.json').read_text())
    bi={key(x):x for x in before['rows']}
    for row in after['rows']:
        pre=bi.get(key(row));assert pre is not None, key(row)
        matrix.append(dict(fix=fix,case=row['case'],country=row['country'],sector=row['sector'],metric=row['metric'],
          before=pre['actual'],after=row['actual'],expected=row['expected'],unit=row['unit'],
          absolute_error=row['absolute_error'],relative_error=row['relative_error'],
          before_absolute_error=pre['absolute_error'],tolerance=row['tolerance'],
          before_test_status=pre['test_status'],test_status=row['test_status'],
          evidence_type='SYNTHETIC_FUNCTION_REGRESSION',detail=row['detail'],before_detail=pre['detail']))
    summaries.append(dict(fix=fix,before_rows=len(before['rows']),before_fail=sum(x['test_status']=='FAIL' for x in before['rows']),
      after_rows=len(after['rows']),after_fail=sum(x['test_status']=='FAIL' for x in after['rows']),
      max_after_MWh_error=max(x['absolute_error'] or 0 for x in after['rows'] if x['unit']=='MWh'),
      all_after_pass=after['all_pass']))
(D/'FIX_TEST_MATRIX.json').write_text(json.dumps(matrix,indent=2),encoding='utf8')
(R/'evidence/TEST_SUMMARY.json').write_text(json.dumps(summaries,indent=2),encoding='utf8')

meta=[
dict(source_id='ERIA_PILOT2013',name='ERIA revised residential pilot survey',version='June 2013; RPR2012-19 chapter1 section5',year='Sep2011-Feb2012; revised2012',countries='KH;ID;MY;PH;LA;SG;TH;VN',sector='Residential',end_use='space heating; water heating; cooking; cooling; electricity/fuels',unit='Mcal/household; percent; monthly period in section5.5.1',energy_basis='Final energy estimated from fuels/appliance use; not useful heat',location='PDF49 Table6; PDF56-57 Table11',public_private='PUBLIC_REPORT; no respondent microdata retrieved',license='No explicit open-data license verified in inspected section',purpose='B1/B2 regional end-use categories and heterogeneity',quality_limit='112 convenience respondents; not country-representative; old reference period; country/table sample counts require checking before extraction',raw_value='Table11 reports end-use amounts; no annual ASEAN scaling performed',current_pypsa_value='DEFAULT space_heat_share=0.6; no survey mapping',transformation='None; no annualization; no final-to-useful conversion'),
dict(source_id='ERIA_COMMERCIAL2021',name='ERIA commercial building technical guidelines',version='October2021; FY2021 No14',year='Underlying Malaysia2016 table',countries='MY',sector='Services/commercial;12 categories',end_use='water heating; space cooling; lighting; other',unit='Table2.2 GWh; Figure2.2 label says ktoe (conflict)',energy_basis='Final electricity',location='PDF16-17 Table2.2; PDF18 Figure2.2',public_private='PUBLIC_REPORT',license='ERIA copyright2021; acknowledgement clause; no unrestricted dataset license assumed',purpose='B1 services source tracing, not direct adoption',quality_limit='Figure unit conflicts with table; traced to MY_NEB2016 Table47; model geography/sector mapping still pending',raw_value='Table2.2 water heating1034.62 GWh; total39106.00 GWh; Figure total39106 ktoe',current_pypsa_value='Services end-use not mapped',transformation='None; retain both labels and identify original source'),
dict(source_id='MY_NEB2016',name='Energy Commission Malaysia National Energy Balance2016',version='2016 edition; official release2018-08-29; current official migrated URL',year='R tables2011-2016; commercial2014-2016',countries='MY (survey described as Peninsular Malaysia)',sector='Residential; Services/commercial12 categories',end_use='Residential five end uses by fuel; commercial four electricity end uses',unit='Residential ktoe; commercial GWh',energy_basis='Final energy/final electricity, not useful heat',location='PDF92 survey; PDF95 Table42; PDF98 coverage; PDF103 Table47',public_private='PUBLIC_REPORT; microdata not retrieved',license='No explicit open-data redistribution license verified; cite Energy Commission',purpose='B1/B2 strongest new national-agency source family; electric heat/cooking accounting',quality_limit='2000 household survey; Peninsula scope; year mismatch to2019; stock scaling/method and East Malaysia coverage need confirmation; absence of space-heating column is not a measured zero',raw_value='2016 R: water heating70ktoe; cooking655ktoe; total2875ktoe. Commercial: water heating1034.62GWh; total39106.00GWh',current_pypsa_value='No automatic change to UNSD2019 or DEFAULT0.6',transformation='None; original units preserved; useful heat efficiency/COP not chosen'),
dict(source_id='PH_HECS2011',name='Philippines DOE compendium HECS2004 vs2011 tables',version='Compendium1990-2021; indexed official legacy PDF',year='2004;2011',countries='PH;regions',sector='Residential',end_use='electricity end uses including water heating and cooking',unit='households in1000; percent; kWh/household; recall period unresolved',energy_basis='Final electricity, not useful heat',location='Energy Surveys Table2 (indexed source; full page not locally retrieved)',public_private='PUBLIC_INDEXED_REPORT; raw PDF unavailable via current URLs',license='Not verified',purpose='B1/B2 candidate for official household end-use and regional coverage',quality_limit='Legacy DNS unavailable; currentURL returned non-PDF; survey period/weights and raw source pending; no raw values adopted',raw_value='',current_pypsa_value='No mapping established',transformation='None; no annualization'),
dict(source_id='BELDA2017',name='Murakoshi et al. ECEEE2017 Southeast Asia household survey',version='2017 proceedings; author-associated BELDA copy',year='Oct2014-Sep2015 energy data',countries='MY;TH;VN;KH (selected cities/villages)',sector='Residential',end_use='water heating; space heating; cooking; cooling; appliances',unit='GJ/household/year; percent; appliance-use survey',energy_basis='Final energy estimates, not useful heat',location='PDF2 Table1; PDF3 Table2; PDF5-6 end-use discussion/Fig3',public_private='PUBLIC_PAPER; microdata not retrieved',license='No explicit open-data license verified in PDF',purpose='B1/B2 country/climate heterogeneity; B3 usage-method lead',quality_limit='1190 respondents across selected areas; mixture of sampling methods; no all-country representativeness; do not digitize graph or extrapolate zeros',raw_value='Text: Hanoi/HoaBinh space heating less than1% of sample total energy; no national split extracted',current_pypsa_value='DEFAULT0.6 unvalidated; BDEW retained only as comparator',transformation='None; no graph-pixel digitization'),
dict(source_id='VN_WATER2018',name='Toyosada et al. Vietnam future water usage controlled living experiment',version='JWARP10(2),204-214; DOI10.4236/jwarp.2018.102012',year='Published2018; December winter experiment; 2014 project attribution',countries='VN;Hanoi',sector='Residential;9 high-income households/35 persons',end_use='hot+cold water use; shower use/time',unit='L;L/min;hours; not MWh thermal',energy_basis='Water-volume/service observations; hot+cold combined profiles',location='HTML sections2.1-2.2; figures3-5; conclusion',public_private='PUBLIC_FULL_TEXT; no raw time-series retrieved',license='Publisher Creative Commons attribution indication; no license for unprovided microdata assumed',purpose='B3 local temporal-method candidate',quality_limit='Short overnight controlled stay; high-income sample; mixed hot+cold water; C1 excluded; no representative weekday/weekend or services profile',raw_value='Qualitative timing peaks near18:00,23:00,06:00 in test stay; not a full-year thermal profile',current_pypsa_value='BDEW water profile flat; no replacement',transformation='None; temperature difference/flow separation not inferred'),
dict(source_id='VN_TUYHOA2019',name='Le and Pitts electrical appliance survey TuyHoa',version='Energy and Buildings197:229-241; DOI10.1016/j.enbuild.2019.05.051',year='Survey2017;publication2019',countries='VN;TuyHoa',sector='Residential;60 households',end_use='cooling;LPG cooking;appliances; electricity',unit='kWh/household/year;percent',energy_basis='Final energy',location='Publisher/repository abstract; full repository PDF inaccessible locally403',public_private='PUBLIC_METADATA; raw PDF unavailable locally',license='Full-text/microdata license not verified',purpose='B1 accounting and materiality check only',quality_limit='One city; abstract-level evidence only; no useful heat or hourly hot-water data retrieved',raw_value='Abstract cooking gas25.6% and cooling31.9% of sample total; not ASEAN estimates',current_pypsa_value='Cooking not an independent module',transformation='None'),
dict(source_id='ACE_MY_SURVEYS',name='ACE Malaysia survey benchmarking announcement',version='Official ACE article; candidate discovery metadata',year='Prior R survey2016; commercial2018 mentioned',countries='MY',sector='Residential;commercial',end_use='End-use survey programme; no numeric table',unit='N/A(metadata)',energy_basis='Metadata only',location='Article body',public_private='PUBLIC_LANDING',license='Website terms; dataset license not verified',purpose='Discovery of official survey family and follow-up metadata',quality_limit='Announcement does not provide survey raw records; cannot replace source table',raw_value='',current_pypsa_value='No mapped value',transformation='None'),
]
retrieval={r['source_id']:r for r in json.loads((R/'data/raw/buildings/RETRIEVAL_MANIFEST.json').read_text())}
candidates=[]
for m in meta:
    f=retrieval[m['source_id']]
    candidates.append({**m,'official_url':f['official_url'],'filename':f['filename'] if f['access']=='RETRIEVED' else '',
      'sha256':f.get('sha256',''),'resolved_url':f.get('resolved_url',''),'access':f['access'],'transformation_script':'build_evidence.py (metadata only; no model-input transform)',
      'final_candidate_value':'','status':'UNVERIFIED','human_confirmation':'PENDING'})
(D/'DATA_CANDIDATES.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2),encoding='utf8')
with (OLD/'BUILDINGS_DATA_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as f:registry=list(csv.DictReader(f))
for row in registry:
    # Preserve old record contents; make relative identities usable from new table.
    if row['filename'].startswith('data/') or row['filename'].startswith('evidence/'):
        row['filename']='../buildings_heat_alignment/'+row['filename']
for c in candidates:
    registry.append(dict(source_id=c['source_id'],source_family='PHASE3A3_BUILDINGS',name=c['name'],official_url=c['official_url'],
      version=c['version'],year=c['year'],filename=c['filename'],sha256=c['sha256'],unit=c['unit'],countries=c['countries'],
      sector=c['sector'],purpose=c['purpose'],transformation_script=c['transformation_script'],status=c['status'],
      human_confirmation=c['human_confirmation'],access=c['access'],notes=c['quality_limit']+'; license='+c['license']))
assert len({x['source_id'] for x in registry})==len(registry)
(D/'DATA_REGISTRY_UPDATED.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2),encoding='utf8')

# Bounded static accounting/carrier trace from the pinned upstream snapshots.
S=R.parent/'buildings_heat/source_snapshot/upstream/scripts'
trace={}
for filename in ['prepare_sector_network.py','prepare_heat_data.py','prepare_energy_totals.py','build_base_energy_totals.py','build_demand_profiles.py','final_asean_adjustment.py']:
    p=S/filename;lines=p.read_text(encoding='utf-8').splitlines()
    trace[filename]=dict(sha256=sha(p),matches=[dict(line=i+1,text=s.strip()) for i,s in enumerate(lines)
      if re.search(r'services? electricity|cooking|cooling|chiller|cold storage|electric_heat_supply|elec_carrier|only_elec_network',s,re.I)])
(R/'evidence/CODE_SCOPE_TRACE.json').write_text(json.dumps(trace,indent=2),encoding='utf8')
print(json.dumps(dict(test_rows=len(matrix),candidates=len(candidates),registry=len(registry),summaries=summaries)))
