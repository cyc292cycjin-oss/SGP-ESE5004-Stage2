"""Test double for scripts_project/s2_solve.py (S4L-3 script tests only; no Gurobi, no network). Accepts the same arguments, writes the
PRE-SOLVE receipt into --output, spawns a grandchild process (sleep) like a real solver thread pool would outlive its parent, sleeps
FAKE_SOLVE_S seconds, then writes the POST-SOLVE receipt (termination_condition optimal). A wall-clock kill of the whole process group must
end both this process and its child before the receipt becomes post-solve."""
import json, os, subprocess, sys, time

args = sys.argv[1:]
out = args[args.index("--output") + 1]
os.makedirs(out, exist_ok=True)
marker = os.environ.get("FAKE_MARKER", "s4l3-fake-solve")
child = subprocess.Popen(["sleep", "600"], env=dict(os.environ, S4L3_FAKE_CHILD=marker))   # grandchild of /usr/bin/time; must die with the group
pre = dict(label="FORMAL_TRIAL_365X24H", solver="gurobi", started_epoch=time.time(), optimize_calls=1, fake=marker, child_pid=child.pid)
json.dump(pre, open(os.path.join(out, "SOLVE_RECEIPT.json"), "w"))
open(os.path.join(out, "gurobi.linopy.log"), "a").write("Barrier iteration 1 primal 1e12 dual 1e11\n")
time.sleep(float(os.environ.get("FAKE_SOLVE_S", "3")))
pre.update(termination_condition="optimal", status="ok", objective=1.0, finished_epoch=time.time())
json.dump(pre, open(os.path.join(out, "SOLVE_RECEIPT.json"), "w"))
open(os.path.join(out, "V5_GATES.json"), "w").write(json.dumps(dict(all_passed_solver_tolerances=True)))
child.terminate()
print(json.dumps(dict(status="ok", objective=1.0)))
