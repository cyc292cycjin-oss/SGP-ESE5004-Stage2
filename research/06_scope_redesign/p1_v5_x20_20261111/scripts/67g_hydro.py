"""只读：v5main 与 v5off F1 网络 meta research_hydro_inflow 的 ID / LA / MY 明细（运营份额、存量、目标）。用法：python 67g_hydro.py"""
import json
from pathlib import Path

import netCDF4

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
for lab in ("v5off", "v5main"):
    ds = netCDF4.Dataset(str(D / f"builds/{lab}/integrated/integrated_2920_3h_unsolved.nc")); m = json.loads(ds.getncattr("meta")); ds.close()
    h = m["research_hydro_inflow"]
    print("==", lab, "keys", sorted(h))
    print({k: v for k, v in h.items() if k not in ("countries",)} if len(json.dumps({k: v for k, v in h.items() if k != "countries"})) < 3000 else json.dumps({k: v for k, v in h.items() if k != "countries"})[:3000])
    for c in ("ID", "LA", "MY", "VN"):
        print(c, json.dumps(h["countries"].get(c), default=str)[:1500])
