"""X20 §3 第 5 步：v4 -> v5 输入修订桥表 X20_BRIDGE.csv（只列输入，不涉及求解结果），以及第 4 步 (e) 的陆上风电合理性对照 ONWIND_SANITY_V5.csv。
v4 值取 v5off 网络（= W14 数据，evidence/V5OFF_VS_W14_*.json 逐值相同），v5 值取 v5 主集网络；两者都是 F1 integrated 2920x3h 未求解网络。
F2 no_new_xb 只在跨境结构上不同：脚本对 F2 重算同一张表，逐行比较，结果写进 evidence/X20_BRIDGE_F2_CHECK.json。
列 = revision, decision, switch, country, quantity, unit, v4_value, v5_value, delta, source_table, grade（X20_SPEC.md §5 第 5 项），另加 note。
grade：VERIFIED = 由两张网络（或其 meta）的数组直接算出。
①1 / ①2 的分离：存量陆上风电的 CF 同时受新曲线（①1）和改取最好等级（①2）影响；用 v5 曲线文件 profiles_calibrated_gwa_v5_c3_3h.nc 的 '<node>|0'
（= v4 规则 class0）算出"只有 ①1"的中间值。CF = 按快照权重的年均 p_max_pu（与 s4a_layers 相同的 clip_p_max_pu 规则），按 p_nom（存量）或 p_nom_max（候选）加权。
用法：PYTHONHASHSEED=0 python x20_bridge.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa
import xarray as xr

R = Path("/home/jin/wt_v5_x20"); sys.path.insert(0, str(R / "scripts_project"))
W = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
X03 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x03_renew_20261111")
COUNTRIES = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]
R_FARM = dict(TH=1.07, VN=1.44, PH=1.52)   # GWA gross / observed at the farm points of the three calibrated countries (X20_SPEC.md §5 4 (e), EXACT X03)
rows = []


def add(rev, dec, sw, c, q, unit, a, b, src, note=""):
    a = None if a is None else float(a); b = None if b is None else float(b)
    rows.append(dict(revision=rev, decision=dec, switch=sw, country=c, quantity=q, unit=unit, v4_value=a, v5_value=b,
                     delta=(None if a is None or b is None else b - a), source_table=src, grade="VERIFIED", note=note))


def country(n, buses: pd.Series) -> pd.Series:
    c = buses.map(n.buses.country) if "country" in n.buses else pd.Series(np.nan, index=buses.index)
    return c.where(c.notna() & (c.astype(str) != ""), buses.astype(str).str[:2]).astype(str)


def cf(n, names, clip=0.0) -> pd.Series:
    w = n.snapshot_weightings.generators
    P = n.generators_t.p_max_pu
    out = {}
    for g in names:
        s = P[g] if g in P.columns else pd.Series(float(n.generators.at[g, "p_max_pu"]), index=n.snapshots)
        if clip > 0:
            s = s.where(s >= clip, 0.0)
        out[g] = float((s * w).sum() / w.sum())
    return pd.Series(out, dtype=float)


def wmean(v: pd.Series, wt: pd.Series) -> float:
    wt = wt.loc[v.index].replace(np.inf, np.nan).fillna(0.0)
    return float((v * wt).sum() / wt.sum()) if wt.sum() > 0 else float("nan")


def link_out_mw(n, sel) -> pd.Series:
    L = n.links.loc[sel]
    eff = L.efficiency.astype(float)
    if "efficiency" in n.links_t and len(n.links_t.efficiency.columns):
        tv = [x for x in L.index if x in n.links_t.efficiency.columns]
        for x in tv:
            eff.loc[x] = float(n.links_t.efficiency[x].mean())
    return L.p_nom.astype(float) * eff


def table(n0, n5, tag) -> list:
    global rows
    rows = []
    g0, g5 = n0.generators, n5.generators
    c0, c5 = country(n0, g0.bus), country(n5, g5.bus)
    clip = float(((n5.meta.get("research_config") or {}).get("renewable") or {}).get("clip_p_max_pu", 0.0))
    # ①1 onshore-wind candidates: potential-weighted CF and potential, by country and class
    for c in COUNTRIES:
        i0 = g0.index[(g0.carrier == "onwind") & g0.p_nom_extendable & (c0 == c)]; i5 = g5.index[(g5.carrier == "onwind") & g5.p_nom_extendable & (c5 == c)]
        if not len(i0) and not len(i5):
            continue
        add("1-1", 241, "onwind_calibration: ember_country -> gwa_cell_ember", c, "onwind candidate CF, potential-weighted", "fraction",
            wmean(cf(n0, i0), g0.p_nom_max) if len(i0) else None, wmean(cf(n5, i5), g5.p_nom_max) if len(i5) else None,
            "renewable_v5/profiles_calibrated_gwa_v5_c3_3h.nc; S4A_PROFILE_CLASSES_calibrated_gwa_v5_c3.csv")
        add("1-1", 241, "onwind_calibration: ember_country -> gwa_cell_ember", c, "onwind candidate potential (sum p_nom_max)", "MW",
            g0.loc[i0, "p_nom_max"].sum(), g5.loc[i5, "p_nom_max"].sum(), "S4A_PROFILE_CLASSES_calibrated_gwa_v5_c3.csv (class shares x unchanged node potential)",
            "SG: classes 0 and 2 fall below the S4L-1 dust threshold (1 MW / 1 GWh a) and are removed" if c == "SG" else "")
        for k in (0, 1, 2):
            def cls(idx, g):
                return [x for x in idx if (k == 0 and not str(x).endswith((" c1", " c2"))) or str(x).endswith(f" c{k}") and k > 0]
            a, b = cls(i0, g0), cls(i5, g5)
            add("1-1", 241, "onwind_calibration", c, f"onwind candidate CF class {k}", "fraction", wmean(cf(n0, a), g0.p_nom_max) if a else None,
                wmean(cf(n5, b), g5.p_nom_max) if b else None, "profiles_calibrated_gwa_v5_c3_3h.nc", "classes re-binned per node on the v5 cell CFs")
            add("1-1", 241, "onwind_calibration", c, f"onwind candidate potential class {k}", "MW", g0.loc[a, "p_nom_max"].sum() if a else None,
                g5.loc[b, "p_nom_max"].sum() if b else None, "S4A_PROFILE_CLASSES_calibrated_gwa_v5_c3.csv")
    # ①1 / ①2 existing onshore wind: CF v4 (class0, v4 curve) -> class0 on the v5 curve (only ①1) -> best class on the v5 curve (①1 + ①2)
    ds = xr.open_dataset(R / "research_inputs/renewable_v5/profiles_calibrated_gwa_v5_c3_3h.nc"); prof = ds["onwind"].to_pandas(); ds.close()
    w = n5.snapshot_weightings.generators.values
    for c in COUNTRIES:
        e0 = g0.index[(g0.carrier == "onwind existing") & (c0 == c)]; e5 = g5.index[(g5.carrier == "onwind existing") & (c5 == c)]
        if not len(e0) and not len(e5):
            continue
        mid = {}
        for x in e5:
            col = f"{g5.at[x, 'bus']}|0"
            if col in prof.columns:
                s = prof[col].values.astype(float); s = np.where(s >= clip, s, 0.0) if clip > 0 else s
                mid[x] = float((s * w).sum() / w.sum())
        mid = pd.Series(mid, dtype=float)
        v4cf = wmean(cf(n0, e0), g0.p_nom) if len(e0) else None
        v5cf = wmean(cf(n5, e5), g5.p_nom) if len(e5) else None
        mcf = wmean(mid, g5.p_nom) if len(mid) else None
        add("1-1", 241, "onwind_calibration (existing wind, class0 kept)", c, "existing onwind CF, p_nom-weighted (v5 stock)", "fraction", v4cf, mcf,
            "profiles_calibrated_gwa_v5_c3_3h.nc '<node>|0'", "intermediate: v5 curve, v4 class rule (class0); v4_value on the v4 stock")
        add("1-2", 241, "existing_wind_profile: class0 -> best_class", c, "existing onwind CF, p_nom-weighted (v5 stock)", "fraction", mcf, v5cf,
            "profiles_calibrated_gwa_v5_c3_3h.nc best class column", "from the class0 intermediate to the best class")
        add("2-5", 244, "lifetime_boundary: strict -> inclusive (GEM additions table)", c, "existing onwind capacity", "MW", g0.loc[e0, "p_nom"].sum(), g5.loc[e5, "p_nom"].sum(),
            "fleet_v5/FLEET_ADDITIONS_2050_V5.csv")
    # Q12 existing solar profile
    for c in COUNTRIES:
        e0 = g0.index[(g0.carrier == "solar existing") & (c0 == c)]; e5 = g5.index[(g5.carrier == "solar existing") & (c5 == c)]
        if not len(e0) and not len(e5):
            continue
        add("Q12", 246, "existing_solar_profile: class0 -> node_average", c, "existing solar CF, p_nom-weighted", "fraction",
            wmean(cf(n0, e0), g0.p_nom) if len(e0) else None, wmean(cf(n5, e5), g5.p_nom) if len(e5) else None, "EXISTING_SOLAR_PROFILE_CHOICE.csv (node c1 profile = rooftop column)")
    # ①4 / ①3 main unchanged: solar candidate potential, offshore candidate capital cost
    for c in COUNTRIES:
        for car, rev, sw, q, col, unit in (("solar", "1-4", "solar_cap_scale_* = 1.0, solar_landuse_my = lc100", "solar candidate potential (sum p_nom_max)", "p_nom_max", "MW"),
                                           ("offwind-ac", "1-3", "offwind_asean_premium_pct = 0", "offwind-ac candidate capital cost (sum)", "capital_cost", "EUR/MW/a"),
                                           ("offwind-dc", "1-3", "offwind_asean_premium_pct = 0", "offwind-dc candidate capital cost (sum)", "capital_cost", "EUR/MW/a")):
            i0 = g0.index[(g0.carrier == car) & g0.p_nom_extendable & (c0 == c)]; i5 = g5.index[(g5.carrier == car) & g5.p_nom_extendable & (c5 == c)]
            if len(i0) or len(i5):
                add(rev, 241, sw, c, q, unit, g0.loc[i0, col].replace(np.inf, np.nan).sum(), g5.loc[i5, col].replace(np.inf, np.nan).sum(), "v5 main value = v4 value")
    # ①5 hydro inflow of the existing stock
    h0, h5 = n0.meta.get("research_hydro_inflow", {}).get("countries", {}), n5.meta.get("research_hydro_inflow", {}).get("countries", {})
    for c in sorted(set(h0) | set(h5)):
        a, b = h0.get(c, {}), h5.get(c, {})
        add("1-5", 241, "hydro_inflow_denominator: all_stock -> operating_only", c, "existing hydro + ror inflow energy", "TWh/a",
            a.get("energy_after_mwh", 0) / 1e6, b.get("energy_after_mwh", 0) / 1e6, "meta research_hydro_inflow (operating share of HYDRO stock)",
            f"stock {b.get('stock_mw')} MW; CF after v4 {a.get('cf_after', float('nan')):.4f} -> v5 {b.get('cf_after', float('nan')):.4f}; target {b.get('target_mwh', 0) / 1e6:.3f} TWh")
    nb0 = pd.DataFrame(n0.meta.get("research_hydro_inflow", {}).get("new_build", [])); nb5 = pd.DataFrame(n5.meta.get("research_hydro_inflow", {}).get("new_build", []))
    for (c, kind), d5 in nb5.groupby(["country", "kind"]):
        d0 = nb0[(nb0.country == c) & (nb0.kind == kind)]
        add("1-5", 241, "hydro_inflow_denominator: all_stock -> operating_only", c, f"new-build {kind} inflow CF, p_nom_max-weighted (research_new_hydro_inflow_tie)", "fraction",
            float((d0.cf_after * d0.p_nom_max).sum() / d0.p_nom_max.sum()) if len(d0) else None, float((d5.cf_after * d5.p_nom_max).sum() / d5.p_nom_max.sum()),
            "meta research_hydro_inflow.new_build (s4c_layers L411-416)",
            f"{len(d5)} candidates, p_nom_max {d5.p_nom_max.sum():.0f} MW (unchanged); scopes {sorted(set(d5['scope']))}; inflow and p_nom_max written together")
    # ①6 geothermal candidate caps; ②5 existing geothermal
    for c in COUNTRIES:
        i0 = g0.index[(g0.carrier == "geothermal") & g0.p_nom_extendable & (c0 == c)]; i5 = g5.index[(g5.carrier == "geothermal") & g5.p_nom_extendable & (c5 == c)]
        if len(i0) or len(i5):
            add("1-6", 241, "geothermal_cap_id: resource_potential -> reserves_2017 (ID); PH rebuild via the 40-year life", c, "geothermal candidate cap (sum p_nom_max)", "MW",
                g0.loc[i0, "p_nom_max"].sum(), g5.loc[i5, "p_nom_max"].sum(), "potentials_v5/GEOTHERMAL_ID_POTENTIAL_V5.csv; s2_layers geothermal rule")
    # ①7 biomass pools
    s0 = n0.stores[n0.stores.bus.str.startswith("solid biomass")]; s5 = n5.stores[n5.stores.bus.str.startswith("solid biomass")]
    p0 = s0.groupby(country(n0, s0.bus)).e_initial.sum(); p5 = s5.groupby(country(n5, s5.bus)).e_initial.sum()
    for c in sorted(set(p0.index) | set(p5.index)):
        add("1-7", 241, "biomass_residue_fix: v4 -> corrected", c, "solid biomass pool (sum e_initial)", "TWh/a", p0.get(c, 0.0) / 1e6, p5.get(c, 0.0) / 1e6,
            "biomass_v5 *_V5FIX tables; industry_v4/out_ras_v5")
    # ②1 PH DC links and B2B
    for car in ("DC", "B2B"):
        a = n0.links[n0.links.carrier == car]; b = n5.links[n5.links.carrier == car]
        for x in sorted(set(a.index) | set(b.index)):
            pa = float(a.at[x, "p_nom"]) if x in a.index else None; pb = float(b.at[x, "p_nom"]) if x in b.index else None
            if pa != pb:
                bb = a if x in a.index else b
                add("2-1", 244, "ph_dc_stock: frozen_base -> ngcp_tdp", "PH", f"{car} link p_nom {x} ({bb.at[x, 'bus0']} -> {bb.at[x, 'bus1']})", "MW", pa, pb,
                    "corridors/PH_DC_STOCK_V5.csv (NGCP TDP 2025-2050)", "candidate p_nom_max = p_nom + 20,000 MW (unchanged rule)" if car == "DC" else "B2B placeholder removed (p_nom 0)")
    # ②2 AC lines: s_nom by country (domestic) and by line where changed
    l0, l5 = n0.lines, n5.lines
    k0 = country(n0, l0.bus0) + np.where(country(n0, l0.bus0) == country(n0, l0.bus1), "", "-" + country(n0, l0.bus1))
    k5 = country(n5, l5.bus0) + np.where(country(n5, l5.bus0) == country(n5, l5.bus1), "", "-" + country(n5, l5.bus1))
    for k in sorted(set(k0) | set(k5)):
        a, b = float(l0.s_nom[k0 == k].sum()), float(l5.s_nom[k5 == k].sum())
        if abs(a - b) > 1e-6:
            add("2-2", 244, "ac_dedup: frozen_base -> dedup_cables", k, "AC line s_nom (sum)", "MW", a, b, "corridors/AC_DEDUP_V5.csv; OSM_WAY_TAGS_V5.csv")
    for x in l0.index.intersection(l5.index):
        if abs(float(l0.at[x, "s_nom"]) - float(l5.at[x, "s_nom"])) > 1e-6:
            add("2-2", 244, "ac_dedup", k5.loc[x], f"AC line {x} s_nom ({l5.at[x, 'bus0']} - {l5.at[x, 'bus1']})", "MW", l0.at[x, "s_nom"], l5.at[x, "s_nom"], "corridors/AC_DEDUP_V5.csv",
                f"s_nom_max {l0.at[x, 's_nom_max']:.1f} -> {l5.at[x, 's_nom_max']:.1f}; num_parallel {l0.at[x, 'num_parallel']:.3f} -> {l5.at[x, 'num_parallel']:.3f}")
    # ②3 gas production caps
    for nn, lab in ((n0, "v4"), (n5, "v5")):
        caps = nn.meta.get("external_annual_caps", {}); gp = nn.generators[nn.generators.carrier == "gas production"]
        nn._gas = pd.Series({k: float(caps.get(k, 0.0)) for k in gp.index}).groupby(country(nn, gp.bus)).sum()
    for c in sorted(set(n0._gas.index) | set(n5._gas.index)):
        add("2-3", 244, "gas_cap_rule: marketed -> field_status", c, "gas production annual cap", "TWh/a", n0._gas.get(c, 0.0) / 1e6, n5._gas.get(c, 0.0) / 1e6,
            "gas_v5/GAS_CAP_FRACTIONS_V5.csv x GAS_PRODUCTION_CAPS_2050_V4.csv", "fields with fraction 0 are removed with their wellhead bus")
    # ②4 NEU gas feedstock loads
    wo = n0.snapshot_weightings.objective
    def ann(n, idx):
        return pd.Series({l: (float((n.loads_t.p_set[l] * wo).sum()) if l in n.loads_t.p_set.columns else float(n.loads.at[l, "p_set"]) * float(wo.sum())) for l in idx}, dtype=float)
    f0 = n0.loads[n0.loads.carrier == "gas feedstock"]; f5 = n5.loads[n5.loads.carrier == "gas feedstock"]
    a0 = ann(n0, f0.index).groupby(country(n0, f0.bus)).sum(); a5 = ann(n5, f5.index).groupby(country(n5, f5.bus)).sum()
    for c in sorted(set(a0.index) | set(a5.index)):
        add("2-4", 244, "neu_gas_growth: industry_multiplier -> product", c, "gas feedstock (NEU) load", "TWh/a", a0.get(c, 0.0) / 1e6, a5.get(c, 0.0) / 1e6,
            "industry_v4/out_ras_v5; evidence NEU_GAS_PRODUCT_RULE_V5.csv")
    # ②5 existing stock by country and carrier (generators p_nom; power links p_nom x efficiency; storage units p_nom)
    for comp, df0, df5, val in (("Generator", g0, g5, lambda n, d, s: d.loc[s, "p_nom"].astype(float)), ("Link", n0.links, n5.links, lambda n, d, s: link_out_mw(n, s)),
                                ("StorageUnit", n0.storage_units, n5.storage_units, lambda n, d, s: d.loc[s, "p_nom"].astype(float))):
        bus = "bus1" if comp == "Link" else "bus"
        for car in sorted(set(df0.carrier.astype(str)) | set(df5.carrier.astype(str))):
            if "existing" not in car or car in ("onwind existing",):
                continue
            s0_ = df0.index[df0.carrier.astype(str) == car]; s5_ = df5.index[df5.carrier.astype(str) == car]
            v0 = val(n0, df0, s0_).groupby(country(n0, df0.loc[s0_, bus])).sum(); v5 = val(n5, df5, s5_).groupby(country(n5, df5.loc[s5_, bus])).sum()
            for c in sorted(set(v0.index) | set(v5.index)):
                a, b = float(v0.get(c, 0.0)), float(v5.get(c, 0.0))
                if abs(a - b) > 1e-6:
                    add("2-5", 244, "lifetime_boundary: strict -> inclusive; geothermal_existing_lifetime 30 -> 40", c, f"existing {comp} {car} capacity" + (" (output = p_nom x efficiency)" if comp == "Link" else ""),
                        "MW", a, b, "fleet_v5/FLEET_ADDITIONS_2050_V5.csv; s2_layers geothermal unit table", "see evidence/FLEET_ADDITIONS_V5_VS_W14.csv and Q2_BOUNDARY_UNITS.csv")
    # ②5 consequence: LA dedicated export sources (the moved existing stock behind the dedicated plant lines)
    d0 = {s["node"]: s for s in n0.meta["research_dedicated_lines"]["sources"]}; d5 = {s["node"]: s for s in n5.meta["research_dedicated_lines"]["sources"]}
    for nd in sorted(set(d0) | set(d5)):
        a, b = d0.get(nd, {}), d5.get(nd, {})
        if a.get("moved_mw") != b.get("moved_mw"):
            add("2-5", 244, "lifetime_boundary (GEM additions at dedicated-source nodes)", "LA", f"dedicated source {nd}: moved existing capacity (= source-to-grid link p_nom)", "MW",
                a.get("moved_mw"), b.get("moved_mw"), "meta research_dedicated_lines", f"v5 by carrier {b.get('moved_mw_by_carrier')}; plant lines {b.get('plant_lines')}; contract {b.get('contract_mw')} MW unchanged")
    # ②6 coordinate corrections
    for m in ((n5.meta.get("v5_x20") or {}).get("ledgers", {}).get("gem_coord_2_6") or {}).get("moved") or []:
        add("2-6", 244, "gem_coord_fix: gem -> verified", m["node_from"][:2], f"{m['plant']} ({m['gem_unit_id']}) node {m['node_from']} -> {m['node_to']}", "MW", m["mw"], m["mw"],
            "fleet_v5/GEM_COORD_CORRECTIONS_V5.csv", "capacity unchanged; node assignment changed")
    # ③1 / ③2 / ③3 main unchanged
    add("3-1", 244, "storage_potential_case = P50 / 50 (unchanged); extra_asean_capacity_mt = null", "ASEAN", "research_co2_storage meta identical", "bool",
        1.0, float(json.dumps(n0.meta.get("research_co2_storage"), sort_keys=True, default=str) == json.dumps(n5.meta.get("research_co2_storage"), sort_keys=True, default=str)),
        "co2_v5/CO2_STORAGE_CASES_V5.csv (low cases are switches)", "1 = identical")
    dac0 = n0.links[n0.links.carrier == "DAC"].capital_cost.sum(); dac5 = n5.links[n5.links.carrier == "DAC"].capital_cost.sum()
    add("3-2", 244, "cost_scaling.DAC = 1.0", "ASEAN", "DAC capital cost (sum over links)", "EUR/MW/a", dac0, dac5, "configs/research/baseline.yaml cost_scaling")
    ev0 = n0.loads[n0.loads.carrier == "land transport EV"]; ev5 = n5.loads[n5.loads.carrier == "land transport EV"]
    e0_ = ann(n0, ev0.index).groupby(country(n0, ev0.bus)).sum(); e5_ = ann(n5, ev5.index).groupby(country(n5, ev5.bus)).sum()
    for c in sorted(set(e0_.index) | set(e5_.index)):
        add("3-3", 244, "s2.demand.ev_smart_share = 1.0", c, "EV load (land transport EV)", "TWh/a", e0_.get(c, 0.0) / 1e6, e5_.get(c, 0.0) / 1e6, "v3_layers EV")
    # ③4 distribution grid: loads on LV buses, LV links, distribution links
    for c in COUNTRIES:
        L0 = n0.loads[country(n0, n0.loads.bus) == c]; L5 = n5.loads[country(n5, n5.loads.bus) == c]
        lv0 = L0.index[L0.bus.astype(str).str.endswith(" low voltage")]; lv5 = L5.index[L5.bus.astype(str).str.endswith(" low voltage")]
        add("3-4", 244, "distribution_grid: hv_lossless -> lv_pypsa_eur", c, "load energy on low-voltage buses", "TWh/a", ann(n0, lv0).sum() / 1e6, ann(n5, lv5).sum() / 1e6,
            "v5_layers.apply_distribution_grid_v5", "electricity, industry electricity, agriculture machinery electric")
        for nn, lab in ((n0, "v4"), (n5, "v5")):
            Lk = nn.links[country(nn, nn.links.bus0) == c]
            nn._lv = int((Lk.bus0.astype(str).str.endswith(" low voltage") & (Lk.carrier != "electricity distribution grid")).sum())
            nn._dg = Lk[Lk.carrier == "electricity distribution grid"]
        add("3-4", 244, "distribution_grid", c, "links drawing from low-voltage buses (BEV charger, heat pumps, cooking, boilers)", "count", n0._lv, n5._lv, "v5_layers.apply_distribution_grid_v5")
        add("3-4", 244, "distribution_grid", c, "electricity distribution grid links", "count", len(n0._dg), len(n5._dg), "v5_layers.apply_distribution_grid_v5", "v5: forward + reversed twin, capacities synchronised")
        add("3-4", 244, "distribution_grid", c, "electricity distribution grid efficiency (mean)", "fraction", n0._dg.efficiency.mean() if len(n0._dg) else None,
            n5._dg.efficiency.mean() if len(n5._dg) else None, "v5_layers.apply_distribution_grid_v5 (registry v5_x20)")
    add("3-5", 244, "bunker carbon attribution (post-processing only)", "ASEAN", "no input change", "-", None, None, "v5_bunker_attribution.py", "report produced after the solve")
    add("4-1", 244, "meta run_status / build_history (export only)", "ASEAN", "no input change", "-", None, None, "v5_common.export_meta")
    return rows


def onwind_sanity(n0, n5) -> pd.DataFrame:
    """X20_SPEC.md §5 4 (e): country v4 -> v5 candidate CF vs GWA IEC3 gross / r; r of the 8 other countries = farm-capacity-weighted r of TH / VN / PH
    (the weights of the alpha_weighted_calibrated value, WIND_CALIBRATION_ALPHA_V5.csv farm_capacity_onshore_mw)."""
    al = pd.read_csv(R / "research_inputs/renewable_v5/WIND_CALIBRATION_ALPHA_V5.csv").set_index("country")
    wcap = al.loc[list(R_FARM), "farm_capacity_onshore_mw"].astype(float)
    r_other = float(sum(R_FARM[c] * wcap[c] for c in R_FARM) / wcap.sum())
    cells = pd.read_csv(X03 / "cache/onwind_cells/onwind_node_cells.csv")
    gwa = cells.groupby("country").apply(lambda d: float((d.gwa_cf_iec3 * d.w_mw).sum() / d.w_mw.sum()))
    g0, g5 = n0.generators, n5.generators; c0, c5 = country(n0, g0.bus), country(n5, g5.bus)
    out = []
    for c in COUNTRIES:
        i0 = g0.index[(g0.carrier == "onwind") & g0.p_nom_extendable & (c0 == c)]; i5 = g5.index[(g5.carrier == "onwind") & g5.p_nom_extendable & (c5 == c)]
        r = R_FARM.get(c, r_other)
        v4, v5 = wmean(cf(n0, i0), g0.p_nom_max), wmean(cf(n5, i5), g5.p_nom_max)
        ref = float(gwa.get(c, np.nan)) / r
        out.append(dict(country=c, cf_v4=v4, cf_v5=v5, gwa_iec3_gross_potential_weighted=float(gwa.get(c, np.nan)), r=r, r_basis=("farm points" if c in R_FARM else "capacity-weighted TH/VN/PH"),
                        gwa_gross_over_r=ref, v5_over_reference=v5 / ref if ref else np.nan, v4_over_reference=v4 / ref if ref else np.nan,
                        alpha_v5=float(al.at[c, "alpha_main"]), grade="VERIFIED (arrays); reference r EXACT X03"))
    return pd.DataFrame(out)


def main():
    import gc
    sub = dict(F1="integrated/integrated_2920_3h_unsolved.nc", F2="no_new_xb/no_new_xb_2920_3h_unsolved.nc")
    res = {}
    for tag in ("F1", "F2"):
        n0 = pypsa.Network(str(W / "builds/v5off" / sub[tag])); n5 = pypsa.Network(str(W / "builds/v5main" / sub[tag]))
        res[tag] = pd.DataFrame(table(n0, n5, tag))
        if tag == "F1":
            s = onwind_sanity(n0, n5); s.to_csv(W / "ONWIND_SANITY_V5.csv", index=False, lineterminator="\n"); print(s.round(4).to_string())
        del n0, n5; gc.collect()
    b = res["F1"]; b.to_csv(W / "X20_BRIDGE.csv", index=False, lineterminator="\n")
    f2 = res["F2"]
    key = ["revision", "country", "quantity"]
    m = b.merge(f2, on=key, how="outer", suffixes=("", "_F2"), indicator=True)
    diff = m[(m._merge != "both") | ~np.isclose(m.v4_value.astype(float), m.v4_value_F2.astype(float), equal_nan=True, rtol=0, atol=1e-6)
             | ~np.isclose(m.v5_value.astype(float), m.v5_value_F2.astype(float), equal_nan=True, rtol=0, atol=1e-6)]
    chk = dict(rows_F1=len(b), rows_F2=len(f2), differing=diff[key + ["v4_value", "v4_value_F2", "v5_value", "v5_value_F2", "_merge"]].astype(str).to_dict("records"))
    (W / "evidence/X20_BRIDGE_F2_CHECK.json").write_text(json.dumps(chk, indent=1) + "\n")
    print("rows", len(b), "F2 differing rows", len(chk["differing"]))
    print(b[b.delta.abs() > 1e-9].groupby("revision").size().to_string())


if __name__ == "__main__":
    main()
