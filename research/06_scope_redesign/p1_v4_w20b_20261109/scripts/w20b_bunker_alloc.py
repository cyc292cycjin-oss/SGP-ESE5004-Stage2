"""V4 W20b section 2.3 (V4_W20B_INSTRUCTION.md SHA 25f1db61; decision 230): x_{B,i}, the Owen dual-form allocation of the bunker player split by
bunkering country (the country of the port / airport node of each bunker load), from the v4 main 56-snapshot solves used by W20 (D2c smoke R1 =
W14 smoke, integrated) and, for the strict "bunker benefit by bunkering country", the matching no_new_xb solve (D2c smoke R2). No solver.

    PYTHONHASHSEED=0 python w20b_bunker_alloc.py --repo /home/jin/wt_v4_w20b --smoke <results_project/v4d2c/smoke56> --out-json <..> --out-csv <..> --out-loads <..>

Method (same code path as M12, scripts_project/m12_rhs_audit.py audit, NODAL branch, formula unchanged): the LP is BUILT with
l23_violation_analysis.build_model (never solved), owners from m12_rhs_audit.Owners, loads split by owner (load_split), row multipliers from the
exported arrays of the solve (lp/ + solution/Pi, lp_array_duals). The rebuilt LP is checked against the exported one first: the same row and
column label sets and, for every nodal-balance row, the right-hand side equals the exported row bounds.
    x_{B,i} = sum over the nodal-balance rows of the bunker buses located at nodes of country i of  y x (BUNKER part of the right-hand side).
The other BUNKER-owned terms of the M12 dual form (non-nodal rows owned by BUNKER - the per-meter net-zero rows, rhs 0 -, column-bound terms and
objective constants of BUNKER-owned components) are computed and reported; acceptance |sum_i x_{B,i} - x_B(OWEN.json)| <= 0.01 bn.
Market form side by side: sum_t marginal_price(bus, t) x p(load, t) x objective weight on the solved network, by country, against OWEN.json
market_form BUNKER. Benefit (strict reading, decision 230 section 0): b_{B,i} = x_{B,i}(no_new_xb) - x_{B,i}(integrated); merged b_i^m = b_i + b_{B,i}.
"""
import argparse
import csv
import hashlib
import json
import logging
import os
import resource
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
TOL = 1e7   # 0.01 bn (instruction section 2.3 / 5)
RUNS = {"F1": dict(dir="v4d2c_F1", scenario="integrated", solved="integrated_SMOKE_TEST_ONLY_solved.nc"),
        "F2": dict(dir="v4d2c_F2", scenario="no_new_xb", solved="no_new_xb_SMOKE_TEST_ONLY_solved.nc")}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def run_one(repo: Path, d: Path, scenario: str, solved: str, truncate: int) -> dict:
    from l23_violation_analysis import build_model
    from m12_rhs_audit import NODAL, Owners, load_split, lp_array_duals, objective_constants
    from m12_allocation import BUNKER
    t0 = time.time()
    O_json = json.loads((d / "m12_owen" / "OWEN.json").read_text()); R = json.loads((d / "SOLVE_RECEIPT.json").read_text())
    network = Path(O_json["network"])
    if sha(network) != O_json["network_sha256"]:
        raise SystemExit(f"{network} differs from the network of OWEN.json")
    n, m, _ = build_model(repo, network, scenario, truncate, "W20B_BUNKER_ALLOC")
    t_build = time.time() - t0
    O = Owners(n)
    # --- the rebuilt LP is the exported LP (label sets, nodal right-hand sides) ------------------------------------------------------
    meta = json.loads((d / "lp" / "MATH_PROBLEM.json").read_text())
    clab = np.load(d / "lp" / "clabels.npy"); vlab = np.load(d / "lp" / "vlabels.npy")
    rl = np.load(d / "lp" / "row_lower.npy"); ru = np.load(d / "lp" / "row_upper.npy")
    cl_model = np.concatenate([np.asarray(m.constraints[c].labels.values).ravel() for c in m.constraints]); cl_model = np.sort(cl_model[cl_model >= 0])
    vl_model = np.concatenate([np.asarray(m.variables[v].labels.values).ravel() for v in m.variables]); vl_model = np.sort(vl_model[vl_model >= 0])
    lp_check = dict(num_row=int(meta.get("num_row", -1)), num_col=int(meta.get("num_col", -1)), rows_model=int(len(cl_model)), cols_model=int(len(vl_model)),
                    row_labels_equal=bool(np.array_equal(cl_model, np.sort(clab))), col_labels_equal=bool(np.array_equal(vl_model, np.sort(vlab))))
    pos = np.full(int(max(clab.max(), cl_model.max())) + 1, -1, dtype=np.int64); pos[clab] = np.arange(len(clab))
    top = max(int(np.asarray(m.variables[v].labels).max()) for v in m.variables) + 1
    vown = np.zeros(top, dtype=np.int32)
    for v in m.variables:
        lab = m.variables[v].labels; arr = np.asarray(lab.values).ravel(); oc = O.array(v, lab).ravel()
        ok = (arr >= 0) & (arr < top); vown[arr[ok]] = oc[ok]
    dual_of, rc_terms, col_info = lp_array_duals(d, vown, O)
    loads = load_split(n, O); inv = O.inv(); bcode = O.code(BUNKER)
    bc = n.buses.country.astype(str); loc = n.buses.location.astype(str)
    by_bus, rest_bus, nodal_dev = {}, {}, 0.0
    for name in NODAL:
        if name not in m.constraints:
            continue
        con = m.constraints[name]; lab = con.labels
        bdim = [x for x in lab.dims if str(x).startswith("Bus")][0]
        lab = lab.transpose("snapshot", bdim); rhs = np.asarray(con.rhs.broadcast_like(lab).transpose("snapshot", bdim).values, dtype=float)
        L = np.asarray(lab.values); valid = L >= 0
        p = pos[L[valid]]
        if (p < 0).any():
            raise SystemExit(f"{name}: rows of the rebuilt LP missing in the exported LP")
        nodal_dev = max(nodal_dev, float(np.max(np.abs(rl[p] - rhs[valid]))), float(np.max(np.abs(ru[p] - rhs[valid]))))
        nz = valid & np.isfinite(rhs) & (rhs != 0)
        y = np.asarray(dual_of(name, lab), dtype=float); oc = O.array(name, lab)
        buses = list(map(str, lab.coords[bdim].values)); snaps = lab.coords["snapshot"].values
        for j, b in enumerate(buses):
            ls = loads.get(b); bo = inv[int(oc[0, j])]
            has_b = ls is not None and BUNKER in ls.columns and np.abs(ls[BUNKER].to_numpy()).sum() > 0
            if not has_b and bo != BUNKER:
                continue
            r = np.where(nz[:, j], rhs[:, j], 0.0); yj = np.nan_to_num(y[:, j])
            tot = ls.sum(axis=1).reindex(snaps).fillna(0.0).to_numpy() if ls is not None else np.zeros(len(r))
            hs = tot != 0
            ratio = np.where(hs, r / np.where(hs, tot, 1.0), 0.0)
            part = ls[BUNKER].reindex(snaps).fillna(0.0).to_numpy() * ratio if has_b else np.zeros(len(r))
            by_bus[b] = by_bus.get(b, 0.0) + float((yj * part).sum())
            rest = np.where(hs, 0.0, r)
            if bo == BUNKER and rest.any():
                rest_bus[b] = rest_bus.get(b, 0.0) + float((yj * rest).sum())
    lp_check["nodal_rhs_max_abs_dev_vs_exported_bounds"] = nodal_dev
    lp_check["passed"] = bool(lp_check["row_labels_equal"] and lp_check["col_labels_equal"] and lp_check["rows_model"] == lp_check["num_row"]
                              and lp_check["cols_model"] == lp_check["num_col"] and nodal_dev == 0.0)
    # --- other BUNKER-owned terms of the dual form (m12_rhs_audit.audit rules: unresolved rows take a unique variable owner) ----------------
    nonnodal = {}
    for name in m.constraints:
        if name in NODAL:
            continue
        con = m.constraints[name]; lab = con.labels
        L = np.asarray(lab.values); valid = L >= 0
        oc = O.array(name, lab)
        V = np.asarray(con.vars.transpose(*lab.dims, "_term").values) if "_term" in con.vars.dims else np.asarray(con.vars.values)[..., None]
        Vo = np.where(V >= 0, vown[np.clip(V, 0, top - 1)], -1)
        lo_ = np.where(Vo >= 0, Vo, np.iinfo(np.int32).max).min(axis=-1); hi_ = Vo.max(axis=-1)
        oc = np.where(valid & (oc == 0) & (hi_ >= 0) & (lo_ == hi_), hi_, oc)
        mine = valid & (oc == bcode)
        if not mine.any():
            continue
        rhs = np.asarray(con.rhs.broadcast_like(lab).transpose(*lab.dims).values, dtype=float)
        nz = mine & np.isfinite(rhs) & (rhs != 0)
        yv = dual_of(name, lab)
        val = float(np.nansum(np.asarray(yv, dtype=float)[nz] * rhs[nz])) if nz.any() else 0.0
        nonnodal[name] = dict(rows=int(mine.sum()), rhs_nonzero_rows=int(nz.sum()), y_b_eur=val)
    consts = objective_constants(n, O)["by_owner"]
    x_B_owen = float(O_json["allocation_eur"]["0.5"][BUNKER])
    nodal_total = float(sum(by_bus.values())); rest_total = float(sum(rest_bus.values()))
    nn_total = float(sum(v["y_b_eur"] for v in nonnodal.values())); col_b = float(rc_terms.get(BUNKER, 0.0)); const_b = float(consts.get(BUNKER, 0.0))
    # --- by bunkering country; per load; market form on the solved network ---------------------------------------------------------------
    import pypsa
    ns = pypsa.Network(str(d / solved))
    w_obj = ns.snapshot_weightings.objective; w_gen = ns.snapshot_weightings.generators
    term = sorted(b for b in ns.buses.index[ns.buses.country.astype(str) == "ASEAN"] if b != "co2 bunkers ASEAN")
    lds = ns.loads[ns.loads.bus.astype(str).isin(term)]
    p = ns.loads_t.p[lds.index] if len(ns.loads_t.p.columns) else ns.get_switchable_as_dense("Load", "p_set")[lds.index]
    pset = n.get_switchable_as_dense("Load", "p_set")[lds.index]
    price = ns.buses_t.marginal_price
    rows = []
    for x in lds.index:
        b = str(lds.at[x, "bus"]); node = str(loc[b]); c = str(bc[node])
        nb = int((lds.bus == b).sum())
        rows.append(dict(load=str(x), bus=b, node=node, country=c, carrier=str(lds.at[x, "carrier"]), loads_on_bus=nb,
                         energy_mwh=float((pset[x] * w_gen.reindex(pset.index).to_numpy()).sum()),
                         x_dual_eur=(by_bus.get(b, 0.0) + rest_bus.get(b, 0.0)) / nb,
                         x_market_eur=float((price[b] * p[x] * w_obj).sum()),
                         realised_minus_pset_max_abs_mw=float(np.max(np.abs(p[x].to_numpy() - pset[x].reindex(p.index).to_numpy())))))
    # buses with a NON-ZERO BUNKER right-hand-side term but no load in the solved table (none expected); BUNKER-owned buses without a load
    # (the account bus, terminal buses without a load in the base) enter by_bus with 0 and are only counted
    loaded = {r["bus"] for r in rows}
    missing = sorted(b for b in set(by_bus) | set(rest_bus) if b not in loaded and (by_bus.get(b, 0.0) != 0.0 or rest_bus.get(b, 0.0) != 0.0))
    zero_buses = sorted(b for b in set(by_bus) | set(rest_bus) if b not in loaded and b not in missing)
    D = pd.DataFrame(rows)
    byc = {}
    for c in COUNTRIES:
        z = D[D.country == c]
        byc[c] = dict(loads=int(len(z)), aviation_loads=int((z.carrier == "oil final energy").sum()), methanol_loads=int((z.carrier == "shipping methanol").sum()),
                      energy_twh=float(z.energy_mwh.sum() / 1e6), aviation_twh=float(z[z.carrier == "oil final energy"].energy_mwh.sum() / 1e6),
                      methanol_twh=float(z[z.carrier == "shipping methanol"].energy_mwh.sum() / 1e6),
                      x_dual_eur=float(z.x_dual_eur.sum()), x_market_eur=float(z.x_market_eur.sum()))
    sum_i = float(sum(v["x_dual_eur"] for v in byc.values())); sum_mkt = float(sum(v["x_market_eur"] for v in byc.values()))
    x_B_mkt = float(O_json["market_form"]["allocation_alpha_half_eur"][BUNKER])
    del ns, n, m
    return dict(solve_dir=str(d), scenario=scenario, network=str(network), network_sha256=O_json["network_sha256"], owen_sha256=sha(d / "m12_owen" / "OWEN.json"),
                solved_network=str(d / solved), solved_network_sha256=sha(d / solved), objective_eur=float(R["objective"]),
                build_seconds=round(t_build, 1), seconds=round(time.time() - t0, 1), peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20,
                lp_check=lp_check, column_terms_info=col_info,
                x_B_owen_eur=x_B_owen, x_B_market_owen_eur=x_B_mkt,
                bunker_terms=dict(nodal_rows_bunker_part_eur=nodal_total, nodal_rows_without_load_bunker_buses_eur=rest_total, non_nodal_rows_eur=nn_total,
                                  non_nodal_rows=nonnodal, column_bound_terms_eur=col_b, objective_constants_eur=const_b,
                                  recomputed_total_eur=nodal_total + rest_total + nn_total + col_b + const_b),
                sum_i_x_B_i_eur=sum_i, diff_sum_i_minus_x_B_eur=sum_i - x_B_owen, check_passed=bool(abs(sum_i - x_B_owen) <= TOL and lp_check["passed"] and not missing),
                buses_with_bunker_rhs_not_in_solved_loads=missing, bunker_owned_buses_without_load_zero_term=zero_buses,
                sum_i_market_eur=sum_mkt, diff_market_sum_minus_owen_market_eur=sum_mkt - x_B_mkt,
                by_country=byc, loads=rows, x_owen_alpha_half_eur={k: float(v) for k, v in O_json["allocation_eur"]["0.5"].items()},
                x_owen_market_alpha_half_eur={k: float(v) for k, v in O_json["market_form"]["allocation_alpha_half_eur"].items()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--smoke", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True); ap.add_argument("--out-csv", type=Path, required=True); ap.add_argument("--out-loads", type=Path, required=True)
    ap.add_argument("--truncate", type=int, default=56)
    a = ap.parse_args()
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise SystemExit("PYTHONHASHSEED=0 required (constraint label order of the meshed buses depends on it)")
    sys.path.insert(0, str(a.repo / "scripts_project"))
    logging.disable(logging.WARNING)
    res = dict(script="work/p1_v4_w20b_20261109/scripts/w20b_bunker_alloc.py", solver_called=False, decision="230", tolerance_eur=TOL, runs={})
    for k, v in RUNS.items():
        res["runs"][k] = run_one(a.repo, a.smoke / v["dir"], v["scenario"], v["solved"], a.truncate)
        r = res["runs"][k]
        print(f"{k}: lp_check={r['lp_check']['passed']} x_B={r['x_B_owen_eur']/1e9:.6f} sum_i={r['sum_i_x_B_i_eur']/1e9:.6f} diff={r['diff_sum_i_minus_x_B_eur']:.3f} EUR "
              f"market diff={r['diff_market_sum_minus_owen_market_eur']:.3f} EUR terms={json.dumps({kk: vv for kk, vv in r['bunker_terms'].items() if kk != 'non_nodal_rows'})} "
              f"({r['seconds']} s, {r['peak_rss_gib']:.2f} GiB)", flush=True)
    B = json.loads((a.smoke / "M12_BENEFIT" / "BENEFIT.json").read_text())
    ben = {k: float(v) for k, v in B["owen"]["benefit_eur"].items()}
    F1, F2 = res["runs"]["F1"], res["runs"]["F2"]
    tot_e = sum(F1["by_country"][c]["energy_twh"] for c in COUNTRIES)
    out_rows = []
    for c in COUNTRIES:
        a1, a2 = F1["by_country"][c], F2["by_country"][c]
        bB = a2["x_dual_eur"] - a1["x_dual_eur"]
        out_rows.append(dict(country=c, bunker_loads=a1["loads"], aviation_loads=a1["aviation_loads"], methanol_loads=a1["methanol_loads"],
                             energy_twh=a1["energy_twh"], aviation_twh=a1["aviation_twh"], methanol_twh=a1["methanol_twh"], energy_share=a1["energy_twh"] / tot_e,
                             x_B_i_dual_F1_eur=a1["x_dual_eur"], x_B_i_share_F1=a1["x_dual_eur"] / F1["sum_i_x_B_i_eur"],
                             avg_price_F1_eur_per_mwh=(a1["x_dual_eur"] / (a1["energy_twh"] * 1e6) if a1["energy_twh"] > 0 else float("nan")),
                             x_B_i_market_F1_eur=a1["x_market_eur"], x_B_i_dual_F2_eur=a2["x_dual_eur"], x_B_i_market_F2_eur=a2["x_market_eur"],
                             x_i_dual_F1_eur=F1["x_owen_alpha_half_eur"][c], x_i_merged_dual_F1_eur=F1["x_owen_alpha_half_eur"][c] + a1["x_dual_eur"],
                             x_i_market_F1_eur=F1["x_owen_market_alpha_half_eur"][c], x_i_merged_market_F1_eur=F1["x_owen_market_alpha_half_eur"][c] + a1["x_market_eur"],
                             benefit_i_eur=ben[c], benefit_B_i_strict_eur=bB, benefit_i_merged_eur=ben[c] + bB,
                             benefit_B_i_energy_key_eur=a1["energy_twh"] / tot_e * ben["BUNKER"]))
    res["benefit"] = dict(source=str(a.smoke / "M12_BENEFIT" / "BENEFIT.json"), b6_eur=float(B["b6_eur"]), benefit_eur=ben,
                          bunker_benefit_eur=ben["BUNKER"], sum_i_benefit_B_i_strict_eur=float(sum(r["benefit_B_i_strict_eur"] for r in out_rows)),
                          diff_strict_sum_minus_bunker_benefit_eur=float(sum(r["benefit_B_i_strict_eur"] for r in out_rows)) - ben["BUNKER"],
                          merged_sum_eur=float(sum(r["benefit_i_merged_eur"] for r in out_rows)))
    res["table"] = out_rows
    res["passed"] = bool(F1["check_passed"] and F2["check_passed"])
    a.out_json.write_text(json.dumps(res, indent=1, default=str) + "\n")
    with open(a.out_csv, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()), lineterminator="\n"); wr.writeheader()
        for r in out_rows:
            wr.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})
        tot = {k: (sum(r[k] for r in out_rows) if isinstance(out_rows[0][k], (int, float)) and k not in ("avg_price_F1_eur_per_mwh",) else "") for k in out_rows[0]}
        tot["country"] = "TOTAL"; tot["avg_price_F1_eur_per_mwh"] = F1["sum_i_x_B_i_eur"] / (tot_e * 1e6)
        wr.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in tot.items()})
    with open(a.out_loads, "w", newline="") as f:
        L1 = {r["load"]: r for r in F1["loads"]}; L2 = {r["load"]: r for r in F2["loads"]}
        cols = ["load", "bus", "node", "country", "carrier", "loads_on_bus", "energy_mwh", "x_dual_F1_eur", "x_market_F1_eur", "x_dual_F2_eur", "x_market_F2_eur"]
        wr = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); wr.writeheader()
        for k in sorted(L1):
            r = L1[k]; q = L2.get(k, {})
            wr.writerow(dict(load=k, bus=r["bus"], node=r["node"], country=r["country"], carrier=r["carrier"], loads_on_bus=r["loads_on_bus"], energy_mwh=f"{r['energy_mwh']:.6f}",
                             x_dual_F1_eur=f"{r['x_dual_eur']:.6f}", x_market_F1_eur=f"{r['x_market_eur']:.6f}",
                             x_dual_F2_eur=f"{q.get('x_dual_eur', float('nan')):.6f}", x_market_F2_eur=f"{q.get('x_market_eur', float('nan')):.6f}"))
    print("W20B_BUNKER_ALLOC:" + ("PASS" if res["passed"] else "FAIL"),
          f"sum_i strict bunker benefit {res['benefit']['sum_i_benefit_B_i_strict_eur']/1e9:.6f} vs {ben['BUNKER']/1e9:.6f} bn")
    for r in out_rows:
        print(f"{r['country']} loads={r['bunker_loads']:3d} E={r['energy_twh']:8.3f} TWh x_B_i={r['x_B_i_dual_F1_eur']/1e9:8.4f} mkt={r['x_B_i_market_F1_eur']/1e9:8.4f} "
              f"F2={r['x_B_i_dual_F2_eur']/1e9:8.4f} b_B_i={r['benefit_B_i_strict_eur']/1e9:+.4f} (energy key {r['benefit_B_i_energy_key_eur']/1e9:+.4f}) "
              f"b_i={r['benefit_i_eur']/1e9:+.4f} b_i^m={r['benefit_i_merged_eur']/1e9:+.4f}")
    return 0 if res["passed"] else 3


if __name__ == "__main__":
    sys.exit(main())
