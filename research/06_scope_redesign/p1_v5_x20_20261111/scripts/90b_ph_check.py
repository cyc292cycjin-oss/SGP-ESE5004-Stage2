"""只读：C-2 网络中 PH 陆上风电候选的剖面列匹配情况（截断效应表中 PH 截断后高于截断前的原因）。用法：python 90b_ph_check.py"""
from pathlib import Path

import pandas as pd
import pypsa
import xarray as xr

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111"); R = Path("/home/jin/wt_v5_x20")
n = pypsa.Network(str(D / "builds/c2main/integrated/integrated_2920_3h_unsolved.nc"))
g = n.generators; cty = g.bus.map(n.buses.country); w = n.snapshot_weightings.generators; P = n.generators_t.p_max_pu
ds = xr.open_dataset(R / "research_inputs/renewable_v5/profiles_calibrated_gwa_v5q_c3_3h.nc"); prof = ds["onwind"].to_pandas(); ds.close()
cand = [x for x in g.index[(g.carrier == "onwind") & g.p_nom_extendable] if cty[x] == "PH"]
for x in cand:
    k = 2 if x.endswith(" c2") else (1 if x.endswith(" c1") else 0); key = f"{g.at[x, 'bus']}|{k}"
    pr = float((prof[key].values * w.values).sum() / w.sum()) if key in prof.columns else None
    nt = float((P[x] * w).sum() / w.sum()) if x in P.columns else None
    print(f"{x:32s} bus={g.at[x, 'bus']:16s} key_in_profile={key in prof.columns} p_nom_max={g.at[x, 'p_nom_max']:10.1f} cf_profile={pr} cf_network={nt}")
