"""S4B-5 smoke summary (S4B instruction section S4B-5 item 3): run table (status, objective, LP size, barrier, time, memory) against the S4A and
S4B-0 smokes, gates under the BarConvTol (V4) and the solver-tolerance (decision 71) acceptance, disconnected gaps, capacity / generation by country
(s4a_4_smoke_compare.tables), new hydro / geothermal / PHS / nuclear / SMR builds against their caps, cross-border exports, B5 / B6 trial.
SMOKE_TEST_ONLY results, representative weights 8760/56; no scientific meaning before the cloud run (decision 47).

    python scripts_project/s4b_5_summary.py --run results_project/s4b/s4b5 --s4a results_project/s4a/smoke --s4b0 results_project/s4b/s4b0
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

RUNS = ["integrated", "disconnected", "disconnected_gap", "integrated_gap"]
OLD_GATES = ["A1_A2", "A3", "A4", "A5", "A6", "B1", "B2", "B3", "B8", "B11", "B12", "B13", "B14", "B15"]
NEW_GATES = ["A1_A2_S4B", "A3_S4B", "A5_S4B", "B1_S4B", "B3_S4B"]
NEW_BUILD_CARRIERS = {"hydro": "StorageUnit", "ror": "Generator", "PHS": "StorageUnit", "geothermal": "Generator", "nuclear": "Generator", "nuclear SMR": "Generator"}


def status_lines(run_dir):
    out = {}
    f = run_dir / "STATUS.txt"
    if not f.exists():
        return out
    for line in f.read_text().splitlines():
        m = re.match(r"(RUN|BUILD)_(\w+?):(.*)", line)
        if not m:
            continue
        rss = re.search(r"Maximum resident set size \(kbytes\): (\d+)", line); wall = re.search(r"(\d+)s:", line); el = re.search(r"Elapsed .*?: ([\d:.]+)", line)
        out[f"{m.group(1)}_{m.group(2)}"] = dict(line=line[:400], peak_rss_gib=(int(rss.group(1)) / 1048576 if rss else None), wall_s=(int(wall.group(1)) if wall and m.group(1) == "RUN" else None), elapsed=(el.group(1) if el else None))
    return out


def run_row(run_dir, tag, label):
    d = run_dir / "solves" / tag; rec = d / "SOLVE_RECEIPT.json"
    st = status_lines(run_dir).get(f"RUN_{tag}", {})
    row = dict(source=label, run=tag, status_line=st.get("line"), wall_s=st.get("wall_s"), peak_rss_gib_time=st.get("peak_rss_gib"))
    if not rec.exists():
        return row
    r = json.loads(rec.read_text()); lp = r.get("lp") or {}; gl = r.get("gurobi_log_stats") or {}
    bar = " ".join((gl.get("lines") or {}).get("barrier", [])); m = re.search(r"in (\d+) iterations and ([\d.]+) seconds", bar)
    cs = (gl.get("coefficient_statistics") or {}).get("matrix") or {}
    row.update(termination=r.get("termination_condition"), objective_eur=r.get("objective"), num_col=lp.get("num_col"), num_row=lp.get("num_row"), nnz=lp.get("nnz"),
               barrier_iterations=(int(m.group(1)) if m else None), barrier_seconds=(float(m.group(2)) if m else None), solve_seconds=r.get("solve_seconds"),
               peak_rss_gib_receipt=(r.get("peak_rss_bytes") or 0) / 2**30, matrix_min=cs.get("min"), matrix_max=cs.get("max"),
               presolved=" ".join((gl.get("lines") or {}).get("presolved", [])))
    return row


def gate_row(run_dir, tag):
    f = run_dir / "solves" / tag / "V5_GATES.json"
    if not f.exists():
        return None
    g = json.loads(f.read_text())
    row = dict(run=tag, acceptance_basis=g.get("acceptance_basis"), all_passed_barconvtol=g.get("all_passed_barconvtol"), all_passed_solver_tolerances=g.get("all_passed_solver_tolerances"))
    for k in OLD_GATES + NEW_GATES:
        if isinstance(g.get(k), dict):
            row[k] = g[k].get("passed")
    a = g.get("A1_A2_S4B") or {}
    row["A1_A2_S4B_detail"] = {k: a.get(k) for k in ["row_fail_count", "column_fail_count", "row_max_ratio_to_budget", "column_max_ratio_to_budget", "stationarity_fail_count", "stationarity_normalized_max",
                                                     "dual_sign_fail_count", "dual_sign_normalized_max", "gap_relative", "failing_stationarity", "failing_columns"] if k in a}
    o = g.get("A1_A2") or {}
    row["A1_A2_failed_criteria"] = [k for k, v in (o.get("criteria") or {}).items() if v is False]
    row["A3_failed"] = (g.get("A3") or {}).get("failed"); row["A3_S4B_failed"] = (g.get("A3_S4B") or {}).get("failed")
    row["B1_failed_countries"] = [c.get("country") for c in ((g.get("B1") or {}).get("countries") or []) if isinstance(c, dict) and c.get("passed") is False]
    row["B3_S4B_failing"] = (g.get("B3_S4B") or {}).get("failing")
    return row


def solved(run_dir, tag):
    fs = sorted((run_dir / "solves" / tag).glob("*_solved.nc"))
    return fs[0] if fs else None


def new_builds(n):
    """Capacity by country of the candidate (extendable) hydro / ror / PHS / geothermal / nuclear / SMR, with the existing stock of the same carrier."""
    rows = []
    for carrier, comp in NEW_BUILD_CARRIERS.items():
        df = n.storage_units if comp == "StorageUnit" else n.generators
        for c in [carrier, f"{carrier} existing"]:
            sub = df[df.carrier == c]
            if sub.empty:
                continue
            ctry = sub.bus.map(n.buses.country).fillna(sub.bus.str[:2])
            ext = sub.p_nom_extendable.astype(bool)
            opt = sub.p_nom_opt.where(ext, sub.p_nom) if "p_nom_opt" in sub else sub.p_nom
            pmax = sub.p_nom_max.where(ext & np.isfinite(sub.p_nom_max), np.nan)
            for cc in sorted(set(ctry)):
                k = ctry == cc
                rows.append(dict(carrier=carrier, component_carrier=c, country=cc, existing_mw=float(sub.p_nom[k & ~ext].sum()), new_mw=float((opt[k & ext] - sub.p_nom[k & ext]).sum()),
                                 new_p_nom_max_mw=(float(pmax[k].sum()) if pmax[k].notna().any() else None), extendable_units=int((k & ext).sum())))
    return pd.DataFrame(rows)


def net_exports(flows_csv):
    if not flows_csv or not Path(flows_csv).exists():
        return {}
    f = pd.read_csv(flows_csv); out = {}
    for tc, sub in f.groupby("transport_carrier"):
        s = {}
        for r in sub.itertuples():
            net = (r.energy_0_to_1_mwh - r.energy_1_to_0_mwh) / 1e6
            s[r.country0] = s.get(r.country0, 0.0) + net; s[r.country1] = s.get(r.country1, 0.0) - net
        out[str(tc)] = {k: round(v, 3) for k, v in sorted(s.items()) if abs(v) > 1e-6}
    return out


def slack_penalty_cost(n, gap_table):
    w = n.snapshot_weightings.generators; g = n.generators[n.generators.get("research_role", pd.Series(dtype=str)) == "GAP_DIAGNOSTIC_SLACK"]
    gen = float((n.generators_t.p.reindex(columns=g.index, fill_value=0.0).mul(w, axis=0).sum() * g.marginal_cost).sum()) if len(g) else 0.0
    pen = float((n.meta.get("gap_diagnostic") or {}).get("penalty_eur_per_tco2", 0.0))
    co2 = sum(float(r.get("co2_gap_t") or 0.0) for r in gap_table.get("rows", []) if r.get("country") != "ASEAN") * pen
    return dict(generator_slack_cost_eur=gen, co2_slack_cost_eur=co2, total_eur=gen + co2, penalty_eur_per_tco2=pen)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", type=Path, required=True); ap.add_argument("--s4a", type=Path, required=True); ap.add_argument("--s4b0", type=Path, required=True)
    a = ap.parse_args(); out_dir = a.run / "analysis"; out_dir.mkdir(parents=True, exist_ok=True)
    import pypsa
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    from s4a_4_smoke_compare import tables
    from s4b_smoke_summary import system_items
    res = dict(label="SMOKE_TEST_ONLY (56x3h, representative weights 8760/56; decision 47)", builds={k: v for k, v in status_lines(a.run).items() if k.startswith("BUILD_")})
    # 1. run table
    rows = [run_row(a.run, t, "S4B5") for t in RUNS] + [run_row(a.s4b0, t, "S4B0") for t in ["integrated", "disconnected", "disconnected_gap"]] + [run_row(a.s4a, t, "S4A") for t in ["integrated", "disconnected"]]
    rt = pd.DataFrame(rows); rt.to_csv(out_dir / "S4B5_RUN_TABLE.csv", index=False); res["runs"] = rows
    # 2. gates (old = V4 BarConvTol basis, new = decision 71 solver tolerances)
    res["gates"] = {t: gate_row(a.run, t) for t in RUNS if gate_row(a.run, t) is not None}
    res["gates_reference"] = {f"S4B0_{t}": gate_row(a.s4b0, t) for t in ["integrated", "disconnected_gap"] if gate_row(a.s4b0, t) is not None}
    # 3. gaps
    for t in ["disconnected_gap", "integrated_gap"]:
        f = a.run / "solves" / t / "GAP_TABLE.json"
        if f.exists():
            res[f"gap_table_{t}"] = json.loads(f.read_text())
    # 4. capacity / generation and system items
    ni_p = solved(a.run, "integrated"); comp = {}
    if ni_p:
        ni = pypsa.Network(str(ni_p)); tn = tables(ni); tn.to_csv(out_dir / "CAP_GEN_BY_COUNTRY_S4B5.csv", index=False)
        res["items_integrated"] = system_items(ni); res["asean_integrated"] = tn.groupby("group")[["gw", "twh"]].sum().round(3).to_dict("index")
        nb = new_builds(ni); nb.to_csv(out_dir / "NEW_BUILDS_S4B5_INTEGRATED.csv", index=False); res["new_builds_integrated"] = nb.to_dict("records")
        res["meta_candidate_caps"] = ni.meta.get("research_candidates_s4b2"); res["meta_nuclear_caps"] = ni.meta.get("research_nuclear_caps")
        for lab, base in [("S4A", a.s4a), ("S4B0", a.s4b0)]:
            p = solved(base, "integrated")
            if not p:
                continue
            no = pypsa.Network(str(p)); to = tables(no); to.to_csv(out_dir / f"CAP_GEN_BY_COUNTRY_{lab}.csv", index=False)
            m = tn.merge(to, on=["group", "country"], how="outer", suffixes=("_S4B5", f"_{lab}")).fillna(0.0)
            m["d_gw"] = m["gw_S4B5"] - m[f"gw_{lab}"]; m["d_twh"] = m["twh_S4B5"] - m[f"twh_{lab}"]
            m.to_csv(out_dir / f"CAP_GEN_BY_COUNTRY_S4B5_VS_{lab}.csv", index=False)
            comp[lab] = dict(asean=to.groupby("group")[["gw", "twh"]].sum().round(3).to_dict("index"), items=system_items(no))
            nbo = new_builds(no); nbo.to_csv(out_dir / f"NEW_BUILDS_{lab}_INTEGRATED.csv", index=False)
            comp[lab]["new_builds"] = nbo.to_dict("records")
            comp[lab]["net_exports_twh"] = net_exports(p.parent / "cross_border_flows.csv")
        res["reference"] = comp
        res["net_exports_twh_integrated"] = net_exports(ni_p.parent / "cross_border_flows.csv")
    ng_p = solved(a.run, "disconnected_gap")
    if ng_p:
        ng = pypsa.Network(str(ng_p)); tg = tables(ng); tg.to_csv(out_dir / "CAP_GEN_BY_COUNTRY_S4B5_DISCONNECTED_GAP.csv", index=False)
        res["items_disconnected_gap"] = system_items(ng); res["new_builds_disconnected_gap"] = new_builds(ng).to_dict("records")
        res["slack_cost_disconnected_gap"] = slack_penalty_cost(ng, res.get("gap_table_disconnected_gap", {}))
        # 5. B5 / B6 trial: the disconnected main has no solution (structurally infeasible); B5 uses the disconnected gap diagnostic (same topology),
        # B6 compares the integrated objective with the disconnected diagnostic objective with and without the slack penalty cost (trial only, not a gate result)
        if ni_p:
            from v5.v5_gates import gate_b5_single_switch, gate_b6_cost
            from phase4_static import config
            b5 = gate_b5_single_switch(config(HERE.parent, "integrated"), config(HERE.parent, "disconnected"), n_dis_solved=ng, n_int_solved=ni)
            b5["note"] = "trial: disconnected network = gap diagnostic solution (disconnected main infeasible); config differences of the two main configurations"
            obj_g = float(ng.objective); pen = res["slack_cost_disconnected_gap"]["total_eur"]
            res["B5_trial"] = b5
            res["B6_trial"] = dict(with_slack_penalty=gate_b6_cost(float(ni.objective), obj_g, "integrated", "disconnected_gap_diagnostic"),
                                   net_of_slack_penalty=gate_b6_cost(float(ni.objective), obj_g - pen, "integrated", "disconnected_gap_diagnostic_net_of_slack_cost"),
                                   note="trial only: the disconnected diagnostic relaxes the country constraints through penalised slacks, so neither objective is the disconnected system cost")
    ig_p = solved(a.run, "integrated_gap")
    if ig_p and ni_p:
        nig = pypsa.Network(str(ig_p))
        res["integrated_gap_vs_main"] = dict(objective_main=float(ni.objective), objective_gap=float(nig.objective), difference=float(nig.objective) - float(ni.objective),
                                             slack_cost=slack_penalty_cost(nig, res.get("gap_table_integrated_gap", {})))
    sg = a.run / "analysis" / "S4B5_STRUCTURAL_GAP_ANNUAL.json"
    if sg.exists():
        res["structural_gap"] = json.loads(sg.read_text())
    (out_dir / "S4B5_SMOKE_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str))
    print(rt[["source", "run", "termination", "objective_eur", "num_col", "num_row", "nnz", "barrier_iterations", "barrier_seconds", "solve_seconds", "wall_s", "peak_rss_gib_time"]].to_string())
    for t, g in res["gates"].items():
        print(t, {k: g.get(k) for k in ["all_passed_barconvtol", "all_passed_solver_tolerances"] + OLD_GATES + NEW_GATES})


if __name__ == "__main__":
    main()
