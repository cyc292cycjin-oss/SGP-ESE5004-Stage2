"""X20 C 段（决策 253 第 ② 项、决策 252 第 2 点）：按等级的陆上风电候选 CF 与 v5 / 参照比值表，以及存量风电 CF 与 Ember 实测对照。只读，不求解。

(A) 等级表（三种口径：v4 = calibrated_modern、B = calibrated_gwa_v5、C-2 = calibrated_gwa_v5q）：按 s4a_profiles.py 的同一规则重算每个格点的年 CF
    （作者 layout 潜力、节点区域、覆盖率归一的权重 w[b,c]），每个节点在 [cf_min, cf_max] 间线性分 3 级；每级：潜力、潜力加权模型 CF、
    同一批格点的潜力加权 GWA IEC3 毛值（X03 cache/onwind_cells/onwind_node_cells.csv，按节点与格点坐标匹配）。国别 × 等级聚合（潜力加权）；
    参照 = GWA 毛值 ÷ r（r 同 ONWIND_SANITY_V5.csv），比值 = 模型 CF ÷ 参照。另列网络口径：三套 F1 网络（c2off = v4 数据、v5main = B、c2main = C-2）
    候选 c0 / c1 / c2 的 p_nom_max 加权年均 p_max_pu（含构建时 clip_p_max_pu 规则）。
(B) 存量陆上风电（'onwind existing'）p_nom 加权年 CF：v4（c2off）、B（v5main）、C-2（c2main），对照 Ember 实测（WIND_CALIBRATION_ALPHA_V5.csv cf_obs，
    2019-2025 中位数，风电校准所用同一套数）；注意 2050 年存量机组与 2019-2025 年的实测风场不是同一批机组。
(C) BN 的网络口径下降：同一 C-2 剖面文件在 clip_p_max_pu 之前与网络值（之后）对照。
用法：python 90_class_table.py   输出 evidence/C2_ONWIND_CLASS_TABLE.csv、C2_EXISTING_WIND_VS_EMBER.csv、C2_CLIP_EFFECT.csv、C2_CLASS_TABLE.json"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

R = Path("/home/jin/wt_v5_x20"); sys.path.insert(0, str(R / "scripts_project"))
D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
X03 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x03_renew_20261111")
import s4a_profiles as S   # noqa: E402

NCLS = 3
ref = pd.read_csv(D / "ONWIND_SANITY_V5.csv").set_index("country")
r_c = ref.r.to_dict()


def cell_cf(cutout, onshore, var):
    spec = S.VARIANTS[var]["onwind"]; plain = {k: v for k, v in spec.items() if k not in S.NON_ATLITE_KEYS}
    if var == "calibrated_modern":
        cut, _ = S.alpha_cutout(cutout, onshore, R / "research_inputs/renewable_v5/WIND_CALIBRATION_ALPHA.csv", spec["alpha"])
        corr, cf = S.convert(cut, plain, capacity_factor=True); return (corr * cf).fillna(0.0).load().values.astype(np.float64)
    tab = R / spec["alpha_table"]
    if var == "calibrated_gwa_v5":
        cut, _ = S.alpha_cutout(cutout, onshore, tab, spec["alpha"], R / spec["cell_factor"])
        corr, cf = S.convert(cut, plain, capacity_factor=True); return (corr * cf).fillna(0.0).load().values.astype(np.float64)
    Q = xr.open_dataset(R / spec["cell_quantiles"]).load(); acc = None
    for j in Q.q.values:
        f = xr.DataArray(Q.factor.sel(q=j).values, coords=dict(y=cutout.data.y, x=cutout.data.x), dims=["y", "x"])
        cut, _ = S.alpha_cutout(cutout, onshore, tab, spec["alpha"], f)
        corr, cq = S.convert(cut, plain, capacity_factor=True)
        t = cq.fillna(0.0).load().values.astype(np.float64) * Q.weight.sel(q=j).values
        acc = t if acc is None else acc + t
        del cut
    return corr * acc


def main():
    import atlite
    import geopandas as gpd
    cutout = atlite.Cutout(str(S.CUTOUT))
    nodes = pd.read_csv(S.NODES, index_col=0)
    onshore = gpd.read_file(S.AUTHOR / "shapes/country_shapes.geojson").set_index("name")
    reg = S.node_regions(nodes, onshore, "onshore")
    pot = S.author_potential("onwind", cutout)
    I_arr = cutout.indicatormatrix(reg.geometry).toarray().reshape(len(reg), len(cutout.data.y), len(cutout.data.x))
    cov = I_arr.sum(axis=0); pot_eff = np.where(cov > 0, pot.values / np.maximum(cov, 1e-12), 0.0)
    xs, ys = np.round(cutout.data.x.values, 3), np.round(cutout.data.y.values, 3)
    cells = pd.read_csv(X03 / "cache/onwind_cells/onwind_node_cells.csv")
    gwa = {(r.node, round(float(r.x), 3), round(float(r.y), 3)): float(r.gwa_cf_iec3) for r in cells.itertuples()}
    rows, miss = [], 0
    for var, lab in (("calibrated_modern", "v4"), ("calibrated_gwa_v5", "B"), ("calibrated_gwa_v5q", "C2")):
        cfv = cell_cf(cutout, onshore, var)
        for b, node in enumerate(reg.index):
            w = I_arr[b] * pot_eff
            if w.sum() <= 0:
                continue
            sel = w > 0; cmin, cmax = float(cfv[sel].min()), float(cfv[sel].max())
            edges = cmin + (cmax - cmin) * np.linspace(0, 1, NCLS + 1)
            iy, ix = np.nonzero(sel)
            g = np.array([gwa.get((node, xs[j], ys[i]), np.nan) for i, j in zip(iy, ix)])
            miss += int(np.isnan(g).sum())
            for k in range(NCLS):
                m = sel & (cfv >= edges[k]) & ((cfv < edges[k + 1]) if k < NCLS - 1 else (cfv <= cmax))
                if not m.any():
                    continue
                mk = m[iy, ix]; wk = w[iy, ix][mk]; gk = g[mk]; ok = np.isfinite(gk)
                rows.append(dict(set=lab, variant=var, node=node, country=reg.at[node, "country"], cls=k, potential_mw=float(wk.sum()), cf=float((wk * cfv[iy, ix][mk]).sum() / wk.sum()),
                                 gwa_gross=float((wk[ok] * gk[ok]).sum() / wk[ok].sum()) if ok.any() else np.nan, gwa_weight_share=float(wk[ok].sum() / wk.sum())))
        print(var, "done", flush=True)
    T = pd.DataFrame(rows)
    agg = []
    for (lab, c, k), d in T.groupby(["set", "country", "cls"]):
        p = d.potential_mw; cf = float((p * d.cf).sum() / p.sum()); okd = d[d.gwa_gross.notna()]
        gg = float((okd.potential_mw * okd.gwa_gross).sum() / okd.potential_mw.sum()) if len(okd) else np.nan
        rr = r_c.get(c, np.nan); refv = gg / rr
        agg.append(dict(set=lab, country=c, cls=k, potential_gw=float(p.sum()) / 1e3, cf_model=cf, gwa_gross=gg, r=rr, reference=refv, ratio=cf / refv if refv else np.nan))
    A = pd.DataFrame(agg)
    # network-side class CF (with the build clip rule)
    import pypsa
    netrows = []
    for lab, sub in (("v4", "c2off"), ("B", "v5main"), ("C2", "c2main")):
        n = pypsa.Network(str(D / f"builds/{sub}/integrated/integrated_2920_3h_unsolved.nc"))
        g = n.generators; cty = g.bus.map(n.buses.country); w = n.snapshot_weightings.generators; P = n.generators_t.p_max_pu
        cand = g.index[(g.carrier == "onwind") & g.p_nom_extendable]
        cls = pd.Series([2 if str(x).endswith(" c2") else (1 if str(x).endswith(" c1") else 0) for x in cand], index=cand)
        for (c, k), names in pd.Series(cand, index=cand).groupby([cty.reindex(cand), cls]):
            cols = [x for x in names if x in P.columns]; cap = g.loc[cols, "p_nom_max"]
            cf = (P[cols].mul(w, axis=0).sum() / w.sum())
            netrows.append(dict(set=lab, country=c, cls=int(k), cf_network=float((cf * cap).sum() / cap.sum()), p_nom_max_gw=float(cap.sum()) / 1e3))
        ex = g.index[g.carrier == "onwind existing"]
        for c, names in pd.Series(ex, index=ex).groupby(cty.reindex(ex)):
            cols = [x for x in names if x in P.columns]; cap = g.loc[cols, "p_nom"]
            cf = (P[cols].mul(w, axis=0).sum() / w.sum())
            netrows.append(dict(set=lab, country=c, cls="existing", cf_network=float((cf * cap).sum() / cap.sum()), p_nom_max_gw=float(cap.sum()) / 1e3))
        if lab == "C2":   # clip effect: C-2 profile file before the build clip rule vs the network
            clip = float(((n.meta.get("research_config") or {}).get("renewable") or {}).get("clip_p_max_pu", 0.0))
            ds = xr.open_dataset(R / "research_inputs/renewable_v5/profiles_calibrated_gwa_v5q_c3_3h.nc"); prof = ds["onwind"].to_pandas(); ds.close()
            ce = []
            for c in sorted(set(cty.reindex(cand).dropna())):
                names = [x for x in cand if cty[x] == c and x in P.columns]; cap = g.loc[names, "p_nom_max"]
                def key(x):
                    k = 2 if str(x).endswith(" c2") else (1 if str(x).endswith(" c1") else 0); return f"{g.at[x, 'bus']}|{k}"
                raw = pd.Series({x: float((prof[key(x)].values * w.values).sum() / w.sum()) for x in names if key(x) in prof.columns})
                net = (P[names].mul(w, axis=0).sum() / w.sum())
                below = float(np.mean([(prof[key(x)].values < clip).mean() for x in names if key(x) in prof.columns]))
                ce.append(dict(country=c, clip=clip, cf_profile_before_clip=float((raw * cap[raw.index]).sum() / cap[raw.index].sum()), cf_network_after_clip=float((net * cap).sum() / cap.sum()),
                               share_of_values_below_clip=below))
            pd.DataFrame(ce).to_csv(D / "evidence/C2_CLIP_EFFECT.csv", index=False, lineterminator="\n")
        del n
    N = pd.DataFrame(netrows)
    cand_tab = A.merge(N[N.cls != "existing"].astype({"cls": int}), on=["set", "country", "cls"], how="outer")
    cand_tab["ratio_network"] = cand_tab.cf_network / cand_tab.reference
    cand_tab.to_csv(D / "evidence/C2_ONWIND_CLASS_TABLE.csv", index=False, lineterminator="\n")
    al = pd.read_csv(R / "research_inputs/renewable_v5/WIND_CALIBRATION_ALPHA_V5.csv").set_index("country")
    E = N[N.cls == "existing"].pivot(index="country", columns="set", values="cf_network")
    E["p_nom_gw_C2"] = N[(N.cls == "existing") & (N.set == "C2")].set_index("country").p_nom_max_gw
    E["ember_cf_obs"] = al.cf_obs.reindex(E.index)
    E.to_csv(D / "evidence/C2_EXISTING_WIND_VS_EMBER.csv", lineterminator="\n")
    (D / "evidence/C2_CLASS_TABLE.json").write_text(json.dumps(dict(gwa_cells_missing=miss, rule=__doc__.split("\n")[2]), indent=1) + "\n")
    pd.set_option("display.width", 250)
    print(cand_tab.pivot_table(index=["country", "cls"], columns="set", values=["cf_model", "ratio", "ratio_network"]).round(3).to_string())
    print(E.round(4).to_string()); print("gwa cells missing", miss)
    print(pd.read_csv(D / "evidence/C2_CLIP_EFFECT.csv").round(4).to_string())


if __name__ == "__main__":
    main()
