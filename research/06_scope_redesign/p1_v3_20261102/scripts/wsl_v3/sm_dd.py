import pandas as pd
pd.set_option("display.width", 200, "display.max_columns", 30)
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
d = pd.read_csv(D + "DEMAND_DIFF_V3_V2.csv")
print(list(d.columns))
print(d.head(2).to_string()[:420])
k = [x for x in d.columns if "diff" in x.lower() or "delta" in x.lower()]
print(k)
v = k[0] if k else d.columns[-1]
x = d[d.sector.astype(str).str.lower() == "industry"]
p = x.pivot_table(index="country", columns="carrier", values=v, aggfunc="sum").round(1)
print(p.to_string())
print(p.sum().round(1).to_dict())
