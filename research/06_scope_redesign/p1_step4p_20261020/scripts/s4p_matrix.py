"""S4P: COUNTRY_AUDIT_MATRIX.csv / .md - 13 objects x 8 aspects, each cell with five items (物理量 / 成本影响 / 外部对照 / 判定 / 影响量级).
Numbers come from A_CHANNEL_*, ASPECT*_*.csv, ASPECTS_SUMMARY.json (VERIFIED); magnitude estimates are INFERENCE (arithmetic, no re-solve).
External comparisons cite registry sources and the EXT_*_BENCHMARKS files written by the web-search sub-agents (S4P)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4p_paths import BN_, COUNTRIES, OUT, load_json  # noqa: E402

OBJECTS = COUNTRIES + ["ASEAN_BUNKER", "ASEAN_POOL"]
ASPECTS = ["1 区域外兜底选项", "2 跨境流动与通道", "3 技术可用性", "4 需求", "5 CO2 封存", "6 生物质", "7 成本参数", "8 结算规则"]
A = load_json(OUT / "A_SUMMARY.json")
S = load_json(OUT / "ASPECTS_SUMMARY.json")
co2 = pd.read_csv(OUT / "ASPECT5_CO2.csv").set_index("country")
bio = pd.read_csv(OUT / "ASPECT6_BIOMASS.csv").set_index("country")
rule = pd.read_csv(OUT / "ASPECT8_B6_BY_RULE.csv", index_col=0)
vre = pd.read_csv(OUT / "ASPECT3_VRE_GW_FROM_LEDGER.csv").set_index(["carrier", "entity"])
EXT_PATH = OUT / "evidence" / "EXT_OVERRIDES.json"   # cell-level external comparison text filled after the sub-agents reported
EXT = load_json(EXT_PATH) if EXT_PATH.exists() else {}


def d(e):
    return A["entities"][e]["dis_minus_int_bn"]


def ch(e, s, k="dis_minus_int"):
    return A["entities"][e]["channels_bn"].get(s, {}).get(k, 0.0)


def tot(e, run):
    return A["entities"][e]["total_bn"][run]


def ext(obj, asp, default):
    return EXT.get(f"{obj}|{asp}", default)


# --------------------------------------------------------------------------------- hand-written cells (VERIFIED numbers; INFERENCE magnitudes)
C = {}


def cell(obj, asp, phys, cost, extc, verdict, mag):
    C[(obj, asp)] = dict(phys=phys, cost=cost, ext=ext(obj, asp, extc), verdict=verdict, mag=mag)


# ---- aspect 1: extra-ASEAN fall-back options (use TWh int / dis / NZE from ASPECT1)
U = S["aspect1"]["use_twh"]


def use(car, e):
    v = U.get(f"{car}|{e}", {})
    return f"{v.get('integrated', 0):.1f} / {v.get('disconnected', 0):.1f} / {v.get('integrated_nze', 0):.1f}"


A1 = {
    "BN": ("无 LNG / H₂ 码头；气产上限 110 TWh/a（用 17 / 17 / 110）；煤 1 节点；区域外 CO₂ 0", f"气产可变成本 0.28 / 0.46 / 1.50 bn；差额 +0.18（不互联自发电）", "UNSD 2019 气产 110 TWh（注册表 gas_production_cap_2050_BN）", "合理", 0.2),
    "ID": (f"LNG 5 节点上限 422 TWh，用 {use('LNG import','ID')}（NZE 99.7 %）；H₂ 进口 {use('H2 import','ID')}；煤 {use('coal','ID')} TWh；区域外 CO₂ 0", "LNG 10.6 / 10.6 / 5.8 bn；煤 0.53 / 0.97 / 0.25；油池购 17.8 / 17.8 / 6.0；差额 +0.4（煤 +50 TWh）", "GEM LNG 码头 11.75 mtpa（注册表）；IEA WEO 2025 表 2.3 价格", "合理", 0.4),
    "KH": (f"LNG 1 拟建节点上限 14.67 TWh **三情景绑定**；H₂ 进口 {use('H2 import','KH')}；无气产；煤 2 节点", "LNG 0.40 bn 不变；H₂ 0.06 / 0.03 / 0；差额 ≈ 0", "GEM 拟建 1.1 mtpa（注册表 lng_candidate）", "待核实（上限小且绑定，KH 终端气 23 TWh 其余靠 Sabatier 5.7 TWh）", 0.3),
    "LA": ("无码头、无气产；终端气 9.9 TWh 不互联时全部由 Sabatier 合成；煤 2.6 TWh；区域外 CO₂ 0（有过境外送链路，未用）", "可变成本 0.24 / 0.26 / 0.21；差额 +0.02", "—", "合理", 0.1),
    "MM": ("无码头；气产上限 185 TWh（用 6.8 / 6.8 / 185，NZE 出口 175 TWh 给 TH）；煤 2 节点", "气产可变成本 5.0 / 0.18 / 2.5 bn；差额 −4.8（不互联时无出口市场）", "UNSD 2019 气产 185 TWh；GEM 气田份额（注册表）", "合理（出口依赖互联，属真实差异）", 4.8),
    "MY": (f"LNG 1 节点上限 243.3 TWh **三情景绑定**；气产上限 850 TWh 三情景用满（NZE 出口 515）；H₂ 进口 ≈ 0；煤 {use('coal','MY')} TWh", "LNG 6.59 bn 不变；气产 9.8 / 23.0 / 11.6（不互联自用 850 TWh 于 CCGT CC 590 TWh）；差额 +13.2（气产）", "GEM LNG 7.3 mtpa 存量（3 单元缺容量 DATA_PENDING）", "待核实（码头上限绑定；F2）", 2.0),
    "PH": (f"LNG 2 节点上限 490 TWh，用 {use('LNG import','PH')}；气产 43 TWh 上限；H₂ {use('H2 import','PH')}；煤 {use('coal','PH')}", "LNG 1.15 / 0.49 / 4.38；差额 −0.67", "GEM 14.7 mtpa 存量 + 9.5 拟建", "合理", 0.7),
    "SG": (f"LNG 1 节点上限 366.7 TWh，一体化 / NZE 绑定（366.4 / 366.7），不互联 310；无气产；SG 再出口气 55 TWh 给 MY（一体化）", "LNG 9.92 / 8.40 / 5.01；差额 −1.52；气管道再出口收入 −1.8 → 0", "GEM 11 mtpa + 5 拟建", "待核实（码头上限绑定；SG 作 LNG 枢纽依赖管道）", 1.5),
    "TH": (f"LNG 1 节点上限 633 TWh（NZE 绑定；用 {use('LNG import','TH')}）；气产 367 TWh 上限；H₂ 进口 {use('H2 import','TH')}；NZE 再出口气 686 TWh", "LNG 11.9 / 7.0 / 8.7；气产 9.9 / 0.67 / 5.0；差额 −14.2（气产 −9.3、LNG −4.9）", "GEM 19 mtpa + 10.8 拟建", "待核实（TH 作区域气枢纽，依赖码头上限与管道）", 14.2),
    "TL": ("无码头；气产上限 61.3 TWh（UNSD 2019 Bayu-Undan 全部出口）：不互联用 0.5，一体化 / NZE 用满并出口 61.5 TWh", "气产可变成本 1.66 / 0.01 / 0.84；管道出口收入 −1.74 / 0 / −1.23；差额净 +0.1", "UNSD 2019（Bayu-Undan 2023 年已枯竭、Greater Sunrise 未开发：2050 产量 DATA_PENDING）", "待核实（2050 气产上限沿用 2019 产量）", 1.7),
    "VN": (f"LNG 5 节点上限 278.67 TWh **三情景绑定**；H₂ 进口 {use('H2 import','VN')} TWh（不互联 219.8 TWh → Sabatier 35 GW 制甲烷 224 TWh）；煤 {use('coal','VN')}；非化石油品池购 40 TWh（不互联）；区域外 CO₂ 0", "H₂ 0.54 / 23.24 / 0；LNG 7.54 不变；Sabatier + 电解投资 0 / 6.4 / 0；非化石油品 0 / 6.0 / 0；差额 +22.7（氢）+6.0（油品）+6.4（设备）", "GEM 存量 4 mtpa + 拟建 25.86 mtpa（6 单元缺容量）；氢进口价 105.75 EUR/MWh（Neumann 2025 × 1.2）", "**待核实**（F2：码头上限把 VN 推向 106 EUR/MWh 的进口氢）", 20.0),
    "ASEAN_BUNKER": ("甲醇 486 TWh、非化石油品 240 TWh 由区域池供应；区域外 FT / 甲醇进口 ≈ 0（150 / 145 EUR/MWh 高于区域合成成本）", "甲醇 55.8 / 54.5 / 48.8；油品 21.9 / 22.0 / 17.7；差额 −1.2", "Neumann 2025 进口价（注册表）", "合理", 1.2),
    "ASEAN_POOL": ("原油进口 1,397 / 1,331 / 1,414 TWh（35.3 EUR/MWh）；FT 进口 0.01 / 0.08 / 0 TWh；氨 / 甲醇进口 0", "原油 49.3 / 47.0 / 16.4 bn 全部转售各国；池盈余 ≈ 0", "WEO 2025 STEPS / NZE 2050 原油价", "合理", 0.0),
}
for o, (p, c, e, v, m) in A1.items():
    cell(o, ASPECTS[0], p, c, e, v, m)

# ---- aspect 2: corridors and flows
NI = {r["country"]: r for r in S["aspect2_net_imports_integrated"]}
CB = {r["country"]: r for r in S["aspect2_candidates_by_country"]}


def ni(c):
    r = NI[c]
    return f"一体化净进口 {r['net_import_twh']:.1f} TWh = 固定电力负荷 {r['fixed_elec_load_twh']:.0f} TWh 的 {r['net_import_pct_of_load']:.0f} %；候选电力通道 {CB[c]['lines']} 条（{CB[c]['pairs']}），存量 {CB[c]['stock_mw']:,.0f} MW、扩建上限 {CB[c]['max_mw']:,.0f} MW"


A2 = {
    "BN": (ni("BN") + "；BN–MY 建 0.98 GW，利用率 43 %", f"网络贸易 +0.24 → 0（差额 {ch('BN','network_trade_AC'):+.2f}）", "APG 无 BN–MY 项目（S4E-1 邻接补齐）", "合理", 0.2),
    "ID": (ni("ID") + "；ID–SG 直流只建 0.2 GW（SG 几乎不进口电）；气管道 MY→ID 121 TWh，CO₂ 管道 SG→ID 83 Mt", f"交流 {ch('ID','network_trade_AC'):+.2f}、直流 {ch('ID','network_trade_DC'):+.2f}、气管道 {ch('ID','network_trade_gas pipeline'):+.2f}（一体化付 5.4）、CO₂ 管道 {ch('ID','network_trade_CO2 pipeline'):+.2f}（一体化收 2.5）", "APG #4 2,130、#6 777、#16 3,400 MW（AIMS III 2040）", "合理（ID 近自给，差额小是真实的）", 2.8),
    "KH": (ni("KH") + "；KH–VN 建 51.8 GW（利用率 56 %）、KH–TH 22.9 GW；出口电来自 KH 光伏 252–359 GW（光伏上限 359 GW 一体化用满）", f"交流收入 {tot('KH','integrated'):.2f} 总成本中 −8.9；差额 {ch('KH','network_trade_AC'):+.2f}；CO₂ 管道付 1.0", "APG #12 VN–KH 1,353 MW、#14 TH–KH 1,315、#13 LA–KH 625（AIMS III）", "待核实（F3：52 GW vs 规划 1.35 GW）", 8.1),
    "LA": (ni("LA") + "；LA 为过境国：TH→LA 294 TWh、LA→VN 503 TWh；LA–VN 建 112 GW（9 条 × 上限 20 GW 之内）、LA–TH 78.8 GW；LA 自身光伏 112–119 GW（上限绑定）、水电 28 TWh", f"交流收入 −6.3 → 0（差额 {ch('LA','network_trade_AC'):+.2f}）；拥塞租 −2.7 → 0；设施分摊 2.4 → 0", "APG #10 LA–VN 625 MW、#9 TH–LA 955、#17 LA–MM 630", "待核实（F3：112 GW vs 规划 0.6 GW；过境模型无损耗以外的约束）", 4.8),
    "MM": (ni("MM") + "；MM–TH 建 38.5 GW（利用率 36 %）；气管道 MM→TH 176 TWh（存量 13.8 GW + 扩建至 50.5 GW）；氢管道 MM→LA 17 TWh；出口电来自 MM 光伏 565 GW（一体化）", f"交流 {ch('MM','network_trade_AC'):+.2f}、气管道 {ch('MM','network_trade_gas pipeline'):+.2f}、氢管道 {ch('MM','network_trade_H2 pipeline'):+.2f}（一体化合计收入 10.1）", "APG #11 TH–MM 1,262 MW；GEM Yadana / Yetagun / Zawtika 管道（注册表 gas_pipeline）", "待核实（F3）", 9.7),
    "MY": (ni("MY") + "；进口来源 TH 102 TWh（MY–TH 交流建至 20.9 GW，含单条 20 GW 上限 1 条）、PH 46 TWh（MY–PH 直流 12.1 GW）、ID 18 TWh；气管道进口 350 TWh（TH→MY 405 TWh 含过境）", f"交流 {ch('MY','network_trade_AC'):+.2f}、直流 {ch('MY','network_trade_DC'):+.2f}、气管道 {ch('MY','network_trade_gas pipeline'):+.2f}（一体化付 22.8）", "APG #2 TH–MY 1,043、#7 PH–Sabah 500、#1 MY–SG 1,050、#4 2,130 MW", "待核实（F3）", 22.8),
    "PH": (ni("PH") + "；唯一候选 MY–PH 直流（852 km，上限 20 GW，建 12.1 GW，利用率 43 %）；PH 为出口方（光伏 299 GW 上限 97–100 % 用满）", f"直流收入 −1.35 → 0（差额 {ch('PH','network_trade_DC'):+.2f}）", "APG #7 PH–Sabah 500 MW；无 PH–ID / PH–VN 项目", "合理（单走廊属 APG 范围；差额 0.01 为出口收入与自建成本相抵）", 1.3),
    "SG": (ni("SG") + "；ID–SG 直流 0.2 GW、MY–SG 交流 1.06 GW；SG 再出口气 55 TWh 给 MY；CO₂ 管道 SG→ID 83 Mt（一体化）/ 船运 84 Mt（不互联）", f"交流 {ch('SG','network_trade_AC'):+.2f}、气管道 {ch('SG','network_trade_gas pipeline'):+.2f}、CO₂ 管道 {ch('SG','network_trade_CO2 pipeline'):+.2f}（一体化付 2.6）", "APG #16 SG–Sumatra 3,400 MW（AIMS III）；SG–ID / SG–MY CO₂ 跨境 MoU（EXT_TECH_POLICY）", "合理（SG 进口电很少：本地 CCGT CC + CO₂ 外送更便宜）", 2.6),
    "TH": (ni("TH") + "；TH 出口电至 LA（294）、MY（102）、KH；气出口 405（MY）+ 207（LA）+ 59（KH）TWh；CO₂ 进口 150 Mt（LA 116、KH 25、MM 8）；出口电来自 TH 光伏 1,099–1,108 GW（上限 99–100 %）", f"交流 {ch('TH','network_trade_AC'):+.2f}、气管道 {ch('TH','network_trade_gas pipeline'):+.2f}、CO₂ 管道 {ch('TH','network_trade_CO2 pipeline'):+.2f}、氢管道 {ch('TH','network_trade_H2 pipeline'):+.2f}（一体化合计收入 32.1）", "APG #9 / #14 / #11 / #2 合计约 4.6 GW（AIMS III）", "待核实（F3）", 32.7),
    "TL": (ni("TL") + "；ID–TL 交流建 0.33 GW；气管道 TL→ID 61 TWh、氢管道 TL→ID 8 TWh（一体化）", f"气管道 {ch('TL','network_trade_gas pipeline'):+.2f}、氢管道 {ch('TL','network_trade_H2 pipeline'):+.2f}", "APG 无 TL 项目（S4E-1 邻接补齐）", "合理（差额由气出口决定，见方面 1）", 2.2),
    "VN": (ni("VN") + "；LA–VN 112.1 GW（9 条，利用率 51 %）、KH–VN 51.8 GW（6 条，56 %）；电源：KH 光伏、TH 光伏经 LA 过境；气管道进口 266 TWh（LA→VN 201 + KH→VN 47）；CO₂ 管道外送 107 Mt（VN→LA→TH）；氢管道进口 32 TWh", f"交流 {ch('VN','network_trade_AC'):+.2f}（一体化付 29.0 = 757 TWh × 38 EUR/MWh）、气管道 {ch('VN','network_trade_gas pipeline'):+.2f}、CO₂ 管道 {ch('VN','network_trade_CO2 pipeline'):+.2f}、氢管道 {ch('VN','network_trade_H2 pipeline'):+.2f}；拥塞租 {ch('VN','xb_share_congestion_rent'):+.2f}、设施分摊 {ch('VN','xb_share_infrastructure_cost'):+.2f}", "APG #10 LA–VN 625 MW、#12 VN–KH 1,353 MW（AIMS III 2040）", "**待核实**（F3：164 GW 新建 vs 规划 2 GW）", 42.7),
    "ASEAN_BUNKER": ("无通道；海运燃料由区域池供应，与互联无关", "—", "—", "合理", 0.0),
    "ASEAN_POOL": ("无通道；池为海运贸易（决定 18 / 44），两情景相同", "池盈余 ≈ 0", "—", "合理", 0.0),
}
for o, (p, c, e, v, m) in A2.items():
    cell(o, ASPECTS[1], p, c, e, v, m)

# ---- aspect 3: technology availability
CAPS = S["aspect3_candidate_caps_gw"]
PN = S["aspect3_pnom_opt_gw"]


def cap(car, c):
    v = CAPS.get(car, {}).get(c)
    return "无" if v is None or (isinstance(v, float) and pd.isna(v) and car not in ("nuclear", "nuclear SMR")) else ("∞" if (isinstance(v, float) and pd.isna(v)) else f"{v:.1f}")


def built(car, c):
    v = PN.get(f"{car}|{c}", {})
    return f"{v.get('integrated', 0):.1f} / {v.get('disconnected', 0):.1f} / {v.get('integrated_nze', 0):.1f}"


def sol(c):
    return f"{vre.loc[('solar', c), 'integrated']:.0f} / {vre.loc[('solar', c), 'disconnected']:.0f} / {vre.loc[('solar', c), 'integrated_nze']:.0f}"


A3 = {
    "BN": (f"候选上限 GW：光伏 {cap('solar','BN')}（建 {sol('BN')}，绑定）、屋顶 1.5、陆上风 10.5（CF 0.04）、海上风 9.5（CF 0.08–0.18）；水电 / 地热无；核电 + SMR 无上限（未建）", "差额中技术项：CCGT CC +0.09", "GEM 2026-09 无水电；核电无规划", "合理", 0.1),
    "ID": (f"地热 22.4（建 21.2 三情景）、水电 80.3 + 径流 6.2、PHS 2.4、光伏 {cap('solar','ID')}（建 {sol('ID')}，**绑定**；ESDM 技术潜力 3,294 GW）、屋顶 356、陆上风 3,950（ESDM 155 GW，模型 25×）、海上风 2,786；SMR 不互联 0.85 GW；核电规划 10 GW", "差额：陆上风 +0.77、SMR +0.62、CCGT CC −1.6", "ESDM 2023 / Badan Geologi 2024（注册表）；核电 RUPTL 2025 首堆 2032–34", "待核实（光伏上限 0.26×、陆上风 25× 官方；对 ID 差额影响小）", 1.0),
    "KH": (f"水电 4.2、光伏 {cap('solar','KH')}（建 {sol('KH')}）、陆上风 320、海上风 47；SMR / 核电无上限（未建）", "差额：光伏 −3.3（不互联少建 107 GW）、DAC +1.1、电解 +1.0", "GEM 管线 4.17 GW 水电；PDP 2022–2040", "合理（KH 光伏为一体化出口资源，待核实见 F3）", 3.3),
    "LA": (f"水电 5.1 + 径流 6.5（AEO8 26 GW − 存量 14.4）、PHS 0.1、光伏 {cap('solar','LA')}（建 {sol('LA')}，94–100 %）、陆上风 529；无海上风", "差额：电解 +2.1、甲醇合成 +0.9、DAC +0.8", "AEO8 p.75（26 GW，C 级）/ MEM 18 GW 敏感性", "合理", 2.1),
    "MM": (f"水电 38.1（ADB 46 − 存量）、径流 3.9、光伏 {cap('solar','MM')}（建 {sol('MM')}，唯一有大余量的国家）、陆上风 1,621、海上风 267", "差额：光伏 −10.8（一体化多建 352 GW 供出口 + 制甲醇）、电解 −5.3、甲醇合成 −2.5、DAC −2.2", "ADB 2016 水电；无核电规划", "合理（MM 作区域合成燃料与电力出口基地依赖光伏余量与 F3）", 10.8),
    "MY": (f"水库水电 6.0、径流 2.4、地热 0.23、光伏 {cap('solar','MY')}（建 {sol('MY')}，**绑定**；MyRER 269 GW）、屋顶 83（MyRER 42）、陆上风 742、海上风 374；**SMR 不互联建 7.27 GW**（MY 无核电政策）", "差额：SMR +5.3 + 运行 +1.3、CCGT CC +1.6、生物质 CC +0.7", "SEDA MyRER 2021；核电政策见 EXT_TECH_POLICY", "待核实（光伏上限 0.29×；SMR 与政策不符）", 6.6),
    "PH": (f"水电 11.8、PHS 8.0、地热 3.1、光伏 {cap('solar','PH')}（建 {sol('PH')}；CREZ 58 GW，模型 5.1×）、陆上风 550（CREZ 94）、海上风 280（世行 178）；核电规划 4.8 GW", "差额：电解 +0.57、电制生物燃料 +0.58、光伏 −0.28", "DOE CREZ 2024；DOE / 世行海上风电路线图 2022；PEP 2023–2050 核电", "待核实（潜力高于官方 3–6×，PH 出口方地位依赖此）", 1.0),
    "SG": (f"光伏 0.44 + 屋顶 5.3、海上风 1.3；水电 / 地热无；**SMR 允许无上限**（未建）；大型核电不允许", "差额：CCGT CC +0.07", "EMA 2024 核电可行性研究（EXT_TECH_POLICY）", "合理（SMR 未建；政策 2050 不确定）", 0.1),
    "TH": (f"PHS 2.5、水电 / 地热无、光伏 {cap('solar','TH')}（建 {sol('TH')}，99–100 % **绑定**）、陆上风 580（alpha 1.29 校准）、海上风 324；核电规划 0.6 GW SMR", "差额：电解 +4.7、DAC +2.1、甲醇合成 +1.4、封存 −1.4", "GEM 管线；PDP2024 草案", "待核实（光伏上限决定 TH 出口能力）", 4.7),
    "TL": (f"光伏 9.6（建 {sol('TL')}，绑定）、陆上风 37、海上风 1.9；核电 + SMR 无上限（未建）", "差额：DAC +0.09、甲醇合成 +0.07", "无官方潜力（DATA_PENDING）", "合理", 0.1),
    "VN": (f"水电 16.0 + 径流 6.1、PHS 1.5、地热 0.04、光伏 {cap('solar','VN')}（建 {sol('VN')}，**三情景绑定**；PDP8 技术潜力 963 GW）、屋顶 122（PDP8 48）、陆上风 577（PDP8 221）、海上风 636（PDP8 600）；不互联建：海上风 112.7 GW（类上限，CF 0.44–0.58）、SMR 23.0 GW（规划 14.4）、陆上风 26.4、径流 6.1", "差额：海上风 +26.8 + 2.2、SMR +16.7 + 3.8、电解 +4.4、屋顶 +2.7、陆上风 +2.2、径流 +2.0、Sabatier +1.9", "PDP8 决定 500 / 768（注册表 A 级）；核电 2035 4–6.4 GW；海上风电 CF 见 EXT_COST", "**待核实**（F1 光伏上限 0.43×；F8 SMR > 规划；F9 海上 CF）", 35.0),
    "ASEAN_BUNKER": ("不适用", "—", "—", "—", 0.0),
    "ASEAN_POOL": ("池内：甲醇 / 氨储罐（无上限，投资 1.0 bn）；区域内合成设施归各国", "—", "—", "合理", 0.0),
}
for o, (p, c, e, v, m) in A3.items():
    cell(o, ASPECTS[2], p, c, e, v, m)

# ---- aspect 4: demand (model loads; external from EXT_DEMAND_BENCHMARKS)
DEM = {  # fixed loads TWh (integrated build network): electricity base, industry elec, EV, agri; TFEC 2050 TWh (x2019); H2 TWh; biomass; gas final; oil final
    "BN": (3.2, 2.2, 2.0, 0.1, 27.5, 1.40, 0.0, 0.1, 1.1, 0.3), "ID": (301.1, 1801.0, 168.9, 3.2, 4727.1, 2.74, 13.6, 577.4, 201.9, 464.6),
    "KH": (17.4, 12.8, 24.8, 3.1, 200.7, 3.32, 0.0, 10.7, 23.2, 30.1), "LA": (4.9, 7.0, 6.3, 0.2, 63.6, 1.85, 0.0, 5.0, 9.9, 1.2),
    "MM": (14.5, 80.7, 11.2, 9.2, 307.0, 1.48, 0.3, 28.1, 7.8, 29.9), "MY": (139.7, 425.9, 171.2, 6.1, 1917.3, 2.44, 10.2, 127.4, 35.4, 63.2),
    "PH": (103.7, 102.2, 91.4, 1.8, 899.7, 2.19, 3.1, 75.0, 62.1, 110.3), "SG": (41.2, 100.8, 10.5, 0.0, 1044.7, 1.23, 0.2, 0.0, 31.6, 1.5),
    "TH": (208.6, 472.7, 241.6, 23.9, 3219.2, 2.77, 6.2, 285.0, 111.8, 138.4), "TL": (0.9, 0.0, 0.9, 0.0, 4.8, 2.43, 0.0, 0.0, 0.0, 0.0),
    "VN": (197.2, 963.7, 82.1, 10.2, 2572.5, 3.82, 40.3, 123.3, 584.2, 83.7),
}
A4V = {"BN": "合理", "ID": "待核实", "KH": "待核实（乘数 4.7）", "LA": "合理", "MM": "合理", "MY": "合理", "PH": "合理", "SG": "合理", "TH": "待核实", "TL": "合理", "VN": "**待核实**（F4：工业 1,823 TWh、水泥 581 Mt、钢 80 Mt）"}
A4M = {"BN": 0.0, "ID": 0.0, "KH": 0.5, "LA": 0.0, "MM": 0.0, "MY": 0.5, "PH": 0.0, "SG": 0.0, "TH": 1.0, "TL": 0.0, "VN": 10.0}
for c, (eb, ie, ev, ag, tf, mul, h2, bm, gs, ol) in DEM.items():
    phys = f"固定电力负荷 {eb+ie+ev+ag:,.0f} TWh（基础 {eb}、工业 {ie}、EV {ev}、农业 {ag}）；终端能耗 2050 {tf:,.0f} TWh = 2019 × {mul}；氢 {h2}、固定生物质 {bm}、终端气 {gs}、终端油 {ol} TWh" + ("；第 104 项修正后 VN 基础负荷 197.2 TWh（S4J）" if c == "VN" else "")
    cost = "需求是三情景共同输入，不直接产生差额；决定该国全部成本规模" + (f"（VN 工业电力 964 TWh 由 1,043 TWh 工业煤经 pypsa_eur_2050 路线转换；溢出甲烷 233 TWh）" if c == "VN" else "")
    cell(c, ASPECTS[3], phys, cost, "外部 2050 基准见 evidence/EXT_DEMAND_BENCHMARKS.md（偏差 > ±25 % 处在报告 §4.4 标出）", A4V[c], A4M[c])
cell("ASEAN_BUNKER", ASPECTS[3], "国际航空油品 240 TWh（非化石）、国际航运甲醇 486 TWh（= 油当量 × 0.40 / 0.46）；SG 639 TWh 燃料舱在池内不计入 SG", "差额 −1.2（池内甲醇价差）", "D1 bunker 表（UNSD 2019 × PyPSA-Eur 份额）；IMO / IEA 2050 航运燃料展望 DATA_PENDING", "合理", 1.2)
cell("ASEAN_POOL", ASPECTS[3], "不适用（池无需求）", "—", "—", "—", 0.0)

# ---- aspect 5: CO2 (from ASPECT5_CO2.csv)
A5V = {"BN": ("合理", 0.1), "ID": ("合理（用 62 %）", 2.8), "KH": ("合理（上限 1.7 Mt 绑定，靠船运 / DAC）", 1.0), "LA": ("待核实（潜力未评估 SOURCE_ZERO）", 0.4), "MM": ("待核实（潜力未评估）", 0.4),
       "MY": ("合理（用 8 %）", 0.8), "PH": ("合理", 0.0), "SG": ("合理（无潜力，外送 83–84 Mt）", 3.5), "TH": ("待核实（一体化上限绑定，作区域封存地）", 3.3), "TL": ("合理", 0.0), "VN": ("待核实（上限 236 Mt 三情景绑定 + DAC 124–144 Mt）", 2.0)}
for c in COUNTRIES:
    r = co2.loc[c]
    phys = (f"年注入上限 {r.annual_cap_Mt:.1f} Mt（潜力 / 50 年；封存 30 EUR/t）；封存 {r.integrated_seq_Mt:.1f} / {r.disconnected_seq_Mt:.1f} / {r.integrated_nze_seq_Mt:.1f} Mt；"
            f"船运出 {r.integrated_ship_out_Mt:.1f} / {r.disconnected_ship_out_Mt:.1f} / {r.integrated_nze_ship_out_Mt:.1f}、船运入 {r.integrated_ship_in_Mt:.1f} / {r.disconnected_ship_in_Mt:.1f} / {r.integrated_nze_ship_in_Mt:.1f}；"
            f"DAC {r.integrated_dac_Mt:.1f} / {r.disconnected_dac_Mt:.1f} / {r.integrated_nze_dac_Mt:.1f} Mt；区域外封存 0")
    cost = f"CO₂ 封存服务 {ch(c,'co2_storage_service'):+.2f}、船运运费 {ch(c,'co2_ship_freight'):+.2f}、CO₂ 管道贸易 {ch(c,'network_trade_CO2 pipeline'):+.2f}、DAC 投资 {A['entities'][c]['channels_bn'].get('capex_new',{}).get('dis_minus_int',0):+.2f}（含其他投资）"
    extc = "ERIA 2024 / IEA 2021 / OGCI 2025 潜力（注册表 co2_storage_potential_*）；封存与船运成本基准见 EXT_TECH_POLICY / EXT_COST"
    cell(c, ASPECTS[4], phys, cost, extc, A5V[c][0], A5V[c][1])
cell("ASEAN_BUNKER", ASPECTS[4], "燃料舱 co2 bunkers 账户：化石航空油品 0，非化石油品零排放（origin_neutral）", "0", "—", "合理", 0.0)
cell("ASEAN_POOL", ASPECTS[4], "不适用", "—", "—", "—", 0.0)

# ---- aspect 6: biomass (from ASPECT6_BIOMASS.csv)
A6V = {"BN": ("待核实（固定需求 = 0.98 × 池，溢出转甲烷 0.5 TWh）", 0.0), "ID": ("合理", 0.0), "KH": ("合理", 0.0), "LA": ("合理", 0.0), "MM": ("合理", 0.0), "MY": ("合理", 0.0), "PH": ("合理", 0.0),
       "SG": ("待核实（池 0.03 TWh，溢出 18.7 TWh 转甲烷）", 0.3), "TH": ("合理（89 %，未溢出）", 0.5), "TL": ("合理", 0.0), "VN": ("**待核实**（F5：需求 340 TWh > 池 125.8，溢出 233 TWh 转甲烷）", 10.0)}
for c in COUNTRIES:
    r = bio.loc[c]
    phys = (f"池 {int(r.pools)} 个、潜力 {r.e_nom_twh:.1f} TWh（原料成本 {r.mc_min:.1f}–{r.mc_max:.1f} EUR/MWh）；固定生物质终端需求 {r.fixed_biomass_final_twh:.1f} TWh = 潜力的 {r.fixed_over_pool_pct:.0f} %；"
            f"池全部用完（三情景提取 {r.int_withdraw_twh:.1f} TWh）；影子价格（母线年均）一体化 {r.int_solid_biomass_price_mean:.1f} / 不互联 {r.dis_solid_biomass_price_mean:.1f} EUR/MWh")
    cost = f"生物质可变成本差额 {A['entities'][c]['channels_bn'].get('variable_cost',{}).get('dis_minus_int',0):+.2f}（含全部可变成本）；稀缺租 = 影子价 − 原料成本"
    extc = "BIOMASS_POTENTIAL_2050.csv（FAOSTAT × IRENA RPR，B / C 级）；IRENA 2022 可收集残余物对照 BIOMASS_CROSSCHECK_IRENA.csv（VN 1.03×、TH 1.24×、ID 1.43×、MY 4.9×、MM 12×）"
    cell(c, ASPECTS[5], phys, cost, extc, A6V[c][0], A6V[c][1])
cell("ASEAN_BUNKER", ASPECTS[5], "不适用（生物质不跨境，决定 36）", "—", "—", "—", 0.0)
cell("ASEAN_POOL", ASPECTS[5], "生物质→甲醇（biomass-to-methanol）进池 ≈ 0", "0", "—", "合理", 0.0)

# ---- aspect 7: cost parameters
WACC = {"ID": "IEA 2024 名义税后：光伏 8.5–11 %、燃气 9–10 %、储能 9–11 %", "VN": "IEA 2024：光伏 8.5–10 %、燃气 10–10.5 %、海上风 10.5–12 %（2023）", "PH": "IEA 2024：光伏 7–8.5 %、燃气 8–9 %", "MY": "IEA 2024：光伏 6–7 %", "TH": "IEA 2024：光伏 6–8 %、燃气 9–11.5 %"}
OFF = {r["country"]: r for r in S["aspect3_offwind"] if r["carrier"] == "offwind-dc"}
ALPHA = {"BN": 1.046, "ID": 1.046, "KH": 1.046, "LA": 1.046, "MM": 1.046, "MY": 1.046, "PH": 0.910, "SG": 1.046, "TH": 1.294, "TL": 1.046, "VN": 0.995}
for c in COUNTRIES:
    o = OFF.get(c)
    phys = (f"折现率统一 0.07（实际）；技术成本统一（technology-data v0.15.0 2050 EUR2020；SMR AEO8 D.15 8,421 EUR/kW）；燃料价统一（STEPS 2050）；国别项只有：海上风电并网距离（offwind-dc 年化 {o['cc_mean']:,.0f} EUR/MW/a，区间 {o['cc_min']:,.0f}–{o['cc_max']:,.0f}）"
            if o else "折现率统一 0.07；技术与燃料成本统一；无海上风电候选") + f"；陆上风校准 alpha {ALPHA[c]}（PH / TH / VN 为 B 级实测，其余 C 级均值）；台风溢价关闭；cost_scaling 全 1.0"
    cost = "无直接差额项；WACC 国别化会按资本密集度改变两情景成本（见 F7）"
    extc = WACC.get(c, "IEA 资本成本观测站无该国数据（注册表 wacc_country_model_* DATA_PENDING）") + "；技术成本基准见 EXT_COST_BENCHMARKS.md"
    verdict = "待核实（统一 WACC 对高资本成本国相对有利）" if c in ("VN", "ID", "PH", "KH", "LA", "MM") else ("待核实（TH alpha 1.29 对 TH 有利）" if c == "TH" else "合理")
    mag = {"VN": 10.0, "ID": 2.0, "PH": 1.0, "TH": 1.0}.get(c, 0.2)
    cell(c, ASPECTS[6], phys, cost, extc, verdict, mag)
cell("ASEAN_BUNKER", ASPECTS[6], "池价格 = 节点对偶；燃料舱不承担投资", "—", "—", "合理", 0.0)
cell("ASEAN_POOL", ASPECTS[6], "进口价：原油 35.3、FT 150.1、甲醇 145.2、氨 116.8 EUR/MWh；储罐 technology-data", "—", "Neumann 2025 × 1.2（B 级）；WEO 2025", "合理", 0.0)

# ---- aspect 8: settlement rules (from ASPECT8_B6_BY_RULE.csv)
for c in COUNTRIES:
    r = rule.loc[c]
    vals = " / ".join(f"{r[k]:.2f}" for k in ["(i) 现行", "(ii) 拥塞租归进口方", "(iii) 拥塞租归出口方", "(iv) 只计境内物理成本", "(v) 按境内长度分摊"])
    phys = f"差额（不互联 − 一体化，bn）在规则 (i)/(ii)/(iii)/(iv)/(v) 下：{vals}；份额 (i) {r['share_(i)_pct']:.1f} %、(iv) {r['share_(iv)_pct']:.1f} %"
    cost = f"规则 (ii)–(iii) 区间宽度 {abs(r['(ii) 拥塞租归进口方']-r['(iii) 拥塞租归出口方']):.2f} bn；(iv) 与 (i) 之差 {r['(iv) 只计境内物理成本']-r['(i) 现行']:+.2f} bn（= 贸易结算与池结算的净额）"
    verdict = "合理（规则依赖小）" if abs(r['(ii) 拥塞租归进口方'] - r['(iii) 拥塞租归出口方']) < max(0.1 * abs(r['(i) 现行']), 0.3) else "合理（拥塞租归属改变 ≥ 10 %，报告中给区间）"
    cell(c, ASPECTS[7], phys, cost, "总 B6 与规则无关（账本恒等式 B16 相对误差 ≤ 7e-9）", verdict, abs(r['(ii) 拥塞租归进口方'] - r['(iii) 拥塞租归出口方']))
cell("ASEAN_BUNKER", ASPECTS[7], "燃料舱按池对偶结算；与拥塞租规则无关；差额 −1.22 bn 在 (i)–(v) 相同", "—", "—", "合理", 0.0)
cell("ASEAN_POOL", ASPECTS[7], "池盈余 = 账本恒等式差项（≤ 0.4 M EUR）", "—", "—", "合理", 0.0)


def main():
    rows = []
    for o in OBJECTS:
        for a in ASPECTS:
            c = C[(o, a)]
            rows.append({"object": o, "aspect": a, "物理量": c["phys"], "成本影响_一体化_不互联_NZE_差额": c["cost"], "外部对照": c["ext"], "判定": c["verdict"], "影响量级_bn": c["mag"]})
    with open(OUT / "COUNTRY_AUDIT_MATRIX.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    md = ["# S4P 核查矩阵：13 个对象 × 8 个方面（只读；数字为 VERIFIED，量级为 INFERENCE）", "",
          "每格五项：物理量；成本影响（一体化 / 不互联 / NZE 与差额，bn EUR，正 = 该国支出增加）；外部对照；判定（合理 / 待核实 / 错误）；对 B6 与该国差额的影响量级（bn，绝对值估计）。",
          f"B6 = {A['b6_detail_bn']:.3f} bn；分国差额：" + "，".join(f"{e} {d(e):+.3f}" for e in OBJECTS) + "。", ""]
    for o in OBJECTS:
        md.append(f"## {o}（差额 不互联−一体化 {d(o):+.3f} bn；NZE−一体化 {A['entities'][o]['nze_minus_int_bn']:+.3f} bn）")
        md.append("")
        md.append("| 方面 | 物理量 | 成本影响 | 外部对照 | 判定 | 量级 bn |")
        md.append("|---|---|---|---|---|---|")
        for a in ASPECTS:
            c = C[(o, a)]
            md.append(f"| {a} | {c['phys']} | {c['cost']} | {c['ext']} | {c['verdict']} | {c['mag']:.1f} |")
        md.append("")
    (OUT / "COUNTRY_AUDIT_MATRIX.md").write_text("\n".join(md), encoding="utf-8")
    verdicts = pd.Series([C[(o, a)]["verdict"] for o in OBJECTS for a in ASPECTS])
    print("cells", len(rows), "待核实", int(verdicts.str.contains("待核实").sum()), "错误", int(verdicts.str.contains("错误").sum()), "歧义", int(verdicts.str.contains("歧义").sum()))


if __name__ == "__main__":
    main()
