"""M12 C4.1 / C4.2 (item 133): Owen allocation on toy 3-country LPs solved with scipy linprog (HiGHS) - no model network, no Gurobi.

Toy linear production game: every right-hand side belongs to a player (demand rows, potentials, line half-rights); a cross-border line is two
halves (its rows carry the pair code "A|B" and are open only if both countries are in the coalition); extra-regional imports at fixed prices;
objective constants (sunk costs) belong to players, a cross-border constant split with the same alpha as the line's rent. All 7 coalition LPs
are solved explicitly: the Owen allocation is in the core, the identity holds, alpha changes no total; the market-settlement form (asset cost +
net purchases at the nodal duals - net rent share) equals the dual form y' b; every alpha in [0, 1] of the degenerate half-line rows is in the core."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
import m12_allocation as M  # noqa: E402

P3 = ("A", "B", "C")


class LP:
    """tiny row-wise LP: rows lo <= a x <= hi with an owner code; one-sided or equality rows only."""

    def __init__(self):
        self.names, self.c, self.vlo, self.vhi, self.rows = [], [], [], [], []

    def var(self, name, cost=0.0, lo=0.0, hi=np.inf):
        self.names.append(name); self.c.append(float(cost)); self.vlo.append(lo); self.vhi.append(hi)
        return len(self.names) - 1

    def row(self, coef: dict, lo, hi, owner, name=""):
        assert np.isinf(lo) or np.isinf(hi) or lo == hi
        self.rows.append((coef, float(lo), float(hi), owner, name))

    def arrays(self, S=None):
        """row bounds of coalition S: a player's finite bounds kept iff the player (both players of a pair) is in S, else 0."""
        lo = np.array([r[1] for r in self.rows]); hi = np.array([r[2] for r in self.rows]); own = [r[3] for r in self.rows]
        if S is not None:
            f = np.array([1.0 if all(p in S for p in o.split("|")) or o == M.SHARED else 0.0 for o in own])
            lo = np.where(np.isfinite(lo), np.nan_to_num(lo, posinf=0.0, neginf=0.0) * f, lo); hi = np.where(np.isfinite(hi), np.nan_to_num(hi, posinf=0.0, neginf=0.0) * f, hi)
        A = np.zeros((len(self.rows), len(self.names)))
        for k, r in enumerate(self.rows):
            for j, v in r[0].items():
                A[k, j] += v
        return A, lo, hi, own

    def solve(self, S=None, lo_override=None, hi_override=None):
        A, lo, hi, own = self.arrays(S)
        if lo_override is not None:
            lo, hi = lo_override, hi_override
        eq = lo == hi; up = ~eq & np.isfinite(hi); dn = ~eq & np.isfinite(lo)
        A_ub = np.vstack([A[up], -A[dn]]); b_ub = np.concatenate([hi[up], -lo[dn]])
        r = linprog(self.c, A_ub=A_ub if len(b_ub) else None, b_ub=b_ub if len(b_ub) else None, A_eq=A[eq] if eq.any() else None,
                    b_eq=hi[eq] if eq.any() else None, bounds=list(zip(self.vlo, self.vhi)), method="highs")
        assert r.status == 0, r.message
        pi = np.zeros(len(lo)); mu = r.ineqlin.marginals
        pi[np.flatnonzero(up)] = mu[: up.sum()]; pi[np.flatnonzero(dn)] = -mu[up.sum():]
        if eq.any():
            pi[np.flatnonzero(eq)] = r.eqlin.marginals
        return dict(obj=float(r.fun), x=r.x, pi=pi, lo=lo, hi=hi, own=own, A=A)


W = np.array([2.0, 1.0, 1.0, 2.0])
D = {"A": [3, 4, 5, 4], "B": [6, 5, 7, 6], "C": [4, 6, 5, 5]}
AV = {"A": [0.9, 0.6, 0.3, 0.8], "B": [0.4, 0.7, 0.5, 0.3], "C": [0.2, 0.5, 0.9, 0.4]}
CG = {"A": 10.0, "B": 14.0, "C": 12.0}; GMAX = {"A": 20.0, "B": 6.0, "C": 5.0}; PIMP = {"A": 9.0, "B": 8.0, "C": 11.0}
CONST = {"A": 2.0, "B": 1.0, "C": 0.5, "A|C": 1.5}   # objective constants (existing FOM; sunk annuity of the existing A-C line)
KVL_BC = 1.0                                          # capacity of the existing B-C line of the KVL loop
BUNKER_PIMP, BUNKER_EFF, BUNKER_MCAP = 25.0, 0.9, 1.2  # bunker player: extra-regional fuel import price; A -> bunker metering link efficiency, capacity
BUNKER_D = [1.0, 2.0, 1.5, 1.0]


