"""Read-only diagnosis of the S4L-1 cleaned network infeasibility (no solve): per country fixed biomass demand vs pools; loaded buses without
any supply; INFEASIBILITY_DIAGNOSIS structural table; what the deleted objects fed."""
import sys, json, logging
import numpy as np, pandas as pd, pypsa
logging.getLogger("pypsa").setLevel(logging.ERROR)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 100)
k = pypsa.Network(sys.argv[1]); l = pypsa.Network(sys.argv[2]); sc = sys.argv[3]
w = k.snapshot_weightings.generators

def ports(df):
    return [c for c in df.columns if c.startswith("bus") and (c == "bus" or c[3:].isdigit())]

def suppliers(n, bus):
    s = set(n.generators.index[n.generators.bus == bus])
    L = n.links
    for col in [c for c in L if c.startswith("bus") and c[3:].isdigit() and c != "bus0"]:
        eff = "efficiency" if col == "bus1" else "efficiency" + col[3:]
        if eff in L:
            s |= set(L.index[(L[col] == bus) & (L[eff] > 0)])
    s |= set(L.index[(L.bus0 == bus) & (L.p_min_pu < 0)])
    s |= set(n.stores.index[n.stores.bus == bus]); s |= set(n.storage_units.index[n.storage_units.bus == bus])
    for t in ("Line",):
        d = n.df(t); s |= set(d.index[(d.bus0 == bus) | (d.bus1 == bus)])
    return s

for name, n in (("S4K", k), ("S4L", l)):
    pset = n.get_switchable_as_dense("Load", "p_set"); ann = pset.mul(w, axis=0).sum()
    pos = ann[ann > 0]
    nosup = [(b, float(pos[[x for x in n.loads.index[n.loads.bus == b] if x in pos.index]].sum())) for b in sorted(set(n.loads.bus[pos.index])) if not suppliers(n, b)]
    print(f"== {name} {sc}: loaded buses without any supplier:", len(nosup), nosup[:20])
    # biomass: fixed loads on solid biomass / biomass-final buses by country
    bc = n.buses.carrier
    bio_loads = n.loads[n.loads.bus.map(bc).astype(str).str.contains("biomass")]
    dem = ann.reindex(bio_loads.index).groupby(bio_loads.country.astype(str)).sum()
    pools = n.stores[n.stores.research_role == "FINITE_RESOURCE"]
    solid = pools[pools.carrier == "solid biomass"].groupby("country").e_nom.sum(); biog = pools[pools.carrier == "biogas"].groupby("country").e_nom.sum()
    T = pd.DataFrame(dict(biomass_fixed_demand_mwh=dem, solid_pool_mwh=solid, biogas_pool_mwh=biog, pools=pools.groupby("country").size())).fillna(0.0)
    print(T.round(1).to_string())
    print("biomass load carriers:", bio_loads.carrier.value_counts().to_dict(), "buses:", sorted(set(bio_loads.bus.map(bc)))[:6])
# what fed the biomass final loads: links into their buses
bc = l.buses.carrier
bl = l.loads[l.loads.bus.map(bc).astype(str).str.contains("biomass")]
for c in ("SG", "BN", "TL", "MY"):
    buses = sorted(set(bl.bus[bl.country == c]))
    for b in buses[:3]:
        sup = suppliers(l, b)
        print(c, b, "load MWh/a:", round(float(l.get_switchable_as_dense("Load", "p_set")[bl.index[bl.bus == b]].mul(w, axis=0).sum().sum()), 1), "suppliers:", sorted(sup)[:6])
        for s in sorted(sup)[:6]:
            if s in l.links.index:
                z = l.links.loc[s]; print("    link", s, z.bus0, "->", z.bus1, "p_nom", z.p_nom, "ext", z.p_nom_extendable, "eff", z.efficiency, "cap", z.capital_cost)
                print("    bus0 suppliers:", sorted(suppliers(l, z.bus0))[:8])
d = json.load(open(sys.argv[4]))
st = d.get("structural", {})
print("== INFEASIBILITY_DIAGNOSIS structural (S4L run):")
print(pd.DataFrame(st).T[["biomass_pool_mwh", "electricity_demand_mwh", "renewable_potential_mwh", "storage_cap_t", "can_store_or_export_co2", "net_zero_structurally_possible"]].to_string())
