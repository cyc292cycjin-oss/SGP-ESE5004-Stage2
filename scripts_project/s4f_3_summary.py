"""S4F-3 smoke summary (S4F instruction section S4F-3): integrated STEPS, disconnected STEPS, integrated NZE (profile A, 56x3h) against the S4E-3
smoke. Generic part = s4d_5_summary (run table, gates under both bases, B5 / B6, capacity / generation by country vs the reference, CO2 flows,
ledgers); S4F part = corridor builds under the individual extension limit (new corridors total, largest single build, components at the cap,
vs S4E), TH-MY stock components, disconnected - integrated by country (KH, LA, VN, TH, MY, ID, PH, BN, TL) vs S4E, B16, CO2: intra-ASEAN shipping
and the Lao rail transit into the Vietnamese store. SMOKE_TEST_ONLY: 56 snapshots, the scale cannot be judged (decision 47).

    python scripts_project/s4f_3_summary.py --run results_project/s4f/s4f3 --ref results_project/s4e/s4e3
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
FOCUS = ("KH", "LA", "VN", "TH", "MY", "ID", "PH", "BN", "TL")
AT_CAP_MW = 1.0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", type=Path, required=True); ap.add_argument("--ref", type=Path, required=True); a = ap.parse_args()
    out = a.run / "analysis"; out.mkdir(parents=True, exist_ok=True)
    ref = a.run / "ref_s4e"; ref.mkdir(exist_ok=True)
    for t in ("integrated", "disconnected", "integrated_nze"):
        lnk = ref / t
        if not lnk.exists():
            lnk.symlink_to((a.ref / "solves" / t).resolve())
    import s4d_5_summary
    sys.argv = ["s4d_5_summary.py", "--mains", str(a.run / "solves"), "--nze", str(a.run / "solves"), "--s4c", str(ref), "--out", str(out)]
    s4d_5_summary.main()
    gen = json.loads((out / "S4D5_SMOKE_SUMMARY.json").read_text())
    (out / "S4D5_SMOKE_SUMMARY.json").rename(out / "GENERIC_SUMMARY_VS_S4E.json")
    s4e = json.loads((a.ref / "analysis/S4E3_SMOKE_SUMMARY.json").read_text())
    import pypsa
    from s4c_6_summary import solved_in
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    res = dict(label=gen["label"], reference="S4E-3 smoke (results_project/s4e/s4e3/solves, code 2bfafb91)", runs=gen["runs"], gates=gen["gates"], vs_s4e=gen["s4c"],
               B5=gen.get("B5"), B6=gen.get("B6"), co2=gen["co2"], co2_s4e=gen["co2_s4c"], ledgers=gen["ledgers"],
               disconnected_minus_integrated_bn_eur=gen.get("disconnected_minus_integrated_bn_eur"), largest_changes={k: gen[k] for k in gen if k.startswith("largest_changes")},
               corridors={}, at_cap={}, th_my={}, shipping={}, lao_vn_store={}, focus={})
    for t in ("integrated", "disconnected", "integrated_nze"):
        p = solved_in(a.run / "solves" / t)
        if not p:
            continue
        n = pypsa.Network(str(p)); w = n.snapshot_weightings.objective
        L = n.lines; D = n.links[n.links.carrier == "DC"]
        rows = []
        for k, z in L.iterrows():
            if str(k).startswith("S4E1"):
                rows.append(dict(component=k, type="AC", countries=f"{n.buses.at[z.bus0, 'country']}-{n.buses.at[z.bus1, 'country']}", mw=float(z.s_nom_opt), cap_mw=float(z.s_nom_max)))
        for k, z in D.iterrows():
            if str(k).startswith(("APG", "S4E1")):
                rows.append(dict(component=k, type="DC", countries=f"{n.buses.at[z.bus0, 'country']}-{n.buses.at[z.bus1, 'country']}", mw=float(z.p_nom_opt), cap_mw=float(z.p_nom_max),
                                 domestic=str(z.get("border_class", "")) == "domestic"))
        built = [r for r in rows if r["mw"] > 1.0]
        pipes = n.links[n.links.carrier.isin(["H2 pipeline", "CO2 pipeline", "gas pipeline"]) & (n.links.border_class == "cross_border")]
        s4e_c = (s4e.get("corridors") or {}).get(t, {})
        res["corridors"][t] = dict(new_components=len(rows), built_over_1mw=sorted(built, key=lambda r: -r["mw"]), built_total_mw=round(sum(r["mw"] for r in built), 1),
                                   largest_mw=round(max([r["mw"] for r in built] or [0.0]), 1), s4e_built_total_mw=s4e_c.get("built_total_mw"),
                                   s4e_largest_mw=round(max([r["mw"] for r in s4e_c.get("built_over_1mw", [])] or [0.0]), 1),
                                   xb_pipelines_built_over_1mw={car: int(((pipes.carrier == car) & (pipes.p_nom_opt > 1.0)).sum()) for car in ("H2 pipeline", "CO2 pipeline", "gas pipeline")})
        cap = []
        for typ, d, opt, mx in (("Line", L, "s_nom_opt", "s_nom_max"), ("Link", D, "p_nom_opt", "p_nom_max")):
            for k, z in d.iterrows():
                if np.isfinite(z[mx]) and z[opt] >= z[mx] - AT_CAP_MW:
                    cap.append(dict(component_type=typ, component=k, countries=f"{n.buses.at[z.bus0, 'country']}-{n.buses.at[z.bus1, 'country']}", border_class=str(z.get("border_class", "")),
                                    existing_mw=float(z[mx]) - 20000.0, optimal_mw=float(z[opt]), cap_mw=float(z[mx])))
        res["at_cap"][t] = dict(count=len(cap), cross_border=sum(c["border_class"] == "cross_border" for c in cap), domestic=sum(c["border_class"] == "domestic" for c in cap),
                                components=sorted(cap, key=lambda c: c["countries"]),
                                all_added_gw=round(float((L.s_nom_opt - L.s_nom).sum() + (D.p_nom_opt - D.p_nom).sum()) / 1e3, 1))
        res["th_my"][t] = {k: dict(existing_mw=float(z.s_nom), optimal_mw=float(z.s_nom_opt)) for k, z in L.iterrows() if k == "91"}
        res["th_my"][t].update({k: dict(existing_mw=float(z.p_nom), optimal_mw=float(z.p_nom_opt)) for k, z in D.iterrows() if "Khlong" in str(k) or str(k).startswith("250878579")})
        sh = gen["co2"].get(t, {}).get("shipping", {})
        res["shipping"][t] = dict(by_pair_mt={k: v["mt"] for k, v in sorted(sh.items(), key=lambda kv: -kv[1]["mt"])}, total_mt=round(sum(v["mt"] for v in sh.values()), 3),
                                  freight_meur=round(sum(v["freight_meur"] for v in sh.values()), 2),
                                  extra_asean_total_mt=round(sum(gen["co2"].get(t, {}).get("extra_asean_mt", {}).values()), 3),
                                  s4e_total_mt=(s4e.get("shipping") or {}).get(t, {}).get("total_mt"))
        rl = n.links[n.links.carrier == "CO2 transit rail"]
        lv = {str(z.bus0).split(" co2")[0]: round(float((n.links_t.p0[k] * w).sum()) / 1e6, 4) for k, z in rl.iterrows() if k in n.links_t.p0}
        res["lao_vn_store"][t] = dict(links=int(len(rl)), by_node_mt=lv, total_mt=round(sum(lv.values()), 4),
                                      freight_meur=round(sum(float((n.links_t.p0[k] * w).sum()) * float(z.marginal_cost) for k, z in rl.iterrows() if k in n.links_t.p0) / 1e6, 3))
    li = (gen["ledgers"].get("integrated") or {}).get("totals_bn_eur", {}); ld = (gen["ledgers"].get("disconnected") or {}).get("totals_bn_eur", {})
    s4e_d = s4e.get("disconnected_minus_integrated_bn_eur", {}) or {}
    res["focus"] = {c: dict(integrated_bn_eur=li.get(c), disconnected_bn_eur=ld.get(c), disconnected_minus_integrated=round(ld.get(c, 0.0) - li.get(c, 0.0), 4),
                            disconnected_minus_integrated_s4e=s4e_d.get(c)) for c in FOCUS}
    (out / "S4F3_SMOKE_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(dict(vs_s4e=res["vs_s4e"], corridors={t: {k: v for k, v in c.items() if k != "built_over_1mw"} for t, c in res["corridors"].items()},
                          at_cap={t: {k: v for k, v in c.items() if k != "components"} for t, c in res["at_cap"].items()}, th_my=res["th_my"],
                          shipping={t: {k: v for k, v in s.items() if k != "by_pair_mt"} for t, s in res["shipping"].items()}, lao_vn_store=res["lao_vn_store"],
                          focus=res["focus"], B6=(res["B6"] or {}).get("difference")), indent=1, default=str))


if __name__ == "__main__":
    main()
