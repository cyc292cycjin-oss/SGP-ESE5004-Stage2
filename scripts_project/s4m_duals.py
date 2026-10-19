"""S4M supplement 01: constraint duals by constraint name (export only).

dual_dataset(m): one xarray Dataset with every linopy constraint dual as a variable; the dims of each constraint are prefixed with the constraint name
('<constraint>|<dim>') so that constraints sharing a dim name with different coordinate values (e.g. 'Generator' for the fixed and the extendable
subset) can live in one file (m.dual itself raises 'conflicting values for variable ...' on this model).

duals_from_solution(solve_dir, network): the same file rebuilt READ ONLY from an existing solve folder - the raw dual vector solution/Pi.npy (original
units, as used by the V5 gates) is mapped onto the constraint label arrays of the model rebuilt with the same create_model + research hooks call as
s2_solve.py (no solve); the mapping is checked against the network's buses_t.marginal_price (Bus-nodal_balance and Bus-meshed-nodal_balance duals
assigned by PyPSA, divided by the snapshot objective weighting) and the file is only written when both checks are exact.

Reproducibility: the rebuild must run with PYTHONHASHSEED=0 like the solves. The order of the strongly meshed buses (pypsa get_strongly_meshed_buses ->
pandas value_counts on str objects) depends on the str hash seed, so with another seed the Bus-meshed-nodal_balance labels are permuted and the mapped
duals are assigned to the wrong buses (found on the S4M-S2 re-run: same value set per snapshot, 199 of 270 buses permuted; exact with seed 0).

    PYTHONHASHSEED=0 python scripts_project/s4m_duals.py --solve <solve dir> [--network <unsolved nc>] [--repo <repo>]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def dual_dataset(m) -> tuple[xr.Dataset, pd.DataFrame]:
    das = {}; rows = []
    for k, con in m.constraints.items():
        try:
            da = con.dual
        except Exception as e:   # no dual assigned
            rows.append(dict(constraint=k, dims="", size=0, nan=0, error=str(e)[:120])); continue
        da = da.reset_coords(drop=True).rename({d: f"{k}|{d}" for d in da.dims})   # drop non-dimension coordinates (e.g. a 'Generator' coordinate variable carried by linopy labels), prefix the dims
        das[k] = da
        v = np.asarray(da.values, dtype=float)
        rows.append(dict(constraint=k, dims="|".join(str(d).split("|", 1)[-1] for d in da.dims), size=int(v.size), nan=int(np.isnan(v).sum()),
                         is_research=bool(k.lower().startswith("research") or "loss_proxy" in k or "loss_upper" in k), error=""))
    return xr.Dataset(das), pd.DataFrame(rows)


def write_duals(m, out: Path, source: str = "model") -> dict:
    Dd, idx = dual_dataset(m)
    Dd.to_netcdf(out / "DUALS_BY_CONSTRAINT.nc"); idx.to_csv(out / "DUALS_INDEX.csv", index=False)
    return dict(file="DUALS_BY_CONSTRAINT.nc", index="DUALS_INDEX.csv", source=source, constraints=int(len(idx)), research_constraints=int(idx.get("is_research", pd.Series(dtype=bool)).fillna(False).sum()),
                values=int(idx["size"].sum()), nan_values=int(idx["nan"].sum()), unassigned=[r["constraint"] for r in idx.to_dict("records") if r.get("error")])


def duals_from_solution(solve_dir: Path, network: Path | None = None, repo: Path | None = None) -> dict:
    """Rebuild the model (create_model + hooks + objective-constant removal, as s2_solve.py) and map solution/Pi.npy onto the constraint labels."""
    import os
    import pypsa
    from assembly_components import install_research_constraint_hooks
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("PYTHONHASHSEED=0 is required for the dual reconstruction (meshed-bus constraint order depends on the str hash seed; the solves run with seed 0)")
    rec = json.loads((solve_dir / "SOLVE_RECEIPT.json").read_text())
    repo = Path(repo) if repo else HERE.parent
    net = Path(network) if network else (repo / rec["input_network"]["path"])
    n = pypsa.Network(str(net))
    if rec["input_network"].get("truncated_to"):
        n.set_snapshots(n.snapshots[: int(rec["input_network"]["truncated_to"])])
        from s2_solve import set_representative_weights
        set_representative_weights(n)
    n.meta.update(solver_allowed=True, artifact_role=rec["label"] + "_UNSOLVED", s2_solve_authorization="S4M supplement 01 read-only dual reconstruction (no solve)", s2_solve_label=rec["label"])
    tl = int((n.meta.get("research_transmission_losses") or {}).get("ac_transmission_losses", 0))
    m = n.optimize.create_model(transmission_losses=tl); install_research_constraint_hooks(n)
    if (rec.get("scaling") or {}).get("objective_constants"):
        from s3b_scaling import remove_objective_constants
        remove_objective_constants(m)
    clabels = np.load(solve_dir / "lp" / "clabels.npy"); Pi = np.load(solve_dir / "solution" / "Pi.npy")
    if len(clabels) != len(Pi):
        raise ValueError("clabels / Pi length mismatch")
    lut = np.full(int(clabels.max()) + 1, np.nan); lut[clabels] = Pi
    das = {}; rows = []
    for k, con in m.constraints.items():
        lab = np.asarray(con.labels.values)
        vals = np.where(lab >= 0, lut[np.clip(lab, 0, len(lut) - 1)], np.nan)
        da = xr.DataArray(vals, coords={d: con.labels.coords[d] for d in con.labels.dims}, dims=con.labels.dims).reset_coords(drop=True).rename({d: f"{k}|{d}" for d in con.labels.dims})
        das[k] = da
        rows.append(dict(constraint=k, dims="|".join(map(str, con.labels.dims)), size=int(vals.size), nan=int(np.isnan(vals).sum()), is_research=bool(k.lower().startswith("research") or "loss_proxy" in k or "loss_upper" in k), error=""))
    Dd = xr.Dataset(das); idx = pd.DataFrame(rows)
    # cross-check: Bus-nodal_balance duals must equal the marginal prices PyPSA assigned from the live model
    check = {}
    solved = next(iter(solve_dir.glob("*_solved.nc")), None)
    if solved is not None and "Bus-nodal_balance" in Dd:
        # the file holds the RAW LP duals (EUR per unit of the row, i.e. per weighted snapshot); PyPSA assigns marginal_price = dual / snapshot_weightings.objective
        ns = pypsa.Network(str(solved)); mp = ns.buses_t.marginal_price; w = ns.snapshot_weightings.objective
        for key, name in (("", "Bus-nodal_balance"), ("meshed_", "Bus-meshed-nodal_balance")):
            if name not in Dd:
                continue
            da = Dd[name]; sd = [d for d in da.dims if d.endswith("|snapshot")][0]; bd = [d for d in da.dims if not d.endswith("|snapshot")][0]
            df = da.transpose(sd, bd).to_pandas(); common = [b for b in df.columns if b in mp.columns]
            scaled = df[common].div(w.to_numpy(), axis=0)
            diff = float(np.nanmax(np.abs(scaled.to_numpy() - mp[common].to_numpy()) / np.maximum(1.0, np.abs(mp[common].to_numpy())))) if common else float("nan")
            check.update({f"{key}buses_compared": len(common), f"{key}max_rel_diff_vs_marginal_price_after_weight_division": diff, f"{key}consistent": bool(diff <= 1e-9)})
        check["note"] = "raw LP duals; marginal_price = dual / snapshot_weightings.objective (PyPSA assign_duals); static constraints are unweighted"
    if len(Pi) != int(m.ncons):
        raise RuntimeError(f"LP rows {len(Pi)} != rebuilt model rows {m.ncons}: the rebuilt model differs from the solved one - file not written")
    if not check or not all(v for k, v in check.items() if k.endswith("consistent")):
        raise RuntimeError(f"dual reconstruction not exact against buses_t.marginal_price - file not written: {check}")
    Dd.to_netcdf(solve_dir / "DUALS_BY_CONSTRAINT.nc"); idx.to_csv(solve_dir / "DUALS_INDEX.csv", index=False)
    return dict(file="DUALS_BY_CONSTRAINT.nc", index="DUALS_INDEX.csv", source="offline reconstruction from solution/Pi.npy + lp/clabels.npy (model rebuilt without solve, PYTHONHASHSEED=0)", constraints=int(len(idx)),
                research_constraints=int(idx.is_research.sum()), values=int(idx["size"].sum()), nan_values=int(idx["nan"].sum()), lp_rows=int(len(Pi)), model_rows=int(m.ncons), cross_check=check)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--solve", type=Path, required=True); ap.add_argument("--network", type=Path, default=None); ap.add_argument("--repo", type=Path, default=None)
    a = ap.parse_args()
    from s1_solve import sha
    res = duals_from_solution(a.solve, a.network, a.repo)
    rec = json.loads((a.solve / "SOLVE_RECEIPT.json").read_text())
    rec["duals"] = dict({k: v for k, v in (rec.get("duals") or {}).items() if k != "export_error"}, **res)
    ex = json.loads((a.solve / "EXPORTS.json").read_text()) if (a.solve / "EXPORTS.json").exists() else {}
    for f in ("DUALS_BY_CONSTRAINT.nc", "DUALS_INDEX.csv"):
        ex[f] = dict(bytes=(a.solve / f).stat().st_size, sha256=sha(a.solve / f))
    (a.solve / "EXPORTS.json").write_text(json.dumps(ex, indent=2)); rec["exports"] = ex
    (a.solve / "SOLVE_RECEIPT.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False, default=str) + "\n")
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
