import pandas as pd
pd.set_option("display.width",220); pd.set_option("display.max_columns",30); pd.set_option("display.max_rows",80); pd.set_option("display.max_colwidth",46)
d=pd.read_csv("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v2.csv")
print(d.groupby("sector").twh.sum().round(2).to_dict(), round(d.twh.sum(),2))
x=d[(d.country=="VN")&(d.sector=="Industry")]; print(x[["subsector","carrier","twh","energy_form","network_account","source_final_energy_twh"]].to_string()[:1900])
y=d[(d.sector=="Transport")&(d.country=="SG")]; print(y[["subsector","carrier","twh","network_account"]].to_string()[:800])
z=d[d.sector=="InternationalBunkers"]; print(z.groupby(["country","carrier"]).twh.sum().round(2).head(8).to_dict(), z.subsector.unique()[:5], z.network_account.unique()[:5])
