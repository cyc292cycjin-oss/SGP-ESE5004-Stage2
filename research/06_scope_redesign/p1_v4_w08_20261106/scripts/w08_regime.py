"""W08 section 5, data-chain check (post-solve, no solver): why the first-order estimate missed. Per country and solid-biomass pool class, the pool
energy (e_initial) in the v3.1 and v4 networks and the value of one more MWh in the pool (|dual of the first-snapshot energy balance|) in the v3.1
smoke and in the v4 smoke. A pool with dual 0 in v3.1 (slack) and > 0 in v4 (binding) is a regime change that a first-order estimate at the v3.1
point cannot see (its cost enters at zero); the convexity bracket (w08_bounds.py) prices it with the v4 duals.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w08_regime.py
Writes tables/W08_SMOKE56_POOL_REGIME.csv and evidence/W08_pool_regime.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pypsa
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from w08_bounds import PAIRS   # noqa: E402

W = Path(__file__).resolve().parents[1]


def duals(sdir: Path) -> dict:
    D = xr.open_dataset(sdir / "DUALS_BY_CONSTRAINT.nc"); eb = D["Store-energy_balance"]
    tdim = [x for x in eb.dims if x.endswith("snapshot")][0]; sdim = [x for x in eb.dims if not x.endswith("snapshot")][0]
    return {str(s): float(abs(v)) for s, v in zip(eb[sdim].values, eb.isel({tdim: 0}).transpose(sdim).values)}


def pools(n: pypsa.Network) -> pd.DataFrame:
    s = n.stores[n.stores.bus.str.startswith("solid biomass") & (n.stores.e_initial > 0)]
    return pd.DataFrame(dict(country=s.country, pool=s.carrier, e=s.e_initial))


def main():
    rows, ev = [], {}
    for pid, (pa, pb, s31, s4, sc) in PAIRS.items():
        A, B = pools(pypsa.Network(str(pa))), pools(pypsa.Network(str(pb)))
        da, db = duals(s31), duals(s4)
        A["dual"] = [da.get(i, float("nan")) for i in A.index]; B["dual"] = [db.get(i, float("nan")) for i in B.index]
        A["value"] = A.e * A.dual; B["value"] = B.e * B.dual
        ga = A.groupby(["country", "pool"]).agg(e=("e", "sum"), value=("value", "sum")); gb = B.groupby(["country", "pool"]).agg(e=("e", "sum"), value=("value", "sum"))
        g = ga.join(gb, how="outer", lsuffix="_v31", rsuffix="_v4").fillna(0.0).reset_index()
        g["dual_v31"] = g.value_v31 / g.e_v31.where(g.e_v31 > 0); g["dual_v4"] = g.value_v4 / g.e_v4.where(g.e_v4 > 0)
        g["delta_e_twh"] = (g.e_v4 - g.e_v31) / 1e6
        g.insert(0, "pair", pid)
        rows.append(g[["pair", "country", "pool", "e_v31", "e_v4", "delta_e_twh", "dual_v31", "dual_v4"]])
        c = g.groupby("country").agg(e_v31=("e_v31", "sum"), e_v4=("e_v4", "sum"), value_v31=("value_v31", "sum"), value_v4=("value_v4", "sum"))
        c["dual_v31"] = c.value_v31 / c.e_v31; c["dual_v4"] = c.value_v4 / c.e_v4.where(c.e_v4 > 0)
        ev[pid] = {k: dict(e_v31_twh=v.e_v31 / 1e6, e_v4_twh=v.e_v4 / 1e6, mean_dual_v31=v.dual_v31, mean_dual_v4=v.dual_v4) for k, v in c.iterrows()}
        print(pid); print(c.assign(e_v31=c.e_v31 / 1e6, e_v4=c.e_v4 / 1e6)[["e_v31", "e_v4", "dual_v31", "dual_v4"]].round(2).to_string(), flush=True)
    pd.concat(rows).to_csv(W / "tables/W08_SMOKE56_POOL_REGIME.csv", index=False, float_format="%.6g", lineterminator="\n")
    (W / "evidence/W08_pool_regime.json").write_text(json.dumps(dict(status="VERIFIED duals and pool sizes; INFERENCE reading", method=__doc__, pairs=ev),
                                                                 indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
