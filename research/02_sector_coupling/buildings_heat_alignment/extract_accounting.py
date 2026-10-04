"""Read retained raw Buildings rows and annual tutorial intermediates only.
Produces audit JSON for the CSV author; does not prepare model inputs.
"""
from pathlib import Path
import ast, hashlib, json
import pandas as pd
import country_converter as coco
R=Path(__file__).resolve().parent;P=R.parent/'buildings_heat';E=P/'evidence'
D=R/'data/processed/buildings';D.mkdir(parents=True,exist_ok=True)
DER=R/'data/derived/buildings';DER.mkdir(parents=True,exist_ok=True)
M=Path('/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean')
countries=['BN','KH','ID','LA','MY','MM','PH','SG','TH','TL','VN']
source=P/'source_snapshot/upstream/scripts/_helpers.py';env={}
t=ast.parse(source.read_text());exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in ['get_conv_factors','aggregate_fuels']],type_ignores=[]),str(source),'exec'),env)
conv=env['get_conv_factors']('industry');groups=dict(zip(['gas','oil','biomass','coal','heat','electricity'],env['aggregate_fuels']('industry')))
raw=json.loads((E/'UNSD_2019_BUILDINGS_ROWS.json').read_text())
for row in raw:
    f=row['Commodity - Transaction'].split(' - ')[0];u=row['Unit'];q=row['Quantity']
    factor=1/1000 if u=='Kilowatt-hours, million' else 1/3600 if u=='Terajoules' else conv.get(f) if u in ['Metric tons,  thousand','Cubic metres, thousand'] else None
    row.update(fuel=f,sector='residential' if 'households' in row['Commodity - Transaction'].lower() else 'services',model_group=next((g for g,fs in groups.items() if f in fs),'other'),model_conversion_factor=factor,model_equivalent_TWh=q*factor if factor is not None else None,unit_validation='PENDING_VOLUME_BASIS' if u=='Cubic metres, thousand' else 'PENDING_HHV_LHV' if 'Metric tons' in u else 'EXACT_ENERGY_UNIT_CONVERSION',status='UNVERIFIED',human_confirmation='PENDING')
(D/'UNSD_2019_BUILDINGS_CLASSIFIED.json').write_text(json.dumps(raw,indent=2))
elec_file=M/'data/demand/unsd/data/UNdata_Export_20250502_110820872.txt'
df=pd.read_csv(elec_file,sep=';',low_memory=False)
df=df[(df.Year==2019)&(df['Commodity - Transaction']=='Electricity - Final energy consumption')].copy()
country_names={r['Country or Area']:r['ISO2'] for r in raw}
df['country']=df['Country or Area'].map(country_names);df=df[df.country.isin(countries)]
assert not df.country.duplicated().any()
national={row.country:float(row.Quantity)/1000 for row in df.itertuples()}
national_rows=json.loads(df.to_json(orient='records'))
(D/'UNSD_2019_NATIONAL_ELECTRICITY.json').write_text(json.dumps(dict(source_file=str(elec_file),source_sha256=hashlib.sha256(elec_file.read_bytes()).hexdigest(),rows=national_rows),indent=2))
annual=json.loads((E/'TUTORIAL_BUILDINGS_ANNUAL.json').read_text())
def subset(c,s):return [x for x in raw if x['ISO2']==c and x['sector']==s]
def amount(c,s,fuel):
    rs=[x for x in subset(c,s) if x['model_group']==fuel]
    return sum(x['model_equivalent_TWh'] for x in rs) if rs and all(x['model_equivalent_TWh'] is not None for x in rs) else None
FIELDS=['row_id','country','sector','year','layer','unit','base_electricity_TWh','residential_direct_electricity_TWh','services_direct_electricity_TWh','explicit_heat_related_electricity_TWh','residual_electricity_TWh','endogenous_conversion_electricity_TWh','annual_total_TWh','reported_final_energy_subtotal_TWh','raw_electricity_TWh','raw_heat_commodity_TWh','raw_gas_TWh','raw_oil_TWh','raw_coal_TWh','raw_biomass_TWh','raw_other_TWh','model_base_electricity_including_coal_TWh','modeled_space_heat_TWh','modeled_water_heat_TWh','modeled_remaining_competitive_heat_TWh','modeled_fixed_heat_fuel_TWh','modeled_gas_final_load_TWh','modeled_oil_final_load_TWh','modeled_biomass_final_load_TWh','class_electricity','class_heat','class_gas','class_oil','class_coal','class_biomass','class_other','double_count_flag','arithmetic_balance_error_TWh','coverage_note','heat_basis','conversion_electricity_note','source_id','source_file','status','human_confirmation']
rows=[]
def row(**kw):
    d={f:None for f in FIELDS};d.update(unit='TWh; heat_basis must be read separately',status='UNVERIFIED',human_confirmation='PENDING',conversion_electricity_note='NOT_SOLVED; do not fill with zero');d.update(kw);rows.append(d);return d
