"""HPR (2026-10-27; RUN_PLAN_HPC.md; instruction H3.6): the two-PBS-job method of the fourth batch on the HPR amendments of run_batch4.sh
(--only <rid>, WAIT_START_OF, MEM_MEASURE auto / rss, cgroup job-directory layouts, R_TL / R_WALL = B1), the job body hpc_package_src/hpr_job.sh,
make_pbs.sh and hpr_consistency.py - driven with the B4P SYNTHETIC stand-ins (tests/research/fixtures/b4p_fake_pipeline.py: no solver, no model).
Covered: the registered values are one single source (b4_batch4.py = run_batch4.sh = preflight.sh = RUN_PLAN_HPC.md = generated PBS scripts);
--only F1 then --only F2 then the POST_ONLY batch job reproduce the batch mode of the same run step by step (calls, parameters, receipts, exports,
labels, B6); F2's Gurobi process waits for F1's start + the licence gap (and safe-stops when F1 never starts); the memory stop by the process-group
RSS when no cgroup accounting is readable and by a cgroup v1 job directory; the projection stop, the post-solve error and the resume rules
(ended -> skipped; started-not-ended -> STOP_SAFE) in --only mode; the batch job when one run is UNUSABLE and when a run has not ended; the refusals
of a formal job (hooks, missing authorisation, dry-run / smoke leftovers, licence file); the job body in smoke56 / build_only mode with stand-ins
(local-drill switches); the job cgroup detection; the preflight CGROUP_ROOT false positive fixed (H3.5).
Never run beside a real local solve (the process counts would see it)."""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(ROOT / "scripts_project"))
import b4_batch4 as B   # noqa: E402
import test_b4p_batch4 as T   # noqa: E402  (the B4P stand-in helpers: _package, _run, _calls, _span, _clean_env)

PKG = T.PKG; FAKE = T.FAKE; HPR = ROOT / "research/06_scope_redesign/p1_hpr_20261027"; HPC = HPR / "hpc_package_src"
pytestmark = pytest.mark.skipif(shutil.which("setsid") is None or not Path("/usr/bin/time").exists(), reason="setsid / GNU time missing")
EXP_OBJ = B.SMOKE_EXPECTED_OBJECTIVE


def _only(tmp, pkg, rid, extra=None, auth="synthetic test", timeout=600):
    return T._run(tmp, pkg, extra, args=("--only", rid, "--auth", auth), timeout=timeout)


def _status(tmp):
    return (tmp / "out" / "STATUS.txt").read_text()


def _kinds(tmp, rid):
    p = tmp / "out" / "CALLS.txt"
    return [x.split()[0] for x in p.read_text().splitlines() if len(x.split()) > 1 and x.split()[1] == rid] if p.exists() else []


def test_registered_values_are_one_single_source():
    src = (PKG / "run_batch4.sh").read_text(); pre = (PKG / "preflight.sh").read_text(); plan = (HPR / "RUN_PLAN_HPC.md").read_text()
    assert B.TIME_LIMIT_S == 864000 and B.WALL_CAP_S == 871200 and B.LICENCE_GAP_S == 330 and B.WAIT_START_MAX_S == 7200
    assert f"R_TL={B.TIME_LIMIT_S}; R_WALL={B.WALL_CAP_S}; R_GAP={B.LICENCE_GAP_S}; R_MODE=split" in src and f"R_TL={B.TIME_LIMIT_S}" in pre
    assert "864,000" in plan and "871,200" in plan and "918,000" in plan and "925,200" in plan and "7,200" in plan
    assert B.REGISTERED_SHA["integrated_2920_3h_unsolved.nc"].startswith("08879f0b") and B.REGISTERED_SHA["disconnected_2920_3h_unsolved.nc"].startswith("d90ca992")
    assert all(v in plan for v in B.REGISTERED_SHA.values()) and "63,873,447" in plan and "63,202,193" in plan and B.BUILD_COMMIT in plan
    j = B.HPC_JOBS
    assert (j["F1"]["ncpus"], j["F1"]["mem_gb"], j["F2"]["ncpus"], j["F2"]["mem_gb"]) == (48, 300, 48, 250) and j["F1"]["queue"] == j["F2"]["queue"] == "parallel"
    assert j["F2"]["depends"] == "after:F1" and j["F2"]["wait_start_of"] == "F1" and j["batch"]["depends"] == "afterany:F1:F2"
    wc = B.walltime_components()
    assert wc["registered_f1_s"] >= wc["sum_f1_s"] and wc["registered_f2_s"] >= wc["sum_f2_s"] and wc["registered_f1_s"] == 918000 and wc["registered_f2_s"] == 925200
    assert wc["sum_f1_s"] == 330 + 3600 + 871200 + 32400 + 2 * 3900 + 1800 and wc["projection_limit_s"] == 691200
    for x in j.values():
        q = B.QUEUE_LIMITS[x["queue"]]; assert x["mem_gb"] <= q["mem_gb"] and x["ncpus"] <= q["ncpus_max"] and B.walltime_s(x["walltime"]) <= q["walltime_h"] * 3600
    assert j["F1"]["ncpus"] + j["F2"]["ncpus"] <= 96 and all(j[r]["mem_gb"] >= 1.25 * B.B4P_HIGH_PEAK_GIB[r] for r in ("F1", "F2"))
    out = subprocess.run([sys.executable, str(ROOT / "scripts_project/b4_batch4.py"), "hpc-plan"], capture_output=True, text=True, check=True).stdout.splitlines()
    assert out[0] == f"LIMITS|{B.TIME_LIMIT_S}|{B.WALL_CAP_S}|330|7200|3600|32400|10800|7200|100" and sum(1 for l in out if l.startswith("JOB|")) == 6
    assert any(l.startswith("NETWORK|integrated_2920_3h_unsolved.nc|08879f0b") for l in out)


