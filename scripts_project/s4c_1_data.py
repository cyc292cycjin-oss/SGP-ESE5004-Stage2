"""S4C-1 registry fragment (decision 82; supplement 01 / decision 16; user decisions 2026-10-16 ~23:15-23:20 SGT).

    python scripts_project/s4c_1_data.py

Writes research_inputs/registry_v5/fragments/s4c_1.csv. Inputs are the S4C-1 data tables (OFFWIND_CONNECTION_DISTANCE_S4C1.csv,
SUBSEA_SHARE_S4C1.csv) and the cost layer; the audit result is registered from results_project/s4c/s4c1/audit_integrated if present.
"""
from __future__ import annotations

import json

import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256

SCRIPT = "scripts_project/s4c_1_data.py"
INSTRUCTION_SHA = "e1bad922b036bcb425cb9b77853e5cc4f9ca771c59c90da1a23321b89a1dcdd3"
SUPPLEMENT_SHA = "e0bc1743b47af0714f2af4d40e237715ca252ec612f16791057b458fe6a8340a"
DIST = ROOT / "research_inputs/renewable_v5/OFFWIND_CONNECTION_DISTANCE_S4C1.csv"
SUB = ROOT / "research_inputs/corridors/SUBSEA_SHARE_S4C1.csv"
LAYER = ROOT / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020_prepared.csv"
PE_ADD_ELEC_SHA = "c93974a14b4bd0d53abb22d8c9475895e0b9df2dbe58e190c2af8a77c84fa428"   # PyPSA-Eur v2025.07.0 scripts/add_electricity.py (read-only view)
PE_PROFILES_SHA = "12fe6776e65d05f86707077fab99406815d8604f18ebce3b895feb15735ec5c3"   # scripts/build_renewable_profiles.py
PE_BASE_SHA = "9a2ea2fa01f00830c7e503c66383cd1f4242565fe2954398fbe9a7508dac8b37"       # scripts/base_network.py
PE_CFG = REG_DIR / "sources" / "pypsa_eur_v2025.07.0_config.default.yaml"
AUDIT = ROOT / "results_project/s4c/s4c1/audit_integrated/COST_AUDIT_S4C1_SUMMARY.json"