for c in countries:
    er,es=amount(c,'residential','electricity'),amount(c,'services','electricity');nat=national.get(c)
    residual=nat-er-es if all(v is not None for v in [nat,er,es]) else None
    row(row_id=f'{c}-2019-national',country=c,sector='national electricity account',year=2019,layer='REPORTED_2019_ARITHMETIC_ONLY',base_electricity_TWh=nat,residential_direct_electricity_TWh=er,services_direct_electricity_TWh=es,residual_electricity_TWh=residual,annual_total_TWh=nat,double_count_flag='ARITHMETIC_PASS_ONLY; ACTUAL_FULL_SC_PENDING' if residual is not None and residual>=0 else 'MISSING_OR_INCONSISTENT',arithmetic_balance_error_TWh=nat-(er+es+residual) if residual is not None else None,coverage_note='Residual is constructed as national final electricity minus reported R and S. Not the actual network residual; existing electric heat/cooling split unmeasured.',heat_basis='NOT_APPLICABLE',source_id='UNSD2019_RAW; UNSD2019_ELEC_TOTAL',source_file=elec_file.name)
    for s in ['residential','services']:
        rs=subset(c,s);base=annual['base'][c];eleck='electricity residential' if s=='residential' else 'services electricity'
        coverage='Absent commodity groups mean not separately reported, NOT measured zero: '+','.join(g for g in [*groups,'other'] if amount(c,s,g) is None)
        common=dict(country=c,sector=s,source_id='UNSD2019_RAW; U_HELPERS; T_ANNUAL',source_file=';'.join(sorted({x['source_file'] for x in rs})),class_electricity='A; historical electric heat and cooling not disaggregated',class_heat='A (fixed service); D (supply); service basis F',class_gas='C allocation; A final fuel loads; DEFAULT electric shifts zero' if s=='residential' else 'A',class_oil='A+B+C(D for shifted heat)' if s=='residential' else 'A',class_coal='B (shift true); E if false',class_biomass='C allocation; A final fuel loads; DEFAULT electric shifts zero' if s=='residential' else 'A',class_other='F if unreported; E if outside model fuel groups',heat_basis='Base: reported Heat/direct thermal commodity, not all useful building heat',coverage_note=coverage)
        r=row(row_id=f'{c}-2019-{s}',year=2019,layer='RAW_FINAL_ENERGY_AND_MODEL_BASE',reported_final_energy_subtotal_TWh=sum(x['model_equivalent_TWh'] for x in rs if x['model_equivalent_TWh'] is not None),model_base_electricity_including_coal_TWh=base[eleck],modeled_space_heat_TWh=base['total '+s+' space'],modeled_water_heat_TWh=base['total '+s+' water'],double_count_flag='END_USE_BRIDGE_PENDING',**common)
        for g in [*groups,'other']:r['raw_'+('heat_commodity' if g=='heat' else g)+'_TWh']=amount(c,s,g)
        r[s+'_direct_electricity_TWh']=er if s=='residential' else es
        for y in ['2030','2040','2050']:
            a=annual[y][c];space=a['total '+s+' space'];water=a['total '+s+' water'];fixed=sum(a['residential heat '+f] for f in ['gas','oil','biomass']) if s=='residential' else None
            r=row(row_id=f'{c}-{y}-{s}',year=int(y),layer='RETAINED_TUTORIAL_PREPROCESSING_DIAGNOSTIC',modeled_space_heat_TWh=space,modeled_water_heat_TWh=water,modeled_remaining_competitive_heat_TWh=space+water-(fixed or 0),modeled_fixed_heat_fuel_TWh=fixed,double_count_flag='FULL_SC_NOT_CLOSED; E1_E2_E3_E4_PENDING',**common)
            r[s+'_direct_electricity_TWh']=a[eleck]
            # This is a generated heat quantity, NOT measured existing electric heat consumption.
            r['explicit_heat_related_electricity_TWh']=None
            r['heat_basis']='R: mixture of converted service and fixed fuel energy before add_residential; S: scaled direct thermal commodity only'
            for f in ['gas','oil','biomass']:r['modeled_'+f+'_final_load_TWh']=a[s+' '+f]+(a['residential heat '+f] if s=='residential' else 0.)
            r['coverage_note']+='; Tutorial artifacts are not U or Research Model annual solves; annual_total intentionally blank because service and final fuel cannot be added.'
(DER/'ACCOUNTING_RECORDS.json').write_text(json.dumps(rows,indent=2,allow_nan=False))
checks={'countries':countries,'rows':len(rows),'national_electricity_countries':sorted(national),'arithmetic_rows_passing':sum(r['arithmetic_balance_error_TWh'] is not None and abs(r['arithmetic_balance_error_TWh'])<1e-9 for r in rows),'arithmetic_tolerance_TWh':1e-9,'missing_or_negative_residual':[r['country'] for r in rows if r['sector']=='national electricity account' and (r['residual_electricity_TWh'] is None or r['residual_electricity_TWh']<0)],'raw_rows':len(raw),'unclassified_raw_rows':[r for r in raw if r['model_group']=='other'],'unknown_conversion_rows':[r for r in raw if r['model_equivalent_TWh'] is None],'all_human_pending':True,'note':'Missing raw groups preserved as null, not zero. This is diagnostic arithmetic, not an accepted Full-SC demand account.'}
(DER/'ACCOUNTING_CHECKS.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