def test_make_pbs_and_consistency(tmp_path):
    pkg = tmp_path / "pkg"; (pkg / "hpc").mkdir(parents=True); shutil.copy(HPC / "make_pbs.sh", pkg / "hpc" / "make_pbs.sh"); (pkg / "COMMIT").write_text("0" * 40 + "\n")
    p = subprocess.run(["bash", str(pkg / "hpc" / "make_pbs.sh")], env=dict(os.environ, REPO=str(ROOT), PY=sys.executable), capture_output=True, text=True, cwd=str(pkg))
    assert p.returncode == 0, p.stdout + p.stderr
    files = sorted(x.name for x in (pkg / "pbs").glob("*.pbs")); assert files == sorted(f"{j['name']}.pbs" for j in B.HPC_JOBS.values())
    f1 = (pkg / "pbs" / "hpr_f1.pbs").read_text(); f2 = (pkg / "pbs" / "hpr_f2.pbs").read_text(); sm = (pkg / "pbs" / "hpr_smoke56.pbs").read_text(); ins = (pkg / "pbs" / "hpr_install.pbs").read_text()
    assert "#PBS -q parallel" in f1 and "#PBS -l select=1:ncpus=48:mem=300gb" in f1 and "#PBS -l walltime=255:00:00" in f1 and "JOB_MODE=formal JOB_RID=F1" in f1 and "JOB_TIME_LIMIT_S=864000" in f1
    assert "#PBS -l select=1:ncpus=48:mem=250gb" in f2 and "#PBS -l walltime=257:00:00" in f2 and "JOB_WAIT_START_OF=F1" in f2 and "JOB_DEPENDS=after:F1" in f2
    assert "for rid in F1 F2 batch; do JOB_RID=$rid bash hpc/hpr_job.sh" in sm and "#PBS -l select=1:ncpus=17:mem=32gb" in sm
    assert "#PBS -q serial" in ins and "exec bash hpc/hpr_install_env.sh" in ins and "-V" not in f1 and "WLSACCESS" not in f1 + f2 + sm
    out = tmp_path / "CONSISTENCY.json"
    p = subprocess.run([sys.executable, str(HPC / "hpr_consistency.py"), "--repo", str(ROOT), "--plan", str(HPR / "RUN_PLAN_HPC.md"), "--runner", str(PKG / "run_batch4.sh"), "--preflight", str(PKG / "preflight.sh"),
                        "--pbs", str(pkg / "pbs"), "--job", str(HPC / "hpr_job.sh"), "--out", str(out)], capture_output=True, text=True)
    assert p.returncode == 0 and "ALL_CONSISTENT" in p.stdout, p.stdout + p.stderr
    r = json.loads(out.read_text()); assert r["all_consistent"] and len(r["rows"]) >= 30 and all(x["consistent"] for x in r["rows"])