def toy(fmax_ab=2.0, duplicate_ab=False, shared_import_cap=None, kvl=False, bunker=None):
    """3 nodes, 4 weighted snapshots: renewables with potential, fixed-price imports, extendable line A-B, lossy one-way link B->C
    (efficiency 0.95), existing fixed line A-C (capacity 1, sunk constant). kvl: + existing line B-C (capacity KVL_BC) and the loop row
    f_AB + f_BC - f_AC = 0 per snapshot (unit reactances; homogeneous, lines of three owners: the KVL coupling of the model). bunker: + a 4th
    player BUNKER with no resource - only a demand bunker[t] at its own bus, supplied by a fixed-price extra-regional fuel import
    (BUNKER_PIMP) and from node A's market through a metering link (efficiency BUNKER_EFF, owned by A)."""
    L = LP(); T = range(4); ix = {}
    for i in P3:
        ix["G", i] = L.var(f"G_{i}", CG[i])
        for t in T:
            ix["g", i, t] = L.var(f"g_{i}_{t}", 0.1 * W[t]); ix["u", i, t] = L.var(f"u_{i}_{t}", PIMP[i] * W[t])
            ix["v", i, t] = L.var(f"v_{i}_{t}", 30.0 * W[t])   # expensive fixed-price backstop import (keeps every coalition LP feasible)
    ix["F", "AB"] = L.var("F_AB", 3.0); ix["F", "BC"] = L.var("F_BC", 2.0)
    for t in T:
        ix["f", "AB", t] = L.var(f"f_AB_{t}", 0.0, -np.inf, np.inf); ix["p", "BC", t] = L.var(f"p_BC_{t}", 0.05 * W[t])
        ix["f", "AC", t] = L.var(f"f_AC_{t}", 0.0, -np.inf, np.inf)
        if kvl:
            ix["f", "BC", t] = L.var(f"f_BC_{t}", 0.0, -np.inf, np.inf)
        if bunker is not None:
            ix["ub", t] = L.var(f"ub_{t}", BUNKER_PIMP * W[t]); ix["m", t] = L.var(f"m_{t}", 0.0)
    for i in P3:
        for t in T:
            inflow = {"A": {ix["f", "AB", t]: -1.0, ix["f", "AC", t]: -1.0}, "B": {ix["f", "AB", t]: 1.0, ix["p", "BC", t]: -1.0},
                      "C": {ix["p", "BC", t]: 0.95, ix["f", "AC", t]: 1.0}}[i]
            if kvl:
                inflow[ix["f", "BC", t]] = {"A": 0.0, "B": -1.0, "C": 1.0}[i]
            if bunker is not None and i == "A":
                inflow[ix["m", t]] = -1.0
            L.row({ix["g", i, t]: 1.0, ix["u", i, t]: 1.0, ix["v", i, t]: 1.0, **inflow}, D[i][t], D[i][t], i, f"bal_{i}_{t}")
            L.row({ix["g", i, t]: 1.0, ix["G", i]: -AV[i][t]}, -np.inf, 0.0, i, f"avail_{i}_{t}")
        L.row({ix["G", i]: 1.0}, -np.inf, GMAX[i], i, f"Gmax_{i}")
    for t in T:
        L.row({ix["f", "AB", t]: 1.0, ix["F", "AB"]: -1.0}, -np.inf, 0.0, "A|B"); L.row({ix["f", "AB", t]: -1.0, ix["F", "AB"]: -1.0}, -np.inf, 0.0, "A|B")
        L.row({ix["p", "BC", t]: 1.0, ix["F", "BC"]: -1.0}, -np.inf, 0.0, "B|C")
        L.row({ix["f", "AC", t]: 1.0}, -np.inf, 1.0, "A|C"); L.row({ix["f", "AC", t]: -1.0}, -np.inf, 1.0, "A|C")
        if kvl:
            L.row({ix["f", "BC", t]: 1.0}, -np.inf, KVL_BC, "B|C"); L.row({ix["f", "BC", t]: -1.0}, -np.inf, KVL_BC, "B|C")
            L.row({ix["f", "AB", t]: 1.0, ix["f", "BC", t]: 1.0, ix["f", "AC", t]: -1.0}, 0.0, 0.0, M.SHARED, f"kvl_{t}")   # homogeneous: no right
        if bunker is not None:
            L.row({ix["ub", t]: 1.0, ix["m", t]: BUNKER_EFF}, bunker[t], bunker[t], M.BUNKER, f"bal_BUNKER_{t}")
            L.row({ix["m", t]: 1.0}, -np.inf, BUNKER_MCAP, "A", f"mcap_{t}")   # the metering link is A's asset (its capacity is A's right)
    if duplicate_ab:   # the two half-rights as two identical rows, one per country (dual degeneracy made explicit)
        L.row({ix["F", "AB"]: 1.0}, -np.inf, fmax_ab, "A", "Fmax_AB_halfA"); L.row({ix["F", "AB"]: 1.0}, -np.inf, fmax_ab, "B", "Fmax_AB_halfB")
    else:
        L.row({ix["F", "AB"]: 1.0}, -np.inf, fmax_ab, "A|B", "Fmax_AB")
    L.row({ix["F", "BC"]: 1.0}, -np.inf, 10.0, "B|C", "Fmax_BC")
    if shared_import_cap is not None:   # an extra-regional import total cap that belongs to no player
        L.row({ix["u", i, t]: W[t] for i in P3 for t in T}, -np.inf, shared_import_cap, M.SHARED, "import_cap")
    return L, ix


def const_of(S, alpha):
    return sum(v for p, v in M.fold(CONST, alpha, P3).items() if p in S) if S is not None else sum(CONST.values())


def coalition_costs(L, alpha):
    return {S: L.solve(S)["obj"] + sum(s * v for k, v in CONST.items() for p, s in M.shares(k, alpha).items() if p in S) for S in M.coalitions(P3)}


def owen(sol, alpha):
    d = M.dual_form(sol["lo"], sol["hi"], sol["pi"], sol["own"])
    raw = dict(d["total"])
    for k, v in CONST.items():
        raw[k] = raw.get(k, 0.0) + v
    return M.fold(raw, alpha, P3), raw


def market_assets(L, ix, sol):
    """asset table of the market-settlement form from the toy solution (cost and nodal-dual value of every asset)."""
    x, pi = sol["x"], sol["pi"]; rid = {r[4]: k for k, r in enumerate(L.rows) if r[4]}
    bal = lambda i, t: pi[rid[f"bal_{i}_{t}"]]   # noqa: E731  (dual of the balance row = weight x nodal price)
    rows = []
    for i in P3:
        rows.append(dict(asset=f"gen_{i}", owner=i, cost=CG[i] * x[ix["G", i]] + sum(0.1 * W[t] * x[ix["g", i, t]] for t in range(4)),
                         value=sum(bal(i, t) * x[ix["g", i, t]] for t in range(4))))
        rows.append(dict(asset=f"imp_{i}", owner=i, cost=sum(PIMP[i] * W[t] * x[ix["u", i, t]] for t in range(4)), value=sum(bal(i, t) * x[ix["u", i, t]] for t in range(4))))
        rows.append(dict(asset=f"backstop_{i}", owner=i, cost=sum(30.0 * W[t] * x[ix["v", i, t]] for t in range(4)), value=sum(bal(i, t) * x[ix["v", i, t]] for t in range(4))))
        rows.append(dict(asset=f"load_{i}", owner=i, cost=0.0, value=-sum(bal(i, t) * D[i][t] for t in range(4))))
    rows.append(dict(asset="line_AB", owner="A|B", cost=3.0 * x[ix["F", "AB"]], value=sum((bal("B", t) - bal("A", t)) * x[ix["f", "AB", t]] for t in range(4))))
    rows.append(dict(asset="link_BC", owner="B|C", cost=2.0 * x[ix["F", "BC"]] + sum(0.05 * W[t] * x[ix["p", "BC", t]] for t in range(4)),
                     value=sum((0.95 * bal("C", t) - bal("B", t)) * x[ix["p", "BC", t]] for t in range(4))))
    rows.append(dict(asset="line_AC", owner="A|C", cost=0.0, value=sum((bal("C", t) - bal("A", t)) * x[ix["f", "AC", t]] for t in range(4))))
    if ("f", "BC", 0) in ix:
        rows.append(dict(asset="line_BC", owner="B|C", cost=0.0, value=sum((bal("C", t) - bal("B", t)) * x[ix["f", "BC", t]] for t in range(4))))
    if ("ub", 0) in ix:
        bb = lambda t: pi[rid[f"bal_BUNKER_{t}"]]   # noqa: E731
        rows.append(dict(asset="bunker_import", owner=M.BUNKER, cost=sum(BUNKER_PIMP * W[t] * x[ix["ub", t]] for t in range(4)), value=sum(bb(t) * x[ix["ub", t]] for t in range(4))))
        rows.append(dict(asset="bunker_meter", owner="A", cost=0.0, value=sum((BUNKER_EFF * bb(t) - bal("A", t)) * x[ix["m", t]] for t in range(4))))
        rows.append(dict(asset="bunker_load", owner=M.BUNKER, cost=0.0, value=-sum(bb(t) * BUNKER_D[t] for t in range(4))))
    rows += [dict(asset=f"const_{k}", owner=k, cost=v, value=0.0) for k, v in CONST.items()]
    return pd.DataFrame(rows)


