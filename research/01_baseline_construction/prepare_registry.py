"""Extract input identities and prepare review-table records; never confirm data."""
from engineering_review import *
import pypsa

def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

families=[
 ('UNSD','UNSD energy statistics','https://data.un.org/Explorer.aspx?d=EDATA','52 exports named 20250502; base year 2019','UNdata_Export_20250502_*.txt','national sector demand','UNVERIFIED','UN data terms; redistribution not established in this review','scripts/build_energy_totals.py; scripts/build_base_industry_totals.py'),
 ('GDP','Gridded GDP PPP','https://doi.org/10.5061/dryad.dk1j0','v2; available 1990–2015; 2015 selected','GDP_PPP_1990_2015_5arcmin_v2.nc','industrial spatial weights','UNVERIFIED','Verify dataset record license; large source manifest only','scripts/build_shapes.py; validate_industrial_recovery.py'),
 ('INDUSTRY','Industrial facilities and allocation inputs','https://github.com/pypsa-meets-earth/pypsa-asean/tree/a3616a68ee44592af6527ca9024a90f1956646ae','existing local inputs; facilities assembled upstream','industrial_database.csv; base_industry_totals_2030.csv','industrial allocation regression','UNVERIFIED','Mixed source terms; no new public binary publication','scripts/build_industrial_database.py; scripts/build_industrial_distribution_key.py'),
 ('TECHCOST','technology-data frozen family','https://github.com/PyPSA/technology-data/tree/ec22a1843632fd28ecb9a139ee5156faf23324a3','v0.13.2 / ec22a1843632fd28ecb9a139ee5156faf23324a3','costs_*.csv; source workbooks','technology costs','PENDING','Repository and original workbook terms must be distinguished','compile_cost_assumptions.py; append_cost_data.py; process_cost_data.py'),
 ('ELECTROLYSER_OVERRIDE','Author electrolyser investment override','https://github.com/PyPSA/technology-data/blob/ec22a1843632fd28ecb9a139ee5156faf23324a3/inputs/manual_input.csv','v0.13.2 author values, EUR2020/kW_e','manual_input.csv','preserve author investment curve','SOURCE_PARTIALLY_VERIFIED','Public table; private communications not recovered','add_manual_input in compile_cost_assumptions.py'),
 ('AEO8','ASEAN Energy Outlook 8 cost append','https://github.com/pypsa-meets-earth/pypsa-asean/tree/5bacad702ccfed17ad19ab510fa710651e966f2c/data','D15/D17/D18 at paper SHA','AEO8 cost tables','ASEAN cost replacement','PENDING','Already upstream tracked; retain source attribution; check original terms','scripts/append_cost_data.py'),
 ('WEATHER_TUTORIAL','Existing six-day weather geometry','https://github.com/pypsa-meets-earth/pypsa-asean','2013-03-01 to 2013-03-07; tutorial only','asean-2013-era5-tutorial.nc','geometry in allocation test; NOT formal weather','UNVERIFIED','Copernicus source terms; retain manifest','atlite indicator matrices'),
 ('WEATHER_PAPER','Official Asian weather bundle candidate','https://drive.google.com/file/d/11-Ax9tVks7oPjrZwG5v3C0x4OmMT_Pv8/view','ZIP member timestamp 2023-08-09; not an edition guarantee','bundle_cutouts_asia.zip -> cutout-2013-era5.nc','paper full-year source candidate','UNVERIFIED','Copernicus/source terms; 27.6 GB archive manifest only','retrieve_databundle_light.py; inspect_weather_archive.py'),
 ('GEOGRAPHY','Country/GADM/EEZ and cluster geometry','https://github.com/pypsa-meets-earth/pypsa-asean/blob/5bacad702ccfed17ad19ab510fa710651e966f2c/configs/bundle_config.yaml','local EEZ v11; existing tutorial GADM/regions','eez_v11.gpkg; gadm_shapes.geojson; regions_onshore_elec_s_50.geojson','spatial mapping and DAG inspection','UNVERIFIED','GADM/EEZ original terms; binary redistribution not cleared','build_shapes.py; build_bus_regions.py; cluster_network.py'),
 ('LANDCOVER','Protected areas / Copernicus / GEBCO','https://github.com/pypsa-meets-earth/pypsa-asean/blob/5bacad702ccfed17ad19ab510fa710651e966f2c/configs/bundle_config.yaml','GEBCO 2025; Copernicus LC100 2019; natura source uncertain','GEBCO_2025_sub_ice.nc; PROBAV*.tif; natura.tiff','renewable exclusions; paper DAG','UNVERIFIED','Mixed licenses; inspect upstream bundle terms','build_renewable_profiles.py'),
 ('GRID','Official prebuilt network','https://github.com/pypsa-meets-earth/pypsa-asean/tree/138ea07b21c55727c937831c396e80286b5ef586/data/osm-plus-prebuilt/0.1.1','osm-plus-prebuilt 0.1.1 (0.1 for comparison)','all_*_build_network.csv; modification_list.txt','topology diagnosis and power boundary','PENDING','Already upstream Git; OSM attribution/ODbL plus model repository licensing','base_network.py; simplify_network.py'),
 ('DEMAND','Electricity forecasts and sector demand scalers','https://github.com/pypsa-meets-earth/pypsa-asean/tree/a3616a68ee44592af6527ca9024a90f1956646ae','paper SSP vs current DemandCast; do not conflate','forecasts_on_historical_period.parquet; energy_totals_*.csv; growth files','electricity and future sector demand','PENDING','Upstream data and original-source terms vary','build_demand_profiles.py; build_energy_totals.py; build_industry_demand.py'),
 ('FLEET','Existing generation fleet','https://github.com/pypsa-meets-earth/pypsa-asean','existing tutorial compiled fleet; author source identity not fully recovered','powerplants.csv; powerplants_osm2pm.csv','existing capacity and lifetime','UNVERIFIED','Powerplantmatching and underlying source terms','build_powerplants.py; add_existing_baseyear.py'),
 ('RENEWABLE','Existing renewable profile intermediates','https://github.com/pypsa-meets-earth/pypsa-asean','tutorial spatial/temporal resolution only','profile_*.nc','renewable profiles; NOT formal-year input','UNVERIFIED','Derived from weather/landcover with their source terms','build_renewable_profiles.py'),
 ('POPULATION','Population and urban shares','https://github.com/pypsa-meets-earth/pypsa-asean','existing model inputs; source approval pending','pop_layout*.csv; urban_percent.csv','spatial service-demand allocation','UNVERIFIED','WorldPop/UN/World Bank source terms','build_population_layouts.py'),
 ('AUTHOR_RESULTS','Author reference networks','https://drive.google.com/file/d/194my_d3eotQ1GvsGGN5KOZGWOHEivoQy/view','results-asean-paper-v1; metadata SHA 5bacad70','baseline-aims-3H 2025; decarbonize-aims-3H 2050','reference evidence ONLY, not regenerated outputs','UNVERIFIED','No new redistribution of large author outputs','inspect_results.py'),
]

