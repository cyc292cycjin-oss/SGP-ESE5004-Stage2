"""M12 C1 (item 133): Owen (1975) allocation of the system cost to the 11 countries and the international-bunker account (12th player, item 91).
READ ONLY - Python only, no solver call; the solve results are not changed.

Principle (linear production game, Owen 1975). The integrated LP  min c'x  s.t.  l <= Ax <= u  has right-hand sides that belong to players
(demand at a bus, resource potentials, fixed capacities, country caps). With b(S) = sum_{i in S} b_i the coalition LP has the same matrix and
the dual y* of the grand LP prices every player's rights and obligations; phi_i = y*' b_i + (player's objective constants) is in the core:
phi(S) = y*' b(S) <= max_y {y' b(S): y dual feasible} = c(S) (weak duality), phi(N) = c(N) (strong duality). Cost version used here
(market-settlement form, equal to y*' b_i when every non-nodal row lies inside one player and the KKT conditions hold exactly):

    phi_i = cost of player i's assets (annuity, FOM, VOM, fuel, extra-ASEAN imports, objective constants)
            + value at the nodal duals of the player's net purchases - net sales (every carrier, every bus)
            - sum over cross-border assets l touching i of  s_{l,i} x (rent_l - annuity_l),   s_{l,i} = alpha or 1 - alpha

Premises (checked by m12_rhs_audit.py): every right-hand side belongs to a player; a cross-border line is two halves, each country owning its
half (both halves have the full rating, so the line exists only if both countries take part); extra-ASEAN trade at fixed prices; the bunker
demand belongs to no country and is the 12th player. Dual degeneracy: two half-rows with the same coefficients carry any split of the line's
shadow value, so every alpha in [0, 1] is an optimal dual (all in the core); reported as an interval, main value alpha = 0.5 (the central split of
the interior-point solution: the analytic centre of the optimal dual face is symmetric in two identical rows). Same-proportion rule: annuity
(investment) and congestion rent of a line are split with the same alpha, i.e. its NET rent is split.

Owner codes used throughout: a country code ("VN"), a sorted pair for cross-border items ("KH|VN", first country gets alpha), "BUNKER", and
"SHARED" for right-hand sides / assets that belong to no player (reported separately, never folded into a player silently).

    PYTHONHASHSEED=0 python scripts_project/m12_allocation.py run --repo . --solved <dir>/<scenario>_solved.nc --scenario integrated --out <dir>
            [--solve-dir <dir>] [--label L] [--alpha 0.5]
    python scripts_project/m12_allocation.py benefit --integrated <dir> --disconnected <dir> --out <dir> [--repo .]
    python scripts_project/m12_allocation.py loo --full <dir> --loo VN=<dir> [--loo TH=<dir> ...] --out <dir> [--reference <json>]
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

SCRIPT = "scripts_project/m12_allocation.py"
COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
BUNKER = "BUNKER"
SHARED = "SHARED"
PLAYERS = COUNTRIES + (BUNKER,)
B16_TOL = 1e-6                      # GATES_V6 G1c / B16: ledger identity relative error
ALPHA_MAIN = 0.5
ALPHA_GRID = (0.0, 0.5, 1.0)


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ----------------------------------------------------------------------------------------------------------------------------- owner codes / alpha
def pair(a: str, b: str) -> str:
    """owner code of an item between a and b: the country itself when equal, else the sorted pair "A|B"."""
    return a if a == b else "|".join(sorted((a, b)))


def shares(owner: str, alpha=ALPHA_MAIN) -> dict:
    """player shares of an owner code; alpha = share of the FIRST country of a sorted pair (scalar, or dict pair -> alpha)."""
    if "|" in owner:
        a, b = owner.split("|")
        al = float(alpha.get(owner, ALPHA_MAIN) if isinstance(alpha, dict) else alpha)
        return {a: al, b: 1.0 - al}
    return {owner: 1.0}


def fold(raw: dict, alpha=ALPHA_MAIN, players=PLAYERS) -> dict:
    """fold amounts by owner code into players (+ SHARED for anything that is not a player or a pair of players)."""
    out = {p: 0.0 for p in players}
    out[SHARED] = 0.0
    for k, v in raw.items():
        for p, s in shares(str(k), alpha).items():
            out[p if p in out and p != SHARED else SHARED] += s * float(v)
    return out


def alpha_interval(raw_excl_pairs: dict, pair_amounts: dict, players=PLAYERS) -> dict:
    """per-player range of the allocation over independent alpha_l in [0, 1] for every pair item.

    pair_amounts: {"A|B": amount added to the players' allocations (cost - value = - net rent)}. Player p's allocation is
    base_p + sum_l s_{l,p} amount_l with s in [0, 1]; the extremes of different players are not reached at the same alphas."""
    base = fold(raw_excl_pairs, ALPHA_MAIN, players)
    lo = dict(base); hi = dict(base)
    for k, v in pair_amounts.items():
        for p in str(k).split("|"):
            if p in lo:
                lo[p] += min(float(v), 0.0); hi[p] += max(float(v), 0.0)
    return {p: dict(min=lo[p], max=hi[p], width=hi[p] - lo[p]) for p in players}


# ----------------------------------------------------------------------------------------------------------------------------- dual form y' b
def dual_form(lo, hi, pi, owners, col_lo=None, col_hi=None, rc=None, col_owners=None) -> dict:
    """Owen dual form: sum of multiplier x active bound by owner code (EUR, objective units).

    Rows l <= a x <= u with multiplier pi (min problem: pi > 0 on the lower side, pi < 0 on the upper side; equality rows either). The
    active bound is l for pi > 0 and u for pi < 0; a multiplier on an infinite side (dual sign error of an interior point) contributes 0 and
    is reported as sign_error. Column bounds the same with the reduced costs rc. Returns dict(rows=..., columns=..., sign_error=...)."""
    def part(lo_, hi_, mu, own):
        lo_ = np.asarray(lo_, float); hi_ = np.asarray(hi_, float); mu = np.asarray(mu, float); own = np.asarray(own, dtype=object)
        b = np.where(mu > 0, lo_, np.where(mu < 0, hi_, 0.0))
        bad = ~np.isfinite(b)
        term = np.where(bad, 0.0, mu * np.where(bad, 0.0, b))
        s = pd.Series(term).groupby(own).sum()
        err = pd.Series(np.where(bad, np.abs(mu), 0.0)).groupby(own).sum()
        return {str(k): float(v) for k, v in s.items() if v != 0.0}, {str(k): float(v) for k, v in err.items() if v != 0.0}
    rows, err_r = part(lo, hi, pi, owners)
    cols, err_c = ({}, {}) if rc is None else part(col_lo, col_hi, rc, col_owners)
    tot = dict(rows)
    for k, v in cols.items():
        tot[k] = tot.get(k, 0.0) + v
    return dict(rows=rows, columns=cols, total=tot, sign_error_rows=err_r, sign_error_columns=err_c)


# ----------------------------------------------------------------------------------------------------------------------------- market-settlement form
def settle(assets: pd.DataFrame, alpha=ALPHA_MAIN, players=PLAYERS) -> dict:
    """market-settlement form from an asset table (one row per asset / load / constant).

    Columns: owner (code), cost (EUR, objective units incl. constants), value (EUR: sum over its buses and snapshots of
    nodal dual x injection; loads negative), value_own (part of value at buses of the same owner), value_foreign (rest).
    Allocation of an owner code = cost - value; pairs folded with alpha (same alpha for annuity and rent)."""
    net = (assets["cost"] - assets["value"]).groupby(assets["owner"].astype(str)).sum()
    raw = {str(k): float(v) for k, v in net.items()}
    alloc = fold(raw, alpha, players)
    pairs = {k: v for k, v in raw.items() if "|" in k}
    single = {k: v for k, v in raw.items() if "|" not in k}
    return dict(raw_by_owner=raw, allocation=alloc, pairs=pairs, interval=alpha_interval(single, pairs, players))


# ----------------------------------------------------------------------------------------------------------------------------- game checks
def coalitions(players) -> list:
    ps = list(players)
    return [frozenset(c) for r in range(1, len(ps) + 1) for c in itertools.combinations(ps, r)]


def core_violations(alloc: dict, cost: dict, tol: float = 0.0) -> list:
    """coalitions S whose allocation exceeds their own cost: sum_{i in S} phi_i - c(S) > tol (cost game core: phi(S) <= c(S))."""
    out = []
    for S, cS in cost.items():
        ex = sum(alloc[i] for i in S) - cS
        if ex > tol:
            out.append(dict(coalition=sorted(S), excess=float(ex)))
    return out


def loo_check(alloc: dict, c_full: float, c_loo: dict, tol: dict) -> dict:
    """leave-one-out: c'(i) = c(N) - c(N - i); core implies phi_i >= c'(i). tol = per-country threshold (bn or EUR, same unit)."""
    rows = {}
    for i, cNi in sorted(c_loo.items()):
        cp = c_full - cNi
        rows[i] = dict(c_N_minus_i=float(cNi), marginal_cost=float(cp), allocation=float(alloc[i]), margin=float(alloc[i] - cp),
                       tolerance=float(tol.get(i, 0.0)), passed=bool(alloc[i] - cp >= -float(tol.get(i, 0.0))))
    sum_marg = float(sum(v["marginal_cost"] for v in rows.values()))
    return dict(countries=rows, sum_marginal_costs=sum_marg, indivisible_cost=float(c_full - sum_marg),
                indivisible_cost_sign=("positive" if c_full - sum_marg > 0 else "negative" if c_full - sum_marg < 0 else "zero"),
                all_passed=bool(all(v["passed"] for v in rows.values())))


def scrb(c_full: float, standalone: dict, marginal: dict) -> dict:
    """separable costs - remaining benefits: phi_i = c'(i) + (c(i) - c'(i)) / sum_j (c(j) - c'(j)) x (c(N) - sum_j c'(j)); remaining
    benefits clipped at 0 (standard SCRB)."""
    nonsep = c_full - sum(marginal.values())
    rb = {i: max(standalone[i] - marginal[i], 0.0) for i in marginal}
    tot = sum(rb.values())
    return {i: float(marginal[i] + (rb[i] / tot * nonsep if tot > 0 else nonsep / len(marginal))) for i in marginal}


def proportional(total: float, weights: dict) -> dict:
    w = {k: float(v) for k, v in weights.items()}
    s = sum(w.values())
    return {k: total * v / s for k, v in w.items()}
