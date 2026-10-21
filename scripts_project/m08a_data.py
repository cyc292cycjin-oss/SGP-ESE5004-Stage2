"""M08a (decisions 129-133): registry rows of the implementation step (no build, no solve).

    python scripts_project/m08a_data.py      # then python scripts_project/d1_registry.py

Writes research_inputs/registry_v5/fragments/m08a.csv (new rows) and fragments/m08a_corrections.csv (full-row
replacements of existing param_ids, applied by d1_registry.py after m080_corrections). A superseded row keeps its
value, gets status REFERENCE_ONLY and the description suffix " | [M08a] 历史：已被 <new id> 替代 ..."; the rows to
replace are taken from the assembly of all other fragments (+ the M08-0 corrections), never from an earlier M08a
output, so re-running gives the same files. One function per instruction task (A2 ...); rows of A1 are written by
scripts_project/s2_0_cost_layer_v015.py (the script that computes them).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from d1_common import COLUMNS, REG_DIR, ROOT, Registry, sha256, write_csv   # noqa: E402
from s2_costs import AEO8_PDF_SHA, D15_FILE, smr_ratios   # noqa: E402

SCRIPT = "scripts_project/m08a_data.py"
STEP = "M08a"
D15 = ROOT / D15_FILE


class Corrections:
    """Full-row replacements built from the registry assembled WITHOUT the M08a fragments (deterministic re-runs)."""

    def __init__(self):
        import d1_registry
        frames = [pd.read_csv(REG_DIR / "fragments" / f"{f}.csv", dtype=str, keep_default_na=False)
                  for f in d1_registry.FRAGMENTS if not f.startswith("m08a")]
        u = Registry("scripts_project/d1_registry.py"); d1_registry.unit_rows(u)
        frames.append(pd.DataFrame(u.rows, columns=COLUMNS))
        df = pd.concat(frames, ignore_index=True)[COLUMNS]
        for f in d1_registry.CORRECTIONS:
            if f.startswith("m08a"):
                continue
            corr = pd.read_csv(REG_DIR / "fragments" / f"{f}.csv", dtype=str, keep_default_na=False)[COLUMNS]
            df = pd.concat([df[~df.param_id.isin(corr.param_id)], corr], ignore_index=True)
        self.base = df.set_index("param_id")
        self.rows = {}

    def supersede(self, pid: str, by: str, step: str, note: str = "", status: str = "REFERENCE_ONLY", **changes):
        if pid in self.rows:
            raise ValueError(f"{pid} superseded twice")
        r = self.base.loc[pid].to_dict()
        r.update({k: ("" if v is None else str(v)) for k, v in changes.items()})
        r["description"] = f"{r['description']} | [{STEP} {step}] 历史：已被 {by} 替代" + (f" ({note})" if note else "")
        r["status"] = status
        refs = [x.strip() for x in str(r.get("decision_ref", "")).replace(";", ",").split(",") if x.strip()]
        r["decision_ref"] = ", ".join(refs + [x for x in ("131",) if x not in refs])
        r["param_id"] = pid
        self.rows[pid] = r

    def modify(self, pid: str, step: str, note: str, **changes):
        """In-place revision of an existing row (proposed action 'modify'): new values, description suffix ' | [M08a <step>] 修改：<note>'."""
        if pid in self.rows:
            raise ValueError(f"{pid} corrected twice")
        r = self.base.loc[pid].to_dict()
        r.update({k: ("" if v is None else str(v)) for k, v in changes.items()})
        r["description"] = f"{r['description']} | [{STEP} {step}] 修改：{note}"
        refs = [x.strip() for x in str(r.get("decision_ref", "")).replace(";", ",").split(",") if x.strip()]
        r["decision_ref"] = ", ".join(refs + [x for x in ("131",) if x not in refs])
        r["param_id"] = pid
        r["derivation_script"] = SCRIPT
        self.rows[pid] = r

    def has(self, pid: str) -> bool:
        return pid in self.base.index

    def value(self, pid: str) -> str:
        return self.base.loc[pid, "value"]


# --- A2 (M08-2, decision 131): nuclear from one source; AEO8 price-year factor -----------------------------------
def a2(reg: Registry, cor: Corrections):
    q = smr_ratios(D15)
    src_d15 = f"AEO8 pdf:{AEO8_PDF_SHA}; D15:{sha256(D15)}"
    reg.add("nuclear_cost_rule", "R6.3 / M08-2 (decision 131): one source for large PWR and SMR = technology-data v0.15.0 'nuclear' (EUR2020 main layer, PyPSA-Eur practice); "
            "SMR = nuclear x AEO8 Table D.15 same-table ratios SMR / LWR: investment 9,600 / 9,000 = 1.0667, FOM share of investment (110.0 / 9,600) / (75.3 / 9,000) = 1.37, "
            "VOM 2.2 / 5.1 = 0.43; lifetime, efficiency, fuel (uranium) and discount rate = technology-data nuclear; ratios are currency-year neutral; INL/ATB 2024 "
            "(USD2022: SMR moderate 2050 4,000, large 3,750 USD/kW) is the registered sensitivity set; config research.cost_layer.smr_cost_source = td_nuclear_x_aeo8_ratio "
            "(main) | aeo8_author_rule_2050 (former: AEO8 D.15 SMR x ECB 2020 FX, registry smr_*)",
            "td_nuclear_x_aeo8_ratio", "rule", "C", "technology-data v0.15.0 nuclear (Lazard v16.0); AEO8 Table D.15 p.197; INL/RPT-24-77048 Rev.2 Table A-1",
            "scripts_project/s2_costs.py smr_rows; AEO8_Table_D15_Cost_Summary.csv rows Nuclear LWR / Nuclear SMR", src_d15, decision_ref="126, 46, 131")
    for k, v, d in [("investment", q["investment"], "investment SMR / LWR = 9,600 / 9,000 kUSD/MW"),
                    ("fom_share", q["fom_share"], "FOM share of investment SMR / LWR = (110.0 / 9,600) / (75.3 / 9,000); applied to the technology-data nuclear FOM in %/a"),
                    ("vom", q["vom"], "VOM SMR / LWR = 2.2 / 5.1 USD/MWh; applied to the technology-data nuclear VOM")]:
        reg.add(f"smr_ratio_aeo8_{k}", f"M08-2 (decision 131): AEO8 Table D.15 same-table ratio for the SMR rule nuclear_cost_rule - {d}", v, "ratio", "B",
                "ACE AEO8 (2024) Appendix D Table D.15 p.197", "AEO8_Table_D15_Cost_Summary.csv", src_d15, decision_ref="131", sensitivity_low=None, sensitivity_high=None)
    reg.add("aeo8_cost_price_year", "R6.2 / M08-2 (decision 131): the AEO8 Table D.15 price year is not stated (Appendix D.3 p.195) -> DATA_PENDING; treatment = sensitivity factor "
            "research.cost_layer.aeo8_price_year_factor in [0.86, 1.00] on the AEO8 EUR2020 values (main 1.0; 0.86 = USD2023 -> USD2020 by FRED A191RD3A086NBEA 0.887 rounded "
            "down for USD2022-23); applied to the geothermal new-build investment (and to the SMR investment / VOM only under the former smr_cost_source aeo8_author_rule_2050; "
            "the main SMR rule uses currency-neutral ratios)", "DATA_PENDING", "year", "C", "ACE AEO8 (2024) Appendix D.3 p.195", "Appendix D", src_d15,
            decision_ref="126, 131", status="DATA_PENDING")
    reg.add("aeo8_price_year_factor_main", "M08-2 (decision 131): research.cost_layer.aeo8_price_year_factor main value 1.0 (AEO8 values used as EUR2020 after ECB 2020 FX); "
            "sensitivity 0.86 (registry aeo8_cost_price_year)", 1.0, "factor", "C", "configs/research/baseline.yaml research.cost_layer.aeo8_price_year_factor",
            "aeo8_price_year_factor", sha256(ROOT / "configs/research/baseline.yaml"), decision_ref="131", sensitivity_low=0.86, sensitivity_high=1.0)
    for pid in ("smr_investment", "smr_FOM", "smr_VOM"):
        cor.supersede(pid, "nuclear_cost_rule", "A2", "kept for the former option smr_cost_source = aeo8_author_rule_2050")


# --- A3 (decision 131): existing stock on technology-data v0.15.0 by commissioning year ----------------------------
def a3(reg: Registry, cor: Corrections):
    import json
    ev = ROOT / "research/06_scope_redesign/p1_m08a_20261021/evidence/M08A_A3_EXISTING_VINTAGE.json"
    e = json.loads(ev.read_text()) if ev.exists() else None
    td = ROOT / "research_inputs/cost_layers_v5/sources/technology_data_v0.15.0/SOURCES_SHA256.txt"
    src = f"technology-data v0.15.0 outputs/costs_<year>.csv (tarball c4787c1d; {td.name}:{sha256(td)})"
    reg.add("existing_fleet_cost_rule", "M08-0 supplement 01 section 4 / M08a A3 (decision 131): existing assets (frozen electric base, GEM additions) priced and parameterised with "
            "technology-data v0.15.0 of the matching commissioning year (outputs costs_2020 ... costs_2050, rebased to EUR2020 like the main layer - active rebase variant "
            "by_year tables): FOM = FOM % x investment (EUR2020/MW_el/a), VOM (EUR2020/MWh_el) and, for the fuel Links CCGT / OCGT / coal / lignite / oil, efficiency; components "
            "grouping units of different years: capacity-weighted FOM / VOM, efficiency = sum MW_el / sum(MW_el / eff) (keeps the fuel-input capacity); hydro / ror / PHS / VRE "
            "efficiencies and profiles unchanged; geothermal keeps AEO8 D.15 (no technology-data investment / VOM); replaces the author technology-data v0.13.2 table "
            "(costs year 2030) of the frozen base and the 2050 table of the GEM additions; config research.fleet.existing_cost_basis = td_v0_15_0_by_commissioning_year "
            "(main) | author_v0_13_2 (former); implementation scripts_project/m08a_layers.apply_existing_vintage_costs",
            "td_v0_15_0_by_commissioning_year", "rule", "C", src, "scripts_project/m08a_layers.py; configs/research/baseline.yaml research.fleet", sha256(td), decision_ref="131")
    reg.add("existing_fleet_cost_year_rule", "M08a A3 (decision 131): commissioning year -> technology-data output year = nearest multiple of 5 (whole years cannot tie), "
            "clipped to [2020, 2050]; units commissioned before 2020 use costs_2020 (no earlier table in v0.15.0); 2021-2022 -> 2020, 2023-2027 -> 2025, 2028-2032 -> 2030 ... "
            "(project rule, grade C: the release has 5-year tables only)", "nearest_5y_2020_2050", "rule", "C", src, "scripts_project/m08a_layers.vintage_year", sha256(td), decision_ref="131")
    reg.add("existing_fleet_geothermal_exception", "M08a A3 (decision 131): existing geothermal keeps the AEO8 Table D.15 'Geothermal average' FOM / VOM of decision 52 (technology-data "
            "v0.15.0 geothermal has no investment and no VOM rows); listed in m08a_layers.VINTAGE_EXCEPTIONS", "aeo8_d15", "rule", "C", "AEO8 Table D.15; technology-data v0.15.0 costs_2050",
            "scripts_project/m08a_layers.py VINTAGE_EXCEPTIONS", sha256(td), decision_ref="52, 131")
    if e:
        cc = e["by_scenario"]["integrated"]["by_carrier"]["CCGT existing"]
        evs = sha256(ev)
        reg.add("existing_fleet_ccgt_efficiency_check", f"M08a A3 check on the S4M-3 built networks (rule applied in memory, networks unchanged): existing CCGT efficiencies after the rule "
                f"{cc['efficiency_after_values']} (technology-data v0.15.0 costs_2020 0.56, costs_2025 0.57, costs_2030 0.58; expected 0.56 / 0.57), capacity-weighted "
                f"{cc['efficiency_after_mw_weighted']:.4f} (before {cc['efficiency_before_mw_weighted']:.4f}: frozen base 0.57 author v0.13.2, GEM additions 0.60)",
                round(cc["efficiency_after_mw_weighted"], 6), "p.u.", "B", "M08A_A3_EXISTING_VINTAGE.json", "by_scenario.integrated.by_carrier['CCGT existing']", evs, decision_ref="131")
        fi, fd = e["by_scenario"]["integrated"]["fom_after_eur"], e["by_scenario"]["disconnected"]["fom_after_eur"]
        reg.add("existing_fleet_fom_after_rule", f"M08a A3 check: existing annual fixed O&M after the rule = {fi / 1e9:.4f} bn EUR2020/a in the integrated and {fd / 1e9:.4f} in the disconnected "
                f"S4M-3 network (identical: the rule has no scenario input); before {e['by_scenario']['integrated']['fom_before_eur'] / 1e9:.4f} bn (author v0.13.2 + 2050 table)",
                fi, "EUR2020/a", "B", "M08A_A3_EXISTING_VINTAGE.json", "by_scenario.*.fom_after_eur", evs, decision_ref="131")
    cor.supersede("existing_fleet_cost_source_unification", "existing_fleet_cost_rule", "A3", "unification done in M08a A3")


# --- A4 (M08-3, decision 131): LNG uncapped at a sourced capex, regasification adder ---------------------------------
USD2024_TO_EUR2020 = 0.73606   # registry: FRED A191RD3A086NBEA 2020/2024 x ECB 2020 FX (fuel prices, S4C-0)
MWH_PER_MMBTU = 0.29307107


def a4(reg: Registry, cor: Corrections):
    cfg_sha = sha256(ROOT / "configs/research/baseline.yaml")
    lng_tab = ROOT / "research_inputs/lng_terminals_v5/LNG_IMPORT_TERMINALS_GEM_2025.csv"
    reg.add("lng_terminal_capacity_source", "R3.1 / M08-3 (decision 131): LNG receiving capacity source = GEM GGIT LNG Terminals (September 2025 release; import terminals; operating / "
            "construction = existing lower bound, proposed = candidate sites); GIIGNL 2026 cross-check; Mtpa -> MW = x 13.3333 MWh/t / 8,760 h = 1,522.1 MW per Mtpa; table unchanged "
            "(research_inputs/lng_terminals_v5/LNG_IMPORT_TERMINALS_GEM_2025.csv, registry lng_gem_ggit_release_verified)", "gem_ggit_2025_09", "flag", "B",
            "GEM GGIT LNG Terminals 2025-09; GIIGNL Annual Report 2026", "LNG_CAPACITY_COMPARISON.csv (S4R)", sha256(lng_tab), decision_ref="126, 131")
    reg.add("lng_terminal_cap_rule", "R3.3 / M08-3 (decision 131): option (a) - no capacity cap on LNG terminals: research.s3.gas.lng_expansion = capex_only, p_nom_max = inf at every "
            "terminal node incl. proposed-only sites, expansion priced at lng_terminal_expansion_capex_main (proposed value label 'uncapped_at_capex'); option (b) GEM project cap "
            "(operating + construction + proposed) not implemented; option (c) 2.5 x existing = lng_expansion cap_factor_cost (former main, decision 72) kept as sensitivity; "
            "the liquid-H2 terminal cap keeps the S3-2 rule (2.5 x existing LNG or proposed capacity)", "capex_only", "rule", "C", "S4R_PLAN.md R3.3",
            "configs/research/baseline.yaml research.s3.gas.lng_expansion; scripts_project/s3_layers.py add_gas_network", cfg_sha, decision_ref="126, 17, 72, 131")
    reg.add("h2_terminal_capex_rule", "M08-3 (decision 131): liquid-H2 import terminal annuity = LNG terminal expansion cost x 1.2 (PyPSA-Eur import branch 5a87cedd lines 4560-4563 "
            "relation kept) = 8,020.43 x 1.2 = 9,624.52 EUR2020/MW/a; follows the LNG cost sensitivity; config research.s3.imports.h2_terminal_capital_cost_rule = lng_x_factor "
            "(former fixed 8,421.6 = 7,018 x 1.2)", 8020.43343542 * 1.2, "EUR2020/MW/a", "C", "PyPSA-Eur import branch 5a87cedd prepare_sector_network.py lines 4560-4563; Ulvestad & Overland (2012)",
            "scripts_project/s3_layers.h2_terminal_capex", cfg_sha, decision_ref="131", sensitivity_low=8020.43343542 * 1.2 * 0.5, sensitivity_high=8020.43343542 * 1.2 * 1.5)
    ul = cor.base.loc["lng_regas_capex_ref_ulvestad_overland_2012"]
    cor.modify("lng_terminal_expansion_capex_main", "A4", "main value 7,018 -> 8,020.43 EUR2020/MW/a (Ulvestad & Overland 2012 converted, price year 2011 assumed; the 7,018 of the "
               "PyPSA-Eur import branch has no source and no price year, DATA_PENDING); +-50 % sensitivity; config research.s3.gas.lng_expansion_capital_cost_eur_per_mw_a",
               value="8020.43343542", unit="EUR2020/MW/a", tier="C", source="Ulvestad & Overland (2012) via registry lng_regas_capex_ref_ulvestad_overland_2012", source_locator="R3.2",
               source_sha256=ul.source_sha256, sensitivity_low="4010.21671771", sensitivity_high="12030.6501531", status="REGISTERED")
    lo, mid, hi = (u * USD2024_TO_EUR2020 / MWH_PER_MMBTU for u in (0.3, 0.5, 1.3))
    cor.modify("fuel_price_lng_regasification_adder", "A4", f"value set: 0.5 USD2024/MMBtu x {USD2024_TO_EUR2020} / {MWH_PER_MMBTU} MWh per MMBtu = {mid:.4f} -> 1.26 EUR2020/MWh "
               "(observed 0.3-1.3 USD/MMBtu: Japan ~0.5, India 0.75, Gate 0.35, China 0.7-1.3; Argus 2024, Hoegh / IGU 2017; a Southeast-Asia-specific IEA / IGU / OIES value stays "
               "DATA_PENDING); added to the LNG import marginal cost (config research.s3.gas.lng_regasification_adder_eur_per_mwh)", value="1.26", unit="EUR2020/MWh", tier="C",
               source="Argus Media 2024-09-13; Hoegh LNG / IGU 2017 (secondary)", source_locator="R3.4", source_sha256=cfg_sha,
               sensitivity_low=f"{lo:.6g}", sensitivity_high=f"{hi:.6g}", status="REGISTERED")
    cor.supersede("fuel_price_regasification_adder_s4c", "fuel_price_lng_regasification_adder", "A4", "adder 1.26 EUR2020/MWh in use since M08a",
                  source_sha256=(cor.base.loc["fuel_price_regasification_adder_s4c", "source_sha256"] or cfg_sha))
    for pid in ["lng_terminal_expansion_mode_s4b", "lng_import_cap_rule_built", "lng_import_cap_factor"] + \
               [f"lng_import_cap_built_{c}" for c in ("BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "TL", "VN")]:
        if cor.has(pid):
            cor.supersede(pid, "lng_terminal_cap_rule", "A4", "the 2.5 x cap is the option (c) sensitivity lng_expansion = cap_factor_cost")


# --- A5 (M08-4, decision 131): CO2 storage unified to ERIA-GCCSI 2024 P50 -------------------------------------------------
CO2_TABLE = ROOT / "research_inputs/co2_v5/CO2_STORAGE_POTENTIAL_UNIFIED.csv"
S4R_CO2 = ROOT / "research/06_scope_redesign/p1_step4r_20261020/CO2_STORAGE_UNIFIED.csv"
ERIA_SRC = "ERIA / GCCSI (2024) Comprehensive CCUS Research Report, Ch.1"
STORAGE_YEARS = 50.0


def co2_table(cor: Corrections) -> pd.DataFrame:
    """11-country table: BN / ID / MY / TH keep the registered ERIA component sums (source unchanged); VN, PH, KH, TL, LA, MM per the S4R unification."""
    s = pd.read_csv(S4R_CO2).set_index("country")
    rows = []
    for c in sorted(s.index):
        r = s.loc[c]
        if c in ("BN", "ID", "MY", "TH"):
            p = float(cor.value(f"co2_storage_potential_{c}"))   # ERIA P50 saline + net hydrocarbon (registered components)
            lo, hi = p - r.eria_saline_p50_gt + r.eria_saline_p90_gt, p - r.eria_saline_p50_gt + r.eria_saline_p10_gt
            st, loc, note = "ERIA_2024_P50", r.eria_locator, "registered ERIA component sum (unchanged); low / high = ERIA saline P90 / P10 + net hydrocarbon"
        elif c == "VN":
            p, lo, hi = float(r.unified_potential_gt), float(r.unified_low_gt), float(r.unified_high_gt)
            st, loc, note = "ERIA_2024_P50", r.eria_locator, "saline P50 5 [P90 3, P10 9] Gt + hydrocarbon 0.3034 Gt; replaces IEA 2021 11.8 Gt"
        elif c == "PH":
            p = lo = hi = float(r.unified_potential_gt)
            st, loc, note = "ERIA_2024_HYDROCARBON_ONLY", r.eria_locator, "no saline data in ERIA; Malampaya 67.2 Mt; replaces IEA 2021 22.3 Gt"
        elif c == "KH":
            p, lo, hi = 0.09, 0.09, 45.0
            st, loc, note = "IJGGC_2014_LOW_CASE", "doi:10.1016/j.ijggc.2014.08.016", "ERIA: not covered; low case 90 Mt structural traps (main, grade C); 45 Gt hydrodynamic high case as sensitivity; replaces OGCI 0.085 Gt"
        elif c == "TL":
            p, lo, hi = 0.0, 0.0, 0.0
            st, loc, note = "UNASSESSED_NO_NATIONAL_ASSESSMENT", "R5", "no national assessment; OGCI 0.25 Gt not re-checkable -> 0; Bayu-Undan CCS ~10 Mtpa (Santos / IFC) is a project-based annual-cap sensitivity, not represented"
        elif c in ("LA", "MM"):
            p, lo, hi = 0.0, 0.0, 0.0
            st, loc, note = "UNASSESSED", "section 1.3.9 p.56", "ERIA: unknown, no analysis completed -> 0 (not SOURCE_ZERO)"
        else:   # SG
            p, lo, hi = 0.0, 0.0, 0.0
            st, loc, note = "SOURCE_ZERO", "section 1.3.8 p.56", "ERIA: no storage potential"
        rows.append(dict(country=c, potential_gt=round(p, 10), low_gt=round(lo, 10), high_gt=round(hi, 10), annual_cap_mt_at_50y=round(p * 1e3 / STORAGE_YEARS, 6), status=st,
                         source=(ERIA_SRC if st.startswith("ERIA") else ("Int. J. Greenhouse Gas Control (2014)" if c == "KH" else ERIA_SRC)), locator=loc, note=note))
    return pd.DataFrame(rows)


def a5(reg: Registry, cor: Corrections):
    t = co2_table(cor)
    CO2_TABLE.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(CO2_TABLE, index=False, float_format="%.10g")
    tsha = sha256(CO2_TABLE)
    reg.add("co2_storage_unified_table", "R5 / M08-4 (decision 131): national CO2 storage potentials unified to ERIA-GCCSI 2024 P50 (VN 5.30, PH 0.067, MY 128.8, ID 51.3, BN 18.6, "
            "TH 16.0 Gt; KH 0.09 Gt IJGGC 2014 low case, grade C; TL / LA / MM 0 with LA / MM UNASSESSED; SG 0); annual injection cap = potential / research.s2.co2.storage_years (50); "
            "config research.s2.co2.storage_potential_source = eria_gccsi_2024_unified (main) | registry_d1 (former co2_injection_cap_*), storage_potential_case p50 | low (ERIA P90) | "
            "high (ERIA P10); build scripts_project/s2_layers.co2_storage_caps", str(CO2_TABLE.relative_to(ROOT)), "file", "B", f"{ERIA_SRC}; IJGGC (2014)",
            "CO2_STORAGE_POTENTIAL_UNIFIED.csv; S4R CO2_STORAGE_UNIFIED.csv", tsha, decision_ref="126, 89, 131")
    reg.add("co2_storage_potential_case_main", "M08-4 (decision 131): research.s2.co2.storage_potential_case main = p50 (ERIA P50); low = ERIA P90 + net hydrocarbon, high = ERIA P10 "
            "(KH 45 Gt hydrodynamic case) as sensitivities", "p50", "flag", "B", ERIA_SRC, "storage_potential_case", tsha, decision_ref="131")
    for r in t.itertuples():
        reg.add(f"co2_injection_cap_unified_{r.country}", f"M08-4 (decision 131): annual CO2 injection cap {r.country} = unified potential {r.potential_gt:g} Gt / 50 years "
                f"(status {r.status}); used by the build via the table (storage_years from the config)", r.potential_gt * 1e9 / STORAGE_YEARS, "tCO2/a",
                "B" if r.country not in ("KH", "TL") else "C", f"{ERIA_SRC}" if r.country != "KH" else "IJGGC (2014)", "CO2_STORAGE_POTENTIAL_UNIFIED.csv", tsha,
                country=r.country, decision_ref="28, 29, 30, 131", sensitivity_low=(r.low_gt * 1e9 / STORAGE_YEARS if r.country in ("KH", "TL") else None),
                sensitivity_high=(r.high_gt * 1e9 / STORAGE_YEARS if r.country in ("KH", "TL") else None))
        cor.supersede(f"co2_injection_cap_{r.country}", f"co2_injection_cap_unified_{r.country}", "A5", "D1 potential / 50; read only by storage_potential_source registry_d1")
    tt = t.set_index("country")
    mods = {"VN": ("B", "ERIA / GCCSI 2024 P50 (saline 5 [3-9] Gt Tables 1.17 / 1.15 p.47 + hydrocarbon 0.303 Gt); replaces IEA 2021 11.8 Gt (ADB 2013 theoretical)"),
            "PH": ("B", "ERIA / GCCSI 2024 (no saline data; Malampaya 67.2 Mt Table 1.18 p.53); replaces IEA 2021 22.3 Gt (ADB 2013 theoretical)"),
            "KH": ("C", "conservative rule = low case 90 Mt (structural traps) of the IJGGC 2014 preliminary assessment (45 Gt hydrodynamic high case = sensitivity); replaces OGCI 0.085 Gt (not re-checkable)"),
            "TL": ("C", "no national assessment; OGCI 0.25 Gt not re-checkable -> 0 (UNASSESSED); Bayu-Undan CCS 10 Mtpa (Santos / IFC) = project-based annual-cap sensitivity, not represented")}
    for c, (tier, note) in mods.items():
        cor.modify(f"co2_storage_potential_{c}", "A5", note, value=f"{tt.at[c, 'potential_gt']:.10g}", tier=tier, sensitivity_low=f"{tt.at[c, 'low_gt']:.10g}",
                   sensitivity_high=f"{tt.at[c, 'high_gt']:.10g}", status="REGISTERED", source=(ERIA_SRC if c in ("VN", "PH") else cor.base.loc[f"co2_storage_potential_{c}", "source"]),
                   source_sha256=(cor.base.loc[f"co2_storage_potential_{c}", "source_sha256"] or tsha))
    for c in ("LA", "MM"):
        cor.modify(f"co2_storage_potential_unassessed_{c}", "A5", "ERIA 2024 section 1.3.9 p.56: unknown, no analysis completed -> 0, UNASSESSED (not SOURCE_ZERO)",
                   value="0", tier="A", status="REGISTERED", source=ERIA_SRC, source_locator="section 1.3.9 p.56",
                   source_sha256=(cor.base.loc[f"co2_storage_potential_unassessed_{c}", "source_sha256"] or tsha))
        cor.modify(f"co2_storage_potential_{c}", "A5", "status SOURCE_ZERO -> REGISTERED 0 with the UNASSESSED label (ERIA: unknown, not a source zero; co2_storage_potential_unassessed_" + c + ")",
                   status="REGISTERED", source_sha256=(cor.base.loc[f"co2_storage_potential_{c}", "source_sha256"] or tsha))


# --- A7 (M08-8 extension, decisions 132, 133): scenario / coalition / finance switches -------------------------------------
WACC_TABLE = ROOT / "research_inputs/finance_v5/COUNTRY_WACC_REAL_M08A.csv"
S4R_WACC = ROOT / "research/06_scope_redesign/p1_step4r_20261020/COUNTRY_WACC_SENSITIVITY_TABLE.csv"


def wacc_table() -> pd.DataFrame:
    s = pd.read_csv(S4R_WACC).set_index("country")
    rows = []
    for c in sorted(s.index):
        r = s.loc[c]
        if pd.notna(r.real_wacc_mid):
            rows.append(dict(country=c, technology="model (real WACC, all new-build technologies of the country)", wacc_real=round(float(r.real_wacc_mid), 4), status="REGISTERED",
                             tier="C", method=f"S4R one method: {r.method}; real = (1 + nominal) / (1 + IMF WEO Oct 2026 CPI 2028-2030) - 1",
                             source="IEA Cost of Capital Observatory 2025; Damodaran 2026-01; IMF WEO Oct 2026 (S4R COUNTRY_WACC_SENSITIVITY_TABLE.csv real_wacc_mid)"))
    tl = round(sum(x["wacc_real"] for x in rows if x["country"] in ("KH", "LA", "MM")) / 3, 6)
    rows.append(dict(country="TL", technology="model (real WACC, all new-build technologies of the country)", wacc_real=tl, status="REGISTERED", tier="C",
                     method="rule (decision 133): no IEA entry and no Damodaran CRP for TL -> mean of KH / LA / MM real WACC (registry wacc_country_tl_rule)",
                     source="derived from the KH / LA / MM rows of this table"))
    return pd.DataFrame(sorted(rows, key=lambda x: x["country"]))


def a7(reg: Registry, cor: Corrections):
    t = wacc_table()
    WACC_TABLE.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(WACC_TABLE, index=False)
    wsha, ssha = sha256(WACC_TABLE), sha256(S4R_WACC)
    cfg_sha = sha256(ROOT / "configs/research/baseline.yaml")
    var_sha = sha256(ROOT / "scripts_project/m08a_variants.py")
    tl = float(t.set_index("country").at["TL", "wacc_real"])
    reg.add("wacc_country_real_table", "R6.6 / F7 / M08a A7 (decision 133): real WACC by country, one method (IEA observatory 2024 solar midpoint or MY reference + Damodaran CRP difference; "
            "deflated with IMF WEO Oct 2026 CPI 2028-2030 average) - research_inputs/finance_v5/COUNTRY_WACC_REAL_M08A.csv (S4R real_wacc_mid; TL by rule); used only by the "
            "finance.wacc_mode country_specific variant", str(WACC_TABLE.relative_to(ROOT)), "file", "C", "IEA Cost of Capital Observatory 2025; Damodaran 2026-01; IMF WEO Oct 2026",
            "COUNTRY_WACC_SENSITIVITY_TABLE.csv", wsha, decision_ref="126, 90, 111, 133")
    reg.add("wacc_country_tl_rule", f"M08a A7 (decision 133): Timor-Leste has no IEA observatory entry and no Damodaran country risk premium -> real WACC = mean of KH / LA / MM = {tl:.4f} "
            "(grade C rule, same family of frontier economies; sensitivity = the KH / MM values)", tl, "real rate", "C", "derived (KH 0.0905, LA 0.0764, MM 0.1102)",
            "COUNTRY_WACC_REAL_M08A.csv row TL", wsha, country="TL", decision_ref="133", sensitivity_low=0.0764, sensitivity_high=0.1102)
    reg.add("wacc_distributed_rule", "M08a A7 (decision 133): distributed technologies in finance.wacc_mode country_specific = cost rows whose technology-data discount rate is below the "
            "uniform 0.07 (0.04: solar-rooftop and decentral rows) keep that household rate (research.finance.distributed_wacc_rule technology_data_fixed). Reason: technology-data / "
            "PyPSA-Eur keep a separate decentral rate that does not derive from the system rate, and the IEA observatory WACC behind the country table covers utility-scale projects "
            "(no country household rate source); sensitivity proportional = r_country x 0.04 / 0.07", "technology_data_fixed", "rule", "C",
            "technology-data v0.15.0 costs (discount rate 0.04 rows); PyPSA-Eur prepare_costs", "configs/research/baseline.yaml research.finance.distributed_wacc_rule", cfg_sha, decision_ref="133")
    reg.add("wacc_cross_border_rule", "M08a A7 (decision 133): assets spanning two countries (cross-border lines / links) are re-annualised with the mean real WACC of the two end countries; "
            "Lines included (AC capital cost row HVAC overhead); existing stock (capital cost 0) unaffected", "mean_of_end_countries", "rule", "C", "project rule",
            "scripts_project/s4c_layers.apply_wacc_mode", cfg_sha, decision_ref="133")
    reg.add("disconnected_definition_main", "R7 / F11 / M08a A7 (decision 132): disconnected = all ASEAN-internal cross-border fixed networks removed, INCLUDING the 2025 stock (corridor "
            "table: 24 electricity edges with 2025 capacity; in the built network after S4F-2 / S4H-1 corrections 16 AC lines + 1 DC link Khlong Ngae - Gurun 300 MW, i.e. 62 cross-border "
            "lines and 292 cross-border links removed in total (S4M-3 integrated network, M08A_A7_VARIANTS.json); gas pipelines ID-SG 8,795 (2 pipelines), MM-TH 13,845 (3), MY-TH "
            "11,244 MW (TTM)); regional liquid pools (oil, oil non-fossil, methanol, ammonia), CO2 shipping and every extra-ASEAN import kept identical in both scenarios; config "
            "research.cross_border.stock_mode = remove_all (s2_network.py disconnected build)", "remove_all", "flag", "B",
            "configs/research/disconnected.yaml; S4P section 4.1 network diff", "R7", cfg_sha, decision_ref="126, 8, 18, 132")
    reg.add("disconnected_definition_sensitivity", "R7 / M08a A7 (decision 132): sensitivity 'keep 2025 stock, no new build' - cross_border.stock_mode = keep_stock_no_new, derived from the "
            "INTEGRATED base by scripts_project/m08a_variants.py: AC lines with s_nom_min > 0, electricity links with p_nom_min > 0 and existing gas pipelines (with their lossy-split "
            "reversed twins) pinned at the 2025 capacity (nominal = min = max; extendable flag kept so the objective treats the stock as in the base); all other cross-border lines / "
            "links removed; pools / shipping / extra-ASEAN unchanged; existing cross-border FOM constant kept", "keep_stock_no_new", "flag", "C", "R7",
            "scripts_project/m08a_layers.apply_stock_mode", var_sha, decision_ref="126, 132")
    reg.add("scenario_switch_co2_shipping_intra_asean", "M08a A7 b1 (decision 132): disconnected.co2_shipping_intra_asean = allow (main: intra-ASEAN CO2 shipping kept in the disconnected "
            "scenario, maritime trade, decision 92) | forbid (variant of a disconnected network: links CO2 ship, CO2 transit ship and CO2 transit rail into another ASEAN country's "
            "national store removed - b1 = no cross-border CO2 transport inside ASEAN when not interconnected, incl. the Lao rail leg into the VN / TH store (scope confirmed by the "
            "user 2026-10-21, M08a supplement 01 item 2); CO2 export extra-ASEAN and CO2 transit export extra-ASEAN kept - the landlocked LA keeps only its transit corridor to "
            "extra-ASEAN storage, rule disconnected_b1_landlocked_transit_rule; every country must keep a permanent sink, checked by the variant script)", "allow", "flag", "C",
            "M08A instruction A7 item 2; M08A_SUPPLEMENT_01.md items 1.2 and 2", "scripts_project/m08a_layers.apply_co2_shipping", var_sha, decision_ref="92, 132")
    reg.add("scenario_switch_remove_countries", "M08a A7 (decision 132): coalition.remove_countries = [] (main) | list of ISO2 - the countries leave the network ENTIRELY: buses, loads, "
            "generators, storage and gas stores, storage potential, existing stock, every line / link with a port on their buses (their half of the cross-border lines, liquid-pool and "
            "CO2-shipping access, extra-ASEAN import points located there) and components tagged with the country (its loads on the regional buses); international bunker demand "
            "(regional, no country) kept; solve hooks iterate n.meta research_countries; NOT the decision-91 cross_border.coalition switch (that keeps the country in the pools)",
            "[]", "flag", "C", "M08A instruction A7 item 3", "scripts_project/m08a_layers.apply_remove_countries", var_sha, decision_ref="91, 132")
    reg.add("scenario_switch_wacc_mode", "M08a A7 (decision 133): finance.wacc_mode = uniform (main: 0.07, distributed technologies 0.04) | country_specific (variant of a built base: "
            "new-build capital costs re-annualised with the real WACC of the asset's country, wacc_country_real_table; TL rule, distributed rule, cross-border rule)", "uniform", "flag", "C",
            "M08A instruction A7 item 4", "scripts_project/s4c_layers.apply_wacc_mode via m08a_variants.py", var_sha, decision_ref="90, 133")
    reg.add("scenario_variant_generation_rule", "M08a A7 (decisions 132, 133): every variant of the four switches is generated deterministically from a base network built by "
            "s2_network.py with the current config, by one script (scripts_project/m08a_variants.py; fixed order remove_countries -> stock_mode -> co2_shipping -> wacc); the receipt "
            "records input and output SHA256 so that the cloud can derive the variants from the uploaded base networks; the build refuses non-default variant keys",
            "m08a_variants.py", "rule", "B", "M08A instruction A7", "scripts_project/m08a_variants.py", var_sha, decision_ref="132, 133")


# --- A8 (M08-9, decisions 128, 133): GATES_V6 and the pre-registered run rules -----------------------------------------------
def a8(reg: Registry, cor: Corrections):
    gdef = ROOT / "research/06_scope_redesign/p1_step4r_20261020/GATES_V6.md"
    notes = ROOT / "research/06_scope_redesign/p1_step4r_20261020/GATES_V6_NOTES.md"
    g6 = ROOT / "scripts_project/v5/gates_v6.py"; runner = ROOT / "scripts_project/m08a_run_batch.sh"
    cfg_sha = sha256(ROOT / "configs/research/baseline.yaml")
    reg.add("gates_v6_contract", "R8 / decision 128 / M08a A8 (decision 133): GATES_V6.md (SHA256 5c0aa8b8...7f9, unchanged): criteria = C1 (a)(b)(c) + structural checks G2.1 network SHA256 "
            "(+ A4 read-back), G2.2 configuration-subset hash (written into the network meta at build: research_config_subset_sha256; compared with the current config + the network's "
            "overrides at solve time), G2.3 result completeness; all other gates diagnostics D0-D16 with absolute + relative budgets tied to FeasibilityTol / OptimalityTol / BarConvTol "
            "(dual budget 10 x max(OptimalityTol, BarConvTol)); labels ACCEPTED_LAYER2 / ACCEPTED_LAYER1 / NOT_ACCEPTED; implementation scripts_project/v5/gates_v6.py; "
            "config research.solver.acceptance = gates_v6", "see_file", "flag", "B", str(gdef.relative_to(ROOT)), "GATES_V6_SHA256.txt; scripts_project/v5/gates_v6.py",
            sha256(gdef), decision_ref="128, 133")
    reg.add("gates_v6_d2_budget_note", "R8 (S4R supplement 01 section 4): D2 dual budget multiplier k = 10 KEPT, GATES_V6.md unchanged; GATES_V6_NOTES.md records that barrier solutions "
            "without crossover carry a normalised dual-sign error of ~40-240 x BarConvTol on the 56x3h OPTIMAL runs (S4M-2 at 1e-8, S4Q at 1e-6) and ~1e-2 on every 365x24h solution "
            "regardless of BarConvTol (S4N pilot 8.6e-3, S4O-6 / L23 4e-2-3e-1); D2 is a diagnostic only, acceptance = G1 (C1) + G2; anomaly note when the D2 ratio exceeds 10 x the "
            "group history (gates_v6.D2_HISTORY_MAX); a k = 100 variant would need a V6.1 definition", 10, "dimensionless", "B", "GATES_V6_NOTES.md; GATES_RETRO_COMPARISON.csv",
            "GATES_V6_NOTES.md sections 2-4", sha256(notes), decision_ref="128, 129")
    reg.add("gates_v6_g22_subset_m08a_additions", "M08a A8 (decision 133): implementation of G2.2 = the literal GATES_V6 key list PLUS cost_layer (whole section: rebase_index, layer files, "
            "smr_cost_source, aeo8_price_year_factor - the list names cost_layer.active only), site_candidates and the new variant sections disconnected / coalition (decision 132), by "
            "the G2.2 purpose 'configuration subset that decides the network and the LP'; excluded as in GATES_V6: solver.profile, solver.profiles, solver.acceptance, solver.run_rules; "
            "GATES_V6.md unchanged - flagged for the user's confirmation", "cost_layer;site_candidates;disconnected;coalition", "list", "C", "scripts_project/v5/gates_v6.py SUBSET_KEYS_M08A_ADDITIONS",
            "gates_v6.py", sha256(g6), decision_ref="128, 132, 133")
    reg.add("run_rule_profile_chain", "M08a A8 (decision 133), registered BEFORE the third / fourth batches: formal-run profile chain - first the 365x24h level-2 runs (decision 127) of "
            "formal_barrier_1e6_t16 vs profile A (formal_barrier) in every level-2 scenario: if C1 (a)(b)(c) all pass AND |objective - profile A| / |profile A| <= 1e-5 the formal runs "
            "use formal_barrier_1e6_t16, otherwise profile A; the BarConvTol 1e-5 profile (pypsa_eur_default) is never a fallback (decision 121 evidence); research.solver.run_rules."
            "profile_chain; gates_v6.select_formal_profile; runner scripts_project/m08a_run_batch.sh (RUN_KIND level2 -> PROFILE_CHOICE.json)", "formal_barrier_1e6_t16_else_formal_barrier",
            "rule", "B", "M08A instruction A8 item 2", "configs/research/baseline.yaml research.solver.run_rules", cfg_sha, decision_ref="121, 123, 127, 133")
    reg.add("run_rule_formal_2920", "M08a A8 (decision 133), registered BEFORE the runs: acceptance by GATES_V6; a formal 2920x3h run must pass C1 (c) to be used for the allocation "
            "(the Owen allocation uses the duals; ACCEPTED_LAYER1 = total cost only); TimeLimit 48 h (172,800 s); a run that does not converge is graded by C1 as returned - no retry, "
            "no parameter change; the runner stops the batch at the first NOT_ACCEPTED run (user decision); gates_v6.formal_run_decision; scripts_project/m08a_run_batch.sh RUN_KIND formal",
            172800.0, "s", "B", "M08A instruction A8 item 2", "configs/research/baseline.yaml research.solver.run_rules", sha256(runner), decision_ref="119, 128, 133")


# --- A9 (M08-10, decisions 125 (4), 133): report currency ---------------------------------------------------------------
def a9(reg: Registry, cor: Corrections):
    cfg_sha = sha256(ROOT / "configs/research/baseline.yaml")
    fx_in = float(cor.value("fx_usd_to_eur_2020")); src = cor.base.loc["fx_usd_to_eur_2020"]
    reg.add("report_currency_rule", "R6.5 / decision 125 (4) / M08a A9 (decision 133) + M08a supplement 01 item 3 (one rate both ways): report currency USD2020 with ONE rate, "
            f"the inverse of the input conversion row: 1 EUR2020 = 1 / fx_usd_to_eur_2020 = 1 / {fx_in:.12g} = {1 / fx_in:.6f} USD2020 (config research.reporting.fx_per_eur2020 = "
            "inverse_of_input; s4d_ledger.report_currency computes it from the registry at export time), so a USD input converted to EUR2020 and reported back in USD2020 "
            "returns its own value (otherwise USD-sourced prices such as fuels would carry a spurious 0.2 % offset); source and method = those of fx_usd_to_eur_2020; the ECB 2020 "
            "annual average 1.1422 is a comparison value only (fx_report_ecb_2020_reference). The model, the LP and the ledger column 'eur' stay EUR2020; ledger exports add "
            "usd2020 / usd2020_length_split (COUNTRY_COST_LEDGER_DETAIL.csv) and COUNTRY_COST_LEDGER_USD2020.csv (s2_solve.py); USD2024 only as an extra line via FRED deflator 1.1918. "
            "Former A9 value (before supplement 01): 1.1422",
            1.0 / fx_in, "USD2020/EUR2020", "B", src["source"], f"1 / fx_usd_to_eur_2020 ({src['source_locator']}); configs/research/baseline.yaml research.reporting",
            src["source_sha256"], decision_ref="125, 126, 133")
    reg.add("fx_report_ecb_2020_reference", f"M08a A9 / supplement 01 item 3: ECB 2020 annual average euro reference rate 1 EUR = 1.1422 USD - COMPARISON VALUE ONLY (not used): "
            f"{1.1422 * fx_in - 1.0:+.3%} against the report rate 1 / fx_usd_to_eur_2020 = {1 / fx_in:.6f}; the input row is the currency_converter 0.18.9 mean over the 366 "
            "calendar days of 2020 (non-trading days carried forward), the ECB figure the mean over trading days. Supersedes the A9 note fx_report_vs_input_rate_note "
            "(the 0.2 % round-trip offset is removed by using one rate)",
            1.1422, "USD2020/EUR2020", "B", "ECB euro reference rates, 2020 annual average (USD 1.1422)", "ECB statistical data warehouse, EXR.A.USD.EUR.SP00.A 2020",
            cfg_sha, decision_ref="125, 133", status="REFERENCE_ONLY")


# --- A6.1 (M08-7, decisions 129, 131): PV density; open-forest trigger; offshore alpha ----------------------------------------
def a6(reg: Registry, cor: Corrections):
    cfg_sha = sha256(ROOT / "configs/research/baseline.yaml")
    pe = ROOT / "research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml"
    pe_sha = sha256(pe) if pe.exists() else cfg_sha
    reg.add("renewable_capacity_per_sqkm_solar", "R2 / M08a A6.1 (decisions 129, 131): solar capacity density aligned to PyPSA-Eur v2025.07.0 (config.default.yaml line 270) - replaces "
            "PyPSA-Earth 4.6; applied as p_nom_max x 5.1 / 4.6 = 1.1087 to every ground-mounted 'solar' candidate (11 countries, before the resource-class split; "
            "research.renewable.solar_density; s4a_layers.apply_solar_density); rooftop / existing PV unchanged; no raster recomputation", 5.1, "MW/km2", "B",
            "PyPSA-Eur v2025.07.0 config.default.yaml renewable.solar.capacity_per_sqkm", "line 270", pe_sha, decision_ref="126, 129, 131")
    reg.add("renewable_landuse_rule_solar", "R2 (S4R supplement 01, decisions 129, 131): MAIN RUN keeps the current solar land classes (Copernicus LC100 [20, 30, 40, 50, 60, 90, 100]; all "
            "forest [111-126], water [80] and protected areas (WDPA / natura) excluded) - same type as the PyPSA-Eur CORINE rule; only the capacity density changes (4.6 -> 5.1). Open "
            "forest [121-126] is an UPPER-BOUND SENSITIVITY (variant s4r_openforest, not implemented in M08a); the model / ESMAP Level-1 ratio 0.18-0.57 decomposes into ~6-18 % density "
            "and the rest basis differences (protected areas, forest and other criteria)", "copernicus_current_classes_main", "rule", "C",
            "ESMAP / Solargis (2020) Ch.2 p.12-13; Copernicus LC100 v3 legend; PyPSA-Eur v2025.07.0 renewable.solar.corine; World Bank WDI", "POTENTIAL_COMPARISON.csv (S4R)", cfg_sha,
            decision_ref="126, 129, 131")
    reg.add("renewable_openforest_sensitivity_trigger", "R2 (S4R supplement 01): after the corrected 365x24h main runs, if a country solar cap binds in either scenario (p_nom_opt >= 0.999 x "
            "p_nom_max) and shadow price x bound capacity >= 1 bn EUR2020/a, the open-forest variant s4r_openforest becomes a formal sensitivity run (both scenarios) in the third batch; "
            "otherwise binding status and shadow prices are recorded in an appendix; shadow prices from the in-run dual export (decision 118), no re-solve", "rule", "flag", "C",
            "IMPLEMENTATION_PLAN.md section 2.1", "section 2.1", cfg_sha, decision_ref="129")
    reg.add("offwind_alpha_calibration_rule", "F9 / R2.5 / M08a A6.3: offshore capacity-factor calibration alpha kept at 1.0 (no observed offshore CF source for the region: VN has only "
            "nearshore / intertidal projects, Bac Lieu / Tra Vinh; DATA_PENDING); S4B-3 onshore method (alpha on ERA5 100 m wind speed) to apply once a source exists; fallback = World "
            "Bank Vietnam offshore wind roadmap 2021 net CF assumptions (page DATA_PENDING)", "DATA_PENDING", "rule", "C", "S4B-3 method; WB Offshore Wind Roadmap for Vietnam 2021",
            "R2.5", cfg_sha, country="VN", decision_ref="126, 131", status="DATA_PENDING")
    cor.supersede("renewable_density_built_solar", "renewable_capacity_per_sqkm_solar", "A6.1", "as-built 4.6 MW/km2 of the electric base; the main run scales p_nom_max by 5.1 / 4.6")
    cor.supersede("renewable_landcover_codes_built_solar", "renewable_landuse_rule_solar", "A6.1", "same classes, now registered as the main-run rule with the open-forest sensitivity")


# --- A10 (decisions 126, 129-133): remaining proposed rows of this step ------------------------------------------------------
def a10(reg: Registry, cor: Corrections):
    cfg_sha = sha256(ROOT / "configs/research/baseline.yaml")
    reg.add("co2_sequestration_cost_price_year", "R5 / R6.4: 30 EUR/t is the PyPSA-Eur v2025.07.0 config constant sector.co2_sequestration_cost (research.s2.co2.sequestration_cost_eur_per_t); "
            "price year not stated -> DATA_PENDING, used as EUR2020; benchmarks GCCSI 2025 offshore US$5-31/t, ERIA 2022 US$12.9/t; +-50 % sensitivity unchanged",
            "DATA_PENDING", "year", "C", "PyPSA-Eur v2025.07.0 config.default.yaml line 711; GCCSI (2025-12) Cost of CO2 Storage p.2, 6; ERIA (2022) Vol. II Table 2.12 p.21",
            "R6.4", cfg_sha, decision_ref="126, 131", status="DATA_PENDING")
    reg.add("co2_storage_vn_shipping_interaction", "R5 x R7 (S4R supplement 01 section 5, INFERENCE): with the VN annual storage cap 236 -> 106 Mt/a (ERIA P50 / 50; M08a A5) about 130 Mt/a "
            "of the 365x24h VN sequestration has to re-route: intra-ASEAN shipping to MY (14.4-15.0 EUR2020/t chain + receiver storage 30) costs +14-15 EUR/t over own storage = "
            "+1.9-2.0 bn/a in each scenario (upper bound before re-optimisation); disconnected VN shipping would rise to ~225 Mt/a; if maritime CO2 trade were removed "
            "(disconnected.co2_shipping_intra_asean forbid, M08a A7) the disconnected case falls back to extra-ASEAN storage at 54.70 EUR/t (+5.5 bn/a); to be checked on the rebuilt "
            "networks", 130, "MtCO2/a re-routed", "C", "S4P ASPECT5_CO2.csv; registry co2_ship_chain_fixed_cost, co2_ship_chain_per_km_cost, co2_extra_asean_storage_cost_unified",
            "S4R_PLAN.md section 8", cfg_sha, country="VN", decision_ref="129, 92, 95, 132", status="REFERENCE_ONLY")


# --- supplement 01 section 2 (b1): landlocked transit corridor; A5 follow-up: ship routes into receivers without a national store ----------
def s01(reg: Registry, cor: Corrections):
    sup = ROOT / "research/06_scope_redesign/p1_m08a_20261021/M08A_SUPPLEMENT_01.md"
    lay = sha256(ROOT / "scripts_project/m08a_layers.py")
    ship = float(cor.value("co2_extra_asean_shipping_chain_4500km")) * float(cor.value("conv_usd2004_to_eur2020")) if cor.has("co2_extra_asean_shipping_chain_4500km") else float("nan")
    legs = {k: float(cor.value(k)) for k in sorted(cor.base.index) if k.startswith("co2_lao_transit_land_cost_")}
    reg.add("disconnected_b1_landlocked_transit_rule", "M08a supplement 01 section 2 (b1, decision 132): with disconnected.co2_shipping_intra_asean = forbid the landlocked LA keeps ONE "
            "kind of outlet - the transit corridor to extra-ASEAN storage of decision 93 ('<node> co2 transit export extra-ASEAN', carrier CO2 transit export extra-ASEAN, one per "
            "Lao buffered node, kept by every variant): cost = rail land leg to the nearest neighbouring coast on the link (registry co2_lao_transit_land_cost_<node>, "
            f"{min(legs.values()):.2f}-{max(legs.values()):.2f} EUR2020/t incl. rail loading) + the extra-ASEAN unit cost on LA's own store 'co2 sequestered extra-ASEAN LA' "
            f"(IEAGHG 2004 shipping chain at 4,500 km incl. liquefaction, harbour, buffer tanks and loading = {ship:.2f} + geological storage 30 = {ship + 30:.2f} EUR2020/t, "
            "registry co2_extra_asean_storage_cost_unified) - the same basis as the coastal extra-ASEAN exports; the corridor ends only in LA's extra-ASEAN store, never in the VN / TH "
            "national store buses (transit only, no storage in the neighbour). Enforced by m08a_layers.check_landlocked_transit (ValueError / AssertionError otherwise); every country "
            "with a captured-CO2 buffer must still reach a permanent sink after b1 (m08a_layers.co2_sink_channels). Convention (INFERENCE, framing only): the right of access to the sea "
            "and freedom of transit of land-locked States (UNCLOS Part X, Article 125; GATT 1994 Article V freedom of transit) - the transit state carries the goods, it does not "
            "store them; the corridor is kept also when the transit state leaves the coalition (coalition.remove_countries [VN]: the link has both ends in LA)",
            "transit_to_extra_asean_only", "flag", "C", "M08A_SUPPLEMENT_01.md section 2; S4D-1 decision 93; S4E-2 decision 95 a",
            "scripts_project/m08a_layers.check_landlocked_transit; evidence/M08A_B1_SINK_CHANNELS.json", sha256(sup) if sup.exists() else lay, country="LA", decision_ref="93, 95, 132")
    reg.add("co2_ship_routes_receivers_rule", "M08a (A5 follow-up): research.co2.ship_routes_table (CO2_SHIP_ROUTES_S4D2.csv, built for the D1 storage potentials) lists 70 routes "
            "into TL, whose national store is gone since the unified table (potential 0); s4d_layers.apply_intra_asean_shipping now builds the routes into the receivers that have a "
            "national store and drops (and records: ledger dropped_routes_no_national_store) the routes into receivers without one; a missing pair or an extra route into an existing "
            "store is still an error. Without this the build stopped with 'ship route table does not match the network' under the A5 configuration. Rule of decision 92 unchanged "
            "(every coastal buffered node -> every other country's national store)", "receivers_with_national_store", "flag", "B", "M08a A5 / decision 92",
            "scripts_project/s4d_layers.apply_intra_asean_shipping", sha256(ROOT / "scripts_project/s4d_layers.py"), decision_ref="92, 131")
    reg.add("co2_passthrough_buses_note", "M08a supplement 01 section 2 check (observation, model unchanged): three 'co2 stored' buses have no captured-CO2 buffer, no pipeline and no "
            "sink link - MY_Peninsular22 0, PH_Visayas10 0, TH21 0 (S4M-3 disconnected build); only Fischer-Tropsch (CO2 input) and SMR CC (CO2 output) touch them, so CO2 captured "
            "there by SMR CC must be used there by Fischer-Tropsch (INFERENCE: harmless for feasibility; the nodes are outside the captured-CO2 buffer set). Listed as pass-through "
            "buses by m08a_layers.co2_sink_channels, not as nodes without sink", 3, "buses", "B", "S4M-3 disconnected build (results_project/s4m/s4m3)",
            "evidence/M08A_B1_SINK_CHANNELS.json passthrough_buses", lay, decision_ref="132", status="REFERENCE_ONLY")


def main(steps=("a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9", "a10", "s01")):
    reg = Registry(SCRIPT); cor = Corrections()
    for s in steps:
        globals()[s](reg, cor)
    out = REG_DIR / "fragments"
    reg.write(out / "m08a.csv")
    rows = [cor.rows[k] for k in sorted(cor.rows)]
    write_csv(rows, out / "m08a_corrections.csv", COLUMNS)
    print(f"m08a.csv {len(reg.rows)} rows; m08a_corrections.csv {len(rows)} rows")


if __name__ == "__main__":
    main()
