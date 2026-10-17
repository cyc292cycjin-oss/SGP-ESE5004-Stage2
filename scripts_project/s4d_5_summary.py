"""S4D-5 smoke summary (S4D instruction section S4D-5): integrated STEPS and disconnected STEPS (the S4D-4 mains, same model code) and integrated
NZE, profile A (formal_barrier), 56x3h. Reports the change against the S4C-6 smoke (CO2 shipping and extra-ASEAN storage, capacity and generation
by country, objective), the country ledgers and identity (B16_LEDGER), B5 / B6 and the gates under both acceptance bases. SMOKE_TEST_ONLY: 56
snapshots (2013-01-01..01-07) re-weighted to 8760 h - the wind / solar scale cannot be judged from it (decision 47).

    python scripts_project/s4d_5_summary.py --mains results_project/s4d/s4d4/solves --nze results_project/s4d/s4d5/solves \
        --s4c results_project/s4c/s4c6/solves_main --out results_project/s4d/s4d5/analysis
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
from s4c_6_summary import gate_row_dir, lng_binding, run_row_dir, solved_in  # noqa: E402

RUNS = ("integrated", "disconnected", "integrated_nze")
FOCUS = ("KH", "LA", "MM", "SG")


def co2_items(d: Path) -> dict:
    p = d / "CO2_FLOWS.json"
    if not p.exists():
        return {}
    f = json.loads(p.read_text())
    ex = f.get("extra_asean_by_country") or {}
    return dict(extra_asean_mt={c: round(v.get("exported_t", 0.0) / 1e6, 4) for c, v in ex.items()},
                transit_mt={c: round(v.get("transit_t", 0.0) / 1e6, 4) for c, v in ex.items() if v.get("transit_t")},
                transit_freight_meur={c: round(v.get("transit_freight_eur", 0.0) / 1e6, 3) for c, v in ex.items() if v.get("transit_freight_eur")},
                shipping={k: dict(mt=round(v["t"] / 1e6, 4), freight_meur=round(v["freight_eur"] / 1e6, 3)) for k, v in (f.get("intra_asean_shipping") or {}).items()},
                sequestered_mt={c: round(v.get("final_level_t", 0.0) / 1e6, 4) for c, v in (f.get("sequestered_by_country") or {}).items()},
                cross_border_pipeline=f.get("cross_border_pipeline"))


def main():
    ap = argparse.ArgumentParser()
    for k in ("mains", "nze", "s4c", "out"):
        ap.add_argument("--" + k, type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    import pypsa
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    from phase4_static import config
    from s4a_4_smoke_compare import tables
    from s4b_smoke_summary import system_items
    from v5.v5_gates import gate_b5_single_switch, gate_b6_cost
    dirs = {"integrated": a.mains / "integrated", "disconnected": a.mains / "disconnected", "integrated_nze": a.nze / "integrated_nze"}
    res = dict(label="SMOKE_TEST_ONLY (56x3h 2013-01-01..01-07, representative weights 8760/56; decision 47) - wind / solar scale cannot be judged from 56 snapshots",
               runs=[], gates={}, s4c={}, ledgers={}, co2={}, co2_s4c={})
    nets, refs = {}, {}
    for t in RUNS:
        d = dirs[t]
        if not (d / "SOLVE_RECEIPT.json").exists():
            continue
        res["runs"].append(dict(run=t) | run_row_dir(d))
        g = gate_row_dir(d.parent, t)
        if g:
            res["gates"][t] = g
        p = solved_in(d)
        if p:
            nets[t] = pypsa.Network(str(p))
        rs = a.s4c / t
        r = json.loads((rs / "SOLVE_RECEIPT.json").read_text()) if (rs / "SOLVE_RECEIPT.json").exists() else {}
        res["s4c"][t] = dict(objective=r.get("objective"))
        q = solved_in(rs)
        if q:
            refs[t] = pypsa.Network(str(q))
        res["co2"][t] = co2_items(d); res["co2_s4c"][t] = co2_items(rs)
        if (d / "COUNTRY_COST_LEDGER.csv").exists():
            L = pd.read_csv(d / "COUNTRY_COST_LEDGER.csv", index_col=0)
            ident = json.loads((d / "LEDGER_IDENTITY.json").read_text())["identity"]
            res["ledgers"][t] = dict(totals_bn_eur={k: round(float(v) / 1e9, 4) for k, v in L["total"].items()},
                                     totals_length_split_bn_eur={k: round(float(v) / 1e9, 4) for k, v in L["total_length_split"].items()},
                                     relative_error=ident["relative_error"], pool_surplus_eur=-ident["difference_sources"]["asean_pool_surplus"])
    for t, n in nets.items():
        tn = tables(n); tn.to_csv(a.out / f"CAP_GEN_BY_COUNTRY_{t}.csv", index=False)
        it = system_items(n); res[f"items_{t}"] = it; res[f"lng_{t}"] = lng_binding(it)
        res[f"asean_{t}"] = tn.groupby("group")[["gw", "twh"]].sum().round(3).to_dict("index")
        if t in refs:
            tr = tables(refs[t])
            m = tn.merge(tr, on=["group", "country"], how="outer", suffixes=("_S4D", "_S4C")).fillna(0.0)
            m["d_gw"] = m["gw_S4D"] - m["gw_S4C"]; m["d_twh"] = m["twh_S4D"] - m["twh_S4C"]
            m.to_csv(a.out / f"CAP_GEN_BY_COUNTRY_{t}_VS_S4C.csv", index=False)
            big = m.loc[(m.d_gw.abs() >= 0.5) | (m.d_twh.abs() >= 2.0)].sort_values("d_twh", key=abs, ascending=False)
            res[f"largest_changes_vs_s4c_{t}"] = big.head(25)[["group", "country", "gw_S4C", "gw_S4D", "d_gw", "twh_S4C", "twh_S4D", "d_twh"]].round(3).to_dict("records")
            res["s4c"][t]["objective_change_eur"] = float(n.objective) - float(refs[t].objective)
            res["s4c"][t]["objective_change_rel"] = (float(n.objective) - float(refs[t].objective)) / float(refs[t].objective)
    if "integrated" in nets and "disconnected" in nets:
        ni, nd = nets["integrated"], nets["disconnected"]
        res["B5"] = gate_b5_single_switch(config(HERE.parent, "integrated"), config(HERE.parent, "disconnected"), n_dis_solved=nd, n_int_solved=ni)
        res["B5_maritime_trade_links_disconnected"] = int((nd.links.border_class == "maritime_trade").sum())
        res["B6"] = gate_b6_cost(float(ni.objective), float(nd.objective), "integrated", "disconnected")
        if "integrated" in res["ledgers"] and "disconnected" in res["ledgers"]:
            li, ld = res["ledgers"]["integrated"]["totals_bn_eur"], res["ledgers"]["disconnected"]["totals_bn_eur"]
            res["disconnected_minus_integrated_bn_eur"] = {k: round(ld.get(k, 0.0) - li.get(k, 0.0), 4) for k in sorted(set(li) | set(ld))}
    res["focus_countries"] = {c: {t: dict(ledger_bn_eur=(res["ledgers"].get(t, {}).get("totals_bn_eur") or {}).get(c),
                                          extra_asean_mt=res["co2"].get(t, {}).get("extra_asean_mt", {}).get(c),
                                          extra_asean_mt_s4c=res["co2_s4c"].get(t, {}).get("extra_asean_mt", {}).get(c),
                                          shipped_out_mt=sum(v["mt"] for k, v in res["co2"].get(t, {}).get("shipping", {}).items() if k.startswith(c + "->")),
                                          shipped_in_mt=sum(v["mt"] for k, v in res["co2"].get(t, {}).get("shipping", {}).items() if k.endswith("->" + c)),
                                          transit_mt=res["co2"].get(t, {}).get("transit_mt", {}).get(c)) for t in RUNS} for c in FOCUS}
    (a.out / "S4D5_SMOKE_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str))
    print(pd.DataFrame(res["runs"])[["run", "termination", "objective_eur", "num_col", "nnz", "barrier_iterations", "barrier_seconds", "solve_seconds", "peak_rss_gib_receipt"]].to_string())
    for t, g in res["gates"].items():
        print(t, {k: g.get(k) for k in ["all_passed_barconvtol", "all_passed_solver_tolerances"]}, "vs S4C", res["s4c"].get(t))
    print("B5", json.dumps(res.get("B5"), default=str)[:300]); print("B6", json.dumps(res.get("B6"), default=str)[:300])
    print("co2", json.dumps(res["co2"], default=str)[:1500]); print("focus", json.dumps(res["focus_countries"], default=str)[:1500])


if __name__ == "__main__":
    main()
