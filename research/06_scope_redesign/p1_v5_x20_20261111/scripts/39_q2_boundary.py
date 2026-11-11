"""X20 ②5 / Q2（决策 246 (b)，补记 §2）：S1 冻结存量中 RetirementYear == 2050 的边界机组逐台去向，以及 v5 GEM 新增表与冻结存量 / S2 地热路径不重复的核查。
只读：S1 存活 JSON、电力底座 meta（netCDF 属性，不加载数组）、GIPT 抽取表、FLEET_ADDITIONS_2050(.csv / _V5.csv)。输出写 D 盘 evidence/。"""
import json
import math
import sys
from pathlib import Path

import netCDF4
import pandas as pd

WT = Path("/home/jin/wt_v5_x20")
sys.path.insert(0, str(WT / "scripts_project"))
from d1_common import SRC_DIR   # noqa: E402
from v5_common import s1_geothermal_in_service   # noqa: E402

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
EV = D / "evidence"
S1 = WT / "research/06_scope_redesign/p1_step1_20261015/evidence/S1_SELECTED_ASSET_SURVIVAL_2050.json"
EB = WT / "results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc"
F = WT / "research_inputs/fleet_v5"

ds = netCDF4.Dataset(EB); ids = json.loads(ds.getncattr("meta"))["existing_unit_components"]; ds.close()
gem = pd.read_csv(SRC_DIR / "GEM_GIPT_2026-09_ASEAN11.csv", low_memory=False).set_index("GEM unit/phase ID")
w14 = pd.read_csv(F / "FLEET_ADDITIONS_2050.csv", dtype={"gem_unit_id": str})
v5 = pd.read_csv(F / "FLEET_ADDITIONS_2050_V5.csv", dtype={"gem_unit_id": str})
S = json.loads(S1.read_text())
rec = S["unit_evidence"]["records"]
geo40 = {str(r["AssetID"]).replace("GEM:", "") for r in s1_geothermal_in_service(S1, "inclusive", 40)}


def km(a, b, c, d):
    p = math.pi / 180
    h = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


# ---- 1. boundary units -------------------------------------------------------------------------------------------------------
rows = []
for r in rec:
    if str(r.get("RetirementYear"))[:4] != "2050" or r.get("Technology") == "Geothermal":
        continue
    gid = str(r["AssetID"]).replace("GEM:", "")
    g = gem.loc[gid] if gid in gem.index else None
    in_frozen = r["AssetID"] in ids
    in_v5 = gid in set(v5.gem_unit_id); in_w14 = gid in set(w14.gem_unit_id)
    # match by name / country / capacity / start year / coordinates when the GEM ID is not in the V5 table (addendum section 2, step 2)
    alt = []
    if not in_v5 and g is not None:
        for _, a in v5[v5.country == r["Country"]].iterrows():
            if a.plant == g["Plant / Project name"] or (abs(float(a.capacity_mw) - float(r["OriginalCapacity"])) < 0.5 and km(float(a.Latitude), float(a.Longitude), float(g.Latitude), float(g.Longitude)) <= 5.0):
                alt.append(f"{a.gem_unit_id} {a.plant} {a.unit} {a.capacity_mw} MW {a.start_year}")
    if in_frozen and in_v5:
        fate = "DUPLICATE"
    elif in_v5:
        fate = "ENTERS_VIA_GEM_ADDITIONS"
    else:
        fate = "NOT_ENTERED"
    rows.append(dict(asset_id=r["AssetID"], country=r["Country"], technology=r["Technology"], s1_capacity_mw=float(r["OriginalCapacity"]), s1_commissioning=r["CommissioningYear"],
                     s1_retirement=r["RetirementYear"], s1_status=r["SurvivalStatus"], s1_lifetime=r.get("Lifetime"), in_frozen_identities=in_frozen, in_w14_additions=in_w14, in_v5_additions=in_v5,
                     gipt_status=(g.Status if g is not None else "not in GIPT"), gipt_start_year=(g["Start year"] if g is not None else None), gipt_capacity_mw=(g["Capacity (MW)"] if g is not None else None),
                     gipt_plant=(g["Plant / Project name"] if g is not None else None), gipt_unit=(g["Unit / Phase name"] if g is not None else None),
                     v5_node=(v5.loc[v5.gem_unit_id == gid, "node"].iloc[0] if in_v5 else None), v5_retire_year=(v5.loc[v5.gem_unit_id == gid, "retire_year"].iloc[0] if in_v5 else None),
                     name_coord_matches_in_v5=" | ".join(alt), fate=fate))
