"""S4A-1 (L14, decisions 70-73): registry fragment `renewable_s4a.csv` - cutout source, profile chain parameters, PyPSA-Eur
alignment switch, external capacity-factor references (IRENA RPGC 2024, Global Wind Atlas 3.3), method validation metrics and
the PROPOSED corrections (GWA bias scaling, modern turbines, floating offshore, typhoon class). Values come from the files written
by s4a_profiles.py / s4a_1_export.py / s4a_1_compare.py; nothing is estimated here.

    python scripts_project/s4a_1_data.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256, write_json

SCRIPT = "scripts_project/s4a_1_data.py"
RV = ROOT / "research_inputs/renewable_v5"
AN = ROOT / "results_project/s4a/analysis"
CUTOUT_ZIP_SHA = "028ae70154a9a84a696f96788fdf97ecde52ebc16a9c011cd30ebc3567f706df"
CUTOUT_NC_SHA = "eaa033a328f39c82bbd4c46f74d72b19b7c7f2fcc1056e10b5cdf3a05f0d6f05"
IRENA_SHA = "ffe8ce4bde29616f3edf9ef1a86dbb6ae2d5381a0ecb9bb1f71bb20204b6bada"
PE_CFG = ROOT / "research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml"
ISO3 = {"BN": "BRN", "KH": "KHM", "ID": "IDN", "LA": "LAO", "MM": "MMR", "MY": "MYS", "PH": "PHL", "SG": "SGP", "TH": "THA", "TL": "TLS", "VN": "VNM"}


def main():
    reg = Registry(SCRIPT)
    pe_sha = sha256(PE_CFG)
    man = json.loads((RV / "MANIFEST.json").read_text())
    reg.add("renewable_cutout_source", "ERA5 2013 atlite cutout for the ASEAN region: PyPSA-Earth Weather Databundle of ASEAN v1 (bundle_cutouts_asean), 175 x 146 cells at 0.3 deg, 89.7-141.9E / -14.4-29.1N, 8,760 hourly steps, 15 variables; "
            "identical grid and values to the author tutorial cutout (8 cells x 4 times x 5 variables, max abs diff 0); weather year 2013 = load / hydro / electric-base year",
            "cutout-2013-era5.nc", "file", "A", "PyPSA-meets-Earth & Andreyana A.M.V. (2026) PyPSA-Earth Weather Databundle of ASEAN v1, Zenodo, CC BY 4.0; ERA5 (C3S CDS, doi:10.24381/cds.adbb2d47)",
            "https://doi.org/10.5281/zenodo.20325289 ; raw11/bundle_cutouts_asean.zip (MD5 78a3525403077ef69d6078552722ca75)", f"zip:{CUTOUT_ZIP_SHA}|nc:{CUTOUT_NC_SHA}", decision_ref="70-73,L14")
    reg.add("renewable_profile_variant", "Main availability-profile variant (S4A-1.4A, PyPSA-Eur alignment): pypsa_eur = rebuilt with the PyPSA-Eur v2025.07.0 renewable defaults (offshore NREL_ReferenceTurbine_2020ATB_5.5MW @120 m, correction 0.8855; "
            "solar CSi latitude-optimal without the 0.854337 correction; onshore Vestas_V112_3MW @80 m unchanged); original = author profiles inherited by the electric base (comparison); fork = rebuilt with the pypsa-asean defaults (method check)",
            "pypsa_eur", "flag", "B", "S4A instruction S4A-1.4 / PyPSA-Eur v2025.07.0 config.default.yaml renewable block", "configs/research/baseline.yaml research.renewable.profile_variant; PyPSA-Eur config lines 179-275", pe_sha, decision_ref="70-73,L14")
    reg.add("renewable_resource_classes", "PyPSA-Eur resource_classes mechanism: number of per-node capacity-factor classes; 1 = PyPSA-Eur default (one profile per node, main); N > 1 splits the node p_nom_max by class potential (sensitivity, S4A_PROFILE_CLASSES_c3.csv)",
            1, "count", "B", "PyPSA-Eur v2025.07.0 config.default.yaml", "lines 187, 208, 227 (resource_classes: 1); build_renewable_profiles.py ~189-238", pe_sha, decision_ref="70-73,L14", sensitivity_low=1, sensitivity_high=3)
    for tech, turb, hub, src in [("onwind", "Vestas_V112_3MW", 80.0, "atlite 0.4.1 resources/windturbine/Vestas_V112_3MW.yaml (hub_height 80, 3.06 MW)"), ("offwind_fork", "NREL_ReferenceTurbine_5MW_offshore", 90.0, "atlite 0.4.1 NREL_ReferenceTurbine_5MW_offshore.yaml (hub_height 90, 5 MW)"),
                                 ("offwind_pypsa_eur", "NREL_ReferenceTurbine_2020ATB_5.5MW", 120.0, "atlite 0.4.1 NREL_ReferenceTurbine_2020ATB_5.5MW.yaml (hub_height 120, 5.5 MW)")]:
        import atlite, os
        yml = Path(os.path.dirname(atlite.__file__)) / "resources" / "windturbine" / (turb + ".yaml")
        reg.add(f"renewable_turbine_hub_height_{tech}", f"{turb}: hub height used by the atlite log-law extrapolation from the ERA5 100 m wind speed (atlite convert.py 564-592, wind.py 24-110)", hub, "m", "A", src, "yaml key hub_height", sha256(yml), decision_ref="70-73,L14", status="REFERENCE_ONLY")
    reg.add("renewable_correction_factor_solar_fork", "Solar correction factor of the original chain (pypsa-asean config.default.yaml line 418, Pietzcker et al. 2014 full-load-hour calibration); not applied in PyPSA-Eur (line 271 commented) and therefore not in the pypsa_eur variant",
            0.854337, "ratio", "B", "pypsa-asean config.default.yaml / author network meta.renewable.solar.correction_factor", "config.default.yaml:412-418", pe_sha, decision_ref="70-73,L14", status="SENSITIVITY")
    reg.add("renewable_correction_factor_offwind_pypsa_eur", "Offshore wind wake-loss proxy applied in PyPSA-Eur (config lines 210, 229, 249; Bosch et al. 2018, doi:10.1016/j.energy.2018.08.153); absent (commented) in the original chain", 0.8855, "ratio", "B",
            "PyPSA-Eur v2025.07.0 config.default.yaml", "lines 210, 229, 249", pe_sha, decision_ref="70-73,L14")
    for k, v in man.items():
        reg.add(f"renewable_profile_file_{k.replace('.nc', '').replace('profiles_', '')}", f"Rebuilt 3 h availability profiles {k} (buses per technology {v['buses']}); scripts_project/s4a_profiles.py + s4a_1_export.py", k, "file", "B",
                "scripts_project/s4a_profiles.py (atlite 0.4.1, ASEAN ERA5 2013 cutout, author exclusion layout reused, coverage-normalised cell weights)", "research_inputs/renewable_v5", v["sha256"], decision_ref="70-73,L14")
    # validation metrics
    val = json.loads((AN / "S4A_PROFILE_METHOD_VALIDATION_TUTORIAL_WEEK_v2.json").read_text()); val_sha = sha256(AN / "S4A_PROFILE_METHOD_VALIDATION_TUTORIAL_WEEK_v2.json")
    for tech, m in val.items():
        reg.add(f"renewable_method_validation_week_{tech.replace('-', '_')}", f"Method reproduction on the author tutorial week (2013-03-01..07, 1,852 unclustered author regions, author potential layout): capacity-weighted CF rebuilt {m['cap_weighted_cf_mine']:.4f} vs author {m['cap_weighted_cf_theirs']:.4f}; "
                f"median correlation {m['corr_median']:.4f} (p10 {m['corr_p10']:.3f}); mean abs diff {m['mean_abs_diff']:.4f}", m["corr_median"], "correlation", "B", "scripts_project/s4a_profiles.py method vs resources/baseline-aims-3H-tutorial/renewable_profiles",
                "results_project/s4a/analysis/S4A_PROFILE_METHOD_VALIDATION_TUTORIAL_WEEK_v2.json", val_sha, decision_ref="70-73,L14", status="REFERENCE_ONLY")
    cmp = json.loads((AN / "S4A_PROFILE_COMPARISON.json").read_text()); cmp_sha = sha256(AN / "S4A_PROFILE_COMPARISON.json")
    for tech in ["onwind", "offwind-ac", "offwind-dc", "solar"]:
        o = cmp[tech]["overall"]
        reg.add(f"renewable_rebuild_vs_original_{tech.replace('-', '_')}", f"Full-year node-level check: mean CF original {o['cf_original']:.4f}, fork rebuild {o['cf_fork']:.4f} (median corr {o['corr_fork_median']:.4f}, p10 {o['corr_fork_p10']:.3f}, median MAE {o['mae_fork_median']:.4f}), pypsa_eur {o['cf_pypsa_eur']:.4f}",
                o["cf_pypsa_eur"], "capacity factor", "B", "scripts_project/s4a_1_compare.py", "results_project/s4a/analysis/S4A_PROFILE_COMPARISON.json", cmp_sha, decision_ref="70-73,L14", status="REFERENCE_ONLY")
    # external references
    reg.add("renewable_cf_irena2024_onshore_other_asia", "IRENA RPGC 2024 Table 2.3 (PDF p.78): onshore wind weighted-average capacity factor of newly commissioned projects, region Other Asia (ASEAN countries are in the Asia group, Annex III PDF p.215): 2024 weighted average 39 %, 5th-95th percentile 24-47 %; 2010: 26 % (22-32 %)",
            0.39, "fraction", "A", "IRENA (2025) Renewable Power Generation Costs in 2024", "Table 2.3, PDF p.78; Annex III PDF p.215", IRENA_SHA, decision_ref="70-73,L14", sensitivity_low=0.24, sensitivity_high=0.47, status="REFERENCE_ONLY")
    for c, lo, hi, last in [("ID", 0.26, 0.38, 0.32), ("PH", 0.27, 0.35, 0.35), ("VN", 0.32, 0.43, 0.42)]:
        reg.add(f"renewable_cf_irena2024_onshore_{c}", f"IRENA RPGC 2024 Figure 2.12 (PDF p.79, line chart, no printed values): {c} onshore wind weighted-average capacity factor of new projects read from the 330 dpi rendering: range about {lo:.0%}-{hi:.0%}, latest point about {last:.0%} (+-2 pp reading uncertainty, grade C)",
                last, "fraction", "C", "IRENA (2025) Renewable Power Generation Costs in 2024", "Figure 2.12, PDF p.79 (read from figure)", IRENA_SHA, country=c, decision_ref="70-73,L14", sensitivity_low=lo, sensitivity_high=hi, status="REFERENCE_ONLY")
    reg.add("renewable_cf_irena2024_solar_global", "IRENA RPGC 2024 Table 3.2 (PDF p.99): utility-scale PV weighted-average capacity factor of projects commissioned in 2024, global (AC/DC basis): 17.4 %, 5th-95th percentile 11.5-22.6 %; no country table",
            0.174, "fraction", "A", "IRENA (2025) Renewable Power Generation Costs in 2024", "Table 3.2, PDF p.99", IRENA_SHA, decision_ref="70-73,L14", sensitivity_low=0.115, sensitivity_high=0.226, status="REFERENCE_ONLY")
    reg.add("renewable_cf_irena2024_offshore_countries", "IRENA RPGC 2024 Table 4.3 (PDF p.123): offshore wind capacity factors 2024 for China 37, Denmark 52, France 44, Germany 46, Japan 37, Netherlands 49, UK 52 %; no ASEAN country listed",
            "no ASEAN value", "fraction", "A", "IRENA (2025) Renewable Power Generation Costs in 2024", "Table 4.3, PDF p.123", IRENA_SHA, decision_ref="70-73,L14", status="REFERENCE_ONLY")
    gwa = pd.read_csv(AN / "GWA_COUNTRY_STATS.csv"); gwa_sha = sha256(AN / "GWA_COUNTRY_STATS.csv")
    for c, iso3 in ISO3.items():
        r2 = gwa[(gwa.iso3 == iso3) & (gwa.layer == "capacity-factor_IEC2")].iloc[0]; r3 = gwa[(gwa.iso3 == iso3) & (gwa.layer == "capacity-factor_IEC3")].iloc[0]; ws = gwa[(gwa.iso3 == iso3) & (gwa.layer == "wind-speed_100")].iloc[0]
        reg.add(f"renewable_gwa33_onshore_cf_{c}", f"Global Wind Atlas 3.3 country layer (250 m, land cells {int(r2.cells):,}): capacity factor at 100 m hub height, IEC class 2 reference turbine: mean {r2['mean']:.3f}, median {r2.p50:.3f}, p90 {r2.p90:.3f}; IEC3 mean {r3['mean']:.3f}; "
                f"100 m wind speed mean {ws['mean']:.2f} m/s; share of land with IEC2 CF > 0.30: {r2.share_gt_0p30:.1%}", float(r2["mean"]), "fraction", "A",
                "Global Wind Atlas 3.3 (DTU / World Bank), public GIS API, fetched 2026-10-16", f"https://globalwindatlas.info/api/gis/country/{iso3}/capacity-factor_IEC2 (and IEC1, IEC3, wind-speed/100)", gwa_sha, country=c,
                decision_ref="70-73,L14", sensitivity_low=float(r2.p10), sensitivity_high=float(r2.p90), status="REFERENCE_ONLY")
    # proposals (not implemented)
    reg.add("renewable_proposed_gwa_bias_scaling", "PROPOSED (S4A-1.4B, not implemented): scale the ERA5 100 m wind speed per cell by GWA 100 m mean wind speed / ERA5 2013 mean before the power curve (PyPSA-Eur community bias correction, not a default); expected onshore CF VN/PH 0.25-0.35, ID/TH 0.10-0.20 (INFERENCE)",
            "not_applied", "flag", "C", "S4A report section 1.4", "scripts_project/s4a_profiles.py (switch absent on purpose)", gwa_sha, decision_ref="70-73,L14", status="CANDIDATE_ONLY")
    reg.add("renewable_proposed_typhoon_class", "PROPOSED (decision 3, ASEAN-specific): typhoon (IEC 61400-1 Tropical T-Class, Vref 57 m/s) cost premium +20-30 % on wind candidates in high tropical-cyclone-frequency zones (PH, northern/central VN coast, northern South China Sea) or exclusion by IBTrACS strike frequency; not implemented",
            0.25, "ratio", "C", "Tarp-Johansen & Clausen (2006) Design of Wind Turbines in Typhoon area, EC-ASEAN Energy Facility (cost +20-30 % vs IEC 61400-1); BSEE (2011) TAP 670AA (load factor +25-50 % for Philippine typhoon regions); Deskos et al. (2026) Wind Energy Science 11:2749-2782 (T-Class Vref 57 m/s)",
            "DTU report p.1 summary / section 7; BSEE report section 2 (Garciano & Koike 2007, 2010)", "dtu:5e4223d639fa1874de097ebc0b1f70eae3ad8727558903239362ed72c7a23a91|bsee:a111e963936f45e7a81f5bb48af14f8ab6b4cd0a8a73adc9d0326659cae6212a",
            decision_ref="3,70-73,L14", sensitivity_low=0.2, sensitivity_high=0.3, status="CANDIDATE_ONLY")
    reg.add("renewable_offshore_depth_rule", "Fixed-bottom offshore candidates: water depth <= 50 m (pypsa-asean config.default.yaml lines 380, 399; GEBCO) vs PyPSA-Eur 60 m (config lines 215, 234), shore distance 30 km split AC/DC in both; no shipping-lane exclusion and no floating class in the model (PyPSA-Eur: ship_threshold 400, floating 60-1,000 m)",
            50.0, "m", "B", "pypsa-asean config.default.yaml / PyPSA-Eur v2025.07.0 config.default.yaml", "lines 380, 399 / 215, 234, 257-258", pe_sha, decision_ref="70-73,L14", status="REFERENCE_ONLY")
    reg.add("renewable_ship_density_raster", "Global shipping density raster for the PyPSA-Eur ship_threshold exclusion (not in the ASEAN data intake)", None, "file", "A", "PyPSA-Eur data bundle (shipdensity_global.zip)", "download list", pe_sha, decision_ref="70-73,L14", status="DATA_PENDING")
    reg.write(REG_DIR / "fragments" / "renewable_s4a.csv")
    write_json(dict(script=SCRIPT, rows=len(reg.rows), manifest=man), RV / "RENEWABLE_S4A_EVIDENCE.json")
    print("rows", len(reg.rows))


if __name__ == "__main__":
    main()
