"""W08 section 5, data-chain check (post-solve, no solver): mean marginal price (weighted by snapshot weight, first 56 snapshots) of the industry heat
buses per country and band in the v3.1 smoke and the v4 smokes, with the annual band demand of each network. Explains the load term of the
first-order estimate (v3.1 prices) against the upper bound (v4 prices).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w08_heat_prices.py
Writes tables/W08_SMOKE56_HEAT_PRICES.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pypsa

sys.path.insert(0, str(Path(__file__).resolve().parent))
from w08_first_order import N, pset   # noqa: E402
from w08_bounds import PAIRS          # noqa: E402

W = Path(__file__).resolve().parents[1]
BANDS = ["industry heat medium A", "industry heat medium B", "industry heat high", "industry heat"]


def table(net: pypsa.Network, solved: pypsa.Network, tag: str) -> pd.DataFrame:
    sn = solved.snapshots[:N]; w = solved.snapshot_weightings.objective.loc[sn]; lam = solved.buses_t.marginal_price.loc[sn]
    P = pset(net, net.snapshots[:N]); P.index = sn
    rows = []
    for b in BANDS:
        for c in sorted(net.buses.country.dropna().unique()):
            buses = [x for x in net.buses.index[(net.buses.country == c) & (net.buses.carrier == b)] if x in lam.columns]
            if not buses:
                continue
            loads = net.loads.index[net.loads.bus.isin(buses)]
            mwh = float((P[loads].sum(axis=1) * w).sum()) if len(loads) else 0.0
            price = float((lam[buses].mean(axis=1) * w).sum() / w.sum())
            rows.append(dict(run=tag, band=b, country=c, demand_twh=mwh / 1e6, mean_price=price))
    return pd.DataFrame(rows)


def main():
    out = []
    for pid, (pa, pb, s31, s4, sc) in PAIRS.items():
        if pid == "v4_F1" or pid == "v4iid_F1":
            if not out:
                out.append(table(pypsa.Network(str(pa)), pypsa.Network(str(s31 / f"{sc}_SMOKE_TEST_ONLY_solved.nc")), "v31_F1"))
            out.append(table(pypsa.Network(str(pb)), pypsa.Network(str(s4 / f"{sc}_SMOKE_TEST_ONLY_solved.nc")), pid))
    t = pd.concat(out)
    p = t.pivot_table(index=["band", "country"], columns="run", values=["demand_twh", "mean_price"])
    p.columns = [f"{a}_{b}" for a, b in p.columns]
    p = p.reset_index(); p.to_csv(W / "tables/W08_SMOKE56_HEAT_PRICES.csv", index=False, float_format="%.6g", lineterminator="\n")
    print(p.round(2).to_string())


if __name__ == "__main__":
    main()
