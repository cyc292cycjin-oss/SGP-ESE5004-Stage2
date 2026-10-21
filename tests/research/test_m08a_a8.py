"""M08a A8 (decisions 128, 133): GATES_V6 and the pre-registered run rules (synthetic files; no build, no solve, no Gurobi)."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project")); sys.path.insert(0, str(ROOT / "scripts_project" / "v5"))
import gates_v6 as g6   # noqa: E402

FAKE = ROOT / "tests/research/fixtures/m08a_fake_pipeline.py"


@pytest.fixture(scope="module")
def cfg():
    from phase4_static import config
    return config(ROOT, "integrated")


def test_definition_pinned():
    p = ROOT / "research/06_scope_redesign/p1_step4r_20261020/GATES_V6.md"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == g6.GATES_V6_SHA256 and g6.K == 10.0


def test_d2_budget_follows_barconvtol():
    assert g6.d2_budget({"BarConvTol": 1e-8}) == pytest.approx(1e-5)      # max(OptimalityTol 1e-6, 1e-8) x 10
    assert g6.d2_budget({"BarConvTol": 1e-6}) == pytest.approx(1e-5)
    assert g6.d2_budget({"BarConvTol": 1e-5}) == pytest.approx(1e-4)
    assert g6.d2_budget({"BarConvTol": 1e-8, "OptimalityTol": 1e-4}) == pytest.approx(1e-3)
    gates = {"A1_A2_S4B": {"dual_sign_normalized_max": 5e-5, "stationarity_normalized_max": 1e-7}}
    tight = g6.diagnostics({"solver_parameters": {"BarConvTol": 1e-8}}, gates, None, None)["D2_dual"]
    loose = g6.diagnostics({"solver_parameters": {"BarConvTol": 1e-5}}, gates, None, None)["D2_dual"]
    assert tight["within"] is False and tight["max_ratio"] == pytest.approx(5.0) and loose["within"] is True and loose["max_ratio"] == pytest.approx(0.5)


def test_subset_hash_ignores_profiles_and_follows_switches(cfg):
    R = cfg["research"]; h = g6.config_subset_sha256(R)
    for path, val in [("solver.profiles.new_profile", {"Method": 2}), ("solver.profile", "formal_barrier_1e6_t16"), ("solver.run_rules.formal_time_limit_s", 1.0),
                      ("solver.acceptance", "decision_120"), ("stage", "X")]:
        r = copy.deepcopy(R); d = r
        for k in path.split(".")[:-1]:
            d = d.setdefault(k, {})
        d[path.split(".")[-1]] = val
        assert g6.config_subset_sha256(r) == h, path
    for path, val in [("cross_border.stock_mode", "keep_stock_no_new"), ("disconnected.co2_shipping_intra_asean", "forbid"), ("coalition.remove_countries", ["VN"]),
                      ("finance.wacc_mode", "country_specific"), ("cross_border.electricity", False), ("solver.interior.solver_tol_factor", 100),
                      ("cost_layer.layers.technology_data_v0_15_0_2050_eur2020.rebase_index", "ea20_gdp_deflator"), ("s3.gas.lng_expansion", "cap_factor_cost"),
                      ("cost_layer.smr_cost_source", "aeo8_author_rule_2050"), ("site_candidates.geothermal.p_nom_max", 1.0)]:
        r = copy.deepcopy(R); d = r
        for k in path.split(".")[:-1]:
            d = d[k]
        d[path.split(".")[-1]] = val
        assert g6.config_subset_sha256(r) != h, path


def test_subset_keys_equal_notes_section_6():
    """M08a supplement 01 item 1: the implemented key list equals GATES_V6_NOTES.md section 6 (26 keys of GATES_V6.md section 2 + 4)."""
    notes = (ROOT / "research/06_scope_redesign/p1_step4r_20261020/GATES_V6_NOTES.md").read_text(encoding="utf-8")
    sec = notes.split("## 6.", 1)[1]
    rows = [ln for ln in sec.splitlines() if ln.startswith("| `GATES_V6.md`") or ln.startswith("| 按 G2.2")]
    import re
    listed = [re.findall(r"`([a-z0-9_.]+)`", r.split("|")[2]) for r in rows]
    assert tuple(listed[0]) == g6.SUBSET_KEYS_GATES_V6 and len(listed[0]) == 26
    assert [k for k in listed[1] if k in g6.SUBSET_KEYS_M08A_ADDITIONS] == list(g6.SUBSET_KEYS_M08A_ADDITIONS) and len(g6.SUBSET_KEYS) == 30


def test_tolerance_diagnostics_d7_d9_d10():
    eps = 1e-6
    for cap in (1.0, 1e6, 3.7e9):
        assert g6.within_cap(cap * (1 + 1e-9), cap, eps)[0] is True
        assert g6.within_cap(cap * (1 + 1e-3) + 1.0, cap, eps)[0] is False
    assert g6.within_cap(1e12, float("inf"), eps)[0] is True
    gates = {"B2": {"countries": {"VN": {"final_level_t": 1.06e8 * (1 + 1e-9), "horizon_limit_t": 1.06e8}}},
             "B14": {"terminals": [{"generator": "x", "p_nom_opt_mw": 5e3, "p_nom_max_mw": float("inf")}]},
             "B15": {"by_country": {"ID": {"cap_mwh": 1e8, "annual_mwh": 1e8 * (1 + 1e-9)}}}}
    D = g6.diagnostics({"solver_parameters": {}}, gates, None, None)
    assert D["D7_storage_caps"]["within"] and D["D9_terminal_caps"]["within"] and D["D10_domestic_gas_caps"]["within"]


def solve_dir(tmp: Path, abc="111", term="optimal", subset=("s" * 64, "s" * 64), net_sha="n" * 64):
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "LEDGER.csv").write_text("x\n")
    ex = {"LEDGER.csv": {"sha256": hashlib.sha256(b"x\n").hexdigest()}}
    (tmp / "EXPORTS.json").write_text(json.dumps(ex))
    (tmp / "SOLVE_RECEIPT.json").write_text(json.dumps(dict(input_network=dict(sha256=net_sha, snapshots=2920), lp=dict(num_col=3, num_row=4),
        solution=dict(X=dict(count=3), Pi=dict(count=4), RC=dict(count=3)), solver_parameters=dict(BarConvTol=1e-8), termination_condition=term, objective=1.0,
        config_subset=dict(network=subset[0], current=subset[1]))))
    (tmp / "V5_GATES.json").write_text(json.dumps(dict(A4=dict(passed=True, status="EXACT_SEMANTIC_ROUNDTRIP"), B16_LEDGER=dict(relative_error=1e-10))))
    (tmp / "PRECISION.json").write_text(json.dumps(dict(computable=True, a_total_cost=dict(passed=abc[0] == "1"), b_primal_violations=dict(passed=abc[1] == "1"),
                                                        c_prices=dict(passed=abc[2] == "1"))))
    return tmp


def test_labels(tmp_path):
    assert g6.acceptance_v6(solve_dir(tmp_path / "a"), "n" * 64)["label"] == "ACCEPTED_LAYER2"
    assert g6.acceptance_v6(solve_dir(tmp_path / "b", term="suboptimal"), "n" * 64)["label"] == "ACCEPTED_LAYER2"   # status is not a criterion (D0)
    assert g6.acceptance_v6(solve_dir(tmp_path / "c", abc="110"), "n" * 64)["label"] == "ACCEPTED_LAYER1"
    assert g6.acceptance_v6(solve_dir(tmp_path / "d", abc="101"), "n" * 64)["label"] == "NOT_ACCEPTED"
    assert g6.acceptance_v6(solve_dir(tmp_path / "e", subset=("s" * 64, "t" * 64)), "n" * 64)["label"] == "NOT_ACCEPTED"   # G2.2
    assert g6.acceptance_v6(solve_dir(tmp_path / "f"), "m" * 64)["label"] == "NOT_ACCEPTED"                              # G2.1
    d = solve_dir(tmp_path / "g"); (d / "LEDGER.csv").write_text("changed\n")
    assert g6.acceptance_v6(d, "n" * 64)["label"] == "NOT_ACCEPTED"                                                        # G2.3


def test_run_rules_registered(cfg):
    r = g6.run_rules(cfg)
    assert cfg["research"]["solver"]["acceptance"] == "gates_v6" and r["formal_time_limit_s"] == 172800.0 and r["formal_requires"] == ["c"]
    ch = r["profile_chain"]
    assert (ch["candidate"], ch["reference"], ch["fallback"], ch["objective_rel_diff_vs_reference_max"]) == ("formal_barrier_1e6_t16", "formal_barrier", "formal_barrier", 1e-5)
    assert "pypsa_eur_default" in ch["never_fallback"] and r["on_non_convergence"].endswith("no_retry_no_parameter_change")
    assert set(ch) >= {"candidate", "level2_resolution"} and ch["level2_resolution"] == "365x24h"


def test_profile_chain(cfg):
    r = g6.run_rules(cfg)
    ok = lambda obj: dict(candidate=dict(profile="formal_barrier_1e6_t16", objective=obj, precision=dict(a=True, b=True, c=True)), reference=dict(profile="formal_barrier", objective=1e11))
    assert g6.select_formal_profile({"integrated": ok(1e11 * (1 + 4e-6)), "disconnected": ok(1e11)}, r)["profile"] == "formal_barrier_1e6_t16"
    assert g6.select_formal_profile({"integrated": ok(1e11 * (1 + 2e-5)), "disconnected": ok(1e11)}, r)["profile"] == "formal_barrier"
    bad = ok(1e11); bad["candidate"]["precision"]["c"] = False
    assert g6.select_formal_profile({"integrated": ok(1e11), "disconnected": bad}, r)["profile"] == "formal_barrier"
    assert g6.select_formal_profile({}, r)["profile"] == "formal_barrier"


def test_formal_run_decision(tmp_path, cfg):
    r = g6.run_rules(cfg)
    l1 = g6.acceptance_v6(solve_dir(tmp_path / "l1", abc="110", term="time_limit"), "n" * 64)
    d = g6.formal_run_decision(l1, r)
    assert d["formal"] and d["label"] == "ACCEPTED_LAYER1" and d["usable_for_allocation"] is False and d["usable_total_cost_only"] is True and d["retry"] is False
    l2 = g6.acceptance_v6(solve_dir(tmp_path / "l2"), "n" * 64)
    assert g6.formal_run_decision(l2, r)["usable_for_allocation"] is True


def _nets(tmp: Path):
    nets = tmp / "nets"; nets.mkdir()
    for sc in ("integrated", "disconnected"):
        for res in ("365_24h", "2920_3h"):
            p = nets / f"{sc}_{res}_unsolved.nc"; p.write_bytes(f"{sc}{res}".encode())
        (nets / f"{sc}_costs_active_research.csv").write_text("technology\n")
        (nets / f"{sc}_BUILD_RECEIPT.json").write_text(json.dumps(dict(network=dict(sha256=hashlib.sha256(f"{sc}2920_3h".encode()).hexdigest()),
                                                                     daily_network=dict(sha256=hashlib.sha256(f"{sc}365_24h".encode()).hexdigest(), snapshots=365))))
    return nets


def _run(tmp, kind, env_extra):
    py = sys.executable
    env = dict(os.environ, RUN_KIND=kind, REPO=str(ROOT), NETS=str(tmp / "nets"), OUT=str(tmp / "out"), PY=py,
               SOLVE_CMD=f"{py} {FAKE} solve", VA_CMD=f"{py} {FAKE} va", C1_CMD=f"{py} {FAKE} c1", VAR_CMD=f"{py} {FAKE} variants", **env_extra)
    return subprocess.run(["bash", str(ROOT / "scripts_project/m08a_run_batch.sh")], env=env, capture_output=True, text=True, timeout=600)


def test_runner_level2_then_formal(tmp_path):
    _nets(tmp_path)
    p = _run(tmp_path, "level2", {"FAKE_OBJ_formal_barrier": "1e11", "FAKE_OBJ_formal_barrier_1e6_t16": "100000000400"})
    assert p.returncode == 0, p.stderr[-800:]
    out = tmp_path / "out"
    calls = [x for x in (out / "CALLS.txt").read_text().splitlines() if x.startswith("solve ")]
    loo = [f"solve integrated_A_minus{c} formal_barrier 21600" for c in ("VN", "TH", "LA")]                    # M12 supplement 01 D7: third batch only
    assert sorted(calls) == sorted([f"solve {sc}_{t} {pr} 21600" for sc in ("integrated", "disconnected") for t, pr in (("A", "formal_barrier"), ("CAND", "formal_barrier_1e6_t16"))] + loo)
    assert json.loads((out / "PROFILE_CHOICE.json").read_text())["profile"] == "formal_barrier_1e6_t16"      # rel diff 4e-9 <= 1e-5, C1 all passed
    assert json.loads((out / "integrated_CAND" / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2"
    n2 = len(calls)
    p = _run(tmp_path, "formal", {"FAKE_C1_integrated": "000"})                                                  # first formal run NOT_ACCEPTED -> stop
    assert p.returncode == 0, p.stderr[-800:]
    calls = [x for x in (out / "CALLS.txt").read_text().splitlines() if x.startswith("solve ")][n2:]
    assert calls == ["solve integrated formal_barrier_1e6_t16 172800.0"]                                         # once, 48 h, no retry, disconnected not started
    st = (out / "STATUS.txt").read_text()
    assert "STOP_NOT_ACCEPTED:integrated" in st and (out / "STOP_NOT_ACCEPTED").exists()
    assert json.loads((out / "integrated" / "FORMAL_DECISION.json").read_text())["retry"] is False


def test_runner_refuses_the_1e5_profile(tmp_path):
    _nets(tmp_path); (tmp_path / "pc.json").write_text(json.dumps(dict(profile="pypsa_eur_default")))
    p = _run(tmp_path, "formal", {"PROFILE_CHOICE": str(tmp_path / "pc.json")})
    assert p.returncode == 3 and "REFUSED_PROFILE:pypsa_eur_default" in (tmp_path / "out" / "STATUS.txt").read_text()
    assert not (tmp_path / "out" / "CALLS.txt").exists()
