"""B4P A3.2 (M10S1 execution deviation, 2026-10-26): run_batch3.sh resolves --into, --use <rid>=<dir> and --arrays given RELATIVE to the caller's
directory before any step runs under cd "$REPO" (the first S1 chain on the instance wrote a relative --into inside repo/ and stopped at the
violation analysis; RUN_PLAN 11.2 wrote the commands with relative paths). Driven with the synthetic stand-ins of test_m10p_batch3 /
test_m10r_s1_modes (no solver, no model): the halted third-batch situation, then --repost R9 (with --arrays) and --summary-s1 (with --use) once with
full paths and once with relative paths from a "wrong" working directory (a sub-folder of tmp_path that is neither the package nor the repo).
The relative run must land in the folder meant by the caller, link the arrays of the run folder, and agree with the full-path run step by step."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_m10p_batch3 import FAKE, ROOT, _calls, _clean_env, sha  # noqa: E402
from test_m10r_s1_modes import _halted_batch, _snapshot  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("setsid") is None or not Path("/usr/bin/time").exists(), reason="setsid / GNU time missing")
F = f"{sys.executable} {FAKE}"
VOLATILE = ("utc", "time", "seconds", "epoch", "written", "created")


def _run_at(tmp: Path, pkg: Path, cwd: Path, extra=None, args=(), timeout=900):
    """test_m10p_batch3._run with an explicit working directory (the caller's directory of the relative paths)."""
    f = f"{sys.executable} {FAKE}"
    env = _clean_env(dict(REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(tmp / "out"), FAKE_OUT=str(tmp / "out"), ALLOW_UNREGISTERED="1", LICENCE_GAP_S="1",
                          GRACE_S="1", MONITOR_S="1", CORES="25", GRB_LICENSE_FILE=str(tmp / "lic"), SOLVE_CMD=f"{sys.executable} {tmp / 'standin' / 'scripts_project' / 's2_solve.py'}",
                          VA_CMD=f"{f} va", C1_CMD=f"{f} c1", M12_CMD=f"{f} m12", M12A_CMD=f"{f} m12a", VAR_CMD=f"{f} variants", FAKE_SLEEP="0.2"))
    env.update(extra or {})
    return subprocess.run(["bash", str(pkg / "run_batch3.sh"), *args], env=env, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)


def _steps(status: Path) -> list:
    """the step sequence of a STATUS.txt: the token before the first ':' of every line (START, REPOST_R9, LEDGER_R9, ..., DONE_REPOST)."""
    return [line.split(":", 1)[0] for line in status.read_text().splitlines() if line.strip()]


def _normalised(obj, subs):
    """JSON content without volatile keys; folder names of the two runs replaced by one placeholder so that only the content is compared."""
    if isinstance(obj, dict):
        return {k: _normalised(v, subs) for k, v in obj.items() if not any(x in k.lower() for x in VOLATILE)}
    if isinstance(obj, list):
        return [_normalised(v, subs) for v in obj]
    if isinstance(obj, str):
        for a in subs:
            obj = obj.replace(a, "<RUN>")
        return obj
    return obj


def test_relative_into_use_and_arrays_resolve_to_the_callers_directory(tmp_path):
    pkg, out = _halted_batch(tmp_path); n0 = len(_calls(tmp_path)); r9_before = _snapshot(out / "R9")
    wrong = tmp_path / "elsewhere" / "deeper"; wrong.mkdir(parents=True)      # the caller's directory: neither the package nor the repo
    abs_into, rel_into = tmp_path / "s1_abs", tmp_path / "s1_rel"
    env_r = {"LEDGER_CMD": f"{F} ledger", "GRB_LICENSE_FILE": ""}
    # ---- --repost R9 --into --arrays: full paths (reference) and relative paths from the wrong directory
    p = _run_at(tmp_path, pkg, wrong, env_r, ("--repost", "R9", "--into", str(abs_into), "--arrays", str(out / "R9")))
    assert p.returncode == 0, p.stdout[-800:] + (abs_into / "STATUS.txt").read_text()[-1500:]
    p = _run_at(tmp_path, pkg, wrong, env_r, ("--repost", "R9", "--into", "../../s1_rel", "--arrays", "../../out/R9"))
    assert p.returncode == 0, p.stdout[-800:] + ((rel_into / "STATUS.txt").read_text()[-1500:] if (rel_into / "STATUS.txt").exists() else " (no STATUS in the relative folder)")
    assert rel_into.is_dir() and (rel_into / "R9" / "REPOST.json").exists(), "the relative --into must resolve against the caller's directory"
    for stray in (wrong / "s1_rel", wrong / ".." / ".." / "repo", ROOT / "s1_rel", ROOT.parent / "s1_rel", ROOT.parent.parent / "s1_rel"):
        assert not stray.exists(), f"stray folder {stray}"
    assert len(_calls(tmp_path)) == n0                                                                     # no solve in either repost
    start = (rel_into / "STATUS.txt").read_text().splitlines()[0]
    assert f":into={rel_into}:" in start and f":arrays={(out / 'R9')}" in start                           # the resolved full paths are recorded
    assert (rel_into / "R9" / "lp").is_symlink() and (rel_into / "R9" / "lp").resolve() == (out / "R9" / "lp").resolve()      # --arrays resolved: the links point at the run folder
    assert (rel_into / "R9" / "solution").resolve() == (out / "R9" / "solution").resolve()
    assert _steps(rel_into / "STATUS.txt") == _steps(abs_into / "STATUS.txt")
    subs = (str(abs_into), str(rel_into))
    for f in ("R9/REPOST.json", "R9/REPOST_CHECK.json", "R9/V6_ACCEPTANCE.json", "R9/STOP_CLASS.json", "R9/PRECISION.json", "R9/V5_GATES.json", "R9/LEDGER_IDENTITY.json"):
        a, b = json.loads((abs_into / f).read_text()), json.loads((rel_into / f).read_text())
        assert _normalised(a, subs) == _normalised(b, subs), f
    r = json.loads((rel_into / "R9" / "REPOST.json").read_text())
    assert r["rid"] == "R9" and r["label_before"] == "NOT_ACCEPTED" and r["repost_dir"] == str(rel_into / "R9") and r["arrays_dir"] == str(out / "R9")
    assert json.loads((rel_into / "R9" / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2"
    assert sorted(p.name for p in (rel_into / "export" / "R9").iterdir()) == sorted(p.name for p in (abs_into / "export" / "R9").iterdir())
    assert len(list(rel_into.glob("results_light_repost_R9_*.tar.gz"))) == 1
    # ---- --summary-s1 --into --use: full paths and relative paths from the wrong directory
    p = _run_at(tmp_path, pkg, wrong, {"GRB_LICENSE_FILE": ""}, ("--summary-s1", "--into", str(abs_into), "--use", f"R9={abs_into / 'R9'}"))
    assert p.returncode == 0, p.stdout[-800:] + (abs_into / "STATUS.txt").read_text()[-1000:]
    p = _run_at(tmp_path, pkg, wrong, {"GRB_LICENSE_FILE": ""}, ("--summary-s1", "--into", "../../s1_rel", "--use", "R9=../../s1_rel/R9"))
    assert p.returncode == 0, p.stdout[-800:] + (rel_into / "STATUS.txt").read_text()[-1000:]
    assert (rel_into / "batch_s1" / "BATCH3_SUMMARY_S1.json").exists() and not (wrong / "s1_rel").exists() and not (ROOT / "s1_rel").exists()
    line = [x for x in (rel_into / "STATUS.txt").read_text().splitlines() if x.startswith("START:") and "mode=summary_s1" in x][-1]
    assert f":use=R9={rel_into / 'R9'}" in line
    a = json.loads((abs_into / "batch_s1" / "BATCH3_SUMMARY_S1.json").read_text()); b = json.loads((rel_into / "batch_s1" / "BATCH3_SUMMARY_S1.json").read_text())
    assert _normalised(a, subs) == _normalised(b, subs)
    sens = {(x["new"], x["base"]): x for x in b["sensitivity"]}
    assert sens[("R9", "R2")]["usable"] is True and sens[("R9", "R2")]["reposted"] == ["R9"] and b["reposts"]["R9"]["label_after"] == "ACCEPTED_LAYER2"
    assert len(_calls(tmp_path)) == n0 and _snapshot(out / "R9") == r9_before                             # no solve; the original run folder untouched by either run


def test_absolute_paths_and_refusals_unchanged(tmp_path):
    """full paths behave as before (test_m10r_s1_modes); the refusals of --use / --arrays outside their modes still fire with relative values."""
    pkg, out = _halted_batch(tmp_path); into = tmp_path / "s1"; wrong = tmp_path / "w"; wrong.mkdir()
    for args, text in ((("--use", "R9=x"), "--use <rid>=<dir> belongs to --summary-s1"), (("--arrays", "x"), "--arrays <dir> belongs to --repost"),
                       (("--summary-s1", "--into", "s1", "--use", "R9=nowhere"), "--use R9=")):
        p = _run_at(tmp_path, pkg, wrong, {"GRB_LICENSE_FILE": ""}, args)
        assert p.returncode == 2 and text in p.stdout, (args, p.stdout[-300:])
    assert not (wrong / "s1").exists() and not (tmp_path / "s1").exists()                                   # refused before anything is written
    p = _run_at(tmp_path, pkg, wrong, {"LEDGER_CMD": f"{F} ledger", "GRB_LICENSE_FILE": ""}, ("--repost", "R9", "--into", str(into)))
    assert p.returncode == 0 and json.loads((into / "R9" / "REPOST.json").read_text())["repost_dir"] == str(into / "R9")
    p = _run_at(tmp_path, pkg, wrong, {"LEDGER_CMD": f"{F} ledger", "GRB_LICENSE_FILE": ""}, ("--repost", "R9", "--into", "../s1"))
    assert p.returncode == 2 and "exists - every repost goes to a new folder" in p.stdout                   # the relative path names the same (existing) folder
