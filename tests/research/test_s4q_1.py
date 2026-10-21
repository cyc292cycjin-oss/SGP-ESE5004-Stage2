"""S4Q-1 (decision 123): the two NON-production candidate profiles of the BarConvTol 1e-6 calibration - formal_barrier_1e6 (Threads 8) and
formal_barrier_1e6_t16 (Threads 16). Each must equal profile A formal_barrier key by key except the listed differences (single factor, two iteration
paths); the production default stays formal_barrier; the run pipeline accepts both and keeps its defaults (FIXED_RUNS off). No Gurobi, no licence."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s2_solve import interior_solution, profile_parameters  # noqa: E402

CFG_TEXT = (ROOT / "configs/research/baseline.yaml").read_text()
SV = yaml.safe_load(CFG_TEXT)["research"]["solver"]
RUN_SCRIPT = (ROOT / "research/06_scope_redesign/p1_step4o_20261019/cloud_package/run_365x24h.sh").read_text()
EXPECTED_DIFF = {"formal_barrier_1e6": {"BarConvTol": 1e-6}, "formal_barrier_1e6_t16": {"BarConvTol": 1e-6, "Threads": 16}}   # S4Q-1 table


def test_candidates_equal_profile_A_except_listed_differences():
    A = SV["profiles"]["formal_barrier"]
    assert A == {"Method": 2, "Crossover": 0, "BarConvTol": 1e-8, "BarHomogeneous": 1, "Threads": 8, "Seed": 123, "AggFill": 0, "PreDual": 0, "GURO_PAR_BARDENSETHRESH": 200}
    for name, diff in EXPECTED_DIFF.items():
        P = SV["profiles"][name]
        assert list(P) == list(A), name   # same keys in the same order, nothing added or dropped
        for k in A:   # key by key
            if k in diff:
                assert P[k] == diff[k] and P[k] != A[k] and type(P[k]) is type(A[k]), (name, k)
            else:
                assert P[k] == A[k] and type(P[k]) is type(A[k]), (name, k)
        assert {k: P[k] for k in P if P[k] != A[k]} == diff, name


def test_production_default_unchanged_and_candidates_marked():
    assert SV["profile"] == "formal_barrier"
    for name in EXPECTED_DIFF:
        line = next(ln for ln in CFG_TEXT.splitlines() if re.match(rf"\s+{name}:\s*\{{", ln))
        comment = line.split("#", 1)[1]
        assert "decision 123" in comment and "NON-production" in comment and "single factor" in comment and "two paths" in comment, name


def test_candidates_pass_key_name_check_and_take_interior_gate_path():
    for name, diff in EXPECTED_DIFF.items():
        p = profile_parameters(SV["profiles"], name, 1750)
        assert p["TimeLimit"] == 1750.0 and p["BarConvTol"] == 1e-6 and p["Threads"] == diff.get("Threads", 8)
        assert interior_solution("gurobi", p)   # Crossover 0 -> interior-point gate path as profile A


def test_run_pipeline_accepts_candidates_and_keeps_defaults():
    case = next(ln for ln in RUN_SCRIPT.splitlines() if ln.startswith('case "$PROFILE" in'))
    allowed = case.split(" in ", 1)[1].split(")", 1)[0].split("|")
    assert {"formal_barrier", "formal_barrier_1e6", "formal_barrier_1e6_t16"} <= set(allowed)
    assert '[ -n "$PROFILE" ] || { PROFILE=formal_barrier;' in RUN_SCRIPT   # default profile A (decision 121)
    assert 'FIXED_RUNS="${FIXED_RUNS:-off}"' in RUN_SCRIPT   # default: S4O stop rule and automatic diagnostic unchanged
