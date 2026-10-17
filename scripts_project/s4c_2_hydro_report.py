"""S4C-2 report tables (user decision 2026-10-17 item 4): per country the author-base inflow, before / after the S4A/S4B additions, after the
correction (option B main, option A sensitivity) with the equivalent capacity factors; the eliminated anomalous units (CF > 1 before).

Inputs are the diagnosis tables of scripts_project/s4c_2_hydro_diagnosis.py run on the frozen_base, main (B) and runoff-shares (A) builds.

    python scripts_project/s4c_2_hydro_report.py --before <diag_frozen_base> --main <diag_integrated> --runoff <diag_runoff_shares> --output <dir>
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    for k in ("before", "main", "runoff", "output"):
        ap.add_argument("--" + k, type=Path, required=True)
    a = ap.parse_args()
    d0 = pd.read_csv(a.before / "HYDRO_INFLOW_DIAGNOSIS_S4C2.csv").set_index("country")
    dB = pd.read_csv(a.main / "HYDRO_INFLOW_DIAGNOSIS_S4C2.csv").set_index("country")
    dA = pd.read_csv(a.runoff / "HYDRO_INFLOW_DIAGNOSIS_S4C2.csv").set_index("country")
    rows = []
    for c in d0.index:
        r0 = d0.loc[c]
        if r0.build_mw == 0:
            continue
        rows.append(dict(country=c, base_mw=r0.base_reservoir_mw + r0.base_ror_mw, base_inflow_twh=r0.base_inflow_twh, base_cf=r0.base_cf,
                         added_mw=r0.added_reservoir_mw + r0.added_ror_mw, added_inflow_twh_before=r0.added_inflow_twh,
                         stock_mw=r0.build_mw, inflow_before_correction_twh=r0.build_inflow_twh, cf_before_correction=r0.build_cf,
                         target_twh=r0.ember_gen_median_twh * 1.1, ember_median_twh=r0.ember_gen_median_twh,
                         inflow_main_B_twh=dB.loc[c, "build_inflow_twh"], cf_main_B=dB.loc[c, "build_cf"],
                         inflow_A_runoff_shares_twh=dA.loc[c, "build_inflow_twh"], cf_A=dA.loc[c, "build_cf"],
                         change_B_vs_before=dB.loc[c, "build_inflow_twh"] / r0.build_inflow_twh - 1, ror_clip_loss_twh=r0.ember_gen_median_twh * 1.1 - dB.loc[c, "build_inflow_twh"]))
    t = pd.DataFrame(rows)
    c0 = pd.read_csv(a.before / "HYDRO_STOCK_COMPONENTS_S4C2.csv"); cB = pd.read_csv(a.main / "HYDRO_STOCK_COMPONENTS_S4C2.csv").set_index("name")
    cA = pd.read_csv(a.runoff / "HYDRO_STOCK_COMPONENTS_S4C2.csv").set_index("name")
    c0["cf_before"] = c0.annual_inflow_mwh / (c0.p_nom * 8760)
    an = c0[c0.cf_before > 1].copy()
    an["cf_main_B"] = [float(cB.at[x, "annual_inflow_mwh"] / (cB.at[x, "p_nom"] * 8760)) for x in an.name]
    an["cf_A"] = [float(cA.at[x, "annual_inflow_mwh"] / (cA.at[x, "p_nom"] * 8760)) for x in an.name]
    an = an[["country", "node", "name", "kind", "origin", "p_nom", "annual_inflow_mwh", "cf_before", "cf_main_B", "cf_A"]].sort_values("cf_before", ascending=False)
    a.output.mkdir(parents=True, exist_ok=True)
    t.to_csv(a.output / "HYDRO_INFLOW_CORRECTION_S4C2_BY_COUNTRY.csv", index=False); an.to_csv(a.output / "HYDRO_ANOMALOUS_UNITS_S4C2.csv", index=False)
    pd.set_option("display.width", 260)
    print(t.round(3).to_string()); print(an.round(3).to_string())
    print("totals: base", round(t.base_inflow_twh.sum(), 2), "before", round(t.inflow_before_correction_twh.sum(), 2), "target", round(t.target_twh.sum(), 2), "B", round(t.inflow_main_B_twh.sum(), 2), "A", round(t.inflow_A_runoff_shares_twh.sum(), 2))


if __name__ == "__main__":
    main()
