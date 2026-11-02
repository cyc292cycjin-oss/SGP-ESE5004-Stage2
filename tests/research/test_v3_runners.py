"""V3 supplement 01 (review decision 8): the 365x24h runner run_dfx.sh and the 2920x3h runner run_batch4.sh with a package BATCH_DEF.json, driven with the synthetic stand-ins of test_dfx_runner.py and
test_b4p_batch4.py (no solver, no model). The v2 behaviour without a definition stays covered by those two files. Never run beside a real local solve (the runners' process counts would see it)."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_b4p_batch4 as TB   # noqa: E402
import test_dfx_runner as TD   # noqa: E402

D3 = ROOT / "research/06_scope_redesign/p1_v3_20261102"
pytestmark = pytest.mark.skipif(shutil.which("setsid") is None or not Path("/usr/bin/time").exists(), reason="setsid / GNU time missing")
sha = TD.sha


def _v3_package(pkg: Path, res: str, definition: str, commit: str) -> Path:
    """the v2 synthetic package turned into a v3 one: no disconnected file, a no_new_xb network with its variant receipt, the definition next to the runner"""
    nets = pkg / "networks"
    for f in nets.glob("disconnected_*"):
        f.unlink()
    d = json.loads((D3 / "batch_def" / definition).read_text(encoding="utf-8")); d["build_commit"] = commit
    (pkg / "BATCH_DEF.json").write_text(json.dumps(d))
    base = nets / f"integrated_{res}_unsolved.nc"; net = nets / f"no_new_xb_{res}_unsolved.nc"; net.write_bytes(base.read_bytes() + b" no_new_xb")
    (nets / f"no_new_xb_{res}_VARIANT_RECEIPT.json").write_text(json.dumps(dict(status="M08A_VARIANT_BUILT", base=dict(sha256=sha(base), scenario="integrated"), output=dict(sha256=sha(net), bytes=net.stat().st_size), sets={"cross_border.stock_mode": "no_new_xb"})))
    return net


def _break_chain(net: Path, res: str):
    p = net.parent / f"no_new_xb_{res}_VARIANT_RECEIPT.json"; r = json.loads(p.read_text()); r["base"]["sha256"] = "0" * 64; p.write_text(json.dumps(r))


def test_definitions_are_the_registered_plan():
    plan = (D3 / "RUN_PLAN_V3.md").read_text(encoding="utf-8")
    for name, res, rids in (("BATCH_DEF_365x24h.json", "365_24h", ("V1", "V2")), ("BATCH_DEF_2920x3h.json", "2920_3h", ("F1", "F2"))):
        d = json.loads((D3 / "batch_def" / name).read_text(encoding="utf-8"))
        assert list(d["runs"]) == list(rids) and all(r["profile"] == "formal_barrier_1e6_t16" and r["costs"] == "integrated" and r["set"] == "" for r in d["runs"].values())
        assert [r["scenario"] for r in d["runs"].values()] == ["integrated", "no_new_xb"] and [r["base"] for r in d["runs"].values()] == [f"integrated_{res}", f"no_new_xb_{res}"]
        assert set(d["registered_sha"]) == set(d["registered_bytes"]) == {r["base"] + "_unsolved.nc" for r in d["runs"].values()}
        assert all(v in plan for v in d["registered_sha"].values()) and all(f"{v:,}" in plan for v in d["registered_bytes"].values()) and d["build_commit"].startswith("85095e7a")


def test_modules_read_the_definition_only_when_it_is_given():
    env = {k: v for k, v in os.environ.items() if k != "BATCH_DEF"}
    run = lambda script, e: subprocess.run([sys.executable, str(ROOT / "scripts_project" / script), "runtable"], env=e, capture_output=True, text=True, check=True).stdout.split()
    assert run("dfx_batch.py", env)[1].startswith("V2|disconnected|disconnected_365_24h") and run("b4_batch4.py", env)[1].startswith("F2|disconnected|disconnected_2920_3h")
    a = run("dfx_batch.py", dict(env, BATCH_DEF=str(D3 / "batch_def/BATCH_DEF_365x24h.json"))); b = run("b4_batch4.py", dict(env, BATCH_DEF=str(D3 / "batch_def/BATCH_DEF_2920x3h.json")))
    assert a[1] == "V2|no_new_xb|no_new_xb_365_24h||formal_barrier_1e6_t16|integrated" and b[1] == "F2|no_new_xb|no_new_xb_2920_3h||formal_barrier_1e6_t16|integrated"


def test_autodl_runner_runs_no_new_xb_as_the_reference(tmp_path):
    pkg = TD._package(tmp_path); net = _v3_package(pkg, "365_24h", "BATCH_DEF_365x24h.json", TD.D.BUILD_COMMIT)
    r = TD._run(tmp_path, pkg, dict(FAKE_OBJ_V2="3e11"))
    assert r.returncode == 0, r.stdout + r.stderr
    st = TD._status(tmp_path); out = tmp_path / "out"
    assert "BASE_CHECK:all_equal" in st and "MISSING_INPUT" not in st and not (out / "STOP").exists()
    run = json.loads((out / "V2" / "RUN.json").read_text())
    assert run["scenario"] == "no_new_xb" and run["base"] == "no_new_xb_365_24h" and run["profile"] == "formal_barrier_1e6_t16" and run["costs_table"].endswith("integrated_costs_active_research.csv")
    assert run["registered_sha256"] == sha(net) == run["network_sha256"]
    acc = json.loads((out / "V2" / "V6_ACCEPTANCE.json").read_text())
    assert acc["G2"]["G2_1"]["registered_sha256"] == sha(net) and acc["label"].startswith("ACCEPTED")   # the variant is registered through its own receipt
    s = json.loads((out / "DFX_SUMMARY.json").read_text())
    assert s["B6"]["b6_bn"] == pytest.approx(100.0) and all(v["state"] == "ended" for v in s["runs"].values())


def test_autodl_runner_stops_on_a_variant_of_another_network(tmp_path):
    pkg = TD._package(tmp_path); net = _v3_package(pkg, "365_24h", "BATCH_DEF_365x24h.json", TD.D.BUILD_COMMIT); _break_chain(net, "365_24h")
    TD._run(tmp_path, pkg); assert "BASE_NETWORK_SHA256" in TD._status(tmp_path) and not TD._calls(tmp_path)


def test_autodl_runner_stops_without_the_variant_receipt(tmp_path):
    pkg = TD._package(tmp_path); net = _v3_package(pkg, "365_24h", "BATCH_DEF_365x24h.json", TD.D.BUILD_COMMIT); (net.parent / "no_new_xb_365_24h_VARIANT_RECEIPT.json").unlink()
    TD._run(tmp_path, pkg); assert "MISSING_INPUT:networks/no_new_xb_365_24h_VARIANT_RECEIPT.json" in TD._status(tmp_path) and not TD._calls(tmp_path)


def test_hpc_runner_runs_no_new_xb_as_the_reference(tmp_path):
    pkg = TB._package(tmp_path); net = _v3_package(pkg, "2920_3h", "BATCH_DEF_2920x3h.json", TB.B.BUILD_COMMIT)
    r = TB._run(tmp_path, pkg, dict(FAKE_OBJ_F2="3e11", CORES="72"))
    assert r.returncode == 0, r.stdout + r.stderr
    out = tmp_path / "out"; st = (out / "STATUS.txt").read_text()
    assert "BASE_CHECK:all_equal" in st and not (out / "STOP").exists()
    run = json.loads((out / "F2" / "RUN.json").read_text())
    assert run["scenario"] == "no_new_xb" and run["base"] == "no_new_xb_2920_3h" and run["registered_sha256"] == sha(net) == run["network_sha256"] and run["costs_table"].endswith("integrated_costs_active_research.csv")
    assert json.loads((out / "F2" / "V6_ACCEPTANCE.json").read_text())["G2"]["G2_1"]["registered_sha256"] == sha(net)
    assert json.loads((out / "BATCH4_SUMMARY.json").read_text())["B6"]["b6_bn"] == pytest.approx(100.0)


def test_hpc_runner_stops_on_a_variant_of_another_network(tmp_path):
    pkg = TB._package(tmp_path); net = _v3_package(pkg, "2920_3h", "BATCH_DEF_2920x3h.json", TB.B.BUILD_COMMIT); _break_chain(net, "2920_3h")
    TB._run(tmp_path, pkg); assert "BASE_NETWORK_SHA256" in (tmp_path / "out" / "STATUS.txt").read_text() and not TB._calls(tmp_path)
