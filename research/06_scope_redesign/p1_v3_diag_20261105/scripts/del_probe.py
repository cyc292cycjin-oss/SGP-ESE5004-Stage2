"""V3 DIAG step 3: group deletion filter (a manual IIS step at constraint-container granularity) on an IN-MEMORY copy of the runner's problem
file - the file, the model code and the network are not changed. Rows of the selected linopy constraint containers (lp_groups.npz of
con_groups.py, aligned with lp/clabels.npy) are removed from the gurobipy model after the read; then the registered profile parameters
(SPLIT_BUILD.json, in order), BarIterLimit 0 and the run protection; one optimize() = presolve only. Only side constraints are removed
(hook rows, never variable bound rows), so the deletion cannot open an unbounded direction through a lost bound.

    GRB_LICENSE_FILE=<path> python del_probe.py --build-dir <dir> --out-dir <new dir> --drop <regex> [--drop <regex> ...] [--grb K=V ...]
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

CHUNK = 1_000_000


def kv(items):
    out = {}
    for it in items or []:
        k, v = it.split("=", 1)
        try:
            out[k] = int(v)
        except ValueError:
            out[k] = float(v)
    return out


def main(a):
    bd = Path(a.build_dir); od = Path(a.out_dir); od.mkdir(parents=True, exist_ok=False)
    build = json.loads((bd / "split" / "SPLIT_BUILD.json").read_text())
    G = np.load(bd / "lp_groups.npz"); names = [str(x) for x in G["names"]]; row_group = G["row_group"]
    cl = np.load(bd / "lp" / "clabels.npy")
    pats = [re.compile(p) for p in a.drop]
    sel = np.array([any(p.search(nm) for p in pats) for nm in names])
    lab_group = np.full(int(cl.max()) + 1, -1, dtype=np.int32); lab_group[cl] = row_group
    params = dict(build["solver_parameters"]); extra = kv(a.grb)
    res = dict(script="work/p1_v3_diag_20261105/scripts/del_probe.py", build_dir=str(bd), problem_sha256_build=build.get("problem_sha256"), drop_patterns=a.drop,
               dropped_containers=[nm for nm, s in zip(names, sel) if s], solver_parameters=params, extra_parameters=dict(BarIterLimit=0, **extra), started_epoch=time.time())
    import gurobipy as gp
    try:
        with gp.Env() as env:
            m = gp.read(build["problem_file"], env=env)
            cons = m.getConstrs(); drop = []
            for i in range(0, len(cons), CHUNK):
                ch = cons[i:i + CHUNK]; nm = m.getAttr("ConstrName", ch)
                lab = np.fromiter((int(s[1:]) for s in nm), dtype=np.int64, count=len(nm))
                g = lab_group[lab]; keep = np.flatnonzero((g >= 0) & sel[np.maximum(g, 0)])
                drop.extend(ch[j] for j in keep)
            del cons
            res["rows_before"] = int(m.NumConstrs); res["rows_dropped"] = len(drop)
            m.remove(drop); m.update(); res["rows_after"] = int(m.NumConstrs)
            if a.fix_zero:   # exact reformulation test: columns fixed at 0 (LB = UB = 0), labels from a JSON list (e.g. bunker_labels.json meter_p_labels)
                path, key = a.fix_zero.rsplit(":", 1); vl = json.loads(Path(path).read_text())[key]
                vs = [m.getVarByName(f"x{int(v)}") for v in vl]; missing = sum(v is None for v in vs); vs = [v for v in vs if v is not None]
                m.setAttr("LB", vs, [0.0] * len(vs)); m.setAttr("UB", vs, [0.0] * len(vs)); m.update()
                res["fixed_zero"] = dict(source=a.fix_zero, columns=len(vs), missing=int(missing))
            for spec in a.row_rhs:   # slack test: one row's right-hand side changed (label=value)
                lab, val = spec.split("="); c = m.getConstrByName(f"c{int(lab)}")
                old = float(c.RHS); c.RHS = float(val); m.update()
                res.setdefault("row_rhs", []).append(dict(row_label=int(lab), sense=str(c.Sense), rhs_old=old, rhs_new=float(val)))
            for k, v in params.items():
                m.setParam(k, v)
            m.setParam("BarIterLimit", 0)
            for k, v in extra.items():
                m.setParam(k, v)
            m.setParam("logfile", str(od / "gurobi.del.log"))
            t0 = time.time()
            try:
                m.optimize(); res["optimize_seconds"] = time.time() - t0
                res["status_code"] = int(m.Status); res["runtime_s"] = float(m.Runtime)
            except gp.GurobiError as e:
                res["gurobi_error"] = dict(errno=int(getattr(e, "errno", -1)), message=str(e)[:300]); res["optimize_seconds"] = time.time() - t0
            m.dispose()
    except Exception as e:
        res["failure"] = dict(error=type(e).__name__, detail=str(e)[:1000])
    log = (od / "gurobi.del.log").read_text(errors="ignore") if (od / "gurobi.del.log").exists() else ""
    if re.search(r"infeasible or unbounded", log, re.I):
        v = "INF_OR_UNBD"
    elif re.search(r"^Model is infeasible", log, re.I | re.M):
        v = "INFEASIBLE"
    elif re.search(r"^Presolved:", log, re.M):
        v = "PRESOLVE_PASSED"
    else:
        v = "UNDECIDED"
    res["verdict"] = v; res["finished_epoch"] = time.time()
    (od / "DEL_PROBE.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res.get(k) for k in ("verdict", "rows_dropped", "status_code", "runtime_s", "gurobi_error", "failure")} | dict(containers=len(res["dropped_containers"]))))
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--build-dir", required=True); p.add_argument("--out-dir", required=True)
    p.add_argument("--drop", action="append", default=[]); p.add_argument("--grb", action="append", default=[])
    p.add_argument("--fix-zero", default=None, help="<json path>:<key> - list of column labels fixed at 0"); p.add_argument("--row-rhs", action="append", default=[], help="<row label>=<value>")
    sys.exit(main(p.parse_args()))
