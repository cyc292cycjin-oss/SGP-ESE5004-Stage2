"""Bounded, read-only Gate4 source and topology identity recovery."""
from pathlib import Path
import csv,io,json,hashlib,subprocess as sp,sys,collections
W=Path(__file__).resolve().parent;E=W/'evidence';E.mkdir(parents=True,exist_ok=True)
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
HEAD='fa82156ee74a1fd2a93a88b774c9f9827c2d3f4c'
def git(*a):return sp.check_output(['git',*a],cwd=R,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert git('branch','--show-current')=='research/full-sc-baseline' and git('rev-parse','HEAD')==HEAD and not git('status','--porcelain')
start=dict(head=HEAD,branch=git('branch','--show-current'),remote_refs=git('ls-remote','origin'),status='CLEAN')
assert HEAD+'\trefs/heads/research/full-sc-baseline' in start['remote_refs']
assert 'a3616a68ee44592af6527ca9024a90f1956646ae\trefs/heads/main' in start['remote_refs']
start['gate2_hashes']={str(p.relative_to(R)):sha(p) for p in (R/'research_inputs/demand').rglob('*') if p.is_file()}
(E/'START.json').write_text(json.dumps(start,indent=2))
sys.path.insert(0,str(R/'scripts_project'));from demand_sources import load_sources
sources=load_sources(R,verify_originals=True)
(E/'SOURCES_VERIFIED.json').write_text(json.dumps({k:dict(source=v['source'],sha256=v['source_sha256'],records=len(v['records'])) for k,v in sources.items()},indent=2))
def rows(path):return list(csv.DictReader(io.StringIO(path)))
versions={}
for tag,prefix in [('plus_01','data/osm-plus-prebuilt/0.1'),('plus_011','data/osm-plus-prebuilt/0.1.1')]:
 obj={}
 for file in ['all_buses_build_network.csv','all_lines_build_network.csv','all_transformers_build_network.csv','all_converters_build_network.csv','all_clean_generators.csv']:
  p=R/prefix/file;rr=rows(p.read_text());selected=[]
  for r in rr:
   keys=['bus_id'] if file.startswith('all_buses') else ['bus0','bus1','bus','bus_id']
   if any(r.get(k) in ('765','766') for k in keys):selected.append({k:v for k,v in r.items() if k not in ('geometry','bounds')})
  obj[file]=dict(sha256=sha(p),rows=len(rr),endpoint_765_766=selected)
 versions[tag]=obj
paper='5bacad702ccfed17ad19ab510fa710651e966f2c'
for ref in [paper,'138ea07b21c55727c937831c396e80286b5ef586']:
 obj={}
 for file in ['all_buses_build_network.csv','all_transformers_build_network.csv']:
  rel='data/osm-plus-prebuilt/0.1.1/'+file;data=sp.check_output(['git','show',ref+':'+rel],cwd=R)
  rr=rows(data.decode());keys=['bus_id'] if file.startswith('all_buses') else ['bus0','bus1']
  obj[file]=dict(sha256=hashlib.sha256(data).hexdigest(),rows=len(rr),endpoint_765_766=[{k:v for k,v in r.items() if k not in ('geometry','bounds')} for r in rr if any(r.get(k) in ('765','766') for k in keys)])
 versions[ref]=obj
(E/'TOPOLOGY_PROVENANCE.json').write_text(json.dumps(versions,indent=2))
(E/'TOPOLOGY_COMMIT.txt').write_text(git('show','--format=fuller','--stat','138ea07b21c55727c937831c396e80286b5ef586'))
(E/'modification_list.txt').write_bytes((R/'data/osm-plus-prebuilt/0.1.1/modification_list.txt').read_bytes())
from phase4_static import config,json_evidence
cfg=config(R);(E/'EFFECTIVE_CONFIG.json').write_text(json.dumps(json_evidence(cfg),indent=2,default=str))
inventory={}
for base in [R,Path('/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean')]:
 files=[]
 for folder,pattern in [('resources','*cost*2050*.csv'),('resources','*energy*2050*.csv'),('data','*growth*.csv'),('data','*calor*'),('data','*cost*2050*.csv')]:
  for p in (base/folder).rglob(pattern):files.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
 inventory[str(base)]=files
(E/'EXISTING_INPUT_FILES.json').write_text(json.dumps(inventory,indent=2))
print('Topology targeted records:',json.dumps(versions,indent=2))
print('Input files:',json.dumps(inventory,indent=2))
for k in ['demand_data','industry','sector','co2','snapshots','scenario']:
 if k=='sector':print(k,json.dumps({x:cfg[k].get(x) for x in ['land_transport_electric_share','land_transport_fuel_cell_share','transport_electric_share','industry','industry_growth','solid_biomass_potential','biogas_potential','co2_sequestration_potential']}))
 else:print(k,json.dumps(cfg.get(k),default=str)[:2500])
