"""Supplement 01, read-only: grouped EV effect, profile comparison, cross-border build, freight, registered biomass potential, B1 details, what 'dispersed' covers."""
import json
from pathlib import Path
import pandas as pd
pd.set_option("display.width", 220, "display.max_columns", 40)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
W = Path("/home/jin/wt_v3_20261102"); D = W / "research/06_scope_redesign/p1_v3_20261102"; E = D / "evidence/smoke_s1"; A = D / "evidence/smoke"; R = M / "v3/smoke_s1"
T = pd.read_csv(E / "COST_BY_CARRIER_V2_FLAT_E2.csv", index_col=0)
G = {"光伏": ["G solar"], "风电": ["G offwind-dc", "G onwind", "G offwind-float", "G offwind-ac"], "气电 + 气体燃料": ["L CCGT CC", "L CCGT", "L OCGT", "L CCGT existing", "L OCGT existing", "G LNG import", "G gas production"], "CO2 封存": ["S co2 sequestered"],
     "电解槽": ["L H2 Electrolysis"], "水电": ["U hydro", "G ror"], "DAC": ["L DAC"]}
used = sum(G.values(), [])
rows = {k: T.reindex(v).fillna(0.0)[["ev_int", "ev_nnx", "rest"]].sum() for k, v in G.items()}; rows["其他"] = T.drop(index=[x for x in used if x in T.index])[["ev_int", "ev_nnx", "rest"]].sum()
g = pd.DataFrame(rows).T; g.loc["合计"] = g.sum(); print(g.round(3).to_string()); print(T.reindex(["L CCGT", "L OCGT", "L CCGT existing", "L OCGT existing"]).round(3).to_string())
for s in ("integrated", "no_new_xb"):
    a = json.loads((A / s / "SOLVE_RECEIPT.json").read_text()); b = json.loads((R / s / "SOLVE_RECEIPT.json").read_text())
    print(s, "profile A", a["objective"], a.get("solver_profile"), "t16", b["objective"], "diff EUR", b["objective"] - a["objective"])
    ga = json.loads((A / s / "V5_GATES.json").read_text()); print("  profile A failed", sorted(k for k, v in ga.items() if isinstance(v, dict) and v.get("passed") is False))
e = json.loads((E / "V3_SMOKE_RESULT.json").read_text()); print("B5 solved", e.get("B5_NO_NEW_XB_solved"), "v2", e.get("v2_smoke_same_56_snapshots", {}).get("objective_eur"), e.get("v2_smoke_same_56_snapshots", {}).get("b6_bn_eur"))
for s in ("integrated", "no_new_xb", "integrated_flat", "no_new_xb_flat"):
    print(s, "xb", json.dumps(e[s].get("cross_border"), default=str)[:520]); print("   ship flow", json.dumps(e[s].get("ship_flow_twh"), default=str)[:300])
    l = pd.read_csv(R / s / "COUNTRY_COST_LEDGER.csv", index_col=0); print("   freight", {c: round(float(l[c].sum()) / 1e9, 4) for c in l.columns if c.startswith("liquid") or "freight" in c})
g = json.loads((R / "integrated/V5_GATES.json").read_text())["B1"]; print("B1 keys", [k for k in g if k not in ("s3_scope",)], {k: (round(v["final_level_tco2"], 5), v["within_cap"]) for k, v in g["countries"].items()}, {k: g.get(k) for k in ("tolerance", "tolerance_tco2", "tol")})
b = pd.read_csv(W / "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv"); x = b[b.country == "VN"][["category", "feedstock_group", "potential_main_mwh", "potential_tier", "status"]]; print(x.to_string()); print("sum TWh", x.potential_main_mwh.sum() / 1e6, "by group", (x.groupby("feedstock_group").potential_main_mwh.sum() / 1e6).round(4).to_dict())