def kvl_coalition_costs(L, alpha, physical):
    """coalition costs of the KVL toy. Matrix game (Owen): the same LP with b(S) - the loop row stays and a line outside S keeps zero
    capacity, so the loop forces zero flow on the remaining lines of the loop. Physical game (the leave-one-out variants): a line outside S is
    removed, the loop is broken and its KVL row disappears (the remaining lines are radial)."""
    kr = [k for k, r in enumerate(L.rows) if r[4].startswith("kvl_")]
    out = {}
    for S in M.coalitions(P3):
        _, loS, hiS, _ = L.arrays(S)
        if physical and not all(all(p in S for p in pr.split("|")) for pr in ("A|B", "B|C", "A|C")):
            loS = loS.copy(); hiS = hiS.copy(); loS[kr] = -np.inf; hiS[kr] = np.inf
        out[S] = L.solve(lo_override=loS, hi_override=hiS)["obj"] + sum(s * v for k, v in CONST.items() for p, s in M.shares(k, alpha).items() if p in S)
    return out


def test_toy_kvl_loop_dual_form_in_core_market_minus_dual_is_loop_transfer():
    """Supplement 01 D1: a homogeneous loop row (KVL type) with lines of three owners. The dual form y'b is in the core of the matrix game
    (Owen's theorem: coalitions = same LP with b(S)); the market-settlement form differs from it exactly by the loop transfer
    sum_t pi_kvl,t x coefficient x flow of every line, folded to the owners (zero-sum). Caveat (documented, not a model change): in the PHYSICAL
    game of the leave-one-out variants the loop of a coalition without one of its lines disappears; c_phys(S) <= c_matrix(S) and the dual form
    can leave that core ({A, B} here) - the leave-one-out check against variant runs is therefore a real test, not implied by the theorem."""
    L, ix = toy(kvl=True); sol = L.solve(); cN = sol["obj"] + sum(CONST.values())
    phi, raw = owen(sol, 0.5)
    assert abs(sum(phi[p] for p in P3) - cN) <= 1e-9 * cN and phi[M.SHARED] == 0.0           # the loop row has no right: y'b of it is 0
    cm = kvl_coalition_costs(L, 0.5, physical=False)
    assert abs(cm[frozenset(P3)] - cN) <= 1e-9 * cN
    assert M.core_violations({p: phi[p] for p in P3}, cm, tol=1e-7) == []                     # matrix game: in the core (theorem)
    st = M.settle(market_assets(L, ix, sol), 0.5, P3)
    kr = [k for k, r in enumerate(L.rows) if r[4].startswith("kvl_")]
    tr = {}
    for t, k in enumerate(kr):
        for name, own in (("AB", "A|B"), ("BC", "B|C"), ("AC", "A|C")):
            tr[own] = tr.get(own, 0.0) + sol["pi"][k] * L.rows[k][0][ix["f", name, t]] * sol["x"][ix["f", name, t]]
    trf = M.fold(tr, 0.5, P3)
    assert max(abs(sol["pi"][k]) for k in kr) > 1e-3 and max(abs(trf[p]) for p in P3) > 1.0   # the loop binds: a real transfer
    assert abs(sum(trf[p] for p in P3)) <= 1e-7 * cN                                          # zero-sum over the owners
    for p in P3:
        assert abs((st["allocation"][p] - phi[p]) - trf[p]) <= 1e-7 * cN                      # market - dual = loop transfer
    assert M.core_violations({p: st["allocation"][p] for p in P3}, cm, tol=1e-7) == []        # the market form is in the matrix core here too
    cp = kvl_coalition_costs(L, 0.5, physical=True)
    assert all(cp[S] <= cm[S] + 1e-9 for S in cm) and abs(cp[frozenset(P3)] - cN) <= 1e-9 * cN
    viol = M.core_violations({p: phi[p] for p in P3}, cp, tol=1e-7)
    assert [v["coalition"] for v in viol] == [["A", "B"]]                                     # the caveat: dual form outside the physical core


@pytest.mark.parametrize("alpha", [0.0, 0.5, 1.0])
def test_toy_owen_in_core_identity_and_market_form(alpha):
    L, ix = toy(); sol = L.solve()
    cN = sol["obj"] + sum(CONST.values())
    phi, raw = owen(sol, alpha)
    assert phi[M.SHARED] == 0.0
    assert abs(sum(phi[p] for p in P3) - cN) <= 1e-9 * cN                                  # identity (strong duality + constants)
    cost = coalition_costs(L, alpha)
    assert abs(cost[frozenset(P3)] - cN) <= 1e-9 * cN
    assert M.core_violations({p: phi[p] for p in P3}, cost, tol=1e-7) == []                 # Owen (1975): in the core, all 7 coalitions
    st = M.settle(market_assets(L, ix, sol), alpha, P3)                                    # market-settlement form = dual form
    for p in P3:
        assert abs(st["allocation"][p] - phi[p]) <= 1e-7 * cN
    rent = {k: -v for k, v in st["pairs"].items()}                                        # net rent = value - cost of every pair item
    assert rent["A|B"] > 1e-6                                                             # A-B cap binds: positive net rent to split
    loo = M.loo_check({p: phi[p] for p in P3}, cN, {i: cost[frozenset(P3) - {i}] for i in P3}, {})
    assert loo["all_passed"]                                                             # core implies phi_i >= c(N) - c(N - i)


