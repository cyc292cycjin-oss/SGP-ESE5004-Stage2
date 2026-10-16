"""S4B-3 (decisions 74, 75): onshore-wind calibration against observed generation (Staffell & Pfenninger 2016, Energy 114:1224-1239;
the Renewables.ninja approach) and the modern-turbine power curve for new onshore wind.

1. Observed capacity factor (Ember yearly data, CC BY 4.0, sources_s4b/ember): CF_y = generation_y / (8,760 h x mean(capacity_y, capacity_y-1)),
   2019-2025; years with capacity growth > 50 % or a missing capacity are dropped; VN 2020-2022 (curtailment period) dropped in the main
   median and reported separately; countries below 200 MW or with < 2 valid years are not calibrated on their own. Median of valid years (grade B).
2. Model CF at the existing wind farms: GEM GIPT 2026-09 operating wind units (onshore and offshore / intertidal, since Ember does not split
   them) with start year <= 2024 or unknown; each farm on its ERA5 0.3 deg cell of the 2013 cutout; atlite 0.4.1 arithmetic reproduced
   (wnd_hub = wnd100m x ln(h/z0)/ln(100/z0), np.interp on the power curve / rated power); capacity-weighted per country. GEM carries no
   wind turbine model, so the calibration turbine is the local atlite NREL_ReferenceTurbine_2020ATB_4MW (150 m rotor, 226 W/m2, hub 110 m),
   a low-specific-power IEC III-class reference comparable to 2018-2022 low-wind turbines (INFERENCE); Vestas V112 3 MW (310.6 W/m2,
   hub 80 m) is reported as a comparison.
3. alpha_c: scaling of the ERA5 100 m wind speed (hence of the hub-height speed) such that the model CF equals the observed CF (bisection);
   uncalibrated countries take the capacity-weighted alpha of the calibrated ones (grade C); any alpha outside [0.8, 1.6] stops the step.
4. New onshore turbine: technology-data v0.15.0 onwind 2050 = DEA data sheet "20 Onshore turbines" (inputs/technology_data_for_el_and_dh.xlsx,
   git blob ce07675b, 2022-03-17): 6 MW, rotor 165 m, hub 110 m, specific power 280.6 W/m2. Power curve: the V112 per-unit curve with the
   partial-load wind speeds scaled by (280.6 / 310.6)^(1/3) (equal Cp shape, rated speed ~ specific power^(1/3)), cut-in 3 m/s x scale,
   cut-out 25 m/s kept; rated 6 MW, hub 110 m (atlite custom turbine dict).
5. GWA cross-check (CF only): alpha_GWA,c = GWA 3.3 country mean 100 m wind speed (S4A-1 section 1.3) / ERA5 2013 country land mean 100 m speed.

    python scripts_project/s4b_3_wind_calibration.py --ember <csv> --output research_inputs/renewable_v5
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
CUTOUT = ROOT / "cutouts/asean_zenodo_20325289/cutout-2013-era5.nc"
GIPT = ROOT / "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv"
AUTHOR_SHAPES = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources/baseline-aims-3H-tutorial/shapes/country_shapes.geojson")
ISO3 = {"BRN": "BN", "KHM": "KH", "IDN": "ID", "LAO": "LA", "MYS": "MY", "MMR": "MM", "PHL": "PH", "SGP": "SG", "THA": "TH", "TLS": "TL", "VNM": "VN"}
GWA_WS100 = {"BN": 4.58, "KH": 4.14, "ID": 4.19, "LA": 3.75, "MM": 4.09, "MY": 3.62, "PH": 5.86, "SG": 4.02, "TH": 4.28, "TL": 4.11, "VN": 6.27}   # S4A-1 section 1.3 (GWA 3.3 country land mean, 100 m)
IRENA_FIG212 = {"ID": "about 26-38 %, series end about 32 %", "PH": "about 35 % (2024)", "VN": "about 42 % (2024)"}   # S4A-1 section 1.3 reading of IRENA RPGC 2024 Fig. 2.12 (grade C, +-2 pp)
V112 = dict(V=[0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 25, 25], POW=[0, 0, 0.005, 0.15, 0.3, 0.525, 0.905, 1.375, 1.95, 2.58, 2.96, 3.05, 3.06, 3.06, 0.0], hub_height=80.0, P=3.06, rotor_m=112.0)
ALPHA_BOUNDS = (0.8, 1.6)


def atlite_turbine(name):
    import yaml
    import atlite
    p = Path(atlite.__file__).parent / "resources/windturbine" / f"{name}.yaml"
    c = yaml.safe_load(p.read_text())
    return dict(V=list(map(float, c["V"])), POW=list(map(float, c["POW"])), hub_height=float(c["HUB_HEIGHT"]), P=float(max(c["POW"])), source=str(p.name))


def dea2050_turbine():
    sp_v112 = V112["P"] * 1e6 / (np.pi * (V112["rotor_m"] / 2) ** 2); sp = 6e6 / (np.pi * 82.5 ** 2); s = (sp / sp_v112) ** (1 / 3)
    V = [0.0] + [v * s for v in V112["V"][1:13]] + [25.0, 25.0]
    POW = [p / V112["P"] * 6.0 for p in V112["POW"]]
    return dict(V=V, POW=POW, hub_height=110.0, P=6.0, rotor_m=165.0, specific_power_w_m2=sp, base="Vestas V112 per-unit curve", wind_speed_scale=s, specific_power_base_w_m2=sp_v112,
                source="technology-data v0.15.0 onwind 2050 = DEA data sheet 20 Onshore turbines (2022-03 sheet, git blob ce07675b): 6 MW, rotor 165 m, hub 110 m")


def cf_series(w100, z0, turb, alpha):
    h = turb["hub_height"]; hub = alpha * w100 * (np.log(h / z0) / np.log(100.0 / z0))
    return np.interp(hub, np.asarray(turb["V"], float), np.asarray(turb["POW"], float) / turb["P"])


def observed(ember_csv):
    e = pd.read_csv(ember_csv); w = e[(e["Electricity source"] == "Wind") & e["ISO 3 code"].isin(ISO3)].copy()
    w["country"] = w["ISO 3 code"].map(ISO3); w = w.sort_values(["country", "Year"])
    rows = []
    for c, d in w.groupby("country"):
        d = d.set_index("Year")
        for y in range(2019, 2026):
            if y not in d.index:
                continue
            g = d.at[y, "Generation (TWh)"]; cap = d.at[y, "Capacity (GW)"]; cap0 = d.at[y - 1, "Capacity (GW)"] if (y - 1) in d.index else np.nan
            valid, why = True, ""
            if pd.isna(cap) or pd.isna(cap0) or pd.isna(g):
                valid, why = False, "capacity or generation missing"
            elif cap0 <= 0 or cap <= 0:
                valid, why = False, "no capacity"
            elif cap / cap0 - 1 > 0.5:
                valid, why = False, f"capacity growth {cap / cap0 - 1:.0%} > 50 %"
            cf = (g * 1e3) / (8760.0 * (cap + cap0) / 2) if (not pd.isna(cap) and not pd.isna(cap0) and (cap + cap0) > 0 and not pd.isna(g)) else np.nan
            curt = (c == "VN" and 2020 <= y <= 2022)
            rows.append(dict(country=c, year=y, generation_twh=g, capacity_gw=cap, capacity_prev_gw=cap0, cf=cf, valid_growth_rule=valid, exclusion_reason=why, vn_curtailment_period=curt,
                             used_in_main=bool(valid and not curt)))
    return pd.DataFrame(rows)


def main():
    import atlite
    ap = argparse.ArgumentParser(); ap.add_argument("--ember", type=Path, required=True); ap.add_argument("--output", type=Path, required=True); a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    obs = observed(a.ember)
    summ = []
    for c, d in obs.groupby("country"):
        maxcap = float(d.capacity_gw.max(skipna=True)) if d.capacity_gw.notna().any() else 0.0
        main_ = d[d.used_in_main]; incl = d[d.valid_growth_rule]
        summ.append(dict(country=c, max_capacity_gw=maxcap, valid_years_main=int(len(main_)), years_main=";".join(map(str, main_.year)), cf_obs_median_main=float(main_.cf.median()) if len(main_) else np.nan,
                         valid_years_incl_curtailment=int(len(incl)), cf_obs_median_incl_curtailment=float(incl.cf.median()) if len(incl) else np.nan,
                         calibrate=bool(maxcap >= 0.2 and len(main_) >= 2), irena_fig_2_12=IRENA_FIG212.get(c, "")))
    S = pd.DataFrame(summ).set_index("country")
    # farms
    gem = pd.read_csv(GIPT, low_memory=False)
    f = gem[(gem.Type == "wind") & (gem.Status == "operating") & (gem["Start year"].isna() | (gem["Start year"] <= 2024)) & gem.Latitude.notna()].copy()
    ds = xr.open_dataset(CUTOUT)
    x0, y0 = float(ds.x.values[0]), float(ds.y.values[0]); dx = float(ds.x.values[1] - ds.x.values[0]); dy = float(ds.y.values[1] - ds.y.values[0])
    f["ix"] = np.clip(np.round((f.Longitude - x0) / dx).astype(int), 0, ds.sizes["x"] - 1); f["iy"] = np.clip(np.round((f.Latitude - y0) / dy).astype(int), 0, ds.sizes["y"] - 1)
    f["cell_x"] = ds.x.values[f.ix]; f["cell_y"] = ds.y.values[f.iy]
    cells = f[["ix", "iy"]].drop_duplicates().reset_index(drop=True)
    # one sequential read of each variable (pointwise netCDF indexing through compressed chunks is very slow), then in-memory indexing
    W = ds["wnd100m"].transpose("time", "y", "x").values; w100 = W[:, cells.iy.values, cells.ix.values].astype(np.float64)
    Z = ds["roughness"]
    z0 = (Z.transpose("time", "y", "x").values[:, cells.iy.values, cells.ix.values] if "time" in Z.dims else np.broadcast_to(Z.transpose("y", "x").values[cells.iy.values, cells.ix.values], w100.shape)).astype(np.float64)
    del Z
    cell_id = {(int(r.ix), int(r.iy)): i for i, r in cells.iterrows()}
    f["cell"] = [cell_id[(int(i), int(j))] for i, j in zip(f.ix, f.iy)]
    turbs = {"nrel_atb2020_4mw": atlite_turbine("NREL_ReferenceTurbine_2020ATB_4MW"), "vestas_v112": atlite_turbine("Vestas_V112_3MW"), "dea2050_synthetic": dea2050_turbine()}
    def country_cf(c, turb, alpha):
        d = f[f.iso == c]
        if not len(d):
            return np.nan
        cfc = cf_series(w100, z0, turb, alpha).mean(axis=0)
        return float((cfc[d.cell.values] * d["Capacity (MW)"].values).sum() / d["Capacity (MW)"].sum())
    def solve(c, turb, target):
        lo, hi = 0.3, 3.0
        if not (country_cf(c, turb, lo) <= target <= country_cf(c, turb, hi)):
            return np.nan
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if country_cf(c, turb, mid) < target:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)
    rows = []
    for c in sorted(ISO3.values()):
        d = f[f.iso == c]; r = dict(country=c, farms=int(len(d)), farm_capacity_mw=float(d["Capacity (MW)"].sum()), farm_capacity_onshore_mw=float(d.loc[d.Technology.astype(str).str.lower().str.startswith("onshore"), "Capacity (MW)"].sum()))
        tgt = S.cf_obs_median_main.get(c, np.nan); cal = bool(S.calibrate.get(c, False))
        r.update(cf_obs=tgt, calibrated_individually=cal)
        for k, t in turbs.items():
            r[f"cf_model_alpha1_{k}"] = country_cf(c, t, 1.0)
            r[f"alpha_{k}"] = solve(c, t, tgt) if (cal and len(d)) else np.nan
        rows.append(r)
    A = pd.DataFrame(rows).set_index("country")
    key = "alpha_nrel_atb2020_4mw"
    calc = A[A.calibrated_individually & A[key].notna()]
    w = S.loc[calc.index, "max_capacity_gw"]; alpha_w = float((calc[key] * w).sum() / w.sum()) if len(calc) else np.nan
    A["alpha_main"] = np.where(A.calibrated_individually & A[key].notna(), A[key], alpha_w)
    A["alpha_grade"] = np.where(A.calibrated_individually & A[key].notna(), "B", "C (capacity-weighted alpha of the calibrated countries)")
    A["alpha_v112_weighted"] = np.nan
    out_of_bounds = A[(A.alpha_main < ALPHA_BOUNDS[0]) | (A.alpha_main > ALPHA_BOUNDS[1])]   # stop rule on the alpha that would be applied; comparison-turbine alphas are reported only
    # calibrated-farm CF with the new turbine at alpha_main (diagnostic)
    A["cf_farms_dea2050_alpha_main"] = [country_cf(c, turbs["dea2050_synthetic"], float(A.at[c, "alpha_main"])) if A.at[c, "farms"] else np.nan for c in A.index]
    # GWA cross-check alpha: GWA land-mean 100 m speed / ERA5 2013 land-mean 100 m speed
    import geopandas as gpd
    cut = atlite.Cutout(str(CUTOUT)); shapes = gpd.read_file(AUTHOR_SHAPES).set_index("name")
    I = cut.indicatormatrix(shapes.geometry).toarray().reshape(len(shapes), cut.data.sizes["y"], cut.data.sizes["x"])
    wmean = W.mean(axis=0, dtype=np.float64); del W
    for i, c in enumerate(shapes.index):
        if c in A.index:
            A.at[c, "era5_land_mean_ws100"] = float((I[i] * wmean).sum() / I[i].sum())
            A.at[c, "gwa_mean_ws100"] = GWA_WS100.get(c, np.nan)
            A.at[c, "alpha_gwa_check"] = A.at[c, "gwa_mean_ws100"] / A.at[c, "era5_land_mean_ws100"]
    # outputs
    obs.to_csv(a.output / "WIND_OBSERVED_CF_EMBER_2019_2025.csv", index=False)
    S.reset_index().to_csv(a.output / "WIND_OBSERVED_CF_SUMMARY.csv", index=False)
    A.reset_index().to_csv(a.output / "WIND_CALIBRATION_ALPHA.csv", index=False)
    fo = f[["GEM unit/phase ID", "Plant / Project name", "iso", "Technology", "Capacity (MW)", "Start year", "Latitude", "Longitude", "cell_x", "cell_y"]].copy()
    for k, t in turbs.items():
        cfc = cf_series(w100, z0, t, 1.0).mean(axis=0); fo[f"cf_alpha1_{k}"] = cfc[f.cell.values]
    fo["alpha_main"] = fo.iso.map(A.alpha_main); fo["cf_calibrated_nrel4mw"] = [float(cf_series(w100[:, [cl]], z0[:, [cl]], turbs["nrel_atb2020_4mw"], al).mean()) for cl, al in zip(f.cell.values, fo.alpha_main.values)]
    fo.to_csv(a.output / "WIND_FARMS_MODEL_CF_2013.csv", index=False)
    turb_out = {k: {kk: (list(map(float, vv)) if isinstance(vv, (list, np.ndarray)) else vv) for kk, vv in t.items()} for k, t in turbs.items()}
    ev = dict(method=__doc__.split("\n\n")[0], ember_rows=int(len(obs)), farms=int(len(f)), cells=int(len(cells)), alpha_bounds=ALPHA_BOUNDS, alpha_weighted_calibrated=alpha_w,
              alpha_out_of_bounds=out_of_bounds.index.tolist(), turbines=turb_out, summary=S.reset_index().to_dict("records"), calibration=A.reset_index().to_dict("records"))
    (a.output / "WIND_CALIBRATION_S4B3.json").write_text(json.dumps(ev, indent=1, default=float))
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(S.round(3).to_string()); print(A.round(3).to_string()); print("alpha weighted", alpha_w, "OUT OF BOUNDS:", out_of_bounds.index.tolist())


if __name__ == "__main__":
    main()
