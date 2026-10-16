"""S3-0.5 diagnosis helper (read-only, no solver): completeness of the four S3-0 runs, HiGHS log endings, gap-diagnostic slack use,
and the binding annual caps / pools / weights in the solved gap networks. Writes S3_0_SMOKE_CHECK.json next to this file.

    PYTHONHASHSEED=0 python research/06_scope_redesign/p1_step3_20261015/s3_0_smoke_check.py
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
S3 = REPO / "results_project" / "s3"
out = {"runs": {}, "gap_networks": {}}
for kind in ["smoke", "gap_diagnostic"]:
    for sc in ["integrated", "disconnected"]:
        d = S3 / kind / sc
        rec = d / "SOLVE_RECEIPT.json"
        row = {"receipt": rec.exists()}
        if rec.exists():
            r = json.loads(rec.read_text())
            row.update(status=r.get("status"), termination=r.get("termination_condition"), objective=r.get("objective"), solve_seconds=r.get("solve_seconds"),
                       finished=r.get("finished_epoch") is not None, decision=r.get("decision"), optimize_calls=r.get("optimize_calls"), retry=r.get("retry"),
                       snapshots=r["input_network"]["snapshots"], weight_h=r["input_network"]["horizon_scaling"]["weight_hours_per_snapshot"],
                       lp={k: r["lp"][k] for k in ["num_col", "num_row", "nnz"]}, gates=r.get("gates"))
            if "gap_table" in r:
                g = pd.DataFrame(r["gap_table"]).set_index("country")
                row["gap_table"] = g[["electricity_gap_mwh", "co2_gap_t", "biomass_gap_mwh"]].to_dict("index")
                row["gap_totals"] = {c: float(g[c].sum()) for c in ["electricity_gap_mwh", "co2_gap_t", "biomass_gap_mwh"]}
            if "emissions_by_country" in r:
                row["net_emissions_t"] = r["emissions_by_country"]
        log = d / "highs.linopy.log"
        if log.exists():
            lines = log.read_text().splitlines()
            row["log_tail"] = lines[-9:]
            row["log_infeasibility_lines"] = [l for l in lines if re.search(r"infeas|Infeas|status|Status|Crossover|crossover|optimal", l)][-12:]
        out["runs"][f"{kind}/{sc}"] = row
# binding caps / pools in the solved gap networks (same structure as the smoke network plus slack generators)
for sc in ["integrated", "disconnected"]:
    p = S3 / "gap_diagnostic" / sc / f"{sc}_GAP_DIAGNOSTIC_solved.nc"
    if not p.exists():
        continue
    n = pypsa.Network(str(p))
    w = n.snapshot_weightings.generators
    res = {"snapshots": len(n.snapshots), "weights_sum_h": float(w.sum()), "weight_unique": sorted(set(float(x) for x in w.unique()))}
    st = n.stores
    role = st.research_role if "research_role" in st else pd.Series("", index=st.index)
    fin = st[role == "FINITE_RESOURCE"]
    used = {}
    for s in fin.index:
        e0 = float(fin.at[s, "e_nom"]); level = float(n.stores_t.e[s].iloc[-1]); drawn = e0 - level if e0 else 0.0
        used[s] = dict(e_nom=e0, final_level=level, utilisation=(drawn / e0) if e0 else None)
    u = pd.DataFrame(used).T
    res["finite_pools_at_or_above_0.999"] = u[u.utilisation >= 0.999].round(6).to_dict("index") if len(u) else {}
    res["finite_pools_count"] = int(len(u))
    seq = st[st.index.str.startswith("co2 sequestered")]
    res["sequestration"] = {s: dict(e_nom_max=float(seq.at[s, "e_nom_max"]), final=float(n.stores_t.e[s].iloc[-1]), at_cap=bool(float(n.stores_t.e[s].iloc[-1]) >= float(seq.at[s, "e_nom_max"]) * (1 - 1e-6))) for s in seq.index}
    caps = n.meta.get("external_annual_caps", {})
    res["external_annual_caps"] = {k: v for k, v in list(caps.items())[:20]}
    res["external_annual_caps_count"] = len(caps)
    slack = n.generators[n.generators.carrier.str.contains("slack|gap", case=False)] if len(n.generators) else n.generators
    if len(slack):
        p_sl = (n.generators_t.p[slack.index].mul(w, axis=0)).sum()
        res["slack_generators_nonzero_mwh"] = {k: float(v) for k, v in p_sl[p_sl.abs() > 1e-9].items()}
        res["slack_generator_count"] = int(len(slack))
    L = n.lines
    xb = L[L.border_class == "cross_border"] if "border_class" in L else L.iloc[0:0]
    res["xb_lines"] = {i: dict(s_nom_min=float(xb.at[i, "s_nom_min"]), s_nom_opt=float(xb.at[i, "s_nom_opt"]), max_abs_flow=float(n.lines_t.p0[i].abs().max()), s_max_pu=float(xb.at[i, "s_max_pu"])) for i in xb.index}
    res["apg_corridor_additions"] = n.meta.get("apg_corridor_additions")
    # per-country net emissions from the atmosphere balance (stores named like 'co2 atmosphere XX'?) -> use the receipt field instead
    out["gap_networks"][sc] = res
(HERE / "S3_0_SMOKE_CHECK.json").write_text(json.dumps(out, indent=1, default=str))
for k, v in out["runs"].items():
    print("==", k, {kk: v.get(kk) for kk in ["receipt", "status", "termination", "objective", "solve_seconds", "finished", "decision", "gap_totals", "snapshots", "weight_h"]})
    for l in v.get("log_infeasibility_lines", []):
        print("   |", l)
for sc, v in out["gap_networks"].items():
    print("== gap network", sc, {k: v[k] for k in ["snapshots", "weights_sum_h", "weight_unique", "finite_pools_count", "external_annual_caps_count"]})
    print("   pools >= 0.999:", json.dumps(v["finite_pools_at_or_above_0.999"], default=str)[:1500])
    print("   sequestration at cap:", {k: vv["at_cap"] for k, vv in v["sequestration"].items()})
    print("   slack nonzero:", v.get("slack_generators_nonzero_mwh"), "count", v.get("slack_generator_count"))
    print("   xb lines (min, opt, maxflow):", {k: (round(vv["s_nom_min"], 1), round(vv["s_nom_opt"], 1), round(vv["max_abs_flow"], 1)) for k, vv in list(v["xb_lines"].items())[:30]})
