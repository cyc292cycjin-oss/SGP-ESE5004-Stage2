"""G3 products (decision 203; S2 method template steps 3-8) for TH, PH, SG: activity, base year, 2019 energy to deduct, 2050 energy, nodes.

    PYTHONHASHSEED=0 python scripts/g3_products.py          (WSL pypsa-earth python; read only on the repository)

Per product (S2 conventions unless stated):
  * cement: v3 2019 cement = EDGAR 2.A.1 / 0.52 / 0.656; USGS 2019 cement (MYB TH 2020-21, PH 2022) -> implied clinker ratio; correction (ii) = grinding
    electricity on USGS cement (scratch patch, g3_chain.py). 2050 unchanged (USGS 2023 output rule of v3).
  * steel: v3 rule re-checked (worldsteel 2019 = USGS 2019; 2050 from the worldsteel 2024 output rule); GEM plant list of v3 -> nodes (same method as v3).
  * pulp and paper (TH, PH): FAOSTAT FO items, base year = last year with new information, literal latest year as sensitivity; 2019 energy = FAOSTAT 2019
    x JRC-IDEES EU27 2019 today intensity with the PyPSA-Eur carrier structure; closed-loop rule (decision 206 item 3): only purchased energy (electricity
    and fossil fuel) is deducted (from the UNSD paper row first) and counted in T_v2 in 2050; the biomass part is reported separately and kept out of T_v2.
  * ethylene / HVC: SFI ethylene units operating in 2019 x utilisation 0.75 / 0.85 / 0.95 (explicit assumption, C), HVC per t ethylene from GEM chemicals
    capacities of the same plants; energy use only (3.269 MWh/t HVC, JRC-IDEES EU27 energy use - NH3 / Cl / MeOH, S2), electricity share 1/12 (ETSAP BAT);
    deducted from the UNSD chemical row; 2050 = HVC x growth x PyPSA-Eur HVC without naphtha. TH: PTTGC cracker No 2 carries Johor coordinates in SFI
    (data error) -> moved to the PTTGC Map Ta Phut site; cracker No 5 (2020) as R4 sensitivity. SG: GEPDSGP0004 'Petrochemical Corp of Singapore'
    (start year unknown) is treated as a duplicate of GEPDSGP0002 (GEM matches PCS to GEPDSGP0002 only) - main without it, sensitivity with it.
    PH: JG Summit (SFI 'Shut down', GEM 'mothballed', start 2014) counted as operating in 2019 (INFERENCE).
  * glass: ETSAP v2.1.0 production 2020 (S0 COVERAGE_ETSAP_PRODUCTION_ASEAN.csv), back-cast to 2019 by R3; JRC-IDEES today 'Glass production'; from the
    non-metallic row after cement, the rest from 'other'.
  * copper (PH, sensitivity): ETSAP 2018 primary smelter 170.9 kt, PyPSA-Eur 'Other non-ferrous metals' (v3 copper route), from 'other'.
  * sugar (closed loop): UNSD bagasse burnt in the food row (TH 22,534 kt, PH 2,411.8 kt) leaves T_v2 with its heat demand (proposed, decision 206 item 3);
    biogas of TH (own wastewater) as sensitivity. FAOSTAT cane x 0.2-0.3 t/t as consistency line.
Outputs tables/<CC>_PRODUCTS_DETAIL.csv, tables/<CC>_PULP_PAPER_FAOSTAT.csv, tables/ETHYLENE_UNITS_SFI.csv, tables/_products_inputs.json (2019 deductions
and 2050 vectors for g3_chain.py), <CC>_NODE_SHARES.csv, tables/_products_evidence.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g3_common as cm   # noqa: E402

PULP_ITEMS = ["Chemical wood pulp", "Dissolving wood pulp", "Mechanical and semi-chemical wood pulp", "Pulp from fibres other than wood"]
PAPER_LEAVES = ["Newsprint", "Printing and writing papers, coated", "Printing and writing papers, uncoated, woodfree", "Printing and writing papers, uncoated, mechanical",
                "Household and sanitary papers", "Case materials", "Cartonboard", "Wrapping papers", "Other papers mainly for packaging",
                "Other paper and paperboard, not elsewhere specified"]
SFI = "downloads/04_sfi_pulp_paper/SFI_ALD_Pulp_Paper_Database_July_2025.xlsx"
SFI_ETH = "downloads/05_sfi_ethylene/Global_Ethylene_Production_Database_December_2025.xlsx"
GEM_CHEM = "downloads/03_gem_chemicals/Plant-level-data-Global-Chemicals-Tracker-November-2026-V1.xlsx"
U_ETH = {"low": 0.75, "central": 0.85, "high": 0.95}
HVC_PRODUCTS = ["ethylene", "propylene", "butadiene", "benzene", "toluene", "xylene"]
ETH_EL_SHARE = 1.0 / 12.0   # S2: ETSAP BAT olefins electricity share (route map)
PTTGC_FIX = (12.697918, 101.142795)   # SFI coordinates of the PTTGC Map Ta Phut crackers No 1, 3, 4 (same company and site)
SG_DUP = "GEPDSGP0004"
SUGAR_PF = (0.2, 0.3)   # IRENA 2017 Table R3 processing residue factor 0.2 (S2); 0.3 typical upper (INFERENCE)
BL_GJ_T = 22.0          # ETSAP v2.1.0 chemical pulp: black liquor 22 GJ/t pulp output, own fuel (V4_PRODUCT_ROUTE_MAP.csv note; S2 BLACK_LIQUOR_GJ_T)
# 2019 electricity shares where the PyPSA-Eur 2050 column is electrified (glass, other non-ferrous): ETSAP v2.1.0 BAT (S0 COVERAGE_ETSAP_BAT_SEC.csv)
GLASS_EL_SHARE = (1.24 / 5.4 + 3.03 / 10.62) / 2      # mean of container (0.230) and flat glass (0.285); product mix not on disk (C)
COPPER_EL_SHARE = (2.368 + 2.144) / (3.2 + 5.199)     # primary smelting + refining and casting


def main():
    ev = cm.Ev("products"); out = cm.G3 / "tables"
    FO, QCL = cm.fao("FO"), cm.fao("QCL")
    usgs = pd.read_csv(out / "USGS_TABLE1_TH_PH.csv").set_index(["country", "item", "year"]).value_t
    S = pd.read_csv(cm.REPO / "research_inputs/demand_v5" / cm.SUMMARY).set_index("country")
    base_m08b = pd.read_csv(cm.REPO / "research_inputs/demand_v5/INDUSTRY_OUTPUT_BASE_M08B.csv")
    rule = pd.read_csv(cm.REPO / "research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country")
    etsap = pd.read_csv(cm.S2W / "evidence/COVERAGE_ETSAP_PRODUCTION_ASEAN.csv")
    tday = cm.ratios_today()
    inputs, detail = {cc: {} for cc in cm.CC3}, {cc: [] for cc in cm.CC3}

    def put_detail(cc, **kw):
        detail[cc].append(kw)

    # ============================================== cement and steel (v3 rule re-check) ==============================================
    for cc in cm.CC3:
        G = cm.gdp_growth(cc)
        ev.put(f"{cc}.G_2022_2050", G, "-", "INDUSTRY_OUTPUT_2050_M08B.csv (AEO8 D.2)", "VERIFIED", "B")
        clk = float(S.at[cc, "clinker_2019_t"]); cem_v3 = float(S.at[cc, "cement_2019_t"]); cem50 = float(S.at[cc, "cement_2050_t"])
        if clk > 0:
            cu = float(usgs[(cc, "cement_hydraulic", 2019)])
            inputs[cc]["cement_usgs_2019_t"] = cu
            put_detail(cc, subsector="cement", route="PyPSA-Eur Cement (v3)", activity_source="EDGAR 2.A.1 / 0.52 (clinker); USGS MYB cement 2019 (correction ii)", base_year=2019,
                       activity_base=cu, activity_2050=cem50, note=f"clinker {clk / 1e6:.2f} Mt; v3 cement = clinker / 0.656 = {cem_v3 / 1e6:.2f} Mt vs USGS {cu / 1e6:.2f} Mt; "
                       f"implied clinker / cement {clk / cu:.3f} (v3 0.656)", grade="B")
            ev.put(f"{cc}.cement.usgs_2019", cu, "t", "USGS MYB Table 1 (tables/USGS_TABLE1_TH_PH.csv)", "VERIFIED", "A")
            ev.put(f"{cc}.cement.v3_2019", cem_v3, "t", "s3_0 summary cement_2019_t (EDGAR / 0.52 / 0.656)", "VERIFIED", "C")
            ev.put(f"{cc}.cement.clinker_ratio_implied", clk / cu, "-", "EDGAR clinker / USGS cement 2019", "INFERENCE", "C")
        st19 = float(S.at[cc, "crude_steel_2019_t"]); st50 = float(S.at[cc, "crude_steel_2050_t"])
        b = base_m08b[base_m08b.country == cc]
        put_detail(cc, subsector="steel", route="30 % H2-DRI + EAF / 70 % scrap EAF (v3)", activity_source="worldsteel 2019 (2019 deduction = UNSD iron-and-steel row) / worldsteel 2024 output rule",
                   base_year=2024, activity_base=st19, activity_2050=st50, note=(f"USGS 2019 raw steel {float(usgs.get((cc, 'raw_steel', 2019), np.nan)) / 1e6:.3f} Mt = worldsteel {st19 / 1e6:.3f} Mt; "
                                                                          f"M08B base: {b.to_dict('records')[:1] if len(b) else 'n/a'}"), grade="A/B")
    # ============================================== pulp and paper (TH, PH) ==========================================================
    for cc in ("TH", "PH"):
        area = cm.NAMES[cc]; rows = []
        for grp, items, sector in (("pulp", PULP_ITEMS, "Pulp production"), ("paper", PAPER_LEAVES, "Paper production")):
            for it in items:
                s = cm.series(FO, area, it)
                if not len(s) or s.value.dropna().empty:
                    continue
                la = cm.latest_actual(s)
                z19 = s[s.year == 2019]
                v19, f19 = (float(z19.value.iloc[0]), str(z19.flag.iloc[0])) if len(z19) else (0.0, "")
                rows.append(dict(group=grp, item=it, sector=sector, q_2019_t=v19, flag_2019=f19, base_year=la["base_year"], q_base_t=la["value"], flag_base=la["flag"], grade_base=la["grade"],
                                 carried_forward_years=";".join(map(str, la["carried_forward_years"])), latest_year=la["latest_year"], q_latest_t=la["latest_value"],
                                 q_2050_main_t=la["value"] * cm.growth(la["base_year"], cc), q_2050_literal_latest_t=la["latest_value"] * cm.growth(la["latest_year"], cc),
                                 series=";".join(f"{int(y)}:{v:.0f}{f}" for y, v, f in zip(s.year, s.value, s.flag))))
        P = pd.DataFrame(rows); P.to_csv(out / f"{cc}_PULP_PAPER_FAOSTAT.csv", index=False, float_format="%.6g")
        tot = P.groupby("group")[["q_2019_t", "q_2050_main_t", "q_2050_literal_latest_t"]].sum()
        e19 = {}
        for g_, sec in (("pulp", "Pulp production"), ("paper", "Paper production")):
            e19[g_] = cm.today_vec(sec, float(tot.at[g_, "q_2019_t"])) if g_ in tot.index else {k: 0.0 for k in ("elec", "coal", "coke", "methane", "biomass", "hydrogen", "heat")}
        el19 = sum(v["elec"] for v in e19.values()); bio19 = sum(v["biomass"] for v in e19.values()); tot19 = sum(sum(v.values()) for v in e19.values())
        # closed loop = black liquor of chemical and dissolving pulp (ETSAP 22 GJ/t pulp, own fuel; route map note), capped at the fuel part
        chem = P[P.item.isin(["Chemical wood pulp", "Dissolving wood pulp"])]
        bl19 = min(float(chem.q_2019_t.sum()) * BL_GJ_T / 3.6, tot19 - el19)
        fuel_purch = tot19 - el19 - bl19
        v50, bl50 = {}, {}
        for case, col in (("main", "q_2050_main_t"), ("literal_latest", "q_2050_literal_latest_t")):
            v = {k: 0.0 for k in cm.OUTC}
            for g_, sec in (("pulp", "Pulp production"), ("paper", "Paper production")):
                if g_ in tot.index:
                    for k, x in cm.vec2050(sec, float(tot.at[g_, col])).items():
                        v[k] += x
            v50[case] = v
            bl50[case] = min(float(chem[col].sum()) * BL_GJ_T / 3.6, v["biomass"])
        inputs[cc]["pulp_paper"] = dict(row="paper pulp and print", el19=el19, fuel19=fuel_purch, closed_loop_bl19=bl19, structure_bio19=bio19, total19=tot19,
                                        v2050_full=v50, closed_loop_bl2050=bl50,
                                        v2050={c: {k: (x - bl50[c] if k == "biomass" else x) for k, x in v.items()} for c, v in v50.items()},
                                        v2050_literal_rule={c: {k: x for k, x in v.items() if k != "biomass"} for c, v in v50.items()})
        put_detail(cc, subsector="pulp and paper", route="PyPSA-Eur Pulp production + Paper production; black-liquor equivalent outside T_v2 (closed loop)",
                   activity_source="FAOSTAT FO (tables/%s_PULP_PAPER_FAOSTAT.csv)" % cc, base_year="per item (last year with new information)",
                   activity_base=float(tot.q_2019_t.sum()), activity_2050=float(tot.q_2050_main_t.sum()), sec_source="JRC-IDEES EU27 2019 today x PyPSA-Eur structure; 2050 PyPSA-Eur ratios",
                   energy_2019_total=tot19, energy_2019_purchased=el19 + fuel_purch, energy_2019_biomass_part=bl19, grade="B/C",
                   note=f"black liquor (chemical + dissolving pulp x {BL_GJ_T} GJ/t) 2019 {bl19 / 1e6:.2f} TWh, 2050 {bl50['main'] / 1e6:.2f} TWh; PyPSA-Eur structure biomass part 2019 {bio19 / 1e6:.2f} TWh")
        for k, v in (("pulp_2019_t", float(tot.at["pulp", "q_2019_t"]) if "pulp" in tot.index else 0.0), ("paper_2019_t", float(tot.at["paper", "q_2019_t"]) if "paper" in tot.index else 0.0),
                     ("pulp_2050_t", float(tot.at["pulp", "q_2050_main_t"]) if "pulp" in tot.index else 0.0), ("paper_2050_t", float(tot.at["paper", "q_2050_main_t"]) if "paper" in tot.index else 0.0),
                     ("e2019_total_mwh", tot19), ("e2019_electricity_mwh", el19), ("e2019_purchased_fuel_mwh", fuel_purch), ("e2019_black_liquor_mwh", bl19),
                     ("e2050_main_tv2_mwh", sum(inputs[cc]["pulp_paper"]["v2050"]["main"].values())), ("e2050_main_black_liquor_mwh", bl50["main"])):
            ev.put(f"{cc}.pp.{k}", v, "t" if k.endswith("_t") else "MWh", "FAOSTAT FO x JRC-IDEES / PyPSA-Eur (S2 convention)", "VERIFIED" if k.endswith("2019_t") else "PROPOSED (quantified)", "B" if k.endswith("2019_t") else "C")
    # ============================================== ethylene / HVC ===================================================================
    X = pd.read_excel(cm.S2W / SFI_ETH, sheet_name=0)
    X = X[X.country.isin([cm.NAMES[c] for c in cm.CC3])].copy()
    X["cap"] = pd.to_numeric(X["capacity (Kt ethylene/year)"], errors="coerce") * 1e3; X["start"] = pd.to_numeric(X.year, errors="coerce")
    X["lat"], X["lon"] = X.latitude.astype(float), X.longitude.astype(float)
    X["note"] = ""
    m = X.uid.eq("GEPDTHA0001")
    X.loc[m, ["lat", "lon"]] = PTTGC_FIX; X.loc[m, "note"] = "SFI coordinates in Johor (MY) - moved to the PTTGC Map Ta Phut site (data error, INFERENCE)"
    X.loc[X.uid.eq(SG_DUP), "note"] = "treated as duplicate of GEPDSGP0002 in the main case (GEM matches PCS to GEPDSGP0002 only; INFERENCE)"
    X.loc[X.country.eq("Philippines"), "note"] = "SFI 'Shut down' / GEM 'mothballed' today; start 2014 -> operating in 2019 (INFERENCE)"
    X["op2019"] = (X.status.eq("Operating") & ~(X.start > 2019)) | X.country.eq("Philippines")
    X.to_csv(out / "ETHYLENE_UNITS_SFI.csv", index=False, columns=["uid", "plant_name", "country", "state", "status", "cap", "start", "feedstock", "lat", "lon", "op2019", "note"])
    gp = pd.read_excel(cm.S2W / GEM_CHEM, sheet_name="Plant Data"); gc = pd.read_excel(cm.S2W / GEM_CHEM, sheet_name="Chemical Capacities")
    v50_hvc = cm.vec2050("HVC", 1.0); hvc50 = sum(v50_hvc.values())
    import s3_0_industry as s30   # noqa: E402  (constants only; on sys.path via cm.import_v3)
    PE = dict(s30.PE); PE["EU27_ammonia_kt"] = float(json.loads((cm.REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_EVIDENCE.json").read_text())["eu27_ammonia_kt_2019"])
    basic = (float(tday.at["HVC", "fec_2019_ktoe"]) - float(tday.at["HVC", "feedstock_2019_ktoe"])) * 11.63 * 1e3
    nh3 = PE["EU27_ammonia_kt"] * 1e3 * (PE["MWh_CH4_per_tNH3_SMR"] + PE["MWh_elec_per_tNH3_SMR"]); cl = PE["chlorine_production_today"] * 1e6 * (PE["MWh_elec_per_tCl"] + PE["MWh_H2_per_tCl"])
    meoh = PE["methanol_production_today"] * 1e6 * (PE["MWh_CH4_per_tMeOH"] + PE["MWh_elec_per_tMeOH"])
    hvc_spec = (basic - nh3 - cl - meoh) / (PE["HVC_production_today"] * 1e6)
    ev.put("eth.hvc_spec_energy_use", hvc_spec, "MWh/t HVC", "JRC-IDEES EU27 2019 basic chemicals energy use - NH3 / Cl / MeOH (s3_0 lines), / 52 Mt HVC (= S2 3.269)", "EXACT", "C")
    ev.put("eth.pypsa_hvc_2050", hvc50, "MWh/t HVC", "PyPSA-Eur 2050 HVC without naphtha", "VERIFIED", "B")
    for cc in cm.CC3:
        z = X[X.country.eq(cm.NAMES[cc])]
        gid = gp[gp["Country/Area"].eq(cm.NAMES[cc])]["GEM Plant ID"]
        gcc = gc[gc["GEM Plant ID"].isin(gid) & gc.Product.isin(HVC_PRODUCTS)]
        both = [p for p, h in gcc.groupby("GEM Plant ID") if (h[h.Product.eq("ethylene")]["Capacity (ttpa)"].sum() > 0) and (h[h.Product.eq("propylene")]["Capacity (ttpa)"].sum() > 0)]
        h_ = gcc[gcc["GEM Plant ID"].isin(both) & ~gcc["Capacity Status"].isin(["developing", "announced", "cancelled"])]
        hvc_per_eth = float(h_["Capacity (ttpa)"].sum()) / float(h_[h_.Product.eq("ethylene")]["Capacity (ttpa)"].sum())
        cases = {"main": z[z.op2019 & ~z.uid.eq(SG_DUP)], "with_duplicate": z[z.op2019], "base_2020_incl_new": z[z.status.eq("Operating") | z.country.eq("Philippines")]}
        res = {}
        for case, zz in cases.items():
            cap = float(zz.cap.sum())
            for lv, u in U_ETH.items():
                if case != "main" and lv != "central":
                    continue
                q_eth = cap * u; q_hvc = q_eth * hvc_per_eth
                yb = 2020 if case == "base_2020_incl_new" else 2019
                d19 = q_hvc * hvc_spec if yb == 2019 else q_hvc * cm.growth(yb, cc) / cm.growth(2019, cc) * hvc_spec
                q50 = q_hvc * cm.growth(yb, cc)
                res[f"{case}|{lv}"] = dict(capacity_t=cap, utilisation=u, ethylene_t=q_eth, hvc_per_ethylene=hvc_per_eth, hvc_t=q_hvc, base_year=yb, d19=d19,
                                           el19=d19 * ETH_EL_SHARE, fuel19=d19 * (1 - ETH_EL_SHARE), hvc_2050_t=q50, v2050={k: q50 * x for k, x in v50_hvc.items()},
                                           v2050_today_intensity={k: q50 * x * hvc_spec / hvc50 for k, x in v50_hvc.items()})   # sensitivity: 2019 intensity, 2050 carrier shares
                ev.put(f"{cc}.eth.{case}.{lv}.energy_2019_mwh", d19, "MWh", "SFI capacity x u x HVC/ethylene (GEM) x 3.269 MWh/t", "INFERENCE", "C")
                ev.put(f"{cc}.eth.{case}.{lv}.energy_2050_mwh", q50 * hvc50, "MWh", "HVC 2050 x PyPSA-Eur HVC (no naphtha)", "PROPOSED (quantified)", "C")
        inputs[cc]["ethylene"] = dict(row="chemical and petrochemical", cases=res, hvc_per_ethylene=hvc_per_eth, gem_plants=both)
        ev.put(f"{cc}.eth.hvc_per_ethylene", hvc_per_eth, "t/t", f"GEM GCT 2026-11 plants with ethylene and propylene: {';'.join(both)}", "INFERENCE", "C")
        c0 = res["main|central"]
        put_detail(cc, subsector="ethylene (HVC)", route="PyPSA-Eur HVC 2050 (naphtha in NEU)", activity_source="SFI ethylene 2025-12 x u 0.85 (C); HVC/ethylene GEM", base_year=c0["base_year"],
                   activity_base=c0["hvc_t"], activity_2050=c0["hvc_2050_t"], sec_source="JRC-IDEES EU27 2019 energy use 3.269 MWh/t HVC; electricity 1/12 (ETSAP BAT)",
                   energy_2019_total=c0["d19"], energy_2019_purchased=c0["d19"], energy_2019_biomass_part=0.0, grade="C",
                   note=f"capacity {c0['capacity_t'] / 1e3:,.0f} kt; HVC/ethylene {hvc_per_eth:.3f}")
    # ============================================== glass (ETSAP 2020) and copper (PH) ================================================
    gv = {"elec", "methane", "coal", "coke", "biomass", "hydrogen", "heat"}
    for cc in cm.CC3:
        z = etsap[(etsap.country == cc) & (etsap["product"] == "Glass")]
        if len(z):
            q20 = float(z.kt.iloc[0]) * 1e3
            q19 = q20 * cm.growth(2020, cc) / cm.growth(2019, cc); q50 = q20 * cm.growth(2020, cc)
            t19 = cm.today_vec("Glass production", q19)
            tot = sum(t19.values()); el19 = tot * GLASS_EL_SHARE; fu19 = tot - el19   # 2019 split: ETSAP BAT (the 2050 PyPSA-Eur glass column is ~99 % electricity)
            inputs[cc]["glass"] = dict(row="non-metallic minerals", el19=el19, fuel19=fu19, v2050=cm.vec2050("Glass production", q50))
            put_detail(cc, subsector="glass", route="PyPSA-Eur Glass production", activity_source="ETSAP v2.1.0 production 2020 (B), R3 back-cast to 2019 (C)", base_year=2020,
                       activity_base=q20, activity_2050=q50, sec_source="JRC-IDEES EU27 2019 today x PyPSA-Eur structure", energy_2019_total=el19 + fu19, energy_2019_purchased=el19 + fu19,
                       energy_2019_biomass_part=0.0, grade="B/C")
            ev.put(f"{cc}.glass.q2020", q20, "t", "ETSAP v2.1.0 Glass_production.xlsx 2020 (S0 coverage table)", "VERIFIED", "B")
            ev.put(f"{cc}.glass.e2019_mwh", el19 + fu19, "MWh", "q2019 x JRC-IDEES today glass", "INFERENCE", "C")
    z = etsap[(etsap.country == "PH") & (etsap["product"] == "Primary copper - smelter production")]
    q18 = float(z.kt.iloc[0]) * 1e3; q19 = q18 * cm.growth(2018, "PH") / cm.growth(2019, "PH"); q50 = q18 * cm.growth(2018, "PH")
    t19 = cm.today_vec("Other non-ferrous metals", q19); tot_cu = sum(t19.values())
    inputs["PH"]["copper"] = dict(row="other", el19=tot_cu * COPPER_EL_SHARE, fuel19=tot_cu * (1 - COPPER_EL_SHARE), v2050=cm.vec2050("Other non-ferrous metals", q50))
    put_detail("PH", subsector="copper (sensitivity)", route="PyPSA-Eur Other non-ferrous metals (v3 copper route)", activity_source="ETSAP 2018 primary smelter (PASAR, B)", base_year=2018,
               activity_base=q18, activity_2050=q50, sec_source="JRC-IDEES EU27 2019 today", energy_2019_total=sum(t19.values()), energy_2019_purchased=sum(t19.values()), energy_2019_biomass_part=0.0, grade="B/C")
    # ============================================== sugar (closed loop) and biogas (TH) ===================================================
    for cc, bag_kt in (("TH", None), ("PH", None)):
        rows = [r for r in cm.base_rows(cc) if r["Commodity"] == "Bagasse"]
        bag_mwh = float(sum(float(r["MWh"]) for r in rows)); bag_kt = float(sum(float(r["RawValue"]) for r in rows))
        cane = cm.series(QCL, cm.NAMES[cc], "Sugar cane"); c19 = float(cane[cane.year == 2019].value.iloc[0])
        inputs[cc]["sugar_closed_loop"] = dict(row="food and tobacco", bio19=bag_mwh, bagasse_kt=bag_kt)
        put_detail(cc, subsector="sugar (bagasse, closed loop)", route="self-produced residue and its heat outside T_v2 (decision 206 item 3)", activity_source="UNSD 2019 bagasse in the food row",
                   base_year=2019, activity_base=bag_kt * 1e3, activity_2050=0.0, energy_2019_total=bag_mwh, energy_2019_purchased=0.0, energy_2019_biomass_part=bag_mwh, grade="B",
                   note=f"FAOSTAT cane 2019 {c19 / 1e6:.1f} Mt; UNSD bagasse production / cane see BIOMASS_CHECK")
        ev.put(f"{cc}.sugar.bagasse_food_mwh", bag_mwh, "MWh", "BASE_RECONSTRUCTION IndustryFinalEnergy bagasse (UNSD 2019)", "VERIFIED", "B")
        ev.put(f"{cc}.sugar.cane_2019", c19, "t", "FAOSTAT QCL", "VERIFIED", "A")
    bg = [r for r in cm.base_rows("TH") if r["Commodity"] == "Biogases"]
    inputs["TH"]["biogas_closed_loop"] = dict(rows={k: tj * 1e3 / 3.6 for k, tj in (("food and tobacco", 19940.0), ("chemical and petrochemical", 5500.0),
                                                                                     ("paper pulp and print", 120.0), ("non-metallic minerals", 40.0))},   # MWh (UNSD 2019 TJ by row)
                                              total=float(sum(float(r["MWh"]) for r in bg)))
    ev.put("TH.biogas.industry_mwh", inputs["TH"]["biogas_closed_loop"]["total"], "MWh", "UNSD 2019 biogases 25,600 TJ in industry (food 19,940, chemical 5,500, paper 120, NMM 40 TJ)", "VERIFIED", "B")

    # ============================================== nodes ==============================================================================
    import geopandas as gpd
    regions = gpd.read_file(cm.MAIN / "research_inputs/renewable_v5/regions_onshore.geojson")
    v3s = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_NODE_SHARES_V3.csv")
    Sf = pd.read_excel(cm.S2W / SFI, sheet_name="SFI_Pulp_Paper_Database")
    nrows = {cc: [] for cc in cm.CC3}

    def compare(cc, sub, shares: pd.Series, v3_sub: str, note: str):
        v3o = v3s[(v3s.country == cc) & (v3s.subsector == v3_sub)].set_index("node").share
        idx = sorted(set(shares.index) | set(v3o.index))
        for n_ in idx:
            a, b = float(shares.get(n_, 0.0)), float(v3o.get(n_, 0.0))
            nrows[cc].append(dict(subsector=sub, node=n_, share_v4=a, share_v3=b, diff_pp=(a - b) * 100, note=f"v3 = '{v3_sub}' shares; {note}"))

    for cc in ("TH", "PH"):
        s = Sf[Sf.country.eq(cm.NAMES[cc])].copy()
        s["cap_pulp"] = pd.to_numeric(s["capacity_pulp (tonnes per year) "], errors="coerce"); s["cap_paper"] = pd.to_numeric(s["capacity_paper (tonnes per year)"], errors="coerce")
        s["lat"], s["lon"] = s.latitude.astype(float), s.longitude.astype(float)
        s["node"], s["node_method"] = cm.node_of(s, regions, cc)
        P = pd.read_csv(out / f"{cc}_PULP_PAPER_FAOSTAT.csv"); tq = P.groupby("group").q_2019_t.sum()
        qp, qq = float(tq.get("pulp", 0.0)), float(tq.get("paper", 0.0)); kp, kq = float(s.cap_pulp.sum()), float(s.cap_paper.sum())
        s["w_pulp"] = s.cap_pulp.fillna(0.0) * (qp / kp if kp else 0.0)
        paper_types = ~s.plant_type.astype(str).str.fullmatch("Pulp"); n_unk = int((s.cap_paper.isna() & paper_types).sum()); resid = max(0.0, qq - kq)
        s["w_paper"] = np.where(s.cap_paper.notna(), s.cap_paper.fillna(0.0) * min(1.0, qq / kq if kq else 0.0), np.where(paper_types, resid / max(1, n_unk), 0.0))
        pp = inputs[cc]["pulp_paper"]; e_pulp = sum(cm.vec2050("Pulp production", 1.0).values()); e_paper = sum(cm.vec2050("Paper production", 1.0).values())
        s["w_e"] = s.w_pulp * e_pulp + s.w_paper * e_paper
        sh = s.groupby("node").w_e.sum(); sh = sh / sh.sum()
        compare(cc, "pulp and paper", sh, "dispersed", f"SFI 2025-07 {len(s)} mills ({int(s.cap_pulp.notna().sum())} with pulp, {int(s.cap_paper.notna().sum())} with paper capacity; "
                f"{n_unk} without capacity share the paper residual {resid / 1e3:,.0f} kt)")
        s[["uid", "plant_name", "state", "lat", "lon", "plant_type", "cap_pulp", "cap_paper", "node", "node_method", "w_pulp", "w_paper"]].to_csv(out / f"{cc}_PULP_PAPER_MILLS_SFI.csv", index=False, float_format="%.6g")
        ev.put(f"{cc}.pp.sfi_mills", len(s), "mills", "SFI 2025-07", "VERIFIED", "B")
    for cc in cm.CC3:
        z = X[X.country.eq(cm.NAMES[cc]) & X.op2019 & ~X.uid.eq(SG_DUP)].copy()
        if len(z):
            z["node"], z["node_method"] = cm.node_of(z, regions, cc)
            sh = z.groupby("node").cap.sum(); sh = sh / sh.sum()
            compare(cc, "ethylene (HVC)", sh, "dispersed" if cc != "SG" else "petrochem", "SFI 2019 operating capacity (PTTGC No 2 moved to Map Ta Phut; SG duplicate excluded)")
        for sub, fn, wcol in (("steel", "GEM_STEEL_ASEAN_OPERATING_V3.csv", "weight"), ("cement", "GEM_CEMENT_ASEAN_OPERATING_V3.csv", "weight")):
            f = pd.read_csv(cm.REPO / "research_inputs/industry_v3" / fn); f = f[f.iso == cc].copy()
            if not len(f):
                continue
            f["node"], f["node_method"] = cm.node_of(f, regions, cc)
            sh = f.groupby("node")[wcol].sum(); sh = sh / sh.sum()
            compare(cc, sub, sh, sub, f"v3 GEM facility list ({len(f)} plants) re-assigned with the same point-in-region rule (check: diff should be 0)")
        if "glass" in inputs[cc]:
            v3d = v3s[(v3s.country == cc) & (v3s.subsector == "dispersed")].set_index("node").share
            compare(cc, "glass", v3d, "dispersed", "no glass facility data on disk (Climate TRACE glass is a model estimate, S0 4.5): v3 dispersed shares kept")
    for cc in cm.CC3:
        pd.DataFrame(nrows[cc]).to_csv(cm.G3 / f"{cc}_NODE_SHARES.csv", index=False, float_format="%.6f")
        pd.DataFrame(detail[cc]).to_csv(out / f"{cc}_PRODUCTS_DETAIL.csv", index=False, float_format="%.6g")
        for r in nrows[cc]:
            if abs(r["diff_pp"]) > 5:
                ev.put(f"{cc}.node.{r['subsector']}.{r['node']}.diff_pp", r["diff_pp"], "pp", f"{cc}_NODE_SHARES.csv", "PROPOSED (quantified)", "C")
    ev.put("PH.copper.q2018", q18, "t", "ETSAP 2018 primary copper smelter production (PASAR)", "VERIFIED", "B")
    cm.jdump(inputs, out / "_products_inputs.json")
    ev.extra["inputs"] = {cc: list(v) for cc, v in inputs.items()}
    ev.write(out / "_products_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 80)
    for cc in cm.CC3:
        print("=====", cc); print(pd.DataFrame(detail[cc]).drop(columns=[c for c in ("route", "sec_source") if c in pd.DataFrame(detail[cc]).columns]).to_string())
        nd = pd.DataFrame(nrows[cc]); print(nd[nd.diff_pp.abs() > 0.5].round(3).to_string() if len(nd) else "")
    for cc in ("TH", "PH"):
        pp = inputs[cc]["pulp_paper"]; print(cc, "pp 2019 total/el/fuel/BL TWh", round(pp["total19"] / 1e6, 3), round(pp["el19"] / 1e6, 3), round(pp["fuel19"] / 1e6, 3), round(pp["closed_loop_bl19"] / 1e6, 3),
                                             "2050 Tv2 / BL / literal Tv2", round(sum(pp["v2050"]["main"].values()) / 1e6, 3), round(pp["closed_loop_bl2050"]["main"] / 1e6, 3),
                                             round(sum(pp["v2050_literal_rule"]["main"].values()) / 1e6, 3))
    for cc in cm.CC3:
        e = inputs[cc]["ethylene"]["cases"]["main|central"]; print(cc, "eth cap kt", e["capacity_t"] / 1e3, "HVC/eth", round(e["hvc_per_ethylene"], 3), "d19 TWh", round(e["d19"] / 1e6, 3), "2050 TWh", round(e["hvc_2050_t"] * hvc50 / 1e6, 3))


if __name__ == "__main__":
    cm.import_v3()
    main()