rows=[]
def add(path,family,stage,root=None):
    path=Path(path)
    if not path.is_file():return
    name=str(path.relative_to(root)) if root else str(path)
    if any(r['path']==name for r in rows):return
    rows.append(dict(source_id=family,path=name,bytes=path.stat().st_size,sha256=sha(path),stage=stage,
                     date='2026-10-01 audit; original retrieval date unknown',status='SOURCE_PARTIALLY_VERIFIED' if family=='ELECTROLYSER_OVERRIDE' else 'UNVERIFIED'))

old=json.loads((HERE.parent/'00_model_audit/INPUT_INVENTORY.json').read_text())
for r in old['files']:
    if 'file' not in r:continue
    rel=r['file'];p=OLD/rel
    if p.name=='.snakemake_timestamp':continue
    family=('UNSD' if '/unsd/data/' in rel or 'unsd_transactions' in rel else
            'TECHCOST' if 'costs_' in rel else 'AEO8' if 'aeo' in rel.lower() else
            'GRID' if '/osm-' in rel or '/transmission_projects/' in rel else
            'FLEET' if 'powerplants' in rel else 'RENEWABLE' if '/renewable_profiles/' in rel else
            'WEATHER_TUTORIAL' if rel.startswith('cutouts/') else
            'INDUSTRY' if any(x in rel for x in ['industr','ammonia','AL_production']) else 'DEMAND')
    add(p,family,'existing_model_input',OLD)
