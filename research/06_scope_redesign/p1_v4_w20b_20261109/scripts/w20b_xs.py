"""V4 W20b section 3 (V4_W20B_INSTRUCTION.md SHA 25f1db61; decision 230): the registered allocations of the 18 runs, BEFORE any W20b solve. No solver.

    python w20b_xs.py --owen <v4d2c_F1/m12_owen/OWEN.json> --receipt <v4d2c_F1/SOLVE_RECEIPT.json> --alloc <evidence/W20B_BUNKER_PORT_ALLOCATION.json>
                      --nets <results_project/v4w20b/nets56> --w20-csv <p1_v4_w20_20261109/CORE_CHECK_V4_56.csv> --out-json <..> --out-csv <..>

R0 (all 11 countries, no bunker): x(N \\ B) = sum of the 11 countries' Owen dual-form allocations (alpha 0.5, OWEN.json of the v4 main 56-snapshot
integrated solve = D2c smoke R1 = W14 smoke); D = c(N \\ B) - x(N \\ B) after the solve; x(N \\ B) <= c(N \\ B) <=> the bunker pays at least its
incremental cost (x_B >= c(N) - c(N \\ B), with c(N) = objective = x(N \\ B) + x_B + SHARED (0) up to the dual-form residual).
Merged game ("ports" coalitions): x^m(S) = sum over i in S of (x_i + x_{B,i}), x_{B,i} from W20B_BUNKER_PORT_ALLOCATION.json (section 2.3, F1);
alpha interval: every cross-border pair with exactly one member contributes alpha v or (1 - alpha) v (pairs inside S cancel; x_{B,i} has no pair term),
so x^m(S) ranges over x^m(S, 0.5) -+ 0.5 sum |v|; market form x_i^mkt + x_{B,i}^mkt; D8 add-back from the network receipt (as W20).
Merged Owen benefit (for reading only): b_i^m = b_i + b_{B,i} with b_{B,i} = x_{B,i}(no_new_xb) - x_{B,i}(integrated) (strict reading); B^m(S) = sum over S.
Identity: |sum of the 11 merged shares - objective| <= 0.01 bn. Threshold (decision 139): violation iff x(S) - c(S) > max(0.01 c(S), 0.01 bn).
"""
import argparse
import csv
import json
import sys
from pathlib import Path

COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")


