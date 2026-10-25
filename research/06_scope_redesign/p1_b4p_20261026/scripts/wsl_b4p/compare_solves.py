"""B4P: compare two solve folders of s2_solve.py (single-process vs split-process, or new code vs an earlier run) bit for bit.
  * receipts: status, termination condition, objective (float equality), LP dimensions, solution array SHA256s, gate verdicts;
  * Gurobi log: fingerprint line, barrier iteration count, work units, 'Optimal objective' line;
  * arrays: solution/{X,Pi,RC}.npy, lp/{vlabels,clabels,cost,col_lower,col_upper,row_lower,row_upper,value,index,start}.npy byte equality (SHA256);
  * CSV / text exports byte equality; JSON exports deep equality after dropping volatile keys (paths, timestamps, seconds, authorisation);
  * NetCDF exports (solved network, DUALS_BY_CONSTRAINT.nc): every data variable compared with numpy array_equal (NaN-aware); attrs listed when different.
Usage: python compare_solves.py <A> <B> <out.json> [--label X]   -> one-line verdict; exit 0 when every compared item is equal."""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

VOLATILE = {"authorization", "started_epoch", "finished_epoch", "solve_finished_epoch", "solve_seconds", "build_seconds", "peak_rss_bytes", "split", "post_solve_errors",
            "post_solve_complete", "path", "file", "solved_network", "solve_dir", "written_utc", "seconds", "timestamp", "utc", "out", "network", "costs_table", "output",
            "decision", "optimize_calls", "gurobi_log_stats", "scrubbed_log", "scrubbed_lines", "parameter_source", "stage", "label", "result_label", "s2_solve_label",
            "s2_solve_authorization", "artifact_role", "time", "elapsed_s", "peak_rss_gib", "repo", "source", "lines", "barrier_seconds",
            "existing_cross_border_fom_ledger", "fom_ledger"}   # the last two: diagnostic counts added by the M10R ledger fix (absent in runs made before it)
ARRAYS = ["solution/X.npy", "solution/Pi.npy", "solution/RC.npy", "lp/vlabels.npy", "lp/clabels.npy", "lp/cost.npy", "lp/col_lower.npy", "lp/col_upper.npy", "lp/row_lower.npy",
          "lp/row_upper.npy", "lp/value.npy", "lp/index.npy", "lp/start.npy"]
TEXT = ["COUNTRY_COST_LEDGER.csv", "COUNTRY_COST_LEDGER_USD2020.csv", "COUNTRY_COST_LEDGER_DETAIL.csv", "NODAL_PRICES.csv", "capacity_reduced_costs.csv", "cross_border_flows.csv",
        "nodal_prices_summary.csv", "COMPONENT_COST_BREAKDOWN.csv", "DUALS_INDEX.csv", "costs_active_research.csv"]
JSONS = ["V5_GATES.json", "LEDGER_IDENTITY.json", "EMISSIONS_BY_COUNTRY.json", "CO2_FLOWS.json", "CAPACITY_BY_TECH_COUNTRY.json", "INTERIOR_CHECKS.json", "BUNKER_ACCOUNT.json",
         "COMPONENT_COST_BREAKDOWN_SUMMARY.json", "v5/kkt_summary.json", "EXPORTS.json", "lp/MATH_PROBLEM.json"]
NETCDF = ["DUALS_BY_CONSTRAINT.nc"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def strip(o):
    if isinstance(o, dict):
        if o.get("gate") == "A4_NETCDF_READBACK":   # the solved network FILE hash differs with the metadata text (authorisation, label); its data are compared variable by variable
            o = {k: v for k, v in o.items() if k != "sha256"}
        return {k: strip(v) for k, v in o.items() if k not in VOLATILE}
    if isinstance(o, list):
        return [strip(v) for v in o]
    return o


def walk(a, b, path, diffs):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                diffs.append(f"{path}/{k}: missing in {'B' if k not in b else 'A'}"); continue
            walk(a[k], b[k], f"{path}/{k}", diffs)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(f"{path}: list length {len(a)} vs {len(b)}"); return
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", diffs)
    elif isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)) and not isinstance(b, bool):
        if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
            return
        if a != b:
            diffs.append(f"{path}: {a!r} vs {b!r} (rel {abs(a - b) / max(1.0, abs(a), abs(b)):.3e})")
    elif a != b:
        diffs.append(f"{path}: {str(a)[:60]!r} vs {str(b)[:60]!r}")


def log_facts(d: Path) -> dict:
    p = d / "GUROBI_LOG_SCRUBBED.txt"
    if not p.exists():
        p = d / "gurobi.linopy.log"
    if not p.exists():
        return dict(missing=True)
    t = p.read_text(errors="ignore"); f = {}
    m = re.search(r"Model fingerprint: (0x[0-9a-f]+)", t); f["fingerprint"] = m.group(1) if m else None
    m = re.search(r"Barrier (?:solved model in|performed) (\d+) iterations (?:and|in) ([\d.]+) seconds \(([\d.]+) work units\)", t)
    f["iterations"] = int(m.group(1)) if m else None; f["barrier_seconds"] = float(m.group(2)) if m else None; f["work_units"] = float(m.group(3)) if m else None
    m = re.search(r"^(Optimal objective|Sub-optimal termination - objective)\s+([-\d.e+]+)", t, re.M); f["objective_line"] = m.group(0) if m else None
    m = re.search(r"Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros", t); f["presolved"] = [int(x) for x in m.groups()] if m else None
    m = re.search(r"Factor NZ\s*:\s*([\d.e+]+)", t); f["factor_nz"] = float(m.group(1)) if m else None
    m = re.search(r"Factor Ops\s*:\s*([\d.e+]+)", t); f["factor_ops"] = float(m.group(1)) if m else None
    m = re.search(r"Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros", t); f["model"] = [int(x) for x in m.groups()] if m else None
    return f


