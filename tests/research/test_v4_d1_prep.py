"""V4 D1 section 2 (decisions 214 items 8 / 9, 215 items 1 / 2 / 7; V4_D1_INSTRUCTION.md section 2): table folders named by switch set (out_<mode> = v4 main
set only, out_<mode>_<sha12> otherwise, V4_SWITCHES.json, the build-time check network meta = folder = configuration), the HVC basis switch (b | a = the I2
items of both bases), the unrounded EV factor, the v4 package runner / status copies (package COMMIT in RUN.json and the solve receipt; objective incl.
the constant and the LP value), the definition draft (PROPOSED). The v3.1 package files are unchanged. No solver, no network build."""
import argparse
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project")); sys.path.insert(0, str(Path(__file__).resolve().parent))
D1 = ROOT / "research/06_scope_redesign/p1_v4_d1_20261107"
V31_RUNNER = ROOT / "research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/run_batch4.sh"
V31_STATUS = ROOT / "research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/hpr_status.sh"
V4_RUNNER = D1 / "hpc_v4/run_batch4.sh"; V4_STATUS = D1 / "hpc_v4/hpr_status.sh"
DEF = D1 / "batch_def/BATCH_DEF_2920x3h_v4hpc.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------------------------------------------- item 1: folders by switch set
def test_out_names_by_switch_set_and_config_keys():
    from phase4_static import config
    from v4_common import V4_MAIN, V31, is_main_set, out_name, switch_sha, switches
    for m in ("ras", "iid"):
        s = dict(V4_MAIN, anchor_mode=m)
        assert is_main_set(s) and out_name(s) == f"out_{m}"
    for k, v in (("hvc_basis", "a"), ("missing_cost_rule", "zero"), ("id_paper_fuelwood", "purchased"), ("bio_cap_share", 1.0)):
        s = dict(V4_MAIN, anchor_mode="ras", **{k: v})
        assert not is_main_set(s) and out_name(s) == f"out_ras_{switch_sha(s)[:12]}"
    assert len({out_name(dict(V4_MAIN, anchor_mode="ras", hvc_basis=x)) for x in "ab"}) == 2
    assert not is_main_set(dict(V31, anchor_mode="ras"))
    cfg = config(ROOT, "integrated")
    assert cfg["research"]["biomass"]["missing_cost_rule"] is None and cfg["research"]["demand"]["v4"]["hvc_basis"] == "b"
    s = switches(cfg)
    assert s["enabled"] is False and s["missing_cost_rule"] == "zero" and s["hvc_basis"] == "b"   # null follows the switch set (v3.1)
    cfg["research"]["demand"]["v4"]["enabled"] = True
    s = switches(cfg)
    assert is_main_set(s) and s["missing_cost_rule"] == "proxy"                                   # v4 main
    cfg["research"]["biomass"]["missing_cost_rule"] = "zero"
    assert switches(cfg)["missing_cost_rule"] == "zero" and not is_main_set(switches(cfg))        # an explicit value overrides
    cfg["research"]["biomass"]["missing_cost_rule"] = "other"
    with pytest.raises(ValueError):
        switches(cfg)
    cfg["research"]["biomass"]["missing_cost_rule"] = None; cfg["research"]["demand"]["v4"]["hvc_basis"] = "c"
    with pytest.raises(ValueError):
        switches(cfg)


