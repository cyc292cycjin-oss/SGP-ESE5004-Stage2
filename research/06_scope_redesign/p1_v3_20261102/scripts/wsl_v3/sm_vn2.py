"""VN subsector x carrier in the v3 industry table, TWh in 2050 (case main), APEC shares of the bucket 'other', read-only."""
from pathlib import Path
import pandas as pd
pd.set_option("display.width", 220, "display.max_columns", 40)
W = Path("/home/jin/wt_v3_20261102")
sc = pd.read_csv(W / "research_inputs/industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv")
v = sc[(sc.country == "VN") & (sc.case == "main")].pivot_table(index="subsector", columns="carrier", values="mwh_2050", aggfunc="sum").fillna(0.0) / 1e6
v["total"] = v.sum(axis=1); print(v.round(2).to_string()); print(v.sum().round(2).to_dict())
d = pd.read_csv(W / "research/06_scope_redesign/p1_v3_20261102/DEMAND_DIFF_V3_V2.csv")
x = d[(d.country == "VN") & (d.sector == "Industry")].pivot_table(index="subsector", columns="carrier", values="twh_v2", aggfunc="sum").fillna(0.0)
print("v2 table"); print(x.round(2).to_string())
y = d[(d.country == "VN") & (d.sector == "Industry")].pivot_table(index="subsector", columns="carrier", values="twh_v3", aggfunc="sum").fillna(0.0)
print("v3 table"); print(y.round(2).to_string())
a = pd.read_csv(W / "research_inputs/industry_v3/APEC2022_VN_INDUSTRY_PJ.csv"); c = ["coal_pj", "oil_pj", "gas_pj", "biomass_pj", "electricity_pj"]; print(a[c].sum().round(1).to_dict(), round(a[c].sum().sum(), 1))
