"""Supplement 04: exact values for the prediction table and the four-column LA table, TH side, where the Lao stock goes. Read-only."""
import json, logging
from pathlib import Path
import pandas as pd, pypsa
logging.disable(logging.WARNING)
pd.set_option("display.width", 200, "display.max_columns", 30)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3")
own = lambda d: pd.read_csv(M / d / "M12_BENEFIT/BENEFIT.csv").set_index("player")["owen_benefit_eur"] / 1e9
print("LA", {k: round(float(own(k)["LA"]), 4) for k in ("smoke_s1", "smoke_s2", "smoke_s3", "smoke_s4")}, "TH", {k: round(float(own(k)["TH"]), 4) for k in ("smoke_s1", "smoke_s2", "smoke_s3", "smoke_s4")})
for sc in ("no_new_xb", "integrated"):
    print("=====", sc)
    for k, d in (("none", "smoke_s1"), ("two_way", "smoke_s2"), ("one_way", "smoke_s3"), ("bound", "smoke_s4")):
        n = pypsa.Network(str(M / d / f"{sc}/{sc}_SMOKE_TEST_ONLY_solved.nc")); w = n.snapshot_weightings.generators; c = n.buses.country.astype(str)
        g = n.generators[n.generators.bus.map(c) == "LA"]; e = (n.generators_t.p[g.index.intersection(n.generators_t.p.columns)].mul(w, axis=0).sum().groupby(g.carrier.astype(str)).sum() / 1e6)
        p = g[g.p_nom_extendable].groupby(g.carrier.astype(str)).p_nom_opt.sum() / 1e3
        av = n.get_switchable_as_dense("Generator", "p_max_pu")[g.index[g.carrier.astype(str).isin(["onwind", "solar"])]]
        pot = (av.mul(g.p_nom_opt.reindex(av.columns)).mul(w, axis=0).sum().groupby(g.carrier.astype(str).reindex(av.columns)).sum() / 1e6)
        th = n.generators[n.generators.bus.map(c) == "TH"]; te = (n.generators_t.p[th.index.intersection(n.generators_t.p.columns)].mul(w, axis=0).sum().groupby(th.carrier.astype(str)).sum() / 1e6)
        print(k, "LA new GW", {x: round(float(p.get(x, 0.0)), 2) for x in ("onwind", "solar")}, "TWh", {x: round(float(e.get(x, 0.0)), 2) for x in ("onwind", "solar", "onwind existing", "ror existing")}, "curtail", {x: round(1 - float(e.get(x, 0.0)) / float(pot.get(x, 1.0)), 3) for x in ("onwind", "solar")}, "TH gas fuels TWh", {x: round(float(te.get(x, 0.0)), 1) for x in te.index if "LNG" in x or "gas" in x})
