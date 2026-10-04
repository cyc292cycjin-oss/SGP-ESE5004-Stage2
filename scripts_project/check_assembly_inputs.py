"""Fail-closed Assembly V1 input gate. Does not build a network or call a solver."""
from pathlib import Path
import argparse,json,hashlib,math,collections
ACCEPTED='ASSEMBLY_V1_ACCEPTED'
COUNTRIES={'BN','KH','ID','LA','MY','MM','PH','SG','TH','TL','VN'}
TARGET_ACCOUNTS={
 'Astar':{'electricity'},
 'ResidentialFuel':{'oil','gas','coal','biomass'},
 'ServicesFuel':{'oil','gas','coal','biomass'},
 'IndustryFinalEnergy':{'oil','gas','coal','biomass'},
 'AgricultureFinalEnergy':{'oil','coal','biomass'},
 'RoadResidualFuel':{'oil','gas','biomass'},
 'DomesticShippingFuel':{'oil'},'DomesticAviationFuel':{'oil'},
 'InternationalShippingBunker':{'oil'},'InternationalAviationBunker':{'oil'},
 'TransportEmbeddedFuelParent':{'unclassified_fuel'},
}
def load_registry(folder):
 folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
 if 'registry.json' not in manifest['files']:raise ValueError('Registry not pinned')
 for rel,digest in manifest['files'].items():
  path=(folder/rel).resolve()
  if not path.is_relative_to(folder.resolve()):raise ValueError('Source outside registry boundary')
  if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Source/registry hash changed: '+rel)
 data=json.loads((folder/'registry.json').read_text())
 base_path=folder/'sources/BASE_RECONSTRUCTION.json'
 if base_path.exists():
  base={r['AccountID']:r for r in json.loads(base_path.read_text())['accounts']}
  for r in data['records']:
   if r.get('Source')!='sources/BASE_RECONSTRUCTION.json' or r['Kind']!='DEMAND' or r['Year']!=2050:continue
   b=base[r['Locator']]
   if r['SourceSHA256']!=manifest['files']['sources/BASE_RECONSTRUCTION.json']:raise ValueError('Base source reference hash mismatch')
   if r.get('BaseValueMWh')!=b['ValueMWh'] or r.get('BaseStatus')!=b['Status']:raise ValueError('Base source/value/status mismatch')
   if r['AssemblyStatus']==ACCEPTED and b['Status']!='NUMERIC_INPUT_READY':raise ValueError('Unqualified base promoted by target method')
   if r.get('Classification')=='SOURCE_SUPPORTED_NOT_APPLICABLE' and (b['Classification']!='SOURCE_SUPPORTED_NOT_APPLICABLE' or r.get('ZeroEvidence')!=';'.join(b['ZeroEvidence'])):raise ValueError('Exclusion has no pinned source proof')
 return data
def validate_records(records):
 seen=set()
 for r in records:
  if r['InputID'] in seen:raise ValueError('Duplicate input ownership')
  seen.add(r['InputID'])
  if r['Year']==2050 and r['Account']=='RoadEVFinalElectricity':
   if (r['Kind']!='BOUNDARY' or r['Required'] or r['Value'] is not None
       or r['Representation']!='EMBEDDED_IN_ASTAR'
       or r.get('Materialisation')!='NOT_SEPARATELY_MATERIALISED'
       or r.get('Sensitivity')!='DEFERRED_TO_EV_SENSITIVITY'
       or r['ParentAccount']!=r['Country']+':2050:Electricity:Astar:electricity'):
    raise ValueError('Assembly V1 Road EV must remain embedded, unknown, and non-materialised')
  if r['Account']=='RoadParent' and (r['Kind']!='ACCOUNTING' or r['Required']):
   raise ValueError('Road parent is accounting-only, not an additional demand Load')
  if r['AssemblyStatus']=='HUMAN_ACCEPTED':raise ValueError('Assembly status cannot impersonate human acceptance')
  if r['AssemblyStatus']!=ACCEPTED:continue
  if not r['SourceQualified'] or not r['Source'] or not r['SourceSHA256'] or not r['Transformation']:raise ValueError('Unqualified accepted source')
  if not isinstance(r['Year'],int) or not isinstance(r['SourceYear'],int):raise ValueError('Unknown year')
  if r['Kind']=='BOUNDARY':
   if r['Value'] is not None:raise ValueError('Boundary availability must not masquerade as zero physical resource')
   continue
  if r['Value'] is None or not r['Unit'] or isinstance(r['Value'],bool):raise ValueError('Accepted number or unit missing')
  value=float(r['Value'])
  if not math.isfinite(value) or value<0:raise ValueError('Invalid accepted input')
  if r['Kind']=='DEMAND':
   if r['Country'] not in COUNTRIES:raise ValueError('Unowned demand')
   if r['Unit']!='MWh/year':raise ValueError('Demand must be normalised once to MWh/year')
   if r['Year']!=r['SourceYear'] and not r.get('ProjectionEvidence'):raise ValueError('Base-year input relabelled as forecast')
   if r['Account']=='Astar' and r['ParentAccount']:raise ValueError('Astar is a national parent, not a duplicate child')
   if value==0 and not r.get('ZeroEvidence'):raise ValueError('No source-qualified zero evidence')
 return True
