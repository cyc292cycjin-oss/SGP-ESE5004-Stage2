"""S4N-4 pilot check (READ ONLY, no solver call; runs ON the instance after DONE): receipt, gate summary, in-run dual export and its cross-check against
buses_t.marginal_price, EXPORTS.json against the files (solve folder and export folder), sizes, licence-marker scan of the export folder.

    python s4n_pilot_check.py --solve <run>/integrated --export <run>/export/integrated --out <json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np

LICENCE_RE = re.compile(rb"licens[e]id|registered\s+to|wls(secre[t]|acces[s]id)", re.I)


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def rel(a, b) -> dict:
    a = np.asarray(a, dtype=float).ravel(); b = np.asarray(b, dtype=float).ravel()
    na, nb = np.isnan(a), np.isnan(b); both = ~na & ~nb
    d = np.abs(a[both] - b[both]); bb = np.abs(b[both]); nz = bb > 0
    return dict(n=int(a.size), nan_mask_equal=bool((na == nb).all()), compared=int(both.sum()), max_abs=float(d.max()) if d.size else 0.0,
                max_rel_scaled=float((d / np.maximum(1.0, bb)).max()) if d.size else 0.0, max_rel_pure=float((d[nz] / bb[nz]).max()) if nz.any() else 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solve", type=Path, required=True); ap.add_argument("--export", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(); d, e = a.solve, a.export
    res: dict = dict(solve_dir=str(d), export_dir=str(e))
    rec = json.loads((d / "SOLVE_RECEIPT.json").read_text())
    res["receipt"] = {k: rec.get(k) for k in ("label", "termination_condition", "status", "objective", "objective_lp", "solve_seconds", "peak_rss_bytes", "retry",
                                             "optimize_calls", "solver_profile", "solver_parameters", "lp", "dust_cleanup", "transmission_losses")}
    res["receipt"]["finished"] = "finished_epoch" in rec
    res["receipt"]["gurobi_lines"] = ((rec.get("gurobi_log_stats") or {}).get("lines"))
    res["receipt"]["duals"] = {k: v for k, v in (rec.get("duals") or {}).items() if k != "note"}
    res["receipt"]["cost_breakdown"] = {k: v for k, v in (rec.get("cost_breakdown") or {}).items() if k in ("extendable", "matched", "matched_share", "by_rule")}
    # gates
    g = json.loads((d / "V5_GATES.json").read_text())
    gates = {}
    for k, v in g.items():
        if isinstance(v, dict) and "passed" in v:
            item = dict(passed=bool(v["passed"]), gate=v.get("gate"))
            for kk in ("criteria", "relative_gap", "max_relative_error", "relative_error", "failed_count", "rows_over_budget", "max_ratio_to_budget"):
                if kk in v:
                    item[kk] = v[kk]
            if isinstance(v.get("failed"), list):
                item["failed_checks"] = len(v["failed"]); item["failed_first"] = v["failed"][:5]
            gates[k] = item
    res["gates"] = dict(all_passed=g.get("all_passed"), all_passed_solver_tolerances=g.get("all_passed_solver_tolerances"), all_passed_barconvtol=g.get("all_passed_barconvtol"),
                        acceptance_basis=g.get("acceptance_basis"), failed=sorted(k for k, v in gates.items() if not v["passed"]), items=gates)
    # files and EXPORTS.json
    ex = json.loads((d / "EXPORTS.json").read_text()) if (d / "EXPORTS.json").exists() else {}
    fx = {}
    for f, meta in ex.items():
        for where, base in (("solve", d), ("export", e)):
            p = base / f
            fx.setdefault(f, {})[where] = dict(exists=p.exists(), bytes=(p.stat().st_size if p.exists() else None),
                                                match=bool(p.exists() and p.stat().st_size == meta.get("bytes") and sha(p) == meta.get("sha256")))
    res["exports_json"] = ex; res["exports_check"] = fx
    res["exports_all_match"] = bool(ex) and all(v["solve"]["match"] and v["export"]["match"] for v in fx.values())
    res["export_dir_files"] = sorted((p.name, p.stat().st_size) for p in e.iterdir() if p.is_file())
    res["export_dir_bytes"] = int(sum(s for _, s in res["export_dir_files"]))
    # dual cross-check (in-run file vs the solved network)
    import pypsa
    import xarray as xr
    solved = next(iter(d.glob("*_solved.nc")), None)
    bus = {}
    if solved is not None and (d / "DUALS_BY_CONSTRAINT.nc").exists():
        ns = pypsa.Network(str(solved)); mp = ns.buses_t.marginal_price; w = ns.snapshot_weightings.objective
        D = xr.open_dataset(d / "DUALS_BY_CONSTRAINT.nc")
        res["duals_file"] = dict(constraints=len(D.data_vars), values=int(sum(D[v].size for v in D.data_vars)),
                                 nan=int(sum(int(np.isnan(D[v].values).sum()) for v in D.data_vars)))
        for name in ("Bus-nodal_balance", "Bus-meshed-nodal_balance"):
            if name not in D:
                bus[name] = dict(present=False); continue
            da = D[name]; sd = [x for x in da.dims if x.endswith("|snapshot")][0]; bd = [x for x in da.dims if not x.endswith("|snapshot")][0]
            df = da.transpose(sd, bd).to_pandas(); common = [b for b in df.columns if b in mp.columns]
            bus[name] = dict(present=True, buses=int(df.shape[1]), buses_compared=len(common), snapshots=int(df.shape[0]), weight_unique=sorted(set(map(float, w))),
                             **rel(df[common].div(w.to_numpy(), axis=0).to_numpy(), mp[common].to_numpy()))
        res["solved_network"] = dict(file=solved.name, bytes=solved.stat().st_size, snapshots=len(ns.snapshots), buses=len(ns.buses))
    res["bus_dual_cross_check"] = bus
    res["bus_dual_cross_check_le_1e-12"] = bool(bus) and all(v.get("present") and v["buses_compared"] == v["buses"] and v["nan_mask_equal"] and v["max_rel_scaled"] <= 1e-12 and v["max_rel_pure"] <= 1e-12 for v in bus.values())
    # licence-marker scan of the export folder (file names only)
    res["licence_scan_export_dir"] = [p.name for p in e.iterdir() if p.is_file() and LICENCE_RE.search(p.read_bytes())]
    a.out.write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(dict(termination=res["receipt"]["termination_condition"], objective=res["receipt"]["objective"], gates_failed=res["gates"]["failed"],
                          all_passed_solver_tolerances=res["gates"]["all_passed_solver_tolerances"], duals=res["receipt"]["duals"], exports_all_match=res["exports_all_match"],
                          bus={k: {kk: v.get(kk) for kk in ("buses_compared", "max_rel_scaled", "max_rel_pure")} for k, v in bus.items()},
                          export_dir_bytes=res["export_dir_bytes"], licence_hits=res["licence_scan_export_dir"]), indent=1, default=str))


if __name__ == "__main__":
    main()
