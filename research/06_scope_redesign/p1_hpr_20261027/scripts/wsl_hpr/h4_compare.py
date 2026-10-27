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
    if not a.exists() and not b.exists():
        return "absent_both"   # e.g. ALLOCATION_LINES.csv of the disconnected scenario (no cross-border lines)
    if not a.exists() or not b.exists():
        return "missing_one"
    return "equal" if a.read_bytes() == b.read_bytes() else "DIFFERENT"


def flat(d, p=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flat(v, p + "/" + str(k)))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.update(flat(v, p + f"[{i}]"))
    else:
        out[p] = d
    return out


def json_numbers_equal(a: Path, b: Path):
    """JSON files: every numeric leaf equal (NaN == NaN); non-numeric differences are listed (paths, tags, timestamps) and do not count."""
    if not a.exists() or not b.exists():
        return "missing_one", []
    fa, fb = flat(json.loads(a.read_text())), flat(json.loads(b.read_text()))
    diff = sorted(k for k in set(fa) | set(fb) if fa.get(k) != fb.get(k) and not (isinstance(fa.get(k), float) and isinstance(fb.get(k), float) and np.isnan(fa[k]) and np.isnan(fb[k])))
    num = [k for k in diff if isinstance(fa.get(k), (int, float)) and isinstance(fb.get(k), (int, float)) and not isinstance(fa.get(k), bool)]
    if not diff:
        return "equal", []
    return ("DIFFERENT" if num else "equal_numbers_paths_differ"), diff[:20]


def netcdf_equal(a: Path, b: Path):
    """Solved networks: every data variable equal (NaN == NaN; object arrays by value); the meta attribute may differ in paths / label / authorisation."""
    if not a.exists() or not b.exists():
        return "missing_one", []
    import xarray as xr
    with xr.open_dataset(a) as x, xr.open_dataset(b) as y:
        if set(x.data_vars) != set(y.data_vars) or set(x.coords) != set(y.coords):
            return "DIFFERENT", ["variable sets differ"]
        bad = []
        for v in list(x.data_vars) + list(x.coords):
            p, q = x[v].values, y[v].values
            if p.shape != q.shape or p.dtype != q.dtype:
                bad.append(v); continue
            if p.dtype.kind in "fc":
                ok = np.array_equal(p, q, equal_nan=True)
            elif p.dtype.kind == "O":
                ok = all((u == w) or (isinstance(u, float) and isinstance(w, float) and np.isnan(u) and np.isnan(w)) for u, w in zip(p.ravel().tolist(), q.ravel().tolist()))
            else:
                ok = np.array_equal(p, q)
            if not ok:
                bad.append(v)
        if bad:
            return "DIFFERENT", bad[:20]
        attrs = sorted(k for k in set(x.attrs) | set(y.attrs) if x.attrs.get(k) != y.attrs.get(k))
        meta_keys = []
        if "meta" in attrs:
            try:
                ma, mb = flat(json.loads(x.attrs["meta"])), flat(json.loads(y.attrs["meta"]))
                meta_keys = sorted(k for k in set(ma) | set(mb) if ma.get(k) != mb.get(k))[:20]
            except Exception:
                meta_keys = ["meta (unparsed)"]
        return ("equal" if not attrs else "equal_data_meta_differs"), (meta_keys or attrs)


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
              "COMPONENT_COST_BREAKDOWN.csv", "DUALS_INDEX.csv", "ALLOCATION.csv", "ALLOCATION_LINES.csv", "LEDGER_IDENTITY.json", "EMISSIONS_BY_COUNTRY.json", "CO2_FLOWS.json",
              "CAPACITY_BY_TECH_COUNTRY.json", "BUNKER_ACCOUNT.json", "INTERIOR_CHECKS.json", "COMPONENT_COST_BREAKDOWN_SUMMARY.json", "lp/MATH_PROBLEM.json", "DUALS_BY_CONSTRAINT.nc"):
        items[f] = text_equal(d / f, e / f)
    notes = {}
    items["m12_owen/OWEN.json"], notes["m12_owen/OWEN.json"] = json_numbers_equal(d / "m12_owen" / "OWEN.json", e / "m12_owen" / "OWEN.json")   # paths / tag differ by construction (BATCH4_<rid> vs SMOKE_<scenario>, run folders)
    items["solved_network.nc"], notes["solved_network.nc"] = netcdf_equal(next(iter(d.glob("*_solved.nc")), d / "none"), next(iter(e.glob("*_solved.nc")), e / "none"))   # meta carries the output path / label / authorisation
    opt = rec.get("termination_condition") == "optimal"; all_opt = all_opt and opt
    core = ("objective_receipt", "termination", "iterations", "gurobi_objective_log", "solution/X.npy", "solution/Pi.npy", "solution/RC.npy", "v6_label")
    bw = all(items[k] == "equal" for k in core); bitwise = bitwise and bw
    exports_ok = all(v in ("equal", "absent_both", "equal_numbers_paths_differ", "equal_data_meta_differs") for v in items.values()); bitwise = bitwise and exports_ok
    res["runs"][rid] = dict(dfx_dir=sc, optimal=opt, objective=rec.get("objective"), dfx_objective=erec.get("objective"), split=dict((k, sp.get(k)) for k in ("gurobi_status_name", "termination_condition", "bar_iter_count", "runtime_s", "work_units", "max_mem_used_gb", "fingerprint", "solve_seconds")),
                            log=ls, dfx_log=els, label=acc.get("label"), dfx_label=eacc.get("label"), items=items, notes=notes, bitwise_core_equal=bw, exports_equal_or_metadata_only=exports_ok,
                            different=[k for k, v in items.items() if v not in ("equal", "absent_both")], post_exits={k.split(":")[0]: k.split(":")[1] for k in [l for l in st.splitlines() if l.startswith((f"VIOLATIONS_{rid}:", f"C1_{rid}:", f"M12_{rid}:", f"M12_OWEN_{rid}:", f"ASSIGN_{rid}:", f"BUILD_{rid}:", f"GUROBI_{rid}:"))]})
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
    print(rid, "optimal", r["optimal"], "| objective", r["objective"], "dfx", r["dfx_objective"], "| iterations", r["log"]["iterations"], "dfx", r["dfx_log"]["iterations"], "| label", r["label"], "| bitwise core", r["bitwise_core_equal"],
          "| exports equal or metadata-only", r["exports_equal_or_metadata_only"], "| non-equal items:", {k: r["items"][k] for k in r["different"]}, "| notes:", {k: v[:8] for k, v in r["notes"].items() if v})
print("B6", res["batch"]["b6_bn"], "dfx", res["batch"]["dfx_smoke_b6_bn"], "| all_optimal", res["all_optimal"], "| bitwise", res["bitwise_equal_to_dfx_smoke"], "| chain_exit_zero", res["chain_exit_zero"], "| job exits", res["job_exits"])
