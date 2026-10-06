from pathlib import Path
import json, linopy, numpy as np, gurobipy as gp
out=Path('/mnt/c/Users/20122/Documents/ChatGPT/ASEAN/work/phase4_final_validation/evidence')
r={'artifact_role':'SYNTHETIC_TEST_ONLY','scientific_results_allowed':False}
try:
 with gp.Env() as env:
  with gp.Model(env=env) as m:
   x=m.addVars(2001,lb=1);m.setObjective(x.sum());m.Params.OutputFlag=0;m.optimize()
   r['gurobi']={'size_probe_status':m.Status}
except gp.GurobiError as e:r['gurobi']={'error_code':e.errno,'message':str(e),'usable_for_production':False}
m=linopy.Model();x=m.add_variables(lower=0,name='synthetic_x');m.add_constraints(x>=2,name='synthetic_min');m.add_objective(3*x)
status,condition=m.solve(solver_name='highs',threads=2,time_limit=30,log_fn=str(out/'synthetic_highs.log'))
assert status=='ok' and condition=='optimal' and np.isclose(m.objective.value,6)
r['highs']={'status':status,'condition':condition,'objective':float(m.objective.value),'license':'MIT / no commercial license required','threads':2}
r['validation_run_limits']={'solver_time_limit_seconds':3600,'threads':2,'wall_limit_seconds':7200,'memory_stop_available_bytes':512*1024**2,'note':'Engineering resource limits, not scientific assumptions; no automatic reruns'}
(out/'SOLVER_PREFLIGHT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
