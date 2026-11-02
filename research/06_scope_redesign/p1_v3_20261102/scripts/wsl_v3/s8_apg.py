import pandas as pd
pd.set_option("display.width", 220, "display.max_columns", 30, "display.max_colwidth", 46, "display.max_rows", 60)
W = "/home/jin/wt_v3_20261102/"
a = pd.read_csv(W + "research_inputs/corridors/CORRIDOR_APG_CROSSCHECK_2024.csv")
print(a[["apg_no", "connection", "country_pair", "apg_existing_mw", "apg_ongoing_to_2024_mw", "apg_future_mw", "aims3_2040_projection_mw", "classification", "corridor_capacity_2025_mw"]].to_string())
s = pd.read_csv(W + "research/06_scope_redesign/p1_v3_20261102/evidence/V2_CROSS_BORDER_STOCK.csv")
print(list(s.columns)); print(s.to_string()[:2600])
