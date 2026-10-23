"""M10R B3.3 (drill of every network type): a SYNTHETIC "solved" run of a network type that has no real 56x3h solve - used only to verify that
the post-processing chain runs through and that the ledger identity is computable (never a result; label SYNTHETIC_TEST_ONLY everywhere).

  1. scripts_project/s2_solve.py --stop-before-solve --truncate N  (the real LP build and export: lp/ arrays, pre-solve receipt; no solver call)
  2. the network truncated like the solve (representative weights), every extendable capacity "built" at its nominal value (p_nom_opt = p_nom:
     no new capacity), every flow / dispatch / state of charge 0, every bus dual 0 -> written as <scenario>_SYNTHETIC_TEST_ONLY_solved.nc;
     objective = the fixed-once constants (existing asset FOM + existing cross-border FOM), so that the ledger identity must hold exactly
  3. solution arrays X / Pi / RC = zeros of the LP dimensions; the receipt completed with termination_condition "synthetic", the solution counts,
     exports {}; V5_GATES.json with an A4 readback entry of the written file (status EXACT_SEMANTIC_ROUNDTRIP only when the round trip is exact)

    PYTHONHASHSEED=0 python scripts_project/m10r_synthetic_solution.py --repo . --network <unsolved nc> --scenario <sc> --out <dir> [--truncate 56] [--costs-table <csv>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
SCRIPT = "scripts_project/m10r_synthetic_solution.py"
LABEL = "SYNTHETIC_TEST_ONLY"
NOM = {"Generator": "p_nom", "Link": "p_nom", "Line": "s_nom", "StorageUnit": "p_nom", "Store": "e_nom"}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=HERE.parent); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--scenario", required=True)
    ap.add_argument("--out", type=Path, required=True); ap.add_argument("--truncate", type=int, default=56); ap.add_argument("--costs-table", type=Path, default=None)
    a = ap.parse_args()
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise SystemExit("run with PYTHONHASHSEED=0")
    logging.disable(logging.WARNING)
    import pypsa
    from network_checks import compare_roundtrip
    from s2_solve import set_representative_weights
    out = a.out; out.mkdir(parents=True, exist_ok=True); t0 = time.time()
    # the LP build uses the smoke label (s2_solve.py accepts a truncated horizon only as a smoke test / diagnostic); the synthetic marker is in the
    # receipt (status SYNTHETIC_TEST_ONLY, synthetic=...), the network meta and SYNTHETIC.json
    cmd = [sys.executable, str(a.repo / "scripts_project/s2_solve.py"), "--repo", str(a.repo), "--network", str(a.network), "--scenario", a.scenario, "--output", str(out),
           "--label", "SMOKE_TEST_ONLY", "--authorization", "M10R drill: synthetic solution, LP build only, no solver call", "--solver", "gurobi", "--solver-profile", "formal_barrier",
           "--scaling", "on", "--time-limit", "1750", "--truncate", str(a.truncate), "--stop-before-solve"]
    if a.costs_table:
        cmd += ["--costs-table", str(a.costs_table)]
    env = {k: v for k, v in os.environ.items() if k != "GRB_LICENSE_FILE"}; env["GRB_LICENSE_FILE"] = "/nonexistent/m10r_drill_no_licence"
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    (out / "build.log").write_text(r.stdout); (out / "build.err").write_text(r.stderr)
    if r.returncode != 0:
        raise SystemExit(f"LP build (--stop-before-solve) failed: {r.stderr[-800:]}")
    rec = json.loads((out / "SOLVE_RECEIPT.json").read_text()); lp = rec["lp"]
    n = pypsa.Network(str(a.network))
    if a.truncate:
        n.set_snapshots(n.snapshots[:a.truncate]); set_representative_weights(n)
    n.meta.update(artifact_role=LABEL + "_SOLVED", result_label=LABEL, synthetic_solution=dict(script=SCRIPT, note="no solver: capacities at nominal, flows 0, duals 0, objective = fixed-once constants"))
    const = float(n.meta.get("existing_cross_border_fom_eur", 0.0))
    for t, nom in NOM.items():
        d = n.df(t)
        if not len(d):
            continue
        d[nom + "_opt"] = d[nom].astype(float)
        if "existing_annual_fixed_om_eur" in d:
            const += float(pd.to_numeric(d.existing_annual_fixed_om_eur, errors="coerce").fillna(0.0).sum())
    zeros = lambda cols: pd.DataFrame(0.0, index=n.snapshots, columns=list(cols))
    n.generators_t.p = zeros(n.generators.index); n.loads_t.p = zeros(n.loads.index); n.stores_t.p = zeros(n.stores.index); n.stores_t.e = zeros(n.stores.index)
    n.storage_units_t.p = zeros(n.storage_units.index); n.storage_units_t.p_dispatch = zeros(n.storage_units.index); n.storage_units_t.p_store = zeros(n.storage_units.index)
    n.storage_units_t.state_of_charge = zeros(n.storage_units.index); n.storage_units_t.spill = zeros(n.storage_units.index)
    for t in ("Line", "Link"):
        d = n.df(t); pnl = n.pnl(t)
        for p in [c for c in d.columns if c.startswith("bus") and c[3:].isdigit()]:
            pnl["p" + p[3:]] = zeros(d.index)
    n.buses_t.marginal_price = zeros(n.buses.index); n.buses_t.p = zeros(n.buses.index)
    n.objective = const
    nc = out / f"{a.scenario}_{LABEL}_solved.nc"; n.export_to_netcdf(nc)
    back = pypsa.Network(str(nc)); compare_roundtrip(n, back)   # raises when the NetCDF round trip is not exact
    from v5.v5_gates import gate_a4_readback
    a4 = gate_a4_readback(n, nc)
    sol = out / "solution"; sol.mkdir(exist_ok=True)
    arr = {"X": np.zeros(int(lp["num_col"])), "Pi": np.zeros(int(lp["num_row"])), "RC": np.zeros(int(lp["num_col"]))}
    for k, v in arr.items():
        np.save(sol / f"{k}.npy", v)
    (out / "EXPORTS.json").write_text("{}")
    rec.update(termination_condition="synthetic", status="SYNTHETIC_TEST_ONLY", objective=const, objective_lp=0.0, optimize_calls=0, solve_seconds=0.0,
               solution={k: dict(count=int(len(v)), sha256=sha(sol / f"{k}.npy")) for k, v in arr.items()}, exports={}, solved_network=str(nc),
               synthetic=dict(script=SCRIPT, note="drill only: no solver call; capacities nominal, flows 0, duals 0; objective = fixed-once constants"),
               decision="SYNTHETIC_DRILL_" + LABEL, finished_epoch=time.time())
    rec.pop("stop_before_solve", None)
    (out / "SOLVE_RECEIPT.json").write_text(json.dumps(rec, indent=1, default=str))
    gates = dict(A4=a4, acceptance_basis="barconvtol", synthetic=True)
    (out / "V5_GATES.json").write_text(json.dumps(gates, indent=1, default=str))
    (out / "v5").mkdir(exist_ok=True); (out / "v5" / "kkt_summary.json").write_text(json.dumps(dict(source="synthetic: no KKT summary (zeros)", primal_objective=None, dual_objective_numeric=None)))
    (out / "SYNTHETIC.json").write_text(json.dumps(dict(script=SCRIPT, network=str(a.network), network_sha256=sha(a.network), scenario=a.scenario, truncate=a.truncate, objective_constants=const,
                                                        lp=dict(num_col=lp["num_col"], num_row=lp["num_row"]), solved_network=dict(path=str(nc), sha256=sha(nc)), readback=a4.get("status"),
                                                        seconds=round(time.time() - t0, 1), solver_runs=0), indent=1, default=str) + "\n")
    print(json.dumps(dict(synthetic=True, objective_constants=const, num_col=lp["num_col"], num_row=lp["num_row"], seconds=round(time.time() - t0, 1))))


if __name__ == "__main__":
    main()
