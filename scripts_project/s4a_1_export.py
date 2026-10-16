"""S4A-1: export the rebuilt profiles (scripts_project/s4a_profiles.py outputs) to research_inputs/renewable_v5 as compact
NetCDF (float32, zlib) on the 2013 3 h snapshots, one variable per technology, bus coordinate "node|class".

    python scripts_project/s4a_1_export.py --source results_project/s4a/profiles_full_c1 --classes 1
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_inputs/renewable_v5"
TECHS = ["onwind", "offwind-ac", "offwind-dc", "solar"]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--source", type=Path, required=True); ap.add_argument("--classes", type=int, required=True); ap.add_argument("--variants", nargs="+", default=["fork", "pypsa_eur"])
    a = ap.parse_args(); OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for var in a.variants:
        data = {}
        for tech in TECHS:
            da = xr.open_dataarray(a.source / f"profile_{tech}_{var}_c{a.classes}_3h.nc")
            da = da.transpose("time", "bus").astype("float32").clip(0, 1)
            data[tech.replace("-", "_")] = da.rename(tech.replace("-", "_"))
        # buses differ per tech -> align on the union with NaN for absent, keep separate variables
        ds = xr.Dataset({k: v for k, v in data.items()})
        ds.attrs.update(variant=var, classes=a.classes, source="scripts_project/s4a_profiles.py", cutout="cutout-2013-era5 (Zenodo 10.5281/zenodo.20325289)", snapshots="2013 3h means")
        f = OUT / f"profiles_{var}_c{a.classes}_3h.nc"
        enc = {k: dict(zlib=True, complevel=6, dtype="float32") for k in ds.data_vars}
        ds.to_netcdf(f, encoding=enc)
        manifest[f.name] = dict(sha256=hashlib.sha256(f.read_bytes()).hexdigest(), bytes=f.stat().st_size, buses={k: int(v.sizes["bus"]) for k, v in ds.data_vars.items()})
    shutil.copy(a.source / "S4A_PROFILE_CLASSES.csv", OUT / f"S4A_PROFILE_CLASSES_c{a.classes}.csv")
    shutil.copy(a.source / "S4A_PROFILES_LOG.json", OUT / f"S4A_PROFILES_LOG_c{a.classes}.json")
    for k in ["regions_onshore.geojson", "regions_offshore.geojson"]:
        if (a.source / k).exists():
            shutil.copy(a.source / k, OUT / k)
    m = OUT / "MANIFEST.json"; old = json.loads(m.read_text()) if m.exists() else {}
    old.update(manifest); m.write_text(json.dumps(old, indent=1))
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
