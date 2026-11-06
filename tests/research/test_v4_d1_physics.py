"""V4 D1 section 4 (decision 212 (a)): registered ranges clipped to physical bounds (fragments/v4_d1_corrections.csv, scripts_project/v4_d1_registry.py).
Only sensitivity_low / sensitivity_high (and the description / decision_ref note) of the eleven rows change; every main value and every other row is unchanged;
the stoichiometric limits follow from the model heating values; after the correction no in-use range violates the checked bounds. No solver."""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))


@pytest.fixture(scope="module")
def regs():
    import d1_registry as DR
    base, _ = DR.assemble([c for c in DR.CORRECTIONS if c != "v4_d1_corrections"])
    final = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False)
    return base.set_index("param_id"), final.set_index("param_id")


def test_limits_from_stoichiometry_and_model_heating_values():
    import v4_d1_registry as V
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False)
    L = V.physics_limits(reg)
    assert V.MOLAR["CO2"] == pytest.approx(44.009) and V.MOLAR["MeOH"] == pytest.approx(32.042) and V.MOLAR["NH3"] == pytest.approx(17.031)
    assert L["lhv_meoh_mwh_t"] == 5.528 and L["lhv_ch4_gj_t"] == 50.04 and L["lhv_ch4_mwh_t"] == pytest.approx(13.9)
    assert L["meoh_per_tco2_max"] == pytest.approx(32.042 / 44.009 * 5.528, rel=1e-12) == pytest.approx(4.0248171, abs=1e-7)
    assert L["meoh_per_mwh_h2_max"] == pytest.approx(32.042 * 5.528 / (3 * 2.016 * 33.33), rel=1e-12) == pytest.approx(0.8786999, abs=1e-7)
    assert L["h2_per_tnh3_min"] == pytest.approx(1.5 * 2.016 / 17.031 * 33.33, rel=1e-12) == pytest.approx(5.918027, abs=1e-6)


def test_only_the_ranges_of_the_eleven_rows_change(regs):
    import v4_d1_registry as V
    base, final = regs
    assert set(base.index) == set(final.index)
    fixes = {f[0] for f in V.PHYSICS_FIXES}
    assert len(fixes) == 11
    changed = [p for p in base.index if not base.loc[p].equals(final.loc[p])]
    assert set(changed) == fixes
    assert (base["value"] == final.loc[base.index, "value"]).all() and (base["status"] == final.loc[base.index, "status"]).all()
    for p in fixes:
        diff = {c for c in base.columns if base.at[p, c] != final.at[p, c]}
        assert diff <= {"sensitivity_low", "sensitivity_high", "description", "decision_ref"} and "212 (a)" in final.at[p, "decision_ref"], (p, diff)
    f = final
    assert (f.at["share_bev_charge_efficiency", "sensitivity_high"], f.at["share_bev_avail_max", "sensitivity_high"]) == ("1", "1")
    assert float(f.at["share_MWh_MeOH_per_tCO2", "sensitivity_high"]) == pytest.approx(4.0248171, abs=1e-7) and f.at["share_MWh_MeOH_per_tCO2", "value"] == "4.0321"
    assert float(f.at["share_MWh_MeOH_per_MWh_H2", "sensitivity_high"]) == pytest.approx(0.8786999, abs=1e-7)
    assert float(f.at["share_MWh_H2_per_tNH3_electrolysis", "sensitivity_low"]) == pytest.approx(5.918027, abs=1e-6)
    for p in ("share_MWh_NH3_per_tNH3", "liquid_ship_mwh_per_t_ammonia", "liquid_ship_mwh_per_t_methanol"):
        assert f.at[p, "sensitivity_low"] == f.at[p, "sensitivity_high"] == f.at[p, "value"]
    assert f.at["liquid_ship_mwh_per_t_oil", "sensitivity_high"] == "13.9" and f.at["conv_gj_per_t_natural_gas_mass", "sensitivity_high"] == "50.04"
    assert f.at["liquid_ship_hours_per_year", "sensitivity_high"] == "8760"


def test_corrections_fragment_is_reproducible(regs):
    import v4_d1_registry as V
    base, _ = regs
    corr, log = V.physics_corrections(base.reset_index())
    frag = pd.read_csv(ROOT / "research_inputs/registry_v5/fragments/v4_d1_corrections.csv", dtype=str, keep_default_na=False)
    pd.testing.assert_frame_equal(corr.sort_values("param_id").reset_index(drop=True), frag.sort_values("param_id").reset_index(drop=True))
    note = {x["param_id"]: x["main_value_note"] for x in log}
    assert "above the physical upper bound" in note["share_MWh_MeOH_per_tCO2"] and note["share_bev_charge_efficiency"] == ""


def test_no_in_use_range_violates_the_checked_bounds_after_correction(regs):
    import v4_d1_registry as V
    _, f = regs
    use = f[f.status.isin(["REGISTERED", "SENSITIVITY", "DATA_PENDING"])].copy()
    lo, hi = pd.to_numeric(use.sensitivity_low, errors="coerce"), pd.to_numeric(use.sensitivity_high, errors="coerce")
    frac = use.unit.isin(["fraction", "share", "p.u.", "MWh_useful/MWh_fuel"])
    assert ((lo[frac].dropna() >= 0) & (lo[frac].dropna() <= 1)).all() and ((hi[frac].dropna() >= 0) & (hi[frac].dropna() <= 1)).all()
    assert (lo.dropna() >= 0).all() and (hi.dropna() >= 0).all()
    L = V.physics_limits(f.reset_index())
    assert hi["share_MWh_MeOH_per_tCO2"] <= L["meoh_per_tco2_max"] + 1e-9 and hi["share_MWh_MeOH_per_MWh_H2"] <= L["meoh_per_mwh_h2_max"] + 1e-9
    assert lo["share_MWh_H2_per_tNH3_electrolysis"] >= L["h2_per_tnh3_min"] - 1e-9
    assert hi[use.unit == "h/a"].max() <= 8760
