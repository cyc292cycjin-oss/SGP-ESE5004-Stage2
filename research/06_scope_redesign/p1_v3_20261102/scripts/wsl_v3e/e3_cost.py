"""V3 supplement 06 item 4, read-only: V5 - V1 (365x24h) annualised cost and capacity by technology group. Same cost rule as supplement 01
(sm_cmp2.cost: capital_cost x optimal capacity of extendable components + marginal cost x dispatch x objective weight), extended to
time-varying marginal costs and Store dispatch. Networks are loaded one at a time; nothing is written back. No solver."""
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

logging.disable(logging.WARNING)
W = Path("/home/jin/wt_v3_20261102"); OUT = W / "research/06_scope_redesign/p1_v3_20261102/evidence/evdiag"
X = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/cloud_results/final_20261103T063207Z/full_unpacked/export")
RUNS = {"V1": X / "V1/integrated_DFX_365X24H_solved.nc", "V5": X / "V5/integrated_DFX_365X24H_solved.nc"}
ELEC_XB = {"AC", "DC", "dedicated plant line", "electricity"}


def mc(n, comp, name, default):
    t = n.pnl(comp)["marginal_cost"]
    return t[name] if name in t else default


def table(n):
    wo = n.snapshot_weightings.objective; wg = n.snapshot_weightings.generators; rows = []
    for name, z in n.generators.iterrows():
        p = n.generators_t.p[name] if name in n.generators_t.p else pd.Series(0.0, index=n.snapshots)
        rows.append(dict(comp="Generator", carrier=str(z.carrier), border="", cap=z.capital_cost * z.p_nom_opt if z.p_nom_extendable else 0.0,
                         op=float((p * mc(n, "Generator", name, z.marginal_cost) * wo).sum()), gw=z.p_nom_opt / 1e3, gwh=0.0, twh=float((p * wg).sum()) / 1e6))
    p0 = n.links_t.p0; p1 = n.links_t.p1
    for name, z in n.links.iterrows():
        a = p0[name] if name in p0 else pd.Series(0.0, index=n.snapshots); b = p1[name] if name in p1 else pd.Series(0.0, index=n.snapshots)
        rows.append(dict(comp="Link", carrier=str(z.carrier), border=str(z.get("border_class", "") or ""), cap=z.capital_cost * z.p_nom_opt if z.p_nom_extendable else 0.0,
                         op=float((a * mc(n, "Link", name, z.marginal_cost) * wo).sum()), gw=z.p_nom_opt / 1e3, gwh=0.0, twh=float((-b * wg).sum()) / 1e6))
    for name, z in n.stores.iterrows():
        p = n.stores_t.p[name] if name in n.stores_t.p else pd.Series(0.0, index=n.snapshots)
        rows.append(dict(comp="Store", carrier=str(z.carrier), border="", cap=z.capital_cost * z.e_nom_opt if z.e_nom_extendable else 0.0,
                         op=float((p * mc(n, "Store", name, z.marginal_cost) * wo).sum()), gw=0.0, gwh=z.e_nom_opt / 1e3, twh=0.0))
    for name, z in n.storage_units.iterrows():
        p = n.storage_units_t.p_dispatch[name] if name in n.storage_units_t.p_dispatch else pd.Series(0.0, index=n.snapshots)
        rows.append(dict(comp="StorageUnit", carrier=str(z.carrier), border="", cap=z.capital_cost * z.p_nom_opt if z.p_nom_extendable else 0.0,
                         op=float((p * mc(n, "StorageUnit", name, z.marginal_cost) * wo).sum()), gw=z.p_nom_opt / 1e3, gwh=z.p_nom_opt * z.max_hours / 1e3, twh=float((p * wg).sum()) / 1e6))
    for name, z in n.lines.iterrows():
        rows.append(dict(comp="Line", carrier="AC line", border=str(z.get("border_class", "") or ""), cap=z.capital_cost * z.s_nom_opt if z.s_nom_extendable else 0.0, op=0.0, gw=z.s_nom_opt / 1e3, gwh=0.0, twh=0.0))
    t = pd.DataFrame(rows)
    return t.groupby(["comp", "carrier", "border"], dropna=False)[["cap", "op", "gw", "gwh", "twh"]].sum()


