"""V4 D1 section 5 (decision 214 (a), T03): the per-country palm mill self-use table research_inputs/biomass_v5/PALM_MILL_SELF_USE.csv, read by
v4_biomass_potential.py (W08 constants kept as fallback). The T03 verdict keeps fibre 1.00 / PKS 0.50 in every country (TH PKS contradictory, grade D), so
the v4 potential is byte-identical; low / high give the registered sensitivities. Registry rows equal the table. No solver."""
import io
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
D1 = ROOT / "research/06_scope_redesign/p1_v4_d1_20261107"
TAB = ROOT / "research_inputs/biomass_v5/PALM_MILL_SELF_USE.csv"


def test_table_schema_and_verdicts():
    t = pd.read_csv(TAB).set_index("country")
    assert set(t.index) == {"ID", "MY", "TH", "PH", "KH"}
    for s in ("fibre", "pks"):
        assert ((t[f"{s}_low"] <= t[f"{s}_mid"]) & (t[f"{s}_mid"] <= t[f"{s}_high"]) & (t[f"{s}_low"] >= 0) & (t[f"{s}_high"] <= 1)).all(), s
    assert (t.fibre_mid == 1.0).all() and (t.pks_mid == 0.5).all()
    assert t.at["TH", "verdict_pks"] == "CONTRADICTORY" and t.at["TH", "grade_pks"] == "D"
    assert (t.drop(index="TH").verdict_pks == "CONSISTENT").all() and (t.verdict_fibre == "CONSISTENT").all()
    assert t.at["MY", "grade_fibre"] == "B" and set(t.grade_pks.drop(index="TH")) == {"C"}
    assert all(x.startswith("T03-") for s in ("sources_fibre", "sources_pks") for v in t[s] for x in v.split(";"))
    assert (D1 / "PALM_MILL_SELF_USE.csv").read_bytes() == TAB.read_bytes()


def test_table_keeps_the_v4_potential_byte_identical():
    import v4_biomass_potential as B
    adj_t, tab_t = B.adjust()
    adj_c, tab_c = B.adjust(source="constant")
    pd.testing.assert_frame_equal(adj_t, adj_c)
    num = ["potential_v3_TWh", "F3_bagasse_R2_TWh", "F4_self_use_TWh", "potential_adjusted_TWh", "F7_cap_99pct_TWh"]
    pd.testing.assert_frame_equal(tab_t[num], tab_c[num])
    buf = io.StringIO(); adj_t.to_csv(buf, index=False, lineterminator="\n")
    assert B.OUT.read_text() == buf.getvalue()
    import hashlib
    assert hashlib.sha256(B.OUT.read_bytes()).hexdigest().startswith("cd9df282168598cc")   # = W08 = I2 BIOMASS_POTENTIAL_2050_I2.csv
    r = tab_t.set_index(["country", "category"])
    assert "PALM_MILL_SELF_USE.csv mid, contradictory" in r.at[("TH", "oil_palm_pks"), "rule"] and r.at[("TH", "oil_palm_pks"), "grade"] == "D"
    assert "consistent" in r.at[("TH", "oil_palm_fibre"), "rule"] and r.at[("MY", "oil_palm_fibre"), "grade"] == "B"
    assert B.self_use("constant")["ID"]["fibre"] == B.FIBRE_IN_MILL_SHARE == 1.0 and B.self_use("constant")["ID"]["pks"] == B.PKS_IN_MILL_SHARE == 0.5


@pytest.mark.parametrize("level", ["low", "high"])
def test_low_high_sensitivity(level):
    import v4_biomass_potential as B
    t = pd.read_csv(TAB).set_index("country")
    _, mid = B.adjust(); _, x = B.adjust(level=level)
    m = mid.set_index(["country", "category"]).potential_adjusted_TWh; y = x.set_index(["country", "category"]).potential_adjusted_TWh
    v3 = mid.set_index(["country", "category"]).potential_v3_TWh
    for cc in t.index:
        for s, cat in (("fibre", "oil_palm_fibre"), ("pks", "oil_palm_pks")):
            assert y[(cc, cat)] - m[(cc, cat)] == pytest.approx(-(t.at[cc, f"{s}_{level}"] - t.at[cc, f"{s}_mid"]) * v3[(cc, cat)], abs=1e-9), (cc, cat)
    # F4d (food / n.e.s. 5150 self-use) is netted against the palm deduction, so rice / coconut residues may move with the palm shares; nothing else moves
    other = [k for k in m.index if k[1] not in ("oil_palm_fibre", "oil_palm_pks", "rice_residues", "coconut_residues", "TOTAL solid") and k[0] != "ASEAN11"]
    assert (y[other] == m[other]).all()
    _, w = B.adjust(pks_share=0.0)        # W08 interface: one PKS share for every country
    ww = w.set_index(["country", "category"])
    assert ww.at[("ID", "oil_palm_pks"), "potential_adjusted_TWh"] == pytest.approx(v3[("ID", "oil_palm_pks")])


def test_registry_rows_equal_the_table():
    from v4_common import sha256
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    t = pd.read_csv(TAB).set_index("country")
    f = reg.loc["v4_palm_mill_self_use_table"]
    assert f.source_sha256 == sha256(TAB) and f.source_locator == "file: research_inputs/biomass_v5/PALM_MILL_SELF_USE.csv"
    ev = sha256(D1 / "evidence/T03_LITERATURE.json")
    for cc in t.index:
        for s in ("fibre", "pks"):
            r = reg.loc[f"v4_palm_mill_{s}_self_use_{cc}"]
            assert float(r.value) == t.at[cc, f"{s}_mid"] and float(r.sensitivity_low) == pytest.approx(t.at[cc, f"{s}_low"]) and float(r.sensitivity_high) == pytest.approx(t.at[cc, f"{s}_high"])
            assert r.source_sha256 == ev and r.status == "REGISTERED" and r.country == cc and f"grade {t.at[cc, f'grade_{s}']}" in r.description
    assert "fallback" in reg.at["v4_pks_in_mill_share", "description"]
