"""只读：三套 F1 网络（c2off = v4 数据、v5main = B、c2main = C-2）meta research_renewable 的 untouched 列表（S4A 剖面没有覆盖、保留电力底座原曲线的组件），
按 carrier 与节点列出 p_nom_max / p_nom 与年均 p_max_pu。用法：python 90c_untouched.py   输出 evidence/C2_RENEWABLE_UNTOUCHED.csv"""
import json
from pathlib import Path

import netCDF4
import pandas as pd
import pypsa

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
rows = []
for lab, sub in (("v4", "c2off"), ("B", "v5main"), ("C2", "c2main")):
    p = D / f"builds/{sub}/integrated/integrated_2920_3h_unsolved.nc"
    ds = netCDF4.Dataset(str(p)); m = json.loads(ds.getncattr("meta")); ds.close()
    un = (m.get("research_renewable") or {}).get("untouched") or []
    n = pypsa.Network(str(p)); g = n.generators; w = n.snapshot_weightings.generators; P = n.generators_t.p_max_pu
    for x in un:
        if x not in g.index:
            continue
        cf = float((P[x] * w).sum() / w.sum()) if x in P.columns else float(g.at[x, "p_max_pu"])
        rows.append(dict(set=lab, generator=x, carrier=g.at[x, "carrier"], bus=g.at[x, "bus"], country=n.buses.at[g.at[x, "bus"], "country"],
                         extendable=bool(g.at[x, "p_nom_extendable"]), p_nom=float(g.at[x, "p_nom"]), p_nom_max=float(g.at[x, "p_nom_max"]), cf=cf))
    del n
t = pd.DataFrame(rows); t.to_csv(D / "evidence/C2_RENEWABLE_UNTOUCHED.csv", index=False, lineterminator="\n")
pd.set_option("display.width", 220)
print(t.groupby(["set", "carrier"]).agg(n=("generator", "size"), p_nom_max_gw=("p_nom_max", lambda s: s.sum() / 1e3), p_nom_mw=("p_nom", "sum")).round(2).to_string())
print(t[t.set == "C2"].sort_values(["carrier", "bus"]).to_string(index=False)[:4000])
