"""Re-derive accepted target values from pinned raw sources and human methods.

The registry supplies the approved ownership/representation inventory. Its stored
Value and CandidateValue fields are NOT inputs to the numerical derivation.
Unqualified rows are never promoted. Output is a reviewable JSON, not an in-place
source update; no solver. Source reconstruction is recomputed independently.
"""
from pathlib import Path
from decimal import Decimal as D,localcontext
import json,argparse,math
from reconstruct_base_accounts import reconstruct
from check_assembly_inputs import load_registry,ACCEPTED
def derive(folder):
 folder=Path(folder);data=load_registry(folder);s=folder/'sources'
 source=json.loads((s/'electricity.json').read_text())
 base={r['Country']:D(r['Quantity'])*1000 for r in source['records'] if r['Commodity - Transaction']=='Electricity - Final energy consumption' and r['Year']=='2019' and r['Unit']=='Kilowatt-hours, million'}
 if len(base)!=11:raise ValueError('Missing unique country electricity parents')
 decisions=json.loads((s/'GATE4_CONTINUE_DECISIONS.json').read_text());road=json.loads((s/'GATE4_ROAD_NON_ELECTRIC_DECISION.json').read_text())
 source_aeo=json.loads((s/'AEO8_BAS_SOURCE_VALUES.json').read_text())['values'];astar=D(next(r['value'] for r in source_aeo if r['id']=='Astar2050'))*D(decisions['mtoe']['Mtoe_MWh'])
 total=sum(v for c,v in base.items() if c!='TL');b={(r['Country'],r['Account'],r['Carrier']):r for r in reconstruct(s)['accounts']}
 frozen=json.loads((s/'FROZEN_ACCEPTED_BUNKER_2019.json').read_text())['values'];out=[]
 with localcontext() as ctx:
  ctx.prec=40
  for r in data['records']:
   if r['Year']!=2050 or r['Kind']!='DEMAND' or r['AssemblyStatus']!=ACCEPTED:continue
   c,a,k=r['Country'],r['Account'],r['Carrier']
   if a=='Astar':value=astar*base[c]/total;formula='225Mtoe *11,630,000 * national2019FinalElectricity/sumASEAN10FinalElectricity; TL independently extrapolated'
   else:
    z=b[c,a,k]
    if z['Status']!='NUMERIC_INPUT_READY':raise ValueError('Promoted unqualified base')
    raw=D(z['ValueMWh'])
    if a in decisions['growth']['ratios']:
     num,den=decisions['growth']['ratios'][a];value=raw*D(num)/D(den);formula=f'Raw2019*({num}/{den})'
    elif a=='RoadResidualFuel':value=raw*D(road['numerator'])/D(road['denominator']);formula='Raw2019*(374.9/145.2)'
    elif a.startswith('International'):
     value=D(frozen[r['InputID']]) if r['InputID'] in frozen else raw;formula='Accepted2019 constant; raw precision and mechanical source correction separately recorded'
    elif a in decisions['domestic']['accounts']:value=raw;formula='Qualified2019 domestic obligation constant'
    elif a in ['RailNonElectric','TransportNEC','OtherNEC']:
     latest=json.loads((s/'GATE4_CONSOLIDATED_BASELINE_DECISIONS.json').read_text())
     key='TransportEmbeddedFuelParent' if a=='RailNonElectric' else a
     if latest['ApprovalStatus']!='HUMAN_ACCEPTED' or r.get('MethodID')!=latest['Methods'][key]:raise ValueError('Unapproved rail/NEC constant method')
     value=raw;formula='Qualified exclusive2019 source-use obligation constant; new human baseline assumption'
    else:raise ValueError('No approved numerical rule')
   if not math.isclose(float(value),float(r['Value']),rel_tol=1e-12,abs_tol=1e-6):raise ValueError('Stored target differs from raw/method derivation: '+r['InputID'])
   out.append(dict(InputID=r['InputID'],RecomputedMWh=str(value),Formula=formula,Status='PASS_INDEPENDENT_RAW_TO_TARGET_REDERIVATION'))
 return dict(records=out,accepted_count=len(out),unqualified_promoted=0,solver_runs=0)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path,required=True);a=p.parse_args();x=derive(a.repo/'research_inputs/assembly_v1');a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({k:v for k,v in x.items() if k!='records'}))