def main():
    reg = Registry(SCRIPT); cfg = "configs/research/baseline.yaml"
    d = pd.read_csv(DIST); s = pd.read_csv(SUB); lay_sha = sha256(LAYER)
    reg.add("cost_layer_electric_base_candidates", "Decision 82 (implementing decision 50): new-build components inherited from the frozen electric base priced from technology-data v0.15.0 2050 EUR2020 - "
            "onwind (incl. resource classes) <- onwind, solar <- solar-utility (as the author chain), solar rooftop <- solar-rooftop, offwind-ac/dc <- offwind + station + connection, battery / home battery "
            "charger <- battery / home battery inverter, battery / home battery store <- battery / home battery storage, distribution grid, AC lines <- HVAC overhead / submarine, DC links <- HVDC overhead / "
            "submarine + inverter pair; electric_base keeps the author costs (comparison)", "cost_layer", "flag", "B", "S4C instruction S4C-1 items 1-3", f"{cfg} research.cost_layer.electric_base_candidates; scripts_project/s4c_layers.apply_cost_layer_s4c1",
            lay_sha, decision_ref="50, 82")
    reg.add("offwind_connection_method", "Offshore wind connection cost (decision 82 item 2; user decision 2026-10-16 'PyPSA-Eur formula'): capital cost = offwind + <car>-station + line_length_factor x (distance-to-shore x "
            "<car>-connection-submarine + landfall_length x <car>-connection-underground) - PyPSA-Eur v2025.07.0 add_electricity.py lines 541, 555-576; distance-to-shore per node x class = layout-weighted distance "
            "of the cells to the node onshore region (build_renewable_profiles.py lines 157-162, 287-304) on the S4A layout (scripts_project/s4c_1_offwind_distance.py)", "pypsa_eur_distance", "flag", "B",
            "PyPSA-Eur v2025.07.0 scripts/add_electricity.py, scripts/build_renewable_profiles.py (GitHub tag v2025.07.0, read-only view 2026-10-16)", "add_electricity.py 541, 555-576; build_renewable_profiles.py 157-162, 287-304",
            f"add_electricity:{PE_ADD_ELEC_SHA}|build_renewable_profiles:{PE_PROFILES_SHA}", decision_ref="50, 82")
    cfg_sha = sha256(PE_CFG)
    reg.add("offwind_landfall_length_ac", "Landfall (underground) length of AC-connected offshore wind", 20.0, "km", "B", "PyPSA-Eur v2025.07.0 config.default.yaml", "line 219 (renewable.offwind-ac.landfall_length)", cfg_sha, decision_ref="82")
    reg.add("offwind_landfall_length_dc", "Landfall (underground) length of DC-connected offshore wind", 30.0, "km", "B", "PyPSA-Eur v2025.07.0 config.default.yaml", "line 238 (renewable.offwind-dc.landfall_length)", cfg_sha, decision_ref="82")
    reg.add("offwind_connection_length_factor", "line_length_factor applied to the offshore connection (PyPSA-Eur lines.length_factor; author chain pypsa-asean config.default.yaml line 295)", 1.25, "ratio", "B",
            "PyPSA-Eur v2025.07.0 config.default.yaml", "line 325", cfg_sha, decision_ref="82")
    lay = d[d.basis == "LAYOUT"]
    for t in ["offwind-ac", "offwind-dc"]:
        x = lay[lay.tech == t]
        reg.add(f"offwind_distance_to_shore_median_{t.replace('-', '_')}", f"{t}: median distance to shore over {len(x)} node x class rows (S4A layout; range {x.average_distance_km.min():.1f}-{x.average_distance_km.max():.1f} km)",
                float(x.average_distance_km.median()), "km", "B", "scripts_project/s4c_1_offwind_distance.py", "research_inputs/renewable_v5/OFFWIND_CONNECTION_DISTANCE_S4C1.csv", sha256(DIST), decision_ref="82", status="REFERENCE_ONLY")
    px = d[d.basis != "LAYOUT"]
    reg.add("offwind_distance_proxy_rows", f"{len(px)} electric-base offshore generators without an S4A layout cell (S4A kept the author profile: " + "; ".join(f"{r.tech} {r.node} ({r.basis})" for r in px.itertuples())
            + ") use the potential-weighted mean distance of the same node (other classes), else country, else ASEAN rows - grade C proxy (no distance in the author network or profile files)",
            int(len(px)), "generators", "C", "scripts_project/s4c_1_offwind_distance.py", "OFFWIND_CONNECTION_DISTANCE_S4C1.csv basis != LAYOUT", sha256(DIST), decision_ref="82", status="REFERENCE_ONLY")
    v = json.loads((ROOT / "research_inputs/renewable_v5/OFFWIND_DISTANCE_S4C1_LOG.json").read_text())["validation"]
    reg.add("offwind_distance_author_validation", "Check against the author network (not passed, stated): the author PyPSA-Earth formula (distance to the bus x underwater-fraction mix, add_electricity.py 549-567 of this repo) "
            f"with the author costs_2050.csv on the S4A regions reproduces the electric-base offshore capital cost with median |rel| {v['offwind-ac']['median_abs_rel_diff']:.3f} (AC) / {v['offwind-dc']['median_abs_rel_diff']:.3f} (DC), "
            f"but the connection part is 2.5 / 3.1 x the author value (correlation {v['offwind-ac']['corr_connection']:.2f} / {v['offwind-dc']['corr_connection']:.2f}): the S4A node regions (per-country Voronoi of the research nodes) "
            "differ from the author 100-cluster regions, which are not in the local cache; the author distances cannot be recovered from the total cost", "not_validated", "flag", "C",
            "scripts_project/s4c_1_offwind_distance.py", "research_inputs/renewable_v5/OFFWIND_DISTANCE_VALIDATION_AUTHOR_S4C1.csv", sha256(ROOT / "research_inputs/renewable_v5/OFFWIND_DISTANCE_VALIDATION_AUTHOR_S4C1.csv"),
            decision_ref="82", status="REFERENCE_ONLY")
    c = s[s.candidate]
    reg.add("corridor_subsea_share_method", "ASEAN-specific treatment 'archipelagic subsea corridors' (working principle 3; user decisions 2026-10-16 ~23:15 / 23:20 SGT on stop report S4C_STOP_01): PyPSA-Eur takes the underwater "
            "fraction from the real route geometry with EEZ offshore shapes (base_network.py lines 603-614), where internal waters are small in Europe; the model has no route data, and the archipelagic waters of Indonesia "
            "and the Philippines (UNCLOS Part IV, inside the archipelagic baselines, not EEZ) are large, so the share is 0 when both nodes lie on the same connected landmass of the author land shape (a small island "
            "not connected to the main island counts as a separate landmass) and otherwise the not-land share of the great-circle route (samples outside the author land shape count as subsea)",
            "landmass_nonland", "flag", "B", "S4C supplement 01; user decision 2026-10-16", f"{cfg} research.corridors.subsea_share; scripts_project/s4c_1_subsea_shares.py", f"supplement:{SUPPLEMENT_SHA}|base_network:{PE_BASE_SHA}", decision_ref="16, WP3")
    reg.add("corridor_subsea_share_switch", "research.corridors.subsea_share values: zero (former state), geometric_all (upper bound: not-land share for every pair), landmass_nonland (main)", "landmass_nonland|geometric_all|zero", "flag", "B",
            "user decision 2026-10-16 (item 3 of the confirmation)", cfg, SUPPLEMENT_SHA, decision_ref="16", status="REFERENCE_ONLY")
    reg.add("corridor_subsea_share_table", f"Decision table of {len(c)} candidate node pairs ({int(c.cross_border.sum())} cross-border; {int(c.same_landmass.sum())} same landmass, {int((~c.same_landmass).sum())} different): "
            f"main share > 0.05 for {int((c.share_landmass_nonland > 0.05).sum())} pairs, geometric_all > 0.05 for {int((c.share_geometric_all > 0.05).sum())}; per component table COMPONENT_SUBSEA_SHARE_S4C1.csv, corridor table CORRIDOR_SUBSEA_SHARE_S4C1.csv",
            int(len(c)), "pairs", "B", "scripts_project/s4c_1_subsea_shares.py", "research_inputs/corridors/SUBSEA_SHARE_S4C1.csv", sha256(SUB), decision_ref="16", status="REFERENCE_ONLY")
    reg.add("corridor_existing_capacity_no_new_capex", "Existing corridor capacity (2025 cross-border lines / links, 2025 gas stock) carries no new investment (decision 48: capital cost x existing capacity is the PyPSA objective constant); "
            "the subsea share is recorded on the component (underwater_fraction) for reporting; the existing cross-border FOM keeps the corridor-table share", "no_new_capex", "flag", "B", "S4C supplement 01 item 3",
            "s4c_layers.apply_cost_layer_s4c1", SUPPLEMENT_SHA, decision_ref="16, 48", status="REFERENCE_ONLY")
    reg.add("co2_sequestration_cost_not_in_cost_layer", "S4C-1 audit: the CO2 sequestration cost (30 EUR/t, research.s2.co2.sequestration_cost_eur_per_t) is the PyPSA-Eur config value sector.co2_sequestration_cost; "
            "technology-data v0.15.0 has no sequestration-cost row (searched: 0 rows), so decision 50 does not apply; classified as a confirmed exception (S2, decisions 28-30)", "exception", "flag", "B",
            "technology-data v0.15.0 costs_2050; PyPSA-Eur v2025.07.0 config.default.yaml line 711", "research.s2.co2.sequestration_cost_eur_per_t", lay_sha, decision_ref="28-30, 82", status="REFERENCE_ONLY")
    if AUDIT.exists():
        a = json.loads(AUDIT.read_text())
        reg.add("cost_audit_s4c1", f"Full audit of the expandable components of the S4C-1 integrated build (scripts_project/s4c_1_cost_audit.py): {a['by_status']}; unresolved {len(a['unresolved'])}",
                len(a["unresolved"]), "unresolved carrier groups", "B", "scripts_project/s4c_1_cost_audit.py", "results_project/s4c/s4c1/audit_integrated", sha256(AUDIT), decision_ref="82", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4c_1.csv")
    print("rows", len(reg.rows))


if __name__ == "__main__":
    main()
