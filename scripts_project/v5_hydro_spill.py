"""V5 X20 revision 1-5 (decision 241): hydro spill report of a solved network file - bookkeeping part of the new-build reservoirs (the inflow of the
unbuilt part, forced into spill by research_new_hydro_inflow) and the true spill (v5_layers.hydro_spill_tables; X03 section 5.4 definitions).
Reads only the static storage-unit columns, the bus countries, the snapshot weights and storage_units_t inflow / spill (whole variables, no fancy
indexing over 9p). Regression: the v4 W14 2920x3h solved networks give F1 527.0 / 519.9 / 7.1 and F2 528.9 / 521.5 / 7.4 TWh (reported / bookkeeping
/ true, X03 [VERIFIED]).

    PYTHONHASHSEED=0 python scripts_project/v5_hydro_spill.py --network <solved .nc> --output HYDRO_SPILL.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from v5_layers import hydro_spill_tables


def read(nc: Path):
    ds = xr.open_dataset(nc)
    su = pd.DataFrame({k: ds[f"storage_units_{k}"].values for k in ("carrier", "bus", "p_nom_opt", "p_nom_max")}, index=ds["storage_units_i"].values.astype(str))
    su["carrier"] = su.carrier.astype(str); su["bus"] = su.bus.astype(str)
    country = pd.Series(ds["buses_country"].values.astype(str), index=ds["buses_i"].values.astype(str))
    wk = "snapshots_generators" if "snapshots_generators" in ds else "snapshot_weightings_generators"
    w = ds[wk].values.astype(float)

    def ts(a):
        v = f"storage_units_t_{a}"
        if v not in ds:
            return pd.DataFrame(index=range(len(w)))
        return pd.DataFrame(ds[v].values, columns=ds[f"{v}_i"].values.astype(str))
    inflow, spill = ts("inflow"), ts("spill")
    ds.close()
    return su, inflow, spill, w, su.bus.map(country)


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--output", type=Path, required=True); a = ap.parse_args(argv)
    su, inflow, spill, w, cty = read(a.network)
    rep = hydro_spill_tables(su, inflow, spill, w, cty)
    rep["network"] = str(a.network)
    a.output.write_text(json.dumps(rep, indent=1, default=float) + "\n")
    t = rep["totals"]
    print(json.dumps({k: round(v, 3) for k, v in t.items()}), "all reported", round(rep["all_reported_spill_twh"], 3))


if __name__ == "__main__":
    main()
