"""V3.1 package (decision 195, V3_FIX_INSTRUCTION.md section 6): the v3.1 definition (= v3 + run_dirs), the run folders runs/batch5 / runs/smoke56_v31 through
b4_batch4.py hpc-plan (RUNDIRS) -> pbs/HPC_PLAN.txt -> hpr_job.sh / hpr_submit.sh / hpr_status.sh, the consistency rows, and the v3 defaults unchanged. Driven with the
B4P SYNTHETIC stand-ins (no solver, no model). Never run beside a real local solve (the process counts would see it)."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(ROOT / "scripts_project"))
import test_b4p_batch4 as T   # noqa: E402
import test_hpr_two_jobs as H   # noqa: E402
import test_v3_hpc_runner as V   # noqa: E402

D3 = ROOT / "research/06_scope_redesign/p1_v3_20261102"; DEF3 = D3 / "batch_def/BATCH_DEF_2920x3h_v3hpc.json"; DEF31 = D3 / "batch_def/BATCH_DEF_2920x3h_v31hpc.json"; HPC = H.HPC
pytestmark = pytest.mark.skipif(shutil.which("setsid") is None or not Path("/usr/bin/time").exists(), reason="setsid / GNU time missing")
RD31 = "RUNDIRS|runs/batch5|runs/smoke56_v31|runs/build_only_f1"


def _plan(defpath):
    p = subprocess.run([sys.executable, "scripts_project/b4_batch4.py", "hpc-plan"], env=dict(os.environ, BATCH_DEF=str(defpath)), capture_output=True, text=True, cwd=str(ROOT))
    return p


def test_v31_definition_is_v3_plus_run_folders():
    d3 = json.loads(DEF3.read_text(encoding="utf-8")); d31 = json.loads(DEF31.read_text(encoding="utf-8"))
    assert set(d31) == set(d3) | {"run_dirs"}
    for k in d3:
        if k not in ("name", "note"):
            assert d31[k] == d3[k], k
    assert d31["run_dirs"] == {"formal": "runs/batch5", "smoke56": "runs/smoke56_v31", "build_only": "runs/build_only_f1"}
    assert d31["limits_status"] == "REGISTERED" and d31["smoke_expected"]["objective"] == {"F1": 329705566422.23596, "F2": 342268691464.4567}


def test_hpc_plan_run_folders_and_refusal(tmp_path):
    p = _plan(DEF31); assert p.returncode == 0 and RD31 in p.stdout.splitlines(), p.stdout + p.stderr
    p = _plan(DEF3); assert p.returncode == 0 and "RUNDIRS|runs/batch4|runs/smoke56|runs/build_only_f1" in p.stdout.splitlines()
    for bad in ({"formal": "../batch5"}, {"formal": "runs/.."}, {"formal": "runs/smoke56", "smoke56": "runs/smoke56"}, {"other": "runs/x"}):
        d = json.loads(DEF31.read_text(encoding="utf-8")); d["run_dirs"] = {**d["run_dirs"], **bad}; f = tmp_path / "bad.json"; f.write_text(json.dumps(d))
        p = _plan(f); assert p.returncode != 0 and "run_dirs of the batch definition" in p.stderr, bad


def test_v31_pbs_consistency_submit_and_status(tmp_path):
    pkg = tmp_path / "pkg"; (pkg / "hpc").mkdir(parents=True)
    for f in ("make_pbs.sh", "hpr_submit.sh", "hpr_status.sh"):
        shutil.copy(HPC / f, pkg / "hpc" / f)
    (pkg / "COMMIT").write_text("0" * 40 + "\n"); shutil.copy(DEF31, pkg / "BATCH_DEF.json")
    p = subprocess.run(["bash", str(pkg / "hpc" / "make_pbs.sh")], env=dict(os.environ, REPO=str(ROOT), PY=sys.executable), capture_output=True, text=True, cwd=str(pkg))
    assert p.returncode == 0, p.stdout + p.stderr
    assert RD31 in (pkg / "pbs" / "HPC_PLAN.txt").read_text().splitlines()
    out = tmp_path / "C.json"
    c = subprocess.run([sys.executable, str(HPC / "hpr_consistency.py"), "--repo", str(ROOT), "--plan", str(D3 / "RUN_PLAN_HPC_V3.md"), "--runner", str(T.PKG / "run_batch4.sh"), "--preflight", str(T.PKG / "preflight.sh"),
                        "--pbs", str(pkg / "pbs"), "--job", str(HPC / "hpr_job.sh"), "--out", str(out)], env=dict(os.environ, BATCH_DEF=str(DEF31)), capture_output=True, text=True)
    assert c.returncode == 0 and "ALL_CONSISTENT" in c.stdout, c.stdout + c.stderr
    rows = {r["item"]: r for r in json.loads(out.read_text())["rows"]}
    assert rows["run folder formal"]["consistent"] and rows["run folder formal"]["values"] == dict(plan="runs/batch5", b4_batch4="runs/batch5", pbs_hpc_plan="runs/batch5")
    assert rows["run folder smoke56"]["values"]["pbs_hpc_plan"] == "runs/smoke56_v31" and rows["job body reads the run folders from pbs/HPC_PLAN.txt (RUNDIRS)"]["consistent"]
    # submission: the smoke status is read from runs/smoke56_v31, the formal folder is runs/batch5; the halted v3 record runs/batch4 does not block it
    bin_ = tmp_path / "bin"; bin_.mkdir(); q = bin_ / "qsub"; log = tmp_path / "qsub.log"
    q.write_text(f"#!/bin/bash\nn=$(( $(wc -l < {log} 2>/dev/null || echo 0) + 1 ))\necho \"$*\" >> {log}\necho \"$n.venus01\"\n"); q.chmod(0o755)
    (pkg / "repo").mkdir(); (pkg / "repo" / ".package_commit").write_text("0" * 40 + "\n"); lic = tmp_path / "lic"; lic.write_text("x"); lic.chmod(0o600)
    auth = tmp_path / "auth.txt"; auth.write_text("synthetic authorisation for the stand-in submission test\n")
    senv = {k: v for k, v in T._clean_env(dict(PATH=f"{bin_}:{os.environ['PATH']}", GRB_LICENSE_FILE=str(lic))).items() if k not in ("BATCH_DEF",)}
    submit = lambda *a: subprocess.run(["bash", str(pkg / "hpc" / "hpr_submit.sh"), *a], env=senv, capture_output=True, text=True, cwd=str(pkg))
    old = pkg / "runs" / "batch4"; old.mkdir(parents=True); (old / "STOP_SAFE").write_text("v3 halted batch record\n")
    s = submit("--auth-file", str(auth), "--motd-checked", "--dry-run")
    assert s.returncode == 0 and "runs/smoke56_v31/SMOKE_STATUS.txt: SMOKE_RESULT:PASS missing" in s.stdout and "1 check(s) above would refuse" in s.stdout, s.stdout
    (pkg / "runs" / "smoke56").mkdir(); (pkg / "runs" / "smoke56" / "SMOKE_STATUS.txt").write_text("SMOKE_RESULT:PASS\n")   # a v3 smoke pass does not count for v3.1
    assert "1 check(s) above would refuse" in submit("--auth-file", str(auth), "--motd-checked", "--dry-run").stdout
    (pkg / "runs" / "smoke56_v31").mkdir(); (pkg / "runs" / "smoke56_v31" / "SMOKE_STATUS.txt").write_text("SMOKE_RESULT:PASS\n")
    s = submit("--auth-file", str(auth), "--motd-checked", "--dry-run")
    assert s.returncode == 0 and "0 check(s) above would refuse" in s.stdout and not log.exists() and not (pkg / "runs" / "batch5").exists(), s.stdout
    s = submit("--auth-file", str(auth), "--motd-checked")
    assert s.returncode == 0, s.stdout + s.stderr
    assert "F1=1.venus01:F2=2.venus01:F3=3.venus01:F4=4.venus01:batch=5.venus01" in (pkg / "runs" / "batch5" / "SUBMITTED.txt").read_text()
    assert not (old / "SUBMITTED.txt").exists() and (old / "STOP_SAFE").read_text() == "v3 halted batch record\n"
    s = submit("--auth-file", str(auth), "--motd-checked")
    assert s.returncode == 2 and "REFUSED: runs/batch5 exists" in s.stdout
    st = subprocess.run(["bash", str(pkg / "hpc" / "hpr_status.sh")], env=senv, capture_output=True, text=True, cwd=str(pkg))
    assert st.returncode == 0 and "; runs runs/batch5" in st.stdout.splitlines()[0], st.stdout


def _pkg31(tmp_path):
    pkg = V._pkg4(tmp_path); (pkg / "hpc").mkdir()
    d = json.loads((pkg / "BATCH_DEF.json").read_text(encoding="utf-8")); d["run_dirs"] = json.loads(DEF31.read_text(encoding="utf-8"))["run_dirs"]
    (pkg / "BATCH_DEF.json").write_text(json.dumps(d, ensure_ascii=False))
    for f in ("hpr_job.sh", "make_pbs.sh"):
        shutil.copy(HPC / f, pkg / "hpc" / f)
    shutil.copy(T.PKG / "preflight.sh", pkg / "preflight.sh"); (pkg / "COMMIT").write_text("0" * 40 + "\n"); os.symlink(ROOT, pkg / "repo"); os.chmod(tmp_path / "lic", 0o600)
    p = subprocess.run(["bash", str(pkg / "hpc" / "make_pbs.sh")], env=dict(os.environ, REPO=str(ROOT), PY=sys.executable), capture_output=True, text=True, cwd=str(pkg))
    assert p.returncode == 0 and RD31 in (pkg / "pbs" / "HPC_PLAN.txt").read_text(), p.stdout + p.stderr
    return pkg, d


def test_job_body_smoke56_writes_into_the_v31_smoke_folder(tmp_path):
    pkg, d = _pkg31(tmp_path); exp = d["smoke_expected"]["objective"]
    for rid in ("F1", "F2", "batch"):
        p = subprocess.run(["bash", str(pkg / "hpc" / "hpr_job.sh")], env=H._job_env(tmp_path, pkg, "smoke56", rid, dict(FAKE_OBJ_F1=repr(exp["F1"]), FAKE_OBJ_F2=repr(exp["F2"]))),
                           capture_output=True, text=True, timeout=600)
        assert p.returncode == 0, (rid, p.stdout[-1500:], p.stderr[-1500:])
    out = pkg / "runs" / "smoke56_v31"; s = (out / "SMOKE_STATUS.txt").read_text()
    assert "SMOKE_RESULT:PASS" in s and s.count("relative_difference=0.000e+00") == 2 and not (pkg / "runs" / "smoke56").exists(), s
    assert "run_dir=" + str(out) in (out / "PBS_JOBS.txt").read_text()


def test_formal_job_body_uses_runs_batch5(tmp_path):
    pkg, _ = _pkg31(tmp_path)
    lf = pkg / "runs" / "batch5" / "F1"; lf.mkdir(parents=True); (lf / ".cond").write_text("build_only")
    p = subprocess.run(["bash", str(pkg / "hpc" / "hpr_job.sh")], env=H._job_env(tmp_path, pkg, "formal", "F1", {"JOB_NCPUS": "48", "JOB_MEM_GB": "300"}, standin=False), capture_output=True, text=True, timeout=120)
    assert p.returncode == 2 and f"REFUSED: {lf} holds a dry-run leftover (.cond=build_only) - the formal RUN_DIR must be fresh (runs/batch5)" in p.stdout, p.stdout
    (pkg / "pbs" / "HPC_PLAN.txt").write_text((pkg / "pbs" / "HPC_PLAN.txt").read_text().replace(RD31, "RUNDIRS|runs/../x|runs/smoke56_v31|runs/build_only_f1"))
    p = subprocess.run(["bash", str(pkg / "hpc" / "hpr_job.sh")], env=H._job_env(tmp_path, pkg, "formal", "F1", {"JOB_NCPUS": "48", "JOB_MEM_GB": "300"}, standin=False), capture_output=True, text=True, timeout=120)
    assert p.returncode == 2 and "is not runs/<name>" in p.stdout, p.stdout
