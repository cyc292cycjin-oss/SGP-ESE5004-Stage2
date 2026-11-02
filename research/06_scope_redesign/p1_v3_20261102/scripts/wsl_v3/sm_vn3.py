import json
from pathlib import Path
import pandas as pd
W = Path("/home/jin/wt_v3_20261102"); M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
p = pd.read_csv(W / "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv"); print(list(p.columns)); print(p[p.country == "VN"].to_string()[:1500])
for tag, f in (("v2", M / "dfx_v3/smoke_v2/integrated/V5_GATES.json"), ("v3", M / "v3/smoke_s1/integrated/V5_GATES.json"), ("v3flat", M / "v3/smoke_s1/integrated_flat/V5_GATES.json")):
    g = json.loads(f.read_text())["B3"]; r = pd.DataFrame(g["rows"]); x = r[r.country == "VN"]
    print(tag, "VN potential", round(x.potential_mwh.sum() / 1e6, 4), "used", round(x.used_mwh.sum() / 1e6, 4), dict(zip(x.category, x.share_used.round(4))))
    c = r.groupby("country")[["potential_mwh", "used_mwh"]].sum() / 1e6; c["share"] = c.used_mwh / c.potential_mwh; print(c.round(3).T.to_string())
