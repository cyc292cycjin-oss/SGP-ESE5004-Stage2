"""V3 phase 2 outputs and tests (instruction phase 2 items 2 and 3): demand table v3, node-level difference table, EV shape figures. No build, no solve.

    PYTHONHASHSEED=0 python scripts_project/v3_tables.py --v2-network <integrated_2920_3h_unsolved.nc> --v2-table <DEMAND_BY_COUNTRY_SECTOR_CARRIER_v2.csv> --main <main checkout> --out <deliverable dir>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from d1_common import DEMAND_DIR, ROOT, sha256
from v3_ev import NODE_TZ, SHAPE, ev_series
from v3_facility_shares import v2_shares
from v3_industry import CARRIERS, SUMMARY, V3_DIR, col, decompose, future_vectors

LOAD_NAME = dict(coal="coal final energy", oil="oil final energy", gas="gas final energy", biomass="biomass final energy", electricity="industry electricity", hydrogen="industry hydrogen", heat="industry heat",
                 ammonia="industry ammonia", methanol="industry methanol", heat_medium_a="industry heat medium A", heat_medium_b="industry heat medium B", heat_high="industry heat high")
FORM = dict(coal="final energy", oil="final energy", gas="final energy", biomass="final energy", electricity="final electricity (process routes)", hydrogen="H2 (DRI steel / chemicals)", heat="useful heat < 150 C",
            ammonia="product (NH3, national bus)", methanol="product (MeOH, national bus)", heat_medium_a="useful heat 150-200 C", heat_medium_b="useful heat 200-400 C", heat_high="useful heat > 400 C")
ACCOUNT = dict(coal="IndustryFinalEnergy", oil="IndustryFinalEnergy", gas="IndustryFinalEnergy", biomass="IndustryFinalEnergy", electricity="IndustryElectricityRoutes", hydrogen="IndustryHydrogenDRI", heat="IndustryLowTemperatureHeat",
               ammonia="IndustryAmmonia", methanol="IndustryMethanol", heat_medium_a="IndustryHeatMediumA", heat_medium_b="IndustryHeatMediumB", heat_high="IndustryHeatHigh")
TOL = 1e-9


def bunker_nodes(main: Path) -> pd.DataFrame:
    """Assembly port / airport size shares (D162-1 a, D162-2 a): country, account, node, share."""
    a = main / "results_project/assembly_v1/final_allocation"; am = json.loads((a / "allocation_manifest.json").read_text())
    z = np.load(a / am["arrays_file"], allow_pickle=False); rows = {}
    for ar in am["records"]:
        p = ar["InputID"].split(":")
        if p[3] in ("InternationalShippingBunker", "InternationalAviationBunker"):
            x = np.asarray(z[ar["ArrayKey"]], dtype=float); x = x.reshape(-1, 1) if x.ndim == 1 else x
            if x.sum() > 0:
                for j, n in enumerate(ar["Nodes"]):
                    if x[:, j].sum() > 0:
                        rows[(p[0], p[3], n)] = float(x[:, j].sum() / x.sum())
    return pd.DataFrame([dict(country=k[0], account=k[1], node=k[2], share=v) for k, v in rows.items()])


def main():
    import pypsa
    import logging
    logging.disable(logging.WARNING)
    p = argparse.ArgumentParser()
    p.add_argument("--v2-network", type=Path, required=True); p.add_argument("--v2-table", type=Path, required=True); p.add_argument("--main", type=Path, required=True); p.add_argument("--out", type=Path, required=True)
    a = p.parse_args(); a.out.mkdir(parents=True, exist_ok=True); (a.out / "figures").mkdir(exist_ok=True); (a.out / "evidence").mkdir(exist_ok=True)
    v2t = pd.read_csv(a.v2_table)
    sub = pd.read_csv(V3_DIR / "INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv"); sub = sub[sub.case == "main"]
    S = pd.read_csv(V3_DIR / "INDUSTRY_NODE_SHARES_V3.csv"); share = {k: dict(zip(g.node, g.share)) for k, g in S.groupby(["country", "subsector"])}
    v2s = v2_shares(a.main); fut = future_vectors(); v2sum = pd.read_csv(DEMAND_DIR / SUMMARY).set_index("country")
    n = pypsa.Network(str(a.v2_network)); bk = n.meta["research_bunkers"]["by_country"]
    tests = {}
    # ---- demand table v3 ---------------------------------------------------------------------------------------------------------------------
    keep = v2t[~v2t.sector.isin(["Industry", "InternationalBunkers"])].copy()
    rows = []
    for _, z in sub.groupby(["country", "subsector", "carrier"], as_index=False).mwh_2050.sum().iterrows():
        rows.append(dict(country=z.country, sector="Industry", subsector=z.subsector, carrier=LOAD_NAME[z.carrier], twh=z.mwh_2050 / 1e6, energy_form=FORM[z.carrier], network_account=ACCOUNT[z.carrier],
                         derivation="v3_industry.py (residual stays in other)"))
    for c, d in sorted(bk.items()):
        rows.append(dict(country=c, sector="InternationalBunkers", subsector="international aviation (nodes; ASEAN bunker account)", carrier="oil final energy", twh=d.get("aviation_oil_mwh", 0.0) / 1e6, energy_form="final energy", network_account="InternationalAviationBunker", derivation="Assembly airport size shares"))
        rows.append(dict(country=c, sector="InternationalBunkers", subsector="international shipping (nodes; ASEAN bunker account)", carrier="shipping methanol", twh=d.get("shipping_shipping_methanol_mwh", 0.0) / 1e6, energy_form="methanol final energy", network_account="InternationalShippingBunker", derivation="Assembly port size shares"))
    v3t = pd.concat([keep, pd.DataFrame(rows)], ignore_index=True).sort_values(["country", "sector", "subsector", "carrier"])
    v3t.to_csv(a.out / "DEMAND_BY_COUNTRY_SECTOR_CARRIER_v3.csv", index=False)
    # test 1: country x sector totals equal v2 (bunkers compared by country)
    # Industry reference = the table the v2 build binds (INDUSTRY_2050_SUMMARY_*): the v2 review csv is above it by 1.55 MWh (SG), 0.02 MWh (BN) from its finer sub-sector split
    x2 = v2t[v2t.sector != "InternationalBunkers"].groupby(["country", "sector"]).twh.sum(); x3 = v3t[v3t.sector != "InternationalBunkers"].groupby(["country", "sector"]).twh.sum()
    bound = v2sum[[col(c) for c in CARRIERS]].sum(axis=1) / 1e6; review_gap = {c: float(x2.get((c, "Industry"), 0.0) - bound[c]) for c in bound.index}
    for c in bound.index:
        if (c, "Industry") in x2.index:
            x2.loc[(c, "Industry")] = bound[c]
    rel = ((x3 - x2).abs() / x2.abs().clip(lower=1e-9)).replace([np.inf], 0).fillna(0)
    tests["T1_country_sector_totals"] = dict(max_rel=float(rel.max()), passed=bool(rel.max() <= TOL), pairs=int(len(rel)), industry_reference="v2 bound table INDUSTRY_2050_SUMMARY_*", v2_review_csv_minus_bound_twh=review_gap)
    # test 2: industry sub-sectors sum to the country total
    t = sub.groupby("country").mwh_2050.sum(); T = v2sum[[col(c) for c in CARRIERS]].sum(axis=1)
    r2 = ((t - T.reindex(t.index)).abs() / T.reindex(t.index)); tests["T2_subsectors_sum_to_industry_total"] = dict(max_rel=float(r2.max()), passed=bool(r2.max() <= TOL))
    # ---- node difference table, test 3 ------------------------------------------------------------------------------------------------------
    diff, node_sum = [], {}
    for c in v2sum.index:
        if float(T[c]) <= 0:
            continue
        base = v2s[c]; d2 = decompose(v2sum.loc[c], fut); t3 = sub[sub.country == c]
        all_keys = {(s, k) for s, v in d2.items() for k in v} | set(zip(t3.subsector, t3.carrier))
        for s, k in sorted(all_keys):
            q2 = float(d2.get(s, {}).get(k, 0.0)); y = t3[(t3.subsector == s) & (t3.carrier == k)].mwh_2050.sum(); q3 = float(y)
            sh3 = base if k == "ammonia" else (share.get((c, s)) or base)
            if abs(sum(sh3.values()) - 1.0) > TOL:
                raise ValueError(f"shares of {c} {s}")
            node_sum[(c, s, k)] = (q3, sum(q3 * x for x in sh3.values()))
            for nd in sorted(set(base) | set(sh3)):
                v2_ = q2 * base.get(nd, 0.0) / 1e6; v3_ = q3 * sh3.get(nd, 0.0) / 1e6
                if abs(v3_ - v2_) > 1e-9:
                    diff.append(dict(country=c, sector="Industry", subsector=s, carrier=LOAD_NAME[k], node=nd, twh_v2=v2_, twh_v3=v3_, delta_twh=v3_ - v2_))
    bn = bunker_nodes(a.main)
    for _, z in bn.iterrows():
        key = "aviation_oil_mwh" if z.account == "InternationalAviationBunker" else "shipping_shipping_methanol_mwh"
        v3_ = bk[z.country].get(key, 0.0) * z.share / 1e6
        if v3_ > 0:
            diff.append(dict(country=z.country, sector="InternationalBunkers", subsector=z.account, carrier="oil final energy" if "Aviation" in z.account else "shipping methanol", node=z.node, twh_v2=0.0, twh_v3=v3_, delta_twh=v3_))
    for lab, name, key in (("InternationalAviationBunker", "oil final energy", "aviation_oil_mwh"), ("InternationalShippingBunker", "shipping methanol", "shipping_shipping_methanol_mwh")):
        v_ = sum(d.get(key, 0.0) for d in bk.values()) / 1e6
        diff.append(dict(country="ASEAN", sector="InternationalBunkers", subsector=lab, carrier=name, node="ASEAN bus", twh_v2=v_, twh_v3=0.0, delta_twh=-v_))
    D = pd.DataFrame(diff); D.to_csv(a.out / "DEMAND_DIFF_V3_V2.csv", index=False)
    tests["T3_node_allocation_conserves_country_subsector"] = dict(max_abs_mwh=float(max(abs(u - w) for u, w in node_sum.values())), passed=bool(max(abs(u - w) / max(1.0, u) for u, w in node_sum.values()) <= TOL), keys=len(node_sum))
    pd.read_csv(V3_DIR / "INDUSTRY_NODE_ALLOCATION_V2_V3.csv").to_csv(a.out / "INDUSTRY_NODE_ALLOCATION_V2_V3.csv", index=False)
    # test 6: bunker country totals
    b3 = D[(D.sector == "InternationalBunkers") & (D.country != "ASEAN")].groupby(["country", "subsector"]).twh_v3.sum()
    dev = 0.0
    for (c, ac), v in b3.items():
        key = "aviation_oil_mwh" if "Aviation" in ac else "shipping_shipping_methanol_mwh"
        dev = max(dev, abs(v - bk[c].get(key, 0.0) / 1e6) / max(v, 1e-9))
    tests["T6_bunker_country_totals"] = dict(max_rel=float(dev), passed=bool(dev <= TOL), total_twh=float(b3.sum()))
    # ---- EV: annual totals, peak hours, figures -------------------------------------------------------------------------------------------------
    w = pd.read_csv(SHAPE); week = w.sort_values(["weekday", "hour"]).consumption_norm.to_numpy(); plug = w.sort_values(["weekday", "hour"]).plugin.to_numpy()
    tz = pd.read_csv(NODE_TZ).set_index("node")
    ev = n.loads[n.loads.carrier == "land transport EV"]; sn = n.snapshots
    res, peak = {}, []
    for name, z in ev.iterrows():
        nd = str(z.bus)[: -len(" EV battery")]; off = float(tz.at[nd, "utc_offset_h"]); s = ev_series(sn, off, week); s = s / s.mean()
        annual = float(z.p_set) * 8760.0; series = float(z.p_set) * s
        res[name] = abs(float((series * 3.0).sum()) - annual) / annual
        lh = ((sn.hour + off) % 24).to_numpy(); wd = ((sn + pd.Timedelta(hours=off)).dayofweek < 5)
        prof = pd.Series(s[wd]).groupby(lh[wd]).mean()
        peak.append(dict(node=nd, country=z.country, utc_offset_h=off, peak_local_snapshot_start_h=float(prof.idxmax()), peak_over_mean=float(prof.max())))
    P = pd.DataFrame(peak); P.groupby(["country", "utc_offset_h"]).agg(nodes=("node", "size"), peak_local_h=("peak_local_snapshot_start_h", "median"), peak_over_mean=("peak_over_mean", "median")).reset_index().to_csv(a.out / "evidence/EV_PEAK_LOCAL_HOURS.csv", index=False)
    tests["T4_ev_annual_totals"] = dict(max_rel=float(max(res.values())), passed=bool(max(res.values()) <= TOL), nodes=len(res))
    tests["T5_ev_peak_local_hour"] = dict(range_h=[float(P.peak_local_snapshot_start_h.min()), float(P.peak_local_snapshot_start_h.max())], rule="snapshot start in 12-18 h local (3 h snapshots, weekday mean; RAMP peak at 16 h local clock)", passed=bool(P.peak_local_snapshot_start_h.between(12, 18).all()))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for off in sorted(tz.utc_offset_h.unique()):
        s = ev_series(sn, off, week); s = s / s.mean(); lh = ((sn.hour + off) % 24).to_numpy(); wd = ((sn + pd.Timedelta(hours=off)).dayofweek < 5)
        prof = pd.Series(s[wd]).groupby(lh[wd]).mean().sort_index(); we = pd.Series(s[~wd]).groupby(lh[~wd]).mean().sort_index()
        fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=140); fig.patch.set_facecolor("#fcfcfb"); ax.set_facecolor("#fcfcfb")
        ax.plot(prof.index + 1.5, prof.values, color="#2a78d6", lw=2, marker="o", ms=4, label="v3 weekday (RAMP 26-country local week)")
        ax.plot(we.index + 1.5, we.values, color="#2a78d6", lw=2, ls=":", label="v3 weekend")
        ax.axhline(1.0, color="#eb6834", lw=2, ls="--", label="v2 flat load")
        ax.set_xlim(0, 24); ax.set_xticks(range(0, 25, 3)); ax.set_ylim(0, None); ax.set_xlabel("local time (h), 3 h snapshot centres", color="#52514e"); ax.set_ylabel("load / annual mean", color="#52514e")
        ax.set_title(f"EV load shape, nodes at UTC+{off:g} ({sorted(tz[tz.utc_offset_h == off].country.unique())})", fontsize=10, loc="left", color="#0b0b0b")
        ax.grid(axis="y", color="#e6e5e0", lw=0.8); [ax.spines[k].set_visible(False) for k in ("top", "right")]; ax.legend(frameon=False, fontsize=8, loc="upper left")
        fig.tight_layout(); fig.savefig(a.out / "figures" / f"EV_SHAPE_V2_V3_UTC+{off:g}.png"); plt.close(fig)
    tests["all_passed"] = bool(all(v["passed"] for v in tests.values() if isinstance(v, dict)))
    tests["outputs"] = {f: sha256(a.out / f) for f in ("DEMAND_BY_COUNTRY_SECTOR_CARRIER_v3.csv", "DEMAND_DIFF_V3_V2.csv", "INDUSTRY_NODE_ALLOCATION_V2_V3.csv")}
    (a.out / "evidence/PHASE2_TESTS.json").write_text(json.dumps(tests, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in tests.items() if k != "outputs"}, indent=0))
    print(P.groupby("utc_offset_h").peak_local_snapshot_start_h.agg(["min", "max"]).to_dict(), "diff rows", len(D), "v3 total TWh", round(v3t.twh.sum(), 2))


if __name__ == "__main__":
    main()
