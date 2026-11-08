"""V4 D2c (decision 223; V4_D2C_INSTRUCTION.md section 2): the oil palm trunk potential on the measured trunk dry mass per palm (T06).
  biomass_potential = v4_adjusted_t06 (v4 main): BIOMASS_BASIS_T06.csv = BIOMASS_BASIS_T05.csv with the trunk row replaced; the T06 potential file differs from T05
  only in the five oil palm trunk rows; T05 (high-sensitivity switch value), T04, v4_adjusted and v3 stay selectable with unchanged files.
No solver, no network build."""
import io
import json
import statistics
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
D2C = ROOT / "research/06_scope_redesign/p1_v4_d2c_20261109"
TRUNKS = {"ID", "MY", "TH", "PH", "KH"}


def test_trunk_dry_mass_table_is_the_median_of_the_measured_sources():
    m = pd.read_csv(D2C / "TRUNK_DRY_MASS.csv", keep_default_na=False).set_index("source_id")
    inc = m[m.included.astype(str) == "True"]
    assert set(inc.index) == {"KHALID1999", "CHOW2008", "HENSON2006"}
    assert float(inc.at["KHALID1999", "per_palm_t_dm"]) == pytest.approx(41.07 / 136.0, abs=1e-6)
    assert float(inc.at["CHOW2008", "per_palm_t_dm"]) == pytest.approx(0.274, abs=1e-9)
    poly = lambda x: 0.0001 * x ** 4 - 0.0114 * x ** 3 + 0.3002 * x ** 2 - 0.2645 * x   # noqa: E731  Henson 2006 Fig. 8, t DM/ha at 148 palms/ha
    assert float(inc.at["HENSON2006", "per_palm_t_dm"]) == pytest.approx(poly(25) / 148.0, abs=1e-6) and float(inc.at["HENSON2006", "density_palms_per_ha"]) == 148.0
    v = [float(x) for x in inc.per_palm_t_dm]
    assert float(m.at["CENTRE", "per_palm_t_dm"]) == pytest.approx(statistics.median(v), abs=1e-6)
    assert float(m.at["LOW", "per_palm_t_dm"]) == pytest.approx(min(v), abs=1e-6) and float(m.at["HIGH", "per_palm_t_dm"]) == pytest.approx(max(v), abs=1e-6)


def test_t06_basis_table_differs_from_t05_only_in_the_trunk_row():
    import v4_biomass_potential as B
    a = B.BASIS_T05.read_text().split("\n"); b = B.BASIS_T06.read_text().split("\n")
    assert len(a) == len(b)
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert len(diff) == 1 and b[diff[0]].startswith("oil_palm_trunk,")
    assert B.t06_changed() == {"oil_palm_trunk"}
    t = pd.read_csv(B.BASIS_T06, keep_default_na=False).set_index("category"); r = t.loc["oil_palm_trunk"]
    m = pd.read_csv(D2C / "TRUNK_DRY_MASS.csv", keep_default_na=False).set_index("source_id")
    for col, key in (("dry_matter_mid", "CENTRE"), ("dry_matter_low", "LOW"), ("dry_matter_high", "HIGH")):
        assert float(r[col]) == pytest.approx(float(m.at[key, "per_palm_t_dm"]) / 2.0, abs=1e-6)   # dry matter per reported t = per-palm dry mass / 2 t per palm
    assert float(r.lhv_dry_gj_t_mid) == pytest.approx(16.12182, abs=1e-9) and float(r.lhv_table_gj_t) == 15.0
    for s in ("mid", "low", "high"):
        assert float(r[f"factor_{s}"]) == pytest.approx(float(r[f"dry_matter_{s}"]) * float(r.lhv_dry_gj_t_mid) / 15.0, abs=1e-12)
    assert float(r.factor_mid) == pytest.approx(0.152322, abs=1e-6) and float(r.factor_low) <= float(r.factor_mid) <= float(r.factor_high) < 0.31348
    assert r.low_rule == "basis" and str(r.applied) == "True"
    f6, f5 = B.basis_factors("t06"), B.basis_factors("t05")
    assert set(f6) == set(f5) == {"oil_palm_efb", "oil_palm_fibre", "oil_palm_trunk"}
    for k in ("oil_palm_efb", "oil_palm_fibre"):
        assert f6[k] == f5[k]   # same factor, same text (T05 rows carried over)
    assert f6["oil_palm_trunk"][0] == pytest.approx(float(r.factor_mid)) and "T06" in f6["oil_palm_trunk"][2]


