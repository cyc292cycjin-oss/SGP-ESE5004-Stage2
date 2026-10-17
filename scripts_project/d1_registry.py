"""D1 section 1/6/7: assemble research_inputs/registry_v5/DATA_REGISTRY.csv from the d1_* fragments.

Adds the unit-conversion constants (d1_common.UNIT_CONSTANTS), the section-6 DATA_PENDING rows
(industrial process emissions and physical output: no local data, download list only) and
validates the registry (unique ids, tiers, statuses, grade-C rows carry a sensitivity range).
Writes the download list, the DATA_PENDING list and D1_EVIDENCE.json.
"""
from __future__ import annotations

import datetime as dt
import platform
import sys

import pandas as pd

from d1_common import (ASEAN, COLUMNS, COST_DIR, BIOMASS_DIR, DEMAND_DIR, LNG_DIR, REG_DIR, ROOT, SRC_DIR,
                       UNIT_CONSTANTS, WORK_DIR, Registry, read_csv, sha256, write_csv, write_json)

SCRIPT = "scripts_project/d1_registry.py"
FRAGMENTS = ["co2_storage", "fuel_prices", "lng_terminals", "fossil_production", "cost_layers", "demand_2050",
             "demand_shares", "biomass", "process_emissions", "cost_layer_v015",  # the last two are S2-0 (supplement 01)
             "industry_2050", "feedstock_territorial",  # S2 supplement 02 R1/R2 (scripts_project/s3_0_industry.py (ex s2b_industry.py), s2b_feedstock.py)
             "industry_sector_ratios", "corridors_apg",  # S3-0 (scripts_project/s3_0_industry_ratios.py, s3_0_corridors.py)
             "gas_network", "imports", "ammonia_methanol", "shipping", "fuel_carbon", "import_price_decline", "solver_r4", "industry_other_bucket", "lng_r3", "renewable_s4a", "fleet_s4a", "potentials_s4a", "s4b_0", "s4b_1", "s4b_2", "s4b_3", "s4b_4", "s4c_0", "s4c_1", "s4c_2", "s4c_3", "s4c_4", "s4d_0", "s4d_1", "s4d_2", "s4d_3", "s4d_6", "s4e_0", "s4e_1", "s4e_2", "s4f_0", "s4f_1", "s4f_2", "s4g_0", "s4g_1", "s4g_2", "s4h_0", "s4h_1"]  # S3-1 .. S3-5, S3-7 (scripts_project/s3_*_data.py, s3_7_import_price_decline.py)
