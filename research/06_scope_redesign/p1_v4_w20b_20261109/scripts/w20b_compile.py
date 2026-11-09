"""V4 W20b section 5: compile CORE_CHECK_V4_56_BUNKER.csv, CHECKPOINTS.csv and EVIDENCE.json from the solve folders, the per-run verdicts and the registered
allocations (evidence/W20B_XS_PRE.json). Read only, no solver.

    PYTHONHASHSEED=0 python w20b_compile.py --solves <results_project/v4w20b/solves> --work <work/p1_v4_w20b_20261109> --repo /home/jin/wt_v4_w20b

Margins c(S) - x(S) (positive: the coalition pays more on its own than its Owen share - the core condition holds strictly). Reading quantities:
Delta_S = c^m(S) - c_W20(S) (the coalition's incremental cost of its own bunker), D_S = x_B(S) - Delta_S (EXACT: margin^m(S) = margin_W20(S) - D_S);
the bunker payment of S at the coalition's own nodal prices (solved coalition network: marginal price x load x objective weight), next to x_B(S) at the
integrated prices; LOO marginal-contribution reading x_i^m - [c(N) - c^m(N - i)] with c(N) = integrated objective (equal to the core margin up to the
-4,519 EUR dual-form residual); R0: D = c(N \\ B) - x(N \\ B) and the bunker's payment above its incremental cost x_B - [c(N) - c(N \\ B)].
"""
import argparse
import csv
import json
import logging
import re
import sys
from pathlib import Path

FLOOR = 1e7


def barrier(R):
    ln = " ".join(((R.get("gurobi_log_stats") or {}).get("lines") or {}).get("barrier") or [])
    m = re.search(r"in (\d+) iterations and ([0-9.]+) seconds", ln)
    return (int(m.group(1)), float(m.group(2))) if m else (None, None)


def verdict(margin, thr):
    return "strict" if margin >= 0 else ("within_tolerance" if -margin <= thr else "VIOLATION")


