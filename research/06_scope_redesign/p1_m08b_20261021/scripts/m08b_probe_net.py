"""M08b probe: quick structure check of a built network (read-only)."""
import logging
import sys

import pandas as pd
import pypsa

logging.getLogger("pypsa").setLevel(logging.ERROR)
n = pypsa.Network(sys.argv[1])
w = n.snapshot_weightings.generators
L = n.loads.copy()
e = n.get_switchable_as_dense("Load", "p_set").mul(w, axis=0).sum()
L["twh"] = e.reindex(L.index).fillna(0) / 1e6
print("loads by carrier (TWh):"); print(L.groupby("carrier").twh.sum().round(2).to_string())
for car in ["industry heat", "industry heat medium", "industry heat high"]:
    print(car, "buses", int((n.buses.carrier == car).sum()))
lk = n.links
print("heat links by carrier:"); print(lk[lk.bus1.str.contains("industry heat", na=False)].groupby("carrier").size().to_string())
print("overflow gas loads:", int(L.index.str.contains("overflow gas").sum()), "overflow heat loads:", int(L.index.str.contains("overflow heat").sum()))
led = n.meta["s2_demand_ledger"]
print("anchor checks:", len(led["anchors"]["checks"]), led["anchors"]["settings"])
print("industry:", {k: led["industry"][k] for k in ("other_bucket", "heat_bands", "biomass_overflow_mode", "physical_output")})
ov = pd.DataFrame(led["industry"]["biomass_overflow"]).T
print(ov[["solid_biomass_potential_mwh", "fixed_biomass_after_mwh", "overflow_industry_mwh", "overflow_agriculture_mwh"]].astype(float).div(1e6).round(3).to_string())
