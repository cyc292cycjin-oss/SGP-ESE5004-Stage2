"""L23 C9 first-round summary (L23 instruction section 3; read-only, no solve): the first cloud batch 365x24h (integrated STEPS, disconnected
STEPS, disconnected gap diagnostic, integrated NZE; profile A, serial) against the S4K smoke (56x3h, results_project/s4k/s4k3) and the S4K
extrapolation (CLOUD_RESOURCE_ESTIMATE.md section 20). Generic part = s4d_5_summary (run table, gates under both bases, B5 / B6, capacity and
generation by country, CO2 flows, ledgers); S4K part = cross-border transport and losses by pair, line builds and lines at the single-line cap,
the TH-MY corridor; L23 part = Gurobi seconds per work unit (instance vs local), gate details, ledger by subject, the registered items (long
clustered AC lines, VN storage, PH, one-way existing gas pipelines), nodal price extremes. DAILY_SCREENING_365X24H: allocation conclusions rest on
2920x3h (working principle / formal resolution item 6).

    python scripts_project/l23_c9_summary.py --export <unpacked>/export --nze-late <nze_late>/unpacked/integrated_nze --status <STATUS.txt> \
        --ref results_project/s4k/s4k3/solves --out <out>
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from s4c_6_summary import solved_in  # noqa: E402
from s4d_5_summary import co2_items  # noqa: E402
from s4g_3_summary import at_cap  # noqa: E402
from s4h_3_summary import b16  # noqa: E402
from s4j_6_detail import th_my  # noqa: E402
from s4j_6_summary import caps, transport  # noqa: E402
from s4k_3_summary import clustering, line_table, totals  # noqa: E402

RUNS = ("integrated", "disconnected", "disconnected_gap", "integrated_nze")
COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
S4B_MAIN_SET = ("A1_A2_S4B", "A3_S4B", "A4", "A5_S4B", "A6", "B1_S4B", "B2", "B3_S4B", "B8", "B11", "B12", "B13", "B14", "B15", "B1_BUNKERS", "B16_LEDGER")
S3B_SET = ("A1_A2", "A3", "A4", "A5", "A6", "B1", "B2", "B3", "B8", "B11", "B12", "B13", "B14", "B15", "B1_BUNKERS", "B16_LEDGER")
WU = re.compile(r"(?:solved model in|performed) (\d+) iterations (?:and|in) ([\d.]+) seconds \(([\d.]+) work units\)")


def log_stats(d: Path) -> dict:
    """Barrier iterations, seconds and work units, and the end message, from the scrubbed Gurobi log of a solve folder."""
    p = d / "GUROBI_LOG_SCRUBBED.txt"
    if not p.exists():
        return {}
    t = p.read_text(errors="replace"); m = WU.findall(t)
    out = dict(end=[s for s in ("Optimal objective", "Sub-optimal termination", "Time limit reached", "Numerical trouble") if s in t])
    if m:
        it, s, w = m[-1]; out.update(barrier_iterations=int(it), barrier_seconds=float(s), work_units=float(w), seconds_per_work_unit=float(s) / float(w))
    for k, rx in (("presolve_s", r"Presolve time: ([\d.]+)s"), ("ordering_s", r"Ordering time: ([\d.]+)s")):
        mm = re.search(rx, t)
        if mm:
            out[k] = float(mm.group(1))
    return out


def run_row(d: Path) -> dict:
    r = json.loads((d / "SOLVE_RECEIPT.json").read_text()); lp = r.get("lp") or {}
    return dict(termination=r.get("termination_condition"), status=r.get("status"), objective_eur=r.get("objective"), num_col=lp.get("num_col"), num_row=lp.get("num_row"),
                nnz=lp.get("nnz"), build_seconds=lp.get("build_seconds"), solve_seconds=r.get("solve_seconds"), peak_rss_gib_receipt=(r.get("peak_rss_bytes") or 0) / 2**30,
                solver_profile=r.get("solver_profile")) | log_stats(d)


def status_walls(p: Path) -> dict:
    out = {}
    for line in p.read_text().splitlines():
        m = re.match(r"RUN_(\w+):(\w+):(\d+)s", line)
        if m:
            out[m.group(1)] = dict(status_line=m.group(2), wall_seconds=int(m.group(3)))
        m = re.match(r"KILLED_3H_(\w+):(\S+)", line)
        if m:
            out.setdefault(m.group(1), {})["killed_3h_utc"] = m.group(2)
    return out


def gate_details(g: dict) -> dict:
    """Pass / fail of every gate under both bases, and the measured quantities of the failing ones."""
    passed = {k: (v.get("passed") if isinstance(v, dict) else None) for k, v in g.items() if isinstance(v, dict) and "passed" in v}
    det = {}
    a = g.get("A1_A2_S4B") or {}
    det["A1_A2_S4B"] = {k: a.get(k) for k in ("row_fail_count", "row_violation_max", "row_max_ratio_to_budget", "column_fail_count", "stationarity_fail_count",
                                              "stationarity_normalized_max", "dual_sign_fail_count", "dual_sign_normalized_max", "relative_gap", "complementarity_over_scale",
                                              "row_fail_by_family", "stationarity_fail_by_family") if k in a}
    a = g.get("A1_A2") or {}
    det["A1_A2"] = dict(criteria=a.get("criteria"), metrics={k: v for k, v in (a.get("metrics") or {}).items() if not isinstance(v, (dict, list))})
    det["A3_S4B"] = [f for f in (g.get("A3_S4B") or {}).get("failed", [])]
    b2 = g.get("B2") or {}
    det["B2"] = {c: dict(utilisation=v.get("utilisation"), final_level_t=v.get("final_level_t"), cap_t=v.get("horizon_limit_t", v.get("cap_t")),
                         excess_t=(v.get("final_level_t", 0.0) - v.get("horizon_limit_t", 0.0)) if "horizon_limit_t" in v else None, within_cap=v.get("within_cap", v.get("within")))
                 for c, v in (b2.get("countries") or {}).items()}
    b3 = g.get("B3_S4B") or {}
    f3 = b3.get("failing") or []
    det["B3_S4B"] = dict(failing=len(f3), by_country=pd.Series([f["country"] for f in f3]).value_counts().to_dict() if f3 else {},
                         min_level_mwh=min((f["min_level_mwh"] for f in f3), default=None))
    b14 = g.get("B14") or {}
    det["B14"] = [dict(generator=t["generator"], p_nom_opt_mw=t["p_nom_opt_mw"], p_nom_max_mw=t["p_nom_max_mw"], excess_mw=t["p_nom_opt_mw"] - t["p_nom_max_mw"])
                  for t in b14.get("terminals", []) if t.get("within_max") is False]
    b15 = g.get("B15") or {}
    det["B15"] = {c: dict(cap_mwh=v["cap_mwh"], annual_mwh=v["annual_mwh"], excess_mwh=v["annual_mwh"] - v["cap_mwh"], excess_rel=(v["annual_mwh"] - v["cap_mwh"]) / v["cap_mwh"])
                  for c, v in (b15.get("by_country") or {}).items() if v["annual_mwh"] > v["cap_mwh"]}
    det["B16_LEDGER"] = {k: (g.get("B16_LEDGER") or {}).get(k) for k in ("relative_error", "tolerance", "difference")}
    bb = g.get("B1_BUNKERS") or {}
    det["B1_BUNKERS"] = {k: bb.get(k) for k in ("final_level_tco2", "tolerance_t")}
    b1 = g.get("B1_S4B") or {}
    det["B1_S4B_max_ratio"] = max((v.get("ratio_to_budget", 0.0) for v in (b1.get("countries") or {}).values()), default=None)
    return dict(passed=passed, all_passed_solver_tolerances=g.get("all_passed_solver_tolerances"), all_passed_barconvtol=g.get("all_passed_barconvtol"),
                failing_solver_tolerances=[k for k in S4B_MAIN_SET if passed.get(k) is False], failing_barconvtol=[k for k in S3B_SET if passed.get(k) is False], details=det)


def ledger(d: Path) -> pd.DataFrame | None:
    p = d / "COUNTRY_COST_LEDGER.csv"
    return pd.read_csv(p, index_col=0) if p.exists() else None


def ledger_subjects(li: pd.DataFrame, ld: pd.DataFrame, ref_i: pd.DataFrame | None, ref_d: pd.DataFrame | None) -> dict:
    """Disconnected - integrated by country and subject (bn EUR); the three largest subjects per country; direction and rank vs the S4K smoke."""
    cols = [c for c in li.columns if c not in ("total", "total_length_split")]
    diff = (ld.reindex(index=li.index.union(ld.index), columns=cols).fillna(0.0) - li.reindex(index=li.index.union(ld.index), columns=cols).fillna(0.0)) / 1e9
    tot = (ld["total"].reindex(diff.index).fillna(0.0) - li["total"].reindex(diff.index).fillna(0.0)) / 1e9
    out = dict(total_bn_eur=tot.round(4).to_dict(), integrated_bn_eur=(li["total"] / 1e9).round(4).to_dict(), disconnected_bn_eur=(ld["total"] / 1e9).round(4).to_dict(),
               by_subject_bn_eur=diff.round(4).to_dict("index"), main_subjects={})
    for c in diff.index:
        s = diff.loc[c]; s = s[s.abs() > 1e-4].sort_values(key=abs, ascending=False)
        out["main_subjects"][c] = [dict(subject=k, bn_eur=round(float(v), 4)) for k, v in s.head(4).items()]
    if ref_i is not None and ref_d is not None:
        rt = (ref_d["total"].reindex(diff.index).fillna(0.0) - ref_i["total"].reindex(diff.index).fillna(0.0)) / 1e9
        cc = [c for c in COUNTRIES if c in tot.index]
        rk = tot[cc].rank(ascending=False).astype(int); rr = rt[cc].rank(ascending=False).astype(int)
        out["vs_s4k_smoke"] = {c: dict(l23_bn_eur=round(float(tot[c]), 4), s4k_smoke_bn_eur=round(float(rt[c]), 4), same_sign=bool(np.sign(tot[c]) == np.sign(rt[c])),
                                       rank_l23=int(rk[c]), rank_s4k_smoke=int(rr[c])) for c in cc}
        out["vs_s4k_smoke_bunker"] = dict(l23_bn_eur=round(float(tot.get("ASEAN_BUNKER", 0.0)), 4), s4k_smoke_bn_eur=round(float(rt.get("ASEAN_BUNKER", 0.0)), 4))
        out["rank_correlation_spearman"] = float(pd.Series(rk).corr(pd.Series(rr), method="pearson"))
    return out


def gas_pipelines(n) -> list:
    """Existing cross-border gas pipelines: direction, capacity, expansion and use (one-way existing pipelines, S4I R11)."""
    w = n.snapshot_weightings.objective; rows = []
    L = n.links[(n.links.carrier == "gas pipeline") & (n.links.border_class == "cross_border")]
    for k, z in L.iterrows():
        if k not in n.links_t.p0:
            continue
        p0 = n.links_t.p0[k]; cap = float(z.p_nom_opt) if z.p_nom_extendable else float(z.p_nom)
        rows.append(dict(link=str(k), bus0=str(z.bus0), bus1=str(z.bus1), countries=f"{n.buses.at[z.bus0, 'country']}->{n.buses.at[z.bus1, 'country']}",
                         existing_mw=float(z.p_nom), opt_mw=cap, new_mw=cap - float(z.p_nom), p_min_pu=float(z.p_min_pu), length_km=float(z.get("length", np.nan)),
                         reversed=bool(z.get("reversed", False)), sent_twh=float(p0.clip(lower=0).mul(w).sum()) / 1e6, back_twh=float((-p0).clip(lower=0).mul(w).sum()) / 1e6,
                         mean_utilisation=(float(p0.mean()) / cap if cap > 1 else None), share_hours_at_cap=(float((p0 >= 0.999 * cap).mean()) if cap > 1 else None)))
    return [r for r in rows if r["existing_mw"] > 1 or r["new_mw"] > 1]


def pipelines_built(n) -> dict:
    out = {}
    for car in ("gas pipeline", "H2 pipeline", "CO2 pipeline"):
        L = n.links[(n.links.carrier == car) & (n.links.border_class == "cross_border")]
        if "reversed" in L:
            L = L[~L.reversed.astype(bool)]
        new = (L.p_nom_opt - L.p_nom).where(L.p_nom_extendable, 0.0)
        d = {}
        for k, v in new.items():
            if v > 1.0:
                pr = "-".join(sorted((str(n.buses.at[L.at[k, "bus0"], "country"]), str(n.buses.at[L.at[k, "bus1"], "country"]))))
                d[pr] = round(d.get(pr, 0.0) + float(v) / 1e3, 3)
        out[car] = dict(new_gw_by_pair=d, existing_gw=round(float(L.p_nom.sum()) / 1e3, 3))
    return out


def long_lines(n, T: pd.DataFrame) -> list:
    """The cross-border AC lines with the largest loss factor or length (S4K section 7 item 2): build, flow, losses."""
    L = n.lines
    cb = T[T.border_class == "cross_border"].copy()
    cb["length_km"] = L.length.reindex(cb.index).astype(float)
    cb["pair"] = [f"{n.buses.at[L.at[k, 'bus0'], 'country']}-{n.buses.at[L.at[k, 'bus1'], 'country']}" for k in cb.index]
    top = cb.sort_values("ac_loss_lambda", ascending=False).head(8)
    return [dict(line=str(k), pair=r.pair, length_km=round(r.length_km, 1), ac_loss_lambda=round(float(r.ac_loss_lambda), 4), s_nom_mw=round(r.s_nom, 1), s_nom_opt_mw=round(r.s_nom_opt, 1),
                 new_mw=round(r.new_mw, 1), at_s_nom_max=bool(r.at_s_nom_max), sent_twh=round(r.sent_twh, 4), loss_twh=round(r.loss_twh, 4),
                 loss_share=(round(r.loss_twh / r.sent_twh, 4) if r.sent_twh > 1e-6 else None)) for k, r in top.iterrows()]


def prices(d: Path) -> dict:
    p = d / "NODAL_PRICES.csv"
    if not p.exists():
        return {}
    P = pd.read_csv(p, index_col=0)
    head = [c for c in ("country", "carrier", "mean", "min", "max") if c in P.columns]
    out = dict(columns=head[:6], buses=int(len(P)))
    if {"carrier", "max", "min", "mean"} <= set(P.columns):
        ac = P[P.carrier == "AC"] if "AC" in set(P.carrier) else P
        out["ac_mean_by_country"] = ac.groupby("country")["mean"].mean().round(2).to_dict() if "country" in ac else None
        out["ac_max_top"] = ac.sort_values("max", ascending=False).head(8)[["country", "max", "mean"]].round(2).reset_index().to_dict("records") if "country" in ac else None
        out["ac_min_bottom"] = ac.sort_values("min").head(5)[["country", "min", "mean"]].round(2).reset_index().to_dict("records") if "country" in ac else None
        out["all_max_top"] = P.sort_values("max", ascending=False).head(8)[[c for c in ("country", "carrier", "max", "mean") if c in P]].round(2).reset_index().to_dict("records")
    return out


def main():
    ap = argparse.ArgumentParser()
    for k in ("export", "nze_late", "status", "ref", "out"):
        ap.add_argument("--" + k.replace("_", "-"), dest=k, type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    import pypsa
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    from phase4_static import config
    from s4a_4_smoke_compare import tables
    from s4b_smoke_summary import system_items
    from v5.v5_gates import gate_b5_single_switch, gate_b6_cost
    dirs = {t: a.export / t for t in RUNS}; dirs["integrated_nze"] = a.nze_late
    walls = status_walls(a.status)
    res = dict(label="FORMAL_TRIAL_365X24H - DAILY_SCREENING_365X24H (allocation conclusions rest on 2920x3h)", runs={}, reference_runs={}, gates={}, B16={}, co2={},
               co2_ref={}, ledgers={}, capacity_generation={}, asean_by_group={}, items={}, transport={}, transport_totals={}, cross_border_capacity={}, pipelines={},
               at_cap={}, clustering={}, long_lines={}, gas_pipelines_cross_border={}, th_my={}, prices={}, bunker={})
    nets = {}
    for t in RUNS:
        d = dirs[t]
        if not (d / "SOLVE_RECEIPT.json").exists():
            continue
        res["runs"][t] = run_row(d) | walls.get(t, {})
        rd = a.ref / t
        if (rd / "SOLVE_RECEIPT.json").exists():
            res["reference_runs"][t] = run_row(rd)
        if (d / "V5_GATES.json").exists():
            res["gates"][t] = gate_details(json.loads((d / "V5_GATES.json").read_text()))
        res["B16"][t] = {k: b16(d).get(k) for k in ("passed", "relative_error", "tolerance", "difference")}
        res["co2"][t] = co2_items(d); res["co2_ref"][t] = co2_items(rd)
        if (d / "BUNKER_ACCOUNT.json").exists():
            res["bunker"][t] = json.loads((d / "BUNKER_ACCOUNT.json").read_text())
        res["prices"][t] = prices(d)
        L = ledger(d)
        if L is not None:
            res["ledgers"][t] = dict(totals_bn_eur=(L["total"] / 1e9).round(4).to_dict(), sum_bn_eur=round(float(L["total"].sum()) / 1e9, 4))
        p = solved_in(d)
        if p is None or t == "disconnected_gap":
            continue
        n = pypsa.Network(str(p)); nets[t] = n
        tn = tables(n); tn.to_csv(a.out / f"CAP_GEN_BY_COUNTRY_{t}.csv", index=False)
        res["capacity_generation"][t] = f"CAP_GEN_BY_COUNTRY_{t}.csv"
        res["asean_by_group"][t] = tn.groupby("group")[["gw", "twh"]].sum().round(3).to_dict("index")
        res["items"][t] = system_items(n)
        tr = transport(n); res["transport"][t] = tr; res["transport_totals"][t] = totals(tr)
        res["cross_border_capacity"][t] = caps(n); res["pipelines"][t] = pipelines_built(n)
        res["at_cap"][t] = at_cap(n)
        T = line_table(n); T.index.name = "line"; T.reset_index().to_csv(a.out / f"LINE_BUILD_{t}.csv", index=False)
        res["clustering"][t] = clustering(T); res["long_lines"][t] = long_lines(n, T)
        res["gas_pipelines_cross_border"][t] = gas_pipelines(n)
        if "Khlong Ngae – Gurun" in n.links.index:
            res["th_my"][t] = th_my(n)
    # B5 / B6 and the NZE comparison
    if "integrated" in nets and "disconnected" in nets:
        ni, nd = nets["integrated"], nets["disconnected"]
        res["B5"] = gate_b5_single_switch(config(HERE.parent, "integrated"), config(HERE.parent, "disconnected"), n_dis_solved=nd, n_int_solved=ni)
        res["B6"] = gate_b6_cost(float(ni.objective), float(nd.objective), "integrated", "disconnected")
    if "integrated" in res["runs"] and "integrated_nze" in res["runs"]:
        oi, on = res["runs"]["integrated"]["objective_eur"], res["runs"]["integrated_nze"]["objective_eur"]
        res["nze_vs_integrated"] = dict(objective_difference_eur=on - oi, relative=(on - oi) / oi)
        if "integrated" in nets and "integrated_nze" in nets:
            gi = pd.read_csv(a.out / "CAP_GEN_BY_COUNTRY_integrated.csv"); gn = pd.read_csv(a.out / "CAP_GEN_BY_COUNTRY_integrated_nze.csv")
            m = gi.merge(gn, on=["group", "country"], how="outer", suffixes=("_int", "_nze")).fillna(0.0)
            m["d_gw"] = m.gw_nze - m.gw_int; m["d_twh"] = m.twh_nze - m.twh_int
            m.to_csv(a.out / "CAP_GEN_NZE_MINUS_INTEGRATED.csv", index=False)
            res["nze_largest_changes"] = m.loc[(m.d_gw.abs() >= 1.0) | (m.d_twh.abs() >= 5.0)].sort_values("d_twh", key=abs, ascending=False).head(20)[
                ["group", "country", "gw_int", "gw_nze", "d_gw", "twh_int", "twh_nze", "d_twh"]].round(3).to_dict("records")
    li, ld = ledger(dirs["integrated"]), ledger(dirs["disconnected"])
    if li is not None and ld is not None:
        res["ledger_difference"] = ledger_subjects(li, ld, ledger(a.ref / "integrated"), ledger(a.ref / "disconnected"))
        rows = []
        for c, sub in res["ledger_difference"]["by_subject_bn_eur"].items():
            rows.append(dict(entity=c, total=res["ledger_difference"]["total_bn_eur"].get(c)) | sub)
        pd.DataFrame(rows).to_csv(a.out / "LEDGER_DISCONNECTED_MINUS_INTEGRATED_BY_SUBJECT.csv", index=False)
    ln = ledger(dirs["integrated_nze"])
    if li is not None and ln is not None:
        res["ledger_nze_minus_integrated_bn_eur"] = ((ln["total"] - li["total"].reindex(ln.index).fillna(0.0)) / 1e9).round(4).to_dict()
    # instance vs local CPU: Gurobi seconds per work unit (same profile, 8 threads), and the non-solve part (build, LP export, gates)
    sp = {}
    for t in ("integrated", "disconnected", "integrated_nze"):
        r, q = res["runs"].get(t, {}), res["reference_runs"].get(t, {})
        if r.get("seconds_per_work_unit") and q.get("seconds_per_work_unit"):
            sp[t] = dict(instance_s_per_wu=r["seconds_per_work_unit"], local_s_per_wu=q["seconds_per_work_unit"],
                         instance_speed_relative_to_local=q["seconds_per_work_unit"] / r["seconds_per_work_unit"])
    res["cpu_speed"] = sp
    (a.out / "L23_C9_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(dict(runs=res["runs"], cpu_speed=sp, B6=res.get("B6"), gates={t: dict(f=g["failing_solver_tolerances"], f3=g["failing_barconvtol"]) for t, g in res["gates"].items()},
                          ledger=(res.get("ledger_difference") or {}).get("total_bn_eur"), nze=res.get("nze_vs_integrated")), indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
