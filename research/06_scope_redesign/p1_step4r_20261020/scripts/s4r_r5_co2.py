"""S4R R5: CO2_STORAGE_UNIFIED.csv - unified storage potential (ERIA-GCCSI 2024 P50 saline + hydrocarbon) and annual injection cap
(potential / 50 a, unchanged rule) vs the current registry values. Read-only."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4r_paths import COUNTRIES, OUT, md_table  # noqa: E402

YEARS = 50.0
# ERIA / GCCSI (2024) Comprehensive CCUS Research Report, Ch.1 (Consoli et al.): saline P50 [P90-P10] Gt, hydrocarbon net Mt, table / page
ERIA = {"MY": (127.0, 80.0, 197.0, 1773.0, "Tables 1.9 & 1.7, p.26 (Sabah not assessed)"), "ID": (49.0, 32.0, 75.0, 2275.0, "Tables 1.6 & 1.4, p.14-15 (3 of 10 basins)"),
        "BN": (18.0, 13.0, 25.0, 579.0, "Table 1.12 p.35; Table 1.10 p.37"), "TH": (15.0, 11.0, 22.0, 1024.0, "Tables 1.14 & 1.13, p.40"),
        "VN": (5.0, 3.0, 9.0, 303.4, "Tables 1.17 & 1.15, p.47 (Cuu Long / Bach Ho only)"), "PH": (0.0, 0.0, 0.0, 67.2, "Table 1.18 p.53 (no saline data; Malampaya only)"),
        "SG": (0.0, 0.0, 0.0, 0.0, "section 1.3.8 p.56: no storage potential"), "KH": (None, None, None, None, "section 1.3.9 p.56: unknown, no analysis completed"),
        "LA": (None, None, None, None, "section 1.3.9 p.56: unknown"), "MM": (None, None, None, None, "section 1.3.9 p.56: unknown"), "TL": (None, None, None, None, "not covered")}
CURRENT = {"BN": 18.5793, "ID": 51.275, "KH": 0.085, "LA": 0.0, "MM": 0.0, "MY": 128.773, "PH": 22.3, "SG": 0.0, "TH": 16.024, "TL": 0.25, "VN": 11.8}   # registry co2_storage_potential_* (Gt)
CURRENT_SRC = {"BN": "ERIA 2024", "ID": "ERIA 2024", "KH": "OGCI CSRC Cycle 5 (not re-checkable)", "LA": "SOURCE_ZERO", "MM": "SOURCE_ZERO", "MY": "ERIA 2024", "PH": "IEA 2021 p.35 (ADB 2013 theoretical, eff. 0.01)",
               "SG": "ERIA 2024", "TH": "ERIA 2024", "TL": "OGCI CSRC Cycle 5 (not re-checkable)", "VN": "IEA 2021 p.35 (ADB 2013 theoretical, eff. 0.001)"}
# other re-checkable sources for the countries ERIA leaves open
OTHER = {"KH": ("Preliminary assessment, Int. J. Greenhouse Gas Control (Kyoto Univ. repository, doi:10.1016/j.ijggc.2014.08.016): 90 Mt (structural traps, low case) to 45 Gt (hydrodynamic traps, high case); Khmer Basin most suitable", 0.09, 45.0),
         "TL": ("Santos / IFC: Bayu-Undan CCS ~10 Mtpa injection potential (project, not a national assessment); total reservoir capacity not published", None, None)}


def main():
    rows = []
    for c in COUNTRIES:
        e = ERIA[c]; cur = CURRENT[c]
        if e[0] is not None:
            p50 = e[0] + e[3] / 1000.0; lo = e[1] + e[3] / 1000.0; hi = e[2] + e[3] / 1000.0; status = "ERIA 2024 P50 (unified)"
        else:
            p50 = lo = hi = np.nan; status = "ERIA: unknown / not covered"
        proposed = p50 if pd.notna(p50) else 0.0
        rule = ""
        if c == "KH":
            proposed = 0.09; rule = "conservative rule: low case 0.09 Gt (structural traps) of the IJGGC 2014 preliminary assessment; high case 45 Gt as sensitivity"
        if c == "TL":
            proposed = 0.0; rule = "DATA_PENDING: no national assessment; Bayu-Undan 10 Mtpa project capacity (Santos) could be registered as a project-based annual cap (sensitivity); main = 0 until a total capacity source is found"
        if c in ("LA", "MM"):
            rule = "ERIA: unknown (no analysis) -> 0, registered as UNASSESSED (not SOURCE_ZERO)"
        if c == "SG":
            rule = "ERIA: no storage potential -> 0"
        rows.append(dict(country=c, current_potential_gt=cur, current_source=CURRENT_SRC[c], current_annual_cap_mt=cur * 1000 / YEARS,
                         eria_saline_p50_gt=e[0], eria_saline_p90_gt=e[1], eria_saline_p10_gt=e[2], eria_hydrocarbon_net_mt=e[3], eria_locator=e[4],
                         unified_potential_gt=proposed, unified_low_gt=lo if pd.notna(lo) else np.nan, unified_high_gt=hi if pd.notna(hi) else np.nan,
                         unified_annual_cap_mt=proposed * 1000 / YEARS, change_pct=((proposed / cur - 1) * 100) if cur > 0 else np.nan, status=status, rule=rule,
                         other_source=OTHER.get(c, ("", None, None))[0]))
    df = pd.DataFrame(rows).set_index("country")
    df.to_csv(OUT / "CO2_STORAGE_UNIFIED.csv", float_format="%.4f")
    md = ["# R5 CO₂ 封存潜力统一表（Gt；年注入上限 = 潜力 ÷ 50 年，11 国同一规则；封存成本 30 EUR/t 沿用 PyPSA-Eur 常数，价格年 DATA_PENDING）", "",
          md_table(df.reset_index()[["country", "current_potential_gt", "current_source", "unified_potential_gt", "unified_low_gt", "unified_high_gt", "unified_annual_cap_mt", "change_pct", "status", "rule"]], "{:,.3f}"), "",
          "- 注入爬坡（只记录）：已批项目 Kasawari 3.3 Mtpa（2027）、Arthit ~1 Mtpa（2028）、Tangguh UCC 约 15 Mt 累计（FID 2024-11）；模型年上限远高于此，不设政策上限（敏感性候选）。"]
    (OUT / "CO2_STORAGE_UNIFIED.md").write_text("\n".join(md), encoding="utf-8")
    print(df[["current_potential_gt", "unified_potential_gt", "unified_annual_cap_mt", "change_pct"]].round(3).to_string())


if __name__ == "__main__":
    main()