def test_toy_alpha_changes_no_total_and_interval():
    L, ix = toy(); sol = L.solve(); cN = sol["obj"] + sum(CONST.values())
    tot = [sum(owen(sol, a)[0][p] for p in P3) for a in np.linspace(0, 1, 11)]
    assert max(tot) - min(tot) <= 1e-9 * cN
    st = M.settle(market_assets(L, ix, sol), 0.5, P3)
    for a in (0.0, 1.0):
        ph = owen(sol, a)[0]
        for p in P3:
            assert st["interval"][p]["min"] - 1e-9 <= ph[p] <= st["interval"][p]["max"] + 1e-9
    assert st["interval"]["A"]["width"] > 0 and st["interval"]["B"]["width"] > 0


def test_toy_dual_degeneracy_every_alpha_in_core():
    """C4.2: the A-B capacity right as two identical half-rows (one per country): any split of its shadow value is an optimal dual, the
    returned (vertex) split is one point of the interval, every alpha in [0, 1] is in the core, alphas far outside are not."""
    Ld, _ = toy(duplicate_ab=True); sd = Ld.solve(); L1, _ = toy(); s1 = L1.solve()
    assert abs(sd["obj"] - s1["obj"]) <= 1e-9 * abs(s1["obj"])
    rid = {r[4]: k for k, r in enumerate(Ld.rows) if r[4]}
    ya, yb = sd["pi"][rid["Fmax_AB_halfA"]], sd["pi"][rid["Fmax_AB_halfB"]]
    y = s1["pi"][[k for k, r in enumerate(L1.rows) if r[4] == "Fmax_AB"][0]]
    assert ya <= 0 and yb <= 0 and abs((ya + yb) - y) <= 1e-9 and y < -1e-6                 # binding right; the two halves share its value
    a_ret = ya / (ya + yb)
    assert 0.0 <= a_ret <= 1.0
    cost_d = {S: Ld.solve(S)["obj"] for S in M.coalitions(P3)}                             # coalition LPs of the explicit two-row form ...
    cost_1 = {S: L1.solve(S)["obj"] for S in M.coalitions(P3)}                             # ... equal those of the pair code (line open iff both in S)
    assert all(abs(cost_d[S] - cost_1[S]) <= 1e-9 * max(1.0, abs(cost_1[S])) for S in cost_1)
    # Owen with the returned duals of the two-row form = the pair form at alpha_ret (constants of A|C at the same alpha)
    raw_d = dict(M.dual_form(sd["lo"], sd["hi"], sd["pi"], sd["own"])["total"])
    for k, v in CONST.items():
        raw_d[k] = raw_d.get(k, 0.0) + v
    ph_d = M.fold(raw_d, {"A|C": a_ret, "B|C": a_ret, "A|B": a_ret}, P3)
    ph_1 = M.fold({**{k: v for k, v in owen(s1, a_ret)[1].items()}}, a_ret, P3)
    assert all(abs(ph_d[p] - ph_1[p]) <= 1e-7 for p in P3)
    for a in np.linspace(0.0, 1.0, 21):
        ph = owen(s1, a)[0]
        assert M.core_violations({p: ph[p] for p in P3}, coalition_costs(L1, a), tol=1e-7) == []
    out = [a for a in (-3.0, 4.0) if M.core_violations({p: owen(s1, a)[0][p] for p in P3}, coalition_costs(L1, a), tol=1e-7)]
    assert out, "an alpha far outside [0, 1] must leave the core (the interval is not vacuous)"


def test_toy_shared_rhs_breaks_attribution_until_assigned():
    """a right-hand side that belongs to no player (total extra-regional import cap) leaves a SHARED amount; once its RHS is assigned to
    players by fixed shares (coalition S gets the sum of its shares) the Owen allocation is in the core again."""
    L0, _ = toy(); base = L0.solve()
    used = sum(W[t] * base["x"][L0.names.index(f"u_{i}_{t}")] for i in P3 for t in range(4))
    cap = 0.7 * used
    L, _ = toy(shared_import_cap=cap); sol = L.solve(); cN = sol["obj"] + sum(CONST.values())
    phi, raw = owen(sol, 0.5)
    assert phi[M.SHARED] < -1e-6                                                           # the cap's rent is not a player's
    assert abs(sum(phi[p] for p in P3) + phi[M.SHARED] - cN) <= 1e-9 * cN
    wts = {"A": 0.2, "B": 0.5, "C": 0.3}                                                   # proposal: assign the cap by fixed shares
    raw2 = {k: v for k, v in raw.items() if k != M.SHARED}
    for p, s in wts.items():
        raw2[p] = raw2.get(p, 0.0) + s * raw[M.SHARED]
    phi2 = M.fold(raw2, 0.5, P3)
    A, lo, hi, own = L.arrays()
    k_cap = [k for k, r in enumerate(L.rows) if r[4] == "import_cap"][0]
    cost = {}
    for S in M.coalitions(P3):
        _, loS, hiS, _ = L.arrays(S); hiS = hiS.copy(); hiS[k_cap] = cap * sum(wts[p] for p in S)
        cost[S] = L.solve(lo_override=loS, hi_override=hiS)["obj"] + sum(s * v for k, v in CONST.items() for p, s in M.shares(k, 0.5).items() if p in S)
    assert abs(sum(phi2[p] for p in P3) - cN) <= 1e-9 * cN
    assert M.core_violations({p: phi2[p] for p in P3}, cost, tol=1e-7) == []


SMOKE = Path(os.environ.get("M12_SMOKE_DIR", str(ROOT / "results_project/s4o/s4o3/solves/s4o_integrated")))   # local 56x3h S4O-3 solve (git-ignored)


