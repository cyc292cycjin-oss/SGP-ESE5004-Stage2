"""G5 summary: country table, ID longitude-rule comparison and EVIDENCE.json (key, value, unit, source, status, grade). Read-only.

    python g5_summary.py --g5 <G5 dir>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--g5", type=Path, required=True); a = ap.parse_args()
    g, ev = a.g5, a.g5 / "evidence"
    probe = json.loads((ev / "G5_PROBE_NETWORK.json").read_text()); prof = json.loads((ev / "G5_PROFILES.json").read_text(encoding="utf-8"))
    peaks = json.loads((ev / "G5_PEAKS.json").read_text())
    O = pd.read_csv(ev / "G5_PEAK_IMPACT.csv"); TT = pd.read_csv(ev / "G5_PEAK_IMPACT_ASEAN.csv"); C = pd.read_csv(ev / "G5_INDUSTRY_COMPOSITION.csv")
    TZ = pd.read_csv(g / "TIMEZONE_NODES.csv"); S = pd.read_csv(ev / "G5_SHAPE_STATS.csv"); M = pd.read_csv(g / "PROFILE_MAPPING.csv")
    sol = pd.read_csv(ev / "G5_SOLAR_PEAK_HOUR_1H.csv"); H = pd.read_csv(ev / "G5_HEAT_PEAKS.csv")
    # ---- country summary (electricity)
    me = M[M.etype == "elec"].set_index("subsector").shape_main
    ce = C[C.etype == "elec"].copy(); ce["main_shape"] = ce.key.map(me)
    rows = []
    for c, q in ce.groupby("country"):
        tot = q.mwh.sum(); o = O[O.country == c].set_index("variant")
        rows.append(dict(country=c, industry_elec_2050_twh=tot / 1e6, share_flat_main=q[q.main_shape == "FLAT"].mwh.sum() / tot,
                         share_other=q[q.key == "other"].mwh.sum() / tot, share_shaped_rows=q[(q.main_shape != "FLAT") & (q.key != "other")].mwh.sum() / tot,
                         main_peak_over_mean_1h=o.at["MAIN", "peak_over_mean_1h"], main_peak_over_mean_3h=o.at["MAIN", "peak_over_mean_3h"],
                         main_peak_over_mean_daily=o.at["MAIN", "peak_over_mean_daily"], main_industry_peak_change_3h_gw=o.at["MAIN", "peak_change_3h_gw"],
                         industry_share_of_ac_fixed_energy=o.at["MAIN", "industry_share_of_ac_fixed_energy"],
                         main_ac_fixed_peak_change_gw=o.at["MAIN", "ac_fixed_load_peak_change_gw"], main_ac_fixed_peak_change_pct=o.at["MAIN", "ac_fixed_load_peak_change_pct"],
                         min_ac_change_pct=o.drop(index="FLAT").ac_fixed_load_peak_change_pct.min(), min_ac_change_variant=o.drop(index="FLAT").ac_fixed_load_peak_change_pct.idxmin(),
                         max_ac_change_pct=o.drop(index="FLAT").ac_fixed_load_peak_change_pct.max(), max_ac_change_variant=o.drop(index="FLAT").ac_fixed_load_peak_change_pct.idxmax(),
                         s2_other_flat_ac_change_pct=o.at["S2_OTHER_FLAT", "ac_fixed_load_peak_change_pct"], s8_upper_ac_change_pct=o.at["S8_UPPER", "ac_fixed_load_peak_change_pct"],
                         main_heat_peak_over_mean_3h=float(H[(H.country == c) & (H.variant == "MAIN")].peak_over_mean_3h.iloc[0]) if ((H.country == c) & (H.variant == "MAIN")).any() else np.nan))
    CS = pd.DataFrame(rows); CS.to_csv(ev / "G5_COUNTRY_SUMMARY.csv", index=False, float_format="%.4f")
    # ---- ID: legal (province) zone vs nearest-meridian longitude rule (boundaries 112.5 E and 127.5 E)
    idn = TZ[TZ.country == "ID"].copy()
    idn["lon_rule_tz"] = np.select([idn.x < 112.5, idn.x < 127.5], [7.0, 8.0], 9.0)
    diff = idn[idn.lon_rule_tz != idn.utc_offset_h]
    diff[["node", "province", "x", "utc_offset_h", "lon_rule_tz", "industry_electricity_2050_twh_v3"]].to_csv(ev / "G5_ID_LONGITUDE_RULE_DIFF.csv", index=False, float_format="%.4f")
    # ---- evidence
    E = []
    def add(key, value, unit, source, status, grade="", note=""):
        E.append(dict(key=key, value=value, unit=unit, source=source, status=status, grade=grade, note=note))
    sn = probe["snapshots"]
    add("network_sha256", probe["network_sha256"], "", "v3.1 F1 integrated_2920_3h_unsolved.nc (package copy)", "VERIFIED", "", "same file as V3 HPC package F1")
    add("snapshots", f'{sn["n"]} x {sn["step_h"]:g} h, {sn["first"]} .. {sn["last"]}, tz={sn["tz"]}', "", "evidence/G5_PROBE_NETWORK.json", "VERIFIED")
    add("snapshot_clock", "UTC", "", "evidence/G5_SOLAR_PEAK_HOUR_NETWORK.csv, G5_SOLAR_PEAK_HOUR_1H.csv, G5_ELEC_LOAD_CYCLE.csv", "VERIFIED", "",
        "network solar peak in snapshot 03 or 06 UTC for all 11 countries; base electricity peak in snapshot 09-12 UTC (local evening)")
    d = (sol.centroid_hour - sol.utc_solar_noon_h)
    add("solar_1h_centroid_minus_utc_noon_median_h", float(d.median()), "h", "evidence/G5_SOLAR_PEAK_HOUR_1H.csv (287 bus classes)", "VERIFIED", "",
        "a local clock would give about +7 h; the ~0.5 h left after the +0.5 h interval convention fits ERA5 accumulation labels at the end of the hour (INFERENCE)")
    add("solar_1h_centroid_minus_utc_noon_p05_p95_h", [float(d.quantile(0.05)), float(d.quantile(0.95))], "h", "evidence/G5_SOLAR_PEAK_HOUR_1H.csv", "VERIFIED")
    add("industry_loads_static", f'{probe["loads"]["total"]} loads, {probe["loads"]["with_ts"]} with time series ({", ".join(probe["loads"]["ts_carriers"])})', "",
        "evidence/G5_LOAD_CARRIERS.csv", "VERIFIED", "", "industry loads are per node x carrier, not per subsector")
    ft = prof["ffe_tests"]
    add("ffe_day_alignment_offset", ft["day_alignment"]["labelling_offset_best"], "days", "FfE 59 curve 13", "VERIFIED", "", "0 = file day 0 is 2017-01-01 (Sunday)")
    add("ffe_holiday_days_detected", ft["holiday_days"]["n"], "days", "evidence/G5_FFE_HOLIDAY_DAYS.csv", "VERIFIED", "",
        f'{ft["holiday_days"]["matched_german_holidays"]} of them are German holidays 2017 (holiday list from memory: INFERENCE)')
    add("ffe_clock_test_lags", {k: v["best_lag_summer_to_winter_h"] for k, v in ft["clock"].items()}, "h", "evidence/G5_PROFILES.json ffe_tests.clock", "VERIFIED", "",
        "lag 0 = same index hours in winter and summer; verdict: " + ft["clock_verdict"])
    add("ffe_clock_main", "German local clock (CET/CEST)", "", "S0 6.4 proposal; clock test inconclusive", "PROPOSED", "C", "UTC reading = sensitivity S4")
    add("ffe_licence", "CC-BY-4.0, attribution '© FfE, eXtremOS Project'; citation 'Normalized Industrial Electrical Load Profiles (Germany): <URL>; München: FfE München, 2021'",
        "", "metadata JSON on disk + https://opendata.ffe.de/dataset/normalized-industrial-electrical-load-profiles-germany/ (read 2026-11-06)", "VERIFIED")
    add("nrel_licence", "DOE/NREL/ALLIANCE data licence (not Creative Commons): free use and copying; credit DOE/NREL/ALLIANCE in publications; the notice must appear in all copies of the Data",
        "", "https://data.nlr.gov/node/118/license (read 2026-11-06); dataset 'Manufacturing Thermal Energy Use in 2014', McMillan 2019, DOI 10.7799/1570008", "VERIFIED")
    add("nrel_dayofweek_convention", "0 = Monday", "", "parquet weekday_single schedules lower on 5 and 6", "VERIFIED")
    for _, r in S[S["shape"].isin(["FFE_NONSPEC", "FFE_FOOD", "FFE_NMM", "FFE_TRANSPORT_MACH", "FFE_MINING", "FFE_STEEL_PAPER", "NREL_ALL", "MIX_DISPERSED_elec", "MIX_DISPERSED_heat"])].iterrows():
        add(f"shape_{r['shape']}_peak_over_mean", float(r.peak_over_mean), "-", "evidence/G5_SHAPE_STATS.csv (168-h local week, season removed)", "EXACT", "C")
        add(f"shape_{r['shape']}_weekday_over_weekend", float(r.weekday_over_weekend), "-", "evidence/G5_SHAPE_STATS.csv", "EXACT", "C")
        if r["shape"].startswith("FFE") and r.removed_month_max_over_min == r.removed_month_max_over_min:
            add(f"shape_{r['shape']}_removed_month_max_over_min", float(r.removed_month_max_over_min), "-", "FfE 2017 monthly means", "EXACT", "C")
    add("mix_dispersed_weights", prof["mix_dispersed_weights"], "share", "S0 evidence/V3_DISPERSED_BY_UNSD_ROW.csv (v3 2050 dispersed energy by PyPSA-Eur sector)", "EXACT", "D",
        "row energy of all carriers used as weight for electricity and heat (INFERENCE)")
    add("profiles_distinct_curves", prof["profiles"]["curves"], "curves", "PROFILES_8760.parquet", "EXACT")
    add("profiles_max_abs_mean_minus_1", prof["profiles"]["max_abs_mean_minus_1"], "-", "PROFILES_8760.parquet", "EXACT")
    add("profiles_variants", prof["profiles"]["variants"], "", "PROFILE_INDEX.csv", "PROPOSED")
    tz = prof["timezones"]
    add("tz_nodes_by_offset", tz["by_offset"], "nodes", "TIMEZONE_NODES.csv (EV_NODE_TIMEZONE_V3.csv, decision 165)", "VERIFIED")
    add("tz_province_rule_failures", tz["checks_failed"], "nodes", "TIMEZONE_NODES.csv vs Keppres 41/1987 province list (list from memory: INFERENCE)", "VERIFIED")
    add("tz_id_multi_zone_nodes", tz["id_nodes_multi_tz_area"], "nodes", "ADM1_NODE_OVERLAP_V3.csv", "VERIFIED", "", f'{tz["id_multi_tz_industry_elec_twh"]:.2f} TWh v3 2050 industry electricity in them')
    add("tz_id_longitude_rule_differs", int(len(diff)), "nodes", "evidence/G5_ID_LONGITUDE_RULE_DIFF.csv", "EXACT", "", "nearest-meridian rule (112.5 / 127.5 E) vs legal province zone")
    add("composition_check_max_abs_diff_mwh", float(max(abs(r["diff_mwh"]) for r in peaks["composition_check"])), "MWh",
        "evidence/G5_PEAKS.json composition_check (v3 table electricity vs network 'industry electricity', by country and ID zone)", "EXACT")
    for _, r in CS.iterrows():
        add(f"{r.country}_industry_elec_2050_twh", float(r.industry_elec_2050_twh), "TWh", "v3 INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv main", "VERIFIED", "C")
        add(f"{r.country}_main_industry_peak_over_mean_1h_3h_daily", [round(float(r.main_peak_over_mean_1h), 4), round(float(r.main_peak_over_mean_3h), 4), round(float(r.main_peak_over_mean_daily), 4)],
            "-", "evidence/G5_PEAK_IMPACT.csv", "PROPOSED", "C")
        add(f"{r.country}_main_ac_fixed_peak_change", [round(float(r.main_ac_fixed_peak_change_gw), 3), round(float(r.main_ac_fixed_peak_change_pct), 2)], "GW, %",
            "evidence/G5_PEAK_IMPACT.csv (3 h, base electricity + agriculture + industry)", "PROPOSED", "C")
        add(f"{r.country}_ac_change_range_pct", [round(float(r.min_ac_change_pct), 2), round(float(r.max_ac_change_pct), 2)], "%", "evidence/G5_PEAK_IMPACT.csv (9 variants)", "PROPOSED", "C",
            f"{r.min_ac_change_variant} .. {r.max_ac_change_variant}")
    for _, r in TT.iterrows():
        add(f"ASEAN_{r.variant}_ac_fixed_peak_change_gw", round(float(r.ac_fixed_peak_change_gw), 3), "GW", "evidence/G5_PEAK_IMPACT_ASEAN.csv (coincident, 3 h)", "PROPOSED", "C")
    add("ASEAN_flat_ac_fixed_peak_gw", round(float(TT.ac_fixed_peak_3h_gw.iloc[0]), 3), "GW", "evidence/G5_PEAK_IMPACT_ASEAN.csv", "VERIFIED", "C")
    keys = [e["key"] for e in E]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate evidence keys")
    (g / "EVIDENCE.json").write_text(json.dumps(dict(session="V4 W07 G5", instruction_sha256="20d03b692f1d32733f34b04d85c01fb3df1345f95f366a6bf25de36ac7ec7baf",
                                                     solver_runs=0, entries=E), indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    print(CS.round(3).to_string()); print(diff[["node", "province", "x", "utc_offset_h", "lon_rule_tz", "industry_electricity_2050_twh_v3"]].round(2).to_string()); print(len(E), "evidence entries")


if __name__ == "__main__":
    main()
