"""S4D-4 (decision 91b) summary: coalition verification on the 56x3h smoke (profile A) and the connected-coalition count of the corridor graph.

(a) all-11 coalition vs the integrated main: relative objective difference <= 1e-6; (b) [] vs the disconnected main: the same; (c) {MY,SG} and
{LA,TH}: objective, cross-border components by carrier, ledger identity (gate B16_LEDGER). Count: subsets S of the 11 countries whose corridor
graph (edges = country pairs joined by any cross-border component of the integrated build) restricted to S is connected.

    python scripts_project/s4d_4_summary.py --run results_project/s4d/s4d4
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from carrier_architecture import COUNTRIES
from d1_common import sha256
from s4d_layers import connected_coalitions

RUNS = ("integrated", "disconnected", "coal_all11", "coal_empty", "coal_MY_SG", "coal_LA_TH")
TOL = 1e-6


def main():
    import pypsa
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--run", type=Path, required=True); a = ap.parse_args()
    out = {}
    for t in RUNS:
        d = a.run / "solves" / t
        r = json.loads((d / "SOLVE_RECEIPT.json").read_text()) if (d / "SOLVE_RECEIPT.json").exists() else {}
        g = json.loads((d / "V5_GATES.json").read_text()) if (d / "V5_GATES.json").exists() else {}
        sc = "disconnected" if t == "disconnected" else "integrated"
        net = a.run / "builds" / t / f"{sc}_2920_3h_unsolved.nc"
        n = pypsa.Network(str(net))
        xb = {}
        for typ in ("Line", "Link"):
            df = n.df(typ); df = df[df.border_class == "cross_border"]
            for car, k in df.carrier.value_counts().items():
                xb[f"{typ}:{car}"] = int(k)
        pairs = sorted({"-".join(sorted((str(n.buses.at[z.bus0, "country"]), str(n.buses.at[z.bus1, "country"])))) for typ in ("Line", "Link")
                        for _, z in n.df(typ)[n.df(typ).border_class == "cross_border"].iterrows()})
        led = pd.read_csv(d / "COUNTRY_COST_LEDGER.csv", index_col=0) if (d / "COUNTRY_COST_LEDGER.csv").exists() else None
        out[t] = dict(termination=r.get("termination_condition"), objective=r.get("objective"), wall_s=r.get("solve_seconds", r.get("seconds")),
                      all_passed_solver_tolerances=g.get("all_passed_solver_tolerances"), all_passed_barconvtol=g.get("all_passed_barconvtol"),
                      failed=[k for k, v in g.items() if isinstance(v, dict) and v.get("passed") is False],
                      b16=(g.get("B16_LEDGER") or {}).get("relative_error"), b16_passed=(g.get("B16_LEDGER") or {}).get("passed"),
                      cross_border_components=xb, cross_border_pairs=pairs, maritime_trade_links=int((n.links.border_class == "maritime_trade").sum()),
                      coalition=(n.meta.get("research_cross_border", {}).get("ledger", {}).get("coalition")), network_sha256=sha256(net),
                      ledger_totals_bn_eur=({k: round(float(v) / 1e9, 4) for k, v in led["total"].items()} if led is not None else None))
    rel = lambda x, y: abs(x - y) / max(1.0, abs(y)) if x is not None and y is not None else None
    checks = dict(a_all11_vs_integrated=rel(out["coal_all11"]["objective"], out["integrated"]["objective"]),
                  b_empty_vs_disconnected=rel(out["coal_empty"]["objective"], out["disconnected"]["objective"]))
    checks["a_passed"] = checks["a_all11_vs_integrated"] is not None and checks["a_all11_vs_integrated"] <= TOL
    checks["b_passed"] = checks["b_empty_vs_disconnected"] is not None and checks["b_empty_vs_disconnected"] <= TOL
    edges = {tuple(p.split("-")) for p in out["integrated"]["cross_border_pairs"]}
    cc = connected_coalitions(edges, sorted(COUNTRIES))
    linked = sorted({c for e in edges for c in e})
    cc_linked = connected_coalitions(edges, linked)
    res = dict(runs=out, checks=checks, tolerance=TOL, corridor_edges=sorted("-".join(e) for e in edges), isolated=sorted(set(COUNTRIES) - set(linked)),
               connected_coalitions_all_countries=cc, connected_coalitions_linked_countries=cc_linked,
               note="isolated countries (no cross-border corridor) form connected coalitions only as singletons; coalitions of two or more members need one "
                    "run each (the grand coalition = integrated, singletons = the disconnected structure)")
    (a.run / "S4D4_COALITION.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(dict(checks=checks, edges=res["corridor_edges"], isolated=res["isolated"], cc=cc, cc_linked=cc_linked), indent=1))
    for t, v in out.items():
        print(t, v["termination"], v["objective"], "pass", v["all_passed_solver_tolerances"], v["failed"], "B16", v["b16"], "xb", sum(v["cross_border_components"].values()), v["cross_border_pairs"])


if __name__ == "__main__":
    main()
