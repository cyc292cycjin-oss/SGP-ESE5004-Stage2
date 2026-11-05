"""I2 section 5: all MISSING_DATA files of G0-G5, W12 and I1 merged, de-duplicated by data source (topic), ranked by the possible effect on T_v2,
the solid-biomass potential or B6, with the items found in I2. Writes MISSING_DATA_ALL.csv (topic level) and tables/I2_MISSING_DATA_ROWS.csv (every
source row with its topic).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i2_missing.py

Impact magnitudes come from the I2 sensitivity runs (tables/I2_SENSITIVITY_ALL.csv, SENSITIVITY_TOP10.csv) or the session reports; 'before W08'
= the W08 implementation or its acceptance numbers depend on it; 'after W08' = refines a number without changing the method.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i2_common as cm   # noqa: E402

FILES = ["G0/ID_MISSING_DATA.csv", "G1/MY_MISSING_DATA.csv", "G2/VN_MISSING_DATA.csv", "G3/TH_MISSING_DATA.csv", "G3/PH_MISSING_DATA.csv", "G3/SG_MISSING_DATA.csv",
         "G4/MM_MISSING_DATA.csv", "G4/KH_MISSING_DATA.csv", "G4/LA_MISSING_DATA.csv", "G4/BN_MISSING_DATA.csv", "G4/TL_MISSING_DATA.csv", "G5/MISSING_DATA.csv",
         "W12/MISSING_DATA.csv", "I1/MISSING_DATA.csv"]
# (topic, regex on item + purpose); first match wins
RULES = [
    ("T01", r"AEO8|AEDS"),
    ("T04", r"IRENA 2017|moisture"),
    ("T02", r"[Ee]nergy [Bb]alance|Energy Statistics|Neraca|balance table|energy consumption by sub-sector"),
    ("T10", r"DOEB|Thai coal|coal import quality"),
    ("T09", r"coal NCV|coal quality|CONVERSION_FACTOR|Coal quality|NCV|conversion factor"),
    ("T18", r"[Ss]ugar|OCSB|SRA |bagasse|cane"),
    ("T03", r"kernel shell|PKS|palm.oil mill|mill steam|palm"),
    ("T04", r"IRENA 2017|moisture"),
    ("T05", r"[Nn]ickel|RKEF|IMIP|IWIP|HPAL"),
    ("T06", r"[Cc]linker|252310|2523|CEMAP|TCMA"),
    ("T07", r"UNdata export|re-download|100000|100,000"),
    ("T08", r"UNSD (methodolog|note|questionnaire)|IRES|methodology note|reallocation|revision"),
    ("T10", r"DOEB|Thai coal|coal import quality"),
    ("T11", r"VINACOMIN|EVN"),
    ("T09", r"coal NCV|coal quality|CONVERSION_FACTOR|Coal quality|NCV"),
    ("T12", r"[Ee]thylene|[Cc]racker|LINE|Chandra|Olefin|PTT Global|Long Son|JG Summit|Pengerang|PIC|HVC"),
    ("T13", r"[Mm]ethanol|Kaltim|Labuan"),
    ("T14", r"EMA|[Rr]efinery gas|Jurong"),
    ("T15", r"Sabah|NEB|gas supply by|aluminium|aluminum|smelter output|Press Metal"),
    ("T16", r"[Pp]ulp|[Pp]aper|APKI|VPPA|Sun Paper|MPCI|mill"),
    ("T17", r"autoproducer|captive|Petron|SPP|VSPP|Tigyit|Myainggalay|own-use|IUPTLS"),
    ("T18", r"[Ss]ugar|OCSB|SRA|bagasse|cane"),
    ("T19", r"load curve|load profile|Ganz|holiday|time-of-use|TOU|maintenance|NREL|[Ww]eekend|Keppres|'holidays'|tariff"),
    ("T20", r"SKK Migas|gas balance|marketed"),
    ("T21", r"[Cc]opper|Sepon|[Pp]otash|USGS Minerals Yearbook"),
    ("T22", r"GSO|enterprise census|APEC EGEDA|Viet ?Nam.*(statistics|balance)|Vietnam Energy Statistics"),
    ("T23", r"Hengyi|BN cement|Brunei"),
    ("T02", r"energy balance|Energy Balance|Energy Statistics|HEESI|ESDM|DEDE|EPPO|MOEE|DOE|national energy|Neraca|DES|balance table|Statistics 20"),
    ("T24", r"glass|lime|[Cc]hemical|ammonia|[Ff]ertili[sz]er|plant data|production 20"),
]
TOPIC = {
    "T01": ("AEO8 各国 × 部门历史与预测数据（AEDS，AEO8 表背后的数据）", "锚构造（IId / IIa / IIb）与东盟部门合计对 C.3 的偏离；判断各国工业锚",
            "锚构造 IIb / IIa 相对 IId：东盟 `T_v2` +477 / +468 TWh（SENSITIVITY_TOP10 第 1、2）；东盟交通对 C.3 +26 %", "W08 之前", "用户（向 ACE 申请）"),
    "T02": ("各国国家能源平衡表 2019 / 2022（ID ESDM 与 HEESI、TH DEDE / EPPO、VN MOIT、PH DOE、MM MOEE、LA MEM、KH MME、BN DES、TL、SG EMA）",
            "第 210 项第 4 条：逐国核定平衡表的生物质覆盖范围（自用残渣是否在锚内）；家庭汽油、分行业结构、AEO8 基数折算热值",
            "平衡表都不含自用残渣：东盟 `T_v2` +41 TWh（TH +26.4、VN +8.9）；MM 家庭汽油 −1.2；ID 热值按 (i) −59 TWh", "W08 之前（ID、TH、VN、PH）；其余之后", "用户"),
    "T03": ("棕榈油厂蒸汽与电力平衡、棕榈仁壳（PKS）出口与厂内燃用（GAPKI、BPS、MPOB、ERIA）", "第 209 项 F4 与第 210 项第 4 条：潜力中扣除厂内自用的纤维与果壳",
            "PKS 厂内份额 0–100 %：东盟潜力 ±49 TWh（ID ±33、MY ±13）；纤维全部扣除已在主算（ID 149、MY 60 TWh）", "W08 之前", "用户"),
    "T04": ("IRENA 2017 残余物系数的含水率说明（0.2 t/t 甘蔗是否湿基）", "第 209 项 F3：蔗渣单一热值的读法（R2 主算、R1 对照）",
            "R1 代替 R2：东盟潜力 −29 TWh（TH −27）", "W08 之前", "审阅端（文献）"),
    "T05": ("印尼 RKEF 镍铁（11–14 % Ni NPI）与 HPAL 单耗文献；IMIP / IWIP 分产品产量与园区自备电", "镍单耗（第 208 项 Case 3）与镍空间分配（2023 年设施）",
            "NPI Case 4：ID“其他” −172 TWh；NIUPPER −418 TWh（`T_v2` 不变，守恒）；节点份额", "W08 之后（主算已定 Case 3）", "用户"),
    "T06": ("UN Comtrade 熟料与水泥贸易（HS 252310 / 2523）2019–2024：ID、VN、KH、LA、MM、PH、TH", "熟料量（EDGAR = USGS 水泥 × 0.786，非独立）与 2019 年窑燃料扣除",
            "KH 熟料下调时 `T_v2` 上升数 TWh（倍数 3.68）；VN 熟料出口影响 2019 年水泥扣除", "W08 之后", "用户"),
    "T07": ("UNdata 导出分批重下（柴油、燃料油 < 10 万行）", "原用于补截断；第 210 项第 1 条已改用 SDMX 当前库", "已由 SDMX 基年关闭（VN 柴油 +115.7 TWh 2019 已在基年中）", "不需要", "—"),
    "T08": ("UNSD 方法说明：ID 2019 硬煤折算系数改动、ID / VN 燃料木材 2018–2019 重分配、TH 自备电厂申报口径", "热值与燃料木材版本的依据",
            "ID 热值维持 v3 25.80：ID `T_v2` +103 TWh（G0）；ID 燃料木材 SDMX 2019 −59、2020–2021 年均 +43 TWh；VN 燃料木材导出版本 +32 TWh", "W08 之前（只需书面说明）", "用户（函询 UNSD）"),
    "T09": ("煤质 / 热值：HEESI 分用户煤热值、ESDM 煤质统计、MM 煤质", "第 207 项热值的证据（ID 20.29 的适用范围；MM 23.26 对 18.9）",
            "ID 热值 24.48 / 18.9：+78 / −26 TWh（G0，口径 I）；MM 18.9 −0.4", "W08 之后", "用户"),
    "T10": ("TH DOEB 进口煤按热值分级吨数 2019", "TH 父项 / 子项热值取舍", "子项 / IPCC +41.9、EPPO 26.37 +81.2 TWh（G3，口径 I）", "W08 之后", "用户"),
    "T11": ("VN VINACOMIN 煤质分级、EVN 2019 年报（煤电与耗煤）", "VN 热值 23.446 的实物核对", "21.695 −34.5、26.7 +64.1 TWh（G2，口径 I）", "W08 之后", "用户"),
    "T12": ("乙烯 / HVC 装置运行记录：Chandra Asri 与 LINE、PTTGC / MOC / Cracker No 5、JG Summit、新加坡裂解装置、龙山、PIC", "HVC 产量与利用率；新装置投产",
            "利用率 0.75 / 0.95：东盟 −9.3 / +6.9 TWh；新装置不进主算 −57 TWh", "W08 之后", "用户"),
    "T13": ("甲醇装置产量与燃料去向：Kaltim（ID）、Brunei Methanol（BN）、Labuan / Sarawak（MY）", "第 210 项第 7 条：甲醇按能源用途显式化；BN 能源用途在 UNSD 非能源用途",
            "BN 甲醇 2050 年 +2.9 TWh（BN `T_v2` 1.6 → 4.6）；W08 须同步扣 NEU 气", "W08 之前（BN、ID 的 NEU 拆分）", "用户"),
    "T14": ("EMA 新加坡能源统计（2019 平衡、工业分行）与炼厂气用途说明；裕廊岛蒸汽供应", "SG 化工行炼厂气超出供应 783 kt 的处理；SG“其他”拆分",
            "SG 炼厂气超出部分移出：SG `T_v2` −10.9 TWh", "W08 之后", "用户"),
    "T15": ("MY NEB 分地区分用户供气（沙巴）、原铝实际产量、水泥窑燃料构成、化工装置数据", "沙巴 16.94 TWh 工业用气归属；原铝活动量；MY“其他”空间分配",
            "沙巴工业用气转 NEU：MY `T_v2` −21.0 TWh；原铝 1,080 kt：MY“其他”占比 −2 个百分点", "W08 之后（主算已定暂留“其他”）", "用户"),
    "T16": ("纸浆造纸统计：APKI（ID）、VPPA（VN）、TH 协会、Sun Paper Laos（含 2021 年纸线）、MY 纸厂、PH 纸厂", "外购燃料与黑液；LA 纸线进主算后的单耗",
            "2019 扣除以造纸行为上限：东盟 +9 TWh（TH +2.5、MY +5.4、MM +0.8）；字面闭环 −38 TWh；LA 纸线 +4.2 TWh", "W08 之后", "用户"),
    "T17": ("自备电厂数据：MM MOEE 自备煤电、PH Petron 炼厂机组、TH SPP / VSPP 燃料清单、ID 园区自备（IUPTLS）", "第 204 项 (b) 的中心值与档位",
            "ID 自备煤低 / 中 / 高：+20 / −27 / −116 TWh；PH、MM < 2 TWh", "W08 之后", "用户"),
    "T18": ("糖厂统计：OCSB（TH）、SRA（PH）——甘蔗、蔗渣、热电联产", "蔗渣自用比例（潜力扣除）与蔗渣热值读法",
            "蔗渣自用比例按 1.0：TH 潜力再 −31 TWh；蔗渣留在 T_v2（旧读法）+171 TWh", "W08 之后", "用户"),
    "T19": ("小时曲线数据：东盟实测工业负荷曲线、Ganz 2021 原文、2013 年节假日、分时电价、检修停产、NREL 县级数据、周末规则、Keppres 41/1987", "G5 曲线形状与时区（“其他”的形状最敏感）",
            "东盟固定交流负荷峰值增量 +11.2（“其他”平线）至 +42.0 GW（v4 量）；主算 +21.5 GW", "W08 之后（主算形状已定）", "用户"),
    "T20": ("SKK Migas / 国家天然气平衡（商品气与上游自用）", "第 209 项 F1：气产量上限口径（商品气，或再扣自用）", "ID 再扣上游自用 216,060 TJ（约 60 TWh）；B6 一阶 ≈ 0", "W08 之后", "用户"),
    "T21": ("USGS 国别卷（缅甸、老挝 2019–2022）、Sepon 铜状态、钾肥单耗", "MM / LA 铜与钾肥的活动量", "LA 铜停产：LA `T_v2` +0.3；钾肥未显式（量小）", "W08 之后", "用户"),
    "T22": ("VN 分行业统计：APEC EGEDA 2019 VN 平衡、GSO 企业调查（含能耗）", "VN 混合拆分中“未细分”部分的分配", "VN“其他”占比随拆分来源在 18.7–23.6 % 间（本步 S6b → S6c）", "W08 之后", "用户"),
    "T23": ("BN：恒逸 PMB 2019–2022 产量与燃料 / 电、水泥粉磨站熟料进口", "BN 化工（第 202 项第 4 条）与水泥 (iii)", "量小（< 1 TWh，甲醇除外）", "W08 之后", "用户"),
    "T24": ("其他产品数据（玻璃、石灰、化工装置、化肥）", "显式子部门活动量", "各国 < 3 TWh", "W08 之后", "用户"),
}
I2_NEW = [
    ("T02", "I2：各国平衡表对自用残渣（蔗渣、5150、黑液）的覆盖范围（第 210 项第 4 条要求逐国核定；本步除 ID 外按“与 UNSD 相同”默认）", "锚边界对齐的扣减", "", "I2"),
    ("T03", "I2：PKS 厂内份额（本步中心值 50 %，D 级假设）", "潜力扣除", "", "I2"),
    ("T13", "I2：BN、ID 甲醇装置能源用途在 UNSD 中记在哪个流向（NEU 或工业化工行）", "避免与 NEU 气重复", "", "I2"),
    ("T16", "I2：Sun Paper Laos 2021 年纸线 2023 年产量、燃料与电力平衡（第 208 项新装置规则下进入主算）", "LA 纸线单耗", "", "I2"),
]


def main():
    rows = []
    for f in FILES:
        t = pd.read_csv(cm.W07 / f, dtype=str, keep_default_na=False)
        for r in t.to_dict("records"):
            text = f"{r.get('item', '')} {r.get('purpose', '')}"
            topic = next((k for k, rx in RULES if re.search(rx, str(r.get("item", "")))), None) or next((k for k, rx in RULES if re.search(rx, text)), "T24")
            rows.append(dict(source=f, country=r.get("country", f.split("/")[1][:2] if "_" in f.split("/")[1] else ""), item=r.get("item", ""), purpose=r.get("purpose", ""),
                             url_if_known=r.get("url_if_known", ""), priority_session=r.get("priority", ""), topic=topic))
    for topic, item, purpose, url, src in I2_NEW:
        rows.append(dict(source=src, country="", item=item, purpose=purpose, url_if_known=url, priority_session="", topic=topic))
    R = pd.DataFrame(rows)
    R.to_csv(cm.TABLES / "I2_MISSING_DATA_ROWS.csv", index=False, lineterminator="\n")
    order = ["T01", "T02", "T03", "T08", "T13", "T04", "T05", "T12", "T17", "T15", "T10", "T11", "T09", "T18", "T14", "T16", "T19", "T06", "T22", "T20", "T21", "T23", "T24", "T07"]
    out = []
    for i, t in enumerate(order, 1):
        g = R[R.topic == t]
        if g.empty and t not in TOPIC:
            continue
        name, use, impact, prio, who = TOPIC[t]
        urls = sorted({u.strip() for x in g.url_if_known for u in re.split(r"[;\s]+", x) if u.strip().startswith("http")})
        out.append(dict(rank=i, topic=t, 项目=name, 用途=use, 影响量级=impact, 已知网址="; ".join(urls), 优先级=prio, 由谁获取=who,
                        来源=";".join(sorted(set(g.source))), 合并的原始条目数=len(g), 原始条目=" || ".join(sorted(set(x[:120] for x in g.item if x)))))
    pd.DataFrame(out).to_csv(cm.I2 / "MISSING_DATA_ALL.csv", index=False, lineterminator="\n")
    print(pd.DataFrame(out)[["rank", "topic", "优先级", "合并的原始条目数"]].to_string()); print(R.topic.value_counts().to_string())


if __name__ == "__main__":
    main()
