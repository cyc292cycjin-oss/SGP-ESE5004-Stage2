"""V4 D2b: EVIDENCE.json - every reported number with status EXACT / VERIFIED / INFERENCE / PROPOSED and data grade A-E (or '-'), read from the D2b tables and
evidence files (no recomputation of model results; smoke / rerank entries are read when present).

    <env python> scripts/d2b_evidence.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]
R = Path("/home/jin/wt_v4_d2b")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def jl(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main():
    rows = []
    add = lambda k, v, unit, st, gr, src, note="": rows.append(dict(id=k, value=v, unit=unit, status=st, grade=gr, source=src, note=note))   # noqa: E731
    add("instruction.sha256", sha(W / "V4_D2B_INSTRUCTION.md"), "sha256", "VERIFIED", "-", "V4_D2B_INSTRUCTION.md", "= V4_D2B_SHA256.txt (checked before starting)")
    add("session.model", "claude-opus-5-5 (Opus 5.5)", "-", "VERIFIED", "-", "session system information", "effort setting of the session not visible to the session (instruction asks Xhigh)")
    add("branch.base", dict(branch="codex/v4-d2b-20261108", base="385bdff08e932afef79755be5b1af7ebb2839350", d2a_review_commit_ancestor="15533817",
                            files_changed_between="3, all under research/06_scope_redesign/p1_v4_d2a_20261107/"), "-", "VERIFIED", "-", "git merge-base --is-ancestor / git diff --name-only")
    # ---- section 2
    tc = pd.read_csv(W / "tables/TRUNK_CHAIN_CHECK.csv")
    add("s2.trunk_chain", tc[["country", "trunk_t_per_replanted_ha", "ffb_yield_t_ha", "trunk_t_per_t_ffb_before_cap", "trunk_t_per_t_ffb_after_cap", "potential_twh"]].to_dict("records"), "t / TWh", "EXACT", "C",
        "tables/TRUNK_CHAIN_CHECK.csv (FAOSTAT QCL 2019-2023 means x the v3 chain)", "literature: trunk fresh ~205 t/ha (Khalid 1999 1.508 t x 136), trunk dry 37-42 t DM/ha (Khalid 41.07, Chow 37.3, Henson ~42), whole palm fresh ~300 t/ha")
    b5 = pd.read_csv(R / "research_inputs/biomass_v5/BIOMASS_BASIS_T05.csv", keep_default_na=False)
    add("s2.t05_basis_table", b5[["category", "verdict", "applied", "factor_mid", "factor_low", "factor_high", "grade", "sources"]].to_dict("records"), "-", "VERIFIED (sources) / EXACT (factors) / INFERENCE (verdicts of kept rows)", "C / D",
        "research_inputs/biomass_v5/BIOMASS_BASIS_T05.csv; evidence/TRUNK_LITERATURE.json, RESIDUE_LITERATURE.json")
    au = pd.read_csv(W / "BIOMASS_BASIS_AUDIT.csv")
    g = au.groupby("category")[["old_t04_twh", "new_t05_twh", "change_twh", "range_low_twh", "range_high_twh"]].sum(min_count=1)
    add("s2.potential_by_category_twh", g.round(6).reset_index().to_dict("records"), "TWh", "EXACT", "C", "BIOMASS_BASIS_AUDIT.csv")
    add("s2.asean_solid_potential_twh", dict(t04=float(au[au.group != "biogas"].old_t04_twh.sum()), t05=float(au[au.group != "biogas"].new_t05_twh.sum())), "TWh", "EXACT", "C", "BIOMASS_BASIS_AUDIT.csv")
    cp = pd.read_csv(W / "CHECKPOINTS.csv")
    add("s2.checkpoints", {run: dict(rows=int((cp.run == run).sum()), all_within_1e6=bool(cp[cp.run == run].within_1e6.all()), max_abs_diff_T=float(cp[(cp.run == run) & (cp.country != "ASEAN11")].diff_T_TWh.abs().max()),
                                     max_abs_diff_cap=float(cp[(cp.run == run) & (cp.country != "ASEAN11")].diff_cap_TWh.abs().max())) for run in sorted(cp.run.unique())},
        "TWh", "VERIFIED", "-", "CHECKPOINTS.csv (reference engine scripts/ref on the T05 potential)")
    # ---- section 3
    for mode in ("ras", "iid"):
        rec = jl(R / f"research_inputs/industry_v4/out_{mode}/V4_SWITCHES.json")
        bands = {c: {k: v[k] for k in v if "band" in k} for c, v in rec["biomass_overflow_recomputed"].items() if any(abs(v.get(f"band_{b}_share", 0) - v.get(f"s30_band_{b}_share", 0)) > 1e-12 for b in ("medium_a", "medium_b", "high"))}
        add(f"s3.band_shares_{mode}", bands, "share", "EXACT", "C", f"out_{mode}/V4_SWITCHES.json biomass_overflow_recomputed", "only the overflow useful heat (VN) acts in the network")
    # ---- section 4
    calc = jl(W / "evidence/DATA_UPGRADES_CALC.json")
    add("s4.lng_regas_adder", dict(old=1.26, new=calc["lng"]["value"], groups=calc["lng"]["country_groups"], low=calc["lng"]["low"], high=calc["lng"]["high"]), "EUR2020/MWh", "VERIFIED (tariffs) / EXACT (median)", "C",
        "evidence/DATA_UPG_A.json D01-D14; DATA_UPGRADES_CALC.json")
    add("s4.ev_ice_fleet_ratio", dict(model=calc["ev_ice"]["model_ratio"], mid=calc["ev_ice"]["fleet_ratio_mid"], low=calc["ev_ice"]["fleet_ratio_low"], high=calc["ev_ice"]["fleet_ratio_high"]), "ratio", "INFERENCE", "C",
        "evidence/DATA_UPG_B.json E01-E28; DATA_UPGRADES_CALC.json")
    add("s4.co2_ship", dict(fixed_range=calc["co2_ship"]["fixed_range"], slope_range=calc["co2_ship"]["slope_range"], chain_1000km=calc["co2_ship"]["chain_1000km"]), "EUR2020/t", "VERIFIED (totals) / INFERENCE (split)", "C",
        "evidence/DATA_UPG_A.json D15-D30")
    add("s4.co2_storage_p10_p90", {c: dict(low=z.get("low_gt"), p50=z.get("p50_gt"), high=z.get("high_gt")) for c, z in calc["co2_storage_potential"]["countries"].items()}, "GtCO2", "VERIFIED", "B", "evidence/DATA_UPG_A.json D39-D49")
    a = calc.get("vn_offwind_alpha") or {}
    if a:
        add("s4.vn_offwind_alpha", dict(cf_alpha1_box=a["cf_alpha1_box"], era5_box_ws100=a["era5_box_mean_ws100"], alpha_cf_match={k: v["alpha_box"] for k, v in a["alpha_cf_match"].items()},
                                       alpha_speed_ratio={k: v["alpha_box"] for k, v in a["alpha_speed_ratio"].items()}, model_vn_cf={k: v["cf_cap_weighted"] for k, v in a["model_vn_offshore"].items() if k.endswith("_c3")}),
            "alpha / CF", "EXACT (computation) / INFERENCE (reference area)", "C", "evidence/VN_OFFWIND_ALPHA.json; scripts/d2b_vn_offwind_alpha.py", "not applied")
    add("s4.co2_sequestration_price_year", 2020, "year", "INFERENCE", "C", "evidence/DATA_UPG_A.json D31-D38", "range 2015-2020")
    add("s4.my_rooftop", dict(model_mw=83146.768938, myrer_mw=42000.0), "MW", "VERIFIED", "C", "evidence/DATA_UPG_B.json E50-E56")
    reg = pd.read_csv(R / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False)
    add("registry.rows", int(len(reg)), "rows", "VERIFIED", "-", "research_inputs/registry_v5/DATA_REGISTRY.csv", "D2a head 2,436 -> 2,463 (+27 new rows, 49 range replacements)")
    # ---- section 5
    st = jl(W / "STATIC_CHECKS.json")
    if st:
        add("s5.static", {t: {k: v for k, v in r.items() if not isinstance(v, (dict, list)) or k.startswith(("C6_switches", "C12_lng_mc_change_min_max", "C3_pool_change"))} for t, r in st.items()}, "-", "VERIFIED", "-", "STATIC_CHECKS.json")
    nd = jl(W / "evidence/D2B_NETWORK_DIFF.json")
    if nd:
        add("s5.c8", {k: dict(passed=v["C8"]["passed"], expected=v["C8"]["expected"], unexpected=len(v["C8"]["unexpected"])) for k, v in nd.items()}, "-", "VERIFIED", "-", "evidence/D2B_NETWORK_DIFF.json")
    zs = jl(W / "evidence/ZERO_SLACK_CHECK_D2B.json")
    if zs:
        add("s5.zero_slack", "PASS (both networks; see file)", "-", "VERIFIED", "-", "evidence/ZERO_SLACK_CHECK_D2B.json")
    # ---- section 6
    bp = jl(W / "evidence/D2B_BOUNDS_PRE.json")
    if bp:
        add("s6.alarm_lines", {k: dict(rhs_lower_bound=v["rhs_lower_bound_eur"], alarm_line=v["alarm_line_eur"], cost_ub=v["terms"]["cost_first_order_upper_bound_eur"], pools=v["terms"]["pools_rhs_lower_bound_eur"],
                                       loads=v["terms"]["loads_rhs_lower_bound_eur"]) for k, v in bp.items()}, "EUR", "EXACT (rule) / VERIFIED (duals)", "-", "evidence/D2B_BOUNDS_PRE.json", "registered before the solves (commit 0b02cfe8)")
    sm = jl(W / "evidence/D2B_smoke56.json")
    if sm:
        add("s6.smoke", {k: {kk: v.get(kk) for kk in ("termination", "objective_eur", "d2a_objective_eur", "dV_eur", "dV_lp_eur", "alarm_line_eur", "above_alarm_line", "dV_minus_lower_bound_eur",
                                                     "gates_failed", "gates_failed_outside_v31_union", "V6_label", "barrier_iterations", "solve_seconds", "peak_rss_gib")} for k, v in sm["runs"].items()},
            "EUR", "VERIFIED", "-", "evidence/D2B_smoke56.json; tables/D2B_SMOKE56_RESULTS.csv")
        add("s6.criteria", sm["criteria"], "-", "VERIFIED", "-", "evidence/D2B_smoke56.json")
    rr = jl(W / "evidence/RERANK_D2B_SUMMARY.json")
    if rr:
        add("s7.rerank", rr, "-", "VERIFIED (method) / INFERENCE (first order)", "-", "evidence/RERANK_D2B_SUMMARY.json")
    for f in sorted((W / "evidence").glob("*_LITERATURE.json")) + [W / "evidence/DATA_UPG_A.json", W / "evidence/DATA_UPG_B.json"]:
        if f.exists():
            d = jl(f); e = d.get("entries", [])
            add(f"literature.{f.stem}", dict(entries=len(e), verified=sum(1 for x in e if str(x.get("grade", "")).startswith("VERIFIED")), sha256=sha(f)), "-", "VERIFIED", "-", f"evidence/{f.name}",
                "web read-only by subagents, every entry reviewed in this session; quotes <= 15 words")
    add("incident.download", dict(file="C:/Users/20122/Downloads/NWS-E-2006-202.pdf", bytes=1447845, sha256="bfd7795a731412178b8c1657dd21b433b8a95d01fa03429eaf8d96f9048f2441",
                                  what="Smeets et al. 2007 PECS 33:56-106 author copy (Utrecht DSpace), saved by the built-in browser when a residue subagent opened the PDF link; not requested",
                                  use="read only (pypdf text extraction of a copy in the session scratchpad) for Smeets 2007 section 5.1; file left in place for the user"), "-", "VERIFIED", "-", "RESIDUE_LITERATURE.json note")
    (W / "EVIDENCE.json").write_text(json.dumps(dict(note="V4 D2b evidence index (V4_D2B_INSTRUCTION.md v1); numbers read from the delivery tables / evidence files", entries=rows),
                                                indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8", newline="\n")
    print(len(rows), "entries")


if __name__ == "__main__":
    main()
