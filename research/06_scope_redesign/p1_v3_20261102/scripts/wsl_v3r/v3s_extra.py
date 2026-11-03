"""V3 screening rerun (supplement 07): the quantities the registered predictions (RUN_PLAN_V3.md sections 11, 17.4, 19.5, 21.5) need beyond the batch tables, from the solved
networks of the recovered full pack. Read-only, no solver. Per run: plant-line flow by link and by month (use of the contract capacity), LA net export by kind,
SG marine methanol by origin (scripts_project/v3_smoke_eval.py liquid_balance / sg_marine), annual mean liquid duals per country (same as v3_smoke_eval main).
    PYTHONHASHSEED=0 python v3s_extra.py <repo> <full_unpacked/export dir> <out dir> [runs, default V1,V2]"""
import json
import sys
from pathlib import Path

import pandas as pd
import pypsa

repo, ex, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
runs = (sys.argv[4] if len(sys.argv) > 4 else "V1,V2").split(",")
sys.path.insert(0, str(repo / "scripts_project"))
import v3_smoke_eval as ev  # noqa: E402

res, monthly = {}, []
for rid in runs:
    nc = sorted((ex / rid).glob("*_solved.nc"))
    if not nc:
        res[rid] = None; continue
    n = pypsa.Network(str(nc[0])); w = n.snapshot_weightings.generators; c = n.buses.country.astype(str)
    r = dict(solved_network=nc[0].name, snapshots=int(len(n.snapshots)), hours=float(w.sum()), weight_objective_first=float(n.snapshot_weightings.objective.iloc[0]))
    P = n.links[n.links.carrier.astype(str) == "dedicated plant line"]
    if len(P):
        p0 = n.links_t.p0[P.index]; cap = P.p_nom_opt
        r["plant_lines"] = {k: dict(origin=str(P.at[k, "bus0"]), destination=str(P.at[k, "bus1"]), p_nom_mw=float(cap[k]), flow_twh=float(p0[k].mul(w).sum()) / 1e6,
                                    mean_use=float(p0[k].mul(w).sum() / w.sum() / cap[k]) if cap[k] else None, min_p0_mw=float(p0[k].min())) for k in P.index}
        tot = p0.sum(axis=1); m = pd.Series(n.snapshots, index=n.snapshots).dt.month if not isinstance(n.snapshots, pd.MultiIndex) else None
        r["plant_total"] = dict(p_nom_mw=float(cap.sum()), flow_twh=float(tot.mul(w).sum()) / 1e6, mean_use=float(tot.mul(w).sum() / w.sum() / cap.sum()))
        if m is not None:
            g = pd.DataFrame(dict(e=tot.mul(w), h=w, m=m.values)).groupby("m").sum()
            for mon, row in g.iterrows():
                monthly.append(dict(run=rid, month=int(mon), flow_twh=float(row.e) / 1e6, mean_mw=float(row.e / row.h), use_of_contract=float(row.e / row.h / cap.sum())))
    # LA net export: AC lines and electricity links across the LA border, signed from LA
    la = lambda b: c[b] == "LA"
    L = n.lines[(n.lines.border_class == "cross_border")]; L = L[[la(a) != la(b) for a, b in zip(L.bus0, L.bus1)]]
    ac = sum((n.lines_t.p0[k] if la(L.at[k, "bus0"]) else -n.lines_t.p0[k] for k in L.index), start=pd.Series(0.0, index=n.snapshots))
    K = n.links[(n.links.border_class == "cross_border") & (n.links.transport_carrier.astype(str) == "electricity")]; K = K[[la(a) != la(b) for a, b in zip(K.bus0, K.bus1)]]
    lk = sum((n.links_t.p0[k] if la(K.at[k, "bus0"]) else -n.links_t.p0[k] for k in K.index), start=pd.Series(0.0, index=n.snapshots))
    r["la_net_export_twh"] = dict(apg_ac=float(ac.mul(w).sum()) / 1e6, electricity_links=float(lk.mul(w).sum()) / 1e6, total=float((ac + lk).mul(w).sum()) / 1e6,
                                  links_counted=int(len(K)), lines_counted=int(len(L)))
    bal = ev.liquid_balance(n, rid); r["sg_marine"] = ev.sg_marine(n, bal)
    mp = n.buses_t.marginal_price
    r["liquid_dual_annual_mean_eur_per_mwh"] = {k: {cc: float(mp[f"{cc} {k}"].mean()) for cc in ev.COUNTRIES if f"{cc} {k}" in mp} for k in ev.LOAD_CARRIERS}
    res[rid] = r; print(rid, json.dumps({k: v for k, v in r.items() if k != "plant_lines"}, default=str)[:1500], flush=True)
(out / "V3_SCREEN_EXTRA.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
if monthly:
    pd.DataFrame(monthly).to_csv(out / "V3_SCREEN_PLANT_LINE_MONTHLY.csv", index=False)
    print(pd.DataFrame(monthly).pivot(index="month", columns="run", values="use_of_contract").round(3).to_string())
