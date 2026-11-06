"""Fable W08 review, dimension 9: S7 checkpoints reproduced in the clean copy against REFERENCE_V4_MAIN.csv / REFERENCE_V4_IID.csv (per country,
T_v2, other, carriers, overflow, cap), tolerance 1e-6 TWh. usage: s7_compare.py <cp_ras/step_S7.json> <cp_iid/step_S7.json> <w08 dir> <OUT.json>"""
import json
import sys
from pathlib import Path

import pandas as pd

ras, iid, W08, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
CARS = {"electricity": "T_elec", "heat": "T_heat_lt150", "heat_medium_a": "T_heat_150_200", "heat_medium_b": "T_heat_200_400", "heat_high": "T_heat_gt400", "oil": "T_oil", "gas": "T_gas",
        "coal": "T_coal", "biomass": "T_biomass", "hydrogen": "T_H2", "ammonia": "T_ammonia", "methanol": "T_methanol"}
out = {}
for label, p, ref in (("main", ras, "REFERENCE_V4_MAIN.csv"), ("iid", iid, "REFERENCE_V4_IID.csv")):
    a = json.loads(p.read_text()); R = pd.read_csv(W08 / ref); R = R[R.step == "S7"].set_index("country")
    rows = []
    for c, x in a["countries"].items():
        r = R.loc[c]
        dc = {k: x["T_car"].get(k, 0.0) / 1e6 - float(r[v]) for k, v in CARS.items()}
        do = {k: x["other_car"].get(k, 0.0) / 1e6 - float(r[v.replace("T_", "other_")]) for k, v in CARS.items()}
        rows.append(dict(country=c, T_repro=x["T"] / 1e6, T_ref=float(r.T_v2_2050_TWh), dT=x["T"] / 1e6 - float(r.T_v2_2050_TWh), other_repro=x["other"] / 1e6, other_ref=float(r.other_2050_TWh),
                         d_other=x["other"] / 1e6 - float(r.other_2050_TWh), max_dcar=max(abs(v) for v in dc.values()), max_dcar_other=max(abs(v) for v in do.values()),
                         d_overflow=x["overflow"] / 1e6 - float(r.biomass_overflow_TWh), d_cap=x["pot"] / 1e6 - float(r.solid_potential_cap_TWh),
                         d_land=a["ats_sectors"][c]["land"] / 1e6 - float(r.land_fuel_2050_TWh), d_ev=a["ats_sectors"][c]["ev"] / 1e6 - float(r.ev_electricity_2050_TWh)))
    df = pd.DataFrame(rows)
    tot = sum(x["T"] for x in a["countries"].values()) / 1e6
    out[label] = dict(rows=rows, asean_repro=tot, asean_ref=float(R.at["ASEAN11", "T_v2_2050_TWh"]), max_abs=float(df[["dT", "d_other", "max_dcar", "max_dcar_other", "d_overflow", "d_cap", "d_land", "d_ev"]].abs().max().max()),
                      all_within_1e6=bool((df[["dT", "d_other", "max_dcar", "max_dcar_other", "d_overflow", "d_cap", "d_land", "d_ev"]].abs() <= 1e-6).all().all()))
    pd.set_option("display.width", 250); print(label, "ASEAN repro", round(tot, 9), "ref", out[label]["asean_ref"], "max |diff| TWh", out[label]["max_abs"], "all within 1e-6:", out[label]["all_within_1e6"])
    print(df.round(9).to_string())
json.dump(out, open(OUT, "w"), indent=1, default=float)