CONST_SHA = {
    "UNSD": "UNSD_energy_statistics_2014_conversion_05.pdf", "IPCC": "IPCC_2006_Vol2_Ch1_Introduction.pdf",
    "FRED": "A191RD3A086NBEA.csv", "NIST": None, "EIA": None, "ECB": None,
}
CLOSED_IN_S3 = [  # S3 (batches 8 and 9; read-only public fetches)
    dict(item="JRC-IDEES-2021 Industry workbook EU27 (JRC-IDEES-2021_Industry_EU27.xlsx)", closed_by="raw8/JRC-IDEES-2021_EU27.zip -> registry_v5/sources/jrc_idees_2021/EU27/ -> scripts_project/s3_0_industry_ratios.py (decision 61)"),
    dict(item="ACE 2024 APG Interconnections Project Profiles (AIMS III priority interconnections)", closed_by="raw8/ACE2024_APG_Interconnections_Project_Profiles.pdf -> extraction/APG_AIMS3_PRIORITY_INTERCONNECTIONS_2024.csv -> scripts_project/s3_0_corridors.py (decisions 59/62)"),
    dict(item="GEM Global Gas Infrastructure Tracker - gas pipelines (ASEAN cross-border and domestic)", closed_by="raw9/GEM-GGIT-Gas-Pipelines-2025-11.xlsx -> extraction/GEM_GGIT_GAS_PIPELINES_ASEAN.csv -> S3-1 gas network (existing cross-border pipeline capacities; units without capacity stay DATA_PENDING)"),
    dict(item="USGS Minerals Yearbook nitrogen table (PyPSA-Eur ammonia_production.csv input)", closed_by="read-only fetch of myb1-2022-nitro-ert.xlsx (public S3 URL from PyPSA-Eur v2025.07.0 retrieve.smk) -> s3_0_industry_ratios.build_ammonia_production (grade B, replaces the 17,000 kt proxy)"),
]
CLOSED_IN_S2B = [  # S2 supplement 02 (batch 7)
    dict(item="worldsteel Steel Statistical Yearbook 2019/2020 - crude steel production by process", closed_by="raw7/worldsteel_SSY2020_concise.pdf -> extraction/WORLDSTEEL_2019_ASEAN.csv -> scripts_project/s2b_industry.py (R1, decision 55)"),
]
CLOSED_IN_S2_0 = [  # D1 download-list items delivered by the user in batches 5 and 6 (S2 supplement 01) and closed by S2-0
    dict(item="EDGAR_2025_GHG annual fossil CO2 (IEA-EDGAR CO2 v4)", closed_by="raw5/IEA_EDGAR_CO2_1970_2024.zip -> s2_0_process_emissions.py (55 process_emissions_* rows replaced)"),
    dict(item="USGS MCS 2025 cement / iron and steel", closed_by="raw5 PDFs used only as cross-check (EDGAR2025_USGS2025_PROCESS_EMISSIONS.md section 2); industrial_output_* rows dropped (not needed)"),
    dict(item="UNSD international marine bunkers 2019 for BN/KH/LA/TL", closed_by="raw6/UNSD_EB_2019_*.csv -> marine bunkers = 0 (grade A), demand_bunker_pending_* replaced by demand_bunker_marine_zero_*"),
    dict(item="Logging-residue factors", closed_by="decision 54: logging residues = 0 in the main potential (ZERO_BY_DECISION); FAO/APFC 2001 Table 7 x JRC98626 A3-3 67 % as high-biomass sensitivity"),
    dict(item="Wood processing residues for BN/KH/LA/MM/PH/SG/TL", closed_by="FAO/APFC 2001 Tables 9/12/13 recovery rates x FAOSTAT FO sawnwood and plywood production"),
    dict(item="technology-data geothermal electricity parameters", closed_by="decision 52: v0.15.0 still has no geothermal investment/VOM -> AEO8 D.15 Geothermal average (grade C, +-30 %), registered in S2-1"),
]
DOWNLOAD_LIST = [
    dict(item="GEM gas pipeline units without capacity (Malaysia-Singapore pipeline 1991; JDA-Arthit 2008 TH; other ASEAN rows with CapacityBcm/y '--')",
         link="https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/", landing="https://www.gem.wiki/Malaysia-Singapore_Gas_Pipeline",
         fields="Capacity (bcm/y or BOE/d) for the GEM_GGIT_GAS_PIPELINES_ASEAN.csv rows with empty capacity; owner/operator capacity statements",
         purpose="S3-1 existing cross-border gas pipeline capacities (rows without capacity carried as DATA_PENDING)", param_ids="gas_pipeline_existing_* with DATA_PENDING", section="S3-1"),
    dict(item="Oil palm trunk/frond feedstock price survey (none found in NEDO/NRI 2024 or ERIA 2024)",
         link="https://www.nedo.go.jp/content/800028002.pdf", landing="https://www.eria.org/uploads/Development-of-the-Bioenergy-Supply-Chain-in-AZEC-Partner-Countries.pdf",
         fields="USD/t delivered, moisture basis", purpose="section 5 cost of oil_palm_trunk (DATA_PENDING)", param_ids="biomass_cost_*_oil_palm_trunk", section="5"),
    dict(item="What a Waste 3.0 composition for Lao PDR (food/garden share missing in the country dataset)",
         link="https://datacatalog.worldbank.org/search/dataset/0039597", landing="https://datatopics.worldbank.org/what-a-waste/",
         fields="Composition - food, garden/green (% weight MSW)", purpose="section 5 msw_organic LA (DATA_PENDING)", param_ids="biomass_potential_LA_msw_organic", section="5"),
    dict(item="National CO2 storage assessments for Lao PDR and Myanmar (none published; ERIA 2024 p.56)",
         link="https://www.eria.org/research/carbon-capture-utilisation-and-storage-in-asean", landing="https://www.eria.org/",
         fields="GtCO2 storage resource by basin, P10/P50/P90", purpose="section 1 CO2 storage LA/MM (treated as 0, decision 30)",
         param_ids="co2_storage_potential_unassessed_LA, co2_storage_potential_unassessed_MM", section="1"),
    dict(item="GEM LNG terminal units without capacity (Haiphong FSRU VN under construction; proposed units in MY/VN/ID)",
         link="https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/", landing="https://www.gem.wiki/Haiphong_FSRU",
         fields="CapacityinMtpa for UnitIDs listed in LNG_IMPORT_TERMINALS_GEM_2025.csv with empty capacity",
         purpose="section 1 LNG caps (VN existing cap excludes one unit)", param_ids="lng_candidate_* with DATA_PENDING, lng_existing_capacity_VN", section="1"),
    dict(item="Regasification tariff for ASEAN LNG terminals (to add to the WEO Japan customs-border price)",
         link="https://www.iea.org/reports/world-energy-outlook-2025", landing="https://www.iea.org/reports/world-energy-outlook-2025",
         fields="USD/MBtu regasification + send-out cost", purpose="section 1 fuel price (fuel_price_lng_regasification_adder DATA_PENDING)",
         param_ids="fuel_price_lng_regasification_adder", section="1"),
]