@pytest.mark.skipif(not (SMOKE / "integrated_SMOKE_TEST_ONLY_solved.nc").exists(), reason="local 56x3h smoke solve (results_project, git-ignored) not present")
def test_network_allocation_on_local_smoke(tmp_path):
    """market-settlement form on a real solved network: B16 identity, alpha 0.5 = the current ledger entity by entity, corridor table = the
    ledger's, totals independent of alpha, outputs registered in EXPORTS.json (copy of the run dir; the original is not touched)."""
    res = M.run(SMOKE / "integrated_SMOKE_TEST_ONLY_solved.nc", "integrated", tmp_path, SMOKE, "TEST", ROOT, register=True)
    assert res["computable"] and res["identity"]["passed"] and res["identity"]["relative_error_incl_shared"] <= 1e-9
    assert res["checks"]["ledger_alpha_half_max_abs_dev_eur"] <= 1e-3 and res["checks"]["corridor_table_max_abs_dev_eur"] <= 1e-3
    tot = [sum(v[p] for p in M.PLAYERS) for v in res["allocation_eur"].values()]
    assert max(tot) - min(tot) <= 1e-6 * abs(res["objective"])
    for p in M.PLAYERS:
        it = res["interval_eur"][p]
        assert it["min"] - 1e-3 <= res["allocation_eur"]["0"][p] <= it["max"] + 1e-3 and it["min"] - 1e-3 <= res["allocation_eur"]["1"][p] <= it["max"] + 1e-3
    ex = json.loads((tmp_path / "EXPORTS.json").read_text())
    assert {"ALLOCATION.json", "ALLOCATION.csv", "ALLOCATION.md", "ALLOCATION_LINES.csv"} <= set(ex)
    assert res["s4p_rules"]["applicable"]
    for c, v in res["s4p_rules"]["by_country_eur"].items():   # (ii) - its same-proportion counterpart = +/- half of the corridor infrastructure costs
        assert abs(v["ii_rent_to_importer_minus_same_proportion"] + v["iii_rent_to_exporter_minus_same_proportion"]) <= 1e-3


def test_loo_rhs_compare_merges_nodal_families(tmp_path):
    """C2: b(N - i) = b(N) on the remaining owners; a balance row that moves between the meshed and the plain nodal family is the same right."""
    import m12_rhs_audit as RA
    full = pd.DataFrame([("Bus-nodal_balance", "MY", 10.0, 4), ("Bus-meshed-nodal_balance", "MY", 5.0, 2), ("Generator-ext-p_nom-upper", "VN", 7.0, 1),
                         ("Line-ext-s_nom-upper", "MY|VN", 3.0, 1), ("Generator-ext-p_nom-upper", "MY", 2.0, 1)], columns=["family", "owner", "rhs_sum", "rows"])
    var = pd.DataFrame([("Bus-nodal_balance", "MY", 12.0, 5), ("Bus-meshed-nodal_balance", "MY", 3.0, 1), ("Generator-ext-p_nom-upper", "MY", 2.0, 1)], columns=full.columns)
    full.to_csv(tmp_path / "f.csv", index=False); var.to_csv(tmp_path / "v.csv", index=False)
    assert RA.loo_compare(tmp_path / "f.csv", tmp_path / "v.csv", ["VN"], tmp_path)["passed"]
    var.loc[2, "rhs_sum"] = 2.5                                                              # a remaining country's potential changed
    var.to_csv(tmp_path / "v.csv", index=False)
    r = RA.loo_compare(tmp_path / "f.csv", tmp_path / "v.csv", ["VN"], tmp_path)
    assert not r["passed"] and r["remaining_rights_changed_count"] == 1


@pytest.mark.skipif(not (SMOKE / "lp" / "clabels.npy").exists() or os.environ.get("PYTHONHASHSEED") != "0",
                    reason="local 56x3h smoke solve with exported arrays not present, or PYTHONHASHSEED != 0")
def test_rhs_audit_and_dual_form_on_local_smoke(tmp_path):
    """C2 on the real LP structure (built, not solved): every non-zero right-hand side has an owner; the only coupling family is the homogeneous
    KVL; the Owen dual form closes on the objective within the returned duality gap; market form - dual form = KVL transfer + KKT residuals."""
    import m12_rhs_audit as RA
    net = SMOKE.parents[3] / "s4m/s4m1/builds/integrated/integrated_2920_3h_unsolved.nc"
    if not net.exists():
        pytest.skip("smoke input network not present")
    al = M.run(SMOKE / "integrated_SMOKE_TEST_ONLY_solved.nc", "integrated", tmp_path / "a", SMOKE, "TEST", ROOT, register=False)
    r = RA.audit(ROOT, net, "integrated", tmp_path / "b", 56, None, SMOKE, tmp_path / "a" / "ALLOCATION.json", "TEST")
    p = r["owen_premise"]
    assert p["nonzero_rhs_rows_by_class"]["unresolved"] == 0 and p["nonzero_rhs_rows_by_class"]["shared"] == 0
    assert p["coupling_families_nonhomogeneous"] == [] and p["coupling_families_homogeneous"] == ["Kirchhoff-Voltage-Law"]
    d = r["dual_form"]
    assert abs(d["dual_total_minus_objective_eur"]) <= 1e-4 * abs(d["objective"])
    assert d["decomposition"]["check_max_abs_dev_eur"] <= 1e3
    kv = d["kvl_loop_transfer_alpha_half"]
    assert abs(sum(v for k, v in kv.items() if k in M.PLAYERS)) <= 1e6                         # loop transfers are zero-sum over the owners
    o = json.loads((tmp_path / "b" / "OWEN.json").read_text())                                 # supplement 01 D1: main value = dual form
    assert o["main_form"] == "owen_dual_form" and o["allocation_eur"]["0.5"] == d["allocation_alpha_half"]
    assert {"OWEN.csv", "OWEN.md"} <= {p.name for p in (tmp_path / "b").iterdir()}
    mm = o["market_minus_dual"]
    for p in M.PLAYERS:                                                                      # difference = KVL + residual (+ the decomposition's check deviation)
        assert abs(mm["total_eur"][p] - mm["kvl_loop_transfer_eur"].get(p, 0.0) - mm["residual_eur"][p] - mm["unexplained_eur"][p]) <= 1e-3
    assert o["identity"]["relative_error"] == abs(o["identity"]["players_sum"] - o["identity"]["objective"]) / abs(o["identity"]["objective"])
    ls = o["length_split_eur"]                                                                # D2: length split keeps the total, inside the interval
    assert abs(sum(ls[p] for p in M.PLAYERS) - sum(o["allocation_eur"]["0.5"][p] for p in M.PLAYERS)) <= 1e-6 * abs(o["identity"]["objective"])
    assert all(o["interval_eur"][p]["min"] - 1e-3 <= ls[p] <= o["interval_eur"][p]["max"] + 1e-3 for p in M.PLAYERS)


