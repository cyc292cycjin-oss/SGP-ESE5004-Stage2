"""S4K-1 (decision 108): AC lines - linear loss proxy instead of the PyPSA piecewise tangents (model structure only, no solve)."""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4k_layers import (LAMBDA_COL, PROXY_HOOK, PYPSA_TANGENTS, REFERENCE_TYPE, ac_loss_mode, apply_ac_losses, install_ac_loss_proxy,  # noqa: E402
                        line_lambda, reference_check, reference_loading)

CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
C = ROOT / "research_inputs/corridors"
B = ROOT / "results_project/s4k/s4k1/builds/integrated/integrated_2920_3h_unsolved.nc"


def toy(extendable_second: bool = True):
    import pypsa
    n = pypsa.Network(); n.set_snapshots(range(3))
    for i, x in enumerate((0.0, 1.0, 2.0)):
        n.add("Bus", f"b{i}", v_nom=380.0, x=100.0 + x, y=10.0, carrier="AC")
    n.add("Line", "l0", bus0="b0", bus1="b1", type=REFERENCE_TYPE, length=100.0, s_max_pu=0.7, s_nom=1000.0, num_parallel=1.0)
    n.add("Line", "l1", bus0="b1", bus1="b2", type=REFERENCE_TYPE, length=250.0, s_max_pu=0.7, s_nom=0.0, s_nom_extendable=extendable_second,
          s_nom_max=20000.0, capital_cost=1.0, num_parallel=1.0)
    n.add("Generator", "g0", bus="b0", p_nom=5000.0, marginal_cost=10.0)
    n.add("Load", "d2", bus="b2", p_set=300.0)
    n.add("Load", "d1", bus="b1", p_set=200.0)
    return n


def test_switches():
    assert ac_loss_mode(CFG) == "linear_proxy" and reference_loading(CFG) == 0.5
    c = copy.deepcopy(CFG); del c["research"]["network"]["ac_losses"]; del c["research"]["network"]["ac_loss_reference_loading"]
    assert ac_loss_mode(c) == "pypsa_tangent" and reference_loading(c) == 0.5
    c["research"]["network"]["ac_losses"] = "quadratic"
    with pytest.raises(ValueError):
        ac_loss_mode(c)
    c["research"]["network"]["ac_loss_reference_loading"] = 0.0
    with pytest.raises(ValueError):
        reference_loading(c)
    assert PYPSA_TANGENTS == 2


def test_lambda_formula_and_reference():
    n = toy()
    T = line_lambda(n, 0.5)
    exp = math.sqrt(3) * 0.5 * 0.7 * 2.58 * 0.03 * 100.0 / 380.0
    assert abs(T.at["l0", "ac_loss_lambda"] - exp) < 1e-15 and abs(T.at["l1", "ac_loss_lambda"] / T.at["l0", "ac_loss_lambda"] - 2.5) < 1e-12
    assert abs(line_lambda(n, 1.0).at["l0", "ac_loss_lambda"] - 2 * exp) < 1e-15
    ref = reference_check(n)
    assert ref["0.5"]["within"] and ref["1.0"]["within"] and abs(ref["0.5"]["lambda_100km"] - 0.012348) < 1e-5
    n.lines.loc["l0", "num_parallel"] = 7.0   # one circuit: lambda does not depend on num_parallel
    assert abs(line_lambda(n, 0.5).at["l0", "ac_loss_lambda"] - exp) < 1e-15


def test_apply_modes():
    n = toy(); losses = dict(mode="pypsa_eur", ac_transmission_losses=2)
    led = apply_ac_losses(n, CFG, losses)
    assert led["mode"] == "linear_proxy" and losses["ac_transmission_losses"] == 0 and PROXY_HOOK in n.meta["required_constraint_hooks"] and LAMBDA_COL in n.lines
    c = copy.deepcopy(CFG); c["research"]["network"]["ac_losses"] = "pypsa_tangent"
    n2 = toy(); l2 = dict(mode="pypsa_eur", ac_transmission_losses=2)
    assert apply_ac_losses(n2, c, l2)["mode"] == "pypsa_tangent" and l2["ac_transmission_losses"] == 2 and LAMBDA_COL not in n2.lines
    n3 = toy(); l3 = dict(mode="none", ac_transmission_losses=0)
    assert apply_ac_losses(n3, CFG, l3)["mode"] == "none" and l3["ac_transmission_losses"] == 0 and PROXY_HOOK not in n3.meta.get("required_constraint_hooks", [])


