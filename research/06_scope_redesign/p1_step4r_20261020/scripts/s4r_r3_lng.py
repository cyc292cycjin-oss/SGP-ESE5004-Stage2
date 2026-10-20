"""S4R R3: LNG receiving capacity comparison (read-only): model table (GEM 2025-08 extraction, research_inputs/lng_terminals_v5) and
model p_nom_max per country vs GEM GGIT 2025-09 by status (user download) and GIIGNL 2026 cross-checks. Output LNG_CAPACITY_COMPARISON.csv / .md."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4r_paths import COUNTRIES, EV, MWH_PER_T_LNG, OUT, REPO, S4P, dump_json, load_json, md_table  # noqa: E402

MW_PER_MTPA = 1e6 * MWH_PER_T_LNG / 8760.0    # 1 Mtpa = 13.333 TWh/a = 1,522.1 MW continuous
GIIGNL = {  # GIIGNL Annual Report 2026 (text extraction): 2025 LNG imports MT (p.?: table "LNG imports by country"), terminal notes
    "TH": dict(imports_2025_mt=10.5, note="Map Ta Phut 3 (Gulf MTP) 5 MTPA initial, expandable 10.8, COD Q1 2029 (AR 2026 terminal section)"),
    "SG": dict(imports_2025_mt=5.7, note=""), "ID": dict(imports_2025_mt=5.3, note=""), "MY": dict(imports_2025_mt=2.3, note=""), "PH": dict(imports_2025_mt=1.9, note=""),
    "VN": dict(imports_2025_mt=0.5, note="Thi Vai 1 MTPA (2023) expansion to 3 MTPA underway; Cai Mep (Hai Linh) 3 MTPA expandable to 6, commercial June 2025 (AR 2026 terminal section)"),
    "MM": dict(imports_2025_mt=0.04, note="first LNG cargo 2025 (AR 2026 note 3)"),
}


def main():
    model = pd.read_csv(REPO / "research_inputs/lng_terminals_v5/LNG_IMPORT_TERMINALS_GEM_2025.csv")
    caps = pd.read_csv(REPO / "research_inputs/lng_terminals_v5/LNG_IMPORT_CAPS_BY_COUNTRY.csv").set_index("country")
    S = load_json(S4P / "ASPECTS_SUMMARY.json")
    term = pd.DataFrame(S["aspect1"]["terminals"]); term = term[term.carrier == "LNG import"].set_index("country")
    gem = pd.read_csv(EV / "GEM_GGIT_LNG_IMPORT_TERMINALS_2025-09_ASEAN11.csv")
    rows = []
    for c in COUNTRIES:
        m = model[model.country == c]
        ms = m.groupby("status").capacity_mtpa.sum() if len(m) else pd.Series(dtype=float)
        g = gem[gem.iso == c]; gs = g.groupby("Status").mtpa.sum() if len(g) else pd.Series(dtype=float)
        gcount = g.groupby("Status").size() if len(g) else pd.Series(dtype=int)
        p_nom = float(term.p_nom_mw.get(c, 0.0)) if c in term.index else 0.0; p_max = float(term.p_nom_max_mw.get(c, 0.0)) if c in term.index else 0.0
        rows.append(dict(country=c,
                         model_existing_mtpa=float(caps.existing_mtpa.get(c, 0.0)), model_proposed_mtpa=float(caps.proposed_mtpa.get(c, 0.0)), model_units_missing_capacity=int(caps.units_missing_capacity.get(c, 0)),
                         model_table_operating_mtpa=float(ms.get("operating", 0.0)), model_table_construction_mtpa=float(ms.get("construction", 0.0)), model_table_proposed_mtpa=float(ms.get("proposed", 0.0)),
                         model_p_nom_mw=p_nom, model_p_nom_max_mw=p_max, model_p_nom_mtpa_equiv=p_nom / MW_PER_MTPA, model_p_nom_max_mtpa_equiv=p_max / MW_PER_MTPA, model_cap_twh=p_max * 8760 / 1e6,
                         gem2509_operating_mtpa=float(gs.get("operating", 0.0)), gem2509_construction_mtpa=float(gs.get("construction", 0.0)), gem2509_proposed_mtpa=float(gs.get("proposed", 0.0)),
                         gem2509_shelved_mtpa=float(gs.get("shelved", 0.0)), gem2509_cancelled_mtpa=float(gs.get("cancelled", 0.0)), gem2509_mothballed_mtpa=float(gs.get("mothballed", 0.0)),
                         gem2509_units_operating=int(gcount.get("operating", 0)), gem2509_units_proposed=int(gcount.get("proposed", 0)),
                         gem2509_project_cap_mtpa=float(gs.get("operating", 0.0) + gs.get("construction", 0.0) + gs.get("proposed", 0.0)),
                         giignl_imports_2025_mt=GIIGNL.get(c, {}).get("imports_2025_mt", np.nan), giignl_note=GIIGNL.get(c, {}).get("note", "")))
    df = pd.DataFrame(rows).set_index("country")
    df["option_a_uncapped"] = "endogenous at the terminal capex (no cap)"
    df["option_b_project_cap_mw"] = df.gem2509_project_cap_mtpa * MW_PER_MTPA
    df["option_c_current_cap_mw"] = df.model_p_nom_max_mw
    df["utilisation_2025_imports_over_operating"] = df.giignl_imports_2025_mt / df.gem2509_operating_mtpa.replace(0, np.nan)
    df.to_csv(OUT / "LNG_CAPACITY_COMPARISON.csv", float_format="%.3f")
    md = ["# R3 LNG 接收站容量对照（Mtpa；MW = Mtpa × 13.333 TWh/a ÷ 8,760 h = 1,522.1 MW/Mtpa，注册表 `lng_mwh_per_t` 13.333 MWh/t）", "",
          "- 模型表 = `LNG_IMPORT_TERMINALS_GEM_2025.csv`（GEM 2025-08 提取；existing = operating + construction；拟建按拟建容量，无容量的拟建单元计 0）；GEM 2025-09 = 用户下载的 GGIT 表（进口码头，按状态求和）；GIIGNL 2026 = 2025 年进口量与码头动态。", ""]
    show = df[["model_existing_mtpa", "model_proposed_mtpa", "model_p_nom_max_mtpa_equiv", "model_cap_twh", "gem2509_operating_mtpa", "gem2509_construction_mtpa", "gem2509_proposed_mtpa", "gem2509_shelved_mtpa", "gem2509_cancelled_mtpa", "gem2509_project_cap_mtpa", "giignl_imports_2025_mt", "utilisation_2025_imports_over_operating"]].copy()
    show.columns = ["模型存量", "模型拟建", "模型上限(Mtpa当量)", "模型上限 TWh", "GEM 运营", "GEM 在建", "GEM 拟建", "GEM 搁置", "GEM 取消", "GEM 项目口径(运营+在建+拟建)", "GIIGNL 2025 进口", "2025 进口/运营"]
    md.append(md_table(show.reset_index())); md.append("")
    md.append("备注（GIIGNL 2026）：" + "；".join(f"{c}: {v['note']}" for c, v in GIIGNL.items() if v["note"]))
    (OUT / "LNG_CAPACITY_COMPARISON.md").write_text("\n".join(md), encoding="utf-8")
    dump_json(df.reset_index().to_dict(orient="records"), OUT / "evidence/R3_LNG.json")
    print(show.round(2).to_string())


if __name__ == "__main__":
    main()
