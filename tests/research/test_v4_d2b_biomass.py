"""V4 D2b (decision 221; V4_D2B_INSTRUCTION.md sections 2 / 4.1): the energy-basis audit of every biomass category (T05) and the LNG regasification switch.
  biomass_potential = v4_adjusted_t05 (v4 main): T04 plus the oil palm trunk (fresh mass x 15 GJ/t -> dry matter x LHV_dry); T04 / W08 files unchanged
  lng_regas_adder   = asean_tariffs (v4 main, registry v4_lng_regas_adder_asean_tariffs) | m08a (v3.1: the configured 1.26)
No solver, no network build."""
import io
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
BIO = ROOT / "research_inputs/biomass_v5"


def test_t05_table_rules():
    import v4_biomass_potential as B
    t = pd.read_csv(B.BASIS_T05, keep_default_na=False).set_index("category")
    cats = {"oil_palm_efb", "oil_palm_fibre", "oil_palm_pks", "oil_palm_trunk", "rice_residues", "maize_residues", "sugarcane_residues", "coconut_residues", "cassava_residues",
            "other_crop_residues", "wood_processing_residues", "msw_organic_biogas", "oil_palm_pome"}
    assert set(t.index) == cats   # every category of the potential table is audited
    applied = {k for k in t.index if str(t.at[k, "applied"]) == "True"}
    assert applied == {"oil_palm_efb", "oil_palm_fibre", "oil_palm_trunk"}
    for k in applied:
        r = t.loc[k]
        assert r.verdict.startswith("INCONSISTENT")
        assert float(r.factor_mid) == pytest.approx(float(r.dry_matter_mid) * float(r.lhv_dry_gj_t_mid) / float(r.lhv_table_gj_t), abs=1e-12)
        assert float(r.factor_low) <= float(r.factor_mid) <= float(r.factor_high)
    t4 = pd.read_csv(B.BASIS_T04, keep_default_na=False).set_index("category")
    for k in ("oil_palm_efb", "oil_palm_fibre"):   # the T04 rows carried over with the same factors
        assert float(t.at[k, "factor_mid"]) == pytest.approx(float(t4.at[k, "factor_mid"]), abs=1e-9)
    tr = t.loc["oil_palm_trunk"]
    assert float(tr.moisture_reported_mid) == pytest.approx(0.708333, abs=1e-6) and float(tr.lhv_dry_gj_t_mid) == pytest.approx(16.1218, abs=1e-4)
    assert float(tr.factor_mid) == pytest.approx(0.3134798, abs=1e-6) and tr.low_rule == "basis" and float(tr.factor_low) == pytest.approx(0.274 * float(tr.lhv_dry_gj_t_low) / 30.0, abs=1e-12)
    for k in t.index:
        if k not in applied:
            assert t.at[k, "verdict"].startswith(("CONSISTENT", "UNDETERMINED")) and float(t.at[k, "factor_low"]) <= 1.0 <= float(t.at[k, "factor_high"]) + 1e-12
    f = B.basis_factors("t05")
    assert set(f) == applied and f["oil_palm_trunk"][3] == "basis" and f["oil_palm_efb"][0] == pytest.approx(0.48)


def test_t05_files_are_the_rule_output_and_older_files_unchanged():
    import v4_biomass_potential as B
    adj4, _ = B.adjust(basis="t04"); adj5, tab5 = B.adjust(basis="t05"); adj0, _ = B.adjust()
    for adj, out in ((adj0, B.OUT), (adj4, B.OUT_T04), (adj5, B.OUT_T05)):
        buf = io.StringIO(); adj.to_csv(buf, index=False, lineterminator="\n")
        assert out.read_text() == buf.getvalue(), out.name
    a4 = adj4.set_index(["country", "category"]); a5 = adj5.set_index(["country", "category"])
    num = lambda v: 0.0 if (pd.isna(v) or str(v) == "") else float(v)   # noqa: E731
    f = B.basis_factors("t05")["oil_palm_trunk"]
    for (c, k), r in a5.iterrows():
        p4, p5 = num(a4.at[(c, k), "potential_main_mwh"]), num(r.potential_main_mwh)
        if k == "oil_palm_trunk":
            assert p5 == pytest.approx(p4 * f[0], rel=1e-12) and num(r.potential_low_mwh) == pytest.approx(p4 * f[4], rel=1e-12)
            assert float(r.lhv_gj_per_t) == pytest.approx(15.0 * f[0])
        else:
            assert p5 == p4, (c, k)
    t = tab5[tab5.country == "ASEAN11"].iloc[0]
    assert t.potential_adjusted_TWh == pytest.approx(1289.32, abs=0.005)
    trunk = sum(num(r.potential_main_mwh) for (c, k), r in a5.iterrows() if k == "oil_palm_trunk") / 1e6
    assert trunk == pytest.approx(72.50, abs=0.01)


