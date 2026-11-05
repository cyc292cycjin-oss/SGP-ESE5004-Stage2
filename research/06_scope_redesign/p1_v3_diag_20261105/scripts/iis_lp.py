"""V3 DIAG step 3: IIS on the runner's problem file in a gurobipy-only process (memory: the linopy model of a month window needs 8.5 GiB and
cannot sit beside the Gurobi model on this machine). The IIS is computed exactly as linopy 0.5.5 Model.compute_infeasibilities() does it
(solver_model.computeIIS(), then the .ilp file written by Gurobi parsed for the constraint names " c<label>:" with the same rule); the labels
are mapped to linopy constraint / variable names in a separate process (iis_map.py: the same build rebuilt, label vectors checked, then
Model.constraints.print_labels = the body of Model.print_infeasibilities).

Parameters: the profile of SPLIT_BUILD.json (as b4_split_solve.py, in order), TimeLimit replaced by --time-limit (IIS <= 30 min, instruction 4),
then --grb KEY=VALUE (run protection / measurement), then the log file. computeIIS() is called on the unsolved model (Gurobi determines
infeasibility itself); a GurobiError (e.g. the model is feasible) is recorded with its code and message.

    GRB_LICENSE_FILE=<path> python iis_lp.py --build-dir <dir with split/problem.lp> --out-dir <new dir> [--time-limit 1800] [--grb K=V ...]
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np


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
    params = dict(build["solver_parameters"]); params["TimeLimit"] = float(a.time_limit); extra = kv(a.grb)
    res = dict(script="work/p1_v3_diag_20261105/scripts/iis_lp.py", build_dir=str(bd), problem_file=build["problem_file"], problem_sha256_build=build.get("problem_sha256"),
               solver_parameters=params, extra_parameters=extra, started_epoch=time.time())
    import gurobipy as gp
    res["gurobipy_version"] = ".".join(map(str, gp.gurobi.version()))
    try:
        with gp.Env() as env:
            m = gp.read(build["problem_file"], env=env)
            res.update(num_vars=int(m.NumVars), num_constrs=int(m.NumConstrs), fingerprint=f"0x{int(m.Fingerprint) & 0xffffffff:08x}")
            for k, v in params.items():
                m.setParam(k, v)
            for k, v in extra.items():
                m.setParam(k, v)
            m.setParam("logfile", str(od / "gurobi.iis.log"))
            t0 = time.time()
            try:
                m.computeIIS()
                res["iis_seconds"] = time.time() - t0
                res["iis_minimal"] = bool(m.IISMinimal)
                ilp = od / "iis.ilp"; m.write(str(ilp))
                labels = []   # linopy 0.5.5 compute_infeasibilities() parsing rule
                pattern = re.compile(r"^ [^:]+#([0-9]+):")
                for line in ilp.read_text(errors="ignore").splitlines(keepends=True):
                    try:
                        if line.startswith(" c"):
                            labels.append(int(line.split(":")[0][2:]))
                    except ValueError:
                        mm = pattern.match(line)
                        if mm:
                            labels.append(int(mm.group(1)))
                res["iis_constraint_labels"] = labels
                txt = ilp.read_text(errors="ignore"); sec = txt.split("Bounds", 1)[1] if "Bounds" in txt else ""
                res["iis_bound_lines"] = [ln.strip() for ln in sec.splitlines() if ln.strip() and not ln.strip().lower().startswith("end")][:2000]
                res["iis_bound_var_labels"] = sorted({int(x) for ln in res["iis_bound_lines"] for x in re.findall(r"\bx(\d+)\b", ln)})
                res["outcome"] = "IIS_FOUND"
            except gp.GurobiError as e:
                res["iis_seconds"] = time.time() - t0
                res["outcome"] = "GUROBI_ERROR"; res["error"] = dict(errno=int(getattr(e, "errno", -1)), message=str(e)[:500])
            res["status_code_after"] = int(m.Status); res["runtime_s"] = float(m.Runtime)
            try:
                res["max_mem_used_gb"] = float(m.MaxMemUsed)
            except Exception:
                pass
            m.dispose()
    except Exception as e:
        res["outcome"] = res.get("outcome") or "FAILURE"; res["failure"] = dict(error=type(e).__name__, detail=str(e)[:1000])
    res["finished_epoch"] = time.time()
    (od / "IIS_LP.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res.get(k) for k in ("outcome", "iis_seconds", "iis_minimal", "status_code_after", "max_mem_used_gb", "error", "failure")}
                     | dict(iis_constraints=len(res.get("iis_constraint_labels", [])), iis_bounds=len(res.get("iis_bound_var_labels", [])))))
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--build-dir", required=True); p.add_argument("--out-dir", required=True)
    p.add_argument("--time-limit", type=float, default=1800.0); p.add_argument("--grb", action="append", default=[])
    sys.exit(main(p.parse_args()))
