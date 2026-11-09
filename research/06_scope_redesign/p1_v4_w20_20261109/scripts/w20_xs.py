"""V4 W20 section 3: x(S) of the 17 coalitions from the M12 output of the v4 main 56-snapshot integrated solution (D2c smoke R1 = W14 smoke
expectation: same network data, objective 363,190,038,821.0828 EUR, W14 drill relative difference 0). No solver; read only.

    python w20_xs.py --owen <v4d2c_F1/m12_owen/OWEN.json> --receipt <v4d2c_F1/SOLVE_RECEIPT.json> --nets <results_project/v4w20/nets56> --out-json <..> --out-csv <..>

x(S) = sum over i in S of the Owen dual-form total-cost allocation at alpha 0.5 (OWEN.json allocation_eur["0.5"]); alpha interval of x(S): every
cross-border pair with exactly one member contributes alpha * v or (1 - alpha) * v (v = pair value: rows y'b of the pair + its objective constant),
so x(S) ranges over x(S, 0.5) -+ 0.5 * sum |v| (pairs inside S cancel); market form = OWEN.json market_form.allocation_alpha_half_eur.
Identity (instruction section 3): |sum of the 12 players - objective| <= 0.01 bn. LOO, decision 141 reading: c(N) := x(N) = sum of the 11 countries
= objective - x(BUNKER) (the bunker-free grand coalition is not solved: 17 solves), so x_i - [c(N) - c(N - i)] = c(N - i) - x(N - i) - the core margin.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--owen", type=Path, required=True); ap.add_argument("--receipt", type=Path, required=True)
    ap.add_argument("--nets", type=Path, required=True); ap.add_argument("--out-json", type=Path, required=True); ap.add_argument("--out-csv", type=Path, required=True)
    ap.add_argument("--repo", type=Path, default=Path("/home/jin/wt_v4_w20"))
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    from v4_coalition import COALITION_ORDER, coalitions, sha
    O = json.loads(a.owen.read_text()); R = json.loads(a.receipt.read_text())
    x = {k: float(v) for k, v in O["allocation_eur"]["0.5"].items()}
    mk = {k: float(v) for k, v in O["market_form"]["allocation_alpha_half_eur"].items()}
    pv = {k: float(v) for k, v in O["pair_values_eur"].items()}
    obj = float(R["objective"]); players = sum(x[k] for k in COUNTRIES) + x["BUNKER"] + x.get("SHARED", 0.0)
    ident = dict(objective_eur=obj, objective_lp_eur=float(R.get("objective_lp", float("nan"))), sum_12_players_eur=players, difference_eur=players - obj,
                 tolerance_eur=1e7, passed=abs(players - obj) <= 1e7, owen_identity=O["identity"], owen_usable_for_allocation=O["usable_for_allocation"],
                 dual_acceptance_passed=O["dual_acceptance"]["passed"], x_bunker_eur=x["BUNKER"], shared_eur=x.get("SHARED", 0.0),
                 x_N_11_countries_eur=sum(x[k] for k in COUNTRIES), market_identity=O["market_form"]["identity"])
    rows, out = [], {}
    for name in COALITION_ORDER:
        S = set(coalitions()[name])
        xs = sum(x[c] for c in S); ms = sum(mk[c] for c in S)
        bnd = {p: v for p, v in pv.items() if len(set(p.split("|")) & S) == 1}
        half = 0.5 * sum(abs(v) for v in bnd.values())
        rec = json.loads((a.nets / f"{name}_56_COALITION_RECEIPT.json").read_text()); L = rec["ledger"]
        stock = L["retained_cross_border_stock"]
        r = dict(coalition=name, members=" ".join(sorted(S)), n_members=len(S), network_sha256=rec["output"]["sha256"],
                 x_dual_eur=xs, x_dual_alpha_min_eur=xs - half, x_dual_alpha_max_eur=xs + half, boundary_pairs=" ".join(sorted(bnd)),
                 x_market_eur=ms, retained_cross_border=len(L["retained_cross_border"]), retained_stock=len(stock),
                 retained_stock_lines=sum(1 for s in stock if s["component_type"] == "Line"), retained_stock_links=sum(1 for s in stock if s["component_type"] == "Link"),
                 retained_stock_pairs=" ".join(sorted({"|".join(s["countries"]) for s in stock})), boundary_removed=sum(L["boundary_by_carrier"].values()),
                 d8_addback_eur=L["d8_addback_eur"], dead_end_fixed_cost_constant_eur=L["dead_end_fixed_cost_constant_eur"],
                 transit_via_non_member=len(L["transit_via_non_member"]))
        if name.startswith("minus"):
            i = name[5:]
            r.update(loo_country=i, x_i_dual_eur=x[i], x_i_market_eur=mk[i], c_N_eur=ident["x_N_11_countries_eur"])
        rows.append(r); out[name] = dict(r, retained_cross_border_stock=stock, boundary_pair_values_eur=bnd, transit_via_non_member=L["transit_via_non_member"])
    res = dict(script="work/p1_v4_w20_20261109/scripts/w20_xs.py", owen=str(a.owen), owen_sha256=sha(a.owen), receipt=str(a.receipt), receipt_sha256=sha(a.receipt),
               solve_network_sha256=O.get("network_sha256"), identity=ident, x_dual_alpha_half_eur=x, x_market_alpha_half_eur=mk, pair_values_eur=pv, coalitions=out,
               threshold_rule="violation iff x(S) - c(S) > max(0.01 * c(S), 1e7 EUR) (decision 139, registered before the solves)")
    a.out_json.write_text(json.dumps(res, indent=1, default=str) + "\n")
    cols = list(rows[0].keys()) + [k for k in rows[-1].keys() if k not in rows[0]]
    with open(a.out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})
    print(json.dumps(dict(identity_passed=ident["passed"], difference_eur=ident["difference_eur"], x_N=ident["x_N_11_countries_eur"], x_bunker=x["BUNKER"]), indent=1))
    for r in rows:
        print(f"{r['coalition']:8s} x_dual={r['x_dual_eur']/1e9:9.4f} [{r['x_dual_alpha_min_eur']/1e9:9.4f},{r['x_dual_alpha_max_eur']/1e9:9.4f}] x_mkt={r['x_market_eur']/1e9:9.4f} "
              f"stock={r['retained_stock']} ({r['retained_stock_pairs']}) d8={r['d8_addback_eur']/1e6:.3f}M transit={r['transit_via_non_member']}")
    return 0 if ident["passed"] else 3


if __name__ == "__main__":
    sys.exit(main())
