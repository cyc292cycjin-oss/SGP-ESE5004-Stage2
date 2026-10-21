"""M12 C4.1 / C4.2 (item 133): Owen allocation on toy 3-country LPs solved with scipy linprog (HiGHS) - no model network, no Gurobi.

Toy linear production game: every right-hand side belongs to a player (demand rows, potentials, line half-rights); a cross-border line is two
halves (its rows carry the pair code "A|B" and are open only if both countries are in the coalition); extra-regional imports at fixed prices;
objective constants (sunk costs) belong to players, a cross-border constant split with the same alpha as the line's rent. All 7 coalition LPs
are solved explicitly: the Owen allocation is in the core, the identity holds, alpha changes no total; the market-settlement form (asset cost +
net purchases at the nodal duals - net rent share) equals the dual form y' b; every alpha in [0, 1] of the degenerate half-line rows is in the core."""
from __future__ import annotations

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


def toy(fmax_ab=2.0, duplicate_ab=False, shared_import_cap=None):
    """3 nodes, 4 weighted snapshots: renewables with potential, fixed-price imports, extendable line A-B, lossy one-way link B->C
    (efficiency 0.95), existing fixed line A-C (capacity 1, sunk constant)."""
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
    for i in P3:
        for t in T:
            inflow = {"A": {ix["f", "AB", t]: -1.0, ix["f", "AC", t]: -1.0}, "B": {ix["f", "AB", t]: 1.0, ix["p", "BC", t]: -1.0},
                      "C": {ix["p", "BC", t]: 0.95, ix["f", "AC", t]: 1.0}}[i]
            L.row({ix["g", i, t]: 1.0, ix["u", i, t]: 1.0, ix["v", i, t]: 1.0, **inflow}, D[i][t], D[i][t], i, f"bal_{i}_{t}")
            L.row({ix["g", i, t]: 1.0, ix["G", i]: -AV[i][t]}, -np.inf, 0.0, i, f"avail_{i}_{t}")
        L.row({ix["G", i]: 1.0}, -np.inf, GMAX[i], i, f"Gmax_{i}")
    for t in T:
        L.row({ix["f", "AB", t]: 1.0, ix["F", "AB"]: -1.0}, -np.inf, 0.0, "A|B"); L.row({ix["f", "AB", t]: -1.0, ix["F", "AB"]: -1.0}, -np.inf, 0.0, "A|B")
        L.row({ix["p", "BC", t]: 1.0, ix["F", "BC"]: -1.0}, -np.inf, 0.0, "B|C")
        L.row({ix["f", "AC", t]: 1.0}, -np.inf, 1.0, "A|C"); L.row({ix["f", "AC", t]: -1.0}, -np.inf, 1.0, "A|C")
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
    rows += [dict(asset=f"const_{k}", owner=k, cost=v, value=0.0) for k, v in CONST.items()]
    return pd.DataFrame(rows)


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


def test_scrb_and_proportional_sum_to_total():
    L, _ = toy(); cost = coalition_costs(L, 0.5); cN = cost[frozenset(P3)]
    marg = {i: cN - cost[frozenset(P3) - {i}] for i in P3}; alone = {i: cost[frozenset({i})] for i in P3}
    s = M.scrb(cN, alone, marg)
    assert abs(sum(s.values()) - cN) <= 1e-9 * cN
    pr = M.proportional(10.0, {"A": 1, "B": 3, "C": 1})
    assert pr == {"A": 2.0, "B": 6.0, "C": 2.0}
