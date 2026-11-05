"""V3.1 section 5.2: the local 56x3h regression (v3.1 smoke job body, runner path) against the pre-fix local smoke (RUN_PLAN_V3.md section 25,
work/p1_v3_20261102/evidence/hpc/smoke). Read-only. Stop rule (instruction 5.2): objective relative deviation > 1e-6; any of the 12 players' Owen
benefit changes sign or moves by more than max(0.1 % of |old|, 1 M EUR). The per-country ledger is listed item by item with the same tolerance
(reported; a ledger total over it is flagged too).
    python compare_56.py --new <run dir runs/smoke56_v31> --ref <evidence/hpc/smoke> --out <dir>"""
import argparse
import json
import math
from pathlib import Path

import pandas as pd

RUNS = {"F1": "integrated", "F2": "no_new_xb"}
PLAYERS = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN", "BUNKER"]
BUNKER_BUS = "co2 bunkers ASEAN"


def jl(p):
    return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}


def tol(old):
    return max(1e-3 * abs(old), 1e6)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--new", type=Path, required=True); ap.add_argument("--ref", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(); res = dict(new=str(a.new), ref=str(a.ref), runs={}, stop=[], notes=[])
    for rid, sc in RUNS.items():
        n, r = a.new / rid, a.ref / sc
        rn, rr = jl(n / "SOLVE_RECEIPT.json"), jl(r / "SOLVE_RECEIPT.json")
        on, oo = rn.get("objective"), rr.get("objective")
        rel = abs(on - oo) / abs(oo) if (on is not None and oo) else None
        sp = jl(n / "split" / "SPLIT_SOLVE.json"); pn, pr = jl(n / "PRECISION.json").get("grade", {}), jl(r / "PRECISION.json").get("grade", {})
        gn = jl(n / "V5_GATES.json"); ba = jl(n / "BUNKER_ACCOUNT.json"); ss = jl(n / "split" / "SPLIT_BUILD.json")
        lp_n, lp_r = rn.get("lp") or {}, rr.get("lp") or {}
        run = dict(termination_new=rn.get("termination_condition"), termination_ref=rr.get("termination_condition"), objective_new=on, objective_ref=oo, objective_relative_difference=rel,
                   objective_difference_eur=(on - oo) if rel is not None else None, iterations_new=sp.get("bar_iter_count"), gurobi_status_new=sp.get("gurobi_status_name"), runtime_s_new=sp.get("runtime_s"),
                   v6_label_new=jl(n / "V6_ACCEPTANCE.json").get("label"), v6_label_ref=jl(r / "V6_ACCEPTANCE.json").get("label"),
                   c1_new=dict(grade=pn.get("grade"), a=pn.get("a"), b=pn.get("b"), c=pn.get("c")), c1_ref=dict(grade=pr.get("grade"), a=pr.get("a"), b=pr.get("b"), c=pr.get("c")),
                   lp_rows_new=lp_n.get("num_row"), lp_rows_ref=lp_r.get("num_row"), lp_cols_new=lp_n.get("num_col"), lp_cols_ref=lp_r.get("num_col"), lp_nnz_new=lp_n.get("nnz"), lp_nnz_ref=lp_r.get("nnz"),
                   research_constraints_new=lp_n.get("research_constraints"),
                   b1_bunkers=dict(passed=(gn.get("B1_BUNKERS") or {}).get("passed"), final_level_tco2=ba.get("final_level_tco2"), tolerance_t=ba.get("tolerance_t"), gross_co2_flow_t=ba.get("gross_co2_flow_t")),
                   failing_gates_new=sorted(k for k, v in gn.items() if isinstance(v, dict) and v.get("passed") is False),
                   failing_gates_ref=sorted(k for k, v in jl(r / "V5_GATES.json").items() if isinstance(v, dict) and v.get("passed") is False))
        if rel is None or rel > 1e-6:
            res["stop"].append(f"{rid}: objective relative difference {rel} > 1e-6")
        if run["termination_new"] != "optimal" or not str(run["v6_label_new"]).startswith("ACCEPTED"):
            res["stop"].append(f"{rid}: termination {run['termination_new']} / label {run['v6_label_new']}")
        # ledger per entity: every subject column and the totals
        Ln = pd.read_csv(n / "COUNTRY_COST_LEDGER.csv", index_col=0); Lr = pd.read_csv(r / "COUNTRY_COST_LEDGER.csv", index_col=0)
        cols = sorted(set(Ln.columns) | set(Lr.columns)); ents = sorted(set(Ln.index) | set(Lr.index))
        Ln, Lr = Ln.reindex(index=ents, columns=cols).fillna(0.0), Lr.reindex(index=ents, columns=cols).fillna(0.0)
        D = Ln - Lr; led = {}
        for e in ents:
            o, v = float(Lr.at[e, "total"]), float(Ln.at[e, "total"])
            big = D.loc[e].abs().sort_values(ascending=False)
            led[e] = dict(total_ref=o, total_new=v, total_difference=v - o, tolerance=tol(o), over_tolerance=bool(abs(v - o) > tol(o)),
                          total_length_split_difference=float(D.at[e, "total_length_split"]) if "total_length_split" in D.columns else None,
                          bunker_co2_settlement_ref=float(Lr.at[e, "bunker_co2 bunkers"]) if "bunker_co2 bunkers" in Lr.columns else None,
                          bunker_co2_settlement_new=float(Ln.at[e, "bunker_co2 bunkers"]) if "bunker_co2 bunkers" in Ln.columns else None,
                          largest_subject_differences={k: float(D.at[e, k]) for k in big.index[:3] if k not in ("total", "total_length_split")})
            if led[e]["over_tolerance"]:
                res["stop"].append(f"{rid}: ledger {e} total differs by {v - o:.6g} EUR (tolerance {tol(o):.6g})")
        run["ledger"] = led
        # nodal price table: the bunker account row NaN + note (V3.1); the raw dual of that bus in the solved network for information
        npf = n / "NODAL_PRICES.csv"
        if npf.exists():
            P = pd.read_csv(npf, index_col=0)
            if BUNKER_BUS in P.index:
                run["nodal_prices_bunker_row"] = dict(mean=None if pd.isna(P.at[BUNKER_BUS, "mean"]) else float(P.at[BUNKER_BUS, "mean"]), note=str(P.at[BUNKER_BUS, "note"])[:120] if "note" in P.columns else None)
        res["runs"][rid] = run
    Bn, Br = jl(a.new / "M12_BENEFIT" / "BENEFIT.json"), jl(a.ref / "M12_BENEFIT" / "BENEFIT.json")
    cn = pd.read_csv(a.new / "M12_BENEFIT" / "BENEFIT.csv", index_col=0); cr = pd.read_csv(a.ref / "M12_BENEFIT" / "BENEFIT.csv", index_col=0)
    ow = {}
    for p in PLAYERS:
        o, v = float(cr.at[p, "owen_benefit_eur"]), float(cn.at[p, "owen_benefit_eur"])
        sign_same = (math.copysign(1, o) == math.copysign(1, v)) or (o == 0 and v == 0)
        ow[p] = dict(owen_ref=o, owen_new=v, difference=v - o, tolerance=tol(o), sign_same=bool(sign_same), over_tolerance=bool(abs(v - o) > tol(o)),
                     interval_ref=[float(cr.at[p, "owen_benefit_min_eur"]), float(cr.at[p, "owen_benefit_max_eur"])], interval_new=[float(cn.at[p, "owen_benefit_min_eur"]), float(cn.at[p, "owen_benefit_max_eur"])],
                     market_form_ref=float(cr.at[p, "market_form_benefit_eur"]), market_form_new=float(cn.at[p, "market_form_benefit_eur"]))
        if not sign_same:
            res["stop"].append(f"Owen benefit of {p} changes sign ({o:.6g} -> {v:.6g})")
        if ow[p]["over_tolerance"]:
            res["stop"].append(f"Owen benefit of {p} differs by {v - o:.6g} EUR (tolerance {tol(o):.6g})")
    res["owen_benefit"] = ow
    res["b6"] = dict(ref_eur=Br.get("b6_eur"), new_eur=Bn.get("b6_eur"), difference_eur=(Bn.get("b6_eur") - Br.get("b6_eur")) if (Bn.get("b6_eur") is not None and Br.get("b6_eur") is not None) else None)
    res["passed"] = not res["stop"]
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "REGRESSION_56.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
    L = ["# V3.1 本机 56×3h 回归对比（第 5.2 节；只读）", "", f"- 新：`{a.new}`（v3.1 冒烟作业体，运行器 split 路径）", f"- 参照：`{a.ref}`（修正前本机冒烟，`RUN_PLAN_V3.md` 第 25 节）", f"- 结论：**{'通过' if res['passed'] else '停止：' + '；'.join(res['stop'])}**", "",
         "| 运行 | 终止（新 / 参照） | 目标值 新 EUR | 目标值 参照 EUR | 相对差 | 迭代 | V6 标签（新 / 参照） | C1 abc 新 | LP 行（新 − 参照） |", "|---|---|---:|---:|---:|---:|---|---|---:|"]
    for rid, x in res["runs"].items():
        c = x["c1_new"]
        L.append(f"| {rid} | {x['termination_new']} / {x['termination_ref']} | {x['objective_new']!r} | {x['objective_ref']!r} | {x['objective_relative_difference']:.3e} | {x['iterations_new']} | {x['v6_label_new']} / {x['v6_label_ref']} | {int(bool(c['a']))}{int(bool(c['b']))}{int(bool(c['c']))} | "
                 f"{(x['lp_rows_new'] or 0) - (x['lp_rows_ref'] or 0):,} |")
    L += ["", "| 参与者 | Owen 受益 参照 EUR | Owen 受益 新 EUR | 差 EUR | 容差 EUR | 符号相同 | 超容差 |", "|---|---:|---:|---:|---:|---|---|"]
    for p, x in ow.items():
        L.append(f"| {p} | {x['owen_ref']:,.0f} | {x['owen_new']:,.0f} | {x['difference']:,.1f} | {x['tolerance']:,.0f} | {x['sign_same']} | {x['over_tolerance']} |")
    for rid, x in res["runs"].items():
        L += ["", f"**{rid} 各国台账（total，EUR）**", "", "| 主体 | 参照 | 新 | 差 | 容差 | 超容差 | 燃料舱 CO₂ 结算 参照 / 新 |", "|---|---:|---:|---:|---:|---|---|"]
        for e, y in x["ledger"].items():
            L.append(f"| {e} | {y['total_ref']:,.0f} | {y['total_new']:,.0f} | {y['total_difference']:,.1f} | {y['tolerance']:,.0f} | {y['over_tolerance']} | {y['bunker_co2_settlement_ref']} / {y['bunker_co2_settlement_new']} |")
    L += ["", f"B6：参照 {res['b6']['ref_eur']!r} EUR，新 {res['b6']['new_eur']!r} EUR，差 {res['b6']['difference_eur']!r} EUR。"]
    (a.out / "REGRESSION_56.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps(dict(passed=res["passed"], stop=res["stop"], objective_rel={k: v["objective_relative_difference"] for k, v in res["runs"].items()}, b6=res["b6"]), default=str))


if __name__ == "__main__":
    main()
