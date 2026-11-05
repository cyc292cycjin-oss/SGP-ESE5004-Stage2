"""V4 W07 G1 steps 3-6 (Malaysia): physical output, base years and 2019 / 2050 energy of the explicit sub-sectors.

    PYTHONHASHSEED=0 python scripts/v4g1_products.py        (WSL pypsa-earth python; after v4g1_base.py)

v3 rules re-checked (no change of the v3 rule itself unless stated as an option):
  steel     worldsteel 2019 (2019 deduction) / 2024 (2050 base) and GEM GIST 2026-09 capacity; boundary: UNSD MY reports coke into blast
            furnaces as transformation (1,474 kt, outside T_v2) and the blast-furnace gas as iron-and-steel consumption (15,799 TJ, inside).
  cement    EDGAR 2025 2.A.1 / 0.52 = clinker, v3 cement equivalent = clinker / 0.656, against USGS MYB 2023 T22 (MY 2019 16,102 kt): implied
            clinker / cement; correction (ii) = grinding electricity on USGS cement; the v3 2019 kiln fuel above the UNSD NMM coal row.
  aluminium v3 750 kt (USGS 2017-18 Asia-Pacific estimate, 2018 used for 2019) against USGS GIS capacity 1,080 kt and the NEB 2019 Sarawak
            industry electricity; the network supply mode (load node, hydro at the node, no separate captive supply).
  ammonia   USGS 2019 1,457 kt (v3) and the GEM plants: where the process fuel sits (UNSD MY has no chemical row; NEB 2019 gas by region).
New explicit products (energy use only, feedstock stays in NEU; deducted from 'other' because MY has no UNSD chemical / paper row):
  methanol  GEM operating capacity 2019 x utilisation 0.75 / 0.85 / 0.95 (stated assumption, C).
  HVC       olefins: ETSAP 2018 production 1,949 kt (B) x HVC / olefins from GEM same-plant capacities; aromatics: GEM capacity x 0.85 (C).
            PRefChem / PIC Pengerang (refinery-integrated, start 2019-2020) is outside the 2019 base (R4 sensitivity).
  pulp and paper  FAOSTAT FO (last year with new information); closed-loop rule (decision 206 item 3): only purchased energy is explicit.
  lime      ETSAP 2018 production 1,447 kt (B); EDGAR 2.A.2 as a cross-check; ETSAP BAT energy (no PyPSA-Eur lime sector, C).
  glass     no MY production on disk (MISSING).
Outputs tables/MY_STEEL_CHECK.csv, MY_CEMENT_CHECK.csv, MY_ALUMINIUM_CHECK.csv, MY_CHEM_PLANTS.csv, MY_CHEM_ENERGY.csv,
MY_PULP_PAPER_FAOSTAT.csv, MY_PULP_PAPER_ENERGY.csv, MY_LIME.csv, tables/_products_evidence.json (extra.chain_inputs for v4g1_chain.py).
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4g1_common as cm   # noqa: E402

OUT = cm.G1 / "tables"
GEM_CHEM = cm.S2W / "downloads/03_gem_chemicals/Plant-level-data-Global-Chemicals-Tracker-November-2026-V1.xlsx"
SFI_ETH = cm.S2W / "downloads/05_sfi_ethylene/Global_Ethylene_Production_Database_December_2025.xlsx"
SFI_PP = cm.S2W / "downloads/04_sfi_pulp_paper/SFI_ALD_Pulp_Paper_Database_July_2025.xlsx"
U_LEVELS = {"low": 0.75, "central": 0.85, "high": 0.95}   # stated utilisation assumption where no plant output exists (as S2 ethylene), grade C
USGS_CEMENT_MY = {2019: 16102, 2020: 19936, 2021: 19961, 2022: 19856, 2023: 23191}   # kt, USGS MYB 2023 Cement T22 (repository source), read below
REGION_OF_STATE = {"Sabah": "Sabah", "Labuan": "Sabah", "Sarawak": "Sarawak"}   # NEB regions; every other state -> Peninsular Malaysia


def region(state: str) -> str:
    return REGION_OF_STATE.get(str(state), "Peninsular Malaysia")


def main():
    ev = cm.Ev("products"); OUT.mkdir(exist_ok=True)
    base = json.loads((OUT / "_base_evidence.json").read_text())["extra"]
    neb = base["neb_checks"]
    G = cm.gdp_growth(); ev.put("growth.G_2022_2050", G, "-", "INDUSTRY_OUTPUT_2050_M08B.csv (AEO8 table D.2)", "VERIFIED", "B")
    for y in (2018, 2019, 2023, 2024, 2025):
        ev.put(f"growth.factor_from_{y}", cm.growth(y), "-", "S0 R2: G^((2050 - y_b)/28 x 0.5)", "EXACT", "B")
    r50, tday = cm.ratios_2050(), cm.ratios_today()
    bat = pd.read_csv(cm.S2W / "evidence/COVERAGE_ETSAP_BAT_SEC.csv").set_index(["route", "item"]).bat_mwh_per_t
    etp = pd.read_csv(cm.S2W / "evidence/COVERAGE_ETSAP_PRODUCTION_ASEAN.csv"); etp = etp[etp.country == cm.CC]
    ev.extra["etsap_production_my"] = etp.astype(str).to_dict("records")
    pz = pd.read_csv(cm.REPO / "research_inputs/demand_v5/INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"); pz = pz[pz.country == cm.CC]
    import geopandas as gpd
    regions = gpd.read_file(cm.MAIN / "research_inputs/renewable_v5/regions_onshore.geojson")
    chain_inputs = {}

    # =============================================== STEEL ===================================================================
    ws = pd.read_csv(cm.REPO / "research_inputs/registry_v5/sources/WORLDSTEEL_2019_ASEAN.csv").set_index("iso2").loc[cm.CC]
    b24 = pd.read_csv(cm.REPO / "research_inputs/demand_v5/INDUSTRY_OUTPUT_BASE_M08B.csv").set_index("country").loc[cm.CC]
    gs = pd.read_csv(cm.S2W / "evidence/COVERAGE_GEM_STEEL_OPERATING_CAPACITY_KTPA.csv").set_index("iso").loc[cm.CC]
    st19 = pz[pz.subsector == "iron and steel"].groupby("carrier").mwh_2019.sum() / 1e6
    steel = [dict(item="worldsteel 2019 crude steel", value=float(ws.crude_steel_2019_kt), unit="kt", source="WORLDSTEEL_2019_ASEAN.csv (v3 2019 deduction activity)", grade="B"),
             dict(item="worldsteel 2019 BOF (oxygen)", value=float(ws.bof_oxygen_kt), unit="kt", source="same", grade="B"),
             dict(item="worldsteel 2019 EAF + other", value=float(ws.eaf_electric_kt) + float(ws.get("other_kt", 0) or 0), unit="kt", source="same", grade="B"),
             dict(item="worldsteel 2024 crude steel (v3 2050 base)", value=float(b24.steel_base_kt), unit="kt", source="INDUSTRY_OUTPUT_BASE_M08B.csv", grade="B"),
             dict(item="GEM GIST 2026-09 operating capacity: crude / BOF / EAF / IF / BF / DRI", value=float(gs.crude), unit="kt/a",
                  source=f"BOF {gs.bof:.0f} / EAF {gs.eaf:.0f} / IF {gs.ind:.0f} / BF {gs.bf:.0f} / DRI {gs.dri:.0f} (S0 coverage table)", grade="B"),
             dict(item="utilisation 2024 = worldsteel 2024 / GEM operating crude capacity", value=float(b24.steel_base_kt) / float(gs.crude), unit="-", source="derived", grade="C"),
             dict(item="UNSD 2019 coke into blast furnaces (transformation, outside T_v2)", value=1474.024, unit="kt", source="UNdata export / SDMX (A)", grade="B"),
             dict(item="UNSD 2019 blast furnace gas consumed by iron and steel (inside T_v2, steel row)", value=15799.179 / 3600, unit="TWh", source="UNdata export (A)", grade="B")]
    for car, v in st19.items():
        steel.append(dict(item=f"v3 2019 steel deduction: {car}", value=float(v), unit="TWh", source="s3_0 INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv (steel row coal = BFG; rest taken from other)", grade="C"))
    steel.append(dict(item="v3 2019 steel deduction total", value=float(st19.sum()), unit="TWh", source="same", grade="C"))
    ST = pd.DataFrame(steel); ST.to_csv(OUT / "MY_STEEL_CHECK.csv", index=False, float_format="%.6f")
    for r in ST.itertuples():
        ev.put(f"steel.{r.item}", r.value, r.unit, r.source, "VERIFIED" if r.grade == "B" else "EXACT", r.grade)

    # =============================================== CEMENT ==================================================================
    ed = pd.read_csv(cm.REPO / "research_inputs/registry_v5/sources/EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv")
    ed = ed[(ed.iso == cm.CC)].set_index("ipcc_code_2006_for_standard_report")
    t22 = pd.read_excel(cm.REPO / "research_inputs/demand_v5/sources/m08b/myb1-2023-cemen-ERT.xlsx", sheet_name="T22", header=None)
    rowm = t22[t22[0].astype(str).str.strip().eq("Malaysia")].iloc[0]
    nums = [float(x) for x in rowm.values[1:] if str(x).replace(".", "").isdigit()]
    usgs = dict(zip((2019, 2020, 2021, 2022, 2023), nums[:5]))
    if usgs != {k: float(v) for k, v in USGS_CEMENT_MY.items()}:
        raise ValueError(f"USGS T22 Malaysia row differs: {usgs}")
    clk19 = float(ed.at["2.A.1", "kt_CO2_2019"]) / 0.52; clk24 = float(ed.at["2.A.1", "kt_CO2_2024"]) / 0.52
    cem_eq19 = clk19 / 0.656
    cem19 = pz[pz.subsector == "cement"].groupby("carrier").mwh_2019.sum() / 1e6
    fuel19 = (float(r50.at["methane", "Cement"]) + float(r50.at["biomass", "Cement"])) * cem_eq19 * 1e3 / 1e6
    el19 = float(r50.at["elec", "Cement"]) * cem_eq19 * 1e3 / 1e6
    nmm_coal = 1232.691 * cm.TWH_PER_KT_HARD_COAL_V3
    gcem = pd.read_csv(cm.S2W / "evidence/COVERAGE_GEM_CEMENT_OPERATING.csv"); gcem = gcem[gcem.iso == cm.CC] if "iso" in gcem.columns else gcem[gcem.iloc[:, 0] == cm.CC]
    cement = [dict(item="EDGAR 2025 2.A.1 2019", value=float(ed.at["2.A.1", "kt_CO2_2019"]), unit="kt CO2", source="EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv", grade="B"),
              dict(item="EDGAR 2025 2.A.1 2024", value=float(ed.at["2.A.1", "kt_CO2_2024"]), unit="kt CO2", source="same", grade="B"),
              dict(item="clinker 2019 = 2.A.1 / 0.52", value=clk19, unit="kt", source="IPCC 2006 default EF with CKD (registry industry_clinker_emission_factor_ipcc)", grade="C"),
              dict(item="clinker 2024 = 2.A.1 / 0.52", value=clk24, unit="kt", source="same", grade="C"),
              dict(item="v3 cement equivalent 2019 = clinker / 0.656", value=cem_eq19, unit="kt", source="s3_0 (technology-data cement finishing)", grade="C"),
              *[dict(item=f"USGS cement {y}", value=v, unit="kt", source="USGS MYB 2023 Cement T22", grade="A") for y, v in usgs.items()],
              dict(item="implied clinker / cement 2019 (EDGAR / USGS)", value=clk19 / usgs[2019], unit="-", source="derived", grade="C"),
              dict(item="implied clinker / cement, EDGAR 2024 / USGS 2023", value=clk24 / usgs[2023], unit="-", source="derived (years differ)", grade="C"),
              dict(item="v3 cement equivalent / USGS 2019", value=cem_eq19 / usgs[2019], unit="-", source="derived", grade="C"),
              dict(item="v3 2019 cement deduction total", value=float(cem19.sum()), unit="TWh", source="s3_0 output", grade="C"),
              dict(item="v3 2019 kiln fuel (0.7548 MWh/t x cement equivalent)", value=fuel19, unit="TWh", source="PyPSA-Eur Cement ratio", grade="C"),
              dict(item="v3 2019 grinding electricity (0.1066 MWh/t x cement equivalent)", value=el19, unit="TWh", source="PyPSA-Eur Cement ratio", grade="C"),
              dict(item="UNSD 2019 NMM hard coal (Estimate) x v3 factor", value=nmm_coal, unit="TWh", source="UNdata export 1,232.691 kt x 0.007167 TWh/kt", grade="C"),
              dict(item="kiln fuel taken from 'other' (gas and oil, spread) in v3", value=fuel19 - nmm_coal, unit="TWh", source="s3_0 cement logic (excess over the NMM row)", grade="C"),
              dict(item="grinding electricity taken from 'other' in v3", value=el19, unit="TWh", source="s3_0 cement logic (NMM row has no electricity)", grade="C"),
              dict(item="correction (ii): grinding electricity on USGS 2019 cement", value=float(r50.at["elec", "Cement"]) * usgs[2019] * 1e3 / 1e6, unit="TWh", source="0.1066 MWh/t x 16,102 kt", grade="C"),
              dict(item="correction (ii): change of the 2019 cement deduction", value=float(r50.at["elec", "Cement"]) * (usgs[2019] - cem_eq19) * 1e3 / 1e6, unit="TWh", source="derived", grade="C"),
              dict(item="kiln heat need at ETSAP BAT 2.9 GJ/t clinker, as hard coal at 26.394 GJ/t", value=clk19 * 2.9 / 26.394, unit="kt coal-eq", source="ETSAP BAT clinker heat", grade="C"),
              dict(item="kiln fuel of v3 (0.7548 MWh/t cement-eq) as hard coal at 26.394 GJ/t", value=fuel19 * 3.6e3 / 26.394, unit="kt coal-eq", source="derived", grade="C"),
              dict(item="NEB 2019 industry coal (table 9) = UNSD NMM coal + coke into BF (difference, t)", value=neb["industry_coal_t_minus_unsd_nmm_coal_and_bf_coke_t"], unit="t", source="NEB 2019 p.46; UNSD", grade="A")]
    if len(gcem):
        g0 = gcem.iloc[0]
        for k in ("cement_mtpa", "clinker_mtpa", "plants"):
            if k in gcem.columns:
                cement.append(dict(item=f"GEM GCCT 2026-07 {k}", value=float(g0[k]), unit="-", source="S0 coverage table", grade="B"))
    CE = pd.DataFrame(cement); CE.to_csv(OUT / "MY_CEMENT_CHECK.csv", index=False, float_format="%.6f")
    for r in CE.itertuples():
        ev.put(f"cement.{r.item}", r.value, r.unit, r.source, "VERIFIED" if r.grade in ("A", "B") else "EXACT", r.grade)
    chain_inputs["cement_usgs_2019_t"] = usgs[2019] * 1e3
    chain_inputs["cement_kiln_fuel_from_other_2019_mwh"] = (fuel19 - nmm_coal) * 1e6

    # =============================================== ALUMINIUM ===============================================================
    nf = pd.read_csv(cm.REPO / "research_inputs/industry_v3/NONFERROUS_PRODUCTION_V3.csv"); nf = nf[nf.country == cm.CC].iloc[0]
    al_today = cm.today_vec("Aluminium - primary production", 1.0)
    al_el_t = al_today["elec"]
    import xarray as xr
    ds = xr.open_dataset(cm.NETWORK)
    su = pd.DataFrame({k: ds[f"storage_units_{k}"].values for k in ("bus", "carrier", "p_nom", "p_nom_max", "p_nom_min", "max_hours") if f"storage_units_{k}" in ds}, index=ds["storage_units_i"].values)
    hy = su[su.index.astype(str).str.startswith("MY_") & su.carrier.eq("hydro")]
    ld = pd.DataFrame({k: ds[f"loads_{k}"].values for k in ("bus", "carrier", "p_set")}, index=ds["loads_i"].values)
    node_el = ld[ld.index.astype(str).str.startswith("MY_") & ld.carrier.eq("industry electricity")].groupby("bus").p_set.apply(lambda s: s.astype(float).sum() * 8760 / 1e6)
    sw_ind_el = ld[ld.index.astype(str).str.startswith("MY_Sarawak") & ld.carrier.eq("industry electricity")].p_set.astype(float).sum() * 8760 / 1e6
    my_ind_el = ld[ld.index.astype(str).str.startswith("MY_") & ld.carrier.eq("industry electricity")].p_set.astype(float).sum() * 8760 / 1e6
    sar_el = float(neb["industry_electricity_share_Sarawak"]) * float(neb["industry_electricity_twh"])
    al = [dict(item="v3 primary aluminium 2019 activity", value=float(nf.q_2019_t) / 1e3, unit="kt", source=str(nf.source_locator)[:160], grade=str(nf.tier)),
          dict(item="USGS GIS capacity (Press Metal Bintulu 960 + Mukah 120)", value=float(nf.q_2023_t) / 1e3, unit="kt/a", source="NONFERROUS_PRODUCTION_V3.csv q_2023_t (v3 NF2023 sensitivity uses it as output)", grade="B"),
          dict(item="JRC-IDEES today primary aluminium electricity", value=al_el_t, unit="MWh/t", source="today total 15.07 MWh/t x PyPSA-Eur structure", grade="C"),
          dict(item="v3 2019-equivalent aluminium electricity (750 kt)", value=float(nf.q_2019_t) * al_el_t / 1e6, unit="TWh", source="derived", grade="C"),
          dict(item="aluminium electricity at capacity 1,080 kt", value=float(nf.q_2023_t) * al_el_t / 1e6, unit="TWh", source="derived", grade="C"),
          dict(item="NEB 2019 Sarawak industry electricity", value=sar_el, unit="TWh", source="NEB 2019 table 17 (22,128 GWh, 28.2 %)", grade="A"),
          dict(item="upper bound of 2019 output if all Sarawak industry electricity were smelting", value=sar_el * 1e6 / al_el_t / 1e3, unit="kt", source="derived (bound, not an estimate)", grade="C"),
          dict(item="Sarawak industry electricity minus aluminium at 750 kt", value=sar_el - float(nf.q_2019_t) * al_el_t / 1e6, unit="TWh", source="derived (ferro-alloys, polysilicon, other)", grade="C"),
          dict(item="Sarawak industry electricity minus aluminium at 1,080 kt", value=sar_el - float(nf.q_2023_t) * al_el_t / 1e6, unit="TWh", source="derived", grade="C"),
          *[dict(item=f"network: industry electricity load at {b}", value=float(v), unit="TWh", source="v3.1 F1 network; industry loads are per node and carrier (aluminium is inside the node's industry electricity)", grade="B")
            for b, v in node_el.items() if str(b).startswith("MY_Sarawak")],
          dict(item="network: MY industry electricity loads 2050", value=my_ind_el, unit="TWh", source="v3.1 F1 network, carrier 'industry electricity'", grade="B"),
          dict(item="network: Sarawak industry electricity loads 2050", value=sw_ind_el, unit="TWh", source="same, buses MY_Sarawak4 *", grade="B"),
          dict(item="network: Sarawak share of MY industry electricity 2050", value=sw_ind_el / my_ind_el, unit="-", source="derived", grade="C"),
          dict(item="NEB 2019 Sarawak share of MY industry electricity", value=float(neb["industry_electricity_share_Sarawak"]), unit="-", source="NEB 2019 table 17", grade="A")]
    for r in hy.itertuples():
        al.append(dict(item=f"network hydro storage unit {r.Index} p_nom_max", value=float(r.p_nom_max), unit="MW", source=f"v3.1 F1 network (p_nom {float(r.p_nom):.1f}, p_nom_min {float(getattr(r, 'p_nom_min', 0) or 0):.1f}, max_hours {float(getattr(r, 'max_hours', 0) or 0):.1f})", grade="B"))
    sh = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_NODE_SHARES_V3.csv")
    for r in sh[(sh.country == cm.CC) & (sh.subsector == "nonferrous_aluminium_primary")].itertuples():
        al.append(dict(item=f"v3 aluminium node share {r.node}", value=float(r.share), unit="-", source="INDUSTRY_NODE_SHARES_V3.csv (USGS GIS smelters)", grade="B"))
    AL = pd.DataFrame(al); AL.to_csv(OUT / "MY_ALUMINIUM_CHECK.csv", index=False, float_format="%.6f")
    for r in AL.itertuples():
        ev.put(f"aluminium.{r.item}", r.value, r.unit, r.source, "VERIFIED" if r.grade in ("A", "B") else "EXACT", r.grade if r.grade in "ABCDE" else "C")

    # =============================================== CHEMICALS (GEM, SFI) ====================================================
    gp = pd.read_excel(GEM_CHEM, sheet_name="Plant Data"); gc = pd.read_excel(GEM_CHEM, sheet_name="Chemical Capacities")
    gp = gp[gp["Country/Area"].astype(str).eq("Malaysia")].copy()
    gc = gc[gc["GEM Plant ID"].isin(gp["GEM Plant ID"])].copy()
    X = pd.read_excel(SFI_ETH, sheet_name=0); X = X[X.country.eq("Malaysia")].copy()
    X["cap"] = pd.to_numeric(X["capacity (Kt ethylene/year)"], errors="coerce"); X["start"] = pd.to_numeric(X.year, errors="coerce")
    gp[["lat", "lon"]] = gp.Coordinates.str.split(",", expand=True).astype(float)
    gp["node"], gp["node_method"] = cm.node_of(gp, regions)
    gp["region"] = gp["Subnational Unit"].map(region)
    gp["start"] = pd.to_numeric(gp["Start Date | Year"], errors="coerce")
    gc["cap"] = pd.to_numeric(gc["Capacity (ttpa)"], errors="coerce")
    op = gc[gc["Capacity Status"].eq("operating")]
    P = gp.merge(op.groupby(["GEM Plant ID", "Product Group"]).cap.sum().unstack(fill_value=0.0), left_on="GEM Plant ID", right_index=True, how="left").fillna({k: 0.0 for k in ("ammonia", "methanol", "olefins", "aromatics")})
    P["in_2019_base"] = P["Operating Status"].eq("operating") & (P.start <= 2019) & ~P["Plant Name (English)"].str.contains("PRefChem")
    usgs_nh3_19 = 1457.142857
    nh3_cap19 = float(P[P.in_2019_base].ammonia.sum()); u_nh3 = usgs_nh3_19 / nh3_cap19
    # ---- unit energy (MWh per t product), energy use only
    PE = dict(nh3_ch4=10.8, nh3_el=0.7, meoh_ch4=10.25, meoh_el=0.167)   # s3_0_industry.PE (PyPSA-Eur v2025.07.0 today, feedstock + fuel)
    feed_nh3 = float(bat[("ammonia_gas", "feedstock_gas")]); feed_meoh = float(bat[("methanol_gas", "feedstock")])
    spec = {"ammonia": {"central": dict(gas=PE["nh3_ch4"] - feed_nh3, electricity=PE["nh3_el"]),
                        "low": dict(gas=float(bat[("ammonia_gas", "fuel_gas")]), electricity=float(bat[("ammonia_gas", "electricity")]))},
            "methanol": {"central": dict(gas=PE["meoh_ch4"] - feed_meoh, electricity=PE["meoh_el"]),
                         "low": dict(gas=float(bat[("methanol_gas", "fuel")]), electricity=float(bat[("methanol_gas", "electricity")]))}}
    spec["ammonia"]["high"] = spec["ammonia"]["central"]; spec["methanol"]["high"] = spec["methanol"]["central"]
    # JRC-IDEES EU27 2019 HVC energy use per t HVC (S2 method: basic chemicals energy use minus ammonia, chlorine, methanol, / 52 Mt)
    cm.import_v3(); import s3_0_industry as s30   # noqa: E402 (constants only)
    PEs = dict(s30.PE); PEs["EU27_ammonia_kt"] = float(json.loads((cm.REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_EVIDENCE.json").read_text())["eu27_ammonia_kt_2019"])
    basic = (float(tday.at["HVC", "fec_2019_ktoe"]) - float(tday.at["HVC", "feedstock_2019_ktoe"])) * 11.63 * 1e3
    nh3e = PEs["EU27_ammonia_kt"] * 1e3 * (PEs["MWh_CH4_per_tNH3_SMR"] + PEs["MWh_elec_per_tNH3_SMR"]); cle = PEs["chlorine_production_today"] * 1e6 * (PEs["MWh_elec_per_tCl"] + PEs["MWh_H2_per_tCl"])
    meohe = PEs["methanol_production_today"] * 1e6 * (PEs["MWh_CH4_per_tMeOH"] + PEs["MWh_elec_per_tMeOH"])
    hvc_spec = (basic - nh3e - cle - meohe) / (PEs["HVC_production_today"] * 1e6)
    el_share_hvc = float(bat[("olefins_naphtha_steam_cracking", "electricity")]) / float(bat[("olefins_naphtha_steam_cracking", "total_energy")])
    ev.put("chem.hvc_today_energy_use_spec", hvc_spec, "MWh/t HVC", "JRC-IDEES EU27 2019 basic chemicals energy use - NH3, Cl, MeOH (s3_0 constants) / 52 Mt (S2 method)", "EXACT", "C")
    ev.put("chem.hvc_electricity_share", el_share_hvc, "-", "ETSAP BAT olefins electricity / total energy", "VERIFIED", "C")
    for prod in ("ammonia", "methanol"):
        for lv, d in spec[prod].items():
            for car, v in d.items():
                ev.put(f"chem.spec.{prod}.{lv}.{car}", v, "MWh/t", "central: PyPSA-Eur today total gas (s3_0 PE) minus ETSAP BAT feedstock; low: ETSAP BAT fuel (energy use only)", "INFERENCE", "C")
    # ---- HVC activity: olefins ETSAP 2018 production; HVC per olefins from GEM same-plant capacities of the 2019 crackers
    olef18 = float(etp[etp["product"].astype(str).str.lower().str.contains("olefin")].kt.sum())
    cr = P[P.in_2019_base & (P.olefins > 0)]
    crgid = cr["GEM Plant ID"].tolist()
    cc_ = op[op["GEM Plant ID"].isin(crgid)]
    olef_cap = float(cc_[cc_.Product.isin(["ethylene", "propylene"])].cap.sum()); hvc_cap = float(cc_[cc_.Product.isin(["ethylene", "propylene", "butadiene", "benzene", "toluene", "xylene"])].cap.sum())
    hvc_per_olef = hvc_cap / olef_cap
    arom_cap19 = float(P[P.in_2019_base & (P.olefins == 0)].aromatics.sum())   # stand-alone aromatics (PC Aromatics Kerteh)
    q_olef19 = olef18 * cm.growth(2018) / cm.growth(2019)   # R3 back-cast to 2019 (one year)
    for k, v in dict(olefins_2018_etsap_kt=olef18, olefins_capacity_2019_gem_kt=olef_cap, hvc_capacity_2019_crackers_gem_kt=hvc_cap, hvc_per_olefins=hvc_per_olef,
                     utilisation_olefins_2018=olef18 / olef_cap, aromatics_standalone_capacity_2019_kt=arom_cap19, sfi_ethylene_capacity_2019_kt=float(X[X.start.fillna(0) <= 2019].cap.sum()),
                     sfi_ethylene_capacity_all_kt=float(X.cap.sum()), olefins_2019_backcast_kt=q_olef19, ammonia_capacity_2019_kt=nh3_cap19, ammonia_utilisation_2019=u_nh3,
                     methanol_capacity_2019_kt=float(P[P.in_2019_base].methanol.sum())).items():
        ev.put(f"chem.{k}", v, "kt" if k.endswith("kt") else "-", "GEM GCT 2026-11 / SFI ethylene 2025-12 / ETSAP v2.1.0 production 2018 / USGS 2019 ammonia", "VERIFIED" if k.endswith(("etsap_kt", "gem_kt", "2019_kt")) and "backcast" not in k else "INFERENCE", "B" if "etsap" in k or "gem" in k else "C")
    # ---- per-plant table with 2019 activity, energy use, feedstock and where the fuel is recorded
    neu_gas = {r: float(neb[f"neu_gas_twh_{r}"]) for r in ("Peninsular Malaysia", "Sabah", "Sarawak")}
    ind_gas = {r: float(neb[f"industry_gas_twh_{r}"]) for r in ("Peninsular Malaysia", "Sabah", "Sarawak")}
    rows = []
    for _, p in P.iterrows():
        base = dict(gem_id=p["GEM Plant ID"], plant=p["Plant Name (English)"], owner=p["Owner (English)"], state=p["Subnational Unit"], region=p.region, node=p.node,
                    node_method=p.node_method, status=p["Operating Status"], start_year=p.start, in_2019_base=bool(p.in_2019_base), feedstock=str(p["Feedstock"]))
        for prod in ("ammonia", "methanol", "olefins", "aromatics"):
            cap = float(p[prod])
            if cap <= 0:
                continue
            r = dict(base, product=prod, capacity_kt=cap)
            if prod == "ammonia":
                r["output_2019_kt"] = cap * u_nh3 if p.in_2019_base else 0.0; r["output_rule"] = f"capacity x USGS 2019 national / GEM 2019 capacity = {u_nh3:.3f}"
            elif prod == "methanol":
                r["output_2019_kt"] = cap * U_LEVELS["central"] if p.in_2019_base else 0.0; r["output_rule"] = "capacity x 0.85 (stated assumption, 0.75 / 0.95 sensitivity)"
            elif prod == "olefins":
                pc = op[op["GEM Plant ID"] == p["GEM Plant ID"]]
                cap_ep = float(pc[pc.Product.isin(["ethylene", "propylene"])].cap.sum())
                hv = float(pc[pc.Product.isin(["ethylene", "propylene", "butadiene", "benzene", "toluene", "xylene"])].cap.sum())
                r["capacity_ethylene_propylene_kt"] = cap_ep
                r["output_2019_kt"] = q_olef19 * cap_ep / olef_cap if p.in_2019_base else 0.0
                r["output_rule"] = "ETSAP 2018 olefins (ethylene + propylene) production shared by GEM ethylene + propylene capacity, back-cast to 2019 (R3)"
                r["hvc_per_product"] = hv / cap_ep if cap_ep else np.nan
            else:
                r["output_2019_kt"] = cap * U_LEVELS["central"] if (p.in_2019_base and float(p.olefins) == 0) else 0.0
                r["output_rule"] = "stand-alone aromatics: capacity x 0.85 (C); cracker by-product aromatics are inside the cracker HVC"
            r["standalone"] = float(p.olefins) == 0
            # where the 2019 process fuel is recorded (evidence: NEB 2019 table 7 gas by region; UNSD MY has no chemical row)
            if p.region == "Sarawak":
                r["fuel_recorded_in"] = f"NEU or energy sector (Sarawak industry gas only {ind_gas['Sarawak']:.2f} TWh < plant fuel; Sarawak NEU gas {neu_gas['Sarawak']:.1f} TWh)"
                r["fuel_in_other_central"] = False
            elif "PRefChem" in r["plant"]:
                r["fuel_recorded_in"] = "not in the 2019 base (refinery-integrated, crackers from 2020); later fuel most likely refinery own use / refinery gas"
                r["fuel_in_other_central"] = False
            elif p.region == "Sabah":
                r["fuel_recorded_in"] = f"industry gas (Sabah industry gas {ind_gas['Sabah']:.1f} TWh vs NEU {neu_gas['Sabah']:.1f} TWh; Sabah industry electricity only 1.55 TWh, so the gas is these plants)"
                r["fuel_in_other_central"] = True
            else:
                r["fuel_recorded_in"] = f"industry gas n.e.s. (Peninsular industry gas {ind_gas['Peninsular Malaysia']:.1f} TWh; NEU {neu_gas['Peninsular Malaysia']:.1f} TWh is about the ethane and ammonia feed)"
                r["fuel_in_other_central"] = True
            rows.append(r)
    CP = pd.DataFrame(rows)
    # ---- energy per plant and level
    E = []
    for r in CP.itertuples():
        q = r.output_2019_kt * 1e3
        for lv in ("low", "central", "high"):
            if r.product in ("ammonia", "methanol"):
                s = spec[r.product][lv]
                q_lv = q if r.product == "ammonia" else (r.capacity_kt * 1e3 * U_LEVELS[lv] if r.in_2019_base else 0.0)
                gas, el = s["gas"] * q_lv, s["electricity"] * q_lv
                feed = q_lv * (feed_nh3 if r.product == "ammonia" else feed_meoh)
            else:
                hvc_q = q * (r.hvc_per_product if r.product == "olefins" else 1.0)
                if r.product == "aromatics" and r.in_2019_base and r.standalone and lv != "central":
                    hvc_q = r.capacity_kt * 1e3 * U_LEVELS[lv]
                tot = hvc_q * hvc_spec; el = tot * el_share_hvc; gas = tot - el
                q_lv = hvc_q
                feed = hvc_q * float(bat[("olefins_naphtha_steam_cracking", "feedstock")]) if r.product == "olefins" else hvc_q * float(bat[("aromatics", "feedstock")])
            if r.product == "ammonia":
                in_other = (r.region == "Sabah") if lv == "low" else (r.region != "Sarawak" if lv == "central" else True)
            elif r.product == "olefins" and lv == "low":
                in_other = False   # low: cracker fuel is self-produced off-gas outside the industry statistics; only electricity in 'other'
            else:
                in_other = bool(r.fuel_in_other_central) if r.in_2019_base else False
            el_other = el if (r.in_2019_base and (in_other or (r.product == "olefins" and lv == "low"))) else 0.0
            E.append(dict(gem_id=r.gem_id, plant=r.plant, region=r.region, node=r.node, product=r.product, level=lv, in_2019_base=r.in_2019_base, activity_2019_t=q_lv,
                          energy_gas_2019_mwh=gas if r.in_2019_base else 0.0, energy_el_2019_mwh=el if r.in_2019_base else 0.0, feedstock_2019_mwh=feed if r.in_2019_base else 0.0,
                          fuel_in_other=in_other and r.in_2019_base, deduct_gas_2019_mwh=(gas if (in_other and r.in_2019_base) else 0.0), deduct_el_2019_mwh=el_other))
    CE_ = pd.DataFrame(E)
    CP.to_csv(OUT / "MY_CHEM_PLANTS.csv", index=False, float_format="%.6g")
    CE_.to_csv(OUT / "MY_CHEM_ENERGY.csv", index=False, float_format="%.6g")
    agg = CE_.groupby(["product", "level"])[["activity_2019_t", "energy_gas_2019_mwh", "energy_el_2019_mwh", "feedstock_2019_mwh", "deduct_gas_2019_mwh", "deduct_el_2019_mwh"]].sum()
    for (prod, lv), r in agg.iterrows():
        for k, v in r.items():
            ev.put(f"chem.{prod}.{lv}.{k}", v / 1e6 if k.endswith("mwh") else v, "TWh" if k.endswith("mwh") else "t", "tables/MY_CHEM_ENERGY.csv (GEM plants x rule)", "PROPOSED (quantified)", "C")
    # ---- 2050 explicit vectors (energy use only)
    v50 = {}
    for lv in ("low", "central", "high"):
        a = agg.xs(lv, level="level")
        meoh_q = float(a.at["methanol", "activity_2019_t"]) if "methanol" in a.index else 0.0
        hvc_q = float(a.loc[[x for x in ("olefins", "aromatics") if x in a.index], "activity_2019_t"].sum())
        s = spec["methanol"][lv]
        meoh50 = {k: 0.0 for k in cm.OUTC}; meoh50["gas"] = s["gas"] * meoh_q * cm.growth(2019); meoh50["electricity"] = s["electricity"] * meoh_q * cm.growth(2019)
        v50[lv] = dict(methanol=meoh50, hvc=cm.vec2050("HVC", hvc_q * cm.growth(2019)),
                       methanol_product_rule=cm.vec2050("Methanol", meoh_q * cm.growth(2019)))
        ev.put(f"chem.2050.{lv}.methanol_energy_use", sum(meoh50.values()) / 1e6, "TWh", "2019 energy-use intensity x activity x growth (no PyPSA-Eur energy-only methanol column)", "PROPOSED (quantified)", "C")
        ev.put(f"chem.2050.{lv}.methanol_product_rule", sum(v50[lv]["methanol_product_rule"].values()) / 1e6, "TWh", "PyPSA-Eur Methanol 5.528 MWh_MeOH/t (sensitivity; needs an NEU feed deduction)", "PROPOSED (quantified)", "C")
        ev.put(f"chem.2050.{lv}.hvc", sum(v50[lv]["hvc"].values()) / 1e6, "TWh", "PyPSA-Eur HVC 2050 without naphtha (6.103 MWh/t)", "PROPOSED (quantified)", "C")
    # PIC (PRefChem Pengerang), R4 sensitivity: base 2025, HVC capacity x 0.85
    pic = op[op["GEM Plant ID"].isin(P[P["Plant Name (English)"].str.contains("PRefChem")]["GEM Plant ID"])]
    pic_hvc = float(pic[pic.Product.isin(["ethylene", "propylene", "butadiene", "benzene", "toluene", "xylene"])].cap.sum()) * 1e3 * U_LEVELS["central"]
    v50["pic_2025"] = cm.vec2050("HVC", pic_hvc * cm.growth(2025))
    sp_cap = float(op[op["GEM Plant ID"].isin(P[P["Plant Name (English)"].str.contains("Sarawak Petchem")]["GEM Plant ID"])].cap.sum()) * 1e3
    v50["sarawak_petchem_2023"] = {k: 0.0 for k in cm.OUTC}
    v50["sarawak_petchem_2023"]["gas"] = spec["methanol"]["central"]["gas"] * sp_cap * U_LEVELS["central"] * cm.growth(2023)
    v50["sarawak_petchem_2023"]["electricity"] = spec["methanol"]["central"]["electricity"] * sp_cap * U_LEVELS["central"] * cm.growth(2023)
    ev.put("chem.2050.pic_2025_hvc", sum(v50["pic_2025"].values()) / 1e6, "TWh", "PRefChem HVC capacity x 0.85 x G-factor from 2025 x PyPSA-Eur HVC (R4)", "PROPOSED (quantified)", "C")
    ev.put("chem.2050.sarawak_petchem_2023", sum(v50["sarawak_petchem_2023"].values()) / 1e6, "TWh", "Sarawak Petchem 1,750 kt x 0.85 x G-factor from 2023 x central energy use (R4)", "PROPOSED (quantified)", "C")
    # ammonia: NEU over-deduction of DFX F2.4 where the fuel is in industry (outside T_v2, W08 note)
    nh3_50 = 2.598199e6
    for lv in ("low", "central", "high"):
        a = CE_[(CE_["product"] == "ammonia") & (CE_.level == lv)]
        sh_in = float(a[a.fuel_in_other].activity_2019_t.sum()) / float(a.activity_2019_t.sum())
        ev.put(f"chem.ammonia.{lv}.share_of_output_with_fuel_in_industry", sh_in, "-", "GEM plants x location rule", "INFERENCE", "C")
        ev.put(f"chem.ammonia.{lv}.dfx_f24_neu_overdeduction_2050", nh3_50 * sh_in * spec["ammonia"][lv]["gas"] / 1e6, "TWh", "DFX F2.4 removes 10.8 MWh/t from NEU; the fuel part of plants whose fuel is in industry was never in NEU (outside T_v2)", "INFERENCE", "C")
    chain_inputs["chem_moves_2019"] = {lv: {prod: dict(gas=float(agg.at[(prod, lv), "deduct_gas_2019_mwh"]), electricity=float(agg.at[(prod, lv), "deduct_el_2019_mwh"]))
                                            for prod in ("ammonia", "methanol", "olefins", "aromatics") if (prod, lv) in agg.index} for lv in ("low", "central", "high")}
    chain_inputs["chem_2050"] = {lv: {k: {kk: float(vv) for kk, vv in v.items()} for k, v in d.items()} for lv, d in v50.items() if lv in ("low", "central", "high")}
    chain_inputs["chem_2050_r4"] = {k: {kk: float(vv) for kk, vv in v50[k].items()} for k in ("pic_2025", "sarawak_petchem_2023")}

    # =============================================== PULP AND PAPER (FAOSTAT FO) =============================================
    FO = cm.fao("FO")
    my = FO[(FO.Area == cm.AREA) & (FO.Element == "Production")]
    items = sorted(my.Item.unique())
    # leaf items of the FAOSTAT FO hierarchy (aggregates, roundwood 'Pulpwood', 'Recovered paper' (collection) and the discontinued 1961-2016 items excluded)
    PULP_LEAVES = ["Chemical wood pulp, sulphate, bleached", "Chemical wood pulp, sulphate, unbleached", "Chemical wood pulp, sulphite, bleached", "Chemical wood pulp, sulphite, unbleached",
                   "Dissolving wood pulp", "Mechanical and semi-chemical wood pulp", "Pulp from fibres other than wood"]
    PAPER_LEAVES = ["Newsprint", "Printing and writing papers, coated", "Printing and writing papers, uncoated, mechanical", "Printing and writing papers, uncoated, woodfree",
                    "Household and sanitary papers", "Cartonboard", "Case materials", "Wrapping papers", "Other papers mainly for packaging", "Other paper and paperboard, not elsewhere specified"]
    PAPER_AGG = {"Printing and writing papers": PAPER_LEAVES[1:4], "Other paper and paperboard": PAPER_LEAVES[4:], "Chemical wood pulp": PULP_LEAVES[:4]}
    pulp_items = [i for i in PULP_LEAVES if i in items]; paper_items = [i for i in PAPER_LEAVES if i in items]
    ev.extra["fao_items_my"] = items
    for a_, lv_ in PAPER_AGG.items():
        if a_ in items:
            av = cm.value(FO, cm.AREA, a_, 2019)[0]; sv = sum(cm.value(FO, cm.AREA, l, 2019)[0] for l in lv_ if l in items and not np.isnan(cm.value(FO, cm.AREA, l, 2019)[0]))
            ev.put(f"pp.aggregate_minus_leaves_2019.{a_}", av - sv, "t", "FAOSTAT FO 2019 aggregate minus its leaf items", "EXACT", "B")
    rows = []
    for grp, its in (("pulp", pulp_items), ("paper", paper_items)):
        for it in its:
            s = cm.series(FO, cm.AREA, it)
            if not len(s) or s.value.dropna().empty:
                continue
            la = cm.latest_actual(s)
            try:
                v19, f19 = cm.value(FO, cm.AREA, it, 2019)
            except KeyError:
                v19, f19 = np.nan, ""
            rows.append(dict(group=grp, item=it, q_2019_t=v19, flag_2019=f19, base_year=la["base_year"], q_base_t=la["value"], flag_base=la["flag"], grade_base=la["grade"],
                             carried_forward_years=";".join(map(str, la["carried_forward_years"])), latest_year=la["latest_year"], q_latest_t=la["latest_value"],
                             q_2050_main_t=la["value"] * cm.growth(la["base_year"]), q_2050_literal_latest_t=la["latest_value"] * cm.growth(la["latest_year"]),
                             series=";".join(f"{int(y)}:{v:.0f}{f}" for y, v, f in zip(s.year, s.value, s.flag))))
    PF = pd.DataFrame(rows); PF.to_csv(OUT / "MY_PULP_PAPER_FAOSTAT.csv", index=False, float_format="%.6g")
    leaves = PF   # PF holds leaf items only; the aggregate identities are checked above
    agg_check = {r["key"]: r["value"] for r in ev.rows if ".aggregate_minus_leaves_2019." in r["key"]}
    tot = leaves.groupby("group")[["q_2019_t", "q_base_t", "q_2050_main_t", "q_2050_literal_latest_t"]].sum()
    for g_, r in tot.iterrows():
        for k, v in r.items():
            ev.put(f"pp.{g_}.{k}", v, "t", "tables/MY_PULP_PAPER_FAOSTAT.csv (leaf items)", "VERIFIED" if k == "q_2019_t" else "PROPOSED (rule)", "B/C")
    e19 = {}; e50 = {}; e50b = {}
    for g_, sec in (("pulp", "Pulp production"), ("paper", "Paper production")):
        q19 = float(tot.at[g_, "q_2019_t"]) if g_ in tot.index else 0.0
        q50 = float(tot.at[g_, "q_2050_main_t"]) if g_ in tot.index else 0.0
        e19[g_] = cm.today_vec(sec, q19)
        e50[g_] = cm.vec2050(sec, q50, exclude=("biomass",))      # closed-loop rule: biomass rows not in T_v2
        e50b[g_] = cm.vec2050(sec, q50)                            # sensitivity: biomass rows as purchased heat
    el19 = sum(v["elec"] for v in e19.values()); tot19 = sum(sum(v.values()) for v in e19.values()); fuel19 = tot19 - el19
    bio50 = sum(v["biomass"] for v in e50b.values())
    PP = pd.DataFrame([dict(case="2019 deduction (FAOSTAT 2019 x JRC-IDEES today, PyPSA-Eur structure; fuel = purchased, spread over the MY 'other' fuel mix)", total_twh=tot19 / 1e6,
                            electricity_twh=el19 / 1e6, fuel_twh=fuel19 / 1e6, pulp_twh=sum(e19["pulp"].values()) / 1e6, paper_twh=sum(e19["paper"].values()) / 1e6),
                       dict(case="2050 main: PyPSA-Eur 2050 without the biomass rows (closed-loop rule, decision 206 item 3)", total_twh=sum(sum(v.values()) for v in e50.values()) / 1e6,
                            electricity_twh=sum(v["electricity"] for v in e50.values()) / 1e6, heat_low_twh=sum(v["heat"] for v in e50.values()) / 1e6, closed_loop_biomass_twh=bio50 / 1e6),
                       dict(case="2050 sensitivity: biomass rows counted as purchased heat", total_twh=sum(sum(v.values()) for v in e50b.values()) / 1e6, closed_loop_biomass_twh=0.0)])
    PP.to_csv(OUT / "MY_PULP_PAPER_ENERGY.csv", index=False, float_format="%.6f")
    for r in PP.itertuples():
        ev.put(f"pp.energy.{r.case[:40]}", r.total_twh, "TWh", r.case, "PROPOSED (quantified)", "C")
    ev.put("pp.2050.closed_loop_biomass", bio50 / 1e6, "TWh", "PyPSA-Eur 2050 biomass rows of pulp and paper (outside T_v2 by the closed-loop rule)", "PROPOSED (quantified)", "C")
    chain_inputs["pp_2019"] = dict(electricity=el19, fuel=fuel19)
    chain_inputs["pp_2050"] = {"main": {k: sum(v[k] for v in e50.values()) for k in cm.OUTC}, "biomass_as_purchased": {k: sum(v[k] for v in e50b.values()) for k in cm.OUTC}}
    chain_inputs["pp_closed_loop_biomass_2050_mwh"] = bio50
    # SFI mills (spatial)
    S = pd.read_excel(SFI_PP, sheet_name="SFI_Pulp_Paper_Database"); S = S[S.country.eq("Malaysia")].copy()
    S["cap_pulp"] = pd.to_numeric(S["capacity_pulp (tonnes per year) "], errors="coerce"); S["cap_paper"] = pd.to_numeric(S["capacity_paper (tonnes per year)"], errors="coerce")
    S["lat"], S["lon"] = S.latitude.astype(float), S.longitude.astype(float)
    S["node"], S["node_method"] = cm.node_of(S, regions)
    n_mills = len(S)
    q_paper = float(tot.at["paper", "q_2019_t"]) if "paper" in tot.index else 0.0
    kq = float(S.cap_paper.sum()); paper_types = ~S.plant_type.astype(str).str.fullmatch("Pulp")
    n_unknown = int((S.cap_paper.isna() & paper_types).sum()); resid = max(0.0, q_paper - kq)
    S["w_paper"] = np.where(S.cap_paper.notna(), S.cap_paper.fillna(0.0) * min(1.0, q_paper / kq if kq else 0.0), np.where(paper_types, resid / max(1, n_unknown), 0.0))
    S["w_pulp"] = S.cap_pulp.fillna(0.0)
    S[["plant_name", "state", "plant_type", "cap_pulp", "cap_paper", "lat", "lon", "node", "node_method", "w_paper", "w_pulp"]].to_csv(OUT / "MY_PULP_PAPER_MILLS_SFI.csv", index=False, float_format="%.6g")
    ev.put("pp.sfi.mills", n_mills, "mills", "SFI 2025-07", "VERIFIED", "B")
    ev.put("pp.sfi.paper_capacity_known", kq, "t", "SFI 2025-07", "VERIFIED", "B")
    ev.put("pp.sfi.paper_mills_without_capacity", n_unknown, "mills", "SFI 2025-07", "VERIFIED", "B")

    # =============================================== LIME (ETSAP 2018) =======================================================
    lime18 = float(etp[etp["product"].astype(str).str.lower().eq("lime")].kt.sum()) * 1e3
    lime_ed = float(ed.at["2.A.2", "kt_CO2_2019"]) * 1e3 / 0.75
    q19 = lime18 * cm.growth(2018) / cm.growth(2019); q50 = lime18 * cm.growth(2018)
    lf, le = float(bat[("lime", "fuel")]), float(bat[("lime", "electricity")])
    LI = pd.DataFrame([dict(item="ETSAP 2018 lime production", value=lime18 / 1e3, unit="kt", source="ETSAP v2.1.0 01_Production_quantities", grade="B"),
                       dict(item="EDGAR 2.A.2 2019 / 0.75 tCO2/t (IPCC high-calcium lime default)", value=lime_ed / 1e3, unit="kt", source="EDGAR 2025 (cross-check)", grade="C"),
                       dict(item="lime 2019 (R3 back-cast)", value=q19 / 1e3, unit="kt", source="derived", grade="C"),
                       dict(item="lime 2050", value=q50 / 1e3, unit="kt", source="G-factor from 2018", grade="C"),
                       dict(item="2019 energy: fuel (ETSAP BAT 1.181 MWh/t)", value=q19 * lf / 1e6, unit="TWh", source="ETSAP BAT (no ODA factor)", grade="C"),
                       dict(item="2019 energy: electricity (ETSAP BAT 0.061 MWh/t)", value=q19 * le / 1e6, unit="TWh", source="ETSAP BAT", grade="C"),
                       dict(item="2050 energy: gas (fuel, BAT unchanged)", value=q50 * lf / 1e6, unit="TWh", source="no PyPSA-Eur lime sector (C)", grade="C"),
                       dict(item="2050 energy: electricity", value=q50 * le / 1e6, unit="TWh", source="same", grade="C")])
    LI.to_csv(OUT / "MY_LIME.csv", index=False, float_format="%.6f")
    for r in LI.itertuples():
        ev.put(f"lime.{r.item}", r.value, r.unit, r.source, "VERIFIED" if r.grade == "B" else "PROPOSED (quantified)", r.grade)
    lv50 = {k: 0.0 for k in cm.OUTC}; lv50["gas"] = q50 * lf; lv50["electricity"] = q50 * le
    chain_inputs["lime_2019"] = dict(fuel=q19 * lf, electricity=q19 * le); chain_inputs["lime_2050"] = lv50
    ev.put("glass.my_production_on_disk", 0, "-", "ETSAP has no MY glass; EDGAR 2.A.3 MY 2019 1.57 kt CO2 (carbonate process only); no plant list", "VERIFIED", "E")

    ev.extra["chain_inputs"] = chain_inputs
    ev.extra["usgs_cement_my_kt"] = usgs
    ev.write(OUT / "_products_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200); pd.set_option("display.max_colwidth", 70)
    print(CE.to_string()); print(AL.to_string())
    print(CP[["plant", "region", "node", "product", "capacity_kt", "output_2019_kt", "in_2019_base", "fuel_in_other_central"]].to_string())
    print((agg / 1e6).round(3).to_string())
    print(PF[["group", "item", "q_2019_t", "flag_2019", "base_year", "q_base_t", "flag_base", "latest_year", "q_latest_t"]].to_string()); print(agg_check)
    print(PP.round(3).to_string()); print(LI.round(3).to_string())
    print(json.dumps({k: (v if not isinstance(v, dict) else "...") for k, v in chain_inputs.items()}, default=str))


if __name__ == "__main__":
    main()
