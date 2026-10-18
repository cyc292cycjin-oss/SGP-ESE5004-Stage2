"""S4J-6 smoke summary (S4J instruction section S4J-6): integrated STEPS, disconnected STEPS, integrated NZE (profile A, 56x3h) against the S4H-3 smoke.
Generic part = s4d_5_summary (run table, gates under both bases, B5 / B6, capacity / generation vs the reference, CO2 flows, ledgers); S4J part =
LP size and time increase vs S4H, disconnected - integrated by country vs S4H (focus VN, ID, SG, MY, PH, MM and the ends of the long pairs), B16,
cross-border flows and transmission losses by country pair (AC line losses p0 + p1, DC losses p0 + p1 over forward + reversed links, H2 / gas
compression electricity p2; shares of the energy sent), domestic losses, the TH-MY DC both directions, the solver-tolerance acceptance of the three
runs. SMOKE_TEST_ONLY: 56 snapshots, the scale cannot be judged (decision 47).

    python scripts_project/s4j_6_summary.py --run results_project/s4j/s4j6 --ref results_project/s4h/s4h3
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
from s4g_3_summary import at_cap  # noqa: E402
from s4h_3_summary import b16, tolerance_flags  # noqa: E402

FOCUS = ("VN", "ID", "SG", "MY", "PH", "MM", "TH", "LA", "KH", "BN", "TL")
RUNS = ("integrated", "disconnected", "integrated_nze")
KNG = "Khlong Ngae – Gurun"


def pair(n, b0, b1):
    return "-".join(sorted((str(n.buses.at[b0, "country"]), str(n.buses.at[b1, "country"]))))


def transport(n) -> dict:
    """Energy sent, losses and compression electricity by carrier and country pair (TWh); domestic totals apart."""
    w = n.snapshot_weightings.objective; out = {}; dom = {}

    def add(key, car, sent, loss, comp=0.0):
        o = out.setdefault(key, {}).setdefault(car, dict(sent_twh=0.0, loss_twh=0.0, compression_el_twh=0.0))
        o["sent_twh"] += sent; o["loss_twh"] += loss; o["compression_el_twh"] += comp
    if len(n.lines):
        p0 = n.lines_t.p0.mul(w, axis=0); p1 = n.lines_t.p1.mul(w, axis=0)
        for k, z in n.lines.iterrows():
            if k not in p0:
                continue
            sent = float(pd.concat([n.lines_t.p0[k], n.lines_t.p1[k]], axis=1).max(axis=1).clip(lower=0).mul(w).sum()) / 1e6
            loss = float((p0[k] + p1[k]).sum()) / 1e6
            key = pair(n, z.bus0, z.bus1) if z.border_class == "cross_border" else "domestic"
            add(key, "AC", sent, loss)
    for car in ("DC", "H2 pipeline", "gas pipeline", "CO2 pipeline"):
        idx = n.links.index[n.links.carrier == car]
        for k in idx:
            z = n.links.loc[k]
            if k not in n.links_t.p0:
                continue
            p0 = n.links_t.p0[k].mul(w); p1 = n.links_t.p1[k].mul(w)
            comp = float(n.links_t.p2[k].mul(w).sum()) / 1e6 if ("p2" in n.links_t and k in n.links_t.p2 and str(z.get("bus2", ""))) else 0.0
            sent = float(p0.clip(lower=0).sum() + (-p0).clip(lower=0).sum()) / 1e6   # one-way after the split; CO2 pipelines both ways
            loss = float((p0 + p1).sum()) / 1e6
            key = pair(n, z.bus0, z.bus1) if z.border_class == "cross_border" else "domestic"
            add(key, car, sent, loss, comp)
    for key, cars in out.items():
        for car, o in cars.items():
            o["loss_share"] = (o["loss_twh"] / o["sent_twh"]) if o["sent_twh"] > 1e-9 else None
            o["compression_share"] = (o["compression_el_twh"] / o["sent_twh"]) if o["sent_twh"] > 1e-9 else None
            for k in ("sent_twh", "loss_twh", "compression_el_twh"):
                o[k] = round(o[k], 4)
    return out


def caps(n) -> dict:
    """Cross-border capacity by pair (GW): AC lines s_nom_opt; DC links p_nom_opt of the forward links only."""
    d = {}
    for k, z in n.lines[n.lines.border_class == "cross_border"].iterrows():
        d.setdefault(pair(n, z.bus0, z.bus1), dict(ac_gw=0.0, dc_gw=0.0))["ac_gw"] += float(z.s_nom_opt) / 1e3
    L = n.links[(n.links.carrier == "DC") & (n.links.border_class == "cross_border")]
    if "reversed" in L:
        L = L[~L.reversed.astype(bool)]
    for k, z in L.iterrows():
        d.setdefault(pair(n, z.bus0, z.bus1), dict(ac_gw=0.0, dc_gw=0.0))["dc_gw"] += float(z.p_nom_opt) / 1e3
    return {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in sorted(d.items())}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", type=Path, required=True); ap.add_argument("--ref", type=Path, required=True); a = ap.parse_args()
    out = a.run / "analysis"; out.mkdir(parents=True, exist_ok=True)
    ref = a.run / "ref_s4h"; ref.mkdir(exist_ok=True)
    for t in RUNS:
        lnk = ref / t
        if not lnk.exists():
            lnk.symlink_to((a.ref / "solves" / t).resolve())
    import s4d_5_summary
    sys.argv = ["s4d_5_summary.py", "--mains", str(a.run / "solves"), "--nze", str(a.run / "solves"), "--s4c", str(ref), "--out", str(out)]
    s4d_5_summary.main()
    gen = json.loads((out / "S4D5_SMOKE_SUMMARY.json").read_text())
    (out / "S4D5_SMOKE_SUMMARY.json").rename(out / "GENERIC_SUMMARY_VS_S4H.json")
    s4h = json.loads((a.ref / "analysis/S4H3_SMOKE_SUMMARY.json").read_text())
    import pypsa
    from s4c_6_summary import solved_in
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    res = dict(label=gen["label"], reference="S4H-3 smoke (results_project/s4h/s4h3/solves, code 1887d975)", runs=gen["runs"], gates=gen["gates"], vs_s4h=gen["s4c"],
               tolerance=tolerance_flags(gen["gates"]), B5=gen.get("B5"), B6=gen.get("B6"), B6_s4h=s4h.get("B6"), co2=gen["co2"], ledgers=gen["ledgers"],
               disconnected_minus_integrated_bn_eur=gen.get("disconnected_minus_integrated_bn_eur"), B16={}, transport={}, capacity={}, at_cap={}, focus={}, lp_vs_s4h={}, th_my={})
    href = {r["run"]: r for r in s4h["runs"]}
    for r in gen["runs"]:
        h = href.get(r["run"], {})
        res["lp_vs_s4h"][r["run"]] = {k: dict(s4j=r.get(k), s4h=h.get(k), change_rel=((r.get(k) / h.get(k) - 1) if (h.get(k) and r.get(k) is not None) else None))
                                       for k in ("num_col", "num_row", "nnz", "barrier_iterations", "barrier_seconds", "solve_seconds", "peak_rss_gib_receipt")}
    for t in RUNS:
        g, gq = b16(a.run / "solves" / t), b16(a.ref / "solves" / t)
        if g:
            res["B16"][t] = dict(passed=g.get("passed"), relative_error=g.get("relative_error"), tolerance=g.get("tolerance"), difference_eur=g.get("difference"), s4h_relative_error=gq.get("relative_error"))
        p, q = solved_in(a.run / "solves" / t), solved_in(a.ref / "solves" / t)
        if not p:
            continue
        n = pypsa.Network(str(p)); f = pypsa.Network(str(q)) if q else None
        res["transport"][t] = dict(s4j=transport(n), s4h=(transport(f) if f is not None else None))
        res["capacity"][t] = dict(s4j=caps(n), s4h=(caps(f) if f is not None else None))
        cs, cf = at_cap(n), (at_cap(f) if f is not None else [])
        res["at_cap"][t] = dict(s4j=cs, s4h=cf, added=sorted(set(cs) - set(cf)), removed=sorted(set(cf) - set(cs)))
        if KNG in n.links.index:
            w = n.snapshot_weightings.objective
            fw = float(n.links_t.p0[KNG].mul(w).sum()) / 1e6 if KNG in n.links_t.p0 else 0.0
            rv = float(n.links_t.p0[KNG + "-reversed"].mul(w).sum()) / 1e6 if (KNG + "-reversed") in n.links_t.p0 else None
            res["th_my"][t] = dict(p_nom_opt_mw=float(n.links.at[KNG, "p_nom_opt"]), th_to_my_twh=fw, my_to_th_twh=rv,
                                   b2b_p_nom_opt_mw={c: float(n.links.at[c, "p_nom_opt"]) for c in ("convert_412_577", "convert_599_890") if c in n.links.index},
                                   s4h_th_to_my_twh=(float(f.links_t.p0[KNG].mul(f.snapshot_weightings.objective).sum()) / 1e6 if (f is not None and KNG in f.links_t.p0) else None))
    li = (gen["ledgers"].get("integrated") or {}).get("totals_bn_eur", {}); ld = (gen["ledgers"].get("disconnected") or {}).get("totals_bn_eur", {})
    h_focus = s4h.get("focus", {})
    res["focus"] = {c: dict(integrated_bn_eur=li.get(c), disconnected_bn_eur=ld.get(c), disconnected_minus_integrated=round(ld.get(c, 0.0) - li.get(c, 0.0), 4),
                            s4h_integrated_bn_eur=(h_focus.get(c) or {}).get("integrated_bn_eur"), s4h_disconnected_bn_eur=(h_focus.get(c) or {}).get("disconnected_bn_eur"),
                            s4h_disconnected_minus_integrated=(h_focus.get(c) or {}).get("disconnected_minus_integrated")) for c in FOCUS}
    od = next((r for r in gen["runs"] if r["run"] == "disconnected"), {}); of = (gen["s4c"] or {}).get("disconnected", {})
    res["disconnected_objective_vs_s4h"] = dict(s4j=od.get("objective_eur"), s4h=of.get("objective"), relative=of.get("objective_change_rel"))
    (out / "S4J6_SMOKE_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(dict(vs_s4h=res["vs_s4h"], tolerance=res["tolerance"], B16=res["B16"], lp_vs_s4h=res["lp_vs_s4h"], th_my=res["th_my"],
                          focus=res["focus"], B6=(res["B6"] or {}).get("difference"), B6_s4h=(res["B6_s4h"] or {}).get("difference")), indent=1, default=str))


if __name__ == "__main__":
    main()
