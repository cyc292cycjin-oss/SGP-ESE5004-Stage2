"""V4 D2b (decision 221; V4_D2B_INSTRUCTION.md sections 2-4): registry rows of the D2b data step, assembled into DATA_REGISTRY.csv by scripts_project/d1_registry.py.

    PYTHONHASHSEED=0 python scripts_project/v4_d2b_registry.py && python scripts_project/d1_registry.py

  fragments/v4_d2b.csv              new rows: BIOMASS_BASIS_T05.csv and the T05 potential tables (file rows); oil palm trunk moisture / dry LHV / energy per fresh
                                    tonne (section 2.1); the energy-basis factor and range of every audited category (section 2.2-2.3); the source band rule (section 3);
                                    the ASEAN LNG regasification adder of the v4 main set (section 4.1); literature ranges and notes of sections 4.2-4.8 (CO2 ship
                                    chain, storage price year, EV / ICE fleet ratio, CO2 storage P10 / P90, VN offshore calibration coefficient, MY rooftop, WACC basis).
  fragments/v4_d2b_corrections.csv  full-row replacements of existing rows: registered ranges refreshed from the D2b literature (main values unchanged; the v3.1 rows
                                    keep their values - the v4 main values live in the new rows / tables); written against the registry assembled without these
                                    corrections (idempotent).
Evidence: research/06_scope_redesign/p1_v4_d2b_20261108/evidence/*.json (synced from the delivery folder before this script runs). Deterministic. Nothing is solved.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import d1_registry as DR   # noqa: E402
from d1_common import REG_DIR, Registry, fmt   # noqa: E402
from v4_common import BIOMASS_DIR, LNG_REGAS_ROW, ROOT, sha256   # noqa: E402

SCRIPT = "scripts_project/v4_d2b_registry.py"
D2B = "research/06_scope_redesign/p1_v4_d2b_20261108"
COLUMNS = ["param_id", "description", "value", "unit", "country", "node", "tier", "source", "source_locator", "source_sha256", "derivation_script",
           "sensitivity_low", "sensitivity_high", "decision_ref", "status"]
EV = {k: ROOT / D2B / "evidence" / f for k, f in dict(trunk="TRUNK_LITERATURE.json", res="RESIDUE_LITERATURE.json", a="DATA_UPG_A.json", b="DATA_UPG_B.json",
                                                         calc="DATA_UPGRADES_CALC.json", alpha="VN_OFFWIND_ALPHA.json").items()}
UNDET = ("cassava_residues", "coconut_residues", "other_crop_residues")


def file_row(r: Registry, pid: str, p: Path, desc: str, tier: str) -> None:
    r.add(pid, desc, int(p.stat().st_size), "bytes", tier, "V4 D2b (sections 2-4; evidence in the D2b delivery)", f"file: {p.relative_to(ROOT)}", sha256(p), decision_ref="221", status="REFERENCE_ONLY")


def new_rows(calc: dict) -> Registry:
    r = Registry(SCRIPT)
    basis = BIOMASS_DIR / "BIOMASS_BASIS_T05.csv"
    file_row(r, "v4_biomass_basis_table_t05", basis, "T05: mass basis and heating-value basis of every biomass category, verdict (INCONSISTENT -> dry matter x LHV_dry; CONSISTENT -> kept; UNDETERMINED -> kept + range), factor mid / low / high (V4 D2b section 2)", "C")
    file_row(r, "v4_biomass_potential_2050_t05", BIOMASS_DIR / "BIOMASS_POTENTIAL_2050_V4_T05.csv", "solid-biomass potential of the v4 main set (research.demand.v4.biomass_potential = v4_adjusted_t05): T04 plus the oil palm trunk basis correction (x 0.3134 before the deductions); ASEAN11 1,289.32 TWh", "C")
    file_row(r, "v4_biomass_potential_adjustment_t05", BIOMASS_DIR / "BIOMASS_POTENTIAL_ADJ_V4_T05.csv", "F3 / F4 / F5 (T05) adjustment by country and category", "C")
    t = pd.read_csv(basis, keep_default_na=False).set_index("category")
    ev_t, ev_r = sha256(EV["trunk"]), sha256(EV["res"])
    x = t.loc["oil_palm_trunk"]
    loc = f"{D2B}/evidence/TRUNK_LITERATURE.json; BIOMASS_BASIS_T05.csv"
    r.add("v4_oil_palm_trunk_moisture_fresh", "oil palm trunk at replanting: moisture of the fresh trunk, wet basis; median of 5 author groups (Khalid 1999 0.80, Chow 2008 0.76, Husin POD 36 0.708, Abdullah & Sulaiman 2013 0.70, Fakhri 0.678)",
          float(x.moisture_reported_mid), "share", "C", "Khalid, Zin & Anderson (1999) JOPR 11(1); Chow, Mohd Basri & Chan (2008) OPB 56; Mohamad Husin et al. POD 36 (MPOB); Abdullah & Sulaiman (2013); Fakhri (2023)",
          loc, ev_t, sensitivity_low=float(x.moisture_reported_low), sensitivity_high=float(x.moisture_reported_high), decision_ref="221", status="REGISTERED")
    r.add("v4_oil_palm_trunk_lhv_dry", "oil palm trunk lower heating value, dry basis: HHV dwb 17.471 (Chow 2008) / 17.41 (Umar 2020) minus 2.442 x 9 x H 6.0 % (Chow 2008 ultimate analysis); high = the HHV",
          float(x.lhv_dry_gj_t_mid), "GJ/t dry", "C", "Chow, Mohd Basri & Chan (2008) OPB 56 Table 2-3; Umar et al. (2020) IOP Conf. Ser. MSE 863:012011", loc, ev_t,
          sensitivity_low=float(x.lhv_dry_gj_t_low), sensitivity_high=float(x.lhv_dry_gj_t_high), decision_ref="221", status="REGISTERED")
    r.add("v4_oil_palm_trunk_energy_per_fresh_t", "oil palm trunk energy per reported (fresh) tonne of the potential chain (IRENA 2022 App. A 2 t per palm, 80 % water): (1 - moisture) x LHV_dry; W08 / T04: 15 GJ/t on the fresh mass. "
          "Low = measured trunk dry mass 0.274 t per palm (Chow 2008) instead of 2 t fresh x dry matter (the IRENA 2 t is the whole above-ground fresh palm, Khalid 1999: trunk 1.51 t)",
          15.0 * float(x.factor_mid), "GJ per fresh t", "C", "derived: BIOMASS_BASIS_T05.csv", f"scripts_project/v4_biomass_potential.py basis_factors('t05'); {loc}", sha256(basis),
          sensitivity_low=15.0 * float(x.factor_low), sensitivity_high=15.0 * float(x.factor_high), decision_ref="221", status="REGISTERED")
    for cat, z in t.iterrows():
        if cat == "oil_palm_trunk" or str(z.origin).startswith("T04"):
            continue
        st = "SENSITIVITY" if z.verdict == "CONSISTENT" else "DATA_PENDING"
        r.add(f"v4_biomass_basis_factor_{cat}", f"{cat}: energy-basis verdict {z.verdict} (V4 D2b section 2); value kept (factor 1); range = factor_low - factor_high on the T04 energy; mass basis: {z.mass_basis}; "
              f"heating value: {z.heat_basis_table}; rule: {z.rule}", 1.0, "factor", "C", "V4 D2b RESIDUE_LITERATURE.json (Koopmans & Koppejan 1997; Junginger 2000; TISTR biomass database; IRENA 2014 / 2017a; UNSD 2022; Smeets et al. 2007)",
              f"{D2B}/evidence/RESIDUE_LITERATURE.json ({z.sources}); BIOMASS_BASIS_T05.csv", ev_r, sensitivity_low=float(z.factor_low), sensitivity_high=float(z.factor_high), decision_ref="221", status=st)
    # section 3
    r.add("v4_source_band_basis_rule", "Source temperature band shares of the fixed industrial biomass after the product vectors (research.demand.v4.source_band_basis = post_product): high = cement-kiln "
          "biomass of the conservation layer / T_v2 biomass, the rest split at 200 C with the s3_0 medium_a_fraction (v4_common.source_band_shares; below 1 MWh the s3_0 shares stay); fallback s30",
          "post_product", "rule", "B", "V4 D2b section 3 (Fable F-02 side note, D2a FABLE_FIXES.md 1.1)", "scripts_project/v4_outputs.py write_tables", sha256(HERE / "v4_outputs.py"), decision_ref="221", status="REGISTERED")
    # section 4
    L = calc["lng"]; ev_a, ev_b, ev_c = sha256(EV["a"]), sha256(EV["b"]), sha256(EV["calc"])
    r.add(LNG_REGAS_ROW, "LNG regasification adder of the v4 main set (research.demand.v4.lng_regas_adder = asean_tariffs) on the LNG import marginal cost: median of the published regulated terminal tariffs at full "
          f"utilisation, country groups TH ERC 2020 {L['country_groups']['TH']:.4f} / MY ST 2025 {L['country_groups']['MY']:.4f} / SG EMA-SLNG FY26 {L['country_groups']['SG']:.4f} / ID Arun 2017 {L['country_groups']['ID']:.4f} EUR2020/MWh "
          "(local currency -> EUR at the Eurostat annual average -> EUR2020 by euro-area HICP); v3.1 fallback fuel_price_lng_regasification_adder 1.26. Full-cost tariffs: on new terminal capacity the capital part overlaps the expansion capex (open question)",
          float(L["value"]), "EUR2020/MWh", "C", "ERC Thailand (The Nation 2020-08-29); Suruhanjaya Tenaga via The Star 2025-03-20; SLNG schedule of approved tariffs 2026-27, EMA GSC; detikFinance 2017-04-06 (Arun)",
          f"{D2B}/evidence/DATA_UPG_A.json D01-D14; DATA_UPGRADES_CALC.json lng", ev_a, sensitivity_low=float(L["low"]), sensitivity_high=float(L["high"]), decision_ref="221", status="REGISTERED")
    S = calc["co2_ship"]
    r.add("v4_co2_ship_chain_literature_fixed", "CO2 ship chain, distance-independent part derived from the literature (ZEP 2011 Tables 1-2 OLS; IEAGHG 2020 / BEIS 2018 totals minus the model slope); not a source value; model 11.4167 kept (bases differ: 7 barg vs 100 bar chain, pre-pressurised inlet)",
          float(S["model"]["fixed"]), "EUR2020/tCO2", "C", "ZEP (2011) The Costs of CO2 Transport; IEAGHG (2020-10); Element Energy for BEIS (2018)", f"{D2B}/evidence/DATA_UPG_A.json D15-D30", ev_a,
          sensitivity_low=float(S["fixed_range"][0]), sensitivity_high=float(S["fixed_range"][1]), decision_ref="221", status="REFERENCE_ONLY")
    r.add("v4_co2_ship_chain_literature_per_km", "CO2 ship chain, slope per t and km of one-way distance: model (IEAGHG 2004) 0.0029515; ZEP 2011 OLS 0.00437-0.00553, BEIS 2018 sensitivity 0.00393 (derived); kept",
          float(S["model"]["slope"]), "EUR2020/(tCO2 km)", "C", "ZEP (2011); Element Energy for BEIS (2018)", f"{D2B}/evidence/DATA_UPG_A.json D24-D26", ev_a,
          sensitivity_low=float(S["slope_range"][0]), sensitivity_high=float(S["slope_range"][1]), decision_ref="221", status="REFERENCE_ONLY")
    for c, z in calc["co2_storage_potential"]["countries"].items():
        if z.get("low_gt") is None:
            continue
        r.add(f"v4_co2_storage_potential_p10_p90_{c}", f"{c} CO2 storage potential range ERIA / GCCSI 2024 Ch.1: saline P90 / P50 / P10 + hydrocarbon P50 (main stays P50, decision 126); annual cap range = / 50 years "
              f"{z['cap_low_t'] / 1e6:.2f}-{z['cap_high_t'] / 1e6:.2f} Mt/a", float(z["p50_gt"]), "GtCO2", "B", "ERIA / GCCSI (2024) Comprehensive CCUS Research Report, Ch.1", f"{D2B}/evidence/DATA_UPG_A.json {z['ev']}", ev_a,
              country=c, sensitivity_low=float(z["low_gt"]), sensitivity_high=float(z["high_gt"]), decision_ref="221, 126", status="SENSITIVITY")
    E = calc["ev_ice"]
    r.add("v4_transport_fleet_energy_ratio_asean", "ASEAN fleet-weighted ratio of combustion to electric energy per km (two-wheelers 6.0-8.9, cars 3.6-4.5, buses 1.5-3.3; weights: two-wheeler share of road fuel 8-27 % IEA 2018, heavy 20-51 % ADBI 2015); "
          "mid differs from the model 53.19 / 16.0712 = 3.31 by +1.7 % (< 10 %) -> kept; range registered (INFERENCE: trucks not comparable, weights contradictory)",
          float(E["fleet_ratio_mid"]), "ratio", "C", "ITDP Indonesia 2023; ADB 2022; ADBI WP 1025 (2019); ERIA RPR 2022-18; IEA / GFEI 2019; Achariyaviriya 2023; Le 2023; IEA 2018 (2/3W)",
          f"{D2B}/evidence/DATA_UPG_B.json E01-E28; DATA_UPGRADES_CALC.json ev_ice", ev_b, sensitivity_low=float(E["fleet_ratio_low"]), sensitivity_high=float(E["fleet_ratio_high"]), decision_ref="221", status="SENSITIVITY")
    A = calc.get("vn_offwind_alpha", {})
    if A:
        m = A["alpha_cf_match"]; vals = sorted([m["pecc3_binh_thuan_net"]["alpha_box"], m["tc2021_fixed_2050_incl_outages"]["alpha_box"], m["wb_roadmap_2050_net"]["alpha_box"]])
        r.add("v4_offwind_alpha_vn_reference_area", "VN offshore calibration coefficient under the S4B-3 rule on the Binh Thuan reference area (ERA5 2013, NREL 2020ATB 5.5 MW x 0.8855): alpha matching the net CF of "
              f"EVNPECC3 50 % / Technology Catalogue 2050 53 % / WB roadmap 2050 ~60 % = {vals[0]:.3f} / {vals[1]:.3f} / {vals[2]:.3f}; speed ratio 8.5 m/s / ERA5 {A['era5_box_mean_ws100']:.2f} = {A['alpha_speed_ratio']['wb_ref_site_2030_2035_100m']['alpha_box']:.3f}. "
              "Not applied (one reference area, no zone values, roadmap CFs for 20 MW+ rotors; WB and TC not fully independent): alpha stays 1.0", vals[1], "alpha", "C",
              "World Bank / ESMAP (2021) Offshore Wind Roadmap for Vietnam Tables 8.2-9.3; EREA / DEA Viet Nam Technology Catalogue 2021; EVNPECC3 via Vietnam Energy 2021-04-14",
              f"{D2B}/evidence/VN_OFFWIND_ALPHA.json; DATA_UPG_B.json E30-E42", sha256(EV["alpha"]), country="VN", sensitivity_low=vals[0], sensitivity_high=vals[2], decision_ref="221", status="SENSITIVITY")
    r.add("v4_wacc_basis_note", "WACC basis: IEA Cost of Capital Observatory = nominal, after tax, local currency; COUNTRY_WACC_REAL_M08A.csv converts the IEA nominal post-tax midpoints to real (after tax); the uniform 7 % "
          "(technology-data / PyPSA-Eur fill value) has no stated basis - its documented origin (Hirth 2013; Noothout et al. 2016 nominal post-tax) is applied to real constant-EUR2020 costs: the two are not on the same basis (note only; country WACC stays a W19 sensitivity)",
          "note", "flag", "C", "IEA Cost of Capital Observatory (2025); PyPSA-Eur v0.3.0 / v2025.07.0 config; Noothout et al. (2016) DiaCore D3.4; Hirth (2013)", f"{D2B}/evidence/DATA_UPG_B.json E60-E70", ev_b,
          decision_ref="221", status="REFERENCE_ONLY")
    return r


def corrections(base: pd.DataFrame, calc: dict) -> pd.DataFrame:
    R = base.set_index("param_id"); rows = []
    t = pd.read_csv(BIOMASS_DIR / "BIOMASS_BASIS_T05.csv", keep_default_na=False).set_index("category")

    def put(pid, lo=None, hi=None, desc="", **kw):
        x = R.loc[pid].to_dict()
        y = dict(x, param_id=pid, description=f"{x['description']} | [V4 D2b, decision 221] {desc}", decision_ref=(x["decision_ref"] + ", 221").strip(", "))
        if lo is not None:
            y["sensitivity_low"] = fmt(lo)
        if hi is not None:
            y["sensitivity_high"] = fmt(hi)
        y.update(kw)
        rows.append({c: y[c] for c in COLUMNS})

    for pid in R.index:
        if not pid.startswith("biomass_potential_"):
            continue
        cat = next((k for k in ("oil_palm_trunk",) + UNDET if pid.endswith("_" + k)), None)
        if cat is None:
            continue
        v = float(R.at[pid, "value"]); fl, fh = float(t.at[cat, "factor_low"]), float(t.at[cat, "factor_high"])
        olo = R.at[pid, "sensitivity_low"]; ohi = R.at[pid, "sensitivity_high"]
        if cat == "oil_palm_trunk":
            put(pid, v * fl, v * fh, f"range = energy basis (T05: fresh mass x 15 GJ/t -> dry matter x LHV_dry, factor 0.3134 in the v4 main table; low {fl:.4f} = measured trunk dry mass, high {fh:.4f}); "
                f"former range {olo}-{ohi} (dry matter 0.2 x 15 / trunks + fronds)")
        else:
            new_lo = min(float(olo), v * fl) if olo != "" else v * fl
            put(pid, new_lo, None, f"low end extended to the energy-basis low of the category ({cat}: factor {fl:.4f}; UNDETERMINED in T05 - value kept, reviewer); former low {olo}")
    L = calc["lng"]
    put("fuel_price_lng_regasification_adder", L["low"], L["high"], f"range = published ASEAN regulated terminal tariffs (TH 1.80 - ID Arun 4.77 EUR2020/MWh); the v4 main set uses {LNG_REGAS_ROW} = {L['value']:.4f} (asean_tariffs); value 1.26 = v3.1 fallback")
    E = calc["ev_ice"]
    lo, hi = E["ev_eff_range_at_ice_16_0712"]
    put("share_transport_electric_efficiency", lo, hi, f"range = ASEAN fleet ratio {E['fleet_ratio_low']:.3f}-{E['fleet_ratio_high']:.3f} x 16.0712 (v4_transport_fleet_energy_ratio_asean; mid {E['fleet_ratio_mid']:.3f} within 10 % of 3.31 -> value kept)")
    S = calc["co2_ship"]
    put("co2_ship_chain_fixed_cost", S["fixed_range"][0], S["fixed_range"][1], "range = literature-derived distance-independent part (ZEP 2011 OLS, IEAGHG 2020 / BEIS 2018 at the model slope); value kept (bases differ)")
    put("co2_ship_chain_per_km_cost", S["slope_range"][0], S["slope_range"][1], "range = model slope to ZEP 2011 OLS slope (derived); value kept")
    put("renewable_cap_built_solar_rooftop_MY", 42000.0, None, "low end = SEDA MyRER 2021 rooftop resource 42 GW (p.39; one source lineage -> range only, value kept)")
    for c, z in calc["co2_storage_potential"]["countries"].items():
        if z.get("low_gt") is None:
            continue
        pid = f"co2_injection_cap_unified_{c}"
        if pid in R.index:
            put(pid, z["cap_low_t"], z["cap_high_t"], f"range = ERIA 2024 P90 / P10 storage {z['low_gt']:.4f} / {z['high_gt']:.4f} Gt / 50 years (main P50 unchanged, decision 126)")
    Y = calc["co2_sequestration_price_year"]
    put("co2_sequestration_cost_price_year", 2015.0, 2020.0, f"price year determined by INFERENCE as 2020: {Y['basis']} (DATA_UPG_A.json D31-D38); the 30 EUR/t stays as used; "
        "range 2015-2020 = the technology-data currency year before v0.12 (2015, when the former 10 EUR/t was set) to v0.13.2 (2020); factor 0.952-1.0 by euro-area HICP", value="2020", status="REGISTERED")
    A = calc.get("vn_offwind_alpha", {})
    if A:
        put("offwind_alpha_calibration_rule", None, None, "coefficient under the S4B-3 rule on the Binh Thuan reference area 0.849-1.042 (mid 0.896, registry v4_offwind_alpha_vn_reference_area); not applied, alpha stays 1.0 (VN_OFFWIND_ALPHA.json)")
    return pd.DataFrame(rows, columns=COLUMNS)


def main():
    for k, p in EV.items():
        if not p.exists():
            raise SystemExit(f"{p} missing: sync the D2b delivery folder into the repository first")
    calc = json.loads(EV["calc"].read_text())
    r = new_rows(calc)
    out = REG_DIR / "fragments" / "v4_d2b.csv"
    r.write(out)
    base, _ = DR.assemble([c for c in DR.CORRECTIONS if c != "v4_d2b_corrections"])
    corr = corrections(base, calc)
    corr.sort_values("param_id").to_csv(REG_DIR / "fragments" / "v4_d2b_corrections.csv", index=False, lineterminator="\n")
    print(out, len(r.rows), "rows; corrections", len(corr))


if __name__ == "__main__":
    main()
