from pathlib import Path
import sys,csv,json,hashlib,subprocess as sp,collections,io
W=Path(__file__).resolve().parent;E=W/'evidence';R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');N=W.parents[1]
T=Path('/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 return list(csv.DictReader(io.StringIO(p.read_text(encoding='utf-8-sig').lstrip('\r\n'))))
cost=T/'resources/baseline-aims-3H-tutorial/pre_costs_2050.csv'
official=N/'research/00_source_provenance/official/technology-data/outputs/costs_2050.csv'
assert sha(cost)==sha(official)
selected=[r for r in read(cost) if r['technology'] in ['electrolysis','Fischer-Tropsch','gas','oil','coal','hydrogen storage tank type 1 including compressor'] and r['parameter'] in ['investment','efficiency','fuel','lifetime','FOM']]
(E/'COST_CANDIDATES_2050.json').write_text(json.dumps(dict(source=str(cost),sha256=sha(cost),official_file=str(official),official_sha256=sha(official),git_version='ec22a1843632fd28ecb9a139ee5156faf23324a3',records=selected),indent=2))
paths=['data/demand/growth_factors_cagr.csv','data/demand/industry_growth_cagr.csv','data/demand/efficiency_gains_cagr.csv']
growth={}
for rel in paths:
 rr=read(R/rel);growth[rel]=dict(sha256=sha(R/rel),country_keys=[next(iter(x.values())) for x in rr],records=rr,git_log=sp.check_output(['git','log','-4','--format=%H %s','--',rel],cwd=R,text=True))
(E/'GROWTH_SOURCE_REVIEW.json').write_text(json.dumps(growth,indent=2))
for rel in ['scripts/prepare_energy_totals.py','scripts/build_industry_demand.py','scripts/final_asean_adjustment.py']:
 q=E/'source'/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((R/rel).read_bytes())
ledger=read(R/'research/04_model_assembly/gate2/RESEARCH_DEMAND_LEDGER.csv')
print('ledger',len(ledger),'2050',dict(collections.Counter(r['Status'] for r in ledger if r['Year']=='2050')))
print('costs',json.dumps(selected,indent=2))
for group,x in growth.items():print(group,x['country_keys'])
