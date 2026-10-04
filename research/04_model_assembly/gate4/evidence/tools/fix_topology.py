"""Record failing check, remove exactly one proven obsolete row, then validate."""
from pathlib import Path
import subprocess as sp,json,hashlib,sys,os
W=Path(__file__).resolve().parent;E=W/'evidence';S=W/'stage';R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
P='/home/jin/miniforge3/envs/pypsa-earth/bin/python'
def git(*a):return sp.check_output(['git',*a],cwd=R,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert git('rev-parse','HEAD')=='fa82156ee74a1fd2a93a88b774c9f9827c2d3f4c'
assert set(git('status','--porcelain').splitlines()) <= {'?? scripts_project/research_topology.py','?? tests/research/test_topology_integrity.py'}
if (E/'TOPOLOGY_BEFORE.log').exists():
 (E/'TOPOLOGY_INITIAL_DIAGNOSTIC.log').write_bytes((E/'TOPOLOGY_BEFORE.log').read_bytes())
for rel in ['scripts_project/research_topology.py','tests/research/test_topology_integrity.py']:
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((S/rel).read_bytes());p.chmod(0o644)
def test(name):
 p=sp.run([P,'tests/research/test_topology_integrity.py'],cwd=R,stdout=sp.PIPE,stderr=sp.STDOUT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'));(E/name).write_bytes(p.stdout);return p.returncode
assert test('TOPOLOGY_BEFORE.log')!=0
sys.path.insert(0,str(R/'scripts_project'));from research_topology import tables,inspect,FILES
folder=R/'data/osm-plus-prebuilt/0.1.1';before=inspect(tables(folder));assert before['issues']==[dict(issue='DANGLING_ENDPOINT',component='Transformer',name='transf_524_0',missing=['766'])]
inputs={name:sha(folder/name) for name in FILES.values()}
path=folder/FILES['Transformer'];data=path.read_bytes();lines=data.splitlines(keepends=True)
removed=[line for line in lines if b',transf_524_0,765,766,' in line];assert len(removed)==1
assert '* 766' in (folder/'modification_list.txt').read_text()
path.write_bytes(b''.join(line for line in lines if line not in removed))
assert test('TOPOLOGY_AFTER.log')==0
after=inspect(tables(folder));assert after['status']=='PASS'
assert before['retained_bus_connected_components']==after['retained_bus_connected_components']
assert all(sha(folder/name)==h for name,h in inputs.items() if name!=FILES['Transformer'])
proof=dict(before=before,after=after,removed_row=removed[0].decode().strip(),input_hashes_before=inputs,input_hashes_after={name:sha(folder/name) for name in FILES.values()},retained_bus_partition_unchanged=True,new_buses=0,removed_buses=0,removed_transformers=1,evidence_commit='138ea07b21c55727c937831c396e80286b5ef586',paper_reference='5bacad702ccfed17ad19ab510fa710651e966f2c',classification='engineering fix to retained obsolete reference; no physical new bus or line')
(E/'TOPOLOGY_FIX_PROOF.json').write_text(json.dumps(proof,indent=2))
paths=['data/osm-plus-prebuilt/0.1.1/all_transformers_build_network.csv','scripts_project/research_topology.py','tests/research/test_topology_integrity.py']
(E/'TOPOLOGY_FIX.diff').write_text(git('diff','--',paths[0]))
assert len(git('diff','--numstat','--',paths[0]).split())==3
sp.run(['git','add','--',*paths],cwd=R,check=False)
assert set(git('diff','--cached','--name-only').splitlines())==set(paths)
assert not git('diff','--name-only')
sp.run(['git','-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','commit','-m','fix: repair dangling upstream topology reference','-m','Commit 138ea07b explicitly removed Thai bus 766 in prebuilt 0.1.1 but retained transf_524_0. Remove that sole obsolete transformer; keep bus 765 and all other rows unchanged. Original 0.1 bus 766 had no line/converter connection. Before: actual referential test fails. After: 9 tests pass; retained-bus connectivity partition and country mapping unchanged. No network assembly or solver.'],cwd=R,check=True)
assert not git('status','--porcelain');(E/'TOPOLOGY_COMMIT.json').write_text(json.dumps({'head':git('rev-parse','HEAD'),'paths':paths},indent=2))
print(json.dumps(dict(head=git('rev-parse','HEAD'),before=before['status'],after=after['status'],retained_nodes=after['counts']['Bus'],edges=len(after['electricity_edges']),tests=9)))