def test_v4_tables_and_network_meta_check(tmp_path):
    from phase4_static import config
    from v4_common import check_network_meta, out_name, switches, v4_tables
    cfg = config(ROOT, "integrated"); cfg["research"]["demand"]["v4"]["enabled"] = True
    t = v4_tables(cfg)
    assert t["dir"].name == "out_ras" and t["record"]["dir"] == "out_ras" and t["record"]["main_set"] is True
    rel = "research_inputs/industry_v4/out_ras"
    meta = {"v4_w08": dict(switch_sha256=t["record"]["switch_sha256"], tables_dir=rel, files=t["record"]["files"]),
            "s2_demand_ledger": {"industry": {"v4_w08": dict(tables_dir=rel, switch_sha256=t["record"]["switch_sha256"])}}}
    chk = check_network_meta(meta, cfg)
    assert chk["enabled"] and chk["main_set"] and chk["tables_dir"] == rel and chk["missing_cost_rule"] == "proxy"
    for path, val in ((("v4_w08", "switch_sha256"), "0" * 64), (("s2_demand_ledger", "industry", "v4_w08", "switch_sha256"), "1" * 64),
                      (("s2_demand_ledger", "industry", "v4_w08", "tables_dir"), "research_inputs/industry_v4/out_iid"), (("v4_w08", "tables_dir"), "x"),
                      (("v4_w08", "files"), {})):
        bad = json.loads(json.dumps(meta)); d = bad
        for k in path[:-1]:
            d = d[k]
        d[path[-1]] = val
        with pytest.raises(ValueError):
            check_network_meta(bad, cfg)
    with pytest.raises(ValueError):
        check_network_meta({}, cfg)                    # v4 enabled, no record
    cfg0 = config(ROOT, "integrated")
    assert check_network_meta({}, cfg0) == dict(enabled=False, missing_cost_rule="zero")
    with pytest.raises(ValueError):
        check_network_meta(meta, cfg0)                 # v4 disabled, record present
    # another switch set: its own folder; missing -> FileNotFoundError; a folder holding another set's record -> ValueError
    cfg["research"]["demand"]["v4"]["hvc_basis"] = "a"
    s = switches(cfg); name = out_name(s)
    assert name.startswith("out_ras_") and len(name) == len("out_ras_") + 12
    with pytest.raises(FileNotFoundError):
        v4_tables(cfg, tmp_path)
    fake = tmp_path / "research_inputs/industry_v4" / name; fake.mkdir(parents=True)
    (fake / "V4_SWITCHES.json").write_text(json.dumps(dict(switches={}, switch_sha256=t["record"]["switch_sha256"], dir=name, files={})))
    with pytest.raises(ValueError):
        v4_tables(cfg, tmp_path)


def test_committed_table_folders_carry_their_switch_sets():
    from v4_common import V4_DIR, out_name, sha256, switch_sha
    dirs = sorted(p for p in V4_DIR.glob("out_*") if p.is_dir())
    assert {"out_ras", "out_iid"} <= {p.name for p in dirs}
    for p in dirs:
        rec = json.loads((p / "V4_SWITCHES.json").read_text())
        assert rec["switch_sha256"] == switch_sha(rec["switches"]) and rec["dir"] == p.name == out_name(rec["switches"]), p.name
        for f, h in rec["files"].items():
            assert sha256(p / f) == h, (p.name, f)


# ---------------------------------------------------------------------------------------------------------------- item 2: HVC basis
def test_hvc_basis_items_equal_i2():
    import v4_products as P
    ref = pd.read_csv(D1 / "tables/D1_HVC_REF_I2.csv", keep_default_na=False)
    for basis in ("b", "a"):
        H = P.hvc_plants(basis); r = ref[ref.basis == basis].set_index("country")
        assert set(H) == set(r.index), basis
        for cc, h in H.items():
            x = r.loc[cc]
            for k in ("hvc19_t", "hvc50_base_t", "hvc50_new_t", "el19_per_t", "fuel19_per_t"):
                assert h[k] == pytest.approx(float(x[k]), rel=1e-12, abs=1e-9), (basis, cc, k)
            assert (h["row"] or "") == x.row and (json.dumps(h["fuel_split"]) if h["fuel_split"] else "") == x.fuel_split
            it = P.hvc_item(h)
            assert it["fuel19"] == pytest.approx(float(x.item_fuel19_mwh), rel=1e-12, abs=1e-9) and it["el19"] == pytest.approx(float(x.item_el19_mwh), rel=1e-12, abs=1e-9)
            for got, want in ((it["v2050"], json.loads(x.item_v2050_json)), (P.vec(h["vec"], h["hvc50_new_t"]) if h["hvc50_new_t"] > 0 else {}, json.loads(x.new_v2050_json))):
                g = {k: v for k, v in got.items() if v}
                assert set(g) == set(want) and all(g[k] == pytest.approx(want[k], rel=1e-12) for k in want), (basis, cc)
    assert sum(P.HVC_VEC_A.values()) == pytest.approx(6.103, abs=5e-4) and P.HVC_C1 == pytest.approx(3.269, abs=5e-4)
    with pytest.raises(ValueError):
        P.hvc_plants("c")


def test_hvc_basis_reaches_the_steps():
    import v4_industry as V
    import v4_products as P
    from v4_common import V4_MAIN
    I = V.Inputs()
    for basis in ("b", "a"):
        case = V.final_case(I, dict(V4_MAIN, anchor_mode="ras", hvc_basis=basis))
        H = P.hvc_plants(basis)
        hv = {cc: [x for x in items if x["name"] == "hvc"] for cc, items in case["products"].items()}
        for cc, h in H.items():
            want = P.hvc_item(h)
            if h["hvc19_t"] > 0 or h["hvc50_base_t"] > 0:
                assert len(hv[cc]) == 1 and hv[cc][0]["fuel19"] == want["fuel19"] and hv[cc][0]["v2050"] == want["v2050"], (basis, cc)
            if h["hvc50_new_t"] > 0:
                assert case["extra"][cc]["hvc_new_plants"] == P.vec(h["vec"], h["hvc50_new_t"]), (basis, cc)
    assert I.items_for(dict(hvc_basis="a"))["hvc"] != I.items_for(dict(hvc_basis="b"))["hvc"]


