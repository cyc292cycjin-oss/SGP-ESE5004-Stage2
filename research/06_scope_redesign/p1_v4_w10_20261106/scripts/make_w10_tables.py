#!/usr/bin/env python3
"""V4 W10-3: download candidates for the TOP30 rows and the treatment of the remaining grade-C rows.

Reads TOP30.csv, IMPACT_FIRST_ORDER.csv and C_GRADE_INVENTORY.csv (written by rerank_with_results.py / build_inventory.py) and the curated
source table below; writes W10_DOWNLOAD_CANDIDATES.csv and REMAINING_C_TREATMENT.csv. The sources are named from memory unless stated:
every source carries status INFERENCE (the reviewer verifies the address before the user downloads). Data grades follow I2: A actual
statistics, B official / national statistics, C derived, D model estimate or assumption, E missing.

usage: python make_w10_tables.py --dir <delivery dir>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

# param_id or prefix -> (current grade, target grade, sources, fields, difficulty, access, note)
SRC = {
    "scenario_switch_wacc_mode": ("C", "B（ID/MY/PH/TH/VN）；C（其余 6 国仍按 CRP 法）",
        "IEA Cost of Capital Observatory（2024/2025 更新，各国公用事业光伏 / 风电 WACC 区间）；IRENA (2023) The cost of financing for renewable power（国别 WACC 估计）；Damodaran 国家风险溢价表（2026-01，已用）；IMF WEO 2026-10 CPI（已用，名义转实际）",
        "各国名义税后 WACC（区间与中值）、技术、年份；通胀预期", "低", "公开网页 / PDF",
        "主算模式（uniform / country_specific）是用户决定；数据升级只核实 11 国实际 WACC 表 COUNTRY_WACC_REAL_M08A.csv"),
    "renewable_cap_built_solar_rooftop_": ("C", "B",
        "Joshi et al. (2021) Nature Communications 12:5738 全球屋顶光伏潜力网格数据（figshare）；Microsoft Global ML Building Footprints / Overture Maps 建筑轮廓（重算屋顶面积）；SG：SERIS / EMA 新加坡光伏路线图（屋顶潜力）；MY：SEDA Malaysia Renewable Energy Roadmap (MyRER) 屋顶潜力；VN：MOIT / GIZ 屋顶光伏潜力研究",
        "各国（最好各节点）可用屋顶面积或屋顶光伏技术潜力 GW", "中", "公开数据集（较大）+ 公开报告",
        "MY / VN / BN / TH / SG 的屋顶上限在 F2 中多为紧约束；作者链用建筑面积 × 0.1 kW/m²，未与东盟统计核对"),
    "share_transport_electric_efficiency": ("D", "B",
        "IEA Global EV Outlook 2025（分车型每公里电耗）；ICCT 东南亚两轮 / 三轮车与乘用车能耗研究；ACE AEO8 ATS 交通假设（AEDS 数据，见 I2 MISSING T01）；ADB 东南亚电动出行报告",
        "按车型（两轮、乘用车、公交、货车）的 kWh/km 与车队构成", "中", "公开报告；AEDS 需申请",
        "PyPSA-Eur 的 53.19 是欧洲乘用车值；东盟两轮车占比高，按车队构成加权会显著改变 EV 用电"),
    "share_land_transport_electric_share_2050": ("D", "B",
        "ACE AEO8 ATS 情景的 2050 交通燃料结构（AEDS）；IEA Southeast Asia Energy Outlook 2024（APS / NZE 情景电动化率）；各国 EV 路线图（TH 30@30、ID、VN）",
        "2050 年道路交通电、油、氢的能源或服务份额", "中", "公开报告；AEDS 需申请",
        "登记区间 0.7–1 实为情景选择（电动化率）；一阶估计按 30 % 转 ICE，变动大"),
    "share_transport_ice_efficiency": ("D", "B",
        "IEA GEVO 2025 / IEA Fuel Economy in Southeast Asia；ICCT 燃油经济性数据；各国车辆能效标签数据",
        "按车型的 L/100 km 或 MJ/km 与车队构成", "中", "公开报告",
        "影响 EV 负荷（oil_to_el = ICE / EV 效率）与 EV 车队代理"),
    "share_bev_charge_efficiency": ("D", "B",
        "IEA GEVO（充电损失）；美国 INL / ICCT 交流充电效率实测；SAE / IEC 充电桩效率测试", "交流 / 直流充电效率（电网到电池）", "低", "公开报告", ""),
    "offwind_alpha_calibration_rule": ("E", "C（偏差系数）/ B（若有实测）",
        "World Bank / ESMAP Offshore Wind Roadmap for Vietnam (2021) 各站点容量因子；Global Wind Atlas 3（DTU）海上 100 m 风速；EVN 近岸风电场（Bac Lieu、Soc Trang）发电量；ERA5 海上风速偏差文献",
        "海上风电容量因子或 100 m 风速观测，用于 alpha", "中", "公开报告 / 网页数据",
        "目前所有国家海上 alpha = 1；F2 中 VN 海上候选接近进入，一阶不可靠"),
    "fuel_price_lng_regasification_adder": ("D", "B",
        "TH ERC 公布的 PTT LNG（Map Ta Phut）终端服务费；MY Suruhanjaya Tenaga 第三方接入再气化费率（RGT Melaka / Pengerang）；SG SLNG 终端费率；ID BPH Migas 再气化费（Nusantara Regas、Arun）；IGU World LNG Report 2024",
        "再气化 + 外输费 USD/MMBtu，年份", "低", "监管机构公开文件",
        "F2 的 LNG 用量约为 F1 的 4 倍，所以对 B6 敏感"),
    "co2_ship_chain_": ("C", "B",
        "IEAGHG (2020) The status and challenges of CO2 shipping infrastructures；ZEP (2024) CO2 transport and storage costs 更新；Roussanaly et al. (2021) Energies 14:5635（7 / 15 barg 船运成本比较）；Element Energy (2018) Shipping CO2 – UK cost estimation study（BEIS）；ERIA CCUS in ASEAN 船运成本",
        "液化、船舶、港口、装卸的单位成本（固定段与每 km 段）、船型、年份", "低", "公开 PDF",
        "现用 IEAGHG 2004 换算；F2 中 CO₂ 船运量远大于 F1"),
    "co2_ship_route_factor": ("C", "B", "searoute 类港到港航线距离工具或 IMO / UNCTAD 港间距离表", "港间海上距离", "低", "公开工具", ""),
    "gas_production_node_allocation_": ("C", "B",
        "TH DMF（矿物燃料司）分气田月产量；MY PETRONAS / Suruhanjaya Tenaga 国家能源平衡（分区域产量）；ID SKK Migas 年报（分合同区产量）；MM MOGE；GEM GGIT 管道登陆点（已有）",
        "分气田产量与登陆点 / 处理厂所在节点", "中", "公开统计 + 已有 GEM 数据",
        "关键不是气田位置而是登陆点节点；一阶估计用了无井口节点的价格代理，且是规则切换，须求解确认"),
    "onwind_alpha_": ("D", "C / B（有风电场实测时）",
        "Global Wind Atlas 3（DTU，已用于 gwa_mean_ws100 检查）；IRENA Renewable Energy Statistics 2025（各国风电装机与发电量）；LA Monsoon Wind（600 MW）运行数据（EDL / 开发商）；Renewables.ninja 国家风电序列",
        "风电场实测容量因子或 100 m 风速偏差", "中", "公开网页数据；风电场数据需申请",
        "8 个代理国用 PH / TH / VN 校准值的容量加权；CF 对 alpha 的弹性约 2.8，区间端点外推"),
    "co2_sequestration_cost_price_year": ("E", "B",
        "PyPSA-Eur v2025.07.0 文档与 config 历史（co2_sequestration_cost 的价格年）；ERIA (2022/2024) CCUS in ASEAN 封存单位成本；IEAGHG 封存成本曲线；ZEP (2024)",
        "封存单位成本 EUR/t 及价格年", "低", "公开文档", "国内封存量约 650 Mt/a，价格年系数 0.86 时 ΔZ 约 −2.7 bn"),
    "biomass_potential_ID_oil_palm_trunk": ("C", "B",
        "ID 种植园总署 Statistik Perkebunan Kelapa Sawit（翻种面积、树龄结构）；BPDPKS PSR（小农翻种）数据；MPOB（MY 对照）；油棕树干可得性文献",
        "年翻种面积、每公顷树干量、可收集比例", "中", "公开统计 PDF",
        "登记区间 31.7–681 TWh 极宽；对 B6 小（−0.21 bn）但对 ID 的 Owen 分摊与系统成本大（上端 F1 −20.4 bn）"),
    "xb_stock_la_th_dedicated_lines": ("E", "B",
        "EGAT 年报（老挝 IPP 购电与专线）；EDL 年报；EPPO 购电合同清单（Nam Theun 2、Nam Ngum 2、Theun-Hinboun、Hongsa、Xayaburi、Xe Pian-Xe Namnoy、Nam Ngiep 1 合同 MW）；ACE APG Interconnections Project Profiles 2024（已用 955 MW）",
        "各专线额定容量与运行状态", "中", "公开年报", "F2 中专线价值高（−50 % 时 F2 +0.12 bn）"),
    "lng_terminal_expansion_capex_main": ("D", "B",
        "IGU World LNG Report 2024（再气化终端单位投资）；GIIGNL Annual Report 2025；OIES FSRU 与陆上终端成本研究", "单位投资 USD/(t/a) 或 USD/MW、寿命、年份", "低", "公开 PDF",
        "F1 / F2 新建终端容量差别大，且有未建终端接近进入"),
    "share_MWh_MeOH_per_tCO2": ("C", "A（化学计量，EXACT 可推导）",
        "化学计量 CO2 + 3H2 → CH3OH + H2O：每 t CO2 产甲醇 32.04 / 44.01 t × 5.528 MWh/t ≈ 4.025 MWh；DEA Technology Data for Renewable Fuels（甲醇合成）", "无需下载（可直接推导）", "低", "推导",
        "可直接以化学计量升级，不需外部数据"),
    "share_MWh_MeOH_per_MWh_H2": ("C", "B",
        "DEA Technology Data for Renewable Fuels（甲醇合成效率）；IRENA & Methanol Institute (2021) Innovation Outlook: Renewable Methanol", "合成段 MWh_MeOH / MWh_H2", "低", "公开 PDF",
        "航运全部用甲醇，ΔZ 大（低端 +9.1 bn），但 F1 / F2 相近"),
    "th_my_line91_s_nom_2025": ("C", "B",
        "EGAT / TNB 年报中 Sadao–Bukit Keteri 132 kV（或 115 kV）互联额定容量；HAPUA / ACE APG 现状报告（AIMS III）", "TH–MY 交流互联额定 MW 与运行状态", "低", "公开年报",
        "F2 中该线拥塞价值约 31 万 EUR/MW/a"),
    "ev_annual_km_per_vehicle": ("D", "C / B",
        "各国车辆年行驶里程统计（TH 陆运厅、VN、ID 交通部门调查）；ICCT / ADB 东南亚车辆活动数据；IEA Mobility Model（需授权）", "按车型的年行驶里程", "中至高", "公开统计稀缺",
        "第 186 项 F3 / F4（EV 车队 ×0.5）会直接求解这一方向"),
    "share_bev_dsm_restriction_value": ("D", "D（保留，敏感性）",
        "东盟充电行为调查（ADB / ICCT，若有）", "早晨最低电量要求", "高", "罕见", "行为假设，建议保留 C 并在正式批次做敏感性"),
    "share_agriculture_machinery_": ("D", "C",
        "FAO 农业机械化统计；各国农业普查（拖拉机数量与燃料）；AEO8 ATS 农业部门燃料结构", "农机燃料与电动化份额、效率", "高", "零散",
        "对 B6 约 0.05–0.07 bn；一阶估计把份额作用于整个农业燃油负荷（INFERENCE）"),
}


def lookup(pid: str):
    if pid in SRC:
        return SRC[pid]
    for k, v in SRC.items():
        if k.endswith("_") and pid.startswith(k):
            return v
    return ("C", "", "", "", "", "", "")


def short_flags(s: str) -> str:
    import re
    found = re.findall(r"(bound_switch|would_enter|investment_F1_F2_differs|degenerate|large_change|discrete_alternative|rank_unstable_vs_\w+|proxy|upper_bound|inference|not_representable|scenario_choice)", s or "")
    return ",".join(sorted(set(found)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    d = Path(ap.parse_args().dir)
    top = pd.read_csv(d / "TOP30.csv")
    rows = []
    for i, r in top.reset_index(drop=True).iterrows():
        cur, tgt, src, fields, diff, access, note = lookup(r.param_id)
        rows.append(dict(rank=i + 1, param_id=r.param_id, value=r.value, unit=r.unit, dB6_meur=round(r.dB6 / 1e6, 3), abs_dZ_max_meur=round(r.abs_dZ_max / 1e6, 3),
                         owen_max_country=r.owen_max_country, owen_max_meur=round(r.owen_max_eur / 1e6, 3) if pd.notna(r.owen_max_eur) else None,
                         first_order_flags=short_flags(r["flags"] if isinstance(r["flags"], str) else ""), current_grade=cur, target_grade=tgt, candidate_sources=src,
                         source_status="INFERENCE：凭记忆列出，网址待审阅端核实后交用户下载", fields_needed=fields, difficulty=diff, access=access, note=note,
                         evidence_tag="dB6 / dZ：INFERENCE（一阶外推，局部导数取自对偶，EXACT）"))
    pd.DataFrame(rows).to_csv(d / "W10_DOWNLOAD_CANDIDATES.csv", index=False, lineterminator="\n")
    # remaining rows: treatment by group
    imp = pd.read_csv(d / "IMPACT_FIRST_ORDER.csv")
    inv = pd.read_csv(d / "C_GRADE_INVENTORY.csv", dtype=str, keep_default_na=False)
    rest = imp[~imp.param_id.isin(top.param_id)].copy()
    mj = inv.set_index("param_id").mech_json.map(json.loads)
    rest["reason_key"] = ""
    for idx, r in rest.iterrows():
        m = mj.get(r.param_id, {})
        fl = r["flags"] if isinstance(r["flags"], str) else ""
        if r.side == "demand":
            key = "需求侧（第 211 项：已在 I2 SENSITIVITY_TOP10 / MISSING_DATA_ALL 排过，引用不重复）"
        elif m.get("duplicate_of"):
            key = f"与 {m['duplicate_of']} 同一机制，不重复排序"
        elif m.get("scenario_choice"):
            key = "情景选择（0→1 的区间），一阶不适用；建议作为情景而不是数据升级"
        elif r.mechanism == "zero":
            key = "主算中不起作用：" + m.get("reason", "")
        elif r.mechanism == "discrete":
            key = "离散规则 / 开关：一阶不可表示，需按备选规则求解"
        elif "not_representable" in fl:
            key = "网络中没有对应候选（DATA_PENDING → p_nom_max 0）：需先建候选再求解"
        elif r.abs_dB6 < 1e6:
            key = "|ΔB6| < 1 M EUR：影响小，保留 C 级"
        elif r.abs_dB6 < 10e6:
            key = "1–10 M EUR：影响小，保留 C 级，正式批次可不做敏感性"
        else:
            key = "10 M EUR 以上但未进前 30：保留 C 级，列入正式批次一揽子敏感性（按族同向扰动）"
        rest.at[idx, "reason_key"] = key
    sens = {
        "需求": "由 I2 / W08 的需求敏感性覆盖",
        "主算中不起作用": "只在对应开关打开时检查（同开关一起做敏感性）",
        "离散": "若开关对 B6 有意义，在 v4 正式批次以备选规则直接求解",
        "网络中没有": "补候选数据后作为新候选进入（数据升级而非敏感性）",
        "|ΔB6| < 1": "不做单独敏感性",
        "1–10": "不做单独敏感性；族级同向扰动覆盖",
        "10 M": "族级同向扰动（如生物质成本全部 ±50 %、潜力全部低档）一次求解",
        "与 ": "随主参数",
        "情景": "作为情景（例如 FCEV / 航运氢）而非数据敏感性",
    }
    g = rest.groupby(["reason_key", "family_201"]).agg(rows=("param_id", "size"), sum_abs_dB6_meur=("abs_dB6", lambda s: round(s.fillna(0).sum() / 1e6, 3)),
                                                       max_abs_dB6_meur=("abs_dB6", lambda s: round(s.fillna(0).max() / 1e6, 3)),
                                                       max_abs_dZ_meur=("abs_dZ_max", lambda s: round(s.fillna(0).max() / 1e6, 3)),
                                                       examples=("param_id", lambda s: "; ".join(list(s)[:4]))).reset_index()
    g["suggested_sensitivity"] = g.reason_key.map(lambda k: "登记区间退化（低 = 高 = 主值），无需敏感性" if "degenerate registered range" in k
                                                  else next((v for kk, v in sens.items() if k.startswith(kk) or kk in k[:6]), ""))
    g.to_csv(d / "REMAINING_C_TREATMENT.csv", index=False, lineterminator="\n")
    rest[["param_id", "family_201", "side", "mechanism", "dB6", "abs_dZ_max", "reason_key"]].to_csv(d / "REMAINING_C_BY_ROW.csv", index=False, lineterminator="\n")
    print(len(rows), "download candidates;", len(rest), "remaining rows in", len(g), "groups")


if __name__ == "__main__":
    main()
