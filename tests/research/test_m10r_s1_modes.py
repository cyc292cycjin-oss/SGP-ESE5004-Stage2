"""M10R (third-batch close-out; supplement S1): the per-run modes of run_batch3.sh driven with the synthetic stand-ins of
tests/research/fixtures/m10p_fake_pipeline.py (no solver, no model) - after a batch halted by a G2 failure of R9 (the ledger B16 not computable,
as on 2026-10-24): --only R11 solves the never-started run with the registered rules and leaves everything else alone; --repost R9 --into
re-does the post-processing of the ended run into a new folder without a solve or a licence and never touches the original folder / STOP /
summary; --summary-s1 recomputes the batch-level summary with the reposted run; refusals (ended run, missing batch reference, STOP_SAFE,
mode mixes, --auth in a no-solve mode); the graded rules for the selected run (no solution -> UNUSABLE, G2 -> STOP)."""
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_m10p_batch3 import FAKE, PKG, _calls, _package, _run, sha  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts_project"))
import m10_batch3_summary as S  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("setsid") is None or not Path("/usr/bin/time").exists(), reason="setsid / GNU time missing")
F = f"{sys.executable} {FAKE}"


def _halted_batch(tmp_path):
    """the third-batch situation: R9 G2 (B16 not computable) -> STOP, R11 never started, R10 of the other lane finished."""
    pkg = _package(tmp_path); out = tmp_path / "out"
    # lane A R7 (8 s) -> R9 (4 s, B16 fails -> STOP) -> R11; lane B R8 (0.2 s) -> R10 (10 s): R10 starts well before the STOP (wait_gap polls every 5 s) and finishes
    p = _run(tmp_path, pkg, {"FAKE_B16_FAIL_R9": "1", "FAKE_SLEEP_R7": "8", "FAKE_SLEEP_R9": "4", "FAKE_SLEEP_R10": "10"})
    st = (out / "STATUS.txt").read_text()
    assert p.returncode == 3, st[-3000:]
    assert (out / "STOP").read_text().split() == ["R9"] and "STOP_NOT_ACCEPTED:R9:g2" in st and "LANE_A:R11 not started" in st
    assert sorted(c[1] for c in _calls(tmp_path)) == sorted(r for r in S.RUNS if r != "R11")
    v6 = json.loads((out / "R9" / "V6_ACCEPTANCE.json").read_text())
    assert v6["label"] == "NOT_ACCEPTED" and v6["G2"]["G2_3"]["checks"]["b16_computable"] is False and v6["G1"]["a"]
    assert (out / "R10" / "V6_ACCEPTANCE.json").exists() and (out / "BATCH3_SUMMARY.json").exists()
    return pkg, out


def _snapshot(d: Path) -> dict:
    return {str(p.relative_to(d)): sha(p) for p in d.rglob("*") if p.is_file()}


