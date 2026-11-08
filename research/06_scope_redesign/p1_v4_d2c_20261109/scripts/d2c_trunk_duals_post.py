"""V4 D2c section 4 (after the solves, read only): marginal value of the oil palm trunk pools (|Store-energy_balance| at the first snapshot) and their end-of-horizon
energy in the D2b and D2c 56-snapshot solves; solid-biomass bus prices (weighted mean) of the five trunk countries. Explains the small convexity excess (INFERENCE).
Writes evidence/D2C_TRUNK_DUALS_POST.json. Nothing is solved.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa
import xarray as xr

W = Path(__file__).resolve().parents[1]
RP = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
RUNS = {"F1": ("v4d2b/smoke56/v4d2b_F1", "v4d2c/smoke56/v4d2c_F1", "integrated"), "F2": ("v4d2b/smoke56/v4d2b_F2", "v4d2c/smoke56/v4d2c_F2", "no_new_xb")}


def trunk(d: Path, sc: str) -> dict:
    n = pypsa.Network(str(d / f"{sc}_SMOKE_TEST_ONLY_solved.nc"))
    D = xr.open_dataset(d / "DUALS_BY_CONSTRAINT.nc"); x = D["Store-energy_balance"]
    tdim = [k for k in x.dims if k.endswith("snapshot")][0]; cdim = [k for k in x.dims if not k.endswith("snapshot")][0]
    mv = pd.Series(np.abs(x.isel({tdim: 0}).transpose(cdim).values), index=[str(c) for c in x[cdim].values])
    w = n.snapshot_weightings.objective
    out = {}
    for s in [i for i in n.stores.index if " biomass oil_palm_trunk" in i]:
        bus = n.stores.at[s, "bus"]
        price = float((n.buses_t.marginal_price[bus] * w).sum() / w.sum()) if bus in n.buses_t.marginal_price.columns else None
        out[s] = dict(e_initial_mwh=float(n.stores.at[s, "e_initial"]), e_end_mwh=float(n.stores_t.e[s].iloc[-1]), marginal_value_eur_per_mwh=float(mv.get(s, np.nan)),
                      marginal_cost_eur_per_mwh=float(n.stores.at[s, "marginal_cost"]), bus=bus, bus_price_weighted_mean=price)
    D.close()
    return out


def main():
    res = {}
    for k, (b, c, sc) in RUNS.items():
        res[k] = dict(d2b=trunk(RP / b, sc), d2c=trunk(RP / c, sc))
        for s in res[k]["d2c"]:
            a, z = res[k]["d2b"][s], res[k]["d2c"][s]
            print(k, s, "| MV D2b", round(a["marginal_value_eur_per_mwh"], 3), "D2c", round(z["marginal_value_eur_per_mwh"], 3), "| e_end D2c", round(z["e_end_mwh"], 4),
                  "| bus price D2b", None if a["bus_price_weighted_mean"] is None else round(a["bus_price_weighted_mean"], 3), "D2c", None if z["bus_price_weighted_mean"] is None else round(z["bus_price_weighted_mean"], 3),
                  "| mc", round(z["marginal_cost_eur_per_mwh"], 4))
    (W / "evidence/D2C_TRUNK_DUALS_POST.json").write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
