"""S4G-3 smoke summary (S4G instruction section S4G-3): integrated STEPS, disconnected STEPS, integrated NZE (profile A, 56x3h) against the S4F-3 smoke.
Generic part = s4d_5_summary (run table, gates under both bases, B5 / B6, capacity / generation vs the reference, CO2 flows, ledgers); S4G part =
the 19 corrected cross-border AC lines (flow, expansion, at the individual limit), Mekong cross-border flows (LA, TH, KH, VN) and new corridor
builds by country pair, components at the limit vs S4F, disconnected - integrated by country (focus LA, KH, TH, VN) vs S4F, B16, disconnected
objective vs S4F. SMOKE_TEST_ONLY: 56 snapshots, the scale cannot be judged (decision 47).

    python scripts_project/s4g_3_summary.py --run results_project/s4g/s4g3 --ref results_project/s4f/s4f3
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
FOCUS = ("LA", "KH", "TH", "VN", "MY", "ID", "PH", "BN", "TL", "MM", "SG")
MEKONG = {"LA", "TH", "KH", "VN"}
AT_CAP_MW = 1.0


def xb_flows(n):
    """country pair -> dict(abs_twh, net_twh from the alphabetically first country) over cross-border AC lines and DC links."""
    w = n.snapshot_weightings.objective; out = {}
    for typ, d in (("Line", n.lines), ("Link", n.links[n.links.carrier == "DC"])):
        d = d[d.border_class == "cross_border"] if "border_class" in d else d.iloc[0:0]
        for k, z in d.iterrows():
            c0, c1 = str(n.buses.at[z.bus0, "country"]), str(n.buses.at[z.bus1, "country"])
            f = n.pnl(typ)["p0"][k] * w if k in n.pnl(typ)["p0"] else pd.Series(0.0)
            a, b = sorted((c0, c1)); sign = 1.0 if c0 == a else -1.0
            o = out.setdefault(f"{a}-{b}", dict(abs_twh=0.0, net_twh=0.0))
            o["abs_twh"] += float(f.abs().sum()) / 1e6; o["net_twh"] += sign * float(f.sum()) / 1e6
    return {k: {kk: round(vv, 4) for kk, vv in v.items()} for k, v in sorted(out.items())}


def at_cap(n):
    cap = []
    for typ, d, opt, mx in (("Line", n.lines, "s_nom_opt", "s_nom_max"), ("Link", n.links[n.links.carrier == "DC"], "p_nom_opt", "p_nom_max")):
        for k, z in d.iterrows():
            if np.isfinite(z[mx]) and z[opt] >= z[mx] - AT_CAP_MW:
                cap.append(f"{typ}:{k}")
    return sorted(cap)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", type=Path, required=True); ap.add_argument("--ref", type=Path, required=True); a = ap.parse_args()
    out = a.run / "analysis"; out.mkdir(parents=True, exist_ok=True)
    ref = a.run / "ref_s4f"; ref.mkdir(exist_ok=True)
    for t in ("integrated", "disconnected", "integrated_nze"):
        lnk = ref / t
        if not lnk.exists():
            lnk.symlink_to((a.ref / "solves" / t).resolve())
    import s4d_5_summary
    sys.argv = ["s4d_5_summary.py", "--mains", str(a.run / "solves"), "--nze", str(a.run / "solves"), "--s4c", str(ref), "--out", str(out)]
    s4d_5_summary.main()
    gen = json.loads((out / "S4D5_SMOKE_SUMMARY.json").read_text())
    (out / "S4D5_SMOKE_SUMMARY.json").rename(out / "GENERIC_SUMMARY_VS_S4F.json")
    s4f = json.loads((a.ref / "analysis/S4F3_SMOKE_SUMMARY.json").read_text())
    import pypsa
    from s4c_6_summary import solved_in
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    T = pd.read_csv(HERE.parent / "research_inputs/corridors/READJUST_IMPEDANCE_S4G1.csv", dtype={"line": str}).set_index("line")
    res = dict(label=gen["label"], reference="S4F-3 smoke (results_project/s4f/s4f3/solves, code d9bc8012)", runs=gen["runs"], gates=gen["gates"], vs_s4f=gen["s4c"],
               B5=gen.get("B5"), B6=gen.get("B6"), co2=gen["co2"], co2_s4f=gen["co2_s4c"], ledgers=gen["ledgers"],
               disconnected_minus_integrated_bn_eur=gen.get("disconnected_minus_integrated_bn_eur"), lines_19={}, mekong={}, corridors={}, at_cap={}, focus={})
    for t in ("integrated", "disconnected", "integrated_nze"):
        p, q = solved_in(a.run / "solves" / t), solved_in(a.ref / "solves" / t)
        if not p:
            continue
        n = pypsa.Network(str(p)); f = pypsa.Network(str(q)) if q else None; w = n.snapshot_weightings.objective
        rows = {}
        for k in T.index:
            if k not in n.lines.index:
                continue
            z = n.lines.loc[k]; fl = n.lines_t.p0[k] * w if k in n.lines_t.p0 else pd.Series(0.0)
            r = dict(country_pair=T.at[k, "country_pair"], s_nom=float(z.s_nom), s_nom_opt=round(float(z.s_nom_opt), 2), added=round(float(z.s_nom_opt - z.s_nom), 2),
                     at_cap=bool(z.s_nom_opt >= z.s_nom_max - AT_CAP_MW), abs_flow_twh=round(float(fl.abs().sum()) / 1e6, 4),
                     loading_max=round(float((n.lines_t.p0[k].abs() / max(float(z.s_nom_opt), 1e-9)).max()), 3) if k in n.lines_t.p0 else None)
            if f is not None and k in f.lines.index:
                zf = f.lines.loc[k]; ff = f.lines_t.p0[k] * f.snapshot_weightings.objective if k in f.lines_t.p0 else pd.Series(0.0)
                r.update(s4f_s_nom_opt=round(float(zf.s_nom_opt), 2), s4f_at_cap=bool(zf.s_nom_opt >= zf.s_nom_max - AT_CAP_MW), s4f_abs_flow_twh=round(float(ff.abs().sum()) / 1e6, 4))
            rows[k] = r
        res["lines_19"][t] = rows
        fx = xb_flows(n); ffx = xb_flows(f) if f is not None else {}
        res["mekong"][t] = {k: dict(s4g=v, s4f=ffx.get(k)) for k, v in fx.items() if set(k.split("-")) <= MEKONG}
        def new_built(net):
            d = {}
            for typ, df, opt in (("Line", net.lines, "s_nom_opt"), ("Link", net.links[net.links.carrier == "DC"], "p_nom_opt")):
                for k, z in df.iterrows():
                    if str(k).startswith(("S4E1", "APG")) and z[opt] > 1.0:
                        pr = "-".join(sorted((str(net.buses.at[z.bus0, "country"]), str(net.buses.at[z.bus1, "country"]))))
                        d[pr] = d.get(pr, 0.0) + float(z[opt])
            return {k: round(v / 1e3, 3) for k, v in sorted(d.items())}
        nb, fb = new_built(n), (new_built(f) if f is not None else {})
        res["corridors"][t] = dict(new_built_gw_by_pair={k: dict(s4g=nb.get(k), s4f=fb.get(k)) for k in sorted(set(nb) | set(fb))}, total_gw=round(sum(nb.values()), 2),
                                   s4f_total_gw=round(sum(fb.values()), 2))
        cs, cf = at_cap(n), (at_cap(f) if f is not None else [])
        res["at_cap"][t] = dict(s4g=cs, s4f=cf, added=sorted(set(cs) - set(cf)), removed=sorted(set(cf) - set(cs)))
    li = (gen["ledgers"].get("integrated") or {}).get("totals_bn_eur", {}); ld = (gen["ledgers"].get("disconnected") or {}).get("totals_bn_eur", {})
    s4f_d = s4f.get("disconnected_minus_integrated_bn_eur", {}) or {}
    res["focus"] = {c: dict(integrated_bn_eur=li.get(c), disconnected_bn_eur=ld.get(c), disconnected_minus_integrated=round(ld.get(c, 0.0) - li.get(c, 0.0), 4),
                            disconnected_minus_integrated_s4f=s4f_d.get(c)) for c in FOCUS}
    od = next((r for r in gen["runs"] if r["run"] == "disconnected"), {}); of = (gen["s4c"] or {}).get("disconnected", {})
    res["disconnected_objective_vs_s4f"] = dict(s4g=od.get("objective_eur"), s4f=of.get("objective"), relative=of.get("objective_change_rel"))
    (out / "S4G3_SMOKE_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(dict(vs_s4f=res["vs_s4f"], disconnected_objective_vs_s4f=res["disconnected_objective_vs_s4f"],
                          lines_19={t: {k: v for k, v in r.items() if k in ("61", "60", "91", "23", "43", "47", "39")} for t, r in res["lines_19"].items()},
                          mekong=res["mekong"], corridors=res["corridors"], at_cap=res["at_cap"], focus=res["focus"], B6=(res["B6"] or {}).get("difference")), indent=1, default=str))


if __name__ == "__main__":
    main()
