"""Strict referential audit of pinned prebuilt electricity inputs; no model/solve."""
from pathlib import Path
import csv,hashlib,json,argparse,collections,math
FILES={'Bus':'all_buses_build_network.csv','Line':'all_lines_build_network.csv','Transformer':'all_transformers_build_network.csv','Link':'all_converters_build_network.csv','Generator':'all_clean_generators.csv'}
COUNTRIES={'BN','KH','ID','LA','MY','MM','PH','SG','TH','TL','VN'}
def tables(folder):
 result={}
 for k,name in FILES.items():
  with (Path(folder)/name).open(newline='') as f:result[k]=list(csv.DictReader(f))
 return result
def inspect(t):
 buses={r['bus_id']:r for r in t['Bus']};bad=[];reviews=[]
 if len(buses)!=len(t['Bus']):bad.append({'issue':'DUPLICATE_BUS'})
 for b,r in buses.items():
  if r['country'] not in COUNTRIES:bad.append({'issue':'UNKNOWN_COUNTRY','bus':b})
  for key in ['lon','lat','voltage']:
   try:valid=math.isfinite(float(r[key])) and (key!='voltage' or float(r[key])>0)
   except (ValueError,KeyError):valid=False
   if not valid:bad.append({'issue':'INVALID_BUS_METADATA','bus':b,'field':key})
 adjacency={b:set() for b in buses};edge_rows=[]
 for kind,rows in t.items():
  if kind=='Bus':continue
  for r in rows:
   ports={k:v for k,v in r.items() if k in ('bus','bus_id') or k.startswith('bus') and k[3:].isdigit()}
   ports={k:v for k,v in ports.items() if v not in ('',None)}
   identity=r.get('line_id',r.get('converter_id',r.get('name',r.get('',''))))
   missing=[v for v in ports.values() if v not in buses]
   if missing:bad.append(dict(issue='DANGLING_ENDPOINT',component=kind,name=identity,missing=missing))
   if kind in ('Line','Transformer','Link'):
    a,b=r['bus0'],r['bus1'];ca=buses.get(a,{}).get('country');cb=buses.get(b,{}).get('country')
    if ca and cb:
     adjacency[a].add(b);adjacency[b].add(a)
     # Valid foreign-country endpoints are not referential errors. Preserve
     # their explicit border classification for physical/control-set review.
     if kind=='Transformer' and ca!=cb:reviews.append(dict(issue='CROSS_BORDER_TRANSFORMER_REVIEW',name=identity,country0=ca,country1=cb))
    edge_rows.append(dict(component=kind,name=identity,bus0=a,bus1=b,country0=ca,country1=cb,classification='UNKNOWN' if not ca or not cb else 'DOMESTIC' if ca==cb else 'CROSS_BORDER'))
 seen=set();groups=[]
 for b in sorted(buses):
  if b in seen:continue
  todo=[b];group=[];seen.add(b)
  while todo:
   x=todo.pop();group.append(x)
   for other in adjacency[x]-seen:seen.add(other);todo.append(other)
  groups.append(sorted(group))
 groups=sorted(groups)
 return dict(status='FAIL' if bad else 'PASS',issues=bad,ownership_reviews=reviews,counts={k:len(v) for k,v in t.items()},country_counts=dict(collections.Counter(r['country'] for r in t['Bus'])),retained_bus_connected_components=groups,electricity_edges=edge_rows)
def require_valid(folder):
 result=inspect(tables(folder))
 if result['issues']:raise ValueError(json.dumps(result['issues']))
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 result=inspect(tables(a.folder));result['input_hashes']={n:hashlib.sha256((a.folder/n).read_bytes()).hexdigest() for n in FILES.values()}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2));print(json.dumps({k:result[k] for k in ['status','issues','counts']}))
 raise SystemExit(bool(result['issues']))
