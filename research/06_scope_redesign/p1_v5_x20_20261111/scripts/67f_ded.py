"""只读：v5main 与 v5off 专用电源（LA2 1-5）各源的移入容量（按 carrier）与 v5 状态回退名单长度。用法：python 67f_ded.py"""
import json
from pathlib import Path

import netCDF4

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
for lab in ("v5off", "v5main"):
    ds = netCDF4.Dataset(str(D / f"builds/{lab}/integrated/integrated_2920_3h_unsolved.nc")); m = json.loads(ds.getncattr("meta")); ds.close()
    r = m["research_dedicated_lines"]
    print("==", lab, "status_table", r.get("status_table"), "v5_status_from_identity", len(r.get("v5_status_from_identity") or []))
    for s in r["sources"]:
        print(" ", s["node"], s["contract_mw"], s["moved_mw"], s["moved_mw_by_carrier"], "stayed", len(s.get("stayed_units") or []))
    if lab == "v5main":
        print({k: v for k, v in r.items() if k.startswith("v5")} .keys())
