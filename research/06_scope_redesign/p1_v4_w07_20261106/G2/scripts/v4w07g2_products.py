"""G2-4: Viet Nam sub-sectors (B-G2 item 2; template steps 3-6): steel boundary, cement clinker ratio, pulp and paper (closed-loop rule,
decision 206 item 3), glass, alumina, ethylene (sensitivity), and the inputs of the chain steps of G2-7.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/v4w07g2_products.py

Sources (local, read only): worldsteel 2019 (repository), USGS MYB 2022 Vietnam table 1 (page text, extracted/), USGS MYB 2023 cement T22
(repository m08b source), EDGAR 2025 IPPU (repository), GEM cement / steel (S0 extracted), FAOSTAT FO (S2 download, SHA256 checked), ETSAP route
map (S0), JRC-IDEES EU27 2019 today table and PyPSA-Eur 2050 ratios (repository), UNSD SDMX (sdmx/), SFI ethylene, GEM chemicals.
Nothing is changed in the repository; the chain runs are in v4w07g2_steps.py.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4w07g2_common as cm   # noqa: E402

sys.path.insert(0, str(cm.S2W / "scripts"))
import v4s2_common as s2   # noqa: E402  (FAOSTAT readers with the SHA256 check and the 'last year with new information' rule)

T = cm.WORK / "tables"
BLACK_LIQUOR_GJ_T = 22.0   # ETSAP v2.1.0 route map note (chemical pulp output, own fuel), as S2
U_ETH = {"low": 0.75, "central": 0.85, "high": 0.95}   # explicit assumption (C), as S2
CEMENT_T22 = cm.REPO / "research_inputs/demand_v5/sources/m08b/myb1-2023-cemen-ERT.xlsx"
EDGAR = cm.REPO / "research_inputs/registry_v5/sources/EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv"
T22_NAME = {"BN": "Brunei", "MM": "Burma", "KH": "Cambodia", "ID": "Indonesia", "LA": "Laos", "MY": "Malaysia", "PH": "Philippines", "TH": "Thailand", "VN": "Vietnam"}
PULP_ITEMS = ["Chemical wood pulp", "Dissolving wood pulp", "Mechanical and semi-chemical wood pulp", "Pulp from fibres other than wood"]
PAPER_LEAVES = ["Newsprint", "Printing and writing papers, coated", "Printing and writing papers, uncoated, woodfree", "Printing and writing papers, uncoated, mechanical",
                "Household and sanitary papers", "Case materials", "Cartonboard", "Wrapping papers", "Other papers mainly for packaging",
                "Other paper and paperboard, not elsewhere specified"]
CARS = ("elec", "coal", "coke", "methane", "biomass", "hydrogen", "heat")


def usgs_vn(label: str) -> list:
    """Numbers of a USGS MYB 2022 Vietnam table 1 line (2018 ... 2022), footnote letters dropped."""
    for p in sorted((cm.WORK / "extracted/usgs_myb_2022_vietnam").glob("p00[7-8].txt")):
        for line in p.read_text(encoding="utf-8").splitlines():
            s = re.sub(r"\s+", " ", line).strip()
            if s.startswith(label):
                vals = re.findall(r"(?<![A-Za-z])(\d{1,3}(?:,\d{3})+|\d+)(?:\s?[re](?:,\s?[re])*)?(?=\s|$)", s[len(label):])
                return [float(v.replace(",", "")) for v in vals][-5:]
    raise KeyError(label)


def today_vec(sector: str, t: float) -> dict:
    """S1 convention: JRC-IDEES EU27 2019 today total x carrier structure of the PyPSA-Eur ratio column (grade C)."""
    r50 = cm.ratios_2050(); td = cm.ratios_today()
    col = r50[sector]; tf = float(sum(col[c] for c in CARS)); tot = float(td.at[sector, "today_total_mwh_per_t"])
    return {c: float(col[c]) / tf * tot * t for c in CARS}


def main():
    ev = cm.Ev("products"); chain_in = {}
    G = cm.gdp_growth()
    ev.put("growth.G_2022_2050", G, "-", "INDUSTRY_OUTPUT_2050_M08B.csv gdp_growth_2022_2050 (AEO8 D.2), VN", "VERIFIED", "B")
    # ================= USGS table 1 =================
    us = {k: dict(zip(range(2018, 2023), usgs_vn(lab))) for k, lab in (("raw_steel_kt", "Raw steel do."), ("pig_iron_kt", "Pig iron do."),
                                                                          ("cement_kt", "Cement, hydraulic thousand metric tons"), ("alumina_t", "Alumina"),
                                                                          ("ammonia_n_kt", "Nitrogen, ammonia, N content thousand metric tons"))}
    assert us["raw_steel_kt"][2019] == 17469 and us["cement_kt"][2019] == 105533 and us["alumina_t"][2019] == 1365000, us
    for k, d in us.items():
        for y, x in d.items():
            ev.put(f"usgs.{k}.{y}", x, k.split("_")[-1], "USGS MYB 2022 Vietnam table 1 (extracted page text)", "VERIFIED", "A")
    # ================= STEEL: 2019 boundary check =================
    ws = pd.read_csv(cm.REPO / "research_inputs/registry_v5/sources/WORLDSTEEL_2019_ASEAN.csv").set_index("iso2").loc[cm.CC]
    bof, eaf, ind, pig = float(ws.bof_oxygen_kt) * 1e3, float(ws.eaf_electric_kt) * 1e3, float(ws.other_kt) * 1e3, float(ws.pig_iron_2019_kt) * 1e3
    td = cm.ratios_today(); r50 = cm.ratios_2050()
    rm = pd.read_csv(cm.S2W / "V4_PRODUCT_ROUTE_MAP.csv").set_index("route")
    s = cm.sdmx_long()
    sv = lambda com, tr, y: float(s[(s.commodity == com) & (s.transaction == tr) & (s.year == y)].value.sum())
    split = pd.read_csv(T / "VN_SPLIT_VARIANTS.csv").set_index("variant")
    jrc = (bof * float(td.at["Integrated steelworks", "today_total_mwh_per_t"]) + (eaf + ind) * float(td.at["Electric arc", "today_total_mwh_per_t"])) / 1e6
    bat = (bof * (float(rm.at["BF-BOF", "bat_electricity_gj_per_t"]) + float(rm.at["BF-BOF", "bat_fuel_or_heat_gj_per_t"]))
           + (eaf + ind) * (float(rm.at["scrap EAF / IF", "bat_electricity_gj_per_t"]) + float(rm.at["scrap EAF / IF", "bat_fuel_or_heat_gj_per_t"]))) / 3.6 / 1e6
    bat_oda = (bof * (float(rm.at["BF-BOF", "base_electricity_mwh_per_t"]) + float(rm.at["BF-BOF", "base_fuel_mwh_per_t"]))
               + (eaf + ind) * (float(rm.at["scrap EAF / IF", "base_electricity_mwh_per_t"]) + float(rm.at["scrap EAF / IF", "base_fuel_mwh_per_t"]))) / 1e6
    v3_want = (bof * sum(float(r50.at[c, "Integrated steelworks"]) for c in ("coal", "coke", "methane", "elec")) + (eaf + ind) * sum(float(r50.at[c, "Electric arc"]) for c in ("methane", "elec"))) / 1e6
    coke = 5326.0 * 0.0078334
    el_st = {y: sv("7000", "1211", y) / 1e3 for y in (2020, 2021, 2022)}
    hc_st = {y: sv("0100", "1211", y) for y in (2021, 2022)}
    st = [dict(item="worldsteel 2019: crude / BOF / EAF / induction / pig iron (kt)", value=f"{ws.crude_steel_2019_kt} / {ws.bof_oxygen_kt} / {ws.eaf_electric_kt} / {ws.other_kt} / {ws.pig_iron_2019_kt}", twh=np.nan, source="repository WORLDSTEEL_2019_ASEAN.csv", status="VERIFIED", grade="A"),
          dict(item="JRC-IDEES EU27 2019 final-energy boundary: BOF x 2.292 + (EAF + IF) x 1.362 MWh/t", value="", twh=jrc, source="INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv", status="EXACT", grade="C"),
          dict(item="ETSAP BAT whole route (BF-BOF 19.51 GJ/t incl. blast-furnace reductant; scrap EAF / IF 2.68 GJ/t)", value="", twh=bat, source="S0 V4_PRODUCT_ROUTE_MAP.csv", status="EXACT", grade="C"),
          dict(item="ETSAP BAT x ODA whole route", value="", twh=bat_oda, source="S0 V4_PRODUCT_ROUTE_MAP.csv", status="EXACT", grade="C"),
          dict(item="v3 s3_0 want_steel 2019 (PyPSA-Eur ratio table x worldsteel; Integrated steelworks coal + coke + gas + elec)", value="", twh=v3_want, source="s3_0_industry.py lines 187-192", status="EXACT", grade="C"),
          dict(item="UNSD 2019 iron-and-steel row in the model base: coke 5,326 kt + LPG 50 kt + fuel oil 6 kt", value="", twh=coke + 0.7238, source="industry_cache.json / SDMX", status="EXACT", grade="A"),
          dict(item="  of which coke (blast furnace + sinter; VN reports no blast-furnace transformation)", value=f"{5326 / 9836 * 1000:.0f} kg per t pig iron", twh=coke, source="SDMX 0311/1211; worldsteel pig iron", status="EXACT", grade="A"),
          dict(item="  diesel of the steel row missing from the model base (export truncated): 102 kt", value="", twh=102 * 0.01194, source="SDMX 4670/1211 2019", status="EXACT", grade="A"),
          dict(item="UNSD steel electricity (reported only from 2020): 2020 / 2021 / 2022 GWh", value=" / ".join(f"{el_st[y] * 1e3:,.0f}" for y in el_st), twh=el_st[2020], source="SDMX 7000/1211", status="VERIFIED", grade="A"),
          dict(item="  per t raw steel 2020 (USGS 19,900 kt), MWh/t", value=f"{el_st[2020] * 1e6 / (us['raw_steel_kt'][2020] * 1e3):.3f}", twh=el_st[2020] * 1e6 / (us['raw_steel_kt'][2020] * 1e3) * us["raw_steel_kt"][2019] * 1e3 / 1e6,
               source="back-cast to 2019 with USGS 2019 raw steel (C)", status="INFERENCE", grade="C"),
          dict(item="UNSD steel hard coal (reported only 2021-2022), kt", value=" / ".join(f"{hc_st[y]:,.0f}" for y in hc_st), twh=hc_st[2021] * 23.446 / 3600, source="SDMX 0100/1211", status="VERIFIED", grade="A"),
          dict(item="APEC 2022 iron and steel row (177 PJ; 20,004 kt raw steel), scaled to 2019 output", value="", twh=177 / 3.6 * us["raw_steel_kt"][2019] / us["raw_steel_kt"][2022], source="APEC2022_VN_INDUSTRY_PJ.csv x USGS", status="INFERENCE", grade="C"),
          dict(item="v3 decomposition (APEC 2022 shares): 2019 steel energy deducted", value="", twh=float(split.at["apec2022", "steel_2019_deducted_twh"]), source="tables/VN_SPLIT_VARIANTS.csv", status="EXACT", grade="C"),
          dict(item="hybrid decomposition: 2019 steel energy deducted", value="", twh=float(split.at["hybrid", "steel_2019_deducted_twh"]), source="tables/VN_SPLIT_VARIANTS.csv", status="EXACT", grade="C")]
    ST = pd.DataFrame(st); ST.to_csv(T / "VN_STEEL_2019_CHECK.csv", index=False, float_format="%.4f")
    for i, r in ST.iterrows():
        if pd.notna(r.twh):
            ev.put(f"steel2019.{i:02d}", float(r.twh), "TWh", f"{r.item} ({r.source})", r.status, r.grade)
    # ================= CEMENT: clinker ratio =================
    t22 = pd.read_excel(CEMENT_T22, sheet_name="T22", header=None)
    ed = pd.read_csv(EDGAR); ed = ed[ed.ipcc_code_2006_for_standard_report == "2.A.1"].set_index("iso")
    cem = []
    for iso, nm in T22_NAME.items():
        row = t22[t22[0].astype(str).str.startswith(nm)].iloc[0]
        u19 = float(row[2]); u23 = float(row[10])
        ck19 = float(ed.at[iso, "kt_CO2_2019"]) / 0.52 if pd.notna(ed.at[iso, "kt_CO2_2019"]) else np.nan
        ck24 = float(ed.at[iso, "kt_CO2_2024"]) / 0.52 if pd.notna(ed.at[iso, "kt_CO2_2024"]) else np.nan
        cem.append(dict(iso=iso, usgs_cement_2019_kt=u19, usgs_cement_2023_kt=u23, edgar_clinker_2019_kt=ck19, edgar_clinker_2024_kt=ck24,
                        edgar_clinker_over_usgs_cement_2019=ck19 / u19, v3_cement_2019_kt=ck19 / 0.656, v3_over_usgs_2019=ck19 / 0.656 / u19))
    CE = pd.DataFrame(cem); CE.to_csv(T / "VN_CEMENT_EDGAR_CHECK_ASEAN.csv", index=False, float_format="%.6f")
    vnr = CE.set_index("iso").loc["VN"]
    for k in ("edgar_clinker_2019_kt", "edgar_clinker_over_usgs_cement_2019", "v3_cement_2019_kt", "v3_over_usgs_2019"):
        ev.put(f"cement.vn.{k}", float(vnr[k]), "kt" if k.endswith("kt") else "ratio", "EDGAR 2025 2.A.1 / 0.52; USGS MYB 2023 cement T22", "EXACT", "B")
    same = CE[(CE.edgar_clinker_over_usgs_cement_2019 - 0.786).abs() < 0.001].iso.tolist()
    ev.put("cement.edgar_fixed_ratio_countries", ";".join(same), "list", "countries whose EDGAR 2019 clinker / USGS 2019 cement = 0.786 +- 0.001", "EXACT", "B")
    gem_cem = pd.read_csv(cm.S2W / "evidence/COVERAGE_GEM_CEMENT.csv") if (cm.S2W / "evidence/COVERAGE_GEM_CEMENT.csv").exists() else None
    chain_in["cement_usgs_2019_t"] = 105533.0e3
    # ================= PULP AND PAPER (closed-loop rule) =================
    FO = s2.fao("FO"); area = "Viet Nam"
    rows = []
    for grp, items, sector in (("pulp", PULP_ITEMS, "Pulp production"), ("paper", PAPER_LEAVES, "Paper production")):
        for it in items:
            ser = s2.series(FO, area, it)
            if not len(ser) or ser.value.dropna().empty:
                continue
            la = s2.latest_actual(ser)
            try:
                v19, f19 = s2.value(FO, area, it, 2019)
            except KeyError:
                v19, f19 = np.nan, ""
            yb = la["base_year"]
            rows.append(dict(group=grp, item=it, pypsa_eur_sector=sector, q_2019_t=v19, flag_2019=f19, grade_2019=s2.FLAG_GRADE.get(f19, "C"), base_year=yb,
                             q_base_t=la["value"], flag_base=la["flag"], grade_base=la["grade"], carried_forward_years=";".join(map(str, la["carried_forward_years"])),
                             latest_year=la["latest_year"], q_latest_t=la["latest_value"], growth_main=cm.growth(yb), q_2050_main_t=la["value"] * cm.growth(yb),
                             q_2050_literal_latest_t=la["latest_value"] * cm.growth(la["latest_year"]), q_2050_base2019_t=(v19 * cm.growth(2019) if pd.notna(v19) else np.nan),
                             series=";".join(f"{int(y)}:{v:.0f}{f}" for y, v, f in zip(ser.year, ser.value, ser.flag))))
    P = pd.DataFrame(rows); P.to_csv(T / "VN_PULP_PAPER_FAOSTAT.csv", index=False, float_format="%.6g")
    tot = P.groupby("group")[["q_2019_t", "q_2050_main_t", "q_2050_literal_latest_t", "q_2050_base2019_t"]].sum()
    for g_, r in tot.iterrows():
        for k, x in r.items():
            ev.put(f"pp.{g_}.{k}", float(x), "t", "tables/VN_PULP_PAPER_FAOSTAT.csv (FAOSTAT FO, VN)", "VERIFIED" if k == "q_2019_t" else "PROPOSED", "C")
    chem_pulp19 = float(P[P.item.isin(["Chemical wood pulp", "Dissolving wood pulp"])].q_2019_t.sum())
    chem_pulp50 = float(P[P.item.isin(["Chemical wood pulp", "Dissolving wood pulp"])].q_2050_main_t.sum())
    bl19, bl50 = chem_pulp19 * BLACK_LIQUOR_GJ_T / 3.6, chem_pulp50 * BLACK_LIQUOR_GJ_T / 3.6   # MWh, own residue (closed loop)
    e19 = {g_: today_vec(sec, float(tot.at[g_, "q_2019_t"])) for g_, sec in (("pulp", "Pulp production"), ("paper", "Paper production"))}
    tot19 = sum(sum(v.values()) for v in e19.values()); el19 = sum(v["elec"] for v in e19.values())
    # purchased 2019 = JRC intensity total minus the own residue (black liquor), electricity from the JRC structure, purchased fuels by the VN
    # APEC 2022 paper-row mix (coal 28, oil 1.8, gas 0.3 PJ); the closed-loop biomass stays outside T_v2 and is not deducted
    A = pd.read_csv(cm.REPO / cm.APEC_REL).set_index("cache_subsector").loc["paper pulp and print"]
    # coal and oil only: UNSD 2019 reports industry gas only for chemicals and non-metallic minerals (no paper gas in the 2019 base)
    fmix = {"coal": float(A.coal_pj), "oil": float(A.oil_pj)}; fs = sum(fmix.values())
    fuel_purch19 = max(0.0, tot19 - el19 - bl19)
    pp19 = {"electricity": el19, **{k: fuel_purch19 * v / fs for k, v in fmix.items()}, "gas": 0.0}
    v50 = {k: 0.0 for k in cm.OUTC}
    for g_, sec in (("pulp", "Pulp production"), ("paper", "Paper production")):
        for k, x in cm.vec2050(sec, float(tot.at[g_, "q_2050_main_t"])).items():
            v50[k] += x
    v50_main = dict(v50); v50_main["biomass"] = max(0.0, v50["biomass"] - bl50)   # purchased steam fuel in T_v2; own black liquor outside
    v50_literal = dict(v50); v50_literal["biomass"] = 0.0                          # rule read literally: all biomass rows outside T_v2
    chain_in.update(pp_2019_purchased_mwh=pp19, pp_2050_main=v50_main, pp_2050_literal=v50_literal, pp_closed_loop_2019_mwh=bl19, pp_closed_loop_2050_mwh=bl50,
                    pp_2050_biomass_rows_mwh=v50["biomass"])
    E = pd.DataFrame([dict(case="2019 total (FAOSTAT 2019 x JRC-IDEES EU27 2019 today: pulp 3.567, paper 2.581 MWh/t)", twh=tot19 / 1e6, electricity=el19 / 1e6),
                      dict(case="2019 own residue: chemical + dissolving pulp x 22 GJ/t black liquor (closed loop, outside T_v2)", twh=bl19 / 1e6),
                      dict(case="2019 purchased (deducted): electricity + coal / oil / gas by the APEC 2022 paper-row fuel mix", twh=sum(pp19.values()) / 1e6, electricity=pp19["electricity"] / 1e6,
                           coal=pp19["coal"] / 1e6, oil=pp19["oil"] / 1e6, gas=pp19["gas"] / 1e6),
                      dict(case="2019 hybrid decomposition paper row (UNSD 2019 x APEC 2022 shares), for comparison", twh=float(pd.read_csv(T / "VN_SUBSECTOR_2019_BY_MATRIX.csv").set_index("subsector").at["paper pulp and print", "hybrid"])),
                      dict(case="2050 PyPSA-Eur ratios x FAOSTAT base-year rule (all rows)", twh=sum(v50.values()) / 1e6, electricity=v50["electricity"] / 1e6, biomass=v50["biomass"] / 1e6, heat=v50["heat"] / 1e6),
                      dict(case="2050 own residue (black liquor, closed loop, outside T_v2)", twh=bl50 / 1e6),
                      dict(case="2050 explicit in T_v2 (main: PyPSA-Eur biomass rows minus own black liquor = purchased steam fuel)", twh=sum(v50_main.values()) / 1e6,
                           electricity=v50_main["electricity"] / 1e6, biomass=v50_main["biomass"] / 1e6, heat=v50_main["heat"] / 1e6),
                      dict(case="2050 explicit, rule read literally (all biomass rows outside T_v2)", twh=sum(v50_literal.values()) / 1e6, electricity=v50_literal["electricity"] / 1e6, heat=v50_literal["heat"] / 1e6)])
    E.to_csv(T / "VN_PULP_PAPER_ENERGY.csv", index=False, float_format="%.6f")
    for i, r in E.iterrows():
        ev.put(f"pp.energy.{i}", float(r.twh), "TWh", r.case, "PROPOSED" if "2050" in r.case else "INFERENCE", "C")
    # ================= GLASS (ETSAP 2020) and ALUMINA (USGS) =================
    glass20 = 2155.8e3   # ETSAP v2.1.0 production quantities, VN glass 2020 (S0 V4_DATA_SCOPE.md 4.6)
    glass19 = glass20 * G ** ((2019 - 2020) / 28 * 0.5)
    # 2019 carrier split by ETSAP BAT (electricity 1.24, fuel 4.16 GJ/t): the PyPSA-Eur 2050 glass column is all-electric and does not describe 2019
    g_tot = float(td.at["Glass production", "today_total_mwh_per_t"]) * glass19
    eg = float(rm.at["container / float", "bat_electricity_gj_per_t"]); fg = float(rm.at["container / float", "bat_fuel_or_heat_gj_per_t"])
    g19 = {"elec": g_tot * eg / (eg + fg), "fuel": g_tot * fg / (eg + fg)}
    g50 = cm.vec2050("Glass production", glass20 * cm.growth(2020))
    al19_t = us["alumina_t"][2019]; al_base = us["alumina_t"][2022]
    a19 = today_vec("Alumina production", al19_t); a50 = cm.vec2050("Alumina production", al_base * cm.growth(2022))
    chain_in.update(glass_2019={"electricity": g19["elec"], "fuel": sum(v for k, v in g19.items() if k != "elec")}, glass_2050=g50,
                    alumina_2019={"electricity": a19["elec"], "fuel": sum(v for k, v in a19.items() if k != "elec")}, alumina_2050=a50)
    GA = pd.DataFrame([dict(product="glass", activity_2019_t=glass19, activity_basis="ETSAP 2020 2,155.8 kt back-cast to 2019 by the growth rule (R3, C)", base_year=2020,
                            energy_2019_twh=sum(g19.values()) / 1e6, electricity_2019_twh=g19["elec"] / 1e6, energy_2050_twh=sum(g50.values()) / 1e6, deducted_from="non-metallic minerals row (dispersed), excess from other"),
                       dict(product="alumina", activity_2019_t=al19_t, activity_basis="USGS MYB 2022 VN table 1 (A); base year 2022 (last value)", base_year=2022,
                            energy_2019_twh=sum(a19.values()) / 1e6, electricity_2019_twh=a19["elec"] / 1e6, energy_2050_twh=sum(a50.values()) / 1e6, deducted_from="other (UNSD and APEC have no non-ferrous energy)"),
                       dict(product="lime (not made explicit)", activity_2019_t=us.get("lime_t", {}).get(2019, 665000.0), activity_basis="USGS 2019 665 kt (e); no PyPSA-Eur lime sector: stays in the non-metallic minerals dispersed row",
                            base_year=np.nan, energy_2019_twh=np.nan, electricity_2019_twh=np.nan, energy_2050_twh=np.nan, deducted_from="none"),
                       dict(product="copper (not made explicit)", activity_2019_t=19200.0, activity_basis="USGS 2019 primary smelter 19.2 kt x JRC 3.64 MWh/t = 0.07 TWh: below materiality", base_year=np.nan,
                            energy_2019_twh=19200 * float(td.at["Other non-ferrous metals", "today_total_mwh_per_t"]) / 1e6, electricity_2019_twh=np.nan, energy_2050_twh=np.nan, deducted_from="none")])
    GA.to_csv(T / "VN_GLASS_ALUMINA.csv", index=False, float_format="%.6f")
    for r in GA.itertuples():
        for k in ("energy_2019_twh", "energy_2050_twh"):
            if pd.notna(getattr(r, k)):
                ev.put(f"{r.product.split()[0]}.{k}", float(getattr(r, k)), "TWh", r.activity_basis, "PROPOSED" if "2050" in k else "INFERENCE", "C")
    # ================= ETHYLENE: sensitivity only (no cracker operating in 2019) =================
    sfi = pd.read_excel(cm.S2W / "downloads/05_sfi_ethylene/Global_Ethylene_Production_Database_December_2025.xlsx", sheet_name=None)
    sh = [k for k in sfi if "thylene" in k or "Database" in k or "data" in k.lower()]
    df = sfi[sh[0]] if sh else list(sfi.values())[0]
    ccol = [c for c in df.columns if str(c).lower().startswith("country")][0]
    vnu = df[df[ccol].astype(str).str.contains("Viet", case=False)].copy()
    vnu.to_csv(T / "VN_ETHYLENE_UNITS_SFI.csv", index=False)
    capcol = [c for c in vnu.columns if "capacity" in str(c).lower()]
    cap_t = float(pd.to_numeric(vnu[capcol[0]], errors="coerce").sum()) * (1e3 if pd.to_numeric(vnu[capcol[0]], errors="coerce").sum() < 1e5 else 1.0) if capcol else np.nan
    hvc_ratio = 1.697   # S2 (GEM GCT same-plant olefin capacities, ID); VN-specific value not derived (C)
    eth = []
    for lv, u in U_ETH.items():
        q50 = cap_t * u * hvc_ratio * cm.growth(2023)
        v = cm.vec2050("HVC", q50); v.pop("naphtha", None)
        eth.append(dict(level=lv, utilisation=u, ethylene_capacity_t=cap_t, hvc_2050_t=q50, energy_2050_twh=sum(v.values()) / 1e6, base_year=2023,
                        note="R4 sensitivity: Long Son Petrochemicals started in 2023; nothing in the 2019 base; deduction would come from the chemical row"))
    ET = pd.DataFrame(eth); ET.to_csv(T / "VN_ETHYLENE_SENS.csv", index=False, float_format="%.6f")
    ev.put("ethylene.capacity_t", cap_t, "t", "SFI 2025-12 VN units (operating capacity)", "VERIFIED", "B")
    ev.put("ethylene.2050_central_twh", float(ET.set_index("level").at["central", "energy_2050_twh"]), "TWh", "capacity x 0.85 x 1.697 x growth(2023) x PyPSA-Eur HVC without naphtha", "PROPOSED", "C")
    ev.extra = dict(chain_inputs=chain_in, usgs=us)
    ev.write(cm.WORK / "evidence/_products_evidence.json")
    cm.jdump(chain_in, cm.WORK / "evidence/_chain_inputs.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 110)
    print(ST[["item", "value", "twh"]].round(3).to_string()); print(CE.round(4).to_string())
    print(P[["group", "item", "q_2019_t", "flag_2019", "base_year", "q_base_t", "q_2050_main_t"]].to_string()); print(E.round(3).to_string()); print(GA.round(3).to_string()); print(ET.round(3).to_string())
    print(vnu.iloc[:, :12].to_string())


if __name__ == "__main__":
    main()
