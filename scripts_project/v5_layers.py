"""V5 X20 build layers (decisions 241, 244, 246; research/06_scope_redesign/p1_v5_x20_20261111/X20_SPEC.md, X20_SPEC_ADDENDUM_246.md). Every layer
returns at once with research.demand.v5 disabled (v5_common.V5_OFF), so a v5-off build equals the 26c2e47d build.

  gem_node_override        2-6  checked coordinates of GEM additions (GEM_COORD_CORRECTIONS_V5.csv): node of the units whose node changes
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from v5_common import switches

ROOT = Path(__file__).resolve().parents[1]
GEM_COORD_TABLE = "research_inputs/fleet_v5/GEM_COORD_CORRECTIONS_V5.csv"


def gem_node_override(df: pd.DataFrame, cfg, repo: Path = ROOT) -> tuple[pd.DataFrame, list]:
    """2-6 (decision 244): node of the GEM addition rows whose checked coordinate moves them (GEM_COORD_CORRECTIONS_V5.csv node_changes = True;
    scripts_project/v5_gem_coord_data.py). The row node must be the table's GEM node, otherwise the build stops."""
    s = switches(cfg)
    if s["gem_coord_fix"] != "verified":
        return df, []
    t = pd.read_csv(Path(repo) / GEM_COORD_TABLE, dtype={"gem_unit_id": str})
    t = t[t.node_changes.astype(str).str.lower() == "true"]
    moved = []
    df = df.copy()
    for r in t.itertuples():
        m = df.gem_unit_id.astype(str) == r.gem_unit_id
        if not m.any():
            raise ValueError(f"GEM coordinate correction: unit {r.gem_unit_id} not in the GEM addition tables")
        if not (df.loc[m, "node"] == r.gem_node).all():
            raise ValueError(f"GEM coordinate correction: unit {r.gem_unit_id} node {df.loc[m, 'node'].tolist()} differs from the table {r.gem_node}")
        df.loc[m, "node"] = r.checked_node
        moved.append(dict(gem_unit_id=r.gem_unit_id, plant=r.plant, mw=float(df.loc[m, "capacity_mw"].sum()), node_from=r.gem_node, node_to=r.checked_node))
    return df, moved