# ---------------------------------------------------------------------------------------------------------------- item 3: EV factor
def test_ev_factor_unrounded_from_the_registry():
    import v4_industry as V
    r = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id").value
    want = float(r["share_transport_ice_efficiency"]) / float(r["share_transport_electric_efficiency"]) * float(r["share_land_transport_electric_share_2050"])
    assert V.EV_FACTOR == want == 16.0712 / 53.19
    assert V.EV_FACTOR_W08 / V.EV_FACTOR - 1.0 == pytest.approx(9.9e-6, abs=5e-8)   # the W08 static-check difference


# ---------------------------------------------------------------------------------------------------------------- item 4: runner and status copies
def test_v31_package_files_unchanged():
    assert sha(V31_RUNNER) == "dc83d53a1f51e87d2007d296ec84ffb4d0538bb94eb6ad592416123fbeece264"
    assert sha(V31_STATUS) == "4fd0bd5c91f29fb3b990f129c138366eb9872d14f402d1c1c0dbf227821fd7e8"


@pytest.mark.parametrize("orig,copy", [(V31_RUNNER, V4_RUNNER), (V31_STATUS, V4_STATUS)])
def test_v4_copies_change_only_marked_lines(orig, copy):
    a = orig.read_text().splitlines(); b = copy.read_text().splitlines()
    hunks, cur = [], None
    for line in difflib.unified_diff(a, b, lineterm="", n=0):
        if line.startswith("@@"):
            cur = []; hunks.append(cur)
        elif cur is not None and line[:1] in "+-" and not line.startswith(("+++", "---")):
            cur.append(line)
    assert hunks
    for h in hunks:
        added = "\n".join(x[1:] for x in h if x.startswith("+"))
        assert "V4 D1" in added or "package_commit" in added or "PKG_COMMIT" in added or "PKGC" in added, h


def _v4_package(tmp_path):
    import test_b4p_batch4 as T
    pkg = T._package(tmp_path)
    shutil.copy(V4_RUNNER, pkg / "run_batch4.sh")
    (pkg / "COMMIT").write_text("0123456789abcdef0123456789abcdef01234567\n")
    w = tmp_path / "standin" / "scripts_project"
    for name in ("s2_solve.py", "b4_split_solve.py"):   # record the argument vector, then the B4P stand-in
        src = (w / name).read_text()
        (w / name).write_text(f"import json, os, sys\nopen({str(tmp_path / 'ARGV.jsonl')!r}, 'a').write(json.dumps([{name!r}, *sys.argv[1:]]) + '\\n')\n" + src)
    return pkg


def test_v4_runner_writes_the_package_commit(tmp_path):
    import test_b4p_batch4 as T
    pkg = _v4_package(tmp_path)
    p = T._run(tmp_path, pkg, dict(CORES="25"), args=("--only", "F1", "--auth", "synthetic test"))
    st = (tmp_path / "out" / "STATUS.txt").read_text()
    assert p.returncode == 0, st[-3000:]
    run = json.loads((tmp_path / "out" / "F1" / "RUN.json").read_text())
    assert run["package_commit"] == "0123456789abcdef0123456789abcdef01234567" and run["repo_commit"] is None
    calls = [json.loads(x) for x in (tmp_path / "ARGV.jsonl").read_text().splitlines()]
    s2 = [c for c in calls if c[0] == "s2_solve.py"]
    assert {c[c.index("--split-stage") + 1] for c in s2} == {"build", "assign"}
    assert all(c[c.index("--package-commit") + 1] == run["package_commit"] for c in s2)


def test_v4_runner_formal_run_refuses_without_matching_repo_commit(tmp_path):
    import test_b4p_batch4 as T
    pkg = _v4_package(tmp_path)   # COMMIT present, ./repo (here REPO = the repository) has no .package_commit; no ALLOW_UNREGISTERED -> formal
    q = subprocess.run(["bash", str(pkg / "run_batch4.sh"), "--only", "F1", "--auth", "synthetic test"],
                       env=T._clean_env(dict(REPO=str(ROOT), PY=sys.executable, RUN_DIR=str(tmp_path / "out2"), CORES="25")), capture_output=True, text=True, timeout=300)
    assert q.returncode == 2 and "REFUSED: package COMMIT" in q.stdout, q.stdout[-2000:]
    assert not (tmp_path / "out2" / "F1" / "RUN.json").exists()


