"""V4 S2 section 2 (decision 203): products added to the Indonesian industry split - pulp and paper, ethylene (HVC), sugar (check), palm-oil milling (check).

    PYTHONHASHSEED=0 python scripts/v4s2_products.py          (WSL pypsa-earth python; read-only on the repository)

1. Pulp and paper (FAOSTAT FO, file of 2026-11-06): production by item with flag and grade; aggregates checked against their components;
   base year per item = the last year that carries new information (later E / I values equal to it are carry-forwards), literal 2024 as a
   sensitivity; 2050 = q(y_b) x G^((2050 - y_b) / 28 x 0.5) (S0 R1-R2). Products -> PyPSA-Eur sectors 'Pulp production' / 'Paper production'.
   2019 energy = FAOSTAT 2019 x JRC-IDEES-2021 EU27 2019 specific energy (today table), carrier structure of the PyPSA-Eur ratio column (the S1
   convention); this is what leaves the 'other' bucket in 2019 (ID has no UNSD paper row). 2050 = 2050 activity x PyPSA-Eur 2050 ratios.
   Comparison with the S0 section 7.5 preview and with ETSAP BAT (x ODA). Biomass check line: the PyPSA-Eur biomass part and the black liquor of
   the chemical pulp (ETSAP 22 GJ/t, route map) against the UNSD 'other' biomass. Spatial: SFI pulp & paper mills (2025-07) -> v3 onshore nodes.
2. Ethylene: SFI operating cracker capacity x an explicit utilisation range (grade C, no plant output), HVC per t ethylene from the GEM chemicals
   capacities of the same plant; energy use only (feedstock in NEU, outside T_v2); 2019 energy = JRC-IDEES EU27 HVC energy-use intensity (s3_0
   convention) with ETSAP BAT as cross-check; 2050 = PyPSA-Eur HVC ratio without naphtha; deducted from the UNSD chemicals row (dispersed).
3. Sugar: FAOSTAT sugar cane x IRENA 2017 process-residue factor against UNSD bagasse (consistency only), 2010-2022 ratio series.
4. Palm-oil milling: FAOSTAT oil palm fruit / palm oil x IRENA 2022 Box 4 mass balance x residue energy content (IRENA 2017 convention, ERIA 2024
   PKS NCV): mill fibre and shell energy as a check line for section 3; suggestion on an explicit sub-sector (only a suggestion).
Outputs s2/ID_PULP_PAPER_*.csv, s2/ID_ETHYLENE.csv, s2/ID_SUGAR_PALM_CHECK.csv, s2/_products_evidence.json (incl. the inputs of the chain runs).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4s2_common as cm   # noqa: E402

PULP_ITEMS = ["Chemical wood pulp", "Dissolving wood pulp", "Mechanical and semi-chemical wood pulp", "Pulp from fibres other than wood"]
PAPER_LEAVES = ["Newsprint", "Printing and writing papers, coated", "Printing and writing papers, uncoated, woodfree", "Printing and writing papers, uncoated, mechanical",
                "Household and sanitary papers", "Case materials", "Cartonboard", "Wrapping papers", "Other papers mainly for packaging",
                "Other paper and paperboard, not elsewhere specified"]
PAPER_AGG = {"Printing and writing papers": ["Printing and writing papers, coated", "Printing and writing papers, uncoated, woodfree", "Printing and writing papers, uncoated, mechanical"],
             "Other paper and paperboard": ["Household and sanitary papers", "Case materials", "Cartonboard", "Wrapping papers", "Other papers mainly for packaging",
                                            "Other paper and paperboard, not elsewhere specified"],
             "Chemical wood pulp": ["Chemical wood pulp, sulphate, bleached", "Chemical wood pulp, sulphate, unbleached", "Chemical wood pulp, sulphite"]}
SFI = "downloads/04_sfi_pulp_paper/SFI_ALD_Pulp_Paper_Database_July_2025.xlsx"
SFI_ETH = "downloads/05_sfi_ethylene/Global_Ethylene_Production_Database_December_2025.xlsx"
GEM_CHEM = "downloads/03_gem_chemicals/Plant-level-data-Global-Chemicals-Tracker-November-2026-V1.xlsx"
U_ETH = {"low": 0.75, "central": 0.85, "high": 0.95}   # explicit assumption (grade C): no plant output on disk
BLACK_LIQUOR_GJ_T = 22.0   # V4_PRODUCT_ROUTE_MAP.csv chemical pulp note: ETSAP v2.1.0 black liquor 22 GJ/t pulp output (own fuel)
IRENA_BOX4 = dict(fibre=0.144, shell=0.064, efb=0.21, pome=0.583, cpo=0.24)   # IRENA 2022 Box 4 p.40 (Eriza 2010), registered in biomass_v5
RES_GJ_T = 15.0   # IRENA 2017 p.7: residues 15 GJ/t (repository BIOMASS_POTENTIAL_2050.csv lhv_gj_per_t)
PKS_KCAL = (3500.0, 4200.0)   # ERIA/IEEJ 2024 Table 3.8: PKS 3,500-4,200 kcal/kg, NCV > 3,500 kcal/kg (biomass_v5/sources excerpt)
KCAL_GJ = 4.1868e-3
SUGAR_PF = 0.2   # IRENA 2017 Table R3: sugar cane processing residue factor (biomass_v5/sources/IRENA2017_TABLE_R3_PARSED.csv)


def main():
    W = cm.WORK; out = W / "s2"; out.mkdir(exist_ok=True)
    ev = cm.Ev("2")
    FO, QCL = cm.fao("FO"), cm.fao("QCL")
    G = cm.gdp_growth("ID")
    ev.put("growth.G_2022_2050", G, "-", "INDUSTRY_OUTPUT_2050_M08B.csv gdp_growth_2022_2050 (AEO8 table D.2)", "VERIFIED", "B")
    for y in (2017, 2019, 2021, 2023, 2024):
        ev.put(f"growth.factor_from_{y}", cm.growth(y), "-", "S0 R2: G^((2050 - y_b)/28 x 0.5)", "EXACT", "B")

    # ================================================= 1. PULP AND PAPER ========================================================
    rows = []
    for agg, leaves in PAPER_AGG.items():   # aggregate identities in 2019
        a, fa = cm.value(FO, "Indonesia", agg, 2019)
        s = 0.0
        for l in leaves:
            try:
                s += cm.value(FO, "Indonesia", l, 2019)[0]
            except KeyError:
                pass
        ev.put(f"pp.aggregate_check.{agg}", a - s, "t", f"FAOSTAT FO 2019: {agg} minus its components", "EXACT", "B")
        if abs(a - s) > 1:
            raise ValueError(f"{agg}: aggregate {a} != components {s}")
    tday = cm.ratios_today(); r50 = cm.ratios_2050()
    for grp, items, sector in (("pulp", PULP_ITEMS, "Pulp production"), ("paper", PAPER_LEAVES, "Paper production")):
        for it in items:
            s = cm.series(FO, "Indonesia", it)
            if not len(s) or s.value.dropna().empty:
                continue
            la = cm.latest_actual(s)
            v19, f19 = cm.value(FO, "Indonesia", it, 2019)
            rows.append(dict(group=grp, item=it, pypsa_eur_sector=sector, q_2019_t=v19, flag_2019=f19, grade_2019=cm.FLAG_GRADE.get(f19, "C"),
                             base_year=la["base_year"], q_base_t=la["value"], flag_base=la["flag"], grade_base=la["grade"], carried_forward_years=";".join(map(str, la["carried_forward_years"])),
                             latest_year=la["latest_year"], q_latest_t=la["latest_value"], flag_latest=la["latest_flag"],
                             growth_main=cm.growth(la["base_year"]), q_2050_main_t=la["value"] * cm.growth(la["base_year"]),
                             q_2050_literal2024_t=la["latest_value"] * cm.growth(la["latest_year"]), q_2050_base2019_t=v19 * cm.growth(2019),
                             series=";".join(f"{int(y)}:{v:.0f}{f}" for y, v, f in zip(s.year, s.value, s.flag))))
    P = pd.DataFrame(rows)
    P["mapping_note"] = P.item.map({
        "Chemical wood pulp": "kraft (sulphate) pulp -> Pulp production (JRC-IDEES pulp: wood preparation, pulping thermal / electric, cleaning)",
        "Dissolving wood pulp": "chemical pulp for viscose -> Pulp production (INFERENCE: same route class as kraft; acid sulphite / pre-hydrolysis kraft)",
        "Mechanical and semi-chemical wood pulp": "-> Pulp production (mechanical pulping is electricity-intensive; PyPSA-Eur has one pulp column; 0 from 2021)",
        "Pulp from fibres other than wood": "-> Pulp production (non-wood; constant 105 kt since 2010, carry-forward)"}).fillna("-> Paper production (one PyPSA-Eur column for all paper and paperboard)")
    P.to_csv(out / "ID_PULP_PAPER_FAOSTAT.csv", index=False, float_format="%.6g")
    tot = P.groupby("group")[["q_2019_t", "q_2050_main_t", "q_2050_literal2024_t", "q_2050_base2019_t"]].sum()
    for g_, r in tot.iterrows():
        for k, v in r.items():
            ev.put(f"pp.{g_}.{k}", v, "t", "s2/ID_PULP_PAPER_FAOSTAT.csv (FAOSTAT FO)", "VERIFIED" if k == "q_2019_t" else "PROPOSED (rule)", "B/C")
    for r in P.itertuples():
        ev.put(f"pp.item.{r.item}.q2019", r.q_2019_t, "t", f"FAOSTAT FO 2019 flag {r.flag_2019}", "VERIFIED", r.grade_2019)
        ev.put(f"pp.item.{r.item}.base_year", r.base_year, "year", "last year with new information", "PROPOSED (rule)", r.grade_base)
        ev.put(f"pp.item.{r.item}.q_base", r.q_base_t, "t", f"FAOSTAT FO {r.base_year} flag {r.flag_base}", "VERIFIED", r.grade_base)

    def today_vec(sector, t):   # S1 convention: JRC-IDEES EU27 2019 today total, carrier structure of the PyPSA-Eur ratio column
        cars = ("elec", "coal", "coke", "methane", "biomass", "hydrogen", "heat")
        col = r50[sector]; tf = float(sum(col[c] for c in cars)); T = float(tday.at[sector, "today_total_mwh_per_t"])
        return {c: float(col[c]) / tf * T * t for c in cars}
    e19 = {g_: today_vec(sec, float(tot.at[g_, "q_2019_t"])) for g_, sec in (("pulp", "Pulp production"), ("paper", "Paper production"))}
    d19_el = sum(e19[g_]["elec"] for g_ in e19); d19_tot = sum(sum(v.values()) for v in e19.values()); d19_fuel = d19_tot - d19_el
    d19_bio_part = sum(e19[g_]["biomass"] for g_ in e19)
    ev.put("pp.2019.energy_total", d19_tot / 1e6, "TWh", "FAOSTAT 2019 x JRC-IDEES EU27 2019 today (pulp 3.567, paper 2.581 MWh/t)", "INFERENCE", "C")
    ev.put("pp.2019.electricity", d19_el / 1e6, "TWh", "PyPSA-Eur ratio column structure scaled to the today total (S1 convention)", "INFERENCE", "C")
    ev.put("pp.2019.fuel", d19_fuel / 1e6, "TWh", "thermal part (biomass + low-enthalpy heat of the PyPSA-Eur structure)", "INFERENCE", "C")
    ev.put("pp.2019.biomass_part", d19_bio_part / 1e6, "TWh", "biomass part of the structure (black liquor, bark in EU27)", "INFERENCE", "C")
    for g_ in e19:
        ev.put(f"pp.2019.{g_}.total", sum(e19[g_].values()) / 1e6, "TWh", "FAOSTAT 2019 x JRC-IDEES EU27 2019", "INFERENCE", "C")
    rm = pd.read_csv(W / "V4_PRODUCT_ROUTE_MAP.csv").set_index("product")
    et = {}
    for g_, prod in (("pulp", "chemical pulp"), ("paper", "paper")):
        q = float(tot.at[g_, "q_2019_t"]); z = rm.loc[prod]
        et[g_] = dict(bat=q * (float(z.bat_electricity_gj_per_t) + float(z.bat_fuel_or_heat_gj_per_t)) / 3.6, bat_oda=q * (float(z.base_electricity_mwh_per_t) + float(z.base_fuel_mwh_per_t)))
        ev.put(f"pp.2019.{g_}.etsap_bat", et[g_]["bat"] / 1e6, "TWh", "ETSAP v2.1.0 BAT (route map)", "INFERENCE", "C")
        ev.put(f"pp.2019.{g_}.etsap_bat_oda", et[g_]["bat_oda"] / 1e6, "TWh", "ETSAP BAT x ODA (route map; S0 preview method)", "INFERENCE", "C")
    # 2050
    cases = {"main": "q_2050_main_t", "literal2024": "q_2050_literal2024_t", "base2019": "q_2050_base2019_t"}
    e50 = {}
    for case, colname in cases.items():
        v = {k: 0.0 for k in cm.OUTC}
        for g_, sec in (("pulp", "Pulp production"), ("paper", "Paper production")):
            for k, x in cm.vec2050(sec, float(tot.at[g_, colname])).items():
                v[k] += x
        e50[case] = v
        ev.put(f"pp.2050.{case}.total", sum(v.values()) / 1e6, "TWh", f"{colname} x PyPSA-Eur 2050 ratios (elec, biomass, heat)", "PROPOSED (quantified)", "C")
        for k in ("electricity", "biomass", "heat"):
            ev.put(f"pp.2050.{case}.{k}", v[k] / 1e6, "TWh", "PyPSA-Eur v2025.07.0 ratio table", "PROPOSED (quantified)", "C")
    # S0 preview (V4_DATA_SCOPE.md 7.5): ETSAP x ODA 2018 75.9 TWh, 2050 111.6 TWh
    s0 = pd.read_csv(W / "evidence/S1_ID_PREVIEW.csv")
    ev.extra["s0_preview_rows"] = s0.astype(str).to_dict("records")
    bl = float(P[P.item.isin(["Chemical wood pulp", "Dissolving wood pulp"])].q_2019_t.sum()) * BLACK_LIQUOR_GJ_T / 3.6
    ev.put("pp.2019.black_liquor_etsap", bl / 1e6, "TWh", "chemical + dissolving pulp 2019 x 22 GJ/t (ETSAP, route map note)", "INFERENCE", "C")
    E = pd.DataFrame([dict(case="2019 deduction (FAOSTAT 2019 x JRC-IDEES today)", basis="main", total_twh=d19_tot / 1e6, electricity_twh=d19_el / 1e6, fuel_twh=d19_fuel / 1e6,
                           biomass_part_twh=d19_bio_part / 1e6, pulp_twh=sum(e19["pulp"].values()) / 1e6, paper_twh=sum(e19["paper"].values()) / 1e6)]
                     + [dict(case="2019 ETSAP BAT (no ODA)", basis="comparison", total_twh=(et["pulp"]["bat"] + et["paper"]["bat"]) / 1e6, pulp_twh=et["pulp"]["bat"] / 1e6, paper_twh=et["paper"]["bat"] / 1e6),
                        dict(case="2019 ETSAP BAT x ODA (S0 preview method)", basis="comparison", total_twh=(et["pulp"]["bat_oda"] + et["paper"]["bat_oda"]) / 1e6, pulp_twh=et["pulp"]["bat_oda"] / 1e6, paper_twh=et["paper"]["bat_oda"] / 1e6),
                        dict(case="2019 black liquor (chemical + dissolving pulp x 22 GJ/t, ETSAP)", basis="biomass check", total_twh=bl / 1e6)]
                     + [dict(case=f"2050 {c} (PyPSA-Eur 2050 ratios)", basis=c, total_twh=sum(v.values()) / 1e6, electricity_twh=v["electricity"] / 1e6, biomass_part_twh=v["biomass"] / 1e6,
                             heat_low_twh=v["heat"] / 1e6) for c, v in e50.items()])
    E.to_csv(out / "ID_PULP_PAPER_ENERGY.csv", index=False, float_format="%.6f")
    # ---- spatial: SFI mills -> nodes
    import geopandas as gpd
    sys.path.insert(0, str(W / "scripts"))
    import v4s1_facilities as f1   # noqa: E402  (node_of only)
    regions = gpd.read_file(cm.MAIN / "research_inputs/renewable_v5/regions_onshore.geojson")
    S = pd.read_excel(W / SFI, sheet_name="SFI_Pulp_Paper_Database")
    S = S[S.country.eq("Indonesia")].copy()
    S["cap_pulp"] = pd.to_numeric(S["capacity_pulp (tonnes per year) "], errors="coerce"); S["cap_paper"] = pd.to_numeric(S["capacity_paper (tonnes per year)"], errors="coerce")
    S["lat"], S["lon"] = S.latitude.astype(float), S.longitude.astype(float)
    S["node"], S["node_method"] = f1.node_of(S, regions)
    q_pulp, q_paper = float(tot.at["pulp", "q_2019_t"]), float(tot.at["paper", "q_2019_t"])
    kp, kq = float(S.cap_pulp.sum()), float(S.cap_paper.sum())
    u_p = q_pulp / kp
    S["w_pulp"] = S.cap_pulp.fillna(0.0) * u_p
    paper_types = ~S.plant_type.astype(str).str.fullmatch("Pulp")
    n_unknown = int((S.cap_paper.isna() & paper_types).sum())
    resid = max(0.0, q_paper - kq)
    S["w_paper_main"] = np.where(S.cap_paper.notna(), S.cap_paper.fillna(0.0) * min(1.0, q_paper / kq), np.where(paper_types, resid / max(1, n_unknown), 0.0))
    S["w_paper_known_only"] = S.cap_paper.fillna(0.0) / kq * q_paper
    ev.put("pp.sfi.mills", len(S), "mills", "SFI 2025-07", "VERIFIED", "B")
    ev.put("pp.sfi.pulp_capacity", kp, "t", "SFI 2025-07 (mills with a value)", "VERIFIED", "B")
    ev.put("pp.sfi.pulp_mills_with_capacity", int(S.cap_pulp.notna().sum()), "mills", "SFI 2025-07", "VERIFIED", "B")
    ev.put("pp.sfi.u_pulp_2019", u_p, "-", "FAOSTAT 2019 pulp / SFI pulp capacity", "INFERENCE", "C")
    ev.put("pp.sfi.paper_capacity", kq, "t", "SFI 2025-07", "VERIFIED", "B")
    ev.put("pp.sfi.paper_mills_with_capacity", int(S.cap_paper.notna().sum()), "mills", "SFI 2025-07", "VERIFIED", "B")
    ev.put("pp.sfi.paper_mills_without_capacity", n_unknown, "mills", "SFI 2025-07 (plant type not pulp-only)", "VERIFIED", "B")
    ev.put("pp.sfi.mills_outside_regions", int((S.node_method != "point in region").sum()), "mills", "nearest node", "VERIFIED", "B")
    S[["uid", "plant_name", "state", "lat", "lon", "accuracy", "status", "plant_type", "products", "cap_pulp", "cap_paper", "node", "node_method", "w_pulp", "w_paper_main", "w_paper_known_only"]].to_csv(
        out / "ID_PULP_PAPER_MILLS_SFI.csv", index=False, float_format="%.6g")
    v3s = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_NODE_SHARES_V3.csv")
    v3o = v3s[(v3s.country == "ID") & (v3s.subsector == "other")].set_index("node").share   # same node names as regions_onshore ('ID_...')
    pul50 = sum(cm.vec2050("Pulp production", float(tot.at["pulp", "q_2050_main_t"])).values()); pap50 = sum(cm.vec2050("Paper production", float(tot.at["paper", "q_2050_main_t"])).values())
    N = S.groupby("node")[["w_pulp", "w_paper_main", "w_paper_known_only"]].sum()
    N["pulp_share"] = N.w_pulp / N.w_pulp.sum(); N["paper_share_main"] = N.w_paper_main / N.w_paper_main.sum(); N["paper_share_known_only"] = N.w_paper_known_only / N.w_paper_known_only.sum()
    N["pp_2050_twh_main"] = (N.pulp_share * pul50 + N.paper_share_main * pap50) / 1e6
    N["pp_share_main"] = N.pp_2050_twh_main / N.pp_2050_twh_main.sum()
    N = N.join(v3o.rename("v3_other_share"), how="outer").fillna(0.0)
    N["diff_pp"] = N.pp_share_main - N.v3_other_share
    N.reset_index().rename(columns={"index": "node"}).to_csv(out / "ID_PULP_PAPER_NODES.csv", index=False, float_format="%.6f")
    for n_, r in N[N.pp_share_main > 0.01].iterrows():
        ev.put(f"pp.node.{n_}.share", r.pp_share_main, "-", "s2/ID_PULP_PAPER_NODES.csv (SFI)", "PROPOSED (quantified)", "C")
        ev.put(f"pp.node.{n_}.v3_other_share", r.v3_other_share, "-", "INDUSTRY_NODE_SHARES_V3.csv", "VERIFIED", "C")

    # ================================================= 2. ETHYLENE ============================================================
    X = pd.read_excel(W / SFI_ETH, sheet_name=0)
    X = X[X.country.eq("Indonesia")].copy()
    X["cap"] = pd.to_numeric(X["capacity (Kt ethylene/year)"], errors="coerce"); X["start"] = pd.to_numeric(X.year, errors="coerce")
    op19 = X[X.status.eq("Operating") & (X.start <= 2019)]
    cap19 = float(op19.cap.sum()) * 1e3
    gc = pd.read_excel(W / GEM_CHEM, sheet_name="Chemical Capacities")
    gp = pd.read_excel(W / GEM_CHEM, sheet_name="Plant Data")
    gid = gp[gp["SFI ID"].isin(op19.uid)]["GEM Plant ID"].tolist()
    gcc = gc[gc["GEM Plant ID"].isin(gid) & gc["Capacity Status"].eq("operating")]
    eth_g = float(gcc[gcc.Product.eq("ethylene")]["Capacity (ttpa)"].sum()); hvc_g = float(gcc[gcc.Product.isin(["ethylene", "propylene", "butadiene", "benzene", "toluene", "xylene"])]["Capacity (ttpa)"].sum())
    olef_g = float(gcc[gcc.Product.isin(["ethylene", "propylene"])]["Capacity (ttpa)"].sum())
    hvc_per_eth = hvc_g / eth_g; olef_per_eth = olef_g / eth_g
    cm.import_v3()   # puts the repository scripts_project on sys.path (read only)
    import s3_0_industry as s30   # noqa: E402  (constants only; repository read only)
    import json
    PE = dict(s30.PE); PE["EU27_ammonia_kt"] = float(json.loads((cm.REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_EVIDENCE.json").read_text())["eu27_ammonia_kt_2019"])
    basic = (float(tday.at["HVC", "fec_2019_ktoe"]) - float(tday.at["HVC", "feedstock_2019_ktoe"])) * 11.63 * 1e3
    nh3 = PE["EU27_ammonia_kt"] * 1e3 * (PE["MWh_CH4_per_tNH3_SMR"] + PE["MWh_elec_per_tNH3_SMR"]); cl = PE["chlorine_production_today"] * 1e6 * (PE["MWh_elec_per_tCl"] + PE["MWh_H2_per_tCl"])
    meoh = PE["methanol_production_today"] * 1e6 * (PE["MWh_CH4_per_tMeOH"] + PE["MWh_elec_per_tMeOH"])
    hvc_spec = (basic - nh3 - cl - meoh) / (PE["HVC_production_today"] * 1e6)   # MWh per t HVC, energy use only (s3_0 weights)
    zb = rm.loc["olefins (ethylene, propylene)"]
    bat_spec = (float(zb.bat_electricity_gj_per_t) + float(zb.bat_fuel_or_heat_gj_per_t)) / 3.6; bat_el_share = float(zb.bat_electricity_gj_per_t) / (float(zb.bat_electricity_gj_per_t) + float(zb.bat_fuel_or_heat_gj_per_t))
    bat_oda_spec = float(zb.base_electricity_mwh_per_t) + float(zb.base_fuel_mwh_per_t)
    v50 = cm.vec2050("HVC", 1.0); hvc50 = sum(v50.values())
    erows = []
    for lv, u in U_ETH.items():
        q_eth = cap19 * u; q_hvc = q_eth * hvc_per_eth
        d19 = q_hvc * hvc_spec
        q50 = q_hvc * cm.growth(2019)
        erows.append(dict(level=lv, utilisation=u, ethylene_2019_t=q_eth, hvc_per_ethylene=hvc_per_eth, hvc_2019_t=q_hvc, spec_mwh_per_t_hvc=hvc_spec, energy_2019_twh=d19 / 1e6,
                          electricity_share=bat_el_share, energy_2019_etsap_bat_twh=q_eth * olef_per_eth * bat_spec / 1e6, energy_2019_etsap_bat_oda_twh=q_eth * olef_per_eth * bat_oda_spec / 1e6,
                          growth_2019_2050=cm.growth(2019), hvc_2050_t=q50, energy_2050_twh=q50 * hvc50 / 1e6, **{f"e2050_{k}_twh": q50 * v / 1e6 for k, v in v50.items() if v}))
    cap25 = float(X[X.start <= 2025].cap.sum()) * 1e3   # incl. the LINE project (SFI: under construction 2025; GEM: operating 2025)
    q25 = cap25 * U_ETH["central"] * hvc_per_eth
    erows.append(dict(level="central, base 2025 incl. LINE (R4 sensitivity)", utilisation=U_ETH["central"], ethylene_2019_t=np.nan, hvc_per_ethylene=hvc_per_eth, hvc_2019_t=np.nan,
                      growth_2019_2050=cm.growth(2025), hvc_2050_t=q25 * cm.growth(2025), energy_2050_twh=q25 * cm.growth(2025) * hvc50 / 1e6))
    EX = pd.DataFrame(erows); EX.to_csv(out / "ID_ETHYLENE.csv", index=False, float_format="%.6g")
    X[["uid", "plant_name", "state", "status", "cap", "start", "feedstock", "latitude", "longitude"]].to_csv(out / "ID_ETHYLENE_UNITS_SFI.csv", index=False)
    ev.put("eth.capacity_2019", cap19, "t ethylene", f"SFI ethylene 2025-12, operating and start <= 2019: {';'.join(op19.plant_name)}", "VERIFIED", "B")
    ev.put("eth.hvc_per_ethylene", hvc_per_eth, "t/t", f"GEM GCT 2026-11 operating capacities of the same plant (ethylene {eth_g:.0f}, HVC {hvc_g:.0f} kt)", "INFERENCE", "C")
    ev.put("eth.olefins_per_ethylene", olef_per_eth, "t/t", "GEM GCT (ethylene + propylene) / ethylene", "INFERENCE", "C")
    ev.put("eth.gem_ethylene_capacity", eth_g * 1e3, "t", "GEM GCT 2026-11 (differs from SFI 860 kt)", "VERIFIED", "B")
    ev.put("eth.hvc_spec_energy_use", hvc_spec, "MWh/t HVC", "JRC-IDEES EU27 2019 basic chemicals energy use - NH3 / Cl / MeOH (s3_0 lines), / 52 Mt HVC", "EXACT", "C")
    ev.put("eth.etsap_bat_spec", bat_spec, "MWh/t olefins", "ETSAP v2.1.0 BAT olefins naphtha steam cracking (route map), no ODA factor", "VERIFIED", "C")
    ev.put("eth.etsap_bat_oda_spec", bat_oda_spec, "MWh/t olefins", "ETSAP BAT x ODA (route map; ODA chemicals factor not per product)", "VERIFIED", "C")
    ev.put("eth.pypsa_hvc_2050_no_naphtha", hvc50, "MWh/t HVC", "PyPSA-Eur 2050 HVC column without naphtha (v3 route convention)", "VERIFIED", "B")
    for r in EX.itertuples():
        if r.level in U_ETH:
            for k in ("utilisation", "ethylene_2019_t", "hvc_2019_t", "energy_2019_twh", "energy_2019_etsap_bat_twh", "energy_2019_etsap_bat_oda_twh", "hvc_2050_t", "energy_2050_twh"):
                ev.put(f"eth.{r.level}.{k}", getattr(r, k), "TWh" if k.endswith("twh") else ("t" if k.endswith("_t") else "-"), "s2/ID_ETHYLENE.csv",
                       "PROPOSED (assumption)" if k == "utilisation" else "INFERENCE", "C")
    ev.put("eth.base2025.energy_2050", float(EX.iloc[-1].energy_2050_twh), "TWh", "s2/ID_ETHYLENE.csv (incl. LINE 1,000 kt)", "INFERENCE", "C")

    # ================================================= 3-4. SUGAR AND PALM ======================================================
    import glob
    u = pd.concat((pd.read_csv(f, sep=";", dtype=str) for f in sorted(glob.glob(str(cm.Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/demand/unsd/data") / "*.txt")))), ignore_index=True)
    u = u[u["Country or Area"].eq("Indonesia")]
    sp = u["Commodity - Transaction"].str.split(" - ", n=1, expand=True); u["commodity"], u["transaction"] = sp[0].str.strip(), sp[1].fillna("").str.strip()
    u["q"] = pd.to_numeric(u.Quantity, errors="coerce"); u["y"] = u.Year.astype(int)
    bag = u[u.commodity.eq("Bagasse") & u.transaction.eq("Production")].set_index("y").q * 1e3
    cane = cm.series(QCL, "Indonesia", "Sugar cane").set_index("year")
    srows = []
    for y in range(2010, 2023):
        if y in bag.index and y in cane.index:
            srows.append(dict(check="sugar", year=y, cane_t=float(cane.at[y, "value"]), cane_flag=cane.at[y, "flag"], unsd_bagasse_t=float(bag.at[y]),
                              implied_bagasse_per_cane=float(bag.at[y]) / float(cane.at[y, "value"]), irena_bagasse_t=float(cane.at[y, "value"]) * SUGAR_PF,
                              unsd_over_irena=float(bag.at[y]) / (float(cane.at[y, "value"]) * SUGAR_PF)))
    SG = pd.DataFrame(srows)
    r19 = SG[SG.year == 2019].iloc[0]
    for k in ("cane_t", "unsd_bagasse_t", "implied_bagasse_per_cane", "irena_bagasse_t", "unsd_over_irena"):
        ev.put(f"sugar.2019.{k}", r19[k], "t" if k.endswith("_t") else "-", "FAOSTAT QCL (flag X) / UNSD bagasse production / IRENA 2017 Table R3 factor 0.2", "VERIFIED" if k in ("cane_t", "unsd_bagasse_t") else "INFERENCE", "B")
    ev.put("sugar.ratio_range_2010_2022.min", SG.implied_bagasse_per_cane.min(), "t/t", "UNSD bagasse / FAOSTAT cane", "INFERENCE", "B")
    ev.put("sugar.ratio_range_2010_2022.max", SG.implied_bagasse_per_cane.max(), "t/t", "UNSD bagasse / FAOSTAT cane", "INFERENCE", "B")
    ev.put("sugar.2019.raw_sugar", cm.value(QCL, "Indonesia", "Raw cane or beet sugar (centrifugal only)", 2019)[0], "t", "FAOSTAT QCL flag A", "VERIFIED", "A")
    ev.put("sugar.2019.unsd_bagasse_twh", float(bag.at[2019]) * 0.002144 / 1e3, "TWh", "UNSD 6,964.7 kt x 0.002144 TWh/kt (pypsa-asean factor, UNSD 2014 methodology)", "EXACT", "B")
    ffb = cm.series(QCL, "Indonesia", "Oil palm fruit").set_index("year"); cpo = cm.series(QCL, "Indonesia", "Palm oil").set_index("year")
    pk = cm.series(QCL, "Indonesia", "Palm kernels").set_index("year")
    fw = u[u.commodity.eq("Fuelwood") & u.transaction.eq("Consumption not elsewhere specified (industry)")].set_index("y").q * 1e3
    prows = []
    for y in range(2010, 2023):
        if y not in ffb.index:
            continue
        F = float(ffb.at[y, "value"])
        fib, shl = F * IRENA_BOX4["fibre"], F * IRENA_BOX4["shell"]
        prows.append(dict(check="palm", year=y, ffb_t=F, ffb_flag=ffb.at[y, "flag"], cpo_t=float(cpo.at[y, "value"]) if y in cpo.index else np.nan,
                          oer=(float(cpo.at[y, "value"]) / F) if y in cpo.index else np.nan, fibre_t=fib, shell_t=shl, efb_t=F * IRENA_BOX4["efb"],
                          fibre_twh=fib * RES_GJ_T / 3.6 / 1e6, shell_twh_ncv_low=shl * PKS_KCAL[0] * KCAL_GJ / 3.6 / 1e6, shell_twh_15gj=shl * RES_GJ_T / 3.6 / 1e6,
                          mill_fuel_low_twh=fib * RES_GJ_T / 3.6 / 1e6, mill_fuel_high_twh=(fib * RES_GJ_T + shl * RES_GJ_T) / 3.6 / 1e6,
                          unsd_fuelwood_industry_nes_m3=float(fw.at[y]) if y in fw.index else np.nan,
                          unsd_fuelwood_industry_nes_twh=float(fw.at[y]) * 0.00254 / 1e3 if y in fw.index else np.nan))
    PL = pd.DataFrame(prows)
    pd.concat([SG, PL], ignore_index=True).to_csv(out / "ID_SUGAR_PALM_CHECK.csv", index=False, float_format="%.6g")
    p19 = PL[PL.year == 2019].iloc[0]
    for k in ("ffb_t", "cpo_t", "oer", "fibre_t", "shell_t", "efb_t", "fibre_twh", "shell_twh_ncv_low", "shell_twh_15gj", "mill_fuel_low_twh", "mill_fuel_high_twh",
              "unsd_fuelwood_industry_nes_m3", "unsd_fuelwood_industry_nes_twh"):
        ev.put(f"palm.2019.{k}", p19[k], "TWh" if k.endswith("twh") else ("t" if k.endswith("_t") else ("m3" if k.endswith("m3") else "-")),
               {"ffb_t": "FAOSTAT QCL oil palm fruit 2019 flag E", "cpo_t": "FAOSTAT QCL palm oil 2019 flag A"}.get(k, "FFB x IRENA 2022 Box 4 (p.40, Eriza 2010) x 15 GJ/t (IRENA 2017 p.7) / ERIA 2024 T3.8 PKS NCV"),
               "VERIFIED" if k in ("ffb_t", "cpo_t", "unsd_fuelwood_industry_nes_m3") else "INFERENCE", "C" if k != "cpo_t" else "A")
    ev.put("palm.2019.palm_kernels", float(pk.at[2019, "value"]), "t", "FAOSTAT QCL flag X", "VERIFIED", "B")
    c_ = np.corrcoef(PL.dropna(subset=["unsd_fuelwood_industry_nes_m3"]).ffb_t, PL.dropna(subset=["unsd_fuelwood_industry_nes_m3"]).unsd_fuelwood_industry_nes_m3)[0, 1]
    ev.put("palm.corr_ffb_vs_unsd_industry_fuelwood_2010_2022", c_, "-", "Pearson r of the two series (s2/ID_SUGAR_PALM_CHECK.csv)", "INFERENCE", "C")
    ev.extra["chain_inputs"] = dict(pp_2019_electricity_mwh=d19_el, pp_2019_fuel_mwh=d19_fuel, pp_2019_biomass_part_mwh=d19_bio_part,
                                    pp_2050={c: v for c, v in e50.items()},
                                    eth={lv: dict(d19_mwh=float(EX[EX.level == lv].energy_2019_twh.iloc[0]) * 1e6, el_share=bat_el_share,
                                                  v2050={k: float(EX[EX.level == lv].hvc_2050_t.iloc[0]) * x for k, x in v50.items()}) for lv in U_ETH},
                                    eth_base2025_v2050={k: float(EX.iloc[-1].hvc_2050_t) * x for k, x in v50.items()})
    ev.write(out / "_products_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(P[["group", "item", "q_2019_t", "flag_2019", "base_year", "q_base_t", "flag_base", "latest_year", "q_2050_main_t", "q_2050_literal2024_t"]].to_string())
    print(E.round(3).to_string()); print(EX.round(4).T.to_string())
    print(N[N.pp_share_main > 0.005].round(4).to_string())
    print(SG.round(3).to_string()); print(PL.round(2).to_string())
    print("u_pulp", u_p, "paper known cap", kq, "unknown mills", n_unknown, "corr", c_)


if __name__ == "__main__":
    main()
