"""W12-2 (b): first-order cost effect of removing the duplicated rail parent from the EV loads (fix variant a), per solved run.

EV loads are constant p_set on '<node> EV battery' buses; dC/dp = sum_t lambda_t w_t (buses_t_marginal_price x snapshots_objective),
so removing dE MWh/a of constant load changes the cost by about -dE x (sum_t lambda_t w_t / sum_t w_t) (first order; for a load
DEcrease the true saving is at most this, by convexity). B6 = no_new_xb - integrated. Owen: the load row belongs to the load's country,
so with duals fixed the country's share changes by the same amount. Reads tables/W12_2_NETWORK_RAIL_EV_LOADS.csv for the parent
fraction. Nothing is solved.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w12_common as cm  # noqa: E402

RUNS = ["S56_F1", "S56_F2", "SCR_V1", "SCR_V2", "S07_V1", "S07_V2"]


def main():
    ev = cm.Evidence("W12_2b")
    net = pd.read_csv(cm.TABLES / "W12_2_NETWORK_RAIL_EV_LOADS.csv")
    frac = net[net.network.str.contains("integrated_2920_3h")].set_index("country").parent_fraction_of_land.to_dict()
    rows = []
    for run in RUNS:
        folder, scen, res, ver = cm.SOLVED[run]
        ds = xr.open_dataset(cm.solved_nc(folder))
        try:
            li = [str(x) for x in ds["loads_i"].values]
            acc = pd.Series([str(x) for x in ds["loads_account"].values], index=li)
            cty = pd.Series([str(x) for x in ds["loads_country"].values], index=li)
            bus = pd.Series([str(x) for x in ds["loads_bus"].values], index=li)
            ps = pd.Series(ds["loads_p_set"].values.astype(float), index=li)
            w = ds["snapshots_objective"].values.astype(float)
            bi = [str(x) for x in ds["buses_t_marginal_price_i"].values]; bidx = {b: i for i, b in enumerate(bi)}
            mp = ds["buses_t_marginal_price"].values
            for c, f in frac.items():
                if f <= 0:
                    continue
                evl = acc.index[(acc == "LandTransportEV") & (cty == c)]
                dE = 0.0; dC = 0.0
                for l in evl:
                    e = float(ps[l]) * float(w.sum()) * f
                    lam = float((mp[:, bidx[bus[l]]] * w).sum() / w.sum())
                    dE += e; dC += e * lam
                rows.append(dict(run=run, scenario=scen, resolution=res, model=ver, country=c, ev_parent_mwh=dE, weighted_price_eur_per_mwh=(dC / dE if dE else None),
                                 first_order_saving_eur=dC))
        finally:
            ds.close()
    R = pd.DataFrame(rows)
    cm.write_csv(R.to_dict("records"), cm.TABLES / "W12_2_EV_PARENT_FIRST_ORDER_BY_RUN.csv")
    pairs = [("S56", "S56_F2", "S56_F1"), ("SCR", "SCR_V2", "SCR_V1"), ("S07", "S07_V2", "S07_V1")]
    out = []
    for name, a, b in pairs:
        A = R[R.run == a].set_index("country"); B = R[R.run == b].set_index("country")
        for c in A.index:
            # removing the load lowers both costs; dB6 = -(saving_no_new_xb - saving_integrated)
            out.append(dict(pair=name, country=c, saving_no_new_xb_eur=float(A.at[c, "first_order_saving_eur"]), saving_integrated_eur=float(B.at[c, "first_order_saving_eur"]),
                            price_no_new_xb=float(A.at[c, "weighted_price_eur_per_mwh"]), price_integrated=float(B.at[c, "weighted_price_eur_per_mwh"]),
                            dB6_first_order_eur=-(float(A.at[c, "first_order_saving_eur"]) - float(B.at[c, "first_order_saving_eur"]))))
        out.append(dict(pair=name, country="ALL", saving_no_new_xb_eur=float(A.first_order_saving_eur.sum()), saving_integrated_eur=float(B.first_order_saving_eur.sum()),
                        dB6_first_order_eur=-(float(A.first_order_saving_eur.sum()) - float(B.first_order_saving_eur.sum()))))
    cm.write_csv(out, cm.TABLES / "W12_2_EV_PARENT_B6_FIRST_ORDER.csv")
    for r in out:
        ev.add(f"{r['pair']}.{r['country']}.dB6_first_order_eur", r["dB6_first_order_eur"], "EUR2020/a", "INFERENCE", "C", "W12_2_EV_PARENT_B6_FIRST_ORDER.csv",
               "-(saving no_new_xb - saving integrated); saving = parent EV MWh x weighted EV-battery-bus price")
    for r in rows:
        ev.add(f"{r['run']}.{r['country']}.weighted_price", r["weighted_price_eur_per_mwh"], "EUR2020/MWh", "VERIFIED", "A", f"{r['run']} buses_t_marginal_price x snapshots_objective")
    p = ev.write()
    pd.set_option("display.width", 220)
    print(R.to_string()); print(pd.DataFrame(out).to_string()); print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
