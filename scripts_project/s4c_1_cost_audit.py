"""S4C-1 item 3-4 (decision 82): audit of every expandable component's capital cost against the decision-50 cost layer.

For each extendable Generator / Link / StorageUnit / Store / Line of a built network, the expected annualised capital cost is recomputed
from the active cost table of the same build (costs_active_research.csv: technology-data v0.15.0 2050 EUR2020 + the appended AEO8 rows)
with the formula of the code that builds the component (code reference per rule), and compared with the network value
(|rel| <= 1e-9 or 1e-6 EUR). Status:
  COST_LAYER           value = cost-layer formula
  EXCEPTION_CONFIRMED  confirmed exception: SMR / geothermal AEO8 (decisions 46, 52), LNG terminal (72), import terminals (17),
                       CO2 sequestration cost (PyPSA-Eur config value, no technology-data row; S2, decisions 28-30)
  NO_CAPEX_BY_DESIGN   capital cost 0 by construction (import / supply generators, accounting and distribution links, dischargers)
  UNRESOLVED           no rule or value differs -> stop and report (S4C-1 item 3)
Before / after: the same audit keys on the S4C-0 build (before S4C-1) give the unit-cost comparison per technology and country.

    python scripts_project/s4c_1_cost_audit.py --after results_project/s4c/build_s4c1/integrated --before results_project/s4c/build_s4c0/integrated --output <dir>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

ROOT = Path(__file__).resolve().parents[1]


def rules(n, c, cfg):
    """carrier rule: (component, carrier) -> (expected function of the component row, status, cost rows, code reference, decision)."""
    f = lambda t: float(c.at[t, "fixed"]); e = lambda t: float(c.at[t, "efficiency"]); p = lambda t, k: float(c.at[t, k])
    ef_gas, ef_bio = p("gas", "CO2 intensity"), p("solid biomass", "CO2 intensity")
    cc = float(cfg["sector"]["cc_fraction"]); R = cfg["research"]
    cap_row = "biomass boiler capture" if "biomass boiler capture" in c.index and np.isfinite(c.at["biomass boiler capture", "fixed"]) else "biomass CHP capture"
    from s4a_layers import offshore_distance_table
    dist, _ = offshore_distance_table(cfg, ROOT)   # M08a A6.2: the class table of the active offshore rule
    sub = pd.read_csv(ROOT / R["corridors"]["subsea_table"]); col = {"zero": "share_zero", "geometric_all": "share_geometric_all", "landmass_nonland": "share_landmass_nonland"}[R["corridors"]["subsea_share"]]
    from s4c_layers import bus_location, _class_of
    stab = {(r.loc0, r.loc1): float(getattr(r, col)) for r in sub.itertuples()}

    def s(z):
        k = tuple(sorted((bus_location(n, z.bus0), bus_location(n, z.bus1))))
        return 0.0 if k[0] == k[1] else stab[k]

    def offw(car):
        def fn(name, z):
            d = dist.loc[(car, str(z.bus), _class_of(name))]
            return f("offwind-float" if car == "offwind-float" else "offwind") + f(f"{car}-station") + float(d.line_length_factor) * (float(d.average_distance_km) * f(f"{car}-connection-submarine") + float(d.landfall_km) * f(f"{car}-connection-underground"))
        return fn

    def pipe(on, sb):
        return lambda name, z: float(z.length) * ((1 - s(z)) * f(on) + s(z) * f(sb))
    mm = float(R["s3"]["ammonia_methanol"]["MWh_MeOH_per_MWh_H2"])
    L, S4C1, S2L, S3L, S4BL = "COST_LAYER", "s4c_layers.apply_cost_layer_s4c1", "s2_layers", "s3_layers", "s4b_layers.apply_sector_alignment"
    G, K, SU, ST, LN = "Generator", "Link", "StorageUnit", "Store", "Line"
    lng = float(R["s3"]["gas"]["lng_expansion_capital_cost_eur_per_mw_a"]) * (1 + float(R["s3"]["gas"].get("lng_expansion_cost_sensitivity", 0.0)))
    return {
        (G, "onwind"): (lambda nm, z: f("onwind"), L, "onwind", S4C1, "50, 82"),
        (G, "solar"): (lambda nm, z: f("solar-utility"), L, "solar-utility", S4C1, "50, 82"),
        (G, "solar rooftop"): (lambda nm, z: f("solar-rooftop"), L, "solar-rooftop", S4C1, "50, 82"),
        (G, "offwind-ac"): (offw("offwind-ac"), L, "offwind + offwind-ac-station + 1.25 x (d x -connection-submarine + 20 km x -connection-underground)", S4C1 + "; PyPSA-Eur v2025.07.0 add_electricity.py 541, 555-576", "50, 82"),
        (G, "offwind-dc"): (offw("offwind-dc"), L, "offwind + offwind-dc-station + 1.25 x (d x -connection-submarine + 30 km x -connection-underground)", S4C1 + "; PyPSA-Eur v2025.07.0 add_electricity.py 541, 555-576", "50, 82"),
        (G, "offwind-float"): (offw("offwind-float"), L, "offwind-float + offwind-float-station + 1.25 x (d x -connection-submarine + 40 km x -connection-underground)", S4C1 + "; M08a A6.2; PyPSA-Eur v2025.07.0 config lines 239-260", "129, 131"),
        (G, "nuclear"): (lambda nm, z: f("nuclear"), L, "nuclear", "s1_candidates.add_nuclear", "38, 50"),
        (G, "nuclear SMR"): (lambda nm, z: f("nuclear SMR"), "EXCEPTION_CONFIRMED", "nuclear SMR (appended AEO8 D.15 row)", "s2_costs.build_research_costs; s1_candidates.add_nuclear", "46"),
        (G, "geothermal"): (lambda nm, z: f("geothermal"), "EXCEPTION_CONFIRMED", "geothermal (appended AEO8 D.15 row)", "s2_costs.build_research_costs; s1_candidates.add_site_candidates", "46, 52"),
        (G, "ror"): (lambda nm, z: f("ror"), L, "ror", "s1_candidates.add_site_candidates", "50, 78"),
        (G, "LNG import"): (lambda nm, z: lng, "EXCEPTION_CONFIRMED", "PyPSA-Eur import-branch terminal constant 7,018 EUR/MW/a", "s3_layers.add_gas_network", "72"),
        (G, "H2 import"): (lambda nm, z: float(R["s3"]["imports"]["h2_terminal_capital_cost_eur_per_mw_a"]), "EXCEPTION_CONFIRMED", "PyPSA-Eur import-branch liquid-H2 terminal 7,018 x 1.2", "s3_layers.add_imports", "17"),
        (SU, "hydro"): (lambda nm, z: f("hydro"), L, "hydro", "s1_candidates.add_site_candidates; s4b_candidates", "50, 78"),
        (SU, "PHS"): (lambda nm, z: f("PHS"), L, "PHS", "s1_candidates.add_site_candidates; s4b_candidates", "50, 78"),
        (K, "CCGT"): (lambda nm, z: f("CCGT") * e("CCGT"), L, "CCGT x efficiency", "build_research_assets.build_fragment", "50"),
        (K, "OCGT"): (lambda nm, z: f("OCGT") * e("OCGT"), L, "OCGT x efficiency", "build_research_assets.build_fragment", "50"),
        (K, "OCGT methanol"): (lambda nm, z: f("OCGT") * e("OCGT"), L, "OCGT x efficiency", S3L + ".add_ammonia_methanol", "44, 50"),
        (K, "H2 turbine"): (lambda nm, z: f("OCGT") * e("OCGT"), L, "OCGT x efficiency (H2 turbine proxy, decision 42)", "sector_adapter.add_hydrogen", "42, 50"),
        (K, "H2 Fuel Cell"): (lambda nm, z: f("fuel cell") * e("fuel cell"), L, "fuel cell x efficiency", "sector_adapter.add_hydrogen", "50"),
        (K, "H2 Electrolysis"): (lambda nm, z: f("electrolysis"), L, "electrolysis", "sector_adapter.add_hydrogen", "50"),
        (K, "SMR"): (lambda nm, z: f("SMR"), L, "SMR", "build_research_assets.build_fragment", "50"),
        (K, "SMR CC"): (lambda nm, z: f("SMR CC"), L, "SMR CC", "build_research_assets.build_fragment", "50"),
        (K, "CCGT CC"): (lambda nm, z: f("CCGT") * e("CCGT") + f("biomass CHP capture") * ef_gas * cc, L, "CCGT x eff + biomass CHP capture x EF_gas x cc", S2L + ".add_co2_layer", "50"),
        (K, "Fischer-Tropsch"): (lambda nm, z: f("Fischer-Tropsch") * e("Fischer-Tropsch"), L, "Fischer-Tropsch x efficiency", "build_research_assets.build_fragment", "50"),
        (K, "Sabatier"): (lambda nm, z: f("methanation") * e("methanation"), L, "methanation x efficiency", S4BL, "50, 70"),
        (K, "methanolisation"): (lambda nm, z: f("methanolisation") * mm, L, "methanolisation x MWh_MeOH_per_MWh_H2", S3L + ".add_ammonia_methanol", "44, 50"),
        (K, "Haber-Bosch"): (lambda nm, z: f("Haber-Bosch") / p("Haber-Bosch", "electricity-input"), L, "Haber-Bosch / electricity-input", S3L + ".add_ammonia_methanol", "44, 50"),
        (K, "ammonia cracker"): (lambda nm, z: f("Ammonia cracker") / p("Ammonia cracker", "ammonia-input"), L, "Ammonia cracker / ammonia-input", S3L + ".add_ammonia_methanol", "44, 50"),
        (K, "DAC"): (lambda nm, z: f("direct air capture") * float(z.efficiency), L, "direct air capture x t/MWh_el", S2L + ".add_co2_layer", "11, 50"),
        (K, "BtL"): (lambda nm, z: f("BtL") * e("BtL"), L, "BtL x efficiency (decision 86 a)", S2L + ".add_biomass_layer", "50, 86"),
        (K, "electrobiofuels"): (lambda nm, z: f("BtL") * e("BtL") + p("BtL", "C stored") * f("Fischer-Tropsch") * e("Fischer-Tropsch"), L, "BtL x eff + C stored x FT x eff", S4BL, "50, 70"),
        (K, "biomass EOP"): (lambda nm, z: f("biomass EOP") * e("biomass EOP"), L, "biomass EOP x efficiency", S2L + ".add_biomass_layer", "50"),
        (K, "biomass EOP CC"): (lambda nm, z: f("biomass EOP") * e("biomass EOP") + f("biomass CHP capture") * ef_bio * cc, L, "EOP x eff + capture x EF_bio x cc", S2L + ".add_biomass_layer", "50"),
        (K, "biogas upgrading"): (lambda nm, z: f("biogas upgrading"), L, "biogas upgrading", S2L + ".add_biomass_layer", "50"),
        (K, "biomass-to-methanol"): (lambda nm, z: f("biomass-to-methanol") / e("biomass-to-methanol"), L, "biomass-to-methanol / efficiency", S3L + ".add_ammonia_methanol", "44, 50"),
        (K, "industry electric boiler"): (lambda nm, z: f("electric boiler steam") * e("electric boiler steam"), L, "electric boiler steam x eff", S2L + ".add_industrial_heat", "50"),
        (K, "industry heat pump"): (lambda nm, z: f("industrial heat pump high temperature") * e("industrial heat pump high temperature"), L, "industrial heat pump high temperature x COP", S2L + ".add_industrial_heat", "50"),
        (K, "industry gas boiler"): (lambda nm, z: f("gas boiler steam") * e("gas boiler steam"), L, "gas boiler steam x eff", S2L + ".add_industrial_heat", "50"),
        (K, "industry biomass boiler"): (lambda nm, z: f("solid biomass boiler steam") * e("solid biomass boiler steam"), L, "solid biomass boiler steam x eff", S2L + ".add_industrial_heat", "50"),
        (K, "industry biomass boiler CC"): (lambda nm, z: f("solid biomass boiler steam") * e("solid biomass boiler steam") + f(cap_row) * ef_bio * cc, L, f"solid biomass boiler steam x eff + {cap_row} x EF_bio x cc", S2L + ".add_industrial_heat", "50"),
        (K, "industry biomass CC"): (lambda nm, z: f(cap_row) * ef_bio * cc, L, f"{cap_row} x EF_bio x cc", S2L + ".add_demand_layer", "50"),
        (K, "process emissions CC"): (lambda nm, z: f("cement capture"), L, "cement capture", S2L + ".add_co2_layer", "50"),
        (K, "battery charger"): (lambda nm, z: f("battery inverter"), L, "battery inverter", S4C1, "50, 82"),
        (K, "home battery charger"): (lambda nm, z: f("home battery inverter"), L, "home battery inverter", S4C1, "50, 82"),
        (K, "electricity distribution grid"): (lambda nm, z: f("electricity distribution grid"), L, "electricity distribution grid", S4C1, "50, 82"),
        (K, "DC"): (lambda nm, z: float(z.length) * ((1 - s(z)) * f("HVDC overhead") + s(z) * f("HVDC submarine")) + f("HVDC inverter pair"), L, "length x ((1-s) HVDC overhead + s HVDC submarine) + HVDC inverter pair", S4C1 + "; PyPSA-Eur add_electricity.py 491-502", "16, 50, 82"),
        (K, "H2 pipeline"): (pipe("H2 (g) pipeline", "H2 (g) submarine pipeline"), L, "L x ((1-s) H2 (g) pipeline + s H2 (g) submarine pipeline)", S4C1, "16, 50, 59"),
        (K, "CO2 pipeline"): (pipe("CO2 pipeline", "CO2 submarine pipeline"), L, "L x ((1-s) CO2 pipeline + s CO2 submarine pipeline)", S4C1, "16, 50, 59"),
        (K, "gas pipeline"): (pipe("CH4 (g) pipeline", "CH4 (g) submarine pipeline"), L, "L x ((1-s) CH4 (g) pipeline + s CH4 (g) submarine pipeline)", S4C1, "15, 16, 50"),
        (ST, "H2 Store Tank"): (lambda nm, z: f("hydrogen storage tank type 1 including compressor"), L, "hydrogen storage tank type 1 including compressor", "sector_adapter.add_hydrogen", "50"),
        (ST, "co2 stored"): (lambda nm, z: f("CO2 storage tank"), L, "CO2 storage tank", S2L + ".add_co2_layer", "50"),
        (ST, "co2 sequestered"): (lambda nm, z: float(R["s2"]["co2"]["sequestration_cost_eur_per_t"]), "EXCEPTION_CONFIRMED", "PyPSA-Eur config sector.co2_sequestration_cost 30 EUR/t (technology-data has no sequestration-cost row)", S2L + ".add_co2_layer", "28-30"),
        (ST, "ammonia store"): (lambda nm, z: f("NH3 (l) storage tank incl. liquefaction"), L, "NH3 (l) storage tank incl. liquefaction", S3L + ".add_ammonia_methanol", "44, 50"),
        (ST, "methanol store"): (lambda nm, z: f("General liquid hydrocarbon storage (product)"), L, "General liquid hydrocarbon storage (product)", S3L + ".add_ammonia_methanol", "44, 50"),
        (ST, "battery"): (lambda nm, z: f("battery storage"), L, "battery storage", S4C1, "50, 82"),
        (ST, "home battery"): (lambda nm, z: f("home battery storage"), L, "home battery storage", S4C1, "50, 82"),
        (LN, "AC"): (lambda nm, z: float(z.length) * ((1 - s(z)) * f("HVAC overhead") + s(z) * f("HVAC submarine")), L, "length x ((1-s) HVAC overhead + s HVAC submarine)", S4C1 + "; PyPSA-Eur add_electricity.py 475-479", "16, 50, 82"),
    }


def audit(build_dir: Path, scenario: str):
    from phase4_static import config
    n = pypsa.Network(str(build_dir / f"{scenario}_2920_3h_unsolved.nc"))
    c = pd.read_csv(build_dir / "costs_active_research.csv", index_col=0)
    cfg = config(ROOT, scenario)
    rec = json.loads((build_dir / f"{scenario}_BUILD_RECEIPT.json").read_text())
    for ov in rec.get("research_config_overrides", []) or n.meta.get("research_config", {}).get("config_overrides", []):
        key, val = ov.split("=", 1); d = cfg["research"]; parts = key.split(".")
        for k in parts[:-1]:
            d = d[k]
        old = d[parts[-1]]; d[parts[-1]] = type(old)(val) if not isinstance(old, bool) else (val.lower() in ("1", "true", "yes"))
    rl = rules(n, c, cfg)
    rows, comp_rows = [], []
    for comp, attr in [("Generator", "p_nom_extendable"), ("Link", "p_nom_extendable"), ("StorageUnit", "p_nom_extendable"), ("Store", "e_nom_extendable"), ("Line", "s_nom_extendable")]:
        df = n.df(comp); ext = df[df[attr]]
        for car, x in ext.groupby("carrier"):
            key = (comp, str(car))
            if (x.capital_cost == 0).all() and key not in rl:
                rows.append(dict(component=comp, carrier=car, n=len(x), status="NO_CAPEX_BY_DESIGN", value_min=0.0, value_max=0.0, cost_rows="-", code="-", decision="-", max_abs_rel_dev=0.0))
                continue
            if key not in rl:
                rows.append(dict(component=comp, carrier=car, n=len(x), status="UNRESOLVED", value_min=float(x.capital_cost.min()), value_max=float(x.capital_cost.max()), cost_rows="no rule",
                                 code="-", decision="-", max_abs_rel_dev=np.nan)); continue
            fn, status, crow, code, dec = rl[key]
            exp = pd.Series({nm: fn(nm, z) for nm, z in x.iterrows()})
            dev = (x.capital_cost - exp).abs(); rel = dev / exp.abs().clip(lower=1e-12)
            ok = (dev <= 1e-6) | (rel <= 1e-9)
            for nm in x.index:
                comp_rows.append(dict(component=comp, name=nm, carrier=car, country=str(x.at[nm, "country"]) if "country" in x else "", capital_cost=float(x.at[nm, "capital_cost"]), expected=float(exp[nm]), ok=bool(ok[nm])))
            rows.append(dict(component=comp, carrier=car, n=len(x), status=(status if ok.all() else "UNRESOLVED"), value_min=float(x.capital_cost.min()), value_max=float(x.capital_cost.max()),
                             cost_rows=crow, code=code, decision=dec, max_abs_rel_dev=float(rel.max()), mismatches=int((~ok).sum())))
    return n, pd.DataFrame(rows), pd.DataFrame(comp_rows)


def unit_costs(n):
    out = []
    for comp, attr in [("Generator", "p_nom_extendable"), ("Link", "p_nom_extendable"), ("StorageUnit", "p_nom_extendable"), ("Store", "e_nom_extendable"), ("Line", "s_nom_extendable")]:
        df = n.df(comp); ext = df[df[attr] & (df.capital_cost > 0)].copy()
        if comp == "Line":
            ext["country"] = n.buses.loc[ext.bus0, "country"].values
        for (car, cty), x in ext.groupby(["carrier", "country"]):
            per_km = (x.capital_cost / x.length).mean() if "length" in x and (x.length > 0).all() and car in ("AC", "DC", "H2 pipeline", "CO2 pipeline", "gas pipeline") else np.nan
            out.append(dict(component=comp, carrier=car, country=cty, n=len(x), mean=float(x.capital_cost.mean()), min=float(x.capital_cost.min()), max=float(x.capital_cost.max()), mean_per_km=per_km))
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--after", type=Path, required=True); ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("--scenario", default="integrated"); ap.add_argument("--output", type=Path, required=True); a = ap.parse_args()
    import sys; sys.path.insert(0, str(ROOT / "scripts_project"))
    n, tab, comp = audit(a.after, a.scenario)
    nb = pypsa.Network(str(a.before / f"{a.scenario}_2920_3h_unsolved.nc"))
    ua, ub = unit_costs(n), unit_costs(nb)
    ba = ub.merge(ua, on=["component", "carrier", "country"], how="outer", suffixes=("_before", "_after"))
    ba["ratio_after_before"] = ba.mean_after / ba.mean_before
    by_car = ba.groupby(["component", "carrier"]).apply(lambda x: pd.Series(dict(n=x.n_after.sum(), before_mean=(x.mean_before * x.n_before).sum() / x.n_before.sum() if x.n_before.sum() else np.nan,
                                                                                 after_mean=(x.mean_after * x.n_after).sum() / x.n_after.sum() if x.n_after.sum() else np.nan))).reset_index()
    by_car["ratio"] = by_car.after_mean / by_car.before_mean
    tab = tab.merge(by_car[["component", "carrier", "before_mean", "after_mean", "ratio"]], on=["component", "carrier"], how="left")
    a.output.mkdir(parents=True, exist_ok=True)
    # offshore wind connection cost per generator (user request 2026-10-16: distance distribution and connection share of the offshore cost)
    from s4c_layers import _class_of
    from phase4_static import config
    cfg = config(ROOT, a.scenario); c = pd.read_csv(a.after / "costs_active_research.csv", index_col=0)
    from s4a_layers import offshore_distance_table
    dist, _ = offshore_distance_table(cfg, ROOT)
    ow = []
    for name, z in n.generators[n.generators.carrier.isin(["offwind-ac", "offwind-dc", "offwind-float"]) & n.generators.p_nom_extendable].iterrows():
        car = z.carrier; d = dist.loc[(car, str(z.bus), _class_of(name))]; turbine = "offwind-float" if car == "offwind-float" else "offwind"
        sub_c = float(d.line_length_factor) * float(d.average_distance_km) * float(c.at[f"{car}-connection-submarine", "fixed"])
        land_c = float(d.line_length_factor) * float(d.landfall_km) * float(c.at[f"{car}-connection-underground", "fixed"])
        ow.append(dict(generator=name, tech=car, node=str(z.bus), country=str(n.buses.at[z.bus, "country"]), cls=_class_of(name), p_nom_max_mw=float(z.p_nom_max), distance_km=float(d.average_distance_km),
                       distance_basis=str(d.get("basis", "LAYOUT")), turbine_eur_per_mw_a=float(c.at[turbine, "fixed"]), station_eur_per_mw_a=float(c.at[f"{car}-station", "fixed"]), submarine_eur_per_mw_a=sub_c,
                       landfall_eur_per_mw_a=land_c, capital_cost=float(z.capital_cost), connection_share=(sub_c + land_c) / float(z.capital_cost)))
    owd = pd.DataFrame(ow); owd.to_csv(a.output / "OFFWIND_CONNECTION_COST_S4C1.csv", index=False)
    tab.to_csv(a.output / "COST_AUDIT_S4C1.csv", index=False); comp.to_csv(a.output / "COST_AUDIT_S4C1_COMPONENTS.csv", index=False)
    ba.to_csv(a.output / "COST_BEFORE_AFTER_S4C1_BY_COUNTRY.csv", index=False)
    wq = lambda x, col: float(np.average(x[col], weights=x.p_nom_max_mw.where(np.isfinite(x.p_nom_max_mw), 0.0))) if x.p_nom_max_mw.where(np.isfinite(x.p_nom_max_mw), 0.0).sum() > 0 else float(x[col].mean())
    offw = {t: dict(generators=int(len(x)), proxy_rows=int((x.distance_basis != "LAYOUT").sum()), distance_km=x.distance_km.describe().round(2).to_dict(),
                    connection_share=x.connection_share.describe().round(4).to_dict(), connection_share_potential_weighted=wq(x, "connection_share"),
                    capital_cost_potential_weighted=wq(x, "capital_cost")) for t, x in owd.groupby("tech")}
    summ = dict(carriers=int(len(tab)), by_status=tab.status.value_counts().to_dict(), unresolved=tab[tab.status == "UNRESOLVED"].to_dict("records"), offwind=offw,
                changed=by_car[(by_car.ratio - 1).abs() > 1e-9][["component", "carrier", "before_mean", "after_mean", "ratio"]].to_dict("records"))
    (a.output / "COST_AUDIT_S4C1_SUMMARY.json").write_text(json.dumps(summ, indent=1, default=str) + "\n")
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200); pd.set_option("display.max_colwidth", 60)
    print(tab[["component", "carrier", "n", "status", "value_min", "value_max", "before_mean", "after_mean", "ratio", "max_abs_rel_dev", "decision"]].round(4).to_string())
    print(json.dumps(dict(by_status=summ["by_status"], unresolved=len(summ["unresolved"]), offwind=offw), default=str, indent=1))


if __name__ == "__main__":
    main()
