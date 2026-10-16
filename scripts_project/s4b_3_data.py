"""S4B-3 registry fragment (decisions 74, 75): observed onshore-wind CF, calibration factors, turbines, profile variant, limitations.

    python scripts_project/s4b_3_data.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256

SCRIPT = "scripts_project/s4b_3_data.py"
RV = ROOT / "research_inputs/renewable_v5"
EMBER_SHA = "b2ac49fa9b27035fedda3c6afb85917bf136de9253bfcbaf09c3410904ec7cd1"
DEA_XLSX_BLOB = "ce07675ba570a3b6376910505bd2bebcf163c0ba"
VN_CURTAILMENT = ("no quantified wind curtailment for VN 2020-2022 found; public sources describe transmission congestion and curtailment of wind and solar in 2021-2022 "
                  "(IUCN Viet Nam news 2022-05 'Grid integration for renewable energy'; Energy Transition Partnership 2024 'Managing Vietnam's Grid Issues for Effective Energy Transition'); "
                  "the only quantified figure seen is about 1.3 TWh of solar not dispatched in 2021 (search summaries, grade C)")


def main():
    A = pd.read_csv(RV / "WIND_CALIBRATION_ALPHA.csv").set_index("country"); S = pd.read_csv(RV / "WIND_OBSERVED_CF_SUMMARY.csv").set_index("country")
    ev = json.loads((RV / "WIND_CALIBRATION_S4B3.json").read_text()); dea = ev["turbines"]["dea2050_synthetic"]
    reg = Registry(SCRIPT); a_sha = sha256(RV / "WIND_CALIBRATION_ALPHA.csv")
    for c, r in S.iterrows():
        if not np.isfinite(r.cf_obs_median_main):
            continue
        reg.add(f"onwind_observed_cf_ember_{c}", f"Observed wind capacity factor {c}: median of {int(r.valid_years_main)} valid years ({r.years_main}) of Ember generation / (8,760 h x mean of current and previous year capacity); "
                f"growth > 50 % years dropped" + ("; VN 2020-2022 curtailment period dropped (" + VN_CURTAILMENT + ")" if c == "VN" else "") + ("" if r.calibrate else "; below 200 MW -> not calibrated on its own"),
                float(r.cf_obs_median_main), "p.u.", "B", "Ember yearly electricity data (CC BY 4.0), release_generation_yearly_global.csv", "WIND_OBSERVED_CF_EMBER_2019_2025.csv", EMBER_SHA, country=c, decision_ref="74")
    for c, r in A.iterrows():
        cal = r.calibrated_individually and np.isfinite(r.alpha_nrel_atb2020_4mw)
        reg.add(f"onwind_alpha_{c}", f"ERA5 100 m wind-speed calibration factor {c} (Staffell & Pfenninger 2016): " + (f"model CF at the {int(r.farms)} GEM farms with the NREL ATB 2020 4 MW turbine {r.cf_model_alpha1_nrel_atb2020_4mw:.3f} -> observed {r.cf_obs:.3f}; "
                f"V112 comparison alpha {r.alpha_vestas_v112:.3f}" if cal else "capacity-weighted alpha of PH / TH / VN (not calibrated on its own)"), float(r.alpha_main), "factor", ("B" if cal else "C"),
                "S4B-3 calibration (scripts_project/s4b_3_wind_calibration.py)", "WIND_CALIBRATION_ALPHA.csv", a_sha, country=c,
                sensitivity_low=(None if cal else float(A.loc[A.calibrated_individually, "alpha_main"].min())), sensitivity_high=(None if cal else float(A.loc[A.calibrated_individually, "alpha_main"].max())), decision_ref="74")
    reg.add("onwind_calibration_turbine", "Calibration turbine at the existing farms: atlite NREL_ReferenceTurbine_2020ATB_4MW (4 MW, rotor 150 m, 226 W/m2, hub 110 m), low-specific-power reference comparable to 2018-2022 low-wind turbines; "
            "GEM carries no wind turbine model; Vestas V112 (310.6 W/m2, hub 80 m) reported as comparison; alpha absorbs turbine differences (limitation)", "NREL_ReferenceTurbine_2020ATB_4MW", "turbine", "C",
            "atlite 0.4.1 resources/windturbine", "NREL_ReferenceTurbine_2020ATB_4MW.yaml", a_sha, decision_ref="74", status="REFERENCE_ONLY")
    reg.add("onwind_new_turbine_dea2050", f"New onshore turbine = technology-data v0.15.0 onwind 2050 cited DEA data sheet '20 Onshore turbines' (inputs/technology_data_for_el_and_dh.xlsx git blob {DEA_XLSX_BLOB}, 2022-03-17): "
            f"6 MW, rotor 165 m, hub 110 m, {dea['specific_power_w_m2']:.1f} W/m2; power curve = V112 per-unit curve with partial-load wind speeds x {dea['wind_speed_scale']:.4f} (specific-power scaling), cut-out 25 m/s; "
            "DEA August 2026 edition (comparison): 2050 specific power ~280.6 W/m2, hub 110 m, 3,800 full-load hours (Fig. 24, identical); unit capacity / rotor not given in that PDF", 6.0, "MW", "B",
            "DEA Technology Data for Generation of Electricity and District Heating (sheet cited by technology-data v0.15.0)", "sheet 20 Onshore turbines rows 5, 26-28 (2050 column)", DEA_XLSX_BLOB, decision_ref="74")
    reg.add("renewable_profile_variant_s4b3", "research.renewable.profile_variant = calibrated_modern (main): onshore wind = ERA5 100 m speed x alpha_main + DEA 2050 turbine; offshore / solar = pypsa_eur; pypsa_eur (V112 uncalibrated) = lower-bound comparison",
            "calibrated_modern", "flag", "B", "S4B instruction S4B-3 item 5", "configs/research/baseline.yaml research.renewable", a_sha, decision_ref="74")
    reg.add("renewable_resource_classes_s4b3", "research.renewable.resource_classes = 3 (main, decision 75); 1 = comparison", 3, "classes", "B", "S4B instruction S4B-3 item 5 (decision 75)", "configs/research/baseline.yaml research.renewable", a_sha, decision_ref="75")
    reg.add("onwind_gwa_crosscheck_s4b3", "Cross-check only (no network variant): alpha_GWA = GWA 3.3 country land-mean 100 m speed / ERA5 2013 land mean (1.10-1.89); with the DEA turbine the best class would exceed GWA p90 / IRENA in PH, VN, TL",
            None, "flag", "C", "GWA 3.3 country statistics (S4A-1 section 1.3)", "ONWIND_CF_CHECK_S4B3.csv", a_sha, decision_ref="74", status="REFERENCE_ONLY")
    reg.add("onwind_calibration_limitations_s4b3", "Limitations: observed years (2019-2025) differ from the 2013 weather year (inter-annual +-5-10 %); with unknown turbines alpha absorbs turbine differences; offshore wind has no observation and is not calibrated; "
            "Ember does not split onshore / intertidal (VN intertidal farms included); farm cells at 0.3 deg", None, "flag", "C", "S4B instruction S4B-3 item 3", "WIND_CALIBRATION_S4B3.json", a_sha, decision_ref="74", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4b_3.csv")
    print(len(reg.rows), "rows")


if __name__ == "__main__":
    main()
