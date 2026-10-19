"""Test double of s2_solve.py for the speed_probe.sh test (no Gurobi): writes a post-solve receipt and a Gurobi-style log with a 'Barrier solved model'
line so the probe's parser and ratio arithmetic can be checked locally. FAKE_BARRIER='iterations seconds work_units' sets the line."""
import json, os, sys, time

args = sys.argv[1:]
out = args[args.index("--output") + 1]
os.makedirs(out, exist_ok=True)
it, sec, wu = (os.environ.get("FAKE_BARRIER", "124 428.0 356.67")).split()
open(os.path.join(out, "gurobi.linopy.log"), "w").write("Set parameter Threads to value 8\nBarrier solved model in %s iterations and %s seconds (%s work units)\nOptimal objective 6.45375574e+11\n" % (it, sec, wu))
time.sleep(1)
json.dump(dict(label="SMOKE_TEST_ONLY", termination_condition="optimal", status="ok", objective=648262301211.7622, finished_epoch=time.time(), solve_seconds=float(sec) + 20), open(os.path.join(out, "SOLVE_RECEIPT.json"), "w"))
print(json.dumps(dict(status="ok")))
