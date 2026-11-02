import json, numpy as np, pandas as pd
from pathlib import Path
pd.set_option("display.width",220); pd.set_option("display.max_columns",40); pd.set_option("display.max_rows",60)
W=Path("/home/jin/wt_v3_20261102"); MAIN=Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")
am=json.load(open(MAIN/"results_project/assembly_v1/final_allocation/allocation_manifest.json"))
z=np.load(MAIN/"results_project/assembly_v1/final_allocation"/am["arrays_file"],allow_pickle=False)
cnt={}
for ar in am["records"]:
    c,y,s,acc,car=ar["InputID"].split(":")
    if acc in("InternationalShippingBunker","InternationalAviationBunker"):
        a=np.asarray(z[ar["ArrayKey"]],dtype=float); a=a.reshape(-1,1) if a.ndim==1 else a
        sh=a.sum(axis=0); nn=[n for n,v in zip(ar["Nodes"],sh) if v>0]
        cnt.setdefault(acc,{}).setdefault(c,set()).update(nn)
print({k:{c:len(v) for c,v in d.items()} for k,d in cnt.items()}); print({k:sum(len(v) for v in d.values()) for k,d in cnt.items()})
t=pd.read_csv(W/"research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv")
print(t.columns.tolist()); print(t[t.sector.str.contains("lumin|non-ferrous|Other non|Pulp|Paper|Food|Textile|Other ind",regex=True)][["sector","today_total_mwh_per_t"]+[c for c in t.columns if "fec_2019" in c or "prod" in c][:2]].round(3).to_string())
r=pd.read_csv(W/"research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv",index_col=0)
print(r[[c for c in r.columns if "lumin" in c or "non-ferrous" in c or "Other industrial" in c]].round(3).to_string())
q=pd.read_csv(W/"research_inputs/co2_v5/CO2_SHIP_ROUTES_S4D2.csv")
for o in ("SG2 0","ID_Java-Bali1 0","MY_Peninsular2 1","TH2 3","VN2 5","PH_Luzon5 0","MM2 1","KH2 0"):
    x=q[q.origin==o][["receiver","landing","sea_km"]]
    print(o,{a:(b,round(c)) for a,b,c in x.itertuples(index=False)})
