"""I2 section 2 item 5: the key numbers of I1 and G0-G4 are reproduced by the I2 engine under the same settings (before any I2 rule is used).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i2_repro.py

R1  I1: anchor variants I / IIa / IId on the I1 base cases S5, S5x (repository cache) and S5c, S5xc (I1's SDMX caches, committed in
    I1/BASE2019_SDMX/INDUSTRY_CACHE_SDMX_2019*.json); I1 inputs: /home/jin/v4i1/d1_base_S0.csv, d1_base_S5.csv (I1 scratch, read only).
    Reference: I1/tables/I1_CHAIN_RESULTS.csv, T_v2 by country.
R2  G3 (TH, PH, SG), v3 NCV line, all steps (captive central, cement ii, pulp capped at the paper row, ethylene main|central, glass, bagasse
    closed loop) - reference G3/tables/<CC>_COMBINED.csv scenario 'v3:8'.
R3  G4 (MM, KH, LA, BN), v3 NCV line, step 4 (captive low, cement ii / BN iii, products with G4's rule: fuel from the row by its fuel mix, the
    rest from 'other', electricity from 'other') - reference G4/evidence/G4_SCENARIOS.csv.
R4  G1 (MY), v3 sequence step 10 - reference G1/tables/MY_CHAIN_SCENARIOS.csv.
R5  G0 (ID), v3 NCV, nickel Case 3 path, step 8 - reference G0/ID_OTHER_SHARE_STEPS.csv (path alt_ni_case3, ncv v3, step 8).
R6  G2 (VN), v3 NCV line, step 1 (hybrid split as decomposition matrix, v3 two-run rule) - reference G2/tables/VN_STEPS_LONG.csv.
Writes tables/I2_REPRODUCTION.csv and evidence/I2_repro.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i2_common as cm   # noqa: E402
import i2_engine as E    # noqa: E402
import i2_items as IT    # noqa: E402
from i2_chain import KEY, d1_series   # noqa: E402

I1W = Path("/home/jin/v4i1")


def tv2(r, cc):
    return r["snap"][cc]["T"] / 1e6


def main():
    ev = cm.Evidence("I2_repro"); rows = []
    eng = E.Engine(); eng.reproduce()
    # ------------------------------------------------------------------------------------------------------------------------------ R1 I1
    ref = pd.read_csv(cm.G["I1"] / "tables/I1_CHAIN_RESULTS.csv")
    S0 = d1_series(I1W / "d1_base_S0.csv"); S5 = d1_series(I1W / "d1_base_S5.csv")
    P = pd.read_csv(cm.G["I1"] / "BASE2019_SDMX/BASE2019_SDMX_COMMODITY_BY_STEP.csv")
    v5150 = P[(P.account == "IndustryFinalEnergy") & (P.commodity == "other vegetal material and residues")].set_index("country")
    S5x = S5.copy()
    for c, r in v5150.iterrows():
        k = (c, "Industry", "biomass", "IndustryFinalEnergy"); S5x[k] = S5x[k] - float(r["S5"])
    cs = json.loads((cm.G["I1"] / "BASE2019_SDMX/INDUSTRY_CACHE_SDMX_2019.json").read_text())
    cx = json.loads((cm.G["I1"] / "BASE2019_SDMX/INDUSTRY_CACHE_SDMX_2019_WITHOUT_5150.json").read_text())
    for mode, am in (("I", "I"), ("IIa", "ras"), ("IId", "fixedcol")):
        for case, d1, cache in (("S5", S5, None), ("S5x", S5x, None), ("S5c", S5, cs), ("S5xc", S5x, cx)):
            r = eng.run(dict(d1=d1, d1_s0=S0, anchor_mode=am, cache=cache))
            for cc in cm.ASEAN:
                x = ref[(ref["mode"] == mode) & (ref.case == case) & (ref.country == cc)]
                rows.append(dict(check=f"R1 I1 {mode} {case}", country=cc, i2=tv2(r, cc), reference=float(x.T_v2_twh.iloc[0]), quantity="T_v2_2050_TWh"))
    print("R1 done", flush=True)
    # ------------------------------------------------------------------------------------------------------------------------------ R2 G3
    S = IT.load_sessions(); P3 = S["g3_p"]; C3 = S["g3_cap"]
    moves, prods = [], {}
    conv = json.loads((cm.SRC / "FROZEN_UPSTREAM_CONVERSIONS.json").read_text())["constants"]["fuels_conv_toTWh"]
    for it in C3["PH"]["levels"]["central"]:
        C = it["coal_kt"] * conv[it["commodity"]] * 1e6   # v3 line: frozen upstream factor (G3 Runner.gj_t)
        moves.append(("PH", it["row"], "coal", C))
        if it["electricity_added"]:
            moves.append(("PH", it["row"], "electricity", -it["E_gwh"] * 1e3))
    for cc in ("TH", "PH", "SG"):
        p = P3[cc]
        if "sugar_closed_loop" in p:
            moves.append((cc, p["sugar_closed_loop"]["row"], "biomass", p["sugar_closed_loop"]["bio19"]))
        items = []
        if "pulp_paper" in p:
            q = p["pulp_paper"]; items.append(dict(name="pulp_paper", row=q["row"], fuel19=q["fuel19"], el19=q["el19"], v2050=IT.vec(q["v2050"]["main"]), spill=False))
        e = p["ethylene"]["cases"]["main|central"]; items.append(dict(name="ethylene", row=p["ethylene"]["row"], fuel19=e["fuel19"], el19=e["el19"], v2050=IT.vec(e["v2050"])))
        if "glass" in p:
            g = p["glass"]; items.append(dict(name="glass", row=g["row"], fuel19=g["fuel19"], el19=g["el19"], v2050=IT.vec(g["v2050"])))
        prods[cc] = items
    cem = {cc: P3[cc]["cement_usgs_2019_t"] for cc in ("TH", "PH") if "cement_usgs_2019_t" in P3[cc]}
    r = eng.run(dict(moves=moves, products=prods, cem=cem))
    for cc in ("TH", "PH", "SG"):
        D = pd.read_csv(cm.G["G3"] / f"tables/{cc}_COMBINED.csv").set_index("scenario").loc["v3:8"]
        rows.append(dict(check="R2 G3 v3 line step 8", country=cc, i2=tv2(r, cc), reference=float(D.T_2050_twh), quantity="T_v2_2050_TWh"))
        rows.append(dict(check="R2 G3 v3 line step 8", country=cc, i2=r["snap"][cc]["other"] / 1e6, reference=float(D.other_2050_twh), quantity="other_2050_TWh"))
    print("R2 done", flush=True)
    # ------------------------------------------------------------------------------------------------------------------------------ R3 G4
    g4 = S["g4_ci"]; cap = g4["captive_MM"]["low"]
    moves = [("MM", IT.NMM, "coal", cap["C_mwh_v3"]), ("MM", "other", "electricity", -cap["E_mwh"])]
    prows = {"MM_paper": ("MM", "paper pulp and print"), "MM_pulp": ("MM", "paper pulp and print"), "MM_copper": ("MM", "non-ferrous metals"), "LA_pulp": ("LA", None), "LA_copper": ("LA", None)}
    prods = {"MM": [], "LA": []}
    for p, (cc, row) in prows.items():
        d = g4["products"][p]
        prods[cc].append(dict(name=p, row=row, fuel19=d["e2019_purchased_fuel"], el19=d["e2019_purchased_el"], el_from="other", v2050=IT.vec(d["v2050_counted"])))
    r = eng.run(dict(moves=moves, products=prods, cem=dict(g4["cement_usgs_2019_t"]), edgar_zero=["BN"], bn_iii=True))
    G4S = pd.read_csv(cm.G["G4"] / "evidence/G4_SCENARIOS.csv")
    for cc in ("MM", "KH", "LA", "BN"):
        x = G4S[(G4S.scenario == "4 products (closed loop)") & (G4S.ncv_scheme == "v3") & (G4S.country == cc)]
        rows.append(dict(check="R3 G4 v3 line step 4", country=cc, i2=tv2(r, cc), reference=float(x.T_v2_2050_TWh.iloc[0]), quantity="T_v2_2050_TWh"))
        rows.append(dict(check="R3 G4 v3 line step 4", country=cc, i2=r["snap"][cc]["other"] / 1e6, reference=float(x.other_2050_TWh.iloc[0]), quantity="other_2050_TWh"))
    print("R3 done", flush=True)
    # ------------------------------------------------------------------------------------------------------------------------------ R4 G1
    ci = S["g1_ci"]
    mv = []
    for prod in ("ammonia", "methanol", "olefins", "aromatics"):
        m = ci["chem_moves_2019"]["central"][prod]
        mv += [("MY", "other", "gas", m["gas"]), ("MY", "other", "electricity", m["electricity"])]
    items = [dict(name="pulp_paper", row=None, fuel19=ci["pp_2019"]["fuel"], el19=ci["pp_2019"]["electricity"], v2050=IT.vec(ci["pp_2050"]["main"])),
             dict(name="lime", row=None, fuel19=ci["lime_2019"]["fuel"], el19=ci["lime_2019"]["electricity"], v2050=IT.vec(ci["lime_2050"]))]
    extra = {"MY": {"methanol": IT.vec(ci["chem_2050"]["central"]["methanol"]), "hvc": IT.vec(ci["chem_2050"]["central"]["hvc"])}}
    r = eng.run(dict(moves=mv, products={"MY": items}, extra=extra, cem={"MY": ci["cement_usgs_2019_t"]}))
    G1S = pd.read_csv(cm.G["G1"] / "tables/MY_CHAIN_SCENARIOS.csv"); x = G1S[(G1S.sequence == "v3") & (G1S.step == 10)].iloc[0]
    rows.append(dict(check="R4 G1 v3 sequence step 10", country="MY", i2=tv2(r, "MY"), reference=float(x.T_2050_twh), quantity="T_v2_2050_TWh"))
    rows.append(dict(check="R4 G1 v3 sequence step 10", country="MY", i2=r["snap"]["MY"]["other"] / 1e6, reference=float(x.other_2050_twh), quantity="other_2050_TWh"))
    print("R4 done", flush=True)
    # ------------------------------------------------------------------------------------------------------------------------------ R5 G0
    s2c = S["s2_chain"]; capi = S["id_captive"]["central"]
    C_v3 = float(pd.read_csv(cm.S2D / "s1/ID_CAPTIVE_COAL_2019.csv").query("group == '合计' and level == 'central'").coal_in_industry_twh_model.iloc[0]) * 1e6
    B = {x["key"]: x["value"] for x in json.loads((cm.S2D / "s2/_biomass_evidence.json").read_text())["numbers"]}
    fw = (B["3.unsd2019.Fuelwood.Consumption not elsewhere specified (industry)"] - B["3.series.industry_mean_2010_2017_km3"]) * B["3.factor.Fuelwood"] * 1e6
    mv = [("ID", "other", "coal", C_v3), ("ID", "other", "electricity", -capi["E_mwh"]), ("ID", "other", "biomass", fw)]
    eq = s2c["eth"]["central"]
    items = [dict(name="pulp_paper", row=None, fuel19=s2c["pp_2019_fuel_mwh"] - s2c["pp_2019_biomass_part_mwh"], el19=s2c["pp_2019_electricity_mwh"], fuel_split="fossil",
                  v2050=dict(IT.vec(s2c["pp_2050"]["main"]), biomass=0.0)),
             dict(name="ethylene", row=IT.CHEM, fuel19=eq["d19_mwh"] * (1 - eq["el_share"]), el19=eq["d19_mwh"] * eq["el_share"], v2050=IT.vec(s2c["eth_base2025_v2050"]))]
    nf = {"ID": {"nonferrous_nickel": dict(eng.nf["nf2023"]["ID"]["nonferrous_nickel"])}}
    r = eng.run(dict(moves=mv, products={"ID": items}, cem={"ID": IT.CEMENT_USGS_2019_T["ID"]}, nf=nf))
    G0S = pd.read_csv(cm.G["G0"] / "ID_OTHER_SHARE_STEPS.csv"); x = G0S[(G0S.path == "alt_ni_case3") & (G0S.ncv_scheme == "v3") & (G0S.step.astype(str) == "8")].iloc[0]
    rows.append(dict(check="R5 G0 v3 NCV, Case 3 path, step 8", country="ID", i2=tv2(r, "ID"), reference=float(x.T_v2_2050_TWh), quantity="T_v2_2050_TWh"))
    rows.append(dict(check="R5 G0 v3 NCV, Case 3 path, step 8", country="ID", i2=r["snap"]["ID"]["other"] / 1e6, reference=float(x.other_2050_TWh), quantity="other_2050_TWh"))
    print("R5 done", flush=True)
    # ------------------------------------------------------------------------------------------------------------------------------ R6 G2
    from i2_chain import vn_hybrid
    bio = json.loads((cm.G["G2"] / "evidence/_biomass_chain_inputs.json").read_text())
    conv = json.loads((cm.SRC / "FROZEN_UPSTREAM_CONVERSIONS.json").read_text())["constants"]["fuels_conv_toTWh"]
    bag = bio["bagasse_2019_export_kt"] * conv["Bagasse"] * 1e6
    H = vn_hybrid(json.loads(eng.orig[E.CACHE_REL]), S["vn_el_rows"], bag)
    r = eng.run(dict(vn_dec_matrix=H))
    L = pd.read_csv(cm.G["G2"] / "tables/VN_STEPS_LONG.csv"); L = L[(L.ncv_scheme == "v3") & (L.step == 1)].set_index("subsector").twh_2050
    for sub in ("steel", "dispersed", "cement", "ammonia"):
        rows.append(dict(check="R6 G2 v3 line step 1 (hybrid split, v3 two-run rule)", country="VN", i2=r["snap"]["VN"]["L"]["by_sub"][sub] / 1e6, reference=float(L[sub]), quantity=f"{sub}_2050_TWh"))
    rows.append(dict(check="R6 G2 v3 line step 1 (hybrid split, v3 two-run rule)", country="VN", i2=tv2(r, "VN"), reference=float(sum(pd.read_csv(cm.DEMAND / E.SUMMARY).set_index("country").loc["VN", eng.v3.col(x)] for x in eng.v3.CARRIERS)) / 1e6,
                     quantity="T_v2_2050_TWh (unchanged by the split; reference = repository summary row)"))
    print("R6 done", flush=True)
    D = pd.DataFrame(rows); D["dev_twh"] = D.i2 - D.reference
    D.to_csv(cm.TABLES / "I2_REPRODUCTION.csv", index=False, float_format="%.9f", lineterminator="\n")
    for g, z in D.groupby("check"):
        ev.add(f"{g}.max_abs_dev_twh", float(z.dev_twh.abs().max()), "TWh", "EXACT", "C", "tables/I2_REPRODUCTION.csv", f"{len(z)} values")
    ev.write()
    pd.set_option("display.width", 200)
    print(D.groupby("check").dev_twh.agg(lambda s: s.abs().max()).to_string())
    print(D[D.dev_twh.abs() > 1e-6].to_string())


if __name__ == "__main__":
    main()
