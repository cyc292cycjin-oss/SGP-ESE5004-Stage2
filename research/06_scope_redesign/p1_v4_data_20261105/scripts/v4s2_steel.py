"""V4 S2 section 1 step 4 (decision 204 item 5): Indonesian steel - national total unchanged, spatial allocation by the facility method.

    PYTHONHASHSEED=0 python scripts/v4s2_steel.py          (WSL pypsa-earth python; read-only on the repository)

2019 stays on the UNSD iron-and-steel row (no change to the 2019 deduction, the 'other' bucket or T_v2). The 2050 national steel energy of v3
(output rule, worldsteel 2024 base) is distributed over nodes by 2024 facility activity: GEM plant production where reported (Krakatau Steel,
GRP West Java), capacity x u with u capped at 1 elsewhere (s1/ID_STEEL_FACILITIES.csv); the remaining national output (worldsteel 2024 minus the
GEM facilities, ~2.81 Mt) goes to the IMIP node in Central Sulawesi (main) or pro rata to the existing facilities (two sensitivities).
Power-source check: GIPT captive coal units in Central Sulawesi and their GEM type against the 2019 base of option (b) (s1/ID_CAPTIVE_UNITS_GIPT.csv).
Outputs s2/ID_STEEL_NODE_SHARES_S2.csv, s2/ID_STEEL_POWER_CHECK.csv, s2/_steel_evidence.json.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4s2_common as cm   # noqa: E402

DEXIN = "P100000120504"   # GEM GIST: PT Gunbuster Nickel / Dexin Steel Indonesia, IMIP Morowali (Central Sulawesi), BOF 7,000 kt, start 2020


def main():
    W = cm.WORK; out = W / "s2"; ev = cm.Ev("1.steel")
    S = pd.read_csv(W / "s1/ID_STEEL_FACILITIES.csv")
    op = S[S.operating_2024.eq("yes")].copy()
    ws24 = float(pd.read_csv(cm.REPO / "research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country").at["ID", "steel_base_mt"]) * 1e3   # kt (worldsteel 2024)
    fac = float(op.activity_capped_kt_2024.sum()); gap = ws24 - fac
    imip_node = S[S.gem_plant_id.eq(DEXIN)].node.iloc[0]
    prod_based = op.activity_basis_2024.str.startswith("GEM plant production")
    op["main_kt"] = op.activity_capped_kt_2024
    op["sens_a_kt"] = op.activity_capped_kt_2024 + (~prod_based) * gap * op.crude_cap_kt / float(op[~prod_based].crude_cap_kt.sum())   # = S1 (u = 1.19 on capacity-based lines)
    op["sens_b_kt"] = op.activity_capped_kt_2024 * ws24 / fac   # pro rata to all facility activity
    by = {k: op.groupby("node")[f"{k}_kt"].sum() for k in ("main", "sens_a", "sens_b")}
    by["main"] = by["main"].add(pd.Series({imip_node: gap}), fill_value=0.0)
    v3s = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_NODE_SHARES_V3.csv")
    v3st = v3s[(v3s.country == "ID") & (v3s.subsector == "steel")].set_index("node").share
    sub = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv")
    steel50 = float(sub[(sub.case == "main") & (sub.country == "ID") & (sub.subsector == "steel")].mwh_2050.sum()) / 1e6
    s1sh = op.groupby("node").activity_kt_2024.sum(); s1sh = s1sh / s1sh.sum()   # S1 facility shares (u = 1.19 uniform on capacity lines)
    N = pd.DataFrame({k: v / v.sum() for k, v in by.items()}).fillna(0.0)
    N = N.join(v3st.rename("v3_share"), how="outer").join(s1sh.rename("s1_share"), how="outer").fillna(0.0)
    N["main_minus_v3_pp"] = (N["main"] - N.v3_share) * 100; N["main_minus_s1_pp"] = (N["main"] - N.s1_share) * 100
    N["steel_2050_twh_main"] = N["main"] * steel50
    N.index.name = "node"; N.reset_index().to_csv(out / "ID_STEEL_NODE_SHARES_S2.csv", index=False, float_format="%.6f")
    ev.put("worldsteel_2024_kt", ws24, "kt", "INDUSTRY_OUTPUT_2050_M08B.csv steel_base_mt (worldsteel 2024)", "VERIFIED", "A")
    ev.put("facilities_capped_2024_kt", fac, "kt", "s1/ID_STEEL_FACILITIES.csv activity_capped_kt_2024 (u <= 1; plant production for KS and GRP)", "VERIFIED", "B")
    ev.put("gap_2024_kt", gap, "kt", "worldsteel 2024 - GEM facilities (u <= 1)", "INFERENCE", "C")
    ev.put("imip_node", imip_node, "-", f"node of GEM {DEXIN} (IMIP, Morowali, Central Sulawesi)", "VERIFIED", "B")
    ev.put("steel_2050_v3_twh", steel50, "TWh", "INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv main ID steel (unchanged)", "VERIFIED", "C")
    for n_, r in N.iterrows():
        for k in ("main", "sens_a", "sens_b", "v3_share", "s1_share"):
            if r[k] > 0:
                ev.put(f"share.{n_}.{k}", r[k], "-", "s2/ID_STEEL_NODE_SHARES_S2.csv", "PROPOSED (quantified)" if k in ("main", "sens_a", "sens_b") else "VERIFIED", "C")
    # ---- power-source check (decision 204 item 5): captive units in Central Sulawesi
    G = pd.read_csv(W / "s1/ID_CAPTIVE_UNITS_GIPT.csv")   # GIPT 'Subnational unit' is the island group only: select by distance to the Dexin plant (IMIP)
    d0 = S[S.gem_plant_id.eq(DEXIN)].iloc[0]
    G["km_to_dexin"] = 111.0 * np.hypot(G.Latitude - d0.lat, (G.Longitude - d0.lon) * np.cos(np.radians(d0.lat)))
    cs = G[G.km_to_dexin < 30].copy()
    cs["in_2019"] = cs.op_2019_yearend.astype(bool)
    keep = ["GEM unit/phase ID", "Plant / Project name", "Unit / Phase name", "Capacity (MW)", "Status", "Start year", "Captive Industry Type", "Captive Industry Use", "Owner(s)", "in_2019", "w_2019_avg", "group", "v3_subsector", "km_to_dexin"]
    cs.sort_values(["Start year", "Plant / Project name"])[keep].to_csv(out / "ID_STEEL_POWER_CHECK.csv", index=False, float_format="%.6g")
    ev.put("imip_captive_units_all", len(cs), "units", "GIPT 2026-09 captive coal units within 30 km of the Dexin plant (IMIP, all statuses)", "VERIFIED", "B")
    ev.put("imip_captive_mw_2019_yearend", float(cs.loc[cs.in_2019, "Capacity (MW)"].sum()), "MW", "GIPT, operating at the end of 2019 (Sulawesi Mining power station)", "VERIFIED", "B")
    ev.put("imip_captive_mw_2020_start", float(cs.loc[cs["Start year"].eq(2020), "Capacity (MW)"].sum()), "MW", "GIPT units starting 2020 (Dexin start year)", "VERIFIED", "B")
    for t, z in cs[cs.in_2019].groupby("Captive Industry Type"):
        ev.put(f"imip_captive_mw_2019.{t}", float(z["Capacity (MW)"].sum()), "MW", "GIPT Captive Industry Type", "VERIFIED", "B")
    ev.put("imip_captive_mw_steel_typed_all", float(cs[cs["Captive Industry Type"].astype(str).str.contains("steel")]["Capacity (MW)"].sum()), "MW", "GIPT units typed iron & steel near IMIP", "VERIFIED", "B")
    ev.put("dexin_start", str(S[S.gem_plant_id.eq(DEXIN)].line_start_date.iloc[0]), "-", "GEM GIST (start after 2019: not in the 2019 base of option b)", "VERIFIED", "B")
    ev.write(out / "_steel_evidence.json")
    pd.set_option("display.width", 250)
    print(N.round(4).to_string()); print("gap", gap, "imip", imip_node)
    print(cs[keep].to_string()[:6000])


if __name__ == "__main__":
    main()
