"""M12 C4.1 / C4.2 evidence (item 133): numbers of the toy 3-country LP of tests/research/test_m12_allocation.py (scipy linprog, HiGHS; no model
network, no Gurobi) - coalition costs, Owen allocation at alpha 0 / 0.5 / 1, core slacks, leave-one-out, SCRB, the vertex split HiGHS returns
for the two identical half-rows and the alpha range that keeps the allocation in the core.

    python m12_toy_evidence.py --repo /home/jin/wt_m12_20261021 --out <evidence/toy>
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    spec = importlib.util.spec_from_file_location("toytest", a.repo / "tests/research/test_m12_allocation.py"); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
    M = T.M; P3 = T.P3
    L, ix = T.toy(); sol = L.solve(); cN = sol["obj"] + sum(T.CONST.values())
    res = dict(lp=dict(variables=len(L.names), rows=len(L.rows), objective_lp=sol["obj"], constants=T.CONST, c_N=cN), by_alpha={})
    for al in (0.0, 0.5, 1.0):
        phi, raw = T.owen(sol, al); cost = T.coalition_costs(L, al)
        slack = {"+".join(sorted(S)): float(cost[S] - sum(phi[p] for p in S)) for S in cost}
        st = M.settle(T.market_assets(L, ix, sol), al, P3)
        loo = M.loo_check({p: phi[p] for p in P3}, cN, {i: cost[frozenset(P3) - {i}] for i in P3}, {})
        res["by_alpha"][f"{al:g}"] = dict(owen={p: phi[p] for p in P3}, market_form={p: st["allocation"][p] for p in P3}, coalition_costs={"+".join(sorted(S)): float(v) for S, v in cost.items()},
                                         core_slack=slack, min_core_slack=min(slack.values()), net_rent={k: -v for k, v in st["pairs"].items()},
                                         loo=dict(marginal={i: v["marginal_cost"] for i, v in loo["countries"].items()}, indivisible_cost=loo["indivisible_cost"]),
                                         scrb=M.scrb(cN, {i: cost[frozenset({i})] for i in P3}, {i: v["marginal_cost"] for i, v in loo["countries"].items()}))
    Ld, _ = T.toy(duplicate_ab=True); sd = Ld.solve(); rid = {r[4]: k for k, r in enumerate(Ld.rows) if r[4]}
    ya, yb = float(sd["pi"][rid["Fmax_AB_halfA"]]), float(sd["pi"][rid["Fmax_AB_halfB"]])
    grid = np.round(np.arange(-5.0, 6.0 + 1e-9, 0.05), 4); ok = []
    for al in grid:
        phi = T.owen(sol, float(al))[0]
        if not M.core_violations({p: phi[p] for p in P3}, T.coalition_costs(L, float(al)), tol=1e-7):
            ok.append(float(al))
    res["degeneracy"] = dict(half_row_duals=dict(A=ya, B=yb), returned_alpha=ya / (ya + yb), alpha_grid_step=0.05, core_alpha_min=min(ok), core_alpha_max=max(ok),
                             contiguous=bool(len(ok) == int(round((max(ok) - min(ok)) / 0.05)) + 1),
                             note="alpha = share of the first country (A) of the A-B pair for its net rent and the A-C sunk constant alike")
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "TOY_EVIDENCE.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(dict(c_N=cN, min_slack={k: v["min_core_slack"] for k, v in res["by_alpha"].items()}, degeneracy=res["degeneracy"]), indent=1))


if __name__ == "__main__":
    main()
