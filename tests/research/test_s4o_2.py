"""S4O-2 (decision 120) / S4O supplement 01 (decision 121): solver profiles - production profile A formal_barrier (decision 121), the registered
non-production profile pypsa_eur_default (key names, Threads 8), key-name recognition, interior-point gate path - and the C1 precision step of the
run pipeline (decision 119 (a)(b)(c)) on a toy LP; no Gurobi, no licence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s2_solve import interior_solution, profile_parameters  # noqa: E402
import s4o_c1_precision as C1  # noqa: E402

CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
SV = CFG["research"]["solver"]
SRC = ROOT / "research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml"


def test_production_profile_A_and_registered_pypsa_eur_default():
    P = SV["profiles"]["pypsa_eur_default"]
    assert SV["profile"] == "formal_barrier"   # decision 121: production back to profile A; pypsa_eur_default kept as a registered non-production profile
    assert P == {"Threads": 8, "Method": 2, "Crossover": 0, "BarConvTol": 1e-5, "Seed": 123, "AggFill": 0, "PreDual": 0, "GURO_PAR_BARDENSETHRESH": 200}
    src = yaml.safe_load(SRC.read_text())["solving"]["solver_options"]["gurobi-default"]   # PyPSA-Eur v2025.07.0 lines 1056-1064
    assert {k.lower(): v for k, v in src.items() if k != "threads"} == {k.lower(): v for k, v in P.items() if k != "Threads"} and src["threads"] == 32
    A = SV["profiles"]["formal_barrier"]   # profile A unchanged (verification reference)
    assert A == {"Method": 2, "Crossover": 0, "BarConvTol": 1e-8, "BarHomogeneous": 1, "Threads": 8, "Seed": 123, "AggFill": 0, "PreDual": 0, "GURO_PAR_BARDENSETHRESH": 200}
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    assert reg.at["s4o_decision_120_production_profile", "decision_ref"] == "107,119,120" and "Threads 8" in reg.at["s4o_decision_120_production_profile", "description"]
    r121 = reg.loc["s4o_decision_121_production_profile_A"]
    assert r121["value"] == "formal_barrier" and "121" in r121["decision_ref"] and "0.01 bn" in r121["description"]


def test_profile_key_names_recognised():
    for name in SV["profiles"]:   # every configured profile passes the key-name check
        p = profile_parameters(SV["profiles"], name, 60)
        assert p["TimeLimit"] == 60.0
    with pytest.raises(ValueError, match="code convention"):   # S4N finding 10: lowercase keys copied from PyPSA-Eur are refused
        profile_parameters({"raw": {"threads": 32, "method": 2, "crossover": 0, "BarConvTol": 1e-5}}, "raw", 60)
    assert profile_parameters({"x": {"Crossover": 0, "GURO_PAR_BARDENSETHRESH": 200}}, "x", 1)["GURO_PAR_BARDENSETHRESH"] == 200


def test_interior_gate_path():
    prof = SV["profiles"]
    assert interior_solution("gurobi", profile_parameters(prof, "pypsa_eur_default", 60))   # Crossover 0 -> interior-point gate path (was missed with lowercase keys)
    assert interior_solution("gurobi", profile_parameters(prof, "formal_barrier", 60))
    assert not interior_solution("gurobi", profile_parameters(prof, "crossover_diagnostic", 60))
    assert not interior_solution("highs", profile_parameters(prof, "pypsa_eur_default", 60))
    assert not interior_solution("gurobi", {"crossover": 0})   # lowercase key is not read: this is why the profile keys are capitalised


def _toy():
    """min c x  s.t.  l <= A x <= u, bounds; solved by HiGHS through scipy (duals = marginals; scipy and Gurobi share the sign convention used by C1)."""
    from scipy.optimize import linprog
    import scipy.sparse as sp
    c = np.array([2.0, 3.0, 1.0])
    A = np.array([[1.0, 1.0, 0.0], [0.0, 1.0, 1.0], [1.0, 0.0, 1.0]])
    lo = np.array([4.0, 3.0, -np.inf]); hi = np.array([np.inf, np.inf, 6.0])   # x0 + x1 >= 4, x1 + x2 >= 3, x0 + x2 <= 6
    cl = np.zeros(3); cu = np.array([np.inf, 10.0, np.inf])
    r = linprog(c, A_ub=np.vstack([-A[:2], A[2:]]), b_ub=np.concatenate([-lo[:2], hi[2:]]), bounds=list(zip(cl, [None, 10.0, None])), method="highs")
    assert r.status == 0
    pi = np.concatenate([-r.ineqlin.marginals[:2], r.ineqlin.marginals[2:]])   # >= rows: d obj / d lo = -marginal of the negated <= row
    rc = r.lower.marginals + r.upper.marginals
    return sp.csc_matrix(A), c, r.x, pi, rc, lo, hi, cl, cu, r.fun


def test_c1_kkt_terms_toy_model():
    A, c, x, pi, rc, lo, hi, cl, cu, obj = _toy()
    T = C1.kkt_terms(A, c, x, pi, rc, lo, hi, cl, cu)
    assert np.abs(c - A.T @ pi - rc).max() < 1e-9   # stationarity holds at the optimum (sign convention check)
    assert T["S"].sum() < 1e-9 and T["R"].sum() < 1e-9 and T["K"].sum() < 1e-9 and T["KS"].sum() < 1e-12 and T["row_violation"].max() < 1e-9
    assert abs(float(c @ x) - obj) < 1e-9 and abs(float(lo[:2] @ pi[:2] + hi[2:] @ pi[2:]) - obj) < 1e-9   # primal = dual objective
    xb = x + np.array([-0.5, 0.0, 0.0])   # a primal violation of the first row and a non-stationary / non-complementary point
    pib = pi + np.array([0.0, 0.0, -0.25])
    Tb = C1.kkt_terms(A, c, xb, pib, rc, lo, hi, cl, cu)
    assert Tb["row_violation"][0] == pytest.approx(0.5) and Tb["S"].sum() > 0 and Tb["R"].sum() > 0


def _res(first_order_bn: float, s_plus_r_bn: float, termination="optimal", a_ok=True, b16=1e-9) -> dict:
    cc_b = {c: dict(first_order_cost_bn=(first_order_bn if c == "PH" else 0.0)) for c in C1.ENTITIES}
    cc_c = {c: dict(stationarity_bn=0.0, row_complementarity_bn=0.0, S_plus_R_bn=(s_plus_r_bn if c == "PH" else 0.0), column_complementarity_bn=0.0, column_dual_sign_bn=0.0,
                    all_terms_bn=(s_plus_r_bn if c == "PH" else 0.0)) for c in C1.ENTITIES}
    bp = dict(rows_over_budget_on_BN_SG_VN_pools=0, rows_over_budget_total=0, max_ratio_row_is_BN_SG_VN_pool=False, dominant=False)
    return dict(solve_dir="toy", termination=termination, objective=1.0, computable=True,
                a_total_cost=dict(passed=a_ok, kkt_summary_returned_arrays={}, returned_difference_bn=0.0, returned_relative=0.0),
                b_primal_violations=dict(country_check=cc_b, rows_violated=0, rows_over_budget=0, consistency_with_l23_script=dict(equal=True), row_violation_max=0.0,
                                         row_max_ratio=0.0, first_order_cost_eur_all_rows=0.0, biomass_pools_BN_SG_VN=bp),
                c_prices=dict(country_check=cc_c, b16=dict(relative_error=b16, passed=b16 <= 1e-6), formulas=dict(attribution="toy")))


def test_c1_grade_acceptance_and_reference():
    r = C1.apply_reference(_res(0.005, 0.005), C1.L23_REFERENCE)   # PH tolerance = max(1 % x 0.0099, 0.01) = 0.01 bn
    assert r["grade"]["grade"] == "layer1_plus_nodal_price_settlement" and r["acceptance"]["accepted"]
    assert C1.apply_reference(_res(0.005, 0.02), C1.L23_REFERENCE)["grade"]["grade"] == "layer1_total_cost_screening"   # (c) fails -> prices provisional
    assert C1.apply_reference(_res(0.02, 0.0), C1.L23_REFERENCE)["grade"]["grade"] == "not_layer1"
    nonopt = C1.apply_reference(_res(0.0, 0.0, termination="suboptimal"), C1.L23_REFERENCE)
    assert nonopt["grade"]["grade"] == "layer1_plus_nodal_price_settlement" and not nonopt["acceptance"]["accepted"]   # acceptance needs optimal (decision 120)
    big = dict(source="test", differences_bn={"PH": 3.0})   # PH tolerance 0.03 bn
    assert C1.apply_reference(_res(0.02, 0.02), big)["acceptance"]["accepted"]


def test_c1_pipeline_reference_regrade_exports(tmp_path):
    ents = list(C1.COUNTRIES) + ["ASEAN_BUNKER", "ASEAN_POOL"]
    li = pd.DataFrame({"total": [1e9 * (i + 1) for i in range(len(ents))]}, index=pd.Index(ents, name="entity"))
    ld = li.copy(); ld.loc["PH", "total"] += 2.5e9; ld.loc["ASEAN_BUNKER", "total"] -= 1.0e9; ld.loc["ASEAN_POOL", "total"] -= 0.25e9
    (tmp_path / "i").mkdir(); (tmp_path / "d").mkdir(); li.to_csv(tmp_path / "i/COUNTRY_COST_LEDGER.csv"); ld.to_csv(tmp_path / "d/COUNTRY_COST_LEDGER.csv")
    ref = C1.reference_from_ledgers(tmp_path / "i", tmp_path / "d")
    assert ref["differences_bn"]["PH"] == pytest.approx(2.5) and ref["differences_bn"]["ASEAN"] == pytest.approx(-1.25) and ref["differences_bn"]["VN"] == 0.0
    sd = tmp_path / "run"; sd.mkdir(); (sd / "EXPORTS.json").write_text(json.dumps({"DUALS_INDEX.csv": {"bytes": 1, "sha256": "x"}}))
    C1.write(sd, C1.apply_reference(_res(0.02, 0.02), C1.L23_REFERENCE))
    first = json.loads((sd / "PRECISION.json").read_text()); assert not first["acceptance"]["accepted"] and first["reference"]["source"].startswith("L23")
    res = C1.regrade(sd, ref)   # the batch's own difference: PH tolerance 0.025 bn -> passes
    assert res["acceptance"]["accepted"] and res["grade_history"][0]["grade"] == "not_layer1" and res["reference"]["source"].startswith("this batch")
    ex = json.loads((sd / "EXPORTS.json").read_text())
    assert set(ex) >= {"DUALS_INDEX.csv", "PRECISION.json", "PRECISION.md"} and ex["PRECISION.json"]["sha256"] == C1.sha(sd / "PRECISION.json")
    assert "验收" in (sd / "PRECISION.md").read_text(encoding="utf-8")


PILOT = ROOT / "research/06_scope_redesign/p1_step4n_20261019/cloud_results/20261019T072454Z_5125/unpacked/s4n_pilot_light_20261019T072454Z_5125"


@pytest.mark.skipif(not (PILOT / "PILOT_PRECISION.json").exists(), reason="S4N pilot light package not archived")
def test_c1_regrade_pilot_copy_with_batch_disconnected(tmp_path):
    """decision 121: reference = this batch's disconnected - S4N pilot integrated; the pilot's C1 (S4N tool format) is re-graded on a COPY."""
    src = PILOT / "PILOT_PRECISION.json"; before = C1.sha(src)
    ld = pd.read_csv(PILOT / "export_integrated/COUNTRY_COST_LEDGER.csv", index_col=0); ld["total"] = ld["total"] + 2e9   # synthetic disconnected: +2 bn each
    (tmp_path / "d").mkdir(); ld.to_csv(tmp_path / "d/COUNTRY_COST_LEDGER.csv")
    ref = C1.reference_from_ledgers(PILOT / "export_integrated", tmp_path / "d")
    assert ref["differences_bn"]["VN"] == pytest.approx(2.0) and ref["differences_bn"]["ASEAN"] == pytest.approx(2.0 * sum(str(k).startswith("ASEAN") for k in ld.index))
    cp = tmp_path / "pilot"; cp.mkdir(); (cp / "PRECISION.json").write_bytes(src.read_bytes())
    res = C1.regrade(cp, ref)
    assert res["grade_history"][0]["grade"] == "layer1_plus_nodal_price_settlement" and res["reference"]["source"].startswith("this batch")
    assert res["acceptance"]["optimal"] and res["acceptance"]["accepted"]   # pilot optimal, (a)(b)(c) pass with the +2 bn tolerances (0.02 bn per country)
    assert C1.sha(src) == before and (cp / "EXPORTS.json").exists()


def test_c1_not_computable_without_solution(tmp_path):
    (tmp_path / "SOLVE_RECEIPT.json").write_text(json.dumps(dict(termination_condition="time_limit")))
    res = C1.compute(ROOT, tmp_path, tmp_path / "none.nc", tmp_path / "VIOLATIONS.json", C1.L23_REFERENCE, "integrated", None, "FORMAL_TRIAL_365X24H")
    assert res["computable"] is False and res["grade"]["grade"] == "not_computable" and not res["acceptance"]["accepted"]
    C1.write(tmp_path, res); assert "无法计算" in (tmp_path / "PRECISION.md").read_text(encoding="utf-8")
