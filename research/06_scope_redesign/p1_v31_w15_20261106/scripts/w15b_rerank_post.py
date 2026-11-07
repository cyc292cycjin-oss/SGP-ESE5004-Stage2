"""V31 W15 stage B, section 7.2-7.4: post-processing of the W10 rerank run on the v3.1 2920x3h results (read only; no solver).

  python -I w15b_rerank_post.py --rerank <rerank output dir> --cache <extract cache> --summary <RERANK_SUMMARY.json> --b6 <B6_CHECK.json>
         --registry <DATA_REGISTRY.csv> --out <work/p1_v31_w15_20261106>

Writes RERANK_TOP30_V31.csv, RERANK_OWEN_TOP10_V31.csv, RERANK_FOCUS.csv, PHYSICS_CAPPED.csv, FIRST_ORDER_EV_CHECK.json,
evidence/RERANK_COMPARISON.json.
"""
import argparse, json
from pathlib import Path

import pandas as pd

# 7.3 stoichiometric limits, CO2 + 3 H2 -> CH3OH + H2O, with the model's own heating values (registry / PyPSA-Eur config)
M_CO2, M_H2, M_MEOH = 44.009, 2.01588, 32.042        # g/mol
LHV_MEOH = 5.528                                      # MWh/t, registry liquid_ship_mwh_per_t_methanol (PyPSA-Eur MWh_MeOH per t)
LHV_H2 = 33.33                                        # MWh/t, technology-data / PyPSA-Eur hydrogen LHV
STOICH = {"share_MWh_MeOH_per_tCO2": M_MEOH / M_CO2 * LHV_MEOH,
          "share_MWh_MeOH_per_MWh_H2": M_MEOH / (3 * M_H2) * LHV_MEOH / LHV_H2}
CAP_ONE = ("share_bev_charge_efficiency", "share_bev_avail_max")
FOCUS = {"电池": r"battery", "抽蓄": r"PHS", "EV 需求响应 / 充电": r"bev|ev_|EV", "屋顶光伏": r"rooftop"}


