import pandas as pd
W = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102"
r = pd.read_csv(f"{W}/evidence/DEMAND_NETWORK_CHECK_V3.csv")
heat = r.carrier.str.startswith("industry heat") | (r.carrier == "biomass final energy")
x = r[~heat].copy()
for c in ("integrated_2920", "no_new_xb_2920", "integrated_365", "no_new_xb_365"):
    x["gap_" + c] = x[c] - x.table
    x["rel_" + c] = x["gap_" + c].abs() / x.table.clip(lower=1e-3)
pd.set_option("display.width", 200, "display.max_columns", 20)
print(x.sort_values("rel_integrated_365", ascending=False)[["country", "carrier", "table", "gap_integrated_2920", "gap_integrated_365", "rel_integrated_2920", "rel_integrated_365"]].head(8).to_string())
print(x[[c for c in x if c.startswith("gap_")]].abs().max())
