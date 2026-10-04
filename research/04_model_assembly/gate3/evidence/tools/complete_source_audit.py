from pathlib import Path
import csv,json,hashlib,collections,sys,math,argparse
import pypsa
parser=argparse.ArgumentParser();parser.add_argument('--evidence',type=Path);parser.add_argument('--repo',type=Path,default=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model'));args=parser.parse_args()
W=Path(__file__).resolve().parent;E=args.evidence or W/'evidence';R=args.repo
raw=json.loads((E/'TUTORIAL_COMPONENTS.json').read_text())
if hashlib.sha256(Path(raw['source']).read_bytes()).hexdigest()!=raw['sha256']:raise ValueError('Original reference network changed')
n=pypsa.Network(raw['source'])
carriers=n.carriers.to_dict('index');(E/'CARRIER_FACTORS.json').write_text(json.dumps(carriers,default=str))
p=R/'data/osm-plus-prebuilt/0.1.1';bp=p/'all_buses_build_network.csv'
with bp.open() as f:bus={r['bus_id']:r for r in csv.DictReader(f)}
rows=[];hashes={bp.name:hashlib.sha256(bp.read_bytes()).hexdigest()}
for typ,name,idcol in [('Line','all_lines_build_network.csv','line_id'),('Link','all_converters_build_network.csv','converter_id'),('Transformer','all_transformers_build_network.csv','line_id')]:
    path=p/name;hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open() as f:
        for r in csv.DictReader(f):
            a,b=r['bus0'],r['bus1'];ca=bus.get(a,{}).get('country','');cb=bus.get(b,{}).get('country','')
            kind='UNKNOWN' if not ca or not cb else 'DOMESTIC' if ca==cb else 'CROSS_BORDER'
            rows.append(dict(Name=r[idcol],ComponentType=typ,Carrier='DC' if r.get('dc','').lower() in ('true','1') or typ=='Link' else 'AC',
                Bus0=a,Bus1=b,Country0=ca,Country1=cb,Classification=kind,FutureControllable=kind=='CROSS_BORDER',
                Evidence='CURRENT_PINNED_RAW_TOPOLOGY_NOT_FINAL_CLUSTERED_MODEL',Source=str(path)))
(E/'RAW_ELECTRICITY_CLASSIFICATION.json').write_text(json.dumps({'hashes':hashes,'rows':rows},ensure_ascii=False))
graph=json.loads((E/'REFERENCE_GRAPH_AUDIT.json').read_text());country=graph['country_map'];pol=[]
def coef(row):
    vals=[]
    for k,v in row.items():
        if k.startswith('bus') and k[3:].isdigit() and v=='co2 atmosphere':
            eff=row.get('efficiency' if k=='bus1' else 'efficiency'+k[3:],None)
            if eff is not None:vals.append(float(eff))
    return sum(vals) if vals else None
for typ in ['Generator','Link','Load']:
    for r in raw['tables'][typ]:
        carrier=r.get('carrier','');name=r['Name'];cs={country.get(v,'') for k,v in r.items() if (k=='bus' or k.startswith('bus') and k[3:].isdigit()) and country.get(v,'')}
        c=next(iter(cs)) if len(cs)==1 else 'UNRESOLVED'
        factor=coef(r) if typ=='Link' else None;sector='UNKNOWN';policy='PENDING';reason='Not an identified emitting component';relevant=False
        if typ=='Generator':
            factor=carriers.get(carrier,{}).get('co2_emissions',0)
            bus=r.get('bus');buscarrier=n.buses.at[bus,'carrier']
            if buscarrier in ('AC','DC') and carrier in ('geothermal','nuclear','coal','oil','lignite','OCGT','CCGT'):
                sector='Power';policy=True;relevant=True;reason='Explicit electricity Generator family; retains nonzero geothermal factor if present'
                eff=r.get('efficiency',1)
                factor=float(factor)/float(eff) if factor is not None else None
            elif carrier in ('gas','oil','coal','lignite'):
                sector='ExternalSupply';policy=False;relevant=True;factor=0.;reason='Fuel price source; combustion accounted downstream once'
        elif typ=='Link':
            if carrier in ('OCGT','CCGT','coal','oil','lignite') and r.get('bus1') in n.buses.index and n.buses.at[r['bus1'],'carrier'] in ('AC','DC'):
                sector='Power';policy=True;relevant=True;reason='convert_conventional_generators_to_links explicit power plant role'
            elif carrier in ('SMR','SMR CC') or 'CHP' in carrier:
                sector='SHARED_USE_PENDING';policy='PENDING_SHARED_USE_ALLOCATION';relevant=True;reason='Shared H2/CHP cannot be allocated by name or arbitrary ratio; original power scope requires accepted split'
            elif 'gas boiler' in carrier:
                sector='Buildings';policy=False;relevant=True;reason='add_heat fuel boiler, not electricity generation'
            elif carrier in ('gas for industry','gas for industry CC','solid biomass for industry','solid biomass for industry CC','process emissions','process emissions CC'):
                sector='Industry';policy=False;relevant=True;reason='Explicit industrial fuel/process conversion; not power policy'
            elif carrier in ('Fischer-Tropsch','Sabatier','helmeth','DAC','biogas to gas','co2 vent','biomass EOP'):
                sector='Power' if carrier=='biomass EOP' else 'Conversion';relevant=True;policy='PENDING_CAPTURE_OR_ORIGIN_SCOPE' if carrier in ('DAC','biogas to gas','co2 vent') else (True if carrier=='biomass EOP' else False)
                reason='Physical carbon transfer/uptake/vent role requires origin and accepted credit scope; FT transfer not new emission'
        else:
            if r.get('bus')=='co2 atmosphere':
                relevant=True;sector='AGGREGATED_UNRESOLVED';policy=False;reason='Historical fixed CO2 Load not a fuel-energy obligation; cannot recover country/domestic/bunker split from aggregate name';factor='FIXED_CO2_LOAD_NOT_PER_MWH'
        if relevant:
            pol.append(dict(Component=typ+':'+name,Carrier=carrier,Sector=sector,Country=c,EmissionFactor=factor,
                PolicyCO2Power=policy,ReportingCO2FullSystem=(False if sector=='ExternalSupply' else True),Reason=reason,
                Source=raw['source']+'; current scripts/prepare_sector_network.py',Status='REFERENCE_MAPPING_NOT_NUMERIC_ACCEPTANCE'))
(E/'REFERENCE_POLICY_MAP.json').write_text(json.dumps(pol,ensure_ascii=False))
print('RAW ELECTRICITY',len(rows),dict(collections.Counter(x['Classification'] for x in rows)))
print('UNKNOWN',[x['Name'] for x in rows if x['Classification']=='UNKNOWN'])
print('POLICY MAP',len(pol),dict(collections.Counter(str(x['PolicyCO2Power']) for x in pol)))