def group(comp, carrier, border):
    c = carrier.lower()
    if c in ("bev charger", "ev battery", "v2g", "land transport ev"):
        return "EV 相关链路"
    if border == "cross_border":
        return "跨境输电" if (comp == "Line" or carrier in ELEC_XB or "dedicated" in c) else "跨境管道（H2、气、CO2）"
    if comp == "Line" or c in ("dc", "dedicated plant source", "electricity distribution grid") or c.startswith("ac"):
        return "国内输电与配电"
    if "boiler" in c or "heat pump" in c or "useful heat" in c:
        return "工业供热"
    if "process emissions" in c:
        return "CO2 捕集、运输、封存与 DAC"
    if "battery" in c:
        return "固定式电池"
    if "h2" in c or "electrolysis" in c or "fuel cell" in c or c.startswith("smr"):
        return "氢储与电解（含 SMR）"
    if "solar" in c:
        return "光伏"
    if "wind" in c:
        return "风电"
    if any(k in c for k in ("ccgt", "ocgt", "lng", "gas production", "gas chp", "gas pipeline")) or c == "gas":
        return "气电与气体燃料"
    if any(k in c for k in ("coal", "lignite", "oil existing", "biomass chp", "solid biomass to electricity", "geothermal", "nuclear")) and "accounting" not in c and "feedstock" not in c:
        return "其他火电与基荷"
    if c in ("hydro", "ror", "phs") or "hydro" in c:
        return "水电"
    if "dac" in c or "co2" in c or "sequest" in c:
        return "CO2 捕集、运输、封存与 DAC"
    if any(k in c for k in ("methanol", "ammonia", "haber", "fischer", "ft ", "oil", "btl", "electrobiofuel", "cracker")):
        return "液体燃料（生产、进口、船运）"
    return "其他"


T = {}
for k, p in RUNS.items():
    n = pypsa.Network(str(p)); T[k] = table(n)
    if k == "V1":
        ev = n.stores[n.stores.carrier == "EV battery"]
        ev_info = dict(standing_loss=sorted(set(ev.standing_loss.round(12))), e_cyclic=sorted(set(ev.e_cyclic)), e_max_pu=sorted(set(ev.e_max_pu)), marginal_cost=sorted(set(ev.marginal_cost)), capital_cost=sorted(set(ev.capital_cost)))
    obj = dict(objective=float(n.objective), objective_constant=float(getattr(n, "objective_constant", 0.0) or 0.0))
    T[k + "_obj"] = obj
    del n
A = pd.concat({k: T[k] for k in ("V1", "V5")}, axis=1).fillna(0.0)
D = pd.DataFrame({"cost_V1_bn": (A["V1"].cap + A["V1"].op) / 1e9, "cost_V5_bn": (A["V5"].cap + A["V5"].op) / 1e9, "cap_V1_bn": A["V1"].cap / 1e9, "cap_V5_bn": A["V5"].cap / 1e9,
                  "op_V1_bn": A["V1"].op / 1e9, "op_V5_bn": A["V5"].op / 1e9, "gw_V1": A["V1"].gw, "gw_V5": A["V5"].gw, "gwh_V1": A["V1"].gwh, "gwh_V5": A["V5"].gwh, "twh_V1": A["V1"].twh, "twh_V5": A["V5"].twh})