b = pd.DataFrame(rows).sort_values(["country", "asset_id"])
b.to_csv(EV / "Q2_BOUNDARY_UNITS.csv", index=False, lineterminator="\n")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print("boundary units (RetirementYear 2050, S1):", len(b), "MW", round(b.s1_capacity_mw.sum(), 1))
print(b[["asset_id", "country", "technology", "s1_capacity_mw", "s1_commissioning", "in_frozen_identities", "in_w14_additions", "in_v5_additions", "gipt_status", "gipt_start_year", "gipt_capacity_mw", "gipt_plant", "gipt_unit", "v5_node", "fate"]].to_string(index=False))

# ---- 2. no double count of the whole V5 table ------------------------------------------------------------------------------------
frozen_gem = {k.replace("GEM:", "") for k in ids if k.startswith("GEM:")}
c1 = sorted(set(v5.gem_unit_id) & frozen_gem)
c2 = sorted(set(v5.gem_unit_id) & geo40)
# same physical unit under another ID: (country, plant, unit name) of the frozen GEM identities (via GIPT) vs the V5 additions
fz = gem.loc[[g for g in frozen_gem if g in gem.index], ["iso", "Plant / Project name", "Unit / Phase name", "Capacity (MW)"]]
key_f = set(zip(fz.iso, fz["Plant / Project name"], fz["Unit / Phase name"].astype(str)))
c3 = [f"{a.gem_unit_id} {a.country} {a.plant} {a.unit}" for a in v5.itertuples() if (a.country, a.plant, str(a.unit)) in key_f]
c4 = int(v5.gem_unit_id.duplicated().sum())
nongem = {k: v for k, v in ids.items() if not k.startswith("GEM:")}
c5 = []
for k, v in nongem.items():
    for a in v5.itertuples():
        if a.node == v.get("node") and abs(float(a.capacity_mw) - float(v.get("capacity_mw", -1))) < 0.5:
            c5.append(f"{k} ({v.get('capacity_mw')} MW at {v.get('node')}) vs {a.gem_unit_id} {a.plant}")
diff_new = v5[~v5.gem_unit_id.isin(w14.gem_unit_id)]; diff_gone = w14[~w14.gem_unit_id.isin(v5.gem_unit_id)]
both = v5.merge(w14, on="gem_unit_id", suffixes=("_v5", "_w14"))
changed = both[(both.lifetime_v5 != both.lifetime_w14) | (both.node_v5 != both.node_w14) | (both.capacity_mw_v5 != both.capacity_mw_w14)]
res = dict(v5_rows=int(len(v5)), v5_mw=float(v5.capacity_mw.sum()), w14_rows=int(len(w14)), w14_mw=float(w14.capacity_mw.sum()),
           new_rows=int(len(diff_new)), new_mw=float(diff_new.capacity_mw.sum()), removed_rows=int(len(diff_gone)), removed_mw=float(diff_gone.capacity_mw.sum()),
           removed_units=diff_gone[["gem_unit_id", "country", "plant", "unit", "model_class", "capacity_mw", "start_year"]].to_dict("records"),
           lifetime_or_node_changed=int(len(changed)), new_by_country_class={f"{c}|{k}": v for (c, k), v in diff_new.groupby(["country", "model_class"]).capacity_mw.sum().round(1).items()},
           new_by_reason=dict(boundary_only=float(diff_new[(diff_new.retire_year == 2050)].capacity_mw.sum()),
                              geothermal_40a=float(diff_new[(diff_new.model_class == "geothermal existing")].capacity_mw.sum())),
           checks=dict(v5_ids_in_frozen_identities=c1, v5_ids_in_s2_geothermal_40a=c2, same_plant_unit_as_frozen=c3, duplicate_ids_in_v5=c4, nongem_frozen_same_node_capacity=c5),
           boundary_units=dict(units=int(len(b)), mw=float(b.s1_capacity_mw.sum()), fate=b.groupby("fate").s1_capacity_mw.agg(["count", "sum"]).to_dict("index")),
           s2_geothermal_40a=dict(units=len(geo40), ids=sorted(geo40)))
pd.DataFrame([dict(change="new", **r) for r in diff_new.to_dict("records")] + [dict(change="removed", **r) for r in diff_gone.to_dict("records")]).to_csv(
    EV / "FLEET_ADDITIONS_V5_VS_W14.csv", index=False, lineterminator="\n")
(EV / "Q2_NO_DOUBLE_COUNT.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
print(json.dumps({k: v for k, v in res.items() if k not in ("new_by_country_class",)}, indent=1, default=str)[:6000])
print("new by country / class MW:"); print(diff_new.groupby(["country", "model_class"]).capacity_mw.sum().round(1).to_string())
