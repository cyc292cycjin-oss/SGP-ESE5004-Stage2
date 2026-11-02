"""Numbers for the report, re-read from the evidence, so that the report does not rest on figures typed from memory."""
import json
from pathlib import Path
import pandas as pd
E = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/smoke")
e = json.loads((E / "V3_SMOKE_RESULT.json").read_text())
for s in ("integrated", "no_new_xb"):
    x = e[s]; sg = x["sg_marine_fuel"]; ins = sg["ship_in_twh_by_origin"]; tot = sum(ins.values())
    print(s, "peak", round(x["peak_rss_gib"], 2), "solve_s", round(x["solve_seconds"], 1), "obj", round(x["objective_eur"] / 1e9, 4), "ledger", x["ledger_relative_error"], "duals", x["ship_capacity_duals"]["max_abs_eur_per_mwh"], "util", round(x["ship_capacity_duals"]["max_utilisation"], 4))
    print("   SG load", round(sg["marine_load_twh"], 2), "supplied", round(sg["supplied_twh"], 2), "share by origin", {k: round(v / tot * 100, 2) for k, v in ins.items() if v > 0.01})
    d = x["liquid_dual_annual_mean_eur_per_mwh"]
    print("   dual range", {k: (round(min(v.values()), 2), round(max(v.values()), 2), max(v, key=v.get), round(v.get("SG", 0), 2)) for k, v in d.items()})
b = pd.read_csv(E / "V3_LIQUID_BALANCE.csv")
print("trade TWh", b[(b.term == "ship out")].groupby(["scenario", "carrier"]).twh.sum().round(1).to_dict())
print("ext import TWh", b[b.term == "import outside ASEAN"].groupby(["scenario", "carrier"]).twh.sum().round(3).to_dict())
d = pd.read_csv(E / "V3_SHIP_CAPACITY_DUALS.csv"); print("dual csv", d.groupby("scenario").agg(links=("link", "count"), above=("mu_upper_max_abs", lambda s: int((s > 1e-6).sum())), util=("max_utilisation", "max")).to_dict("index"))