for p in (OLD/'data/GDP').glob('*'):add(p,'GDP','raw_NC' if p.suffix=='.nc' else 'INVALID_OLD_CACHE_DIAGNOSTIC',OLD)
for version in ['0.1','0.1.1']:
    for kind in ['buses','transformers','lines']:add(OLD/f'data/osm-plus-prebuilt/{version}/all_{kind}_build_network.csv','GRID','upstream_tracked_raw',OLD)
add(BASE/'upstream_sc_baseline/data/osm-plus-prebuilt/0.1.1/modification_list.txt','GRID','upstream_tracked_explanation',BASE/'upstream_sc_baseline')
d=OLD/'resources/baseline-aims-3H-tutorial'
for rel,fam in [('shapes/gadm_shapes.geojson','GEOGRAPHY'),('bus_regions/regions_onshore_elec_s_50.geojson','GEOGRAPHY'),('population_shares/pop_layout_elec_s_50_2030.csv','POPULATION'),('demand/base_industry_totals_2030.csv','INDUSTRY')]:add(d/rel,fam,'existing_intermediate_used_in_diagnostic',OLD)
for rel,fam in [('resources/industrial_database.csv','INDUSTRY'),('cutouts/asean-2013-era5-tutorial.nc','WEATHER_TUTORIAL'),('data/eez/eez_v11.gpkg','GEOGRAPHY'),('data/natura/natura.tiff','LANDCOVER')]:add(OLD/rel,fam,'existing_input_used_in_diagnostic',OLD)
cost=HERE.parent/'00_source_provenance/official/technology-data'
for p in (cost/'inputs').glob('*'):
    if p.is_file():add(p,'ELECTROLYSER_OVERRIDE' if p.name=='manual_input.csv' else 'TECHCOST','frozen_source_audit_copy',HERE.parent.parent)
for p in (cost/'outputs').glob('*.csv'):add(p,'TECHCOST','frozen_prepared_cost',HERE.parent.parent)
for p in (HERE.parent/'00_source_provenance/official/author_run/data').rglob('*.csv'):
    add(p,'AEO8','paper_tracked_cost_append',HERE.parent.parent)
for r in json.loads((HERE.parent/'00_source_provenance/RESULTS_MEMBER_HASHES.json').read_text()):
    add(HERE.parent/'00_source_provenance'/r['path'].replace('\\','/'),'AUTHOR_RESULTS','AUTHOR_OUTPUT_NOT_REPRODUCTION',HERE.parent.parent)
source_rows=[]
for ident,name,url,version,filename,use,status,license_,processing in families:
    hashes=sorted([r['sha256'] for r in rows if r['source_id']==ident])
    source_rows.append(dict(source_id=ident,name=name,official_source=url,version=version,date='2026-10-01 audit (not original retrieval)',filename=filename,
        sha256=hashlib.sha256('\n'.join(hashes).encode()).hexdigest() if hashes else '',hash_kind='SHA256_OF_SORTED_MEMBER_SHA256_LINES' if hashes else 'NOT_AVAILABLE',license=license_,used_for=use,status=status,retrieval_script='retrieve_registered_input.py (explicit pinned URL+hash required); upstream retrieval rules are evidence, not auto-update authority',processing_script=processing,member_hash_table='DATA_HASHES.csv',human_confirmation='PENDING'))

