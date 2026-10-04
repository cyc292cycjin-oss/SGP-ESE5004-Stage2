"""Fail-closed Assembly V1 input gate. Does not build a network or call a solver."""
from pathlib import Path
import argparse,json,hashlib,math,collections
ACCEPTED='ASSEMBLY_V1_ACCEPTED'
COUNTRIES={'BN','KH','ID','LA','MY','MM','PH','SG','TH','TL','VN'}
def load_registry(folder):
 folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
 if 'registry.json' not in manifest['files']:raise ValueError('Registry not pinned')
 for rel,digest in manifest['files'].items():
  path=(folder/rel).resolve()
  if not path.is_relative_to(folder.resolve()):raise ValueError('Source outside registry boundary')
  if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Source/registry hash changed: '+rel)
 return json.loads((folder/'registry.json').read_text())
def validate_records(records):
 seen=set()
 for r in records:
  if r['InputID'] in seen:raise ValueError('Duplicate input ownership')
  seen.add(r['InputID'])
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
   if r['Year']!=r['SourceYear'] and not r.get('ProjectionEvidence'):raise ValueError('Base-year input relabelled as forecast')
   if r['Account']=='Astar' and r['ParentAccount']:raise ValueError('Astar is a national parent, not a duplicate child')
   if value==0 and not r.get('ZeroEvidence'):raise ValueError('No source-qualified zero evidence')
 return True
def check(records,year):
 validate_records(records)
 demands=[r for r in records if r['Kind']=='DEMAND' and r['Year']==year and r['Required']]
 if not demands:raise ValueError('Empty target-year obligation registry')
 missing=[r for r in demands if r['AssemblyStatus']!=ACCEPTED or not r['TargetReady']]
 # Even a numerically accepted input requires node/time ownership before it
 # is a materialisable obligation. No default allocation is inferred here.
 allocation_missing=[r['InputID'] for r in demands if r['AssemblyStatus']==ACCEPTED and (not r.get('SpatialEvidence') or not r.get('TemporalEvidence'))]
 astar={r['Country'] for r in demands if r['Account']=='Astar' and r['AssemblyStatus']==ACCEPTED and r['TargetReady']}
 supply_pending=[r['InputID'] for r in records if r['Kind']=='EXTERNAL_SUPPLY' and r['Year']==year and (r['AssemblyStatus']!=ACCEPTED or not r['TargetReady'])]
 return dict(status='BLOCKED_INPUT_FREEZE' if missing or allocation_missing or supply_pending or astar!=COUNTRIES else 'INPUT_GATE_ONLY_PASS',year=year,required_target_demands=len(demands),accepted_target_demands=len(demands)-len(missing),unresolved_by_sector=dict(collections.Counter(r['Sector'] for r in missing)),missing_astar_countries=sorted(COUNTRIES-astar),allocation_missing=allocation_missing,external_supply_pending=supply_pending,network_construction_started=False,network_exported=False,solver_status='NOT_RUN',solver_runs=0)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--year',type=int,default=2050);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 result=check(load_registry(a.repo/'research_inputs/assembly_v1')['records'],a.year)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2));print(json.dumps(result))
 raise SystemExit(2 if result['status']=='BLOCKED_INPUT_FREEZE' else 0)
