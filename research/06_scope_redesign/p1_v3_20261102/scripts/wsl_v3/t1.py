import sys
sys.path.insert(0,"/home/jin/wt_v3_20261102/scripts_project")
import pandas as pd, numpy as np
from v3_industry import CARRIERS,col,SUMMARY
from d1_common import DEMAND_DIR
pd.set_option("display.width",200); pd.set_option("display.max_rows",40); pd.set_option("display.float_format",lambda v:f"{v:.9g}")
a=pd.read_csv("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v2.csv")
b=pd.read_csv("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v3.csv")
x=a[a.sector!="InternationalBunkers"].groupby(["country","sector"]).twh.sum(); y=b[b.sector!="InternationalBunkers"].groupby(["country","sector"]).twh.sum()
r=((y-x).abs()/x.abs().clip(lower=1e-9)).replace([np.inf],0).fillna(0).sort_values(ascending=False)
t=pd.DataFrame(dict(v2=x,v3=y,rel=r)).sort_values("rel",ascending=False).head(6); print(t)
s=pd.read_csv(DEMAND_DIR/SUMMARY).set_index("country"); T=s[[col(c) for c in CARRIERS]].sum(axis=1)/1e6
i=a[a.sector=="Industry"].groupby("country").twh.sum(); print(pd.DataFrame(dict(table=i,summary=T,diff=i-T)))
print(a[(a.sector=="Industry")&(a.country=="BN")][["subsector","carrier","twh"]].head(8).to_string())
