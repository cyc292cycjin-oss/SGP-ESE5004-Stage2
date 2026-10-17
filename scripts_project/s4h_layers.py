"""S4H model layers (S4H instruction v1, 2026-10-17; decisions 100-101).

S4H-1 (decision 100): research.network.la_vn_stock = aims_zero (main) | author (the S4G state, comparison; default when absent).
  aims_zero applies research.network.la_vn_stock_table (LA_VN_STOCK_S4H1.csv): the LA-VN grid-to-grid stock is 0 (AIMS; author script comment
  "no grid-to-grid connections in 2024"); the four clustered LA-VN lines 59 / 60 / 63 / 64 become zero-capacity candidate lines - s_nom = s_nom_min
  = 0, extendable, individual limit 0 + 20,000 MW (decision 96, applied later), length / unit cost / subsea share unchanged (the decision-50 cost
  layer prices them like every other extendable AC line), border_class cross_border (removed in the disconnected scenario), num_parallel / x / r /
  b by the candidate convention (apply_candidate_num_parallel). The corridor table is corrected the same way in memory (capacity 0).
S4H-2 (decision 101): research.corridors.candidate_num_parallel = one_circuit (main) | template43 (former convention, comparison; default when
  absent). Every zero-capacity AC candidate line (S4E-1 adjacency candidates, APG11, the four LA-VN lines of S4H-1, the S4H-2 completion lines)
  gets num_parallel = 1 (one circuit of the 380 kV representative type) - template43 keeps the num_parallel of the corridor-candidate template
  (line 43, frozen 1.286); x / r / b by the PyPSA line-type formulas (pf.apply_line_types), stored so that the network file agrees with the values
  PyPSA recomputes. PyPSA-Eur has no zero-capacity AC candidate lines (PyPSA-Earth's augmented connections are DC links); this is the model's
  convention - AC is kept because 380 kV interconnections on one landmass are subject to Kirchhoff's voltage law.
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PREFIXES = ("S4E1 ", "S4H2 ", "APG11_TH_MM")


def _flag(v, allowed, key):
    v = str(v).lower()
    if v not in allowed:
        raise ValueError(f"Unknown {key} {v}")
    return v


def la_vn_stock_mode(cfg) -> str:
    return _flag((cfg["research"].get("network") or {}).get("la_vn_stock", "author"), ("aims_zero", "author"), "research.network.la_vn_stock")


def apply_la_vn_stock(n, corridors: pd.DataFrame, cfg, repo: Path = ROOT):
    """S4H-1 (decision 100): returns (corridor table, ledger). Checks the stock values first (s_nom, s_nom_min, length, type)."""
    mode = la_vn_stock_mode(cfg); led = dict(mode=mode)
    if mode == "author":
        n.meta["research_la_vn_stock"] = led
        return corridors, led
    path = str(cfg["research"]["network"]["la_vn_stock_table"])
    t = pd.read_csv(repo / path, dtype={"component": str}, float_precision="round_trip")
    corridors = corridors.copy(); rows = []
    for _, r in t.iterrows():
        k = str(r.component)
        if k not in n.lines.index:
            raise ValueError(f"LA-VN stock: line {k} not in the network")
        z = n.lines.loc[k]; c = {str(n.buses.at[z.bus0, "country"]), str(n.buses.at[z.bus1, "country"])}
        checks = dict(pair=c == {"LA", "VN"}, s_nom=abs(float(z.s_nom) - float(r.s_nom_author_mw)) < 1e-9 * max(1.0, float(r.s_nom_author_mw)),
                      s_nom_min=abs(float(z.s_nom_min) - float(r.s_nom_author_mw)) < 1e-9 * max(1.0, float(r.s_nom_author_mw)),
                      length=abs(float(z.length) - float(r.length_km)) < 1e-6, type=str(z.type) == str(r["type"]), extendable=bool(z.s_nom_extendable))
        if not all(checks.values()):
            raise ValueError(f"LA-VN stock: line {k} differs from the table {[c_ for c_, ok in checks.items() if not ok]}")
        n.lines.loc[k, ["s_nom", "s_nom_min"]] = 0.0
        sel = (corridors.component_type == "Line") & (corridors.component.astype(str) == k)
        if int(sel.sum()) != 1:
            raise ValueError(f"LA-VN stock: corridor row of line {k} not unique")
        corridors.loc[sel, ["capacity_2025_mw", "nominal_mw_in_base"]] = 0.0
        rows.append(dict(line=k, s_nom_before=float(r.s_nom_author_mw), s_nom_after=0.0, length_km=float(z.length), capital_cost_eur_per_mw_a=float(z.capital_cost)))
    led.update(table=path, rows=rows, stock_before_mw=float(sum(x["s_nom_before"] for x in rows)), stock_after_mw=0.0)
    n.meta["research_la_vn_stock"] = led
    return corridors.reset_index(drop=True), led


def candidate_np_mode(cfg) -> str:
    return _flag((cfg["research"].get("corridors") or {}).get("candidate_num_parallel", "template43"), ("one_circuit", "template43"),
                 "research.corridors.candidate_num_parallel")


def apply_candidate_num_parallel(n, cfg) -> dict:
    """S4H-2 a (decision 101): see the module docstring. Call after every candidate is added and after apply_la_vn_stock."""
    mode = candidate_np_mode(cfg)
    add = n.meta.get("apg_corridor_additions") or []
    tmpl_np = next((float(x["num_parallel"]) for x in add if x.get("num_parallel") is not None), None)
    target = 1.0 if mode == "one_circuit" else tmpl_np
    if target is None:
        raise ValueError("candidate num_parallel: no corridor-candidate template recorded")
    la_vn = {x["line"] for x in (n.meta.get("research_la_vn_stock") or {}).get("rows", [])}
    cand = n.lines[(n.lines.s_nom == 0) & (n.lines.s_nom_min == 0) & n.lines.s_nom_extendable]
    unknown = [k for k in cand.index if not (str(k).startswith(CANDIDATE_PREFIXES) or k in la_vn)]
    if unknown:
        raise ValueError(f"candidate num_parallel: zero-capacity lines outside the candidate sets {unknown[:5]}")
    lt = n.line_types; rows = []; unchanged = 0
    for k, z in cand.iterrows():
        if k not in la_vn and abs(float(z.num_parallel) - target) <= 1e-12 * target:
            unchanged += 1; continue   # already on the convention (template43: the S4E-1 / APG11 values are kept bit for bit)
        t = lt.loc[z.type]; L = float(z.length)
        x = float(t.x_per_length) * L / target; r = float(t.r_per_length) * L / target
        b = 2 * math.pi * 1e-9 * float(t.f_nom) * float(t.c_per_length) * L * target
        rows.append(dict(line=str(k), num_parallel_before=float(z.num_parallel), num_parallel_after=target, x_before=float(z.x), x_after=x))
        n.lines.loc[k, ["num_parallel", "x", "r", "b"]] = [target, x, r, b]
    led = dict(mode=mode, num_parallel=target, template_num_parallel=tmpl_np, template_line=next((x.get("template_line") for x in add if x.get("template_line")), None),
               candidates=int(len(cand)), changed=len(rows), unchanged=unchanged, la_vn_lines=sorted(la_vn), type=sorted(set(cand.type)), rows=rows)
    n.meta["research_candidate_num_parallel"] = led
    return led
