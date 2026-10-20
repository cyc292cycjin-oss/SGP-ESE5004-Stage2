"""S4P aspects 1, 2, 3, 5, 6, 7, 8 and analysis B from the extracted network tables (evidence/net/NET_*.csv), the
cloud exports (cross_border_flows.csv, CAPACITY_BY_TECH_COUNTRY.json, CO2_FLOWS.json, LEDGER_IDENTITY.json, NODAL_PRICES.csv)
and the ledger details. Read-only. Writes ASPECT_*.csv/.md and ASPECTS_SUMMARY.json."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4p_paths import BN_, COUNTRIES, OUT, RUNS, dump_json, ledger_detail, ledger_total, load_json, md_table  # noqa: E402

NET = OUT / "evidence" / "net"
H = 8760.0
SOLVED = ["disconnected", "integrated_nze"]
STRUCT = {"integrated": "integrated_unsolved", "disconnected": "disconnected_unsolved"}
EXTRA_GEN = ["H2 import", "LNG import", "FT fuel import", "ammonia import", "methanol import", "oil import", "coal", "lignite"]
MD = []
SUMMARY = {}


def net(label, table):
    return pd.read_csv(NET / f"NET_{label}_{table}.csv", index_col=0)


def section(title):
    MD.append(f"\n## {title}\n")


def put(df, fmt="{:,.3f}"):
    MD.append(md_table(df.reset_index() if df.index.name or not isinstance(df.index, pd.RangeIndex) else df, fmt))
    MD.append("")


# ------------------------------------------------------------------ aspect 1: extra-ASEAN fall-back options
def aspect1():
    section("方面 1：区域外兜底选项（价格、上限、各国各情景用量）")
    gi = net("integrated_unsolved", "generators"); gd = net("disconnected_unsolved", "generators")
    ex = gi[gi.carrier.isin(EXTRA_GEN)].copy()
    ex["country"] = ex.country.replace("", "ASEAN").fillna("ASEAN")
    struct = ex.groupby(["carrier", "country"]).agg(n=("bus", "size"), p_nom_mw=("p_nom", "sum"), p_nom_max_mw=("p_nom_max", "sum"),
                                                     mc_eur_mwh=("marginal_cost", "mean"), capex_eur_mw_a=("capital_cost", "mean"), bus=("bus", lambda s: ";".join(sorted(s)[:3])))
    # same structure in the disconnected build?
    exd = gd[gd.carrier.isin(EXTRA_GEN)]
    same = (len(exd) == len(ex)) and np.allclose(exd.reindex(ex.index).p_nom_max.replace(np.inf, 1e15).values, ex.p_nom_max.replace(np.inf, 1e15).values) and np.allclose(exd.reindex(ex.index).marginal_cost.values, ex.marginal_cost.values)
    MD.append(f"- 一体化与不互联构建网络中的区域外发电机（进口）集合、`p_nom_max`、`marginal_cost` 是否完全相同：**{same}**（不互联只断开区域内跨境网络组件，区域外进口不变；`configs/research/disconnected.yaml` 注释与注册表 `s4e1_adjacency_switch` 一致）。")
    MD.append("- 区域外选项的价格（EUR2020/MWh）：H2 import 105.75（注册表 `import_price_hydrogen`，Neumann 2025 欧洲最低 × 1.2），LNG import 27.07（WEO 2025 STEPS 2050 日本 LNG），FT fuel import（非化石油品）150.11，methanol import 145.16，ammonia import 116.78，oil import 35.32（WEO STEPS 2050 原油），coal 8.86，lignite 6.62（成本层）。NZE 情景只改 gas / oil / coal（13.67 / 11.62 / 5.17）。")
    MD.append("")
    t = struct.reset_index()
    t["p_nom_max_mw"] = t.p_nom_max_mw.replace(np.inf, np.nan)
    put(t, "{:,.2f}")
    # usage per scenario
    rows = []
    cap = load_json(RUNS["integrated"] / "CAPACITY_BY_TECH_COUNTRY.json")
    capg = pd.DataFrame(cap.get("Generator", []))
    Li = ledger_detail("integrated")
    for lab in ["integrated"] + SOLVED:
        if lab == "integrated":
            vc = Li[(Li.subject == "variable_cost") & (Li.carrier.isin(EXTRA_GEN))].groupby(["entity", "carrier"]).eur.sum()
            for (e, c), eur in vc.items():
                mc = float(ex[ex.carrier == c].marginal_cost.mean())
                pno = float(capg[(capg.carrier == c) & (capg.country == (e if e != "ASEAN_POOL" else "ASEAN"))].p_nom_opt.sum()) if len(capg) else np.nan
                rows.append(dict(run=lab, entity=e, carrier=c, energy_twh=eur / mc / 1e6 if mc else np.nan, cost_bn=eur / BN_, p_nom_opt_mw=pno, basis="variable_cost / marginal_cost (试点无求解后网络)"))
        else:
            g = net(lab, "generators"); g = g[g.carrier.isin(EXTRA_GEN)].copy(); g["country"] = g.country.replace("", "ASEAN_POOL").fillna("ASEAN_POOL")
            a = g.groupby(["country", "carrier"]).agg(energy_mwh=("energy_mwh", "sum"), p_nom_opt=("p_nom_opt", "sum"), mc=("marginal_cost", "mean"))
            for (e, c), r in a.iterrows():
                rows.append(dict(run=lab, entity=e, carrier=c, energy_twh=r.energy_mwh / 1e6, cost_bn=r.energy_mwh * r.mc / BN_, p_nom_opt_mw=r.p_nom_opt, basis="solved network"))
    use = pd.DataFrame(rows)
    piv = use.pivot_table(index=["carrier", "entity"], columns="run", values="energy_twh", aggfunc="sum").fillna(0.0)
    piv = piv[[c for c in ["integrated", "disconnected", "integrated_nze"] if c in piv]]
    piv["dis_minus_int"] = piv.get("disconnected", 0) - piv.get("integrated", 0)
    MD.append("### 用量（TWh/a；进口发电机的年发电量；coal / lignite 为节点池供应量）")
    put(piv.reset_index(), "{:,.2f}")
    pivc = use.pivot_table(index=["carrier", "entity"], columns="run", values="cost_bn", aggfunc="sum").fillna(0.0)
    pivc = pivc[[c for c in ["integrated", "disconnected", "integrated_nze"] if c in pivc]]
    MD.append("### 成本（bn EUR/a = 用量 × 价格；不含码头投资）")
    put(pivc.reset_index())
    # CO2 extra-ASEAN export use
    co2 = {lab: load_json(RUNS[lab] / "CO2_FLOWS.json") for lab in ["integrated", "disconnected", "integrated_nze"]}
    rows = []
    for c in COUNTRIES:
        r = {"country": c}
        for lab, d in co2.items():
            r[f"{lab}_extra_asean_Mt"] = d["extra_asean_by_country"].get(c, {}).get("exported_t", 0.0) / 1e6
            r[f"{lab}_dac_Mt"] = d["dac_by_country"].get(c, 0.0) / 1e6
        rows.append(r)
    MD.append("### 区域外 CO₂ 封存（Mt/a）与 DAC 捕集（Mt/a）")
    put(pd.DataFrame(rows), "{:,.4f}")
    # H2 / LNG terminal capacities per country (structure)
    term = ex[ex.carrier.isin(["H2 import", "LNG import"])].groupby(["country", "carrier"]).agg(nodes=("bus", "size"), p_nom_mw=("p_nom", "sum"), p_nom_max_mw=("p_nom_max", "sum")).reset_index()
    MD.append("### H₂ / LNG 码头候选（按国；`p_nom` = 存量 LNG 再气化能力，`p_nom_max` = 第 17 项上限 2.5 × 存量或拟建容量；H₂ 码头与 LNG 码头同节点、同上限）")
    put(term, "{:,.0f}")
    SUMMARY["aspect1"] = {"structure_same_int_dis": bool(same), "use_twh": {f"{k[0]}|{k[1]}": v for k, v in piv.to_dict(orient="index").items()},
                          "terminals": term.to_dict(orient="records")}
    use.to_csv(OUT / "ASPECT1_EXTRA_ASEAN_USE.csv", index=False)
    return use


# ------------------------------------------------------------------ aspect 2: cross-border corridors
def aspect2():
    section("方面 2：跨境流动与通道拓扑")
    li = net("integrated_unsolved", "lines"); lk = net("integrated_unsolved", "links")
    xl = li[li.border_class == "cross_border"].copy(); xk = lk[lk.border_class == "cross_border"].copy()
    xl["pair"] = [f"{min(a,b)}-{max(a,b)}" for a, b in zip(xl.country0, xl.country1)]
    xk["pair"] = [f"{min(a,b)}-{max(a,b)}" for a, b in zip(xk.country0, xk.country1)]
    cand = pd.concat([xl.assign(kind="Line", cap=xl.s_nom, capmax=xl.s_nom_max)[["pair", "carrier", "kind", "cap", "capmax", "length"]],
                      xk.assign(kind="Link", cap=xk.p_nom, capmax=xk.p_nom_max)[["pair", "carrier", "kind", "cap", "capmax", "length"]]])
    cand["is_reversed"] = cand.index.str.endswith("-reversed")
    cl = cand[~cand.is_reversed].groupby(["pair", "carrier"]).agg(n=("cap", "size"), stock_mw=("cap", "sum"), max_mw=("capmax", lambda s: s.replace(np.inf, np.nan).sum()), inf=("capmax", lambda s: int(np.isinf(s).sum())), km_mean=("length", "mean")).reset_index()
    MD.append("### 候选通道清单（一体化构建网络；`stock_mw` = 2025 存量，`max_mw` = 扩建上限合计（每条 +20,000 MW，第 96 项；管道无上限 = inf）；反向链路不重复计）")
    put(cl, "{:,.1f}")
    elec = cl[cl.carrier.isin(["AC", "DC"])].groupby("pair").agg(lines=("n", "sum"), stock_mw=("stock_mw", "sum"), max_mw=("max_mw", "sum")).reset_index()
    MD.append("### 各国电力候选通道数（AC + DC）")
    cc = {c: elec[elec.pair.str.contains(c)] for c in COUNTRIES}
    t = pd.DataFrame([{"country": c, "pairs": ";".join(cc[c].pair), "lines": int(cc[c].lines.sum()), "stock_mw": float(cc[c].stock_mw.sum()), "max_mw": float(cc[c].max_mw.sum())} for c in COUNTRIES])
    put(t, "{:,.0f}")
    SUMMARY["aspect2_candidates_by_country"] = t.to_dict(orient="records")
    # flows per scenario
    flows = {}
    for lab in ["integrated", "integrated_nze"]:
        f = pd.read_csv(RUNS[lab] / "cross_border_flows.csv")
        f["pair"] = [f"{min(a,b)}-{max(a,b)}" for a, b in zip(f.country0, f.country1)]
        # orient energies from the lexicographically smaller country to the larger
        swap = f.country0 > f.country1
        f["e_ab"] = np.where(swap, f.energy_1_to_0_mwh, f.energy_0_to_1_mwh)
        f["e_ba"] = np.where(swap, f.energy_0_to_1_mwh, f.energy_1_to_0_mwh)
        f["cap_h"] = f.capacity_opt_mw * H
        flows[lab] = f
        agg = f.groupby(["pair", "carrier"]).agg(n=("component", "size"), cap_opt_mw=("capacity_opt_mw", "sum"), cap_init_mw=("capacity_initial_mw", "sum"),
                                                 e_ab_twh=("e_ab", lambda s: s.sum() / 1e6), e_ba_twh=("e_ba", lambda s: s.sum() / 1e6), cap_h=("cap_h", "sum"), max_abs=("max_abs_flow_mw", "max")).reset_index()
        agg["util_pct"] = 100 * (agg.e_ab_twh + agg.e_ba_twh) * 1e6 / agg.cap_h.replace(0, np.nan)
        agg["net_ab_twh"] = agg.e_ab_twh - agg.e_ba_twh
        MD.append(f"### {lab}：各通道两向年流量（TWh 或 CO₂ Mt·(MWh 单位按 t) ）、容量与利用率（相对 cap_opt × 8760）")
        put(agg[["pair", "carrier", "n", "cap_init_mw", "cap_opt_mw", "e_ab_twh", "e_ba_twh", "net_ab_twh", "util_pct", "max_abs"]], "{:,.2f}")
        SUMMARY[f"aspect2_flows_{lab}"] = agg.to_dict(orient="records")
        # expansion vs the +20,000 MW cap per line (electricity)
        fe = f[f.carrier.isin(["AC", "DC"])].copy()
        fe["added_mw"] = fe.capacity_opt_mw - fe.capacity_initial_mw
        near = fe[fe.added_mw > 0.95 * 20000]
        MD.append(f"- {lab}：单条电力通道扩建接近 20,000 MW 上限（≥ 95 %）的条数：**{len(near)}**；最大单条扩建 {fe.added_mw.max():,.0f} MW（{fe.loc[fe.added_mw.idxmax(), 'component'] if len(fe) else ''}）。")
        MD.append("")
    # country net electricity imports vs demand
    for lab in ["integrated", "integrated_nze"]:
        f = flows[lab]; fe = f[f.carrier.isin(["AC", "DC"])]
        imp = {c: 0.0 for c in COUNTRIES}; expo = {c: 0.0 for c in COUNTRIES}
        for r in fe.itertuples():
            a, b = sorted([r.country0, r.country1])
            imp[b] += r.e_ab; expo[a] += r.e_ab; imp[a] += r.e_ba; expo[b] += r.e_ba
        loads = net("integrated_unsolved", "loads")
        el = loads[loads.bus_carrier.isin(["AC", "Li ion"])].groupby("country_bus").energy_mwh.sum()
        t = pd.DataFrame({"country": COUNTRIES, "gross_import_twh": [imp[c] / 1e6 for c in COUNTRIES], "gross_export_twh": [expo[c] / 1e6 for c in COUNTRIES]})
        t["net_import_twh"] = t.gross_import_twh - t.gross_export_twh
        t["fixed_elec_load_twh"] = [el.get(c, 0.0) / 1e6 for c in COUNTRIES]
        t["net_import_pct_of_load"] = 100 * t.net_import_twh / t.fixed_elec_load_twh.replace(0, np.nan)
        MD.append(f"### {lab}：各国电力净进出口（按通道端点计，含线损前的送端量）与固定电力负荷（AC 母线负荷 + EV 充电负荷）的比例")
        put(t, "{:,.2f}")
        SUMMARY[f"aspect2_net_imports_{lab}"] = t.to_dict(orient="records")
    # generation mix by country (solved nets) for the export-source question
    for lab in SOLVED:
        g = net(lab, "generators"); su = net(lab, "storage_units"); lk = net(lab, "links")
        gen = g[g.bus_carrier.isin(["AC", "DC"])].groupby(["country", "carrier"]).energy_mwh.sum()
        # link-based electricity producers: p1 (negative = delivered to bus1 if bus1 is AC)
        el_links = lk[lk.bus1_carrier.isin(["AC", "DC"]) & ~lk.bus0_carrier.isin(["AC", "DC", "battery", "home battery", "Li ion"])]
        gl = (-el_links.energy_p1_mwh).groupby([el_links.country1, el_links.carrier]).sum()
        hyd = su.groupby(["country", "carrier"]).dispatch_mwh.sum()
        mix = pd.concat([gen, gl, hyd]).groupby(level=[0, 1]).sum().unstack(0).fillna(0.0) / 1e6
        mix = mix.reindex(columns=[c for c in COUNTRIES if c in mix.columns])
        mix = mix[(mix.abs().sum(axis=1) > 0.05)]
        MD.append(f"### {lab}：分国发电量（TWh；发电机 + 向电母线送电的链路 + 水电储能调度）")
        put(mix.round(2))
        SUMMARY[f"aspect2_generation_{lab}"] = mix.to_dict()
    MD.append("- 一体化试点没有求解后网络（完整包未下载），分国发电量结构记 DATA_PENDING（需要 `results_20261019T072454Z_5125.tar.gz` 中的 `integrated_FORMAL_TRIAL_365X24H_solved.nc`）；NZE 为同拓扑的替代参照。")
    return flows


# ------------------------------------------------------------------ aspect 3: technology availability
def aspect3():
    section("方面 3：技术可用性（候选上限与存量，按国）")
    g = net("integrated_unsolved", "generators"); su = net("integrated_unsolved", "storage_units"); lk = net("integrated_unsolved", "links")
    cand = g[g.p_nom_extendable == True]  # noqa: E712
    t = cand.groupby(["carrier", "country"]).p_nom_max.sum().unstack(0)
    t = t.reindex(COUNTRIES)
    t = t[[c for c in ["nuclear", "nuclear SMR", "geothermal", "ror", "offwind-ac", "offwind-dc", "onwind", "solar", "solar rooftop", "H2 import", "LNG import"] if c in t.columns]] / 1e3
    t = t.replace(np.inf, np.nan)
    MD.append("### 可扩建发电机候选上限（GW；NaN = 无上限 inf；缺 = 该国无此候选）")
    put(t.round(2))
    inf = cand[np.isinf(cand.p_nom_max)].groupby(["carrier", "country"]).size().unstack(0).reindex(COUNTRIES).fillna(0).astype(int)
    MD.append("### 无上限（inf）候选的节点数")
    put(inf)
    sut = su[su.p_nom_extendable == True].groupby(["carrier", "country"]).p_nom_max.sum().unstack(0).reindex(COUNTRIES) / 1e3  # noqa: E712
    MD.append("### 可扩建储能候选上限（GW）：hydro / PHS")
    put(sut.replace(np.inf, np.nan).round(2))
    ex = g[~g.p_nom_extendable].groupby(["carrier", "country"]).p_nom.sum().unstack(0).reindex(COUNTRIES) / 1e3
    ex = ex.loc[:, ex.sum() > 0]
    MD.append("### 存量发电机（GW，非扩建）")
    put(ex.round(2))
    sue = su[~su.p_nom_extendable].groupby(["carrier", "country"]).p_nom.sum().unstack(0).reindex(COUNTRIES) / 1e3
    MD.append("### 存量储能单元（GW）")
    put(sue.round(2))
    exl = lk[(~lk.p_nom_extendable) & lk.carrier.str.contains("existing")].groupby(["carrier", "country1"]).p_nom.sum().unstack(0).reindex(COUNTRIES) / 1e3
    MD.append("### 存量火电链路（GW）")
    put(exl.round(2))
    # SMR / nuclear / offwind outcomes per scenario
    cap = load_json(RUNS["integrated"] / "CAPACITY_BY_TECH_COUNTRY.json")
    rows = []
    gi = pd.DataFrame(cap.get("Generator", []))
    for lab in ["integrated"] + SOLVED:
        if lab == "integrated":
            d = gi.groupby(["carrier", "country"]).p_nom_opt.sum()
        else:
            gg = net(lab, "generators"); d = gg.groupby(["carrier", "country"]).p_nom_opt.sum()
        for car in ["nuclear", "nuclear SMR", "geothermal", "offwind-ac", "offwind-dc", "onwind", "solar", "solar rooftop", "ror"]:
            for c in COUNTRIES:
                rows.append(dict(run=lab, carrier=car, country=c, p_nom_opt_gw=d.get((car, c), 0.0) / 1e3))
    r = pd.DataFrame(rows).pivot_table(index=["carrier", "country"], columns="run", values="p_nom_opt_gw").fillna(0.0)
    r = r[["integrated", "disconnected", "integrated_nze"]]
    r = r[(r.abs().sum(axis=1) > 0.01)]
    MD.append("### 各情景新建容量结果（GW，p_nom_opt）：核电 / SMR / 地热 / 风 / 光 / 径流")
    put(r.round(2))
    SUMMARY["aspect3_pnom_opt_gw"] = {f"{k[0]}|{k[1]}": v for k, v in r.to_dict(orient="index").items()}
    SUMMARY["aspect3_candidate_caps_gw"] = t.to_dict()
    # offwind connection cost per country
    ow = g[g.carrier.isin(["offwind-ac", "offwind-dc"])].groupby(["carrier", "country"]).agg(cc_min=("capital_cost", "min"), cc_mean=("capital_cost", "mean"), cc_max=("capital_cost", "max"), pmax_gw=("p_nom_max", lambda s: s.sum() / 1e3), cf=("p_max_pu_mean", "mean")).reset_index()
    MD.append("### 海上风电候选：单位年化成本（EUR/MW/a，含并网）、上限、平均可用率（按国）")
    put(ow, "{:,.3f}")
    SUMMARY["aspect3_offwind"] = ow.to_dict(orient="records")
    on = g[g.carrier.isin(["onwind", "solar"])].groupby(["carrier", "country"]).agg(cc_mean=("capital_cost", "mean"), pmax_gw=("p_nom_max", lambda s: s.sum() / 1e3), cf_mean=("p_max_pu_mean", "mean"), cf_max=("p_max_pu_mean", "max")).reset_index()
    MD.append("### 陆上风、光伏候选：成本、上限、可用率（按国）")
    put(on, "{:,.3f}")
    SUMMARY["aspect3_onwind_solar"] = on.to_dict(orient="records")


# ------------------------------------------------------------------ aspect 5: CO2 storage
def aspect5():
    section("方面 5：CO₂ 封存：潜力、年注入上限、各情景用量、外送依赖")
    s = net("integrated_unsolved", "stores")
    seq = s[s.carrier == "co2 sequestered"][["country", "e_nom_max", "capital_cost", "marginal_cost"]].set_index("country")
    rows = []
    co2 = {lab: load_json(RUNS[lab] / "CO2_FLOWS.json") for lab in ["integrated", "disconnected", "integrated_nze"]}
    for c in COUNTRIES:
        r = {"country": c, "annual_cap_Mt": seq.e_nom_max.get(c, 0.0) / 1e6, "store_cost_eur_t": seq.capital_cost.get(c, np.nan)}
        for lab, d in co2.items():
            r[f"{lab}_seq_Mt"] = d["sequestered_by_country"].get(c, {}).get("final_level_t", 0.0) / 1e6
            r[f"{lab}_extra_Mt"] = d["extra_asean_by_country"].get(c, {}).get("exported_t", 0.0) / 1e6
            ship_out = sum(v["t"] for k, v in d["intra_asean_shipping"].items() if k.startswith(c + "->")) / 1e6
            ship_in = sum(v["t"] for k, v in d["intra_asean_shipping"].items() if k.endswith("->" + c)) / 1e6
            r[f"{lab}_ship_out_Mt"] = ship_out; r[f"{lab}_ship_in_Mt"] = ship_in
            r[f"{lab}_dac_Mt"] = d["dac_by_country"].get(c, 0.0) / 1e6
        rows.append(r)
    t = pd.DataFrame(rows)
    t["int_cap_util_pct"] = 100 * t.integrated_seq_Mt / t.annual_cap_Mt.replace(0, np.nan)
    t["dis_cap_util_pct"] = 100 * t.disconnected_seq_Mt / t.annual_cap_Mt.replace(0, np.nan)
    put(t, "{:,.3f}")
    # pipeline cross-border CO2 per pair per scenario
    for lab in ["integrated", "integrated_nze"]:
        cb = co2[lab]["cross_border_pipeline"]
        agg = {}
        for k, v in cb.items():
            key = f"{v['from_country']}->{v['to_country']}"
            agg[key] = agg.get(key, 0.0) + v["net_t_0_to_1"] / 1e6
        MD.append(f"- {lab} 跨境 CO₂ 管道净流量（Mt/a，from->to 为正）：" + ", ".join(f"{k} {v:.2f}" for k, v in sorted(agg.items(), key=lambda kv: -abs(kv[1])) if abs(v) > 0.01))
    # CO2 price duals
    for lab in SOLVED:
        b = net(lab, "buses")
        p = b[b.carrier == "co2 stored"].groupby("country").price_mean_w.mean()
        q = b[b.carrier == "co2 sequestered"].groupby("country").price_mean_w.mean()
        MD.append(f"- {lab}：`co2 stored` 母线年均对偶（EUR/t，按国均值）：" + ", ".join(f"{c} {p.get(c, np.nan):.1f}" for c in COUNTRIES) + "；`co2 sequestered` 封存库对偶：" + ", ".join(f"{c} {q.get(c, np.nan):.1f}" for c in q.index))
    MD.append("")
    SUMMARY["aspect5"] = t.to_dict(orient="records")
    t.to_csv(OUT / "ASPECT5_CO2.csv", index=False)


# ------------------------------------------------------------------ aspect 6: biomass
def aspect6():
    section("方面 6：生物质：潜力（池容量）、固定需求占比、影子价格")
    s = net("integrated_unsolved", "stores")
    bio = s[s.carrier == "solid biomass"].groupby("country").agg(pools=("bus", "size"), e_nom_twh=("e_nom", lambda x: x.sum() / 1e6), mc_min=("marginal_cost", "min"), mc_max=("marginal_cost", "max"))
    loads = net("integrated_unsolved", "loads")
    fixed = loads[loads.carrier == "biomass final energy"].groupby("country_bus").energy_mwh.sum() / 1e6
    bio["fixed_biomass_final_twh"] = fixed.reindex(bio.index).fillna(0.0)
    bio["fixed_over_pool_pct"] = 100 * bio.fixed_biomass_final_twh / bio.e_nom_twh
    # shadow prices
    nod = pd.read_csv(RUNS["integrated"] / "NODAL_PRICES.csv", usecols=["bus", "carrier", "country", "mean", "min", "max"])
    sp = nod[nod.carrier == "solid biomass"].groupby("country")["mean"].mean()
    bio["int_solid_biomass_price_mean"] = sp.reindex(bio.index)
    for lab in SOLVED:
        b = net(lab, "buses")
        bio[f"{lab[:3]}_solid_biomass_price_mean"] = b[b.carrier == "solid biomass"].groupby("country").price_mean_w.mean().reindex(bio.index)
        st = net(lab, "stores"); st = st[st.carrier == "solid biomass"]
        bio[f"{lab[:3]}_withdraw_twh"] = st.groupby("country").p_withdraw_mwh.sum().reindex(bio.index) / 1e6
    bio = bio.reindex(COUNTRIES)
    put(bio.round(3))
    MD.append("- 池的 `marginal_cost` = 原料成本（EUR/MWh）；母线价格 − 原料成本 = 稀缺租。第 115 项：BN / SG / VN 固定需求 = 0.98 × 潜力（其余 2 % 转甲烷）。")
    SUMMARY["aspect6"] = bio.to_dict(orient="index")
    bio.to_csv(OUT / "ASPECT6_BIOMASS.csv")


# ------------------------------------------------------------------ aspect 7: cost parameters per country
def aspect7():
    section("方面 7：成本参数：各国是否存在系统性差异（原则 8）")
    g = net("integrated_unsolved", "generators")
    cand = g[g.p_nom_extendable == True]  # noqa: E712
    t = cand.groupby(["carrier", "country"]).capital_cost.mean().unstack(0).reindex(COUNTRIES)
    t = t[[c for c in ["nuclear", "nuclear SMR", "geothermal", "ror", "offwind-ac", "offwind-dc", "onwind", "solar", "solar rooftop", "H2 import", "LNG import"] if c in t.columns]]
    MD.append("### 候选发电机年化单位投资（EUR/MW/a，按国平均）")
    put(t.round(0), "{:,.0f}")
    var = (t.max() / t.min() - 1) * 100
    MD.append("- 各载体跨国最大/最小之比 − 1（%）：" + ", ".join(f"{k} {v:.1f}" for k, v in var.items()))
    lk = net("integrated_unsolved", "links")
    lc = lk[lk.p_nom_extendable == True]  # noqa: E712
    t2 = lc.groupby(["carrier", "country1"]).capital_cost.mean().unstack(0).reindex(COUNTRIES)
    t2 = t2[[c for c in ["CCGT", "CCGT CC", "OCGT", "H2 Electrolysis", "SMR", "SMR CC", "DAC", "Fischer-Tropsch", "industry heat pump", "battery charger", "CO2 sequestration"] if c in t2.columns]]
    MD.append("### 候选链路年化单位投资（EUR/MW/a，按国平均；按 bus1 国家）")
    put(t2.round(0), "{:,.0f}")
    var2 = (t2.max() / t2.min() - 1) * 100
    MD.append("- 跨国差异（%）：" + ", ".join(f"{k} {v:.1f}" for k, v in var2.items()))
    mc = cand.groupby(["carrier", "country"]).marginal_cost.mean().unstack(0).reindex(COUNTRIES)
    mc = mc[[c for c in ["coal", "lignite", "gas production", "LNG import", "H2 import"] if c in mc.columns]]
    MD.append("### 燃料 / 进口边际成本（EUR/MWh，按国）")
    put(mc.round(2))
    SUMMARY["aspect7_capex_gen"] = t.to_dict(); SUMMARY["aspect7_capex_link"] = t2.to_dict()


# ------------------------------------------------------------------ aspect 8: settlement rules
def aspect8():
    section("方面 8：结算规则：分国拆分如何随规则变化（只用已有结果）")
    rules = {}
    for lab in ["integrated", "integrated_nze"]:
        L = ledger_detail(lab); T = ledger_total(lab)
        ident = load_json(RUNS[lab] / "LEDGER_IDENTITY.json")
        corr = ident["diagnostics"]["corridors"]   # XB:A|B -> costs, settlement, net (net = corridor surplus incl. costs)
        f = pd.read_csv(RUNS[lab] / "cross_border_flows.csv")
        # importer of a pair: net electricity flow direction (AC+DC); fall back to all carriers
        imp = {}
        for pair, grp in f.groupby([f[["country0", "country1"]].min(axis=1), f[["country0", "country1"]].max(axis=1)]):
            a, b = pair
            ge = grp[grp.carrier.isin(["AC", "DC"])]
            if not len(ge):
                ge = grp
            e_ab = np.where(ge.country0 == a, ge.energy_0_to_1_mwh, ge.energy_1_to_0_mwh).sum()
            e_ba = np.where(ge.country0 == a, ge.energy_1_to_0_mwh, ge.energy_0_to_1_mwh).sum()
            imp[f"XB:{a}|{b}"] = (b if e_ab > e_ba else a, a if e_ab > e_ba else b, e_ab / 1e6, e_ba / 1e6)
        base = T["total"].reindex(COUNTRIES)
        rent_half = L[(L.subject == "xb_share_congestion_rent")].groupby("entity").eur.sum().reindex(COUNTRIES).fillna(0.0)
        infra_half = L[(L.subject == "xb_share_infrastructure_cost")].groupby("entity").eur.sum().reindex(COUNTRIES).fillna(0.0)
        trade = L[L.subject.str.startswith("network_trade")].groupby("entity").eur.sum().reindex(COUNTRIES).fillna(0.0)
        pools = L[L.subject.str.startswith("liquid_pool")].groupby("entity").eur.sum().reindex(COUNTRIES).fillna(0.0)
        co2s = L[L.subject.isin(["co2_storage_service"])].groupby("entity").eur.sum().reindex(COUNTRIES).fillna(0.0)
        direct = L[L.subject.isin(["capex_new", "fom_existing", "variable_cost", "co2_ship_freight", "co2_transit_freight", "co2_transit_rail_freight", "co2_transit_ship_freight"])].groupby("entity").eur.sum().reindex(COUNTRIES).fillna(0.0)
        # corridor rent per pair: the corridor's settlement surplus = -(settlement) - costs? In the ledger: corridor net = costs + settlement; rent share booked = net/2 each? check:
        # xb_share_congestion_rent (country) = sum over its corridors of settlement/2 ; xb_share_infrastructure_cost = costs/2
        chk_rent = {c: 0.0 for c in COUNTRIES}; chk_inf = {c: 0.0 for c in COUNTRIES}
        for k, v in corr.items():
            a, b = k[3:].split("|")
            chk_rent[a] += v["settlement"] / 2; chk_rent[b] += v["settlement"] / 2
            chk_inf[a] += v["costs"] / 2; chk_inf[b] += v["costs"] / 2
        chk = pd.DataFrame({"ledger_rent_half": rent_half, "pairs_settlement_half": pd.Series(chk_rent), "ledger_infra_half": infra_half, "pairs_costs_half": pd.Series(chk_inf)})
        max_dev = float((chk.ledger_rent_half - chk.pairs_settlement_half).abs().max() + (chk.ledger_infra_half - chk.pairs_costs_half).abs().max())
        # rule ii / iii: move the whole corridor settlement (rent) to importer / exporter
        rent_imp = {c: 0.0 for c in COUNTRIES}; rent_exp = {c: 0.0 for c in COUNTRIES}
        for k, v in corr.items():
            a, b = k[3:].split("|")
            ic, ec = imp.get(k, (b, a, np.nan, np.nan))[:2]
            rent_imp[ic] += v["settlement"]; rent_exp[ec] += v["settlement"]
        r1 = base
        r2 = base - rent_half + pd.Series(rent_imp)
        r3 = base - rent_half + pd.Series(rent_exp)
        r4 = direct + infra_half   # physical costs only: own direct costs + half of corridor infrastructure (no trade, no pool, no rent, no CO2 service)
        r5 = T["total_length_split"].reindex(COUNTRIES)
        res = pd.DataFrame({"(i) 现行": r1, "(ii) 拥塞租归进口方": r2, "(iii) 拥塞租归出口方": r3, "(iv) 只计境内物理成本": r4, "(v) 按境内长度分摊": r5}) / BN_
        rules[lab] = res
        MD.append(f"### {lab}：各国成本（bn EUR）在五种规则下")
        MD.append(f"- 核对：账本的拥塞租 / 设施分摊与 `LEDGER_IDENTITY.json` 走廊表按对半分的重算最大偏差 {max_dev:,.0f} EUR。")
        MD.append("- 进口方按该国家对的电力净流向判定（无电力通道时按全部载体），见下表。")
        put(res.round(3))
        imps = pd.DataFrame([{"pair": k, "importer": v[0], "exporter": v[1], "e_to_importer_twh": max(v[2], v[3]), "e_to_exporter_twh": min(v[2], v[3]), "corridor_costs_bn": corr[k]["costs"] / BN_, "corridor_settlement_bn": corr[k]["settlement"] / BN_, "net_bn": corr[k]["net"] / BN_} for k, v in imp.items() if k in corr])
        MD.append("走廊结算（settlement < 0 = 走廊实体净收入 = 拥塞租；costs = 走廊资本 + 运维；现行规则两国各半）：")
        put(imps, "{:,.3f}")
        SUMMARY[f"aspect8_{lab}"] = {"rules_bn": res.to_dict(), "corridors": imps.to_dict(orient="records"), "max_dev_eur": max_dev}
    # B6 per country under the rules (disconnected has no trade: its total is rule-invariant except (iv))
    Ld = ledger_detail("disconnected"); Td = ledger_total("disconnected")
    dbase = Td["total"].reindex(COUNTRIES)
    ddirect = Ld[Ld.subject.isin(["capex_new", "fom_existing", "variable_cost", "co2_ship_freight", "co2_transit_freight", "co2_transit_rail_freight", "co2_transit_ship_freight"])].groupby("entity").eur.sum().reindex(COUNTRIES).fillna(0.0)
    res = rules["integrated"]
    b6 = pd.DataFrame({k: (dbase / BN_ - res[k]) for k in res.columns if k != "(iv) 只计境内物理成本"})
    b6["(iv) 只计境内物理成本"] = ddirect / BN_ - res["(iv) 只计境内物理成本"]
    b6["share_(i)_pct"] = 100 * b6["(i) 现行"] / b6["(i) 现行"].sum()
    b6["share_(iv)_pct"] = 100 * b6["(iv) 只计境内物理成本"] / b6["(iv) 只计境内物理成本"].sum()
    MD.append("### 分国差额（不互联 − 一体化，bn EUR）随规则变化；不互联无跨境贸易，其总额与规则 (i)(ii)(iii)(v) 无关")
    put(b6.round(3))
    MD.append(f"- 11 国合计（规则 (i)–(iii)(v) 相同）：{b6['(i) 现行'].sum():.3f} bn；(iv) 合计 {b6['(iv) 只计境内物理成本'].sum():.3f} bn（差别 = 燃料舱与共享池的直接成本差与结算项）。")
    SUMMARY["aspect8_b6_by_rule"] = b6.to_dict()
    b6.to_csv(OUT / "ASPECT8_B6_BY_RULE.csv")


# ------------------------------------------------------------------ analysis B: cross-entity consistency
def analysisB(use):
    section("必做 B：跨区域一致性")
    for lab in ["integrated", "integrated_nze"]:
        L = ledger_detail(lab)
        settle = L[~L.subject.isin(["capex_new", "fom_existing", "variable_cost"])].eur.sum()
        trade = L[L.subject.str.startswith("network_trade")].groupby("entity").eur.sum()
        rent = L[L.subject == "xb_share_congestion_rent"].eur.sum()
        MD.append(f"- {lab}：全部结算科目之和 {settle:,.0f} EUR（应 ≈ 0：转移支付相互抵消，差为共享池盈余）；各国网络贸易之和 {trade.sum():,.0f} EUR，拥塞租分摊之和 {rent:,.0f} EUR → 网络贸易之和 + 拥塞租之和 = {trade.sum()+rent:,.0f}（走廊实体净收入与各国支付对账）。")
        pool = L[L.subject.str.startswith("liquid_pool")].groupby("entity").eur.sum()
        MD.append(f"  液体池结算：各国 + 燃料舱支付合计 {pool.drop('ASEAN_POOL', errors='ignore').sum()/BN_:,.3f} bn，共享池收入 {-pool.get('ASEAN_POOL', 0)/BN_:,.3f} bn（池自身直接成本 = 油 / 非化石油品 / 甲醇 / 氨进口与存储）。")
    # fall-back totals
    tot = use.groupby(["run", "carrier"]).agg(energy_twh=("energy_twh", "sum"), cost_bn=("cost_bn", "sum")).reset_index()
    MD.append("兜底选项总用量与成本（TWh，bn EUR）：")
    put(tot.pivot_table(index="carrier", columns="run", values=["energy_twh", "cost_bn"]).round(2))


def main():
    MD.append("# S4P 方面 1–3、5–8 与必做 B 的数据表（只读；来源：提取的网络表 `evidence/net/`、云端导出、账本明细）\n")
    MD.append("- 一体化 = S4N 试点（只有轻量导出：账本、流量表、容量表、CO₂ 表、节点价格；无求解后网络）；不互联 / NZE = S4O-6（有求解后网络）。\n")
    use = aspect1()
    aspect2()
    aspect3()
    aspect5()
    aspect6()
    aspect7()
    aspect8()
    analysisB(use)
    (OUT / "ASPECTS_TABLES.md").write_text("\n".join(MD), encoding="utf-8")
    dump_json(SUMMARY, OUT / "ASPECTS_SUMMARY.json")
    print("done")


if __name__ == "__main__":
    main()
