"""DFX (instruction v3 F6; RUN_PLAN_DFX.md): the DFX 365x24h screening runner research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/run_dfx.sh,
scripts_project/dfx_batch.py and preflight_dfx.sh, driven end to end with the third-batch SYNTHETIC stand-ins (tests/research/fixtures/
m10p_fake_pipeline.py: no solver, no model) on a package-like folder with synthetic 365x24h network files (ALLOW_UNREGISTERED=1 -> base-check
--no-registered: receipt checks only). Covers: the registered table / limits / schedule; one lane below 33 cores and two lanes at 33; batch reference,
regrade, B6 = V2 - V1, the third-batch comparison, summary, packs, resume; the graded stop rule for the two reference runs (nosol, c1a, g2;
C1 (b) / (c) alone never stops); the wall-clock kill; safe stops (base SHA256, a 2920x3h file, a solver running at start); the BUILD_ONLY dry run
with the licence tripwire; the refusals of a formal run; preflight guards and the resource floor. Never runs while a real solve is running (busy())."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx"
PKG3 = ROOT / "research/06_scope_redesign/p1_m10p_20261022/cloud_package"
FAKE = ROOT / "tests/research/fixtures/m10p_fake_pipeline.py"
sys.path.insert(0, str(ROOT / "scripts_project"))
import dfx_batch as D   # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("setsid") is None or not Path("/usr/bin/time").exists(), reason="setsid / GNU time missing")
HOOK_KEYS = ("ALLOW_UNREGISTERED", "BUILD_ONLY", "POST_ONLY", "DRY", "TRUNCATE", "SOLVE_CMD", "VA_CMD", "C1_CMD", "M12_CMD", "M12A_CMD", "VAR_CMD", "G6_CMD",
             "SUM_CMD", "PACK_CMD", "WALL_CAP_S", "GUROBI_TIME_LIMIT_S", "LICENCE_GAP_S", "GRACE_S", "MONITOR_S", "POST_TIMEOUT_S", "PACK_TIMEOUT_S", "CORES", "RUN_DIR")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _clean_env(extra=None):
    env = {k: v for k, v in os.environ.items() if k not in HOOK_KEYS and not k.startswith("FAKE_")}
    env.update(extra or {})
    return env


def _package(tmp: Path) -> Path:
    pkg = tmp / "pkg"; nets = pkg / "networks"; nets.mkdir(parents=True)
    shutil.copy(PKG / "run_dfx.sh", pkg / "run_dfx.sh"); shutil.copy(PKG / "preflight_dfx.sh", pkg / "preflight_dfx.sh"); shutil.copy(PKG3 / "pack_results.sh", pkg / "pack_results.sh")
    shutil.copy(PKG.parent / "BATCH3_REFERENCE_VALUES.json", pkg / "BATCH3_REFERENCE_VALUES.json")
    for sc in ("integrated", "disconnected"):
        f = nets / f"{sc}_365_24h_unsolved.nc"; f.write_bytes(f"{sc}365_24h v2".encode())
        (nets / f"{sc}_costs_active_research.csv").write_text("technology\n")
        (nets / f"{sc}_BUILD_RECEIPT.json").write_text(json.dumps(dict(code_sha=D.BUILD_COMMIT, network=dict(sha256=hashlib.sha256(f"{sc}2920_3h v2".encode()).hexdigest(), snapshots=2920),
                                                                     daily_network=dict(sha256=sha(f), bytes=f.stat().st_size, snapshots=365))))
    (tmp / "lic").write_text("synthetic placeholder")
    w = tmp / "standin" / "scripts_project"; w.mkdir(parents=True)   # the solve stand-in under the real script name (busy() counts "s2_solve.py" lines)
    (w / "s2_solve.py").write_text(f"import runpy, sys\nsys.argv = [{str(FAKE)!r}, 'solve', *sys.argv[1:]]\nrunpy.run_path({str(FAKE)!r}, run_name='__main__')\n")
    return pkg


def _run(tmp: Path, pkg: Path, extra=None, args=("--auth", "synthetic test"), timeout=600):
    f = f"{sys.executable} {FAKE}"
    env = _clean_env(dict(REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(tmp / "out"), FAKE_OUT=str(tmp / "out"), ALLOW_UNREGISTERED="1", LICENCE_GAP_S="1",
                          GRACE_S="1", MONITOR_S="1", CORES="25", GRB_LICENSE_FILE=str(tmp / "lic"), SOLVE_CMD=f"{sys.executable} {tmp / 'standin' / 'scripts_project' / 's2_solve.py'}",
                          VA_CMD=f"{f} va", C1_CMD=f"{f} c1", M12_CMD=f"{f} m12", M12A_CMD=f"{f} m12a", FAKE_SLEEP="0.2"))
    env.update(extra or {})
    return subprocess.run(["bash", str(pkg / "run_dfx.sh"), *args], env=env, capture_output=True, text=True, timeout=timeout)


def _calls(tmp: Path, kind="solve"):
    p = tmp / "out" / "CALLS.txt"
    return [x.split() for x in p.read_text().splitlines() if x.split()[0] == kind] if p.exists() else []


def _span(calls, rid):
    c = next(x for x in calls if x[1] == rid)
    return float(c[4]), float(c[5])


def _overlap(calls, a, b):
    (a0, a1), (b0, b1) = _span(calls, a), _span(calls, b)
    return a0 < b1 and b0 < a1


def _status(tmp: Path) -> str:
    return (tmp / "out" / "STATUS.txt").read_text()


def test_run_table_limits_and_schedule_are_the_registered_plan():
    assert list(D.RUNS) == ["V1", "V2"] and all(r["profile"] == D.T16 and r["set"] == "" and r["base"].endswith("365_24h") for r in D.RUNS.values())
    assert D.RUNS["V1"]["scenario"] == "integrated" and D.RUNS["V2"]["scenario"] == "disconnected" and D.RUNS["V1"]["costs"] == "integrated" and D.RUNS["V2"]["costs"] == "disconnected"
    assert D.SCHEDULE == [("1", ["V1"], ["V2"])] and D.STOP_ALWAYS == ("V1", "V2") and D.LABEL == "DFX_365X24H"
    assert D.TIME_LIMIT_S == {"V1": 21600, "V2": 10800} and D.WALL_MARGIN_S == 1200 and D.LICENCE_GAP_S == 330 and D.PARALLEL_MIN_CORES == 33   # user amendment 2026-10-27 (was 3 x 4,882 / 1,423)
    assert D.BUILD_COMMIT == "72083fde6bffd89580869af6dd00885a8d76721f" and len(D.BUILD_COMMIT) == 40
    assert D.REGISTERED_SHA == {"integrated_365_24h_unsolved.nc": "82928a4c9151a6a176ac8c81bf56bbe41867e16ba0d059ce2ad8c6e78e59f6b2",
                                "disconnected_365_24h_unsolved.nc": "5c75bfa0e338fde4104deb41cdcaa72dddcf7b3782e6ad8ca1f4fb6c15cfbd5c"}
    assert D.REGISTERED_BYTES == {"integrated_365_24h_unsolved.nc": 31292240, "disconnected_365_24h_unsolved.nc": 30620986}
    thr = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())["research"]["solver"]["profiles"][D.T16]["Threads"]
    assert thr == 16 and D.PARALLEL_MIN_CORES == 2 * thr + 1
    out = subprocess.run([sys.executable, str(ROOT / "scripts_project/dfx_batch.py"), "limits"], capture_output=True, text=True, check=True).stdout.split()
    assert out == ["V1|21600|22800", "V2|10800|12000"]
    out = subprocess.run([sys.executable, str(ROOT / "scripts_project/dfx_batch.py"), "runtable"], capture_output=True, text=True, check=True).stdout.split()
    assert out == ["V1|integrated|integrated_365_24h||formal_barrier_1e6_t16|integrated", "V2|disconnected|disconnected_365_24h||formal_barrier_1e6_t16|disconnected"]
    src = (PKG / "run_dfx.sh").read_text()
    assert "R_GAP=330; R_PAR_CORES=33" in src and "dfx_batch.py" in src and "--only" not in src.split("\n", 60)[0] and "m08a_variants" not in src
    plan = (PKG.parent / "RUN_PLAN_DFX.md").read_text()
    assert all(s in plan for s in D.REGISTERED_SHA.values()) and "21,600" in plan and "10,800" in plan and "33" in plan and "R3 / R4" in plan
    rec = ROOT / "results_project/dfx_v3/builds_v2"   # the real build receipts when present (main checkout; not in a worktree)
    for sc in ("integrated", "disconnected"):
        r = rec / sc / f"{sc}_BUILD_RECEIPT.json"
        if r.exists():
            j = json.loads(r.read_text()); assert j["code_sha"] == D.BUILD_COMMIT and j["daily_network"]["sha256"] == D.REGISTERED_SHA[f"{sc}_365_24h_unsolved.nc"]


def test_serial_batch_reference_regrade_b6_summary_packs_and_resume(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, dict(FAKE_SLEEP_V1="3", FAKE_SLEEP_V2="3", FAKE_C1_V2="101", FAKE_C1_REGRADE_V2="111"))
    out = tmp_path / "out"; st = _status(tmp_path)
    assert p.returncode == 0, st[-3000:] + p.stderr[-2000:]
    calls = _calls(tmp_path)
    assert [c[1] for c in calls] == ["V1", "V2"] and not _overlap(calls, "V1", "V2") and "PHASE_1:one_lane:V1,V2:threads=32:cores=25:min_cores=33" in st
    assert all(c[2] == D.T16 and c[6] == str(tmp_path / "lic") for c in calls) and float(calls[0][3]) == 21600.0 and float(calls[1][3]) == 10800.0
    for rid in ("V1", "V2"):
        run = json.loads((out / rid / "RUN.json").read_text())
        assert run["registered_sha256"] == sha(pkg / "networks" / f"{run['base']}_unsolved.nc") == run["network_sha256"] and run["label"] == "DFX_365X24H" and run["wall_cap_s"] == run["time_limit"] + 1200
        prec = json.loads((out / rid / "PRECISION.json").read_text())
        assert prec["reference"]["source"].startswith("this batch") and len(prec["grade_history"]) == 1
        assert (out / rid / "V6_ACCEPTANCE_PROVISIONAL.json").exists() and (out / rid / ".label").read_text().strip().startswith("ACCEPTED")
        assert (out / rid / "m12_owen" / "OWEN_REGRADE_BATCH_REFERENCE.json").exists() and (out / "export" / rid / "SOLVE_RECEIPT.json").exists()
    assert (out / "BATCH_REFERENCE.json").exists() and "BATCH_REFERENCE:exit=0" in st and "REGRADE_V1:" in st and "REGRADE_V2:" in st and not (out / "STOP").exists()
    s = json.loads((out / "DFX_SUMMARY.json").read_text())
    assert s["B6"]["b6_bn"] == pytest.approx(100.0) and s["B6"]["runs"] == dict(integrated="V1", disconnected="V2") and all(v["state"] == "ended" for v in s["runs"].values())
    assert s["benefit"]["b6_bn"] == pytest.approx(100.0) and (out / "M12_BENEFIT" / "BENEFIT.json").exists()
    c = s["comparison"]; ref = json.loads((pkg / "BATCH3_REFERENCE_VALUES.json").read_text())
    assert c["batch3_b6_bn"] == ref["batch3"]["b6_bn"] and c["delta_b6_bn"] == pytest.approx(100.0 - ref["batch3"]["b6_bn"]) and c["first_order"]["predicted_delta_b6_bn"] == ref["first_order"]["delta_b6_bn"]
    assert c["delta_b6_minus_first_order_bn"] == pytest.approx(100.0 - ref["batch3"]["b6_bn"] - ref["first_order"]["delta_b6_bn"])
    assert c["main_runs"] == dict(integrated="R3", disconnected="R4") and c["alternative_runs"] == dict(integrated="R1", disconnected="R2")   # user amendment 2026-10-27
    assert c["objective_difference_bn"]["V1_minus_R3"] == pytest.approx((2e11 - ref["batch3"]["objective_eur"]["R3"]) / 1e9)
    assert c["objective_difference_bn"]["V2_minus_R2"] == pytest.approx((3e11 - ref["batch3"]["objective_eur"]["R2"]) / 1e9) and c["delta_b6_alternative_bn"] == pytest.approx(100.0 - ref["batch3"]["b6_alternative_bn"])
    md = (out / "DFX_SUMMARY.md").read_text(); assert "B6（V2 − V1）" in md and "一阶预测" in md and "100.0000 bn" in md
    assert len(list(out.glob("results_light_final_*.tar.gz"))) == 1 and len(list(out.glob("results_full_final_*.tar.gz"))) == 1 and "DONE:" in st
    assert (out / "export" / "batch" / "DFX_SUMMARY.md").exists() and (out / "export" / "batch" / "BATCH3_REFERENCE_VALUES.json").exists()
    n = len(calls)
    p = _run(tmp_path, pkg)   # resume: nothing is re-solved
    st = _status(tmp_path)
    assert p.returncode == 0 and "SKIP_ENDED_V1:optimal" in st and "SKIP_ENDED_V2:optimal" in st and len(_calls(tmp_path)) == n and st.count("DONE:") == 2


def test_two_lanes_at_33_cores_and_one_lane_below(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, dict(CORES="33", FAKE_SLEEP_V1="5", FAKE_SLEEP_V2="5"))
    st = _status(tmp_path); calls = _calls(tmp_path)
    assert p.returncode == 0, st[-2000:]
    assert "PHASE_1:two_lanes:A=V1:B=V2:threads=32:cores=33:min_cores=33" in st and _overlap(calls, "V1", "V2")
    t2 = tmp_path / "b"; t2.mkdir(); pkg2 = _package(t2)
    p = _run(t2, pkg2, dict(CORES="32", FAKE_SLEEP_V1="3", FAKE_SLEEP_V2="3"))
    st = _status(t2); calls = _calls(t2)
    assert p.returncode == 0 and "PHASE_1:one_lane:V1,V2:threads=32:cores=32:min_cores=33" in st and not _overlap(calls, "V1", "V2")
    gap = _span(calls, "V2")[0] - _span(calls, "V1")[1]
    assert gap >= 1.0   # LICENCE_GAP_S=1 in the tests (registered 330 s)


@pytest.mark.parametrize("rid,extra,cls,other_started", [
    ("V1", {"FAKE_NOSOL_V1": "1"}, "nosol", False),                                     # reference run without a solution: STOP, V2 never starts (one lane)
    ("V2", {"FAKE_C1_V2": "011"}, "c1a", True),                                         # reference run with C1 (a) failed: STOP after V2
    ("V1", {"FAKE_SUBSET_V1": "differ"}, "g2", False),                                  # input problem (configuration subset differs): STOP
])
def test_graded_stop_rule_stops_on_the_reference_runs(tmp_path, rid, extra, cls, other_started):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, extra)
    out = tmp_path / "out"; st = _status(tmp_path)
    assert p.returncode == 3, st[-2000:]
    assert (out / "STOP").read_text().split() == [rid] and f"STOP_NOT_ACCEPTED:{rid}:{cls}:" in st and "HALTED:" in st
    sc = json.loads((out / rid / "STOP_CLASS.json").read_text()); assert sc["cls"] == cls and sc["action"] == "stop" and "V1 / V2 are both batch reference runs" in sc["rule"]
    other = "V2" if rid == "V1" else "V1"
    assert ([c[1] for c in _calls(tmp_path)].count(other) == 1) == other_started
    assert len(list(out.glob("results_light_halted_*.tar.gz"))) == 1 and not (out / "UNUSABLE").exists()
    n = len(_calls(tmp_path))
    p = _run(tmp_path, pkg)   # resume after a STOP: nothing new is solved (the ended run is skipped, the other is not started)
    assert p.returncode == 3 and len(_calls(tmp_path)) == n and _status(tmp_path).count("HALTED:") == 2


def test_c1_b_c_alone_never_stops(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, dict(FAKE_C1_V2="101", FAKE_C1_REGRADE_V2="101"))
    st = _status(tmp_path)
    assert p.returncode == 0, st[-2000:]
    assert not (tmp_path / "out" / "STOP").exists() and "STOP_NOT_ACCEPTED" not in st and "DONE:" in st
    sc = tmp_path / "out" / "V2" / "STOP_CLASS.json"
    if sc.exists():
        assert json.loads(sc.read_text())["cls"] == "ref_dependent" and "NOT_ACCEPTED_REFERENCE_DEPENDENT:V2" in st


def test_wall_clock_kill_is_recorded_and_stops_the_batch(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"WALL_CAP_S": "3", "FAKE_SLEEP_V1": "60"})
    out = tmp_path / "out"; st = _status(tmp_path)
    assert p.returncode == 3, st[-2000:]
    assert "KILLED_3S_V1:" in st and (out / "V1" / ".cond").read_text().strip() == "killed_pre_solve" and (out / "STOP").read_text().split() == ["V1"]
    assert json.loads((out / "V1" / "STOP_CLASS.json").read_text())["cls"] == "nosol" and not [c for c in _calls(tmp_path) if c[1] == "V2"]
    assert not [x for x in os.popen("ps -eo args").read().splitlines() if str(tmp_path) in x and "s2_solve.py" in x]   # the process group is gone


def test_safe_stops_base_sha256_2920_file_and_solver_running(tmp_path):
    pkg = _package(tmp_path); nets = pkg / "networks"
    r = json.loads((nets / "integrated_BUILD_RECEIPT.json").read_text()); r["daily_network"]["sha256"] = "0" * 64; (nets / "integrated_BUILD_RECEIPT.json").write_text(json.dumps(r))
    p = _run(tmp_path, pkg)
    st = _status(tmp_path)
    assert p.returncode == 3 and "STOP_SAFE:BASE_NETWORK_SHA256:DIFFERENT:integrated_365_24h_unsolved.nc" in st and _calls(tmp_path) == []
    t2 = tmp_path / "b"; t2.mkdir(); pkg2 = _package(t2); (pkg2 / "networks" / "integrated_2920_3h_unsolved.nc").write_bytes(b"x")
    p = _run(t2, pkg2)
    assert p.returncode == 3 and "STOP_SAFE:BASE_NETWORK_SHA256:DIFFERENT::2920x3h_present" in _status(t2) and _calls(t2) == []
    t3 = tmp_path / "c"; t3.mkdir(); pkg3 = _package(t3)
    busy = subprocess.Popen([sys.executable, "-c", "import sys, time; time.sleep(60)", "s2_solve.py", str(t3)])
    try:
        time.sleep(0.5); p = _run(t3, pkg3)
        assert p.returncode == 3 and "STOP_SAFE:SOLVER_PROCESS_RUNNING_AT_START:1 s2_solve processes" in _status(t3) and _calls(t3) == []
    finally:
        busy.kill(); busy.wait()


def test_build_only_dry_run_no_solver_and_licence_tripwire(tmp_path):
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"BUILD_ONLY": "1"}, args=())
    out = tmp_path / "out"; st = _status(tmp_path)
    assert p.returncode == 0, st[-2000:]
    builds = _calls(tmp_path, "build")
    assert [b[1] for b in builds] == ["V1", "V2"] and _calls(tmp_path) == [] and all(b[4] == "/nonexistent/dfx_dry_run_no_licence" for b in builds)
    assert float(builds[0][3]) == 21600.0 and float(builds[1][3]) == 10800.0
    for rid in D.RUNS:
        bc = json.loads((out / rid / "BUILD_CHECK.json").read_text()); assert bc["passed"], (rid, bc["checks"])
        assert "BUILD_CHECK_%s:" % rid in st and (out / "export" / rid / "BUILD_CHECK.json").exists()
    assert "PHASE_1:one_lane:V1,V2:threads=32:cores=25:min_cores=33:no_solve_mode" in st and len(list(out.glob("results_light_final_*.tar.gz"))) == 1 and "DONE:" in st
    assert (out / "export" / "batch" / "DFX_SUMMARY.json").exists() and json.loads((out / "DFX_SUMMARY.json").read_text())["B6"] is None


def test_formal_run_refuses_hooks_unregistered_values_and_no_solve_auth(tmp_path):
    pkg = _package(tmp_path)
    base = dict(REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(tmp_path / "o"), GRB_LICENSE_FILE=str(tmp_path / "lic"))
    def run(extra, args=("--auth", "x")):
        return subprocess.run(["bash", str(pkg / "run_dfx.sh"), *args], env=_clean_env(dict(base, **extra)), capture_output=True, text=True, timeout=60)
    p = run(dict(SOLVE_CMD="python x")); assert p.returncode == 2 and "REFUSED: SOLVE_CMD set" in p.stdout
    p = run(dict(FAKE_SLEEP_V1="9")); assert p.returncode == 2 and "REFUSED: FAKE_SLEEP_V1 set" in p.stdout
    p = run(dict(GUROBI_TIME_LIMIT_S="100")); assert p.returncode == 2 and "REFUSED: GUROBI_TIME_LIMIT_S is set" in p.stdout
    p = run(dict(WALL_CAP_S="100")); assert p.returncode == 2 and "REFUSED: WALL_CAP_S is set" in p.stdout
    p = run(dict(LICENCE_GAP_S="1")); assert p.returncode == 2 and "REFUSED: LICENCE_GAP_S=1 differs from the registered value 330" in p.stdout
    p = run(dict(TRUNCATE="56")); assert p.returncode == 2 and "REFUSED: TRUNCATE is for smoke tests only" in p.stdout
    p = run(dict(BUILD_ONLY="1")); assert p.returncode == 2 and "REFUSED: --auth together with BUILD_ONLY / POST_ONLY / DRY" in p.stdout
    p = run({}, args=()); assert p.returncode == 2 and "--auth" in p.stdout
    p = run({}, args=("--only", "V1")); assert p.returncode == 2 and "unknown argument --only" in p.stdout
    assert not (tmp_path / "o" / "STATUS.txt").exists()


def test_preflight_guards_and_resource_floor(tmp_path):
    pkg = _package(tmp_path); cg = tmp_path / "cg"; cg.mkdir()
    (pkg / "COMMIT").write_text("0" * 40 + "\n")
    p = subprocess.run(["bash", str(pkg / "preflight_dfx.sh")], env=_clean_env({"PREFLIGHT_ONLY": "guards", "PY": sys.executable}), capture_output=True, text=True)
    assert p.returncode == 0 and "no test hook / dry-run switch set" in p.stdout and "PREFLIGHT OK" in p.stdout
    p = subprocess.run(["bash", str(pkg / "preflight_dfx.sh")], env=_clean_env({"PREFLIGHT_ONLY": "guards", "PY": sys.executable, "SOLVE_CMD": "x", "FAKE_SLEEP_V1": "1"}), capture_output=True, text=True)
    assert p.returncode == 1 and "SET IN THIS SHELL - unset before the formal run: SOLVE_CMD FAKE_SLEEP_V1" in p.stdout and "PREFLIGHT FAILED" in p.stdout
    disk = next((d for d in (str(ROOT), "/") if shutil.disk_usage(d).free / 1e9 >= 45), None)
    if disk is None:
        pytest.skip("no file system with >= 45 GB free")
    def pre(cores, mem_gib):
        (cg / "cpu.max").write_text(f"{cores * 100000} 100000\n"); (cg / "memory.max").write_text(f"{mem_gib * 2**30}\n")
        return subprocess.run(["bash", str(pkg / "preflight_dfx.sh")], env=_clean_env({"PREFLIGHT_ONLY": "resources", "PY": sys.executable, "CGROUP_ROOT": str(cg), "PREFLIGHT_DISK_PATH": disk}),
                              capture_output=True, text=True)
    p = pre(17, 70)
    assert p.returncode == 0 and "container CPU cores 17 [cgroup v2 cpu.max (1700000/100000)]" in p.stdout and "cores >= 17, memory >= 64 GiB, free data disk >= 45 GB" in p.stdout
    assert "PREFLIGHT OK" in p.stdout and "17 cores < 33: V2 runs after V1" in p.stdout
    p = pre(33, 70); assert p.returncode == 0 and ">= 33 cores: V1 and V2 run side by side" in p.stdout
    p = pre(16, 70); assert p.returncode == 1 and "RESOURCE CHECK FAILED" in p.stdout
    p = pre(25, 60); assert p.returncode == 1 and "RESOURCE CHECK FAILED" in p.stdout and "PREFLIGHT FAILED" in p.stdout
    p = subprocess.run(["bash", str(pkg / "preflight_dfx.sh")], env=_clean_env({"PREFLIGHT_ONLY": "networks", "PY": sys.executable}), capture_output=True, text=True, cwd=str(pkg))
    assert p.returncode == 1 and "no 2920x3h network in the package" in p.stdout   # synthetic files differ from the registered values: the formal check fails as it must


def _acc(d: Path, label="NOT_ACCEPTED", a=True, g21=True, sha_eq=True, g22=True, g23=True):
    d.mkdir(parents=True, exist_ok=True)
    (d / "V6_ACCEPTANCE.json").write_text(json.dumps(dict(label=label, G1=dict(a=a, b=True, c=True), G2=dict(G2_1=dict(passed=g21, sha256_equal=sha_eq), G2_2=dict(passed=g22), G2_3=dict(passed=g23)))))
    (d / "RUN.json").write_text(json.dumps(dict(rid=d.name, network_sha256="x" * 64, registered_sha256="x" * 64)))


def _sol(d: Path, subset_ok=True):
    (d / "solution").mkdir(exist_ok=True); (d / "solution" / "X.npy").write_bytes(b"0")
    (d / "SOLVE_RECEIPT.json").write_text(json.dumps(dict(solution=dict(X=dict(count=1)), input_network=dict(sha256="x" * 64), config_subset=dict(network="s", current="s" if subset_ok else "t"))))


def test_stop_class_cases(tmp_path):
    cases = {}
    d = tmp_path / "V1"; _acc(d, "ACCEPTED_LAYER2"); _sol(d); cases["accepted"] = (d, "accepted", "none")
    d = tmp_path / "V2"; _acc(d, "NOT_ACCEPTED", a=True); _sol(d); cases["ref_dependent"] = (d, "ref_dependent", "none")
    d = tmp_path / "a" / "V1"; _acc(d, "NOT_ACCEPTED", a=False); _sol(d); cases["c1a"] = (d, "c1a", "stop")
    d = tmp_path / "b" / "V2"; _acc(d, "NOT_ACCEPTED"); cases["nosol"] = (d, "nosol", "stop")
    d = tmp_path / "c" / "V1"; _acc(d, "NOT_ACCEPTED", g23=False); _sol(d); cases["g2_with_solution"] = (d, "g2", "stop")
    d = tmp_path / "d" / "V2"; _acc(d, "NOT_ACCEPTED", g21=False, sha_eq=False); (d / "SOLVE_RECEIPT.json").write_text(json.dumps(dict(input_network=dict(sha256="y" * 64)))); cases["g2_no_solution"] = (d, "g2", "stop")
    d = tmp_path / "e" / "V1"; d.mkdir(parents=True); _sol(d); cases["missing_acceptance"] = (d, "g2", "stop")
    for name, (d, cls, act) in cases.items():
        r = D.stop_class(d); assert (r["cls"], r["action"]) == (cls, act), (name, r)
        assert json.loads((d / "STOP_CLASS.json").read_text())["rule"].startswith("RUN_PLAN_DFX 3.3")


def test_summary_without_runs_and_base_check_on_synthetic_files(tmp_path):
    r = D.summary(tmp_path)
    assert r["B6"] is None and r["comparison"] is None and all(v["state"] == "not_started" for v in r["runs"].values())
    md = (tmp_path / "DFX_SUMMARY.md").read_text(); assert "不可计算" in md and "未提供第三批参照文件" in md
    pkg = _package(tmp_path / "p"); nets = pkg / "networks"
    bc = D.base_check(nets, registered=False); assert bc["all_equal"] and all(v["receipt_equal"] and not v["registered_equal"] for v in bc["networks"].values())
    bc = D.base_check(nets, registered=True); assert not bc["all_equal"] and bc["registered_checked"]
    (nets / "integrated_2920_3h_unsolved.nc").write_bytes(b"x"); bc = D.base_check(nets, registered=False); assert not bc["all_equal"] and bc["files_2920x3h_present"] == ["integrated_2920_3h_unsolved.nc"]
