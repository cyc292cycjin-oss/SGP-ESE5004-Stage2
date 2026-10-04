"""Build data identities from prior immutable manifests and this round's receipts."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;P=R.parent/'buildings_heat';E=P/'evidence'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
rows=[];cs='BN;KH;ID;LA;MY;MM;PH;SG;TH;TL;VN'
def add(**kw):
    row=dict(source_id='',source_family='',name='',official_url='',version='',year='',filename='',sha256='',unit='',countries=cs,sector='Residential;Services',purpose='',transformation_script='',status='UNVERIFIED',human_confirmation='PENDING',access='',notes='')
    row.update(kw);rows.append(row)
raw=read(E/'UNSD_2019_BUILDINGS_ROWS.json');urls={r['Unnamed: 0'].strip():r['Link'] for r in read(E/'UNSD_DOWNLOAD_REGISTRY.json')}
for r in read(E/'LOCAL_INPUT_HASHES.json'):
    p=Path(r['path']);rs=[x for x in raw if x['source_file']==p.name]
    if rs:
        fuel=rs[0]['Commodity - Transaction'].split(' - ')[0]
        add(source_id='UNSD_RAW_'+p.stem,source_family='UNSD2019_RAW',name=fuel,official_url=urls.get('Total Electricity' if fuel=='Electricity' else fuel) or 'https://data.un.org/Explorer.aspx?d=EDATA',version='retained UNdata export named 20250502; not refetched',year=2019,filename=r['path'],sha256=r['sha256'],unit=';'.join(sorted({x['Unit'] for x in rs})),countries=';'.join(sorted({x['ISO2'] for x in rs})),purpose='Original R/S final-energy rows; not useful-heat measurements',transformation_script='extract_accounting.py -> _helpers.get_conv_factors/aggregate_fuels',access='RETAINED_LOCAL_ORIGINAL',notes='Auditable 92-row subset in prior evidence; per-country absent commodity is not a measured zero.')
    elif p.name.startswith('energy_totals_'):
        add(source_id='T_ANNUAL_'+p.stem,source_family='T_ANNUAL',name=p.name,official_url='https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/tree/ce327bfae2abe5526d4c1976173f0f8d08366ba5',version='retained tutorial artifacts; input hashes from Phase 3A-1',year=p.stem.split('_')[-1],filename=r['path'],sha256=r['sha256'],unit='TWh; mixed thermal-service/fuel basis',purpose='Diagnostic only; never label as U full-year result',transformation_script='build_base_energy_totals.py; prepare_energy_totals.py',access='RETAINED_LOCAL_ORIGINAL')
    elif 'heat_demand_s' in p.name:
        add(source_id='T_HEAT_'+p.stem,source_family='T_HEAT',name=p.name,official_url='https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/tree/ce327bfae2abe5526d4c1976173f0f8d08366ba5',version='tutorial six days, 2013 weather; saved hourly heat preprocessing',year=p.stem.split('_')[-1],filename=r['path'],sha256=r['sha256'],unit='MW; annual quantity normalized into selected snapshots',purpose='Reused positive-annual/NaN profile evidence',transformation_script='prepare_heat_data.py; prior validate_accounting.py',access='RETAINED_LOCAL_ORIGINAL')
families={'heat_load_profile_BDEW.csv':'BDEW','fuel_shares.csv':'FUEL_SPLIT','district_heating.csv':'DH_DEFAULT','growth_factors_cagr.csv':'GROWTH_DEFAULT','efficiency_gains_cagr.csv':'EFFICIENCY_DEFAULT','existing_heating_raw.csv':'EU_STOCK','config.default.yaml':'DEFAULT_CONFIG','config.asean.yaml':'ASEAN_CONFIG','_helpers.py':'U_HELPERS','Energy_Statistics_Database.xlsx':'UNSD_DOWNLOAD_MAP'}
national=read(R/'data/processed/buildings/UNSD_2019_NATIONAL_ELECTRICITY.json')
add(source_id='UNSD2019_ELEC_TOTAL',source_family='UNSD2019_ELEC_TOTAL',name='2019 national electricity final energy consumption',official_url=urls['Total Electricity'],version='retained UNdata export named 20250502; not refetched',year=2019,filename=national['source_file'],sha256=national['source_sha256'],unit='million kWh -> TWh /1000',purpose='National final electricity denominator; not generation or measured residual',transformation_script='extract_accounting.py',access='RETAINED_LOCAL_ORIGINAL')
for r in read(P/'SOURCE_MANIFEST.json')['source_files']:
    if r['layer']!='upstream' or Path(r['path']).name not in families:continue
    fam=families[Path(r['path']).name];p=P/'source_snapshot/upstream'/r['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
    add(source_id=fam,source_family=fam,name=r['path'],official_url=f"https://github.com/pypsa-meets-earth/pypsa-asean/blob/{r['sha']}/{r['path']}",version=r['sha'],year='2012' if fam=='EU_STOCK' else 'not specified / config-dependent',filename='../buildings_heat/source_snapshot/upstream/'+r['path'],sha256=r['sha256'],unit='GW' if fam=='EU_STOCK' else 'dimensionless profiles / parameter-specific',countries='EU28+3; no ASEAN stock rows' if fam=='EU_STOCK' else cs,purpose='Frozen current-model source; not human-accepted ASEAN data',transformation_script='see BUILDINGS_HEAT_BASELINE_MAP.md',access='IMMUTABLE_GIT_SNAPSHOT',notes='DEFAULT fallback is not country-specific evidence.')
meta={
 'AEO8':('8th ASEAN Energy Outlook','2024 edition, official current downloadable bytes; corrigendum separate','historical 2005-2022; end-use details projection 2023+','Mtoe; appliance shares','ASEAN10; TL not covered','Regional source-family and end-use boundary check; not 2019 end-use input'),
 'AEO8_CORRIGENDUM':('AEO8 corrigendum notice','official notice downloaded separately','2024','page/figure corrections','ASEAN10','Check candidate report version, do not silently replace'),
 'ESDM2019':('HEESI 2019, ESDM','2019 edition, published 2020','2019','original fuel units; GWh; thousand BOE','ID','Same-year R/S definition and raw-value comparison, not replacement'),
 'KH2019':('Cambodia Energy Statistics 2000-2019, MME/ERIA','ERIA RPR 2022 No.08, September 2022','2000-2019','ktoe; GWh; kt','KH','Country balance candidate; some sectoral consumption estimated'),
 'NEA2017':('NEA household energy consumption study','official news 5 May 2018; study 2017','2017','shares of household electricity','SG; residential only','Check that cooling/water heating coexist inside residential electricity'),
 'COOLING2022':('Roadmap towards sustainable and energy-efficient space cooling in ASEAN','ACE official landing, 6 June 2022; author IEA','2022 report','aggregate cooling electricity','ASEAN report; not an 11-country R/S input table','Regional cooling boundary context; landing metadata only'),
 'IEAENDUSE2026':('Energy End-uses and Efficiency Indicators','June 2026 product metadata only','2000-2024','final energy by product/end use; see product','IEA members and beyond; ASEAN coverage not verified','Candidate metadata only; no paid data obtained; not harmonized 11-country table'),
}
for r in read(R/'data/raw/buildings/RETRIEVAL_MANIFEST.json'):
    name,ver,year,unit,coverage,purpose=meta[r['source_id']]
    add(source_id=r['source_id'],source_family=r['source_id'],name=name,official_url=r['official_url'],version=ver,year=year,filename=r['filename'],sha256=r['sha256'],unit=unit,countries=coverage,purpose=purpose,transformation_script='retrieve_candidates.py; inspect_candidate_pdfs.py',access=r['access'],notes='Candidate only. Retrieval URL/time/byte count in RETRIEVAL_MANIFEST.json; raw PDFs/HTML ignored by Git.')
for p in sorted((R/'data/processed/buildings').glob('*.json')):
    add(source_id=p.stem,source_family='AUDIT_DERIVED',name=p.stem,official_url='https://data.un.org/Explorer.aspx?d=EDATA',version='Phase 3A-2 deterministic audit extraction',year=2019,filename=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),unit='raw quantities + diagnostic TWh equivalents',purpose='Reviewable exact subset; model values untouched',transformation_script='extract_accounting.py',access='GIT_REVIEWABLE_JSON')
# Weather and population: identify existing receipts rather than fabricate missing binary hashes.
for sid,url,unit,note in [('ERA5','https://cds.climate.copernicus.eu/','K; hourly weather','Existing tutorial cutout identity follows previous audit; no new weather download. Exact accepted future cutout hash still pending.'),('WORLDPOP','https://www.worldpop.org/','population','Frozen config selects standard WorldPop and 2020 shapes; accept resolution/date separately.'),('UNCTAD_URBAN','https://unctadstat.unctad.org/','urban population share','Live US.PopTotal request is not a pinned country-year input version.')]:
    add(source_id=sid,source_family=sid,name=sid,official_url=url,version='source family only; see frozen population/weather scripts',year='2013 weather / 2020 shapes / planning-year urban shares',filename='NOT_COPIED_IN_THIS_ROUND',sha256='PENDING_EXACT_RESEARCH_INPUT',unit=unit,purpose='Annual spatial allocation and temporal shape source; no inferred binary identity',transformation_script='build_heat_demand.py; build_population_layouts.py; prepare_urban_percent.py',access='SOURCE_FAMILY_IDENTIFIED',notes=note)
(R/'data/derived/buildings/REGISTRY_RECORDS.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))
assert len({r['source_id'] for r in rows})==len(rows)
print(json.dumps({'registry_rows':len(rows),'human_confirmation':'all PENDING'}))