def test_halted_batch_then_only_r11_repost_r9_and_summary_s1(tmp_path):
    pkg, out = _halted_batch(tmp_path)
    r9_before = _snapshot(out / "R9"); summ = sha(out / "BATCH3_SUMMARY.json"); r1 = sha(out / "R1" / "V6_ACCEPTANCE.json"); n0 = len(_calls(tmp_path))
    # ---- --only R11: solved once with the registered rules; nothing else touched; the STOP of R9 is acknowledged, not a reason to stop R11
    p = _run(tmp_path, pkg, {}, args=("--auth", "synthetic test", "--only", "R11"))
    st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, st[-2500:]
    calls = _calls(tmp_path)
    assert len(calls) == n0 + 1 and calls[-1][1] == "R11" and calls[-1][2] == "formal_barrier" and float(calls[-1][3]) == 28800.0
    only = st.split("ONLY_MODE:")[-1]
    assert "existing_stop=R9" in only and "DONE_ONLY:" in only and "runs=R11" in only and "SKIP_ENDED_" not in only and "SOLVE_R11" in only
    assert (out / "STOP").read_text().split() == ["R9"] and sha(out / "BATCH3_SUMMARY.json") == summ and sha(out / "R1" / "V6_ACCEPTANCE.json") == r1
    assert _snapshot(out / "R9") == r9_before and not (out / "UNUSABLE").exists()
    assert json.loads((out / "R11" / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2" and {c[1]: c[2] for c in _calls(tmp_path, "c1")}["R11"] == "ref=batch"
    assert "REGRADE_" not in only and "PROFILE_CHOICE" not in only and "M12_LOO" not in only
    assert len(list(out.glob("results_light_only_R11_*.tar.gz"))) == 1 and (out / "export" / "R11" / "ONLY_STATUS.txt").exists() and (out / "export" / "R11" / "ARRAYS_MANIFEST.json").exists()
    assert "R11" in json.loads((out / "export" / "R11" / "ARRAYS_MANIFEST.json").read_text())["runs"]
    p = _run(tmp_path, pkg, {}, args=("--auth", "synthetic test", "--only", "R11"))                                   # a solve is never repeated
    assert p.returncode == 2 and "REFUSED: --only R11 has ended" in p.stdout and len(_calls(tmp_path)) == n0 + 1
    # ---- --repost R9 --into: no solve, no licence, the original folder / STOP / STATUS / summary unchanged, label recomputed in the new folder
    into = tmp_path / "s1"; st_sha = sha(out / "STATUS.txt")
    p = _run(tmp_path, pkg, {"LEDGER_CMD": f"{F} ledger", "GRB_LICENSE_FILE": ""}, args=("--repost", "R9", "--into", str(into)))
    st1 = (into / "STATUS.txt").read_text()
    assert p.returncode == 0, st1[-2500:]
    assert len(_calls(tmp_path)) == n0 + 1 and _calls(tmp_path, "ledger") == [["ledger", "R9", "None"]]   # no solve; the ledger step runs with GRB_LICENSE_FILE removed (every post-processing step does)
    assert "mode=repost(R9)" in st1 and "REPOST_R9:" in st1 and "LEDGER_R9:exit=0" in st1 and "REPOST_CLASS:R9:label=ACCEPTED_LAYER2:class=accepted" in st1 and "DONE_REPOST:" in st1
    assert "label_before=NOT_ACCEPTED:label_after=ACCEPTED_LAYER2" in st1
    new = into / "R9"
    assert json.loads((new / "REPOST.json").read_text())["label_before"] == "NOT_ACCEPTED" and json.loads((new / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2"
    rc = json.loads((new / "REPOST_CHECK.json").read_text())
    assert rc["violations_equal"] and rc["c1_ab_equal"] and rc["label_before"] == "NOT_ACCEPTED" and rc["label_after"] == "ACCEPTED_LAYER2" and rc["b16"]["before"]["passed"] is False and rc["b16"]["after"]["passed"]
    assert (new / "lp").is_symlink() and (new / "solution").is_symlink() and (new / "ALLOCATION.json").exists() and (new / "m12_owen" / "OWEN.json").exists() and (new / "STOP_CLASS.json").exists()
    assert (into / "export" / "R9" / "V6_ACCEPTANCE.json").exists() and len(list(into.glob("results_light_repost_R9_*.tar.gz"))) == 1 and (into / "POSTPROC_ERRORS").exists() is False
    assert _snapshot(out / "R9") == r9_before and (out / "STOP").read_text().split() == ["R9"] and sha(out / "STATUS.txt") == st_sha and sha(out / "BATCH3_SUMMARY.json") == summ
    p = _run(tmp_path, pkg, {"LEDGER_CMD": f"{F} ledger", "GRB_LICENSE_FILE": ""}, args=("--repost", "R9", "--into", str(into)))
    assert p.returncode == 2 and "exists - every repost goes to a new folder" in p.stdout
    # ---- --summary-s1 with R9 from the repost: sensitivity R9 - R2 usable, R11 pairs computable; the original summary unchanged
    p = _run(tmp_path, pkg, {"GRB_LICENSE_FILE": ""}, args=("--summary-s1", "--into", str(into), "--use", f"R9={new}"))
    st1 = (into / "STATUS.txt").read_text()
    assert p.returncode == 0, st1[-2000:]
    s1 = json.loads((into / "batch_s1" / "BATCH3_SUMMARY_S1.json").read_text())
    sens = {(x["new"], x["base"]): x for x in s1["sensitivity"]}
    assert sens[("R9", "R2")]["usable"] is True and sens[("R9", "R2")]["new_label"] == "ACCEPTED_LAYER2" and sens[("R9", "R2")]["reposted"] == ["R9"] and sens[("R9", "R2")]["computable"]
    assert sens[("R11", "R2")]["usable"] is True and sens[("R11", "R2")]["computable"] and s1["information"][0]["computable"] and s1["information"][0]["usable"] is True
    assert s1["reposts"]["R9"]["label_before"] == "NOT_ACCEPTED" and s1["reposts"]["R9"]["label_after"] == "ACCEPTED_LAYER2" and s1["runs"]["R9"]["v6"] == "ACCEPTED_LAYER2"
    assert s1["stop_not_accepted"] == ["R9"] and s1["name"] == "BATCH3_SUMMARY_S1" and s1["runs"]["R11"]["state"] == "ended"
    orig = json.loads((out / "BATCH3_SUMMARY.json").read_text())
    assert {(x["new"], x["base"]): x["usable"] for x in orig["sensitivity"]}[("R9", "R2")] is False and sha(out / "BATCH3_SUMMARY.json") == summ
    assert (into / "batch_s1" / "BATCH3_SUMMARY_S1.md").exists() and (into / "export" / "batch_s1" / "BATCH3_SUMMARY_S1.json").exists() and "DONE_SUMMARY_S1:" in st1
    assert "R9（NOT_ACCEPTED → ACCEPTED_LAYER2" in (into / "batch_s1" / "BATCH3_SUMMARY_S1.md").read_text()
    assert len(list(into.glob("results_light_summary_s1_*.tar.gz"))) == 1 and json.loads((into / "export" / "batch_s1" / "ARRAYS_MANIFEST.json").read_text())["files"] == []


@pytest.mark.parametrize("extra,code,expect", [({"FAKE_NOSOL_R11": "1"}, 0, "unusable"), ({"FAKE_SUBSET_R11": "differ"}, 3, "stop")])
def test_only_r11_follows_the_graded_rules(tmp_path, extra, code, expect):
    pkg, out = _halted_batch(tmp_path); n0 = len(_calls(tmp_path))
    p = _run(tmp_path, pkg, extra, args=("--auth", "synthetic test", "--only", "R11"))
    st = (out / "STATUS.txt").read_text().split("ONLY_MODE:")[-1]
    assert p.returncode == code, st[-2500:]
    assert len(_calls(tmp_path)) == n0 + 1
    if expect == "unusable":
        assert dict(x.split()[:2] for x in (out / "UNUSABLE").read_text().splitlines()) == {"R11": "nosol"} and "UNUSABLE:R11:nosol" in st and "DONE_ONLY:" in st and "unusable=R11" in st
        assert (out / "STOP").read_text().split() == ["R9"]
    else:
        assert (out / "STOP").read_text().split() == ["R9", "R11"] and "STOP_NOT_ACCEPTED:R11:g2" in st and "HALTED_ONLY:" in st and not (out / "UNUSABLE").exists()
        assert json.loads((out / "R11" / "STOP_CLASS.json").read_text())["cls"] == "g2"
    assert len(list(out.glob("results_light_only_R11_*.tar.gz"))) == 1


def test_refusals_of_the_per_run_modes(tmp_path):
    pkg, out = _halted_batch(tmp_path); n0 = len(_calls(tmp_path)); st_sha = sha(out / "STATUS.txt"); into = tmp_path / "s1"
    A = ("--auth", "synthetic test")
    cases = [
        (A + ("--only", "R9"), {}, "--only R9 has ended"),
        (A + ("--only", "R12"), {}, "not a run of the registered table"),
        (A + ("--only", "R11"), {"POST_ONLY": "1"}, "--only is a solve mode"),
        (A + ("--only", "R11", "--repost", "R9", "--into", str(into)), {}, "--only is a solve mode"),
        (("--repost", "R11", "--into", str(into)), {"GRB_LICENSE_FILE": ""}, "--repost R11 has not ended"),
        (("--repost", "R9"), {"GRB_LICENSE_FILE": ""}, "need --into"),
        (A + ("--repost", "R9", "--into", str(into)), {}, "--auth together with"),
        (("--repost", "R9", "--into", str(into), "--summary-s1"), {"GRB_LICENSE_FILE": ""}, "two steps"),
        (("--summary-s1",), {"GRB_LICENSE_FILE": ""}, "need --into"),
        (("--use", "R9=x",), {"GRB_LICENSE_FILE": ""}, "--use <rid>=<dir> belongs to --summary-s1"),
        (("--arrays", "x",), {"GRB_LICENSE_FILE": ""}, "--arrays <dir> belongs to --repost"),
        (("--summary-s1", "--into", str(into), "--use", "R9=" + str(tmp_path / "nowhere")), {"GRB_LICENSE_FILE": ""}, "--use R9="),
    ]
    for args, extra, text in cases:
        p = _run(tmp_path, pkg, extra, args=args)
        assert p.returncode == 2 and text in p.stdout, (args, p.stdout[-400:])
    ref = out / "BATCH_REFERENCE.json"; ref.rename(out / "BATCH_REFERENCE.json.aside")
    p = _run(tmp_path, pkg, {}, args=A + ("--only", "R11"))
    assert p.returncode == 2 and "needs the batch C1 reference" in p.stdout
    (out / "BATCH_REFERENCE.json.aside").rename(ref)
    (out / "STOP_SAFE").write_text("INTERRUPTED_X\n")
    p = _run(tmp_path, pkg, {}, args=A + ("--only", "R11"))
    assert p.returncode == 2 and "STOP_SAFE present" in p.stdout
    (out / "STOP_SAFE").unlink()
    assert len(_calls(tmp_path)) == n0 and sha(out / "STATUS.txt") == st_sha and not into.exists()   # nothing solved, nothing written


def test_repost_ledger_failure_is_recorded_and_the_label_stays_not_accepted(tmp_path):
    """a ledger redo that fails (exit 1) is a POSTPROC_ERROR of the repost folder; C1 (c) stays not computable, the label NOT_ACCEPTED, the class g2 is recorded only."""
    pkg, out = _halted_batch(tmp_path); into = tmp_path / "s1"
    p = _run(tmp_path, pkg, {"LEDGER_CMD": f"{F} ledger", "GRB_LICENSE_FILE": "", "FAKE_RAISE_LEDGER_R9": "1"}, args=("--repost", "R9", "--into", str(into)))
    st1 = (into / "STATUS.txt").read_text()
    assert p.returncode == 0, st1[-2000:]
    assert "POSTPROC_ERROR:R9:ledger:exit=1" in st1 and (into / "POSTPROC_ERRORS").read_text().startswith("R9 ledger exit=1")
    assert json.loads((into / "R9" / "V6_ACCEPTANCE.json").read_text())["label"] == "NOT_ACCEPTED" and "REPOST_CLASS:R9:label=NOT_ACCEPTED:class=g2:registered_action=stop" in st1
    assert (out / "STOP").read_text().split() == ["R9"] and not (out / "POSTPROC_ERRORS").exists()


def test_only_dry_run_builds_the_selected_run_and_exits_before_the_solver(tmp_path):
    """BUILD_ONLY=1 --only R11 (no --auth): the variant of R11 only, the LP build with --stop-before-solve, BUILD_CHECK, no solve, licence tripwire."""
    pkg = _package(tmp_path); out = tmp_path / "out"
    p = _run(tmp_path, pkg, {"BUILD_ONLY": "1"}, args=("--only", "R11"))
    st = (out / "STATUS.txt").read_text()
    assert p.returncode == 0, st[-2000:]
    assert _calls(tmp_path) == [] and [b[1] for b in _calls(tmp_path, "build")] == ["R11"] and _calls(tmp_path, "build")[0][4] == "/nonexistent/m10p_dry_run_no_licence"
    assert [v[1] for v in _calls(tmp_path, "variant")] == ["R11"] and json.loads((out / "R11" / "BUILD_CHECK.json").read_text())["passed"]
    assert "mode=only(R11)" in st and "BUILD_CHECK_R11" in st and "DONE_ONLY:" in st and not (out / "STOP").exists()
    p = _run(tmp_path, pkg, {"BUILD_ONLY": "1"}, args=("--auth", "x", "--only", "R11"))
    assert p.returncode == 2 and "--auth together with" in p.stdout


def test_preflight_guards_refuse_ledger_cmd(tmp_path):
    import subprocess
    from test_m10p_batch3 import _clean_env
    pkg = _package(tmp_path)
    p = subprocess.run(["bash", str(pkg / "preflight.sh")], env=_clean_env({"PREFLIGHT_ONLY": "guards", "PY": sys.executable, "LEDGER_CMD": "python fake.py"}), capture_output=True, text=True)
    assert p.returncode == 1 and "unset before the formal run: LEDGER_CMD" in p.stdout


def test_batch_mode_without_the_new_arguments_is_unchanged(tmp_path):
    """the plain batch run of test_m10p_batch3 still passes through the same code: START line mode=batch, the STOP semantics unchanged."""
    pkg = _package(tmp_path)
    p = _run(tmp_path, pkg, {"FAKE_SLEEP_R1": "1", "FAKE_SLEEP_R2": "1"})
    st = (tmp_path / "out" / "STATUS.txt").read_text()
    assert p.returncode == 0 and ":mode=batch:" in st and "DONE:" in st and len(_calls(tmp_path)) == 11 and "ONLY_MODE" not in st
    assert S.summary(tmp_path / "out")["reposts"] == {} and (tmp_path / "out" / "BATCH3_SUMMARY.json").exists()
