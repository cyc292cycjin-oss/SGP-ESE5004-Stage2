"""V3 DIAG (instruction V3_DIAG_INSTRUCTION.md v1, decision 194): window builds and IIS through the runner's own process-1 code.

The model is built by scripts_project/s2_solve.py main() itself (the runner's process 1, run_batch4.sh solve_run: s2_solve.py --split-stage build),
unchanged. The only addition is the snapshot WINDOW: right after PyPSA reads the package network, its snapshots are cut to [start, start+len);
main() then applies its own truncation (--truncate len -> n.snapshots[:len] = the whole window) and its own set_representative_weights()
(objective / generators / stores weightings = 8760 / len, annual caps unscaled) - exactly the TRUNCATE path of the runner. With start = 0 the
window is the runner's TRUNCATE itself (control: problem.lp byte-identical to s2_solve.py --truncate len, checked by SHA256).

    --mode build   process 1 only (no licence, no solver call): split/problem.lp, lp/vlabels.npy, lp/clabels.npy, SPLIT_BUILD.json, SOLVE_RECEIPT.json
    --mode iis     process 1 in this process, then ONE Gurobi environment: the problem file read with gurobipy, the profile parameters set as
                   b4_split_solve.py does (profile in order, then the extra --grb KEY=VALUE, then the log file), optimize() (presolve; BarIterLimit 0),
                   and - when the status is INFEASIBLE (or INF_OR_UNBD with --iis-on-infunbd) - linopy Model.compute_infeasibilities() /
                   constraints.print_labels() (= Model.print_infeasibilities without a second computeIIS) on that gurobipy model, with the IIS
                   constraints and bounds mapped to linopy names / coordinates and PyPSA components, buses, countries, snapshots.

    python diag_build.py --mode build --window-start S --window-len L -- <s2_solve.py arguments without --truncate / --split-stage>
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import sys
import time
from pathlib import Path

REPO = Path("/home/jin/wt_v3_fix")
sys.path.insert(0, str(REPO / "scripts_project"))

import numpy as np  # noqa: E402
import pypsa  # noqa: E402

STATE: dict = {}
_Network = pypsa.Network


class WindowNetwork(_Network):
    """pypsa.Network whose snapshots are cut to the diagnosis window right after the package network is read (target path only, once)."""

    def __init__(self, import_name="", *args, **kw):
        super().__init__(import_name, *args, **kw)
        if import_name and STATE.get("target") and str(import_name) == STATE["target"] and not STATE.get("applied"):
            full = self.snapshots
            s, l = STATE["start"], STATE["len"]
            if s < 0 or s + l > len(full):
                raise ValueError(f"window [{s}, {s + l}) outside the {len(full)} snapshots")
            w_before = self.snapshot_weightings.iloc[s:s + l].copy()
            self.set_snapshots(full[s:s + l])
            STATE.update(applied=True, full_snapshots=int(len(full)), first=str(full[s]), last=str(full[s + l - 1]),
                         weights_before_main=dict(objective=float(w_before["objective"].sum()), generators=float(w_before["generators"].sum()), stores=float(w_before["stores"].sum())))
            STATE["n"] = self


pypsa.Network = WindowNetwork
import s2_solve  # noqa: E402

_write_problem_file = s2_solve.write_problem_file


def _capture_write_problem_file(m, fn):
    STATE["m"] = m
    return _write_problem_file(m, fn)


s2_solve.write_problem_file = _capture_write_problem_file

LICENCE_MARKERS = ("license", "licence", "licenseid", "wls", "registered to", "academic", "secret", "accessid", "token")


def scrub(src: Path, dst: Path) -> int:
    if not src.exists():
        return 0
    keep = [ln for ln in src.read_text(errors="ignore").splitlines() if not any(mk in ln.lower() for mk in LICENCE_MARKERS)]
    dst.write_text("\n".join(keep) + "\n")
    return len(keep)


def parse_kv(items):
    out = {}
    for it in items or []:
        k, v = it.split("=", 1)
        try:
            out[k] = int(v)
        except ValueError:
            out[k] = float(v)
    return out


def component_info(n, comp: str, name: str) -> dict:
    """bus(es), carrier, country of one PyPSA component (read only)."""
    try:
        df = n.df(comp)
    except Exception:
        return {}
    if name not in df.index:
        return {}
    z = df.loc[name]
    info = {}
    for k in ("bus", "bus0", "bus1", "bus2", "bus3", "bus4", "carrier", "country"):
        if k in df.columns and str(z.get(k, "")) not in ("", "nan"):
            info[k] = str(z[k])
    if "country" not in info:
        for k in ("bus", "bus0", "bus1"):
            b = info.get(k)
            if b and b in n.buses.index and "country" in n.buses.columns:
                info["country"] = str(n.buses.at[b, "country"])
                break
    if comp == "Bus" and "country" in df.columns:
        info["country"] = str(z.get("country", ""))
    return info


def describe_coords(n, coords: dict) -> dict:
    out = {}
    for k, v in coords.items():
        key = str(k)
        val = str(v)
        out[key] = val
        base = key.split("-")[0]
        if base in ("Generator", "Link", "Store", "StorageUnit", "Line", "Bus", "Load", "Transformer"):
            ci = component_info(n, base, val)
            if ci:
                out[key + "@"] = ci
    return out


def map_iis(n, m, labels: list[int], ilp: Path) -> dict:
    cons = []
    for lab in labels:
        name, coords = m.constraints.get_label_position(int(lab))
        row = dict(label=int(lab), constraint=str(name), coords=describe_coords(n, coords or {}))
        try:
            c = m.constraints[name]
            sel = c.data.sel(coords) if coords else c.data
            row["sign"] = str(np.asarray(sel["sign"]).item())
            row["rhs"] = float(np.asarray(sel["rhs"]).item())
            vs = np.ravel(np.asarray(sel["vars"])); cf = np.ravel(np.asarray(sel["coeffs"]))
            terms = []
            for v, a in zip(vs, cf):
                if int(v) < 0:
                    continue
                vn, vc = m.variables.get_label_position(int(v))
                terms.append(dict(var_label=int(v), coeff=float(a), variable=str(vn), coords=describe_coords(n, vc or {})))
            row["terms"] = terms
        except Exception as e:  # recorded, the label mapping above stays
            row["term_error"] = f"{type(e).__name__}: {e}"[:300]
        cons.append(row)
    bounds = []
    if ilp.exists():
        txt = ilp.read_text(errors="ignore")
        sec = txt.split("Bounds", 1)[1] if "Bounds" in txt else ""
        for ln in sec.splitlines():
            ln = ln.strip()
            if not ln or ln.lower().startswith("end"):
                continue
            mm = re.findall(r"\bx(\d+)\b", ln)
            for v in mm:
                vn, vc = m.variables.get_label_position(int(v))
                bounds.append(dict(line=ln[:200], var_label=int(v), variable=str(vn), coords=describe_coords(n, vc or {})))
    return dict(constraints=cons, bounds=bounds)


def main() -> int:
    argv = sys.argv[1:]
    if "--" not in argv:
        print("usage: diag_build.py --mode build|iis --window-start S --window-len L [--grb K=V ...] -- <s2_solve.py args>")
        return 2
    i = argv.index("--")
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["build", "iis"], required=True)
    p.add_argument("--window-start", type=int, required=True)
    p.add_argument("--window-len", type=int, required=True)
    p.add_argument("--grb", action="append", default=[], help="extra Gurobi parameter after the profile (iis mode)")
    p.add_argument("--iis-time-limit", type=float, default=1800.0)
    p.add_argument("--iis-on-infunbd", action="store_true")
    p.add_argument("--native-weights", action="store_true",
                   help="diagnostic variant: the window WITHOUT --truncate, i.e. s2_solve.main's full-year path (weights as stored = 3 h, no set_representative_weights)")
    a = p.parse_args(argv[:i])
    sargs = argv[i + 1:]
    if any(x in sargs for x in ("--truncate", "--split-stage")):
        print("REFUSED: --truncate / --split-stage are set by this wrapper"); return 2
    sargs = sargs + ([] if a.native_weights else ["--truncate", str(a.window_len)]) + ["--split-stage", "build"]
    # the argument parser of s2_solve.py __main__ (lines 559-565 at 7d22dda1; same names and defaults - parsing only, no model code)
    q = argparse.ArgumentParser()
    q.add_argument("--repo", type=Path, default=s2_solve.HERE.parent); q.add_argument("--network", type=Path, required=True); q.add_argument("--scenario", required=True); q.add_argument("--output", type=Path, required=True)
    q.add_argument("--solver-profile", default=None); q.add_argument("--scaling", choices=["on", "off"], default=None)
    q.add_argument("--kvl-norm", choices=["on", "off"], default=None)
    q.add_argument("--costs-table", type=Path, default=None)
    q.add_argument("--solver", choices=["highs", "gurobi"], default="highs"); q.add_argument("--truncate", type=int, default=0); q.add_argument("--label", default="SMOKE_TEST_ONLY"); q.add_argument("--authorization", required=True); q.add_argument("--time-limit", type=float, default=3600.0); q.add_argument("--highs-ipm", action="store_true")
    q.add_argument("--stop-before-solve", action="store_true")
    q.add_argument("--split-stage", choices=["build", "assign"], default=None)
    sa = q.parse_args(sargs)
    out = Path(sa.output); out.mkdir(parents=True, exist_ok=True)
    STATE.update(target=str(sa.network), start=a.window_start, len=a.window_len)
    t0 = time.time()
    rc = s2_solve.main(sa)
    win = dict(script="work/p1_v3_fix_20261105/scripts/win/diag_build.py (copy of the V3 DIAG entry)", mode=a.mode, window_start=a.window_start, window_len=a.window_len,
               weighting=("native (full-year path: weights as stored, no set_representative_weights)" if a.native_weights else "runner TRUNCATE (set_representative_weights, 8760/len)"),
               window_end_excl=a.window_start + a.window_len, first_snapshot=STATE.get("first"), last_snapshot=STATE.get("last"),
               full_snapshots=STATE.get("full_snapshots"), window_applied=bool(STATE.get("applied")), weights_before_main=STATE.get("weights_before_main"),
               s2_solve_args=sargs, s2_solve_rc=rc, build_wall_s=round(time.time() - t0, 1))
    n = STATE.get("n")
    if n is not None:
        w = n.snapshot_weightings
        win["weights_after_main"] = {c: dict(per_snapshot_min=float(w[c].min()), per_snapshot_max=float(w[c].max()), sum=float(w[c].sum())) for c in w.columns}
        win["representative_weights_meta"] = n.meta.get("representative_weights")
    (out / "DIAG_WINDOW.json").write_text(json.dumps(win, indent=1, default=str) + "\n")
    print(json.dumps(dict(window=[a.window_start, a.window_start + a.window_len], first=STATE.get("first"), last=STATE.get("last"), rc=rc)))
    if rc != 0 or not win["window_applied"]:
        return rc or 3
    if a.mode == "build":
        return 0
    # ---- iis mode: one Gurobi environment in this process
    m = STATE["m"]
    build = json.loads((out / "split" / "SPLIT_BUILD.json").read_text())
    params = dict(build["solver_parameters"]); extra = parse_kv(a.grb)
    res = dict(script=win["script"], mode="iis", window=[a.window_start, a.window_start + a.window_len], first=STATE.get("first"), last=STATE.get("last"),
               solver_parameters=params, extra_parameters=extra, iis_time_limit_s=a.iis_time_limit, started_epoch=time.time())
    import gurobipy as gp
    names = {1: "LOADED", 2: "OPTIMAL", 3: "INFEASIBLE", 4: "INF_OR_UNBD", 5: "UNBOUNDED", 7: "ITERATION_LIMIT", 9: "TIME_LIMIT", 12: "NUMERIC", 13: "SUBOPTIMAL"}
    log = out / "gurobi.iis.log"
    with gp.Env() as env:
        gm = gp.read(str(build["problem_file"]), env=env)
        for k, v in params.items():
            gm.setParam(k, v)
        for k, v in extra.items():
            gm.setParam(k, v)
        gm.setParam("logfile", str(log))
        t1 = time.time(); gm.optimize(); res["optimize_seconds"] = time.time() - t1
        code = int(gm.Status); res.update(status_code=code, status=names.get(code, str(code)), runtime_s=float(gm.Runtime), bar_iter_count=int(gm.BarIterCount),
                                          max_mem_used_gb=float(gm.MaxMemUsed), num_vars=int(gm.NumVars), num_constrs=int(gm.NumConstrs))
        if code == 3 or (code == 4 and a.iis_on_infunbd):
            gm.setParam("TimeLimit", float(a.iis_time_limit))
            m.solver_model = gm
            t2 = time.time(); labels = m.compute_infeasibilities(); res["iis_seconds"] = time.time() - t2
            res["iis_minimal"] = bool(getattr(gm, "IISMinimal", 0))
            ilp = out / "iis.ilp"; gm.write(str(ilp))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                m.constraints.print_labels(labels)   # = Model.print_infeasibilities() body, without a second computeIIS
            (out / "IIS_PRINT.txt").write_text(buf.getvalue())
            res["iis_constraint_labels"] = [int(x) for x in labels]
            res["iis_mapping"] = map_iis(n, m, labels, ilp)
            m.solver_model = None
        gm.dispose()
    res["finished_epoch"] = time.time()
    scrub(log, out / "gurobi_iis_log_scrubbed.txt")   # the raw log stays in the run folder (as the runner's gurobi.linopy.log); only the scrubbed copy goes to evidence
    (out / "DIAG_IIS.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(json.dumps({k: res.get(k) for k in ("status", "runtime_s", "iis_seconds", "iis_minimal", "max_mem_used_gb")} | dict(iis_constraints=len(res.get("iis_constraint_labels", [])))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