def unit_rows(reg: Registry):
    fred = SRC_DIR / "A191RD3A086NBEA.csv"
    for pid, (val, unit, desc, source, loc, tier) in UNIT_CONSTANTS.items():
        if "UNSD" in source:
            sha = sha256(SRC_DIR / CONST_SHA["UNSD"])
        elif "IPCC" in source:
            sha = sha256(SRC_DIR / CONST_SHA["IPCC"])
        elif "FRED" in source:
            sha = sha256(fred) if fred.exists() else "n/a"
        elif "ECB" in source:
            sha = "eurofxref-hist.zip:91163b46eac9f1c3a3f8d98fc11f9012f55d954069bca7262ed5827751a3318d (currency_converter 0.18.9)"
        else:
            sha = "web source (NIST/EIA), no file"
        reg.add(pid, desc, val, unit, tier, source, loc, sha, decision_ref="D1-0 units",
                sensitivity_low=(46.5 if pid == "conv_gj_per_t_natural_gas_mass" else 6.8 if pid == "conv_gj_per_t_msw_biomass_fraction" else 40.1 if pid == "conv_gj_per_t_crude_ncv" else None),
                sensitivity_high=(50.4 if pid == "conv_gj_per_t_natural_gas_mass" else 18.0 if pid == "conv_gj_per_t_msw_biomass_fraction" else 44.8 if pid == "conv_gj_per_t_crude_ncv" else None))


def process_emission_rows(reg: Registry):
    for c in ASEAN:
        for key, desc in [("process_emissions_cement", "cement process CO2 (IPCC 2A1) 2019"),
                          ("process_emissions_chemicals", "chemical industry process CO2 (IPCC 2B) 2019"),
                          ("process_emissions_metals", "metal industry process CO2 (IPCC 2C) 2019"),
                          ("industrial_output_cement", "cement production 2019-2024 (physical)"),
                          ("industrial_output_steel", "crude steel production 2019-2024 (physical)")]:
            src = "EDGAR_2025_GHG IEA_EDGAR_CO2_1970_2024.zip" if key.startswith("process") else "USGS Mineral Commodity Summaries 2025"
            reg.add(f"{key}_{c}", f"{c} {desc}: no local data in work/p2_data_intake; see download list", None,
                    "tCO2/a" if key.startswith("process") else "t/a", "A", src, "download list section 6", "n/a", country=c,
                    decision_ref="10, L19", status="DATA_PENDING")


def validate(df: pd.DataFrame):
    problems = []
    if list(df.columns) != COLUMNS:
        problems.append("columns")
    dup = df.param_id[df.param_id.duplicated()].tolist()
    if dup:
        problems.append(f"duplicate param_id: {dup[:10]}")
    if not set(df.tier) <= {"A", "B", "C"}:
        problems.append("bad tier")
    pend = df[df.status == "DATA_PENDING"]
    if not (pend.value == "DATA_PENDING").all():
        problems.append("DATA_PENDING rows must carry DATA_PENDING as value")
    c_rows = df[(df.tier == "C") & (df.status == "REGISTERED")]
    numeric = pd.to_numeric(c_rows.value, errors="coerce").notna()
    missing = c_rows[numeric & ((c_rows.sensitivity_low == "") | (c_rows.sensitivity_high == ""))]
    if len(missing):
        problems.append(f"grade C numeric rows without sensitivity range: {missing.param_id.tolist()[:10]}")
    nosrc = df[(df.source_sha256 == "") & (df.status != "DATA_PENDING")]
    if len(nosrc):
        problems.append(f"rows without source_sha256: {nosrc.param_id.tolist()[:10]}")
    zbd = df[df.status == "ZERO_BY_DECISION"]
    if len(zbd) and not (pd.to_numeric(zbd.value, errors="coerce") == 0).all():
        problems.append("ZERO_BY_DECISION rows must carry value 0")
    return problems


