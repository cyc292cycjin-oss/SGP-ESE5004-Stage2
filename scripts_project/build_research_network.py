"""Guarded Gate4 assembler: qualified assets + Gate2 allocations + Gate3 fragment.

This entry point never prepares optimization variables or calls a solver. Missing
numeric inputs, allocations, or a source-qualified 2050 asset bundle stop BEFORE
network construction. The cached solved paper network is not an allowed base.
"""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
from check_assembly_inputs import load_registry,check
from carrier_architecture import Fragment,to_pypsa_fragment
from carbon_architecture import classify_record
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pinned(folder,entry):
 p=(folder/entry['file']).resolve()
 if not p.is_relative_to(folder.resolve()) or not p.is_file() or sha(p)!=entry['sha256']:raise ValueError('Qualified asset missing or hash changed')
 return p
def static_validate(n,records,allocation,carbon_map):
 import networkx as nx
 import pandas as pd
 if not n.snapshots.equals(pd.date_range('2013-01-01','2013-12-31 21:00',freq='3h')):raise ValueError('Research snapshot boundary changed')
 if not np.all(n.snapshot_weightings.to_numpy()==3):raise ValueError('Physical weights changed')
 if len(n.buses[n.buses.carrier.isin(['AC','DC'])])!=100:raise ValueError('Not100 geographical electric buses')
 if n.global_constraints.shape[0]:raise ValueError('Baseline cannot carry a policy cap')
 if n.meta.get('solver_allowed') is not False:raise ValueError('Solver guard missing')
 load=n.loads_t.p_set.reindex(columns=n.loads.index)
 if load.isna().any().any() or not np.isfinite(load.values).all() or (load.values<0).any():raise ValueError('Invalid actual Load')
 for name,table in [('loads',n.loads),('generators',n.generators),('stores',n.stores),('storage_units',n.storage_units),('links',n.links),('lines',n.lines),('transformers',n.transformers)]:
  for col in [c for c in table if c=='bus' or c.startswith('bus') and c[3:].isdigit()]:
   if any(b not in n.buses.index for b in table[col] if b):raise ValueError('Dangling '+name+' bus')
 expected={r['InputID']:float(r['Value']) for r in records if r['Year']==2050 and r['Kind']=='DEMAND' and r.get('Classification','REQUIRED_PHYSICAL')=='REQUIRED_PHYSICAL'}
 owners=n.meta['demand_owners'];actual={k:0. for k in expected}
 if set(owners)!=set(n.loads.index):raise ValueError('Unexpected or unowned Load; embedded/legacy duplicate possible')
 for name,rid in owners.items():
  if rid not in actual:raise ValueError('Unaccepted physical obligation')
  actual[rid]+=float((load[name]*n.snapshot_weightings.generators).sum())
 if any(not np.isclose(v,actual[k],rtol=1e-10,atol=1e-6) for k,v in expected.items()):raise ValueError('Actual network demand conservation failed')
 # Exclude electric and atmosphere buses: electricity-mediated benefits are
 # allowed; direct/multihop physical fuel sharing across countries is not.
 electric=set(n.buses.index[n.buses.carrier.isin(['AC','DC','electricity','low voltage'])]);atmo=set(n.buses.index[n.buses.carrier=='co2 atmosphere'])
 g=nx.Graph();g.add_nodes_from(set(n.buses.index)-electric-atmo);borders=[]
 for typ,table in [('Link',n.links),('Line',n.lines),('Transformer',n.transformers)]:
  for name,z in table.iterrows():
   ports=[z[c] for c in table.columns if c.startswith('bus') and c[3:].isdigit() and z[c]]
   physical=[b for b in ports if b not in atmo]
   countries={n.buses.at[b,'country'] for b in physical}
   if len(countries)>1:
    if not set(physical)<=electric:raise ValueError('Cross-country non-electric component: '+name)
    borders.append(dict(type=typ,name=name,countries=sorted(countries)))
   non=[b for b in physical if b not in electric]
   g.add_edges_from(zip(non,non[1:]))
 for component in nx.connected_components(g):
  if len({n.buses.at[b,'country'] for b in component})!=1:raise ValueError('Hidden cross-country carrier path')
 if any(n.buses.carrier=='co2 sequestered'):raise ValueError('Unaccepted geological inventory asset')
 mapped={}
 for r in carbon_map:
  key=(r['component_type'],r['component'])
  if key in mapped:raise ValueError('Duplicate carbon attribution')
  table={'Link':n.links,'Generator':n.generators}[r['component_type']]
  if r['component'] not in table.index:raise ValueError('Carbon map does not refer to actual component')
  mapped[key]=classify_record(r['component'],r['carrier'],r['sector'],r['country'],r['coefficient'],source=r['source'],policy_weight=r['policy_weight'],accepted=r['accepted'])
 events={('Link',name) for name,z in n.links.iterrows() if any(z[c] in atmo for c in n.links if c.startswith('bus') and c[3:].isdigit() and z[c])}
 events|={('Generator',name) for name,z in n.generators.iterrows() if float(n.carriers.at[z.carrier,'co2_emissions'])!=0}
 if set(mapped)!=events:raise ValueError('Incomplete/extraneous actual carbon scope')
 # Require actual local conversion topology, not merely carrier names.
 paths=set()
 for _,z in n.links.iterrows():
  a=n.buses.at[z.bus0,'carrier'];outputs={n.buses.at[z[c],'carrier'] for c in n.links if c.startswith('bus') and c[3:].isdigit() and c!='bus0' and z[c] and float(z['efficiency' if c=='bus1' else 'efficiency'+c[3:]])>0}
  if a in ['AC','electricity','low voltage'] and 'H2' in outputs:paths.add('electrolysis')
  if a=='gas' and 'H2' in outputs:paths.add('steam_methane_reforming')
  if a=='H2' and 'oil' in outputs:paths.add('FT')
 if not {'electrolysis','steam_methane_reforming','FT'}<=paths:raise ValueError('Missing required actual sector-coupling paths')
 # Every finite biomass resource must identify isolated obligation-only buses.
 biomass=[name for name,z in n.stores.iterrows() if z.carrier in ['solid biomass','biomass','biogas']]
 routes=n.meta.get('biomass_obligation_routes',{})
 if set(biomass)!=set(routes):raise ValueError('Biomass routing/cap evidence missing')
 for name in biomass:
  z=n.stores.loc[name];allowed=set(routes[name]['buses']);bus=z.bus
  touching=n.links[n.links.filter(regex=r'^bus\d+$').eq(bus).any(axis=1)]
  for _,link in touching.iterrows():
   if link.bus0!=bus or link.bus1 not in allowed:raise ValueError('Biomass diversion to unapproved technology')
  supplied=[k for k,r in n.loads.iterrows() if r.bus in allowed]
  obligation=float((load[supplied].sum(axis=1)*n.snapshot_weightings.generators).sum())
  if z.e_nom_extendable or z.e_cyclic or not np.isclose(z.e_initial,obligation) or not np.isclose(z.e_nom,obligation):raise ValueError('Biomass cap differs from fixed obligation')
 return dict(status='NETWORK_STATICALLY_VALIDATED',loads=len(n.loads),physical_hours=8760,electricity_border_controls=borders,carbon_components=len(mapped),actual_coupling_paths=sorted(paths),policy_cap_enabled=False,solver_runs=0)
