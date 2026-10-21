"""M12 supplement 01 evidence (item 136): toy LPs of tests/research/test_m12_allocation.py (scipy linprog, HiGHS; no model network, no Gurobi).

D1 - KVL loop toy (lines A-B, B-C, A-C with one homogeneous loop row per snapshot): dual form and market form, the loop transfer, coalition costs
of the matrix game (Owen: same LP with b(S), the loop row stays) and of the physical game (a coalition without one of the loop's lines has no
loop row - the leave-one-out variants), core violations of both forms in both games, for three parameter sets.
D10 - bunker-type player: 4-player allocation, c({BUNKER}), strict standalone cost, core over 15 coalitions.

    python m12_s01_toy_evidence.py --repo /home/jin/wt_m12_20261021 --out <evidence/s01/toy>
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    spec = importlib.util.spec_from_file_location("toytest", a.repo / "tests/research/test_m12_allocation.py"); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
    M = T.M; P3 = T.P3
    name = lambda S: "+".join(sorted(S))   # noqa: E731
    kvl = []
    for kbc, fmax in ((1.0, 2.0), (0.5, 2.0), (2.0, 4.0)):
        T.KVL_BC = kbc
        L, ix = T.toy(fmax_ab=fmax, kvl=True); sol = L.solve(); cN = sol["obj"] + sum(T.CONST.values())
        phi = T.owen(sol, 0.5)[0]; mk = M.settle(T.market_assets(L, ix, sol), 0.5, P3)["allocation"]
        kr = [k for k, r in enumerate(L.rows) if r[4].startswith("kvl_")]
        tr = {}
        for t, k in enumerate(kr):
            for nm, own in (("AB", "A|B"), ("BC", "B|C"), ("AC", "A|C")):
                tr[own] = tr.get(own, 0.0) + sol["pi"][k] * L.rows[k][0][ix["f", nm, t]] * sol["x"][ix["f", nm, t]]
        trf = M.fold(tr, 0.5, P3)
        cm = T.kvl_coalition_costs(L, 0.5, physical=False); cp = T.kvl_coalition_costs(L, 0.5, physical=True)
        kvl.append(dict(KVL_BC=kbc, fmax_ab=fmax, c_N=cN, kvl_duals=[float(sol["pi"][k]) for k in kr],
                        dual_form={p: phi[p] for p in P3}, market_form={p: mk[p] for p in P3}, loop_transfer={p: trf[p] for p in P3},
                        market_minus_dual_minus_transfer_max_abs=max(abs(mk[p] - phi[p] - trf[p]) for p in P3),
                        coalition_cost_matrix={name(S): v for S, v in cm.items()}, coalition_cost_physical={name(S): v for S, v in cp.items()},
                        dual_violations_matrix=M.core_violations({p: phi[p] for p in P3}, cm, 1e-7), dual_violations_physical=M.core_violations({p: phi[p] for p in P3}, cp, 1e-7),
                        market_violations_matrix=M.core_violations({p: mk[p] for p in P3}, cm, 1e-7), market_violations_physical=M.core_violations({p: mk[p] for p in P3}, cp, 1e-7)))
    T.KVL_BC = 1.0
    P4 = P3 + (M.BUNKER,)
    L, ix = T.toy(bunker=T.BUNKER_D); sol = L.solve(); cN = sol["obj"] + sum(T.CONST.values())
    raw = dict(M.dual_form(sol["lo"], sol["hi"], sol["pi"], sol["own"])["total"])
    for k, v in T.CONST.items():
        raw[k] = raw.get(k, 0.0) + v
    phi = M.fold(raw, 0.5, P4)
    cost = {S: L.solve(S)["obj"] + sum(s * v for k, v in T.CONST.items() for p, s in M.shares(k, 0.5).items() if p in S) for S in M.coalitions(P4)}
    strict = sum(T.BUNKER_PIMP * T.W[t] * T.BUNKER_D[t] for t in range(4))
    bunker = dict(c_N=cN, owen={p: phi[p] for p in P4}, c_bunker_alone=cost[frozenset({M.BUNKER})], strict_standalone=strict,
                  share_within_standalone=bool(phi[M.BUNKER] <= strict), core_violations=M.core_violations({p: phi[p] for p in P4}, cost, 1e-7),
                  min_core_slack=min(cost[S] - sum(phi[p] for p in S) for S in cost), meter_flows=[float(sol["x"][ix["m", t]]) for t in range(4)],
                  bunker_imports=[float(sol["x"][ix["ub", t]]) for t in range(4)])
    res = dict(script="m12_s01_toy_evidence.py", kvl_loop=kvl, bunker_player=bunker,
               note="matrix game = Owen's linear production game (coalition LP = same matrix, b(S)); physical game = coalition networks without the "
                    "lines outside S (loop rows of broken loops removed), as in the leave-one-out variants")
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "TOY_S01_EVIDENCE.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(dict(kvl=[dict(KVL_BC=x["KVL_BC"], fmax=x["fmax_ab"], dual_phys=x["dual_violations_physical"], market_phys=x["market_violations_physical"],
                                    dual_matrix=x["dual_violations_matrix"]) for x in kvl],
                          bunker=dict(phi=bunker["owen"][M.BUNKER], strict=strict, core=bunker["core_violations"])), indent=1, default=str))


if __name__ == "__main__":
    main()