def test_proxy_hook_structure():
    n = toy(); apply_ac_losses(n, CFG, dict(mode="pypsa_eur", ac_transmission_losses=2))
    m = n.optimize.create_model(transmission_losses=0)
    led = install_ac_loss_proxy(n)
    assert "Line-loss" in m.variables and m["Line-loss"].size == 3 * 2
    for k in ("Line-loss_proxy-pos", "Line-loss_proxy-neg", "Line-fix-loss_upper", "Line-ext-loss_upper", "Line-fix-s-upper", "Line-ext-s-upper"):
        assert k in m.constraints, k
    assert "Bus-nodal_balance" in led["rebuilt"]
    nb = m.constraints["Bus-nodal_balance"]; LL = np.asarray(m["Line-loss"].labels.values).ravel()
    V, Cc = np.asarray(nb.vars.values).ravel(), np.asarray(nb.coeffs.values).ravel()
    sel = np.isin(V, LL)
    assert sel.sum() == 2 * LL.size and np.allclose(Cc[sel], -0.5)
    up = m.constraints["Line-ext-s-upper"]; V, Cc = np.asarray(up.vars.values).ravel(), np.asarray(up.coeffs.values).ravel()
    assert np.allclose(Cc[np.isin(V, LL)], 1.0)
    lo = m.constraints["Line-fix-s-lower"]; V, Cc = np.asarray(lo.vars.values).ravel(), np.asarray(lo.coeffs.values).ravel()
    assert np.allclose(Cc[np.isin(V, LL)], -1.0)
    with pytest.raises(ValueError):
        install_ac_loss_proxy(n)
    n2 = toy(); apply_ac_losses(n2, CFG, dict(mode="pypsa_eur", ac_transmission_losses=2))
    n2.optimize.create_model(transmission_losses=2)
    with pytest.raises(ValueError):
        install_ac_loss_proxy(n2)


@pytest.mark.skipif(not (C / "AC_LOSS_PROXY_S4K1.json").exists(), reason="S4K-1 tables not present")
def test_tables():
    T = pd.read_csv(C / "LAMBDA_S4K1.csv")
    assert len(T) == 148 and (T.type == REFERENCE_TYPE).all() and np.allclose(T.lambda_alpha_1_0, 2 * T.lambda_alpha_0_5)
    js = json.loads((C / "AC_LOSS_PROXY_S4K1.json").read_text())
    assert all(v["within"] for v in js["reference_check"].values())
    mc = js["model_check"]
    assert mc["solver_transmission_losses"] == 0 and mc["loss_variables"] == 56 * mc["lines"]
    assert all(v["minus_loss_terms_equal"] for v in mc["compare"].values())
    nb = [v for k, v in mc["compare"].items() if k.endswith("nodal_balance")]
    assert sum(v["loss_terms"] for v in nb) == 2 * mc["loss_variables"] and all(v["loss_coefficients"] in ([-0.5], []) for v in nb)
    assert mc["compare"]["Kirchhoff-Voltage-Law"]["loss_terms"] == 0


@pytest.mark.skipif(not B.exists(), reason="S4K-1 build not present")
def test_build():
    import pypsa
    n = pypsa.Network(str(B))
    assert n.meta["research_ac_losses"]["mode"] == "linear_proxy" and PROXY_HOOK in n.meta["required_constraint_hooks"]
    assert int(n.meta["research_transmission_losses"]["ac_transmission_losses"]) == 0
    assert np.allclose(n.lines[LAMBDA_COL], line_lambda(n, 0.5).ac_loss_lambda)