def test_only_mode_equals_batch_mode_step_by_step(tmp_path):
    a = tmp_path / "a"; a.mkdir(); pa = T._package(a)
    pA = T._run(a, pa, dict(CORES="25", FAKE_SLEEP_F1="3", FAKE_SLEEP_F2="2", FAKE_C1_F2="101", FAKE_C1_REGRADE_F2="111"))
    assert pA.returncode == 0, (a / "out" / "STATUS.txt").read_text()[-3000:]
    b = tmp_path / "b"; b.mkdir(); pb = T._package(b)
    p1 = _only(b, pb, "F1", dict(CORES="25", FAKE_SLEEP_F1="3")); st = _status(b)
    assert p1.returncode == 0, st[-3000:]
    assert "ONLY_MODE:" in st and "p1_probe=not_used" in st and "DONE_ONLY:" in st and "P1_PROBE" not in st and not (b / "out" / "P1_DECISION.json").exists()
    assert "BATCH_REFERENCE" not in st and "M12_BENEFIT" not in st and "PACK_" not in st and (b / "out" / "BASE_CHECK_F1.json").exists()
    p2 = _only(b, pb, "F2", dict(CORES="25", FAKE_SLEEP_F2="2", FAKE_C1_F2="101", FAKE_C1_REGRADE_F2="111", WAIT_START_OF="F1")); st = _status(b)
    assert p2.returncode == 0, st[-3000:]
    assert "WAIT_START_F2:F1 ended its solve" in st and (b / "out" / "BASE_CHECK_F2.json").exists()
    p3 = T._run(b, pb, dict(CORES="25", POST_ONLY="1", FAKE_C1_REGRADE_F2="111"), args=()); st = _status(b)   # the regrade happens in the batch job: the same stand-in flag as the batch mode
    assert p3.returncode == 0, st[-3000:]
    assert "BATCH_REFERENCE:exit=0" in st and "REGRADE_F1:" in st and "REGRADE_F2:" in st and "M12_BENEFIT:exit=0" in st and "DONE:" in st
    # the same steps, in the same order, with the same parameters
    for rid in ("F1", "F2"):
        assert _kinds(a, rid) == _kinds(b, rid), (rid, _kinds(a, rid), _kinds(b, rid))
        ca = [x for x in (a / "out" / "CALLS.txt").read_text().splitlines() if x.split()[1:2] == [rid] and x.split()[0] == "gurobi"][0].split()
        cb = [x for x in (b / "out" / "CALLS.txt").read_text().splitlines() if x.split()[1:2] == [rid] and x.split()[0] == "gurobi"][0].split()
        assert ca[2:4] == cb[2:4] and ca[7] == cb[7] and ca[9] == cb[9]   # profile, TimeLimit, OMP, Gurobi status
        drop = {"output", "export", "network", "costs_table", "written_utc"}
        ra = {k: v for k, v in json.loads((a / "out" / rid / "RUN.json").read_text()).items() if k not in drop}
        rb = {k: v for k, v in json.loads((b / "out" / rid / "RUN.json").read_text()).items() if k not in drop}
        assert ra == rb, (rid, ra, rb)
        sa = json.loads((a / "out" / rid / "SOLVE_RECEIPT.json").read_text()); sb = json.loads((b / "out" / rid / "SOLVE_RECEIPT.json").read_text())
        for k in ("scenario", "solver_profile", "solver_parameters", "label", "termination_condition", "objective", "status", "solution", "post_solve_complete"):
            assert sa.get(k) == sb.get(k), (rid, k)
        assert sa["split"]["gurobi_status_name"] == sb["split"]["gurobi_status_name"] and sa["input_network"]["sha256"] == sb["input_network"]["sha256"]
        assert (a / "out" / rid / ".label").read_text() == (b / "out" / rid / ".label").read_text() and (a / "out" / rid / ".cond").read_text() == (b / "out" / rid / ".cond").read_text()
        pa_ = json.loads((a / "out" / rid / "PRECISION.json").read_text()); pb_ = json.loads((b / "out" / rid / "PRECISION.json").read_text())
        assert pa_["grade"] == pb_["grade"] and len(pa_["grade_history"]) == len(pb_["grade_history"])
        ea = sorted(p.name for p in (a / "out" / "export" / rid).rglob("*") if p.is_file() and p.name != "P1_DECISION.json")
        eb = sorted(p.name for p in (b / "out" / "export" / rid).rglob("*") if p.is_file())
        assert ea == eb, (rid, set(ea) ^ set(eb))
        la = {l.split(":")[0] for l in (a / "out" / "STATUS.txt").read_text().splitlines() if l.split(":")[0].endswith(f"_{rid}")}
        lb = {l.split(":")[0] for l in st.splitlines() if l.split(":")[0].endswith(f"_{rid}")}
        assert la - {"P1_PROBE"} <= lb and lb - la <= {f"WAIT_START_{rid}", f"GAP_PHASE_1_{rid}", f"SKIP_ENDED_{rid}", "HALTED_ONLY", "DONE_ONLY"}, (rid, la ^ lb)   # SKIP_ENDED: the POST_ONLY batch job revisits the ended runs
    sA = json.loads((a / "out" / "BATCH4_SUMMARY.json").read_text()); sB = json.loads((b / "out" / "BATCH4_SUMMARY.json").read_text())
    assert sA["B6"]["b6_bn"] == sB["B6"]["b6_bn"] == pytest.approx(100.0) and sA["unusable"] == sB["unusable"] == {} and sB["p1"] is None
    assert len(list((b / "out").glob("results_*_final_*.tar.gz"))) == 2 and json.loads((b / "out" / "F2" / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2"
    # resume of an ended run in --only mode: skipped, nothing re-solved; a started-not-ended run: STOP_SAFE
    n = len(T._calls(b)); p = _only(b, pb, "F1", dict(CORES="25"))
    assert p.returncode == 0 and len(T._calls(b)) == n and "SKIP_ENDED_F1:optimal" in _status(b)
    c = tmp_path / "c"; c.mkdir(); pc = T._package(c); (c / "out" / "F2").mkdir(parents=True); (c / "out" / "F2" / ".started").write_text("x pid=1 pgid=1\n")
    p = _only(c, pc, "F2", dict(CORES="25"))
    assert p.returncode == 3 and "STOP_SAFE:INTERRUPTED_F2" in _status(c) and T._calls(c) == [] and "HALTED_ONLY:" in _status(c)


def test_f2_gurobi_waits_for_f1_start_plus_gap(tmp_path):
    pkg = T._package(tmp_path); env1 = dict(CORES="25", LICENCE_GAP_S="4", FAKE_SLEEP_F1="12")
    f = f"{sys.executable} {FAKE}"; w = tmp_path / "standin" / "scripts_project"
    base = T._clean_env(dict(REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(tmp_path / "out"), FAKE_OUT=str(tmp_path / "out"), ALLOW_UNREGISTERED="1", GRACE_S="1", MONITOR_S="1",
                             MEM_QUOTA_GIB="240", CGROUP_ROOT=str(tmp_path / "cgroup"), GRB_LICENSE_FILE=str(tmp_path / "lic"), GUROBI_TIME_LIMIT_S="1000", WALL_CAP_S="1200",
                             SOLVE_CMD=f"{sys.executable} {w / 's2_solve.py'}", SPLIT_CMD=f"{sys.executable} {w / 'b4_split_solve.py'}", VA_CMD=f"{f} va", C1_CMD=f"{f} c1", M12_CMD=f"{f} m12", M12A_CMD=f"{f} m12a", FAKE_SLEEP="0.2"))
    j1 = subprocess.Popen(["bash", str(pkg / "run_batch4.sh"), "--only", "F1", "--auth", "synthetic"], env=dict(base, **env1), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0)
    p2 = subprocess.run(["bash", str(pkg / "run_batch4.sh"), "--only", "F2", "--auth", "synthetic"], env=dict(base, CORES="25", LICENCE_GAP_S="4", FAKE_SLEEP_F2="1", WAIT_START_OF="F1"), capture_output=True, text=True, timeout=300)
    rc1 = j1.wait(timeout=300); st = _status(tmp_path)
    assert rc1 == 0 and p2.returncode == 0, st[-3000:] + p2.stdout[-500:] + p2.stderr[-500:]
    g = T._calls(tmp_path); (a0, a1), (b0, b1) = T._span(g, "F1"), T._span(g, "F2")
    assert b0 >= a0 + 4.0 - 0.6, (a0, b0)   # F2's Gurobi process starts >= gap after F1's (the fake records its own start; the runner writes .solve_start ~1 s before)
    assert b0 < a1, "F2 started beside F1 (two WLS sessions), not after it"
    assert "WAIT_START_F2:waiting for F1/.solve_start" in st and "WAIT_START_F2:F1 Gurobi started" in st and "DONE_ONLY" in st and st.count("DONE_ONLY") == 2
    assert "SOLVER_PROCESS_RUNNING_AT_START" not in st   # busy() counts only this run's processes in --only mode (the jobs may share a node)


def test_f2_safe_stops_when_f1_never_starts(tmp_path):
    pkg = T._package(tmp_path)
    p = _only(tmp_path, pkg, "F2", dict(CORES="25", WAIT_START_OF="F1", WAIT_START_MAX_S="3", LICENCE_GAP_S="1"))
    st = _status(tmp_path)
    assert p.returncode == 3, st[-2000:]
    assert "STOP_SAFE:WAIT_START:F2" in st and T._calls(tmp_path) == [] and not (tmp_path / "out" / "F2" / ".started").exists() and (tmp_path / "out" / "STOP_SAFE").exists()
    assert [c[1] for c in T._calls(tmp_path, "build")] == ["F2"]   # process 1 (no licence) ran before the wait


def test_memory_stop_by_process_group_rss_without_cgroup_accounting(tmp_path):
    pkg = T._package(tmp_path); (tmp_path / "nocg").mkdir()
    p = _only(tmp_path, pkg, "F1", dict(CORES="25", CGROUP_ROOT=str(tmp_path / "nocg"), MEM_QUOTA_GIB="0.5", FAKE_SLEEP_F1="25", FAKE_RSS_SPIKE_F1="2:700000000", FAKE_IGNORE_TERM_F1="1"))
    st = _status(tmp_path)
    assert p.returncode == 3, st[-2000:]
    assert "mem_measure=auto/rss" in st and "cgroup_anon_source=none" in st and "MEMORY_STOP_F1:" in st and ":measure=rss:" in st and "STOP_SAFE:MEMORY:F1:rss memory above 0.80" in st
    assert (tmp_path / "out" / "F1" / ".cond").read_text().strip() == "killed_memory" and "KILL9_F1" in st and T._calls(tmp_path) == []
    t2 = tmp_path / "b"; t2.mkdir(); pkg2 = T._package(t2); (t2 / "nocg").mkdir()
    p = _only(t2, pkg2, "F1", dict(CORES="25", CGROUP_ROOT=str(t2 / "nocg"), MEM_QUOTA_GIB="240", FAKE_SLEEP_F1="3", FAKE_RSS_SPIKE_F1="1:300000000"))
    assert p.returncode == 0 and "mem_measure=auto/rss" in _status(t2) and "MEMORY_STOP" not in _status(t2)   # the RSS measure within the quota: no stop


def test_memory_stop_by_cgroup_v1_job_directory(tmp_path):
    pkg = T._package(tmp_path); cg = tmp_path / "jobcg"; cg.mkdir()
    (cg / "memory.stat").write_text("cache 99999999999\nrss 1\ntotal_rss 1073741824\n"); (cg / "memory.limit_in_bytes").write_text(str(100 * 2**30) + "\n"); (cg / "memory.usage_in_bytes").write_text("5\n")
    m = B.memstat(cg); assert m["anon_bytes"] == 1073741824 and m["limit_gib"] == 100.0 and m["source"].endswith("memory.stat:total_rss") and not m["stop"]
    p = _only(tmp_path, pkg, "F1", dict(CORES="25", CGROUP_ROOT=str(cg), MEM_QUOTA_GIB="100", FAKE_SLEEP_F1="20", FAKE_MEM_SPIKE_F1=f"3:{int(90 * 2**30)}", FAKE_IGNORE_TERM_F1="1"))
    st = _status(tmp_path)
    assert p.returncode == 3, st[-2000:]
    assert "mem_measure=auto/cgroup" in st and f"cgroup_anon_source={cg}/memory.stat:total_rss" in st and ":measure=cgroup:" in st and "STOP_SAFE:MEMORY:F1:cgroup memory above" in st
    v2 = tmp_path / "v2"; v2.mkdir(); (v2 / "memory.stat").write_text("anon 2147483648\nfile 1\n"); (v2 / "memory.max").write_text(str(10 * 2**30) + "\n"); (v2 / "memory.current").write_text("3\n")
    m = B.memstat(v2); assert m["anon_gib"] == 2.0 and m["limit_gib"] == 10.0 and m["source"].endswith(":anon")


def test_projection_stop_and_post_solve_error_in_only_mode(tmp_path):
    pkg = T._package(tmp_path)
    p = _only(tmp_path, pkg, "F1", dict(CORES="25", FAKE_SLEEP_F1="15", FAKE_ITER_S_F1="10"))   # 10 s x 450 + elapsed > 800 = 0.8 x 1000
    st = _status(tmp_path)
    assert p.returncode == 3 and "PROJECTION_STOP_F1:" in st and "STOP_SAFE:PROJECTION:F1" in st and (tmp_path / "out" / "F1" / ".cond").read_text().strip() == "killed_projection", st[-2000:]
    t2 = tmp_path / "b"; t2.mkdir(); pkg2 = T._package(t2)
    p = _only(t2, pkg2, "F1", dict(CORES="25", FAKE_POST_ERROR_F1="1")); st = _status(t2)
    assert p.returncode == 0, st[-2000:]
    rec = json.loads((t2 / "out" / "F1" / "SOLVE_RECEIPT.json").read_text())
    assert rec["termination_condition"] == "optimal" and rec["solution"]["X"]["count"] == 10 and [e["step"] for e in rec["post_solve_errors"]] == ["co2_flows"]
    assert "ASSIGN_F1:exit=4" in st and json.loads((t2 / "out" / "F1" / "V6_ACCEPTANCE.json").read_text())["label"].startswith("ACCEPTED") and "DONE_ONLY" in st and "UNUSABLE" not in st


def _job_pkg(tmp: Path) -> Path:
    """A package-like folder for hpc_package_src/hpr_job.sh: runner, preflight, pack, hpc/, synthetic networks, repo -> the repository, licence placeholder (mode 600)."""
    pkg = T._package(tmp); (pkg / "hpc").mkdir()
    for f in ("hpr_job.sh", "make_pbs.sh"):
        shutil.copy(HPC / f, pkg / "hpc" / f)
    shutil.copy(PKG / "preflight.sh", pkg / "preflight.sh"); (pkg / "COMMIT").write_text("0" * 40 + "\n"); os.symlink(ROOT, pkg / "repo")
    os.chmod(tmp / "lic", 0o600)
    return pkg


def _job_env(tmp: Path, pkg: Path, mode: str, rid: str, extra=None, standin=True):
    f = f"{sys.executable} {FAKE}"; w = tmp / "standin" / "scripts_project"
    env = T._clean_env(dict(PBS_O_WORKDIR=str(pkg), PBS_JOBID="local.test", JOB_KEY=mode, JOB_MODE=mode, JOB_RID=rid, JOB_NCPUS="17", JOB_MEM_GB="32", JOB_WALLTIME="04:00:00", JOB_TIME_LIMIT_S=str(B.TIME_LIMIT_S),
                           HPR_AUTH="synthetic authorisation", PY=sys.executable, GRB_LICENSE_FILE=str(tmp / "lic"), HPR_LOCAL_DRILL="1"))
    if standin:
        env.update(HPR_TEST_STANDIN="1", FAKE_OUT=str(tmp / "runs_fake"), LICENCE_GAP_S="1", GRACE_S="1", MONITOR_S="1", FAKE_SLEEP="0.2",
                   SOLVE_CMD=f"{sys.executable} {w / 's2_solve.py'}", SPLIT_CMD=f"{sys.executable} {w / 'b4_split_solve.py'}", VA_CMD=f"{f} va", C1_CMD=f"{f} c1", M12_CMD=f"{f} m12", M12A_CMD=f"{f} m12a",
                   FAKE_OBJ_F1=repr(EXP_OBJ["F1"]), FAKE_OBJ_F2=repr(EXP_OBJ["F2"]))
    env.update(extra or {})
    return env


def test_job_body_smoke56_runs_f1_f2_batch_with_standins(tmp_path):
    pkg = _job_pkg(tmp_path)
    for rid, extra in (("F1", {}), ("F2", {"JOB_WAIT_START_OF": "F1"}), ("batch", {})):
        p = subprocess.run(["bash", str(pkg / "hpc" / "hpr_job.sh")], env=_job_env(tmp_path, pkg, "smoke56", rid, extra), capture_output=True, text=True, timeout=600)
        assert p.returncode == 0, (rid, p.stdout[-1500:], p.stderr[-1500:], (pkg / "runs" / "smoke56" / "STATUS.txt").read_text()[-2500:] if (pkg / "runs" / "smoke56" / "STATUS.txt").exists() else "")
    out = pkg / "runs" / "smoke56"; st = (out / "STATUS.txt").read_text(); rec = (out / "PBS_JOBS.txt").read_text()
    assert st.count("DONE_ONLY") == 2 and "DONE:" in st and "truncate=56" in st and "time_limit_s=3000:wall_cap_s=3600" in st and "SMOKE_TEST_ONLY" in (out / "F1" / "RUN.json").read_text()
    assert "WLS_TOKEN_HTTP:skipped_local_drill" in rec and "mem_measure=rss" in rec and "JOB_START:smoke56:smoke56:F1" in rec and rec.count("JOB_END:") == 3 and "PREFLIGHT:smoke56:exit=0" in rec
    s = (out / "SMOKE_STATUS.txt").read_text()
    assert "SMOKE_RESULT:PASS" in s and "F1:termination=optimal" in s and "F2:termination=optimal" in s and "POSTPROC_ERRORS:0" in s and "relative_difference=0.000e+00" in s, s
    assert len(list(out.glob("results_*_final_*.tar.gz"))) == 2
    # the smoke verdict fails when a run is not optimal (second package)
    t2 = tmp_path / "b"; t2.mkdir(); pkg2 = _job_pkg(t2)
    for rid, extra in (("F1", {}), ("F2", {"JOB_WAIT_START_OF": "F1", "FAKE_GUROBI_STATUS_F2": "MEM_LIMIT"})):
        subprocess.run(["bash", str(pkg2 / "hpc" / "hpr_job.sh")], env=_job_env(t2, pkg2, "smoke56", rid, extra), capture_output=True, text=True, timeout=600)
    p = subprocess.run(["bash", str(pkg2 / "hpc" / "hpr_job.sh")], env=_job_env(t2, pkg2, "smoke56", "batch"), capture_output=True, text=True, timeout=600)
    s2 = (pkg2 / "runs" / "smoke56" / "SMOKE_STATUS.txt").read_text()
    assert p.returncode == 3 and "SMOKE_RESULT:FAIL" in s2 and "F2:termination=internal_solver_error" in s2 and "HALTED:True" in s2, s2


def test_job_body_build_only_records_metrics_and_deletes_the_lp(tmp_path):
    pkg = _job_pkg(tmp_path)
    p = subprocess.run(["bash", str(pkg / "hpc" / "hpr_job.sh")], env=_job_env(tmp_path, pkg, "build_only", "F1", {"JOB_NCPUS": "48", "JOB_MEM_GB": "300", "HPR_DRY_TRUNCATE": "56"}), capture_output=True, text=True, timeout=600)
    out = pkg / "runs" / "build_only_f1"; st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, p.stdout[-1500:] + p.stderr[-1500:] + st[-2000:]
    s = (out / "BUILD_ONLY_STATUS.txt").read_text()
    assert "LP_DELETED:" in s and "BUILD_CHECK_F1:" in s and "SCRATCH_WRITE_MBPS:" in s and "PEAK_RSS_GIB:" in s and "LP_FILE_BYTES:" in s and "DONE:" in s, s
    assert T._calls(tmp_path) == [] or not (tmp_path / "runs_fake" / "CALLS.txt").exists() or "gurobi" not in (tmp_path / "runs_fake" / "CALLS.txt").read_text()
    assert not (out / "F1" / "split" / "problem.lp").exists() and (out / "F1" / ".cond").read_text().strip() == "build_only" and json.loads((out / "F1" / "RUN.json").read_text())["truncate"] == 56
    assert "build_only=1" in st and "DONE_ONLY" in st and "only(F1)" in st


def test_job_body_formal_refusals_and_batch_not_ready(tmp_path):
    pkg = _job_pkg(tmp_path)
    def run(mode, rid, extra=None, standin=False):
        env = _job_env(tmp_path, pkg, mode, rid, None, standin=standin); env.pop("HPR_LOCAL_DRILL", None); env.pop("HPR_TEST_STANDIN", None); env.update(extra or {})   # a real-job environment, then the case's extras
        return subprocess.run(["bash", str(pkg / "hpc" / "hpr_job.sh")], env=env, capture_output=True, text=True, timeout=120)
    p = run("formal", "F1", {"BUILD_ONLY": "1"}); assert p.returncode == 2 and "REFUSED: test hook" in p.stdout and "BUILD_ONLY" in p.stdout
    p = run("formal", "F1", {"SPLIT_CMD": "x"}); assert p.returncode == 2 and "SPLIT_CMD" in p.stdout
    p = run("formal", "F1", {"FAKE_SLEEP_F1": "9"}); assert p.returncode == 2 and "FAKE_SLEEP_F1" in p.stdout
    p = run("formal", "F1", {"HPR_AUTH": ""}); assert p.returncode == 2 and "authorisation text is missing" in p.stdout
    p = run("formal", "X1"); assert p.returncode == 2 and "JOB_RID=X1" in p.stdout
    p = run("bogus", "F1"); assert p.returncode == 2 and "JOB_MODE=bogus" in p.stdout
    p = run("formal", "F1", {"GRB_LICENSE_FILE": str(tmp_path / "nolic")}); assert p.returncode == 2 and "licence file missing or not mode 600" in p.stdout
    os.chmod(tmp_path / "lic", 0o644); p = run("formal", "F1"); assert p.returncode == 2 and "not mode 600" in p.stdout; os.chmod(tmp_path / "lic", 0o600)
    d = pkg / "runs" / "batch4" / "F1"; d.mkdir(parents=True); (d / ".cond").write_text("build_only\n")
    p = run("formal", "F1"); assert p.returncode == 2 and "dry-run leftover" in p.stdout
    (d / ".cond").unlink(); (d / "RUN.json").write_text(json.dumps(dict(label="SMOKE_TEST_ONLY", truncate=56)))
    p = run("formal", "F1"); assert p.returncode == 2 and "smoke leftover" in p.stdout
    (d / "RUN.json").unlink(); d.rmdir()
    p = run("formal", "F1", {"HPR_LOCAL_DRILL": "1", "PBS_JOBID": "1234567.venus01"}); assert p.returncode == 2 and "local-drill / test switch" in p.stdout
    p = run("formal", "F1", {"HPR_TEST_STANDIN": "1", "PBS_JOBID": "1234567.venus01"}); assert p.returncode == 2 and "HPR_TEST_STANDIN" in p.stdout
    p = run("batch", "batch"); assert p.returncode == 2 and "not_ready" in p.stdout
    (pkg / "runs" / "batch4" / "F1").mkdir(parents=True); (pkg / "runs" / "batch4" / "F1" / ".ended").write_text("x\n")
    p = run("batch", "batch"); assert p.returncode == 2 and "not_ready" in p.stdout and "F2 has not ended" in p.stdout
    assert not (pkg / "runs" / "batch4" / "STATUS.txt").exists() and not (pkg / "runs" / "batch4" / "PBS_JOBS.txt").exists()
    # the runner's own refusals in --only mode
    base = dict(REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(tmp_path / "o"), GRB_LICENSE_FILE=str(tmp_path / "lic"))
    def r(extra, args=("--only", "F1", "--auth", "x")):
        return subprocess.run(["bash", str(pkg / "run_batch4.sh"), *args], env=T._clean_env(dict(base, **extra)), capture_output=True, text=True, timeout=60)
    p = r(dict(TRUNCATE="56")); assert p.returncode == 2 and "TRUNCATE is for smoke tests only" in p.stdout
    p = r(dict(GUROBI_TIME_LIMIT_S="259200")); assert p.returncode == 2 and "differs from the registered value 864000" in p.stdout
    p = r(dict(WALL_CAP_S="266400")); assert p.returncode == 2 and "differs from the registered value 871200" in p.stdout
    p = r(dict(POST_ONLY="1"), args=("--only", "F1")); assert p.returncode == 2 and "not together with POST_ONLY" in p.stdout
    p = r(dict(MEM_MEASURE="bogus")); assert p.returncode == 2 and "MEM_MEASURE must be" in p.stdout
    p = r({}, args=("--only", "X9", "--auth", "x")); assert p.returncode == 2 and "not a run of the registered table" in p.stdout
    p = r(dict(WAIT_START_OF="F1")); assert p.returncode == 2 and "WAIT_START_OF must name the OTHER run" in p.stdout
    assert not (tmp_path / "o" / "STATUS.txt").exists()


def test_batch_job_after_an_unusable_run(tmp_path):
    pkg = T._package(tmp_path)
    p1 = _only(tmp_path, pkg, "F1", dict(CORES="25")); assert p1.returncode == 0
    p2 = _only(tmp_path, pkg, "F2", dict(CORES="25", WAIT_START_OF="F1", FAKE_GUROBI_STATUS_F2="MEM_LIMIT")); st = _status(tmp_path)
    assert p2.returncode == 3 and "UNUSABLE:F2:nosol" in st and (tmp_path / "out" / "STOP").read_text().split() == ["F2"] and "HALTED_ONLY:" in st, st[-2000:]
    p3 = T._run(tmp_path, pkg, dict(CORES="25", POST_ONLY="1"), args=()); st = _status(tmp_path)
    assert p3.returncode == 3 and "HALTED:" in st and len(list((tmp_path / "out").glob("results_light_halted_*.tar.gz"))) == 1 and not list((tmp_path / "out").glob("results_*_final_*")), st[-2000:]
    s = json.loads((tmp_path / "out" / "BATCH4_SUMMARY.json").read_text())
    assert s["B6"] is None and s["unusable"] and s["runs"]["F1"]["state"] == "ended" and s["runs"]["F2"]["state"] == "ended" and s["stop_not_accepted"] == ["F2"]
    assert "BATCH_REFERENCE:not_available" in st   # no F2 ledger: F1 keeps the provisional default reference, the summary and the halted pack are written


def test_batch_job_runs_when_the_other_run_never_started_after_a_stop(tmp_path):
    """Review F-06: F1 halts the batch (UNUSABLE + STOP) before F2 reached its Gurobi process -> F2's job records NOT_STARTED and writes no .ended; the
    batch job must still summarise and pack as halted (not 'not_ready')."""
    pkg = _job_pkg(tmp_path); out = pkg / "runs" / "batch4"
    f = f"{sys.executable} {FAKE}"; w = tmp_path / "standin" / "scripts_project"
    base = T._clean_env(dict(REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(out), FAKE_OUT=str(out), ALLOW_UNREGISTERED="1", LICENCE_GAP_S="1", GRACE_S="1", MONITOR_S="1", CORES="25",
                             MEM_QUOTA_GIB="240", CGROUP_ROOT=str(tmp_path / "cgroup"), GRB_LICENSE_FILE=str(tmp_path / "lic"), GUROBI_TIME_LIMIT_S="1000", WALL_CAP_S="1200",
                             SOLVE_CMD=f"{sys.executable} {w / 's2_solve.py'}", SPLIT_CMD=f"{sys.executable} {w / 'b4_split_solve.py'}", VA_CMD=f"{f} va", C1_CMD=f"{f} c1", M12_CMD=f"{f} m12", M12A_CMD=f"{f} m12a", FAKE_SLEEP="0.2"))
    p1 = subprocess.run(["bash", str(pkg / "run_batch4.sh"), "--only", "F1", "--auth", "x"], env=dict(base, FAKE_GUROBI_STATUS_F1="MEM_LIMIT"), capture_output=True, text=True, timeout=300)
    st = (out / "STATUS.txt").read_text(); assert p1.returncode == 3 and "UNUSABLE:F1:nosol" in st and (out / "STOP").exists(), st[-1500:]
    p2 = subprocess.run(["bash", str(pkg / "run_batch4.sh"), "--only", "F2", "--auth", "x"], env=dict(base, WAIT_START_OF="F1"), capture_output=True, text=True, timeout=300)
    st = (out / "STATUS.txt").read_text(); assert p2.returncode == 3 and "NOT_STARTED_F2:halted before the start" in st and not (out / "F2" / ".started").exists() and not (out / "F2" / ".ended").exists(), st[-1500:]
    env = _job_env(tmp_path, pkg, "batch", "batch", {"FAKE_OUT": str(out)}); env["HPR_RUN_ROOT"] = str(pkg)
    for k in ("LICENCE_GAP_S", "GRACE_S", "MONITOR_S"):
        env.pop(k, None)   # the batch body runs POST_ONLY without ALLOW_UNREGISTERED: only registered values are accepted (the stand-in gap settings are not needed here)
    p3 = subprocess.run(["bash", str(pkg / "hpc" / "hpr_job.sh")], env=env, capture_output=True, text=True, timeout=300)
    st = (out / "STATUS.txt").read_text()
    assert p3.returncode == 3 and "not_ready" not in p3.stdout and "F2 never started (batch halted)" in p3.stdout, (p3.stdout[-800:], st[-1500:])
    assert "HALTED:" in st and len(list(out.glob("results_light_halted_*.tar.gz"))) == 1 and (out / "BATCH4_SUMMARY.json").exists()
    s = json.loads((out / "BATCH4_SUMMARY.json").read_text()); assert s["runs"]["F1"]["state"] == "ended" and s["runs"]["F2"]["state"] == "not_started" and s["stop_not_accepted"] == ["F1"]
    # a started-not-ended run is never 'settled': not_ready
    (out / "F2").mkdir(exist_ok=True); (out / "F2" / ".started").write_text("x\n")
    p4 = subprocess.run(["bash", str(pkg / "hpc" / "hpr_job.sh")], env=env, capture_output=True, text=True, timeout=120); assert p4.returncode == 2 and "not_ready" in p4.stdout


def test_only_mode_ignores_the_other_job_run_for_post_memory_and_threads(tmp_path):
    """Review F-07: in --only mode the other run (another PBS job, its own cgroup) must not queue this job's post-processing nor shrink its thread
    budget; with MEM_MEASURE=rss the cgroup files under CGROUP_ROOT (root / shared service cgroup) are not read at all."""
    pkg = T._package(tmp_path); out = tmp_path / "out"; (out / "F2").mkdir(parents=True); (out / "F2" / ".started").write_text("x pid=1 pgid=1\n")   # F2 "running" in the other job
    nodewide = tmp_path / "nodewide"; nodewide.mkdir(); (nodewide / "memory.stat").write_text(f"anon {230 * 2**30}\nfile 0\n"); (nodewide / "memory.max").write_text("max\n")   # a node-wide v2-looking root: 230 GiB in use
    p = _only(tmp_path, pkg, "F1", dict(CORES="25", MEM_QUOTA_GIB="240", CGROUP_ROOT=str(nodewide), MEM_MEASURE="rss", FAKE_SLEEP_F1="2"))
    st = _status(tmp_path)
    assert p.returncode == 0, st[-2000:]
    assert "POST_QUEUED" not in st and "mem_measure=rss/rss" in st and "cgroup_anon_source=none(rss_mode)" in st and "DONE_ONLY" in st
    va = [x for x in (out / "CALLS.txt").read_text().splitlines() if x.startswith("va F1")]; assert va and va[0].endswith("omp=25"), va   # thread budget = all cores of this job (the other run does not count)
    mon = (out / "MONITOR_F1.csv").read_text().splitlines(); assert len(mon) >= 2 and all(l.split(",")[4] == "" and l.split(",")[5] == "" for l in mon[1:]), mon[:3]   # cgroup columns empty in rss mode


def test_job_cgroup_detection(tmp_path):
    pkg = _job_pkg(tmp_path); fs = tmp_path / "fs"   # PBS_JOBID=local.test in _job_env: only a cgroup path carrying the job id is the job's own
    v2 = fs / "pbs_jobs.service" / "jobid" / "local.test"; v2.mkdir(parents=True); (v2 / "memory.stat").write_text("anon 1024\nfile 0\n"); (v2 / "memory.max").write_text(str(32 * 2**30) + "\n")
    (tmp_path / "proc_v2").write_text("0::/pbs_jobs.service/jobid/local.test\n")
    v1 = fs / "memory" / "pbspro" / "local.test"; v1.mkdir(parents=True); (v1 / "memory.stat").write_text("rss 1\ntotal_rss 2048\n"); (v1 / "memory.limit_in_bytes").write_text(str(32 * 2**30) + "\n")
    (tmp_path / "proc_v1").write_text("12:memory:/pbspro/local.test\n3:cpu,cpuacct:/pbspro/local.test\n")
    (tmp_path / "proc_root").write_text("0::/\n")
    (fs / "memory").mkdir(exist_ok=True); (fs / "memory" / "memory.stat").write_text("rss 999\ntotal_rss 999\n")   # a v1 ROOT memory.stat exists: must never be used
    (tmp_path / "proc_v1root").write_text("12:memory:/\n")
    svc = fs / "system.slice" / "pbs_mom.service"; svc.mkdir(parents=True); (svc / "memory.stat").write_text("anon 5\nfile 0\n"); (svc / "memory.max").write_text("max\n")   # the MoM's shared cgroup (hook off): never the job's
    (tmp_path / "proc_svc").write_text("0::/system.slice/pbs_mom.service\n")
    other = fs / "pbs_jobs.service" / "jobid" / "999.venus"; other.mkdir(parents=True); (other / "memory.stat").write_text("anon 7\n")   # another job's id: never ours
    (tmp_path / "proc_other").write_text("0::/pbs_jobs.service/jobid/999.venus\n")
    for tag, proc, want in (("v2", "proc_v2", f"version=v2:dir={v2}:limit={32 * 2**30}:anon_key=anon:mem_measure=cgroup"), ("v1", "proc_v1", f"version=v1:dir={v1}:limit={32 * 2**30}:anon_key=total_rss:mem_measure=cgroup"),
                            ("root", "proc_root", "version=none:dir=none:limit=none:anon_key=none:mem_measure=rss"), ("v1root", "proc_v1root", "version=none:dir=none:limit=none:anon_key=none:mem_measure=rss"),
                            ("svc", "proc_svc", "version=none:dir=none:limit=none:anon_key=none:mem_measure=rss"), ("other", "proc_other", "version=none:dir=none:limit=none:anon_key=none:mem_measure=rss")):
        t = tmp_path / tag; t.mkdir(); p = subprocess.run(["bash", str(pkg / "hpc" / "hpr_job.sh")], env=_job_env(tmp_path, pkg, "build_only", "F1", {"HPR_PROC_CGROUP_FILE": str(tmp_path / proc), "HPR_CGROUP_FS": str(fs), "HPR_RUN_ROOT": str(t), "HPR_TEST_PREFLIGHT_SECTIONS": "tools", "FAKE_OUT": str(t / "fake"), "HPR_DRY_TRUNCATE": "56"}),
                                                           capture_output=True, text=True, timeout=300)   # HPR_DRY_TRUNCATE: the dry-run path (ALLOW_UNREGISTERED) so that the stand-in gap / monitor settings are accepted
        rec = (t / "runs" / "build_only_f1" / "PBS_JOBS.txt").read_text()
        assert p.returncode == 0 and want in rec, (tag, want, rec, p.stdout[-800:], p.stderr[-800:])


def test_preflight_cgroup_root_note_fixed_and_job_dir_resources(tmp_path):
    for script in (PKG / "preflight.sh", ROOT / "research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/preflight_dfx.sh"):
        env = {k: v for k, v in os.environ.items() if k not in T.HOOK_KEYS and not k.startswith("FAKE_")}; env.update(PREFLIGHT_ONLY="guards", PY=sys.executable); env.pop("CGROUP_ROOT", None)
        p = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True); assert p.returncode == 0 and "NOTE: CGROUP_ROOT" not in p.stdout and "PREFLIGHT OK" in p.stdout, (script.name, p.stdout)
        p = subprocess.run(["bash", str(script)], env=dict(env, CGROUP_ROOT="/tmp/x"), capture_output=True, text=True); assert p.returncode == 0 and "NOTE: CGROUP_ROOT=/tmp/x" in p.stdout
    pkg = T._package(tmp_path); shutil.copy(PKG / "preflight.sh", pkg / "preflight.sh"); (pkg / "COMMIT").write_text("0" * 40 + "\n")
    disk = next((d for d in (str(ROOT), "/") if shutil.disk_usage(d).free / 1e9 >= 45), None)
    if disk is None:
        pytest.skip("no file system with >= 45 GB free")
    cg = tmp_path / "jobcg"; cg.mkdir(); (cg / "memory.stat").write_text("rss 1\ntotal_rss 3221225472\n"); (cg / "memory.limit_in_bytes").write_text(str(300 * 2**30) + "\n")
    env = T._clean_env({"PREFLIGHT_ONLY": "resources", "PY": sys.executable, "CGROUP_ROOT": str(cg), "PREFLIGHT_DISK_PATH": disk, "NEED_CORES": "1", "NEED_MEM_GIB": "270"})
    p = subprocess.run(["bash", str(pkg / "preflight.sh")], env=env, capture_output=True, text=True, cwd=str(pkg))
    assert p.returncode == 0 and "container memory 300 GiB [cgroup v1 job directory memory.limit_in_bytes]; anon in use now 3.0 GiB" in p.stdout and "PREFLIGHT OK" in p.stdout, p.stdout
    env["NEED_MEM_GIB"] = "301"; p = subprocess.run(["bash", str(pkg / "preflight.sh")], env=env, capture_output=True, text=True, cwd=str(pkg)); assert p.returncode == 1 and "RESOURCE CHECK FAILED" in p.stdout


def test_reference_comparison_and_summary_markdown(tmp_path):
    out = tmp_path / "out"
    for rid, obj, sh in (("F1", 2.0e11, {"BN": 1e9, "VN": 2e9, "BUNKER": 3e9}), ("F2", 3.0e11, {"BN": 1.5e9, "VN": 2.5e9, "BUNKER": 3.2e9})):
        d = out / rid; (d / "m12_owen").mkdir(parents=True); (d / "solution").mkdir()
        (d / "SOLVE_RECEIPT.json").write_text(json.dumps(dict(termination_condition="optimal", objective=obj, finished_epoch=1, solution=dict(X=dict(count=1)), split=dict(bar_iter_count=5, gurobi_status_name="OPTIMAL"))))
        (d / "RUN.json").write_text(json.dumps(dict(rid=rid, network="n", network_sha256="x" * 64))); (d / ".ended").write_text("x\n"); (d / "solution" / "X.npy").write_bytes(b"0")
        (d / "m12_owen" / "OWEN.json").write_text(json.dumps(dict(alpha_main=0.5, allocation_eur={"0.5": sh}, usable_for_allocation=True)))
    ref = tmp_path / "REFERENCE_VALUES.json"
    ref.write_text(json.dumps(dict(source="test", references=dict(main=dict(label="R3 / R4", integrated=dict(rid="R3", objective_eur=1.9e11, owen_alpha_main_eur={"BN": 0.9e9, "VN": 1.9e9, "BUNKER": 2.9e9}),
                                                                                 disconnected=dict(rid="R4", objective_eur=2.8e11, owen_alpha_main_eur={"BN": 1.3e9, "VN": 2.3e9, "BUNKER": 3.0e9}), b6_bn=90.0)))))
    s = B.summary(out, None, ref); rc = s["reference_comparison"]["pairs"]["main"]
    assert rc["objective_difference_bn"] == {"F1_minus_R3": pytest.approx(10.0), "F2_minus_R4": pytest.approx(20.0)} and rc["delta_b6_bn"] == pytest.approx(10.0)
    assert rc["owen_benefit_difference_bn"]["BN"] == pytest.approx(0.1) and rc["owen_benefit_difference_bn"]["BUNKER"] == pytest.approx(0.1) and rc["owen_share_difference_bn"]["F1_minus_R3"]["VN"] == pytest.approx(0.1)
    md = (out / "BATCH4_SUMMARY.md").read_text(); assert "与登记参照值的对比" in md and "R3 / R4" in md and "+10.0000" in md
    p = subprocess.run([sys.executable, str(HPC / "make_reference_values.py"), str(ROOT / "research/06_scope_redesign/p1_dfx_20261026/BATCH3_REFERENCE_VALUES.json"),
                        str(ROOT / "research/06_scope_redesign/p1_dfx_20261026/evidence/phase4/DFX_PHASE4_RESULTS.json"), str(tmp_path / "RV.json")], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    rv = json.loads((tmp_path / "RV.json").read_text())
    assert set(rv["references"]) == {"batch3_main", "batch3_alternative", "dfx_v2_365x24h"} and rv["references"]["batch3_main"]["integrated"]["rid"] == "R3" and rv["references"]["dfx_v2_365x24h"]["b6_bn"] == pytest.approx(14.6153, abs=1e-4)
    assert rv["references"]["dfx_v2_365x24h"]["integrated"]["objective_eur"] == pytest.approx(270785244510.473) and "autodl" not in json.dumps(rv).lower() and "/root/" not in json.dumps(rv)
