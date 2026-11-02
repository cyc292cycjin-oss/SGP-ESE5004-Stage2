"""Supplement 05, before any change: which moved stock units carry a status in the build receipt, and what GIPT 2026-09 and the S1 survival records say by the same GEM id. Read-only, no build, no solve."""
import json, logging
from pathlib import Path
import pandas as pd, pypsa
logging.disable(logging.WARNING)
pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 300, "display.max_colwidth", 44)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"); W = Path("/home/jin/wt_v3_20261102")
n = pypsa.Network(str(M / "results_project/v3/builds_bound/integrated/integrated_2920_3h_unsolved.nc"))
u = pd.DataFrame(n.meta["existing_unit_components"]).T.rename_axis("identity").reset_index()
srcs = {r["node"]: r for r in n.meta["research_dedicated_lines"]["sources"]}
u = u[u.node.isin(srcs)].copy(); u["gem_id"] = u.identity.str.replace("GEM:", "", regex=False)
u["carrier"] = [str(n.df(t).at[c, "carrier"]) for t, c in zip(u.component_type, u.component)]
u["capacity_mw"] = pd.to_numeric(u.capacity_mw)
g = pd.read_csv(M / "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv", low_memory=False).set_index("GEM unit/phase ID")
print("gipt status col values", g.Status.value_counts().to_dict())
u["gipt_status"] = u.gem_id.map(g.Status).fillna("not in GIPT"); u["gipt_plant"] = u.gem_id.map(g["Plant / Project name"]); u["gipt_start"] = u.gem_id.map(g["Start year"]); u["gipt_mw"] = u.gem_id.map(g["Capacity (MW)"])
if "gem_status" not in u:
    u["gem_status"] = None
u["field_blank"] = u.gem_status.isna() | (u.gem_status.astype(str).isin(["None", "nan", ""]))
print("candidates", len(u), round(u.capacity_mw.sum(), 1), "| field blank", int(u.field_blank.sum()), round(u[u.field_blank].capacity_mw.sum(), 1))
print(u.groupby(["field_blank", "gem_status", "gipt_status"], dropna=False).capacity_mw.agg(["count", "sum"]).to_string())
print("identities not GEM ids", list(u.identity[~u.identity.str.startswith("GEM:")]))
print("field filled but differs from GIPT", u[~u.field_blank & (u.gem_status != u.gipt_status)][["identity", "gem_status", "gipt_status", "capacity_mw"]].to_string())
# S1 survival records: the status the frozen stock came with
s1 = json.loads((W / "research/06_scope_redesign/p1_step1_20261015/evidence/S1_SELECTED_ASSET_SURVIVAL_2050.json").read_text())["records"]; sub = {}
for r in s1:
    for z in r.get("SourceSubassets") or []:
        sub[str(z.get("ID"))] = (str(z.get("Status")), str(r.get("SurvivalStatus")), str(r.get("AssetID")))
    a = str(r.get("AssetID", "")).replace("GEM:", "")
    if a and a not in sub:
        sub[a] = (str(r.get("Status", r.get("SourceStatus", "?"))), str(r.get("SurvivalStatus")), str(r.get("AssetID")))
u["s1_status"] = u.gem_id.map(lambda k: sub.get(k, ("not in S1", "", ""))[0]); u["s1_survival"] = u.gem_id.map(lambda k: sub.get(k, ("", "", ""))[1])
print(u[u.field_blank].groupby(["gipt_status", "s1_status", "s1_survival"], dropna=False).capacity_mw.agg(["count", "sum"]).to_string())
print(u[u.field_blank].sort_values(["node", "carrier", "capacity_mw"], ascending=[True, True, False])[["node", "carrier", "gem_id", "capacity_mw", "gipt_mw", "gipt_status", "gipt_start", "s1_status", "gipt_plant", "source"]].assign(source=lambda d: d.source.str[:22]).to_string(index=False))
u["status_by_gipt"] = u.gipt_status
t = u[~u.carrier.isin(["coal existing", "lignite existing"])]
rows = []
for a, r in srcs.items():
    x = u[u.node == a]; y = t[t.node == a]; op = y[y.status_by_gipt == "operating"]; rows.append(dict(node=a, contract_mw=r["contract_mw"], blank_units=int(x.field_blank.sum()), blank_mw=float(x[x.field_blank].capacity_mw.sum()), non_thermal_field_operating_mw=float(y[y.gem_status == "operating"].capacity_mw.sum()), non_thermal_gipt_operating_mw=float(op.capacity_mw.sum()), thermal_gipt_operating_mw=float(x[x.carrier.isin(["coal existing", "lignite existing"]) & (x.status_by_gipt == "operating")].capacity_mw.sum()), gipt_operating_over_contract=float(op.capacity_mw.sum()) / r["contract_mw"]))
s = pd.DataFrame(rows); print(s.round(2).to_string(index=False)); print(s.sum(numeric_only=True).round(1).to_dict())
O = M / "results_project/v3/s5_status"; O.mkdir(exist_ok=True); u.drop(columns=["component"]).to_csv(O / "MOVED_STOCK_STATUS_V3.csv", index=False); s.to_csv(O / "MOVED_STOCK_STATUS_BY_NODE_V3.csv", index=False); print("written", O)
