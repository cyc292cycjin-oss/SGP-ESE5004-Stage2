"""S4J-6 detail (S4J supplement 01 (b)): the TH-MY corridor build and flows (AC lines and the Khlong Ngae - Gurun DC, both directions), the TH and MY
ledgers by subject against S4H-3, and where the AC loss approximation leaves line flows (read-only, no model change).

AC loss approximation (PyPSA define_loss_constraints, tangents N): tangent k at p_k = k / N * s_max_pu * s_nom_max; tangent 1 is zero for
|s| <= p_1 / 2 = s_max_pu * s_nom_max / (2 N), so the approximated loss is zero up to that flow ("zero-loss limit") and rises with slope
2 * r_pu_eff * p_1 above it. The line flow is s = (p0 - p1) / 2 (half of the loss is added to p0 and p1 after the solve).

    python scripts_project/s4j_6_detail.py --run results_project/s4j/s4j6b --ref results_project/s4h/s4h3
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

RUNS = ("integrated", "disconnected", "integrated_nze")
PAIR = ("MY", "TH")
REL = 1e-3


def country(n, b):
    return str(n.buses.at[b, "country"])


def th_my(n) -> list:
    """Every TH-MY electricity component: capacity and energy in both directions (TWh), losses (TWh)."""
    w = n.snapshot_weightings.objective; rows = []
    for k, z in n.lines.iterrows():
        c0, c1 = country(n, z.bus0), country(n, z.bus1)
        if tuple(sorted((c0, c1))) != PAIR or k not in n.lines_t.p0:
            continue
        p0, p1 = n.lines_t.p0[k], n.lines_t.p1[k]; s = (p0 - p1) / 2
        e01 = float(s.clip(lower=0).mul(w).sum()) / 1e6; e10 = float((-s).clip(lower=0).mul(w).sum()) / 1e6
        rows.append(dict(component=f"Line:{k}", carrier="AC", bus0=z.bus0, bus1=z.bus1, capacity_initial_mw=float(z.s_nom), capacity_opt_mw=float(z.s_nom_opt),
                         capacity_max_mw=float(z.s_nom_max) if z.s_nom_extendable else float(z.s_nom), s_max_pu=float(z.s_max_pu),
                         th_to_my_twh=(e01 if c0 == "TH" else e10), my_to_th_twh=(e10 if c0 == "TH" else e01),
                         loss_twh=float((p0 + p1).mul(w).sum()) / 1e6, max_abs_flow_mw=float(s.abs().max())))
    L = n.links[(n.links.carrier == "DC")]
    for k, z in L.iterrows():
        c0, c1 = country(n, z.bus0), country(n, z.bus1)
        if tuple(sorted((c0, c1))) != PAIR or k not in n.links_t.p0:
            continue
        p0, p1 = n.links_t.p0[k], n.links_t.p1[k]
        e = float(p0.clip(lower=0).mul(w).sum()) / 1e6; eb = float((-p0).clip(lower=0).mul(w).sum()) / 1e6
        rows.append(dict(component=f"Link:{k}", carrier="DC", bus0=z.bus0, bus1=z.bus1, capacity_initial_mw=float(z.p_nom), capacity_opt_mw=float(z.p_nom_opt),
                         capacity_max_mw=float(z.p_nom_max) if z.p_nom_extendable else float(z.p_nom), p_min_pu=float(z.p_min_pu), efficiency=float(z.efficiency),
                         th_to_my_twh=(e if c0 == "TH" else eb), my_to_th_twh=(eb if c0 == "TH" else e),
                         loss_twh=float((p0 + p1).mul(w).sum()) / 1e6, max_abs_flow_mw=float(p0.abs().max())))
    for c in ("convert_412_577", "convert_599_890"):   # the two converter B2B (domestic) at the DC ends
        if c in n.links.index:
            z = n.links.loc[c]; p0 = n.links_t.p0[c] if c in n.links_t.p0 else pd.Series(0.0, index=n.snapshots)
            rows.append(dict(component=f"Link:{c}", carrier=str(z.carrier), bus0=z.bus0, bus1=z.bus1, capacity_initial_mw=float(z.p_nom), capacity_opt_mw=float(z.p_nom_opt),
                             capacity_max_mw=float(z.p_nom_max) if z.p_nom_extendable else float(z.p_nom), p_min_pu=float(z.p_min_pu), efficiency=float(z.efficiency),
                             forward_twh=float(p0.clip(lower=0).mul(w).sum()) / 1e6, backward_twh=float((-p0).clip(lower=0).mul(w).sum()) / 1e6,
                             max_abs_flow_mw=float(p0.abs().max())))
    return rows


def loss_kink(n, tangents: int) -> dict:
    """Extendable AC lines against the zero-loss limit s_max_pu * s_nom_max / (2 N)."""
    if not tangents:
        return {}
    n.calculate_dependent_values()
    X = n.lines[n.lines.s_nom_extendable].copy()
    s = (n.lines_t.p0[X.index] - n.lines_t.p1[X.index]) / 2
    smax = n.get_switchable_as_dense("Line", "s_max_pu")[X.index]
    p1 = smax.mul(X.s_nom_max, axis=1) / tangents            # first tangent point
    z = (p1 / 2).max()                                       # zero-loss limit (static s_max_pu in this model)
    X["zero_loss_limit_mw"] = z
    X["max_abs_flow_mw"] = s.abs().max()
    X["rating_mw"] = smax.max() * X.s_nom_opt
    X["slope_above_limit"] = 2 * X.r_pu_eff * (p1.max())       # marginal loss per MW above the limit
    X["flow_at_limit"] = (X.max_abs_flow_mw - X.zero_loss_limit_mw).abs() <= REL * X.zero_loss_limit_mw
    X["rating_at_limit"] = (X.rating_mw - X.zero_loss_limit_mw).abs() <= REL * X.zero_loss_limit_mw
    X["above_limit"] = X.max_abs_flow_mw > X.zero_loss_limit_mw * (1 + REL)
    X["built"] = X.s_nom_opt > X.s_nom + 1.0
    out = {}
    for cls, g in X.groupby(X.border_class.astype(str)):
        out[cls] = dict(lines=int(len(g)), built=int(g.built.sum()), flow_at_limit=int(g.flow_at_limit.sum()), rating_at_limit=int(g.rating_at_limit.sum()),
                        above_limit=int(g.above_limit.sum()), built_and_rating_at_limit=int((g.built & g.rating_at_limit).sum()),
                        new_capacity_gw=round(float((g.s_nom_opt - g.s_nom).sum()) / 1e3, 3),
                        new_capacity_rating_at_limit_gw=round(float((g.s_nom_opt - g.s_nom)[g.rating_at_limit].sum()) / 1e3, 3),
                        slope_above_limit_median=float(g.slope_above_limit.median()), slope_above_limit_max=float(g.slope_above_limit.max()))
    cb = X[(X.border_class == "cross_border")]
    out["cross_border_lines"] = [dict(line=str(k), bus0=r.bus0, bus1=r.bus1, s_nom=float(r.s_nom), s_nom_opt=round(float(r.s_nom_opt), 1), s_nom_max=float(r.s_nom_max),
                                      zero_loss_limit_mw=round(float(r.zero_loss_limit_mw), 1), max_abs_flow_mw=round(float(r.max_abs_flow_mw), 1),
                                      flow_at_limit=bool(r.flow_at_limit), rating_at_limit=bool(r.rating_at_limit), slope_above_limit=round(float(r.slope_above_limit), 4))
                                 for k, r in cb.sort_values("s_nom_opt", ascending=False).iterrows()]
    return out


def ledger(path: Path) -> pd.DataFrame:
    return pd.read_csv(path / "COUNTRY_COST_LEDGER.csv", index_col=0) / 1e9


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", type=Path, required=True); ap.add_argument("--ref", type=Path, required=True); a = ap.parse_args()
    import pypsa
    from s4c_6_summary import solved_in
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    res = dict(label="SMOKE_TEST_ONLY (56 snapshots; scale not to be judged, decision 47)", th_my={}, loss_kink={}, ledger_th_my={})
    for t in RUNS:
        p, q = solved_in(a.run / "solves" / t), solved_in(a.ref / "solves" / t)
        n = pypsa.Network(str(p)); f = pypsa.Network(str(q))
        res["th_my"][t] = dict(s4j=th_my(n), s4h=th_my(f))
        tl = int(json.loads((a.run / "solves" / t / "SOLVE_RECEIPT.json").read_text()).get("transmission_losses", {}).get("ac_tangents", 0))
        res["loss_kink"][t] = dict(ac_tangents=tl, s4j=loss_kink(n, tl))
    for t in ("integrated", "disconnected"):
        J, H = ledger(a.run / "solves" / t), ledger(a.ref / "solves" / t)
        cols = sorted(set(J.columns) | set(H.columns))
        res["ledger_th_my"][t] = {c: {k: dict(s4j=round(float(J.at[c, k]) if k in J else 0.0, 4), s4h=round(float(H.at[c, k]) if k in H else 0.0, 4),
                                             change=round((float(J.at[c, k]) if k in J else 0.0) - (float(H.at[c, k]) if k in H else 0.0), 4)) for k in cols}
                                  for c in ("TH", "MY")}
    out = a.run / "analysis" / "S4J6_DETAIL.json"
    out.write_text(json.dumps(res, indent=1, default=str))
    print(out)


if __name__ == "__main__":
    main()
