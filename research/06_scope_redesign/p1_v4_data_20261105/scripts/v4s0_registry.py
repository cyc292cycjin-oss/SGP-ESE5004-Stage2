"""V4 S0 section 1: data registry of downloads/ (DATA_REGISTRY_V4_DOWNLOADS.csv) and the gap list (evidence/DOWNLOAD_GAPS.csv).

    python scripts/v4s0_registry.py --work <work dir>

Bytes and SHA256 are computed here; source URL from DOWNLOAD_LIST.md; version / release date and licence read from the files
(About sheets, README, metadata JSON, PDF data guide) during S0 and written below with the basis of each statement. 'unknown'
means the files do not state it and the web page was not checked in S0 (no new download / browsing in this step).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

GEM_CC = ("CC BY 4.0", "About 页：Distributed under a Creative Commons Attribution 4.0 International License")
CT_LIC = ("CC BY 4.0（有例外）", "ABOUT_THE_DATA/about_the_data_v5_12_0.pdf：全部数据 CC BY 4.0；其他制造、其他化工、木材、其他金属、其他采矿、玻璃、石灰、食品、纺织等国家级估计转载自 EDGAR / CEDS，须另查其条款")
CT_LIC_OLD = ("CC BY 4.0（有例外）", "内层 ABOUT_THE_DATA/about_the_data_v5_5_0.pdf（未展开阅读；按 v5.12.0 同类说明推定，INFERENCE）")
CT_URL = "https://climatetrace.org/data"
CT_NEW = "Climate TRACE V5.12.0（Inventory October 2026；包生成 2026-10-29）"
CT_OLD = "Climate TRACE V5.5.0（内层文件日期 2026-03-22）"
CT_SUB = {
    "manufacturing_aluminum": "铝", "manufacturing_cement": "水泥", "manufacturing_chemicals": "化工（合成氨等）", "manufacturing_food-beverage-tobacco": "食品饮料烟草",
    "manufacturing_glass": "玻璃", "manufacturing_iron-and-steel": "钢铁", "manufacturing_lime": "石灰", "manufacturing_other-chemicals": "其他化工",
    "manufacturing_other-manufacturing": "其他制造", "manufacturing_other-metals": "其他金属", "manufacturing_petrochemical-steam-cracking": "石化蒸汽裂解",
    "manufacturing_pulp-and-paper": "纸浆造纸", "manufacturing_textiles-leather-apparel": "纺织皮革服装", "manufacturing_wood-and-wood-products": "木材及制品",
    "mineral_extraction_bauxite-mining": "铝土矿开采", "mineral_extraction_copper-mining": "铜矿开采", "mineral_extraction_iron-mining": "铁矿开采",
    "mineral_extraction_other-mining-quarrying": "其他采矿采石", "mineral_extraction_rock-quarrying": "碎石采石", "mineral_extraction_sand-quarrying": "砂石开采",
    "fossil_fuel_operations_oil-and-gas-production": "油气开采", "fossil_fuel_operations_oil-and-gas-refining": "炼油",
}

META = {
    "01_gem_steel/gem-download (2).zip": dict(
        source="GEM Global Iron and Steel Tracker", url="https://globalenergymonitor.org/projects/global-iron-steel-tracker/download-data/",
        version="厂级、炼钢单元、炼铁单元：September 2026 (V1)；附 Global Energy Ownership Tracker October 2026 V1、Met Coal & Iron Ore December 2025 V1", lic=GEM_CC,
        content="5 个 xlsx：厂级表（含 2019–2025 逐厂产量页 Plant production、产能与状态页）、炼钢单元（EAF/BOF/IF/OHF）、炼铁单元（BF/DRI）、所有权表、国别冶金煤与铁矿表",
        note="SHA256 与 v3 摄入 work/p2_data_intake/v3_20261102/02_facilities/gem-download.zip 相同（同一份下载）；Ownership Tracker 与 02 包中的完全相同"),
    "02_gem_cement/gem-download (2).zip": dict(
        source="GEM Global Cement and Concrete Tracker", url="https://globalenergymonitor.org/projects/global-cement-concrete-tracker/download-data/",
        version="July 2026 (V1) Standard Copy；附 Global Energy Ownership Tracker October 2026 V1", lic=GEM_CC,
        content="厂级水泥表 3,884 行：坐标、状态、厂型、水泥与熟料产能（Mt/a）、2024–2025 实际水泥产量、窑数与工艺、替代燃料；另附所有权表",
        note="SHA256 与 v3 摄入 02_facilities/gem-download (1).zip 相同（同一份下载）"),
    "03_gem_chemicals/Plant-level-data-Global-Chemicals-Tracker-November-2026-V1.xlsx": dict(
        source="GEM Global Chemicals Tracker（原 Global Chemicals Inventory 更名）", url="https://globalenergymonitor.org/projects/global-chemicals-inventory/",
        version="November 2026 (V1)；运营状态截至 2026-09-30", lic=GEM_CC,
        content="基础化工厂级表（Plant Data：坐标、状态、主产品、原料、工艺）与产品产能表（Chemical Capacities，ttpa）"),
    "04_sfi_pulp_paper/SFI_ALD_Pulp_Paper_Database_July_2025.xlsx": dict(
        source="Spatial Finance Initiative Global Pulp and Paper Mill Database", url="https://cgfi.ac.uk/spatial-finance-initiative/geoasset-project/pulp-and-paper-database/",
        version="July 2025", lic=("CC BY 4.0", "About_General 页：licensed under the Creative Commons Attribution 4.0 International License"),
        content="全球纸浆与造纸厂 3,416 家：坐标、状态、厂型、产品、纸浆与纸产能（t/a）、燃料、所有权；附各国产能对产量的完整度表"),
    "05_sfi_ethylene/Global_Ethylene_Production_Database_December_2025.xlsx": dict(
        source="Spatial Finance Initiative Global Ethylene Production Database", url="https://zenodo.org/records/17866398",
        version="December 2025", lic=("CC BY 4.0", "下载清单所记 Zenodo 记录页；文件内只有数据页，无许可说明"),
        content="全球乙烯装置 342 个：坐标、状态、乙烯产能（kt/a）、原料、是否炼化一体、投产年、所有权"),
    "07_etsap_industrial_demand/Industrial-energy-demands-v2.1.0.zip": dict(
        source="Follow-ETSAP Industrial-energy-demands（Kerekeš et al., Sci Data 12, 1745 (2025)）", url="https://zenodo.org/records/15524913",
        version="v2.1.0（GitHub 提交 678c2b4）；数据基年 2018（玻璃 2020）；下载清单所记论文版本为 v2.0.2，按清单取了更新版",
        lic=("CC BY 4.0（附说明）", "README.md 与 LICENSE：CC BY 4.0；少量 Statista 数值经 TUM 校园许可引用，不得大量转载"),
        content="12 个产量文件（钢、铝、铜、水泥、玻璃、石灰、纸浆纸、氨、甲醇、烯烃、芳烃、氯）+ 4 个能耗计算文件（BAT 与理论最小单耗、区域能耗分配、TIAM 区域低效系数与缩放能耗、技术验证）+ TIAM_regions.csv",
        note="下载清单网址为 v2.0.2 所在记录页；v2.1.0 的版本页网址在文件中未记录"),
    "08_ffe_profiles/id_opendata_59_metadata.json": dict(
        source="FfE Open Data 数据集 59 Normed Industrial Electrical Load Profile (Germany)", url="https://opendata.ffe.de/dataset/normalized-industrial-electrical-load-profiles-germany/",
        version="参考年 2017（publicationDate 为空）", lic=("CC BY 4.0", "元数据 licenses：CC-BY-4.0，署名 © FfE, eXtremOS Project"),
        content="数据集 59 的 OEP 元数据：说明、14 个行业编码（internal_id 0–13）、许可、字段定义"),
    "08_ffe_profiles/opendata.customization": dict(
        source="FfE Open Data 数据集 59", url="https://opendata.ffe.de/dataset/normalized-industrial-electrical-load-profiles-germany/",
        version="参考年 2017", lic=("CC BY 4.0", "文件内嵌同一份元数据"),
        content="数据集 59 的完整数据（JSON）：键 data 下 11 条曲线，每条带 internal_id 与 2017 年逐小时归一化电负荷 values；FfE 只以此形式发布，无按行业 csv",
        note="文件名保留原样（用户 2026-11-05 确认）"),
    "09_nrel_heat/heat_loadshapes_20190927.tar.gz": dict(
        source="NREL Manufacturing Thermal Load Shapes（data.nlr.gov 提交 118）", url="https://data.nlr.gov/submissions/118",
        version="2019-09-27（目录名）", lic=("未知", "包内无许可说明；网页未在 S0 核对"),
        content="按 NAICS 分区的 parquet（132 个文件），制造业热负荷形状；下载清单所称 Manufacturing_Heat_Loadshapes.tar.gz，实际文件名不同"),
    "09_nrel_heat/all_load_shapes_process_heat.gzip": dict(
        source="NREL Manufacturing Thermal Load Shapes", url="https://data.nlr.gov/submissions/118",
        version="gzip 头时间 2020-02-21", lic=("未知", "文件内无许可说明"),
        content="工艺热负荷形状 CSV（解压 150.7 MB）：月 × 星期 × 小时 × NAICS × 规模类的周运行小时分数（0–1，含高低值）"),
    "09_nrel_heat/all_load_shapes_boiler.gzip": dict(
        source="NREL Manufacturing Thermal Load Shapes", url="https://data.nlr.gov/submissions/118",
        version="gzip 头时间 2020-02-21（下载清单所称勘误版）", lic=("未知", "文件内无许可说明"),
        content="锅炉负荷形状 CSV（解压 129.8 MB），结构同工艺热"),
    "09_nrel_heat/mfg_eu_temps_meta.json": dict(
        source="NREL 同一提交", url="https://data.nlr.gov/submissions/118",
        version="未写", lic=("未知", "文件内无许可说明"),
        content="分县制造业按终端用途与温度能耗表（316 MB CSV，未下载）的字段说明，不是负荷形状本身的元数据"),
    "11_calliope_indonesia/calliope_indonesia_c8584f7b.zip": dict(
        source="Calliope-Indonesia（J. K. A. Langer）", url="https://github.com/JKALanger/calliope_indonesia",
        version="提交 c8584f7b2b8d1f5e5bd04fa6bf12782cafadb9dd，2024-04-01（审阅端附注文件）", lic=("未知（仓库无 LICENSE 文件）", "压缩包内无许可文件；引用前须问师哥"),
        content="Calliope 模型配置（地点、联络线、技术、情景）与 2030/2040/2050 需求曲线、风光水 OTEC 出力曲线 CSV",
        note="包内含 .idea IDE 工作区文件，不进入仓库"),
}
for k, z in CT_SUB.items():
    META[f"06_climate_trace/{k}.zip"] = dict(source="Climate TRACE", url=CT_URL, version=CT_NEW, lic=CT_LIC,
                                            content=f"子行业「{z}」：资产级排放（parquet，全部气体，含 capacity、activity、emissions_factor 等字段）、置信度、不确定度、所有权、国家月度合计")
for k, z in (("fossil_fuel_operations", "化石燃料生产（油气开采、炼油、油气运输、采煤、其他）"), ("manufacturing", "制造业 13 个子行业")):
    META[f"06_climate_trace/{k}.zip"] = dict(source="Climate TRACE（旧版汇总包）", url=CT_URL, version=CT_OLD, lic=CT_LIC_OLD,
                                            content=f"{z}，按 16 种气体分为内层 zip，每个内含 CSV 资产表与国家表",
                                            note="旧版，内容被 V5.12.0 行业分包覆盖（采煤、油气运输除外）；内层 zip 全部展开约超过 10 GB 磁盘上限，S0 只登记成员清单")

GAPS = [
    ("06_climate_trace", "按国家的 11 个数据包", "网站按行业提供下载；改为 22 个行业分包 + 2 个旧版汇总包（清单允许的替代方式），按 iso3_country 过滤即可得到各国", "无"),
    ("06_climate_trace", "采煤、油气运输的 V5.12.0 行业分包", "未下载；只在 V5.5.0 汇总包中有。属于能源部门，不在工业终端，不影响 S0", "无"),
    ("08_ffe_profiles", "按行业的 csv", "FfE 只以 JSON（opendata.customization）发布，用户确认不补；11 条曲线", "无"),
    ("09_nrel_heat", "负荷形状本身的元数据 JSON", "下到的 mfg_eu_temps_meta.json 是分县温度表的元数据；负荷形状字段含义从 CSV 表头和 NREL 说明推断（INFERENCE）", "低：S1 前如需正式引用，补下载页说明"),
    ("09_nrel_heat", "316 MB 分县温度 CSV", "按清单不下", "无"),
    ("10_unsd", "UNSD 2022 能源平衡", "按清单先不下；S0 第 3 节判断是否需要（见报告）", "见报告第 3.3 节"),
    ("07_etsap_industrial_demand", "v2.1.0 版本页网址", "清单给的是 v2.0.2 记录页；文件内只有 GitHub 提交号", "低：登记时补"),
    ("11_calliope_indonesia", "许可证", "仓库无 LICENSE；只能作内部对照，引用前问师哥", "需师哥确认"),
    ("09_nrel_heat", "许可", "包内无许可说明，网页未核对", "低：S1 前核对"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    import argparse as _a
    ap = _a.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); a = ap.parse_args()
    dl = a.work / "downloads"
    rows, missing = [], []
    files = sorted(f for f in dl.rglob("*") if f.is_file())
    for f in files:
        rel = f.relative_to(dl).as_posix()
        m = META.get(rel)
        if m is None:
            missing.append(rel); continue
        stem = f.name[: -len(".tar.gz")] if f.name.endswith(".tar.gz") else (f.stem + "_decompressed" if f.suffix == ".gzip" else f.stem)
        ext = f"extracted/{rel.split('/')[0]}/{stem}/" if f.suffix in (".zip", ".gzip") or f.name.endswith(".tar.gz") else ""
        rows.append(dict(relative_path=f"downloads/{rel}", bytes=f.stat().st_size, sha256=sha256(f), source=m["source"], source_url=m["url"],
                         version_or_release=m["version"], licence=m["lic"][0], licence_basis=m["lic"][1], content=m["content"],
                         extracted_to=ext, note=m.get("note", "")))
    if missing or len(rows) != len(META):
        raise SystemExit(f"registry metadata mismatch: files without metadata {missing}; metadata without file {sorted(set(META) - {r['relative_path'][10:] for r in rows})}")
    with open(a.work / "DATA_REGISTRY_V4_DOWNLOADS.csv", "w", newline="", encoding="utf-8") as o:
        w = csv.DictWriter(o, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    with open(a.work / "evidence" / "DOWNLOAD_GAPS.csv", "w", newline="", encoding="utf-8") as o:
        w = csv.writer(o); w.writerow(["subdir", "missing_item", "reason_or_substitute", "action_needed"]); w.writerows(GAPS)
    print("registered", len(rows), "files,", sum(r["bytes"] for r in rows), "bytes; gaps", len(GAPS))


if __name__ == "__main__":
    main()
