"""V4 S1: V4_S1_EVIDENCE.json - every number the report V4_S1_ID_REPORT.md quotes, with its source table / file, status and data grade,
read back from the S1 tables (s1/*.csv) and the section evidence fragments (s1/_*.json). No number is typed in here.

    python scripts/v4s1_summary.py --work <work dir>      (WSL pypsa-earth python)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); a = ap.parse_args()
    s1 = a.work / "s1"
    J = {p.stem.lstrip("_"): json.loads(p.read_text(encoding="utf-8")) for p in sorted(s1.glob("_*.json"))}
    N = {}

    def put(key, value, unit, source, status, grade):
        N[key] = dict(value=(round(float(value), 6) if isinstance(value, (int, float)) else value), unit=unit, source=source, status=status, grade=grade)

    cap, opt, fac, nic, bpe = J["captive_evidence"], J["captive_options_evidence"], J["facilities_evidence"], J["nickel_evidence"], J["bps_energy_evidence"]
    b = cap["base"]
    put("1.base.nes_coal_raw", b["other_raw_twh"], "TWh", "s1/ID_CAPTIVE_BASE_TRACE.csv (UNSD n.e.s. industry hard coal 37,514.237 kt + coke 57.8 kt)", "EXACT", "B")
    put("1.base.cement_coal_2019", b["cement_coal_2019_twh"], "TWh", "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv", "EXACT", "C")
    put("1.base.other19_coal_v2", b["other19_coal_v2_twh"], "TWh", "INDUSTRY_2050_OTHER_BUCKET.csv", "EXACT", "C")
    put("1.base.other19_coal_v3eq", b["other19_coal_v3eq_twh"], "TWh", "x v3 other scale", "EXACT", "C")
    put("1.base.other19_total_v2", b["other19_total_v2_twh"], "TWh", "INDUSTRY_2050_OTHER_BUCKET.csv", "EXACT", "C")
    put("1.base.other19_total_v3eq", b["other19_total_v3eq_twh"], "TWh", "x v3 other scale", "EXACT", "C")
    put("1.base.other_scale", b["other_scale"], "-", "INDUSTRY_V3_EVIDENCE.json", "VERIFIED", "C")
    put("1.base.multiplier", b["multiplier"], "-", "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", "VERIFIED", "C")
    for k, v in b["ncv_gj_per_t"].items():
        put(f"1.ncv.{k}", v, "GJ/t", "pypsa-asean _helpers / HEESI 2025 Annex 03 x BOE 5.873 GJ", "VERIFIED (factor) / INFERENCE (BOE size)", "B")
    put("1.ncv.boe_gj", b["boe_gj"], "GJ/BOE", "HEESI 2025 Annex 03 electric power 0.6130 BOE/MWh", "INFERENCE", "B")
    ap_ = cap["unsd_autoproducer"]
    for k in ("coal_kt", "gas_tj", "diesel_kt", "production_gwh", "capacity_mw", "fuel_input_total_twh", "main_activity_coal_kt"):
        put(f"1.unsd_autoproducer.{k}", ap_[k], k.split("_")[-1], "UNdata export 2025-05-02, Indonesia 2019", "VERIFIED", "B")
    for k, v in ap_["fuel_input_twh"].items():
        put(f"1.unsd_autoproducer.fuel_input.{k}", v, "TWh", "UNdata x pypsa-asean factors", "VERIFIED", "B")
    H = pd.read_csv(s1 / "HEESI_2025_VALUES_USED.csv")
    for r in H.itertuples():
        put(f"1.heesi.{r.table.split(' ')[0]}.{r.column}.{'' if pd.isna(r.year) else int(r.year)}", r.value, r.unit, f"HEESI 2025 PDF p.{r.pdf_page} (printed p.{r.printed_page})", "VERIFIED", "B")
    g = cap["gipt"]
    for k in ("captive_units_all_status", "captive_operating_2026_mw", "captive_2019_yearend_mw", "captive_2019_avg_mw", "units_2019", "start_2019_mw", "all_coal_operating_2026_mw"):
        put(f"1.gipt.{k}", g[k], "MW" if k.endswith("mw") else "units", "GEM GIPT 2026-09, s1/ID_CAPTIVE_UNITS_GIPT.csv", "VERIFIED", "B")
    for k, v in g["by_type_2019_yearend_mw"].items():
        put(f"1.gipt.type2019.{k}", v, "MW", "GEM GIPT 2026-09", "VERIFIED", "B")
    for lv, L in cap["levels"].items():
        put(f"1.level.{lv}.hours", L["h"], "h", L["h_src"], "VERIFIED (inputs)" if lv != "central" else "PROPOSED", L["h_grade"])
        put(f"1.level.{lv}.spec", L["s"], "t/MWh", L["s_src"], "VERIFIED (inputs)" if lv != "central" else "PROPOSED", L["s_grade"])
    for lv, e in cap["estimate_total"].items():
        for k, v in e.items():
            put(f"1.estimate.{lv}.{k}", v, "", "s1/ID_CAPTIVE_COAL_2019.csv", "PROPOSED" if lv == "central" else "INFERENCE", "C")
    for k, v in cap["topdown"]["residual_gwh"].items():
        put(f"1.topdown.{k}", v, "GWh", "s1/ID_CAPTIVE_CROSSCHECK.csv", "INFERENCE", "C")
    CC = pd.read_csv(s1 / "ID_CAPTIVE_CROSSCHECK.csv")
    for i, r in CC.iterrows():
        put(f"1.crosscheck.{i:02d}", r.estimate, r.unit, f"{r.check} | {r['item']} | {r.level} | reference {r.reference} | ratio {r.ratio}", "INFERENCE", "C")
    OV = pd.read_csv(s1 / "ID_CAPTIVE_V3_OVERLAP.csv")
    for r in OV.itertuples():
        put(f"1.overlap.{r.v3_subsector}.{r.level}.double_count_2050", r.double_count_2050_twh, "TWh", "s1/ID_CAPTIVE_V3_OVERLAP.csv", "INFERENCE", "C")
        put(f"1.overlap.{r.v3_subsector}.{r.level}.gen_share_of_v3_el", r.captive_gen_share_of_v3_el, "-", "s1/ID_CAPTIVE_V3_OVERLAP.csv", "INFERENCE", "C")
    put("1.options.reproduction.max_dev_T", opt["reproduction"]["max_abs_dev_T_carriers_mwh"], "MWh", "scratch chain vs repository", "EXACT", "-")
    put("1.options.reproduction.max_dev_v3_other", opt["reproduction"]["max_abs_dev_v3_other_mwh"], "MWh", "scratch chain vs repository", "EXACT", "-")
    for r in opt["options"]:
        for k in ("captive_coal_removed_2019_twh", "captive_electricity_added_2019_twh", "eta_model", "delta_industry_2019_twh", "other_2019_v3eq_twh", "T_2050_twh", "delta_T_2050_twh",
                  "other_2050_v3_twh", "delta_other_2050_twh", "double_count_2050_explicit_twh", "delta_other_2050_electricity_twh", "delta_other_2050_heat_high_twh",
                  "delta_other_2050_heat_medium_b_twh", "delta_other_2050_heat_medium_a_twh", "delta_other_2050_heat_twh", "delta_other_2050_oil_twh"):
            if r.get(k) is not None:
                put(f"1.option.{r['option']}.{r['level']}.{k}", r[k], "TWh" if k.endswith("twh") else "-", "s1/ID_CAPTIVE_OPTIONS.csv", "PROPOSED (quantified)", "C")
    for y, z in fac["steel_cal"].items():
        for k, v in z.items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    put(f"2.steel.{y}.{k}.{kk}", vv, "-", "s1/ID_STEEL_FACILITIES.csv", "VERIFIED (calibration)", "B")
            else:
                put(f"2.steel.{y}.{k}", v, "kt", "s1/ID_STEEL_FACILITIES.csv", "VERIFIED", "B")
    for y, z in fac["cement_cal"].items():
        for k, v in z.items():
            put(f"2.cement.{y}.{k}", v, "", "s1/ID_CEMENT_FACILITIES.csv", "VERIFIED", "B")
    for k in ("unsd19_twh", "coke_twh", "coal_twh", "c_intensity_mwh_per_t", "bof_coal_gj", "capped_share_2024", "t2050_mt"):
        put(f"2.steel.{k}", fac["steel"][k], "", "s1/_facilities_evidence.json", "VERIFIED", "B")
    put("2.steel.unsd19_gas", fac["steel"]["unsd19_by_carrier"]["gas"], "TWh", "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv", "VERIFIED", "B")
    for k, v in fac["usgs"].items():
        for y, vv in v.items():
            put(f"2.usgs.{k}.{y}", vv, "kt", "USGS MYB 2023 Indonesia table 1 (PDF p.6-7)", "VERIFIED", "A")
    CMP = pd.read_csv(s1 / "ID_S1_COMPARISON.csv")
    for i, r in CMP.iterrows():
        put(f"2.comparison.{i:02d}", r.value, r.unit, f"{r['item']} | {r.basis} | node {r.get('node', '')} | reference {r.reference} | rel {r.rel_diff}", "VERIFIED (calc) / PROPOSED (threshold)", r.grade)
    cc = fac["cement_check"]
    for k in ("edgar_2A1_2019_kt", "edgar_2A1_2024_kt", "clinker_2019_mt", "cement_equivalent_mt", "usgs_2019_mt", "implied_clinker_ratio_vs_usgs", "edgar_2024_clinker_mt",
              "implied_ratio_2023_edgar2024", "correction_ii_delta_cement19_twh", "correction_ii_delta_other50_el_twh"):
        put(f"2.cement_check.{k}", cc[k], "", "s1/_facilities_evidence.json", "VERIFIED" if not k.startswith("correction") else "PROPOSED", "C")
    for k, v in cc["gem"].items():
        if not isinstance(v, dict):
            put(f"2.cement_check.gem.{k}", v, "", "GEM GCCT 2026-07", "VERIFIED", "B")
    for k, z in cc["chain"]["corrections"].items():
        for kk in ("cement19_twh", "other19_twh", "T_twh", "other50_twh"):
            put(f"2.cement_check.{k}.{kk}", z[kk], "TWh", "scratch chain (EDGAR row edited)", "PROPOSED (quantified)", "C")
    NB = pd.read_csv(s1 / "ID_NICKEL_BASEYEAR.csv")
    for i, r in NB.iterrows():
        for k in ("ni_content_t", "electricity_twh", "useful_heat_gt400_twh", "fuel_input_twh", "total_model_twh"):
            if pd.notna(r[k]):
                put(f"3.nickel.{i:02d}.{k}", r[k], "t" if k.endswith("_t") else "TWh", f"{r['item']} | {r.source}"[:300], r.status, r.grade)
    for k, v in nic["mix"].items():
        put(f"3.mix.{k}", v if not isinstance(v, dict) else json.dumps(v), "-", "USGS MYB 2023 Indonesia table 1 / Wei 2020", "VERIFIED", "B")
    for k, v in nic["options"].items():
        put(f"3.option.{k}.nickel_twh", v["nickel_twh"], "TWh", "v3_industry decompose + nonferrous", "PROPOSED (quantified)", "C")
        put(f"3.option.{k}.other_twh", v["other_twh"], "TWh", "v3_industry decompose + nonferrous", "PROPOSED (quantified)", "C")
    K = pd.read_csv(s1 / "ID_BPS_IBS_2019_BY_KBLI.csv", dtype={"kbli": str})
    for r in K.itertuples():
        for k in ("fuels_twh", "el_end_use_twh", "total_end_use_twh", "coal_all_twh", "gas_twh", "oil_twh", "el_purchased_twh", "el_generated_twh", "el_sold_twh"):
            put(f"4.ibs.{r.kbli}.{k}", getattr(r, k), "TWh", "s1/ID_BPS_IBS_2019_BY_KBLI.csv", "VERIFIED (quantities) / INFERENCE (LPG density)", "B / C")
    V = pd.read_csv(s1 / "ID_BPS_VS_UNSD_2019.csv")
    for r in V.itertuples():
        put(f"4.coverage.{r.scope}.{r.carrier}", r.coverage, "-", f"IBS {r.bps_ibs_twh:.3f} vs UNSD {r.unsd_2019_twh} TWh; HEESI {r.heesi_2019_twh}", "VERIFIED", "B")
    S = pd.read_csv(s1 / "ID_OTHER_BUCKET_SPLIT_PROPOSED.csv")
    for i, r in S.iterrows():
        put(f"4.split.{i:02d}", r.total_twh, "TWh", f"block {r.block} | {r.label}", r.status, r.grade)
    PC = pd.read_csv(s1 / "ID_BPS_PARSE_CHECK.csv")
    for (t, l, st), n in PC.groupby(["table", "line", "status"]).size().items():
        put(f"4.parse_check.{t}.{l}.{st}", n, "checks", "s1/ID_BPS_PARSE_CHECK.csv", "VERIFIED", "-")
    put("4.parse_check.total", len(PC), "checks", "s1/ID_BPS_PARSE_CHECK.csv", "VERIFIED", "-")
    put("4.parse_check.max_abs_rel_ok", float(PC[PC.status == "OK"].rel_diff.abs().max()), "-", "s1/ID_BPS_PARSE_CHECK.csv", "VERIFIED", "-")
    out = dict(instruction="V4_S1_INSTRUCTION.md v1 (SHA256 e38b8f174e8a35f839cfe0f136e8573e17cb8ecd5574ce1e2e36966468d23d86)",
               legend=dict(status="VERIFIED / EXACT / INFERENCE / PROPOSED", grade="A actual output or statistic; B official capacity or national statistic with route; C derived, proxy, EU or regional factor; D model estimate; E missing"),
               numbers=N, fragments=sorted(J))
    (a.work / "V4_S1_EVIDENCE.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    print(len(N), "numbers")


if __name__ == "__main__":
    main()
