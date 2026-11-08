"""V4 D2a: EVIDENCE.json - every reported number with status EXACT / VERIFIED / INFERENCE / PROPOSED and data grade A-E (or '-'), read from the D2a tables and
evidence files (no recomputation of model results; smoke / attribution entries are read when present).

    <env python> scripts/d2a_evidence.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]
R = Path("/home/jin/wt_v4_d2a")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def jl(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main():
    rows = []
    add = lambda k, v, unit, st, gr, src, note="": rows.append(dict(id=k, value=v, unit=unit, status=st, grade=gr, source=src, note=note))   # noqa: E731
    add("instruction.sha256", sha(W / "V4_D2A_INSTRUCTION.md"), "sha256", "VERIFIED", "-", "V4_D2A_INSTRUCTION.md", "= V4_D2A_SHA256.txt (checked before starting)")
    add("branch.base", dict(branch="codex/v4-d2a-20261107", base="4026c1c84d8d349e9bb8c11f3e6da8f82588d621", d1_review_commit_ancestor="6142d8ac", files_changed_between="3, all under research/06_scope_redesign/p1_v4_d1_20261107/"),
        "-", "VERIFIED", "-", "git merge-base / git diff --stat")
    # ---- section 2
    for mode in ("ras", "iid"):
        rec = jl(R / f"research_inputs/industry_v4/out_{mode}/V4_SWITCHES.json")
        vn = rec["biomass_overflow_recomputed"]["VN"]
        add(f"s2.f02_vn_overflow_{mode}", dict(s30_twh=vn["s30_overflow_industry_mwh"] / 1e6, recomputed_twh=vn["overflow_industry_mwh"] / 1e6, difference_twh=(vn["overflow_industry_mwh"] - vn["s30_overflow_industry_mwh"]) / 1e6,
                                               biomass_T_v2_twh=vn["biomass_T_v2_mwh"] / 1e6, cap_twh=vn["cap_mwh"] / 1e6), "TWh", "EXACT", "-", f"out_{mode}/V4_SWITCHES.json biomass_overflow_recomputed",
            "overflow after the conservation layer = the build rule (Fable F-02); difference = the VN pulp-and-paper purchased biomass vector")
        bn = rec["bn_neu_methanol"]
        add(f"s2.f07_bn_neu_{mode}", dict(base_2019_before_twh=bn["base_2019_before_mwh"] / 1e6, base_2019_after_twh=bn["base_2019_after_mwh"] / 1e6, value_2050_before_twh=bn["before_mwh"] / 1e6, value_2050_after_twh=bn["after_mwh"] / 1e6),
            "TWh", "EXACT", "C", f"out_{mode}/V4_SWITCHES.json bn_neu_methanol", "BN T_v2 effect 0 (NEU outside T_v2)")
    lit = jl(R / "research_inputs/industry_v4/out_ras_5ba297a881ba/V4_SWITCHES.json"); main_ = jl(R / "research_inputs/industry_v4/out_ras/V4_SWITCHES.json")
    add("s2.f01_literal_reading", dict(id_T_v2_main_twh=main_["T_v2_TWh"]["ID"], id_T_v2_literal_twh=lit["T_v2_TWh"]["ID"], difference_twh=lit["T_v2_TWh"]["ID"] - main_["T_v2_TWh"]["ID"], asean_literal_twh=lit["asean_T_v2_TWh"],
                                       fable_difference_twh=36.889854), "TWh", "EXACT", "C", "out_ras_5ba297a881ba/V4_SWITCHES.json vs out_ras", "= Fable SENS_PAPER_FUELWOOD.json")
    cp = pd.read_csv(W / "CHECKPOINTS.csv")
    add("s2_s5.checkpoints", {run: dict(rows=int((cp.run == run).sum()), all_within_1e6=bool(cp[cp.run == run].within_1e6.all()), max_abs_diff_T=float(cp[(cp.run == run) & (cp.country != "ASEAN11")].diff_T_TWh.abs().max()),
                                        max_abs_diff_overflow=float(cp[(cp.run == run) & (cp.country != "ASEAN11")].diff_overflow_TWh.abs().max()) if "diff_overflow_TWh" in cp else None) for run in sorted(cp.run.unique())},
        "TWh", "VERIFIED", "-", "CHECKPOINTS.csv (corrected reference engine scripts/ref)")
    # ---- section 3
    t04 = pd.read_csv(R / "research_inputs/biomass_v5/PALM_RESIDUE_BASIS_T04.csv", keep_default_na=False)
    add("s3.t04_basis_table", t04[["category", "moisture_ar_mid", "lhv_dry_gj_t_mid", "consistent_gj_per_wet_t_mid", "factor_mid", "factor_low", "factor_high", "verdict", "applied", "grade"]].to_dict("records"), "-", "VERIFIED (sources) / EXACT (factors)", "C",
        "PALM_RESIDUE_BASIS_T04.csv; evidence/T04_LITERATURE.json")
    a0 = pd.read_csv(R / "research_inputs/biomass_v5/BIOMASS_POTENTIAL_ADJ_V4.csv"); a4 = pd.read_csv(R / "research_inputs/biomass_v5/BIOMASS_POTENTIAL_ADJ_V4_T04.csv")
    tot0 = a0[a0.category == "TOTAL solid"].set_index("country").potential_adjusted_TWh; tot4 = a4[a4.category == "TOTAL solid"].set_index("country").potential_adjusted_TWh
    add("s3.t04_potential_change_twh", {c: dict(w08=float(tot0[c]), t04=float(tot4[c]), change=float(tot4[c] - tot0[c])) for c in tot0.index if abs(tot4[c] - tot0[c]) > 1e-6}, "TWh", "EXACT", "C",
        "BIOMASS_POTENTIAL_ADJ_V4_T04.csv vs BIOMASS_POTENTIAL_ADJ_V4.csv")
    recl = pd.read_csv(R / "research_inputs/fleet_v5/PHS_STOCK_RECLASS_V4.csv", keep_default_na=False)
    add("s3.phs_reclass", recl[["identity", "gem_capacity_mw", "reclass_to", "reclass_mw", "drop_mw"]].to_dict("records"), "MW", "VERIFIED", "B", "PHS_STOCK_RECLASS_V4.csv; evidence/PHS_STOCK_LITERATURE.json (EGAT T-01, ANDRITZ T-03, IHA T-20)")
    add("s3.phs_stock_after", dict(TH_pumped_mw=1531.0, TH_conventional_added_mw=608.2, PH_kept_mw=856.0, asean_pumped_mw=4627.0), "MW", "VERIFIED", "B", "STATIC_CHECKS.json PHS_existing_by_country_mw")
    reg = pd.read_csv(R / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    add("s3.meoh_per_tco2", dict(v4_main=float(reg.at["ammonia_methanol_MWh_MeOH_per_tCO2_stoichiometric", "value"]), v31_fallback=4.0321, hydrogen_lhv_mwh_t=float(reg.at["physics_hydrogen_lhv_mwh_per_t", "value"])), "MWh_MeOH/tCO2", "EXACT", "B", "registry rows")
    add("s3.phs_asean_costs", {k: float(reg.at[k, "value"]) for k in ("phs_asean_power_cost_eur2020_per_kw", "phs_asean_energy_cost_eur2020_per_kwh", "phs_asean_fom_eur2020_per_kw_a", "phs_asean_lifetime_a", "phs_asean_round_trip")},
        "EUR2020 / a / per unit", "EXACT (conversion) / VERIFIED (source)", "B", "registry (Lu et al. 2021 Table 3 x fx_usd_to_eur_2020)", "SENSITIVITY rows")
    add("s3.registry_rows", dict(total=int(len(reg)), d2a_fragment=int((reg.derivation_script == "scripts_project/v4_d2a_registry.py").sum()) if "derivation_script" in reg.columns else None), "rows", "VERIFIED", "-", "DATA_REGISTRY.csv")
    # ---- section 4
    rs = jl(W / "evidence/RERANK_D2A_SUMMARY.json")
    add("s4.rerank_summary", {k: rs[k] for k in ("ranked_rows", "ranked_rows_w15", "inactive_basis_rows", "range_updates", "top30_overlap_with_w15", "entered", "left", "spearman_vs_w15", "duplicate_bounds", "bias_classes", "top30_abs_dB6_share")},
        "-", "VERIFIED", "-", "evidence/RERANK_D2A_SUMMARY.json; rerank/")
    top = pd.read_csv(W / "RERANK_D2A_TOP30.csv")
    add("s4.top5", top.head(5)[["rank", "param_id", "bias_class", "dB6", "dZ_F1"]].to_dict("records"), "EUR", "INFERENCE (first order)", "C", "RERANK_D2A_TOP30.csv")
    dup = pd.read_csv(W / "rerank/DUPLICATE_BOUNDS.csv")
    add("s4.kh_co2_cap_dual", dup[dup.country == "KH"][["dual_global_row", "dual_store_e_nom_upper", "dual_total"]].to_dict("records"), "EUR/t", "VERIFIED", "-", "rerank/DUPLICATE_BOUNDS.csv (v31 F1 duals)")
    # ---- section 5
    st = jl(W / "STATIC_CHECKS.json")
    for tag, v in st.items():
        add(f"s5.static_{tag}", {k: v[k] for k in ("network_sha256", "C1_industry_loads_vs_summary_max_abs_mwh", "C2_ev_vs_land_x_ev_factor_max_rel", "C3_max_ratio", "C3_VN_slack_share", "C4_gas_caps_vs_table_max_rel", "C6_switch_sha_equals_tables",
                                                    "C10_overflow_ledger_vs_table_max_abs_mwh", "PHS_existing_by_country_mw", "hydro_inflow_TH_annual_twh", "hydro_inflow_TH_annual_twh_D1", "C3_pool_change_vs_D1_twh")}, "-", "VERIFIED", "-", "STATIC_CHECKS.json")
    nd = jl(W / "evidence/D2A_NETWORK_DIFF.json")
    add("s5.c8_network_diff_vs_d1", {k: dict(passed=v["C8"]["passed"], expected=v["C8"]["expected"], unexpected=v["C8"]["unexpected"]) for k, v in nd.items()}, "-", "VERIFIED", "-", "evidence/D2A_NETWORK_DIFF.json")
    zs = jl(W / "evidence/ZERO_SLACK_CHECK_D2A.json")
    if zs:
        nets = zs.get("networks") if isinstance(zs, dict) and isinstance(zs.get("networks"), (list, dict)) else zs
        items = nets.items() if isinstance(nets, dict) else [(x.get("label"), x) for x in nets]
        add("s5.zero_slack", {k: dict(passed=v.get("passed"), rows=len(v.get("constraints", [])), forcing=v.get("zero_slack_forcing_rows")) for k, v in items if isinstance(v, dict) and "passed" in v}, "-", "VERIFIED", "-", "evidence/ZERO_SLACK_CHECK_D2A.json")
    # ---- section 6
    bp = jl(W / "evidence/D2A_BOUNDS_PRE.json")
    add("s6.alarm_lines", {k: dict(d1_objective_eur=v["d1_objective_eur"], rhs_lower_bound_eur=v["rhs_lower_bound_eur"], coefficient_first_order_eur=v["terms"]["coefficient_first_order_eur"], tolerance_eur=v["tolerance_eur"], alarm_line_eur=v["alarm_line_eur"],
                                   pools_eur=v["terms"]["pools_rhs_lower_bound_eur"], phs_eur=v["terms"]["phs_rhs_lower_bound_eur"], inflow_eur=v["terms"]["th_inflow_rhs_lower_bound_eur"], new_reservoir_eur=v["terms"]["new_reservoir_completion_eur"]) for k, v in bp.items()},
        "EUR", "EXACT (rule) / VERIFIED (D1 duals) / INFERENCE (completion)", "-", "evidence/D2A_BOUNDS_PRE.json", "registered before the solves (commit 63651f19)")
    sm = jl(W / "evidence/D2A_smoke56.json")
    if sm:
        add("s6.smoke_runs", {k: {kk: v[kk] for kk in ("network_sha256", "termination", "objective_eur", "objective_lp_eur", "d1_objective_eur", "dV_eur", "rhs_lower_bound_eur", "alarm_line_eur", "above_alarm_line", "gates_failed", "gates_failed_outside_v31_union", "V6_label", "C1_accepted", "barrier_iterations", "solve_seconds", "peak_rss_gib") if kk in v} for k, v in sm["runs"].items()},
            "EUR", "VERIFIED", "-", "evidence/D2A_smoke56.json (SOLVE_RECEIPT / V5_GATES / PRECISION / V6_ACCEPTANCE)")
        add("s6.criteria", sm["criteria"], "-", "VERIFIED", "-", "evidence/D2A_smoke56.json")
    # ---- section 7
    at = jl(W / "evidence/D2A_attrib56.json")
    if at:
        add("s7.attrib_runs", {k: {kk: v[kk] for kk in ("network_sha256", "termination", "objective_eur", "V6_label", "gates_failed_outside_v31_union") if kk in v} for k, v in at["runs"].items()}, "EUR", "VERIFIED", "-", "evidence/D2A_attrib56.json")
    ab = jl(W / "evidence/ATTRIBUTION_56.json")
    if ab:
        add("s7.shapley", {k: ab["results"][k]["shapley"] for k in ab["results"]}, "EUR", "VERIFIED (3 corners) / INFERENCE ((D31,P31) approximated)", "-", "evidence/ATTRIBUTION_56.json; ATTRIBUTION_56.md")
        add("s7.d31p31_approximation", ab["approximation"]["other_v4_changes_on_v31_eur"], "EUR", "INFERENCE", "-", "evidence/ATTRIB_INPUTS.json")
    # ---- budget
    add("budget.solver_calls", dict(section6=2, section7=len([k for k in (at or {"runs": {}})["runs"]]), authorised=6), "runs", "VERIFIED", "-", "results_project/v4d2a/{smoke56,attrib56}/STATUS.txt")
    out = dict(generated_for="V4 D2a (decision 220)", entries=rows)
    (W / "EVIDENCE.json").write_text(json.dumps(out, indent=1, default=float, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(len(rows), "entries")


if __name__ == "__main__":
    main()
