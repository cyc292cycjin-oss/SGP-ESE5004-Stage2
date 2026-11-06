"""V4 W08 checklist section 8 (decision 209 F1 / F3 / F4 / F7): adjusted solid-biomass potential, overflow cap, marketed gas caps. No solver."""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
I2 = ROOT / "research/06_scope_redesign/p1_v4_w07_20261106/I2"
W12 = ROOT / "research/06_scope_redesign/p1_v4_w07_20261106/W12/tables"


def test_potential_equals_i2_by_country_and_category():
    import v4_biomass_potential as B
    adj, tab = B.adjust()
    ref = pd.read_csv(I2 / "BIOMASS_POTENTIAL_ADJ.csv")
    m = tab.merge(ref, on=["country", "category"], suffixes=("", "_i2"))
    assert len(m) == len(ref)
    for col in ("potential_v3_TWh", "F3_bagasse_R2_TWh", "F4_self_use_TWh", "potential_adjusted_TWh", "F7_cap_99pct_TWh"):
        assert (m[col] - m[f"{col}_i2"]).abs().max() <= 1e-6, col
    a = tab[tab.country == "ASEAN11"].iloc[0]
    assert a.potential_v3_TWh == pytest.approx(1990.82, abs=0.005) and a.potential_adjusted_TWh == pytest.approx(1618.48, abs=0.005)
    assert a.F3_bagasse_R2_TWh == pytest.approx(-25.97, abs=0.005) and a.F4_self_use_TWh == pytest.approx(-346.36, abs=0.005)
    import io
    buf = io.StringIO(); adj.to_csv(buf, index=False, lineterminator="\n")
    assert B.OUT.read_text() == buf.getvalue()   # the committed table is the rule's output
    f = pd.read_csv(B.OUT)
    assert pd.read_csv(ROOT / "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv").shape == f.shape   # v3.1 file unchanged, same layout


def test_overflow_cap_share_in_the_build_rule():
    import s2_layers as L
    # VN-like case: fixed demand above 0.99 x potential -> overflow to the 99 % cap, 1 % of the pool free
    ov_ind, ov_ag, cap, binding = L.biomass_overflow(120.0, 5.0, 120.37 * 0.99, 1.0, 0.999)
    assert cap == pytest.approx(119.1663) and ov_ind + ov_ag == pytest.approx(125.0 - 119.1663)
    # v3.1 path unchanged: below the potential no overflow
    assert L.biomass_overflow(100.0, 0.0, 120.0, 1.0, 0.999)[:2] == (0.0, 0.0)


def test_marketed_gas_caps_and_fugitive_factors():
    import v4_gas_caps as G
    caps, fug = G.compute()
    d = fug.set_index("country").delta_cap_mwh / 1e6
    assert d.sum() == pytest.approx(-298.4, abs=0.05)
    for c, v in dict(ID=-134.0, MY=-134.9, TL=-15.5, VN=-7.5, BN=-3.2, TH=-3.1, MM=-0.2).items():
        assert d[c] == pytest.approx(v, abs=0.05), c
    w = pd.read_csv(W12 / "W12_1_FUGITIVE_FACTOR_COUPLING.csv").set_index("country")
    f = fug.set_index("country")
    for c in w.index:
        assert f.at[c, "gas_cap_marketed_mwh"] == pytest.approx(w.at[c, "gas_cap_marketed_mwh"], rel=1e-9)   # W12 summed floats (VN +2.5e-4 MWh)
        assert f.at[c, "factor_t_per_mwh"] == pytest.approx(w.at[c, "factor_marketed_basis_t_per_mwh"], rel=1e-9)
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    for r in caps.itertuples():
        if r.cap_mwh_per_year > 0:
            assert reg.loc[r.fugitive_factor_id, "unit"].startswith("tCO2/MWh")
            assert float(reg.loc[r.fugitive_factor_id, "value"]) == pytest.approx(f.at[r.country, "factor_t_per_mwh"], rel=1e-11)
    committed = pd.read_csv(G.V4, float_precision="round_trip").set_index("country").cap_mwh_per_year
    assert (committed - caps.set_index("country").cap_mwh_per_year).abs().max() == 0.0