def test_switches_and_files():
    from phase4_static import config
    from v4_common import BIOMASS_POTENTIAL_FILES, SWITCH_VALUES, V31, V4_MAIN, lng_regas_adder_value, switches, v4_tables
    assert BIOMASS_POTENTIAL_FILES["v4_adjusted_t05"].endswith("_V4_T05.csv") and V4_MAIN["biomass_potential"] == "v4_adjusted_t05"
    assert SWITCH_VALUES["lng_regas_adder"] == ("m08a", "asean_tariffs") and V31["lng_regas_adder"] == "m08a" and V4_MAIN["lng_regas_adder"] == "asean_tariffs"
    cfg = config(ROOT, "integrated")
    v31, b31 = lng_regas_adder_value(cfg)
    assert v31 == 1.26 and b31.startswith("m08a")   # v4 disabled: the configured value
    cfg["research"]["demand"]["v4"]["enabled"] = True
    v4, b4 = lng_regas_adder_value(cfg)
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    assert v4 == float(reg.at["v4_lng_regas_adder_asean_tariffs", "value"]) and v4 == pytest.approx(2.0507, abs=1e-4) and b4.startswith("asean_tariffs")
    assert float(reg.at["v4_lng_regas_adder_asean_tariffs", "sensitivity_low"]) == pytest.approx(1.8049, abs=1e-4)
    cfg["research"]["demand"]["v4"]["lng_regas_adder"] = "m08a"
    assert lng_regas_adder_value(cfg)[0] == 1.26
    cfg["research"]["demand"]["v4"]["lng_regas_adder"] = "asean_tariffs"
    assert switches(cfg)["biomass_potential"] == "v4_adjusted_t05" and v4_tables(cfg)["biomass_potential"].endswith("BIOMASS_POTENTIAL_2050_V4_T05.csv")
    import v4_industry as V
    case = V.final_case(V.Inputs(), dict(V4_MAIN, anchor_mode="ras")); assert case["biopot"].endswith("BIOMASS_POTENTIAL_2050_V4_T05.csv")


def test_registry_rows_and_ranges():
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    for pid in ("v4_biomass_basis_table_t05", "v4_biomass_potential_2050_t05", "v4_oil_palm_trunk_moisture_fresh", "v4_oil_palm_trunk_lhv_dry", "v4_oil_palm_trunk_energy_per_fresh_t",
                "v4_source_band_basis_rule", "v4_transport_fleet_energy_ratio_asean", "v4_offwind_alpha_vn_reference_area", "v4_wacc_basis_note"):
        assert pid in reg.index, pid
    assert float(reg.at["v4_oil_palm_trunk_energy_per_fresh_t", "value"]) == pytest.approx(15.0 * 0.3134798, abs=1e-5)
    for c in ("ID", "MY", "TH", "PH", "KH"):   # trunk ranges = v3 value x the basis range
        r = reg.loc[f"biomass_potential_{c}_oil_palm_trunk"]
        assert float(r.sensitivity_low) == pytest.approx(float(r.value) * 0.14697, rel=1e-3) and float(r.sensitivity_high) < float(r.value)
    assert reg.at["co2_sequestration_cost_price_year", "value"] == "2020" and reg.at["co2_sequestration_cost_price_year", "status"] == "REGISTERED"
    assert float(reg.at["co2_injection_cap_unified_VN", "sensitivity_low"]) == pytest.approx(3.3034e9 / 50) and float(reg.at["fuel_price_lng_regasification_adder", "value"]) == 1.26
    t = json.loads((ROOT / "research_inputs/industry_v4/out_ras/V4_SWITCHES.json").read_text())
    assert t["switches"]["lng_regas_adder"] == "asean_tariffs" and t["main_set"]
