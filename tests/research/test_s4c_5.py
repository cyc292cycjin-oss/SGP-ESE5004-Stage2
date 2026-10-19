"""S4C-5 (decision 69 c / 84): Kirchhoff-Voltage-Law row normalisation is an exact reformulation (rhs 0): same objective and flows,
KVL duals restored by pi = pi_normalised / row_max; solver profile C registered."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s3b_scaling import KVL_ROW, normalise_kvl_rows, unscale_kvl_duals  # noqa: E402

CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())


def _loop():
    import pypsa
    n = pypsa.Network(); n.set_snapshots(range(3))
    for b in "abcd":
        n.add("Bus", b, v_nom=380.0)
    for name, b0, b1, x in [("ab", "a", "b", 10.0), ("bc", "b", "c", 30.0), ("ca", "c", "a", 5.0), ("cd", "c", "d", 2.0), ("da", "d", "a", 80.0)]:
        n.add("Line", name, bus0=b0, bus1=b1, x=x, s_nom=1000.0)
    n.add("Generator", "g", bus="a", p_nom=500.0, marginal_cost=1.0)
    n.add("Generator", "g2", bus="b", p_nom=500.0, marginal_cost=5.0)
    n.add("Load", "l", bus="c", p_set=[80.0, 150.0, 200.0])
    n.add("Load", "l2", bus="d", p_set=[10.0, 20.0, 30.0])
    return n


def test_kvl_normalisation_exact():
    n0 = _loop(); m0 = n0.optimize.create_model(); assert m0.solve(solver_name="highs")[0] == "ok"
    obj0 = float(m0.objective.value); flow0 = m0["Line-s"].solution.values; pi0 = m0.constraints[KVL_ROW].dual.values
    n1 = _loop(); m1 = n1.optimize.create_model()
    before = np.abs(m1.constraints[KVL_ROW].coeffs.values); led = normalise_kvl_rows(m1)
    c = m1.constraints[KVL_ROW]; after = np.abs(c.coeffs.where(c.vars != -1).values)
    assert led["applied"] and led["rows"] == 2 * 3   # two independent cycles x three snapshots
    assert np.allclose(np.nanmax(after, axis=-1), 1.0)
    assert led["coefficients_before"]["ratio"] > led["coefficients_after"]["ratio"] >= 1.0 or led["coefficients_after"]["max"] == pytest.approx(1.0)
    assert m1.solve(solver_name="highs")[0] == "ok"
    assert float(m1.objective.value) == pytest.approx(obj0, rel=1e-9)
    assert np.allclose(m1["Line-s"].solution.values, flow0, atol=1e-6)
    unscale_kvl_duals(m1, led)
    assert np.allclose(m1.constraints[KVL_ROW].dual.values, pi0, rtol=1e-6, atol=1e-9)


def test_profiles_and_switch():
    S = CFG["research"]["solver"]
    C = S["profiles"]["barrier_numericfocus2"]; A = S["profiles"]["formal_barrier"]
    assert C["NumericFocus"] == 2 and {k: v for k, v in C.items() if k != "NumericFocus"} == A
    assert S["profile"] == "formal_barrier" and S["scaling"]["kirchhoff_row_normalisation"] is True   # decision 121 (S4O supplement 01): production default back to profile A
