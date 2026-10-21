import json, pandas as pd, numpy as np
d = json.load(open("/home/jin/m08a_offshore_work/author_validation/OFFSHORE_PROFILES_LOG_author.json"))
s4a = json.load(open("/home/jin/wt_m08a_20261021/research_inputs/renewable_v5/S4A_PROFILES_LOG_c3.json"))["potential_by_node"]
out = {}
for t in ("offwind-ac", "offwind-dc"):
    v = d["author_validation"][t]
    new = pd.Series(v["by_node"]); ref = pd.Series(s4a[t])
    j = pd.concat([new.rename("new"), ref.rename("s4a")], axis=1).fillna(0.0)
    j = j[(j.new > 1) | (j.s4a > 1)]
    rel = (j.new / j.s4a - 1).replace([np.inf, -np.inf], np.nan)
    big = j[(j.new - j.s4a).abs() > 0.02 * j.s4a.clip(lower=100)]
    out[t] = dict(total_new_mw=round(v["total_new_mw"], 1), total_author_cells_mw=round(v["total_author_mw"], 1), s4a_nodes_total_mw=round(float(ref.sum()), 1),
                  nodes=len(j), median_abs_rel=float(rel.abs().median()), p90_abs_rel=float(rel.abs().quantile(0.9)), max_abs_rel=float(rel.abs().max()),
                  nodes_off_by_more_than_2pct=len(big), worst=big.assign(rel=rel).sort_values("rel").round(3).head(6).to_dict("index"))
print(json.dumps(out, indent=1))
json.dump(out, open("/home/jin/m08a_offshore_work/author_validation/AUTHOR_VALIDATION_SUMMARY.json", "w"), indent=1)
