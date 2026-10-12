"""DRY RUN ONLY: pipeline test of C09 merge + unchanged V4 algebra, using C07A main-LP vectors.
Not an acceptance of C07A; no solver is called."""
import sys, json, numpy as np, tempfile, shutil, time
REL='/mnt/user-data/uploads/ResearchWorkspaces/ASEAN/work/c07_v4_reliability_20261013/release'
sys.path.insert(0,REL); sys.path.insert(0,REL+'/helpers')
from adapter import open_problem
from v4_algebra_extracted import complete_kkt
B='/mnt/user-data/uploads/ResearchWorkspaces/ASEAN/outputs/'
MP=B+'c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run/bridge/'
V=B+'c07_daily_diagnostic/c07a_daily122_20261012T162928Z_0d9301f2/cloud_run/canonical_raw_for_V4/vectors/'
meta,a=open_problem(MP+'math_problem',verify=True)
D=np.load(MP+'mapping/D.npy');R=np.load(MP+'mapping/R.npy')
bc=np.load('c09/C09_BLOCK_COLUMNS.npy');br=np.load('c09/C09_BLOCK_ROWS.npy');xb=np.load('c09/C09_BLOCK_PRIMAL.npy')
contract=json.load(open(REL+'/V4_APPROVED.json'))
def run(z,pi,rc,tag):
    d=tempfile.mkdtemp();t=time.time()
    out=complete_kkt(meta,a,z,pi,rc,D,R,d+'/kkt',contract);shutil.rmtree(d)
    keys=['row_fail_count','column_fail_count','stationarity_fail_count','dual_sign_fail_count','row_violation_max','stationarity_normalized_max','relative_gap','absolute_gap','complementarity_l1','stationarity_weighted_l1','independent_kkt_pass','primal_objective','dual_objective_numeric']
    r={k:out[k] for k in keys};r['seconds']=time.time()-t;print(tag,json.dumps(r));return r
z0,p0,r0=[np.load(V+k+'.npy') for k in ('X','Pi','RC')]
base=run(z0,p0,r0,'C07A_AS_IS')
z=z0.copy();pi=p0.copy();rc=r0.copy()
z[bc]=xb;pi[br]=0.;rc[bc]=0.
merged=run(z,pi,rc,'C07A_MAIN+C09_BLOCK')
json.dump({'qualification':'DRY_RUN_PIPELINE_TEST_NOT_ACCEPTANCE','note':'C07A main-LP vectors reused only to exercise merge + unchanged V4 algebra; physics/NetCDF part requires PyPSA and runs on AutoDL','C07A_as_is':base,'C07A_main_plus_C09_block':merged},open('c09/C09_DRYRUN_V4_ALGEBRA.json','w'),indent=1)
