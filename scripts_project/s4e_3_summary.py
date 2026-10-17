"""S4E-3 smoke summary (S4E instruction section S4E-3): integrated STEPS, disconnected STEPS, integrated NZE (profile A, 56x3h) against the S4D
smoke (S4D-4 mains + S4D-5 NZE). Generic part = s4d_5_summary (run table, gates under both bases, B5 / B6, capacity / generation by country vs the
reference, CO2 flows, ledgers); S4E part = new corridors built in the integrated runs (capacity), cross-border exchange of BN / PH / TL, intra-ASEAN
CO2 shipping by country pair (Mt/a) incl. the Lao transit-ship links, extra-ASEAN storage vs S4D, disconnected - integrated by country for BN, PH,
TL, KH, LA, MM, SG, MY, ID, ledger identity B16. SMOKE_TEST_ONLY: 56 snapshots, the wind / solar scale cannot be judged (decision 47).

    python scripts_project/s4e_3_summary.py --run results_project/s4e/s4e3 --ref-mains results_project/s4d/s4d4/solves --ref-nze results_project/s4d/s4d5/solves
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
FOCUS = ("BN", "PH", "TL", "KH", "LA", "MM", "SG", "MY", "ID")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, required=True); ap.add_argument("--ref-mains", type=Path, required=True); ap.add_argument("--ref-nze", type=Path, required=True)
    a = ap.parse_args()
    out = a.run / "analysis"; out.mkdir(parents=True, exist_ok=True)
    ref = a.run / "ref_s4d"; ref.mkdir(exist_ok=True)   # reference layout expected by s4d_5_summary (--s4c <dir>/<run>)
    for t, src in (("integrated", a.ref_mains / "integrated"), ("disconnected", a.ref_mains / "disconnected"), ("integrated_nze", a.ref_nze / "integrated_nze")):
        lnk = ref / t
        if not lnk.exists():
            lnk.symlink_to(src.resolve())
    import s4d_5_summary
    sys.argv = ["s4d_5_summary.py", "--mains", str(a.run / "solves"), "--nze", str(a.run / "solves"), "--s4c", str(ref), "--out", str(out)]
    s4d_5_summary.main()
    gen = json.loads((out / "S4D5_SMOKE_SUMMARY.json").read_text())
    (out / "S4D5_SMOKE_SUMMARY.json").rename(out / "GENERIC_SUMMARY_VS_S4D.json")
    import pypsa
    from s4c_6_summary import solved_in
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    res = dict(label=gen["label"], reference="S4D smoke: integrated / disconnected = results_project/s4d/s4d4/solves (6dbc9b9e), integrated_nze = results_project/s4d/s4d5/solves (f47db599)",
               runs=gen["runs"], gates=gen["gates"], vs_s4d=gen["s4c"], B5=gen.get("B5"), B6=gen.get("B6"), co2=gen["co2"], co2_s4d=gen["co2_s4c"], ledgers=gen["ledgers"],
               disconnected_minus_integrated_bn_eur=gen.get("disconnected_minus_integrated_bn_eur"), largest_changes={k: gen[k] for k in gen if k.startswith("largest_changes")},
               corridors={}, exchange={}, shipping={}, focus={})
    for t in ("integrated", "disconnected", "integrated_nze"):
        p = solved_in(a.run / "solves" / t)
        if not p:
            continue
        n = pypsa.Network(str(p)); w = n.snapshot_weightings.objective
        # new corridors built (S4E-1)
        rows = []
        for k, z in n.lines.iterrows():
            if str(k).startswith("S4E1"):
                rows.append(dict(component=k, type="AC", countries=f"{n.buses.at[z.bus0, 'country']}-{n.buses.at[z.bus1, 'country']}", mw=float(z.s_nom_opt), length_km=float(z.length)))
        for k, z in n.links[n.links.carrier == "DC"].iterrows():
            if str(k).startswith(("APG", "S4E1")):
                rows.append(dict(component=k, type="DC", countries=f"{n.buses.at[z.bus0, 'country']}-{n.buses.at[z.bus1, 'country']}", mw=float(z.p_nom_opt), length_km=float(z.length),
                                 domestic=str(z.get("border_class", "")) == "domestic"))
        pipes = n.links[n.links.carrier.isin(["H2 pipeline", "CO2 pipeline", "gas pipeline"]) & (n.links.border_class == "cross_border")]
        new_pairs = {tuple(sorted((r["countries"].split("-")))) for r in rows}
        built = [r for r in rows if r["mw"] > 1.0]
        res["corridors"][t] = dict(new_components=len(rows), built_over_1mw=built, built_total_mw=round(sum(r["mw"] for r in built), 1),
                                   xb_pipelines_built_over_1mw={car: int(((pipes.carrier == car) & (pipes.p_nom_opt > 1.0)).sum()) for car in ("H2 pipeline", "CO2 pipeline", "gas pipeline")})
        # cross-border electricity exchange of BN / PH / TL (TWh imported / exported through their cross-border lines / links)
        ex = {}
        for c in ("BN", "PH", "TL"):
            imp = expo = 0.0
            for typ, flow in (("Line", "p0"), ("Link", "p0")):
                d = n.df(typ); d = d[d.border_class == "cross_border"] if "border_class" in d else d.iloc[0:0]
                if typ == "Link":
                    d = d[d.carrier == "DC"]
                for k, z in d.iterrows():
                    c0, c1 = n.buses.at[z.bus0, "country"], n.buses.at[z.bus1, "country"]
                    if c not in (c0, c1):
                        continue
                    f = n.pnl(typ)[flow][k] * w if k in n.pnl(typ)[flow] else 0.0
                    pos, neg = float(f.clip(lower=0).sum()) / 1e6, float((-f).clip(lower=0).sum()) / 1e6   # p0 > 0: bus0 -> bus1
                    if c == c0:
                        expo += pos; imp += neg
                    else:
                        imp += pos; expo += neg
            ex[c] = dict(import_twh=round(imp, 3), export_twh=round(expo, 3))
        res["exchange"][t] = ex
        sh = gen["co2"].get(t, {}).get("shipping", {})
        res["shipping"][t] = dict(by_pair_mt={k: v["mt"] for k, v in sorted(sh.items(), key=lambda kv: -kv[1]["mt"])}, total_mt=round(sum(v["mt"] for v in sh.values()), 3),
                                  freight_meur=round(sum(v["freight_meur"] for v in sh.values()), 2),
                                  extra_asean_total_mt=round(sum(gen["co2"].get(t, {}).get("extra_asean_mt", {}).values()), 3),
                                  extra_asean_total_mt_s4d=round(sum(gen["co2_s4c"].get(t, {}).get("extra_asean_mt", {}).values()), 3))
    li = (gen["ledgers"].get("integrated") or {}).get("totals_bn_eur", {}); ld = (gen["ledgers"].get("disconnected") or {}).get("totals_bn_eur", {})
    s4d = json.loads((a.ref_mains.parent.parent / "s4d5/analysis/S4D5_SMOKE_SUMMARY.json").read_text()).get("disconnected_minus_integrated_bn_eur", {}) \
        if (a.ref_mains.parent.parent / "s4d5/analysis/S4D5_SMOKE_SUMMARY.json").exists() else {}
    res["focus"] = {c: dict(integrated_bn_eur=li.get(c), disconnected_bn_eur=ld.get(c), disconnected_minus_integrated=round(ld.get(c, 0.0) - li.get(c, 0.0), 4),
                            disconnected_minus_integrated_s4d=s4d.get(c)) for c in FOCUS}
    (out / "S4E3_SMOKE_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(dict(vs_s4d=res["vs_s4d"], corridors={t: dict(built_total_mw=v["built_total_mw"], n_built=len(v["built_over_1mw"]), pipes=v["xb_pipelines_built_over_1mw"]) for t, v in res["corridors"].items()},
                          exchange=res["exchange"], shipping={t: {k: v for k, v in s.items() if k != "by_pair_mt"} for t, s in res["shipping"].items()},
                          focus=res["focus"], B6=(res["B6"] or {}).get("difference")), indent=1, default=str))


if __name__ == "__main__":
    main()
