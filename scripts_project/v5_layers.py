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


OFFSHORE = ("offwind-ac", "offwind-dc", "offwind-float")


def apply_offwind_premium(n, cfg) -> dict:
    """1-3 (decision 241): research.demand.v5.offwind_asean_premium_pct (0 main | 10 | 20 | 30) on the capital cost of every extendable offshore wind
    generator (offwind-ac / -dc / -float, all countries, asset_role existing_survivor excluded; the whole capital cost incl. station and connection, as
    the typhoon premium s4b_layers.py:116). Called after the cost layer, research.cost_scaling and the typhoon premium (s2_network), so the factors
    multiply; pct = 0 leaves the network bit-identical."""
    s = switches(cfg); pct = float(s["offwind_asean_premium_pct"]); led = dict(pct=pct, order="after cost layer, cost_scaling and typhoon premium (multiplicative)")
    if not s["enabled"] or pct == 0.0:
        led.update(generators=0)
        return led
    g = n.generators
    role = g["asset_role"].astype(str) if "asset_role" in g.columns else pd.Series("", index=g.index)
    sel = g.index[g.carrier.isin(OFFSHORE) & g.p_nom_extendable & (role != "existing_survivor")]
    before = g.loc[sel, "capital_cost"].copy()
    n.generators.loc[sel, "capital_cost"] = before * (1.0 + pct / 100.0)
    led.update(generators=int(len(sel)), capital_cost_before_sum=float(before.sum()), capital_cost_after_sum=float(n.generators.loc[sel, "capital_cost"].sum()),
               by_country={str(c): int(k) for c, k in g.loc[sel, "bus"].map(n.buses.country).value_counts().items()})
    return led


SOLAR_MY_VARIANTS = "research_inputs/renewable_v5/SOLAR_MY_LANDUSE_VARIANTS_V5.csv"


def apply_solar_cap_scale(n, cfg, repo: Path = ROOT) -> dict:
    """1-4 (decision 241; Q15 (a)): country factor on p_nom_max of the ground-mounted solar candidates (carrier 'solar', extendable) -
    research.demand.v5.solar_cap_scale_MY / _ID / _VN (1.0 main | 0.5 | 2) times, for MY, the land-use variant factor of solar_landuse_my
    (lc100 main = 1 | open_forest | oil_palm, SOLAR_MY_LANDUSE_VARIANTS_V5.csv, scripts_project/v5_solar_my_variants_data.py; the country
    increment spread pro rata over the MY node caps). Called after apply_solar_density and before the class split
    (s4a_layers.apply_renewable_profiles), so every class keeps its share. Rooftop and existing PV unchanged; all factors 1 -> no change."""
    s = switches(cfg); led = dict(scale={c: float(s[f"solar_cap_scale_{c}"]) for c in ("MY", "ID", "VN")}, landuse_my=s["solar_landuse_my"])
    if not s["enabled"]:
        return led
    fac = dict(led["scale"])
    if s["solar_landuse_my"] != "lc100":
        v = pd.read_csv(Path(repo) / SOLAR_MY_VARIANTS).set_index("variant")
        led["variant_factor"] = float(v.at[s["solar_landuse_my"], "factor"]); fac["MY"] = fac["MY"] * led["variant_factor"]
        import hashlib
        led["variant_table"] = dict(path=SOLAR_MY_VARIANTS, sha256=hashlib.sha256((Path(repo) / SOLAR_MY_VARIANTS).read_bytes()).hexdigest())
    g = n.generators; cty = g.bus.map(n.buses.country)
    out = {}
    for c, f in fac.items():
        if f == 1.0:
            continue
        sel = g.index[(g.carrier == "solar") & g.p_nom_extendable & (cty == c)]
        before = float(g.loc[sel, "p_nom_max"].sum())
        n.generators.loc[sel, "p_nom_max"] = g.loc[sel, "p_nom_max"] * f
        out[c] = dict(factor=f, generators=int(len(sel)), p_nom_max_before_mw=before, p_nom_max_after_mw=float(n.generators.loc[sel, "p_nom_max"].sum()))
    led["by_country"] = out
    return led
