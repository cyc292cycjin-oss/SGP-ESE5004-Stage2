"""DFX F4 (DFX_RULES section 4; weak point 7): registry refresh and backfill for the v2 demand (F1 RAS, F2 ammonia, F3 HVC scope).

Writes, from the regenerated demand tables:
  * research_inputs/registry_v5/fragments/dfx.csv              new rows (cookstove efficiencies, clean-cooking switch, useful-heat efficiency, HVC scope,
                                                               node allocation, AEO8 C.3 ATS values, RAS rule, NEU rule, ammonia rule / production / feedstock gas);
  * research_inputs/registry_v5/fragments/dfx_corrections.csv  full-row replacements of stale rows (industry ammonia / methanol / hydrogen / low-T heat / coal
                                                               retained per country from the anchor-mode table that is built, demand_tfec_2050_* = the ATS
                                                               anchors, shipping_demand_domestic_2050, rule descriptions);
  * research_inputs/registry_v5/REGISTRY_NETWORK_INPUT_MAP.csv  every numeric registry row that maps to a network input and how to read it back from the
                                                               tables (always) and from a built network (when present) - tests/research/test_dfx_demand.py;
  * (changelog mode, after d1_registry.py) research_inputs/registry_v5/REGISTRY_CHANGELOG_DFX.csv: param_id, old value, new value, reason for every row that
    differs from the registry committed before DFX (git blob of the rules commit).
Order: m08b_demand -> m08b_heat_bands -> s3_0_industry -> s2b_feedstock -> s2_0_process_emissions -> m08b_data -> dfx_data -> d1_registry -> dfx_data changelog.

    python scripts_project/dfx_data.py            # fragments + map
    python scripts_project/dfx_data.py changelog  # after d1_registry.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from d1_common import ASEAN, ASEAN10, COLUMNS, DEMAND_DIR, HVC_FEEDSTOCK_ACCOUNTS, NEU_GAS_ACCOUNT, REG_DIR, ROOT, SRC_DIR, Registry, sha256, write_csv   # noqa: E402

SCRIPT = "scripts_project/dfx_data.py"
STEP = "DFX"
ANCHORS = DEMAND_DIR / "DEMAND_ANCHOR_AEO8_ATS.csv"
ANCHOR_TABLE = DEMAND_DIR / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
EVIDENCE = DEMAND_DIR / "DEMAND_ANCHOR_M08B_EVIDENCE.json"
OUTPUT_2050 = DEMAND_DIR / "INDUSTRY_OUTPUT_2050_M08B.csv"
OUTPUT_BASE = DEMAND_DIR / "INDUSTRY_OUTPUT_BASE_M08B.csv"
SUMMARY = DEMAND_DIR / "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"   # the industry table the build reads (other_bucket useful_heat_bands)
PROCESS = REG_DIR / "PROCESS_EMISSIONS_2019_2050.csv"
MAP = REG_DIR / "REGISTRY_NETWORK_INPUT_MAP.csv"
CHANGELOG = REG_DIR / "REGISTRY_CHANGELOG_DFX.csv"
CONFIG = ROOT / "configs" / "research" / "baseline.yaml"
AEO8_TOTALS = SRC_DIR / "AEO8_2050_ASEAN_TOTALS.csv"
AEO8_PDF_SHA = "48c2a81913ed785cb0e14a55e332ea7bc87f912f7fabfbc8c654e09b66b11c06"   # aeo8.pdf (registry demand_* rows), re-read 2026-10-26 with pypdf (p.184, p.202)
PE_CONFIG = SRC_DIR / "pypsa_eur_v2025.07.0_config.default.yaml"
USGS_SHA = "9b055fcd5af81b6157dfae73965d90efcbb467699d745dfae344bfd077dbcc42"   # usgs_myb1-2022-nitro-ert.xlsx (registry_v5/sources/pypsa_eur_data, main checkout; registry row industry_sector_ratios_eu27_ammonia_2019)
IDEES = "JRC-IDEES-2021_Industry_EU27.xlsx (sha256 1fd3bc14deaf515c52a0293b5e0bc4cf91cfba96b01723c0c9265ed4235d3dc3): no ammonia / NH3 / nitrogen row"
TD = ROOT / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv"
RULES_COMMIT = "834a0f19"   # DFX_RULES.md commit (registry before DFX = this blob)
SECTORS = ["Industry", "Transport", "Residential", "Commercial", "AgricultureOthers"]
C3_ITEM = {"Industry": "Industry", "Transport": "Transport", "Residential": "Residential", "Commercial": "Commercial", "AgricultureOthers": "Agriculture and Others", "Total": "Total"}
ATS_SRC = "ACE, 8th ASEAN Energy Outlook 2023-2050 (2024)"


class Corrections:
    """Full-row replacements built from the registry assembled WITHOUT the dfx fragments (deterministic re-runs; mirrors m08b_data.Corrections)."""

    def __init__(self):
        import d1_registry
        frames = [pd.read_csv(REG_DIR / "fragments" / f"{f}.csv", dtype=str, keep_default_na=False) for f in d1_registry.FRAGMENTS if not f.startswith("dfx")]
        u = Registry("scripts_project/d1_registry.py"); d1_registry.unit_rows(u)
        frames.append(pd.DataFrame(u.rows, columns=COLUMNS))
        df = pd.concat(frames, ignore_index=True)[COLUMNS]
        for f in d1_registry.CORRECTIONS:
            if f.startswith("dfx"):
                continue
            corr = pd.read_csv(REG_DIR / "fragments" / f"{f}.csv", dtype=str, keep_default_na=False)[COLUMNS]
            df = pd.concat([df[~df.param_id.isin(corr.param_id)], corr], ignore_index=True)
        self.base = df.set_index("param_id")
        self.rows = {}

    def _refs(self, r, ref):
        refs = [x.strip() for x in str(r.get("decision_ref", "")).replace(";", ",").split(",") if x.strip()]
        return ", ".join(refs + [x for x in (ref,) if x not in refs])

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


def g12(v) -> str:
    return f"{float(v):.12g}"


def fragments():
    an = pd.read_csv(ANCHORS, keep_default_na=False).set_index("country")
    tab = pd.read_csv(ANCHOR_TABLE, keep_default_na=False); tab["v"] = pd.to_numeric(tab.value_2050_mwh, errors="coerce").fillna(0.0)
    ev = json.loads(EVIDENCE.read_text(encoding="utf-8")); ras = ev["ras"]; amm = ev["ammonia"]; tot = ev["totals"]
    out = pd.read_csv(OUTPUT_2050).set_index("country"); base = pd.read_csv(OUTPUT_BASE, keep_default_na=False).set_index("country")
    summ = pd.read_csv(SUMMARY).set_index("country")
    src_an = f"anchors:{sha256(ANCHORS)}; table:{sha256(ANCHOR_TABLE)}; evidence:{sha256(EVIDENCE)}"
    src_ind = f"summary:{sha256(SUMMARY)}; output:{sha256(OUTPUT_2050)}"
    src_cfg = f"config:{sha256(CONFIG)}; s2_layers:{sha256(HERE / 's2_layers.py')}"
    reg = Registry(SCRIPT); cor = Corrections(); maps = []

    def mp(pid, kind, source, selector, unit, note=""):
        maps.append(dict(param_id=pid, kind=kind, source=source, selector=selector, unit=unit, note=note))

    # ---- F1: RAS sector split, AEO8 C.3 values, NEU outside the envelope ----------------------------------------------------------------
    c3 = pd.read_csv(AEO8_TOTALS, dtype=str); c3 = c3[c3.table == "C.3 TFEC by Sector"]
    for s, item in C3_ITEM.items():
        for scen, year, tag in (("ATS", "2050", "2050"), ("historical (as printed in ATS panel)", "2022", "2022")):
            e = c3[(c3["item"] == item) & (c3.scenario == scen) & (c3.year == year)]
            val = float(str(e.value_as_printed.iloc[0]).replace(",", ""))
            reg.add(f"aeo8_c3_ats_{tag}_{s}", f"AEO8 Table C.3 TFEC by sector (Mtoe), ATS panel, {item} {tag} as printed (PDF p.184, printed p.182; re-read from the PDF text layer 2026-10-26, DFX F1); "
                    + ("column target of the DFX F1 RAS sector split (x 11.63e6 MWh x k)" if (tag == "2050" and s != "Total") else "growth 2022 -> 2050 of the electricity weights and of the TL sector weights" if tag == "2022" and s != "Total" else "panel total"),
                    val, "Mtoe", "A", ATS_SRC, "Table C.3 p.184 (printed 182)", f"pdf:{AEO8_PDF_SHA}; csv:{sha256(AEO8_TOTALS)}", decision_ref="DFX F1", status="REGISTERED" if (tag == "2050" and s != "Total") else "REFERENCE_ONLY")
    reg.add("demand_sector_split_ras", "DFX F1 (DFX_RULES section 1.3; weak points 1-2): the sector split of the 10 AEO8 countries is a RAS biproportional fit - seeds = 2019 sector energy use "
            "(D1 table base_2019_mwh, NonEnergyUse excluded), row targets = the country ATS TFEC anchors (C.8 x D.1), column targets = Table C.3 ATS 2050 sector values x 11.63e6 x k "
            f"(k = sum of the anchors / sum of C.3 = {ras['k_scale']:.12f}); rows then columns, tolerance {ras['tolerance']:.0e} on both, max {ras['max_iterations']} iterations "
            f"(converged at iteration {ras['iterations']}, row error {ras['row_error']:.2e}, column error {ras['column_error']:.2e}); zero seeds stay zero; TL outside the fit "
            "(normalised weights, NEU excluded). Replaces the normalised weights 2019 sector quantity x C.3 growth of M08b B1 (demand_anchor_family_main); 10-country sector anchors TWh: "
            + ", ".join(f"{s} {tot[f'ras_sector_anchor_10_{s}_twh']:,.3f}" for s in SECTORS), "ras_c3_ats_2050", "rule", "B", ATS_SRC + "; D1 demand table (2019 sector energy use)",
            "DEMAND_ANCHOR_AEO8_ATS.csv ras_sector_anchor_*_mwh; DEMAND_ANCHOR_M08B_EVIDENCE.json ras", src_an, decision_ref="DFX F1")
    reg.add("demand_ras_k_scale", "DFX F1.3: scaling of the C.3 ATS 2050 column targets to the sum of the country anchors (C.8 x D.1 rounding): k = "
            f"{ras['sum_row_targets_mwh'] / 1e6:,.3f} TWh / {ras['sum_column_targets_printed_mwh'] / 1e6:,.3f} TWh", ras["k_scale"], "dimensionless", "B", ATS_SRC,
            "DEMAND_ANCHOR_M08B_EVIDENCE.json ras.k_scale", src_an, decision_ref="DFX F1")
    for s in SECTORS:
        reg.add(f"demand_ras_sector_anchor_2050_{s}", f"DFX F1: 10-country 2050 energy-use anchor of sector {s} after the RAS fit = k x C.3 ATS 2050 {s} (TL {an.at['TL', f'ras_sector_anchor_{s}_mwh'] / 1e6:,.3f} TWh outside the fit)",
                tot[f"ras_sector_anchor_10_{s}_twh"] * 1e6, "MWh/a", "B", ATS_SRC, f"DEMAND_ANCHOR_AEO8_ATS.csv ras_sector_anchor_{s}_mwh (10 countries)", src_an, decision_ref="DFX F1")
        mp(f"demand_ras_sector_anchor_2050_{s}", "table", ANCHORS.name, f"sum(ras_sector_anchor_{s}_mwh) over ASEAN10", "MWh/a")
    reg.add("demand_neu_outside_tfec", "DFX F1.2 (weak point 1): non-energy use is outside the ATS TFEC envelope (AEO8 Appendix E p.202: TFEC excludes non-energy use and international "
            "transportation); it is no longer part of the industry weight; 2050 NEU = 2019 NEU x the country industry multiplier (energy-use industry anchor / 2019 industry energy use); "
            f"TL has no 2019 industry energy use -> KH / LA / MM mean multiplier (TL rule); 11 countries NEU 2019 {tot['neu_2019_11_twh']:,.1f} TWh -> 2050 {tot['neu_2050_11_twh']:,.1f} TWh "
            "(after the ammonia feedstock gas deduction of F2.4)", "outside_envelope", "rule", "B", ATS_SRC + " Appendix E", "DEMAND_ANCHOR_AEO8_ATS.csv neu_multiplier, neu_2050_mwh", src_an, decision_ref="DFX F1")
    reg.add("demand_tl_industry_multiplier_rule", "DFX F1.2: Timor-Leste 2019 industry energy use = 0 (D1 table) -> industry multiplier undefined; industry rows stay 0, the NEU rows use "
            f"the simple mean of the KH / LA / MM industry multipliers = {an.at['TL', 'neu_multiplier']:.6g} (extension of demand_anchor_tl_rule)", an.at["TL", "neu_multiplier"], "dimensionless", "C",
            "DFX_RULES section 1.2", "DEMAND_ANCHOR_AEO8_ATS.csv row TL", src_an, country="TL", decision_ref="DFX F1", sensitivity_low=min(an.at[p, "industry_multiplier"] for p in ("KH", "LA", "MM")),
            sensitivity_high=max(an.at[p, "industry_multiplier"] for p in ("KH", "LA", "MM")))
    for c in ASEAN:
        reg.add(f"demand_neu_2050_{c}", f"{c} non-energy use 2050 (all carriers, MWh) = 2019 {an.at[c, 'neu_2019_mwh'] / 1e6:,.3f} TWh x multiplier {an.at[c, 'neu_multiplier']:.6g}"
                + (f" - ammonia feedstock gas {an.at[c, 'ammonia_feedstock_gas_deduction_mwh'] / 1e6:,.3f} TWh (F2.4)" if float(an.at[c, "ammonia_feedstock_gas_deduction_mwh"]) > 0 else "")
                + "; the network NEU loads apply the HVC primary fraction to the HVC feedstock oil accounts (F3)", an.at[c, "neu_2050_mwh"], "MWh/a", "B", "derived (DFX F1.2 / F2.4)",
                "DEMAND_ANCHOR_AEO8_ATS.csv neu_2050_mwh", src_an, country=c, decision_ref="DFX F1", status="REGISTERED" if float(an.at[c, "neu_2050_mwh"]) > 0 else "SOURCE_ZERO")
        mp(f"demand_neu_2050_{c}", "table", ANCHOR_TABLE.name, f"sum(value_2050_mwh) sector=NonEnergyUse country={c}", "MWh/a")
    # ---- F2: ammonia -------------------------------------------------------------------------------------------------------------------------
    reg.add("industry_ammonia_output_rule", "DFX F2.1 (DFX_RULES section 2; weak point 5): 2050 ammonia production by country = USGS Minerals Yearbook 2022 Nitrogen Table 12 2019 production "
            "(thousand t contained N x 17/14 -> kt NH3, PyPSA-Eur build_ammonia_production reproduction) x max(G, 1)^((2050 - 2019) / 28 x elasticity 0.5), G = AEO8 D.2 real GDP 2050 / 2022; "
            "no per-capita saturation, no plan cap (same growth term as cement / steel, industry_output_rule_2050); countries not listed by USGS -> 0 (BN, KH, LA, MM, PH, SG, TH, TL); the ammonia "
            "load = production x 5.166 MWh_NH3/t (ratio table) and REPLACES the EU27 chemicals-weight ammonia share (industry_ammonia_eu27_share_dropped_*); methanol, HVC, chlorine and the other "
            f"chemical sectors keep the EU27 weight method (no ASEAN production data on this machine); 11 countries {out.ammonia_2050_mt.sum():,.3f} Mt NH3 2050 (v1 implied 6.17 Mt); registered "
            "alternatives not run: elasticity 0.3 / 0.8 (INDUSTRY_OUTPUT_2050_M08B.csv ammonia_2050_elasticity_low/high_mt), 2019 production held constant (ammonia_2050_constant_2019_mt)",
            "usgs_2019_x_growth_rule", "rule", "C", "USGS MYB 2022 Nitrogen T12; AEO8 Table D.2", "INDUSTRY_OUTPUT_2050_M08B.csv ammonia_*", src_ind, decision_ref="DFX F2",
            sensitivity_low=float(out.ammonia_2050_elasticity_low_mt.sum()), sensitivity_high=float(out.ammonia_2050_elasticity_high_mt.sum()))
    usgs_x = SRC_DIR / "pypsa_eur_data" / "usgs_myb1-2022-nitro-ert.xlsx"   # git-ignored source (main checkout); the SHA256 measured 2026-10-26 is pinned and re-checked when the file is present
    if usgs_x.exists() and sha256(usgs_x) != USGS_SHA:
        raise SystemExit(f"USGS workbook SHA256 differs from the pinned value: {usgs_x}")
    usgs_sha = f"usgs:{USGS_SHA}; csv:{amm['source_sha256']}"
    for c in ASEAN:
        b = float(base.at[c, "ammonia_base_kt"])
        reg.add(f"industry_ammonia_production_2019_{c}", f"{c} ammonia production 2019 = {b:,.3f} kt NH3 ({base.at[c, 'ammonia_source']})", b, "kt NH3/a", "B",
                "USGS Minerals Yearbook 2022 Nitrogen (advance release) Table 12, via PyPSA-Eur v2025.07.0 build_ammonia_production (kt N x 17/14)", "T12 row " + c, usgs_sha, country=c,
                decision_ref="DFX F2", status="REGISTERED" if b > 0 else "SOURCE_ZERO")
        o = out.loc[c]
        reg.add(f"industry_ammonia_output_2050_{c}", f"{c} ammonia production 2050 by industry_ammonia_output_rule = {b:,.3f} kt x {float(o.ammonia_growth_factor):.4f} = {float(o.ammonia_2050_mt) * 1e3:,.3f} kt NH3 ({o.ammonia_binding})",
                float(o.ammonia_2050_mt) * 1e6, "t/a", "C", "rule industry_ammonia_output_rule", f"INDUSTRY_OUTPUT_2050_M08B.csv row {c}", src_ind, country=c, decision_ref="DFX F2",
                sensitivity_low=float(o.ammonia_2050_elasticity_low_mt) * 1e6, sensitivity_high=float(o.ammonia_2050_elasticity_high_mt) * 1e6, status="REGISTERED" if b > 0 else "SOURCE_ZERO")
        mp(f"industry_ammonia_output_2050_{c}", "table", OUTPUT_2050.name, f"ammonia_2050_mt x 1e6 country={c}", "t/a")
    reg.add("industry_ammonia_feedstock_gas_per_t", "DFX F2.4: natural gas deducted from the NEU natural-gas rows per t of 2050 ammonia production = PyPSA-Eur v2025.07.0 config.default.yaml "
            "line 850 MWh_CH4_per_tNH3_SMR 10.8 (the constant of the industry sector ratio script lines 431-437 and of s3_0_industry.py PE); it is the SMR route's TOTAL natural-gas input "
            "(reformer feedstock + fuel), therefore an UPPER BOUND of the feedstock share that UNSD books as non-energy use; JRC-IDEES-2021 (first-priority source) has no ammonia-specific row "
            f"({IDEES}); sensitivity lower bound = stoichiometric feedstock {amm['feedstock_gas_mwh_per_t_stoichiometric']} MWh/t (technology-data Haber-Bosch hydrogen-input 1.1484 x 5.166 MWh/t / 1.2055 MWh_H2 per MWh_CH4), not run",
            amm["feedstock_gas_mwh_per_t"], "MWh_CH4/t NH3", "C", "PyPSA-Eur v2025.07.0 config.default.yaml (industry: MWh_CH4_per_tNH3_SMR)", "line 850", f"config:{sha256(PE_CONFIG)}; td:{sha256(TD)}",
            decision_ref="DFX F2", sensitivity_low=amm["feedstock_gas_mwh_per_t_stoichiometric"], sensitivity_high=amm["feedstock_gas_mwh_per_t"])
    for c in ASEAN:
        ded = float(an.at[c, "ammonia_feedstock_gas_deduction_mwh"]); tr = float(an.at[c, "ammonia_feedstock_gas_truncated_mwh"]); before = float(an.at[c, "neu_gas_2050_before_deduction_mwh"])
        reg.add(f"industry_ammonia_feedstock_gas_deducted_{c}", f"{c} ammonia feedstock gas deducted from the NEU natural-gas row ({NEU_GAS_ACCOUNT}) 2050: {float(an.at[c, 'ammonia_2050_t']):,.0f} t NH3 x "
                f"{amm['feedstock_gas_mwh_per_t']} MWh/t = {float(an.at[c, 'ammonia_2050_t']) * amm['feedstock_gas_mwh_per_t'] / 1e6:,.3f} TWh against {before / 1e6:,.3f} TWh -> deducted {ded / 1e6:,.3f} TWh"
                + (f", TRUNCATED at 0 ({tr / 1e6:,.3f} TWh not deductible)" if tr > 0 else "") + "; sensitivity low = stoichiometric 4.92 MWh/t", ded, "MWh/a", "C", "rule industry_ammonia_feedstock_gas_per_t",
                f"DEMAND_ANCHOR_AEO8_ATS.csv row {c}", src_an, country=c, decision_ref="DFX F2", sensitivity_low=min(before, float(an.at[c, "ammonia_2050_t"]) * amm["feedstock_gas_mwh_per_t_stoichiometric"]),
                sensitivity_high=ded, status="REGISTERED" if ded > 0 else "SOURCE_ZERO")
        mp(f"industry_ammonia_feedstock_gas_deducted_{c}", "table", ANCHORS.name, f"ammonia_feedstock_gas_deduction_mwh country={c}", "MWh/a")
        dropped = float(summ.at[c, "pe_ammonia_eu27_share_dropped_mwh"])
        reg.add(f"industry_ammonia_eu27_share_dropped_{c}", f"{c} EU27 chemicals-weight ammonia share of the chemical sub-sector energy (2019 x weight 0.3075 x multiplier x efficiency 0.449) no longer "
                f"generating an ammonia load (DFX F2.2, replaced by the production rule): {dropped / 1e6:,.3f} TWh; v1 ammonia load", dropped, "MWh/a", "C", "derived (s3_0_industry.py, DFX F2.2)",
                f"{SUMMARY.name} pe_ammonia_eu27_share_dropped_mwh", src_ind, country=c, decision_ref="DFX F2", sensitivity_low=0.0, sensitivity_high=dropped, status="REFERENCE_ONLY")
    # ---- F3: HVC scope -----------------------------------------------------------------------------------------------------------------------
    reg.add("hvc_primary_fraction_scope", "DFX F3 (weak point 8): share_HVC_primary_fraction_2050 (0.4) scales the HVC feedstock non-energy-use oil accounts only: " + ", ".join(HVC_FEEDSTOCK_ACCOUNTS)
            + " (2019 11 countries 326.7 TWh); the other NonEnergy:* oil products (bitumen, lubricants, paraffin waxes, petroleum coke, gas oil, motor gasoline, fuel oil; 55.9 TWh) and the coal / gas rows "
            "keep factor 1.0; config research.s2.industry.hvc_recycling_applies_to_naphtha true = this scope, false = no reduction (new definition; before DFX the factor hit every NEU oil row)",
            "hvc_feedstock_accounts", "flag", "B", "DFX_RULES section 3; d1_common.HVC_FEEDSTOCK_ACCOUNTS; s2_layers.add_demand_layer", "configs/research/baseline.yaml research.s2.industry.hvc_recycling_applies_to_naphtha",
            src_cfg + f"; d1_common:{sha256(HERE / 'd1_common.py')}", decision_ref="DFX F3")
    # ---- F4: unregistered constants and switches ----------------------------------------------------------------------------------------------
    cook_src = "IEA (2020) Defining energy access: 2020 methodology, Table 2 'Cookstove efficiencies by type and region' (Indonesia, Thailand, Other Southeast Asia); no local file - constants in scripts_project/s2_layers.py COOKSTOVE_*"
    for pid, val, desc in (("cookstove_efficiency_basic_ID", 0.08, "Indonesia basic fuelwood stove efficiency"), ("cookstove_efficiency_basic_TH", 0.16, "Thailand basic fuelwood stove efficiency"),
                           ("cookstove_efficiency_basic_default", 0.08, "'Other Southeast Asia' basic fuelwood stove efficiency (the other nine countries)"),
                           ("cookstove_efficiency_modern", 0.53, "modern stove efficiency (LPG, electricity, natural gas) serving the clean-cooking useful energy")):
        reg.add(pid, f"DFX F4 backfill: {desc}; decision 23 clean cooking: traditional biomass of the residential / commercial fuel rows x basic efficiency = useful cooking energy served by "
                "modern stoves (s2_layers.add_demand_layer cooking electric / gas / LPG links); registered as grade C (web source, no local file)", val, "fraction", "C", cook_src,
                "configs/research/baseline.yaml research.s2.demand.cookstove_efficiency_source", src_cfg, decision_ref="23, DFX F4", sensitivity_low=(0.05 if val < 0.5 else 0.45), sensitivity_high=(0.25 if val < 0.5 else 0.60))
    mp("cookstove_efficiency_basic_ID", "network_meta", "n.meta.s2_demand_ledger.parameters", "cookstove_basic.ID", "fraction")
    mp("cookstove_efficiency_basic_TH", "network_meta", "n.meta.s2_demand_ledger.parameters", "cookstove_basic.TH", "fraction")
    mp("cookstove_efficiency_basic_default", "network_meta", "n.meta.s2_demand_ledger.parameters", "cookstove_basic_default", "fraction")
    mp("cookstove_efficiency_modern", "network_meta", "n.meta.s2_demand_ledger.parameters", "cookstove_modern", "fraction")
    reg.add("clean_cooking_switch", "DFX F4 backfill of decision 23: research.s2.demand.clean_cooking true = the biomass rows of the residential / commercial fuel demand become useful cooking "
            "energy (x basic stove efficiency) served by modern stoves (electricity / gas / LPG at 0.53); false = biomass final energy kept", "true", "flag", "B", "decision 23; configs/research/baseline.yaml",
            "research.s2.demand.clean_cooking", src_cfg, decision_ref="23, DFX F4")
    reg.add("industry_useful_heat_efficiency", "DFX F4 backfill: other-bucket industrial fuel -> useful heat efficiency 0.90 (scripts_project/s3_0_industry.py HEAT_EFF; M08b B2 useful_heat_bands; "
            "the same value as research.s2.industry.biomass_overflow_useful_heat_efficiency and existing_boiler_efficiency: technology-data v0.15.0 solid biomass boiler steam efficiency 0.90)",
            0.90, "MWh_useful/MWh_fuel", "C", "technology-data v0.15.0 costs_2050 (solid biomass boiler steam, efficiency)", "scripts_project/s3_0_industry.py HEAT_EFF", f"td:{sha256(TD)}; s3_0:{sha256(HERE / 's3_0_industry.py')}",
            decision_ref="133, DFX F4", sensitivity_low=0.80, sensitivity_high=0.95)
    mp("industry_useful_heat_efficiency", "table", SUMMARY.name, "useful_heat_efficiency (all countries)", "fraction")
    reg.add("demand_node_allocation", "DFX F4 backfill: node shares of the non-electric demand per (country, account) = results_project/assembly_v1/final_allocation (Assembly-V1 arrays), Astar "
            "electricity shares where no array exists (research.s2.demand.node_allocation = assembly_v1_allocation_shares_then_astar; s2_layers.allocation_node_shares)",
            "assembly_v1_allocation_shares_then_astar", "flag", "B", "configs/research/baseline.yaml", "research.s2.demand.node_allocation", src_cfg, decision_ref="DFX F4")
    # ---- F4: refresh of stale rows (anchor-mode values the build reads) ---------------------------------------------------------------------------
    unit = {"ammonia": ("MWh_NH3/a", "pe_ammonia_mwh"), "methanol": ("MWh_MeOH/a", "pe_methanol_mwh"), "hydrogen": ("MWh_H2/a", "pe_hydrogen_mwh"),
            "low_temperature_heat": ("MWh/a", "pe_heat_mwh"), "coal_retained": ("MWh/a", "coal_retained_2050_mwh")}
    for c in ASEAN:
        for key, (u, col) in unit.items():
            pid = f"industry_{key}_2050_{c}"
            v = float(summ.at[c, col])
            if not cor.has(pid):
                continue
            note = (f"anchor-mode value of the industry table the build reads ({SUMMARY.name}, growth_method ats_anchor, other_bucket useful_heat_bands) = {v:.12g} {u}; "
                    "the fragment row held the aeo8_ats_relative sensitivity value (DMD D2 stale rows)")
            if key == "ammonia":
                note += f"; DFX F2: production rule (industry_ammonia_output_rule) {float(out.at[c, 'ammonia_2050_mt']) * 1e3:,.3f} kt x 5.166 MWh/t, EU27 share dropped"
                lo, hi = float(out.at[c, "ammonia_2050_elasticity_low_mt"]) * 1e6 * 5.166, float(out.at[c, "ammonia_2050_elasticity_high_mt"]) * 1e6 * 5.166
                cor.modify(pid, "F2/F4", "DFX F2", note, value=g12(v), tier="C", source="rule industry_ammonia_output_rule (USGS 2019 x growth) x ratio-table 5.166 MWh_NH3/t", source_locator=f"{SUMMARY.name} row {c} pe_ammonia_mwh",
                           source_sha256=src_ind, sensitivity_low=g12(lo), sensitivity_high=g12(hi), status="REGISTERED" if v > 0 else "SOURCE_ZERO")
            else:
                r = cor.base.loc[pid]
                ch = dict(value=g12(v), source_locator=f"{SUMMARY.name} row {c} {col}", source_sha256=src_ind, status="REGISTERED" if v > 0 else "SOURCE_ZERO")
                if r.tier == "C" and r.sensitivity_low != "":
                    old = float(r.value) if r.value not in ("", "DATA_PENDING") else 0.0
                    f_lo = float(r.sensitivity_low) / old if old else 0.0; f_hi = float(r.sensitivity_high) / old if old else 1.0
                    ch.update(sensitivity_low=g12(v * f_lo), sensitivity_high=g12(v * f_hi))
                cor.modify(pid, "F4", "DFX F4", note, **ch)
            mp(pid, "table", SUMMARY.name, f"{col} country={c}", u)
    for c in ASEAN:
        pid = f"demand_tfec_2050_{c}"
        if cor.has(pid):
            cor.modify(pid, "F1/F4", "DFX F1", f"ATS TFEC anchor of the ats_anchor table (C.8 per capita x D.1 population; energy use, NEU outside the envelope; sectors by the RAS split) = {float(an.at[c, 'ats_tfec_2050_mwh']):.12g} MWh; "
                       "the fragment row held an earlier AEO8-relative allocation", value=g12(an.at[c, "ats_tfec_2050_mwh"]), unit="MWh/a", source=ATS_SRC + " (Tables C.8, D.1)", source_locator=f"DEMAND_ANCHOR_AEO8_ATS.csv row {c} ats_tfec_2050_mwh",
                       source_sha256=src_an, tier="B", sensitivity_low="", sensitivity_high="")
            mp(pid, "table", ANCHORS.name, f"ats_tfec_2050_mwh country={c}", "MWh/a")
        pid = f"industry_steel_2050_{c}"
        if cor.has(pid):
            mp(pid, "table", SUMMARY.name, f"crude_steel_2050_t country={c}", "t/a")
        pid = f"industry_cement_2050_{c}"
        if cor.has(pid):
            mp(pid, "table", OUTPUT_2050.name, f"cement_2050_mt country={c}", "Mt/a")
    dom = float(tab[tab.account == "DomesticShippingFuel"].v.sum())
    cor.modify("shipping_demand_domestic_2050", "F1/F4", "DFX F1", f"anchor-table DomesticShippingFuel rows (oil-equivalent) 2050 = {dom:.12g} MWh (RAS transport anchor x 2019 fuel shares); the fragment row held the pre-M08b ratio-table value",
               value=g12(dom), source_locator=f"{ANCHOR_TABLE.name} account DomesticShippingFuel", source_sha256=src_an)
    mp("shipping_demand_domestic_2050", "table", ANCHOR_TABLE.name, "sum(value_2050_mwh) account=DomesticShippingFuel", "MWh_oil_eq/a")
    for pid, note in (("demand_anchor_family_main", "sector split = DFX F1 RAS fit of the 10 AEO8 countries to the C.3 ATS 2050 sector values (demand_sector_split_ras); non-energy use outside the TFEC envelope (demand_neu_outside_tfec)"),
                      ("demand_base_load_rule", "unchanged method; the sector TFEC weights of the other rules are now the RAS sector anchors (demand_sector_split_ras)"),
                      ("demand_transport_anchor_rule", f"transport anchor = RAS transport anchor (C.3 ATS 2050 transport 228.2 Mtoe x k), 11 countries {tot['transport_anchor_11_twh']:,.1f} TWh (was 1,700.4); non-energy use no longer in any weight"),
                      ("demand_sector_fuel_anchor_rule", "sector TFEC anchor = RAS sector anchor (demand_sector_split_ras) - sector electricity anchor; " + "; ".join(f"{k} {tot[f'{k}_fuel_anchor_11_twh']:,.1f} TWh" for k in ("residential", "commercial", "agriculture"))),
                      ("industry_output_rule_2050", "ammonia added with the growth term only (industry_ammonia_output_rule); methanol, HVC and the energy fallback still scale with the ATS industry multiplier (energy use, NEU excluded)"),
                      ("industry_output_base_year", "ammonia 2019 = USGS Minerals Yearbook 2022 Nitrogen Table 12 (thousand t N x 17/14: ID 7,407, MY 1,457, VN 1,396 kt NH3; others not listed -> 0)")):
        if cor.has(pid):
            ch = dict(value="cement 2023; crude steel 2024; ammonia 2019") if pid == "industry_output_base_year" else {}
            cor.modify(pid, "F1" if pid.startswith("demand") else "F2", "DFX F1" if pid.startswith("demand") else "DFX F2", note, **ch)
    # ---- network-level map entries (checked when a built network is present) ------------------------------------------------------------------
    for c in ASEAN:
        for key, acc, car in (("ammonia", "IndustryAmmonia", "industry ammonia"), ("methanol", "IndustryMethanol", "industry methanol"), ("hydrogen", "IndustryHydrogenDRI", "industry hydrogen"),
                              ("low_temperature_heat", "IndustryLowTemperatureHeat", "industry heat")):
            if cor.has(f"industry_{key}_2050_{c}"):
                mp(f"industry_{key}_2050_{c}", "network", "loads", f"sum(annual MWh) account={acc} carrier={car} country={c}", unit[key][0])
        for g in ("minerals", "metals", "chemicals"):
            mp(f"process_emissions_{g}_2050_ats_anchor_{c}", "table", PROCESS.name, f"tco2_2050_ats_anchor country={c} group={g}", "tCO2/a")
    mp("bunker_demand_aviation_2050", "network", "loads", "sum(annual MWh) account=InternationalAviationBunker carrier=oil final energy country=ASEAN", "MWh/a")
    mp("bunker_demand_shipping_methanol_2050", "network", "loads", "sum(annual MWh) account=InternationalShippingBunker carrier=shipping methanol country=ASEAN", "MWh/a")
    mp("share_HVC_primary_fraction_2050", "network_meta", "n.meta.s2_demand_ledger.parameters", "hvc_primary_fraction", "fraction")
    out_dir = REG_DIR / "fragments"
    reg.write(out_dir / "dfx.csv")
    rows = [cor.rows[k] for k in sorted(cor.rows)]
    write_csv(rows, out_dir / "dfx_corrections.csv", COLUMNS)
    write_csv(maps, MAP, ["param_id", "kind", "source", "selector", "unit", "note"])
    print(f"dfx.csv {len(reg.rows)} rows; dfx_corrections.csv {len(rows)} rows; map {len(maps)} rows")


def changelog():
    """REGISTRY_CHANGELOG_DFX.csv: every row whose value / status / tier / description differs from the registry of the rules commit, plus new and removed rows."""
    old_txt = subprocess.run(["git", "show", f"{RULES_COMMIT}:research_inputs/registry_v5/DATA_REGISTRY.csv"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    from io import StringIO
    old = pd.read_csv(StringIO(old_txt), dtype=str, keep_default_na=False).set_index("param_id")
    new = pd.read_csv(REG_DIR / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    dfx = pd.read_csv(REG_DIR / "fragments" / "dfx.csv", dtype=str, keep_default_na=False).set_index("param_id")
    dfxc = pd.read_csv(REG_DIR / "fragments" / "dfx_corrections.csv", dtype=str, keep_default_na=False).set_index("param_id")
    rows = []
    for pid in sorted(set(old.index) | set(new.index)):
        if pid not in old.index:
            rows.append(dict(param_id=pid, change="new", old_value="", new_value=new.at[pid, "value"], old_status="", new_status=new.at[pid, "status"], script=new.at[pid, "derivation_script"],
                             reason=("DFX F4 new row (dfx.csv)" if pid in dfx.index else "new row written by the regenerated data chain")))
            continue
        if pid not in new.index:
            rows.append(dict(param_id=pid, change="removed", old_value=old.at[pid, "value"], new_value="", old_status=old.at[pid, "status"], new_status="", script=old.at[pid, "derivation_script"], reason="row no longer written"))
            continue
        o, n = old.loc[pid], new.loc[pid]
        diff = [k for k in ("value", "status", "tier", "description", "source_sha256", "sensitivity_low", "sensitivity_high", "unit") if o[k] != n[k]]
        if not diff:
            continue
        if pid in dfxc.index:
            reason = "DFX F4 correction (dfx_corrections.csv): " + n["description"].split(f"[{STEP} ")[-1][:160]
        elif n["derivation_script"].endswith("m08b_data.py") or n["derivation_script"].endswith("m08b_demand.py"):
            reason = "regenerated by m08b_data.py from the DFX F1 / F2 anchor tables"
        elif n["derivation_script"].endswith("s3_0_industry.py"):
            reason = "regenerated by s3_0_industry.py (industry multiplier of the RAS split; aeo8_ats_relative registry rows)"
        elif n["derivation_script"].endswith("s2b_feedstock.py"):
            reason = "regenerated by s2b_feedstock.py (DFX F3 HVC scope in the full-release sensitivity; industry multiplier)"
        elif n["derivation_script"].endswith("s2_0_process_emissions.py"):
            reason = "regenerated by s2_0_process_emissions.py (ats_anchor industry multiplier of the RAS split)"
        else:
            reason = "regenerated data chain"
        rows.append(dict(param_id=pid, change="modified:" + "+".join(diff), old_value=o["value"], new_value=n["value"], old_status=o["status"], new_status=n["status"], script=n["derivation_script"], reason=reason))
    write_csv(rows, CHANGELOG, ["param_id", "change", "old_value", "new_value", "old_status", "new_status", "script", "reason"])
    kinds = pd.Series([r["change"].split(":")[0] for r in rows]).value_counts().to_dict() if rows else {}
    print(f"changelog: {len(rows)} rows ({kinds}); old registry {len(old)} rows (commit {RULES_COMMIT}), new {len(new)} rows, sha256 {sha256(REG_DIR / 'DATA_REGISTRY.csv')}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "changelog":
        changelog()
    else:
        fragments()
