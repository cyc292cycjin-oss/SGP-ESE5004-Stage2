"""V4 D1: EVIDENCE.json - every reported number with status EXACT / VERIFIED / INFERENCE / PROPOSED and data grade A-E (or '-'), from the D1 tables and
evidence files (no recomputation of model results; the smoke entries are read from evidence/D1_smoke56.json when present).

    <env python> scripts/d1_evidence.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def jl(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main():
    rows = []
    add = lambda k, v, unit, st, gr, src, note="": rows.append(dict(id=k, value=v, unit=unit, status=st, grade=gr, source=src, note=note))   # noqa: E731
    add("instruction.sha256", sha(W / "V4_D1_INSTRUCTION.md"), "sha256", "VERIFIED", "-", "V4_D1_INSTRUCTION.md", "= V4_D1_SHA256.txt (checked before starting)")
    add("branch.base", dict(branch="codex/v4-d1-20261107", base="7aa356e49d284749d27c79fbdc75ade85f62866a", w08_review_commit_ancestor="bd890bf9",
                            files_changed_between="3, all under research/06_scope_redesign/p1_v4_w08_20261106/"), "-", "VERIFIED", "-", "git merge-base / git diff --name-only")
    # ---- section 2
    hv = pd.read_csv(W / "tables/D1_HVC_CHAIN_CHECK.csv")
    add("s2.hvc_basis_chain_vs_i2", dict(max_abs_diff_basis_b_TWh=float(hv.diff_b.abs().max()), max_abs_diff_basis_a_TWh=float(hv.diff_a.abs().max())), "TWh", "VERIFIED", "-",
        "tables/D1_HVC_CHAIN_CHECK.csv", "S7, I2 main switch set (IId + paper fuelwood purchased); I2 table printed to 6 decimals")
    add("s2.ev_factor", dict(unrounded=16.0712 / 53.19, w08_rounded=0.30215, relative_difference=0.30215 / (16.0712 / 53.19) - 1.0), "MWh_el/MWh_oil", "EXACT", "C",
        "registry share_transport_ice_efficiency / share_transport_electric_efficiency x share_land_transport_electric_share_2050")
    add("s2.out_tables_network_facing_identical", True, "-", "VERIFIED", "-", "scripts/regen_tables.sh", "out_ras / out_iid: 10 tables byte-identical to W08; SNAPSHOT.json and V4_SWITCHES.json changed")
    d = json.loads((W / "batch_def/BATCH_DEF_2920x3h_v4hpc.json").read_text(encoding="utf-8"))
    add("s2.batch_def_draft", dict(limits_status=d["limits_status"], limits=d["limits"], run_dirs=d["run_dirs"], walltime_F1=d["hpc_jobs"]["F1"]["walltime"]), "-", "PROPOSED", "-",
        "batch_def/BATCH_DEF_2920x3h_v4hpc.json", "draft only; not packaged, not registered")
    # ---- section 3
    add("s3.missing_cost_proxy", 6.26706128163, "EUR2020/MWh", "VERIFIED", "C (trunk: D)", "registry biomass_missing_cost_proxy = 32 proxy rows", "applies to the five oil_palm_trunk pools")
    # ---- section 4
    fx = pd.read_csv(W / "PHYSICS_BOUNDS_FIX.csv")
    add("s4.physics_fixes", fx[["param_id", "old_low", "old_high", "new_low", "new_high", "violation_class"]].to_dict("records"), "-", "EXACT", "-", "PHYSICS_BOUNDS_FIX.csv")
    ps = jl(W / "evidence/PHYSICS_SCAN.json")
    add("s4.scan", dict(in_use_rows=ps["in_use_rows"], rows_with_range=ps["rows_with_range"], checks=[(c["check"], c["rows_checked"], len(c["violations"])) for c in ps["checks"]]),
        "rows", "VERIFIED", "-", "evidence/PHYSICS_SCAN.json")
    add("s4.meoh_per_tco2_main_above_limit", dict(main=4.0321, limit=ps["limits"]["meoh_per_tco2_max"], excess_rel=4.0321 / ps["limits"]["meoh_per_tco2_max"] - 1.0), "MWh/t",
        "EXACT", "C", "evidence/PHYSICS_SCAN.json", "main value not changed (instruction 4.1); PyPSA-Eur config value")
    # ---- section 5
    tb = jl(W / "evidence/T03_BALANCE.json")
    add("s5.balance_main", tb["balance_main"], "GJ/t FFB; share", "INFERENCE", "C", "evidence/T03_BALANCE.json", "pooled medians of independent source groups")
    add("s5.balance_corners", dict(low=tb["balance_low_corner"], high=tb["balance_high_corner"]), "GJ/t FFB; share", "INFERENCE", "C", "evidence/T03_BALANCE.json")
    t = pd.read_csv(W / "PALM_MILL_SELF_USE.csv")
    for r in t.itertuples():
        add(f"s5.self_use_{r.country}", dict(fibre=[r.fibre_low, r.fibre_mid, r.fibre_high], pks=[r.pks_low, r.pks_mid, r.pks_high], verdict_fibre=r.verdict_fibre,
                                            verdict_pks=r.verdict_pks, literature=[r.literature_fibre, r.literature_pks], balance=[r.balance_fibre, r.balance_pks]),
            "share", "VERIFIED (literature) / INFERENCE (balance)", f"fibre {r.grade_fibre}, PKS {r.grade_pks}", "PALM_MILL_SELF_USE.csv")
    add("s5.potential_effect_low_high", tb["asean_effect_TWh"], "TWh", "EXACT", "C", "evidence/T03_BALANCE.json", "ASEAN solid-biomass potential vs the kept values")
    add("s5.pks_trade_side_evidence", tb["pks_trade_side_evidence"], "t/a; share", "INFERENCE", "B", "evidence/T03_BALANCE.json", "annualised quarter / month values")
    add("s5.potential_file_identical", "cd9df282168598cc0080 (BIOMASS_POTENTIAL_2050_V4.csv)", "sha256 prefix", "VERIFIED", "-", "test_v4_d1_palm.py")
    cp = pd.read_csv(W / "CHECKPOINTS.csv")
    add("s5.checkpoints", dict(rows=int(len(cp)), all_within_1e6=bool(cp.within_1e6.all()), max_abs_diff_T=float(cp[cp.country != "ASEAN11"].diff_T_TWh.abs().max()),
                               S7={r: float(cp[(cp.run == r) & (cp.step == "S7") & (cp.country == "ASEAN11")].T_v2_repo_TWh.iloc[0]) for r in ("main", "iid", "i2chk")}),
        "TWh", "VERIFIED", "-", "CHECKPOINTS.csv")
    # ---- section 6
    pm = jl(W / "evidence/PHS_MODEL.json")
    bc = pd.DataFrame(pm["by_country"])
    phs = dict(existing_MW=bc[bc.carrier == "PHS existing"].set_index("country").p_nom_MW.to_dict(), candidate_cap_MW=bc[bc.carrier == "PHS"].set_index("country").p_nom_max_MW.to_dict())
    phs["existing_total_MW"] = float(sum(phs["existing_MW"].values())); phs["candidate_total_MW"] = float(sum(phs["candidate_cap_MW"].values()))
    add("s6.model_phs", phs, "MW", "VERIFIED", "-", "evidence/PHS_MODEL.json (by_country, carriers 'PHS existing' / 'PHS')", "the totals field of PHS_MODEL.json also counts reservoir hydro")
    add("s6.cost_eur2020_per_kw", dict(lu2021_6h=754.42, anu2025_6h=740.48, lu2021_24h=1543.92, anu2025_24h=1508.93, model=2297.34), "EUR2020/kW", "INFERENCE", "B",
        "PHS_PROPOSAL.md section 4", "registry conversions deflator_usd_2024_to_2020 x fx_usd_to_eur_2020")
    add("s6.existing_iha_2024", 2260, "MW", "VERIFIED", "B", "evidence/PHS_LITERATURE.json C01-C03")
    # ---- section 7
    st = jl(W / "STATIC_CHECKS.json")
    for k, v in st.items():
        add(f"s7.static_{k}", {x: v[x] for x in ("network_sha256", "network_bytes", "C1_industry_loads_vs_summary_max_abs_mwh", "C2_ev_vs_land_x_ev_factor_max_rel", "C3_max_ratio",
                                                 "C4_total_change_twh", "C6_switch_sha_equals_tables")}, "-", "VERIFIED", "-", "STATIC_CHECKS.json")
    nd = jl(W / "evidence/D1_NETWORK_DIFF.json")
    add("s7.network_diff_vs_w08", {k: v["C8_only_trunk_store_cost_differs"] for k, v in nd.items()}, "-", "VERIFIED", "-", "evidence/D1_NETWORK_DIFF.json")
    zs = jl(W / "evidence/ZERO_SLACK_CHECK_D1.json")
    add("s7.zero_slack_gate", dict(passed=zs.get("passed")), "-", "VERIFIED", "-", "evidence/ZERO_SLACK_CHECK_D1.json")
    bp = jl(W / "evidence/D1_BOUNDS_PRE.json")
    add("s7.bounds_registered", {k: dict(upper_bound_eur=v["upper_bound_eur"], interval_eur=v["registered_interval_eur"]) for k, v in bp.items()}, "EUR", "EXACT", "-",
        "evidence/D1_BOUNDS_PRE.json", "registered in SMOKE56_D1.md section 1 (commit 365c8d62) before any D1 solve")
    sm = jl(W / "evidence/D1_smoke56.json")
    if sm:
        for k, v in sm["runs"].items():
            add(f"s7.smoke_{k}", {x: v.get(x) for x in ("termination", "objective_eur", "objective_lp_eur", "dV_eur", "within_registered", "dV_over_upper", "barrier_iterations",
                                                        "solve_seconds", "peak_rss_gib", "gates_failed", "V6_label")}, "-", "VERIFIED", "-", "evidence/D1_smoke56.json")
        add("s7.smoke_criteria", sm["criteria"], "-", "VERIFIED", "-", "evidence/D1_smoke56.json")
    out = dict(schema="v4-d1-evidence-1", n=len(rows), entries=rows)
    (W / "EVIDENCE.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    print("EVIDENCE.json", len(rows), "entries")


if __name__ == "__main__":
    main()
