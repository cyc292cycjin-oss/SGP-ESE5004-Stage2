"""S4L-2 summary (S4L instruction S4L-2 points 3-5; decision 113 (2)): the 56x3h diagnostic matrix {S4K-3 network, S4L-1 cleaned network} x
{formal_barrier (A), formal_barrier_crossover (X)} x {integrated, disconnected} against the standard fixed before the runs (registry s4l2_comparison_standard):
reference = S4K network + profile A; per combination and scenario |objective / ref - 1| <= 1e-5; B16 <= 1e-6 per run; per country the change of the
'disconnected - integrated' ledger difference <= max(1 % of the reference difference, 0.01 bn EUR). Also: termination, barrier / crossover times,
gates (all_passed_solver_tolerances, A1_A2, B2, B14, B15, B16), nodal prices by country (AC and H2: mean of the bus means, quantiles), LP size, and
the repeat check of the S4K network + A runs against the S4K-3 solves. Reads receipts, gates, ledgers and price tables only (no solve).

    python scripts_project/s4l_2_summary.py --run results_project/s4l/s4l2 --s4k3 results_project/s4k/s4k3
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

NETS = ("s4k", "s4l"); PROFS = ("A", "X"); SCEN = ("integrated", "disconnected")
PROFILE = {"A": "formal_barrier", "X": "formal_barrier_crossover"}
STANDARD = dict(reference="s4k_A", objective_rel_tol=1e-5, b16_tol=1e-6, country_pct=0.01, country_floor_bn_eur=0.01,
                source="S4L instruction S4L-2 point 4; registry s4l2_comparison_standard; fixed before any run")
COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
ENTITIES = COUNTRIES + ("ASEAN_BUNKER",)


def jl(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else {}


def parse_log(p: Path) -> dict:
    out = dict(barrier_iterations=None, barrier_seconds=None, barrier_work_units=None, solved_in_iterations=None, solved_in_seconds=None, solved_with=None,
               crossover_present=False, push_phases=0, extra_simplex_iterations=None, result_line=None, warnings=[])
    if not p.exists():
        return out
    for line in p.read_text(errors="ignore").splitlines():
        m = re.match(r"Barrier solved model in (\d+) iterations and ([\d.]+) seconds(?: \(([\d.]+) work units\))?", line)
        if m:
            out.update(barrier_iterations=int(m.group(1)), barrier_seconds=float(m.group(2)), barrier_work_units=(float(m.group(3)) if m.group(3) else None))
        m = re.match(r"Barrier performed (\d+) iterations in ([\d.]+) seconds", line)   # non-optimal barrier
        if m and out["barrier_iterations"] is None:
            out.update(barrier_iterations=int(m.group(1)), barrier_seconds=float(m.group(2)))
        if line.startswith("Crossover log"):
            out["crossover_present"] = True
        if line.startswith("Push phase complete"):
            out["push_phases"] += 1
        m = re.match(r"Extra simplex iterations after uncrush: (\d+)", line)
        if m:
            out["extra_simplex_iterations"] = int(m.group(1))
        m = re.match(r"Solved with (.+)", line)
        if m:
            out["solved_with"] = m.group(1).strip()
        m = re.match(r"Solved in (\d+) iterations and ([\d.]+) seconds", line)
        if m:
            out.update(solved_in_iterations=int(m.group(1)), solved_in_seconds=float(m.group(2)))
        if re.match(r"^(Optimal objective|Sub-optimal termination|Time limit reached|Model is infeasible|Model is unbounded|Infeasible or unbounded|Numerical trouble|Barrier solved)", line):
            out["result_line"] = line.strip()[:160]
        if line.startswith("Warning:"):
            out["warnings"].append(line.strip()[:160])
    if out["solved_in_seconds"] is not None and out["barrier_seconds"] is not None:
        out["crossover_plus_simplex_seconds"] = round(out["solved_in_seconds"] - out["barrier_seconds"], 2)
        out["crossover_over_barrier"] = round(out["crossover_plus_simplex_seconds"] / out["barrier_seconds"], 3) if out["barrier_seconds"] else None
    return out


def run_row(d: Path, tag: str) -> dict:
    r = jl(d / "SOLVE_RECEIPT.json"); g = jl(d / "V5_GATES.json"); lg = parse_log(d / "GUROBI_LOG_SCRUBBED.txt")
    gp = lambda k: (g.get(k) or {}).get("passed") if isinstance(g.get(k), dict) else None
    row = dict(tag=tag, termination=r.get("termination_condition", "none" if r else "missing"), status=r.get("status"), objective=r.get("objective"), objective_lp=r.get("objective_lp"),
               solve_seconds=r.get("solve_seconds"), build_seconds=(r.get("lp") or {}).get("build_seconds"), num_col=(r.get("lp") or {}).get("num_col"), num_row=(r.get("lp") or {}).get("num_row"),
               nnz=(r.get("lp") or {}).get("nnz"), peak_rss_gib=(r["peak_rss_bytes"] / 2**30 if r.get("peak_rss_bytes") else None), crossover_param=(r.get("solver_parameters") or {}).get("Crossover"),
               dust_mode=(r.get("dust_cleanup") or {}).get("mode"), failure=(r.get("failure") or {}).get("error"),
               all_passed_solver_tolerances=g.get("all_passed_solver_tolerances"), all_passed_barconvtol=g.get("all_passed_barconvtol"),
               A1_A2_gate=(g.get("A1_A2") or {}).get("gate"), A1_A2=gp("A1_A2"), A1_A2_S4B=gp("A1_A2_S4B"), A3_S4B=gp("A3_S4B"), B1_S4B=gp("B1_S4B"), B3_S4B=gp("B3_S4B"),
               B2=gp("B2"), B14=gp("B14"), B15=gp("B15"), B16=gp("B16_LEDGER"), B16_relative_error=(g.get("B16_LEDGER") or {}).get("relative_error"),
               A1_A2_relative_gap=((g.get("A1_A2") or {}).get("relative_gap") if isinstance(g.get("A1_A2"), dict) else None))
    row.update({k: v for k, v in lg.items() if k != "warnings"}); row["gurobi_warnings"] = len(lg["warnings"])
    from s4b_acceptance import S4B_MAIN_SET   # the gate set behind all_passed_solver_tolerances (decision 71)
    failed_all = sorted(k for k, v in g.items() if isinstance(v, dict) and v.get("passed") is False)
    failed = [k for k in S4B_MAIN_SET if isinstance(g.get(k), dict) and g[k].get("passed") is False]
    row["failed_gates_all_bases"] = failed_all; row["failed_gates_solver_tolerance_set"] = failed
    # B12 compares the network's research_config_sha256 (frozen at build time) with the CURRENT config hash: the S4K-3 networks were built before
    # the S4L config additions (research.numerics, the formal_barrier_crossover profile), so B12 fails for them by construction (not a solver matter)
    row["failed_gates_excluding_B12"] = [k for k in failed if k != "B12"]
    row["all_passed_solver_tolerances_excl_B12"] = (len(row["failed_gates_excluding_B12"]) == 0) if g else None
    return row


def ledger_totals(d: Path) -> pd.Series:
    p = d / "COUNTRY_COST_LEDGER.csv"
    if not p.exists():
        return pd.Series(dtype=float)
    t = pd.read_csv(p, index_col=0)
    return (t["total"] / 1e9).reindex(list(ENTITIES))


def prices(d: Path) -> dict:
    p = d / "NODAL_PRICES.csv"
    if not p.exists():
        return {}
    t = pd.read_csv(p); out = {}
    for car in ("AC", "H2"):
        s = t[t.carrier == car]
        if not len(s):
            continue
        for c, g in s.groupby("country"):
            out[f"{car}|{c}"] = dict(carrier=car, country=c, buses=int(len(g)), mean_of_bus_means=float(g["mean"].mean()), p10=float(g["mean"].quantile(0.1)),
                                     p50=float(g["mean"].median()), p90=float(g["mean"].quantile(0.9)), max_bus_mean=float(g["mean"].max()), max_bus_max=float(g["max"].max()), min_bus_min=float(g["min"].min()))
    return out


def bus_means(d: Path, car: str) -> pd.Series:
    p = d / "NODAL_PRICES.csv"
    if not p.exists():
        return pd.Series(dtype=float)
    t = pd.read_csv(p); s = t[t.carrier == car]
    return pd.Series(s["mean"].to_numpy(), index=s.bus.to_numpy())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", type=Path, required=True); ap.add_argument("--s4k3", type=Path, required=True)
    a = ap.parse_args()
    out = a.run / "analysis"; out.mkdir(parents=True, exist_ok=True)
    runs = {}; ledg = {}; pr = {}
    for net in NETS:
        for p in PROFS:
            for sc in SCEN:
                tag = f"{net}_{p}_{sc}"; d = a.run / "solves" / tag
                runs[tag] = run_row(d, tag); ledg[tag] = ledger_totals(d); pr[tag] = prices(d)
    R = pd.DataFrame(runs).T; R.to_csv(out / "S4L2_RUNS.csv")
    res = dict(standard=STANDARD, profiles=PROFILE, runs=runs, status=[x for x in (a.run / "STATUS.txt").read_text().splitlines() if "PROJ" not in x] if (a.run / "STATUS.txt").exists() else [],
               combinations={}, ledger_differences={}, prices_by_country={}, price_differences={}, lp_size={}, repeat_vs_s4k3={})
    # ledger differences (disconnected - integrated) per combination, bn EUR
    diffs = {}
    for net in NETS:
        for p in PROFS:
            li, ld = ledg[f"{net}_{p}_integrated"], ledg[f"{net}_{p}_disconnected"]
            diffs[f"{net}_{p}"] = (ld - li) if len(li) and len(ld) else pd.Series(np.nan, index=list(ENTITIES))
    D = pd.DataFrame(diffs); D.index.name = "entity"; D.to_csv(out / "S4L2_LEDGER_DIFF.csv", float_format="%.6f")
    ref = diffs["s4k_A"]
    for combo, dd in diffs.items():
        ri, rd = runs[f"{combo}_integrated"], runs[f"{combo}_disconnected"]
        oi, od = runs["s4k_A_integrated"]["objective"], runs["s4k_A_disconnected"]["objective"]
        obj = {sc: (abs(runs[f"{combo}_{sc}"]["objective"] / runs[f"s4k_A_{sc}"]["objective"] - 1) if (runs[f"{combo}_{sc}"]["objective"] and runs[f"s4k_A_{sc}"]["objective"]) else None) for sc in SCEN}
        b16 = {sc: runs[f"{combo}_{sc}"]["B16_relative_error"] for sc in SCEN}
        tol = {c: max(STANDARD["country_pct"] * abs(float(ref.get(c, np.nan))), STANDARD["country_floor_bn_eur"]) for c in ENTITIES}
        chg = {c: (float(dd.get(c)) - float(ref.get(c))) if (pd.notna(dd.get(c)) and pd.notna(ref.get(c))) else None for c in ENTITIES}
        cpass = {c: (abs(chg[c]) <= tol[c]) if chg[c] is not None else None for c in ENTITIES}
        res["combinations"][combo] = dict(
            network=combo.split("_")[0], profile=PROFILE[combo.split("_")[1]], terminations={sc: runs[f"{combo}_{sc}"]["termination"] for sc in SCEN},
            all_passed_solver_tolerances={sc: runs[f"{combo}_{sc}"]["all_passed_solver_tolerances"] for sc in SCEN},
            objective={sc: runs[f"{combo}_{sc}"]["objective"] for sc in SCEN}, objective_rel_diff_vs_ref=obj,
            objective_within=({sc: (v is not None and v <= STANDARD["objective_rel_tol"]) for sc, v in obj.items()} if combo != "s4k_A" else "reference"),
            B6_bn_eur=((rd["objective"] - ri["objective"]) / 1e9 if (ri["objective"] and rd["objective"]) else None),
            B6_relative=((rd["objective"] / ri["objective"] - 1) if (ri["objective"] and rd["objective"]) else None),
            b16_relative_error=b16, b16_within={sc: (v is not None and v <= STANDARD["b16_tol"]) for sc, v in b16.items()},
            country_difference_bn_eur={c: (float(dd.get(c)) if pd.notna(dd.get(c)) else None) for c in ENTITIES},
            country_change_vs_ref_bn_eur=chg, country_tolerance_bn_eur=tol, country_within=cpass,
            countries_exceeding=sorted(c for c in ENTITIES if cpass[c] is False),
            crossover={sc: dict(present=runs[f"{combo}_{sc}"]["crossover_present"], seconds=runs[f"{combo}_{sc}"].get("crossover_plus_simplex_seconds"),
                                over_barrier=runs[f"{combo}_{sc}"].get("crossover_over_barrier"), solved_with=runs[f"{combo}_{sc}"]["solved_with"],
                                above_5x_barrier=((runs[f"{combo}_{sc}"].get("crossover_over_barrier") or 0) > 5)) for sc in SCEN},
            all_within=(combo == "s4k_A") or bool(all(obj[sc] is not None and obj[sc] <= STANDARD["objective_rel_tol"] for sc in SCEN) and all(b16[sc] is not None and b16[sc] <= STANDARD["b16_tol"] for sc in SCEN)
                                                 and all(cpass[c] for c in ENTITIES)))
    # prices by country and differences vs the reference run of the same scenario
    for tag, pv in pr.items():
        res["prices_by_country"][tag] = pv
    rowsP = []
    for tag, pv in pr.items():
        for k, v in pv.items():
            rowsP.append(dict(run=tag, **v))
    pd.DataFrame(rowsP).to_csv(out / "S4L2_PRICES_BY_COUNTRY.csv", index=False)
    for net in NETS:
        for p in PROFS:
            for sc in SCEN:
                tag = f"{net}_{p}_{sc}"; refd = a.run / "solves" / f"s4k_A_{sc}"; d = a.run / "solves" / tag
                if tag == f"s4k_A_{sc}":
                    continue
                pdiff = {}
                for car in ("AC", "H2"):
                    x, y = bus_means(d, car), bus_means(refd, car)
                    cc = x.index.intersection(y.index)
                    if not len(cc):
                        continue
                    t = pd.read_csv(d / "NODAL_PRICES.csv").set_index("bus")
                    cty = t.country.reindex(cc)
                    dv = (x[cc] - y[cc])
                    pdiff[car] = dict(buses=int(len(cc)), mean_abs_diff=float(dv.abs().mean()), max_abs_diff=float(dv.abs().max()), rms_diff=float(np.sqrt((dv ** 2).mean())),
                                      ref_mean=float(y[cc].mean()), by_country_mean_abs_diff={c: float(dv[cty == c].abs().mean()) for c in sorted(set(cty.dropna()))},
                                      by_country_max_abs_diff={c: float(dv[cty == c].abs().max()) for c in sorted(set(cty.dropna()))})
                res["price_differences"][tag] = pdiff
    for sc in SCEN:
        k, l = runs[f"s4k_A_{sc}"], runs[f"s4l_A_{sc}"]
        res["lp_size"][sc] = {q: dict(s4k=k[q], s4l=l[q], change_rel=((l[q] / k[q] - 1) if (k[q] and l[q]) else None)) for q in ("num_col", "num_row", "nnz")}
        # repeat check: the S4K network + A run of this matrix against the S4K-3 solve of the same network
        r3 = jl(a.s4k3 / "solves" / sc / "SOLVE_RECEIPT.json"); g3 = jl(a.s4k3 / "solves" / sc / "V5_GATES.json"); l3 = parse_log(a.s4k3 / "solves" / sc / "GUROBI_LOG_SCRUBBED.txt")
        res["repeat_vs_s4k3"][sc] = dict(s4k3_objective=r3.get("objective"), matrix_objective=k["objective"],
                                         rel_diff=((k["objective"] / r3["objective"] - 1) if (r3.get("objective") and k["objective"]) else None),
                                         s4k3_barrier_iterations=l3["barrier_iterations"], matrix_barrier_iterations=k["barrier_iterations"],
                                         s4k3_termination=r3.get("termination_condition"), matrix_termination=k["termination"],
                                         s4k3_all_passed_solver_tolerances=g3.get("all_passed_solver_tolerances"), matrix_all_passed_solver_tolerances=k["all_passed_solver_tolerances"],
                                         s4k3_solve_seconds=r3.get("solve_seconds"), matrix_solve_seconds=k["solve_seconds"])
    (out / "S4L2_MATRIX_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str))
    show = R[["termination", "objective", "solve_seconds", "barrier_iterations", "barrier_seconds", "crossover_plus_simplex_seconds", "solved_with", "all_passed_solver_tolerances", "A1_A2", "B2", "B14", "B15", "B16_relative_error", "peak_rss_gib", "num_row"]] if "crossover_plus_simplex_seconds" in R else R
    print(show.to_string())
    print(json.dumps({c: dict(obj=v["objective_rel_diff_vs_ref"], b16=v["b16_relative_error"], exceeding=v["countries_exceeding"], all_within=v["all_within"], B6=v["B6_bn_eur"]) for c, v in res["combinations"].items()}, indent=1, default=str))
    print(D.round(4).to_string())
    print("lp_size", json.dumps(res["lp_size"])); print("repeat", json.dumps(res["repeat_vs_s4k3"], default=str))


if __name__ == "__main__":
    main()