def nc_compare(pa: Path, pb: Path) -> dict:
    import xarray as xr
    with xr.open_dataset(pa) as A, xr.open_dataset(pb) as B:
        va, vb = set(A.data_vars), set(B.data_vars); diff = []
        for v in sorted(va & vb):
            x, y = np.asarray(A[v].values), np.asarray(B[v].values)
            if x.shape != y.shape:
                diff.append(f"{v}: shape {x.shape} vs {y.shape}"); continue
            if x.dtype.kind in "fc" and y.dtype.kind in "fc":
                eq = np.array_equal(x, y, equal_nan=True)
            else:
                eq = np.array_equal(x, y)
            if not eq:
                diff.append(v)
        attrs_diff = sorted(k for k in set(A.attrs) | set(B.attrs) if A.attrs.get(k) != B.attrs.get(k))
        return dict(status=("equal" if not diff and va == vb else "DIFFERENT"), variables=len(va & vb), only_A=sorted(va - vb)[:10], only_B=sorted(vb - va)[:10],
                    different_variables=diff[:20], attrs_different=attrs_diff[:20], bytes_equal=(sha(pa) == sha(pb)))


def main():
    A, B, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else ""
    rows = {}; ok = True
    ra, rb = json.loads((A / "SOLVE_RECEIPT.json").read_text()), json.loads((B / "SOLVE_RECEIPT.json").read_text())
    keyf = lambda r: dict(status=r.get("status"), termination_condition=r.get("termination_condition"), objective=r.get("objective"), objective_lp=r.get("objective_lp"),
                          lp={k: (r.get("lp") or {}).get(k) for k in ("num_col", "num_row", "nnz")}, solution=r.get("solution"), gates=r.get("gates"), solver_parameters=r.get("solver_parameters"),
                          scaling=strip(r.get("scaling") or {}), input_sha256=(r.get("input_network") or {}).get("sha256"), snapshots=(r.get("input_network") or {}).get("snapshots"))
    ka, kb = keyf(ra), keyf(rb); d = []; walk(ka, kb, "receipt", d); rows["receipt_key_fields"] = dict(status=("equal" if not d else "DIFFERENT"), differences=d[:20], A=ka, B=kb); ok &= not d
    la, lb = log_facts(A), log_facts(B); d = []; walk(strip(la), strip(lb), "log", d)   # barrier_seconds (timing) is volatile
    rows["gurobi_log"] = dict(status=("equal" if not d else "DIFFERENT"), differences=d[:20], A=la, B=lb); ok &= not d; rows["gurobi_log"] = dict(status=("equal" if not d else "DIFFERENT"), differences=d[:20], A=la, B=lb); ok &= not d
    for f in ARRAYS + TEXT:
        pa, pb = A / f, B / f
        if not pa.exists() and not pb.exists():
            continue
        if not pa.exists() or not pb.exists():
            rows[f] = dict(status="missing_in_" + ("A" if not pa.exists() else "B")); ok = False; continue
        eq = sha(pa) == sha(pb); rows[f] = dict(status=("equal" if eq else "DIFFERENT"), bytes=[pa.stat().st_size, pb.stat().st_size], sha256=[sha(pa)[:16], sha(pb)[:16]])
        if not eq and f.endswith(".npy"):
            x, y = np.load(pa), np.load(pb)
            rows[f].update(shape=[list(x.shape), list(y.shape)], values_equal=(x.shape == y.shape and np.array_equal(x, y, equal_nan=True) if x.dtype.kind == "f" else np.array_equal(x, y)),
                           max_abs_diff=(float(np.nanmax(np.abs(x - y))) if x.shape == y.shape and x.dtype.kind == "f" else None))
        ok &= eq
    for f in JSONS:
        pa, pb = A / f, B / f
        if not pa.exists() and not pb.exists():
            continue
        if not pa.exists() or not pb.exists():
            rows[f] = dict(status="missing_in_" + ("A" if not pa.exists() else "B")); ok = False; continue
        d = []; walk(strip(json.loads(pa.read_text())), strip(json.loads(pb.read_text())), "", d)
        rows[f] = dict(status=("equal" if not d else "DIFFERENT"), bytes_equal=(sha(pa) == sha(pb)), differences=len(d), examples=d[:12]); ok &= not d
    for f in NETCDF + [p.name for p in sorted(A.glob("*_solved.nc"))]:
        pa = A / f; cands = [B / f] + sorted(B.glob("*_solved.nc")); pb = next((c for c in cands if c.exists()), None)
        if not pa.exists() and pb is None:
            continue
        if not pa.exists() or pb is None:
            rows[f] = dict(status="missing_in_" + ("A" if not pa.exists() else "B")); ok = False; continue
        try:
            rows[f] = nc_compare(pa, pb)
        except Exception as e:
            rows[f] = dict(status="unreadable", error=str(e)[:200])
        ok &= rows[f].get("status") == "equal"
    res = dict(label=label, A=str(A), B=str(B), all_equal=bool(ok), items=rows)
    out.write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(json.dumps(dict(label=label, all_equal=bool(ok), items={k: v.get("status") for k, v in rows.items()})))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