D["diff_V5_minus_V1_bn"] = D.cost_V5_bn - D.cost_V1_bn
D["group"] = [group(c, ca, b) for c, ca, b in D.index]
D.sort_values("diff_V5_minus_V1_bn", key=abs, ascending=False).to_csv(OUT / "COST_V5_V1_BY_CARRIER.csv")
G = D.groupby("group")[["cost_V1_bn", "cost_V5_bn", "diff_V5_minus_V1_bn", "cap_V1_bn", "cap_V5_bn", "op_V1_bn", "op_V5_bn", "gw_V1", "gw_V5", "gwh_V1", "gwh_V5"]].sum()
G = G.reindex(G.diff_V5_minus_V1_bn.abs().sort_values(ascending=False).index)
G.loc["合计"] = G.sum()
G.to_csv(OUT / "COST_V5_V1_BY_GROUP.csv")
obj_diff = (T["V5_obj"]["objective"] + T["V5_obj"]["objective_constant"]) - (T["V1_obj"]["objective"] + T["V1_obj"]["objective_constant"])
res = dict(objective=dict(V1=T["V1_obj"], V5=T["V5_obj"], diff_bn=obj_diff / 1e9), sum_of_groups_bn=float(G.loc["合计", "diff_V5_minus_V1_bn"]),
           closure_residual_bn=float(G.loc["合计", "diff_V5_minus_V1_bn"] - obj_diff / 1e9), ev_store_attributes=ev_info,
           top5_groups=G.drop(index="合计").head(5)[["diff_V5_minus_V1_bn"]].round(4).to_dict()["diff_V5_minus_V1_bn"],
           group_members={g: sorted({f"{c}:{ca}{(':' + b) if b else ''}" for (c, ca, b) in D[D.group == g].index if abs(D.loc[(c, ca, b), "diff_V5_minus_V1_bn"]) > 1e-4}) for g in G.index if g != "合计"})
KEY = [("Store", "battery", "", "gwh"), ("Link", "battery charger", "domestic", "gw"), ("Link", "H2 Electrolysis", "domestic", "gw"), ("Store", "H2 Store Tank", "", "gwh"),
       ("Link", "SMR CC", "domestic", "gw"), ("Link", "H2 pipeline", "domestic", "gw"), ("Link", "H2 pipeline", "cross_border", "gw"), ("Generator", "solar", "", "gw"),
       ("Generator", "solar rooftop", "", "gw"), ("Generator", "onwind", "", "gw"), ("Link", "CCGT existing", "domestic", "gw"), ("Link", "OCGT", "domestic", "gw"),
       ("Generator", "LNG import", "", "gw"), ("Generator", "gas production", "", "gw"), ("Link", "coal existing", "domestic", "gw"), ("StorageUnit", "hydro", "", "gw"),
       ("Line", "AC line", "cross_border", "gw"), ("Link", "DC", "cross_border", "gw"), ("Line", "AC line", "domestic", "gw"), ("Link", "DC", "domestic", "gw"),
       ("Link", "BEV charger", "domestic", "gw"), ("Store", "EV battery", "", "gwh"), ("Link", "process emissions CC", "domestic", "gw"), ("Link", "DAC", "domestic", "gw")]
kc = []
for c, ca, b, unit in KEY:
    key = next((k for k in D.index if k[0] == c and k[1] == ca and (k[2] == b or (b == "" and k[2] in ("", "nan")))), None)
    if key is None:
        kc.append(dict(component=c, carrier=ca, border=b, unit=unit, missing=True)); continue
    z = D.loc[key]
    kc.append(dict(component=c, carrier=ca, border=b, unit=("GWh" if unit == "gwh" else "GW"), V1=float(z[unit + "_V1"]), V5=float(z[unit + "_V5"]), twh_V1=float(z.twh_V1), twh_V5=float(z.twh_V5), cost_diff_bn=float(z.diff_V5_minus_V1_bn)))
K = pd.DataFrame(kc); K.to_csv(OUT / "KEY_CAPACITY_V5_V1.csv", index=False); res["key_capacity"] = kc
(OUT / "COST_V5_V1_SUMMARY.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str) + "\n")
print(K.round(3).to_string())
pd.set_option("display.width", 260, "display.max_columns", 20, "display.max_rows", 80)
print(G.round(3).to_string())
print(json.dumps({k: v for k, v in res.items() if k != "group_members"}, ensure_ascii=False, default=str))
print(D.sort_values("diff_V5_minus_V1_bn", key=abs, ascending=False).head(30)[["group", "diff_V5_minus_V1_bn", "gw_V1", "gw_V5", "gwh_V1", "gwh_V5", "twh_V1", "twh_V5"]].round(3).to_string())
print(json.dumps(res["group_members"], ensure_ascii=False)[:3000])
