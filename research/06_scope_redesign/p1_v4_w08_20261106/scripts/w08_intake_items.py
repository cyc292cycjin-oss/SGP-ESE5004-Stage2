"""W08 checklist sections 5-7: input tables of the v4 products from the W07 session deliverables (read only), through the reference code
(scripts/ref/i2_items.py load_sessions / pp_tables / hvc_items / methanol_items / other_items; the same objects the reference engine used).
Every value is written with repr (exact), with its source; the derivations from these physical inputs are in scripts_project/v4_products.py.

    W08_REF_SCRATCH=/home/jin/v4w08/ref_main PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w08_intake_items.py

Writes into the W08 worktree research_inputs/industry_v4/: CAPTIVE_COAL_2019.csv, CEMENT_USGS_2019.csv, PULP_PAPER_FAOSTAT_V4.csv, HVC_PLANTS_V4.csv,
METHANOL_PLANTS_V4.csv, PRODUCT_DERIVED_INPUTS_V4.csv (glass, alumina, copper, lime; MY methanol plants: G1 derived energy), MY_AMMONIA_FUEL_DUPLICATE.csv,
VN_HYBRID_ELECTRICITY_ROWS.csv.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent / "ref"))
import i2_common as cm   # noqa: E402
import i2_items as IT    # noqa: E402

OUT = Path("/home/jin/wt_v4_w08/research_inputs/industry_v4")
W07 = "work/p1_v4_w07_20261106"
CARS = list(cm.OUTC)


def r(x):
    return repr(float(x))


def vcols(v: dict) -> dict:
    return {f"v2050_{k}_mwh": r(v.get(k, 0.0)) for k in CARS}


def main():
    S = IT.load_sessions()
    # ---- 1. captive coal (decision 204 items 1-2, 208; option (b), reading I) ------------------------------------------------------
    cap = pd.read_csv(cm.S2D / "s1/ID_CAPTIVE_COAL_2019.csv"); tot = cap[cap.group == "合计"].set_index("level")
    rows = [dict(country="ID", item="captive coal central (S1 method; decision 204, G0)", level="central", coal_row="other", coal_kt=r(tot.at["central", "coal_in_industry_kt"]),
                 gj_per_t="20.29", electricity_row="other", e_gwh=r(tot.at["central", "gen_in_industry_gwh"]), e_mwh="", option="b",
                 source="work/p1_v4_data_20261105/s1/ID_CAPTIVE_COAL_2019.csv group 合计 central (coal_in_industry_kt, gen_in_industry_gwh); NCV decision 207 / 210 item 1", grade="C")]
    mm = S["g4_ci"]["captive_MM"]["low"]
    rows.append(dict(country="MM", item="captive coal low (cement kilns; G4)", level="low", coal_row=IT.NMM, coal_kt=r(mm["C_kt"]), gj_per_t="23.26", electricity_row="other",
                     e_gwh="", e_mwh=r(mm["E_mwh"]), option="b", source=f"{W07}/G4/evidence/_chain_inputs.json captive_MM.low (C_kt, E_mwh); NCV SDMX 23.26", grade="C"))
    for it in S["g3_cap"]["PH"]["levels"]["central"]:
        rows.append(dict(country="PH", item=f"captive coal {it['row']} ({'b' if it['electricity_added'] else 'b-prime, no electricity added'}; G3)", level="central", coal_row=it["row"],
                         coal_kt=r(it["coal_kt"]), gj_per_t="22.058", electricity_row=(it["row"] if it["electricity_added"] else ""),
                         e_gwh=(r(it["E_gwh"]) if it["electricity_added"] else ""), e_mwh="", option=("b" if it["electricity_added"] else "b'"),
                         source=f"{W07}/G3/tables/_captive_inputs.json PH.levels.central; NCV SDMX 22.058", grade="C"))
    for cc in ("TH", "VN", "MY", "BN", "KH", "LA", "SG", "TL"):
        rows.append(dict(country=cc, item="no captive coal moved (S2 section 5 screening / W07 sessions)", level="", coal_row="", coal_kt="0.0", gj_per_t="", electricity_row="",
                         e_gwh="", e_mwh="", option="", source="W07 G1-G4 country sessions: 0", grade="C"))
    pd.DataFrame(rows).to_csv(OUT / "CAPTIVE_COAL_2019.csv", index=False, lineterminator="\n")
    # ---- 2. cement (ii): USGS 2019 cement tonnes; BN (iii) EDGAR 2.A.1 = 0 -------------------------------------------------------------
    pd.DataFrame([dict(country=c, cement_2019_t=r(t), edgar_2a1_zero=(c == "BN"), source="USGS Minerals Yearbook cement 2019 (S2 / G0 / G1-G4 tables; decision 210 item 5 / I2 S5b)",
                       grade="B") for c, t in IT.CEMENT_USGS_2019_T.items()]).to_csv(OUT / "CEMENT_USGS_2019.csv", index=False, lineterminator="\n")
    # ---- 3. pulp and paper FAOSTAT leaf items (one table for the seven producing countries) -------------------------------------------
    src = {"ID": "work/p1_v4_data_20261105/s2/ID_PULP_PAPER_FAOSTAT.csv", "MY": f"{W07}/G1/tables/MY_PULP_PAPER_FAOSTAT.csv", "VN": f"{W07}/G2/tables/VN_PULP_PAPER_FAOSTAT.csv",
           "TH": f"{W07}/G3/tables/TH_PULP_PAPER_FAOSTAT.csv", "PH": f"{W07}/G3/tables/PH_PULP_PAPER_FAOSTAT.csv", "MM": f"{W07}/G4/evidence/PULP_PAPER_FAOSTAT_G4.csv",
           "LA": f"{W07}/G4/evidence/PULP_PAPER_FAOSTAT_G4.csv"}
    pp = []
    for cc, T in IT.pp_tables().items():
        q50 = "q_2050_main_t" if "q_2050_main_t" in T.columns else "q_2050_t"
        for x in T.to_dict("records"):
            q19 = pd.to_numeric(pd.Series([x["q_2019_t"]]), errors="coerce").fillna(0.0).iloc[0]; q5 = pd.to_numeric(pd.Series([x[q50]]), errors="coerce").fillna(0.0).iloc[0]
            pp.append(dict(country=cc, group=x["group"], item=x["item"], q_2019_t=r(q19), q_2050_t=r(q5), source=src[cc] + f" ({q50})", grade="A/B (FAOSTAT; 2050 by the session growth rule)"))
    pd.DataFrame(pp).to_csv(OUT / "PULP_PAPER_FAOSTAT_V4.csv", index=False, lineterminator="\n")
    # ---- 4. HVC plants -------------------------------------------------------------------------------------------------------------------------
    H = IT.hvc_items(S, "i2")
    pd.DataFrame([dict(country=cc, hvc19_t=r(h["hvc19_t"]), hvc50_base_t=r(h["hvc50_base_t"]), hvc50_new_t=r(h["hvc50_new_t"]), row=(h["row"] or ""),
                       fuel_split=(json.dumps(h["fuel_split"]) if h["fuel_split"] else ""), source=h["src"], grade="C") for cc, h in H.items()]).to_csv(OUT / "HVC_PLANTS_V4.csv", index=False, lineterminator="\n")
    # ---- 5. methanol plants (decision 210 item 7) -----------------------------------------------------------------------------------------
    M = IT.methanol_items(S)
    mrows = [dict(country="MY", plant="Labuan (Petronas Methanol Labuan)", status="existing", capacity_kt="2330.0", utilisation="0.85", base_year=2019, row="", spill=True,
                  derivation="derived (G1)", source=M["MY"]["src"] + f"; {W07}/G1/tables/_products_evidence.json products.chem.methanol.central.*; chain_inputs chem_2050.central.methanol"),
             dict(country="ID", plant="Kaltim Methanol Industri", status="existing", capacity_kt="660.0", utilisation="0.85", base_year=2019, row=IT.CHEM, spill=True,
                  derivation="capacity x utilisation x intensity", source=M["ID"]["src"]),
             dict(country="BN", plant="Brunei Methanol Company", status="existing", capacity_kt="850.0", utilisation="0.85", base_year=2019, row="", spill=False,
                  derivation="capacity x utilisation x intensity; 2019 fuel in UNSD non-energy use (no industry deduction; NEU gas lowered by the same energy use)", source=M["BN"]["src"]),
             dict(country="MY", plant="Sarawak Petchem (Bintulu)", status="new", capacity_kt="1750.0", utilisation="", base_year=2023, row="", spill=True,
                  derivation="derived (G1)", source=M["MY_new"]["src"] + f"; {W07}/G1/tables/_products_evidence.json chain_inputs chem_2050_r4.sarawak_petchem_2023")]
    pd.DataFrame(mrows).to_csv(OUT / "METHANOL_PLANTS_V4.csv", index=False, lineterminator="\n")
    # ---- 6. derived inputs (energy values computed by the sessions; grade C) -----------------------------------------------------------------
    O = IT.other_items(S)
    der = []
    for grp in ("glass", "alumina", "copper", "lime"):
        for cc, it in O[grp].items():
            der.append(dict(step="S6b", country=cc, name=it["name"], row=(it["row"] or ""), fuel19_mwh=r(it["fuel19"]), el19_mwh=r(it["el19"]), **vcols(it["v2050"]),
                            source={"glass": {"VN": f"{W07}/G2/evidence/_chain_inputs.json glass_2019 / glass_2050"}.get(cc, f"{W07}/G3/tables/_products_inputs.json {cc}.glass"),
                                    "alumina": f"{W07}/G2/evidence/_chain_inputs.json alumina_2019 / alumina_2050", "copper": f"{W07}/G4/evidence/_chain_inputs.json products.{cc}_copper",
                                    "lime": f"{W07}/G1/tables/_products_evidence.json chain_inputs lime_2019 / lime_2050"}[grp] if grp != "glass" or cc == "VN" else f"{W07}/G3/tables/_products_inputs.json {cc}.glass",
                            grade="C"))
    der.append(dict(step="S5f", country="MY", name="methanol", row="", fuel19_mwh=r(M["MY"]["fuel19"]), el19_mwh=r(M["MY"]["el19"]), **vcols(M["MY"]["v2050"]),
                    source=mrows[0]["source"], grade="C"))
    der.append(dict(step="S5g", country="MY", name="methanol_new_plants", row="", fuel19_mwh="0.0", el19_mwh="0.0", **vcols(M["MY_new"]["v2050"]), source=mrows[3]["source"], grade="C"))
    pd.DataFrame(der).to_csv(OUT / "PRODUCT_DERIVED_INPUTS_V4.csv", index=False, lineterminator="\n")
    pd.DataFrame([dict(country=m[0], sub=m[1], carrier=m[2], mwh_2019=r(m[3]), level="mid", source=f"{W07}/G1/tables/_products_evidence.json chain_inputs chem_moves_2019.central.ammonia", grade="C")
                  for m in O["my_ammonia_dup"]]).to_csv(OUT / "MY_AMMONIA_FUEL_DUPLICATE.csv", index=False, lineterminator="\n")
    pd.DataFrame([dict(country="VN", sub=k, carrier="electricity", mwh_2019=r(v), source=f"{W07}/G2/evidence/_unsd_evidence.json unsd.el_row_2019_backcast.*", grade="C")
                  for k, v in S["vn_el_rows"].items()]).to_csv(OUT / "VN_HYBRID_ELECTRICITY_ROWS.csv", index=False, lineterminator="\n")
    print("written", sorted(p.name for p in OUT.glob("*.csv")))


if __name__ == "__main__":
    main()