def _fake_audit(alloc: dict, shared_rows: int = 0) -> dict:
    """minimal audit result (dual form + premise) for owen_summary."""
    full = {p: float(alloc.get(p, 0.0)) for p in list(M.PLAYERS) + [M.SHARED]}
    nz = dict(country=10, cross_border_pair=1, bunker=1, shared=shared_rows, unresolved=0, country_split_by_load=0)
    return dict(tag="T", network="n.nc", network_sha256="0" * 64, shared_or_unresolved=[dict(constraint="import_cap", rows=shared_rows)] if shared_rows else [],
                owen_premise=dict(nonzero_rhs_rows_by_class=nz, passed=shared_rows == 0, coupling_families_homogeneous=["Kirchhoff-Voltage-Law"],
                                  coupling_families_nonhomogeneous=[]),
                dual_form=dict(allocation_by_alpha={"0": full, "0.5": full, "1": full}, allocation_alpha_half=full, source="fake",
                               interval={p: dict(min=full[p], max=full[p], width=0.0) for p in M.PLAYERS}, pair_values={}))


def test_proportional_rule_bases_d4(tmp_path):
    """Supplement 01 D4: (A) proportional split of B6 tested against the leave-one-out marginal contribution (benefit_i <= phi_i^disc - c'(i),
    i.e. payment_i >= c'(i), D8-adjusted c' preferred); (B) proportional split of the integrated total among the 11 countries tested for
    individual rationality (payment_i <= phi_i^disc)."""
    u = 1e10
    cI = {c: 10 * u for c in M.COUNTRIES} | {M.BUNKER: 5 * u}; cD = {c: 12 * u for c in M.COUNTRIES} | {"VN": 30 * u, M.BUNKER: 4 * u}
    I = _fake_alloc(tmp_path / "i", cI, sum(cI.values()), 0.0, cI); D = _fake_alloc(tmp_path / "d", cD, sum(cD.values()), 0.0, cD)
    lc = tmp_path / "LOO_CHECK.json"
    lc.write_text(json.dumps(dict(check=dict(countries=dict(VN=dict(marginal_cost=29 * u, marginal_cost_adjusted=30 * u), LA=dict(marginal_cost=0.0))))))
    r = M.benefit(I, D, tmp_path / "o", ROOT, loo_check=lc)
    b6 = sum(cD.values()) - sum(cI.values())
    assert r["loo_check_source"] == str(lc)
    for k, v in r["proportional"].items():
        A, B = v["A_split_b6"], v["B_split_total"]
        assert abs(sum(A["benefit_eur"].values()) - b6) <= 1e-6 * u and set(A["loo_check"]) == {"LA", "VN"}
        assert A["loo_check"]["VN"]["marginal_cost_eur"] == 30 * u and A["loo_check"]["VN"]["max_benefit_eur"] == 0.0   # adjusted c' used
        assert "VN" in A["loo_violations"] and "LA" not in A["loo_violations"]                    # VN may get no benefit at all; LA up to 12
        for c, x in A["loo_check"].items():
            assert x["passed"] == (x["benefit_eur"] <= x["max_benefit_eur"] + x["tolerance_eur"])
        assert abs(B["total_eur"] - (sum(cI.values()) - cI[M.BUNKER])) <= 1e-3 and abs(sum(B["payment_eur"].values()) - B["total_eur"]) <= 1e-3
        for c, x in B["ir_check"].items():
            assert x["passed"] == (x["payment_eur"] <= cD[c] + x["tolerance_eur"])
    assert "ID" in r["proportional"]["population_aeo8_d1"]["B_split_total"]["ir_violations"]   # ID's population share of the total > its disconnected cost
    assert r["owen_checks"]["loo"]["VN"]["passed"] is False and r["owen_checks"]["ir"]["VN"]["passed"]
    md = (tmp_path / "o" / "BENEFIT.md").read_text()
    assert "比例规则 (A)" in md and "比例规则 (B)" in md and "✗" in md
    r0 = M.benefit(I, D, tmp_path / "o0", ROOT)                                                 # no leave-one-out check: (A) not testable
    assert all(v["A_split_b6"]["loo_check"] == {} for v in r0["proportional"].values()) and r0["loo_check_source"] is None


def test_weights_same_source_as_model_d5():
    """Supplement 01 D5: main weights from the model's own sources - AEO8 D.1 population (TL UN WPP 2024 1,889,249.5), AEO8 D.2 GDP 2050 (the
    file of the M08b industry growth, byte-identical; TL = mean KH / LA / MM GDP per capita x TL population); SSP2 for comparison."""
    sw = M.socio_weights(ROOT)
    assert sw["d2_sha256"] == "9189d8621fa332edc31608f1e55df3e55ce2d5a4dc7afd11e8cbf235ca1ce793"
    pop, g = sw["population_aeo8_d1_m"], sw["gdp_aeo8_d2_musd2017ppp"]
    assert set(M.COUNTRIES) <= set(pop) and set(M.COUNTRIES) <= set(g)
    assert pop["VN"] == 107.0 and pop["ID"] == 317.2 and pop["TL"] == 1.8892495
    assert g["VN"] == 4207772.0 and g["BN"] == 34750.0
    assert abs(g["TL"] - np.mean([192464.0 / 20.3, 151898.0 / 9.8, 517199.0 / 59.9]) * 1.8892495) <= 1e-6
    assert M.WEIGHTS_MAIN[:2] == ("population_aeo8_d1", "gdp_aeo8_d2") and set(M.WEIGHTS_COMPARISON) == {"population_ssp2", "gdp_ppp_ssp2"}


def _fake_loo_runs(tmp_path, countries, obj_full=100e9, obj_minus=None):
    """full run (ALLOCATION.json + OWEN.json + SOLVE_RECEIPT.json + ALLOCATION_LINES.csv) and leave-one-out receipts; disconnected allocation."""
    a = {c: 8e9 for c in M.COUNTRIES} | {M.BUNKER: 12e9}
    F = _fake_alloc(tmp_path / "full", a, obj_full, 0.0, a, 0.0)
    rec = dict(objective=obj_full, solver_profile="formal_barrier", input_network=dict(snapshots=365), termination_condition="optimal")
    (F / "SOLVE_RECEIPT.json").write_text(json.dumps(rec))
    pd.DataFrame([dict(pair="LA|VN", fom_existing=4e6), dict(pair="LA|TH", fom_existing=2e6), dict(pair="KH|VN", fom_existing=1e6)]).to_csv(F / "ALLOCATION_LINES.csv", index=False)
    runs = {}
    for c in countries:
        d = tmp_path / f"full_minus{c}"; d.mkdir()
        (d / "SOLVE_RECEIPT.json").write_text(json.dumps(dict(rec, objective=(obj_minus or {}).get(c, obj_full - 7e9))))
        runs[c] = d
    S = _fake_alloc(tmp_path / "dis", {c: 9e9 for c in M.COUNTRIES} | {M.BUNKER: 11e9}, 110e9)
    return F, runs, S


