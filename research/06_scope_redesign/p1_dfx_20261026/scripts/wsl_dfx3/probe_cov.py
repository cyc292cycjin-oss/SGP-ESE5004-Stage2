"""DFX v3: locate the v2 table-vs-network coverage gap (1.213 GWh) per (country, account, carrier). Read-only."""
import sys
from pathlib import Path

import pandas as pd
import pypsa

sys.path.insert(0, "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/scripts")
import dfx_demand_review as R  # noqa: E402

tag = sys.argv[1] if len(sys.argv) > 1 else "v2"
OUT = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026")
n = pypsa.Network(str(R.RES / f"builds_{tag}" / "integrated/integrated_2920_3h_unsolved.nc"))
t = R.load_table(n)
g = t.groupby(["country", "account", "carrier"]).mwh.sum()
d1 = pd.read_csv(OUT / f"DEMAND_BY_COUNTRY_SECTOR_CARRIER_{tag}.csv", keep_default_na=False)
tg = d1[d1.network_account != "memo"].groupby(["country", "network_account", "carrier"]).twh_integrated_2920x3h.sum() * 1e6
tg.index.names = ["country", "account", "carrier"]
idx = g.index.union(tg.index)
cmp = pd.DataFrame({"network_mwh": g.reindex(idx).fillna(0.0), "table_mwh": tg.reindex(idx).fillna(0.0)})
cmp["diff_mwh"] = cmp.table_mwh - cmp.network_mwh
bad = cmp[cmp.diff_mwh.abs() > 1e-3].sort_values("diff_mwh")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print(bad.to_string())
print("sum diff MWh:", cmp.diff_mwh.sum(), " n rows:", len(bad))
print("network-only keys:", list(g.index.difference(tg.index))[:40])
print("table-only keys:", list(tg.index.difference(g.index))[:40])