def build(repo,allocation,assets,output,report):
 import yaml
 config=yaml.safe_load((repo/'configs/research/baseline.yaml').read_text())
 if config['research_carbon']['policy_enabled'] or config['research_assembly']['solver_allowed'] or config['research_assembly']['target_year']!=2050:raise ValueError('Unapproved carbon/solve/target-year configuration')
 folder=repo/'research_inputs/assembly_v1';data=load_registry(folder)
 gate=check(data['records'],2050,allocation,folder/'registry.json',data.get('known_unallocated_base_accounts'))
 receipt=dict(input_gate=gate,network_exported=False,network_sha256=None,solver_runs=0,policy_cap_enabled=False)
 def save():report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(receipt,indent=2)+'\n')
 if not gate['ALLOCATION_READY']:receipt['status']=gate['status'];save();return 2
 try:
  bundle=json.loads(assets.read_text());root=assets.parent
  if bundle.get('status')!='SOURCE_QUALIFIED_2050_UNSOLVED' or bundle.get('source_is_solved') is not False:raise ValueError('No qualified2050 electric/carrier asset bundle; solved paper archive is not a substitute')
  import pypsa
  n=pypsa.Network(pinned(root,bundle['electric_base']))
  if len(n.loads) or len(n.global_constraints):raise ValueError('Legacy demand/policy leakage in electric base')
  for component in n.iterate_components():
   if any(len(v.columns) for k,v in component.pnl.items() if component.attrs.at[k,'status']=='Output'):raise ValueError('Solved outputs cannot enter research base')
  f=Fragment();raw=json.loads(pinned(root,bundle['carrier_fragment']).read_text())
  f.buses=raw['buses'];f.components=raw['components'];f.markets=raw.get('markets',{})
  sub=to_pypsa_fragment(f,list(n.snapshots),list(n.snapshot_weightings.generators),component_ids=list(f.components))
  # Electric attachment IDs in the reviewed fragment must be actual base buses.
  for c in sub.iterate_components():
   duplicate=c.df.index.intersection(n.df(c.name).index)
   if len(duplicate) and c.name not in ['Bus','Carrier']:raise ValueError('Duplicate base/fragment component')
   if c.name=='Bus' and any(c.df.at[k,'country']!=n.buses.at[k,'country'] for k in duplicate):raise ValueError('Mismatched electric attachment country')
   table=c.df.loc[c.df.index.difference(n.df(c.name).index)]
   if len(table):n.import_components_from_dataframe(table,c.name)
  n.meta.update(sub.meta);n.meta.update(target_year=2050,weather_year=2013,solver_allowed=False,demand_owners={},biomass_obligation_routes=raw.get('biomass_obligation_routes',{}))
  m=json.loads((allocation/'allocation_manifest.json').read_text());posting=raw['demand_destinations']
  with np.load(allocation/m['arrays_file'],allow_pickle=False) as z:
   for r in m['records']:
    for j,node in enumerate(r['Nodes']):
     if not np.any(z[r['ArrayKey']][:,j]):continue
     key=r['InputID']+'@'+node;bus=posting[key]
     if bus not in n.buses.index or n.buses.at[bus,'country']!=r['Country']:raise ValueError('Missing/misowned demand destination')
     n.add('Load',key,bus=bus,p_set=z[r['ArrayKey']][:,j]);n.meta['demand_owners'][key]=r['InputID']
  carbon=json.loads(pinned(root,bundle['carbon_map']).read_text())
  static_validate(n,data['records'],allocation,carbon)
  output.parent.mkdir(parents=True,exist_ok=True);n.export_to_netcdf(output)
  actual=pypsa.Network(output);validation=static_validate(actual,data['records'],allocation,carbon)
  receipt.update(status='NETWORK_STATICALLY_VALIDATED',network_exported=True,network_sha256=sha(output),actual_network_validation=validation)
 except (ValueError,KeyError,FileNotFoundError) as exc:receipt.update(status='BLOCKED_BUILD_ASSET_OR_STATIC_VALIDATION',reason=str(exc));save();return 2
 save();return 0
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
 for k in ['allocation','assets','output','report']:p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();raise SystemExit(build(**vars(a)))