def main():
    frames = []
    for f in FRAGMENTS:
        p = REG_DIR / "fragments" / f"{f}.csv"
        if not p.exists():
            raise SystemExit(f"missing fragment {p}; run scripts_project/d1_{f}.py first")
        frames.append(pd.read_csv(p, dtype=str, keep_default_na=False))
    reg = Registry(SCRIPT)
    unit_rows(reg)
    # process_emission_rows(reg): the 55 D1 DATA_PENDING rows are superseded by scripts_project/s2_0_process_emissions.py (S2-0.3)
    frames.append(pd.DataFrame(reg.rows, columns=COLUMNS))
    df = pd.concat(frames, ignore_index=True)[COLUMNS].sort_values("param_id").reset_index(drop=True)
    problems = validate(df)
    if problems:
        raise SystemExit("registry validation failed: " + "; ".join(problems))
    out = REG_DIR / "DATA_REGISTRY.csv"
    write_csv(df.to_dict("records"), out, COLUMNS)
    pending = df[df.status == "DATA_PENDING"][["param_id", "description", "country", "source", "decision_ref"]]
    write_csv(pending.to_dict("records"), REG_DIR / "DATA_PENDING_LIST.csv", list(pending.columns))
    write_csv(DOWNLOAD_LIST, REG_DIR / "DOWNLOAD_LIST.csv", list(DOWNLOAD_LIST[0].keys()))
    write_csv(CLOSED_IN_S2_0, REG_DIR / "DOWNLOAD_LIST_CLOSED_S2_0.csv", list(CLOSED_IN_S2_0[0].keys()))
    write_csv(CLOSED_IN_S2B, REG_DIR / "DOWNLOAD_LIST_CLOSED_S2B.csv", list(CLOSED_IN_S2B[0].keys()))
    write_csv(CLOSED_IN_S3, REG_DIR / "DOWNLOAD_LIST_CLOSED_S3.csv", list(CLOSED_IN_S3[0].keys()))
    summary = dict(rows=int(len(df)), by_tier=df.tier.value_counts().to_dict(), by_status=df.status.value_counts().to_dict(),
                   by_script=df.derivation_script.value_counts().to_dict(), data_pending=int(len(pending)))
    outputs = {}
    for d in [REG_DIR, DEMAND_DIR, BIOMASS_DIR, COST_DIR, LNG_DIR]:
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix in (".csv", ".json", ".md", ".txt", ".yaml") and "fragments" not in p.parts:
                outputs[str(p.relative_to(ROOT))] = dict(sha256=sha256(p), bytes=p.stat().st_size)
    evidence = dict(schema="d1-data-registry-evidence-v1", generated_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                    python=sys.version.split()[0], pandas=pd.__version__, platform=platform.platform(), registry=str(out.relative_to(ROOT)),
                    registry_sha256=sha256(out), summary=summary, outputs=outputs,
                    scripts={p: sha256(ROOT / p) for p in [f"scripts_project/d1_{s}.py" for s in ["common", "co2_storage", "fuel_prices", "lng_terminals", "fossil_production", "cost_layers", "demand_2050", "demand_shares", "biomass", "registry"]]
                             + ["scripts_project/s2_0_process_emissions.py", "scripts_project/s2_0_cost_layer_v015.py", "scripts_project/s2b_industry.py", "scripts_project/s2b_feedstock.py",
                                "scripts_project/s3_0_industry_ratios.py", "scripts_project/s3_0_industry.py", "scripts_project/s3_0_corridors.py", "scripts_project/s3_1_gas_data.py", "scripts_project/s3_2_imports_data.py", "scripts_project/s3_3_ammonia_methanol_data.py", "scripts_project/s3_4_shipping_data.py", "scripts_project/s3_5_fuel_carbon_data.py", "scripts_project/s3_7_import_price_decline.py", "scripts_project/s3b_r4_solver_data.py"]},
                    download_list=DOWNLOAD_LIST, closed_in_s2_0=CLOSED_IN_S2_0, closed_in_s2b=CLOSED_IN_S2B, closed_in_s3=CLOSED_IN_S3, solver_runs=0, network_builds=0)
    write_json(evidence, REG_DIR / "D1_EVIDENCE.json")
    print(out, summary)
    print("DATA_PENDING:", len(pending))


if __name__ == "__main__":
    main()
