"""V3 HPC package (instruction V14 sections 5-6; RUN_PLAN_HPC_V3.md): the four-run formal batch on the HPC runner run_batch4.sh / b4_batch4.py / the HPR job scripts,
driven with the B4P SYNTHETIC stand-ins (tests/research/fixtures/b4p_fake_pipeline.py: no solver, no model). Covered: the definition BATCH_DEF_2920x3h_v3hpc.json is the
registered plan (RUN_PLAN_V3.md 24.1, RUN_PLAN_HPC_V3.md); b4_batch4.py outputs with and without a definition (the v2 formats unchanged); F1 -> F2 -> F3 -> F4 as one job
each in a shared RUN_DIR, then the batch job: B6 / benefit per pair and the pair comparison; the start lock (two concurrent starts >= the gap apart; two other Gurobi
processes running -> STOP_SAFE; a lock left behind -> STOP_SAFE); a formal run refused while the limits are PROPOSED; the one-machine batch mode refused for four
runs; BUILD_ONLY over the four runs; the PBS scripts, the consistency check against RUN_PLAN_HPC_V3.md and the submission chain with a stand-in qsub; the job body
refusals. Never run beside a real local solve (the process counts would see it)."""
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(ROOT / "scripts_project"))
import b4_batch4 as B   # noqa: E402  (imported without a definition: the v2 tables)
import test_b4p_batch4 as T   # noqa: E402
import test_hpr_two_jobs as H   # noqa: E402

D3 = ROOT / "research/06_scope_redesign/p1_v3_20261102"; DEF = D3 / "batch_def/BATCH_DEF_2920x3h_v3hpc.json"; HPC = H.HPC
pytestmark = pytest.mark.skipif(shutil.which("setsid") is None or not Path("/usr/bin/time").exists(), reason="setsid / GNU time missing")
sha = T.sha
OBJ = dict(FAKE_OBJ_F1="2.0e11", FAKE_OBJ_F2="2.1e11", FAKE_OBJ_F3="1.9e11", FAKE_OBJ_F4="2.05e11")


def _pkg4(tmp: Path, status: str | None = None) -> Path:
    """the B4P synthetic package turned into the v3 HPC one: F1 / F3 built networks with their own receipts, F2 / F4 variants of F1 / F3, the definition with synthetic SHA256"""
    pkg = T._package(tmp); nets = pkg / "networks"
    for f in nets.glob("disconnected_*"):
        f.unlink()
    f3 = nets / "integrated_ev05_2920_3h_unsolved.nc"; f3.write_bytes(b"integrated ev05 2920_3h")
    r = json.loads((nets / "integrated_BUILD_RECEIPT.json").read_text()); r["network"] = dict(sha256=sha(f3), snapshots=2920); (nets / "integrated_ev05_BUILD_RECEIPT.json").write_text(json.dumps(r))
    for base, out in (("integrated_2920_3h", "no_new_xb_2920_3h"), ("integrated_ev05_2920_3h", "no_new_xb_ev05_2920_3h")):
        b = nets / f"{base}_unsolved.nc"; o = nets / f"{out}_unsolved.nc"; o.write_bytes(b.read_bytes() + b" no_new_xb")
        (nets / f"{out}_VARIANT_RECEIPT.json").write_text(json.dumps(dict(status="M08A_VARIANT_BUILT", base=dict(sha256=sha(b), scenario="integrated"), output=dict(sha256=sha(o), bytes=o.stat().st_size),
                                                                       sets={"cross_border.stock_mode": "no_new_xb"})))
    d = json.loads(DEF.read_text(encoding="utf-8")); d["build_commit"] = B.BUILD_COMMIT
    d["registered_sha"] = {f"{x['base']}_unsolved.nc": sha(nets / f"{x['base']}_unsolved.nc") for x in d["runs"].values()}
    d["registered_bytes"] = {f"{x['base']}_unsolved.nc": (nets / f"{x['base']}_unsolved.nc").stat().st_size for x in d["runs"].values()}
    if status:
        d["limits_status"] = status
    (pkg / "BATCH_DEF.json").write_text(json.dumps(d, ensure_ascii=False))
    return pkg


def _bdef(pkg=None):
    return dict(os.environ, BATCH_DEF=str((pkg / "BATCH_DEF.json") if pkg else DEF))