def check(records,year,allocation_dir=None,registry_path=None,known_unallocated=None):
 validate_records(records)
 demands=[r for r in records if r['Kind']=='DEMAND' and r['Year']==year and r['Required']]
 if not demands:raise ValueError('Empty target-year obligation registry')
 if year==2050:
  expected={(c,a,k) for c in COUNTRIES for a,carriers in TARGET_ACCOUNTS.items() for k in carriers}
  actual={(r['Country'],r['Account'],r['Carrier']) for r in demands}
  if actual!=expected or len(demands)!=len(expected):raise ValueError('Required ownership account set changed without an approved representation')
  embedded=[r for r in records if r['Year']==year and r['Account']=='RoadEVFinalElectricity']
  if len(embedded)!=11 or {r['Country'] for r in embedded}!=COUNTRIES:raise ValueError('Missing country Road EV embedded ownership decision')
 excluded=[r for r in demands if r.get('Classification')=='SOURCE_SUPPORTED_NOT_APPLICABLE']
 for r in excluded:
  if not r.get('ExclusionEvidence') or not r.get('SourceSHA256') or not (r.get('ZeroEvidence') or (r['Country']=='TL' and r['Account']=='IndustryFinalEnergy' and r.get('BaseStatus')=='BOUNDARY_EXCLUSION')):
   raise ValueError('Unsupported exclusion; empty selection is not zero')
  if r['Value'] is not None:raise ValueError('Exclusion must not masquerade as a physical zero Load')
 physical=[r for r in demands if r not in excluded]
 numeric=[r for r in physical if r['AssemblyStatus']==ACCEPTED]
 missing=[r for r in physical if r['AssemblyStatus']!=ACCEPTED]
 allocations=set()
 if allocation_dir:
  from allocate_assembly_inputs import verify_allocation
  allocations=verify_allocation(allocation_dir,records,registry_path)
 allocation_missing=[r['InputID'] for r in numeric if r['InputID'] not in allocations]
 supply_pending=[r['InputID'] for r in records if r['Kind']=='EXTERNAL_SUPPLY' and r['Year']==year and (r['AssemblyStatus']!=ACCEPTED or not r['TargetReady'])]
 unowned=known_unallocated or []
 numeric_ready=not missing and not supply_pending and not unowned
 allocation_ready=numeric_ready and not allocation_missing
 return dict(status='INPUT_GATE_ONLY_PASS' if allocation_ready else 'BLOCKED_INPUT_FREEZE' if not numeric_ready else 'BLOCKED_ALLOCATION',year=year,
  required_target_demands=len(demands),source_supported_nonphysical_accounts=len(excluded),required_physical_accounts=len(physical),
  numeric_accepted_target_demands=len(numeric),accepted_target_demands=len(allocations),numeric_unresolved=len(missing),
  NUMERIC_INPUT_READY=numeric_ready,ALLOCATION_READY=allocation_ready,NETWORK_STATICALLY_VALIDATED=False,
  unresolved_by_sector=dict(collections.Counter(r['Sector'] for r in missing)),unresolved_input_ids=[r['InputID'] for r in missing],
  known_positive_unowned_accounts=sum(r.get('OwnershipStatus')!='UNIQUE_SOURCE_USE_ASSIGNED' for r in unowned),known_positive_target_method_pending=len(unowned),missing_astar_countries=sorted(COUNTRIES-{r['Country'] for r in numeric if r['Account']=='Astar'}),
  allocation_missing=allocation_missing,external_supply_pending=supply_pending,
  embedded_road_ev='EMBEDDED_IN_ASTAR_NOT_SEPARATELY_MATERIALISED' if year==2050 else 'NOT_APPLICABLE',
  carbon_validation_stage='POST_BUILD_STATIC_VALIDATION_BLOCKER',network_construction_started=False,network_exported=False,solver_status='NOT_RUN',solver_runs=0)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--year',type=int,default=2050);p.add_argument('--output',type=Path,required=True);p.add_argument('--allocation',type=Path);a=p.parse_args()
 folder=a.repo/'research_inputs/assembly_v1';data=load_registry(folder)
 result=check(data['records'],a.year,a.allocation,folder/'registry.json',data.get('known_unallocated_base_accounts'))
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['unresolved_input_ids','allocation_missing']}))
 raise SystemExit(0 if result['status']=='INPUT_GATE_ONLY_PASS' else 2)
