"""V3 supplement 02: SCREEN_CMD is a test hook like the others; tests of the five-run definition."""
W = "/home/jin/wt_v3_20261102/"; P = W + "research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/"


def sub(path, pairs):
    s = open(path, encoding="utf-8", newline="").read()
    for a, b in pairs:
        assert s.count(a) == 1, (a[:80], s.count(a))
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8", newline="").write(s)


sub(P + "run_dfx.sh", [("HOOKS_SET=$(for k in SOLVE_CMD VA_CMD C1_CMD M12_CMD M12A_CMD G6_CMD SUM_CMD PACK_CMD TRUNCATE $(compgen", "HOOKS_SET=$(for k in SOLVE_CMD VA_CMD C1_CMD M12_CMD M12A_CMD G6_CMD SUM_CMD PACK_CMD SCREEN_CMD TRUNCATE $(compgen")])
sub(P + "preflight_dfx.sh", [("for k in ALLOW_UNREGISTERED BUILD_ONLY POST_ONLY DRY TRUNCATE SOLVE_CMD VA_CMD C1_CMD M12_CMD M12A_CMD G6_CMD SUM_CMD PACK_CMD WALL_CAP_S", "for k in ALLOW_UNREGISTERED BUILD_ONLY POST_ONLY DRY TRUNCATE SOLVE_CMD VA_CMD C1_CMD M12_CMD M12A_CMD G6_CMD SUM_CMD PACK_CMD SCREEN_CMD WALL_CAP_S")])
sub(W + "tests/research/test_v3_runners.py", [
    ('''def _v3_package(pkg: Path, res: str, definition: str, commit: str) -> Path:
    """the v2 synthetic package turned into a v3 one: no disconnected file, a no_new_xb network with its variant receipt, the definition next to the runner"""
    nets = pkg / "networks"
    for f in nets.glob("disconnected_*"):
        f.unlink()
    d = json.loads((D3 / "batch_def" / definition).read_text(encoding="utf-8")); d["build_commit"] = commit
    (pkg / "BATCH_DEF.json").write_text(json.dumps(d))
''', '''def _v3_package(pkg: Path, res: str, definition: str, commit: str, five: bool = False) -> Path:
    """the v2 synthetic package turned into a v3 one: no disconnected file (kept with five), a no_new_xb network with its variant receipt, the definition next to the runner, cut to V1 and V2 unless five"""
    nets = pkg / "networks"
    d = json.loads((D3 / "batch_def" / definition).read_text(encoding="utf-8")); d["build_commit"] = commit
    if five:
        for b in ("bridge_160_162", "bridge_160_164"):
            f = nets / f"{b}_{res}_unsolved.nc"; f.write_bytes(f"{b} {res}".encode())
            r = json.loads((nets / "integrated_BUILD_RECEIPT.json").read_text()); r["daily_network"] = dict(sha256=sha(f), bytes=f.stat().st_size, snapshots=365); (nets / f"{b}_BUILD_RECEIPT.json").write_text(json.dumps(r))
    else:
        for f in nets.glob("disconnected_*"):
            f.unlink()
        keep = {"V1", "V2"}; d["runs"] = {k: v for k, v in d["runs"].items() if k in keep}
        d = {k: v for k, v in d.items() if k not in ("schedule", "time_limit_s", "bridge")}
    (pkg / "BATCH_DEF.json").write_text(json.dumps(d))
'''),
    ('''def test_definitions_are_the_registered_plan():
    plan = (D3 / "RUN_PLAN_V3.md").read_text(encoding="utf-8")
    for name, res, rids in (("BATCH_DEF_365x24h.json", "365_24h", ("V1", "V2")), ("BATCH_DEF_2920x3h.json", "2920_3h", ("F1", "F2"))):
        d = json.loads((D3 / "batch_def" / name).read_text(encoding="utf-8"))
        assert list(d["runs"]) == list(rids) and all(r["profile"] == "formal_barrier_1e6_t16" and r["costs"] == "integrated" and r["set"] == "" for r in d["runs"].values())
        assert [r["scenario"] for r in d["runs"].values()] == ["integrated", "no_new_xb"] and [r["base"] for r in d["runs"].values()] == [f"integrated_{res}", f"no_new_xb_{res}"]
        assert set(d["registered_sha"]) == set(d["registered_bytes"]) == {r["base"] + "_unsolved.nc" for r in d["runs"].values()}
        assert all(v in plan for v in d["registered_sha"].values()) and all(f"{v:,}" in plan for v in d["registered_bytes"].values()) and d["build_commit"].startswith("85095e7a")
''', '''def test_definitions_are_the_registered_plan():
    plan = (D3 / "RUN_PLAN_V3.md").read_text(encoding="utf-8")
    for name, res, rids in (("BATCH_DEF_365x24h.json", "365_24h", ("V1", "V2", "V3", "V4", "V5")), ("BATCH_DEF_2920x3h.json", "2920_3h", ("F1", "F2"))):
        d = json.loads((D3 / "batch_def" / name).read_text(encoding="utf-8")); r0 = list(d["runs"].values())
        assert list(d["runs"]) == list(rids) and all(r["profile"] == "formal_barrier_1e6_t16" and r["set"] == "" for r in r0)
        assert [r["scenario"] for r in r0[:2]] == ["integrated", "no_new_xb"] and [r["base"] for r in r0[:2]] == [f"integrated_{res}", f"no_new_xb_{res}"] and all(r["costs"] == "integrated" for r in r0[:2])
        assert set(d["registered_sha"]) == set(d["registered_bytes"]) == {r["base"] + "_unsolved.nc" for r in r0}
        assert all(v in plan for v in d["registered_sha"].values()) and all(f"{v:,}" in plan for v in d["registered_bytes"].values()) and d["build_commit"] in plan
    s = json.loads((D3 / "batch_def" / "BATCH_DEF_365x24h.json").read_text(encoding="utf-8"))
    assert [x[1:] for x in s["schedule"]] == [[["V1"], ["V2"]], [["V4"], ["V5"]], [["V3"], []]] and s["runs"]["V3"]["scenario"] == s["runs"]["V3"]["costs"] == "disconnected"
    assert [(s["runs"][k]["base"], s["runs"][k]["scenario"], s["runs"][k]["costs"]) for k in ("V4", "V5")] == [("bridge_160_162_365_24h", "integrated", "integrated"), ("bridge_160_164_365_24h", "integrated", "integrated")]
    assert set(s["time_limit_s"]) == set(s["runs"]) and s["bridge"]["steps"] == [["V4", "160-162"], ["V5", "160-164"], ["V1", "all"]]
'''),
    ('''def test_modules_read_the_definition_only_when_it_is_given():
''', '''def test_autodl_runner_five_screening_runs(tmp_path):
    pkg = TD._package(tmp_path); net = _v3_package(pkg, "365_24h", "BATCH_DEF_365x24h.json", TD.D.BUILD_COMMIT, five=True)
    r = TD._run(tmp_path, pkg, dict(FAKE_OBJ_V2="3e11", SCREEN_CMD=f"{sys.executable} -c pass"))
    assert r.returncode == 0, r.stdout + r.stderr
    st = TD._status(tmp_path); out = tmp_path / "out"
    assert "BASE_CHECK:all_equal" in st and "MISSING_INPUT" not in st and "SCREEN_TABLES:exit=0" in st and "DONE" in st and not (out / "STOP").exists()
    assert [c[1] for c in TD._calls(tmp_path)] == ["V1", "V2", "V4", "V5", "V3"]   # one lane below 33 cores: the two main runs first
    v4 = json.loads((out / "V4" / "RUN.json").read_text()); v3 = json.loads((out / "V3" / "RUN.json").read_text())
    assert v4["scenario"] == "integrated" and v4["base"] == "bridge_160_162_365_24h" and v4["registered_sha256"] == sha(pkg / "networks/bridge_160_162_365_24h_unsolved.nc") and v4["costs_table"].endswith("integrated_costs_active_research.csv")
    assert v3["scenario"] == "disconnected" and v3["costs_table"].endswith("disconnected_costs_active_research.csv") and json.loads((out / "V4" / "V6_ACCEPTANCE.json").read_text())["label"].startswith("ACCEPTED")
    s = json.loads((out / "DFX_SUMMARY.json").read_text())
    assert s["B6"]["runs"] == dict(integrated="V1", disconnected="V2") and len(s["runs"]) == 5 and [x["step"] for x in s["bridge"]["steps"]] == ["v2 -> 160-162", "160-162 -> 160-164", "160-164 -> all"] and s["bridge"]["stock_value_bn"] is not None


def test_autodl_runner_stops_without_a_bridge_receipt(tmp_path):
    pkg = TD._package(tmp_path); _v3_package(pkg, "365_24h", "BATCH_DEF_365x24h.json", TD.D.BUILD_COMMIT, five=True); (pkg / "networks/bridge_160_164_BUILD_RECEIPT.json").unlink()
    TD._run(tmp_path, pkg); assert "MISSING_INPUT:networks/bridge_160_164_BUILD_RECEIPT.json" in TD._status(tmp_path) and not TD._calls(tmp_path)


def test_modules_read_the_definition_only_when_it_is_given():
'''),
    ('''    a = run("dfx_batch.py", dict(env, BATCH_DEF=str(D3 / "batch_def/BATCH_DEF_365x24h.json"))); b = run("b4_batch4.py", dict(env, BATCH_DEF=str(D3 / "batch_def/BATCH_DEF_2920x3h.json")))
''', '''    a = run("dfx_batch.py", dict(env, BATCH_DEF=str(D3 / "batch_def/BATCH_DEF_365x24h.json"))); b = run("b4_batch4.py", dict(env, BATCH_DEF=str(D3 / "batch_def/BATCH_DEF_2920x3h.json")))
    assert len(a) == 5 and a[3] == "V4|integrated|bridge_160_162_365_24h||formal_barrier_1e6_t16|integrated"
'''),
])
print("patched")