def test_definition_is_the_registered_plan():
    d = json.loads(DEF.read_text(encoding="utf-8")); plan = (D3 / "RUN_PLAN_V3.md").read_text(encoding="utf-8"); hp = (D3 / "RUN_PLAN_HPC_V3.md").read_text(encoding="utf-8")
    r = d["runs"]
    assert list(r) == ["F1", "F2", "F3", "F4"] and all(x["profile"] == "formal_barrier_1e6_t16" and x["set"] == "" and x["costs"] == "integrated" for x in r.values())
    assert [x["scenario"] for x in r.values()] == ["integrated", "no_new_xb"] * 2 and [x["pair"] for x in r.values()] == ["A", "A", "B", "B"]
    assert [x["base"] for x in r.values()] == ["integrated_2920_3h", "no_new_xb_2920_3h", "integrated_ev05_2920_3h", "no_new_xb_ev05_2920_3h"] and r["F4"]["parent"] == "integrated_ev05" and "parent" not in r["F2"]
    assert [x["iterations_reference"] for x in r.values()] == [350, 250, 350, 250]
    assert set(d["registered_sha"]) == set(d["registered_bytes"]) == {x["base"] + "_unsolved.nc" for x in r.values()}
    assert all(v in plan for v in d["registered_sha"].values()) and all(f"{v:,}" in plan for v in d["registered_bytes"].values()) and d["build_commit"] in plan
    # decided by the reviewer on the user's authorisation (V3_HPC_UNATTENDED.md section 1; RUN_PLAN_HPC_V3.md section 14)
    assert d["limits_status"] == "REGISTERED" and "登记状态 | **REGISTERED**" in hp and "## 14. 审阅端按用户授权决定（2026-11-04）" in hp and all(v in hp for v in d["registered_sha"].values())
    assert (d["limits"]["time_limit_s"], d["limits"]["build_timeout_s"], d["limits"]["wait_start_max_s"]) == (864000, 5400, 7200)
    assert [d["hpc_jobs"][k]["walltime"] for k in ("F1", "F2", "F3", "F4", "batch")] == ["260:00:00", "262:00:00", "260:00:00", "262:00:00", "48:00:00"]
    j = d["hpc_jobs"]
    assert (j["F2"]["depends"], j["F2"]["wait_start_of"], j["F3"]["depends"], j["F4"]["depends"], j["batch"]["depends"]) == ("after:F1", "F1", "afterany:F1", "afterany:F2", "afterany:F3:F4")
    assert [j[k]["mem_gb"] for k in ("F1", "F2", "F3", "F4")] == [300, 250, 300, 250] and all(j[k]["ncpus"] == 48 for k in ("F1", "F2", "F3", "F4")) and j["batch"]["mem_gb"] == 120


