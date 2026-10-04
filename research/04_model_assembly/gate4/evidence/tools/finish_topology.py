from pathlib import Path
import subprocess as sp,json
W=Path(__file__).resolve().parent;E=W/'evidence';R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
def git(*a):return sp.check_output(['git',*a],cwd=R,text=True).strip()
assert git('rev-parse','HEAD')=='fa82156ee74a1fd2a93a88b774c9f9827c2d3f4c'
paths=['data/osm-plus-prebuilt/0.1.1/all_transformers_build_network.csv','scripts_project/research_topology.py','tests/research/test_topology_integrity.py']
assert set(git('diff','--cached','--name-only').splitlines())==set(paths) and not git('diff','--name-only')
proof=json.loads((E/'TOPOLOGY_FIX_PROOF.json').read_text());assert proof['after']['status']=='PASS' and proof['retained_bus_partition_unchanged']
assert git('diff','--cached','--numstat','--',paths[0]).startswith('0\t1\t')
sp.run(['git','-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','commit','-m','fix: repair dangling upstream topology reference','-m','Upstream 138ea07b deliberately removed bus 766 in 0.1.1 but retained transf_524_0. Delete that sole obsolete row; retain 765 and every other input byte. Failing actual referential test recorded before repair; 9 tests pass after. Retained-node connectivity partition unchanged. Three existing cross-border transformers remain explicitly flagged for ownership review, not silently edited. No assembly or solve.'],cwd=R,check=True)
assert not git('status','--porcelain');(E/'TOPOLOGY_COMMIT.json').write_text(json.dumps({'head':git('rev-parse','HEAD'),'paths':paths},indent=2));print(git('rev-parse','HEAD'))
