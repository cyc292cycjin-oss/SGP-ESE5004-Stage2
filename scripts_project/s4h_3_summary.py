"""S4H-3 smoke summary (S4H instruction section S4H-3): integrated STEPS, disconnected STEPS, integrated NZE (profile A, 56x3h) against the S4G-3 smoke.
Generic part = s4d_5_summary (run table, gates under both bases, B5 / B6, capacity / generation vs the reference, CO2 flows, ledgers); S4H part =
the Lao directions (LA-TH, LA-VN, LA-MM) and KH-LA - flows, stock, expansion of stock lines, new candidate builds, per-component detail -, the
components at the individual limit vs S4G, disconnected - integrated by country (focus LA, MM, VN, TH, KH) vs S4G, B16, the solver-tolerance
acceptance of the three runs, the disconnected objective vs S4G and the decision-100 IPP estimate against the LA / VN ledger differences.
SMOKE_TEST_ONLY: 56 snapshots, the scale cannot be judged (decision 47).

    python scripts_project/s4h_3_summary.py --run results_project/s4h/s4h3 --ref results_project/s4g/s4g3
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from s4g_3_summary import AT_CAP_MW, at_cap, xb_flows  # noqa: E402

FOCUS = ("LA", "MM", "VN", "TH", "KH", "MY", "ID", "PH", "BN", "TL", "SG")
LAO = ("LA-TH", "LA-VN", "LA-MM", "KH-LA")
RUNS = ("integrated", "disconnected", "integrated_nze")


def pair_detail(n, pair: str) -> dict:
    """Stock, optimal capacity, expansion of stock components, new builds of zero-capacity candidates and flows of one country pair."""
    w = n.snapshot_weightings.objective; comps = {}; tot = dict(stock_mw=0.0, opt_mw=0.0, stock_expansion_mw=0.0, candidate_build_mw=0.0)
    for typ, d, nom, opt, mx in (("Line", n.lines, "s_nom", "s_nom_opt", "s_nom_max"), ("Link", n.links[n.links.carrier == "DC"], "p_nom", "p_nom_opt", "p_nom_max")):
        for k, z in d.iterrows():
            if "-".join(sorted((str(n.buses.at[z.bus0, "country"]), str(n.buses.at[z.bus1, "country"])))) != pair:
                continue
            p0 = n.pnl(typ)["p0"]; fl = p0[k] * w if k in p0 else pd.Series(0.0)
            cand = float(z[nom]) == 0.0
            r = dict(type=typ, bus0=z.bus0, bus1=z.bus1, stock_mw=round(float(z[nom]), 3), opt_mw=round(float(z[opt]), 2), added_mw=round(float(z[opt] - z[nom]), 2), candidate=cand,
                     at_cap=bool(z[opt] >= z[mx] - AT_CAP_MW), abs_flow_twh=round(float(fl.abs().sum()) / 1e6, 4),
                     num_parallel=(round(float(z.num_parallel), 6) if typ == "Line" else None), x=(round(float(z.x), 3) if typ == "Line" else None))
            comps[str(k)] = r
            tot["stock_mw"] += float(z[nom]); tot["opt_mw"] += float(z[opt])
            tot["candidate_build_mw" if cand else "stock_expansion_mw"] += float(z[opt] - z[nom])
    return dict(totals={k: round(v, 2) for k, v in tot.items()}, components=comps)


def tolerance_flags(gates: dict) -> dict:
    return {t: dict(all_passed_solver_tolerances=g.get("all_passed_solver_tolerances"), all_passed_barconvtol=g.get("all_passed_barconvtol"),
                    acceptance_basis=g.get("acceptance_basis")) for t, g in (gates or {}).items()}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", type=Path, required=True); ap.add_argument("--ref", type=Path, required=True); a = ap.parse_args()
    out = a.run / "analysis"; out.mkdir(parents=True, exist_ok=True)
    ref = a.run / "ref_s4g"; ref.mkdir(exist_ok=True)
    for t in RUNS:
        lnk = ref / t
        if not lnk.exists():
            lnk.symlink_to((a.ref / "solves" / t).resolve())
    import s4d_5_summary
    sys.argv = ["s4d_5_summary.py", "--mains", str(a.run / "solves"), "--nze", str(a.run / "solves"), "--s4c", str(ref), "--out", str(out)]
    s4d_5_summary.main()
    gen = json.loads((out / "S4D5_SMOKE_SUMMARY.json").read_text())
    (out / "S4D5_SMOKE_SUMMARY.json").rename(out / "GENERIC_SUMMARY_VS_S4G.json")
    s4g = json.loads((a.ref / "analysis/S4G3_SMOKE_SUMMARY.json").read_text())
    import pypsa
    from s4c_6_summary import solved_in
    from s4d_ledger import ledger_gate
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    res = dict(label=gen["label"], reference="S4G-3 smoke (results_project/s4g/s4g3/solves, code 3e64dca0)", runs=gen["runs"], gates=gen["gates"], vs_s4g=gen["s4c"],
               tolerance=tolerance_flags(gen["gates"]), tolerance_s4g=tolerance_flags(s4g.get("gates")), B5=gen.get("B5"), B6=gen.get("B6"), B6_s4g=s4g.get("B6"),
               co2=gen["co2"], co2_s4g=gen["co2_s4c"], ledgers=gen["ledgers"], disconnected_minus_integrated_bn_eur=gen.get("disconnected_minus_integrated_bn_eur"),
               lao={}, xb_flows={}, at_cap={}, focus={}, B16={})
    for t in RUNS:
        p, q = solved_in(a.run / "solves" / t), solved_in(a.ref / "solves" / t)
        li = a.run / "solves" / t / "LEDGER_IDENTITY.json"
        if li.exists():
            g = ledger_gate(json.loads(li.read_text())); gq = a.ref / "solves" / t / "LEDGER_IDENTITY.json"
            res["B16"][t] = dict(passed=g["passed"], relative_error=g["relative_error"], tolerance=g["tolerance"],
                                 s4g_relative_error=(ledger_gate(json.loads(gq.read_text()))["relative_error"] if gq.exists() else None))
        if not p:
            continue
        n = pypsa.Network(str(p)); f = pypsa.Network(str(q)) if q else None
        if t != "disconnected":
            res["lao"][t] = {pr: dict(s4h=pair_detail(n, pr), s4g=(pair_detail(f, pr) if f is not None else None)) for pr in LAO}
        fx = xb_flows(n); ffx = xb_flows(f) if f is not None else {}
        res["xb_flows"][t] = {k: dict(s4h=fx.get(k), s4g=ffx.get(k)) for k in sorted(set(fx) | set(ffx))}
        cs, cf = at_cap(n), (at_cap(f) if f is not None else [])
        res["at_cap"][t] = dict(s4h=cs, s4g=cf, added=sorted(set(cs) - set(cf)), removed=sorted(set(cf) - set(cs)))
    li = (gen["ledgers"].get("integrated") or {}).get("totals_bn_eur", {}); ld = (gen["ledgers"].get("disconnected") or {}).get("totals_bn_eur", {})
    g_focus = s4g.get("focus", {})
    res["focus"] = {c: dict(integrated_bn_eur=li.get(c), disconnected_bn_eur=ld.get(c), disconnected_minus_integrated=round(ld.get(c, 0.0) - li.get(c, 0.0), 4),
                            s4g_integrated_bn_eur=(g_focus.get(c) or {}).get("integrated_bn_eur"),
                            s4g_disconnected_minus_integrated=(g_focus.get(c) or {}).get("disconnected_minus_integrated")) for c in FOCUS}
    od = next((r for r in gen["runs"] if r["run"] == "disconnected"), {}); of = (gen["s4c"] or {}).get("disconnected", {})
    res["disconnected_objective_vs_s4g"] = dict(s4h=od.get("objective_eur"), s4g=of.get("objective"), relative=of.get("objective_change_rel"),
                                                identical=(od.get("objective_eur") == of.get("objective")))
    ipp = json.loads((HERE.parent / "research_inputs/corridors/LA_VN_STOCK_S4H1.json").read_text())["ipp_estimate"]
    lo, hi = (v / 1e9 for v in ipp["annualised_value_eur_per_a"])
    res["ipp_vs_ledger"] = dict(ipp_bn_eur_per_a=[round(lo, 4), round(hi, 4)],
                                ledger_disconnected_minus_integrated_bn_eur={c: res["focus"][c]["disconnected_minus_integrated"] for c in ("LA", "VN")},
                                ledger_integrated_change_vs_s4g_bn_eur={c: (round(li.get(c, 0.0) - res["focus"][c]["s4g_integrated_bn_eur"], 4)
                                                                           if res["focus"][c]["s4g_integrated_bn_eur"] is not None else None) for c in ("LA", "VN")},
                                note="IPP estimate = annualised value of 572 MW LA-VN AC capacity the model now has to build (grade C); smoke ledgers at 56 snapshots")
    (out / "S4H3_SMOKE_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(dict(vs_s4g=res["vs_s4g"], tolerance=res["tolerance"], disconnected_objective_vs_s4g=res["disconnected_objective_vs_s4g"], B16=res["B16"],
                          lao={t: {pr: dict(s4h=v["s4h"]["totals"], s4g=(v["s4g"] or {}).get("totals")) for pr, v in r.items()} for t, r in res["lao"].items()},
                          at_cap=res["at_cap"], focus={c: res["focus"][c] for c in FOCUS[:5]}, ipp_vs_ledger=res["ipp_vs_ledger"],
                          B6=(res["B6"] or {}).get("difference"), B6_s4g=(res["B6_s4g"] or {}).get("difference")), indent=1, default=str))


if __name__ == "__main__":
    main()