def test_b4_batch4_outputs_with_and_without_a_definition():
    env = {k: v for k, v in os.environ.items() if k != "BATCH_DEF"}
    run = lambda cmd, e: subprocess.run([sys.executable, str(ROOT / "scripts_project/b4_batch4.py"), cmd], env=e, capture_output=True, text=True, check=True).stdout.splitlines()
    assert run("runtable", env) == ["F1|integrated|integrated_2920_3h||formal_barrier_1e6_t16|integrated", "F2|disconnected|disconnected_2920_3h||formal_barrier_1e6_t16|disconnected"]
    assert run("runmeta", env) == ["F1|450||A", "F2|250||A"]
    p2 = run("hpc-plan", env)
    assert p2[0] == "LIMITS|864000|871200|330|7200|3600|32400|10800|7200|100" and sum(l.startswith("JOB|") for l in p2) == 6 and "STATUS|REGISTERED" in p2 and "PAIR|A|F1|F2" in p2
    e3 = dict(env, BATCH_DEF=str(DEF))
    assert [l.split("|")[0] for l in run("runtable", e3)] == ["F1", "F2", "F3", "F4"] and run("runtable", e3)[3] == "F4|no_new_xb|no_new_xb_ev05_2920_3h||formal_barrier_1e6_t16|integrated"
    assert run("runmeta", e3) == ["F1|350||A", "F2|250||A", "F3|350||B", "F4|250|integrated_ev05|B"]
    p3 = run("hpc-plan", e3)
    assert p3[0] == "LIMITS|864000|871200|330|7200|5400|32400|10800|7200|100" and "STATUS|REGISTERED" in p3 and {"PAIR|A|F1|F2", "PAIR|B|F3|F4"} <= set(p3)
    jobs = {l.split("|")[1]: l.split("|") for l in p3 if l.startswith("JOB|")}
    assert list(jobs) == ["F1", "F2", "F3", "F4", "batch", "smoke56", "build_only_f1", "install"] and jobs["F3"][9] == "afterany:F1" and jobs["batch"][9] == "afterany:F3:F4"
    assert [l for l in p3 if l.startswith("ITERS|")] == ["ITERS|F1|350", "ITERS|F2|250", "ITERS|F3|350", "ITERS|F4|250"]
    # RUN_PLAN_HPC_V3.md 14.4: base 918,930 s; F2 two waits (F1's start + the start lock, review item 6), F3 / F4 one (the lock); every margin >= 2 h
    code = ("import b4_batch4 as B; w = B.walltime_components(); p = w['per_job']; assert all(v['registered_s'] >= v['sum_s'] and v['margin_s'] >= 7200 for v in p.values()); "
            "base = 330 + 5400 + 864000 + 7200 + 32400 + 2 * 3900 + 1800; assert base == 918930 and [p[k]['sum_s'] - base for k in ('F1', 'F2', 'F3', 'F4')] == [0, 14400, 7200, 7200]; "
            "assert [p[k]['margin_s'] for k in ('F1', 'F2', 'F3', 'F4')] == [17070, 9870, 9870, 17070] and w['projection_limit_s'] == 691200; "
            "assert set(B.STOP_ALWAYS) == set(B.RUNS); print(B.pairs())")
    out = subprocess.run([sys.executable, "-c", code], env=e3, cwd=str(ROOT / "scripts_project"), capture_output=True, text=True)
    assert out.returncode == 0 and "'B': ('F3', 'F4')" in out.stdout, out.stdout + out.stderr


