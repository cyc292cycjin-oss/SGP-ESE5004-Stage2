"""Test double for scripts_project/s2_solve.py (S4O-4 script tests only; no Gurobi, no network). The S4M double (pre-solve receipt, a grandchild
process that must die with the process group, FAKE_SOLVE_S seconds, post-solve receipt, the S4M supplement 01 export files) plus, for the S4O
pipeline: the termination condition from FAKE_COND_<run> (run = basename of --output; default optimal), the solver profile recorded in the receipt,
and a COUNTRY_COST_LEDGER.csv (disconnected = integrated + 1 bn EUR per country) so that the batch reference of the C1 step can be built. No
solution arrays are written: the real C1 module reports such a run as not computable."""
import json, os, subprocess, sys, time

args = sys.argv[1:]
out = args[args.index("--output") + 1]; run = os.path.basename(out.rstrip("/"))
os.makedirs(out, exist_ok=True)
marker = os.environ.get("FAKE_MARKER", "s4l3-fake-solve")
child = subprocess.Popen(["sleep", "600"], env=dict(os.environ, S4L3_FAKE_CHILD=marker))   # grandchild of /usr/bin/time; must die with the group
pre = dict(label="FORMAL_TRIAL_365X24H", solver="gurobi", started_epoch=time.time(), optimize_calls=1, fake=marker, child_pid=child.pid,
           solver_profile=(args[args.index("--solver-profile") + 1] if "--solver-profile" in args else None))
json.dump(pre, open(os.path.join(out, "SOLVE_RECEIPT.json"), "w"))
open(os.path.join(out, "gurobi.linopy.log"), "a").write("Barrier iteration 1 primal 1e12 dual 1e11\n")
time.sleep(float(os.environ.get("FAKE_SOLVE_S", "3")))
cond = os.environ.get("FAKE_COND_" + run, "optimal")
pre.update(termination_condition=cond, status="ok", objective=1.0, finished_epoch=time.time())
json.dump(pre, open(os.path.join(out, "SOLVE_RECEIPT.json"), "w"))
open(os.path.join(out, "V5_GATES.json"), "w").write(json.dumps(dict(all_passed_solver_tolerances=True)))
for f in ("DUALS_BY_CONSTRAINT.nc", "DUALS_INDEX.csv", "COMPONENT_COST_BREAKDOWN.csv", "COMPONENT_COST_BREAKDOWN_SUMMARY.json", "costs_active_research.csv"):   # S4M supplement 01 exports
    open(os.path.join(out, f), "w").write("dummy " + f + "\n")
open(os.path.join(out, "EXPORTS.json"), "w").write(json.dumps({"DUALS_INDEX.csv": dict(bytes=1, sha256="dummy")}))
ents = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN", "ASEAN_BUNKER", "ASEAN_POOL"]
off = 1e9 if run.startswith("disconnected") else 0.0
with open(os.path.join(out, "COUNTRY_COST_LEDGER.csv"), "w") as f:
    f.write("entity,capex_new,total\n" + "".join(f"{e},0.0,{1e10 + off}\n" for e in ents))
open(os.path.join(out, "COSTS_TABLE_ARG.txt"), "w").write(args[args.index("--costs-table") + 1] if "--costs-table" in args else "")
child.terminate()
print(json.dumps(dict(status="ok", objective=1.0)))
