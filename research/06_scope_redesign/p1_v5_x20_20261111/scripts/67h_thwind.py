"""只读：v5off 与 v5main F1 网络中陆上风电（任何 carrier 含 wind）的非扩建容量按国家与 carrier。用法：python 67h_thwind.py"""
from pathlib import Path

import pandas as pd
import pypsa

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
for lab in ("v5off", "v5main"):
    n = pypsa.Network(str(D / f"builds/{lab}/integrated/integrated_2920_3h_unsolved.nc"))
    g = n.generators; g = g[g.carrier.astype(str).str.contains("wind")]
    g = g.assign(country=g.bus.map(n.buses.country).fillna(g.bus.str[:2]))
    print("==", lab); print(g.groupby(["carrier", "country"]).agg(n=("p_nom", "size"), p_nom=("p_nom", "sum"), p_nom_min=("p_nom_min", "sum"), ext=("p_nom_extendable", "sum")).round(1).to_string())
    print("TH onwind p_nom>0:", g[(g.country == "TH") & (g.p_nom > 0)][["carrier", "p_nom", "p_nom_extendable"]].to_string()[:800])
    ex = n.meta.get("existing_unit_components") or {}
    print("existing_unit_components type", type(ex).__name__, len(ex))
