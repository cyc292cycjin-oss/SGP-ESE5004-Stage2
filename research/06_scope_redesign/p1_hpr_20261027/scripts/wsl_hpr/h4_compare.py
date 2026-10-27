"""HPR H4: compare the local drill (runs/smoke56/F1, F2 of the smoke job bodies: split-process solves of the v2 2920x3h networks truncated to 56) with the
DFX F5.5 smoke (results_project/dfx_v3/smoke_v2/integrated, disconnected: single-process solves of the same networks at commit 896828fd) BITWISE:
objective (receipt, with the constant term), Gurobi objective and barrier iterations (log), termination, solution arrays X / Pi / RC, the LP arrays,
the exports (ledgers, prices, flows, allocation, Owen) and the GATES_V6 labels; plus the chain exit codes and the batch-level results. Writes
H4_DRILL.json (the package builder requires it) and prints the table. Read only.
    python h4_compare.py <runs dir of the drill (…/runs/smoke56)> <dfx smoke dir> <out json> <code commit>
"""
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

runs, dfx, out, commit = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
PAIRS = {"F1": "integrated", "F2": "disconnected"}
EXPECTED_ITER = {"F1": 113, "F2": 139}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def log_stats(p: Path):
    t = p.read_text(errors="ignore") if p.exists() else ""
    it = re.search(r"Barrier solved model in (\d+) iterations and ([\d.]+) seconds \(([\d.]+) work units\)", t)
    ob = re.search(r"Optimal objective\s+([-+\d.e]+)", t); fp = re.search(r"Model fingerprint: (0x[0-9a-f]+)", t)
    return dict(iterations=int(it.group(1)) if it else None, seconds=float(it.group(2)) if it else None, work=float(it.group(3)) if it else None, gurobi_objective=ob.group(1) if ob else None, fingerprint=fp.group(1) if fp else None)


def arr_equal(a: Path, b: Path):
    if not a.exists() or not b.exists():
        return "missing"
    x, y = np.load(a), np.load(b)
    return "equal" if x.shape == y.shape and np.array_equal(x, y, equal_nan=True) else "DIFFERENT"


def text_equal(a: Path, b: Path):
    if not a.exists() or not b.exists():
        return "missing"
    return "equal" if a.read_bytes() == b.read_bytes() else "DIFFERENT"


st = (runs / "STATUS.txt").read_text() if (runs / "STATUS.txt").exists() else ""
res = dict(script="scripts/wsl_hpr/h4_compare.py", code_commit=commit, drill_runs=str(runs), dfx_smoke=str(dfx), written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), runs={}, batch={})
all_opt = True; bitwise = True
for rid, sc in PAIRS.items():
    d, e = runs / rid, dfx / sc
    rec = json.loads((d / "SOLVE_RECEIPT.json").read_text()) if (d / "SOLVE_RECEIPT.json").exists() else {}
    erec = json.loads((e / "SOLVE_RECEIPT.json").read_text()) if (e / "SOLVE_RECEIPT.json").exists() else {}
    sp = json.loads((d / "split" / "SPLIT_SOLVE.json").read_text()) if (d / "split" / "SPLIT_SOLVE.json").exists() else {}
    acc = json.loads((d / "V6_ACCEPTANCE.json").read_text()) if (d / "V6_ACCEPTANCE.json").exists() else {}
    eacc = json.loads((e / "V6_ACCEPTANCE.json").read_text()) if (e / "V6_ACCEPTANCE.json").exists() else {}
    ls, els = log_stats(d / "gurobi.linopy.log"), log_stats(e / "GUROBI_LOG_SCRUBBED.txt")
    items = dict(objective_receipt=("equal" if rec.get("objective") == erec.get("objective") else "DIFFERENT"),
                 termination=("equal" if rec.get("termination_condition") == erec.get("termination_condition") == "optimal" else "DIFFERENT"),
                 iterations=("equal" if ls["iterations"] == els["iterations"] == EXPECTED_ITER[rid] and sp.get("bar_iter_count") == EXPECTED_ITER[rid] else "DIFFERENT"),
                 gurobi_objective_log=("equal" if ls["gurobi_objective"] == els["gurobi_objective"] else "DIFFERENT"),
                 fingerprint=("equal" if ls["fingerprint"] == els["fingerprint"] else "DIFFERENT"),
                 solver_parameters=("equal" if rec.get("solver_parameters") == erec.get("solver_parameters") else "DIFFERENT"),
                 input_sha256=("equal" if (rec.get("input_network") or {}).get("sha256") == (erec.get("input_network") or {}).get("sha256") else "DIFFERENT"),
                 v6_label=("equal" if acc.get("label") == eacc.get("label") == "ACCEPTED_LAYER2" else "DIFFERENT"))
    for k in ("X", "Pi", "RC"):
        items[f"solution/{k}.npy"] = arr_equal(d / "solution" / f"{k}.npy", e / "solution" / f"{k}.npy")
    for k in ("vlabels", "clabels", "cost", "col_lower", "col_upper", "row_lower", "row_upper", "value", "index", "start"):
        items[f"lp/{k}.npy"] = arr_equal(d / "lp" / f"{k}.npy", e / "lp" / f"{k}.npy")
    for f in ("COUNTRY_COST_LEDGER.csv", "COUNTRY_COST_LEDGER_USD2020.csv", "COUNTRY_COST_LEDGER_DETAIL.csv", "NODAL_PRICES.csv", "cross_border_flows.csv", "capacity_reduced_costs.csv", "nodal_prices_summary.csv",
              "COMPONENT_COST_BREAKDOWN.csv", "DUALS_INDEX.csv", "ALLOCATION.csv", "ALLOCATION_LINES.csv", "m12_owen/OWEN.json", "LEDGER_IDENTITY.json", "EMISSIONS_BY_COUNTRY.json", "CO2_FLOWS.json",
              "CAPACITY_BY_TECH_COUNTRY.json", "BUNKER_ACCOUNT.json", "INTERIOR_CHECKS.json", "COMPONENT_COST_BREAKDOWN_SUMMARY.json", "lp/MATH_PROBLEM.json", "DUALS_BY_CONSTRAINT.nc"):
        items[f] = text_equal(d / f, e / f)
    items["solved_network.nc"] = text_equal(next(iter(d.glob("*_solved.nc")), d / "none"), next(iter(e.glob("*_solved.nc")), e / "none"))
    opt = rec.get("termination_condition") == "optimal"; all_opt = all_opt and opt
    core = ("objective_receipt", "termination", "iterations", "gurobi_objective_log", "solution/X.npy", "solution/Pi.npy", "solution/RC.npy", "v6_label")
    bw = all(items[k] == "equal" for k in core); bitwise = bitwise and bw
    res["runs"][rid] = dict(dfx_dir=sc, optimal=opt, objective=rec.get("objective"), dfx_objective=erec.get("objective"), split=dict((k, sp.get(k)) for k in ("gurobi_status_name", "termination_condition", "bar_iter_count", "runtime_s", "work_units", "max_mem_used_gb", "fingerprint", "solve_seconds")),
                            log=ls, dfx_log=els, label=acc.get("label"), dfx_label=eacc.get("label"), items=items, bitwise_core_equal=bw,
                            different=[k for k, v in items.items() if v != "equal"], post_exits={k.split(":")[0]: k.split(":")[1] for k in [l for l in st.splitlines() if l.startswith((f"VIOLATIONS_{rid}:", f"C1_{rid}:", f"M12_{rid}:", f"M12_OWEN_{rid}:", f"ASSIGN_{rid}:", f"BUILD_{rid}:", f"GUROBI_{rid}:"))]})