def test_four_runs_one_job_each_then_the_batch_job(tmp_path):
    pkg = _pkg4(tmp_path)
    for rid, extra in (("F1", {}), ("F2", {"WAIT_START_OF": "F1"}), ("F3", {}), ("F4", {})):
        p = H._only(tmp_path, pkg, rid, dict(OBJ, CORES="25", **extra))
        assert p.returncode == 0, (rid, H._status(tmp_path)[-3000:])
    st = H._status(tmp_path); out = tmp_path / "out"
    assert all(f"DONE_ONLY:" in st and f"START_LOCK_{r}:acquired" in st and f"START_LOCK_RELEASED_{r}" in st for r in ("F1", "F2", "F3", "F4")) and not (out / ".gurobi_start_lock").exists()
    for rid, it, base in (("F1", 350, "integrated_2920_3h"), ("F2", 250, "no_new_xb_2920_3h"), ("F3", 350, "integrated_ev05_2920_3h"), ("F4", 250, "no_new_xb_ev05_2920_3h")):
        run = json.loads((out / rid / "RUN.json").read_text())
        assert run["iterations_reference"] == it and run["base"] == base and run["registered_sha256"] == sha(pkg / "networks" / f"{base}_unsolved.nc") == run["network_sha256"]
        assert json.loads((out / rid / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2"
    p = T._run(tmp_path, pkg, dict(CORES="25", POST_ONLY="1"), args=()); st = H._status(tmp_path)
    assert p.returncode == 0, st[-3000:]
    assert "BATCH_REFERENCE:exit=0" in st and "M12_BENEFIT:exit=0" in st and "M12_BENEFIT_B:exit=0" in st and all(f"REGRADE_{r}:" in st for r in ("F1", "F2", "F3", "F4"))
    s = json.loads((out / "BATCH4_SUMMARY.json").read_text())
    assert s["B6"]["b6_bn"] == pytest.approx(10.0) and s["B6_pairs"]["B"]["b6_bn"] == pytest.approx(15.0) and s["pair_comparison"]["delta_b6_bn"] == pytest.approx(5.0)
    assert s["pairs"] == {"A": ["F1", "F2"], "B": ["F3", "F4"]} and len(s["runs"]) == 4 and all(v["state"] == "ended" for v in s["runs"].values())
    assert (out / "export" / "batch" / "M12_BENEFIT_B").is_dir() and "第 B 对（F4 − F3）" in (out / "BATCH4_SUMMARY.md").read_text() and len(list(out.glob("results_*_final_*.tar.gz"))) == 2


def test_start_lock_keeps_two_concurrent_starts_a_gap_apart(tmp_path):
    pkg = _pkg4(tmp_path)
    procs = [subprocess.Popen(["bash", str(pkg / "run_batch4.sh"), "--only", rid, "--auth", "synthetic"], env=T._clean_env(dict(
        REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(tmp_path / "out"), FAKE_OUT=str(tmp_path / "out"), ALLOW_UNREGISTERED="1", LICENCE_GAP_S="4", GRACE_S="1", MONITOR_S="1", CORES="25",
        MEM_QUOTA_GIB="240", CGROUP_ROOT=str(tmp_path / "cgroup"), GRB_LICENSE_FILE=str(tmp_path / "lic"), GUROBI_TIME_LIMIT_S="1000", WALL_CAP_S="1200",
        SOLVE_CMD=f"{sys.executable} {tmp_path / 'standin/scripts_project/s2_solve.py'}", SPLIT_CMD=f"{sys.executable} {tmp_path / 'standin/scripts_project/b4_split_solve.py'}",
        VA_CMD=f"{sys.executable} {T.FAKE} va", C1_CMD=f"{sys.executable} {T.FAKE} c1", M12_CMD=f"{sys.executable} {T.FAKE} m12", M12A_CMD=f"{sys.executable} {T.FAKE} m12a", FAKE_SLEEP="2", **OBJ)),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for rid in ("F3", "F4")]
    for p in procs:
        p.wait(timeout=600); assert p.returncode == 0, p.stdout.read()[-2000:] + H._status(tmp_path)[-3000:]
    s3, s4 = (int((tmp_path / "out" / r / ".solve_start").read_text()) for r in ("F3", "F4"))
    st = H._status(tmp_path)
    assert abs(s3 - s4) >= 4, (s3, s4, st[-3000:])   # the second start waits for the gap after the first (under the lock)
    assert st.count(":acquired:") == 2 and not (tmp_path / "out" / ".gurobi_start_lock").exists()


def test_start_lock_stops_with_two_other_gurobi_processes_and_on_a_stale_lock(tmp_path):
    pkg = _pkg4(tmp_path); out = tmp_path / "out"
    for r in ("F1", "F2"):
        (out / r).mkdir(parents=True); (out / r / ".started").write_text("x"); (out / r / ".solve_start").write_text(str(int(time.time()) - 1000))
    p = H._only(tmp_path, pkg, "F3", dict(OBJ, CORES="25", WAIT_START_MAX_S="6"))
    st = H._status(tmp_path)
    assert p.returncode == 3 and "STOP_SAFE:START_LOCK:F3:no start slot" in st and "other Gurobi processes 2" in st and not T._calls(tmp_path) and not (out / ".gurobi_start_lock").exists()
    t2 = tmp_path / "b"; t2.mkdir(); pkg2 = _pkg4(t2); lk = t2 / "out" / ".gurobi_start_lock"; lk.mkdir(parents=True); (lk / "owner").write_text("F1 0 node 1\n")
    p = H._only(t2, pkg2, "F3", dict(OBJ, CORES="25", WAIT_START_MAX_S="6"))
    assert p.returncode == 3 and "STOP_SAFE:START_LOCK:F3:" in H._status(t2) and "held for 6s by F1 0 node 1" in H._status(t2) and not T._calls(t2) and lk.exists()


def test_refusals_proposed_limits_and_batch_mode_with_four_runs(tmp_path):
    pkg = _pkg4(tmp_path, status="PROPOSED")   # the refusal of PROPOSED limits (the repository definition is REGISTERED since 2026-11-04)
    env = T._clean_env(dict(REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(tmp_path / "out"), GRB_LICENSE_FILE=str(tmp_path / "lic")))
    p = subprocess.run(["bash", str(pkg / "run_batch4.sh"), "--only", "F1", "--auth", "x"], env=env, capture_output=True, text=True, timeout=120)
    assert p.returncode == 2 and "the limits of BATCH_DEF.json are PROPOSED" in p.stdout and not (tmp_path / "out" / "F1").exists()
    p = T._run(tmp_path, pkg, dict(OBJ, CORES="25"))
    assert p.returncode == 2 and "4 runs in the table - they run as one PBS job each" in p.stdout
    p = T._run(tmp_path, pkg, dict(CORES="25", BUILD_ONLY="1"), args=())
    assert p.returncode == 0 and [c[1] for c in T._calls(tmp_path, "build")] == ["F1", "F2", "F3", "F4"] and not T._calls(tmp_path), H._status(tmp_path)[-2000:]


def test_make_pbs_consistency_and_submission_chain(tmp_path):
    pkg = tmp_path / "pkg"; (pkg / "hpc").mkdir(parents=True)
    for f in ("make_pbs.sh", "hpr_submit.sh"):
        shutil.copy(HPC / f, pkg / "hpc" / f)
    (pkg / "COMMIT").write_text("0" * 40 + "\n"); shutil.copy(DEF, pkg / "BATCH_DEF.json")
    make = lambda: subprocess.run(["bash", str(pkg / "hpc" / "make_pbs.sh")], env=dict(os.environ, REPO=str(ROOT), PY=sys.executable), capture_output=True, text=True, cwd=str(pkg))
    p = make()
    assert p.returncode == 0, p.stdout + p.stderr
    pb = {x.stem: x.read_text() for x in (pkg / "pbs").glob("*.pbs")}
    assert sorted(pb) == sorted(j["name"] for j in json.loads(DEF.read_text(encoding="utf-8"))["hpc_jobs"].values())
    assert "#PBS -l walltime=260:00:00" in pb["hpr3_f1"] and "#PBS -l walltime=262:00:00" in pb["hpr3_f2"] and "JOB_TIME_LIMIT_S=864000" in pb["hpr3_f1"] and "JOB_DEPENDS=afterany:F1" in pb["hpr3_f3"] and "JOB_DEPENDS=afterany:F2" in pb["hpr3_f4"]
    assert "JOB_DEPENDS=afterany:F3:F4" in pb["hpr3_batch"] and "#PBS -l select=1:ncpus=48:mem=250gb" in pb["hpr3_f4"] and "for rid in F1 F2 batch" in pb["hpr3_smoke56"] and "STATUS|REGISTERED" in (pkg / "pbs" / "HPC_PLAN.txt").read_text()
    out = tmp_path / "C.json"
    c = subprocess.run([sys.executable, str(HPC / "hpr_consistency.py"), "--repo", str(ROOT), "--plan", str(D3 / "RUN_PLAN_HPC_V3.md"), "--runner", str(T.PKG / "run_batch4.sh"), "--preflight", str(T.PKG / "preflight.sh"),
                        "--pbs", str(pkg / "pbs"), "--job", str(HPC / "hpr_job.sh"), "--out", str(out)], env=_bdef(), capture_output=True, text=True)
    assert c.returncode == 0 and "ALL_CONSISTENT" in c.stdout, c.stdout + c.stderr
    rows = json.loads(out.read_text())["rows"]
    assert any(r["item"].startswith("F4 dependency") and r["consistent"] for r in rows) and sum(r["item"].endswith("walltime margin >= 7,200 s") and r["consistent"] for r in rows) == 4
    bin_ = tmp_path / "bin"; bin_.mkdir(); q = bin_ / "qsub"; log = tmp_path / "qsub.log"
    q.write_text(f"#!/bin/bash\nn=$(( $(wc -l < {log} 2>/dev/null || echo 0) + 1 ))\necho \"$*\" >> {log}\necho \"$n.venus01\"\n"); q.chmod(0o755)
    (pkg / "repo").mkdir(); (pkg / "repo" / ".package_commit").write_text("0" * 40 + "\n"); lic = tmp_path / "lic"; lic.write_text("x"); lic.chmod(0o600)
    auth = tmp_path / "auth.txt"; auth.write_text("synthetic authorisation for the stand-in submission test\n")
    senv = {k: v for k, v in T._clean_env(dict(PATH=f"{bin_}:{os.environ['PATH']}", GRB_LICENSE_FILE=str(lic))).items() if k not in ("BATCH_DEF",)}
    submit = lambda *a: subprocess.run(["bash", str(pkg / "hpc" / "hpr_submit.sh"), *a], env=senv, capture_output=True, text=True, cwd=str(pkg))
    # --dry-run before the smoke passed (operator guide step c2): nothing written or submitted, the chain printed with placeholder ids, the smoke refusal as a note
    s = submit("--auth-file", str(auth), "--motd-checked", "--dry-run")
    assert s.returncode == 0 and s.stdout.splitlines()[-1].startswith("DRY_RUN_OK: nothing submitted") and "1 check(s) above would refuse" in s.stdout, s.stdout + s.stderr
    assert [l for l in s.stdout.splitlines() if l.startswith("DRY-RUN: ")] == ["DRY-RUN: qsub pbs/hpr3_f1.pbs", "DRY-RUN: qsub -W depend=after:F1_JOBID pbs/hpr3_f2.pbs", "DRY-RUN: qsub -W depend=afterany:F1_JOBID pbs/hpr3_f3.pbs",
                                                                         "DRY-RUN: qsub -W depend=afterany:F2_JOBID pbs/hpr3_f4.pbs", "DRY-RUN: qsub -W depend=afterany:F3_JOBID:F4_JOBID pbs/hpr3_batch.pbs"]
    assert "DRY-RUN NOTE: the smoke job has not passed" in s.stdout and not log.exists() and not (pkg / "runs").exists() and not (pkg / "HPR_AUTH.txt").exists()
    s = submit("--dry-run")   # no auth file, no banner confirmation: notes, still exit 0 and nothing written
    assert s.returncode == 0 and "DRY-RUN NOTE: --auth-file" in s.stdout and "DRY-RUN NOTE: confirm that the login banner" in s.stdout and not log.exists() and not (pkg / "HPR_AUTH.txt").exists()
    (pkg / "runs" / "smoke56").mkdir(parents=True); (pkg / "runs" / "smoke56" / "SMOKE_STATUS.txt").write_text("SMOKE_RESULT:PASS\n")
    s = submit("--auth-file", str(auth), "--motd-checked", "--dry-run")
    assert s.returncode == 0 and "0 check(s) above would refuse" in s.stdout and "DRY-RUN NOTE" not in s.stdout and not log.exists() and not (pkg / "runs" / "batch4").exists()
    # submission: refused while PROPOSED (dry run: a note); with the REGISTERED limits the chain of dependencies through a stand-in qsub
    d = json.loads(DEF.read_text(encoding="utf-8")); d["limits_status"] = "PROPOSED"; (pkg / "BATCH_DEF.json").write_text(json.dumps(d, ensure_ascii=False)); shutil.rmtree(pkg / "pbs"); assert make().returncode == 0
    s = submit("--auth-file", str(auth), "--motd-checked")
    assert s.returncode == 2 and "limits of the package are PROPOSED" in s.stdout and not log.exists()
    s = submit("--auth-file", str(auth), "--motd-checked", "--dry-run")
    assert s.returncode == 0 and "DRY-RUN NOTE: the limits of the package are PROPOSED" in s.stdout and not log.exists()
    shutil.copy(DEF, pkg / "BATCH_DEF.json"); shutil.rmtree(pkg / "pbs"); assert make().returncode == 0
    s = submit("--auth-file", str(auth), "--motd-checked")
    assert s.returncode == 0, s.stdout + s.stderr
    assert log.read_text().splitlines() == ["pbs/hpr3_f1.pbs", "-W depend=after:1.venus01 pbs/hpr3_f2.pbs", "-W depend=afterany:1.venus01 pbs/hpr3_f3.pbs",
                                            "-W depend=afterany:2.venus01 pbs/hpr3_f4.pbs", "-W depend=afterany:3.venus01:4.venus01 pbs/hpr3_batch.pbs"]
    assert "F1=1.venus01:F2=2.venus01:F3=3.venus01:F4=4.venus01:batch=5.venus01" in (pkg / "runs" / "batch4" / "SUBMITTED.txt").read_text()
    # review item 6: --resume refuses while a start lock directory is left in runs/batch4 (nothing submitted)
    lk = pkg / "runs" / "batch4" / ".gurobi_start_lock"; lk.mkdir(); (lk / "owner").write_text("F3 0 node 1\n")
    s = submit("--auth-file", str(auth), "--motd-checked", "--resume")
    assert s.returncode == 2 and "REFUSED: runs/batch4/.gurobi_start_lock exists (owner: F3 0 node 1)" in s.stdout and len(log.read_text().splitlines()) == 5 and lk.exists()


def test_job_body_smoke56_with_the_definition(tmp_path):
    """HPC step D on the four-run definition: the F1 / F2 / batch job bodies of the smoke job; the expected objectives are the definition's (the local smoke)"""
    pkg = _pkg4(tmp_path); (pkg / "hpc").mkdir()
    for f in ("hpr_job.sh", "make_pbs.sh"):
        shutil.copy(HPC / f, pkg / "hpc" / f)
    shutil.copy(T.PKG / "preflight.sh", pkg / "preflight.sh"); (pkg / "COMMIT").write_text("0" * 40 + "\n"); os.symlink(ROOT, pkg / "repo"); os.chmod(tmp_path / "lic", 0o600)
    exp = json.loads(DEF.read_text(encoding="utf-8"))["smoke_expected"]["objective"]
    for rid in ("F1", "F2", "batch"):
        p = subprocess.run(["bash", str(pkg / "hpc" / "hpr_job.sh")], env=H._job_env(tmp_path, pkg, "smoke56", rid, dict(FAKE_OBJ_F1=repr(exp["F1"]), FAKE_OBJ_F2=repr(exp["F2"]))),
                           capture_output=True, text=True, timeout=600)
        assert p.returncode == 0, (rid, p.stdout[-1500:], p.stderr[-1500:])
    out = pkg / "runs" / "smoke56"; s = (out / "SMOKE_STATUS.txt").read_text()
    assert "SMOKE_RESULT:PASS" in s and s.count("relative_difference=0.000e+00") == 2 and "F2:termination=optimal" in s, s
    summ = json.loads((out / "BATCH4_SUMMARY.json").read_text())
    assert summ["B6"]["b6_bn"] == pytest.approx((exp["F2"] - exp["F1"]) / 1e9) and summ["B6_pairs"]["B"] is None and not (out / "F3" / ".started").exists() and not (out / "F3" / "RUN.json").exists()


def test_job_body_refusals_with_the_definition(tmp_path):
    pkg = H._job_pkg(tmp_path); d = json.loads(DEF.read_text(encoding="utf-8")); d["limits_status"] = "PROPOSED"; (pkg / "BATCH_DEF.json").write_text(json.dumps(d, ensure_ascii=False))
    for rid, msg in (("F3", "the limits of BATCH_DEF.json are PROPOSED"), ("F5", "JOB_RID=F5 (F1 F2 F3 F4)")):
        p = subprocess.run(["bash", str(pkg / "hpc" / "hpr_job.sh")], env=H._job_env(tmp_path, pkg, "formal", rid, {"JOB_NCPUS": "48", "JOB_MEM_GB": "300"}, standin=False), capture_output=True, text=True, timeout=120)
        assert p.returncode == 2 and msg in p.stdout, (rid, p.stdout, p.stderr)
    p = subprocess.run(["bash", str(pkg / "hpc" / "hpr_job.sh")], env=H._job_env(tmp_path, pkg, "batch", "batch", {"JOB_NCPUS": "12", "JOB_MEM_GB": "120"}, standin=False), capture_output=True, text=True, timeout=120)
    assert p.returncode == 2 and "has not ended (the batch job runs after every run: F1 F2 F3 F4" in p.stdout, p.stdout


def test_job_body_predecessor_not_ended_and_preflight_failure_halt_the_batch(tmp_path):
    """review item 3: F3 (afterany:F1) after an F1 job that ended without a run end and without a halt -> STOP_SAFE:PREDECESSOR_NOT_ENDED, nothing started;
    a formal job whose in-job preflight fails -> STOP_SAFE:PREFLIGHT_FAILED (no later run starts behind it)"""
    pkg = _pkg4(tmp_path); (pkg / "hpc").mkdir()
    for f in ("hpr_job.sh", "make_pbs.sh"):
        shutil.copy(HPC / f, pkg / "hpc" / f)
    shutil.copy(T.PKG / "preflight.sh", pkg / "preflight.sh"); (pkg / "COMMIT").write_text("0" * 40 + "\n"); os.symlink(ROOT, pkg / "repo"); os.chmod(tmp_path / "lic", 0o600)
    out = pkg / "runs" / "batch4"; job = lambda rid, extra: subprocess.run(["bash", str(pkg / "hpc" / "hpr_job.sh")], env=H._job_env(tmp_path, pkg, "formal", rid, dict(JOB_NCPUS="48", JOB_MEM_GB="300", **extra)),
                                                                       capture_output=True, text=True, timeout=600)
    (out / "F1").mkdir(parents=True); (out / "F1" / ".started").write_text("x")   # F1's job was killed (qdel / walltime): started, never ended, no STOP written
    p = job("F3", dict(JOB_DEPENDS="afterany:F1"))
    assert p.returncode == 3 and "STOP_SAFE:PREDECESSOR_NOT_ENDED:F3:F1" in p.stdout, (p.stdout, p.stderr)
    assert (out / "STOP_SAFE").read_text().startswith("PREDECESSOR_NOT_ENDED:F3:F1 has no .ended") and not (out / "F3").exists() and not (out / "STATUS.txt").exists()
    rec = (out / "PBS_JOBS.txt").read_text(); assert "STOP_SAFE:PREDECESSOR_NOT_ENDED:formal:F1" in rec and "JOB_END:formal:formal:F3:exit=3" in rec and "PREFLIGHT:" not in rec
    p = job("F4", dict(JOB_DEPENDS="afterany:F2", ALLOW_UNREGISTERED="1"))   # the batch is halted now: no second STOP_SAFE line from the job body; the (stand-in) runner does not start F4
    assert p.returncode == 3 and (out / "STOP_SAFE").read_text().count("\n") == 1 and "NOT_STARTED_F4:halted before the start" in (out / "STATUS.txt").read_text() and not (out / "F4" / ".started").exists()
    t2 = tmp_path / "b"; t2.mkdir(); pkg2 = _pkg4(t2); (pkg2 / "hpc").mkdir(); shutil.copy(HPC / "hpr_job.sh", pkg2 / "hpc" / "hpr_job.sh"); shutil.copy(T.PKG / "preflight.sh", pkg2 / "preflight.sh")
    (pkg2 / "COMMIT").write_text("0" * 40 + "\n"); os.symlink(ROOT, pkg2 / "repo"); os.chmod(t2 / "lic", 0o600)
    p = subprocess.run(["bash", str(pkg2 / "hpc" / "hpr_job.sh")], env=H._job_env(t2, pkg2, "formal", "F1", dict(JOB_NCPUS="48", JOB_MEM_GB="300", HPR_TEST_PREFLIGHT_SECTIONS="guards")), capture_output=True, text=True, timeout=600)
    o2 = pkg2 / "runs" / "batch4"   # the guards section sees the stand-in hooks of the test environment -> PREFLIGHT FAILED
    assert p.returncode == 1 and (o2 / "STOP_SAFE").read_text().startswith("PREFLIGHT_FAILED:F1:job=local.test:PREFLIGHT FAILED") and "PREFLIGHT_FAILED:formal" in (o2 / "PBS_JOBS.txt").read_text() and not (o2 / "F1").exists()


def test_post_only_post_processes_every_ended_run_when_halted(tmp_path):
    """review item 4: POST_ONLY on a halted batch still post-processes every ended run (here F2 lost its acceptance before the batch job), then summary and halted packs"""
    pkg = _pkg4(tmp_path); out = tmp_path / "out"
    for rid, extra in (("F1", {}), ("F2", {"WAIT_START_OF": "F1"})):
        assert H._only(tmp_path, pkg, rid, dict(OBJ, CORES="25", **extra)).returncode == 0, H._status(tmp_path)[-3000:]
    (out / "F2" / "VIOLATIONS.json").rename(out / "F2" / "VIOLATIONS_before.json"); (out / "STOP_SAFE").write_text("PROJECTION:F3:synthetic halt for the test\n")
    n0 = len(H._status(tmp_path))
    p = T._run(tmp_path, pkg, dict(CORES="25", POST_ONLY="1"), args=()); st = H._status(tmp_path)[n0:]
    assert p.returncode == 3 and "VIOLATIONS_F2:exit=0" in st and "V6_F1:" in st and "V6_F2:" in st and "POST_ONLY_F3:not solved" in st and "POST_ONLY_F4:not solved" in st, st[-3000:]
    assert (out / "F2" / "VIOLATIONS.json").exists() and "HALTED:" in st and len(list(out.glob("results_*_halted_*.tar.gz"))) == 2
