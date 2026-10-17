"""S4D model layers (S4D instruction v1, 2026-10-17; decisions 91-93).

S4D-1 (decision 93; coastal rule: user decision 2026-10-17 on stop report S4D_STOP_01, option A with the physical coastline):
  * export_nodes_mode: research.co2.extra_asean_export_nodes = coastal (main: the extra-ASEAN export links of S4C-4 only at the coastal nodes
    of research.co2.coastal_nodes_table, research_inputs/co2_v5/COASTAL_NODES_S4D1_FINAL.csv; inland captured CO2 reaches the coast through
    the domestic CO2 pipeline candidates, decision 35, endogenous in both scenarios) | all (S4C-4 behaviour; default when the key is absent).
  * transit_mode: research.co2.landlocked_transit = on (main: for the landlocked country LA one transit export link per buffered node,
    '<node> co2 transit export extra-ASEAN', from '<node> co2 stored' to 'co2 sequestered extra-ASEAN LA'; marginal cost = land leg by rail to
    the nearest neighbouring coast, registry co2_lao_transit_land_cost_<node> (Stolaroff et al. 2021 Table 2, grade C +-50 %); the store keeps
    the extra-ASEAN unit cost, so the total per tonne = land leg + co2_extra_asean_storage_cost; treated like the liquid-fuel transit of
    decision 44 - trade, not cross-border network; both scenarios) | off (default when the key is absent). Only with export nodes = coastal.
  The links are added inside s4c_layers.apply_extra_asean_storage (before tag_cross_border: both ends are buses of the exporting country).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

TRANSIT_LINK = "CO2 transit export extra-ASEAN"
LANDLOCKED = ("LA",)
ROOT = Path(__file__).resolve().parents[1]


def _co2(cfg) -> dict:
    return cfg["research"].get("co2", {}) or {}


def export_nodes_mode(cfg) -> str:
    v = str(_co2(cfg).get("extra_asean_export_nodes", "all")).lower()
    if v not in ("coastal", "all"):
        raise ValueError("Unknown research.co2.extra_asean_export_nodes " + v)
    return v


def transit_mode(cfg) -> str:
    v = _co2(cfg).get("landlocked_transit", "off")
    v = {True: "on", False: "off"}.get(v, v) if isinstance(v, bool) else str(v).lower()
    if v not in ("on", "off"):
        raise ValueError("Unknown research.co2.landlocked_transit " + str(v))
    if v == "on" and export_nodes_mode(cfg) != "coastal":
        raise ValueError("research.co2.landlocked_transit = on requires research.co2.extra_asean_export_nodes = coastal")
    return v


def coastal_table(cfg) -> tuple[pd.Series, Path]:
    """node -> coastal (bool) from research.co2.coastal_nodes_table."""
    p = ROOT / str(_co2(cfg).get("coastal_nodes_table", "research_inputs/co2_v5/COASTAL_NODES_S4D1_FINAL.csv"))
    t = pd.read_csv(p)
    return t.set_index("node").coastal.astype(bool), p


def transit_cost_id(node: str) -> str:
    return "co2_lao_transit_land_cost_" + node.replace(" ", "_")
