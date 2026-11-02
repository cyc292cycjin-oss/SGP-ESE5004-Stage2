#!/bin/bash
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
$PY -I /home/jin/v3/irena.py 2>&1 | grep -v fontTools | cut -c1-300
cd /home/jin/wt_v3_20261102
sed -n 1,30p scripts_project/s4d_2_ship_routes.py | cut -c1-190
$PY - <<'P'
import pandas as pd
pd.set_option("display.width",200); pd.set_option("display.max_rows",200)
p=pd.read_csv("research_inputs/co2_v5/PORTS_ASEAN_TO_NODES_S4D1.csv")
print(p.harbor_size.value_counts(dropna=False).to_dict(), p.harbor_type.value_counts().head(6).to_dict())
w={"Large":3,"Medium":2,"Small":1,"Very Small":0.5}
p["w"]=p.harbor_size.map(w).fillna(0.5)
t=p.groupby(["country","node"]).agg(w=("w","sum"),ports=("port",lambda s:", ".join(list(s)[:5]))).reset_index().sort_values(["country","w"],ascending=[True,False])
print(t.groupby("country").head(3).to_string())
l=pd.read_csv("research_inputs/lng_terminals_v5/LNG_IMPORT_TERMINALS_GEM_2025.csv",keep_default_na=False); print(l[l.status=="operating"].groupby("node").size().to_dict() if "node" in l else l.columns.tolist())
P
