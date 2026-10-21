"""M08b (decisions 126, 129, 131, 133, 134) and its supplement 01 (decision 137): registry rows of the demand anchoring / useful-heat step.

    python scripts_project/m08b_data.py      # after m08b_demand.py, m08b_heat_bands.py, s3_0_industry.py; then python scripts_project/d1_registry.py

Writes research_inputs/registry_v5/fragments/m08b.csv (new rows: the 16 M08b rows of REGISTRY_ROWS_PROPOSED_v2.csv as implemented, plus the
rule rows of this step) and fragments/m08b_corrections.csv (full-row replacements applied by d1_registry.py after the M08a corrections).
A superseded row keeps its value, gets status REFERENCE_ONLY and the description suffix " | [M08b <task>] 历史：已被 <new id> 替代 ..."; the
rows to replace are taken from the assembly of all other fragments (+ the M08-0 / M08a corrections), never from an earlier M08b output.
Values are read from the tables the build uses (never typed in twice).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from d1_common import COLUMNS, DEMAND_DIR, REG_DIR, ROOT, Registry, sha256, write_csv   # noqa: E402
from d1_demand_2050 import AEO8_PDF_SHA   # noqa: E402
from s2_layers import HEAT_BAND_TECH   # noqa: E402

SCRIPT = "scripts_project/m08b_data.py"
STEP = "M08b"
ANCHORS = DEMAND_DIR / "DEMAND_ANCHOR_AEO8_ATS.csv"
ANCHOR_TABLE = DEMAND_DIR / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
EVIDENCE = DEMAND_DIR / "DEMAND_ANCHOR_M08B_EVIDENCE.json"
OUTPUT_BASE = DEMAND_DIR / "INDUSTRY_OUTPUT_BASE_M08B.csv"
OUTPUT_2050 = DEMAND_DIR / "INDUSTRY_OUTPUT_2050_M08B.csv"
PLAN_CAPS = DEMAND_DIR / "INDUSTRY_OUTPUT_PLAN_CAPS.csv"
HEAT_BANDS = DEMAND_DIR / "INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv"
HEAT_BANDS_JSON = DEMAND_DIR / "INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.json"
SUMMARY = DEMAND_DIR / "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
D2 = DEMAND_DIR / "sources" / "m08b" / "AEO8_TABLE_D2_REAL_GDP_PPP2017.csv"
TECH_MAP = DEMAND_DIR / "INDUSTRY_HEAT_BAND_TECHNOLOGY_MAP.csv"
S4R_PLAN = ROOT / "research/06_scope_redesign/p1_step4r_20261020/S4R_PLAN.md"   # literature / assumption rows cite the plan that collected them
ATS_SRC = "ACE, 8th ASEAN Energy Outlook 2023-2050 (2024)"
DEA_SRC = "Danish Energy Agency, Technology Data for Industrial Process Heat (catalogue, version 0006 text, 2026); technology-data v0.15.0 rows from its datasheet"


class Corrections:
    """Full-row replacements built from the registry assembled WITHOUT the M08b fragments (deterministic re-runs)."""

    def __init__(self):
        import d1_registry
        frames = [pd.read_csv(REG_DIR / "fragments" / f"{f}.csv", dtype=str, keep_default_na=False) for f in d1_registry.FRAGMENTS if not f.startswith("m08b")]
        u = Registry("scripts_project/d1_registry.py"); d1_registry.unit_rows(u)
        frames.append(pd.DataFrame(u.rows, columns=COLUMNS))
        df = pd.concat(frames, ignore_index=True)[COLUMNS]
        for f in d1_registry.CORRECTIONS:
            if f.startswith("m08b"):
                continue
            corr = pd.read_csv(REG_DIR / "fragments" / f"{f}.csv", dtype=str, keep_default_na=False)[COLUMNS]
            df = pd.concat([df[~df.param_id.isin(corr.param_id)], corr], ignore_index=True)
        self.base = df.set_index("param_id")
        self.rows = {}

    def _refs(self, r, ref):
        refs = [x.strip() for x in str(r.get("decision_ref", "")).replace(";", ",").split(",") if x.strip()]
        return ", ".join(refs + [x for x in (ref,) if x not in refs])

    def supersede(self, pid: str, by: str, task: str, ref: str, note: str = ""):
        if pid in self.rows:
            raise ValueError(f"{pid} superseded twice")
        r = self.base.loc[pid].to_dict()
        r["description"] = f"{r['description']} | [{STEP} {task}] 历史：已被 {by} 替代" + (f" ({note})" if note else "")
        r["status"] = "REFERENCE_ONLY"; r["decision_ref"] = self._refs(r, ref); r["param_id"] = pid
        self.rows[pid] = r

    def modify(self, pid: str, task: str, ref: str, note: str, **changes):
        if pid in self.rows:
            raise ValueError(f"{pid} corrected twice")
        r = self.base.loc[pid].to_dict()
        r.update({k: ("" if v is None else str(v)) for k, v in changes.items()})
        r["description"] = f"{r['description']} | [{STEP} {task}] 修改：{note}"
        r["decision_ref"] = self._refs(r, ref); r["param_id"] = pid; r["derivation_script"] = SCRIPT
        self.rows[pid] = r

    def has(self, pid: str) -> bool:
        return pid in self.base.index


def sens(r, prod: str) -> tuple[float, float]:
    """(low, high) Mt of the registered sensitivities: elasticity 0.3-0.8 and per-capita saturation range, each with the other inputs at the main value."""
    cols = [f"{prod}_2050_elasticity_low_mt", f"{prod}_2050_elasticity_high_mt", f"{prod}_2050_saturation_low_mt", f"{prod}_2050_saturation_high_mt", f"{prod}_2050_mt"]
    vals = [float(r[k]) for k in cols]
    return min(vals), max(vals)


# --- B1 (M08-5, decision 134): activity anchors --------------------------------------------------------------------------------
def b1_demand(reg: Registry, cor: Corrections):
    an = pd.read_csv(ANCHORS).set_index("country"); ev = json.loads(EVIDENCE.read_text()); tot = ev["totals"]
    src = f"anchors:{sha256(ANCHORS)}; table:{sha256(ANCHOR_TABLE)}"
    base_by = ", ".join(f"{c} {an.at[c, 'base_load_anchor_mwh'] / 1e6:,.1f}" for c in ["VN", "ID", "TH", "MY", "PH", "SG", "MM", "KH", "LA", "BN", "TL"])
    reg.add("demand_anchor_family_main", "R1 (decisions 126, 129; M08b B1): activity-level anchor family for the 2050 demand = ACE AEO8 (2024) AMS Targets Scenario (ATS): per-capita "
            "TFEC and electricity by country (Table C.8 p.187) x population (Table D.1 p.188); sector split = regional ATS sector growth (Table C.3 ATS panel, 2022 -> 2050) x each "
            "country 2019 sector structure (D1 table base_2019_mwh), normalised; ONLY activity levels are anchored (base electricity load, transport fuel / service, industry incl. "
            "non-energy use, physical output, and - supplement 01 section 3 - the residential / commercial / agriculture fuel rows, demand_sector_fuel_anchor_rule); industry "
            "electricity and all carrier structures endogenous; international bunkers stay UNSD 2019 constants (decision 10); config research.demand.growth_method = ats_anchor "
            "(demand table DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv, scripts_project/m08b_demand.py); ratio (BAS growth, upper bound) / level and the "
            "country_allocation variants stay as sensitivities",
            "aeo8_ats", "flag", "B", ATS_SRC, "Tables C.3, C.8, D.1; DEMAND_ANCHOR_AEO8_ATS.csv", src, decision_ref="126, 129, 134, 137")
    fu = {k: (tot[f"{k}_fuel_anchor_11_twh"], tot[f"{k}_fuel_ratio_table_11_twh"]) for k in ("residential", "commercial", "agriculture")}
    reg.add("demand_sector_fuel_anchor_rule", "Supplement 01 section 3 (decision 137; M08b): residential / commercial / agriculture-and-others fuel demand 2050 by country = ATS sector "
            "TFEC anchor (ATS country TFEC x the normalised TFEC weight of demand_transport_anchor_rule: 2019 sector TFEC x Table C.3 ATS sector growth) - the sector electricity "
            "anchor of demand_base_load_rule; the fuel rows of the sector keep their 2019 carrier structure (cooking LPG, biomass, coal, ...; the ratio table has one multiplier per "
            "sector) scaled to the anchor; a negative anchor is set to 0 and listed (demand_sector_fuel_anchor_zeroed), never filled from another source; 11 countries TWh "
            + "; ".join(f"{k} {a:,.1f} (ratio table {b:,.1f})" for k, (a, b) in fu.items()) + "; the build checks every country and sector against the anchor (1e-9); "
            "international bunkers unchanged (UNSD 2019, decision 10)", "tfec_minus_electricity", "rule", "B", ATS_SRC + "; D1 demand table (2019 sector structure)",
            "DEMAND_ANCHOR_AEO8_ATS.csv *_fuel_anchor_mwh", src, decision_ref="134, 137")
    zl = tot["fuel_anchor_zeroed"]
    reg.add("demand_sector_fuel_anchor_zeroed", "Supplement 01 section 3 item 3: country-sector fuel anchors set to 0 (TWh, anchor before zeroing): "
            + "; ".join(f"{z['country']} {z['sector']} {z['anchor_mwh'] / 1e6:+.3f} ({z['reason']})" for z in zl)
            + f"; negative = the sector electricity anchor exceeds the sector TFEC anchor (together {-sum(z['anchor_mwh'] for z in zl if z['reason'] == 'negative') / 1e6:,.2f} TWh: the "
            "sector total then equals the electricity anchor and the country TFEC exceeds the ATS TFEC anchor by that amount); no_2019_fuel_rows = positive anchor but the sector has no 2019 "
            "fuel row to carry a carrier structure (left at 0, not allocated); mechanism (INFERENCE): residential TFEC falls in ATS (C.3 0.84 x, traditional biomass phase-out) while "
            "residential electricity rises (1.14 x), and these countries have small 2019 fuel shares", f"{len(zl)} cells", "list", "C", ATS_SRC,
            "DEMAND_ANCHOR_M08B_EVIDENCE.json totals.fuel_anchor_zeroed", src, decision_ref="137")
    cor.supersede("demand_country_allocation_mode", "demand_anchor_family_main", "B1", "134", "aeo8_ats_relative allocation kept as the ratio-table sensitivity")
    cor.supersede("demand_growth_method", "demand_anchor_family_main", "B1", "134", "ratio = BAS-growth upper-bound sensitivity, level = sensitivity")
    reg.add("demand_base_load_rule", "R1 (supplement 01 section 2 (a); M08b B1): base (non-industry) electricity load 2050 by country = AEO8 ATS country electricity (C.8 per capita x D.1 "
            "population) x normalised sector weights restricted to residential + commercial + agriculture/other + 2019 transport electricity (rail / existing electric road; EV is a "
            "separate load); weights = 2019 sector electricity (D1 table) x ATS sector growth 2022-2050 (residential electricity 29.0 -> 33.2 Mtoe, section 3.1.3 p.61; commercial "
            "29.5 -> 50.4, agriculture/others 8.8 -> 27.8, industry 186 -> 387, transport 145.2 -> 228.2 Mtoe, Table C.3 ATS panel); TL by the TL rule; the anchors are written "
            f"into the electricity rows of the ats_anchor table and read through nonindustrial_electricity table_sectors (Astar = hourly shape, node split); result 11 countries "
            f"{tot['base_load_anchor_11_twh']:,.1f} TWh (ratio table {tot['base_load_ratio_table_11_twh']:,.1f}; buildings + agriculture only {tot['base_load_buildings_agri_11_twh']:,.1f}); "
            f"TWh: {base_by}; all non-negative; validation: 10-country residential electricity {tot['residential_elec_10_twh']:,.1f} TWh vs AEO8 ATS {tot['aeo8_ats_residential_elec_2050_twh']:,.1f} TWh; "
            "S4R supplement 01 gave 966 TWh with the BAS-panel industry 2022 value 185.6 (ATS panel prints 186); the build checks every country against the anchor (1e-9)",
            "ats_buildings_agri", "rule", "B", ATS_SRC + "; D1 demand table (2019 sector electricity)", "DEMAND_ANCHOR_AEO8_ATS.csv base_load_anchor_mwh", src, decision_ref="129, 134")
    cor.supersede("s4j1_base_load_sectors", "demand_base_load_rule", "B1", "134", "same sector scope, annual totals from the ATS anchor instead of the ratio table")
    reg.add("demand_transport_anchor_rule", "R1 (supplement 01 section 2 (c); M08b B1): transport anchored at the service level: ATS country TFEC x normalised sector weights (2019 sector "
            "TFEC x Table C.3 ATS growth, non-energy use counted with industry) = 2050 transport final-energy anchor; the transport fuel rows of the ats_anchor table carry (anchor - "
            "transport electricity anchor of demand_base_load_rule) in their 2019 fuel shares, so the transport total equals the anchor and the electricity part is not counted twice; "
            "the service conversion and electrification follow the current method, stated as such: land transport oil-equivalent x PyPSA-Eur v2025.07.0 2050 shares (registry "
            "share_land_transport_electric/fuel_cell/ice_share_2050 = 1 / 0 / 0) and efficiencies (share_transport_*_efficiency), aviation / rail fuel as fuel, shipping as methanol; "
            "AEO8 prints no ATS carrier efficiencies by country -> the table carrier structure is used (grade C); "
            f"11 countries {tot['transport_anchor_11_twh']:,.1f} TWh (ratio table {tot['transport_ratio_table_11_twh']:,.1f})",
            "ats_service", "rule", "C", ATS_SRC, "DEMAND_ANCHOR_AEO8_ATS.csv transport_anchor_mwh, transport_fuel_multiplier", src, decision_ref="129, 134")
    reg.add("demand_industry_electricity_not_anchored", "R1 (supplement 01 section 2 (b)): industry electricity is an endogenous model result (physical output x PyPSA-Eur 2050 routes + "
            "useful-heat bands with carrier choice + other-bucket electricity), never a fixed load anchored to ATS; the earlier M08-5 formula base load = ATS electricity - route "
            "electricity is withdrawn; ATS-implied industry electricity is only reported (DEMAND_ANCHOR_AEO8_ATS.csv industry_elec_ats_implied_mwh)",
            "endogenous", "flag", "B", "S4R supplement 01 section 2", "S4R_PLAN.md R1", src, decision_ref="129, 134")
    reg.add("demand_anchor_family_control", "R1: control anchor = ERIA RPR FY2024 No.12 LCET-CN country chapters (TFEC, generation 2050); IEA SEAEO 2024 STEPS / APS as regional sanity check",
            "eria_lcet_cn", "flag", "B", "ERIA (2024) Analysis on Energy Cost of LCET-CN, RPR FY2024 No.12, Ch.2-16; IEA SEAEO 2024 p.54, 86", "country chapters; S4R_PLAN.md R1", f"plan:{sha256(S4R_PLAN)}", decision_ref="126")
    tl = an.loc["TL"]
    reg.add("demand_anchor_tl_rule", f"R1 (M08b B1): Timor-Leste is outside AEO8 -> per-capita TFEC ({tl.ats_tfec_pc_2050_kgoe:.2f} kgoe) and electricity ({tl.ats_elec_pc_2050_kwh:.1f} kWh) = simple "
            f"mean of the KH / LA / MM ATS 2050 values; population UN WPP 2024 median 2050 = {tl.population_2050_million * 1e6:,.1f} (UN Data Portal export, registry "
            "download_un_wpp2024_tl_population_2050, now used); GDP growth for the output rule = mean of KH / LA / MM (Table D.2)",
            "mean_KH_LA_MM", "rule", "C", "AEO8 Tables C.8, D.2; UN WPP 2024", "DEMAND_ANCHOR_AEO8_ATS.csv row TL", src, country="TL", decision_ref="126, 134")
    reg.add("demand_ats_residential_electricity", "AEO8 ATS residential electricity 2022 -> 2050 = 29.0 -> 33.2 Mtoe (section 3.1.3 p.61); the only sector electricity value AEO8 prints; growth "
            "proxy of the residential weight in demand_base_load_rule (constant in scripts_project/m08b_demand.py)", 33.2, "Mtoe", "B", ATS_SRC, "section 3.1.3 p.61", f"AEO8 pdf:{AEO8_PDF_SHA}", sensitivity_low=29.0, sensitivity_high=33.2, decision_ref="129, 134")
    reg.add("demand_aeo8_d2_real_gdp", "AEO8 Table D.2 real GDP PPP at 2017 constant prices (million USD), 2005-2050 by country, extracted from the PDF text layer (p.190, printed 188) into "
            "research_inputs/demand_v5/sources/m08b/AEO8_TABLE_D2_REAL_GDP_PPP2017.csv; G = 2050 / 2022 for the physical output rule (VN 3.760; the S4R script used D.6 x D.1 = 3.760)",
            "AEO8_TABLE_D2_REAL_GDP_PPP2017.csv", "file", "B", ATS_SRC, "Table D.2 p.190", sha256(D2), decision_ref="134", status="REFERENCE_ONLY")
    reg.add("demand_ats_anchor_table", "M08b B1: demand table of growth_method ats_anchor (same columns as the D1 tables; anchored rows carry the rule in growth_method) and the per-country "
            "anchor table DEMAND_ANCHOR_AEO8_ATS.csv (written by scripts_project/m08b_demand.py)", "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", "file", "B",
            "derived", "research_inputs/demand_v5", src, decision_ref="134", status="REFERENCE_ONLY")


def b1_output(reg: Registry, cor: Corrections):
    out = pd.read_csv(OUTPUT_2050).set_index("country"); base = pd.read_csv(OUTPUT_BASE).set_index("country"); summ = pd.read_csv(SUMMARY).set_index("country")
    src = f"output:{sha256(OUTPUT_2050)}; base:{sha256(OUTPUT_BASE)}"
    reg.add("industry_output_rule_2050", "R1.3 (supplement 01, decisions 129, 134; M08b B1): physical output 2050 = min(base x G^((2050 - base year)/28 x elasticity), per-capita saturation x "
            "population 2050, national plan cap where one exists); plan caps are caps only and never raise output; one rule for the 11 countries; G = AEO8 Table D.2 real GDP "
            "2050 / 2022 (TL mean of KH / LA / MM) applied at the same CAGR after the base year; elasticity industry_output_elasticity, saturation industry_percap_saturation_*, "
            "base years industry_output_base_year; config research.s2.industry.physical_output_rule = sqrt_gdp_capped (industry_multiplier = former 2019 x multiplier rule); "
            f"11 countries cement {out.cement_2050_mt.sum():,.1f} Mt, crude steel {out.steel_2050_mt.sum():,.1f} Mt; non-output industry (ammonia, methanol, HVC, energy fallback) "
            "scales with the ATS industry multiplier, routes PyPSA-Eur 2050", "sqrt_gdp_capped", "rule", "C",
            "AEO8 Tables D.1, D.2; USGS MYB 2023 Cement T22; worldsteel Steel Data Viewer; Decision 1266/QD-TTg (2020); Decision 261/QD-TTg (2026)",
            "INDUSTRY_OUTPUT_2050_M08B.csv", src, decision_ref="126, 129, 134")
    reg.add("industry_output_base_year", "R1.3 (supplement 01; M08b B1): latest year of one source for the 11 countries: cement 2023 = USGS Minerals Yearbook 2023 Cement Table 22 "
            "(thousand t; BN 324 e, ID 66,924, KH 8,700 e, LA 7,100 e, MM 8,500 e, MY 23,191, PH 30,000 e, TH 42,740 e, VN 106,952; e = estimate, flagged grade C; SG, TL not "
            "listed -> 0); crude steel 2024 = worldsteel Steel Data Viewer (thousand t; ID 18,642, MM 500, MY 9,014, PH 1,666, SG 259, TH 4,918, VN 21,974; BN, KH, LA, TL not listed "
            "-> 0); growth after the base year at the AEO8 2022-2050 CAGR", "cement 2023; crude steel 2024", "year", "B",
            "USGS MYB 2023 Cement (advance release); worldsteel Steel Data Viewer (export 2026-10-20)", "INDUSTRY_OUTPUT_BASE_M08B.csv", f"base:{sha256(OUTPUT_BASE)}", decision_ref="129, 131, 134")
    reg.add("industry_output_elasticity", "R1.3 (supplement 01): output-to-GDP elasticity 0.5 registered as an ASSUMPTION (grade C); literature found gives saturation evidence, not a point "
            "elasticity: Bleischwitz et al. 2018 (per-capita steel and cement consumption saturate from ~US$12,000 GDP/cap in four industrialised countries, 30+ year lag), van Ruijven "
            "et al. 2016 (SSP2 steel / cement demand plateaus after rapid growth), Global Cement (cement <= 600 kg/cap above US$25,000 GDP/cap); sensitivity 0.3-0.8 "
            "(INDUSTRY_OUTPUT_2050_M08B.csv *_elasticity_low/high_mt)", 0.5, "dimensionless", "C",
            "Bleischwitz et al. (2018) Global Environmental Change 48:86-96; van Ruijven et al. (2016) RCR 112:15-36; Global Cement magazine", "S4R_PLAN.md R1.3", f"plan:{sha256(S4R_PLAN)}",
            sensitivity_low=0.3, sensitivity_high=0.8, decision_ref="129, 134")
    reg.add("industry_percap_saturation_cement", "R1.3 (supplement 01): cement per-capita saturation 1.0 t/cap/a, ASSUMPTION (grade C), upper end of observed industrialised peaks (China ~1.7-1.8 "
            "t/cap 2014, Viet Nam 0.91 t/cap 2020 incl. exports, USA 0.25-0.31, mature economies <= 0.6 t/cap above US$25,000 GDP/cap); binds for VN (107.0 Mt) and LA (9.8 Mt) in the main run",
            1.0, "t/cap/a", "C", "Global Cement magazine; Statista / IndexBox 2020 per-capita figures (secondary)", "S4R_PLAN.md R1.3", f"plan:{sha256(S4R_PLAN)}", sensitivity_low=0.6, sensitivity_high=1.2, decision_ref="129, 134")
    reg.add("industry_percap_saturation_steel", "R1.3 (supplement 01): crude steel per-capita saturation 0.6 t/cap/a, ASSUMPTION (grade C): worldsteel apparent steel use per capita 2011-2012 Korea "
            "1,114-1,157 kg, Taiwan 784-926 kg, Japan 506 kg (secondary); Pauliuk et al. 2013 in-use stock saturation 13 +- 2 t/cap; Decision 261/QD-TTg 2050 570-650 kg finished steel "
            "per capita; binds for no country in the main run", 0.6, "t/cap/a", "C", "worldsteel World Steel in Figures 2012 / 2013 (via AIST); Pauliuk, Wang, Mueller (2013) RCR 71; Decision 261/QD-TTg (2026)",
            "S4R_PLAN.md R1.3", f"plan:{sha256(S4R_PLAN)}", sensitivity_low=0.4, sensitivity_high=0.8, decision_ref="129, 134")
    v = out.loc["VN"]
    reg.add("industry_cement_2050_VN", f"R1.3 (supplement 01; M08b B1): VN cement 2050 = min(growth rule {v.cement_growth_rule_mt:.1f}, per-capita {v.cement_percap_cap_mt:.1f}, plan cap "
            f"{float(v.cement_plan_cap_mt):.0f}) = {v.cement_2050_mt:.1f} Mt (per-capita cap binds; base USGS 2023 {v.cement_base_mt:.3f} Mt; replaces 581 Mt of the ratio table)",
            v.cement_2050_mt, "Mt/a", "C", "rule industry_output_rule_2050", "INDUSTRY_OUTPUT_2050_M08B.csv row VN", src, country="VN", decision_ref="126, 129, 134",
            sensitivity_low=sens(v, "cement")[0], sensitivity_high=sens(v, "cement")[1])
    for c in out.index:
        if c == "VN":
            continue
        r = out.loc[c]
        reg.add(f"industry_cement_2050_{c}", f"{c} cement 2050 by industry_output_rule_2050 = min(growth {r.cement_growth_rule_mt:.4g}, per-capita {r.cement_percap_cap_mt:.4g}"
                + (f", plan {float(r.cement_plan_cap_mt):.4g}" if str(r.cement_plan_cap_mt) not in ("", "nan") else "") + f") = {r.cement_2050_mt:.4g} Mt ({r.cement_binding}; base "
                f"{base.at[c, 'cement_source']}); sensitivity = elasticity 0.3-0.8 and saturation 0.6-1.2 t/cap", r.cement_2050_mt, "Mt/a", "C", "rule industry_output_rule_2050",
                f"INDUSTRY_OUTPUT_2050_M08B.csv row {c}", src, country=c, decision_ref="134", status="REGISTERED" if r.cement_2050_mt > 0 else "SOURCE_ZERO",
                sensitivity_low=sens(r, "cement")[0], sensitivity_high=sens(r, "cement")[1])
    for c in out.index:
        pid = f"industry_steel_2050_{c}"
        if not cor.has(pid):
            continue
        r = out.loc[c]; s = summ.loc[c]
        note = (f"physical output rule (M08b B1): min(growth {r.steel_growth_rule_mt:.4g}, per-capita {r.steel_percap_cap_mt:.4g}"
                + (f", plan {float(r.steel_plan_cap_mt):.4g}" if str(r.steel_plan_cap_mt) not in ("", "nan") else "") + f") = {r.steel_2050_mt:.4g} Mt ({r.steel_binding}; base worldsteel 2024 "
                f"{r.steel_base_mt:.4g} Mt); H2-DRI primary {s.primary_dri_2050_t:.4g} t, scrap EAF {s.secondary_eaf_2050_t:.4g} t"
                + ("; the earlier S4R value 70 Mt took the plan as a floor and is withdrawn (Decision 261 = cap only)" if c == "VN" else ""))
        lo, hi = sens(r, "steel")
        cor.modify(pid, "B1", "134", note + "; sensitivity = elasticity 0.3-0.8 and saturation 0.4-0.8 t/cap", value=f"{s.crude_steel_2050_t:.12g}", tier="C",
                   source="rule industry_output_rule_2050 (worldsteel 2024 base)", source_locator=f"INDUSTRY_OUTPUT_2050_M08B.csv row {c}", source_sha256=src,
                   sensitivity_low=f"{lo * 1e6:.12g}", sensitivity_high=f"{hi * 1e6:.12g}")
    reg.add("industry_output_plan_sensitivity_VN", "R1.3 (supplement 01): national plan values only as caps / sensitivity - VN crude steel 65-70 Mt 2050 (Decision 261/QD-TTg), VN cement "
            "<= 150 Mt capacity cap (Decision 1266/QD-TTg); never used to raise the main-run output (INDUSTRY_OUTPUT_PLAN_CAPS.csv; without-plan column in INDUSTRY_OUTPUT_2050_M08B.csv)",
            "steel_65_70_cement_150", "sensitivity", "B", "Decision 261/QD-TTg (2026-02-09); Decision 1266/QD-TTg (2020-08-18) Annex I", "MOIT summary page; Cong bao 843-844 pp.34-35",
            f"plan:{sha256(PLAN_CAPS)}", country="VN", decision_ref="129, 134")


# --- B2 (M08-6, decision 133): useful-heat bands and the biomass overflow ------------------------------------------------------
TEMPERATURE_BASIS = {   # (band, technology-data row) -> temperature coverage (DEA industrial process heat catalogue; supplement 01 section 2)
    ("low", "electric boiler steam"): "DEA 310.1 electric boiler steam: 1-16 bar, typically 8 bar / 175 C (covers < 150 C)",
    ("medium_a", "electric boiler steam"): "DEA 310.1 electric boiler steam: 1-16 bar (16 bar saturated steam about 200 C), typically 8 bar / 175 C -> up to 200 C (medium A only)",
    ("low", "industrial heat pump high temperature"): "DEA 302.b high-temperature heat pump up to 150 C (low band only, decision 133)",
    ("low", "gas boiler steam"): "DEA 311.1c steam boiler: steam 125-300 C (up to 311 C at 100 bar); not for firing / melting",
    ("medium_a", "gas boiler steam"): "DEA 311.1c steam boiler: steam 125-300 C (covers 150-200 C)",
    ("medium_b", "gas boiler steam"): "DEA 311.1c steam boiler: steam 125-300 C (up to 311 C at 100 bar) -> covers the 200-300 C part of medium B",
    ("low", "solid biomass boiler steam"): "DEA 311.1e steam boiler wood: steam 125-300 C; not for firing / melting",
    ("medium_a", "solid biomass boiler steam"): "DEA 311.1e steam boiler wood: steam 125-300 C (covers 150-200 C)",
    ("medium_b", "direct firing gas"): "300-400 C part of medium B: no technology-data steam row covers it; fuel combustion reaches the temperature -> the direct-firing gas row "
                                       "(DEA 312.a, 400-1,600 C) is the cost representative (supplement 01 section 2, grade C)",
    ("medium_b", "direct firing solid fuels"): "300-400 C part of medium B: direct-firing solid fuels row (DEA 312.b, coal / biomass multifuel burners) as the cost representative "
                                               "(supplement 01 section 2, grade C)",
    ("high", "direct firing gas"): "DEA 312.a direct firing natural gas: 400-800 C and > 800 C up to 1,600 C",
    ("high", "direct firing solid fuels"): "DEA 312.b direct firing solid fuels (coal / biomass multifuel burners): high-temperature processes",
}


def b2_heat(reg: Registry, cor: Corrections):
    hb = pd.read_csv(HEAT_BANDS).set_index("carrier"); hj = json.loads(HEAT_BANDS_JSON.read_text()); ms = hj["medium_split"]; f_a = float(ms["medium_a_fraction"])
    src = f"bands:{sha256(HEAT_BANDS)}; idees:{hj['source']['sha256']}"
    shares = "; ".join(f"{c} low {hb.at[c, 'share_low']:.3f} / medium A {hb.at[c, 'share_medium_a']:.3f} / medium B {hb.at[c, 'share_medium_b']:.3f} / high {hb.at[c, 'share_high']:.3f} / "
                       f"mechanical {hb.at[c, 'share_mechanical']:.3f}" for c in hb.index)
    reg.add("industry_route_mode_proposed", "R1.4 / R4 (decision 133; M08b B2; supplement 01 decision 137): 'other industry' bucket (UNSD other / construction / mining -> PyPSA-Eur 'Other "
            "industrial sectors') and the biomass overflow are converted to useful heat by temperature band (low < 150 C, medium A 150-200 C, medium B 200-400 C, high > 400 C) served "
            "endogenously by the technology-data v0.15.0 options of each band (industry_heat_band_technology_map); physical-output sectors and the other energy-fallback sub-sectors keep the "
            "PyPSA-Eur 2050 routes (St_primary_fraction 0.3, DRI_fraction 1.0, HVC_primary_fraction 0.4); config research.s3.industry.other_bucket = useful_heat_bands (pypsa_eur_2050 = "
            "former main, sensitivity)",
            "useful_heat_bands", "flag", "C", "deviation from PyPSA-Eur (fixed 2050 carrier ratios) - reason: ASEAN industry base is coal / biomass heat, full-route electrification gave "
            "industry electricity 1.7-4.2 x the external anchors", "S4R_PLAN.md R1.4; s3_0_industry.py useful_heat_bands", src, decision_ref="126, 133, 137")
    cor.supersede("industry_other_bucket_mode", "industry_route_mode_proposed", "B2", "133", "pypsa_eur_2050 kept as sensitivity")
    reg.add("industry_other_bucket_heat_band_shares", "M08b B2 + supplement 01 section 2: temperature-band split of the other-bucket fuels from JRC-IDEES-2021 EU27 'Other industrial "
            "sectors' 2019 final energy by process (sheet OIS_fec; scripts_project/m08b_heat_bands.py): low = low-enthalpy heat, thermal / steam drying, thermal / steam process cooling; "
            f"medium = steam processing, split at 200 C into medium A (x {f_a:g}) and medium B (x {1 - f_a:g}) (industry_heat_band_medium_split); high = thermal processing (fuel-fired "
            "process heating); mechanical = diesel motors (fuel kept as final energy; industry_other_bucket_mechanical_fuel); shares by ASEAN carrier: " + shares +
            "; heat uses x 0.90 (existing_boiler_efficiency) = useful heat; other-bucket electricity kept as electricity (non-thermal; JRC thermal electricity is a small share); "
            "process-to-band mapping is an assumption (grade C; DEA temperature levels); EU27 distribution (ASEAN distribution DATA_PENDING, industry_heat_band_asean_distribution)",
            "INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv", "file", "C", "JRC-IDEES-2021 Industry EU27 (CC BY 4.0); DEA industrial process heat catalogue", "sheet OIS_fec, 2019", src, decision_ref="133, 137")
    reg.add("industry_heat_band_medium_split", "Supplement 01 section 2 (decision 137): the JRC-IDEES temperature split has no 200 C breakpoint (steam processing is one 150-400 C process), "
            f"so the medium share is divided by linear interpolation in temperature inside 150-400 C: medium A (150-200 C) = (200 - 150) / (400 - 150) = {f_a:g} of the medium share, "
            f"medium B (200-400 C) = {1 - f_a:g}; same fraction for every carrier and for the medium part of the fixed industrial biomass (overflow source band); ASSUMPTION grade C; "
            f"sensitivity +-50 % of the 200 C breakpoint share = {ms['sensitivity'][0]:g}-{ms['sensitivity'][1]:g} (research.s2.industry.heat_band_medium_a_fraction; regenerate "
            "the band tables, the build refuses a value that differs from them); note (INFERENCE): DEA quotes industrial steam typically 8 bar / 175 C, so a linear split may put less "
            "of the steam use below 200 C than a temperature-resolved ASEAN distribution would", f_a, "fraction", "C", "linear interpolation (supplement 01 section 2); JRC-IDEES-2021 OIS",
            "m08b_heat_bands.MEDIUM_A_FRACTION", src, sensitivity_low=ms["sensitivity"][0], sensitivity_high=ms["sensitivity"][1], decision_ref="137")
    rows = []
    for band, techs in HEAT_BAND_TECH.items():
        for tech, carrier, fuel in techs:
            rows.append(dict(band=band, technology_data_row=tech, link_carrier=carrier, input=fuel, capture=carrier.endswith(" CC"), temperature_basis=TEMPERATURE_BASIS[(band, tech)]))
    write_csv(rows, TECH_MAP, list(rows[0].keys()))
    reg.add("industry_heat_band_technology_map", "M08b B2 (decision 133) + supplement 01 section 2 (decision 137): useful-heat band -> technology-data v0.15.0 rows (efficiency, investment, "
            "FOM, VOM, lifetime from the active cost layer; biomass CC = same row + biomass boiler capture x CO2 x capture fraction): low = electric boiler steam (0.99), industrial heat "
            "pump high temperature (COP 3.2), gas boiler steam (0.94), solid biomass boiler steam (0.90) +CC; medium A (150-200 C) = electric boiler steam, gas boiler steam, solid biomass "
            "boiler steam +CC; medium B (200-400 C) = gas boiler steam (to 300 C), direct firing gas (1.0) and direct firing solid fuels (biomass, 1.0) +CC as the 300-400 C representative "
            "(fuel combustion reaches the temperature; grade C), NO electric heating (no technology-data row covers > 200 C: electric boiler steam about <= 200 C); high = direct firing gas, "
            "direct firing solid fuels +CC, no electric heating (no electric direct-firing / furnace row in v0.15.0, although the DEA 2026 catalogue lists electric direct firing 400-800 C); "
            "heat pumps low band only; NO hydrogen heating in any band (industry_heat_hydrogen_not_represented); table INDUSTRY_HEAT_BAND_TECHNOLOGY_MAP.csv; code s2_layers.HEAT_BAND_TECH",
            "INDUSTRY_HEAT_BAND_TECHNOLOGY_MAP.csv", "file", "C", "technology-data v0.15.0 (costs_2050); " + DEA_SRC, "s2_layers.HEAT_BAND_TECH",
            f"map:{sha256(TECH_MAP)}", decision_ref="133, 137")
    reg.add("biomass_overflow_rule", "R4 (decision 133; M08b B2; supplement 01): fixed solid-biomass demand above the national potential (industry first, then agriculture) is converted to "
            "useful heat x 0.90 (research.s2.industry.biomass_overflow_useful_heat_efficiency) in the band of its source: industry -> medium A / medium B / high by the source shares of the "
            "fixed industrial biomass (cement kiln fuel high, steam / drying use of the route sectors medium, split at 200 C by industry_heat_band_medium_split; "
            "INDUSTRY_2050_SUMMARY_*_OTHER_USEFUL_HEAT_BANDS.csv biomass_source_band_*), agriculture -> low; the bands are served endogenously (industry_heat_band_technology_map); cap = "
            "potential (decision 115 0.98 withdrawn); replaces decision 36 (overflow -> fixed methane demand); biomass trade stays off (decision 36 trade part) with a cross-border biomass "
            "transport sensitivity at PyPSA-Eur biomass_transport costs; config research.s2.industry.biomass_overflow_mode = useful_heat (methane = historical rule for networks built "
            "before M08b)", "useful_heat_endogenous", "rule", "C",
            "PyPSA-Eur v2025.07.0 (biomass_spatial true, biomass_transport false, solid_biomass_import disabled - no overflow rule upstream)", "R4; s2_layers.add_demand_layer", f"plan:{sha256(S4R_PLAN)}; map:{sha256(TECH_MAP)}",
            decision_ref="126, 36, 115, 133, 137")
    for c in ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "TL", "VN"]:
        cor.supersede(f"industry_biomass_overflow_to_gas_{c}", "biomass_overflow_rule", "B2", "133", "decision-36 overflow -> methane rule removed")
    cor.supersede("s4m_decision_115_biomass_cap_share", "biomass_overflow_rule", "B2", "133", "0.98 cap share no longer needed; key removed from the main config")


# --- supplement 01 (decision 137): review decisions on the M08b report section 6 ---------------------------------------------------------
COST_DIR = ROOT / "research_inputs" / "cost_layers_v5"
LAYER_NOW, LAYER_PRE_M08A = COST_DIR / "technology_data_v0.15.0_EUR2020", COST_DIR / "technology_data_v0.15.0_EUR2020_ea20gdp"   # M08a A1: the ea20gdp files = the former main layer


def s3_3_param_id(tech: str, p: str) -> str:
    """param_id of a technology-data row in scripts_project/s3_3_ammonia_methanol_data.py."""
    return f"ammonia_methanol_td_{tech.replace(' ', '_').replace('(', '').replace(')', '').replace('.', '').lower()}_{p.replace(' ', '_').replace('-', '_')}"


def s01_cost_doc_rows(cor: Corrections) -> list[dict]:
    """Item 11 (M08a open item 9): registry rows that data scripts derived from the cost layer before M08a A1 (EA20 GDP-deflator rebase) still carry the
    old file SHA256; currency values are recomputed from the active layer (EEA HICP rebase), non-currency values must be unchanged; every such row
    gets the active file SHA256. Returns the change list."""
    raw_now, raw_old = pd.read_csv(LAYER_NOW / "costs_2050_EUR2020.csv"), pd.read_csv(LAYER_PRE_M08A / "costs_2050_EUR2020.csv")
    swap = {sha256(LAYER_PRE_M08A / f): (f, sha256(LAYER_NOW / f)) for f in ("costs_2050_EUR2020.csv", "costs_2050_EUR2020_prepared.csv")}
    first = lambda t: {s3_3_param_id(r.technology, r.parameter): (r.technology, r.parameter, float(r.value)) for r in t.drop_duplicates(["technology", "parameter"]).itertuples()}
    td_now, td_old = first(raw_now), first(raw_old)
    pipes = {"gas_pipeline_cost_onshore": "CH4 (g) pipeline", "gas_pipeline_cost_submarine": "CH4 (g) submarine pipeline"}
    val = lambda t, tech, p: float(t[(t.technology == tech) & (t.parameter == p)].value.iloc[0])
    out = []
    for pid, r in cor.base[cor.base.source_sha256.isin(list(swap))].sort_index().iterrows():
        fname, new_sha = swap[r.source_sha256]; old_v = r.value; changes = dict(source_sha256=new_sha)
        if pid in td_now:   # s3_3_ammonia_methanol_data.py rows
            tech, p, v_now = td_now[pid]
            if abs(float(old_v) - td_old[pid][2]) > 1e-9 * max(1.0, abs(td_old[pid][2])):
                raise ValueError(f"{pid}: registry value {old_v} is not the pre-M08a layer value {td_old[pid][2]}")
            changes["value"] = format(v_now, ".12g")
            note = f"重算：technology-data v0.15.0 {tech} {p} 取现行成本层（M08a A1 EEA HICP 回算）{format(td_old[pid][2], '.6g')} → {format(v_now, '.6g')}"
        elif pid in pipes:   # s3_1_gas_data.py: value typed from the layer file
            v_old, v_now = val(raw_old, pipes[pid], "investment"), val(raw_now, pipes[pid], "investment")
            if abs(float(old_v) - v_old) > 1e-9 * v_old:
                raise ValueError(f"{pid}: registry value {old_v} is not the pre-M08a layer value {v_old}")
            changes["value"] = format(v_now, ".12g")
            changes["description"] = r.description.replace(f"investment {v_old:.2f} EUR/MW/km", f"investment {v_now:.2f} EUR/MW/km")
            note = f"重算：{pipes[pid]} investment 取现行成本层（M08a A1 EEA HICP 回算）{v_old:.4f} → {v_now:.4f} EUR2020/MW/km（构建期价格一直取成本层，不受影响）"
        else:   # flags / methods that only cite the layer file
            note = "只更新来源文件 SHA256 为现行成本层（数值 / 标志不变）"
        if "value" in changes and changes["value"] == r.value:
            note = note.split("：")[0] + "：数值不变（非货币行），只更新来源文件 SHA256"
        cor.modify(pid, "S01-11", "137", note + f"；文件 {fname}", **changes)
        out.append(dict(param_id=pid, old_value=old_v, new_value=changes.get("value", old_v), old_sha256=r.source_sha256, new_sha256=new_sha))
    return out


def s01_items(reg: Registry, cor: Corrections):
    an = pd.read_csv(ANCHORS).set_index("country"); summ = pd.read_csv(SUMMARY).set_index("country")
    src = f"anchors:{sha256(ANCHORS)}; table:{sha256(ANCHOR_TABLE)}"
    sup = ROOT / "research/06_scope_redesign/p1_m08b_20261021/M08B_SUPPLEMENT_01.md"; sup_sha = sha256(sup) if sup.exists() else ""
    reg.add("industry_heat_hydrogen_not_represented", "Supplement 01 item A (decision 137): no hydrogen heating option in any useful-heat band - technology-data v0.15.0 has no "
            "hydrogen boiler / hydrogen direct-firing row (decision 133: only rows with an entry); same as PyPSA-Eur (no hydrogen boiler); LIMITATION and direction of the bias: "
            "hydrogen can still reach industrial heat indirectly as synthetic methane (methanation -> gas boilers / direct firing) with an extra conversion loss, so the role of "
            "hydrogen in industrial heat may be UNDERESTIMATED; an extra cost row without a source would break the data rule", "not_represented", "flag", "C",
            "technology-data v0.15.0 costs_2050; PyPSA-Eur v2025.07.0 (no H2 boiler)", "M08B_SUPPLEMENT_01.md section 1 item A", f"supplement:{sup_sha}", decision_ref="133, 137")
    tr_el = float(an.transport_elec_anchor_mwh.sum()) / 1e6
    reg.add("demand_transport_electricity_counted_once", "Supplement 01 item 8 (decision 137): the base load contains the 2050 transport electricity anchor (2019 rail / existing "
            f"electric road electricity x ATS transport growth; 11 countries {tr_el:,.2f} TWh); the transport fuel rows carry (transport anchor - that electricity anchor) and the "
            "land-transport EV / FCEV / ICE loads are derived only from the non-electricity land-transport rows (s2_layers.add_demand_layer, LAND_TRANSPORT_ACCOUNTS, carrier != "
            "electricity), so the transport service anchor does NOT contain the existing transport electricity; it is counted once (base load) and kept there "
            "(transport table total = anchor, checked per country)", "counted_once", "flag", "B", "M08b B1 tables", "DEMAND_ANCHOR_AEO8_ATS.csv transport_elec_anchor_mwh",
            src, decision_ref="134, 137")
    reg.add("demand_transport_carrier_efficiency_assumption", "Supplement 01 item 5 (decision 137): AEO8 prints no ATS carrier efficiencies by country, so the transport service "
            "conversion uses the demand-table carrier structure (land transport oil-equivalent) x the current PyPSA-Eur v2025.07.0 2050 shares and efficiencies (registry "
            "share_land_transport_* / share_transport_*_efficiency); kept, ASSUMPTION grade C (demand_transport_anchor_rule)", "table_structure_x_pypsa_eur_2050", "flag", "C",
            ATS_SRC + "; PyPSA-Eur v2025.07.0", "M08B_SUPPLEMENT_01.md section 1 item 5", f"supplement:{sup_sha}", decision_ref="134, 137")
    mech = {car: float(summ[f"other_mechanical_{car}_mwh"].sum()) / 1e6 for car in ("coal", "oil", "gas", "biomass")}
    reg.add("industry_other_bucket_mechanical_fuel", "Supplement 01 item 6 (decision 137): the diesel-motor part of the other-industry bucket (JRC-IDEES OIS 'Diesel motors', "
            f"construction / mining machinery) stays a fixed oil demand (11 countries {mech['oil']:,.1f} TWh oil, ID {float(summ.at['ID', 'other_mechanical_oil_mwh']) / 1e6:,.1f}); "
            "synthetic fuels, biofuels and DAC can offset its emissions; electrification of it has no sourced rule (unlike agricultural machinery); kept, ASSUMPTION grade C "
            "(flag row: no sourced range for a sensitivity)",
            "fixed_oil", "flag", "C", "JRC-IDEES-2021 OIS (m08b_heat_bands.py)", "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv other_mechanical_oil_mwh",
            f"summary:{sha256(SUMMARY)}", decision_ref="133, 137")
    reg.add("gate_b11_completeness_retired", "Supplement 01 item 9 (decision 137): the S1-era B11 completeness check (v5_gates.gate_b11_completeness: every S1 technology at every "
            "node) is retired for networks from S4A on: candidates are per resource site (geothermal / run-of-river only where a site exists), and the check failed identically on "
            "the S4M-3 and the M08b networks (287 items, M08b report section 3.3); replaced by the B11 supply-route check (v5_gates.gate_b11_supply_routes, >= 2 supply routes for "
            "every load-bearing terminal bus incl. the useful-heat bands), which s2_solve.py already runs as gate B11; s1_solve.py keeps the old check for S1 networks only",
            "retired", "flag", "B", "M08b report section 3.3; scripts/m08b_b11_old.py", "M08B_SUPPLEMENT_01.md section 1 item 9", f"supplement:{sup_sha}", decision_ref="137")
    reg.add("industry_heat_band_asean_distribution", "Supplement 01 item 12 (decision 137): the useful-heat temperature distribution of the other-industry bucket uses the EU27 "
            "JRC-IDEES-2021 OIS process split (industry_other_bucket_heat_band_shares); an ASEAN-specific temperature distribution is not available -> DATA_PENDING; alternative: "
            "calibrate the band shares to the industrial heat / electricity shares of the ERIA LCET-CN country chapters (RPR FY2024 No.12); EU27 kept (the M08b report listed this "
            "item as DATA_PENDING, the registry row is added here)", None, "fraction", "C", "ERIA (2024) LCET-CN country chapters (candidate)", "M08B_SUPPLEMENT_01.md section 1 item 12",
            f"supplement:{sup_sha}", decision_ref="133, 137", status="DATA_PENDING")
    reg.add("network_builder_script", "Supplement 01 item C (decision 137): the research networks are built by scripts_project/s2_network.py (build_scenario_s2; one build writes the "
            "2920x3h network and its exact daily-mean 365x24h network); scripts_project/build_research_network.py holds only the S1 static checks (REQUIRED_PER_NODE); the M08b "
            "instruction section 3.1 named build_research_network.py - corrected here and in the M08b report", "scripts_project/s2_network.py", "flag", "B", "repository code",
            "scripts_project/s2_network.py build_scenario_s2", f"supplement:{sup_sha}", decision_ref="137")
    changes = pd.DataFrame(s01_cost_doc_rows(cor))
    print("item 11 cost-layer documentation rows:"); print(changes.assign(old_sha256=changes.old_sha256.str[:12], new_sha256=changes.new_sha256.str[:12]).to_string(index=False))


def main(steps=("b1_demand", "b1_output", "b2_heat", "s01_items")):
    reg = Registry(SCRIPT); cor = Corrections()
    for s in steps:
        globals()[s](reg, cor)
    out = REG_DIR / "fragments"
    reg.write(out / "m08b.csv")
    rows = [cor.rows[k] for k in sorted(cor.rows)]
    write_csv(rows, out / "m08b_corrections.csv", COLUMNS)
    print(f"m08b.csv {len(reg.rows)} rows; m08b_corrections.csv {len(rows)} rows")


if __name__ == "__main__":
    main()
