"""Actual country/node/time allocations from pinned exogenous author inputs.

The solved reference is used ONLY for geographical buses, snapshot weights and
base-load p_set input shapes. No optimised capacity, dispatch, dual or objective
is read. This does not qualify its 2025 infrastructure as a 2050 research base.
"""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
import pandas as pd
from final_closure_inputs import record_fingerprint
PIN='06152be56ee41f64bfdca42fd24aeaf363ab61f931fec7b5e4bc12f6d6456ecb'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def closest(point,nodes):
 lat=np.radians(nodes.y.to_numpy(float));lon=np.radians(nodes.x.to_numpy(float))
 a=np.sin((lat-np.radians(point.y))/2)**2+np.cos(lat)*np.cos(np.radians(point.y))*np.sin((lon-np.radians(point.x))/2)**2
 return int(np.argmin(a))
def allocate(registry,reference,ports,airports,output,reuse=None,reuse_registry=None):
 import pypsa
 if sha(reference)!=PIN:raise ValueError('Author reference changed')
 n=pypsa.Network(reference);geo=n.buses[n.buses.carrier.isin(['AC','DC'])].copy()
 if len(geo)!=100:raise ValueError('Expected actual 100 geographical buses')
 expected=pd.date_range('2013-01-01','2013-12-31 21:00:00',freq='3h')
 if not n.snapshots.equals(expected):raise ValueError('Not full2013 3h')
 w=n.snapshot_weightings.generators.to_numpy(float)
 if not np.all(w==3) or w.sum()!=8760:raise ValueError('Not physical8760h')
 # Exact base-load identity prevents old EV or industry children being added.
 base_loads=n.loads.index[n.loads.index.isin(geo.index)&(n.loads.carrier=='AC')]
 for name in base_loads:
  bus=n.loads.at[name,'bus']
  if bus not in {name,name+' low voltage'}:raise ValueError('Unverified base-load node attachment')
 p=n.loads_t.p_set.reindex(columns=base_loads).copy()
 if p.isna().any().any() or not np.isfinite(p.values).all() or (p.values<0).any():raise ValueError('Invalid base-load inputs')
 p.columns=base_loads
 p=p.T.groupby(level=0).sum().T
 data=json.loads(Path(registry).read_text());rows=[r for r in data['records'] if r['Year']==2050 and r['Kind']=='DEMAND' and r.get('NumericStatus')=='NUMERIC_INPUT_READY']
 points={'port':pd.read_csv(ports),'airport':pd.read_csv(airports)}
 arrays={'weights':w,'snapshots':n.snapshots.astype(str).to_numpy(dtype='U19')};out=[];mapping=[];failed=[]
 reused={};reused_arrays={};reuse_ids=[]
 if reuse:
  old=json.loads((reuse/'allocation_manifest.json').read_text())
  if any(old[k]!=sha(v) for k,v in [('reference_sha256',reference),('ports_sha256',ports),('airports_sha256',airports)]) or sha(reuse/old['arrays_file'])!=old['arrays_sha256']:raise ValueError('Reuse source/hash drift')
  if not reuse_registry or sha(reuse_registry)!=old['input_registry_sha256']:raise ValueError('Reuse registry/source identity missing')
  prior_records={r['InputID']:r for r in json.loads(Path(reuse_registry).read_text())['records']}
  reused={r['InputID']:dict(r,ScientificInputSHA256=record_fingerprint(prior_records[r['InputID']])) for r in old['records']}
  with np.load(reuse/old['arrays_file'],allow_pickle=False) as z:
   reused_arrays={k:z[v['ArrayKey']].copy() for k,v in reused.items()}
  oldmap=json.loads((reuse/'point_node_mapping.json').read_text())
 for r in rows:
  country=r['Country'];nodes=geo[geo.country==country];ids=list(nodes.index)
  prev=reused.get(r['InputID'])
  if prev and prev['Country']==country and prev['Nodes']==ids and prev['AnnualMWh']==float(r['Value']) and prev['ScientificInputSHA256']==record_fingerprint(r):
   x=reused_arrays[r['InputID']];key='d'+str(len(out))
   if hashlib.sha256(x.tobytes()).hexdigest()!=prev['ArraySHA256']:raise ValueError('Reused array hash changed')
   arrays[key]=x;out.append(dict(prev,ArrayKey=key));reuse_ids.append(r['InputID']);mapping.extend(z for z in oldmap if z['InputID']==r['InputID']);continue
  local=p.reindex(columns=ids,fill_value=0).to_numpy(float);annual=(local*w[:,None]).sum(axis=0)
  if annual.sum()<=0:raise ValueError('No country input shape: '+country)
  if r['Account']=='Astar':
   x=float(r['Value'])*local/annual.sum();method='NORMALISED_AUTHOR_BASE_LOAD_INPUT_PSET'
  else:
   kind='port' if 'Shipping' in r['Account'] else 'airport' if 'Aviation' in r['Account'] else None
   if kind:
    pts=points[kind][points[kind].country==country]
    if pts.empty:
     failed.append(dict(InputID=r['InputID'],reason='No '+kind+' weight; no arbitrary equal/fallback assignment'));continue
    if not np.isfinite(pts[['x','y','fraction']].values).all() or (pts.fraction<0).any() or not np.isclose(pts.fraction.sum(),1,rtol=1e-9):raise ValueError('Invalid point country weights')
    a=np.zeros(len(ids))
    for _,z in pts.iterrows():
     idx=closest(z,nodes);a[idx]+=z.fraction
     mapping.append(dict(InputID=r['InputID'],Country=country,Kind=kind,Point=str(z.get('name','')),x=float(z.x),y=float(z.y),Node=ids[idx],Fraction=float(z.fraction)))
    method='SAME_COUNTRY_NEAREST_GEOGRAPHIC_NODE_'+kind.upper()+'_SIZE_WEIGHTS_FLAT_TIME'
   else:a=annual/annual.sum();method='AUTHOR_BASE_LOAD_ANNUAL_NODE_SHARES_FLAT_TIME'
   x=np.tile(float(r['Value'])*a/w.sum(),(len(w),1))
  if not np.isfinite(x).all() or (x<0).any():raise ValueError('Invalid allocation')
  total=float((x*w[:,None]).sum())
  if not np.isclose(total,float(r['Value']),rtol=1e-12,atol=1e-6):raise ValueError('Country/node/time non-conservation')
  key='d'+str(len(out));arrays[key]=x
  out.append(dict(InputID=r['InputID'],Country=country,Year=2050,ScientificInputSHA256=record_fingerprint(r),Nodes=ids,NodeCountries=list(nodes.country),ArrayKey=key,AnnualMWh=float(r['Value']),AllocatedMWh=total,Method=method,ArraySHA256=hashlib.sha256(x.tobytes()).hexdigest()))
 output=Path(output);output.mkdir(parents=True,exist_ok=True);np.savez_compressed(output/'allocations.npz',**arrays)
 receipt=dict(schema='actual-allocation-v1',input_registry_sha256=sha(registry),reference_sha256=sha(reference),reference_is_solved=True,used_only_exogenous_inputs=True,
  ports_sha256=sha(ports),airports_sha256=sha(airports),snapshots=len(w),hours=float(w.sum()),geographical_buses=100,arrays_file='allocations.npz',arrays_sha256=sha(output/'allocations.npz'),
  records=out,failures=failed,limitations=['Author2025 base-load input supplies relative shape only; absolute2050 load is independent accepted Astar.','Fuel flat-time and base-load node-share proxies are not observed hourly fuel demands.','Port/airport size weights proxy location, not traffic/fuel-burn measurements.','No qualification of reference2025 infrastructure/costs/brownfield history for2050.'],solver_runs=0)
 receipt['reused_unchanged_array_ids']=reuse_ids
 (output/'point_node_mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
 (output/'geographic_nodes.json').write_text(geo[['country','x','y','carrier']].to_json(orient='index',indent=2))
 receipt.update(geographic_nodes_file='geographic_nodes.json',geographic_nodes_sha256=sha(output/'geographic_nodes.json'),point_node_mapping_sha256=sha(output/'point_node_mapping.json'))
 (output/'allocation_manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(dict(allocated_accounts=len(out),failed_accounts=len(failed),snapshots=len(w),hours=float(w.sum()),allocation_sha256=receipt['arrays_sha256'])))
 return receipt
def verify_allocation(folder,records,registry_path=None):
 folder=Path(folder);m=json.loads((folder/'allocation_manifest.json').read_text());p=(folder/m['arrays_file']).resolve()
 if not p.is_relative_to(folder.resolve()) or sha(p)!=m['arrays_sha256']:raise ValueError('Allocation bytes missing or changed')
 if registry_path and sha(registry_path)!=m['input_registry_sha256']:raise ValueError('Allocation made for another registry')
 node_path=(folder/m['geographic_nodes_file']).resolve()
 if not node_path.is_relative_to(folder.resolve()) or sha(node_path)!=m['geographic_nodes_sha256']:raise ValueError('Node ownership table changed')
 nodes=json.loads(node_path.read_text())
 expected={r['InputID']:r for r in records if r['Kind']=='DEMAND' and r['Year']==2050 and r.get('AssemblyStatus')=='ASSEMBLY_V1_ACCEPTED'}
 seen=set()
 with np.load(p,allow_pickle=False) as z:
  weights=z['weights'];times=pd.to_datetime(z['snapshots'])
  if not times.equals(pd.date_range('2013-01-01','2013-12-31 21:00',freq='3h')) or weights.shape!=(2920,) or not np.all(weights==3):raise ValueError('Invalid physical snapshots/weights')
  for a in m['records']:
   rid=a['InputID']
   if rid in seen or rid not in expected:raise ValueError('Duplicate/unowned allocation')
   seen.add(rid);r=expected[rid];x=z[a['ArrayKey']]
   if a.get('ScientificInputSHA256') and a['ScientificInputSHA256']!=record_fingerprint(r):raise ValueError('Allocation source/value/method identity changed')
   if a['Country']!=r['Country'] or set(a['NodeCountries'])!={r['Country']} or len(a['Nodes'])!=len(set(a['Nodes'])) or any(node not in nodes or nodes[node]['country']!=r['Country'] for node in a['Nodes']):raise ValueError('Cross-country/duplicate node allocation')
   if x.shape!=(2920,len(a['Nodes'])) or not np.isfinite(x).all() or (x<0).any():raise ValueError('Invalid demand arrays')
   if hashlib.sha256(x.tobytes()).hexdigest()!=a['ArraySHA256']:raise ValueError('Array fingerprint changed')
   if not np.isclose(float(r['Value']),(x*weights[:,None]).sum(),rtol=1e-10,atol=1e-6):raise ValueError('Country/node/time conservation failed')
 return seen
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for x in ['registry','reference','ports','airports','output']:p.add_argument('--'+x,type=Path,required=True)
 p.add_argument('--reuse',type=Path)
 p.add_argument('--reuse-registry',type=Path)
 a=p.parse_args();allocate(**vars(a))
