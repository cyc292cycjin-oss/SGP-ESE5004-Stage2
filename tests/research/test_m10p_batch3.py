"""M10P (instruction sections 2-5; supplement 01) + M10A (pre-cloud review): third-batch runner run_batch3.sh, preflight guards, results pack and
scripts_project/m10_batch3_summary.py.

The runner is driven end to end with SYNTHETIC stand-ins (tests/research/fixtures/m10p_fake_pipeline.py: no solver, no model) on a package-like
folder; GATES_V6, the graded stop class, the level-2 profile choice, the batch summary and the pack are the real code. The solve stand-in is
called through a wrapper named scripts_project/s2_solve.py (M10A), so the runner's running-solver count busy() sees the same command line as on
the instance (the GNU time wrapper line also holds "s2_solve.py"). Covered: the pre-registered run table and schedule (supplement 01 item 1:
R3 | R5 and R4 | R6 side by side on 25 cores, never two T16 sessions; one lane below 24 / 16 cores), licence gaps, C1 provisional -> batch
reference -> regrade with grade_history, the graded stop rule (supplement 01 item 2: R3-R11 without a returned solution or with C1 (a) failed are
recorded unusable and the batch goes on; R1 / R2 failures and any G2 failure stop the batch; the other lane's running solve finishes and is
post-processed), resume without re-solving, safe stops (interrupted solve, base network / variant SHA256, a solver process at start), wall-clock
kill of the process group (also when the solve ignores TERM), the local dry-run mode (no solver, licence tripwire), refusal of unregistered
limits, of test hooks in a formal run and of --auth in the no-solve modes, the preflight guards, post-processing crashes and timeouts
(POSTPROC_ERROR: the schedule goes on; C1 inputs missing follow the rules), the thread budget of the auxiliary steps (the solve environment
unchanged except TMPDIR), licence scan of the pack. P1 left the batch (supplement 01 item 3).
M10P_PKG_DIR=<folder with run_batch3.sh / pack_results.sh / preflight.sh> runs the same tests against another copy of the scripts (M10A: the v3
package before the fixes)."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(os.environ["M10P_PKG_DIR"]) if os.environ.get("M10P_PKG_DIR") else ROOT / "research/06_scope_redesign/p1_m10p_20261022/cloud_package"
FAKE = ROOT / "tests/research/fixtures/m10p_fake_pipeline.py"
sys.path.insert(0, str(ROOT / "scripts_project"))
import m10_batch3_summary as S   # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("setsid") is None or not Path("/usr/bin/time").exists(), reason="setsid / GNU time missing")
THREADS = {p: v["Threads"] for p, v in yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())["research"]["solver"]["profiles"].items()
           if p in (S.A, S.T16)}
HOOK_KEYS = ("ALLOW_UNREGISTERED", "BUILD_ONLY", "POST_ONLY", "DRY", "TRUNCATE", "SOLVE_CMD", "VA_CMD", "C1_CMD", "M12_CMD", "M12A_CMD", "VAR_CMD", "G6_CMD",
             "SUM_CMD", "PACK_CMD", "WALL_CAP_S", "GUROBI_TIME_LIMIT_S", "LICENCE_GAP_S", "GRACE_S", "MONITOR_S", "POST_TIMEOUT_S", "PACK_TIMEOUT_S")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _clean_env(extra=None):
    env = {k: v for k, v in os.environ.items() if k not in HOOK_KEYS and not k.startswith("FAKE_")}
    env.update(extra or {})
    return env


def _package(tmp: Path) -> Path:
    pkg = tmp / "pkg"; nets = pkg / "networks"; nets.mkdir(parents=True)
    for f in ("run_batch3.sh", "pack_results.sh", "preflight.sh"):
        shutil.copy(PKG / f, pkg / f)
    for sc in ("integrated", "disconnected"):
        (nets / f"{sc}_365_24h_unsolved.nc").write_bytes(f"{sc}365_24h".encode())
        (nets / f"{sc}_costs_active_research.csv").write_text("technology\n")
        (nets / f"{sc}_BUILD_RECEIPT.json").write_text(json.dumps(dict(network=dict(sha256=hashlib.sha256(f"{sc}2920_3h".encode()).hexdigest(), snapshots=2920),
                                                                     daily_network=dict(sha256=sha(nets / f"{sc}_365_24h_unsolved.nc"), snapshots=365))))
    (tmp / "lic").write_text("synthetic placeholder")
    w = tmp / "standin" / "scripts_project"; w.mkdir(parents=True)   # M10A: the solve stand-in under the real script name (busy() counts "s2_solve.py" lines)
    (w / "s2_solve.py").write_text(f"import runpy, sys\nsys.argv = [{str(FAKE)!r}, 'solve', *sys.argv[1:]]\nrunpy.run_path({str(FAKE)!r}, run_name='__main__')\n")
    exp = tmp / "expected_variants"
    for rid, r in S.RUNS.items():   # expected variants = what the stand-in generator writes (the dry run does this with the real generator)
        if r["set"]:
            env = dict(os.environ, PYTHONHASHSEED="0", FAKE_OUT=str(tmp / "expv_calls"))
            subprocess.run([sys.executable, str(FAKE), "variants", "--base", str(nets / f"{r['base']}_unsolved.nc"), "--out", str(exp / rid), "--set", r["set"]], env=env, check=True)
    (pkg / "EXPECTED_VARIANTS.json").write_text(json.dumps(S.variants_expected(exp)))
    return pkg


def _run(tmp: Path, pkg: Path, extra=None, args=("--auth", "synthetic test"), timeout=900):
    f = f"{sys.executable} {FAKE}"
    env = _clean_env(dict(REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(tmp / "out"), FAKE_OUT=str(tmp / "out"), ALLOW_UNREGISTERED="1", LICENCE_GAP_S="1",
                          GRACE_S="1", MONITOR_S="1", CORES="25", GRB_LICENSE_FILE=str(tmp / "lic"), SOLVE_CMD=f"{sys.executable} {tmp / 'standin' / 'scripts_project' / 's2_solve.py'}",
                          VA_CMD=f"{f} va", C1_CMD=f"{f} c1", M12_CMD=f"{f} m12", M12A_CMD=f"{f} m12a", VAR_CMD=f"{f} variants", FAKE_SLEEP="0.2"))
    env.update(extra or {})
    return subprocess.run(["bash", str(pkg / "run_batch3.sh"), *args], env=env, capture_output=True, text=True, timeout=timeout)


def _calls(tmp: Path, kind="solve"):
    return [x.split() for x in (tmp / "out" / "CALLS.txt").read_text().splitlines() if x.split()[0] == kind]


def _span(calls, rid):
    c = next(x for x in calls if x[1] == rid)
    return float(c[4]), float(c[5])


def _overlap(calls, a, b):
    (a0, a1), (b0, b1) = _span(calls, a), _span(calls, b)
    return a0 < b1 and b0 < a1


def _solve_processes(tmp: Path):
    return [x for x in os.popen("ps -eo args").read().splitlines() if str(tmp) in x and "s2_solve.py" in x]


def test_run_table_and_schedule_are_the_registered_plan():
    R = S.RUNS
    assert list(R) == ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11"]                      # P1 left the batch (supplement 01 item 3)
    assert [rid for rid, r in R.items() if r["profile"] == S.T16] == ["R3", "R4"] and all(r["profile"] == S.A for rid, r in R.items() if rid not in ("R3", "R4"))
    assert {rid: r["set"] for rid, r in R.items() if r["set"]} == {"R5": "coalition.remove_countries=[VN]", "R6": "coalition.remove_countries=[TH]", "R7": "coalition.remove_countries=[LA]",
                                                                  "R8": "disconnected.co2_shipping_intra_asean=forbid", "R9": "cross_border.stock_mode=keep_stock_no_new",
                                                                  "R10": "finance.wacc_mode=country_specific", "R11": "finance.wacc_mode=country_specific"}
    assert R["R9"]["base"] == "integrated_365_24h" and R["R9"]["scenario"] == "disconnected"     # keep_stock_no_new derives from the integrated network
    assert all(r["base"].endswith("365_24h") for r in R.values()) and set(S.BASE_RECEIPT) == {"integrated_365_24h", "disconnected_365_24h"}
    assert S.SENSITIVITY == [("R8", "R2", S.SENSITIVITY[0][2]), ("R9", "R2", S.SENSITIVITY[1][2]), ("R10", "R1", S.SENSITIVITY[2][2]), ("R11", "R2", S.SENSITIVITY[3][2])]
    assert S.LEVEL2 == {"integrated": ("R3", "R1"), "disconnected": ("R4", "R2")} and S.LOO == {"R5": "VN", "R6": "TH", "R7": "LA"}
    assert S.SCHEDULE == [("1", ["R1"], ["R2"]), ("2", ["R3", "R4"], ["R5", "R6"]), ("3", ["R7", "R9", "R11"], ["R8", "R10"])]   # supplement 01 item 1
    flat = [r for _, a, b in S.SCHEDULE for r in a + b]
    assert sorted(flat) == sorted(R) and len(flat) == len(R)                                                     # every run exactly once
    assert THREADS == {S.A: 8, S.T16: 16}
    lane_max = [max(THREADS[R[r]["profile"]] for r in a) + max(THREADS[R[r]["profile"]] for r in b) for _, a, b in S.SCHEDULE]
    assert lane_max == [16, 24, 16] and all(sum(R[r]["profile"] == S.T16 for r in lane) in (0, 2) for _, a, b in S.SCHEDULE for lane in (a, b))   # T16 runs share a lane
    assert S.STOP_ALWAYS == ("R1", "R2")


def test_stop_before_solve_exits_before_the_solver_call():
    src = (ROOT / "scripts_project/s2_solve.py").read_text()
    i_stop, i_solve = src.index("if a.stop_before_solve:"), src.index("status, condition = m.solve(")
    i_params, i_export = src.index('run["solver_parameters"] = params'), src.index('lp_meta, M = export_lp(m, out / "lp")')
    assert i_export < i_params < i_stop < i_solve and "--stop-before-solve" in src
    block = src[i_stop:i_solve]
    assert "return 0" in block and "stop_before_solve=True" in block and "optimize_calls" not in block.split("return 0")[0].replace('"optimize_calls"', "")


def test_full_batch_pairing_order_reference_and_resume(tmp_path):
    pkg = _package(tmp_path)
    sl = {f"FAKE_SLEEP_{r}": "5" for r in ("R1", "R2", "R3", "R5", "R7", "R8")}
    p = _run(tmp_path, pkg, dict(sl, FAKE_SLEEP_R4="8", FAKE_SLEEP_R6="8", FAKE_OBJ_R3=str(2e11 * (1 + 5e-6)), FAKE_C1_R2="101", FAKE_C1_REGRADE_R2="111", FAKE_C1_R8="101"))
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, (p.stdout + p.stderr)[-1500:] + st[-3000:]
    assert "STOP_SAFE" not in st                                                                                 # M10A: the second lane starts beside a running solve (busy() = 1, not 2)
    calls = _calls(tmp_path)
    assert sorted(c[1] for c in calls) == sorted(S.RUNS) and len(calls) == 11                                  # every run solved exactly once; no P1
    assert all(c[2] == S.RUNS[c[1]]["profile"] for c in calls) and all(float(c[3]) == 21600.0 for c in calls)  # profiles, registered TimeLimit
    assert all(c[6] == str(tmp_path / "lic") for c in calls)
    assert all(c[7] == "omp=None" and c[8] == f"tmp={out / 'tmp'}" for c in calls)                              # M10A: solve environment untouched except TMPDIR (data disk, run dir)
    assert _overlap(calls, "R1", "R2")                                                                          # phase 1: R1 | R2 (8 + 8)
    assert _overlap(calls, "R3", "R5") and _overlap(calls, "R4", "R6") and "PHASE_2:two_lanes:A=R3,R4:B=R5,R6:threads=24:cores=25" in st   # supplement 01 item 1
    assert _span(calls, "R4")[0] >= _span(calls, "R3")[1] + 1 and _span(calls, "R6")[0] >= _span(calls, "R5")[1] + 1   # lane order and gap
    for rid in ("R3", "R4", "R5", "R6"):
        assert _span(calls, rid)[0] >= max(_span(calls, "R1")[1], _span(calls, "R2")[1]) + 1                  # phase order and gap
    spans = {c[1]: _span(calls, c[1]) for c in calls}
    for t in sorted(x for s in spans.values() for x in s):                                                     # at most two sessions, never two T16
        on = [r for r, (a, b) in spans.items() if a <= t < b]
        assert len(on) <= 2 and sum(THREADS[S.RUNS[r]["profile"]] for r in on) <= 24, (t, on)
    assert _overlap(calls, "R7", "R8") and "PHASE_3:two_lanes:A=R7,R9,R11:B=R8,R10:threads=16:cores=25" in st
    assert min(_span(calls, "R7")[0], _span(calls, "R8")[0]) >= max(spans[r][1] for r in ("R3", "R4", "R5", "R6")) + 1
    for prev, nxt in (("R7", "R9"), ("R9", "R11"), ("R8", "R10")):                                             # lane order and >= gap in the lane
        assert _span(calls, nxt)[0] >= _span(calls, prev)[1] + 1
    va = {v[1]: v[2] for v in _calls(tmp_path, "va")}                                                           # M10A thread budget: cores minus the Threads of the solves running
    assert va["R1"] == "omp=17" and va["R2"] == "omp=25", va                                                    # R1 post-processed while R2 (8 threads) runs; R2 alone
    assert all(1 <= int(v.split("=")[1]) <= 25 for v in va.values()) and len(va) == 11
    var = _calls(tmp_path, "variant")
    assert sorted(v[1] for v in var) == ["R10", "R11", "R5", "R6", "R7", "R8", "R9"] and all(v[-1] == "stale=False" for v in var)
    assert {v[1]: v[3] for v in var}["R10"].endswith("integrated_costs_active_research.csv") and {v[1]: v[3] for v in var}["R11"].endswith("disconnected_costs_active_research.csv")
    c1 = {c[1]: c[2] for c in _calls(tmp_path, "c1")}
    assert c1["R1"] == c1["R2"] == "ref=default" and all(c1[r] == "ref=batch" for r in S.RUNS if r not in ("R1", "R2"))   # provisional before the batch reference
    assert sorted(c[1] for c in _calls(tmp_path, "regrade")) == ["R1", "R2"]
    r2 = json.loads((out / "R2" / "PRECISION.json").read_text())
    assert len(r2["grade_history"]) == 1 and json.loads((out / "R2" / "V6_ACCEPTANCE_PROVISIONAL.json").read_text())["label"] == "NOT_ACCEPTED"
    assert json.loads((out / "R2" / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2"            # provisional NOT_ACCEPTED (b) -> no stop
    assert "NOT_ACCEPTED_REFERENCE_DEPENDENT:R2" in st and "NOT_ACCEPTED_REFERENCE_DEPENDENT:R8" in st and "STOP_NOT_ACCEPTED" not in st and "UNUSABLE:" not in st
    assert json.loads((out / "R8" / "STOP_CLASS.json").read_text())["cls"] == "ref_dependent"
    assert sorted(c[1] for c in _calls(tmp_path, "rhs_loo")) == ["R5", "R6", "R7"]
    assert _calls(tmp_path, "m12_loo")[0][1:] == ["LA", "TH", "VN", "standalone=R2"]
    assert json.loads((out / "PROFILE_CHOICE.json").read_text())["profile"] == "formal_barrier_1e6_t16"         # rel diff 5e-6 <= 1e-5, C1 passed
    summ = json.loads((out / "BATCH3_SUMMARY.json").read_text())
    assert summ["B6"]["passed"] and abs(summ["B6"]["b6_bn"] - 100.0) < 1e-9 and summ["unusable"] == {} and "p1" not in summ and summ["postproc_errors"] == []
    sens = {(x["new"], x["base"]): x for x in summ["sensitivity"]}
    assert set(sens) == {("R8", "R2"), ("R9", "R2"), ("R10", "R1"), ("R11", "R2")} and sens[("R8", "R2")]["usable"] is False   # R8 NOT_ACCEPTED
    assert len(sorted(out.glob("results_*_final_*.tar.gz"))) == 2 and not list(out.glob("results_*_pre_p1_*")) and "DONE:" in st and "unusable=none" in st
    assert "POSTPROC_ERROR" not in st and not (out / "POSTPROC_ERRORS").exists() and (out / "tmp").is_dir()
    n = len(_calls(tmp_path))
    p = _run(tmp_path, pkg)                                                                                     # resume: nothing is solved again
    assert p.returncode == 0 and len(_calls(tmp_path)) == n and (out / "STATUS.txt").read_text().count("SKIP_ENDED_") == 11


def test_one_lane_when_t16_and_a_do_not_fit_the_cores(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"CORES": "20", "FAKE_SLEEP_R1": "3", "FAKE_SLEEP_R2": "3"})
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, st[-2000:]
    calls = _calls(tmp_path)
    assert _overlap(calls, "R1", "R2") and "PHASE_2:one_lane:R3,R5,R4,R6:threads=24:cores=20" in st             # 16 + 8 > 20: one after the other
    for prev, nxt in (("R3", "R5"), ("R5", "R4"), ("R4", "R6")):
        assert _span(calls, nxt)[0] >= _span(calls, prev)[1] + 1
    assert "PHASE_3:two_lanes:A=R7,R9,R11:B=R8,R10:threads=16:cores=20" in st


def test_one_lane_in_every_phase_below_16_cores(tmp_path):
    """M10A drill (k): fewer than 16 cores -> phases 1 and 3 merge too (RUN_PLAN.md 3.2); the thread budget of a step is then the whole container."""
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"CORES": "12"})
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, st[-2000:]
    calls = _calls(tmp_path)
    assert "PHASE_1:one_lane:R1,R2:threads=16:cores=12" in st and "PHASE_2:one_lane:R3,R5,R4,R6:threads=24:cores=12" in st and "PHASE_3:one_lane:R7,R8,R9,R10,R11:threads=16:cores=12" in st
    assert len(calls) == 11 and not any(_overlap(calls, a[1], b[1]) for a in calls for b in calls if a[1] != b[1])
    assert {v[1]: v[2] for v in _calls(tmp_path, "va")}["R1"] == "omp=12" and "DONE:" in st


def test_graded_stop_rule_unusable_runs_and_the_batch_goes_on(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"FAKE_NOSOL_R3": "1", "FAKE_NOSOL_R5": "1", "FAKE_C1_R8": "011"})
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, st[-3000:]
    calls = _calls(tmp_path)
    assert sorted(c[1] for c in calls) == sorted(S.RUNS) and all(c[-1] == "nosolution" for c in calls if c[1] in ("R3", "R5"))   # all 11 started once
    un = dict(x.split()[:2] for x in (out / "UNUSABLE").read_text().splitlines())
    assert un == {"R3": "nosol", "R5": "nosol", "R8": "c1a"} and not (out / "STOP").exists() and "STOP_NOT_ACCEPTED" not in st
    for rid, cls in un.items():
        sc = json.loads((out / rid / "STOP_CLASS.json").read_text())
        assert sc["cls"] == cls and sc["action"] == "unusable" and f"UNUSABLE:{rid}:{cls}" in st
    v6 = json.loads((out / "R3" / "V6_ACCEPTANCE.json").read_text())
    assert v6["label"] == "NOT_ACCEPTED" and not v6["G2"]["G2_3"]["passed"] and v6["G2"]["G2_1"]["sha256_equal"] and v6["G2"]["G2_2"]["passed"]
    assert json.loads((out / "R3" / "STOP_CLASS.json").read_text())["failed_checks"] == []                   # G2 without a solution: input checks only
    assert _calls(tmp_path, "m12_loo")[0][1:] == ["LA", "TH", "standalone=R2"] and "unusable_left_out=R5" in st   # R5 is not a c(N - VN)
    assert json.loads((out / "PROFILE_CHOICE.json").read_text())["profile"] == "formal_barrier"                 # R3 unusable -> profile A
    summ = json.loads((out / "BATCH3_SUMMARY.json").read_text())
    sens = {(x["new"], x["base"]): x for x in summ["sensitivity"]}
    assert summ["unusable"] == un and sens[("R8", "R2")]["usable"] is False and sens[("R8", "R2")]["unusable"] == ["R8"] and sens[("R9", "R2")]["usable"] is True
    assert "DONE:" in st and len(sorted(out.glob("results_full_final_*.tar.gz"))) == 1 and (out / "export" / "batch" / "UNUSABLE").exists()


def test_r3_with_solution_but_c1a_failed_is_unusable_and_profile_a_stays(tmp_path):
    """M10A drill (e): R3 returns a solution, C1 (a) fails -> unusable (the batch goes on), level 2 fails -> the fourth batch keeps profile A."""
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"FAKE_C1_R3": "011"})
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, st[-2000:]
    assert dict(x.split()[:2] for x in (out / "UNUSABLE").read_text().splitlines()) == {"R3": "c1a"} and "UNUSABLE:R3:c1a" in st and not (out / "STOP").exists()
    assert json.loads((out / "R3" / "STOP_CLASS.json").read_text())["action"] == "unusable" and (out / "R3" / "solution" / "X.npy").exists()
    lv = json.loads((out / "LEVEL2.json").read_text())
    assert lv["integrated"]["candidate"]["precision"] == dict(a=False, b=True, c=True) and lv["disconnected"]["candidate"]["precision"] == dict(a=True, b=True, c=True)
    assert json.loads((out / "PROFILE_CHOICE.json").read_text())["profile"] == "formal_barrier" and len(_calls(tmp_path)) == 11 and "DONE:" in st


@pytest.mark.parametrize("rid,extra,cls,solved,running", [
    ("R1", {"FAKE_NOSOL_R1": "1", "FAKE_SLEEP_R1": "5", "FAKE_SLEEP_R2": "8"}, "nosol", ["R1", "R2"], "R2"),         # M10A drill (b): batch reference run without a solution (R2 already running)
    ("R2", {"FAKE_C1_R2": "011"}, "c1a", ["R1", "R2"], None),                                                       # batch reference run: C1 (a)
    ("R6", {"FAKE_NOSOL_R6": "1", "FAKE_SUBSET_R6": "differ", "FAKE_SLEEP_R4": "10", "FAKE_SLEEP_R5": "6"}, "g2", ["R1", "R2", "R3", "R4", "R5", "R6"], "R4"),   # input problem, no solution (R4 started before R6 stops: wait_gap polls every 5 s)
    ("R7", {"FAKE_SUBSET_R7": "differ", "FAKE_SLEEP_R7": "4", "FAKE_SLEEP_R8": "12"}, "g2", ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"], "R8"),   # G2 with a solution
])
def test_graded_stop_rule_stops_on_reference_runs_and_g2(tmp_path, rid, extra, cls, solved, running):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, extra)
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 3, st[-3000:]
    assert sorted(c[1] for c in _calls(tmp_path)) == sorted(solved)                                                # no new solve after the stop
    assert (out / "STOP").read_text().split() == [rid] and f"STOP_NOT_ACCEPTED:{rid}:{cls}" in st and not (out / "UNUSABLE").exists()
    sc = json.loads((out / rid / "STOP_CLASS.json").read_text())
    assert sc["cls"] == cls and sc["action"] == "stop"
    if running:
        assert (out / running / "V6_ACCEPTANCE.json").exists() and (out / "export" / running / "V6_ACCEPTANCE.json").exists()   # the other lane's running solve finished and was post-processed
    assert "HALTED:" in st and (out / "BATCH3_SUMMARY.json").exists() and len(sorted(out.glob("results_full_halted_*.tar.gz"))) == 1


def _acc(d: Path, label="NOT_ACCEPTED", a=True, g21=True, sha_eq=True, g22=True, g23=True):
    d.mkdir(parents=True, exist_ok=True)
    (d / "V6_ACCEPTANCE.json").write_text(json.dumps(dict(label=label, G1=dict(a=a, b=True, c=True), G2=dict(G2_1=dict(passed=g21, sha256_equal=sha_eq),
                                                                                                              G2_2=dict(passed=g22), G2_3=dict(passed=g23)))))


def _sol(d: Path):
    (d / "solution").mkdir(parents=True, exist_ok=True); np.save(d / "solution" / "X.npy", np.zeros(2))
    (d / "SOLVE_RECEIPT.json").write_text(json.dumps(dict(input_network=dict(sha256="x"), config_subset=dict(network="s", current="s"), solution=dict(X=dict(count=2)))))


def test_stop_class_cases(tmp_path):
    def c(rid, setup):
        d = tmp_path / str(len(list(tmp_path.iterdir()))) / rid; d.mkdir(parents=True); setup(d)
        r = S.stop_class(d); assert json.loads((d / "STOP_CLASS.json").read_text())["cls"] == r["cls"]
        return r["cls"], r["action"]
    assert c("R5", lambda d: None) == ("g2", "stop")                                                                # acceptance missing -> stop
    assert c("R5", lambda d: (_sol(d), _acc(d, label="ACCEPTED_LAYER2"))) == ("accepted", "none")
    assert c("R5", lambda d: (_sol(d), _acc(d, a=False))) == ("c1a", "unusable") and c("R1", lambda d: (_sol(d), _acc(d, a=False))) == ("c1a", "stop")
    assert c("R5", lambda d: (_sol(d), _acc(d))) == ("ref_dependent", "none")                                     # C1 (b) / (c) only
    assert c("R8", lambda d: (_sol(d), _acc(d, g23=False))) == ("g2", "stop")                                     # with a solution: every G2 check
    pre = dict(input_network=dict(sha256="x"), config_subset=dict(network="s", current="s"))                        # pre-solve receipt (no solution)
    assert c("R9", lambda d: ((d / "SOLVE_RECEIPT.json").write_text(json.dumps(pre)), _acc(d, a=False, g21=False, g23=False))) == ("nosol", "unusable")
    assert c("R2", lambda d: ((d / "SOLVE_RECEIPT.json").write_text(json.dumps(pre)), _acc(d, a=False, g21=False, g23=False))) == ("nosol", "stop")
    assert c("R9", lambda d: ((d / "SOLVE_RECEIPT.json").write_text(json.dumps(pre)), _acc(d, a=False, g21=False, sha_eq=False, g23=False))) == ("g2", "stop")
    assert c("R9", lambda d: ((d / "SOLVE_RECEIPT.json").write_text(json.dumps(pre)), _acc(d, a=False, g21=False, g22=False, g23=False))) == ("g2", "stop")
    run_ok = dict(network_sha256="n", registered_sha256="n")                                                         # ended before any receipt: RUN.json SHA256
    assert c("R10", lambda d: ((d / "RUN.json").write_text(json.dumps(run_ok)), _acc(d, a=False, g21=False, sha_eq=False, g22=False, g23=False))) == ("nosol", "unusable")
    assert c("R10", lambda d: ((d / "RUN.json").write_text(json.dumps(dict(run_ok, registered_sha256="m"))), _acc(d, a=False, g21=False, sha_eq=False, g22=False, g23=False))) == ("g2", "stop")


def test_wall_clock_kill_stops_the_batch_and_interrupted_solve_is_not_repeated(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"WALL_CAP_S": "3", "FAKE_SLEEP_R1": "60"})
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 3 and "KILLED_3S_R1" in st and (out / "R1" / ".cond").read_text().strip() == "killed_pre_solve"
    assert "STOP_NOT_ACCEPTED:R1:nosol" in st and not any(c[1] == "R3" for c in _calls(tmp_path) if len(c) > 1)   # R1 without a solution stops the batch
    assert _solve_processes(tmp_path) == []                                                                   # whole process group ended
    out2 = tmp_path / "second"; (out2 / "R1").mkdir(parents=True); (out2 / "R1" / ".started").write_text("2026-10-22T00:00:00Z pid=1 pgid=1")
    p = _run(tmp_path, pkg, {"RUN_DIR": str(out2), "FAKE_OUT": str(out2)})
    st = (out2 / "STATUS.txt").read_text()
    solves = [x for x in (out2 / "CALLS.txt").read_text().splitlines() if x.startswith("solve")]
    assert p.returncode == 3 and "STOP_SAFE:INTERRUPTED_R1" in st and solves == []                            # R2 of the other lane not started either


def test_wall_clock_kill_when_the_solve_ignores_term(tmp_path):
    """M10A drill (g): TERM ignored by the solve -> KILL of the process group after GRACE_S; the run ends killed_pre_solve, is exported and
    classified (R1 without a solution stops the batch); no process of the group survives."""
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"WALL_CAP_S": "3", "GRACE_S": "2", "FAKE_SLEEP_R1": "60", "FAKE_IGNORE_TERM_R1": "1", "FAKE_SLEEP_R2": "1"})
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 3, st[-2000:]
    assert "KILLED_3S_R1" in st and "KILL9_R1" in st and "after_grace_2s" in st and "GROUP_SURVIVED" not in st
    assert (out / "R1" / ".cond").read_text().strip() == "killed_pre_solve" and (out / "R1" / ".ended").exists() and (out / "export" / "R1" / "RUN.json").exists()
    assert "STOP_NOT_ACCEPTED:R1:nosol" in st and _solve_processes(tmp_path) == [] and json.loads((out / "R1" / "STOP_CLASS.json").read_text())["cls"] == "nosol"
    assert (out / "R2" / "V6_ACCEPTANCE.json").exists() and "HALTED:" in st                                     # the other lane finished and was post-processed


def test_base_network_sha256_differing_from_the_build_receipt_is_a_safe_stop(tmp_path):
    """M10A drill (f): a base network that is not the registered file -> STOP_SAFE before any variant or solve; exit 3; summary + halted pack."""
    pkg = _package(tmp_path); rec = pkg / "networks" / "integrated_BUILD_RECEIPT.json"
    r = json.loads(rec.read_text()); r["daily_network"]["sha256"] = "0" * 64; rec.write_text(json.dumps(r))
    p = _run(tmp_path, pkg)
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 3 and "STOP_SAFE:BASE_NETWORK_SHA256:DIFFERENT:integrated_365_24h" in st and "HALTED:" in st
    assert not (out / "CALLS.txt").exists() and (out / "BATCH3_SUMMARY.json").exists() and len(list(out.glob("results_light_halted_phase0_*.tar.gz"))) == 1


def test_variant_sha256_differing_from_the_dry_run_is_a_safe_stop(tmp_path):
    pkg = _package(tmp_path)
    e = json.loads((pkg / "EXPECTED_VARIANTS.json").read_text()); e["R9"]["output_sha256"] = "0" * 64
    (pkg / "EXPECTED_VARIANTS.json").write_text(json.dumps(e))
    p = _run(tmp_path, pkg)
    st = (tmp_path / "out" / "STATUS.txt").read_text()
    assert p.returncode == 3 and "STOP_SAFE:VARIANT_SHA256_R9" in st and _calls(tmp_path) == []


def test_solver_process_running_at_start_is_a_safe_stop(tmp_path):
    """M10A drill (l): another s2_solve.py process (an earlier runner) -> STOP_SAFE at phase 0, nothing starts, exit 3."""
    pkg = _package(tmp_path)
    other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)", str(tmp_path / "other" / "s2_solve.py")])
    try:
        time.sleep(0.5)
        p = _run(tmp_path, pkg)
        st = (tmp_path / "out" / "STATUS.txt").read_text()
        assert p.returncode == 3 and "STOP_SAFE:SOLVER_PROCESS_RUNNING_AT_START:1 s2_solve" in st and not (tmp_path / "out" / "CALLS.txt").exists()
    finally:
        other.kill(); other.wait()


def test_build_only_dry_run_no_solver_and_licence_tripwire(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"BUILD_ONLY": "1"}, args=())
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, st[-2000:]
    builds = _calls(tmp_path, "build")
    assert [b[1] for b in builds] == ["R1", "R2", "R3", "R5", "R4", "R6", "R7", "R8", "R9", "R10", "R11"] and _calls(tmp_path) == []   # schedule order, one lane
    assert all(b[4] == "/nonexistent/m10p_dry_run_no_licence" for b in builds)
    for rid in S.RUNS:
        bc = json.loads((out / rid / "BUILD_CHECK.json").read_text()); assert bc["passed"], (rid, bc["checks"])
    assert "PHASE_1:one_lane:R1,R2" in st and "PHASE_2:one_lane:R3,R5,R4,R6" in st and len(list(out.glob("results_light_final_*.tar.gz"))) == 1 and "DONE:" in st


def test_post_only_mode_post_processes_ended_runs_without_any_solve(tmp_path):
    pkg = _package(tmp_path); out = tmp_path / "out"; nets = pkg / "networks"; f = [sys.executable, str(FAKE)]
    env = dict(os.environ, FAKE_OUT=str(out), PYTHONHASHSEED="0")
    subprocess.run(f + ["variants", "--base", str(nets / "integrated_365_24h_unsolved.nc"), "--out", str(tmp_path / "v"), "--set", "coalition.remove_countries=[VN]"], env=env, check=True)
    vnet = next((tmp_path / "v").glob("*_unsolved.nc"))
    for rid, net, sc in (("R1", nets / "integrated_365_24h_unsolved.nc", "integrated"), ("R2", nets / "disconnected_365_24h_unsolved.nc", "disconnected"), ("R5", vnet, "integrated")):
        d = out / rid
        subprocess.run(f + ["solve", "--output", str(d), "--network", str(net), "--solver-profile", "formal_barrier", "--time-limit", "21600", "--scenario", sc,
                            "--label", "BATCH3_365X24H"], env=env, check=True)
        (d / "RUN.json").write_text(json.dumps(dict(rid=rid, scenario=sc, network=str(net), network_sha256=sha(net), registered_sha256=sha(net), label="BATCH3_365X24H")))
        (d / ".ended").write_text("x"); (d / ".cond").write_text("optimal\n")
    n = len(_calls(tmp_path))
    p = _run(tmp_path, pkg, {"POST_ONLY": "1", "GRB_LICENSE_FILE": ""}, args=())
    st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, st[-2000:]
    assert len(_calls(tmp_path)) == n and "PREPARE:skipped" in st and st.count("POST_ONLY_") == 8          # no solve; R3, R4, R6-R11 skipped
    assert sorted(c[1] for c in _calls(tmp_path, "regrade")) == ["R1", "R2"] and [c[1] for c in _calls(tmp_path, "rhs_loo")] == ["R5"]
    assert {c[1]: c[2] for c in _calls(tmp_path, "c1")}["R5"] == "ref=batch"
    assert _calls(tmp_path, "m12_loo")[0][1:] == ["VN", "standalone=R2"]
    assert json.loads((out / "PROFILE_CHOICE.json").read_text())["profile"] == "formal_barrier"                 # R3 / R4 missing -> profile A
    assert json.loads((out / "R5" / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2" and "DONE:" in st


def test_post_processing_crash_is_recorded_and_the_schedule_goes_on(tmp_path):
    """M10A drill (j): the M12 allocation of R2 and the leave-one-out RHS check of R7 raise -> POSTPROC_ERROR records, the batch runs to DONE
    (exit 0); the labels of R2 / R7 are unchanged (GATES_V6 checks only the registered exports), the benefit step reports not computable."""
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"FAKE_RAISE_M12_R2": "1", "FAKE_RAISE_RHS_LOO_R7": "1"})
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, st[-3000:]
    assert len(_calls(tmp_path)) == 11 and "DONE:" in st and "STOP" not in st.replace("STOP_CLASS", "")
    assert "POSTPROC_ERROR:R2:m12:exit=1" in st and "POSTPROC_ERROR:R7:rhs_loo:exit=1" in st and "M12_BENEFIT:not_computable" in st
    rows = (out / "POSTPROC_ERRORS").read_text().splitlines()
    assert [r.split()[:3] for r in rows] == [["R2", "m12", "exit=1"], ["R7", "rhs_loo", "exit=1"]] and (out / "export" / "batch" / "POSTPROC_ERRORS").exists()
    assert json.loads((out / "R2" / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2" and not (out / "R2" / "ALLOCATION.json").exists()
    assert json.loads((out / "R7" / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2" and not (out / "R7" / "m12_loo_rhs" / "LOO_RHS_CHECK.json").exists()
    summ = json.loads((out / "BATCH3_SUMMARY.json").read_text())
    assert [(e["rid"], e["step"], e["exit"]) for e in summ["postproc_errors"]] == [("R2", "m12", "1"), ("R7", "rhs_loo", "1")]
    assert summ["runs"]["R2"]["postproc_errors"] == ["m12:exit=1"] and summ["runs"]["R1"]["postproc_errors"] == [] and summ["benefit"] is None   # benefit step not run (R2 allocation missing)
    assert "R2 m12 exit=1" in (out / "BATCH3_SUMMARY.md").read_text()
    p = _run(tmp_path, pkg, {"POST_ONLY": "1", "GRB_LICENSE_FILE": ""}, args=())                                   # redo: the missing outputs are produced, nothing solved
    assert p.returncode == 0 and (out / "R2" / "ALLOCATION.json").exists() and (out / "R7" / "m12_loo_rhs" / "LOO_RHS_CHECK.json").exists() and len(_calls(tmp_path)) == 11


def test_post_processing_timeout_never_blocks_the_schedule(tmp_path):
    """M10A drill (j, hang): an M12 step of R5 that hangs is ended by the step timeout (POSTPROC_ERROR exit 124), the batch goes on to DONE; a
    violation analysis of R2 that hangs is ended too, then C1 is not computable -> C1 (a) failed for a batch reference run -> stop (RUN_PLAN.md
    3.3, as registered) - the timeout only guarantees that the lane never waits for ever."""
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"POST_TIMEOUT_S": "3", "FAKE_HANG_M12_R5": "1"})
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, st[-3000:]
    assert "POSTPROC_ERROR:R5:m12:exit=124:timeout_3s" in st and "DONE:" in st and len(_calls(tmp_path)) == 11
    assert json.loads((out / "R5" / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2" and not (out / "R5" / "ALLOCATION.json").exists()
    assert not [x for x in os.popen("ps -eo args").read().splitlines() if str(FAKE) in x and "m12" in x]   # the hung step's process group is gone
    pkg2 = _package(tmp_path / "b")
    p = _run(tmp_path / "b", pkg2, {"POST_TIMEOUT_S": "3", "FAKE_HANG_VA_R2": "1", "FAKE_SLEEP_R1": "8"})
    out = tmp_path / "b" / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 3, st[-3000:]
    assert "POSTPROC_ERROR:R2:violations:exit=124:timeout_3s" in st and "STOP_NOT_ACCEPTED:R2:c1a" in st and "HALTED:" in st
    assert (out / "R1" / "V6_ACCEPTANCE.json").exists() and sorted(c[1] for c in _calls(tmp_path / "b")) == ["R1", "R2"]


def test_unregistered_limits_are_refused(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"ALLOW_UNREGISTERED": "0", "WALL_CAP_S": "100", "LICENCE_GAP_S": "330"})
    assert p.returncode == 2 and "REFUSED: WALL_CAP_S=100" in p.stdout
    p = _run(tmp_path, pkg, {"ALLOW_UNREGISTERED": "0", "LICENCE_GAP_S": "330"}, args=())
    assert p.returncode == 2 and "REFUSED" in p.stdout                                                              # (the test hooks are refused first, M10A)
    env = _clean_env(dict(REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(tmp_path / "o3"), GRB_LICENSE_FILE=str(tmp_path / "lic")))
    p = subprocess.run(["bash", str(pkg / "run_batch3.sh")], env=env, capture_output=True, text=True, timeout=120)   # formal environment without --auth
    assert p.returncode == 2 and "--auth" in p.stdout and not (tmp_path / "o3" / "STATUS.txt").exists()


def test_formal_run_refuses_test_hooks_and_no_solve_modes_refuse_auth(tmp_path):
    """M10A drill (m): a stand-in left in the shell is refused by a formal run (solve mode without ALLOW_UNREGISTERED); BUILD_ONLY / POST_ONLY
    left in the shell are refused together with --auth; the test usage (ALLOW_UNREGISTERED=1) and the dry-run usage (no --auth) are unchanged."""
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"ALLOW_UNREGISTERED": "0", "LICENCE_GAP_S": "330"})
    assert p.returncode == 2 and "REFUSED: SOLVE_CMD,VA_CMD,C1_CMD,M12_CMD,M12A_CMD,VAR_CMD,FAKE_OUT,FAKE_SLEEP set - test hooks" in p.stdout and not (tmp_path / "out" / "STATUS.txt").exists()
    env = _clean_env(dict(REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(tmp_path / "o2"), GRB_LICENSE_FILE=str(tmp_path / "lic"), FAKE_SLEEP_R1="9"))
    p = subprocess.run(["bash", str(pkg / "run_batch3.sh"), "--auth", "x"], env=env, capture_output=True, text=True, timeout=120)
    assert p.returncode == 2 and "REFUSED: FAKE_SLEEP_R1 set" in p.stdout
    for mode in ("BUILD_ONLY", "POST_ONLY"):
        p = _run(tmp_path, pkg, {mode: "1"})
        assert p.returncode == 2 and "REFUSED: --auth together with BUILD_ONLY / POST_ONLY / DRY" in p.stdout, mode


def test_preflight_guards_refuse_test_hooks_left_in_the_shell(tmp_path):
    """M10A drill (m): preflight.sh section guards fails when a test hook / dry-run switch is set, passes in a clean shell; operational overrides are only noted."""
    pkg = _package(tmp_path)
    for k, v in (("ALLOW_UNREGISTERED", "1"), ("POST_ONLY", "1"), ("SOLVE_CMD", "python fake.py"), ("FAKE_SLEEP_R1", "3"), ("WALL_CAP_S", "100")):
        p = subprocess.run(["bash", str(pkg / "preflight.sh")], env=_clean_env({"PREFLIGHT_ONLY": "guards", "PY": sys.executable, k: v}), capture_output=True, text=True)
        assert p.returncode == 1 and "PREFLIGHT FAILED" in p.stdout and f"unset before the formal run: {k}" in p.stdout, (k, p.stdout)
    p = subprocess.run(["bash", str(pkg / "preflight.sh")], env=_clean_env({"PREFLIGHT_ONLY": "guards", "PY": sys.executable, "RUN_DIR": "/x"}), capture_output=True, text=True)
    assert p.returncode == 0 and "PREFLIGHT OK" in p.stdout and "no test hook / dry-run switch set" in p.stdout and "NOTE: RUN_DIR=/x" in p.stdout


def test_pack_refuses_licence_strings(tmp_path):
    out = tmp_path / "out"; (out / "export" / "R1").mkdir(parents=True); (out / "export" / "R1" / "x.txt").write_text("ok")
    p = subprocess.run(["bash", str(PKG / "pack_results.sh"), str(out), "t"], env=dict(os.environ, PY=sys.executable), capture_output=True, text=True)
    assert p.returncode == 0 and "PACKED:light=" in p.stdout
    (out / "export" / "R1" / "y.txt").write_text("Set parameter " + "Li" + "censeID to value 1")
    p = subprocess.run(["bash", str(PKG / "pack_results.sh"), str(out), "u"], env=dict(os.environ, PY=sys.executable), capture_output=True, text=True)
    assert p.returncode == 1 and "PACK_REFUSED" in p.stdout and not list(out.glob("results_*_u_*.tar.gz"))


def test_postproc_errors_parser(tmp_path):
    (tmp_path / "POSTPROC_ERRORS").write_text("R2 m12 exit=1 2026-10-22T00:00:00Z\nR7 rhs_loo exit=124 2026-10-22T00:01:00Z\nbad\n")
    assert S.postproc_errors(tmp_path) == [dict(rid="R2", step="m12", exit="1", utc="2026-10-22T00:00:00Z"), dict(rid="R7", step="rhs_loo", exit="124", utc="2026-10-22T00:01:00Z")]
    assert S.postproc_errors(tmp_path / "none") == []


def test_p1_summary_parses_timing_and_memory(tmp_path):
    """The 2920x3h probe parser stays for the memory probe at the start of the fourth batch (supplement 01 item 3)."""
    d = tmp_path / "P1"; d.mkdir()
    (d / "RUN.json").write_text(json.dumps(dict(network="x/integrated_2920_3h_unsolved.nc", profile="formal_barrier", wall_cap_s=3600, time_limit=3600.0)))
    (d / "SOLVE_RECEIPT.json").write_text(json.dumps(dict(lp=dict(num_row=72000000, num_col=30000000, nnz=1, build_seconds=420.5), peak_rss_bytes=60 * 2**30)))
    (d / ".cond").write_text("killed_pre_solve\n")
    log = tmp_path / "log.txt"
    log.write_text("Optimize a model with 100 rows, 50 columns and 300 nonzeros\nPresolve time: 120.50s\nPresolved: 60 rows, 40 columns, 200 nonzeros\n"
                   "Ordering time: 30.00s\n Factor NZ  : 1.6e+09 (roughly 16.0 GB of memory)\n"
                   + "".join(f"  {i:3d}   1.10068623e+15 -6.85867369e+14  2.74e+10 1.51e+04  3.05e+12   {200 + 20 * i}s\n" for i in range(6)))
    (tmp_path / "MONITOR_P1.csv").write_text("utc,elapsed_s,rss_gib_group,cgroup_mem_used_gib,cgroup_mem_limit_gib,host_mem_available_gib,disk_free_gib,gurobi_last_line\n"
                                             "t,10,30.5,40.0,92.0,50,100,x\nt,20,61.2,70.1,92.0,20,100,y\n")
    r = S.p1_summary(d, log)
    assert r["lp_build_seconds"] == 420.5 and r["presolve_seconds"] == 120.5 and r["ordering_seconds"] == 30.0 and r["barrier_iterations_logged"] == 6
    assert r["seconds_per_iteration_median"] == 20 and r["first_iteration_time_s"] == 200 and r["peak_rss_gib_monitor"] == 61.2 and r["peak_cgroup_gib_monitor"] == 70.1
    assert r["ended"] == "killed_pre_solve" and r["factor_memory_estimate"] == "16.0 GB" and r["model"]["rows"] == 100


def test_level2_missing_runs_keep_profile_a(tmp_path):
    lv = S.level2(tmp_path)
    assert set(lv) == {"integrated", "disconnected"} and all(v["candidate"]["precision"] == dict(a=False, b=False, c=False) for v in lv.values())
    sys.path.insert(0, str(ROOT / "scripts_project" / "v5"))
    from gates_v6 import DEFAULT_RUN_RULES, select_formal_profile
    assert select_formal_profile(lv, DEFAULT_RUN_RULES)["profile"] == "formal_barrier"