sector_rows=[]
specs=[
 ('electricity','electrical energy','AC; low voltage','renewables; thermal; distribution','Bus/Generator/Load/Link','generation/storage grid subject to existing minima and limits','v0.13.2 + AEO8','paper SSP; current DemandCast + final demand scaling','electricity.extendable_carriers; final_adjustment.only_elec_network','add_electricity.py','PENDING demand reconciliation; final electric pruning still true'),
 ('hydrogen','conversion/end use','H2','electrolysis; SMR; SMR CC; fuel cell; turbine','Bus/Link/Store','conversion and tanks yes; H2 network false','v0.13.2 manual override + DEA','derived from enabled sector substitution; no validated independent ASEAN H2 demand','sector.hydrogen.*','prepare_sector_network.py:add_hydrogen','CAPABILITY_ONLY; key efficiencies/tank FOM pending'),
 ('heat','space/water/process heat','urban/rural; central/decentral heat','heat pumps; boilers; CHP; thermal stores','Bus/Load/Link/Store','conversion/store yes; demand fixed','v0.13.2; COP weather','UNSD energy totals + weather/population/urban fractions','sector.enable.heat=true; tes=true; boilers=true; chp=true','prepare_sector_network.py:add_heat','PENDING ASEAN demand shares and service equivalence'),
 ('industry','industrial energy + process services','electricity; gas; oil; biomass; H2; heat','electrification; fuel supply; process/CC','Load/Link/Bus','conversion yes; exogenous service demand','v0.13.2 + AEO8 + process factors','UNSD 2019; facilities/GDP; DEFAULT CAGR','sector.enable.industry=true','prepare_sector_network.py:add_industry','10-country base allocation PASS; TL/growth/process pending'),
 ('ammonia','NH3 production/use','NH3; H2; N2','Haber-Bosch; production links','Bus/Link/Store/Load','conversion/store per source yes','v0.13.2','USGS/facilities; 2019 production; industrial ammonia adjustments','sector.ammonia.enable=true','prepare_sector_network.py:add_ammonia','CURRENT UPSTREAM CAPABILITY; inclusion/energy double counting pending'),
 ('land transport','road mobility','EV batteries; H2; oil','BEV charger/V2G; fuel use','Load/Link/Store','EV infrastructure/stock constrained by exogenous shares','v0.13.2 + config efficiencies','UNSD; transport fleet profiles and DEC vehicle shares','sector.enable.land_transport=true; v2g=true; bev_dsm=true','prepare_sector_network.py:add_land_transport','PENDING ASEAN fleet/profile/share acceptance'),
 ('rail','rail mobility','electricity; oil','electric demand; oil supply','Load/Bus','demand fixed; upstream fuel expandable','v0.13.2 fuel','nodal energy totals','sector.enable.rail_transport=true','prepare_sector_network.py:add_rail_transport','PENDING energy totals; final-adjustment carrier handling'),
 ('shipping','shipping energy','oil; H2','oil supply; optional H2 liquefaction','Load/Link/Bus','supply conversion expandable when enabled','v0.13.2 fuel/conversion','UNSD totals + ports; shipping profile','sector.enable.shipping=true; shipping_hydrogen_share.DEC_*=0','prepare_sector_network.py:add_shipping','PENDING port shares/bunkers boundary'),
 ('aviation','aviation energy','oil/kerosene','oil/synthetic fuel supply','Load/Link/Bus','supply conversion expandable','v0.13.2 fuel/FT','UNSD + airport spatial allocation','sector.enable.aviation=true; international_bunkers=false','prepare_sector_network.py:add_aviation','PENDING airport allocation/international fuel boundary'),
 ('agriculture','agricultural energy','electricity; heat; oil','fuel/heat service','Load/Link/Bus','upstream supply yes; service fixed','v0.13.2','nodal energy totals','sector.enable.agriculture=true','prepare_sector_network.py:add_agriculture','PENDING source acceptance; electricity final scaling'),
 ('residential','household electricity and heat','electricity; heat; gas/oil/biomass','boilers; heat pumps; rooftop/storage','Load/Link/Generator/Store','conversion/rooftop/home store yes','v0.13.2 + AEO8','UNSD totals; residential profiles; population','sector.enable.residential=true','prepare_sector_network.py:add_residential','PENDING service-demand consistency with heat sector'),
 ('services','service-sector energy','electricity; heat; gas/oil/biomass','heat/fuel conversion','Load/Link/Bus','supply yes; service fixed','v0.13.2','UNSD totals; services profiles','sector.enable.services=true','prepare_sector_network.py:add_services','PENDING services naming/scaling and heat overlaps'),
 ('biomass','resource and fuel','solid biomass; biogas','combustion; upgrading','Generator/Store/Link','conversion yes; resource caps apply','v0.13.2','global/default potential; 360 TWh solid and 0.5 TWh biogas configured','sector.enable.biomass=true; biomass_transport=false','prepare_sector_network.py:add_biomass','PENDING ASEAN resource entitlement; not accepted supply data'),
 ('storage','temporal balancing','battery; H2; heat; PHS/hydro','charging/discharging','Store/StorageUnit/Link','battery/H2/TES yes; existing hydro resource limited','v0.13.2 + AEO8','cost/efficiency/lifetime plus existing capacities','sector.tes; sector.home_battery; electricity.extendable_carriers','prepare_sector_network.py; add_electricity.py','PENDING key cost/efficiency verification'),
 ('networks','domestic/cross-border transport','AC/DC; gas/H2/CO2 options','transmission; distribution; pipelines','Line/Link/Bus','electric expansion subject to lv2.0 and route rules; gas/H2/CO2 networks false','v0.13.2 + line costs','osm-plus-prebuilt 0.1.1; AIMS/ID projects','lines/links; transmission_projects; sector.*.network','base_network.py; add_transmission_projects.py','PENDING 765→766; future intervention AC/DC cross-border only'),
 ('external supply / CO2','commodity boundary and emissions','gas/oil/coal/lignite; atmosphere','fuel source; capture; DAC; sequestration','Generator/Store/Link/GlobalConstraint','fuel source unconstrained unless explicit resource cap; CO2 store expandable','fuel prices; capture/sequestration costs','manual fuel prices; shared default resource/CO2 settings','sector gas/oil/coal spatial; co2.budget; sector.dac/cc','prepare_sector_network.py:add_carrier_buses/add_co2','POWER-SCOPE NOT EQUIVALENT under full SC; attribution required'),
]
for sector,service,carrier,tech,component,expand,costsource,demandsource,switch,code,status in specs:
    sector_rows.append(dict(Sector=sector,Service_demand=service,Carrier=carrier,Conversion_technology=tech,PyPSA_component=component,Expandable=expand,Cost_source=costsource,Demand_source=demandsource,Config_switch=switch,Source_code=code,Validation_status=status))