def test_scrb_only_with_all_11_d6(tmp_path):
    """Supplement 01 D6: no SCRB with the three leave-one-out runs of the third batch (VN, TH, LA); automatic with all 11, noted as proxied."""
    F, runs, S = _fake_loo_runs(tmp_path, ("LA", "TH", "VN"))
    r = M.loo(F, runs, tmp_path / "o3", None, S)
    assert r["scrb"]["computed"] is False and r["scrb"]["runs"] == 3 and "all 11" in r["scrb"]["reason"]
    assert "有 11 次时自动给出" in (tmp_path / "o3" / "LOO_CHECK.md").read_text()
    F, runs, S = _fake_loo_runs(tmp_path / "x", M.COUNTRIES)
    r = M.loo(F, runs, tmp_path / "o11", None, S)
    assert r["scrb"]["computed"] and "proxy" in r["scrb"]["standalone_proxy"] and abs(sum(r["scrb"]["allocation_eur"].values()) - r["scrb"]["countries_cost_eur"]) <= 1e-3


def test_premise_failed_flag_d3(tmp_path):
    """Supplement 01 D3: a non-zero right-hand side without an owner (e.g. a future total cap on extra-ASEAN imports) sets owen_premise.passed
    False; the OWEN outputs are flagged premise_failed and not usable for the allocation even when the identity holds."""
    import m12_rhs_audit as RA
    a = {c: 1e9 for c in M.COUNTRIES} | {M.BUNKER: 2e9}
    ok = RA.owen_summary(_fake_audit(a), None, None, 13e9)
    assert ok["identity"]["passed"] and ok["premise"]["passed"] and not ok["premise_failed"] and ok["usable_for_allocation"]
    res = _fake_audit(a, shared_rows=3); res["owen"] = RA.owen_summary(res, None, None, 13e9)
    assert res["owen"]["premise_failed"] and not res["owen"]["usable_for_allocation"] and res["owen"]["identity"]["passed"]
    RA.write_owen(res, tmp_path)
    assert "premise_failed" in (tmp_path / "OWEN.md").read_text() and json.loads((tmp_path / "OWEN.json").read_text())["premise_failed"]


def test_dual_length_split_by_component():
    """Supplement 01 D2: the dual form's pair values split by the components' in-country length shares (a "-reversed" link takes its twin's
    share; a pair value not attributable to a component is split 0.5)."""
    import m12_rhs_audit as RA
    sh = pd.DataFrame([dict(component_type="Line", component="l1", country_a="VN", share_a=0.25, country_b="KH", share_b=0.75),
                       dict(component_type="Link", component="k1", country_a="KH", share_a=0.6, country_b="VN", share_b=0.4)])
    pc = {"Line:l1": dict(pair="KH|VN", eur=6.0), "Link:k1-reversed": dict(pair="KH|VN", eur=3.0), "Link:k2": dict(pair="KH|VN", eur=0.0)}
    r = RA.length_split({"KH": 1.0, "VN": 2.0, "KH|VN": 10.0}, pc, sh)
    assert abs(r["allocation"]["KH"] - (1.0 + 0.75 * 6 + 0.6 * 3 + 0.5 * 1.0)) <= 1e-12
    assert abs(r["allocation"]["VN"] - (2.0 + 0.25 * 6 + 0.4 * 3 + 0.5 * 1.0)) <= 1e-12
    assert r["by_pair"]["KH|VN"]["with_length_share"] == 2 and abs(r["by_pair"]["KH|VN"]["not_by_component_eur_split_half"] - 1.0) <= 1e-12


def _fake_alloc(d: Path, alloc: dict, obj: float, width: float = 0.0, owen: dict | None = None, owen_width: float = 0.0):
    """synthetic run dir: ALLOCATION.json (market form) and optionally m12_owen/OWEN.json (dual form); no network."""
    d.mkdir(parents=True, exist_ok=True)
    full = {p: float(alloc.get(p, 0.0)) for p in list(M.PLAYERS) + [M.SHARED]}
    iv = lambda a, w: {p: dict(min=a[p] - w, max=a[p] + w, width=2 * w) for p in M.PLAYERS}   # noqa: E731
    le = {c: {"electricity": 10.0 + i, "industry electricity": 2.0} for i, c in enumerate(M.COUNTRIES)}
    (d / "ALLOCATION.json").write_text(json.dumps(dict(computable=True, objective=obj, allocation_eur={"0": full, "0.5": full, "1": full}, interval_eur=iv(full, width),
                                                        report_currency=dict(fx_per_eur2020=1.139954), load_energy_twh=le, solved_network="fake", solved_network_sha256="0")))
    if owen is not None:
        fo = {p: float(owen.get(p, 0.0)) for p in list(M.PLAYERS) + [M.SHARED]}
        (d / "m12_owen").mkdir(exist_ok=True)
        (d / "m12_owen" / "OWEN.json").write_text(json.dumps(dict(main_form="owen_dual_form", allocation_eur={"0": fo, "0.5": fo, "1": fo}, interval_eur=iv(fo, owen_width),
                                                                  usable_for_allocation=True, identity=dict(passed=True))))
    return d


def test_benefit_main_value_is_dual_form(tmp_path):
    """Supplement 01 D1: the batch benefit uses the Owen dual form of both runs as the main value; the market form is reported alongside;
    without the dual form of one run the market form is the main value (flagged)."""
    cI = {c: 10.0 for c in M.COUNTRIES} | {M.BUNKER: 5.0}; cD = {c: 12.0 for c in M.COUNTRIES} | {M.BUNKER: 4.0}
    oI = dict(cI, VN=9.0, LA=11.0)                                                           # dual form: a KVL transfer of 1 between VN and LA
    I = _fake_alloc(tmp_path / "i", cI, sum(cI.values()), 0.5, oI, 0.1); D = _fake_alloc(tmp_path / "d", cD, sum(cD.values()), 0.0, cD, 0.0)
    r = M.benefit(I, D, tmp_path / "o", ROOT)
    assert r["main_form"] == "owen_dual_form"
    assert r["owen"]["benefit_eur"]["VN"] == 3.0 and r["owen"]["benefit_eur"]["LA"] == 1.0 and r["owen"]["benefit_eur"][M.BUNKER] == -1.0
    assert r["market_form"]["benefit_eur"]["VN"] == 2.0 and r["market_form"]["market_minus_main_benefit_eur"]["VN"] == -1.0
    assert abs(r["owen"]["benefit_interval_eur"]["VN"]["min"] - 2.9) <= 1e-12                # the dual form's interval, not the market form's
    (I / "m12_owen" / "OWEN.json").unlink()
    r2 = M.benefit(I, D, tmp_path / "o2", ROOT)
    assert r2["main_form"].startswith("market_settlement_form") and r2["owen"]["benefit_eur"]["VN"] == 2.0


