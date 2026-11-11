"""只读：v5main 与 v5off F1 2920 网络 meta 中 research_dust_cleanup 的 SG 陆上风电条目与汇总，以及 SG2 0 陆上风电各类别的 p_nom_max。用法：python 67e_dust.py"""
import json
from pathlib import Path

import netCDF4
import xarray as xr

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
for lab in ("v5off", "v5main"):
    p = D / f"builds/{lab}/integrated/integrated_2920_3h_unsolved.nc"
    ds = netCDF4.Dataset(str(p)); m = json.loads(ds.getncattr("meta")); ds.close()
    dc = m.get("research_dust_cleanup")
    s = json.dumps(dc, default=str)
    print("==", lab, "keys", sorted(dc) if isinstance(dc, dict) else type(dc), "len", len(s))
    i = s.find("SG2 0 onwind"); print("SG hit:", s[max(0, i - 300):i + 600] if i >= 0 else None)
    print("thresholds", json.dumps(dc["thresholds"], default=str)[:600]); print("removed", json.dumps(dc["removed"], default=str)[:1200]); print("pypsa_eur", json.dumps(dc["pypsa_eur"], default=str)[:1500])
    x = xr.open_dataset(p); gi = [str(g) for g in x["generators_i"].values]
    pm = x["generators_p_nom_max"].values
    print({g: float(pm[i]) for i, g in enumerate(gi) if g.startswith("SG2 0 onwind")}); x.close()
