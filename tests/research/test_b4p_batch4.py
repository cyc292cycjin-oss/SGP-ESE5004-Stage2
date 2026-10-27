"""B4P (fourth-batch preparation; instruction A4): the fourth-batch runner research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/run_batch4.sh
and scripts_project/b4_batch4.py, driven end to end with SYNTHETIC stand-ins (tests/research/fixtures/b4p_fake_pipeline.py: no solver, no model)
on a package-like folder; GATES_V6, the graded class and the batch summary are the real code. Covered: the registered run table and thresholds;
serial order and resume; the P1 probe (F2 beside F1 only when the F1 peak stays within the threshold AND the cores suffice); the memory stop
(cgroup anon memory above the fraction -> STOP_SAFE:MEMORY, the Gurobi process group killed, F2 not started); the early speed check (iterations
11-20 projection above the fraction of TimeLimit -> STOP_SAFE:PROJECTION); a Gurobi MEM_LIMIT status without solution -> class nosol -> UNUSABLE
and STOP; a post-solve exception that keeps the termination status and the solution (A3.1) -> not nosol, the batch goes to DONE; the local dry run
(BUILD_ONLY, no solver), single mode, refusal of test hooks / unregistered values in a formal run.
The stand-ins carry the real script names (scripts_project/s2_solve.py, b4_split_solve.py) so that the runner's process counts see them (M10A F1).
Never run beside a real local solve (the counts would see it)."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4"
PKG3 = ROOT / "research/06_scope_redesign/p1_m10p_20261022/cloud_package"
FAKE = ROOT / "tests/research/fixtures/b4p_fake_pipeline.py"
sys.path.insert(0, str(ROOT / "scripts_project"))
import b4_batch4 as B   # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("setsid") is None or not Path("/usr/bin/time").exists(), reason="setsid / GNU time missing")
HOOK_KEYS = ("ALLOW_UNREGISTERED", "BUILD_ONLY", "POST_ONLY", "DRY", "TRUNCATE", "SOLVE_CMD", "SPLIT_CMD", "VA_CMD", "C1_CMD", "M12_CMD", "M12A_CMD", "G6_CMD", "SUM_CMD", "PACK_CMD",
             "LEDGER_CMD", "WALL_CAP_S", "GUROBI_TIME_LIMIT_S", "LICENCE_GAP_S", "GRACE_S", "MONITOR_S", "POST_TIMEOUT_S", "PACK_TIMEOUT_S", "SOLVE_MODE", "CORES", "MEM_QUOTA_GIB",
             "CGROUP_ROOT", "P1_WINDOW_S", "P1_THRESHOLD", "P1_MIN_CORES", "RUN_DIR", "REMOVE_LP")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _clean_env(extra=None):
    env = {k: v for k, v in os.environ.items() if k not in HOOK_KEYS and not k.startswith("FAKE_")}
    env.update(extra or {})
    return env


def _package(tmp: Path) -> Path:
    pkg = tmp / "pkg"; nets = pkg / "networks"; nets.mkdir(parents=True)
    shutil.copy(PKG / "run_batch4.sh", pkg / "run_batch4.sh"); shutil.copy(PKG3 / "pack_results.sh", pkg / "pack_results.sh")
    for sc in ("integrated", "disconnected"):
        (nets / f"{sc}_2920_3h_unsolved.nc").write_bytes(f"{sc}2920_3h".encode())
        (nets / f"{sc}_costs_active_research.csv").write_text("technology\n")
        (nets / f"{sc}_BUILD_RECEIPT.json").write_text(json.dumps(dict(code_sha=B.BUILD_COMMIT, network=dict(sha256=sha(nets / f"{sc}_2920_3h_unsolved.nc"), snapshots=2920),
                                                                     daily_network=dict(sha256="d" * 64, snapshots=365))))
    (tmp / "lic").write_text("synthetic placeholder")
    w = tmp / "standin" / "scripts_project"; w.mkdir(parents=True)
    (w / "s2_solve.py").write_text(f"import runpy, sys\nsys.argv = [{str(FAKE)!r}, 'solve', *sys.argv[1:]]\nrunpy.run_path({str(FAKE)!r}, run_name='__main__')\n")
    (w / "b4_split_solve.py").write_text(f"import runpy, sys\nsys.argv = [{str(FAKE)!r}, 'split-solve', *sys.argv[1:]]\nrunpy.run_path({str(FAKE)!r}, run_name='__main__')\n")
    cg = tmp / "cgroup"; cg.mkdir(); (cg / "memory.stat").write_text("anon 1073741824\nfile 0\n"); (cg / "memory.max").write_text("max\n"); (cg / "cpu.max").write_text("max 100000\n")
    return pkg


def _run(tmp: Path, pkg: Path, extra=None, args=("--auth", "synthetic test"), timeout=600, registered_sha=True):
    f = f"{sys.executable} {FAKE}"; w = tmp / "standin" / "scripts_project"
    env = _clean_env(dict(REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(tmp / "out"), FAKE_OUT=str(tmp / "out"), ALLOW_UNREGISTERED="1", LICENCE_GAP_S="1", GRACE_S="1", MONITOR_S="1",
                          CORES="72", MEM_QUOTA_GIB="240", CGROUP_ROOT=str(tmp / "cgroup"), GRB_LICENSE_FILE=str(tmp / "lic"), GUROBI_TIME_LIMIT_S="1000", WALL_CAP_S="1200",
                          SOLVE_CMD=f"{sys.executable} {w / 's2_solve.py'}", SPLIT_CMD=f"{sys.executable} {w / 'b4_split_solve.py'}",
                          VA_CMD=f"{f} va", C1_CMD=f"{f} c1", M12_CMD=f"{f} m12", M12A_CMD=f"{f} m12a", FAKE_SLEEP="0.2", P1_WINDOW_S="3"))
    env.update(extra or {})
    return subprocess.run(["bash", str(pkg / "run_batch4.sh"), *args], env=env, capture_output=True, text=True, timeout=timeout)


def _calls(tmp: Path, kind="gurobi"):
    p = tmp / "out" / "CALLS.txt"
    return [x.split() for x in p.read_text().splitlines() if x.split() and x.split()[0] == kind] if p.exists() else []


def _span(calls, rid):
    c = next(x for x in calls if x[1] == rid)
    return float(c[4]), float(c[5])


def test_run_table_and_thresholds_are_the_registered_plan():
    assert list(B.RUNS) == ["F1", "F2"] and all(r["profile"] == B.T16 for r in B.RUNS.values())
    assert B.RUNS["F1"]["scenario"] == "integrated" and B.RUNS["F2"]["scenario"] == "disconnected" and all(r["set"] == "" for r in B.RUNS.values())
    assert B.RUNS["F1"]["iterations_reference"] == 450 and B.RUNS["F2"]["iterations_reference"] == 250 and B.STOP_ALWAYS == ("F1", "F2")
    assert (B.MEMORY_STOP_FRACTION, B.PROJECTION_FRACTION, B.PROJECTION_AFTER_ITERATION, B.P1_THRESHOLD, B.P1_MIN_CORES, B.P1_WINDOW_S) == (0.80, 0.80, 20, 0.40, 33, 3600)
    # HPR (2026-10-27; user decisions B1 / B2, RUN_PLAN_HPC.md): the registered inputs are the v2 2920x3h networks (63,873,447 / 63,202,193 B, build 72083fde)
    # and the TimeLimit is 864,000 s - the B4P values (64,106,133 B / ec80668f / 259,200 s) are superseded and kept in RUN_PLAN_B4.md
    assert set(B.REGISTERED_SHA) == {"integrated_2920_3h_unsolved.nc", "disconnected_2920_3h_unsolved.nc"} and B.REGISTERED_BYTES["integrated_2920_3h_unsolved.nc"] == 63873447
    assert B.REGISTERED_BYTES["disconnected_2920_3h_unsolved.nc"] == 63202193 and B.BUILD_COMMIT == "72083fde6bffd89580869af6dd00885a8d76721f"
    src = (PKG / "run_batch4.sh").read_text()
    assert f"R_TL={B.TIME_LIMIT_S}; R_WALL={B.WALL_CAP_S}; R_GAP={B.LICENCE_GAP_S}; R_MODE=split" in src and B.TIME_LIMIT_S == 864000 and 'BUILD_ONLY / POST_ONLY / DRY / --repost' in src


def test_projection_p1_and_memstat_helpers(tmp_path):
    d = tmp_path / "F1"; d.mkdir()
    lines = ["Iter       Primal          Dual         Primal    Dual     Compl     Time"] + [f"{i:4d}   1.0e+11  1.0e+11  1e-3 1e-3 1e-3  {100 + i * 30}s" for i in range(22)]
    (d / "gurobi.linopy.log").write_text("\n".join(lines) + "\n")
    r = B.projection(d, time_limit=259200, iterations=450, now_s=800)
    assert r["ready"] and r["seconds_per_iteration_11_20"] == 30.0 and r["projected_total_s"] == 30.0 * 450 + 800 and not r["exceeded"]
    r2 = B.projection(d, time_limit=10000, iterations=450); assert r2["exceeded"] and r2["elapsed_s"] == 100 + 21 * 30
    (d / "gurobi.linopy.log").write_text("\n".join(lines[:15]) + "\n"); assert not B.projection(d, 259200, 450)["ready"]
    mon = tmp_path / "MONITOR_F1.csv"
    mon.write_text("utc,elapsed_s,rss_gib_group,cgroup_mem_used_gib,cgroup_anon_gib,cgroup_mem_limit_gib,host_mem_available_gib,disk_free_gib,gurobi_last_line\n"
                   + "".join(f"t,{e},{10 + e / 100:.2f},,{20 + e / 50:.2f},240,,,\n" for e in range(0, 3601, 60)))
    p = B.p1_decision(mon, 240, 72); assert p["parallel"] and p["column"] == "cgroup_anon_gib" and abs(p["peak_gib"] - 92.0) < 1e-6
    assert not B.p1_decision(mon, 240, 25)["parallel"] and not B.p1_decision(mon, 200, 72)["parallel"] and not B.p1_decision(mon, 240, 72, window_s=7200)["parallel"]
    cg = tmp_path / "cg"; cg.mkdir(); (cg / "memory.stat").write_text("anon 91268055040\nfile 99999999999\n"); (cg / "memory.max").write_text(str(100 * 2**30) + "\n"); (cg / "memory.current").write_text("1\n")
    m = B.memstat(cg); assert m["stop"] and abs(m["fraction"] - 0.85) < 1e-9 and m["anon_gib"] == 85.0 and m["limit_gib"] == 100.0 and m["anon_bytes"] == 91268055040   # the file cache is not counted
    (cg / "memory.stat").write_text("anon 85899345920\nfile 99999999999\n"); assert not B.memstat(cg)["stop"]                                             # exactly 80 %: "above" means strictly above
    (cg / "memory.stat").write_text("anon 1\nfile 99999999999\n"); assert not B.memstat(cg)["stop"]


def test_serial_when_the_probe_fails_reference_regrade_summary_and_resume(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, dict(CORES="25", FAKE_SLEEP_F1="6", FAKE_SLEEP_F2="2", FAKE_C1_F2="101", FAKE_C1_REGRADE_F2="111"))
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, (p.stdout + p.stderr)[-1500:] + st[-3000:]
    g = _calls(tmp_path); assert sorted(c[1] for c in g) == ["F1", "F2"] and all(float(c[3]) == 1000.0 for c in g) and all(c[6] == str(tmp_path / "lic") for c in g)
    assert _span(g, "F2")[0] >= _span(g, "F1")[1] + 1                                                      # F2 after F1 (probe failed: 25 cores < 33) and the gap
    assert "P1_PROBE:" in st and "decision=after_F1" in st and json.loads((out / "P1_DECISION.json").read_text())["parallel"] is False
    assert [c[1] for c in _calls(tmp_path, "build")] == ["F1", "F2"] and [c[1] for c in _calls(tmp_path, "assign")] == ["F1", "F2"]
    assert all(c[7] == "omp=None" and c[8] == f"tmp={out / 'tmp'}" for c in g)                              # solve environment untouched except TMPDIR
    c1 = {c[1]: c[2] for c in _calls(tmp_path, "c1")}; assert c1 == {"F1": "ref=default", "F2": "ref=default"}
    assert sorted(c[1] for c in _calls(tmp_path, "regrade")) == ["F1", "F2"] and (out / "BATCH_REFERENCE.json").exists()
    assert json.loads((out / "F2" / "V6_ACCEPTANCE_PROVISIONAL.json").read_text())["label"] == "NOT_ACCEPTED" and json.loads((out / "F2" / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2"
    assert "STOP_NOT_ACCEPTED" not in st and "STOP_SAFE" not in st and "UNUSABLE:" not in st and "PROJECTION_F1:" in st and "within the limit" in st
    summ = json.loads((out / "BATCH4_SUMMARY.json").read_text())
    assert abs(summ["B6"]["b6_bn"] - 100.0) < 1e-9 and summ["B6"]["usable"] and summ["unusable"] == {} and summ["p1"]["parallel"] is False and summ["projection"]["F1"]["ready"]
    assert (out / "export" / "F1" / "split" / "SPLIT_SOLVE.json").exists() and (out / "export" / "F1" / "MONITOR_F1.csv").exists() and not (out / "F1" / "split" / "problem.lp").exists()   # REMOVE_LP=1
    assert len(sorted(out.glob("results_*_final_*.tar.gz"))) == 2 and "DONE:" in st
    n = len(_calls(tmp_path)); p = _run(tmp_path, pkg, dict(CORES="25"))
    assert p.returncode == 0 and len(_calls(tmp_path)) == n and (out / "STATUS.txt").read_text().count("SKIP_ENDED_") == 2


def test_parallel_when_the_probe_passes(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, dict(FAKE_SLEEP_F1="12", FAKE_SLEEP_F2="3"))
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, (p.stdout + p.stderr)[-1500:] + st[-3000:]
    g = _calls(tmp_path); (a0, a1), (b0, b1) = _span(g, "F1"), _span(g, "F2")
    assert a0 < b0 < a1 and "decision=parallel" in st and json.loads((out / "P1_DECISION.json").read_text())["parallel"] is True
    assert b0 - a0 >= 3.0                                                                                   # not before the probe window
    assert "DONE:" in st and json.loads((out / "BATCH4_SUMMARY.json").read_text())["B6"]["usable"]


def test_memory_stop_kills_the_solve_and_nothing_else_starts(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, dict(CORES="25", MEM_QUOTA_GIB="100", FAKE_SLEEP_F1="20", FAKE_MEM_SPIKE_F1=f"3:{int(90 * 2**30)}", FAKE_IGNORE_TERM_F1="1"))
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 3, st[-2000:]
    assert "MEMORY_STOP_F1:" in st and "STOP_SAFE:MEMORY:F1" in st and (out / "STOP_SAFE").exists() and "KILL9_F1" in st
    assert (out / "F1" / ".cond").read_text().strip() == "killed_memory" and not (out / "F2" / ".started").exists() and _calls(tmp_path) == []   # the stand-in never reached its call line
    assert "HALTED:" in st and not list(out.glob("results_*_final_*"))


def test_projection_stop(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, dict(CORES="25", FAKE_SLEEP_F1="15", FAKE_ITER_S_F1="10"))                   # 10 s x 450 + elapsed > 800 = 0.8 x 1000
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 3, st[-2000:]
    assert "PROJECTION_STOP_F1:" in st and "STOP_SAFE:PROJECTION:F1" in st and json.loads((out / "PROJECTION_F1.json").read_text())["exceeded"]
    assert (out / "F1" / ".cond").read_text().strip() == "killed_projection" and not (out / "F2" / ".started").exists()


def test_mem_limit_status_without_solution_is_nosol_and_stops(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, dict(CORES="25", FAKE_GUROBI_STATUS_F1="MEM_LIMIT"))
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 3, st[-2000:]
    rec = json.loads((out / "F1" / "SOLVE_RECEIPT.json").read_text())
    assert rec["termination_condition"] == "internal_solver_error" and rec["split"]["gurobi_status_name"] == "MEM_LIMIT" and "solution" not in rec
    assert json.loads((out / "F1" / "STOP_CLASS.json").read_text())["cls"] == "nosol" and "UNUSABLE:F1:nosol" in st and (out / "STOP").read_text().split() == ["F1"]
    assert not (out / "F2" / ".started").exists() and "HALTED:" in st


def test_post_solve_error_keeps_status_and_solution(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, dict(CORES="25", FAKE_POST_ERROR_F1="1"))
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, st[-2000:]
    rec = json.loads((out / "F1" / "SOLVE_RECEIPT.json").read_text())
    assert rec["termination_condition"] == "optimal" and rec["solution"]["X"]["count"] == 10 and [e["step"] for e in rec["post_solve_errors"]] == ["co2_flows"] and rec["post_solve_complete"] is False
    assert "ASSIGN_F1:exit=4" in st and "post_errors=" in st
    assert json.loads((out / "F1" / "STOP_CLASS.json").read_text())["cls"] == "accepted" if (out / "F1" / "STOP_CLASS.json").exists() else True
    assert json.loads((out / "F1" / "V6_ACCEPTANCE.json").read_text())["label"].startswith("ACCEPTED") and "UNUSABLE:" not in st and "DONE:" in st
    assert json.loads((out / "BATCH4_SUMMARY.json").read_text())["runs"]["F1"]["post_solve_errors"] == ["co2_flows"]


def test_build_only_dry_run_and_single_mode(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, dict(BUILD_ONLY="1"), args=())
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, st[-2000:]
    assert _calls(tmp_path) == [] and [c[1] for c in _calls(tmp_path, "build")] == ["F1", "F2"] and all(c[4] == "None" for c in _calls(tmp_path, "build"))   # process 1 never sees the licence variable
    for rid in ("F1", "F2"):
        bc = json.loads((out / rid / "BUILD_CHECK.json").read_text()); assert bc["passed"] and bc["receipt_state"] == "split_built", bc["checks"]
    assert "BUILD_CHECK_F1:" in st and "DONE:" in st
    p = _run(tmp_path, pkg, dict(BUILD_ONLY="1"), args=("--auth", "x")); assert p.returncode == 2 and "REFUSED: --auth" in p.stdout
    t2 = tmp_path / "single"; t2.mkdir(); pkg2 = _package(t2)
    p = _run(t2, pkg2, dict(CORES="25", SOLVE_MODE="single", FAKE_SLEEP_F1="3"))
    st = (t2 / "out" / "STATUS.txt").read_text(); assert p.returncode == 0, st[-2000:]
    assert [c[1] for c in _calls(t2, "solve")] == ["F1", "F2"] and _calls(t2) == [] and "DONE:" in st and "solve_mode=single" in st


def test_formal_run_refuses_hooks_and_unregistered_values(tmp_path):
    pkg = _package(tmp_path)
    base = dict(REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(tmp_path / "out"), GRB_LICENSE_FILE=str(tmp_path / "lic"))
    p = subprocess.run(["bash", str(pkg / "run_batch4.sh"), "--auth", "x"], env=_clean_env(dict(base, SOLVE_CMD="python x")), capture_output=True, text=True, timeout=60)
    assert p.returncode == 2 and "REFUSED: SOLVE_CMD set" in p.stdout
    p = subprocess.run(["bash", str(pkg / "run_batch4.sh"), "--auth", "x"], env=_clean_env(dict(base, SOLVE_MODE="single")), capture_output=True, text=True, timeout=60)
    assert p.returncode == 2 and "SOLVE_MODE=single differs from the registered value split" in p.stdout
    p = subprocess.run(["bash", str(pkg / "run_batch4.sh"), "--auth", "x"], env=_clean_env(dict(base, GUROBI_TIME_LIMIT_S="100")), capture_output=True, text=True, timeout=60)
    assert p.returncode == 2 and "GUROBI_TIME_LIMIT_S=100 differs" in p.stdout
    assert not (tmp_path / "out").exists()
