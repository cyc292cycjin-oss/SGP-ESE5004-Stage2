"""GATES_V6 (decision 128; M08a A8, decision 133): post-solve acceptance from the returned solution and the exported files only.

Definition: research/06_scope_redesign/p1_step4r_20261020/GATES_V6.md (SHA256 GATES_V6_SHA256 below, unchanged) and GATES_V6_NOTES.md
(D2 budget multiplier k = 10 kept). Criteria (go / no-go): G1 = C1 (a)(b)(c) of decision 119 (PRECISION.json of
scripts_project/s4o_c1_precision.py) and G2 structural checks - G2.1 network identity, G2.2 configuration-subset hash, G2.3 result
completeness. Everything else is a diagnostic D0-D16 (reported, never deciding); budgets "absolute + relative" tied to the profile
tolerances: D2 = k x max(OptimalityTol, BarConvTol). Labels ACCEPTED_LAYER2 (all pass), ACCEPTED_LAYER1 (G1c fails, rest pass),
NOT_ACCEPTED. The solver status is not a criterion (D0 records it). Never calls a solver.

Pre-registered run rules for the unattended third / fourth batches (research.solver.run_rules): select_formal_profile (profile chain:
formal_barrier_1e6_t16 if its 365x24h level-2 runs pass C1 (a)(b)(c) and stay within 1e-5 of profile A, else profile A; the 1e-5
profile is never a fallback), formal_run_decision (formal 2920x3h runs must pass C1 (c); TimeLimit 48 h; no retry, no parameter
change - a non-converged run is graded by C1 as it is).

    python scripts_project/v5/gates_v6.py accept --solve-dir <run dir> [--registered-sha256 <sha> | --build-receipt <json>] [--repo .]
    python scripts_project/v5/gates_v6.py select-profile --level2 <json> [--repo .]
    python scripts_project/v5/gates_v6.py formal-check --acceptance <V6_ACCEPTANCE.json> [--repo .]
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

GATES_V6_SHA256 = "5c0aa8b8ed322b75a63879fccfc19559606a0ad743ecafee3addfcbfe04fd7f9"
K = 10.0            # budget multiplier (S4B-0 option 1; GATES_V6_NOTES section 4: kept)
ABS = 1e-3          # absolute floor in V4 native units
GUROBI_DEFAULTS = dict(FeasibilityTol=1e-6, OptimalityTol=1e-6, BarConvTol=1e-8)
LABELS = ("ACCEPTED_LAYER2", "ACCEPTED_LAYER1", "NOT_ACCEPTED")
# G2.2: the research-config keys that decide the network and the LP (GATES_V6.md section 2, literal list) ...
SUBSET_KEYS_GATES_V6 = ("scenario", "cross_border", "fuels.price_scenario", "finance", "sector", "s3", "renewable", "fleet", "nuclear", "candidates", "hydro",
                        "hydrogen", "cost_layer.active", "numerics", "network", "corridors", "bunkers", "co2", "s2", "cost_scaling", "carbon", "demand",
                        "transmission", "existing_cross_border_electricity", "solver.scaling", "solver.interior")
# ... plus the keys that also change the network / LP but are not in that list (M08a A8, by the G2.2 purpose "the configuration subset that
# decides the network and the LP"; GATES_V6.md unchanged, listed for the user's confirmation): the whole cost_layer (rebase_index, layer files,
# smr_cost_source, aeo8_price_year_factor - the literal list has cost_layer.active only), site_candidates, and the new variant sections
# disconnected / coalition (decision 132). Excluded as in GATES_V6: solver.profile, solver.profiles, solver.acceptance, solver.run_rules,
# stage / status labels, config_overrides (their effect is in the values).
SUBSET_KEYS_M08A_ADDITIONS = ("cost_layer", "site_candidates", "disconnected", "coalition")
SUBSET_KEYS = SUBSET_KEYS_GATES_V6 + SUBSET_KEYS_M08A_ADDITIONS
# D2 history (GATES_V6_NOTES section 2, VERIFIED maxima of the D2 ratio under the V6 budget) for the anomaly note of section 4
D2_HISTORY_MAX = {("56x3h", 1e-8): 0.24, ("56x3h", 1e-6): 19.3, ("56x3h", 1e-5): 769.0, ("365x24h", 1e-8): 33378.0}


# --------------------------------------------------------------------------------------------- G2.2 configuration subset
def _get(R: dict, dotted: str):
    d = R
    for k in dotted.split("."):
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def config_subset(R: dict) -> dict:
    """Canonical subset {dotted key: value} of the research config (absent keys -> null)."""
    return {k: _get(R, k) for k in sorted(set(SUBSET_KEYS))}


def config_subset_sha256(R: dict) -> str:
    return hashlib.sha256(json.dumps(config_subset(R), sort_keys=True, default=str).encode()).hexdigest()


# --------------------------------------------------------------------------------------------- tolerances and budgets
def tolerances(params: dict | None) -> dict:
    p = dict(GUROBI_DEFAULTS, **{k: float(v) for k, v in (params or {}).items() if k in GUROBI_DEFAULTS})
    return dict(eps_f=p["FeasibilityTol"], eps_o=p["OptimalityTol"], eps_b=p["BarConvTol"], eps_d=max(p["OptimalityTol"], p["BarConvTol"]))


def d2_budget(params: dict | None, k: float = K) -> float:
    """D2 dual budget = k x max(OptimalityTol, BarConvTol) (GATES_V6 section 3; S4Q finding 1)."""
    return k * tolerances(params)["eps_d"]


def within_cap(value, cap, eps_f: float, k: float = K) -> tuple[bool, float | None]:
    """D7 / D9 / D10: value <= cap (1 + k eps_f) + 1e-3; inf caps always within."""
    if value is None or cap is None:
        return True, None
    cap = float(cap); value = float(value)
    if math.isinf(cap):
        return True, 0.0
    budget = cap * (1 + k * eps_f) + ABS
    return value <= budget, (value / budget if budget else 0.0)


def resolution(receipt: dict) -> str:
    s = int(((receipt or {}).get("input_network") or {}).get("snapshots") or 0)
    return {56: "56x3h", 365: "365x24h", 2920: "2920x3h"}.get(s, f"{s} snapshots")


# --------------------------------------------------------------------------------------------- files
def _jl(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _first(d: Path, *names):
    for nm in names:
        if (d / nm).exists():
            return d / nm
    return None


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# --------------------------------------------------------------------------------------------- criteria
def g1(prec: dict | None) -> dict:
    if not prec or prec.get("computable") is False:
        return dict(computable=False, a=False, b=False, c=False, note="PRECISION.json missing or not computable")
    return dict(computable=True, a=bool((prec.get("a_total_cost") or {}).get("passed")), b=bool((prec.get("b_primal_violations") or {}).get("passed")),
                c=bool((prec.get("c_prices") or {}).get("passed")),
                a_relative=(prec.get("a_total_cost") or {}).get("returned_relative"), a_bn=(prec.get("a_total_cost") or {}).get("returned_difference_bn"),
                reference=str((prec.get("reference") or {}).get("source", ""))[:120])


def g2_1(receipt: dict | None, gates: dict | None, registered_sha: str | None) -> dict:
    actual = ((receipt or {}).get("input_network") or {}).get("sha256")
    a4 = (gates or {}).get("A4") or {}
    ident = (registered_sha is not None) and (actual == registered_sha)
    readback = bool(a4.get("passed")) and a4.get("status") == "EXACT_SEMANTIC_ROUNDTRIP"
    return dict(passed=bool(ident and readback), input_network_sha256=actual, registered_sha256=registered_sha, sha256_equal=ident,
                readback=a4.get("status"), note=(None if registered_sha else "no registered SHA256 given (package SHA256SUMS / BUILD_RECEIPT)"))


def g2_2(receipt: dict | None) -> dict:
    c = (receipt or {}).get("config_subset") or {}
    net, cur = c.get("network"), c.get("current")
    return dict(passed=bool(net) and net == cur, network_subset_sha256=net, current_subset_sha256=cur,
                note=(None if net else "network has no research_config_subset_sha256 (built before M08a A8)"))


def g2_3(solve_dir: Path, receipt: dict | None, gates: dict | None) -> dict:
    checks = {}
    rec = receipt or {}
    ex = _jl(solve_dir / "EXPORTS.json") or rec.get("exports") or {}
    bad = []
    for nm, v in ex.items():
        p = solve_dir / nm
        if not p.exists() or (isinstance(v, dict) and v.get("sha256") and _sha(p) != v["sha256"]):
            bad.append(nm)
    checks["exports_present_and_sha256_equal"] = bool(ex) and not bad
    lp = rec.get("lp") or {}; sol = rec.get("solution") or {}
    dims = {}
    for key, want in (("X", lp.get("num_col")), ("Pi", lp.get("num_row")), ("RC", lp.get("num_col"))):
        got = (sol.get(key) or {}).get("count")
        dims[key] = dict(count=got, lp=want, equal=(got is not None and want is not None and int(got) == int(want)))
    checks["solution_dimensions_equal_lp"] = all(d["equal"] for d in dims.values())
    b16 = (gates or {}).get("B16_LEDGER") or {}
    checks["b16_computable"] = b16.get("relative_error") is not None
    checks["receipt_fields"] = all(rec.get(k) is not None for k in ("solver_parameters", "termination_condition", "objective")) and bool((rec.get("input_network") or {}).get("sha256"))
    return dict(passed=all(checks.values()), checks=checks, missing_or_changed_exports=bad[:10], solution_dimensions=dims)


# --------------------------------------------------------------------------------------------- diagnostics
def diagnostics(receipt: dict | None, gates: dict | None, kkt: dict | None, interior: dict | None) -> dict:
    rec = receipt or {}; G = gates or {}
    tol = tolerances(rec.get("solver_parameters")); res = resolution(rec)
    D = {}
    D["D0_solver_status"] = dict(termination=rec.get("termination_condition"), status=rec.get("status"), retry=rec.get("retry"), solve_seconds=rec.get("solve_seconds"),
                                 time_limit=(rec.get("solver_parameters") or {}).get("TimeLimit"))
    a = G.get("A1_A2_S4B") or {}
    rr = a.get("row_max_ratio_to_budget")
    D["D1_primal"] = dict(within=(rr <= 1.0) if rr is not None else None, max_ratio=rr, fail_count=a.get("row_fail_count"))
    bud = K * tol["eps_d"]; ds, st = a.get("dual_sign_normalized_max"), a.get("stationarity_normalized_max")
    ratio = max(x for x in (ds, st, 0.0) if x is not None) / bud if (ds is not None or st is not None) else None
    hist = D2_HISTORY_MAX.get((res, tol["eps_b"]))
    D["D2_dual"] = dict(budget=bud, k=K, eps_d=tol["eps_d"], dual_sign_max=ds, stationarity_max=st, max_ratio=ratio,
                        within=(ratio <= 1.0) if ratio is not None else None, history_max_ratio=hist,
                        anomaly=(bool(ratio is not None and hist is not None and ratio > 10 * hist)),
                        note="diagnostic only (GATES_V6_NOTES): interior-point solutions without crossover exceed k = 10 routinely")
    gap = a.get("relative_gap", (kkt or {}).get("relative_gap")); comp = a.get("complementarity_over_scale")
    D["D3_gap_complementarity"] = dict(budget=10 * tol["eps_b"], relative_gap=gap, complementarity_over_scale=comp,
                                       within=(all(x <= 10 * tol["eps_b"] for x in (gap, comp) if x is not None) if (gap is not None or comp is not None) else None))
    for code, key in (("D4_physics", "A3_S4B"), ("D5_objective_reconciliation", "A5_S4B"), ("D6_country_net_zero", "B1_S4B"), ("D8_biomass_pools", "B3_S4B"),
                      ("D11_demand_conservation", "B8"), ("D12_supply_routes", "B11"), ("D13_imports_one_way", "B13"), ("D16_whole_config_hash", "B12")):
        g = G.get(key)
        D[code] = dict(source=key, within=(None if g is None else (str(g.get("passed")) == "True")))
    rows = []   # D7 storage caps (B2 rows) with the V6 tolerance
    for c, r in ((G.get("B2") or {}).get("countries") or {}).items():
        ok, q = within_cap(r.get("final_level_t"), r.get("horizon_limit_t"), tol["eps_f"])
        rows.append((c, ok, q))
    D["D7_storage_caps"] = dict(items=len(rows), within=all(x[1] for x in rows) if rows else None, worst_ratio=max([x[2] or 0.0 for x in rows], default=None))
    rows = []   # D9 terminal caps (B14 rows)
    for r in (G.get("B14") or {}).get("terminals") or []:
        ok, q = within_cap(r.get("p_nom_opt_mw"), r.get("p_nom_max_mw"), tol["eps_f"])
        rows.append((r.get("generator"), ok, q))
    D["D9_terminal_caps"] = dict(items=len(rows), within=all(x[1] for x in rows) if rows else None, worst_ratio=max([x[2] or 0.0 for x in rows], default=None),
                                 expansion=(G.get("B14") or {}).get("expansion"))
    rows = []   # D10 domestic gas production (B15 by country)
    for c, r in ((G.get("B15") or {}).get("by_country") or {}).items():
        ok, q = within_cap(r.get("annual_mwh"), r.get("cap_mwh"), tol["eps_f"])
        rows.append((c, ok, q))
    D["D10_domestic_gas_caps"] = dict(items=len(rows), within=all(x[1] for x in rows) if rows else None, worst_ratio=max([x[2] or 0.0 for x in rows], default=None))
    D["D14_scenario_pair"] = dict(within=None, note="B5 / B6 need both scenarios (pair report)")
    D["D15_interior_cleanup"] = dict(within=None if interior is None else bool((interior or {}).get("interior_solution", True)), keys=sorted(interior or {})[:5])
    return D


# --------------------------------------------------------------------------------------------- acceptance
def label(G1: dict, G2: dict) -> str:
    g2 = all(G2[k]["passed"] for k in ("G2_1", "G2_2", "G2_3"))
    if not (G1["a"] and G1["b"] and g2):
        return "NOT_ACCEPTED"
    return "ACCEPTED_LAYER2" if G1["c"] else "ACCEPTED_LAYER1"


def acceptance_v6(solve_dir: Path, registered_sha: str | None = None) -> dict:
    d = Path(solve_dir)
    rec = _jl(d / "SOLVE_RECEIPT.json"); gates = _jl(d / "V5_GATES.json"); kkt = _jl(_first(d, "kkt_summary.json", "v5/kkt_summary.json") or d / "-")
    prec = _jl(d / "PRECISION.json"); inter = _jl(d / "INTERIOR_CHECKS.json")
    G1 = g1(prec)
    G2 = dict(G2_1=g2_1(rec, gates, registered_sha), G2_2=g2_2(rec), G2_3=g2_3(d, rec, gates))
    lab = label(G1, G2)
    return dict(schema="gates-v6-acceptance-v1", definition=dict(file="research/06_scope_redesign/p1_step4r_20261020/GATES_V6.md", sha256=GATES_V6_SHA256,
                notes="GATES_V6_NOTES.md (k = 10 kept)", subset_keys=list(SUBSET_KEYS), subset_keys_m08a_additions=list(SUBSET_KEYS_M08A_ADDITIONS)),
                solve_dir=str(d), resolution=resolution(rec), profile=(rec or {}).get("solver_profile"), label=lab, G1=G1, G2=G2,
                diagnostics=diagnostics(rec, gates, kkt, inter), solver_runs=0)


# --------------------------------------------------------------------------------------------- pre-registered run rules
DEFAULT_RUN_RULES = dict(acceptance="gates_v6", formal_resolution="2920x3h", formal_requires=["c"], formal_time_limit_s=172800.0,
                         on_non_convergence="grade_by_c1_no_retry_no_parameter_change",
                         profile_chain=dict(candidate="formal_barrier_1e6_t16", level2_resolution="365x24h", candidate_requires=["a", "b", "c"],
                                            objective_rel_diff_vs_reference_max=1e-5, reference="formal_barrier", fallback="formal_barrier",
                                            never_fallback=["pypsa_eur_default"]))


def run_rules(cfg: dict | None) -> dict:
    r = copy.deepcopy(DEFAULT_RUN_RULES)
    given = (((cfg or {}).get("research") or {}).get("solver") or {}).get("run_rules") or {}
    for k, v in given.items():
        if isinstance(v, dict) and isinstance(r.get(k), dict):
            r[k].update(v)
        else:
            r[k] = v
    return r


def select_formal_profile(level2: dict, rules: dict) -> dict:
    """Profile chain (pre-registered): level2 = {scenario: {"candidate": {"precision": PRECISION or {"a","b","c"}, "objective": x, "profile": p},
    "reference": {"objective": y, "profile": "formal_barrier"}}}. Candidate chosen only if EVERY listed scenario has C1 (a)(b)(c) and
    |x - y| / |y| <= 1e-5; otherwise the fallback (profile A). The 1e-5 profile is never chosen."""
    ch = rules["profile_chain"]
    rows, ok = {}, bool(level2)
    for sc, v in sorted((level2 or {}).items()):
        cand, ref = v.get("candidate") or {}, v.get("reference") or {}
        if cand.get("profile", ch["candidate"]) != ch["candidate"] or ref.get("profile", ch["reference"]) != ch["reference"]:
            raise ValueError(f"{sc}: level-2 profiles must be {ch['candidate']} vs {ch['reference']}")
        p = cand.get("precision") or {}
        flags = {k: bool(p.get(k)) if k in p else bool(g1(p).get(k)) for k in ("a", "b", "c")}
        x, y = cand.get("objective"), ref.get("objective")
        rel = abs(float(x) - float(y)) / abs(float(y)) if (x is not None and y not in (None, 0)) else None
        passed = all(flags[k] for k in ch["candidate_requires"]) and rel is not None and rel <= float(ch["objective_rel_diff_vs_reference_max"])
        rows[sc] = dict(c1=flags, objective_rel_diff=rel, passed=bool(passed)); ok &= bool(passed)
    chosen = ch["candidate"] if ok else ch["fallback"]
    if chosen in ch["never_fallback"]:
        raise AssertionError("the 1e-5 profile is never a fallback")
    return dict(profile=chosen, candidate=ch["candidate"], reference=ch["reference"], level2=rows,
                reason=("candidate passed C1 (a)(b)(c) and the 1e-5 objective criterion in every level-2 scenario" if ok else
                        ("no level-2 results" if not level2 else "candidate failed in at least one level-2 scenario -> profile A")))


def formal_run_decision(acc: dict, rules: dict) -> dict:
    """Formal 2920x3h runs: usable for the allocation only with C1 (c) (Owen allocation uses the duals); a non-converged run is graded
    by C1 as it is (no retry, no parameter change)."""
    lab = acc["label"]; formal = acc.get("resolution") == rules["formal_resolution"]
    need = all(bool(acc["G1"].get(k)) for k in rules["formal_requires"])
    usable = (lab == "ACCEPTED_LAYER2") if formal else (lab != "NOT_ACCEPTED")
    return dict(formal=formal, label=lab, requires=rules["formal_requires"], requires_met=need, usable_for_allocation=bool(formal and usable and need),
                usable_total_cost_only=bool(formal and lab == "ACCEPTED_LAYER1"), retry=False, parameter_change=False,
                time_limit_s=rules["formal_time_limit_s"], termination=acc["diagnostics"]["D0_solver_status"]["termination"],
                rule=rules["on_non_convergence"])


def _config(repo: Path):
    import sys
    sys.path.insert(0, str(Path(repo) / "scripts_project"))
    from phase4_static import config
    return config(Path(repo), "integrated")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("accept"); a.add_argument("--solve-dir", type=Path, required=True); a.add_argument("--registered-sha256"); a.add_argument("--build-receipt", type=Path)
    a.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2]); a.add_argument("--out", type=Path)
    s = sub.add_parser("select-profile"); s.add_argument("--level2", type=Path, required=True); s.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    f = sub.add_parser("formal-check"); f.add_argument("--acceptance", type=Path, required=True); f.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    x = ap.parse_args()
    if x.cmd == "accept":
        reg = x.registered_sha256
        if reg is None and x.build_receipt:
            br = _jl(x.build_receipt) or {}
            rec = _jl(x.solve_dir / "SOLVE_RECEIPT.json") or {}
            snaps = int(((rec.get("input_network") or {}).get("snapshots")) or 0)
            reg = ((br.get("daily_network") or {}).get("sha256") if snaps and snaps <= 365 and (br.get("daily_network") or {}).get("snapshots") == 365
                   else (br.get("network") or {}).get("sha256"))
        acc = acceptance_v6(x.solve_dir, reg)
        out = x.out or (x.solve_dir / "V6_ACCEPTANCE.json")
        out.write_text(json.dumps(acc, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
        print(acc["label"])
    elif x.cmd == "select-profile":
        print(json.dumps(select_formal_profile(_jl(x.level2) or {}, run_rules(_config(x.repo))), indent=1, default=str))
    else:
        print(json.dumps(formal_run_decision(_jl(x.acceptance), run_rules(_config(x.repo))), indent=1, default=str))


if __name__ == "__main__":
    main()
