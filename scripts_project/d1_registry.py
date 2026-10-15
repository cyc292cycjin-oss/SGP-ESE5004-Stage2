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
             "demand_shares", "biomass"]
CONST_SHA = {
    "UNSD": "UNSD_energy_statistics_2014_conversion_05.pdf", "IPCC": "IPCC_2006_Vol2_Ch1_Introduction.pdf",
    "FRED": "A191RD3A086NBEA.csv", "NIST": None, "EIA": None, "ECB": None,
}
DOWNLOAD_LIST = [
    dict(item="EDGAR_2025_GHG annual fossil CO2 by country and sector (IEA-EDGAR CO2 v4)",
         link="https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/EDGAR_2025_GHG/IEA_EDGAR_CO2_1970_2024.zip",
         landing="https://edgar.jrc.ec.europa.eu/dataset_ghg2025",
         fields="xlsx inside zip: Country_code_A3, ipcc_code_1996_for_standard_report (2A non-metallic minerals, 2B chemical, 2C metal), Y_1970..Y_2024 (kt CO2); licence CC BY-NC-ND 4.0",
         purpose="L19 industrial process emissions by country (cement, chemicals, metals) for 2019 base and process-CC structure",
         param_ids="process_emissions_*", section="6"),
    dict(item="USGS Mineral Commodity Summaries 2025 - Cement (world production table by country)",
         link="https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-cement.pdf", landing="https://www.usgs.gov/centers/national-minerals-information-center/cement-statistics-and-information",
         fields="Table 'World Mine/Plant Production': country, 2023, 2024e (thousand metric tons); Indonesia, Vietnam, Thailand, Philippines, Malaysia listed",
         purpose="L19 cement physical output for process-emission intensity", param_ids="industrial_output_cement_*", section="6"),
    dict(item="USGS Mineral Commodity Summaries 2025 - Iron and Steel (world raw steel production by country)",
         link="https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-iron-steel.pdf", landing="https://www.usgs.gov/centers/national-minerals-information-center/iron-and-steel-statistics-and-information",
         fields="Table 'World Production, raw steel': country, 2023, 2024e (million metric tons)",
         purpose="L19 steel output for DRI/EAF share and process emissions", param_ids="industrial_output_steel_*", section="6"),
    dict(item="UNSD Energy Statistics Database - International marine bunkers 2019 for Brunei, Cambodia, Lao PDR, Timor-Leste",
         link="https://unstats.un.org/unsd/energystats/dataPortal/", landing="https://unstats.un.org/unsd/energystats/",
         fields="Commodity - Transaction = 'Fuel oil - International marine bunkers' and 'Gas Oil/ Diesel Oil - International marine bunkers', Year 2019, Quantity (kt)",
         purpose="section 3 bunkers: the 2019 export in pypsa-asean/data/demand/unsd/data has no marine bunker rows for these four countries (likely not reported; confirm zero vs missing)",
         param_ids="demand_bunker_pending_*", section="3"),
    dict(item="Logging-residue factors for Southeast Asian industrial roundwood (e.g. FAO/IEA Bioenergy Task 43 or JRC ENSPRESO methodology)",
         link="https://data.jrc.ec.europa.eu/dataset/74ed5a04-7d74-4807-9eab-b94774309d9f", landing="https://publications.jrc.ec.europa.eu/repository/handle/JRC98626",
         fields="residue-to-roundwood ratio (t/m3), sustainable removal share",
         purpose="section 5 logging residues (DATA_PENDING)", param_ids="biomass_potential_*_logging_residues", section="5"),
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
    dict(item="technology-data geothermal electricity investment/efficiency/VOM (absent in v0.13.2; v0.15.0 to be checked by user)",
         link="https://github.com/PyPSA/technology-data/releases", landing="https://technology-data.readthedocs.io/",
         fields="technology geothermal: investment EUR/kW_e, efficiency, VOM", purpose="section 1 existing geothermal performance (DATA_PENDING in layer A; layer B has AEO8 Geothermal average)",
         param_ids="geothermal_existing_efficiency, geothermal_existing_VOM, geothermal_existing_investment", section="1"),
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
    process_emission_rows(reg)
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
                    scripts={f"scripts_project/d1_{s}.py": sha256(ROOT / "scripts_project" / f"d1_{s}.py") for s in ["common"] + FRAGMENTS + ["registry"]},
                    download_list=DOWNLOAD_LIST, solver_runs=0, network_builds=0)
    write_json(evidence, REG_DIR / "D1_EVIDENCE.json")
    print(out, summary)
    print("DATA_PENDING:", len(pending))


if __name__ == "__main__":
    main()
