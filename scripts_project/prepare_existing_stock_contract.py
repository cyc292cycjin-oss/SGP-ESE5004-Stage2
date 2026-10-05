"""Source-qualified existing-equipment proxies under the current human scope.

Read input efficiencies only; separate source FOM from annualised investment.
Never obtain stock or performance from solved dispatch/optimised capacities.
"""
from pathlib import Path
import argparse,json,hashlib,collections
import pandas as pd,pypsa
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prepare(repo,reference,costs,cost_sources,output,report):
 n=pypsa.Network(reference);c=pd.read_csv(costs,index_col=0);raw=pd.read_csv(cost_sources)
 contract=json.loads(output.read_text());d=json.loads((repo/'research_inputs/assembly_v1/sources/GATE4_CONSOLIDATED_BASELINE_DECISIONS.json').read_text());auth=d['DecisionReference']+'#3'
 if d['ApprovalStatus']!='HUMAN_ACCEPTED':raise ValueError('Missing engineering proxy authorisation')
 rows=[]
 for tech,carrier,fuel in [('CCGT','CCGT','gas'),('Hard Coal','coal','coal'),('Lignite','lignite','lignite'),('Oil','oil','oil')]:
  inputs=n.links[(n.links.carrier==carrier)&~n.links.p_nom_extendable]
  eff=inputs.efficiency.unique()
  if len(eff)!=1:raise ValueError('Non-unique existing input efficiency '+tech)
  cr=c.loc[carrier];src=raw[raw.technology.eq(carrier)&raw.parameter.isin(['investment','FOM','VOM'])]
  years=sorted(src.currency_year.dropna().unique().tolist());fom=float(cr.investment*cr.FOM/100)
  source=f'{reference} SHA256={sha(reference)}:fixed {carrier} Link.efficiency; {costs} SHA256={sha(costs)}:{carrier} FOM,VOM,investment; {cost_sources} SHA256={sha(cost_sources)}:source/unit/currency metadata'
  p=dict(ApprovalStatus='SOURCE_QUALIFIED_ENGINEERING_PROXY',AuthorizationReference=auth,Source=source,PerformanceBasis='SOURCE_TECHNOLOGY_ENGINEERING_PROXY',Efficiency=float(eff[0]),FixedOM_EUR_per_MW_e_year=fom,VariableOM_EUR_per_MWh_e=float(cr.VOM),CostBasis='EXISTING_NO_NEW_CAPEX',ComponentType='Link',Carrier=carrier+' existing',FuelCarrier=fuel,PhysicalCO2_t_per_MWh_fuel=float(c.at[fuel,'co2_emissions']),ResourceGroup='NO_FINITE_TECHNOLOGY_RESOURCE_LIMIT',ResourceSemantics=dict(ApprovalStatus='SOURCE_QUALIFIED_ENGINEERING_PROXY',AuthorizationReference=auth,Source='Frozen conventional conversion model has no finite site potential for this technology; fixed existing capacity; no change to approved new build availability'),Profiles={},ParameterYear=2030,ReferenceInputNetworkYear=2025,Currency='EUR',SourceCurrencyYears=years,FOMFormula='processed investment(EUR/MW_e) * FOM(%/year) /100; no annuity charged',VOMBasis='EUR/MWh_e; Link marginal_cost=VOM*efficiency; fuel purchase handled separately',ProxyMeaning='Frozen corresponding existing input efficiency; earliest cached processed electricity technology O&M proxy, not individual measured plant performance',SensitivityRequired=True)
  contract['performance'][tech]=p
  rows.append(dict(Technology=tech,Status=p['ApprovalStatus'],Efficiency=p['Efficiency'],FixedOM_EUR_MW_e_year=fom,VOM_EUR_MWh_e=p['VariableOM_EUR_per_MWh_e'],PhysicalCO2_t_MWh_fuel=p['PhysicalCO2_t_per_MWh_fuel'],ParameterYear=2030,SourceCurrencyYears=years,Source=source,SourceDetails=src[['parameter','unit','source','currency_year']].to_dict('records'),AuthorizationReference=auth,NewCAPEX=0,Limitation=p['ProxyMeaning']))
 stock=json.loads((repo/'results_project/assembly_v1/assets/ASSET_SURVIVAL_2050.json').read_text());plants=pd.read_csv(stock['asset_source'])
 reasons={'Reservoir':'Plant-owned inflow covers168h only; full-year reference inflow ownership has not been reconciled to surviving source units. Shared river/node flow cannot be duplicated.', 'Run-Of-River':'Plant-owned168h inflow cannot provide the required annual availability; annual reference availability lacks a qualified source-unit ownership join.', 'Pumped Storage':'Original duration/storage energy missing; reference fixed PHS max_hours=0 is not a qualified usable energy capacity. Resolve source duration/config discrepancy; natural river inflow is not this blocker.'}
 contract['performance']['Hydro']=dict(ApprovalStatus='PENDING',PendingReason='Hydro subtype-specific time/energy qualification pending; see individual unit contract.')
 for r in stock['unit_evidence']['records']:
  if r['Technology']=='Hydro':
   subtype=str(plants.iloc[int(r['ParentAssetID'].split(':')[1])].Technology)
   contract['performance'][r['AssetID']]=dict(ApprovalStatus='PENDING',HydroSubtype=subtype,PendingReason=reasons.get(subtype,'Hydro subtype not qualified'))
 for subtype,ct in [('Reservoir','hydro'),('Run-Of-River','ror'),('Pumped Storage','PHS')]:
  z=c.loc[ct];sr=raw[raw.technology.eq(ct)&raw.parameter.isin(['investment','FOM','VOM'])]
  rows.append(dict(Technology='Hydro / '+subtype,Status='PENDING_PROFILE_OR_ENERGY_QUALIFICATION',Efficiency=float(z.efficiency)**(.5 if ct=='PHS' else 1),FixedOM_EUR_MW_e_year=float(z.investment*z.FOM/100),VOM_EUR_MWh_e=float(z.VOM),ParameterYear=2030,SourceCurrencyYears=sorted(sr.currency_year.dropna().unique().tolist()),Source=str(costs)+' SHA256='+sha(costs),AuthorizationReference=auth,Limitation=reasons[subtype],NumericValuesRole='Source candidates only; no hydro performance contract activated'))
 contract['note']='Current explicit human lifetime/mapping decisions and source-qualified engineering proxies. Incomplete inventory and hydro qualification remain. No blanket source qualification.'
 output.write_text(json.dumps(contract,indent=2)+'\n');report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(dict(rows=rows,inputs={str(p):sha(p) for p in [reference,costs,cost_sources]},solver_runs=0),indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
 for x in ['reference','costs','cost-sources','output','report']:p.add_argument('--'+x,type=Path,required=True)
 a=p.parse_args();prepare(a.repo,a.reference,a.costs,a.cost_sources,a.output,a.report)
