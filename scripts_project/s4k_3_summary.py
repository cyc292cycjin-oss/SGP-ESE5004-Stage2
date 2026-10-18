"""S4K-3 smoke summary (S4K instruction section S4K-3): integrated STEPS, disconnected STEPS, integrated NZE (profile A, 56x3h) against the S4J-6 smoke
(supplement 01 (b), results_project/s4j/s4j6b) and the S4H-3 smoke (results_project/s4h/s4h3).
Generic part = s4d_5_summary against S4J (run table, gates under both bases, B5 / B6, capacity / generation, CO2 flows, ledgers); S4K part = LP size and
time vs S4J, every AC line's build in the three smokes (S4K / S4J / S4H) and whether the builds still cluster on a capacity threshold, cross-border AC
energy, AC / DC losses and compression by country pair (same function as S4J-6), ledgers (disconnected - integrated) with B16 vs S4J and S4H (focus
TH, LA, KH, VN, MY, MM), the TH-MY corridor, the solver-tolerance acceptance. SMOKE_TEST_ONLY: 56 snapshots, the scale cannot be judged (decision 47).

    python scripts_project/s4k_3_summary.py --run results_project/s4k/s4k3 --ref-j results_project/s4j/s4j6b --ref-h results_project/s4h/s4h3
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
from s4g_3_summary import at_cap  # noqa: E402
from s4h_3_summary import b16, tolerance_flags  # noqa: E402
from s4j_6_detail import th_my  # noqa: E402
from s4j_6_summary import caps, transport  # noqa: E402
from s4k_layers import LAMBDA_COL  # noqa: E402

FOCUS = ("TH", "LA", "KH", "VN", "MY", "MM", "ID", "SG", "PH", "BN", "TL")
RUNS = ("integrated", "disconnected", "integrated_nze")


def totals(tr: dict | None) -> dict:
    out = {}
    for key, cars in (tr or {}).items():
        g = "domestic" if key == "domestic" else "cross_border"
        for car, o in cars.items():
            a = out.setdefault(g, {}).setdefault(car, dict(sent_twh=0.0, loss_twh=0.0, compression_el_twh=0.0))
            for k in a:
                a[k] += o[k]
    for g, cars in out.items():
        el = [cars.get(c, {}) for c in ("AC", "DC")]
        s = sum(x.get("sent_twh", 0.0) for x in el); l = sum(x.get("loss_twh", 0.0) for x in el)
        cars["electricity"] = dict(sent_twh=s, loss_twh=l, loss_share=(l / s if s else None))
        cars["compression_total_twh"] = sum(v.get("compression_el_twh", 0.0) for k, v in cars.items() if isinstance(v, dict) and k not in ("electricity",))
        for c in ("AC", "DC"):
            if c in cars:
                cars[c]["loss_share"] = cars[c]["loss_twh"] / cars[c]["sent_twh"] if cars[c]["sent_twh"] else None
    return out


def line_table(n) -> pd.DataFrame:
    L = n.lines; s = (n.lines_t.p0 - n.lines_t.p1) / 2 if len(n.lines_t.p0.columns) else pd.DataFrame(0.0, index=n.snapshots, columns=L.index)
    smax = n.get_switchable_as_dense("Line", "s_max_pu").max()
    w = n.snapshot_weightings.objective
    loss = (n.lines_t.p0 + n.lines_t.p1).mul(w, axis=0).sum() / 1e6
    sent = pd.concat([n.lines_t.p0.clip(lower=0).mul(w, axis=0).sum(), n.lines_t.p1.clip(lower=0).mul(w, axis=0).sum()], axis=1).sum(axis=1) / 1e6
    return pd.DataFrame(dict(border_class=L.border_class.astype(str), s_nom=L.s_nom.astype(float), s_nom_opt=L.s_nom_opt.astype(float), s_nom_max=L.s_nom_max.astype(float),
                             new_mw=(L.s_nom_opt - L.s_nom).astype(float), rating_mw=(smax * L.s_nom_opt).astype(float), max_abs_flow_mw=s.abs().max().reindex(L.index).astype(float),
                             at_s_nom_max=(L.s_nom_opt >= L.s_nom_max - 1.0), s4j_zero_loss_limit_mw=(smax * L.s_nom_max / 4).astype(float),
                             loss_twh=loss.reindex(L.index).astype(float), sent_twh=sent.reindex(L.index).astype(float),
                             ac_loss_lambda=(L[LAMBDA_COL].astype(float) if LAMBDA_COL in L else np.nan)), index=L.index)


def clustering(T: pd.DataFrame) -> dict:
    """Do the extendable AC line builds sit on a common capacity threshold? Repeated new-capacity values among built lines, lines at the S4J
    zero-loss limit (rating = s_max_pu * s_nom_max / 4) and lines at s_nom_max."""
    b = T[T.new_mw > 1.0]
    vc = b.new_mw.round(0).value_counts()
    rep = {str(int(k)): int(v) for k, v in vc[vc >= 2].items()}
    at_kink = b[(b.rating_mw - b.s4j_zero_loss_limit_mw).abs() <= 1e-3 * b.s4j_zero_loss_limit_mw]
    flow_kink = b[(b.max_abs_flow_mw - b.s4j_zero_loss_limit_mw).abs() <= 1e-3 * b.s4j_zero_loss_limit_mw]
    return dict(built=int(len(b)), built_cross_border=int((b.border_class == "cross_border").sum()), repeated_new_capacity_mw=rep,
                rating_at_s4j_zero_loss_limit=sorted(at_kink.index.astype(str)), flow_at_s4j_zero_loss_limit=sorted(flow_kink.index.astype(str)),
                at_s_nom_max=sorted(b.index[b.at_s_nom_max].astype(str)),
                new_capacity_gw=dict(cross_border=round(float(b[b.border_class == "cross_border"].new_mw.sum()) / 1e3, 3), domestic=round(float(b[b.border_class == "domestic"].new_mw.sum()) / 1e3, 3)))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", type=Path, required=True); ap.add_argument("--ref-j", type=Path, required=True); ap.add_argument("--ref-h", type=Path, required=True)
    a = ap.parse_args()
    out = a.run / "analysis"; out.mkdir(parents=True, exist_ok=True)
    ref = a.run / "ref_s4j"; ref.mkdir(exist_ok=True)
    for t in RUNS:
        lnk = ref / t
        if not lnk.exists():
            lnk.symlink_to((a.ref_j / "solves" / t).resolve())
    import s4d_5_summary
    sys.argv = ["s4d_5_summary.py", "--mains", str(a.run / "solves"), "--nze", str(a.run / "solves"), "--s4c", str(ref), "--out", str(out)]
    s4d_5_summary.main()
    gen = json.loads((out / "S4D5_SMOKE_SUMMARY.json").read_text())
    (out / "S4D5_SMOKE_SUMMARY.json").rename(out / "GENERIC_SUMMARY_VS_S4J.json")
    sj = json.loads((a.ref_j / "analysis/S4J6_SMOKE_SUMMARY.json").read_text())
    import pypsa
    from s4c_6_summary import solved_in
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    res = dict(label=gen["label"], reference="S4J-6 smoke (results_project/s4j/s4j6b, code 4937ba13); S4H-3 smoke (results_project/s4h/s4h3, code 1887d975)",
               runs=gen["runs"], gates=gen["gates"], vs_s4j=gen["s4c"], tolerance=tolerance_flags(gen["gates"]), B5=gen.get("B5"), B6=gen.get("B6"),
               B6_s4j=sj.get("B6"), B6_s4h=sj.get("B6_s4h"), co2=gen["co2"], ledgers=gen["ledgers"], disconnected_minus_integrated_bn_eur=gen.get("disconnected_minus_integrated_bn_eur"),
               B16={}, transport={}, transport_totals={}, capacity={}, at_cap={}, focus={}, lp_vs_s4j={}, th_my={}, lines={}, clustering={})
    jref = {r["run"]: r for r in sj["runs"]}
    for r in gen["runs"]:
        h = jref.get(r["run"], {})
        res["lp_vs_s4j"][r["run"]] = {k: dict(s4k=r.get(k), s4j=h.get(k), change_rel=((r.get(k) / h.get(k) - 1) if (h.get(k) and r.get(k) is not None) else None))
                                       for k in ("num_col", "num_row", "nnz", "barrier_iterations", "barrier_seconds", "solve_seconds", "peak_rss_gib_receipt")}
    for t in RUNS:
        g, gj, gh = b16(a.run / "solves" / t), b16(a.ref_j / "solves" / t), b16(a.ref_h / "solves" / t)
        if g:
            res["B16"][t] = dict(passed=g.get("passed"), relative_error=g.get("relative_error"), tolerance=g.get("tolerance"), difference_eur=g.get("difference"),
                                 s4j_relative_error=gj.get("relative_error"), s4h_relative_error=gh.get("relative_error"))
        p, pj, ph = solved_in(a.run / "solves" / t), solved_in(a.ref_j / "solves" / t), solved_in(a.ref_h / "solves" / t)
        if not p:
            continue
        n = pypsa.Network(str(p)); nj = pypsa.Network(str(pj)) if pj else None; nh = pypsa.Network(str(ph)) if ph else None
        tr = transport(n)
        res["transport"][t] = dict(s4k=tr)
        res["transport_totals"][t] = dict(s4k=totals(tr), s4j=totals((sj.get("transport", {}).get(t) or {}).get("s4j")), s4h=totals((sj.get("transport", {}).get(t) or {}).get("s4h")))
        res["capacity"][t] = dict(s4k=caps(n), s4j=(caps(nj) if nj is not None else None), s4h=(caps(nh) if nh is not None else None))
        ck, cj = at_cap(n), (at_cap(nj) if nj is not None else [])
        res["at_cap"][t] = dict(s4k=ck, s4j=cj, added=sorted(set(ck) - set(cj)), removed=sorted(set(cj) - set(ck)))
        T = line_table(n); Tj = line_table(nj) if nj is not None else None; Th = line_table(nh) if nh is not None else None
        W = T.add_suffix("_s4k")
        if Tj is not None:
            W = W.join(Tj[["s_nom_opt", "new_mw", "rating_mw", "max_abs_flow_mw", "loss_twh"]].add_suffix("_s4j"))
        if Th is not None:
            W = W.join(Th[["s_nom_opt", "new_mw"]].add_suffix("_s4h"))
        W.index.name = "line"; W.reset_index().to_csv(out / f"LINE_BUILD_S4K3_{t}.csv", index=False)
        res["lines"][t] = f"LINE_BUILD_S4K3_{t}.csv"
        res["clustering"][t] = dict(s4k=clustering(T), s4j=(clustering(Tj) if Tj is not None else None))
        if "Khlong Ngae – Gurun" in n.links.index:
            res["th_my"][t] = dict(s4k=th_my(n), s4j=(th_my(nj) if nj is not None else None))
    li = (gen["ledgers"].get("integrated") or {}).get("totals_bn_eur", {}); ld = (gen["ledgers"].get("disconnected") or {}).get("totals_bn_eur", {})
    jf = sj.get("focus", {})
    res["focus"] = {c: dict(integrated_bn_eur=li.get(c), disconnected_bn_eur=ld.get(c), disconnected_minus_integrated=round(ld.get(c, 0.0) - li.get(c, 0.0), 4),
                            s4j_integrated_bn_eur=(jf.get(c) or {}).get("integrated_bn_eur"), s4j_disconnected_bn_eur=(jf.get(c) or {}).get("disconnected_bn_eur"),
                            s4j_disconnected_minus_integrated=(jf.get(c) or {}).get("disconnected_minus_integrated"),
                            s4h_integrated_bn_eur=(jf.get(c) or {}).get("s4h_integrated_bn_eur"), s4h_disconnected_bn_eur=(jf.get(c) or {}).get("s4h_disconnected_bn_eur"),
                            s4h_disconnected_minus_integrated=(jf.get(c) or {}).get("s4h_disconnected_minus_integrated")) for c in FOCUS}
    od = next((r for r in gen["runs"] if r["run"] == "disconnected"), {}); of = (gen["s4c"] or {}).get("disconnected", {})
    res["disconnected_objective_vs_s4j"] = dict(s4k=od.get("objective_eur"), s4j=of.get("objective"), relative=of.get("objective_change_rel"))
    (out / "S4K3_SMOKE_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(dict(vs_s4j=res["vs_s4j"], tolerance=res["tolerance"], B16=res["B16"], lp_vs_s4j=res["lp_vs_s4j"], focus=res["focus"],
                          B6=(res["B6"] or {}).get("difference"), B6_s4j=(res["B6_s4j"] or {}).get("difference"), B6_s4h=(res["B6_s4h"] or {}).get("difference"),
                          clustering=res["clustering"], transport_totals=res["transport_totals"]), indent=1, default=str))


if __name__ == "__main__":
    main()
