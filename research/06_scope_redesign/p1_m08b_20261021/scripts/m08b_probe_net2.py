"""M08b probe: how CO2 storage caps, LNG terminals, PV and offshore candidates appear in a built network (read-only)."""
import json
import logging
import sys

import pypsa

logging.getLogger("pypsa").setLevel(logging.ERROR)
n = pypsa.Network(sys.argv[1])
g = n.generators
for car in ["LNG import", "solar", "solar rooftop", "offwind-ac", "offwind-dc", "offwind-float"]:
    s = g[g.carrier == car]
    print(car, len(s), "p_nom_max sum GW", round(float(s.p_nom_max.replace(float("inf"), float("nan")).sum()) / 1e3, 1), "inf:", int((s.p_nom_max == float("inf")).sum()),
          "ext:", int(s.p_nom_extendable.sum()), "cap_cost", sorted(set(s.capital_cost.round(2)))[:3])
st = n.stores
print("store carriers:", sorted(st.carrier.unique()))
seq = st[st.carrier.str.startswith("co2 sequestered")]
print(seq[["carrier", "e_nom", "e_nom_max", "e_nom_extendable", "country"]].head(14).to_string())
print("meta keys:", [k for k in n.meta if "co2" in k or "storage" in k or "renew" in k or "lng" in k.lower()])
cs = n.meta.get("research_co2_storage") or {}
print(json.dumps({k: (v if not isinstance(v, (dict, list)) else (list(v)[:12] if isinstance(v, dict) else v[:3])) for k, v in cs.items()}, default=str)[:1500])
rr = n.meta.get("research_renewable") or {}
print(json.dumps({k: rr[k] for k in rr if k in ("offshore_rules", "solar_p_nom_max_scale", "profile_variant", "resource_classes")}, default=str))
