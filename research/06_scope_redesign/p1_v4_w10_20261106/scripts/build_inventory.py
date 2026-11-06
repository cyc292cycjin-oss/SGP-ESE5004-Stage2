#!/usr/bin/env python3
"""V4 W10-1: inventory of the in-use grade-C parameters of the research registry.

In use = status REGISTERED, SENSITIVITY or DATA_PENDING (this reproduces item 201: 1,436 rows / 441 grade C on the DFX F4 registry
72083fde; the current head carries 462 grade-C rows, the extra 21 are the v3 fragment). For every row the script writes the family of
item 201, the side (supply / cost / network / demand / rule), the one-notch change, why the row is grade C, the code path into the network
(file:line located in the worktree at run time) and the first-order mechanism that rerank_with_results.py evaluates on solved results.

Read only: reads the registry and source files, writes one CSV and one JSON. No network build, no solver.

usage: python build_inventory.py --repo /home/jin/wt_v4_w10 --out <dir>
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path

import pandas as pd

IN_USE = ("REGISTERED", "SENSITIVITY", "DATA_PENDING")
COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
SHIP_CARRIER = {"ammonia": "ammonia ship", "methanol": "methanol ship", "oil": "oil non-fossil ship"}
CONV_USD2004_EUR2020 = None   # read from the registry (conv_usd2004_to_eur2020)
EPS_WIND = 2.7594   # dCF/CF per dalpha/alpha, ID row of WIND_CALIBRATION_ALPHA.csv (alpha 1 -> alpha_main), used for the eight proxy countries
EPS_OFFWIND = 1.5944  # PH row (high-CF regime), used for offshore (no offshore calibration exists)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def family_201(pid: str) -> str:
    for k, pat in [("biomass", r"^biomass_"), ("industry", r"^industry_"), ("route_share", r"^share_"), ("co2", r"^co2_"), ("wacc", r"^wacc_"),
                   ("potential", r"^(potential_|renewable_cap_|candidate_cap_|nuclear_plan_cap_)")]:
        if re.match(pat, pid):
            return k
    return "other"


class Locator:
    """file:line of the first match of a pattern in the worktree (VERIFIED code path at build time)."""

    def __init__(self, repo: Path):
        self.repo = repo
        self.cache: dict[str, list[str]] = {}

    def __call__(self, rel: str, pattern: str) -> str:
        p = self.repo / rel
        if rel not in self.cache:
            self.cache[rel] = p.read_text(encoding="utf-8", errors="replace").splitlines() if p.exists() else []
        for i, line in enumerate(self.cache[rel], 1):
            if pattern in line:
                return f"{rel}:{i}"
        return f"{rel}:NOT_FOUND({pattern})"


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def why_c(r) -> str:
    d = str(r.description)
    hints = []
    if r.status == "DATA_PENDING":
        hints.append("数据缺失（DATA_PENDING）")
    if re.search(r"proxy", d, re.I):
        hints.append("代理值（无直接来源）")
    if re.search(r"ASSUMPTION|assumption", d):
        hints.append("假设值")
    if re.search(r"could not be re-checked|not re-checked", d):
        hints.append("来源未能复核")
    if re.search(r"fallback|no source inside the repository|no sourced", d, re.I):
        hints.append("无可引用来源，取回退值")
    if str(r.unit) in ("rule", "flag", "list", "file", "carrier"):
        hints.append("建模规则 / 开关（非测量值）")
    fam = {
        "biomass_cost": "东南亚 2024 价格调查单点或代理，D1 L13 规定 C 级 ±50 %",
        "biomass_potential": "FAOSTAT × IRENA 残余比 × 收集率 × 饲料份额推导，系数取区域通用值",
        "co2_": "成本链取 IEAGHG 2004 / ZEP 2011 / Stolaroff 2021 的单一来源换算，或国家封存评估缺失",
        "liquid_ship": "评审 D161-2 / 决策 187 的回退值，无东盟航线实测",
        "share_": "PyPSA-Eur v2025.07.0 配置常数（欧洲情景），未针对东盟校核",
        "wacc_": "国家 WACC 只有名义税后值或无公开估计",
        "renewable_cap_built": "作者链屋顶面积 × 0.1 kW/m² 推导，未与东盟屋顶统计核对",
        "onwind_alpha": "无本国风电场观测，取 PH / TH / VN 校准值的容量加权",
        "potential_": "无官方资源评估",
        "industry_": "需求侧推导（I2 已处理）",
        "geothermal_new": "AEO8 D.15 'Geothermal average'，technology-data 无该行（决策 52）",
        "lng_terminal": "无东盟再气化终端单价，取 Ulvestad & Overland (2012) 换算",
        "import_price": "单一文献的 2040→2050 降幅估计",
        "gas_production_node": "GEM 气田最近节点分配（代替负荷份额）",
    }
    for k, v in fam.items():
        if str(r.param_id).startswith(k):
            hints.append(v)
            break
    return "；".join(dict.fromkeys(hints)) or "登记为 C 级（见注册表 description）"


def rows_for(reg: pd.DataFrame, loc: Locator) -> list[dict]:
    rv = lambda pid: num(reg.loc[pid, "value"]) if pid in reg.index else None
    conv04 = rv("conv_usd2004_to_eur2020") or 1.16898
    out = []
    c_rows = reg[(reg.tier == "C") & reg.status.isin(IN_USE)]
    for pid, r in c_rows.iterrows():
        r = r.copy(); r["param_id"] = pid
        v = num(r.value); lo = num(r.sensitivity_low); hi = num(r.sensitivity_high)
        rec = dict(param_id=pid, family_201=family_201(pid), value=r.value, unit=r.unit, country=r.country, status=r.status,
                   sensitivity_low=r.sensitivity_low, sensitivity_high=r.sensitivity_high, decision_ref=r.decision_ref,
                   derivation_script=r.derivation_script, source=str(r.source)[:160], why_C=why_c(r))
        notch_lo, notch_hi, basis = lo, hi, "registered sensitivity range (EXACT)"
        side, mech, comps, code, active, note = "rule", {"mech": "discrete"}, "", "", "yes", ""
        cc = r.country if r.country in COUNTRIES else ""
        m = re.match(r"^biomass_cost_([A-Z]{2})_(.+)$", pid)
        if m:
            c, cat = m.groups(); side = "supply"
            comps = f"Store '{c} biomass {cat}' (marginal_cost)"; code = loc("scripts_project/s2_layers.py", "def add_biomass_layer") + " -> " + loc("scripts_project/s2_layers.py", 'n.add("Store", name')
            mech = {"mech": "store_mc", "name_regex": f"^{c} biomass {re.escape(cat)}$"}
            if r.status == "DATA_PENDING":
                v_net = 0.0; proxy = rv(f"biomass_cost_{c}_other_crop_residues") or 6.26706128163
                notch_lo, notch_hi = 0.0, proxy * 1.5; basis = (f"PROPOSED: cost DATA_PENDING -> 0 EUR/MWh in the network; notch 0 -> registry proxy for unsourced residues "
                                                                 f"{proxy:.3f} x 1.5 (D1 L13 +-50 %)")
                mech["value_in_network"] = v_net; note = "网络中按 0 成本进入（BIOMASS_POTENTIAL_2050.csv 成本列为空 -> marginal_cost 0）"
            elif lo == hi == v:
                mech = {"mech": "zero", "reason": "degenerate registered range (low = high = value)"}
            out.append({**rec, **dict(side=side, notch_low=notch_lo, notch_high=notch_hi, notch_basis=basis, network_components=comps, code_path=code,
                                      active_in_main="yes", mechanism=mech["mech"], mech_json=json.dumps(mech), notes=note)})
            continue
        m = re.match(r"^biomass_potential_([A-Z]{2})_(.+)$", pid)
        if m:
            c, cat = m.groups(); side = "supply"
            comps = f"Store '{c} biomass {cat}' (e_nom = e_initial)"; code = loc("scripts_project/s2_layers.py", "def add_biomass_layer") + " -> " + loc("scripts_project/s2_layers.py", 'n.add("Store", name')
            mech = {"mech": "store_pot", "name_regex": f"^{c} biomass {re.escape(cat)}$"}
            if r.status == "DATA_PENDING":
                kh = rv("biomass_potential_KH_msw_organic_biogas") or 0.0
                proxy = kh * 1040193.0 / 7228626.0
                notch_lo, notch_hi = 0.0, proxy; basis = (f"PROPOSED: LA MSW-organic potential DATA_PENDING (skipped in the network); notch 0 -> KH value x MSW ratio "
                                                          f"1,040,193 / 7,228,626 t = {proxy:,.0f} MWh/a")
                mech = {"mech": "new_store_bus_value", "bus": "biogas LA", "value_in_network": 0.0}
                note = "网络中没有该 Store（DATA_PENDING 行被 add_biomass_layer 跳过）"
            out.append({**rec, **dict(side=side, notch_low=notch_lo, notch_high=notch_hi, notch_basis=basis, network_components=comps, code_path=code,
                                      active_in_main="yes", mechanism=mech["mech"], mech_json=json.dumps(mech), notes=note)})
            continue
        # ---------- everything else: table of rules ----------
        L = loc
        if pid == "biomass_logging_extraction_rate_sensitivity":
            side, mech, active = "supply", {"mech": "zero", "reason": "logging residues = 0 in the main potential (decision 54); the rate acts only in the high-biomass sensitivity"}, "no"
            code = L("scripts_project/d1_biomass.py", "logging")
        elif pid.startswith("biomass_msw_ch4_yield_"):
            share = 0.85 if "food" in pid else 0.15
            side, mech = "supply", {"mech": "store_pot_scale", "name_regex": r" biomass msw_organic_biogas$", "share": share}
            comps = "Stores '<c> biomass msw_organic_biogas' (potential proportional to CH4 yield)"; code = L("scripts_project/d1_biomass.py", "ch4")
            note = f"食物 / 园林垃圾在沼气潜力中的能量份额取 {share}（INFERENCE：各国食物份额 0.32–0.55，园林 0–0.11）"
        elif pid == "biomass_overflow_rule":
            side, mech = "demand", {"mech": "discrete", "indicator": "biomass_overflow"}
            code = L("scripts_project/s2_layers.py", "biomass_overflow_mode"); note = "规则（固定生物质超出潜力部分转有用热）；VN 溢出 20.9 TWh（I2）"
        elif pid == "bunker_node_rule":
            side, mech = "network", {"mech": "discrete"}; code = L("scripts_project/s2_layers.py", "apply_bunker_attribution") if False else L("scripts_project/v3_layers.py", "bunker")
            note = "国际燃料舱负荷的节点分配规则，离散"
        elif pid == "candidate_cap_hydro_all_LA":
            side, mech = "supply", {"mech": "su_pnom_max", "carrier": ["hydro"], "country": "LA"}
            comps = "StorageUnit carrier 'hydro' (new) in LA, p_nom_max"; code = L("scripts_project/s4b_candidates.py", "CANDIDATE_CAPS_S4B2")
        elif pid in ("co2_extra_asean_offshore_storage_eur2009", "co2_extra_asean_storage_cost"):
            side, active = "cost", "no"
            mech = {"mech": "zero", "reason": "decision-89 basis; the main network uses co2_extra_asean_storage_cost_unified (decision 95 a): store capital_cost 54.698 = shipping chain 24.698 + 30"}
            code = L("scripts_project/s4e_layers.py", 'registry.loc["co2_extra_asean_storage_cost"')
        elif pid == "co2_extra_asean_shipping_chain_4500km":
            side, mech = "cost", {"mech": "store_cc", "carrier": ["co2 sequestered extra-ASEAN"], "scale": conv04}
            comps = "Stores 'co2 sequestered extra-ASEAN <c>' capital_cost (EUR/t)"; code = L("scripts_project/s4e_layers.py", "co2_extra_asean_shipping_chain_4500km")
        elif pid == "co2_extra_asean_storage_cost_unified":
            side, mech = "cost", {"mech": "store_cc", "carrier": ["co2 sequestered extra-ASEAN"], "scale": 1.0}
            comps = "Stores 'co2 sequestered extra-ASEAN <c>' capital_cost (EUR/t)"; code = L("scripts_project/s4e_layers.py", "co2_extra_asean_shipping_chain_4500km")
        elif pid in ("co2_injection_cap_unified_KH", "co2_storage_potential_KH", "co2_storage_component_KH_undiscovered_saline_text_about_85_mt"):
            side = "supply"; sc = 1.0 if pid.startswith("co2_injection") else 1e9 / 50.0
            mech = {"mech": "scalar_rhs", "constraint": "research_co2_storage_cap-KH", "scale": sc, "store": "co2 sequestered KH"}
            comps = "Global constraint research_co2_storage_cap-KH (annual injection = potential / 50 a)"; code = L("scripts_project/s2_layers.py", "injection_cap")
            if pid != "co2_injection_cap_unified_KH":
                note = "与 co2_injection_cap_unified_KH 同一约束（潜力 / 50 年），不重复计入排序（duplicate_of）"; mech["duplicate_of"] = "co2_injection_cap_unified_KH"
        elif pid in ("co2_injection_cap_unified_TL", "co2_storage_potential_TL", "co2_storage_component_TL_ogci_aggregated"):
            side, active = "supply", "no"
            mech = {"mech": "zero", "reason": "TL storage potential 0 by status UNASSESSED (no national assessment); no TL storage constraint or store in the network"}
            code = L("scripts_project/s2_layers.py", "injection_cap")
        elif pid in ("co2_land_transport_rail_loading_cost", "co2_land_transport_rail_unit_cost"):
            side, mech = "cost", {"mech": "lao_rail", "role": "loading" if "loading" in pid else "unit"}
            comps = "Links 'LA2 k co2 transit*' (land leg) and 'liquid transit rail' (VN<->LA liquids)"; code = L("scripts_project/v3_layers.py", "co2_land_transport_rail_unit_cost")
            note = "LA 各节点陆段成本（co2_lao_transit_land_cost_LA2_k）由本行推导；排序时两者不重复相加"
        elif pid.startswith("co2_lao_transit_land_cost_"):
            k = pid.rsplit("_", 1)[-1]; side = "cost"
            mech = {"mech": "link_mc", "name_regex": f"^LA2 {k} co2 transit", "formula": "const"}
            comps = f"Links 'LA2 {k} co2 transit to VN store / transit ship / transit export extra-ASEAN' marginal_cost"; code = L("scripts_project/s4d_layers.py", "co2_lao_transit")
            mech["duplicate_of"] = "co2_land_transport_rail_unit_cost"
        elif pid == "co2_sequestration_cost_price_year":
            side = "cost"; notch_lo, notch_hi = 0.86, 1.0
            basis = "PROPOSED: price year of the 30 EUR/t PyPSA-Eur constant unknown; factor 0.86-1.0 by analogy with aeo8_price_year_factor (decision 131)"
            mech = {"mech": "store_cc_factor", "carrier": ["co2 sequestered"], "extra": {"carrier": ["co2 sequestered extra-ASEAN"], "base_part": 30.0}, "value_in_network": 1.0}
            comps = "Stores 'co2 sequestered <c>' capital_cost 30 EUR/t (+ the 30 EUR/t part of the extra-ASEAN cost)"; code = L("scripts_project/s2_layers.py", "sequestration_cost")
        elif pid == "co2_ship_chain_fixed_cost":
            side, mech = "cost", {"mech": "link_mc", "carrier": ["CO2 ship", "CO2 transit ship"], "formula": "const"}
            comps = "Links 'CO2 ship', 'CO2 transit ship' marginal_cost"; code = L("scripts_project/s4d_layers.py", "co2_ship_chain")
        elif pid == "co2_ship_chain_per_km_cost":
            side, mech = "cost", {"mech": "link_mc", "carrier": ["CO2 ship", "CO2 transit ship"], "formula": "co2_per_km"}
            comps = "Links 'CO2 ship', 'CO2 transit ship' marginal_cost"; code = L("scripts_project/s4d_layers.py", "co2_ship_chain")
        elif pid == "co2_ship_route_factor":
            side, mech = "cost", {"mech": "link_mc", "carrier": ["CO2 ship", "CO2 transit ship"], "formula": "co2_route_factor"}
            comps = "Links 'CO2 ship', 'CO2 transit ship' marginal_cost"; code = L("scripts_project/s4d_layers.py", "co2_ship_route_factor")
        elif pid.startswith("cookstove_") or pid.startswith("demand_") or (pid.startswith("industry_") and pid not in ("industry_heat_band_technology_map", "industry_heat_hydrogen_not_represented")):
            side, mech = "demand", {"mech": "demand_I2"}
            code = "I2/SENSITIVITY_TOP10.csv; I2/MISSING_DATA_ALL.csv (第 211 项：需求侧已排，不重复)"
        elif pid in ("industry_heat_band_technology_map", "industry_heat_hydrogen_not_represented"):
            side, mech = "supply", {"mech": "discrete"}; code = L("scripts_project/s2_layers.py", "HEAT_BAND_TECH")
            note = "工业有用热各温度档的可选技术集合（规则）"
        elif pid.startswith("corridor_apg"):
            name = "APG11_TH_MM" if "apg11" in pid else "APG17_LA_MM"; side = "network"
            mech = {"mech": "line_length_cc", "names": [name]}
            comps = f"Line '{name}' capital_cost (per km x length)"; code = L("scripts_project/s3_0_corridors.py", "nearest")
            note = "长度还影响线损代理（未计入，一阶以投资为主）"
        elif pid.startswith("disconnected_") or pid in ("scenario_switch_co2_shipping_intra_asean",):
            side, active = "network", "no"
            mech = {"mech": "zero", "reason": "applies to the disconnected scenario only; F1 (integrated) and F2 (no_new_xb) unchanged -> dB6 = 0"}
            code = L("scripts_project/m08a_layers.py", "def apply_co2_shipping") if "co2_shipping" in pid else L("scripts_project/m08a_layers.py", "def apply_stock_mode")
        elif pid == "scenario_switch_remove_countries":
            side, active = "network", "no"; mech = {"mech": "zero", "reason": "coalition variants only (Owen leave-one-out); F1 / F2 main unchanged"}
            code = L("scripts_project/m08a_layers.py", "def apply_remove_countries")
        elif pid == "scenario_switch_wacc_mode":
            side, mech = "cost", {"mech": "wacc_mode"}; notch_lo = notch_hi = None
            basis = "registered alternative: finance.wacc_mode = country_specific (COUNTRY_WACC_REAL_M08A.csv real rates; cross-border = mean of ends; distributed keep 0.04)"
            comps = "all extendable components with an annuity (COMPONENT_COST_BREAKDOWN rows)"; code = L("scripts_project/s4c_layers.py", "def apply_wacc_mode")
        elif pid.startswith("wacc_"):
            side, active = "cost", "no"
            mech = {"mech": "zero", "reason": "inactive in the main run (finance.wacc_mode = uniform); its effect is inside scenario_switch_wacc_mode"}
            code = L("scripts_project/s4c_layers.py", "def apply_wacc_mode")
        elif pid == "ev_annual_km_per_vehicle":
            side, mech = "supply", {"mech": "ev_fleet", "exponent": -1.0}
            comps = "EV battery stores e_nom and BEV charger p_nom (fleet N = annual EV energy / (km / (53.19 x 100)))"; code = L("scripts_project/v3_layers.py", "def apply_ev_structure")
            note = "第 186 项 F3 / F4（EV 车队 ×0.5）会直接求解这一方向"
        elif pid == "ev_mwh_per_vehicle_year":
            side, active = "supply", "no"; mech = {"mech": "zero", "reason": "derived row (km / efficiency); not read by the build, the effect is counted under ev_annual_km_per_vehicle", "duplicate_of": "ev_annual_km_per_vehicle"}
            code = L("scripts_project/v3_layers.py", "ev_annual_km_per_vehicle")
        elif pid in ("existing_fleet_cost_rule", "existing_fleet_cost_year_rule", "existing_fleet_geothermal_exception"):
            side, mech = "cost", {"mech": "discrete", "indicator": "existing_fom"}
            code = L("scripts_project/m08a_layers.py", "VINTAGE_EXCEPTIONS")
            note = "存量机组 FOM 是目标外常数（F1 / F2 相同存量，对 ΔB6 为 0）；VOM 部分随规则变化，需备选规则才能定量"
        elif pid.startswith("feedstock_full_release_2050_"):
            side, active = "rule", "no"
            mech = {"mech": "discrete", "indicator": "co2_dual_times_range", "country": cc}
            code = L("scripts_project/s2b_feedstock.py", "full"); note = "原料碳全释放口径（敏感性，主算不用）：影响国家 CO₂ 约束右端，需按敏感性求解"
        elif pid in ("fleet_include_construction_units",):
            side, mech = "supply", {"mech": "discrete"}; code = L("scripts_project/m08a_layers.py", "construction") ; active = "yes"
        elif pid == "fleet_waste_to_energy_skipped_s4b":
            side, active = "supply", "no"; mech = {"mech": "zero", "reason": "no waste-fuel pathway in the model (limitation); 170 MW not represented"}
            code = L("scripts_project/s4b_1_fleet_data.py", "waste")
        elif pid == "fuel_price_lng_regasification_adder":
            side, mech = "cost", {"mech": "gen_mc", "carrier": ["LNG import"]}
            comps = "Generators 'LNG import' marginal_cost"; code = L("scripts_project/s3_layers.py", "lng_regasification_adder_eur_per_mwh")
        elif pid.startswith("gas_production_node_allocation_"):
            side = "supply"
            if r.status == "DATA_PENDING":
                mech, active = {"mech": "zero", "reason": "TL has no domestic production field (load shares, DATA_PENDING)"}, "no"
            else:
                mech = {"mech": "gas_alloc", "country": cc}; notch_lo = notch_hi = None
                basis = "registered alternative: research.s3.gas.production_node_allocation = load_shares"
            comps = f"ResearchImportAnnual-<node> gas production caps of {cc}"; code = L("scripts_project/s3_layers.py", "production_node_allocation")
        elif pid == "gates_v6_g22_subset_m08a_additions":
            side, active = "rule", "no"; mech = {"mech": "zero", "reason": "acceptance gate key list; not part of the LP"}; code = L("scripts_project/m08b_static.py", "gates_v6")
        elif pid in ("geothermal_new_FOM_main", "geothermal_new_investment_main"):
            side, mech = "cost", {"mech": "gen_cc_part", "carrier": ["geothermal"], "part": "fom" if "FOM" in pid else "investment"}
            comps = "Generators 'geothermal' (new) capital_cost"; code = L("scripts_project/s2_costs.py", "geothermal")
        elif pid == "geothermal_new_VOM_main":
            side, mech = "cost", {"mech": "gen_mc", "carrier": ["geothermal"]}; comps = "Generators 'geothermal' marginal_cost"; code = L("scripts_project/s2_costs.py", "geothermal")
        elif pid in ("aeo8_price_year_factor_main", "aeo8_cost_price_year"):
            side = "cost"; notch_lo, notch_hi = 0.86, 1.0
            mech = {"mech": "aeo8_factor", "rows": ["geothermal"], "value_in_network": 1.0}
            if pid == "aeo8_cost_price_year":
                mech["duplicate_of"] = "aeo8_price_year_factor_main"; basis = "PROPOSED: treatment of the pending price year = factor 0.86-1.0 (aeo8_price_year_factor_main)"
            comps = "cost rows with aeo8_price_year_factor (costs_active_research.csv: geothermal only)"; code = L("scripts_project/s2_costs.py", "aeo8_price_year_factor")
        elif pid == "h2_terminal_capex_rule":
            side, mech = "cost", {"mech": "gen_cc", "carrier": ["H2 import"]}; comps = "Generators 'H2 import' capital_cost"; code = L("scripts_project/s3_layers.py", "def h2_terminal_capex")
        elif pid.startswith("import_price_decline_estimate_"):
            side, active = "cost", "no"; mech = {"mech": "zero", "reason": "not read by the build: input to import_price_sensitivity_low_fraction"}
            code = L("scripts_project/s3_7_import_price_decline.py", "decline")
        elif pid == "import_price_sensitivity_low_fraction":
            side = "cost"; notch_lo, notch_hi = -0.2, -0.1164; basis = "registered sensitivity: import prices x (1 - 0.2) (and the estimated decline 11.64 %)"
            mech = {"mech": "gen_mc_rel", "carrier": ["H2 import", "ammonia import", "methanol import", "FT fuel import"], "value_in_network": 0.0}
            comps = "Generators 'H2 / ammonia / methanol / FT fuel import' marginal_cost"; code = L("scripts_project/s3_layers.py", "import")
        elif pid == "liquid_co2_structure_rule":
            side, mech = "network", {"mech": "discrete"}; code = L("scripts_project/v3_layers.py", "co2")
        elif pid == "liquid_ship_capacity_rule":
            side, mech = "network", {"mech": "link_pnom_fixed", "carrier": list(SHIP_CARRIER.values()) + ["liquid transit rail"]}
            comps = "ship / transit links p_nom = ASEAN annual demand / 8,760 x 10"; code = L("scripts_project/v3_layers.py", "def add_liquid_shipping")
        elif pid == "liquid_ship_cargo_loss_per_km":
            side, mech = "cost", {"mech": "link_eff_km", "carrier": list(SHIP_CARRIER.values()), "basis": "td_tanker"}
            comps = "ship links efficiency = 1 - loss x km (S-B)"; code = L("scripts_project/v3_layers.py", "def ship_unit")
        elif pid.startswith("liquid_ship_ckm_") or pid.startswith("liquid_ship_fixed_"):
            key = pid.rsplit("_", 1)[-1]; b = "td_tanker" if "_td_" in pid else "ieaghg"; side = "cost"
            mech = {"mech": "link_mc", "carrier": [SHIP_CARRIER[key]], "formula": "const" if "_fixed_" in pid else "route_km", "basis": b}
            comps = f"Links '{SHIP_CARRIER[key]}' marginal_cost ({'S-B 365x24h screening main' if b == 'td_tanker' else 'S-A 2920x3h main, decision 187'})"
            code = L("scripts_project/v3_layers.py", "def ship_unit")
        elif pid in ("liquid_ship_hours_per_year", "liquid_ship_speed_km_h"):
            side, mech = "cost", {"mech": "link_mc", "carrier": list(SHIP_CARRIER.values()), "formula": "inverse_rel", "basis": "td_tanker"}
            comps = "ship links c_km (S-B): capital + FOM per MWh-km proportional to 1 / (hours x speed)"; code = L("scripts_project/v3_layers.py", "def ship_unit")
            note = "INFERENCE：S-B 的每 MWh·km 成本与 航速 × 年运行小时 成反比"
        elif pid.startswith("liquid_ship_mwh_per_t_"):
            key = pid.rsplit("_", 1)[-1]; side = "cost"
            carriers = [SHIP_CARRIER[key]]
            mech = {"mech": "link_mc", "carrier": carriers + ["liquid transit rail"], "formula": "inverse_rel", "transit_carrier_match": key}
            comps = f"Links '{SHIP_CARRIER[key]}' and LA liquid transit marginal_cost (per-t cost / heating value)"; code = L("scripts_project/v3_layers.py", "liquid_ship_mwh_per_t_")
        elif pid in ("lng_terminal_cap_rule", "lng_terminal_expansion_mode"):
            side, mech = "supply", {"mech": "discrete", "indicator": "lng_new_capacity"}; code = L("scripts_project/s3_layers.py", "lng_expansion")
            if pid == "lng_terminal_expansion_mode":
                active = "no"
        elif pid == "lng_terminal_expansion_capex_main":
            side, mech = "cost", {"mech": "gen_cc", "carrier": ["LNG import"]}; comps = "Generators 'LNG import' capital_cost"; code = L("scripts_project/s3_layers.py", "lng_terminal_expansion_capex_main")
        elif pid == "nuclear_cost_rule":
            side, mech = "cost", {"mech": "discrete", "indicator": "unbuilt_rc", "carrier": ["nuclear", "nuclear SMR"]}; code = L("scripts_project/s2_costs.py", "smr_")
        elif pid.startswith("nuclear_plan_cap_"):
            side, active = "supply", "no"; mech = {"mech": "zero", "reason": "sensitivity national_plans only (status SENSITIVITY); nuclear unbuilt in the main runs"}
            code = L("scripts_project/s4b_candidates.py", "nuclear")
        elif pid == "offwind_alpha_calibration_rule":
            side = "supply"; notch_lo, notch_hi = 0.9095 / 1.0456 - 1.0, 1.2944 / 1.0456 - 1.0
            basis = "PROPOSED: no offshore calibration; alpha 1.0 -> relative range of the onshore proxy alpha (-13.0 % / +23.8 %); dCF/CF = 1.59 x dalpha/alpha (PH row, high-CF regime)"
            mech = {"mech": "gen_cf", "carrier": ["offwind-ac", "offwind-dc", "offwind-float", "offwind existing"], "eps": EPS_OFFWIND, "relative_notch": True}
            comps = "offshore wind p_max_pu (all countries)"; code = L("scripts_project/s4a_profiles.py", "WIND_CALIBRATION_ALPHA")
        elif pid.startswith("onwind_alpha_"):
            side = "supply"; mech = {"mech": "gen_cf", "carrier": ["onwind", "onwind existing"], "country": cc, "eps": EPS_WIND}
            comps = f"onshore wind p_max_pu in {cc}"; code = L("scripts_project/s4a_profiles.py", "WIND_CALIBRATION_ALPHA")
            note = f"dCF/CF = {EPS_WIND} x dalpha/alpha（ID 行 alpha 1 -> 主值，VERIFIED 表值；外推到区间端点为 INFERENCE）"
        elif pid.startswith("potential_"):
            side = "supply"; target = {"geothermal": ["geothermal"], "hydro": ["hydro"], "PHS": ["PHS"]}
            kind = "geothermal" if "geothermal" in pid else ("hydro" if "hydro" in pid else "PHS")
            dcap = {"potential_geothermal_total_resource_PH_DATA_PENDING": 4160.0, "potential_hydro_KH_DATA_PENDING": 2973.0, "potential_hydro_TH_DATA_PENDING": 15155.0,
                    "potential_hydro_TL_DATA_PENDING": 252.0, "potential_PHS_per_country_ALL_DATA_PENDING": 20700.0}.get(pid, 100.0)
            notch_lo, notch_hi = 0.0, dcap
            basis = (f"PROPOSED: potential DATA_PENDING; notch = +{dcap:,.0f} MW of candidates (figure quoted in the registry description; "
                     + ("100 MW placeholder where no figure exists" if dcap == 100.0 else "secondary / plan figure") + ")")
            mech = {"mech": "new_capacity_rc", "carrier": target[kind], "country": cc if cc else "", "value_in_network": 0.0}
            comps = f"candidate {kind} capacity (none or capped in the network)"; code = L("scripts_project/s4a_3_potentials.py", kind if kind != "PHS" else "PHS")
        elif pid == "process_emissions_boundary_rule":
            side, mech = "rule", {"mech": "discrete"}; code = L("scripts_project/s2_0_process_emissions.py", "boundary")
        elif pid.startswith("renewable_cap_built_solar_rooftop_"):
            side, mech = "supply", {"mech": "gen_pnom_max", "carrier": ["solar rooftop"], "country": cc}
            comps = f"Generators 'solar rooftop' in {cc}, p_nom_max"; code = "pypsa-asean @5bacad70 prepare_sector_network.py 2862-2925 (rooftop p_nom_max inherited in the network)"
        elif pid in ("renewable_landuse_rule_solar", "renewable_openforest_sensitivity_trigger", "renewable_rooftop_method_built"):
            side, mech = "supply", {"mech": "discrete", "indicator": "solar_cap_binding"}; code = L("scripts_project/m08a_data.py", "landuse") if False else "S4R supplement 01 R2 (registry source_locator)"
        elif pid in ("share_Al_primary_fraction_2050", "share_DRI_fraction_2050", "share_HVC_chemical_recycling_fraction_2050", "share_HVC_mechanical_recycling_fraction_2050",
                     "share_HVC_primary_fraction_2050", "share_HVC_environment_sequestration_fraction", "share_St_primary_fraction_2050", "share_MWh_elec_per_tHVC_chemical_recycling",
                     "share_MWh_elec_per_tHVC_mechanical_recycling"):
            side, mech = "demand", {"mech": "demand_I2", "route_share": True}
            code = L("scripts_project/s3_0_industry_ratios.py", pid.replace("share_", "").replace("_2050", ""))
            note = "工业工艺路线份额：只进入工业需求表推导（I2 / W08 链），网络中体现为工业各载体负荷"
            if pid == "share_HVC_environment_sequestration_fraction":
                mech = {"mech": "zero", "reason": "degenerate registered range (0..0)"}; side = "demand"
        elif pid in ("share_aviation_demand_factor", "share_HVC_demand_factor", "share_bev_avail_max"):
            side, active = "demand" if "demand" in pid else "supply", "no"; mech = {"mech": "zero", "reason": "registered but not read by the network build (grep: only the registry writer)"}
            code = "grep: s4b_0_data.py only" if "demand" in pid else "grep: no consumer"
        elif pid == "share_bev_avail_mean":
            side, active = "supply", "no"; mech = {"mech": "zero", "reason": "v3 EV structure E2 overrides the charger p_max_pu with the plug-in profile (v3_layers.apply_ev_structure)"}
            code = L("scripts_project/s2_layers.py", "bev_avail = ") + " ; " + L("scripts_project/v3_layers.py", "charger_ts[ch] = ev_series")
        elif pid == "share_bev_charge_efficiency":
            side, mech = "supply", {"mech": "link_eff", "carrier": ["BEV charger"], "port": 1}; comps = "Links 'BEV charger' efficiency"; code = L("scripts_project/s2_layers.py", 'add_link(n, f"{node} BEV charger"')
        elif pid == "share_bev_charge_rate":
            side, mech = "supply", {"mech": "link_pnom_fixed", "carrier": ["BEV charger"]}; comps = "Links 'BEV charger' p_nom = N x rate"; code = L("scripts_project/v3_layers.py", "N * rate")
        elif pid in ("share_bev_dsm_availability", "share_bev_energy"):
            side, mech = "supply", {"mech": "store_enom_fixed", "carrier": ["EV battery"]}; comps = "Stores 'EV battery' e_nom = N x e_car x avail"; code = L("scripts_project/v3_layers.py", "e_nom=N * e_car * avail")
        elif pid == "share_bev_dsm_restriction_value":
            side, mech = "supply", {"mech": "store_floor", "carrier": ["EV battery"]}; comps = "Stores 'EV battery' e_min_pu at the restriction hour"; code = L("scripts_project/v3_layers.py", "emin_ts[st]")
        elif pid in ("share_bev_dsm_restriction_time", "share_bev_dsm", "share_ammonia", "share_shipping_hydrogen_liquefaction", "share_waste_to_energy", "share_waste_to_energy_cc"):
            side, mech = "rule", {"mech": "discrete"}; code = "registry source_locator: " + str(r.source_locator)[:80]
        elif pid in ("share_land_transport_electric_share_2050", "share_land_transport_ice_share_2050"):
            side, mech = "route", {"mech": "transport_shift", "to": "oil"}
            if pid.endswith("electric_share_2050"):
                notch_lo, notch_hi = -0.3, 0.0; basis = "registered range 0.7-1 as a shift of 0.3 of land transport from BEV to ICE (paired with the ICE share 0-0.3)"
            else:
                notch_lo, notch_hi = 0.0, -0.3; basis = "registered range 0-0.3 as the same BEV -> ICE shift (paired with the electric share)"; mech["duplicate_of"] = "share_land_transport_electric_share_2050"
            mech["value_in_network"] = 0.0
            comps = "Loads 'land transport EV' (EV battery bus) vs oil final energy (country CO2 meter)"; code = L("scripts_project/s2_layers.py", "share_land_transport_electric_share_2050")
        elif pid == "share_land_transport_fuel_cell_share_2050":
            side, mech = "route", {"mech": "transport_shift", "to": "H2", "value_in_network": 0.0, "scenario_choice": True}; notch_lo, notch_hi = 0.0, -1.0
            basis = "registered range 0-1 as a shift of land transport from BEV to FCEV (regime change; first order unreliable)"
            comps = "Loads 'land transport EV' vs '<node> H2'"; code = L("scripts_project/s2_layers.py", "share_land_transport_fuel_cell_share_2050")
        elif pid in ("share_shipping_methanol_share_2050", "share_shipping_oil_share_2050", "share_shipping_hydrogen_share_2050"):
            side = "route"; to = "H2" if "hydrogen" in pid else "oil"
            mech = {"mech": "shipping_shift", "to": to, "value_in_network": 0.0}
            if pid == "share_shipping_methanol_share_2050":
                notch_lo, notch_hi = -0.45, 0.0; basis = "registered range 0.55-1 as a shift of 0.45 of shipping from methanol to oil (paired with the oil share 0-0.45)"
            elif pid == "share_shipping_oil_share_2050":
                notch_lo, notch_hi = 0.0, -0.45; basis = "registered range 0-0.45 as the same methanol -> oil shift"; mech["duplicate_of"] = "share_shipping_methanol_share_2050"
            else:
                notch_lo, notch_hi = 0.0, -1.0; basis = "registered range 0-1 as a shift from methanol to hydrogen (regime change; first order unreliable)"; mech["scenario_choice"] = True
            comps = "Loads '<node> shipping domestic / international methanol' vs oil final (bunker / country meter) or H2"; code = L("scripts_project/s2_layers.py", "share_shipping_methanol_share_2050")
        elif pid.startswith("share_agriculture_machinery_"):
            side = "route"; what = pid.replace("share_agriculture_machinery_", "")
            mech = {"mech": "agri_shift", "what": what}
            if what == "oil_share":
                mech["duplicate_of"] = "share_agriculture_machinery_electric_share"; note = "与电动份额成对（两者之和为 1），同一移动不重复排序"
            comps = "Loads 'agriculture machinery electric' and agriculture oil final"; code = L("scripts_project/s2_layers.py", "share_agriculture_machinery_electric_share")
        elif pid in ("share_transport_electric_efficiency", "share_transport_ice_efficiency"):
            side = "route"; mech = {"mech": "ev_load_scale", "what": "el_eff" if "electric" in pid else "ice_eff"}
            comps = "Loads 'land transport EV' (oil_to_el = ice / el) and, for ICE efficiency, the EV fleet proxy"; code = L("scripts_project/s2_layers.py", "oil_to_el = ")
        elif pid == "share_transport_fuel_cell_efficiency":
            side, active = "route", "no"; mech = {"mech": "zero", "reason": "fuel-cell share 0 in the main run: no FCEV load"}; code = L("scripts_project/s2_layers.py", "oil_to_h2 = ")
        elif pid in ("share_MWh_H2_per_tNH3_electrolysis", "share_MWh_elec_per_tNH3_electrolysis", "share_MWh_NH3_per_tNH3"):
            side = "supply"; mech = {"mech": "hb_eff", "what": {"share_MWh_H2_per_tNH3_electrolysis": "h2", "share_MWh_elec_per_tNH3_electrolysis": "el", "share_MWh_NH3_per_tNH3": "nh3"}[pid]}
            comps = "Links 'Haber-Bosch' efficiencies (NH3 per H2, electricity per H2)"; code = L("scripts_project/s2_layers.py", "MWh_H2_per_tNH3")
            if pid == "share_MWh_NH3_per_tNH3":
                note = "同时用于工业氨需求 t→MWh 换算（需求侧，I2）"
        elif pid in ("share_MWh_MeOH_per_MWh_H2", "share_MWh_MeOH_per_MWh_e", "share_MWh_MeOH_per_tCO2"):
            side = "supply"; mech = {"mech": "meoh_eff", "what": {"share_MWh_MeOH_per_MWh_H2": "h2", "share_MWh_MeOH_per_MWh_e": "el", "share_MWh_MeOH_per_tCO2": "co2"}[pid]}
            comps = "Links 'methanolisation' efficiencies (and capital cost per MW_H2 for MeOH per H2)"; code = L("scripts_project/s3_layers.py", "meoh_per_h2, meoh_per_tco2, meoh_per_e")
        elif pid == "share_transport_electric_efficiency":
            pass
        elif pid in ("smr_efficiency_proxy", "smr_lifetime_proxy"):
            side, mech = "cost", {"mech": "unbuilt_check", "carrier": ["nuclear SMR"], "what": "efficiency" if "efficiency" in pid else "lifetime"}
            comps = "Generators 'nuclear SMR' (marginal cost / annuity)"; code = L("scripts_project/s2_costs.py", "smr_")
        elif pid == "th_my_line91_s_nom_2025":
            side, mech = "network", {"mech": "line_existing", "names": ["91"]}; comps = "Line '91' MY_Peninsular2 0 - TH2 0 s_nom (stock)"; code = L("scripts_project/s4f_2_corridors.py", "91")
        elif pid == "typhoon_node_flag_rule":
            side, active = "cost", "no"; mech = {"mech": "zero", "reason": "acts only with research.renewable.typhoon_premium on (main off)"}; code = L("scripts_project/s4b_layers.py", "typhoon")
        elif pid == "typhoon_premium_switch":
            side, mech = "cost", {"mech": "typhoon", "threshold_col": "flag_ge_1", "value_in_network": 0.0}; notch_lo, notch_hi = 15.0, 35.0
            basis = "registered sensitivity: premium 15-35 % (main off) on exposed wind node-technologies (>= 1 passage / 10 a)"
            comps = "wind generators at exposed nodes (TYPHOON_EXPOSURE_BY_NODE.csv)"; code = L("scripts_project/s4b_layers.py", "typhoon")
        elif pid.startswith("waste_uncollected_open_burned_share_") or pid == "waste_plastic_share_LA":
            side, mech = "rule", {"mech": "fixed_emission_scale", "carrier": ["plastic waste"], "country": cc}
            comps = f"Generator '<node> plastic waste source' (p_min_pu = p_max_pu = 1) -> atmosphere {cc}"; code = L("scripts_project/s2_layers.py", "plastic waste source")
            note = "INFERENCE 上界：假设该国塑料燃烧排放全部与该份额成正比"
        elif pid == "xb_stock_la_th_dedicated_lines":
            side = "network"; notch_lo, notch_hi = -0.5, 0.5; basis = "PROPOSED: no single source of operating capacity; +-50 % (grade-C default, D1 L13) on the LA-TH dedicated plant lines"
            mech = {"mech": "link_pnom_fixed", "carrier": ["dedicated plant line"], "bus1_prefix": "TH", "relative_notch": True, "value_in_network": 0.0}
            comps = "Links 'dedicated plant line LA2 k - TH2 j' p_nom"; code = L("scripts_project/v3_layers.py", "dedicated plant line")
        else:
            side, mech = "rule", {"mech": "discrete"}; code = "registry source_locator: " + str(r.source_locator)[:80]
            note = "未归类（按离散规则处理）"
        if mech.get("mech") == "discrete" and basis.startswith("registered") and lo is None:
            basis = "discrete rule / flag: no first-order change"
        out.append({**rec, **dict(side=side, notch_low=notch_lo, notch_high=notch_hi, notch_basis=basis, network_components=comps, code_path=code,
                                  active_in_main=active, mechanism=mech["mech"], mech_json=json.dumps(mech), notes=note)})
    return out


def reconcile(repo: Path) -> dict:
    res = {}
    for rev in ("72083fde", "aad8e476"):
        txt = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:research_inputs/registry_v5/DATA_REGISTRY.csv"], capture_output=True, text=True, check=True).stdout
        d = pd.read_csv(io.StringIO(txt), dtype=str, keep_default_na=False)
        use = d[d.status.isin(IN_USE)]; c = use[use.tier == "C"]
        res[rev] = dict(rows=int(len(d)), in_use=int(len(use)), c_in_use=int(len(c)), by_family=c.param_id.map(family_201).value_counts().to_dict(),
                        status_by_tier={s: g.tier.value_counts().to_dict() for s, g in d.groupby("status")})
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    repo, out = Path(a.repo), Path(a.out)
    regp = repo / "research_inputs/registry_v5/DATA_REGISTRY.csv"
    reg = pd.read_csv(regp, dtype=str, keep_default_na=False).set_index("param_id")
    rows = rows_for(reg, Locator(repo))
    df = pd.DataFrame(rows)
    cols = ["param_id", "family_201", "side", "value", "unit", "country", "status", "sensitivity_low", "sensitivity_high", "notch_low", "notch_high", "notch_basis",
            "why_C", "source", "decision_ref", "derivation_script", "code_path", "network_components", "active_in_main", "mechanism", "mech_json", "notes"]
    df = df[cols].sort_values("param_id")
    df.to_csv(out / "C_GRADE_INVENTORY.csv", index=False, lineterminator="\n")
    rec = reconcile(repo)
    meta = dict(registry=str(regp), registry_sha256=sha256(regp), rows=int(len(df)), by_family_201=df.family_201.value_counts().to_dict(),
                by_side=df.side.value_counts().to_dict(), by_mechanism=df.mechanism.value_counts().to_dict(), reconciliation_item_201=rec,
                code_paths_not_found=int(df.code_path.str.contains("NOT_FOUND").sum()))
    (out / "C_GRADE_INVENTORY_META.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(json.dumps({k: meta[k] for k in ("rows", "by_family_201", "by_side", "by_mechanism", "code_paths_not_found")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
