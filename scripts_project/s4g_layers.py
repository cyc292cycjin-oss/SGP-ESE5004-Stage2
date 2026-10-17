"""S4G model layers (S4G instruction v1, 2026-10-17; decisions 98-99).

S4G-1 (decision 98): research.network.readjust_impedance = pypsa_eur (main) | author (the author's parameters, comparison; default when absent).
  pypsa_eur applies research.network.readjust_impedance_table (READJUST_IMPEDANCE_S4G1.csv, scripts_project/s4g_1_data.py) to the 19 cross-border
  AC lines whose s_nom the author's readjust_existing_interconnections set to the AIMS 2024 totals: num_parallel = s_nom / (sqrt3 x v_nom x i_nom)
  (PyPSA-Earth base_network / simplify_network relation; line 91 with the S4F 80 MW), x / r / b by the PyPSA 0.30.3 line-type formulas
  (pf.apply_line_types - the values PyPSA recomputes at every optimisation, stored as well so that the network file agrees). s_nom, s_nom_min,
  length and cost are unchanged; the individual extension limit stays s_nom + 20,000 MW. Applied after the corridor candidates are added (their
  template line - the existing cross-border line closest to the median num_parallel - keeps the frozen values) and checked line by line against
  the frozen-base values first. The disconnected scenario removes these lines later as before.
S4G-2 (decision 99 b): research.co2.lao_transit_th_store = on (main config) - effective only with research.co2.lao_transit_destination =
  existing_port: LA nodes whose transit ends at a Thai coastal node get '<node> co2 transit to TH store' into 'co2 sequestered TH' by the rule of
  decision 97 c (land leg on the link, carrier 'CO2 transit rail', trade class; Thai store cost and annual cap on the store). With the main
  nearest_coast destination every transit ends in Viet Nam and nothing is added.
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _flag(v, allowed, key):
    v = {True: "on", False: "off"}.get(v, v) if isinstance(v, bool) else str(v).lower()
    if v not in allowed:
        raise ValueError(f"Unknown {key} {v}")
    return v


def readjust_impedance_mode(cfg) -> str:
    return _flag((cfg["research"].get("network") or {}).get("readjust_impedance", "author"), ("pypsa_eur", "author"), "research.network.readjust_impedance")


def apply_readjust_impedance(n, cfg, repo: Path = ROOT) -> dict:
    """S4G-1 (decision 98): see the module docstring."""
    mode = readjust_impedance_mode(cfg); led = dict(mode=mode)
    if mode == "author":
        n.meta["research_readjust_impedance"] = led
        return led
    path = str(cfg["research"]["network"]["readjust_impedance_table"])
    t = pd.read_csv(repo / path, dtype={"line": str})
    lt = n.line_types; rows = []
    for _, r in t.iterrows():
        k = r.line
        if k not in n.lines.index:
            raise ValueError(f"readjust impedance: line {k} not in the network")
        z = n.lines.loc[k]
        # s_nom: the table value (S4F-corrected for line 91) or, with research.network.th_my_stock = frozen_base, the frozen value
        s_ok = [s for s in (float(r.s_nom_used_mw), float(r.s_nom_frozen_mw)) if abs(float(z.s_nom) - s) < 1e-6 and abs(float(z.s_nom_min) - s) < 1e-6]
        checks = dict(type=str(z.type) == str(r["type"]), length=abs(float(z.length) - float(r.length_km)) < 1e-6,
                      num_parallel=abs(float(z.num_parallel) - float(r.num_parallel_frozen)) < 1e-9 * max(1.0, float(r.num_parallel_frozen)),
                      x=abs(float(z.x) - float(r.x_stored_frozen)) < 1e-9 * max(1.0, float(r.x_stored_frozen)), s_nom=bool(s_ok))
        if not all(checks.values()):
            raise ValueError(f"readjust impedance: line {k} differs from the frozen values {[c for c, ok in checks.items() if not ok]}")
        t_ = lt.loc[z.type]; v = float(n.buses.at[z.bus0, "v_nom"])
        npar = float(z.s_nom) / (math.sqrt(3) * v * float(t_.i_nom))
        if abs(float(z.s_nom) - float(r.s_nom_used_mw)) < 1e-6 and abs(npar - float(r.num_parallel_s4g)) > 1e-9 * max(1.0, npar):
            raise ValueError(f"readjust impedance: line {k} num_parallel {npar} differs from the table {r.num_parallel_s4g}")
        x = float(t_.x_per_length) * float(z.length) / npar; rr = float(t_.r_per_length) * float(z.length) / npar
        b = 2 * math.pi * 1e-9 * float(t_.f_nom) * float(t_.c_per_length) * float(z.length) * npar
        rows.append(dict(line=k, s_nom=float(z.s_nom), num_parallel_before=float(z.num_parallel), num_parallel_after=npar, x_before=float(z.x), x_after=x, r_before=float(z.r), r_after=rr,
                         b_before=float(z.b), b_after=b))
        n.lines.loc[k, ["num_parallel", "x", "r", "b"]] = [npar, x, rr, b]
    led.update(table=path, lines=len(rows), rows=rows)
    n.meta["research_readjust_impedance"] = led
    return led


def lao_th_store_mode(cfg) -> str:
    return _flag((cfg["research"].get("co2") or {}).get("lao_transit_th_store", "off"), ("on", "off"), "research.co2.lao_transit_th_store")


def apply_lao_th_store(n, cfg, registry: pd.DataFrame) -> dict:
    """S4G-2 (decision 99 b): see the module docstring."""
    from s2_layers import add_link
    from s4e_layers import lao_transit_legs, lao_transit_options
    from s4f_layers import TRANSIT_RAIL_CARRIER
    mode = lao_th_store_mode(cfg); dest, tmode = lao_transit_options(cfg); led = dict(mode=mode, destination=dest, links=0)
    if mode == "off" or dest != "existing_port":
        led["note"] = "nothing added (switch off or destination nearest_coast)"
        n.meta["research_lao_th_store"] = led
        return led
    if "co2 sequestered TH" not in n.buses.index or not ((n.stores.carrier == "co2 sequestered") & (n.stores.country == "TH")).any():
        raise ValueError("research.co2.lao_transit_th_store needs the Thai national store")
    legs = lao_transit_legs(cfg, registry); years = float(cfg["research"]["s2"]["co2"]["storage_years"]); rows = []
    for node, g in sorted(legs.items()):
        if f"{node} co2 stored" not in n.buses.index or str(n.buses.at[g["coastal_node"], "country"]) != "TH":
            continue
        add_link(n, f"{node} co2 transit to TH store", "LA", TRANSIT_RAIL_CARRIER, [f"{node} co2 stored", "co2 sequestered TH"], [1.0], capital_cost=0.0,
                 marginal_cost=g["land_cost"], lifetime=years, role="CO2_TRANSIT",
                 extra={"via_coastal_node": g["coastal_node"], "land_leg_eur_per_t": g["land_cost"], "trade_class": "land transit trade (decision 99 b)",
                        "carbon_rule": "transited captured CO2 counts as abatement of LA (decision 20); stored in the Thai national store, inside its annual cap (decision 28)"})
        rows.append(dict(node=node, via=g["coastal_node"], land=g["land_cost"], mode=tmode))
    led.update(links=len(rows), table=rows)
    n.meta["research_lao_th_store"] = led
    return led
