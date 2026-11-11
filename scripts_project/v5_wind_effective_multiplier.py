"""V5 X20 revision 1-1, decision 251: bound check of the onshore-wind speed scaling on the effective multiplier.

In v5 the country alpha scales the GWA-corrected ERA5 speed, so the v4 bound [0.8, 1.6] on alpha alone (s4b_3_wind_calibration.py ALPHA_BOUNDS) is
replaced (a rule correction made after the point-factor alphas PH 0.699 / VN 0.789 were seen, X20_SPEC_ADDENDUM_246.md section 5) by a check of
  m(y, x) = cell factor f(y, x) x alpha_c   (relative to the ERA5 2013 100 m speed; v4: f = 1)
on the candidate cells of each country:
  candidate cells   author onshore-wind potential > 0 (s4a_profiles.author_potential, profile_onwind.nc), country = the country shape with the largest
                    area share of the cell (the s4a_profiles.alpha_cutout rule)
  statistics        potential-weighted p10 / median / p90 of m (weighted quantile: the first value whose cumulative weight share >= q)
  rule              every country median in [0.8, 1.6] -> continue; any median outside -> the step stops (SystemExit)
  candidate CF      potential-weighted 2013 mean CF of the DEA 2050 turbine (hub 110 m) at the speed m x ERA5 w100, s4b_3_wind_calibration.cf_series arithmetic
Sets: --set label=alpha_csv[:cell] (":cell" multiplies the cell factor); the first set is the checked one (v5 main = WIND_CALIBRATION_ALPHA_V5.csv:cell).

    PYTHONHASHSEED=0 python scripts_project/v5_wind_effective_multiplier.py --set b=research_inputs/renewable_v5/WIND_CALIBRATION_ALPHA_V5.csv:cell \
        --set v4=research_inputs/renewable_v5/WIND_CALIBRATION_ALPHA.csv --output research_inputs/renewable_v5/WIND_EFFECTIVE_MULTIPLIER_V5.csv
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
BOUNDS = (0.8, 1.6)   # decision 251: the v4 alpha bound applied to the country median of the effective multiplier
QUANTILES = (0.1, 0.5, 0.9)


def wquantile(v: np.ndarray, w: np.ndarray, q: float) -> float:
    o = np.argsort(v, kind="stable"); cw = np.cumsum(w[o]) / w.sum()
    return float(v[o][np.searchsorted(cw, q - 1e-12)])


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(argv=None):
    import atlite
    import geopandas as gpd
    from s4a_profiles import AUTHOR, CUTOUT, author_potential
    from s4b_3_wind_calibration import cf_series, dea2050_turbine
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", action="append", required=True, help="label=alpha_csv[:cell]")
    ap.add_argument("--cell-factor", type=Path, default=ROOT / "research_inputs/renewable_v5/WIND_GWA_CELL_FACTOR_V5.nc")
    ap.add_argument("--output", type=Path, required=True); ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    sets = []
    for s in a.set:
        lab, spec = s.split("=", 1); cell = spec.endswith(":cell"); p = Path(spec[:-5] if cell else spec)
        sets.append((lab, p if p.is_absolute() else ROOT / p, cell))
    cut = atlite.Cutout(str(CUTOUT))
    shapes = gpd.read_file(AUTHOR / "shapes/country_shapes.geojson").set_index("name")
    I = cut.indicatormatrix(shapes.geometry).toarray().reshape(len(shapes), cut.data.sizes["y"], cut.data.sizes["x"])
    best = I.argmax(axis=0); has = I.max(axis=0) > 0
    pot = author_potential("onwind", cut).values
    cand = (pot > 0) & has
    iy, ix = np.nonzero(cand)
    cty = np.array([shapes.index[k] for k in best[iy, ix]]); wpot = pot[iy, ix]
    f = xr.open_dataarray(a.cell_factor).transpose("y", "x").values[iy, ix]
    ds = xr.open_dataset(CUTOUT)
    w100 = ds["wnd100m"].transpose("time", "y", "x").values[:, iy, ix].astype(np.float64)   # one sequential read, then in-memory indexing (s4b_3 pattern)
    Z = ds["roughness"]
    z0 = (Z.transpose("time", "y", "x").values[:, iy, ix] if "time" in Z.dims else np.broadcast_to(Z.transpose("y", "x").values[iy, ix], w100.shape)).astype(np.float64)
    ds.close()
    turb = dea2050_turbine()
    rows, stop = [], []
    for k, (lab, p, cell) in enumerate(sets):
        al = pd.read_csv(p).set_index("country").alpha_main
        alpha = np.array([float(al.get(c, np.nan)) for c in cty])
        m = alpha * (f if cell else 1.0)
        cf = cf_series(w100, z0, turb, m).mean(axis=0)
        for c in sorted(set(cty)):
            sel = (cty == c) & np.isfinite(m)
            if not sel.any():
                continue
            r = dict(set=lab, alpha_table=str(p.relative_to(ROOT)) if str(p).startswith(str(ROOT)) else str(p), alpha_table_sha256=sha(p), cell_factor=cell, country=c,
                     alpha=float(al.get(c, np.nan)), candidate_cells=int(sel.sum()), candidate_potential_mw=float(wpot[sel].sum()),
                     **{f"m_p{int(q * 100)}": wquantile(m[sel], wpot[sel], q) for q in QUANTILES},
                     f_median=wquantile(f[sel], wpot[sel], 0.5), cf_candidate_mean=float((cf[sel] * wpot[sel]).sum() / wpot[sel].sum()))
            r["median_in_bounds"] = BOUNDS[0] <= r["m_p50"] <= BOUNDS[1]
            rows.append(r)
            if k == 0 and not r["median_in_bounds"]:
                stop.append((c, r["m_p50"]))
    t = pd.DataFrame(rows)
    t.to_csv(a.output, index=False, lineterminator="\n")
    ev = dict(script="scripts_project/v5_wind_effective_multiplier.py", rule=__doc__.split("\n\n")[1], bounds=BOUNDS, checked_set=sets[0][0], stop=stop,
              cell_factor=dict(path=str(a.cell_factor), sha256=sha(a.cell_factor)), candidate_cells=int(cand.sum()), output=dict(path=str(a.output), sha256=sha(a.output)))
    if a.json:
        a.json.write_text(json.dumps(ev, indent=1, default=str) + "\n")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)
    print(t[["set", "country", "alpha", "candidate_cells", "m_p10", "m_p50", "m_p90", "f_median", "cf_candidate_mean", "median_in_bounds"]].round(4).to_string(index=False))
    if stop:
        raise SystemExit(f"decision 251 bound: country median of the effective multiplier outside {BOUNDS}: {stop}")
    print("decision 251 bound check passed for", sets[0][0])


if __name__ == "__main__":
    main()