def test_t06_potential_files_are_the_rule_output_and_t05_except_the_trunk_rows():
    import v4_biomass_potential as B
    adj6, tab6 = B.adjust(basis="t06")
    buf = io.StringIO(); adj6.to_csv(buf, index=False, lineterminator="\n")
    assert B.OUT_T06.read_text() == buf.getvalue()
    buf = io.StringIO(); tab6.to_csv(buf, index=False, float_format="%.6f", lineterminator="\n")
    assert B.ADJ_T06.read_text() == buf.getvalue()
    a = B.OUT_T05.read_text().split("\n"); b = B.OUT_T06.read_text().split("\n")
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert len(a) == len(b) and {(b[i].split(",")[0], b[i].split(",")[1]) for i in diff} == {(c, "oil_palm_trunk") for c in TRUNKS}
    a5 = pd.read_csv(B.OUT_T05).set_index(["country", "category"]); a6 = pd.read_csv(B.OUT_T06).set_index(["country", "category"])
    f6, f5 = B.basis_factors("t06")["oil_palm_trunk"], B.basis_factors("t05")["oil_palm_trunk"]
    for c in TRUNKS:
        assert float(a6.at[(c, "oil_palm_trunk"), "potential_main_mwh"]) == pytest.approx(float(a5.at[(c, "oil_palm_trunk"), "potential_main_mwh"]) * f6[0] / f5[0], rel=1e-12)
    t = tab6[tab6.country == "ASEAN11"].iloc[0]
    assert t.potential_adjusted_TWh == pytest.approx(1252.05, abs=0.005)
    trunk = float(a6.xs("oil_palm_trunk", level="category").potential_main_mwh.sum()) / 1e6
    assert trunk == pytest.approx(35.2267, abs=0.001)


def test_switch_value_main_set_and_table_folders():
    from phase4_static import config
    from v4_common import BIOMASS_POTENTIAL_FILES, SWITCH_VALUES, V31, V4_MAIN, switches, v4_tables
    assert V4_MAIN["biomass_potential"] == "v4_adjusted_t06" and V31["biomass_potential"] == "v3"
    assert SWITCH_VALUES["biomass_potential"] == ("v3", "v4_adjusted", "v4_adjusted_t04", "v4_adjusted_t05", "v4_adjusted_t06")
    assert BIOMASS_POTENTIAL_FILES["v4_adjusted_t06"].endswith("_V4_T06.csv") and BIOMASS_POTENTIAL_FILES["v4_adjusted_t05"].endswith("_V4_T05.csv")
    cfg = config(ROOT, "integrated")
    assert switches(cfg)["biomass_potential"] == "v3"   # v4 disabled: the v3.1 table (A2 fallback)
    cfg["research"]["demand"]["v4"]["enabled"] = True
    assert switches(cfg)["biomass_potential"] == "v4_adjusted_t06" and v4_tables(cfg)["biomass_potential"].endswith("BIOMASS_POTENTIAL_2050_V4_T06.csv")
    import v4_industry as V
    I = V.Inputs()
    assert V.final_case(I, dict(V4_MAIN, anchor_mode="ras"))["biopot"].endswith("BIOMASS_POTENTIAL_2050_V4_T06.csv")
    assert V.final_case(I, dict(V4_MAIN, anchor_mode="ras", biomass_potential="v4_adjusted_t05"))["biopot"].endswith("BIOMASS_POTENTIAL_2050_V4_T05.csv")
    for d in ("out_ras", "out_iid"):
        rec = json.loads((ROOT / "research_inputs/industry_v4" / d / "V4_SWITCHES.json").read_text())
        assert rec["main_set"] and rec["switches"]["biomass_potential"] == "v4_adjusted_t06"


def test_registry_rows():
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    for pid in ("v4_biomass_basis_table_t06", "v4_biomass_potential_2050_t06", "v4_biomass_potential_adjustment_t06", "v4_oil_palm_trunk_dry_mass_per_palm",
                "v4_oil_palm_trunk_energy_per_reported_t_t06", "v4_oil_palm_replanting_rate"):
        assert pid in reg.index, pid
    r = reg.loc["v4_oil_palm_trunk_dry_mass_per_palm"]
    assert float(r.value) == pytest.approx(0.283446, abs=1e-6) and float(r.sensitivity_low) == pytest.approx(0.274) and float(r.sensitivity_high) == pytest.approx(0.301985, abs=1e-6)
    assert r.tier == "B" and r.status == "REGISTERED" and "223" in r.decision_ref
    r = reg.loc["v4_oil_palm_replanting_rate"]
    assert float(r.value) == 0.04 and float(r.sensitivity_low) == 0.022 and r.status == "SENSITIVITY"
    for c in TRUNKS:   # range = v3 value x T06 low ... v3 value x T05 (the high-sensitivity switch value)
        r = reg.loc[f"biomass_potential_{c}_oil_palm_trunk"]
        assert float(r.sensitivity_low) == pytest.approx(float(r.value) * 0.147245956, rel=1e-9) and float(r.sensitivity_high) == pytest.approx(float(r.value) * 0.3134798333, rel=1e-9)
