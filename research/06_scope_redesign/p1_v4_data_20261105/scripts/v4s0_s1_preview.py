"""V4 S0 section 7 (PROPOSED): order-of-magnitude preview for the Indonesian pilot - national activity x unit energy under the candidate unit-energy
bases, against the UNSD 2019 rows used by v3 and the v3 2050 sub-sectors. Nothing here enters the model; facility-level work is S1.

    python scripts/v4s0_s1_preview.py --work <work dir> --repo /home/jin/wt_v4_data
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

GJ = 3.6


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); ap.add_argument("--repo", type=Path, required=True); a = ap.parse_args()
    ev = a.work / "evidence"; R = a.repo / "research_inputs"
    m = pd.read_csv(a.work / "V4_PRODUCT_ROUTE_MAP.csv")
    today = pd.read_csv(R / "registry_v5/INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv").set_index("sector")
    pe2050 = pd.read_csv(R / "registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", index_col=0)
    v2 = pd.read_csv(R / "demand_v5/INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"); v2 = v2[v2.country == "ID"]
    rule = pd.read_csv(R / "demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country").loc["ID"]
    base = pd.read_csv(R / "demand_v5/INDUSTRY_OUTPUT_BASE_M08B.csv").set_index("country").loc["ID"]
    sub = pd.read_csv(ev / "V3_SUBSECTOR_2050_BY_COUNTRY.csv").set_index(["country", "subsector"])
    ob = pd.read_csv(ev / "V3_OTHER_BUCKET_BY_COUNTRY.csv").set_index("country").loc["ID"]
    cap = pd.read_csv(ev / "COVERAGE_GEM_STEEL_OPERATING_CAPACITY_KTPA.csv").set_index("iso").loc["ID"]
    etp = pd.read_csv(ev / "COVERAGE_ETSAP_PRODUCTION_ASEAN.csv"); etp = etp[etp.country == "ID"]
    chem = pd.read_csv(ev / "COVERAGE_GEM_CHEM_OPERATING_CAPACITY_KTPA_BY_PRODUCT_GROUP.csv").set_index("Product Group")["ID"]
    G = float(rule.gdp_growth_2022_2050)
    grow = lambda y: G ** ((2050 - y) / 28.0 * 0.5)
    sec = lambda prod, route=None: m[(m["product"] == prod) & ((m.route == route) if route else True)].iloc[0]
    rows = []
    # ---- steel: worldsteel 2024 split by operating capacity (BOF vs EAF) -------------------------------------------------------------------
    q24 = float(base.steel_base_kt) * 1e3; f_bof = cap.bof / (cap.bof + cap.eaf)
    bof, eaf = q24 * f_bof, q24 * (1 - f_bof)
    s_bof, s_eaf = sec("crude steel", "BF-BOF"), sec("crude steel", "scrap EAF / IF")
    etsap_twh = (bof * (s_bof.base_electricity_mwh_per_t + s_bof.base_fuel_mwh_per_t) + eaf * (s_eaf.base_electricity_mwh_per_t + s_eaf.base_fuel_mwh_per_t)) / 1e6
    bat_twh = (bof * (s_bof.bat_electricity_gj_per_t + s_bof.bat_fuel_or_heat_gj_per_t) + eaf * (s_eaf.bat_electricity_gj_per_t + s_eaf.bat_fuel_or_heat_gj_per_t)) / GJ / 1e6
    jrc_twh = (bof * float(today.at["Integrated steelworks", "today_total_mwh_per_t"]) + eaf * float(today.at["Electric arc", "today_total_mwh_per_t"])) / 1e6
    unsd19 = float(v2[(v2.subsector == "iron and steel")].mwh_2019.sum()) / 1e6
    rows += [dict(item="steel", basis="activity", value=q24 / 1e6, unit="Mt crude steel 2024 (worldsteel, v3 base)", grade="B", note=f"BOF share {f_bof:.3f} from GEM operating capacity (BOF {cap.bof:.0f} / EAF {cap.eaf:.0f} kt)"),
             dict(item="steel", basis="ETSAP BAT, no inefficiency", value=bat_twh, unit="TWh base year 2024", grade="C", note="whole route incl. BF reductant"),
             dict(item="steel", basis="ETSAP BAT x ODA I&S (el 1.27, fuel 1.351)", value=etsap_twh, unit="TWh base year 2024", grade="C", note="whole route incl. BF reductant"),
             dict(item="steel", basis="JRC-IDEES EU27 2019 today ratios (Integrated steelworks / Electric arc)", value=jrc_twh, unit="TWh base year 2024", grade="C", note="final-energy boundary (no BF / coke-oven transformation)"),
             dict(item="steel", basis="UNSD 2019 iron-and-steel row used by v3", value=unsd19, unit="TWh 2019", grade="B", note="production 2019 USGS 8.565 Mt crude steel"),
             dict(item="steel", basis="v3 2050 steel (H2-DRI 30 % + EAF 70 %)", value=float(sub.loc[("ID", "steel"), "twh_2050"]), unit="TWh 2050", grade="C", note=f"{float(rule.steel_2050_mt):.2f} Mt in 2050")]
    # ---- cement: USGS 2023 ----------------------------------------------------------------------------------------------------------------
    c23 = float(base.cement_base_kt) * 1e3; sc = sec("clinker / cement")
    c19 = float(v2[(v2.subsector == "cement")].mwh_2019.sum()) / 1e6
    rows += [dict(item="cement", basis="activity", value=c23 / 1e6, unit="Mt cement 2023 (USGS T22, v3 base)", grade="B", note=""),
             dict(item="cement", basis="ETSAP BAT x ODA NMM (el 2.234, fuel 1.792), clinker 0.6", value=c23 * (sc.base_electricity_mwh_per_t + sc.base_fuel_mwh_per_t) / 1e6, unit="TWh base year 2023", grade="C", note=""),
             dict(item="cement", basis="PyPSA-Eur Cement ratio (= today, 0.8655 MWh/t)", value=c23 * float(today.at["Cement", "today_total_mwh_per_t"]) / 1e6, unit="TWh base year 2023", grade="C", note="v3 basis"),
             dict(item="cement", basis="v3 2019 cement energy (EDGAR clinker / 0.52, taken from other)", value=c19, unit="TWh 2019", grade="C", note="ID has no UNSD NMM row"),
             dict(item="cement", basis="v3 2050 cement", value=float(sub.loc[("ID", "cement"), "twh_2050"]), unit="TWh 2050", grade="C", note=f"{float(rule.cement_2050_mt):.1f} Mt in 2050")]
    # ---- pulp and paper: ETSAP 2018 national production ---------------------------------------------------------------------------------
    pulp = float(etp[(etp["product"] == "Chemical pulp")].kt.sum()) * 1e3
    paper = float(etp[etp["product"].isin(["Graphical paper", "Hygiene paper", "Packaging paper", "Technical packaging"])].kt.sum()) * 1e3
    sp, sq = sec("chemical pulp"), sec("paper")
    pp_base = (pulp * (sp.base_electricity_mwh_per_t + sp.base_fuel_mwh_per_t) + paper * (sq.base_electricity_mwh_per_t + sq.base_fuel_mwh_per_t)) / 1e6
    pp_2050 = (pulp * float(pe2050["Pulp production"].drop(["process emission", "process emission from feedstock"]).sum()) + paper * float(pe2050["Paper production"].drop(["process emission", "process emission from feedstock"]).sum())) / 1e6 * grow(2018)
    rows += [dict(item="pulp and paper", basis="activity", value=(pulp + paper) / 1e6, unit=f"Mt (chemical pulp {pulp/1e6:.2f} + paper {paper/1e6:.2f}) 2018 ETSAP/FAO", grade="B", note=""),
             dict(item="pulp and paper", basis="ETSAP BAT x ODA P&P (el 1.313, fuel 1.500)", value=pp_base, unit="TWh base year 2018", grade="C", note="black liquor covers much of the pulp heat"),
             dict(item="pulp and paper", basis="PyPSA-Eur 2050 ratios x v3 growth rule G^((2050-2018)/28 x 0.5)", value=pp_2050, unit="TWh 2050", grade="C", note=f"growth factor {grow(2018):.3f}; would be deducted from ID other (no UNSD paper row)")]
    # ---- chemicals: GEM operating capacity x 0.8 (assumed utilisation, sensitivity 0.7-0.9) ----------------------------------------------
    u = 0.8
    for grp, prod in (("olefins", "olefins (ethylene, propylene)"), ("aromatics", "aromatics"), ("methanol", "methanol")):
        s = sec(prod); q = float(chem.get(grp, 0.0)) * 1e3 * u
        rows.append(dict(item=f"chemicals: {grp}", basis="GEM capacity x 0.8 x ETSAP BAT energy (no inefficiency; feedstock excluded)", value=q * (s.bat_electricity_gj_per_t + s.bat_fuel_or_heat_gj_per_t) / GJ / 1e6,
                         unit="TWh base year", grade="C", note=f"capacity {float(chem.get(grp, 0.0)):.0f} kt; ID has a UNSD chemical row (v3 dispersed 49.9 TWh in 2050): deduct there first"))
    rows += [dict(item="other bucket", basis="v3 2019-equivalent", value=float(ob.other_2019_v3_twh), unit="TWh 2019", grade="C", note="target of the reduction"),
             dict(item="other bucket", basis="v3 2050 network-bound", value=float(ob.other_2050_v3_twh), unit="TWh 2050", grade="C", note="")]
    T = pd.DataFrame(rows); T.to_csv(ev / "S1_ID_PREVIEW.csv", index=False, float_format="%.4f")
    print(T.round(3).to_string())
    # ---- every country: candidate sub-sectors beyond steel / cement / ammonia / non-ferrous, 2050-equivalent without route change (INFERENCE) ------
    # base-year energy x v3 growth rule G^((2050 - base) / 28 x 0.5); deducted from the v3 dispersed row of the same UNSD sub-sector where it exists,
    # the excess (and everything in countries without that row) from other. Chemicals: GEM operating capacity x 0.8 x ETSAP BAT energy (no feedstock,
    # no inefficiency); pulp, paper, glass, lime: ETSAP national production x BAT x ODA factor.
    allrule = pd.read_csv(R / "demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country")
    allp = pd.read_csv(ev / "COVERAGE_ETSAP_PRODUCTION_ASEAN.csv")
    chem_all = pd.read_csv(ev / "COVERAGE_GEM_CHEM_OPERATING_CAPACITY_KTPA_BY_PRODUCT_GROUP.csv").set_index("Product Group")
    disp = pd.read_csv(ev / "V3_DISPERSED_BY_UNSD_ROW.csv").groupby(["country", "unsd_row"]).twh_2050.sum()
    obc = pd.read_csv(ev / "V3_OTHER_BUCKET_BY_COUNTRY.csv").set_index("country")
    out = []
    for c in ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "VN"]:
        g = lambda y: float(allrule.at[c, "gdp_growth_2022_2050"]) ** ((2050 - y) / 28.0 * 0.5)
        p = allp[allp.country == c]
        cand = {}
        pulp = float(p[p["product"] == "Chemical pulp"].kt.sum()) * 1e3; paper = float(p[p["product"].isin(["Graphical paper", "Hygiene paper", "Packaging paper", "Technical packaging"])].kt.sum()) * 1e3
        cand["paper pulp and print"] = (pulp * (sp.base_electricity_mwh_per_t + sp.base_fuel_mwh_per_t) + paper * (sq.base_electricity_mwh_per_t + sq.base_fuel_mwh_per_t)) / 1e6 * g(2018)
        sg_, sl_ = sec("glass"), sec("lime")
        cand["non-metallic minerals"] = (float(p[p["product"] == "Glass"].kt.sum()) * 1e3 * (sg_.base_electricity_mwh_per_t + sg_.base_fuel_mwh_per_t) * g(2020)
                                         + float(p[p["product"] == "Lime"].kt.sum()) * 1e3 * (sl_.base_electricity_mwh_per_t + sl_.base_fuel_mwh_per_t) * g(2018)) / 1e6
        ch = 0.0
        for grp, prod in (("olefins", "olefins (ethylene, propylene)"), ("aromatics", "aromatics"), ("methanol", "methanol")):
            s = sec(prod); ch += float(chem_all.at[grp, c]) * 1e3 * 0.8 * (s.bat_electricity_gj_per_t + s.bat_fuel_or_heat_gj_per_t) / GJ
        cand["chemical and petrochemical"] = ch / 1e6 * g(2024)
        for row, e in cand.items():
            d_avail = float(disp.get((c, row), 0.0))
            from_disp = min(e, d_avail); from_other = e - from_disp
            out.append(dict(country=c, unsd_row=row, explicit_2050eq_twh=e, v3_dispersed_row_twh=d_avail, from_dispersed_twh=from_disp, from_other_twh=from_other))
    O = pd.DataFrame(out)
    tot = O.groupby("country")[["explicit_2050eq_twh", "from_dispersed_twh", "from_other_twh"]].sum()
    tot["other_2050_v3_twh"] = obc.other_2050_v3_twh.reindex(tot.index)
    tot["other_reduction_share"] = tot.from_other_twh / tot.other_2050_v3_twh
    O.to_csv(ev / "S1_OTHER_REDUCTION_PREVIEW.csv", index=False, float_format="%.4f"); tot.to_csv(ev / "S1_OTHER_REDUCTION_PREVIEW_BY_COUNTRY.csv", float_format="%.4f")
    print(tot.round(3).to_string()); print("ASEAN from other", round(tot.from_other_twh.sum(), 2), "of", round(obc.at["ASEAN11", "other_2050_v3_twh"], 2))


if __name__ == "__main__":
    main()
