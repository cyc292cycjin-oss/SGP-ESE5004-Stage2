"""V4 D2b section 4: DATA_UPGRADES.csv from evidence/DATA_UPGRADES_CALC.json (scripts/d2b_data_upgrades.py) - one row per item / parameter: old value, new value
(v4 main), range registered, sources (evidence ids), grade, verdict, where it acts. No solver.

    python scripts/d2b_data_upgrades_table.py
"""
import csv
import json
from pathlib import Path

W = Path(__file__).resolve().parents[1]


def main():
    c = json.loads((W / "evidence/DATA_UPGRADES_CALC.json").read_text())
    L, S, E, A, R, Wc, Y, ST = c["lng"], c["co2_ship"], c["ev_ice"], c.get("vn_offwind_alpha", {}), c["my_rooftop"], c["wacc"], c["co2_sequestration_price_year"], c["co2_storage_potential"]
    am = A.get("alpha_cf_match", {})
    alpha = sorted([am[k]["alpha_box"] for k in ("pecc3_binh_thuan_net", "tc2021_fixed_2050_incl_outages", "wb_roadmap_2050_net")]) if am else [None] * 3
    rows = [
        dict(item="4.1", parameter="fuel_price_lng_regasification_adder -> v4_lng_regas_adder_asean_tariffs", unit="EUR2020/MWh", old_value=1.26, new_value=round(L["value"], 6),
             range_low=round(L["low"], 6), range_high=round(L["high"], 6), status="REPLACED (v4 main; switch lng_regas_adder = asean_tariffs, v3.1 fallback m08a = 1.26)",
             sources="D01-D14 (TH ERC 2020; MY ST 2019 / 2025; SG SLNG-EMA FY26; ID Arun 2017)", grade="C", verdict=L["verdict"], acts_on="LNG import marginal cost (s3_layers.add_gas_network)", note=L["caveat"]),
        dict(item="4.2", parameter="co2_ship_chain_fixed_cost", unit="EUR2020/tCO2", old_value=round(S["model"]["fixed"], 6), new_value=round(S["model"]["fixed"], 6), range_low=round(S["fixed_range"][0], 4),
             range_high=round(S["fixed_range"][1], 4), status="KEPT + RANGE", sources="D15-D30 (IEAGHG 2020-10; BEIS 2018; ZEP 2011; ZEP 2024 / Clarksons 2024 / Roussanaly 2021 not read)", grade="C",
             verdict=S["verdict"], acts_on="CO2 ship link marginal cost (s4d_layers)", note=f"chain at 1,000 km: model {S['chain_1000km']['model']:.2f}, IEAGHG 2020 {S['chain_1000km']['ieaghg2020']:.2f}, ZEP T1 {S['chain_1000km']['zep_t1']:.2f}, ZEP T2 {S['chain_1000km']['zep_t2']:.2f} EUR2020/t"),
        dict(item="4.2", parameter="co2_ship_chain_per_km_cost", unit="EUR2020/(tCO2 km)", old_value=S["model"]["slope"], new_value=S["model"]["slope"], range_low=S["slope_range"][0], range_high=S["slope_range"][1],
             status="KEPT + RANGE", sources="D24-D26", grade="C", verdict="slope from one independent source group (ZEP; BEIS derived) and derived by OLS, not stated", acts_on="CO2 ship link marginal cost", note=""),
        dict(item="4.3", parameter="co2_sequestration_cost_price_year", unit="year", old_value="DATA_PENDING", new_value=2020, range_low=2015, range_high=2020, status="DETERMINED (INFERENCE); value 30 EUR/t unchanged",
             sources="D31-D38 (PyPSA-Eur v2025.07.0 config / docs / commit e43746df PR #1753; technology-data v0.13.2 eur_year)", grade="C", verdict=Y["verdict"], acts_on="none (registry only)", note=Y["basis"]),
        dict(item="4.4", parameter="share_transport_electric_efficiency / share_transport_ice_efficiency (fleet ratio)", unit="ratio", old_value=round(E["model_ratio"], 6), new_value=round(E["model_ratio"], 6),
             range_low=round(E["fleet_ratio_low"], 4), range_high=round(E["fleet_ratio_high"], 4), status="KEPT + RANGE (mid %.3f = %+.1f %% of 3.31)" % (E["fleet_ratio_mid"], E["mid_vs_model_pct"]),
             sources="E01-E28 (ITDP 2023; ADB 2022; ADBI WP1025; ERIA 2020 / 2023; IEA-GFEI 2019; ASEAN FE roadmap; Achariyaviriya 2023; Le 2023; IEA 2018)", grade="C", verdict=E["verdict"],
             acts_on="EV land-transport load (ev_load_scale)", note=f"EV efficiency range at ICE 16.0712: {E['ev_eff_range_at_ice_16_0712'][0]:.2f}-{E['ev_eff_range_at_ice_16_0712'][1]:.2f}; electrification share unchanged (scenario)"),
    ]
    for k, z in ST["countries"].items():
        if z.get("low_gt") is None:
            continue
        rows.append(dict(item="4.5", parameter=f"co2_storage_potential_{k} / co2_injection_cap_unified_{k}", unit="GtCO2", old_value=z["p50_gt"], new_value=z["p50_gt"], range_low=z["low_gt"], range_high=z["high_gt"],
                         status="RANGE ONLY (main P50, decision 126)", sources=f"{z['ev']} (ERIA / GCCSI 2024 Ch.1)", grade="B", verdict=ST["verdict"], acts_on="none (registry ranges for W19)",
                         note=f"annual cap range {z['cap_low_t'] / 1e6:.2f}-{z['cap_high_t'] / 1e6:.2f} Mt/a"))
    rows += [
        dict(item="4.5", parameter="co2_storage_potential_PH / KH", unit="GtCO2", old_value="0.0672 / 0.09", new_value="0.0672 / 0.09", range_low="", range_high="", status="NO RANGE", sources="D44, D46, D48 (OGCI not read)", grade="B / C",
             verdict="PH: hydrocarbon fields only, no ERIA range; KH not assessed by ERIA", acts_on="none", note=""),
        dict(item="4.6", parameter="offwind_alpha_calibration_rule (VN)", unit="alpha", old_value="1.0 (DATA_PENDING)", new_value="1.0 (not applied)", range_low=alpha[0], range_high=alpha[2],
             status="COEFFICIENT GIVEN, NOT APPLIED (registry v4_offwind_alpha_vn_reference_area mid %.3f)" % alpha[1] if alpha[1] else "NOT COMPUTED",
             sources="E30-E42 (WB / ESMAP 2021 roadmap; EREA / DEA Technology Catalogue 2021; EVNPECC3 2021); VN_OFFWIND_ALPHA.json", grade="C",
             verdict="S4B-3 rule on the Binh Thuan reference area (ERA5 2013 box mean 9.34 m/s, model turbine x 0.8855: CF 0.583 at alpha 1): alpha matching 50 / 53 / 60 % net CF; one reference area, no zone values, 20 MW+ rotors in the roadmap, WB and TC not fully independent -> not applied",
             acts_on="none (offshore profiles unchanged)", note="speed ratio 8.5 / 9.34 = 0.910; the model's VN capacity-weighted offshore CF AC 0.28 / DC 0.38 / float 0.34"),
        dict(item="4.7", parameter="renewable_cap_built_solar_rooftop_MY", unit="MW", old_value=83146.768938, new_value=83146.768938, range_low=42000.0, range_high=124720.153407,
             status="RANGE ONLY (one source lineage)", sources="E50-E56 (SEDA MyRER 2021 p.39 42 GW; SEDA 2019 34.2 GW / 37.4 GW peninsular; BCG 4.4 GW non-residential)", grade="C", verdict=R["verdict"], acts_on="none (registry range)", note=f"MyRER / model = {R['ratio']:.3f}"),
        dict(item="4.8", parameter="COUNTRY_WACC_REAL_M08A.csv vs uniform 7 %", unit="basis", old_value="", new_value="", range_low="", range_high="", status="NOTE ONLY", sources="E60-E70", grade="C",
             verdict=Wc["verdict"], acts_on="none", note=f"IEA: {Wc['iea']}; table: {Wc['country_table']}; uniform: {Wc['uniform']}"),
    ]
    cols = ["item", "parameter", "unit", "old_value", "new_value", "range_low", "range_high", "status", "sources", "grade", "verdict", "acts_on", "note"]
    with open(W / "DATA_UPGRADES.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader(); [w.writerow(r) for r in rows]
    print(len(rows), "rows")


if __name__ == "__main__":
    main()
