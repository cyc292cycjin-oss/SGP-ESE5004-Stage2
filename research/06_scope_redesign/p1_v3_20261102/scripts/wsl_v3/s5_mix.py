"""Supplement 05: stock components of the plant nodes holding units of more than one status; the columns and series of those components. Read-only."""
import logging
from pathlib import Path
import pandas as pd, pypsa
logging.disable(logging.WARNING)
pd.set_option("display.width", 230, "display.max_columns", 40, "display.max_rows", 100, "display.max_colwidth", 60)
print("pypsa", pypsa.__version__)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3")
u = pd.read_csv(M / "s5_status/MOVED_STOCK_STATUS_V3.csv")
n = pypsa.Network(str(M / "builds_bound/integrated/integrated_2920_3h_unsolved.nc"))
i = pd.DataFrame(n.meta["existing_unit_components"]).T.rename_axis("identity").reset_index(); u = u.merge(i[["identity", "component"]], on="identity")
g = u.groupby(["node", "component_type", "component"]).agg(units=("identity", "count"), mw=("capacity_mw", "sum"), status=("gipt_status", lambda s: ",".join(sorted(set(s)))))
print(g[g.status.str.contains(",")].to_string()); print("components", len(g), "mixed", int(g.status.str.contains(",").sum()))
print(u[u.component.isin(g[g.status.str.contains(",")].index.get_level_values("component"))][["component", "identity", "capacity_mw", "gipt_status", "gipt_plant", "gipt_start"]].to_string(index=False))
for t, k in (("StorageUnit", "existing_survivor::LA2 1::hydro existing::S4A"), ("Generator", "existing_survivor::LA2 5::ror existing::S4A")):
    d = n.df(t); print(t, k); print(d.loc[k].dropna().to_string()); print({a: (k in f.columns) for a, f in n.pnl(t).items() if len(f.columns)})
print("dtypes SU", n.storage_units.dtypes.astype(str).value_counts().to_dict())
print("FOM total meta", n.meta.get("existing_annual_fixed_om_eur"), "columns", {t: float(pd.to_numeric(n.df(t).get("existing_annual_fixed_om_eur"), errors="coerce").sum()) for t in ("Generator", "StorageUnit", "Link", "Store") if "existing_annual_fixed_om_eur" in n.df(t)})
