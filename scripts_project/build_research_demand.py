"""Rebuild Gate2 observation/contract tables from pinned source capsules.

python scripts_project/build_research_demand.py --repo . --output results_project/gate2 --csv
--verify-originals also checks the original local files; no downloads or solver.
The default JSON is suitable for review/export. CSV contains the SAME typed data.
"""
from pathlib import Path
from decimal import Decimal
import argparse,csv,hashlib,io,json,math
from demand_accounting import COUNTRIES,FIELDS,validate_ledger,materialise
from demand_sources import row,electricity,load_sources
import demand_buildings,demand_transport,demand_industry_agriculture

TABLES={'electricity_parent.csv':'electricity','buildings_accounting.csv':'Buildings',
        'transport_accounting.csv':'Transport','industry_accounting.csv':'Industry',
        'agriculture_accounting.csv':'Agriculture','bunker_accounting.csv':'bunker'}
MATRIX_FIELDS='RowID Country Year Sector Carrier SourceMWh LedgerMWh SourceToSector Spatial Temporal EvidenceClass Status Notes'.split()
BLOCKER_FIELDS='BlockerID RowID Country Year Sector Carrier Code RequiredAction'.split()


def parent_rows(sources):
    out=[]
    for c in COUNTRIES:
        for year in [2019,2030,2040,2050]:
            r=row(c,year,'Electricity','Astar','electricity',DemandType='DIRECT_ELECTRICITY',
                IncludedInAstar=True,Group='electricity',Notes='End-user final electricity before any accepted transfers; future conversion inputs excluded')
            if year==2019:
                r=electricity(r,sources['electricity'],'Final energy consumption')
                r.update(ParentBefore=r['ConvertedMWh'],ParentAfter=r['ConvertedMWh'],IndependentReference=r['ConvertedMWh'],TransferredChild=0.)
            else:r.update(Notes='FUTURE_DIRECT_ELECTRICITY_PENDING; no AEO8 generation/DemandCast/default-growth fallback')
            out.append(r)
        for name in ['HeatPump','Electrolysis','FischerTropsch','ResistiveHeating','EVIfConversion']:
            out.append(row(c,2019,'Conversion',name,'electricity',DemandType='ENDOGENOUS_CONVERSION_INPUT',
                FixedOrEndogenous='ENDOGENOUS',Representation='CONTRACT_ONLY',Posting=False,Required=False,
                Status='PENDING',Group='electricity',Notes='No predetermined demand or Load; future accepted conversion Link owns its electricity input'))
    return out