def main():
    ap = argparse.ArgumentParser()
    for k in ("rerank", "cache", "summary", "b6", "registry", "out"):
        ap.add_argument("--" + k, required=True)
    a = ap.parse_args()
    R, OUT = Path(a.rerank), Path(a.out)
    wide = pd.read_csv(R / "IMPACT_FIRST_ORDER.csv", keep_default_na=False, low_memory=False)
    for c in ("abs_dB6", "dB6", "dZ_F1", "dZ_F2", "rank", "rank_s07", "rank_v31ev05", "dB6_s07", "dB6_v31ev05", "owen_max_eur", "dB6_low", "dB6_high",
              "dZ_F1_low", "dZ_F2_low", "dZ_F1_high", "dZ_F2_high", "value", "notch_low", "notch_high"):
        if c in wide:
            wide[c] = pd.to_numeric(wide[c], errors="coerce")
    wide["ranked"] = wide["ranked"].astype(str).isin(("True", "true", "1"))
    summ = json.loads(Path(a.summary).read_text())
    rk = wide[wide.ranked].copy()
    top = rk.sort_values("rank").head(30)
    cols = ["rank", "param_id", "family_201", "country", "status", "mechanism", "direction_max", "dB6", "dZ_F1", "dZ_F2", "owen_max_country", "owen_max_eur",
            "rank_s07", "dB6_s07", "rank_v31ev05", "dB6_v31ev05", "flags"]
    top[[c for c in cols if c in top]].to_csv(OUT / "RERANK_TOP30_V31.csv", index=False, lineterminator="\n")
    ow = rk.assign(abs_owen=rk.owen_max_eur.abs()).sort_values("abs_owen", ascending=False).head(10)
    ow[[c for c in cols if c in ow] + ["owen_by_country"]].to_csv(OUT / "RERANK_OWEN_TOP10_V31.csv", index=False, lineterminator="\n")
    # rank comparison vs s07
    def cmp(other):
        r0 = rk.set_index("param_id")["rank"]; r1 = rk.set_index("param_id")[f"rank_{other}"]
        t0, t1 = set(r0[r0 <= 30].index), set(r1[r1 <= 30].index)
        return dict(spearman=float(r0.corr(r1, method="spearman")), top30_overlap=len(t0 & t1), entered_v31_top30=sorted(t0 - t1), left_v31_top30=sorted(t1 - t0))
    comp = dict(reference="v31", stability=summ.get("stability"), b6_base=summ.get("b6_base"), vs_s07=cmp("s07"), vs_v31ev05=cmp("v31ev05"))
    # focus items
    fr = []
    for lab, rx in FOCUS.items():
        sub = wide[wide.param_id.str.contains(rx, case=False, regex=True)]
        for r in sub.itertuples():
            fr.append(dict(focus=lab, param_id=r.param_id, ranked=r.ranked, mechanism=r.mechanism, status=r.status, rank_v31=r.rank, dB6_v31=r.dB6, dZ_F1_v31=r.dZ_F1,
                           rank_s07=getattr(r, "rank_s07", None), dB6_s07=getattr(r, "dB6_s07", None), flags=str(r.flags)[:200]))
    pd.DataFrame(fr).to_csv(OUT / "RERANK_FOCUS.csv", index=False, lineterminator="\n")
    # 7.3 physics-capped column
    pc = []
    for pid in list(CAP_ONE) + list(STOICH):
        r = wide[wide.param_id == pid]
        if not len(r):
            continue
        r = r.iloc[0]; v, hi = float(r.value) if str(r.value) not in ("", "nan") else None, r.notch_high
        cap = 1.0 if pid in CAP_ONE else STOICH[pid]
        f = (cap - v) / (hi - v) if v is not None and hi == hi and hi != v else 0.0
        z1h, z2h = r.dZ_F1_high * f, r.dZ_F2_high * f
        capped_db6_high = z2h - z1h
        best = max([("low", r.dB6_low), ("high_capped", capped_db6_high)], key=lambda t: abs(t[1]) if t[1] == t[1] else -1)
        pc.append(dict(param_id=pid, value=v, notch_high_registered=hi, cap=cap, cap_basis=("1 (efficiency / share cannot exceed 1)" if pid in CAP_ONE else
                       "stoichiometric limit CO2 + 3 H2 -> CH3OH + H2O with LHV MeOH 5.528 MWh/t, H2 33.33 MWh/t"), main_minus_cap=(v - cap) if v is not None else None,
                       scale_of_high_notch=f, dZ_F1_high_registered=r.dZ_F1_high, dZ_F2_high_registered=r.dZ_F2_high, dB6_high_registered=r.dB6_high,
                       dZ_F1_high_capped=z1h, dZ_F2_high_capped=z2h, dB6_high_capped=capped_db6_high, dB6_low=r.dB6_low,
                       abs_dB6_registered=r.abs_dB6, abs_dB6_capped=abs(best[1]), direction_capped=best[0], rank_registered=r["rank"], mechanism=r.mechanism))
    pcd = pd.DataFrame(pc)
    if len(pcd):
        # new rank of the capped rows among the ranked universe (other rows unchanged)
        base = rk.set_index("param_id").abs_dB6.copy()
        for x in pcd.itertuples():
            if x.param_id in base.index:
                base[x.param_id] = x.abs_dB6_capped
        newrank = base.rank(ascending=False, method="first")
        pcd["rank_capped"] = pcd.param_id.map(newrank)
    pcd.to_csv(OUT / "PHYSICS_CAPPED.csv", index=False, lineterminator="\n")
    # 7.4 first-order check: EV fleet proxy x0.5 from the duals of v31 (F1, F2), bracketed by the duals of v31ev05 (F3, F4)
    meta = {}
    for d in Path(a.cache).iterdir():
        if (d / "meta.json").exists():
            m = json.loads((d / "meta.json").read_text())
            meta[m["run"].get("rid")] = d
    def grad(d):   # dZ/d(scale) at the extract: sum over EV stores d_enom * e_nom - sum over BEV chargers capacity value * p_nom
        s = pd.read_csv(d / "stores.csv", index_col=0); k = pd.read_csv(d / "links.csv", index_col=0, low_memory=False)
        st = s[s.carrier == "EV battery"]; ch = k[k.carrier == "BEV charger"]
        return float((st.d_enom_fixed * st.e_nom).sum()), float((ch.avail_value_per_mw * ch.p_nom).sum()), len(st), len(ch)
    B6 = json.loads(Path(a.b6).read_text())
    Z = {"F1": B6["A"]["Z_integrated"], "F2": B6["A"]["Z_no_new_xb"], "F3": B6["B"]["Z_integrated"], "F4": B6["B"]["Z_no_new_xb"]}
    ev = dict(method=("dZ = rel x (sum EV-store d_enom_fixed x e_nom - sum BEV-charger capacity value x p_nom), W10 mechanism 'ev_fleet'; "
                      "rel = -0.5 from F1/F2 (full fleet -> x0.5), +1.0 from F3/F4 (x0.5 -> full); the fleet enters as a right-hand side, Z is convex in it, "
                      "so each one-sided first-order estimate is a lower bound of the true change (decision 212 (b)) and the two give a bracket"), runs={})
    for full, half in (("F1", "F3"), ("F2", "F4")):
        gs, gc, ns, nc = grad(meta[full]); hs, hc, _, _ = grad(meta[half])
        pred_from_full = -0.5 * (gs - gc)                 # lower bound of Z(half) - Z(full)
        pred_from_half_rev = +1.0 * (hs - hc)             # lower bound of Z(full) - Z(half)  -> Z(half) - Z(full) <= -this
        actual = Z[half] - Z[full]
        ev["runs"][f"{half}-{full}"] = dict(actual=actual, first_order_from_full=pred_from_full, upper_from_half=-pred_from_half_rev,
                                             rel_error_first_order=(pred_from_full - actual) / actual, lower_bound_holds=pred_from_full <= actual + 1e-6 * abs(actual),
                                             bracket_holds=pred_from_full <= actual <= -pred_from_half_rev + 1e-6 * abs(actual),
                                             components=dict(full_store_term=gs, full_charger_term=gc, half_store_term=hs, half_charger_term=hc, ev_stores=ns, chargers=nc))
    a_db6 = (Z["F4"] - Z["F3"]) - (Z["F2"] - Z["F1"])
    p_db6 = ev["runs"]["F4-F2"]["first_order_from_full"] - ev["runs"]["F3-F1"]["first_order_from_full"]
    ev["dB6"] = dict(actual=a_db6, first_order=p_db6, rel_error=(p_db6 - a_db6) / a_db6 if a_db6 else None, sign_same=(p_db6 > 0) == (a_db6 > 0),
                     note="dB6 is a difference of two lower bounds: no bound guarantee")
    (OUT / "FIRST_ORDER_EV_CHECK.json").write_text(json.dumps(ev, indent=1) + "\n", encoding="utf-8", newline="\n")
    (OUT / "evidence").mkdir(exist_ok=True)
    (OUT / "evidence" / "RERANK_COMPARISON.json").write_text(json.dumps(dict(comp, stoich=STOICH, stoich_inputs=dict(M_CO2=M_CO2, M_H2=M_H2, M_MeOH=M_MEOH, LHV_MeOH=LHV_MEOH, LHV_H2=LHV_H2)),
                                                                         indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(dict(vs_s07={k: v for k, v in comp["vs_s07"].items()}, vs_v31ev05={k: comp["vs_v31ev05"][k] for k in ("spearman", "top30_overlap")}), ensure_ascii=False)[:1500])
    print(top[["rank", "param_id", "dB6", "rank_s07"]].head(30).to_string())
    print(pcd.to_string() if len(pcd) else "no capped rows")
    print(json.dumps(ev, indent=1)[:2500])


if __name__ == "__main__":
    main()
