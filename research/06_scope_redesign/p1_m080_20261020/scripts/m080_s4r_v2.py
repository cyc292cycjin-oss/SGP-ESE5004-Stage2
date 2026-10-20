"""M08-0 item 5: S4R REGISTRY_ROWS_PROPOSED.csv -> REGISTRY_ROWS_PROPOSED_v2.csv (new version; the S4R original is read only).

v2 changes: (1) every row whose param_id has no row of the same name in the registry (after the M08-0 backfill) gets action = add;
(2) new rows that replace existing registry rows name them in `supersedes` (M08 marks those rows historical when it writes the new ones);
(3) the misaligned lng_terminal_cap_rule row (10 fields, source_locator missing) is re-aligned by column name;
(4) the renewable_offshore_rule description no longer implies that the 5.5 MW turbine / 0.8855 wake factor are a change (M08-0 item 2).
Output: <out>/REGISTRY_ROWS_PROPOSED_v2.csv and evidence/M080_S4R_V2_CHANGES.json

    python -I m080_s4r_v2.py --s4r /mnt/d/.../p1_step4r_20261020 --registry /home/jin/wt_m080_20261020/research_inputs/registry_v5/DATA_REGISTRY.csv --out /mnt/d/.../p1_m080_20261020
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

COLS = ["param_id", "description", "value", "unit", "country", "tier", "source", "source_locator", "decision_ref", "status", "action"]
NEW_COLS = COLS + ["registry_row_exists", "supersedes", "m08_write_note", "v2_change"]
ASEAN = ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "TL", "VN"]
HIST = "M08: when writing this row, mark the superseded rows historical (REFERENCE_ONLY, description '历史：已被 {pid} 替代')"
# param_id -> (superseded registry rows, note). Only rows whose content the new row actually replaces; "" = none in the registry.
SUPERSEDES = {
    "demand_anchor_family_main": ("demand_country_allocation_mode", "current main allocation = aeo8_ats_relative (demand_aeo8_ats_relative_factor_*)"),
    "demand_base_load_rule": ("s4j1_base_load_sectors", "S4J-1 table_sectors base-load total (decision 104); the Astar hourly shape (demand_astar_shape_source) stays"),
    "industry_output_rule_2050": ("", "current industry multipliers (demand_country_multiplier_2019_2050_*) remain for the non-output sectors; M08 to confirm"),
    "industry_steel_2050_VN": ("", "same-name row exists (modify)"),
    "industry_cement_2050_VN": ("", "no registry row: the replaced 581 Mt is only in research_inputs/demand_v5/INDUSTRY_2050_SUMMARY_aeo8_ats_relative.csv (registry gap kept)"),
    "renewable_capacity_per_sqkm_solar": ("renewable_density_built_solar", "as-built 4.6 MW/km2 registered by M08-0"),
    "renewable_landuse_rule_solar": ("renewable_landcover_codes_built_solar", "main-run classes unchanged; the rule row records main + open-forest sensitivity"),
    "renewable_offshore_rule": ("renewable_landcover_codes_built_offwind_ac; renewable_landcover_codes_built_offwind_dc; renewable_density_built_offwind_dc; renewable_offshore_depth_rule",
                                "turbine / wake rows unchanged (already as proposed, renewable_offwind_profile_check_built)"),
    "lng_terminal_capacity_source": ("", "the registry already labels GEM GGIT LNG Terminals 2025-09 (lng_gem_ggit_release_verified); no row to replace"),
    "lng_terminal_cap_rule": ("lng_terminal_expansion_mode_s4b; lng_import_cap_rule_built; lng_import_cap_factor; " + "; ".join(f"lng_import_cap_built_{c}" for c in ASEAN),
                              "option (a) removes the decision-72 cap; the 2.5 x existing rows lng_import_cap_* stay as the option (c) sensitivity"),
    "biomass_overflow_rule": ("; ".join(f"industry_biomass_overflow_to_gas_{c}" for c in ASEAN) + "; s4m_decision_115_biomass_cap_share",
                              "decision-36 overflow -> methane rows; decision 115 cap share 0.98 (main since S4M-0)"),
    "nuclear_cost_rule": ("smr_investment; smr_FOM; smr_VOM", "SMR = technology-data v0.15.0 nuclear x AEO8 ratios; smr_lifetime_proxy / smr_efficiency_proxy unchanged (equal to v0.15.0)"),
    "report_currency_rule": ("", "fx_usd_to_eur_2020 stays (source of the rate)"),
    "disconnected_definition_main": ("", "s4e1_adjacency_switch is a different switch; M08 to confirm"),
    "co2_sequestration_cost_price_year": ("", "co2_sequestration_cost_not_in_cost_layer stays (audit row)"),
    "cost_layer_deflator_hicp": ("conv_eur2025_to_eur2020", "EA20 GDP deflator rebase replaced by HICP (deflator_ea20_gdp_* rows kept as comparison)"),
}
OFFSHORE_DESC = ("R2 (M08-0 v2: current state checked): offshore wind rules aligned to PyPSA-Eur v2025.07.0 - CHANGES: fixed <= 60 m (now 50 m), floating "
                 "60-1000 m (new class offwind-float; none now), ship_threshold 400 (no shipping-lane exclusion now; raster already in raw12), "
                 "excluder_resolution 200, density 2 MW/km2 all classes (now AC 2 / DC 3); ALREADY IN THE SCREENING NETWORKS (no change): turbine "
                 "NREL_ReferenceTurbine_2020ATB_5.5MW and correction_factor 0.8855 (wake) via profile_variant pypsa_eur / calibrated_modern since S4A "
                 "(registry renewable_offwind_profile_check_built); the 'NREL 5 MW, no wake' state applies to the author / fork profiles only")


# M08-0 supplement 01 (item 131): one added rule row (section 4) and notes on rows whose inputs are now downloaded (section 3); values unchanged
EXTRA_ROWS = [dict(
    param_id="existing_fleet_cost_rule",
    description=("M08-0 supplement 01 section 4: existing assets of the electric base (Assembly V1) priced and parameterised with technology-data v0.15.0 "
                 "values of the matching commissioning year (outputs costs_2020, costs_2025, ... costs_2050 of the v0.15.0 release; e.g. CCGT efficiency "
                 "0.56 / 0.57 / 0.60 for 2020 / 2025 / 2050), rebased to EUR2020 like the main layer - replaces the author technology-data v0.13.2 table "
                 "(costs year 2030) so that source and version are unified while older units keep their lower efficiency; mapping of commissioning years "
                 "before 2020 to costs_2020 to be fixed in M08"),
    value="td_v0_15_0_by_commissioning_year", unit="rule", country="", tier="C",
    source="PyPSA technology-data v0.15.0 outputs/costs_<year>.csv (tarball c4787c1d)", source_locator="M080_SUPPLEMENT_01.md section 4; registry existing_fleet_cost_source_unification",
    decision_ref="131", status="PROPOSED", action="add")]
EXTRA_SUPERSEDES = {"existing_fleet_cost_rule": ("existing_fleet_cost_source_unification",
                                                 "electric-base existing-asset costs / efficiencies (Assembly V1 model_cost_layer.json) to be rebuilt in M08; model unchanged in M08-0")}
NOTES = {
    "industry_output_base_year": "M08-0 supplement 01: inputs now downloaded - cement base year = 2023 (USGS MYB 2023 T22, latest year in the source; SG / TL -> 0), crude steel = 2024 (worldsteel Steel Data Viewer; BN / KH / LA / TL -> 0); registry download_usgs_myb2023_cement_world_t22, download_worldsteel_crude_steel_2021_2025",
    "demand_anchor_tl_rule": "M08-0 supplement 01: UN WPP 2024 primary file obtained (TL 2050 median 1,889,249.5; registry download_un_wpp2024_tl_population_2050)",
    "cost_layer_deflator_hicp": "M08-0 supplement 01: technology-data v0.15.0 inflates with the EEA annual average rate of change (product 2021-2025 = 1.25733), not EU27 / EA20 indices; the Eurostat download (registry download_eurostat_hicp_aind_2016_2025, Sheet 6) has the same rates",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--s4r", type=Path, required=True)
    ap.add_argument("--registry", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    src = a.s4r / "REGISTRY_ROWS_PROPOSED.csv"
    raw = list(csv.reader(open(src, encoding="utf-8", newline="")))
    assert raw[0] == COLS, raw[0]
    reg = {r["param_id"] for r in csv.DictReader(open(a.registry, encoding="utf-8", newline=""))}
    out, log = [], []
    for fields in raw[1:]:
        ch = []
        if len(fields) != len(COLS):
            # lng_terminal_cap_rule: source "S4R_PLAN.md R3.3" then "126, 17", "PROPOSED", "modify" -> source_locator missing
            assert fields[0] == "lng_terminal_cap_rule" and len(fields) == 10, fields[:2]
            fields = fields[:7] + ["R3.3"] + fields[7:]
            ch.append("re-aligned by column name (v1 had 10 fields: source_locator missing, decision_ref / status / action shifted one column left; "
                      "source_locator set to R3.3 from the source text)")
        r = dict(zip(COLS, fields))
        exists = r["param_id"] in reg
        if not exists and r["action"] != "add":
            ch.append(f"action {r['action'] or '(empty)'} -> add (no registry row named {r['param_id']})")
            r["action"] = "add"
        if exists and r["action"] == "add":
            ch.append("WARNING: action add but a registry row of the same name exists")
        if r["param_id"] == "renewable_offshore_rule":
            r["description"] = OFFSHORE_DESC
            ch.append("description: current state corrected (turbine 5.5 MW and wake 0.8855 already in the screening networks, M08-0 item 2)")
        if r["param_id"] == "lng_terminal_capacity_source":
            ch.append("note: GEM release verified as September 2025 (S4R files label the model table '2025-08'; same workbook SHA256 20ae2b67)")
        sup, note = SUPERSEDES.get(r["param_id"], ("", ""))
        r["registry_row_exists"] = "yes" if exists else "no"
        r["supersedes"] = sup
        r["m08_write_note"] = (HIST.format(pid=r["param_id"]) + ("; " + note if note else "")) if sup else note
        if r["param_id"] in NOTES:
            r["m08_write_note"] = (r["m08_write_note"] + "; " if r["m08_write_note"] else "") + NOTES[r["param_id"]]
            ch.append("note added (M08-0 supplement 01)")
        r["v2_change"] = "; ".join(ch)
        out.append(r)
        log.append(dict(param_id=r["param_id"], action=r["action"], registry_row_exists=exists, supersedes=sup, changes=ch))
    for x in EXTRA_ROWS:
        r = dict(x)
        exists = r["param_id"] in reg
        sup, note = EXTRA_SUPERSEDES.get(r["param_id"], ("", ""))
        r["registry_row_exists"] = "yes" if exists else "no"
        r["supersedes"] = sup
        r["m08_write_note"] = (HIST.format(pid=r["param_id"]) + ("; " + note if note else "")) if sup else note
        r["v2_change"] = "row added by M08-0 supplement 01 (item 131)"
        out.append(r)
        log.append(dict(param_id=r["param_id"], action=r["action"], registry_row_exists=exists, supersedes=sup, changes=[r["v2_change"]]))
    dst = a.out / "REGISTRY_ROWS_PROPOSED_v2.csv"
    with open(dst, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=NEW_COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    summary = dict(source=str(src), source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(), registry=str(a.registry),
                   registry_sha256=hashlib.sha256(a.registry.read_bytes()).hexdigest(), rows=len(out),
                   actions={k: sum(1 for r in out if r["action"] == k) for k in sorted({r["action"] for r in out})},
                   changed_to_add=[x["param_id"] for x in log if any("-> add" in c for c in x["changes"])],
                   with_supersedes=[x["param_id"] for x in log if x["supersedes"]], warnings=[x for x in log if any("WARNING" in c for c in x["changes"])],
                   output=str(dst), output_sha256=hashlib.sha256(dst.read_bytes()).hexdigest(), rows_detail=log)
    (a.out / "evidence").mkdir(parents=True, exist_ok=True)
    (a.out / "evidence/M080_S4R_V2_CHANGES.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows_detail"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