industry=json.loads((HERE/'INDUSTRIAL_RECOVERY_EVIDENCE.json').read_text())['countries']
payload={
 'data_registry/DATA_SOURCES.csv':source_rows,
 'data_registry/DATA_HASHES.csv':rows,
 'INDUSTRIAL_CONSERVATION.csv':industry,
 'SECTOR_ENABLEMENT.csv':sector_rows}
(HERE/'REGISTRY_RECORDS.json').write_text(json.dumps(payload,indent=2))
# Direct final author accounting evidence: finite nonzero carrier factors and emission ports.
author=[]
for r in json.loads((HERE.parent/'00_source_provenance/RESULTS_MEMBER_HASHES.json').read_text()):
    p=HERE.parent/'00_source_provenance'/r['path'].replace('\\','/')
    n=pypsa.Network(p)
    factors=n.carriers.co2_emissions[n.carriers.co2_emissions!=0]
    emit=[]
    for col in n.links.columns[n.links.columns.str.match(r'bus[2-9]')]:
        hit=n.links[n.links[col]=='co2 atmosphere']
        emit.append({'port':col,'carriers':hit.groupby('carrier').size().to_dict()})
    author.append({'member':r['member'],'co2_carrier_factors':factors.to_dict(),'emitting_links':emit,'co2_limit':n.global_constraints.to_dict('index'),
     'atmosphere_store':n.stores.loc[n.stores.index.intersection(['co2 atmosphere']),['carrier','e_cyclic','e_initial']].to_dict('index')})
(HERE/'PAPER_CARBON_ACCOUNTING.json').write_text(json.dumps(author,indent=2))
# Correct initial filename assumption after inspecting the effective metadata and ZIP directory.
p=HERE/'PAPER_PREFLIGHT_FOLLOWUP.json';r=json.loads(p.read_text())
r['official_asia_cutout_probe']['paper_exact_identity']='FILENAME_MATCHES effective paper metadata: cutout-2013-era5.nc; author input SHA256 still unavailable'
r['identity_followup']='WEATHER_ARCHIVE_DIRECTORY.json confirms one member with that filename; no full download or CRC validation performed'
p.write_text(json.dumps(r,indent=2))
print(json.dumps({k:len(v) for k,v in payload.items()},indent=2))
