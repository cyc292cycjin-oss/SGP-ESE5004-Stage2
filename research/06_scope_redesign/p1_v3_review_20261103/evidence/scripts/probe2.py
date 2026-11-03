"""Independent review probe 2 (read-only): demand conservation vs tables, cost table / annuity, registry parameters, EV and ship parameters."""
import json, glob, logging
import numpy as np, pandas as pd, pypsa
logging.disable(logging.WARNING)
WT = "/home/jin/wt_v3_review"
OUT = "/home/jin/v3rev/out/probe2.json"
R = {}
n = pypsa.Network("/home/jin/v3rev/nets/dmax/integrated_365_24h_unsolved.nc")
w = n.snapshot_weightings.generators
p = n.get_switchable_as_dense("Load", "p_set").mul(w, axis=0).sum() / 1e6
ident = n.meta.get("demand_identity", {})
rows = []
for ld in n.loads.index:
    z = ident.get(ld, {})
    rows.append(dict(load=ld, country=z.get("country", str(n.loads.at[ld, "country"]) if "country" in n.loads else ""), sector=z.get("sector", ""), account=z.get("account", ""), carrier=z.get("carrier", str(n.loads.at[ld, "carrier"])), load_carrier=str(n.loads.at[ld, "carrier"]), twh=float(p.get(ld, 0.0)), bus=str(n.loads.at[ld, "bus"])))
L = pd.DataFrame(rows)
L["bus_country"] = L.bus.map(n.buses.country.astype(str))
R["loads_without_identity"] = int((L.sector == "").sum())
R["identity_country_vs_bus_country_mismatch"] = L[(L.country != L.bus_country) & (L.country != "ASEAN")][["load", "country", "bus_country"]].head(20).to_dict("records")
R["asean_tag_loads"] = dict(n=int((L.country == "ASEAN").sum()), twh=float(L[L.country == "ASEAN"].twh.sum()), by_bus_country={k: float(v) for k, v in L[L.country == "ASEAN"].groupby("bus_country").twh.sum().items()}, sectors=L[L.country == "ASEAN"].sector.value_counts().to_dict())
by_cs = L.groupby(["country", "sector"]).twh.sum()
R["twh_by_country_sector"] = {f"{a}|{b}": float(v) for (a, b), v in by_cs.items()}
R["twh_by_sector"] = {k: float(v) for k, v in L.groupby("sector").twh.sum().items()}
R["twh_total"] = float(L.twh.sum())
# v3 deliverable table
cands = glob.glob(f"{WT}/research/06_scope_redesign/p1_v3_20261102/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v3.csv")
if cands:
    t = pd.read_csv(cands[0]); R["v3_table_columns"] = list(t.columns); R["v3_table_head"] = t.head(5).to_dict("records")
    R["v3_table_total_twh"] = float(t.twh.sum()) if "twh" in t else None
    if {"country", "sector", "twh"} <= set(t.columns):
        tt = t.groupby(["country", "sector"]).twh.sum()
        cmp = pd.DataFrame(dict(table=tt, network=by_cs)).fillna(0.0)
        cmp["diff"] = cmp.network - cmp.table
        R["v3_table_vs_network_by_country_sector"] = {f"{a}|{b}": dict(table=float(r.table), network=float(r.network), diff=float(r["diff"])) for (a, b), r in cmp.iterrows() if abs(r["diff"]) > 1e-6}
        R["v3_table_vs_network_max_abs_diff_twh"] = float(cmp["diff"].abs().max())
        R["v3_table_vs_network_sector_sums"] = {s: dict(table=float(cmp.xs(s, level=1).table.sum()), network=float(cmp.xs(s, level=1).network.sum())) for s in sorted(set(cmp.index.get_level_values(1)))}
