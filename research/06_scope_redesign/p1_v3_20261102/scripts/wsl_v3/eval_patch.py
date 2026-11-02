"""Supplement 01: smoke evaluation with the flat control and review decision 4; test helper cleaned."""
W = "/home/jin/wt_v3_20261102/"


def sub(path, pairs):
    s = open(path, encoding="utf-8", newline="").read()
    for a, b in pairs:
        assert s.count(a) == 1, (a[:70], s.count(a))
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8", newline="").write(s)


sub(W + "scripts_project/v3_smoke_eval.py", [
    ('''Criteria, both runs: Gurobi optimal (or decision 119 (a)(b) from PRECISION.json), ledger identity B16_LEDGER; B6 = objective(no_new_xb) - objective(integrated) > 0, SG marine fuel has a
source, no shedding or slack component in use. Reported in addition:''',
     '''Criteria, both runs: Gurobi optimal or decision 119 (a)(b) from PRECISION.json (instruction), C1 (a)(b)(c) with a GATES_V6 ACCEPTED label (review decision 4; termination status and the decision 120
field stay numerical information), ledger identity B16_LEDGER; B6 = objective(no_new_xb) - objective(integrated) > 0, SG marine fuel has a source, no shedding or slack component in use. With the
folders integrated_flat / no_new_xb_flat (supplement 01, control only, never an acceptance item): EV effect = flat - E2 on cost and on B6, and the cost difference to v2 left after it. Reported in addition:'''),
    ('SCEN = ["integrated", "no_new_xb"]\n', 'SCEN = ["integrated", "no_new_xb"]\nFLAT = {"integrated_flat": "integrated", "no_new_xb_flat": "no_new_xb"}\n'),
    ('''               v5_failed=sorted(k for k, v in v5.items() if isinstance(v, dict) and v.get("passed") is False))
    optimal = str(out["termination_condition"]) == "optimal"
    out["criterion_optimal_or_119ab"] = bool(optimal or (acc.get("a") and acc.get("b")))
''', '''               v5_failed=sorted(k for k, v in v5.items() if isinstance(v, dict) and v.get("passed") is False),
               b8_sectors_out=dict((k, r["rel"]) for k, r in ((v5.get("B8") or {}).get("sector_totals") or {}).items() if abs(r.get("rel") or 0.0) >= 1e-6))
    optimal = str(out["termination_condition"]) == "optimal"
    out["criterion_optimal_or_119ab"] = bool(optimal or (acc.get("a") and acc.get("b")))
    out["criterion_c1_abc_and_gates_v6"] = bool(acc.get("a") and acc.get("b") and acc.get("c") and str(out["v6_label"]).startswith("ACCEPTED"))
'''),
    ('''    res = {sc: one(a.run / sc, sc) for sc in SCEN}; nets, duals, bal = {}, [], []
    for sc in SCEN:
        f = a.run / sc / f"{sc}_SMOKE_TEST_ONLY_solved.nc"
        res[sc]["solved_network"] = f.exists()
        if not f.exists():
            continue
        n = nets[sc] = pypsa.Network(f)
        d = ship_duals(n, sc); b = liquid_balance(n, sc); duals.append(d); bal.append(b)
        nz = d[d.mu_upper_max_abs.fillna(0.0) > DUAL_TOL]
        res[sc]["ship_capacity_duals"] =''', '''    res = {sc: one(a.run / sc, sc) for sc in SCEN}; nets, duals, bal = {}, [], []
    res.update({k: one(a.run / k, sc) for k, sc in FLAT.items() if (a.run / k / "SOLVE_RECEIPT.json").exists()})
    for rid in [k for k in (*SCEN, *FLAT) if k in res]:
        sc = FLAT.get(rid, rid); f = a.run / rid / f"{sc}_SMOKE_TEST_ONLY_solved.nc"
        res[rid]["solved_network"] = f.exists()
        if not f.exists():
            continue
        n = nets[rid] = pypsa.Network(f)
        sc = rid; d = ship_duals(n, sc); b = liquid_balance(n, sc); duals.append(d); bal.append(b)
        nz = d[d.mu_upper_max_abs.fillna(0.0) > DUAL_TOL]
        res[sc]["ship_capacity_duals"] ='''),
    ('''    if len(nets) == 2:
''', '''    if "integrated" in nets and "no_new_xb" in nets:
'''),
    ('''    if a.v2_run:
        o = {sc: jl(a.v2_run / sc / "SOLVE_RECEIPT.json").get("objective") for sc in ("integrated", "disconnected")}
        res["v2_smoke_same_56_snapshots"] = dict(objective_eur=o, b6_bn_eur=(o["disconnected"] - o["integrated"]) / 1e9, note="profile formal_barrier_1e6_t16 and the fully separated reference: level comparison only, not the 365x24h figure of the prediction")
''', '''    o = None
    if a.v2_run:
        o = {sc: jl(a.v2_run / sc / "SOLVE_RECEIPT.json").get("objective") for sc in ("integrated", "disconnected")}
        res["v2_smoke_same_56_snapshots"] = dict(objective_eur=o, b6_bn_eur=(o["disconnected"] - o["integrated"]) / 1e9, note="profile formal_barrier_1e6_t16 and the fully separated reference: level comparison only, not the 365x24h figure of the prediction")
    fi, fr = (res.get(k, {}).get("objective_eur") for k in FLAT)
    if v is not None and fi is not None and fr is not None:
        res["flat_control"] = dict(b6_flat_bn=(fr - fi) / 1e9, ev_effect_cost_bn=dict(integrated=(fi - oi) / 1e9, no_new_xb=(fr - or_) / 1e9), ev_effect_b6_bn=((fr - fi) - v) / 1e9,
                                   note="EV effect = flat - E2; control runs only, not an acceptance item")
        if o:
            res["flat_control"].update(v3_e2_minus_v2_integrated_bn=(oi - o["integrated"]) / 1e9, v3_flat_minus_v2_integrated_bn=(fi - o["integrated"]) / 1e9, v3_flat_no_new_xb_minus_v2_disconnected_bn=(fr - o["disconnected"]) / 1e9,
                                       note_v2="v3 flat - v2 integrated: what is left after the EV effect, mainly the industry carriers and the other changes; the v2 disconnected run is another reference scenario")
'''),
    ('''    res["criteria"] = dict(optimal_or_119ab=all(res[s]["criterion_optimal_or_119ab"] for s in SCEN), b16_ledger=''',
     '''    res["criteria"] = dict(optimal_or_119ab=all(res[s]["criterion_optimal_or_119ab"] for s in SCEN), c1_abc_and_gates_v6=all(res[s]["criterion_c1_abc_and_gates_v6"] for s in SCEN), b16_ledger='''),
    ('''for sc in SCEN}), indent=1, default=str))
''', '''for sc in [k for k in (*SCEN, *FLAT) if k in res]}, flat_control=res.get("flat_control")), indent=1, default=str))
'''),
])
sub(W + "tests/research/test_v3_runners.py", [
    ('def _v3_package(pkg: Path, res: str, definition: str, commit: str, key: str) -> Path:\n', 'def _v3_package(pkg: Path, res: str, definition: str, commit: str) -> Path:\n'),
    ('''    pkg = TD._package(tmp_path); net = _v3_package(pkg, "365_24h", "BATCH_DEF_365x24h.json", TD.D.BUILD_COMMIT, "daily_network")
    r = TD._run(''', '''    pkg = TD._package(tmp_path); net = _v3_package(pkg, "365_24h", "BATCH_DEF_365x24h.json", TD.D.BUILD_COMMIT)
    r = TD._run('''),
    ('''net = _v3_package(pkg, "365_24h", "BATCH_DEF_365x24h.json", TD.D.BUILD_COMMIT, "daily_network"); _break_chain(net, "365_24h")''', '''net = _v3_package(pkg, "365_24h", "BATCH_DEF_365x24h.json", TD.D.BUILD_COMMIT); _break_chain(net, "365_24h")'''),
    ('''net = _v3_package(pkg, "365_24h", "BATCH_DEF_365x24h.json", TD.D.BUILD_COMMIT, "daily_network"); (net.parent''', '''net = _v3_package(pkg, "365_24h", "BATCH_DEF_365x24h.json", TD.D.BUILD_COMMIT); (net.parent'''),
    ('''    pkg = TB._package(tmp_path); net = _v3_package(pkg, "2920_3h", "BATCH_DEF_2920x3h.json", TB.B.BUILD_COMMIT, "network")
    r = TB._run(''', '''    pkg = TB._package(tmp_path); net = _v3_package(pkg, "2920_3h", "BATCH_DEF_2920x3h.json", TB.B.BUILD_COMMIT)
    r = TB._run('''),
    ('''net = _v3_package(pkg, "2920_3h", "BATCH_DEF_2920x3h.json", TB.B.BUILD_COMMIT, "network"); _break_chain(net, "2920_3h")''', '''net = _v3_package(pkg, "2920_3h", "BATCH_DEF_2920x3h.json", TB.B.BUILD_COMMIT); _break_chain(net, "2920_3h")'''),
])
print("patched")