def test_runner_hooks_after_c1_before_acceptance(tmp_path):
    """C3: m08a_run_batch.sh (third / fourth batch runner) runs the M12 allocation after C1 and registers it in EXPORTS.json before the GATES_V6
    acceptance; the batch benefit after the regrade; the leave-one-out hook once OUT/<tag>_minus<CC>/ exists. Synthetic stand-ins for the solve
    (tests/research/fixtures/m08a_fake_pipeline.py) - no solver."""
    import hashlib
    import subprocess
    fake = ROOT / "tests/research/fixtures/m08a_fake_pipeline.py"
    nets = tmp_path / "nets"; nets.mkdir(); out = tmp_path / "out"
    for sc in ("integrated", "disconnected"):
        for res in ("365_24h", "2920_3h"):
            (nets / f"{sc}_{res}_unsolved.nc").write_bytes(f"{sc}{res}".encode())
        (nets / f"{sc}_costs_active_research.csv").write_text("technology\n")
        (nets / f"{sc}_BUILD_RECEIPT.json").write_text(json.dumps(dict(network=dict(sha256=hashlib.sha256(f"{sc}2920_3h".encode()).hexdigest()),
                                                                     daily_network=dict(sha256=hashlib.sha256(f"{sc}365_24h".encode()).hexdigest(), snapshots=365))))
    py = sys.executable
    env = dict(os.environ, RUN_KIND="level2", REPO=str(ROOT), NETS=str(nets), OUT=str(out), PY=py, SOLVE_CMD=f"{py} {fake} solve", VA_CMD=f"{py} {fake} va",
               C1_CMD=f"{py} {fake} c1", VAR_CMD=f"{py} {fake} variants", FAKE_OBJ_formal_barrier="1e11", FAKE_OBJ_formal_barrier_1e6_t16="100000000400")
    env.pop("PYTHONHASHSEED", None)                                                          # the runner sets it for the variant generation itself
    p = subprocess.run(["bash", str(ROOT / "scripts_project/m08a_run_batch.sh")], env=env, capture_output=True, text=True, timeout=900)
    assert p.returncode == 0, p.stderr[-800:]
    st = (out / "STATUS.txt").read_text().splitlines()
    pos = lambda s: next(i for i, x in enumerate(st) if x.startswith(s))   # noqa: E731
    for tag in ("integrated_A", "disconnected_A", "integrated_CAND", "disconnected_CAND"):
        assert pos(f"C1_{tag}:") < pos(f"M12_{tag}:exit=0") < pos(f"V6_{tag}:")
        ex = json.loads((out / tag / "EXPORTS.json").read_text())
        assert {"ALLOCATION.json", "ALLOCATION.md"} <= set(ex)                               # registered (fake runs: no solved network -> not computable)
        assert json.loads((out / tag / "V6_ACCEPTANCE.json").read_text())["label"] == "ACCEPTED_LAYER2" if tag.endswith("CAND") else True
    assert pos("REFERENCE_A:") < pos("M12_LOO_integrated_A:exit=0:runs=3") < pos("M12_BENEFIT_A:exit=0:loo_check=2") < pos("V6_integrated_A:")
    assert json.loads((out / "M12_BENEFIT_A" / "BENEFIT.json").read_text())["computable"] is False
    # supplement 01 D7: variants generated in the run from the 365x24h integrated base (no stale switch), solved once each with profile A
    calls = (out / "CALLS.txt").read_text().splitlines()
    cpos = lambda s: calls.index(s)   # noqa: E731
    assert cpos("solve disconnected_A formal_barrier 21600") < cpos("variant VN stale=False") < cpos("solve integrated_A_minusVN formal_barrier 21600") \
        < cpos("solve integrated_A_minusLA formal_barrier 21600") < cpos("solve integrated_CAND formal_barrier_1e6_t16 21600")
    assert "REFERENCE_A:done:loo_regraded=3" in st and all(f"regrade integrated_A_minus{c}" in calls for c in ("VN", "TH", "LA"))
    for c in ("VN", "TH", "LA"):
        rc = json.loads((out / "variants" / f"integrated_minus{c}_365_24h_VARIANT_RECEIPT.json").read_text())
        net = out / "variants" / f"integrated_minus{c}_365_24h_unsolved.nc"
        assert rc["output"]["sha256"] == hashlib.sha256(net.read_bytes()).hexdigest() and f"VARIANT_{c}:sha256={rc['output']['sha256']}" in st
        r = json.loads((out / f"integrated_A_minus{c}" / "SOLVE_RECEIPT.json").read_text())
        assert r["input_network"]["path"] == str(net) and r["costs_table"].endswith("integrated_costs_active_research.csv")
        acc = json.loads((out / f"integrated_A_minus{c}" / "V6_ACCEPTANCE.json").read_text())
        assert acc["label"] == "ACCEPTED_LAYER2" and acc["G2"]["G2_1"]["registered_sha256"] == rc["output"]["sha256"]
        assert pos(f"M12_integrated_A_minus{c}:exit=0") < pos("REFERENCE_A:")
    assert not any(x.startswith("solve integrated_CAND_minus") for x in calls)                # profile A only


def test_scrb_and_proportional_sum_to_total():
    L, _ = toy(); cost = coalition_costs(L, 0.5); cN = cost[frozenset(P3)]
    marg = {i: cN - cost[frozenset(P3) - {i}] for i in P3}; alone = {i: cost[frozenset({i})] for i in P3}
    s = M.scrb(cN, alone, marg)
    assert abs(sum(s.values()) - cN) <= 1e-9 * cN
    pr = M.proportional(10.0, {"A": 1, "B": 3, "C": 1})
    assert pr == {"A": 2.0, "B": 6.0, "C": 2.0}
