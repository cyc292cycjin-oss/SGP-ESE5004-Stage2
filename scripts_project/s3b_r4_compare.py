"""S3B R4.3 equivalence test: unscaled (A) vs scaled (B) formal_barrier solutions of the same 56x3h integrated LP, against the S3-7 Gurobi
barrier objective 6.98803335e11; LP identity of A with the S3-7 exported LP; coefficient statistics and warnings; main quantities.

    python scripts_project/s3b_r4_compare.py --a <dir A> --b <dir B> --s37-lp <dir> --output <json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
REF = 6.98803335e11
REL_TOL_OBJ = 1e-6
REL_TOL_Q = 1e-4


def quantities(n):
    w = n.snapshot_weightings.generators
    q = {}
    for typ, nom in [("Generator", "p_nom"), ("Link", "p_nom"), ("StorageUnit", "p_nom"), ("Store", "e_nom"), ("Line", "s_nom")]:
        d = n.df(typ); ext = d[nom + "_extendable"]
        for car, v in d.loc[ext].groupby("carrier")[nom + "_opt"].sum().items():
            q[f"capacity|{typ}|{car}"] = float(v)
    for car, cols in n.generators.groupby("carrier").groups.items():
        q[f"energy|Generator|{car}"] = float(n.generators_t.p[list(cols)].mul(w, axis=0).to_numpy().sum())
    for car in ["CCGT", "OCGT", "CCGT CC", "CCGT existing", "H2 Electrolysis", "Haber-Bosch", "methanolisation", "biomass-to-methanol", "DAC", "process emissions CC", "SMR", "SMR CC", "gas pipeline", "H2 pipeline", "CO2 pipeline", "DC"]:
        idx = n.links.index[n.links.carrier == car]
        if len(idx):
            q[f"flow_abs|Link|{car}"] = float(n.links_t.p0[idx].abs().mul(w, axis=0).to_numpy().sum())
    for s in n.stores.index[n.stores.index.str.startswith("co2 sequestered")]:
        q[f"co2_sequestered|{s.split()[-1]}"] = float(n.stores_t.e[s].iloc[-1])
    xb = n.lines.index[n.lines.border_class == "cross_border"]
    q["xb_line_capacity_total"] = float(n.lines.loc[xb, "s_nom_opt"].sum())
    return q


def main():
    p = argparse.ArgumentParser(); p.add_argument("--a", type=Path, required=True); p.add_argument("--b", type=Path, required=True); p.add_argument("--s37-lp", type=Path, required=True); p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    import pypsa, logging
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    ra, rb = json.loads((a.a / "SOLVE_RECEIPT.json").read_text()), json.loads((a.b / "SOLVE_RECEIPT.json").read_text())
    out = dict(reference_objective=REF, tolerance_objective=REL_TOL_OBJ, tolerance_quantities=REL_TOL_Q)
    for lab, r in [("A_unscaled", ra), ("B_scaled", rb)]:
        out[lab] = dict(status=r.get("termination_condition"), objective_total=r.get("objective"), objective_lp=r.get("objective_lp"), rel_diff_to_reference=(abs(r["objective"] - REF) / REF if r.get("objective") else None),
                        solve_seconds=r.get("solve_seconds"), peak_rss_gib=(r.get("peak_rss_bytes") or 0) / 2**30, lp=r.get("lp", {}) and {k: r["lp"][k] for k in ["num_col", "num_row", "nnz"]},
                        coefficient_statistics=(r.get("gurobi_log_stats") or {}).get("coefficient_statistics"), warnings=(r.get("gurobi_log_stats") or {}).get("lines", {}).get("warning", []),
                        barrier=(r.get("gurobi_log_stats") or {}).get("lines", {}).get("barrier"), result=(r.get("gurobi_log_stats") or {}).get("lines", {}).get("result"),
                        scaling=r.get("scaling"), gates=r.get("gates"))
    if ra.get("objective") and rb.get("objective"):
        out["rel_diff_A_B"] = abs(ra["objective"] - rb["objective"]) / abs(ra["objective"])
        out["objective_equivalent"] = bool(out["A_unscaled"]["rel_diff_to_reference"] <= REL_TOL_OBJ and out["B_scaled"]["rel_diff_to_reference"] <= REL_TOL_OBJ and out["rel_diff_A_B"] <= REL_TOL_OBJ)
    # LP identity: exported arrays of A vs the S3-7 exported LP (same network content, rebuilt with the solver block in the config)
    ma = json.loads((a.a / "lp" / "MATH_PROBLEM.json").read_text()); ms = json.loads((a.s37_lp / "MATH_PROBLEM.json").read_text())
    out["lp_identity_A_vs_S3_7"] = {k: (ma["arrays"][k]["sha256"] == ms["arrays"][k]["sha256"]) for k in ma["arrays"] if k in ms["arrays"]}
    out["lp_identity_A_vs_S3_7_all"] = all(out["lp_identity_A_vs_S3_7"].values())
    na = pypsa.Network(str(next(a.a.glob("*_solved.nc")))); nb = pypsa.Network(str(next(a.b.glob("*_solved.nc"))))
    qa, qb = quantities(na), quantities(nb)
    thr = json.loads((a.b / "INTERIOR_CHECKS.json").read_text())["cleanup_thresholds"]["groups"] if (a.b / "INTERIOR_CHECKS.json").exists() else {}
    rows = []
    for k in sorted(set(qa) | set(qb)):
        va, vb = qa.get(k, 0.0), qb.get(k, 0.0); scale = max(abs(va), abs(vb))
        tau = 0.0
        if k.startswith("capacity|"):
            tau = thr.get(f"{k.split('|')[1]}.{'s_nom_opt' if k.split('|')[1] == 'Line' else ('e_nom_opt' if k.split('|')[1] == 'Store' else 'p_nom_opt')}", {}).get("tau", 0.0)
        ok = abs(va - vb) <= max(REL_TOL_Q * scale, tau, 1e-6)
        rows.append(dict(quantity=k, A=va, B=vb, abs_diff=abs(va - vb), rel_diff=(abs(va - vb) / scale if scale else 0.0), within_tolerance=bool(ok)))
    df = pd.DataFrame(rows)
    out["quantities"] = dict(count=len(df), within=int(df.within_tolerance.sum()), outside=df[~df.within_tolerance].sort_values("rel_diff", ascending=False).head(25).to_dict("records"),
                             max_rel_diff=float(df.rel_diff.max()), table=df.to_dict("records"))
    for lab, d in [("A_unscaled", a.a), ("B_scaled", a.b)]:
        ic = d / "INTERIOR_CHECKS.json"
        if ic.exists():
            j = json.loads(ic.read_text())
            out[lab]["simultaneous_charge_discharge"] = j["simultaneous_charge_discharge"]
            out[lab]["cleanup_below_threshold"] = {k: dict(tau=v["tau"], below=v["below"], share=v["below_share_of_abs_sum"]) for k, v in j["cleanup_thresholds"]["groups"].items()}
        g = d / "V5_GATES.json"
        if g.exists():
            G = json.loads(g.read_text()); out[lab]["A1_A2"] = {k: v for k, v in G["A1_A2"].items() if k != "metrics"} | {"metrics": G["A1_A2"].get("metrics")}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=1, default=str))
    for lab in ["A_unscaled", "B_scaled"]:
        o = out[lab]; print("==", lab, o["status"], "total", o["objective_total"], "rel ref", o["rel_diff_to_reference"], "secs", round(o["solve_seconds"] or 0, 1), "GiB", round(o["peak_rss_gib"], 2))
        print("   coeff stats:", o["coefficient_statistics"]); print("   warnings:", o["warnings"]); print("   A1_A2:", (o.get("A1_A2") or {}).get("passed"), (o.get("A1_A2") or {}).get("criteria"))
        print("   simultaneous:", {k: (v.get("instances"), round(v.get("max_simultaneous_mw", 0), 3)) for k, v in (o.get("simultaneous_charge_discharge") or {}).items() if isinstance(v, dict) and "instances" in v})
    print("rel_diff_A_B", out.get("rel_diff_A_B"), "equivalent", out.get("objective_equivalent"), "| LP identity A vs S3-7:", out["lp_identity_A_vs_S3_7_all"], out["lp_identity_A_vs_S3_7"])
    print("quantities within tol:", out["quantities"]["within"], "/", out["quantities"]["count"], "max rel", out["quantities"]["max_rel_diff"])
    for r in out["quantities"]["outside"][:12]:
        print("   outside:", r["quantity"], "%.6g" % r["A"], "%.6g" % r["B"], "rel %.3g" % r["rel_diff"])


if __name__ == "__main__":
    main()
