"""V4 D2a (decision 220; V4_D2A_INSTRUCTION.md section 3.2, T04): palm-residue energy basis of the solid-biomass potential - the v4 main switch value
biomass_potential = v4_adjusted_t04 (EFB and fibre energy = wet mass x (1 - moisture) x LHV_dry), the W08 basis kept as v4_adjusted. No solver."""
import io
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
BIO = ROOT / "research_inputs/biomass_v5"


def test_basis_table_factors_and_verdicts():
    import v4_biomass_potential as B
    t = pd.read_csv(B.BASIS_T04, keep_default_na=False).set_index("category")
    assert set(t.index) >= {"oil_palm_efb", "oil_palm_fibre", "oil_palm_pks", "oil_palm_trunk"}
    for cat in ("oil_palm_efb", "oil_palm_fibre"):
        r = t.loc[cat]; assert str(r.applied) == "True" and r.verdict.startswith("INCONSISTENT")
        assert float(r.factor_mid) == pytest.approx((1 - float(r.moisture_ar_mid)) * float(r.lhv_dry_gj_t_mid) / 15.0, abs=1e-9)
        assert float(r.factor_low) == pytest.approx((1 - float(r.moisture_ar_high)) * float(r.lhv_dry_gj_t_low) / 15.0, abs=1e-6)
        assert float(r.factor_high) == pytest.approx((1 - float(r.moisture_ar_low)) * float(r.lhv_dry_gj_t_high) / 15.0, abs=1e-6)
    assert t.loc["oil_palm_pks"].verdict.startswith("CONSISTENT") and str(t.loc["oil_palm_pks"].applied) == "False"
    assert t.loc["oil_palm_trunk"].verdict.startswith("UNDETERMINED") and str(t.loc["oil_palm_trunk"].applied) == "False"
    f = B.basis_factors("t04")
    assert set(f) == {"oil_palm_efb", "oil_palm_fibre"} and f["oil_palm_efb"][0] == pytest.approx(0.48) and f["oil_palm_fibre"][0] == pytest.approx(0.7602)
    assert B.basis_factors("w08") == {}
    with pytest.raises(ValueError):
        B.basis_factors("other")


def test_t04_potential_file_is_the_rule_output_and_w08_file_unchanged():
    import v4_biomass_potential as B
    adj0, tab0 = B.adjust(); adj4, tab4 = B.adjust(basis="t04")
    for adj, out in ((adj0, B.OUT), (adj4, B.OUT_T04)):
        buf = io.StringIO(); adj.to_csv(buf, index=False, lineterminator="\n")
        assert out.read_text() == buf.getvalue(), out.name
    assert B.OUT.read_text() == (ROOT / "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4.csv").read_text()
    a0 = adj0.set_index(["country", "category"]); a4 = adj4.set_index(["country", "category"])
    assert list(a0.index) == list(a4.index)
    m0 = pd.to_numeric(a0.mass_main_t, errors="coerce").fillna(-1.0); m4 = pd.to_numeric(a4.mass_main_t, errors="coerce").fillna(-1.0)
    assert (m0 == m4).all()   # masses unchanged, energy basis changed
    f = B.basis_factors("t04")
    num = lambda v: 0.0 if (pd.isna(v) or str(v) == "") else float(v)   # noqa: E731  (empty potential = biogas rows without a figure)
    for (c, k), r in a4.iterrows():
        p0 = num(a0.at[(c, k), "potential_main_mwh"]); p4 = num(r.potential_main_mwh)
        if k == "oil_palm_efb":
            assert p4 == pytest.approx(p0 * f[k][0], rel=1e-12) and float(r.lhv_gj_per_t) == pytest.approx(7.2)
        elif k == "oil_palm_fibre":
            assert p4 == 0.0 and p0 == 0.0   # 100 % in-mill (T03)
        elif k in ("oil_palm_pks", "oil_palm_trunk", "sugarcane_residues", "wood_processing_residues") or r.feedstock_group == "biogas":
            assert p4 == pytest.approx(p0, rel=1e-12), (c, k)
    # F5 column of the ADJ table; ASEAN totals
    t4 = tab4[tab4.country == "ASEAN11"].iloc[0]; t0 = tab0[tab0.country == "ASEAN11"].iloc[0]
    assert t0.potential_adjusted_TWh == pytest.approx(1618.48, abs=0.005) and "F5_basis_TWh" in tab4.columns and "F5_basis_TWh" not in tab0.columns
    efb0 = pd.to_numeric(a0[a0.index.get_level_values(1) == "oil_palm_efb"].potential_main_mwh, errors="coerce").fillna(0.0).sum() / 1e6
    assert t0.potential_adjusted_TWh - t4.potential_adjusted_TWh == pytest.approx((1 - 0.48) * efb0, rel=0.05)   # the EFB cut dominates (fibre is in-mill, the 5150 offsets are small)
    assert t4.potential_adjusted_TWh < t0.potential_adjusted_TWh - 150.0


def test_switch_value_and_table_selection():
    from phase4_static import config
    from v4_common import BIOMASS_POTENTIAL_FILES, SWITCH_VALUES, V31, V4_MAIN, switches, v4_tables
    assert SWITCH_VALUES["biomass_potential"] == ("v3", "v4_adjusted", "v4_adjusted_t04") and V4_MAIN["biomass_potential"] == "v4_adjusted_t04" and V31["biomass_potential"] == "v3"
    assert BIOMASS_POTENTIAL_FILES["v3"] is None and BIOMASS_POTENTIAL_FILES["v4_adjusted_t04"].endswith("_V4_T04.csv")
    cfg = config(ROOT, "integrated"); cfg["research"]["demand"]["v4"]["enabled"] = True
    assert switches(cfg)["biomass_potential"] == "v4_adjusted_t04" and v4_tables(cfg)["biomass_potential"].endswith("BIOMASS_POTENTIAL_2050_V4_T04.csv")
    rec = json.loads((ROOT / "research_inputs/industry_v4/out_ras/V4_SWITCHES.json").read_text())
    assert rec["switches"]["biomass_potential"] == "v4_adjusted_t04"
    import v4_industry as V
    I = V.Inputs()
    case = V.final_case(I, dict(V4_MAIN, anchor_mode="ras")); assert case["biopot"].endswith("BIOMASS_POTENTIAL_2050_V4_T04.csv")
    case = V.final_case(I, dict(V4_MAIN, anchor_mode="ras", biomass_potential="v4_adjusted")); assert case["biopot"].endswith("BIOMASS_POTENTIAL_2050_V4.csv")
    assert "biopot" not in V.final_case(I, dict(V4_MAIN, anchor_mode="ras", biomass_potential="v3"))


def test_registry_rows_of_the_basis():
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    assert float(reg.at["v4_palm_residue_moisture_ar_efb", "value"]) == 0.60 and float(reg.at["v4_palm_residue_lhv_dry_efb", "value"]) == 18.0
    assert float(reg.at["v4_palm_residue_energy_per_wet_t_efb", "value"]) == pytest.approx(7.2) and reg.at["v4_palm_residue_energy_per_wet_t_efb", "status"] == "REGISTERED"
    assert float(reg.at["v4_palm_residue_energy_per_wet_t_pks", "value"]) == 15.0 and reg.at["v4_palm_residue_energy_per_wet_t_pks", "status"] == "SENSITIVITY"
    assert float(reg.at["v4_palm_residue_energy_per_wet_t_efb", "sensitivity_low"]) == pytest.approx(15.0 * 0.34826, abs=1e-4)