# anchor / v2 tables
for pat, key in ((f"{WT}/research_inputs/**/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", "anchor"), (f"{WT}/research_inputs/**/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v2.csv", "v2"), (f"{WT}/research_inputs/**/INDUSTRY_2050_SUMMARY_V3.csv", "ind_v3"), (f"{WT}/research_inputs/**/INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv", "ind_v2")):
    f = glob.glob(pat, recursive=True)
    R[f"{key}_files"] = f
    if f:
        t = pd.read_csv(f[0]); R[f"{key}_columns"] = list(t.columns); R[f"{key}_head"] = t.head(4).astype(str).to_dict("records")
        if key.startswith("ind"):
            pe = [c for c in t.columns if c.startswith("pe_")]
            R[f"{key}_pe_total_twh"] = float(t[pe].sum().sum() / 1e6) if pe else None
            R[f"{key}_pe_by_country_twh"] = {str(r[t.columns[0]]): float(sum(r[c] for c in pe)) / 1e6 for _, r in t.iterrows()} if pe else None
# industry sector check in network
ind = L[L.sector == "Industry"]
R["industry_twh_by_country_network"] = {k: float(v) for k, v in ind.groupby("country").twh.sum().items()}
R["industry_twh_by_carrier_network"] = {k: float(v) for k, v in ind.groupby("load_carrier").twh.sum().items()}
R["industry_total_twh_network"] = float(ind.twh.sum())
# EV / transport
ev = L[L.load_carrier == "land transport EV"]
R["ev_twh_by_country"] = {k: float(v) for k, v in ev.groupby("country").twh.sum().items()}; R["ev_total_twh"] = float(ev.twh.sum())
# registry rows
reg = pd.read_csv(f"{WT}/research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
keys = [k for k in reg.index if k.startswith("share_bev") or k.startswith("ev_") or k.startswith("liquid_ship") or k.startswith("share_transport_electric") or k.startswith("fx_usd") or k.startswith("co2_land_transport_rail") or k.startswith("fuel_price_gas_STEPS") or k.startswith("fuel_price_oil_STEPS") or k.startswith("fuel_price_coal_STEPS")]
R["registry_rows"] = {k: dict(value=reg.at[k, "value"], unit=reg.at[k, "unit"] if "unit" in reg else None, tier=reg.at[k, "tier"] if "tier" in reg else None, status=reg.at[k, "status"] if "status" in reg else None, source=str(reg.at[k, "source"])[:160] if "source" in reg else None) for k in keys}
R["registry_columns"] = list(reg.columns)
# cost table
c = pd.read_csv("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_dmax/networks/integrated_costs_active_research.csv", index_col=0)
R["costs_columns"] = list(c.columns)
def annuity(nn, r):
    return r / (1.0 - 1.0 / (1.0 + r) ** nn) if r > 0 else 1.0 / nn
chk = {}
for tech in ["solar", "onwind", "offwind", "battery storage", "battery inverter", "electrolysis", "H2 (g) pipeline", "HVAC overhead", "HVDC overhead", "HVDC submarine", "HVDC inverter pair", "OCGT", "CCGT", "gas", "oil", "coal", "lignite", "nuclear", "nuclear SMR", "Fischer-Tropsch", "methanolisation", "Haber-Bosch", "MeOH transport ship", "FT fuel transport ship", "NH3 (l) transport ship", "General liquid hydrocarbon storage (product)", "NH3 (l) storage tank incl. liquefaction", "direct air capture", "CO2 pipeline", "hydro", "ror", "biomass", "solar-rooftop", "home battery storage", "decentral air-sourced heat pump", "geothermal"]:
    if tech in c.index:
        r = c.loc[tech]
        rec = {k: (float(r[k]) if k in r and pd.notna(r[k]) else None) for k in ("investment", "FOM", "VOM", "lifetime", "discount rate", "fixed", "marginal_cost", "efficiency", "fuel", "CO2 intensity")}
        if rec["investment"] is not None and rec["lifetime"] and rec["discount rate"] is not None:
            rec["fixed_recomputed"] = (annuity(rec["lifetime"], rec["discount rate"]) + (rec["FOM"] or 0.0) / 100.0) * rec["investment"]
            rec["fixed_rel_dev"] = (rec["fixed"] - rec["fixed_recomputed"]) / rec["fixed_recomputed"] if rec["fixed"] else None
        chk[tech] = rec
R["cost_rows"] = chk
R["discount_rates"] = {str(k): int(v) for k, v in c["discount rate"].round(4).value_counts().items()} if "discount rate" in c else None
R["lifetime_range"] = [float(c.lifetime.min()), float(c.lifetime.max())] if "lifetime" in c else None
# capital_cost of network components vs costs 'fixed' for sample carriers
samp = {}
for car, tech in (("solar", "solar"), ("onwind", "onwind"), ("battery", "battery storage"), ("H2 Electrolysis", "electrolysis"), ("OCGT", "OCGT"), ("CCGT", "CCGT")):
    for typ in ("Generator", "Link", "Store", "StorageUnit"):
        d = n.df(typ); g = d[(d.carrier == car) & d[("e_nom_extendable" if typ == "Store" else "p_nom_extendable")].astype(bool)]
        if len(g):
            samp[f"{typ}:{car}"] = dict(n=int(len(g)), capital_cost_unique=sorted(set(np.round(g.capital_cost.to_numpy(), 2)))[:6], marginal_cost_unique=sorted(set(np.round(g.marginal_cost.to_numpy(), 3)))[:6], cost_fixed=float(c.at[tech, "fixed"]) if tech in c.index else None, cost_marginal=float(c.at[tech, "marginal_cost"]) if tech in c.index else None)
R["network_capital_cost_samples"] = samp
# existing FOM constants
R["existing_fom"] = dict(meta_existing_annual_fixed_om_eur=n.meta.get("existing_annual_fixed_om_eur"), sum_component_cols={t: float(pd.to_numeric(n.df(t)["existing_annual_fixed_om_eur"], errors="coerce").fillna(0.0).sum()) for t in ("Generator", "Link", "StorageUnit", "Store") if "existing_annual_fixed_om_eur" in n.df(t)}, xb_fom=n.meta.get("existing_cross_border_fom_eur"), xb_rows=len(n.meta.get("existing_cross_border_fom_ledger", [])))
# marginal costs of fuel supply
for car in ("gas", "oil", "coal", "lignite", "oil import", "methanol import", "ammonia import", "FT fuel import", "LNG import", "H2 import", "gas production", "uranium", "biomass", "solid biomass"):
    g = n.generators[n.generators.carrier == car]
    if len(g):
        R.setdefault("fuel_supply_generators", {})[car] = dict(n=int(len(g)), marginal_cost_unique=sorted(set(np.round(g.marginal_cost.to_numpy(), 3)))[:6], p_nom_ext=int(g.p_nom_extendable.sum()), p_nom_max_inf=int(np.isinf(g.p_nom_max).sum()), countries=sorted(set(g.country.astype(str)))[:12] if "country" in g else None)
# ship links
sh = n.links[n.links.carrier.isin(["oil non-fossil ship", "methanol ship", "ammonia ship", "liquid transit rail"])]
R["ship_links"] = {car: dict(n=int(len(g)), mc_range=[float(g.marginal_cost.min()), float(g.marginal_cost.max())], eff_range=[float(g.efficiency.min()), float(g.efficiency.max())], p_nom=sorted(set(np.round(g.p_nom.to_numpy(), 1)))[:4], p_min_pu=sorted(set(g.p_min_pu)), route_km_range=[float(g.route_km.min()), float(g.route_km.max())] if "route_km" in g else None) for car, g in sh.groupby("carrier")}
# national liquid import generators and prices
imp = n.generators[n.generators.carrier.astype(str).str.contains("import")]
R["import_generators"] = {car: dict(n=int(len(g)), mc=sorted(set(np.round(g.marginal_cost.to_numpy(), 3))), buses=sorted(set(g.bus))[:3]) for car, g in imp.groupby("carrier")}
# DAC / sequestration caps
R["co2_storage_caps"] = n.meta.get("research_co2_storage")
R["research_carbon"] = n.meta.get("research_carbon")
R["research_bunkers_summary"] = {k: v for k, v in (n.meta.get("research_bunkers") or {}).items() if k in ("mode", "notes", "loads_moved", "by_country", "account")}
R["research_biomass"] = {k: (v if not isinstance(v, (list, dict)) or len(json.dumps(v)) < 3000 else "...") for k, v in (n.meta.get("research_biomass") or {}).items()}
json.dump(R, open(OUT, "w"), indent=1, default=str)
print("done")