def build(repo,verify_originals=False):
    sources=load_sources(repo,verify_originals)
    rows=parent_rows(sources)+demand_buildings.build(sources)+demand_transport.build(sources)+demand_industry_agriculture.build(sources)
    rows.sort(key=lambda r:r['RowID'])
    blocked=validate_ledger(rows)
    matrix=[]
    for r in rows:
        # Independent Decimal reconstruction, not a sum of the target ledger.
        source=None;status='PENDING'
        if r['ConvertedMWh'] is not None and r['RawValue'] is not None:
            factor={'Kilowatt-hours, million':Decimal(1000),'TWh/year':Decimal(1000000),'MWh/year':Decimal(1)}[r['RawUnit']]
            source=float(Decimal(str(r['RawValue']))*factor)
            if not math.isclose(source,r['ConvertedMWh'],rel_tol=1e-10,abs_tol=1e-6):raise ValueError('Independent source/ledger mismatch')
            status='PASS_SOURCE_TO_LEDGER'
        matrix.append(dict(RowID=r['RowID'],Country=r['Country'],Year=r['Year'],Sector=r['Sector'],Carrier=r['Carrier'],
            SourceMWh=source,LedgerMWh=r['ConvertedMWh'],SourceToSector=status,
            Spatial='NOT_APPLICABLE' if not r['Posting'] else 'PENDING_ACCEPTED_WEIGHTS',
            Temporal='NOT_APPLICABLE' if not r['Posting'] else 'PENDING_ACCEPTED_PROFILE',
            EvidenceClass='OBSERVATION_NOT_MODEL_VALIDATION',Status='PARTIAL' if source is not None else 'PENDING',
            Notes='Source is raw UNSD or named derived cache, as ledger states. Cache conversion PASS does not prove original fuel/calorific completeness.'))
    for r in rows:
        if r['Status']=='BLOCKER':blocked.append((r['RowID'],'RAW_SELECTION_INCOMPLETE'))
        if r['Required'] and r['Year']>2019:blocked.append((r['RowID'],'FUTURE_DIRECT_ELECTRICITY_PENDING' if r['ChildAccount']=='Astar' else 'PENDING_FUTURE_GROWTH_OR_EV_PATH'))
        if r['Required'] and r['Year']==2019 and r['NumericAccepted']:
            blocked.append((r['RowID'],'SPATIAL_TEMPORAL_ACCEPTANCE_PENDING'))
    lookup={r['RowID']:r for r in rows};blockers=[]
    for i,(rid,code) in enumerate(sorted(set(blocked)),1):
        r=lookup[rid];blockers.append(dict(BlockerID=f'G2-{i:04d}',RowID=rid,Country=r['Country'],Year=r['Year'],Sector=r['Sector'],Carrier=r['Carrier'],Code=code,
            RequiredAction='Human acceptance of identified source/boundary; no numeric replacement' if code=='NUMERIC_ACCEPTANCE_PENDING' else
            'Provide/accept missing source or explicit not-applicable representation; never zero-fill' if code=='MISSING_ANNUAL_DATA' else
            'Gate3 energy destination for preserved fuel; not a CO2-only substitute' if code=='MISSING_ENERGY_OBLIGATION' else
            'Resolve the named contract/evidence before full-model assembly'))
    tables={name:{'fields':FIELDS,'rows':[r for r in rows if r['Group']==group]} for name,group in TABLES.items()}
    tables['RESEARCH_DEMAND_LEDGER.csv']={'fields':FIELDS,'rows':rows}
    tables['RESEARCH_DEMAND_CONSERVATION_MATRIX.csv']={'fields':MATRIX_FIELDS,'rows':matrix}
    tables['RESEARCH_DEMAND_BLOCKERS.csv']={'fields':BLOCKER_FIELDS,'rows':blockers}
    # Direct-electricity partition is diagnostic only. The unsummed remainder
    # stays in the authoritative Astar; never publish it as a fabricated O Load.
    parts={}
    for c in COUNTRIES:
        labels=['Consumption by households','Consumption by commercial and public services','Consumption by manufacturing, construction and non-fuel industry','Consumption by transport','Consumption in agriculture, forestry and fishing','Consumption by other']
        x=[z for z in sources['electricity']['records'] if z['Country']==c]
        parent=next(z for z in x if z['Commodity - Transaction']=='Electricity - Final energy consumption')
        selected=[z for z in x if z['Commodity - Transaction'] in ['Electricity - '+q for q in labels]]
        parts[c]={'parent_mwh':float(Decimal(parent['Quantity'])*1000),'available_selected_mwh':float(sum(Decimal(z['Quantity'])*1000 for z in selected)),
                  'present_labels':[z['Commodity - Transaction'] for z in selected],
                  'status':'REFERENCE_ONLY_NO_RESIDUAL_ACCOUNT_CREATED'}
    guards={}
    for c in COUNTRIES:
        for year in [2019,2030,2040,2050]:
            try:materialise(rows,c,year,{})
            except ValueError as exc:guards[f'{c}:{year}']=str(exc)
            else:raise AssertionError('Unaccepted country/year materialised')
    report={'ledger_rows':len(rows),'countries':list(COUNTRIES),'years':[2019,2030,2040,2050],
        'numeric_accepted_rows':sum(r['NumericAccepted'] for r in rows),'astar_raw_base_countries':11,
        'posted_candidate_obligations':sum(r['Posting'] for r in rows),'source_to_ledger_pass':sum(x['SourceToSector'].startswith('PASS') for x in matrix),
        'blocker_rows':len(blockers),'guarded_country_years':len(guards),'all_materialisations_blocked':True,
        'electricity_partition_diagnostic':parts,'guards':guards,'solver_status':'NOT_RUN'}
    return tables,report


def scalar(v):
    if v is None:return ''
    if isinstance(v,bool):return 'true' if v else 'false'
    return str(v)


def csv_bytes(table):
    stream=io.StringIO(newline='');writer=csv.writer(stream,quoting=csv.QUOTE_ALL,lineterminator='\r\n')
    writer.writerow(table['fields'])
    for row in table['rows']:writer.writerow([scalar(row[k]) for k in table['fields']])
    return ('\ufeff'+stream.getvalue()).encode('utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--verify-originals',action='store_true');p.add_argument('--csv',action='store_true');args=p.parse_args()
    tables,report=build(args.repo,args.verify_originals);args.output.mkdir(parents=True,exist_ok=True)
    for table in tables.values():table['export_values']=[table['fields']]+[[scalar(r[k]) for k in table['fields']] for r in table['rows']]
    (args.output/'tables.json').write_text(json.dumps(tables,ensure_ascii=False,allow_nan=False))
    (args.output/'BUILD_REPORT.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    if args.csv:
        for name,t in tables.items():(args.output/name).write_bytes(csv_bytes(t))
    print(json.dumps({k:v for k,v in report.items() if k not in ('electricity_partition_diagnostic','guards')}))
