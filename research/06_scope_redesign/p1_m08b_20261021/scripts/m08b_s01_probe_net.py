"""M08b supplement 01 probe (read-only): heat-band loads / links and the ledger anchor checks of a built network."""
import sys
import logging
import pandas as pd
import pypsa

logging.getLogger("pypsa").setLevel(logging.ERROR)
n = pypsa.Network(sys.argv[1])
w = n.snapshot_weightings.generators
e = n.get_switchable_as_dense("Load", "p_set").mul(w, axis=0).sum()
L = n.loads.assign(mwh=e)
heat = L[L.carrier.str.startswith("industry heat")].groupby("carrier").mwh.sum() / 1e6
print("heat loads TWh:", heat.round(2).to_dict())
for bc in ["industry heat", "industry heat medium A", "industry heat medium B", "industry heat high"]:
    buses = n.buses.index[n.buses.carrier == bc]
    lk = n.links[n.links.bus1.isin(buses)]
    print(bc, "buses", len(buses), "links", lk.groupby("carrier").size().to_dict(), "inputs", sorted(set(n.buses.carrier.reindex(lk.bus0).fillna("?"))))
led = n.meta["s2_demand_ledger"]
chk = pd.DataFrame(led["anchors"]["checks"]).set_index("country")
cols = [c for c in chk.columns if "fuel" in c]
print((chk[cols] / 1e6).round(3).to_string())
ov = led["industry"]["biomass_overflow"]
print("overflow:", {c: (round(v["overflow_industry_mwh"] / 1e6, 3), round(v["overflow_agriculture_mwh"] / 1e6, 3)) for c, v in ov.items() if v["overflow_industry_mwh"] + v["overflow_agriculture_mwh"] > 0})
print("heat band settings:", led["industry"].get("heat_band_settings"))
