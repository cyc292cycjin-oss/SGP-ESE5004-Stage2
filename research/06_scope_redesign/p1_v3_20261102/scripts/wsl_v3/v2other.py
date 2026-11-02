import json, pandas as pd
from pathlib import Path
pd.set_option("display.width",220); pd.set_option("display.max_columns",40); pd.set_option("display.max_rows",100)
W=Path("/home/jin/wt_v3_20261102/research_inputs/demand_v5")
o=pd.read_csv(W/"INDUSTRY_2050_OTHER_BUCKET.csv"); o=o[o["mode"]=="aeo8_ats_anchor"]
print(o[["country","industry_2019_mwh","other_2019_mwh","other_share_of_industry_2019","industry_multiplier"]].assign(a=lambda d:d.industry_2019_mwh/1e6,b=lambda d:d.other_2019_mwh/1e6)[["country","a","b","other_share_of_industry_2019","industry_multiplier"]].round(3).to_string())
print("ALL", o.other_2019_mwh.sum()/o.industry_2019_mwh.sum())
s=pd.read_csv(W/"INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv")
col=[c for c in s if c.startswith("pe_") and c.endswith("_mwh") and "before" not in c and "dropped" not in c]
s2=s.set_index("country")[col]/1e6; s2["sum"]=s2.sum(axis=1); print(s2.round(1).to_string()); print(s2.sum().round(1).to_dict())
print(s.set_index("country")[["other_fuel_2050_mwh","other_electricity_2050_mwh","crude_steel_2050_t","cement_2050_t","ammonia_2050_t","unsd_subsector_rows_present"]].assign(other_fuel_2050_mwh=lambda d:d.other_fuel_2050_mwh/1e6,other_electricity_2050_mwh=lambda d:d.other_electricity_2050_mwh/1e6).round(2).to_string())
d=pd.read_csv(W/"DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv",keep_default_na=False)
d["v"]=pd.to_numeric(d.value_2050_mwh,errors="coerce").fillna(0)
ind=d[d.sector=="Industry"].groupby("country").v.sum()/1e6
print("anchor table Industry TWh", ind.round(1).to_dict(), round(ind.sum(),1))
print(d[d.sector=="Industry"].groupby("account").v.sum().div(1e6).round(1).to_dict())
c=json.load(open("/home/jin/wt_v3_20261102/research_inputs/assembly_v1/sources/industry_cache.json"))
print(c.keys()); r=pd.DataFrame(c["records"]); print(r.columns.tolist()); 
subs=[x for x in r.columns if x not in("country","carrier")]
for k in subs: r[k]=pd.to_numeric(r[k],errors="coerce")
g=r.groupby("country")[subs].sum(); g["total"]=g.sum(axis=1); print(g.round(1).to_string()[:2400]); print(c.get("unit"),c.get("source"),c.get("source_sha256"))
g2=g.div(g.total,axis=0); print(g2.round(3).to_string()[:2400])
