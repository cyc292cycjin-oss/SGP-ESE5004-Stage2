"""S4B-1 (decision 77): existing-stock rules for 2050.

1. Units under construction count as 2050 stock (research.fleet.include_construction true, kept from S4A); announced / pre-construction units do
   not; false stays a sensitivity. The S1 survival rule NOT_INHERITED_COMMITTED_OR_PLANNED is relaxed for construction only: the 45 S1 records
   (3,881 MW) are cross-checked against GEM GIPT 2026-09 (FLEET_S1_NOT_INHERITED_ITEM77.csv).
2. Units without a start year: the 74 under construction are counted - GEM status construction in the 2026-09 tracker means not commissioned
   before 2026, so the start year is >= 2026 and every S1 lifetime (>= 25 a) keeps them in service in 2050; node mapping and parameters as S4A-2.
   The 170 operating units without a start year stay UNRESOLVED (not counted). Unit lists written.
3. The 11 network units that GIPT 2026 lists as cancelled / mothballed / retired / absent (2,854 MW) are removed from the stock by
   research.fleet.remove_not_operating_gipt2026 (data correction); their identities stay in FLEET_REMOVED_NOT_OPERATING_GIPT2026.csv and the registry.
4. Waste-to-energy units stay skipped (no fuel pathway; limitation).
5. Before / after stock by country and class (FLEET_STOCK_2050_S4B1_BY_COUNTRY_CLASS.csv).

    python scripts_project/s4b_1_fleet_data.py --network results_project/s4b/s4b0/builds/integrated/integrated_2920_3h_unsolved.nc
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

from d1_common import REG_DIR, ROOT, SRC_DIR, Registry, sha256, src_sha, write_csv, write_json
from s4a_2_fleet_data import GIPT, GIPT_XLSX_SHA, LIFETIME, ZIP_SHA, model_class, nearest_node, s1_fuel

SCRIPT = "scripts_project/s4b_1_fleet_data.py"
OUT = ROOT / "research_inputs/fleet_v5"
S1_SURVIVAL = ROOT / "research/06_scope_redesign/p1_step1_20261015/evidence/S1_SELECTED_ASSET_SURVIVAL_2050.json"
TRACKER_YEAR = 2026   # GIPT release 2026-09: a unit still under construction is commissioned in 2026 or later
REMOVAL_REASON = {"cancelled": "GIPT 2026-09 status cancelled", "mothballed": "GIPT 2026-09 status mothballed", "retired": "GIPT 2026-09 status retired",
                  "not in GIPT": "unit absent from GIPT 2026-09"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); a = ap.parse_args()
    gem = pd.read_csv(SRC_DIR / GIPT, low_memory=False); gem_sha = src_sha(GIPT); src = f"zip:{ZIP_SHA}|gipt:{GIPT_XLSX_SHA}|extraction:{gem_sha}"
    n = pypsa.Network(str(a.network)); nodes = n.buses[n.buses.carrier == "AC"][["x", "y", "country"]]
    s4a = pd.read_csv(OUT / "FLEET_ADDITIONS_2050.csv"); unres = pd.read_csv(OUT / "FLEET_UNRESOLVED_START_YEAR.csv")
    # ---- 2. construction units without a start year ---------------------------------------------------------------------------
    g = gem.set_index("GEM unit/phase ID")
    con = unres[unres.Status == "construction"].copy(); opr = unres[unres.Status == "operating"].copy()
    assert len(con) == 74 and len(opr) == 170, (len(con), len(opr))
    rows = g.loc[con["GEM unit/phase ID"]].reset_index()
    rows["s1_fuel"] = rows.apply(s1_fuel, axis=1); rows["lifetime"] = rows.s1_fuel.map(LIFETIME)
    rows["assumed_start_year"] = TRACKER_YEAR; rows["retire_year"] = TRACKER_YEAR + rows.lifetime
    assert (rows.retire_year > 2050).all()
    rows["model_class"] = rows.apply(model_class, axis=1)
    mapped = rows.apply(lambda r: nearest_node(nodes, r.iso, r.Latitude, r.Longitude), axis=1, result_type="expand"); rows["node"] = mapped[0]; rows["node_distance_km"] = mapped[1]
    rows["param_source"] = rows.model_class.map(lambda k: "technology-data v0.15.0 (grade B)")
    rows.loc[rows.model_class.isin(["hydro existing", "ror existing", "PHS existing"]), "param_source"] = "technology-data v0.15.0 FOM/efficiency (B); inflow / availability / duration proxy from node or country existing units (C)"
    rows.loc[rows.model_class.isin(["solar existing", "onwind existing", "offwind existing"]), "param_source"] = "technology-data v0.15.0 FOM (B); availability = node candidate profile (research.renewable variant)"
    rows.loc[rows.model_class == "geothermal existing", "param_source"] = "AEO8 D.15 FOM/VOM and C.4/C.5 capacity factor 0.7194 (decision 52, grade C)"
    rows.loc[rows.model_class == "waste existing", "param_source"] = "not added: no waste-to-energy pathway (limitation)"
    rows["start_year"] = np.nan; rows["age_basis"] = "ASSUMED_LOWER_BOUND_CONSTRUCTION_NO_START_YEAR (GIPT 2026-09 construction -> start >= 2026)"
    cols = ["GEM unit/phase ID", "GEM location ID", "Plant / Project name", "Unit / Phase name", "iso", "Type", "Technology", "Fuel (combustion only)", "Status", "Capacity (MW)", "start_year", "assumed_start_year", "s1_fuel", "lifetime",
            "retire_year", "model_class", "Latitude", "Longitude", "Location accuracy", "node", "node_distance_km", "param_source", "age_basis", "GEM.Wiki URL"]
    con_add = rows[cols].rename(columns={"GEM unit/phase ID": "gem_unit_id", "GEM location ID": "gem_location_id", "Plant / Project name": "plant", "Unit / Phase name": "unit", "iso": "country", "Capacity (MW)": "capacity_mw",
                                         "Fuel (combustion only)": "fuel", "Location accuracy": "location_accuracy", "GEM.Wiki URL": "gem_wiki_url"}).sort_values(["country", "model_class", "capacity_mw"], ascending=[True, True, False])
    assert con_add.node.notna().all()
    write_csv(con_add.to_dict("records"), OUT / "FLEET_ADDITIONS_CONSTRUCTION_NO_START_YEAR_2050.csv", list(con_add.columns))
    opr_out = g.loc[opr["GEM unit/phase ID"]].reset_index()[["GEM unit/phase ID", "Plant / Project name", "Unit / Phase name", "iso", "Type", "Technology", "Status", "Capacity (MW)", "Start year", "GEM.Wiki URL"]]
    opr_out["status_s4b"] = "UNRESOLVED (operating, no start year): not counted (decision 77)"
    write_csv(opr_out.to_dict("records"), OUT / "FLEET_UNRESOLVED_OPERATING_NO_START_YEAR.csv", list(opr_out.columns))
    # ---- 3. removals ---------------------------------------------------------------------------------------------------------
    rev = pd.read_csv(OUT / "FLEET_NETWORK_UNITS_NOT_OPERATING_IN_GIPT_2026.csv")
    rev["removal_reason"] = rev.gipt_status_2026.map(REMOVAL_REASON).fillna("GIPT 2026-09 status " + rev.gipt_status_2026) + " -> removed from the 2050 stock (data correction, decision 77)"
    rev["country"] = rev.node.map(n.buses.country)
    ids = n.meta["existing_unit_components"]
    rev["component_type"] = rev.identity.map(lambda k: ids[k]["component_type"] if k in ids else None)
    rev["model_class"] = rev.apply(lambda r: str(n.df(r.component_type).at[r.component, "carrier"]) if r.component_type else None, axis=1)
    assert rev.component_type.notna().all()
    write_csv(rev.to_dict("records"), OUT / "FLEET_REMOVED_NOT_OPERATING_GIPT2026.csv", list(rev.columns))
    # ---- 1. S1 NOT_INHERITED_COMMITTED_OR_PLANNED cross-check ----------------------------------------------------------------
    s1 = pd.DataFrame(json.loads(S1_SURVIVAL.read_text())["records"]); ni = s1[s1.SurvivalStatus == "NOT_INHERITED_COMMITTED_OR_PLANNED"]
    counted = set(s4a.gem_unit_id) | set(con_add.gem_unit_id); xrows = []
    for _, r in ni.iterrows():
        for sub in r.SourceSubassets:
            gid = sub.get("ID"); st26 = str(g.Status.get(gid, "not in GIPT")); sy = g["Start year"].get(gid, np.nan)
            how = ("counted: S4A-2 addition (start year known)" if gid in set(s4a.gem_unit_id) else "counted: S4B-1 construction without start year" if gid in set(con_add.gem_unit_id)
                   else "not counted: GIPT 2026 status " + st26 if st26 not in ("operating", "construction") else "not counted: retires before 2050 by the S1 lifetime rule" if pd.notna(sy) else "not counted: operating without start year (UNRESOLVED)")
            xrows.append(dict(s1_asset=r.AssetID, country=r.Country, technology=r.Technology, s1_capacity_mw=float(r.OriginalCapacity), gem_unit_id=gid, s1_source_status=sub.get("Status"),
                              gipt_2026_status=st26, gipt_capacity_mw=float(g["Capacity (MW)"].get(gid, np.nan)), gipt_start_year=sy, item77_treatment=how))
    xdf = pd.DataFrame(xrows); write_csv(xdf.to_dict("records"), OUT / "FLEET_S1_NOT_INHERITED_ITEM77.csv", list(xdf.columns))
    # ---- 5. before / after stock (MW_el by country and class) ------------------------------------------------------------------
    st = pd.DataFrame([dict(identity=k, country=str(n.buses.country.get(v["node"], "")), cls=str(n.df(v["component_type"]).at[v["component"], "carrier"]), mw=float(v["capacity_mw"])) for k, v in ids.items()])
    before = st.groupby(["country", "cls"]).mw.sum()
    add_b = con_add[con_add.model_class != "waste existing"].groupby(["country", "model_class"]).capacity_mw.sum(); add_b.index.names = ["country", "cls"]
    rem_b = rev.groupby(["country", "model_class"]).capacity_mw.sum(); rem_b.index.names = ["country", "cls"]
    tab = pd.concat([before.rename("before_s4a_mw"), add_b.rename("added_construction_no_start_mw"), rem_b.rename("removed_not_operating_mw")], axis=1).fillna(0.0)
    tab["after_s4b1_mw"] = tab.before_s4a_mw + tab.added_construction_no_start_mw - tab.removed_not_operating_mw
    tab = tab.reset_index().sort_values(["country", "cls"])
    write_csv(tab.round(3).to_dict("records"), OUT / "FLEET_STOCK_2050_S4B1_BY_COUNTRY_CLASS.csv", list(tab.columns))
    # ---- registry -------------------------------------------------------------------------------------------------------------
    reg = Registry(SCRIPT); s1_sha = sha256(S1_SURVIVAL)
    reg.add("fleet_survival_rule_committed_planned_item77", "Decision 77: the S1 survival rule NOT_INHERITED_COMMITTED_OR_PLANNED (S1_SELECTED_ASSET_SURVIVAL_2050.json, 45 records, 3,881 MW) is relaxed for units under "
            "construction only: GEM status construction counts as 2050 stock (lifetime rule), announced / pre-construction / shelved units do not; research.fleet.include_construction false = sensitivity "
            f"(cross-check FLEET_S1_NOT_INHERITED_ITEM77.csv: {int(xdf.item77_treatment.str.startswith('counted').sum())} of {len(xdf)} GEM sub-units counted)", "construction_only", "rule", "B",
            "S4B instruction S4B-1 item 1 (decision 77)", "research/06_scope_redesign/p1_step1_20261015/evidence/S1_SELECTED_ASSET_SURVIVAL_2050.json SurvivalStatus", s1_sha, decision_ref="77")
    reg.add("fleet_construction_no_start_year_counted", f"Decision 77: {len(con_add)} GEM units under construction without a start year ({con_add.capacity_mw.sum():,.0f} MW) counted as 2050 stock (start >= 2026 from the 2026-09 status; "
            "every S1 lifetime >= 25 a keeps them in service); nearest-node mapping and parameters as S4A-2; waste units skipped", float(con_add.capacity_mw.sum()), "MW", "B", "GEM GIPT 2026-09",
            "FLEET_ADDITIONS_CONSTRUCTION_NO_START_YEAR_2050.csv", src, decision_ref="77")
    reg.add("fleet_operating_no_start_year_unresolved", f"Decision 77: {len(opr_out)} operating GEM units without a start year ({opr_out['Capacity (MW)'].sum():,.0f} MW) stay UNRESOLVED and are not counted", float(opr_out["Capacity (MW)"].sum()), "MW", "B",
            "GEM GIPT 2026-09", "FLEET_UNRESOLVED_OPERATING_NO_START_YEAR.csv", src, decision_ref="77", status="REFERENCE_ONLY")
    reg.add("fleet_remove_not_operating_gipt2026", f"Decision 77: {len(rev)} network stock units ({rev.capacity_mw.sum():,.1f} MW) that GIPT 2026-09 lists as cancelled / mothballed / retired / absent are removed from the 2050 stock "
            "(research.fleet.remove_not_operating_gipt2026, data correction); identities kept in FLEET_REMOVED_NOT_OPERATING_GIPT2026.csv", float(rev.capacity_mw.sum()), "MW", "B", "GEM GIPT 2026-09 reverse check (S4A-2 section 2.3)",
            "FLEET_REMOVED_NOT_OPERATING_GIPT2026.csv", src, decision_ref="77")
    for r in rev.itertuples():
        reg.add(f"fleet_removed_{r.identity.replace(':', '_')}", f"Removed from the 2050 stock (data correction, decision 77): {r.identity} in {r.component} ({r.model_class}, {r.country}), {r.removal_reason}", float(r.capacity_mw), "MW", "B",
                str(r.source).split("/")[-1], "FLEET_REMOVED_NOT_OPERATING_GIPT2026.csv", src, country=str(r.country), node=str(r.node), decision_ref="77", status="REFERENCE_ONLY")
    waste = con_add[con_add.model_class == "waste existing"]
    reg.add("fleet_waste_to_energy_skipped_s4b", f"Waste-to-energy units stay skipped (no waste fuel pathway in the model; limitation): S4A-2 100 MW plus {waste.capacity_mw.sum():,.0f} MW under construction without a start year", None, "MW", "C",
            "S4B instruction S4B-1 item 4", "FLEET_ADDITIONS_2050.csv / FLEET_ADDITIONS_CONSTRUCTION_NO_START_YEAR_2050.csv (model_class waste existing)", src, decision_ref="77", status="DATA_PENDING")
    reg.write(REG_DIR / "fragments" / "s4b_1.csv")
    ev = dict(script=SCRIPT, construction_no_start=dict(units=int(len(con_add)), mw=float(con_add.capacity_mw.sum()), by_class=con_add.groupby("model_class").capacity_mw.sum().round(1).to_dict(),
                                                        by_country=con_add.groupby("country").capacity_mw.sum().round(1).to_dict(), node_distance_km=dict(median=float(con_add.node_distance_km.median()), max=float(con_add.node_distance_km.max()))),
              operating_no_start=dict(units=int(len(opr_out)), mw=float(opr_out["Capacity (MW)"].sum()), by_type=opr_out.groupby("Type")["Capacity (MW)"].sum().round(1).to_dict()),
              removed=dict(units=int(len(rev)), mw=float(rev.capacity_mw.sum()), by_status=rev.groupby("gipt_status_2026").capacity_mw.sum().to_dict()),
              s1_not_inherited=dict(records=int(len(ni)), mw=float(ni.OriginalCapacity.sum()), sub_units=int(len(xdf)), treatment=xdf.item77_treatment.value_counts().to_dict(),
                                    counted_mw=float(xdf[xdf.item77_treatment.str.startswith("counted")].gipt_capacity_mw.sum())),
              stock_totals_mw=dict(before=float(tab.before_s4a_mw.sum()), added=float(tab.added_construction_no_start_mw.sum()), removed=float(tab.removed_not_operating_mw.sum()), after=float(tab.after_s4b1_mw.sum())))
    write_json(ev, OUT / "FLEET_S4B1_EVIDENCE.json")
    print(json.dumps(ev, indent=1, default=float)[:3000])


if __name__ == "__main__":
    main()
