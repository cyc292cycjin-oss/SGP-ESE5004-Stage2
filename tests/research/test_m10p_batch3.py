"""M10P (instruction sections 2-5): third-batch runner run_batch3.sh, results pack and scripts_project/m10_batch3_summary.py.

The runner is driven end to end with SYNTHETIC stand-ins (tests/research/fixtures/m10p_fake_pipeline.py: no solver, no model) on a package-like
folder; GATES_V6, the level-2 profile choice, the batch summary and the pack are the real code. Covered: the pre-registered run table and order,
two sessions only within the cores (R3 / R4 one after the other on 25 cores), licence gaps, C1 provisional -> batch reference -> regrade with
grade_history, the item-138 D12 stop rule, resume without re-solving, safe stops (interrupted solve, variant SHA256), wall-clock kill of the
process group, the local dry-run mode (no solver, licence tripwire), refusal of unregistered limits, licence scan of the pack."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research/06_scope_redesign/p1_m10p_20261022/cloud_package"
FAKE = ROOT / "tests/research/fixtures/m10p_fake_pipeline.py"
sys.path.insert(0, str(ROOT / "scripts_project"))
import m10_batch3_summary as S   # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("setsid") is None or not Path("/usr/bin/time").exists(), reason="setsid / GNU time missing")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _package(tmp: Path) -> Path:
    pkg = tmp / "pkg"; nets = pkg / "networks"; nets.mkdir(parents=True)
    for f in ("run_batch3.sh", "pack_results.sh"):
        shutil.copy(PKG / f, pkg / f)
    for sc in ("integrated", "disconnected"):
        for res in ("365_24h", "2920_3h"):
            (nets / f"{sc}_{res}_unsolved.nc").write_bytes(f"{sc}{res}".encode())
        (nets / f"{sc}_costs_active_research.csv").write_text("technology\n")
        (nets / f"{sc}_BUILD_RECEIPT.json").write_text(json.dumps(dict(network=dict(sha256=sha(nets / f"{sc}_2920_3h_unsolved.nc"), snapshots=2920),
                                                                     daily_network=dict(sha256=sha(nets / f"{sc}_365_24h_unsolved.nc"), snapshots=365))))
    (tmp / "lic").write_text("synthetic placeholder")
    exp = tmp / "expected_variants"
    for rid, r in S.RUNS.items():   # expected variants = what the stand-in generator writes (the dry run does this with the real generator)
        if r["set"]:
            env = dict(os.environ, PYTHONHASHSEED="0", FAKE_OUT=str(tmp / "expv_calls"))
            subprocess.run([sys.executable, str(FAKE), "variants", "--base", str(nets / f"{r['base']}_unsolved.nc"), "--out", str(exp / rid), "--set", r["set"]], env=env, check=True)
    (pkg / "EXPECTED_VARIANTS.json").write_text(json.dumps(S.variants_expected(exp)))
    return pkg


def _run(tmp: Path, pkg: Path, extra=None, args=("--auth", "synthetic test")):
    f = f"{sys.executable} {FAKE}"
    env = dict(os.environ, REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(tmp / "out"), FAKE_OUT=str(tmp / "out"), ALLOW_UNREGISTERED="1", LICENCE_GAP_S="1",
               GRACE_S="1", MONITOR_S="1", P1_MONITOR_S="1", CORES="25", GRB_LICENSE_FILE=str(tmp / "lic"), SOLVE_CMD=f"{f} solve", VA_CMD=f"{f} va",
               C1_CMD=f"{f} c1", M12_CMD=f"{f} m12", M12A_CMD=f"{f} m12a", VAR_CMD=f"{f} variants", FAKE_SLEEP="0.2")
    env.update(extra or {})
    return subprocess.run(["bash", str(pkg / "run_batch3.sh"), *args], env=env, capture_output=True, text=True, timeout=900)


def _calls(tmp: Path, kind="solve"):
    return [x.split() for x in (tmp / "out" / "CALLS.txt").read_text().splitlines() if x.split()[0] == kind]


def _span(calls, rid):
    c = next(x for x in calls if x[1] == rid)
    return float(c[4]), float(c[5])


def test_run_table_is_the_registered_plan():
    R = S.RUNS
    assert list(R) == ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11", "P1"]
    assert [rid for rid, r in R.items() if r["profile"] == S.T16] == ["R3", "R4"] and all(r["profile"] == S.A for rid, r in R.items() if rid not in ("R3", "R4"))
    assert {rid: r["set"] for rid, r in R.items() if r["set"]} == {"R5": "coalition.remove_countries=[VN]", "R6": "coalition.remove_countries=[TH]", "R7": "coalition.remove_countries=[LA]",
                                                                  "R8": "disconnected.co2_shipping_intra_asean=forbid", "R9": "cross_border.stock_mode=keep_stock_no_new",
                                                                  "R10": "finance.wacc_mode=country_specific", "R11": "finance.wacc_mode=country_specific"}
    assert R["R9"]["base"] == "integrated_365_24h" and R["R9"]["scenario"] == "disconnected"     # keep_stock_no_new derives from the integrated network
    assert R["P1"]["base"] == "integrated_2920_3h" and all(r["base"].endswith("365_24h") for rid, r in R.items() if rid != "P1")
    assert S.SENSITIVITY == [("R8", "R2", S.SENSITIVITY[0][2]), ("R9", "R2", S.SENSITIVITY[1][2]), ("R10", "R1", S.SENSITIVITY[2][2]), ("R11", "R2", S.SENSITIVITY[3][2])]
    assert S.LEVEL2 == {"integrated": ("R3", "R1"), "disconnected": ("R4", "R2")} and S.LOO == {"R5": "VN", "R6": "TH", "R7": "LA"}


def test_stop_before_solve_exits_before_the_solver_call():
    src = (ROOT / "scripts_project/s2_solve.py").read_text()
    i_stop, i_solve = src.index("if a.stop_before_solve:"), src.index("status, condition = m.solve(")
    i_params, i_export = src.index('run["solver_parameters"] = params'), src.index('lp_meta, M = export_lp(m, out / "lp")')
    assert i_export < i_params < i_stop < i_solve and "--stop-before-solve" in src
    block = src[i_stop:i_solve]
    assert "return 0" in block and "stop_before_solve=True" in block and "optimize_calls" not in block.split("return 0")[0].replace('"optimize_calls"', "")


def test_full_batch_order_parallel_rules_reference_and_resume(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"FAKE_SLEEP_R1": "5", "FAKE_SLEEP_R2": "5", "FAKE_SLEEP_R5": "5", "FAKE_SLEEP_R6": "5", "FAKE_OBJ_R3": str(2e11 * (1 + 5e-6)),
                             "FAKE_C1_R2": "101", "FAKE_C1_REGRADE_R2": "111", "FAKE_C1_R8": "101"})
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, (p.stdout + p.stderr)[-1500:] + st[-3000:]
    calls = _calls(tmp_path)
    assert sorted(c[1] for c in calls) == sorted(S.RUNS) and len(calls) == 12                                  # every run solved exactly once
    assert all(c[2] == S.RUNS[c[1]]["profile"] for c in calls)
    assert all(float(c[3]) == (3600.0 if c[1] == "P1" else 21600.0) for c in calls)                            # registered TimeLimits
    assert all(c[6] == str(tmp_path / "lic") for c in calls)
    (a1, b1), (a2, b2) = _span(calls, "R1"), _span(calls, "R2")
    assert a1 < b2 and a2 < b1                                                                                  # R1 | R2 at the same time (8 + 8 <= 25)
    (a3, b3), (a4, b4) = _span(calls, "R3"), _span(calls, "R4")
    assert b3 <= a4 or b4 <= a3                                                                                 # 16 + 16 > 25: one after the other
    assert min(a3, a4) >= max(b1, b2) + 1 and "PHASE_2:one_after_the_other:R3,R4" in st                        # phase order and gap
    (a5, b5), (a6, b6) = _span(calls, "R5"), _span(calls, "R6")
    assert a5 < b6 and a6 < b5 and min(a5, a6) >= max(b3, b4) + 1                                               # two lanes in phase 3
    for prev, nxt in (("R5", "R7"), ("R7", "R9"), ("R9", "R11"), ("R6", "R8"), ("R8", "R10")):                 # lane order and >= gap in the lane
        assert _span(calls, nxt)[0] >= _span(calls, prev)[1] + 1
    ap1 = _span(calls, "P1")[0]
    assert ap1 >= max(_span(calls, r)[1] for r in S.RUNS if r != "P1") + 1                                      # P1 last, alone
    var = _calls(tmp_path, "variant")
    assert sorted(v[1] for v in var) == ["R10", "R11", "R5", "R6", "R7", "R8", "R9"] and all(v[-1] == "stale=False" for v in var)
    assert {v[1]: v[3] for v in var}["R10"].endswith("integrated_costs_active_research.csv") and {v[1]: v[3] for v in var}["R11"].endswith("disconnected_costs_active_research.csv")
    c1 = {c[1]: c[2] for c in _calls(tmp_path, "c1")}
    assert c1["R1"] == c1["R2"] == "ref=default" and all(c1[r] == "ref=batch" for r in ("R3", "R4", "R5", "R8", "R11"))   # provisional before the batch reference
    assert sorted(c[1] for c in _calls(tmp_path, "regrade")) == ["R1", "R2"]
    r2 = json.loads((out / "R2" / "PRECISION.json").read_text())
    assert len(r2["grade_history"]) == 1 and json.loads((out / "R2" / "V6_ACCEPTANCE_PROVISIONAL.json").read_text())["label"] == "NOT_ACCEPTED"
    assert json.loads((out / "R2" / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2"            # provisional NOT_ACCEPTED (b) -> no stop
    assert "NOT_ACCEPTED_REFERENCE_DEPENDENT:R2" in st and "NOT_ACCEPTED_REFERENCE_DEPENDENT:R8" in st and "STOP_NOT_ACCEPTED" not in st
    assert sorted(c[1] for c in _calls(tmp_path, "rhs_loo")) == ["R5", "R6", "R7"]
    assert _calls(tmp_path, "m12_loo")[0][1:] == ["LA", "TH", "VN", "standalone=R2"]
    assert json.loads((out / "PROFILE_CHOICE.json").read_text())["profile"] == "formal_barrier_1e6_t16"         # rel diff 5e-6 <= 1e-5, C1 passed
    summ = json.loads((out / "BATCH3_SUMMARY.json").read_text())
    assert summ["B6"]["passed"] and abs(summ["B6"]["b6_bn"] - 100.0) < 1e-9
    sens = {(x["new"], x["base"]): x for x in summ["sensitivity"]}
    assert set(sens) == {("R8", "R2"), ("R9", "R2"), ("R10", "R1"), ("R11", "R2")} and sens[("R8", "R2")]["usable"] is False   # R8 NOT_ACCEPTED
    assert (out / "export" / "P1" / "P1_SUMMARY.json").exists() and not (out / "P1" / "PRECISION.json").exists()   # P1: probe only
    packs = sorted(x.name for x in out.glob("results_*_final_*.tar.gz"))
    assert len(packs) == 2 and len(sorted(out.glob("results_light_pre_p1_*.tar.gz"))) == 1 and "DONE:" in st
    n = len(_calls(tmp_path))
    p = _run(tmp_path, pkg)                                                                                     # resume: nothing is solved again
    assert p.returncode == 0 and len(_calls(tmp_path)) == n and (out / "STATUS.txt").read_text().count("SKIP_ENDED_") == 12


def test_two_t16_sessions_need_32_cores_and_stop_rule_d12(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"CORES": "32", "FAKE_SLEEP_R3": "5", "FAKE_SLEEP_R4": "5", "FAKE_SLEEP_R5": "5", "FAKE_SLEEP_R6": "10", "FAKE_C1_R5": "011"})
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 3, st[-2000:]
    calls = _calls(tmp_path)
    (a3, b3), (a4, b4) = _span(calls, "R3"), _span(calls, "R4")
    assert a3 < b4 and a4 < b3 and "PHASE_2:parallel:R3+R4:threads=32:cores=32" in st                          # 16 + 16 <= 32
    assert sorted(c[1] for c in calls) == ["R1", "R2", "R3", "R4", "R5", "R6"]                                  # C1 (a) of R5 fails: no new solve
    assert "STOP_NOT_ACCEPTED:R5" in st and (out / "STOP").read_text().split() == ["R5"]
    assert (out / "R6" / "V6_ACCEPTANCE.json").exists()                                                         # the running R6 finished and was post-processed
    assert "HALTED:" in st and (out / "BATCH3_SUMMARY.json").exists() and len(sorted(out.glob("results_full_halted_*.tar.gz"))) == 1


def test_wall_clock_kill_stops_the_batch_and_interrupted_solve_is_not_repeated(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"WALL_CAP_S": "3", "FAKE_SLEEP_R1": "60"})
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 3 and "KILLED_3S_R1" in st and (out / "R1" / ".cond").read_text().strip() == "killed_pre_solve"
    assert "STOP_NOT_ACCEPTED:R1" in st and not any(c[1] == "R3" for c in _calls(tmp_path) if len(c) > 1)
    assert not [x for x in os.popen("ps -eo cmd").read().splitlines() if str(FAKE) in x and "solve" in x]   # whole process group ended
    out2 = tmp_path / "second"; (out2 / "R1").mkdir(parents=True); (out2 / "R1" / ".started").write_text("2026-10-22T00:00:00Z pid=1 pgid=1")
    p = _run(tmp_path, pkg, {"RUN_DIR": str(out2), "FAKE_OUT": str(out2)})
    st = (out2 / "STATUS.txt").read_text()
    solves = [x for x in (out2 / "CALLS.txt").read_text().splitlines() if x.startswith("solve")]
    assert p.returncode == 3 and "STOP_SAFE:INTERRUPTED_R1" in st and solves == []                            # R2 of the other lane not started either


def test_variant_sha256_differing_from_the_dry_run_is_a_safe_stop(tmp_path):
    pkg = _package(tmp_path)
    e = json.loads((pkg / "EXPECTED_VARIANTS.json").read_text()); e["R9"]["output_sha256"] = "0" * 64
    (pkg / "EXPECTED_VARIANTS.json").write_text(json.dumps(e))
    p = _run(tmp_path, pkg)
    st = (tmp_path / "out" / "STATUS.txt").read_text()
    assert p.returncode == 3 and "STOP_SAFE:VARIANT_SHA256_R9" in st and _calls(tmp_path) == []


def test_build_only_dry_run_no_solver_and_licence_tripwire(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"BUILD_ONLY": "1"}, args=())
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, st[-2000:]
    builds = _calls(tmp_path, "build")
    assert sorted(b[1] for b in builds) == sorted(r for r in S.RUNS if r != "P1") and _calls(tmp_path) == []
    assert all(b[4] == "/nonexistent/m10p_dry_run_no_licence" for b in builds)
    for rid in S.RUNS:
        if rid == "P1":
            assert json.loads((out / "P1" / "PARAM_CHECK.json").read_text())["passed"]
        else:
            bc = json.loads((out / rid / "BUILD_CHECK.json").read_text()); assert bc["passed"], (rid, bc["checks"])
    assert "PHASE_1:one_after_the_other" in st and len(list(out.glob("results_light_final_*.tar.gz"))) == 1 and "DONE:" in st


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
    assert len(_calls(tmp_path)) == n and "PREPARE:skipped" in st and st.count("POST_ONLY_") == 9          # no solve; R3, R4, R6-R11, P1 skipped
    assert sorted(c[1] for c in _calls(tmp_path, "regrade")) == ["R1", "R2"] and [c[1] for c in _calls(tmp_path, "rhs_loo")] == ["R5"]
    assert {c[1]: c[2] for c in _calls(tmp_path, "c1")}["R5"] == "ref=batch"
    assert _calls(tmp_path, "m12_loo")[0][1:] == ["VN", "standalone=R2"]
    assert json.loads((out / "PROFILE_CHOICE.json").read_text())["profile"] == "formal_barrier"                 # R3 / R4 missing -> profile A
    assert json.loads((out / "R5" / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2" and "DONE:" in st


def test_unregistered_limits_are_refused(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"ALLOW_UNREGISTERED": "0", "WALL_CAP_S": "100", "LICENCE_GAP_S": "330"})
    assert p.returncode == 2 and "REFUSED: WALL_CAP_S=100" in p.stdout
    p = _run(tmp_path, pkg, {"ALLOW_UNREGISTERED": "0", "LICENCE_GAP_S": "330"}, args=())
    assert p.returncode == 2 and "--auth" in p.stdout


def test_pack_refuses_licence_strings(tmp_path):
    out = tmp_path / "out"; (out / "export" / "R1").mkdir(parents=True); (out / "export" / "R1" / "x.txt").write_text("ok")
    p = subprocess.run(["bash", str(PKG / "pack_results.sh"), str(out), "t"], env=dict(os.environ, PY=sys.executable), capture_output=True, text=True)
    assert p.returncode == 0 and "PACKED:light=" in p.stdout
    (out / "export" / "R1" / "y.txt").write_text("Set parameter " + "Li" + "censeID to value 1")
    p = subprocess.run(["bash", str(PKG / "pack_results.sh"), str(out), "u"], env=dict(os.environ, PY=sys.executable), capture_output=True, text=True)
    assert p.returncode == 1 and "PACK_REFUSED" in p.stdout and not list(out.glob("results_*_u_*.tar.gz"))


def test_p1_summary_parses_timing_and_memory(tmp_path):
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
