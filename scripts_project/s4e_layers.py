"""S4E model layers (S4E instruction v1, 2026-10-17; decisions 94-95).

S4E-1 (decision 94, implementing decision 15): research.corridors.adjacency_completion = on (main) | off (default when absent: the original
corridor table). With on, the corridor table is research.corridors.corridors_table_s4e1 (cross_border_corridors.csv + the S4E-1 candidates:
land-adjacent node pairs as AC lines, APG AIMS III cross-sea projects #4 / #7 / #16 as DC links; scripts_project/s4e_1_corridors.py) and the
domestic candidates of research.corridors.domestic_table_s4e1 (APG national projects #3 / #18a / #18b, DC links) are added in both scenarios.
Every candidate starts at capacity 0 and is extendable; the 2025 stock rows are unchanged. AC rows absent from the frozen base are added by
s2_layers.add_apg_corridor_lines (base conventions); DC rows by add_corridor_dc_links with the conventions of the frozen base's AC-to-AC DC link
(HVDC XLPE 1000, bidirectional, lossless as in the base); the decision-50 cost layer (S4C-1) prices both from length and subsea share
(research.corridors.subsea_table). H2 / CO2 / gas candidates follow the electricity topology (decision 59). The disconnected scenario removes
every cross-border line / link as before (apply_cross_border_switches_s2).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DC_TEMPLATE = "1076672675-1_0+4"   # frozen-base DC link between two AC buses (PH_Mindanao6 0 - PH_Visayas7 0)


def corridor_mode(cfg) -> str:
    v = (cfg["research"].get("corridors") or {}).get("adjacency_completion", "off")
    v = {True: "on", False: "off"}.get(v, v) if isinstance(v, bool) else str(v).lower()
    if v not in ("on", "off"):
        raise ValueError("Unknown research.corridors.adjacency_completion " + str(v))
    return v


def corridor_tables(cfg) -> tuple[str, str | None]:
    """(corridor table, domestic candidate table or None), paths relative to the repository."""
    R = cfg["research"]; C = R.get("corridors") or {}
    if corridor_mode(cfg) == "on":
        return str(C["corridors_table_s4e1"]), str(C["domestic_table_s4e1"])
    return str(R["existing_cross_border_electricity"]["corridors_file"]), None


def _dc_template(n):
    dc = n.links[n.links.carrier == "DC"]
    if DC_TEMPLATE in dc.index:
        return dc.loc[DC_TEMPLATE]
    return dc.iloc[0]


def _add_dc(n, name, bus0, bus1, length, cap, subsea, tmpl):
    cpk = float(tmpl.capital_cost) / float(tmpl.length)
    n.add("Link", name, bus0=bus0, bus1=bus1, carrier="DC", type=str(tmpl.get("type", "")), length=float(length), p_nom=float(cap), p_nom_min=float(cap),
          p_nom_extendable=True, p_min_pu=-1.0, efficiency=float(tmpl.efficiency), capital_cost=cpk * float(length), lifetime=float(tmpl.lifetime), build_year=0)
    if "underwater_fraction" in n.links.columns:
        n.links.at[name, "underwater_fraction"] = float(subsea)
    return dict(component=name, bus0=bus0, bus1=bus1, length_km=float(length), capacity_2025_mw=float(cap), subsea_share=float(subsea),
                placeholder_capital_cost_eur_per_mw_a=cpk * float(length), template_link=str(tmpl.name))


def add_corridor_dc_links(n, corridors: pd.DataFrame) -> list:
    """Corridor-table rows of type Link (carrier DC) absent from the network -> DC links (S4E-1 cross-sea candidates)."""
    tmpl = _dc_template(n); added = []
    for _, r in corridors.iterrows():
        if r.component_type != "Link" or str(r.component) in n.links.index:
            continue
        if str(r.carrier) != "DC":
            raise ValueError(f"corridor row {r.component}: only DC links can be added")
        added.append(_add_dc(n, str(r.component), r["from"], r["to"], r.length_km, r.capacity_2025_mw, r.subsea_share, tmpl) | dict(status=str(r.status)))
    n.meta["s4e_corridor_dc_additions"] = added
    return added


def add_domestic_candidates(n, table: pd.DataFrame) -> list:
    """S4E-1 item 4: domestic candidates (both scenarios) - DC links for node pairs on different landmasses; AC rows use the cross-border AC
    conventions (s2_layers.add_apg_corridor_lines)."""
    from s2_layers import add_apg_corridor_lines
    if (table.country_from != table.country_to).any():
        raise ValueError("domestic candidate table holds a cross-border row")
    tmpl = _dc_template(n); added = []
    for _, r in table.iterrows():
        if str(r.component) in n.links.index or str(r.component) in n.lines.index:
            raise ValueError(f"domestic candidate {r.component} already in the network")
        if r.component_type == "Link":
            added.append(_add_dc(n, str(r.component), r["from"], r["to"], r.length_km, r.capacity_2025_mw, r.subsea_share, tmpl) | dict(status=str(r.status)))
    lines = table[table.component_type == "Line"]
    if len(lines):
        keep = n.meta.get("apg_corridor_additions")
        added += add_apg_corridor_lines(n, lines)
        n.meta["apg_corridor_additions"] = keep
    n.meta["s4e_domestic_additions"] = added
    return added
