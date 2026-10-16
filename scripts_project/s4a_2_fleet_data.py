"""S4A-2 (L15): existing-fleet coverage against the GEM Global Integrated Power Tracker (2026-09) and the units to add for 2050,
plus the gas-field node allocation from the GEM Global Oil and Gas Extraction Tracker (2026-03) (S3 report section 11 item 8).

Coverage: GEM units (operating + construction, ASEAN-11) are joined to the network existing-unit identities by GEM unit ID
(`existing_unit_components` of the built network; 745 of 748 identities are GEM IDs). 2050 service: S1 lifetime rule
(configs/powerplantmatching_config.yaml fuel_to_lifetime, geothermal 30 a from lifetime_decisions_s1.json; survives when
start year <= 2050 < start year + lifetime); units without a start year are UNRESOLVED and not added. Node: nearest AC node of
the same country (great circle). Performance parameters: technology-data v0.15.0 (grade B) -> decision-52 AEO8 rows
(geothermal, grade C) -> hydro / ROR / PHS time-series proxies from the node or country existing units (grade C).

    python scripts_project/s4a_2_fleet_data.py --network results_project/s3b/smoke/builds/integrated/integrated_2920_3h_unsolved.nc
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

from d1_common import ASEAN, REG_DIR, ROOT, SRC_DIR, Registry, read_csv, sha256, src_sha, write_csv, write_json

SCRIPT = "scripts_project/s4a_2_fleet_data.py"
OUT = ROOT / "research_inputs/fleet_v5"
GIPT = "GEM_GIPT_2026-09_ASEAN11.csv"
GOGET_FIELDS = "GEM_GOGET_2026-03_ASEAN_fields.csv"
GOGET_PROD = "GEM_GOGET_2026-03_ASEAN_gas_production.csv"
GIPT_XLSX_SHA = "1c99186c44ef7c1753b36ffee3c011041ba4723da43941286fd571d38b2db18e"
GOGET_XLSX_SHA = "10ed7bc007e47895c2f387449365c20d0a87679cb8c69be678d0cc60df4d1aa5"
ZIP_SHA = "b0d3139dbf82f58e8bd6aec6e39fcbadb154fbb5380d2f52a692be5f8ed59bf5"
# S1 lifetime rule: configs/powerplantmatching_config.yaml lines 419-432 (generic fill, decision GATE4 #A); geothermal 30 a (lifetime_decisions_s1.json, S1-3)
LIFETIME = {"Hard Coal": 45, "Lignite": 45, "Natural Gas": 40, "Oil": 40, "Hydro": 100, "Nuclear": 50, "Geothermal": 30, "Solar": 25, "Wind": 25, "Solid Biomass": 20, "Biogas": 20, "Waste": 25}
UNSD_GAS_CAP_TWH = {"BN": 109.84, "ID": 727.58, "MM": 184.90, "MY": 849.53, "PH": 43.01, "TH": 367.18, "TL": 61.29, "VN": 103.62}
MW_PER_BCM_Y_GCV, GCV_TO_NCV = 1199.0, 0.90   # s3_1_gas_data.py lines 26-27


def s1_fuel(row):
    t, tech, fuel = str(row["Type"]), str(row["Technology"]).lower(), str(row["Fuel (combustion only)"]).lower()
    if t == "coal":
        return "Lignite" if "lignite" in fuel else "Hard Coal"
    if t == "oil/gas":
        if "gas" in fuel and "liquids" not in fuel.split(",")[0]:
            return "Natural Gas"
        if fuel.startswith("fossil liquids") and "gas" not in fuel:
            return "Oil"
        return "Natural Gas" if "gas" in fuel else "Oil"
    if t == "bioenergy":
        return "Biogas" if "biogas" in fuel or "landfill" in fuel else ("Waste" if "waste" in fuel or "refuse" in fuel else "Solid Biomass")
    return {"hydropower": "Hydro", "geothermal": "Geothermal", "nuclear": "Nuclear", "utility-scale solar": "Solar", "wind": "Wind"}[t]


def model_class(row):
    """Research-layer component class for an added unit."""
    f = row["s1_fuel"]; tech = str(row["Technology"]).lower()
    if f in ("Hard Coal", "Lignite", "Oil"):
        return {"Hard Coal": "coal existing", "Lignite": "lignite existing", "Oil": "oil existing"}[f]
    if f == "Natural Gas":
        return "OCGT existing" if "gas turbine" in tech or "internal combustion" in tech else "CCGT existing"
    if f == "Hydro":
        return "PHS existing" if "pumped" in tech else ("ror existing" if tech.startswith("run-of-river") else "hydro existing")
    return {"Geothermal": "geothermal existing", "Solar": "solar existing", "Wind": "offwind existing" if "offshore" in tech else "onwind existing", "Nuclear": "nuclear existing", "Solid Biomass": "biomass existing", "Biogas": "biogas existing", "Waste": "waste existing"}[f]


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0; p1, p2 = np.radians(lat1), np.radians(lat2); d = np.radians(lon2 - lon1); dp = p2 - p1
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(d / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def nearest_node(nodes, country, lat, lon):
    c = nodes[nodes.country == country]
    if not len(c) or pd.isna(lat) or pd.isna(lon):
        return None, np.nan
    d = haversine(lat, lon, c.y.values, c.x.values); i = int(np.argmin(d))
    return c.index[i], float(d[i])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--include-construction", type=int, default=1)
    a = ap.parse_args(); OUT.mkdir(parents=True, exist_ok=True)
    gem = pd.read_csv(SRC_DIR / GIPT, low_memory=False); gem_sha = src_sha(GIPT)
    n = pypsa.Network(str(a.network)); nodes = n.buses[n.buses.carrier == "AC"][["x", "y", "country"]]
    ids = pd.DataFrame(n.meta["existing_unit_components"]).T; ids["gem_id"] = ids.index.str.replace("GEM:", "", regex=False)
    ids["node_country"] = ids.node.map(n.buses.country)
    op = gem[gem.Status.isin(["operating", "construction"])].copy()
    op["s1_fuel"] = op.apply(s1_fuel, axis=1); op["lifetime"] = op.s1_fuel.map(LIFETIME)
    op["retire_year"] = op["Start year"] + op.lifetime
    op["in_network"] = op["GEM unit/phase ID"].isin(set(ids.gem_id))
    op["age_status"] = np.where(op["Start year"].isna(), "UNRESOLVED_COMMISSIONING", np.where(op.retire_year > 2050, "SURVIVES_2050", "NOT_ACTIVE_2050"))
    op["model_class"] = op.apply(model_class, axis=1)
    mapped = op.apply(lambda r: nearest_node(nodes, r.iso, r.Latitude, r.Longitude), axis=1, result_type="expand"); op["node"] = mapped[0]; op["node_distance_km"] = mapped[1]
    # reverse check: network identities whose GEM unit is no longer operating/construction in the 2026-09 tracker
    gem_status = gem.set_index("GEM unit/phase ID").Status
    ids["gipt_status_2026"] = ids.gem_id.map(gem_status).fillna("not in GIPT")
    rev = ids[~ids.gipt_status_2026.isin(["operating", "construction"])]
    # coverage table (today and 2050)
    rows = []
    for (t, c), d in op.groupby(["Type", "iso"]):
        surv = d[d.age_status == "SURVIVES_2050"]
        rows.append(dict(gem_type=t, country=c, gem_operating_mw=d.loc[d.Status == "operating", "Capacity (MW)"].sum(), gem_construction_mw=d.loc[d.Status == "construction", "Capacity (MW)"].sum(),
                         matched_in_network_mw=d.loc[d.in_network, "Capacity (MW)"].sum(), coverage_today=(d.loc[d.in_network & (d.Status == "operating"), "Capacity (MW)"].sum() / d.loc[d.Status == "operating", "Capacity (MW)"].sum()) if d.loc[d.Status == "operating", "Capacity (MW)"].sum() else np.nan,
                         survives_2050_mw=surv["Capacity (MW)"].sum(), survives_2050_in_network_mw=surv.loc[surv.in_network, "Capacity (MW)"].sum(), survives_2050_missing_mw=surv.loc[~surv.in_network, "Capacity (MW)"].sum(),
                         survives_2050_missing_construction_mw=surv.loc[~surv.in_network & (surv.Status == "construction"), "Capacity (MW)"].sum(), unresolved_mw=d.loc[d.age_status == "UNRESOLVED_COMMISSIONING", "Capacity (MW)"].sum(), unresolved_units=int((d.age_status == "UNRESOLVED_COMMISSIONING").sum())))
    cov = pd.DataFrame(rows).round(1); write_csv(cov.to_dict("records"), OUT / "FLEET_COVERAGE_GEM_2026_BY_COUNTRY_TYPE.csv", list(cov.columns))
    # additions: surviving, not in network, resolved age, (construction optional)
    add = op[(op.age_status == "SURVIVES_2050") & ~op.in_network & op.node.notna()].copy()
    if not a.include_construction:
        add = add[add.Status == "operating"]
    add["param_source"] = add.model_class.map(lambda k: "technology-data v0.15.0 (grade B)" if k.split()[0] in ("coal", "lignite", "oil", "CCGT", "OCGT", "solar", "onwind", "offwind", "biomass", "biogas", "waste", "nuclear", "hydro", "ror", "PHS") else "AEO8 decision 52 (grade C)")
    add.loc[add.model_class.isin(["hydro existing", "ror existing", "PHS existing"]), "param_source"] = "technology-data v0.15.0 FOM/efficiency (B); inflow / availability / duration proxy from node or country existing units (C)"
    add.loc[add.model_class.isin(["solar existing", "onwind existing", "offwind existing"]), "param_source"] = "technology-data v0.15.0 FOM (B); availability = node candidate profile (research.renewable variant)"
    add.loc[add.model_class == "geothermal existing", "param_source"] = "AEO8 D.15 FOM/VOM and C.4/C.5 capacity factor 0.7194 (decision 52, grade C)"
    cols = ["GEM unit/phase ID", "GEM location ID", "Plant / Project name", "Unit / Phase name", "iso", "Type", "Technology", "Fuel (combustion only)", "Status", "Capacity (MW)", "Start year", "s1_fuel", "lifetime", "retire_year", "model_class", "Latitude", "Longitude", "Location accuracy", "node", "node_distance_km", "param_source", "GEM.Wiki URL"]
    add = add[cols].rename(columns={"GEM unit/phase ID": "gem_unit_id", "GEM location ID": "gem_location_id", "Plant / Project name": "plant", "Unit / Phase name": "unit", "iso": "country", "Capacity (MW)": "capacity_mw", "Start year": "start_year", "Fuel (combustion only)": "fuel", "Location accuracy": "location_accuracy", "GEM.Wiki URL": "gem_wiki_url"})
    add = add.sort_values(["country", "model_class", "capacity_mw"], ascending=[True, True, False])
    write_csv(add.to_dict("records"), OUT / "FLEET_ADDITIONS_2050.csv", list(add.columns))
    unres = op[(op.age_status == "UNRESOLVED_COMMISSIONING") & ~op.in_network][["GEM unit/phase ID", "Plant / Project name", "Unit / Phase name", "iso", "Type", "Technology", "Status", "Capacity (MW)", "GEM.Wiki URL"]]
    write_csv(unres.to_dict("records"), OUT / "FLEET_UNRESOLVED_START_YEAR.csv", list(unres.columns))
    write_csv(rev.reset_index().rename(columns={"index": "identity"})[["identity", "component", "capacity_mw", "node", "gipt_status_2026", "source"]].to_dict("records"), OUT / "FLEET_NETWORK_UNITS_NOT_OPERATING_IN_GIPT_2026.csv", ["identity", "component", "capacity_mw", "node", "gipt_status_2026", "source"])
    # ---- gas fields (S3 section 11 item 8) ----
    fields = pd.read_csv(SRC_DIR / GOGET_FIELDS); prod = pd.read_csv(SRC_DIR / GOGET_PROD)
    latest = prod.sort_values("Data Year").groupby("Unit ID").tail(1)
    latest = latest[(latest.Status == "operating") & (latest["Units (converted)"] == "million m³/y") & latest.Latitude.notna()].copy()
    mapped = latest.apply(lambda r: nearest_node(nodes, r.iso, r.Latitude, r.Longitude), axis=1, result_type="expand"); latest["node"] = mapped[0]; latest["node_distance_km"] = mapped[1]
    latest = latest[latest.node.notna()]
    latest["share_in_country"] = latest["Quantity (converted)"] / latest.groupby("iso")["Quantity (converted)"].transform("sum")
    gf = latest[["Unit ID", "Unit Name", "iso", "Status", "Quantity (converted)", "Data Year", "Latitude", "Longitude", "Onshore/Offshore", "node", "node_distance_km", "share_in_country"]].rename(columns={"Unit ID": "gem_unit_id", "Unit Name": "field", "iso": "country", "Quantity (converted)": "production_mcm_per_y", "Data Year": "data_year"})
    write_csv(gf.sort_values(["country", "share_in_country"], ascending=[True, False]).to_dict("records"), OUT / "GAS_FIELD_NODE_ALLOCATION.csv", list(gf.columns))
    node_share = gf.groupby(["country", "node"]).share_in_country.sum().reset_index()
    covrows = []
    for c, cap in UNSD_GAS_CAP_TWH.items():
        s = float(gf[gf.country == c].production_mcm_per_y.sum()); twh = s / 1e3 * MW_PER_BCM_Y_GCV * 8760 * GCV_TO_NCV / 1e6
        covrows.append(dict(country=c, gem_fields_with_production=int((gf.country == c).sum()), gem_latest_production_bcm=s / 1e3, gem_production_twh_ncv=twh, unsd_2019_cap_twh=cap, coverage_ratio=twh / cap if cap else np.nan,
                            nodes_with_fields=int(node_share[node_share.country == c].node.nunique()), allocation=("gem_fields" if (gf.country == c).sum() else "load_shares (no GEM field with production; DATA_PENDING)")))
    write_csv(covrows, OUT / "GAS_FIELD_COVERAGE_VS_UNSD.csv", list(covrows[0].keys()))
    write_csv(node_share.to_dict("records"), OUT / "GAS_PRODUCTION_NODE_SHARES_GEM.csv", ["country", "node", "share_in_country"])
    # ---- registry ----
    reg = Registry(SCRIPT); src = f"zip:{ZIP_SHA}|gipt:{GIPT_XLSX_SHA}|extraction:{gem_sha}"
    reg.add("fleet_gem_gipt_source", "GEM Global Integrated Power Tracker, September 2026 release (raw10 gem-data.zip), ASEAN-11 extraction (6,958 units); unit ID join with the network existing-unit identities", "Global Integrated Power September 2026.xlsx", "file", "A",
            "Global Energy Monitor, Global Integrated Power Tracker 2026-09 (CC BY 4.0)", "sheet Power facilities; extraction GEM_GIPT_2026-09_ASEAN11.csv", src, decision_ref="L15")
    reg.add("fleet_lifetime_rule_s1", "2050 in-service rule for GEM units: start year <= 2050 < start year + lifetime; lifetimes Hard Coal/Lignite 45, Natural Gas/Oil 40, Hydro 100, Nuclear 50, Geothermal 30 (S1-3), Solar/Wind 25, Solid Biomass/Biogas 20, Waste 25; no start year -> UNRESOLVED, not added",
            "S1 fuel_to_lifetime", "rule", "B", "configs/powerplantmatching_config.yaml lines 419-432; research_inputs/asset_survival/lifetime_decisions_s1.json", "fuel_to_lifetime", src, decision_ref="L15,52")
    reg.add("fleet_include_construction_units", "GEM status construction units are counted as in service in 2050 when the lifetime rule holds (S4A instruction compares operating + construction); switch research.fleet.include_construction", bool(a.include_construction), "flag", "C",
            "S4A instruction S4A-2.1", "configs/research/baseline.yaml research.fleet", src, decision_ref="L15", status="SENSITIVITY")
    tot = cov.groupby("gem_type")[["gem_operating_mw", "matched_in_network_mw", "survives_2050_mw", "survives_2050_missing_mw", "unresolved_mw"]].sum()
    for t, r in tot.iterrows():
        reg.add(f"fleet_coverage_{t.replace(' ', '_').replace('/', '_').replace('-', '_')}", f"GEM {t} ASEAN-11: operating {r.gem_operating_mw:,.0f} MW, matched in network {r.matched_in_network_mw:,.0f} MW, in service 2050 by the S1 rule {r.survives_2050_mw:,.0f} MW of which missing from the network {r.survives_2050_missing_mw:,.0f} MW, unresolved start year {r.unresolved_mw:,.0f} MW",
                float(r.survives_2050_missing_mw), "MW", "B", "GEM GIPT 2026-09 x network existing_unit_components", "FLEET_COVERAGE_GEM_2026_BY_COUNTRY_TYPE.csv", src, decision_ref="L15", status="REFERENCE_ONLY")
    for c, d in add.groupby("country"):
        reg.add(f"fleet_additions_2050_{c}", f"{c}: GEM units in service 2050 added to the network (S4A-2): " + "; ".join(f"{k} {v:,.0f} MW" for k, v in d.groupby('model_class').capacity_mw.sum().items()), float(d.capacity_mw.sum()), "MW", "B",
                "GEM GIPT 2026-09, nearest-node mapping", "FLEET_ADDITIONS_2050.csv", src, country=c, decision_ref="L15")
    for r in covrows:
        reg.add(f"gas_production_node_allocation_{r['country']}", f"{r['country']} domestic gas production node allocation (S3 section 11 item 8): {r['allocation']}; GEM GOGET 2026-03 operating fields with production {r['gem_fields_with_production']}, latest-year production {r['gem_latest_production_bcm']:.2f} bcm = {r['gem_production_twh_ncv']:.1f} TWh NCV vs UNSD 2019 cap {r['unsd_2019_cap_twh']} TWh (coverage {r['coverage_ratio']:.2f}); shares by field production, nearest node",
                r["coverage_ratio"], "ratio", ("B" if r["coverage_ratio"] >= 0.5 else "C"), "GEM Global Oil and Gas Extraction Tracker 2026-03 (raw10), field-level production data", f"GAS_FIELD_NODE_ALLOCATION.csv; xlsx:{GOGET_XLSX_SHA}", f"fields:{src_sha(GOGET_FIELDS)}|prod:{src_sha(GOGET_PROD)}",
                country=r["country"], decision_ref="43,L15", status=("REGISTERED" if r["gem_fields_with_production"] else "DATA_PENDING"),
                # grade C below 50 % coverage: range = [GEM coverage, full coverage]; the load_shares switch is the alternative allocation
                sensitivity_low=(r["coverage_ratio"] if r["coverage_ratio"] < 0.5 else None), sensitivity_high=(1.0 if r["coverage_ratio"] < 0.5 else None))
    reg.write(REG_DIR / "fragments" / "fleet_s4a.csv")
    write_json(dict(script=SCRIPT, sources=dict(gipt_csv=gem_sha, goget_fields=src_sha(GOGET_FIELDS), goget_prod=src_sha(GOGET_PROD)), include_construction=bool(a.include_construction),
                    coverage_totals=tot.round(1).to_dict("index"), additions_by_class=add.groupby("model_class").capacity_mw.sum().round(1).to_dict(), additions_units=int(len(add)),
                    reverse_check_units=int(len(rev)), reverse_check_mw=float(rev.capacity_mw.sum()), gas_coverage=covrows), OUT / "FLEET_S4A_EVIDENCE.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(tot.round(0).to_string()); print("additions by class MW"); print(add.groupby(["model_class"]).capacity_mw.sum().round(0).to_string()); print("by country"); print(add.groupby(["country", "model_class"]).capacity_mw.sum().unstack(fill_value=0).round(0).to_string())
    print("reverse check: network units not operating/construction in GIPT 2026:", len(rev), round(float(rev.capacity_mw.sum())), "MW"); print(rev.gipt_status_2026.value_counts().to_dict())
    print(pd.DataFrame(covrows).round(2).to_string())


if __name__ == "__main__":
    main()
