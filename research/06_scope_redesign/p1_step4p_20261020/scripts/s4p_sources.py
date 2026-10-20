"""S4P: EXTERNAL_SOURCES.md - one list of every external source used (registry sources cited in the matrix + the three
web-search benchmark files), with institution / document / year / page-or-table / URL / retrieval date; DATA_PENDING records listed separately."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4p_paths import OUT  # noqa: E402

FILES = {
    "需求、工业产量（EXT_DEMAND_BENCHMARKS.json）": OUT / "evidence/EXT_DEMAND_BENCHMARKS.json",
    "政策、封存、海上风电、生物质（EXT_TECH_POLICY_BENCHMARKS.json）": OUT / "evidence/EXT_TECH_POLICY_BENCHMARKS.json",
    "成本参数（EXT_COST_BENCHMARKS.json）": OUT / "evidence/EXT_COST_BENCHMARKS.json",
}
REGISTRY_SOURCES = [
    ("Decision 500/QD-TTg (PDP VIII, 2023-05-15) / Decision 768/QD-TTg (revised PDP VIII, 2025-04-15)", "VN 光伏 / 陆上 / 海上风电技术潜力、水电、核电规划", "注册表 potential_*_VN_*、nuclear_plan_cap_VN"),
    ("ERIA / GCCSI (2024) Comprehensive CCUS Research Report, Ch.1 Geological Storage Potential of CO2 in Southeast Asia", "ID / MY / BN / TH 封存潜力 P50", "注册表 co2_storage_potential_*；提取记录 CO2_STORAGE_EXTRACTION.md"),
    ("IEA (2021) CCUS: The Opportunity in Southeast Asia, p.35", "VN 11.8、PH 22.3 Gt 封存潜力（ADB 2013 理论值）", "注册表 co2_storage_component_VN_* / PH_*"),
    ("OGCI / CSRC Cycle 5 (2025) Appendix B Asia", "KH 0.085、TL 0.25 Gt", "注册表；本次未能复核（bot 检查）"),
    ("IEA WEO 2025 Table 2.3 (p.109)", "2050 STEPS / NZE / CPS 气、油、煤价", "注册表 fuel_price_*；FUEL_PRICES_2050_EUR2020.csv"),
    ("Neumann, Hampp, Brown (2025) Nat. Commun. doi:10.1038/s41467-025-60652-1; Zenodo 10.5281/zenodo.14872184", "氢、氨、甲醇、FT 进口价（欧洲最低 × 1.2）", "注册表 import_price_*"),
    ("technology-data v0.15.0 (costs_2050), rebased EUR2025 → EUR2020", "全部技术成本层（SMR 除外）", "cost_layers_v5"),
    ("ACE AEO8 (2024) Table D.15 (SMR), Appendix C.3 / C.8 / D.1", "SMR 投资 8,421 EUR2020/kW；需求增长、ATS 相对因子", "注册表 smr_*、demand_aeo8_*"),
    ("IEA Cost of Capital Observatory (2025 dashboard update)", "ID / VN / PH / MY / TH 名义 WACC", "finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv"),
    ("GEM Global Gas Infrastructure Tracker 2025-11 / GOGET 2026-03 / GIPT 2026-09", "LNG 码头、气田份额、机组", "lng_terminals_v5、fleet_v5"),
    ("UNSD Energy Balances 2019", "2019 需求基数、气产上限", "demand_v5、FOSSIL_PRODUCTION_CAPS_2050.csv"),
    ("ACE (2024) APG Interconnections; AIMS III 2040 projections", "走廊规划上限", "corridors/APG_PLAN_CAPS_S4F1.csv"),
    ("World Bank / ESMAP (2019-2020) Global Offshore Wind Technical Potential; WB Offshore Wind Roadmap for Vietnam (2021) / Philippines (2022)", "海上风电技术潜力", "注册表 potential_offwind_*（PH、VN）"),
    ("FAOSTAT 2019-2023; IRENA (2017, 2022) biomass", "生物质潜力", "biomass_v5"),
    ("IEAGHG (2004) PH4/30; ZEP (2011); Stolaroff et al. (2021)", "CO₂ 船运链、封存与过境成本", "co2_v5/EXTRA_ASEAN_STORAGE_COST_S4C4.csv"),
    ("PyPSA-Eur v2025.07.0 config.default.yaml; PyPSA-Earth", "20,000 MW 单线扩建上限、长度系数、工业路线、光伏 / 风电布局", "configs/research/baseline.yaml"),
]


def main():
    md = ["# S4P 外部来源清单（带出处）", "", "## A. 注册表中已登记、本次核查引用的来源", "", "| 来源 | 用于 | 注册表 / 文件 |", "|---|---|---|"]
    for s, u, r in REGISTRY_SOURCES:
        md.append(f"| {s} | {u} | {r} |")
    total = 0; pending = 0
    for title, p in FILES.items():
        if not p.exists():
            md.append(f"\n## {title}\n\n（文件缺失）")
            continue
        recs = json.load(open(p, encoding="utf-8"))
        if isinstance(recs, dict):
            recs = recs.get("records", list(recs.values())[0] if recs else [])
        md.append(f"\n## B. {title}（{len(recs)} 条；检索日期 2026-10-20）\n")
        md.append("| 国 / 区域 | 量 | 年 | 值 | 单位 | 机构 | 文件 | 年份 | 页 / 表 | URL |")
        md.append("|---|---|---|---|---|---|---|---|---|---|")
        pend = []
        for r in recs:
            total += 1
            val = str(r.get("value", ""))
            row = [str(r.get("country", r.get("region_or_country", ""))), str(r.get("quantity", r.get("topic", ""))), str(r.get("year", r.get("year_basis", ""))), val,
                   str(r.get("unit", "")), str(r.get("source_institution", "")), str(r.get("source_document", ""))[:120], str(r.get("source_year", "")), str(r.get("page_or_table", ""))[:80], str(r.get("url", ""))[:160]]
            row = [c.replace("|", "/").replace("\n", " ") for c in row]
            if "DATA_PENDING" in val.upper():
                pend.append(row); pending += 1
            md.append("| " + " | ".join(row) + " |")
        if pend:
            md.append(f"\n其中 DATA_PENDING {len(pend)} 条：" + "；".join(f"{p[0]} {p[1]} {p[2]}" for p in pend))
    md.insert(2, f"外部检索记录共 {total} 条，其中 DATA_PENDING {pending} 条（未找到即如实标注，未估算）。每条记录在对应 JSON 中含完整字段（含 notes 与 retrieval_date）。\n")
    (OUT / "EXTERNAL_SOURCES.md").write_text("\n".join(md), encoding="utf-8")
    print("records", total, "pending", pending)


if __name__ == "__main__":
    main()