def test_v4_status_shows_objective_with_constant_and_lp(tmp_path):
    d = tmp_path / "runs/batch6/F1"; (d / "split").mkdir(parents=True); (tmp_path / "hpc").mkdir()
    shutil.copy(V4_STATUS, tmp_path / "hpc/hpr_status.sh")
    (d / "RUN.json").write_text(json.dumps(dict(rid="F1", package_commit="0123456789abcdef")))
    (d / "SOLVE_RECEIPT.json").write_text(json.dumps(dict(scaling=dict(objective_constants=dict(total_eur=2370400000.0)), package_commit="0123456789abcdef")))
    (d / "split/SPLIT_SOLVE.json").write_text(json.dumps(dict(objective=302682094040.97, termination_condition="optimal")))
    run = lambda: subprocess.run(["bash", "hpc/hpr_status.sh", "runs/batch6"], cwd=tmp_path, env=dict(os.environ, PY=sys.executable), capture_output=True, text=True, timeout=120)   # noqa: E731
    out = run().stdout
    assert "objective incl. constant: 305,052,494,040.97 EUR [objective_lp + constant of the process-1 receipt (process 3 pending)]" in out, out
    assert "objective_lp: 302,682,094,040.97 EUR; constant: 2,370,400,000.00 EUR; package_commit RUN.json 01234567 / receipt 01234567" in out, out
    (d / "SOLVE_RECEIPT.json").write_text(json.dumps(dict(objective=305052496175.77, objective_lp=302682094040.97, scaling=dict(objective_constants=dict(total_eur=2370402134.80)))))
    out = run().stdout
    assert "objective incl. constant: 305,052,496,175.77 EUR [SOLVE_RECEIPT.json (process 3)]; objective_lp: 302,682,094,040.97 EUR" in out, out


def test_s2_solve_records_the_package_commit_only_when_given(tmp_path):
    import s2_solve
    for pc, out in (("0123456789abcdef", tmp_path / "with"), (None, tmp_path / "without")):
        a = argparse.Namespace(repo=ROOT, network=tmp_path / "missing_unsolved.nc", scenario="integrated", output=out, label="SMOKE_TEST_ONLY",
                               authorization="unit test: no network, no solve", solver="highs", truncate=0, package_commit=pc)
        with pytest.raises(Exception):
            s2_solve.main(a)   # fails on the missing network before any build or solve; the failure receipt is written
        rec = json.loads((out / "SOLVE_RECEIPT.json").read_text())
        assert "failure" in rec and rec.get("package_commit") == pc and (pc is not None or "package_commit" not in rec)


# ---------------------------------------------------------------------------------------------------------------- item 5: definition draft
def test_definition_draft_proposed():
    d = json.loads(DEF.read_text(encoding="utf-8"))
    assert d["limits_status"] == "PROPOSED" and d["run_dirs"] == dict(formal="runs/batch6", smoke56="runs/smoke56_v4", build_only="runs/build_only_f1_v4")
    L = d["limits"]
    assert L["time_limit_s"] == 259200 and L["build_timeout_s"] == 7200 and L["assign_timeout_s"] == 32400 and L["wall_margin_s"] == 7200
    assert d["runs"]["F1"]["iterations_reference"] == 350 and d["runs"]["F2"]["iterations_reference"] == 300 and set(d["runs"]) == {"F1", "F2"}
    w = 330 + L["build_timeout_s"] + (L["time_limit_s"] + L["wall_margin_s"]) + L["assign_timeout_s"] + 2 * 3900 + 1800
    assert w == 315930
    for rid in ("F1", "F2"):
        h, m, s = (int(x) for x in d["hpc_jobs"][rid]["walltime"].split(":"))
        assert h * 3600 + m * 60 + s >= w + 2 * 3600 and h == 96
    r = subprocess.run([sys.executable, "scripts_project/b4_batch4.py", "hpc-plan"], cwd=ROOT, env=dict(os.environ, BATCH_DEF=str(DEF), PYTHONHASHSEED="0"),
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    assert "STATUS|PROPOSED" in r.stdout and "RUNDIRS|runs/batch6|runs/smoke56_v4|runs/build_only_f1_v4" in r.stdout
