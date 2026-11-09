"""V4 W20b section 2.4: static checks of the 18 networks (R0 + 17 merged-game coalitions with include_bunker="ports"), the same checks as W20
(work/p1_v4_w20_20261109/scripts/w20_static.py) plus the bunker part. No solver.

    PYTHONHASHSEED=0 python w20b_static.py --repo /home/jin/wt_v4_w20b --nets <results_project/v4w20b/nets56> --base56 <w14_integrated_56.nc> --out <STATIC_CHECKS_W20B.json>

Per network: (1) the V3.1 zero-slack gate (zero_slack_check.check_network: model built as the solve builds it - create_model + every required hook - on
the first 3 snapshots; a final-level / annual row with cap <= 1e-9 and only one-way inflow ports is a forced zero-margin row and fails; the bunker
hook must be the per-variable form covering every metering link x snapshot); (2) every member's net-zero row exists and its atmosphere has a removal
or two-way port, no row of a non-member; (3) no NaN beyond the base 56-snapshot network; (4) CO2 sinks and liquid-fuel sources per member (as W20);
(5) bunker part: R0 has no bunker component and no bunker hook; every ports network keeps the hook, the account and exactly the metering links of the
receipt, every kept bunker terminal with a load has a supply link from a member national liquid bus, and every member with bunker loads has a
source (generator or inflow link) on the national liquid bus feeding them; the hook set equals the base set (ports) / the base set without the bunker hook (R0).
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--nets", type=Path, required=True)
    ap.add_argument("--base56", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--w20-static", type=Path, default=None, help="folder of w20_static.py (default: <repo>/research/06_scope_redesign/p1_v4_w20_20261109/scripts)")
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project")); sys.path.insert(0, str(a.w20_static or a.repo / "research/06_scope_redesign/p1_v4_w20_20261109/scripts"))
    logging.disable(logging.WARNING)
    import pypsa
    from v4_coalition import BUNKER_HOOK, BUNKER_STORE, port_columns, sha, w20b_runs
    from w20_static import nan_report, sinks   # the W20 checks, unchanged
    from zero_slack_check import check_network
    base = pypsa.Network(str(a.base56)); nan0 = nan_report(base); hooks0 = sorted(base.meta.get("required_constraint_hooks", [])); del base
    res = dict(script="work/p1_v4_w20b_20261109/scripts/w20b_static.py", solver_called=False, base56=str(a.base56), base56_nan=nan0, base_hooks=hooks0, networks={})
    for name, spec in w20b_runs().items():
        t0 = time.time(); net = spec["net"]; p = a.nets / f"{net}_56_unsolved.nc"; S = list(spec["members"]); ports = spec["include_bunker"] == "ports"
        zs = check_network(a.repo, net, "integrated", p, 3)
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
        rec = json.loads((a.nets / f"{net}_56_COALITION_RECEIPT.json").read_text()); L = rec["ledger"]
        hooks = sorted(n.meta.get("required_constraint_hooks", []))
        bc = n.buses.country.astype(str); loc = n.buses.location.astype(str)
        asean = set(n.buses.index[bc == "ASEAN"]); term = sorted(asean - {BUNKER_STORE})
        P = port_columns(n.links)
        bk = dict(hooks_expected=(hooks == hooks0) if ports else (hooks == sorted(h for h in hooks0 if h != BUNKER_HOOK)))
        if not ports:
            bk.update(asean_buses=len(asean), bunker_hook=BUNKER_HOOK in hooks, zero_slack_bunker_present=zs["bunker"].get("present"),
                      passed=bool(not asean and BUNKER_HOOK not in hooks and not zs["bunker"].get("present") and bk["hooks_expected"]))
        else:
            meters = sorted(n.links.index[n.links[P].astype(str).eq(BUNKER_STORE).any(axis=1)])
            ld = n.loads[n.loads.bus.astype(str).isin(term)]
            # supply of every kept terminal with a load: a link from a member bus that is NOT a metering link into the account (the fossil meters
            # are fixed to 0 by the per-meter net-zero rows), i.e. the non-fossil kerosene meter or the methanol link
            no_supply, supply_from = [], set()
            for b in sorted(set(ld.bus.astype(str))):
                inc = n.links[(n.links.bus1.astype(str) == b) & ~n.links.index.isin(meters)]
                ok = inc[inc.bus0.map(bc).isin(S) & (inc.p_nom_extendable.astype(bool) | (inc.p_nom > 0))]
                if not len(ok):
                    no_supply.append(b)
                supply_from |= {str(x) for x in ok.bus0}
            src = {}
            for lb in sorted(supply_from):   # a source on the feeding bus: generator, store, inflow link, or a two-way link with bus0 there (node <-> national pool)
                gens = int((n.generators.bus == lb).sum()); sto = int((n.stores.bus == lb).sum()); inl = int((n.links.bus1.astype(str) == lb).sum())
                two = int(((n.links.bus0.astype(str) == lb) & (n.links.p_min_pu < 0)).sum())
                src[lb] = dict(country=str(bc[lb]), generators=gens, stores=sto, inflow_links=inl, two_way_links=two, has_source=bool(gens + sto + inl + two > 0))
            zb = zs["bunker"]
            bk.update(account=bool(BUNKER_STORE in n.stores.index), bunker_hook=BUNKER_HOOK in hooks, metering_links=len(meters),
                      metering_links_receipt=L["bunker"]["metering_links_kept"], loads=int(len(ld)), loads_receipt=L["bunker"]["loads_kept"],
                      load_node_countries=sorted({str(bc[loc[b]]) for b in ld.bus.astype(str)}), terminals_without_member_supply=no_supply,
                      liquid_sources=src, zero_slack_bunker=dict(present=zb.get("present"), passed=zb.get("passed"), metering_links=zb.get("metering_links"),
                                                                 rows=zb.get("rows"), expected_rows=zb.get("expected_rows"), covers_every_metering_flow=zb.get("covers_every_metering_flow"),
                                                                 premises_passed=(zb.get("premises_full_network") or {}).get("passed")),
                      energy_twh_by_country={k: v / 1e6 for k, v in L["bunker"]["energy_mwh_kept_by_country"].items()})
            bk["passed"] = bool(bk["account"] and bk["bunker_hook"] and bk["hooks_expected"] and len(meters) == bk["metering_links_receipt"] > 0
                                and len(ld) == bk["loads_receipt"] and set(bk["load_node_countries"]) <= set(S) and not no_supply
                                and all(v["has_source"] for v in src.values()) and zb.get("present") and zb.get("passed") and zb.get("covers_every_metering_flow")
                                and zb.get("metering_links") == len(meters))
        ok_nz = bool(all(v["row"] and v["verdict"] == "removal_ports_present" for v in nz.values()) and not extra)
        res["networks"][name] = dict(network=net, members=S, include_bunker=spec["include_bunker"], network_sha256=sha(p), bytes=p.stat().st_size,
                                     snapshots=int(len(n.snapshots)), weights_8760_over_56=bool(np.allclose(n.snapshot_weightings.to_numpy(), 8760.0 / 56, rtol=0, atol=1e-12)),
                                     zero_slack=dict(passed=zs["passed"], forcing_rows=zs["zero_slack_forcing_rows"], verdicts=zs["verdicts"], forms=zs["forms"],
                                                     bunker=zs["bunker"], configured_caps_without_row=zs["configured_caps_without_row"], hooks=zs["required_constraint_hooks"], seconds=zs["seconds"]),
                                     net_zero_rows=nz, net_zero_rows_of_non_members=extra, storage_cap_rows=cap_rows, net_zero_all_members_with_removal_port=ok_nz,
                                     nan=nanr, nan_new_vs_base=new_nan, sinks=sinks(n, S), bunker=bk,
                                     ledger=dict(removed_total=L["removed_total"], removed_by_rule=L["removed_by_rule"], boundary=sum(L["boundary_by_carrier"].values()),
                                                 retained_cross_border=len(L["retained_cross_border"]), retained_stock=len(L["retained_cross_border_stock"]),
                                                 dangling=len(L["dangling_buses_removed"]), carriers_removed=L["carriers_removed"],
                                                 dead_end_kept=len(L["dead_end_member_components_kept"]), dead_end_fixed_cost_constant_eur=L["dead_end_fixed_cost_constant_eur"],
                                                 transit_via_non_member=len(L["transit_via_non_member"]), d8_addback_eur=L["d8_addback_eur"], rules_version=L["rules_version"]),
                                     components={k: v for k, v in L["components_after"].items() if k in ("Bus", "Line", "Link", "Generator", "Store", "StorageUnit", "Load")},
                                     passed=bool(zs["passed"] and not new_nan and ok_nz and bk["passed"]), seconds=round(time.time() - t0, 1))
        del n
        r = res["networks"][name]
        print(f"{name}: passed={r['passed']} zero_slack={zs['passed']} forcing={zs['zero_slack_forcing_rows']} net_zero_ok={ok_nz} bunker_ok={bk['passed']} "
              f"meters={bk.get('metering_links')} loads={bk.get('loads')} new_nan={new_nan} verdicts={zs['verdicts']} ({r['seconds']} s)", flush=True)
    res["passed"] = bool(all(v["passed"] for v in res["networks"].values()))
    a.out.write_text(json.dumps(res, indent=1, default=str) + "\n")
    print("W20B_STATIC:" + ("PASS" if res["passed"] else "FAIL"))
    return 0 if res["passed"] else 3


if __name__ == "__main__":
    sys.exit(main())