def main():
    ap = argparse.ArgumentParser()
    for k in ("owen", "receipt", "alloc", "nets", "w20-csv", "out-json", "out-csv"):
        ap.add_argument("--" + k, type=Path, required=True)
    ap.add_argument("--repo", type=Path, default=Path("/home/jin/wt_v4_w20b"))
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    from v4_coalition import sha, w20b_runs
    O = json.loads(a.owen.read_text()); R = json.loads(a.receipt.read_text()); A = json.loads(a.alloc.read_text())
    if not A.get("passed"):
        raise SystemExit("the x_{B,i} allocation check did not pass - not registered")
    F1 = A["runs"]["F1"]
    if F1["owen_sha256"] != sha(a.owen):
        raise SystemExit("the allocation was computed from a different OWEN.json")
    x = {k: float(v) for k, v in O["allocation_eur"]["0.5"].items()}
    mk = {k: float(v) for k, v in O["market_form"]["allocation_alpha_half_eur"].items()}
    pv = {k: float(v) for k, v in O["pair_values_eur"].items()}
    xb = {c: float(F1["by_country"][c]["x_dual_eur"]) for c in COUNTRIES}; xbm = {c: float(F1["by_country"][c]["x_market_eur"]) for c in COUNTRIES}
    ben = {r["country"]: r for r in A["table"]}
    bm = {c: float(ben[c]["benefit_i_merged_eur"]) for c in COUNTRIES}; b = {c: float(ben[c]["benefit_i_eur"]) for c in COUNTRIES}
    obj = float(R["objective"])
    xm = {c: x[c] + xb[c] for c in COUNTRIES}; xmm = {c: mk[c] + xbm[c] for c in COUNTRIES}
    ident = dict(objective_eur=obj, sum_11_merged_eur=sum(xm.values()), difference_eur=sum(xm.values()) + x.get("SHARED", 0.0) - obj, tolerance_eur=1e7,
                 x_B_eur=x["BUNKER"], sum_i_x_B_i_eur=sum(xb.values()), x_B_split_difference_eur=sum(xb.values()) - x["BUNKER"],
                 x_N_minus_B_eur=sum(x[c] for c in COUNTRIES), market_sum_11_merged_eur=sum(xmm.values()))
    ident["passed"] = bool(abs(ident["difference_eur"]) <= 1e7 and abs(ident["x_B_split_difference_eur"]) <= 1e7)
    w20 = {r["coalition"]: r for r in csv.DictReader(open(a.w20_csv))}
    rows, out = [], {}
    for name, spec in w20b_runs().items():
        S = set(spec["members"]); ports = spec["include_bunker"] == "ports"
        rec = json.loads((a.nets / f"{spec['net']}_56_COALITION_RECEIPT.json").read_text()); L = rec["ledger"]
        bnd = {p: v for p, v in pv.items() if len(set(p.split("|")) & S) == 1}; half = 0.5 * sum(abs(v) for v in bnd.values())
        if ports:
            xs = sum(xm[c] for c in S); ms = sum(xmm[c] for c in S); xbs = sum(xb[c] for c in S); B = sum(bm[c] for c in S)
        else:
            xs = sum(x[c] for c in S); ms = sum(mk[c] for c in S); xbs = 0.0; B = sum(b[c] for c in S)
        r = dict(run=name, network=spec["net"], include_bunker=str(spec["include_bunker"]), members=" ".join(sorted(S)), n_members=len(S),
                 network_sha256=rec["output"]["sha256"], x_dual_eur=xs, x_dual_alpha_min_eur=xs - half, x_dual_alpha_max_eur=xs + half,
                 x_bunker_part_eur=xbs, x_countries_part_eur=sum(x[c] for c in S), x_market_eur=ms, boundary_pairs=" ".join(sorted(bnd)),
                 owen_benefit_merged_eur=B, d8_addback_eur=L["d8_addback_eur"], dead_end_fixed_cost_constant_eur=L["dead_end_fixed_cost_constant_eur"],
                 retained_stock=len(L["retained_cross_border_stock"]), transit_via_non_member=len(L["transit_via_non_member"]),
                 bunker_loads_kept=(L["bunker"] or {}).get("loads_kept", 0), bunker_metering_links_kept=(L["bunker"] or {}).get("metering_links_kept", 0),
                 bunker_energy_twh=sum((L["bunker"] or {}).get("energy_mwh_kept_by_country", {}).values()) / 1e6 if ports else 0.0)
        if name in w20:   # W20 (decision 228): the same countries without any bunker component (c(S), margin c(S) - x(S)); reference only
            r.update(w20_c_eur=float(w20[name]["c_eur"]), w20_x_eur=float(w20[name]["x_dual_eur"]), w20_margin_eur=float(w20[name]["margin_dual_eur"]))
        if name.startswith("minus"):
            i = name[5:]
            r.update(loo_country=i, x_i_eur=x[i], x_B_i_eur=xb[i], x_i_merged_eur=xm[i], b_i_merged_eur=bm[i])
        rows.append(r); out[name] = dict(r, boundary_pair_values_eur=bnd, bunker_ledger=L["bunker"])
    res = dict(script="work/p1_v4_w20b_20261109/scripts/w20b_xs.py", owen=str(a.owen), owen_sha256=sha(a.owen), receipt=str(a.receipt), receipt_sha256=sha(a.receipt),
               alloc=str(a.alloc), alloc_sha256=sha(a.alloc), identity=ident, x_dual_alpha_half_eur=x, x_market_alpha_half_eur=mk, x_B_i_dual_eur=xb, x_B_i_market_eur=xbm,
               x_merged_dual_eur=xm, x_merged_market_eur=xmm, benefit_merged_eur=bm, benefit_eur=b, pair_values_eur=pv, runs=out,
               threshold_rule="violation iff x(S) - c(S) > max(0.01 * c(S), 1e7 EUR) (decision 139, registered before the solves)")
    a.out_json.write_text(json.dumps(res, indent=1, default=str) + "\n")
    cols = []
    for r in rows:
        cols += [k for k in r if k not in cols]
    with open(a.out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})
    print(json.dumps(dict(identity=ident), indent=1))
    for r in rows:
        print(f"{r['run']:8s} {r['include_bunker']:6s} x={r['x_dual_eur']/1e9:9.4f} [{r['x_dual_alpha_min_eur']/1e9:9.4f},{r['x_dual_alpha_max_eur']/1e9:9.4f}] "
              f"xB={r['x_bunker_part_eur']/1e9:7.4f} mkt={r['x_market_eur']/1e9:9.4f} B^m={r['owen_benefit_merged_eur']/1e9:7.4f} d8={r['d8_addback_eur']/1e6:.3f}M "
              f"bunkerTWh={r['bunker_energy_twh']:.2f} loads={r['bunker_loads_kept']}")
    return 0 if ident["passed"] else 3


if __name__ == "__main__":
    sys.exit(main())