summ = json.loads((runs / "BATCH4_SUMMARY.json").read_text()) if (runs / "BATCH4_SUMMARY.json").exists() else {}
res["batch"] = dict(b6_bn=(summ.get("B6") or {}).get("b6_bn"), dfx_smoke_b6_bn=json.loads((dfx / "SMOKE_SUMMARY.json").read_text()).get("b6_56_snapshots_bn") if (dfx / "SMOKE_SUMMARY.json").exists() else None,
                    labels=(summ.get("B6") or {}).get("labels"), unusable=summ.get("unusable"), stop_safe=summ.get("stop_safe"), stop=summ.get("stop_not_accepted"),
                    reference_comparison_present=bool(summ.get("reference_comparison")), postproc_errors=summ.get("postproc_errors"),
                    packs=sorted(p.name for p in runs.glob("results_*.tar.gz")), done=("DONE:" in st), done_only=st.count("DONE_ONLY:"), status_lines=len(st.splitlines()))
res["b6_equal_to_dfx_smoke"] = res["batch"]["b6_bn"] == res["batch"]["dfx_smoke_b6_bn"]
res["all_optimal"] = all_opt; res["bitwise_equal_to_dfx_smoke"] = bitwise and res["b6_equal_to_dfx_smoke"]
res["chain_exit_zero"] = (not summ.get("postproc_errors")) and res["batch"]["done"] and res["batch"]["done_only"] == 2 and not summ.get("stop_safe") and not summ.get("stop_not_accepted")
pbs = (runs / "PBS_JOBS.txt").read_text() if (runs / "PBS_JOBS.txt").exists() else ""
res["job_exits"] = re.findall(r"JOB_END:(\S+?):(\S+?):(\S+?):exit=(\d+)", pbs); res["all_job_exits_zero"] = bool(res["job_exits"]) and all(x[3] == "0" for x in res["job_exits"])
res["smoke_status"] = (runs / "SMOKE_STATUS.txt").read_text() if (runs / "SMOKE_STATUS.txt").exists() else None
out.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str) + "\n")
for rid, r in res["runs"].items():
    print(rid, "optimal", r["optimal"], "| objective", r["objective"], "dfx", r["dfx_objective"], "| iterations", r["log"]["iterations"], "dfx", r["dfx_log"]["iterations"], "| label", r["label"], "| bitwise core", r["bitwise_core_equal"], "| different:", r["different"])
print("B6", res["batch"]["b6_bn"], "dfx", res["batch"]["dfx_smoke_b6_bn"], "| all_optimal", res["all_optimal"], "| bitwise", res["bitwise_equal_to_dfx_smoke"], "| chain_exit_zero", res["chain_exit_zero"], "| job exits", res["job_exits"])