def bunker_at_coalition_prices(solved: Path) -> dict:
    import pypsa
    n = pypsa.Network(str(solved))
    bc = n.buses.country.astype(str); loc = n.buses.location.astype(str)
    term = [b for b in n.buses.index[bc == "ASEAN"] if b != "co2 bunkers ASEAN"]
    ld = n.loads[n.loads.bus.astype(str).isin(term)]
    if not len(ld):
        return dict(loads=0, payment_eur=0.0, by_country={})
    w = n.snapshot_weightings.objective; p = n.loads_t.p[ld.index]; price = n.buses_t.marginal_price
    by = {}
    for x in ld.index:
        b = str(ld.at[x, "bus"]); c = str(bc[loc[b]]); by[c] = by.get(c, 0.0) + float((price[b] * p[x] * w).sum())
    wg = n.snapshot_weightings.generators
    e = float(p.mul(wg, axis=0).sum().sum())
    return dict(loads=int(len(ld)), energy_twh=e / 1e6, payment_eur=float(sum(by.values())), by_country=by, avg_price_eur_per_mwh=float(sum(by.values())) / e if e else None)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--solves", type=Path, required=True); ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--repo", type=Path, default=Path("/home/jin/wt_v4_w20b"))
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project")); logging.disable(logging.WARNING)
    from v4_coalition import w20b_runs
    XS = json.loads((a.work / "evidence/W20B_XS_PRE.json").read_text())
    AL = json.loads((a.work / "evidence/W20B_BUNKER_PORT_ALLOCATION.json").read_text())
    cN = float(XS["identity"]["objective_eur"]); xB = float(XS["identity"]["x_B_eur"]); xNB = float(XS["identity"]["x_N_minus_B_eur"])
    st = (a.solves / "STATUS.txt").read_text().splitlines() if (a.solves / "STATUS.txt").exists() else []
    wall, gaps, packs = {}, {}, {}
    for ln in st:
        m = re.match(r"END_(\w+):[^:]+:[^:]+:[^:]+:exit=(-?\d+):(\d+)s:", ln)
        if m:
            wall[m.group(1)] = (int(m.group(2)), int(m.group(3)))
        m = re.match(r"GAP_(\w+):[^:]+:[^:]+:[^:]+:(\d+)s", ln)
        if m:
            gaps[m.group(1)] = int(m.group(2))
        m = re.match(r"PACK_(\w+):[^:]+:[^:]+:[^:]+:files=(\d+):ok=(\d+):bad=(\d+):bytes_before=(\d+):dir_bytes_after=(\d+)", ln)
        if m:
            packs[m.group(1)] = dict(files=int(m.group(2)), ok=int(m.group(3)), bad=int(m.group(4)), bytes_before=int(m.group(5)), dir_bytes_after=int(m.group(6)))
    rows, cps = [], []
    for name, spec in w20b_runs().items():
        X = XS["runs"][name]; d = a.solves / name; rp = d / "SOLVE_RECEIPT.json"
        r = dict(run=name, network=X["network"], include_bunker=X["include_bunker"], n_members=X["n_members"], members=X["members"], network_sha256=X["network_sha256"],
                 x_dual_eur=X["x_dual_eur"], x_bunker_part_eur=X["x_bunker_part_eur"], x_dual_alpha_min_eur=X["x_dual_alpha_min_eur"], x_dual_alpha_max_eur=X["x_dual_alpha_max_eur"],
                 x_market_eur=X["x_market_eur"], d8_addback_eur=X["d8_addback_eur"], owen_benefit_merged_eur=X["owen_benefit_merged_eur"])
        if not rp.exists():
            r.update(termination="not_run"); rows.append(r); continue
        R = json.loads(rp.read_text()); it, bs = barrier(R)
        P = json.loads((d / "PRECISION.json").read_text()) if (d / "PRECISION.json").exists() else {}
        pa = P.get("a_total_cost") or {}; g = P.get("grade") if isinstance(P.get("grade"), dict) else {}
        BA = json.loads((d / "BUNKER_ACCOUNT.json").read_text()) if (d / "BUNKER_ACCOUNT.json").exists() else None
        gates = R.get("gates") or {}
        r.update(termination=R.get("termination_condition"), status=R.get("status"), gurobi_result=" ".join(((R.get("gurobi_log_stats") or {}).get("lines") or {}).get("result") or []),
                 barrier_iterations=it, barrier_seconds=bs, solve_seconds=R.get("solve_seconds"), wall_seconds=(wall.get(name) or (None, None))[1], exit_code=(wall.get(name) or (None, None))[0],
                 gap_before_s=gaps.get(name), peak_rss_gib=(R.get("peak_rss_bytes") or 0) / 2**30, lp_cols=(R.get("lp") or {}).get("num_col"), lp_rows=(R.get("lp") or {}).get("num_row"),
                 post_solve_errors=" ".join(e.get("step", "") for e in R.get("post_solve_errors") or []),
                 c1_grade=g.get("grade", P.get("grade") if not isinstance(P.get("grade"), dict) else None), c1_a=g.get("a"), c1_b=g.get("b"), c1_c=g.get("c"),
                 c1_primal_minus_dual_eur=((pa.get("returned_iteration_by_log") or pa.get("last_iteration") or {}).get("difference_eur")),
                 gate_b1_bunkers=(BA.get("passed") if BA is not None else (gates.get("B1_BUNKERS") if isinstance(gates.get("B1_BUNKERS"), bool) else None)),
                 receipt_gates_false="|".join(sorted(k for k, v in gates.items() if v is False)),
                 bunker_final_level_t=(BA or {}).get("final_level_tco2"), bunker_gate_tolerance_t=(BA or {}).get("tolerance_t"),
                 pack_ok=(packs.get(name) or {}).get("ok"), pack_bad=(packs.get(name) or {}).get("bad"), pack_bytes_before=(packs.get(name) or {}).get("bytes_before"),
                 dir_bytes_after=(packs.get(name) or {}).get("dir_bytes_after"))
        if R.get("status") == "ok" and R.get("objective") is not None:
            c = float(R["objective"]); thr = max(0.01 * c, FLOOR)
            mg = c - X["x_dual_eur"]; mga = c - X["x_dual_alpha_max_eur"]; mm = c - X["x_market_eur"]
            B = float(X["owen_benefit_merged_eur"])
            r.update(c_eur=c, objective_lp_eur=R.get("objective_lp"), margin_dual_eur=mg, threshold_eur=thr, violation_dual_eur=max(0.0, -mg), verdict=verdict(mg, thr),
                     margin_dual_alpha_worst_eur=mga, verdict_alpha_worst=verdict(mga, thr), margin_market_eur=mm, verdict_market=verdict(mm, thr),
                     c_d8_eur=c + X["d8_addback_eur"], margin_dual_d8_eur=c + X["d8_addback_eur"] - X["x_dual_eur"], margin_relative=mg / c,
                     margin_over_benefit=(mg / B if B else None))
            if X.get("w20_c_eur") is not None:
                dS = c - float(X["w20_c_eur"])
                r.update(w20_c_eur=float(X["w20_c_eur"]), w20_margin_eur=float(X["w20_margin_eur"]), bunker_increment_eur=dS,
                         D_S_eur=float(X["x_bunker_part_eur"]) - dS, margin_change_vs_w20_eur=mg - float(X["w20_margin_eur"]))
                sol = d / "integrated_SMOKE_TEST_ONLY_solved.nc"
                if sol.exists() and spec["include_bunker"] == "ports":
                    bp = bunker_at_coalition_prices(sol)
                    r.update(bunker_payment_coalition_prices_eur=bp["payment_eur"], bunker_avg_price_coalition_eur_per_mwh=bp["avg_price_eur_per_mwh"],
                             bunker_avg_price_integrated_eur_per_mwh=(float(X["x_bunker_part_eur"]) / (bp["energy_twh"] * 1e6) if bp.get("energy_twh") else None),
                             bunker_energy_twh=bp.get("energy_twh"))
            if name == "R0":
                r.update(D_eur=mg, bunker_incremental_cost_eur=cN - c, bunker_payment_above_incremental_cost_eur=xB - (cN - c),
                         bunker_pays_at_least_incremental_cost=bool(xB - (cN - c) >= 0))
            if X.get("loo_country"):
                i = X["loo_country"]; xi = float(X["x_i_merged_eur"]); bi = float(X["b_i_merged_eur"])
                r.update(loo_country=i, x_i_merged_eur=xi, b_i_merged_eur=bi, c_N_eur=cN, c_N_minus_c_eur=cN - c, margin_marginal_contribution_eur=xi - (cN - c),
                         margin_over_b_i_merged=(mg / bi if bi else None))
        rows.append(r)
        cps.append(dict(step="W20b-3", item=f"solve {name}", result=r.get("verdict", r.get("termination")),
                        detail=f"{r.get('termination')} c={r.get('c_eur', float('nan'))/1e9:.4f} bn margin={r.get('margin_dual_eur', float('nan'))/1e9:+.4f} bn pack ok={r.get('pack_ok')} bad={r.get('pack_bad')}",
                        file=f"results_project/v4w20b/solves/{name}/SOLVE_RECEIPT.json"))
    cols = []
    for r in rows:
        cols += [k for k in r if k not in cols]
    with open(a.work / "CORE_CHECK_V4_56_BUNKER.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})
    done = [r for r in rows if "c_eur" in r]; merged = [r for r in done if r["include_bunker"] == "ports"]
    summ = dict(solves=len([r for r in rows if r.get("termination") not in (None, "not_run")]), evaluated=len(done),
                optimal=len([r for r in rows if r.get("termination") == "optimal"]), strict=len([r for r in done if r["verdict"] == "strict"]),
                within_tolerance=[r["run"] for r in done if r["verdict"] == "within_tolerance"], violations=[r["run"] for r in done if r["verdict"] == "VIOLATION"],
                R0=({k: v for k, v in rows[0].items() if k in ("c_eur", "D_eur", "verdict", "bunker_payment_above_incremental_cost_eur", "bunker_incremental_cost_eur")} if rows and "c_eur" in rows[0] else None),
                merged_min_margin=min(((r["margin_dual_eur"], r["run"]) for r in merged), default=None),
                merged_max_margin=max(((r["margin_dual_eur"], r["run"]) for r in merged), default=None),
                merged_min_margin_market=min(((r["margin_market_eur"], r["run"]) for r in merged), default=None),
                merged_min_relative_margin=min(((r["margin_relative"], r["run"]) for r in merged), default=None),
                market_violations=[r["run"] for r in done if r["verdict_market"] == "VIOLATION"], market_strict=len([r for r in done if r["verdict_market"] == "strict"]),
                alpha_worst_violations=[r["run"] for r in done if r["verdict_alpha_worst"] == "VIOLATION"],
                solve_seconds_total=sum(float(r.get("solve_seconds") or 0) for r in rows), wall_seconds_total=sum(float(r.get("wall_seconds") or 0) for r in rows),
                peak_rss_gib_max=max((r.get("peak_rss_gib") or 0) for r in rows), pack_bad_total=sum(int(r.get("pack_bad") or 0) for r in rows),
                b1_bunkers_failed=[r["run"] for r in rows if r.get("gate_b1_bunkers") is False])
    ev = dict(step="V4 W20b", decision="230", instruction=dict(file="V4_W20B_INSTRUCTION.md", sha256="25f1db61db5e59914656ea24478311b3371f3b37e3b51dc35ff73f814b953e14"),
              model="claude-opus-5-5", effort="xhigh", branch="asean/v4-w20b-20261109", start_commit="b62ef3c020a2514df4db4c4809809f88ef36e475",
              tool_commit="06c1ed1d", networks_commit="98bdff71", registration_commit="bbff7550306e5707da68035d860a25ad73f7c76a",
              base_network=dict(file="hpc_package_v4/networks/integrated_2920_3h_unsolved.nc", sha256="86f6d6a0fce2f0e04d12ee7993aee885256fcaadadaeeca308414017738c801d"),
              allocation=dict(file="evidence/W20B_BUNKER_PORT_ALLOCATION.json", passed=AL["passed"], F1_sum_i_minus_x_B_eur=AL["runs"]["F1"]["diff_sum_i_minus_x_B_eur"],
                              F2_sum_i_minus_x_B_eur=AL["runs"]["F2"]["diff_sum_i_minus_x_B_eur"], lp_check_F1=AL["runs"]["F1"]["lp_check"], lp_check_F2=AL["runs"]["F2"]["lp_check"],
                              strict_bunker_benefit_sum_minus_bunker_benefit_eur=AL["benefit"]["diff_strict_sum_minus_bunker_benefit_eur"]),
              x_source=dict(owen=XS["owen"], owen_sha256=XS["owen_sha256"], identity=XS["identity"]), threshold_rule=XS["threshold_rule"], summary=summ,
              runs={r["run"]: {k: v for k, v in r.items() if k != "run"} for r in rows}, solver_calls=summ["solves"], stop_conditions=dict(violation=bool(summ["violations"])))
    (a.work / "EVIDENCE.json").write_text(json.dumps(ev, indent=1, default=str) + "\n")
    with open(a.work / "CHECKPOINTS.csv", "w", newline="") as f:
        base = [dict(step="W20b-0", item="instruction SHA256", result="match", detail="25f1db61... = V4_W20B_SHA256.txt", file="V4_W20B_SHA256.txt"),
                dict(step="W20b-0", item="session model / start conditions", result="ok", detail="claude-opus-5-5 effort xhigh; no running session (idle W20 CLI process only); no Gurobi process; token route ok; 9 GiB", file="PROGRESS.md"),
                dict(step="W20b-0", item="c477db3d ancestor of b62ef3c0, diff only W20 delivery", result="ok", detail="2 files, 0 outside research/06_scope_redesign/p1_v4_w20_20261109", file="PROGRESS.md"),
                dict(step="W20b-1a", item="tests (W20 file unchanged + W20b ports file)", result="69 passed", detail="25 + 44: (a) identity 2920/56, (b) 17 W20 networks byte-identical, (c)(d) 17 ports coalitions", file="logs/tests_v4_coalition_w20b.txt"),
                dict(step="W20b-1a", item="x_{B,i} (section 2.3)", result="pass", detail="rebuilt LP = exported LP; sum_i x_{B,i} - x_B = 0.000 EUR (F1 and F2)", file="evidence/W20B_BUNKER_PORT_ALLOCATION.json"),
                dict(step="W20b-1b", item="18 networks built", result="18/18", detail="at 06c1ed1d, clean tree", file="logs/build_nets56.txt"),
                dict(step="W20b-1b", item="static checks + zero-slack gate", result="18/18 pass", detail="first run failed on a check error (two-way pool links), check fixed, networks unchanged", file="evidence/STATIC_CHECKS_W20B.json"),
                dict(step="W20b-2", item="registration committed and pushed before solves", result="bbff7550", detail="identity -4,519.48 EUR <= 0.01 bn", file="CORE_CHECK_V4_56_BUNKER.md")]
        w = csv.DictWriter(f, fieldnames=["step", "item", "result", "detail", "file"], lineterminator="\n"); w.writeheader()
        for r in base + cps:
            w.writerow(r)
    print(json.dumps(summ, indent=1, default=str))


if __name__ == "__main__":
    main()
