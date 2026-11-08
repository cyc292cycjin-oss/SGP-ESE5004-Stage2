"""V4 D2c: EVIDENCE.json - every reported number with status EXACT / VERIFIED / INFERENCE / PROPOSED and data grade A-C (or '-'), read from the D2c tables
and evidence files (no recomputation of model results; smoke / test entries are read when present).

    /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/d2c_evidence.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]
R = Path("/home/jin/wt_v4_d2c")
BIO = R / "research_inputs/biomass_v5"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def jl(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def last_pytest(p: Path):
    if not p.exists():
        return None
    m = [l for l in p.read_text(encoding="utf-8", errors="replace").splitlines() if re.search(r"\d+ passed", l)]
    return m[-1].strip() if m else None


def main():
    rows = []
    add = lambda k, v, unit, st, gr, src, note="": rows.append(dict(id=k, value=v, unit=unit, status=st, grade=gr, source=src, note=note))   # noqa: E731
    add("instruction.sha256", sha(W / "V4_D2C_INSTRUCTION.md"), "sha256", "VERIFIED", "-", "V4_D2C_INSTRUCTION.md", "= V4_D2C_SHA256.txt (checked before starting)")
    add("session.model", "claude-opus-5-5 (Opus 5.5)", "-", "VERIFIED", "-", "session system information", "effort setting of the session not visible to the session (instruction asks Xhigh)")
    add("branch.base", dict(branch="codex/v4-d2c-20261109", base="25bd7cf0be0c17caac1fcc272ed2f3c2779312d2", d2b_review_commit_ancestor="4e90ea4b",
                            files_changed_between="2, all under research/06_scope_redesign/p1_v4_d2b_20261108/"), "-", "VERIFIED", "-", "git merge-base --is-ancestor / git diff --name-only (/home/jin/v4d2c/s1_verify.log)")
    # ---- section 2.1
    m = pd.read_csv(W / "TRUNK_DRY_MASS.csv", keep_default_na=False)
    add("s2.trunk_dry_mass_sources", m[m.source_id.isin(["KHALID1999", "CHOW2008", "HENSON2006"])][["source_id", "value_reported", "unit_reported", "density_palms_per_ha", "age_years", "conversion", "per_palm_t_dm"]].to_dict("records"),
        "t DM per palm", "VERIFIED (source values and densities) / EXACT (division)", "B", "TRUNK_DRY_MASS.csv; evidence/D2C_TRUNK_LITERATURE.json H1-H3; D2b evidence/TRUNK_LITERATURE.json T01 T04 T09 T12",
        "Henson Fig. 8 includes the Khalid 1999 points (compilation, not fully independent)")
    s = m.set_index("source_id")
    add("s2.trunk_dry_mass_per_palm", dict(centre=float(s.at["CENTRE", "per_palm_t_dm"]), low=float(s.at["LOW", "per_palm_t_dm"]), high=float(s.at["HIGH", "per_palm_t_dm"]),
                                           per_ha_at_model_140=dict(centre=float(s.at["CENTRE", "per_ha_at_model_140_t_dm"]), low=float(s.at["LOW", "per_ha_at_model_140_t_dm"]), high=float(s.at["HIGH", "per_ha_at_model_140_t_dm"]))),
        "t DM per palm", "EXACT", "B", "TRUNK_DRY_MASS.csv (median / min / max of the three included sources)")
    add("s2.not_used_sources", m[(m.included.astype(str) == "False")][["source_id", "per_palm_t_dm", "evidence_grade", "note"]].to_dict("records"), "t DM per palm", "VERIFIED / SNIPPET", "-", "TRUNK_DRY_MASS.csv")
    calc = jl(W / "evidence/D2C_TRUNK_CALC.json")
    add("s2.centre_robustness", dict(robustness_of_centre=calc["robustness_of_centre"], henson_age={k: v["t_dm_per_palm"] for k, v in calc["henson_age"].items()}), "t DM per palm", "EXACT", "-",
        "evidence/D2C_TRUNK_CALC.json", "medians if the not-used values were included; Henson per palm at 23-27 years")
    b6 = pd.read_csv(BIO / "BIOMASS_BASIS_T06.csv", keep_default_na=False).set_index("category").loc["oil_palm_trunk"]
    b5 = pd.read_csv(BIO / "BIOMASS_BASIS_T05.csv", keep_default_na=False).set_index("category").loc["oil_palm_trunk"]
    add("s2.trunk_factor", dict(t06=dict(mid=float(b6.factor_mid), low=float(b6.factor_low), high=float(b6.factor_high), dry_matter_per_reported_t=float(b6.dry_matter_mid), lhv_dry=float(b6.lhv_dry_gj_t_mid)),
                                t05=dict(mid=float(b5.factor_mid), low=float(b5.factor_low), high=float(b5.factor_high)), ratio_t06_t05=float(b6.factor_mid) / float(b5.factor_mid)),
        "factor on the W08 energy", "EXACT", "C", "research_inputs/biomass_v5/BIOMASS_BASIS_T06.csv / _T05.csv", "factor = dry mass per palm / 2 t per palm x 16.12182 / 15")
    # ---- section 2.2
    a5 = pd.read_csv(BIO / "BIOMASS_POTENTIAL_ADJ_V4_T05.csv"); a6 = pd.read_csv(BIO / "BIOMASS_POTENTIAL_ADJ_V4_T06.csv")
    tr = lambda a: {r.country: float(r.potential_adjusted_TWh) for r in a[a.category == "oil_palm_trunk"].itertuples()}   # noqa: E731
    tot = lambda a: {r.country: float(r.potential_adjusted_TWh) for r in a[a.category == "TOTAL solid"].itertuples()}   # noqa: E731
    add("s2.trunk_potential_twh", dict(t05=tr(a5), t06=tr(a6), sum_t05=sum(tr(a5).values()), sum_t06=sum(tr(a6).values())), "TWh", "EXACT", "C", "BIOMASS_POTENTIAL_ADJ_V4_T05.csv / _T06.csv")
    add("s2.solid_potential_twh", dict(t05=tot(a5), t06=tot(a6)), "TWh", "EXACT", "C", "BIOMASS_POTENTIAL_ADJ_V4_T05.csv / _T06.csv (TOTAL solid)", "ASEAN11 row = sum")
    add("s2.files", {p.name: sha(p) for p in (BIO / "BIOMASS_BASIS_T06.csv", BIO / "BIOMASS_POTENTIAL_2050_V4_T06.csv", BIO / "BIOMASS_POTENTIAL_ADJ_V4_T06.csv")}, "sha256", "VERIFIED", "-",
        "research_inputs/biomass_v5", "W08 / T04 / T05 files byte-identical to HEAD of D2b (logs/s2_pot.txt); T06 potential = T05 except the five trunk lines")
    cp = pd.read_csv(W / "CHECKPOINTS.csv")
    add("s2.checkpoints", {run: dict(rows=int((cp.run == run).sum()), all_within_1e6=bool(cp[cp.run == run].within_1e6.all()), max_abs_diff_T=float(cp[(cp.run == run) & (cp.country != "ASEAN11")].diff_T_TWh.abs().max()),
                                     max_abs_diff_cap=float(cp[(cp.run == run) & (cp.country != "ASEAN11")].diff_cap_TWh.abs().max()),
                                     T_v2_S7_asean=float(cp[(cp.run == run) & (cp.step == "S7") & (cp.country == "ASEAN11")].T_v2_repo_TWh.iloc[0])) for run in sorted(cp.run.unique())},
        "TWh", "VERIFIED", "-", "CHECKPOINTS.csv (reference engine scripts/ref on the T06 potential)", "T_v2 unchanged vs D2b (3,490.338 / 3,166.522 TWh)")
    for mode in ("ras", "iid"):
        rec = jl(R / f"research_inputs/industry_v4/out_{mode}/V4_SWITCHES.json")
        add(f"s2.table_folder_{mode}", dict(switch_sha256=rec["switch_sha256"], biomass_potential=rec["switches"]["biomass_potential"], main_set=rec["main_set"]), "-", "VERIFIED", "-", f"research_inputs/industry_v4/out_{mode}/V4_SWITCHES.json")
    # ---- section 2.3
    reg = pd.read_csv(R / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    ids = ["v4_oil_palm_trunk_dry_mass_per_palm", "v4_oil_palm_trunk_energy_per_reported_t_t06", "v4_oil_palm_replanting_rate", "v4_biomass_basis_table_t06",
           "v4_biomass_potential_2050_t06", "v4_biomass_potential_adjustment_t06"] + [f"biomass_potential_{c}_oil_palm_trunk" for c in ("ID", "KH", "MY", "PH", "TH")]
    add("s2.registry_rows", {p: {k: reg.at[p, k] for k in ("value", "unit", "tier", "sensitivity_low", "sensitivity_high", "status", "decision_ref")} for p in ids}, "-", "VERIFIED", "B / C",
        "research_inputs/registry_v5/DATA_REGISTRY.csv", f"rows {len(reg)} (D2b 2,463)")
    # ---- section 3
    st = jl(W / "STATIC_CHECKS.json"); nd = jl(W / "evidence/D2C_NETWORK_DIFF.json"); zs = jl(W / "evidence/ZERO_SLACK_CHECK_D2C.json")
    add("s3.networks", {k: dict(sha256=v["network_sha256"], bytes=v["network_bytes"], sha256_365=v["network_365_sha256"]) for k, v in st.items()}, "-", "VERIFIED", "-", "STATIC_CHECKS.json; logs/build_main.txt")
    add("s3.c8", {k: dict(passed=v["C8"]["passed"], expected=v["C8"]["expected"], unexpected=v["C8"]["unexpected"], meta_keys=v["diff"]["meta_keys_differing"]) for k, v in nd.items()}, "-", "VERIFIED", "-",
        "evidence/D2C_NETWORK_DIFF.json", "expected set registered in scripts/d2c_static.py before the first build")
    add("s3.static", {k: {c: v[c] for c in ("C1_industry_loads_vs_summary_max_abs_mwh", "C2_ev_vs_land_x_ev_factor_max_rel", "C3_max_ratio", "C3_pools_at_or_above_0.999", "C4_gas_caps_vs_table_max_rel",
                                              "C6_switch_sha_equals_tables", "C10_overflow_ledger_vs_table_max_abs_mwh", "C11_band_shares_ledger_vs_table_max_abs", "C12_lng_mc_change_max_dev")} for k, v in st.items()},
        "-", "VERIFIED", "-", "STATIC_CHECKS.json")
    zz = zs if isinstance(zs, list) else (zs.get("networks") or zs.get("results") or zs)
    if isinstance(zz, dict):
        zz = [dict(v, network=k) for k, v in zz.items() if isinstance(v, dict)]
    add("s3.zero_slack", [{k: z.get(k) for k in ("network", "label", "scenario", "passed", "zero_slack_forcing_rows") if k in z} | dict(rows=len(z.get("constraints", []))) for z in zz if isinstance(z, dict)],
        "-", "VERIFIED", "-", "evidence/ZERO_SLACK_CHECK_D2C.json")
    # ---- section 4
    bp = jl(W / "evidence/D2C_BOUNDS_PRE.json")
    add("s4.alarm_lines", {k: dict(rhs_lower_bound_eur=v["rhs_lower_bound_eur"], tolerance_eur=v["tolerance_eur"], alarm_line_eur=v["alarm_line_eur"],
                                   pool_terms={p["store"]: dict(marginal_value=p["marginal_value_eur_per_mwh"], delta_mwh=p["delta_annual_mwh"], term_eur=p["lb_term_eur"]) for p in v["pools"]},
                                   loads=len(v["loads"]), costs=len(v["costs"])) for k, v in bp.items()}, "EUR", "EXACT (rule) / VERIFIED (D2b duals)", "-", "evidence/D2C_BOUNDS_PRE.json; SMOKE56_D2C.md 1.3",
        "registered in commit 88bbbe57 before the solves")
    sm = jl(W / "evidence/D2C_smoke56.json")
    if sm:
        add("s4.smoke", {k: {c: v.get(c) for c in ("termination", "objective_eur", "d2b_objective_eur", "dV_eur", "alarm_line_eur", "above_alarm_line", "dV_minus_lower_bound_eur",
                                                   "gates_failed", "gates_failed_d2b", "gates_failed_outside_v31_union", "C1_accepted", "V6_label", "barrier_iterations", "solve_seconds", "peak_rss_gib")}
                         for k, v in sm["runs"].items()}, "EUR", "VERIFIED", "-", "evidence/D2C_smoke56.json; tables/D2C_SMOKE56_RESULTS.csv")
        add("s4.criteria", sm["criteria"], "-", "VERIFIED", "-", "evidence/D2C_smoke56.json", "B6 at 56 snapshots: regression only")
    # ---- tests
    add("tests", dict(v4_set=last_pytest(W / "logs/ut_v4_all.txt"), network=last_pytest(W / "logs/ut_net_d2c.txt"), full=last_pytest(W / "logs/ut_full.txt")), "-", "VERIFIED", "-", "logs/ut_*.txt")
    add("literature_access", dict(henson_pdf_sha256="402652ec26f019c337aa425cb2f13c3f6bdddd7f80d54346d26ca1b16485486f", via="WebFetch (read only); kept in the session scratch, not in the repository / zip",
                                  user_downloads_folder="unchanged (listing before / after)"), "-", "VERIFIED", "-", "evidence/D2C_TRUNK_LITERATURE.json note")
    (W / "EVIDENCE.json").write_text(json.dumps(dict(step="V4 D2c (decision 223)", entries=rows), indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8", newline="\n")
    print("EVIDENCE.json", len(rows), "entries")


if __name__ == "__main__":
    main()
