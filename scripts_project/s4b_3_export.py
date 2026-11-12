"""S4B-3: export research.renewable.profile_variant = calibrated_modern to research_inputs/renewable_v5 (same format as s4a_1_export.py).

Onshore wind from the S4B-3 run (scripts_project/s4a_profiles.py --variant calibrated_modern gwa_check --techs onwind), offshore wind and
solar unchanged from the S4A pypsa_eur run (results_project/s4a/profiles_full_c{N}_v2, identical specs). The class table
S4A_PROFILE_CLASSES_c{N}.csv gains the calibrated_modern rows (onwind from the new run, other technologies copied from pypsa_eur) and the
gwa_check onwind rows (annual capacity factors only, cross-check); existing rows are left as they are.

    python scripts_project/s4b_3_export.py --classes 3
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
OUT = ROOT / "research_inputs/renewable_v5"
TECHS = ["onwind", "offwind-ac", "offwind-dc", "solar"]


def export_v5(a, N, on_src, base):
    """V5 X20 (1-1, decisions 241, 246 Q1 (b), 251): research_inputs/renewable_v5/profiles_calibrated_gwa_v5_c{N}_3h.nc - onwind from the
    calibrated_gwa_v5 run, offshore wind and solar from the same pypsa_eur run as calibrated_modern (asserted equal to the committed
    profiles_calibrated_modern_c{N}_3h.nc arrays). The class table, manifest and run log are separate files (S4A_PROFILE_CLASSES_calibrated_gwa_v5_c{N}.csv,
    MANIFEST_V5.json, S4B3_PROFILES_LOG_calibrated_gwa_v5_c{N}.json), so every v4 input stays byte-identical."""
    var = a.variant; data = {}   # calibrated_gwa_v5 (X20 B) or calibrated_gwa_v5q (C-2, decision 252: quantile-bin cell CF)
    ref = xr.open_dataset(OUT / f"profiles_calibrated_modern_c{N}_3h.nc")
    for tech in TECHS:
        f = on_src / f"profile_{tech}_{var}_c{N}_3h.nc" if tech == "onwind" else base / f"profile_{tech}_pypsa_eur_c{N}_3h.nc"
        da = xr.open_dataarray(f).transpose("time", "bus").astype("float32").clip(0, 1)
        k = tech.replace("-", "_"); data[k] = da.rename(k)
    ds = xr.Dataset(data)   # one bus dimension (outer join of the technologies, NaN where a technology has no bus), as in the calibrated_modern export
    for k in ds.data_vars:
        if k != "onwind" and not (list(ds[k].bus.values) == list(ref[k].bus.values) and np.array_equal(ds[k].values, ref[k].values, equal_nan=True)):
            raise SystemExit(f"V5 X20: {k} of the pypsa_eur run differs from profiles_calibrated_modern_c{N}_3h.nc")
    ref.close()
    desc = ("ERA5 100 m wind x GWA v4 cell factor (WIND_GWA_CELL_FACTOR_V5.nc) x country alpha (WIND_CALIBRATION_ALPHA_V5.csv alpha_main, farm-point calibration) + DEA 2050 turbine "
            "(6 MW, 165 m, hub 110 m)") if var == "calibrated_gwa_v5" else \
           ("ERA5 100 m wind x GWA v4 quantile-bin factors (WIND_GWA_CELL_QUANTILES_V5.nc: 10 equal-area bins per cell, cell CF = area-weighted mean of the bin CFs) x country alpha "
            "(WIND_CALIBRATION_ALPHA_V5.csv alpha_main, farm-point calibration) + DEA 2050 turbine (6 MW, 165 m, hub 110 m)")
    ds.attrs.update(variant=var, classes=N, source=f"scripts_project/s4a_profiles.py (onwind V5 X20 {var}, others S4A pypsa_eur)", cutout="cutout-2013-era5 (Zenodo 10.5281/zenodo.20325289)",
                    snapshots="2013 3h means", onwind=desc)
    out = OUT / f"profiles_{var}_c{N}_3h.nc"
    ds.to_netcdf(out, encoding={k: dict(zlib=True, complevel=6, dtype="float32") for k in ds.data_vars})
    cls = pd.read_csv(OUT / f"S4A_PROFILE_CLASSES_c{N}.csv"); new = pd.read_csv(on_src / "S4A_PROFILE_CLASSES.csv")
    other = cls[(cls.variant == "pypsa_eur") & (cls.tech != "onwind")].assign(variant=var)
    merged = pd.concat([new[new.variant == var], other], ignore_index=True)
    cls_f = OUT / f"S4A_PROFILE_CLASSES_{var}_c{N}.csv"; merged.to_csv(cls_f, index=False)
    m = OUT / "MANIFEST_V5.json"; man = json.loads(m.read_text()) if m.exists() else {}
    man[out.name] = dict(sha256=hashlib.sha256(out.read_bytes()).hexdigest(), bytes=out.stat().st_size, buses={k: int(v.sizes["bus"]) for k, v in ds.data_vars.items()})
    man[cls_f.name] = dict(sha256=hashlib.sha256(cls_f.read_bytes()).hexdigest(), rows=int(len(merged)))
    (OUT / f"S4B3_PROFILES_LOG_{var}_c{N}.json").write_text((on_src / "S4A_PROFILES_LOG.json").read_text())
    m.write_text(json.dumps(man, indent=1, sort_keys=True))
    print(out.name, man[out.name], "class rows", len(merged))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--classes", type=int, required=True)
    ap.add_argument("--onwind-source", type=Path, default=None); ap.add_argument("--base-source", type=Path, default=None)
    ap.add_argument("--variant", choices=("calibrated_modern", "calibrated_gwa_v5", "calibrated_gwa_v5q"), default="calibrated_modern")
    a = ap.parse_args(); N = a.classes
    if a.variant in ("calibrated_gwa_v5", "calibrated_gwa_v5q"):
        return export_v5(a, N, a.onwind_source, a.base_source or ROOT / f"results_project/s4a/profiles_full_c{N}_v2")
    on_src = a.onwind_source or ROOT / f"results_project/s4b/profiles_full_c{N}"; base = a.base_source or ROOT / f"results_project/s4a/profiles_full_c{N}_v2"
    data = {}
    for tech in TECHS:
        f = on_src / f"profile_{tech}_calibrated_modern_c{N}_3h.nc" if tech == "onwind" else base / f"profile_{tech}_pypsa_eur_c{N}_3h.nc"
        da = xr.open_dataarray(f).transpose("time", "bus").astype("float32").clip(0, 1)
        data[tech.replace("-", "_")] = da.rename(tech.replace("-", "_"))
    ds = xr.Dataset(data)
    ds.attrs.update(variant="calibrated_modern", classes=N, source="scripts_project/s4a_profiles.py (onwind S4B-3, others S4A pypsa_eur)", cutout="cutout-2013-era5 (Zenodo 10.5281/zenodo.20325289)",
                    snapshots="2013 3h means", onwind="ERA5 100 m wind x country alpha (WIND_CALIBRATION_ALPHA.csv alpha_main) + DEA 2050 turbine (6 MW, 165 m, hub 110 m)")
    out = OUT / f"profiles_calibrated_modern_c{N}_3h.nc"
    ds.to_netcdf(out, encoding={k: dict(zlib=True, complevel=6, dtype="float32") for k in ds.data_vars})
    cls_f = OUT / f"S4A_PROFILE_CLASSES_c{N}.csv"; cls = pd.read_csv(cls_f)
    cls = cls[~cls.variant.isin(["calibrated_modern", "gwa_check"])]
    new = pd.read_csv(on_src / "S4A_PROFILE_CLASSES.csv")
    other = cls[(cls.variant == "pypsa_eur") & (cls.tech != "onwind")].assign(variant="calibrated_modern")
    merged = pd.concat([cls, new[new.variant == "calibrated_modern"], other, new[new.variant == "gwa_check"]], ignore_index=True)
    merged.to_csv(cls_f, index=False)
    m = OUT / "MANIFEST.json"; man = json.loads(m.read_text()) if m.exists() else {}
    man[out.name] = dict(sha256=hashlib.sha256(out.read_bytes()).hexdigest(), bytes=out.stat().st_size, buses={k: int(v.sizes["bus"]) for k, v in ds.data_vars.items()})
    man[cls_f.name] = dict(sha256=hashlib.sha256(cls_f.read_bytes()).hexdigest(), rows=int(len(merged)))
    (OUT / f"S4B3_PROFILES_LOG_c{N}.json").write_text((on_src / "S4A_PROFILES_LOG.json").read_text())
    m.write_text(json.dumps(man, indent=1))
    print(out.name, man[out.name], "class rows", len(merged))


if __name__ == "__main__":
    main()
