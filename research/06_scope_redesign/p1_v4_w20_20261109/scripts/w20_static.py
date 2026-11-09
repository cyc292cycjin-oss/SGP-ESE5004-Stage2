"""V4 W20 section 2.4: static checks of the 17 coalition networks (no solver).

    PYTHONHASHSEED=0 python w20_static.py --repo /home/jin/wt_v4_w20 --nets <results_project/v4w20/nets56> --base56 <w14_integrated_56.nc> --out <STATIC_CHECKS_W20.json>

Per network: (1) the V3.1 zero-slack gate (scripts_project/zero_slack_check.check_network: the model is built exactly as the solve builds it - create_model
+ every required hook - on the first 3 snapshots; every research hook row classified; a final-level / annual row with cap <= 1e-9 and only one-way
inflow ports is a forced zero-margin row and fails); (2) every member's net-zero row research_country_co2_limit-<c> exists and its atmosphere has a
removal or two-way port; (3) no NaN in the LP-relevant static attributes and in any time series (pre-existing NaN columns of the base 56-snapshot
network listed apart); (4) CO2 sink channels and liquid-fuel sources per member (structural reading of a possible infeasibility).
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

LP_ATTR = {"Generator": ["p_nom", "p_nom_max", "p_nom_min", "capital_cost", "marginal_cost", "efficiency", "p_min_pu", "p_max_pu", "sign"],
           "Link": ["p_nom", "p_nom_max", "p_nom_min", "capital_cost", "marginal_cost", "efficiency", "efficiency2", "efficiency3", "efficiency4", "p_min_pu", "p_max_pu"],
           "Line": ["s_nom", "s_nom_max", "s_nom_min", "capital_cost", "x", "r", "s_max_pu", "ac_loss_lambda"],
           "Store": ["e_nom", "e_nom_max", "e_nom_min", "e_initial", "capital_cost", "marginal_cost", "e_min_pu", "e_max_pu", "standing_loss"],
           "StorageUnit": ["p_nom", "p_nom_max", "p_nom_min", "capital_cost", "marginal_cost", "efficiency_store", "efficiency_dispatch", "max_hours", "inflow", "p_min_pu", "p_max_pu", "standing_loss"],
           "Load": ["p_set"]}


def nan_report(n) -> dict:
    out = {}
    for c, cols in LP_ATTR.items():
        df = n.df(c)
        for col in cols:
            if col in df and len(df):
                k = int(pd.to_numeric(df[col], errors="coerce").isna().sum())
                if k:
                    out[f"{c}.{col}"] = k
        for attr, fr in n.pnl(c).items():
            if len(fr.columns):
                k = int(np.isnan(fr.to_numpy(dtype=float)).sum())
                if k:
                    out[f"{c}_t.{attr}"] = k
    return out


def sinks(n, members) -> dict:
    """per member: CO2 outlets (own capped store, own extra-ASEAN store, links into other members' stores) and liquid-fuel sources."""
    caps = (n.meta.get("research_co2_storage") or {}).get("caps_t_per_year", {})
    L = n.links; bc = n.buses.country.astype(str)
    out = {}
    for c in members:
        own = f"co2 sequestered {c}"; ex = f"co2 sequestered extra-ASEAN {c}"
        into_ex = int((L.bus1 == ex).sum()) if ex in n.buses.index else 0
        frm = L[(L.bus0.map(bc) == c) & L.bus1.isin(n.stores.index[n.stores.carrier == "co2 sequestered"])]
        other = sorted({str(bc[b]) for b in frm.bus1 if str(bc[b]) != c})
        liq = {}
        for car in ("oil", "oil non-fossil", "methanol", "ammonia"):
            b = f"{c} {car}"
            if b in n.buses.index:
                gens = int((n.generators.bus == b).sum()); inc = L[L.bus1 == b]
                liq[car] = dict(generators=gens, inflow_links=int(len(inc)), from_other_members=sorted({str(bc[x]) for x in inc.bus0 if str(bc[x]) != c}))
        out[c] = dict(own_store=bool(own in n.stores.index), own_cap_t_per_year=float(caps.get(c, 0.0)), extra_asean_store=bool(ex in n.stores.index), links_into_extra_asean=into_ex,
                      links_into_other_member_stores=int(len(frm[frm.bus1.map(bc) != c])), other_member_stores=other, liquids=liq)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--nets", type=Path, required=True)
    ap.add_argument("--base56", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    logging.disable(logging.WARNING)
    import pypsa
    from v4_coalition import COALITION_ORDER, coalitions, sha
    from zero_slack_check import check_network
    base = pypsa.Network(str(a.base56)); nan0 = nan_report(base); del base
    res = dict(script="work/p1_v4_w20_20261109/scripts/w20_static.py", solver_called=False, base56=str(a.base56), base56_nan=nan0, networks={})
    for name in COALITION_ORDER:
        t0 = time.time(); p = a.nets / f"{name}_56_unsolved.nc"; S = list(coalitions()[name])
        zs = check_network(a.repo, name, "integrated", p, 3)
        rows = {r["name"]: r for r in zs["constraints"]}
        nz = {}
        for c in S:
            r = rows.get(f"research_country_co2_limit-{c}")
            nz[c] = dict(row=bool(r), verdict=(r or {}).get("verdict"), removal_or_two_way_ports=(r or {}).get("removal_or_two_way_ports"),
                         removal_examples=(r or {}).get("removal_examples", [])[:3], cap=(r or {}).get("cap_max"))
        extra = sorted(k for k in rows if k.startswith("research_country_co2_limit-") and k.split("-", 1)[1] not in S)
        cap_rows = sorted(k.split("-", 1)[1] for k in rows if k.startswith("research_co2_storage_cap-"))
        n = pypsa.Network(str(p)); nanr = nan_report(n)
        new_nan = {k: v for k, v in nanr.items() if k not in nan0}
        rec = json.loads((a.nets / f"{name}_56_COALITION_RECEIPT.json").read_text())
        res["networks"][name] = dict(members=S, network_sha256=sha(p), bytes=p.stat().st_size, snapshots=int(len(n.snapshots)),
                                     weights_8760_over_56=bool(np.allclose(n.snapshot_weightings.to_numpy(), 8760.0 / 56, rtol=0, atol=1e-12)),
                                     zero_slack=dict(passed=zs["passed"], forcing_rows=zs["zero_slack_forcing_rows"], verdicts=zs["verdicts"], forms=zs["forms"],
                                                     bunker=zs["bunker"], configured_caps_without_row=zs["configured_caps_without_row"], hooks=zs["required_constraint_hooks"], seconds=zs["seconds"]),
                                     net_zero_rows=nz, net_zero_rows_of_non_members=extra, storage_cap_rows=cap_rows,
                                     net_zero_all_members_with_removal_port=bool(all(v["row"] and v["verdict"] == "removal_ports_present" for v in nz.values()) and not extra),
                                     nan=nanr, nan_new_vs_base=new_nan, sinks=sinks(n, S),
                                     ledger=dict(removed_total=rec["ledger"]["removed_total"], boundary=sum(rec["ledger"]["boundary_by_carrier"].values()),
                                                 retained_cross_border=len(rec["ledger"]["retained_cross_border"]), retained_stock=len(rec["ledger"]["retained_cross_border_stock"]),
                                                 dangling=len(rec["ledger"]["dangling_buses_removed"]), carriers_removed=rec["ledger"]["carriers_removed"],
                                                 dead_end_kept=len(rec["ledger"]["dead_end_member_components_kept"]), dead_end_fixed_cost_constant_eur=rec["ledger"]["dead_end_fixed_cost_constant_eur"],
                                                 transit_via_non_member=len(rec["ledger"]["transit_via_non_member"]), d8_addback_eur=rec["ledger"]["d8_addback_eur"]),
                                     passed=bool(zs["passed"] and not new_nan and all(v["row"] and v["verdict"] == "removal_ports_present" for v in nz.values()) and not extra),
                                     seconds=round(time.time() - t0, 1))
        del n
        r = res["networks"][name]
        print(f"{name}: passed={r['passed']} zero_slack={zs['passed']} forcing={zs['zero_slack_forcing_rows']} net_zero_ok={r['net_zero_all_members_with_removal_port']} "
              f"new_nan={new_nan} verdicts={zs['verdicts']} ({r['seconds']} s)", flush=True)
    res["passed"] = bool(all(v["passed"] for v in res["networks"].values()))
    a.out.write_text(json.dumps(res, indent=1, default=str) + "\n")
    print("W20_STATIC:" + ("PASS" if res["passed"] else "FAIL"))
    return 0 if res["passed"] else 3


if __name__ == "__main__":
    sys.exit(main())
