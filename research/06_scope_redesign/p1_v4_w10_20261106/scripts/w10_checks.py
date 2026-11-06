#!/usr/bin/env python3
"""V4 W10 checks on every extracted solved run: (1) capacity stationarity of the extendable generators
cc - sum_t |mu_t| p_max_pu_t - dual(p_nom >= lower) - dual(p_nom <= upper) = 0, from the exported duals; (2) nodal prices from the balance duals
against the exported NODAL_PRICES.csv mean; (3) objectives and B6 of each set. Writes evidence/CHECKS.json. Read only.

usage: python w10_checks.py --dir <delivery dir> --set label=F1,F2 [...]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import rerank_with_results as R   # noqa: E402


def stationarity(run_dir: Path, ext_dir: Path) -> dict:
    g = pd.read_csv(ext_dir / "generators.csv", index_col=0)
    ds = xr.open_dataset(run_dir / "DUALS_BY_CONSTRAINT.nc")
    lo = R._dual1d(ds, "Generator-ext-p_nom-lower"); up = R._dual1d(ds, "Generator-ext-p_nom-upper")
    e = g[g.ext & (g.capital_cost > 0)].copy()
    e["resid"] = e.capital_cost - e.avail_value_per_mw - lo.reindex(e.index).fillna(0.0) - up.reindex(e.index).fillna(0.0)
    rel = (e.resid / e.capital_cost).abs()
    built = e.new_cap > R.TOL_BUILT
    ds.close()
    return dict(extendable_with_cost=int(len(e)), built=int(built.sum()), max_rel_residual_built=float(rel[built].max()), max_rel_residual_all=float(rel.max()),
                unbuilt_entry_gap_negative=int(((e.capital_cost - e.avail_value_per_mw - up.reindex(e.index).fillna(0.0)) < -1e-6 * e.capital_cost)[~built].sum()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--set", action="append", required=True)
    a = ap.parse_args()
    d = Path(a.dir)
    out = {}
    for s in a.set:
        lab, dirs = s.split("=", 1)
        res = {}
        for role, rd in zip(("F1", "F2"), dirs.split(",")):
            rd = Path(rd)
            key = R.sha256(R.run_files(rd)["nc"])[:16] + "_" + R.SCHEMA.rsplit("-", 1)[-1]
            ext = d / "cache" / key
            meta = json.loads((ext / "meta.json").read_text())
            res[role] = dict(run_dir=str(rd), nc_sha256=meta["nc_sha256"], objective=meta["objective"], snapshots=meta["snapshots"], weight_first=meta["weight_first"],
                             ship_cost_basis=meta["ship_cost_basis"], ev_mode=meta["ev"].get("mode"), price_check=meta["price_check_vs_NODAL_PRICES"],
                             stationarity=stationarity(rd, ext))
        res["B6"] = res["F2"]["objective"] - res["F1"]["objective"]
        out[lab] = res
    (d / "evidence").mkdir(exist_ok=True)
    (d / "evidence" / "CHECKS.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    imp = pd.read_csv(d / "IMPACT_FIRST_ORDER.csv")
    r = imp[imp.ranked].copy()
    r["abs_owen"] = r.owen_max_eur.abs()
    ow = r.sort_values("abs_owen", ascending=False).head(10)[["param_id", "owen_max_country", "owen_max_eur", "dB6", "dZ_F1", "rank"]]
    ow.to_csv(d / "evidence" / "OWEN_TOP10.csv", index=False, lineterminator="\n")
    fam = imp.groupby("family_201").agg(rows=("param_id", "size"), ranked=("ranked", "sum"), sum_abs_dB6=("abs_dB6", lambda s: float(s.fillna(0).sum())),
                                        max_abs_dB6=("abs_dB6", lambda s: float(s.fillna(0).max())), max_abs_dZ=("abs_dZ_max", lambda s: float(s.fillna(0).max())))
    fam.to_csv(d / "evidence" / "FAMILY_SUMMARY.csv", lineterminator="\n")
    print(json.dumps({k: dict(B6=v["B6"], F1=v["F1"]["stationarity"], F2=v["F2"]["stationarity"], pc=v["F1"]["price_check"]) for k, v in out.items()}, indent=1))
    print(ow.to_string())


if __name__ == "__main__":
    main()
