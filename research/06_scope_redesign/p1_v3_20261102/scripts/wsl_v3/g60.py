import json
from pathlib import Path
import pandas as pd
D = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102"); t = pd.read_csv(D.parent.parent.parent / "research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv")
print(t[["project", "contract_mw", "eppo_section", "eppo_cod", "gem_status", "gem_start_year", "gem_capacity_mw", "network_component", "plant_node", "landing_node"]].to_string(index=False)[:1900])
e = json.loads((D / "evidence/smoke_s2/V3_SMOKE_RESULT.json").read_text())
print({k: (v if not isinstance(v, dict) else {a: b for a, b in v.items() if a in ("b6_bn", "passed", "difference")}) for k, v in e.items() if k in ("B6", "passed")})
print(e["B5_NO_NEW_XB_solved"]["passed"], {s: e[s]["cross_border"] for s in ("integrated", "no_new_xb")})
print({s: {k: round(v, 3) for k, v in (e[s].get("ship_flow_twh") or {}).items()} for s in ("integrated", "no_new_xb")})
for s in ("integrated", "no_new_xb"):
    l = pd.read_csv(D / "evidence/smoke_s2" / s / "COUNTRY_COST_LEDGER.csv", index_col=0); print(s, "freight", round(float(l["liquid_ship_freight"].sum() + l["liquid_transit_freight"].sum()) / 1e9, 4)); r = json.loads((D / "evidence/smoke_s2" / s / "SOLVE_RECEIPT.json").read_text()); print(" ", r.get("solve_seconds"), r.get("termination_condition"), r.get("network_sha256", "")[:8], (r.get("input_network") or {}).get("sha256", "")[:8])
