"""V4 D2b section 4.6: VN offshore-wind calibration coefficient under the existing S4B-3 rule (scripts_project/s4b_3_wind_calibration.py), with the
World Bank / ESMAP Offshore Wind Roadmap for Vietnam (2021) reference-site values as the target (no zone / site table exists in the roadmap, D2b
evidence DATA_UPG_B.json E30-E35; Viet Nam Technology Catalogue 2021 E37 / E38; EVNPECC3 E39). Nothing is solved; the network is not changed.

    python scripts/d2b_vn_offwind_alpha.py <repo> <main checkout> <out json>

  1. model CF: research_inputs/renewable_v5/offshore_m08a/OFFSHORE_CLASSES_pypsa_eur_v2025_07.csv, VN rows (capacity-weighted cf_annual_weighted per tech,
     the per-unit 3 h profile mean x 0.8855 of the build; ERA5 2013).
  2. reference area: ERA5 2013 cells of the Binh Thuan offshore box (lat 10.0-11.3 N, lon 108.0-109.6 E) with sea roughness (z0 < 0.002 m) - the roadmap's
     conventional fixed reference site lies off Binh Thuan (roadmap Table 9.1: 7.5 / 8.5 / 8.5 m/s at 100 m for 2023 / 2030 / 2035 sites).
  3. S4B-3 item 3 (CF match): alpha scales the ERA5 100 m speed so that the box-mean CF of the model's fixed-bottom turbine (atlite
     NREL_ReferenceTurbine_2020ATB_5.5MW, hub 120 m, x 0.8855 wake / availability factor of the build) equals the target net CF (bisection, 0.3-3.0).
     Targets: Technology Catalogue 2050 fixed 53 % (incl. outages), roadmap ~60 % (2050, 20 MW+ low-wind rotors, net at the offshore substation),
     EVNPECC3 ~50 % (net, Binh Thuan). Also on the best (highest mean speed) cell. Search interval [0.3, 1.6] (the S4B-3 bound; the box CF is not monotone
     in alpha up to 3.0 because of the 25 m/s cut-out).
  4. S4B-3 item 5 (speed ratio, the GWA cross-check form): alpha = roadmap reference wind speed at 100 m / ERA5 2013 box-mean 100 m speed.
  Bounds of the rule: alpha outside [0.8, 1.6] is reported (the S4B-3 stop rule applies to an applied alpha; nothing is applied here).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

REPO, MAIN, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(REPO / "scripts_project"))
from s4b_3_wind_calibration import cf_series, atlite_turbine   # noqa: E402

CORR = 0.8855
TARGETS = {"tc2021_fixed_2050_incl_outages": 0.53, "wb_roadmap_2050_net": 0.60, "pecc3_binh_thuan_net": 0.50, "tc2021_fixed_2030": 0.46}
REF_SPEED = {"wb_ref_site_2030_2035_100m": 8.5, "wb_ref_site_2023_100m": 7.5}


def main():
    cls = pd.read_csv(REPO / "research_inputs/renewable_v5/offshore_m08a/OFFSHORE_CLASSES_pypsa_eur_v2025_07.csv")
    v = cls[(cls.country == "VN") & (cls.rules == "pypsa_eur_v2025_07")]
    model = {}
    for (tech, ncls), z in v.groupby(["tech", "classes"]):
        model[f"{tech}_c{ncls}"] = dict(potential_mw=float(z.potential_mw.sum()), cf_cap_weighted=float((z.cf_annual_weighted * z.potential_mw).sum() / z.potential_mw.sum()),
                                        cf_best_class=float(z.cf_annual_weighted.max()), rows=int(len(z)))
    ds = xr.open_dataset(MAIN / "cutouts/asean_zenodo_20325289/cutout-2013-era5.nc")
    ys, xs = ds.y.values, ds.x.values
    iy = np.where((ys >= 10.0) & (ys <= 11.3))[0]; ix = np.where((xs >= 108.0) & (xs <= 109.6))[0]
    sub = ds.isel(y=slice(iy.min(), iy.max() + 1), x=slice(ix.min(), ix.max() + 1))
    w = sub["wnd100m"].transpose("time", "y", "x").values.astype(np.float64)
    z0r = sub["roughness"]
    z0 = (z0r.transpose("time", "y", "x").values if "time" in z0r.dims else np.broadcast_to(z0r.transpose("y", "x").values, w.shape)).astype(np.float64)
    T, ny, nx = w.shape
    W, Z = w.reshape(T, ny * nx), z0.reshape(T, ny * nx)
    sea = np.nanmean(Z, axis=0) < 0.002
    W, Z = W[:, sea], Z[:, sea]
    yy, xx = np.meshgrid(sub.y.values, sub.x.values, indexing="ij"); cells = list(zip(yy.reshape(-1)[sea], xx.reshape(-1)[sea]))
    turb = atlite_turbine("NREL_ReferenceTurbine_2020ATB_5.5MW")
    mean_ws = W.mean(axis=0)
    best = int(np.argmax(mean_ws))

    def cf(alpha, cols=None):
        ww, zz = (W, Z) if cols is None else (W[:, cols], Z[:, cols])
        return float(cf_series(ww, zz, turb, alpha).mean() * CORR)

    def solve(target, cols=None):
        lo, hi = 0.3, 1.6   # D2b: upper end = the S4B-3 bound (above it the 25 m/s cut-out makes the box CF fall again: not monotone up to 3.0)
        if not (cf(lo, cols) <= target <= cf(hi, cols)):
            return None
        for _ in range(50):
            mid = 0.5 * (lo + hi)
            if cf(mid, cols) < target:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    res = dict(model_vn_offshore=model, box=dict(lat=[10.0, 11.3], lon=[108.0, 109.6], sea_cells=int(sea.sum()), cells=[[float(a), float(b)] for a, b in cells]),
               era5_box_mean_ws100=float(mean_ws.mean()), era5_best_cell=dict(lat=float(cells[best][0]), lon=float(cells[best][1]), ws100=float(mean_ws[best])),
               turbine=dict(name="NREL_ReferenceTurbine_2020ATB_5.5MW", hub_height=turb["hub_height"], P=turb["P"], correction=CORR),
               cf_alpha1_box=cf(1.0), cf_alpha1_best=cf(1.0, [best]), alpha_cf_match={}, alpha_speed_ratio={}, bounds=[0.8, 1.6])
    for k, t in TARGETS.items():
        res["alpha_cf_match"][k] = dict(target=t, alpha_box=solve(t), alpha_best_cell=solve(t, [best]))
    for k, s in REF_SPEED.items():
        res["alpha_speed_ratio"][k] = dict(ref_ws100=s, alpha_box=s / float(mean_ws.mean()), alpha_best_cell=s / float(mean_ws[best]))
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "box"}, indent=1, default=float))


if __name__ == "__main__":
    main()
