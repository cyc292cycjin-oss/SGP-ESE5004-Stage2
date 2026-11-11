"""V5 X20 build layers (decisions 241, 244, 246; research/06_scope_redesign/p1_v5_x20_20261111/X20_SPEC.md, X20_SPEC_ADDENDUM_246.md). Every layer
returns at once with research.demand.v5 disabled (v5_common.V5_OFF), so a v5-off build equals the 26c2e47d build.

  gem_node_override        2-6  checked coordinates of GEM additions (GEM_COORD_CORRECTIONS_V5.csv): node of the units whose node changes
  apply_offwind_premium    1-3  ASEAN capital-cost premium on extendable offshore wind (after cost layer, cost scaling and typhoon premium)
  apply_solar_cap_scale    1-4  country factor on the ground-mounted solar caps (MY / ID / VN) and the MY open-forest / oil-palm variants
  operating_share          1-5  share of a hydro component's capacity operating in 2025 (identities of existing_unit_components; s4c_layers)
  hydro_spill_tables / hydro_spill_report  1-5  bookkeeping part and true spill of a solved network (s2_solve HYDRO_SPILL.json, v5_hydro_spill.py)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
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
    g = n.generators; out = {}
    cty = g.bus.map(n.buses.country) if any(f != 1.0 for f in fac.values()) else None   # all factors 1 (main): nothing to map
    for c, f in fac.items():
        if f == 1.0:
            continue
        sel = g.index[(g.carrier == "solar") & g.p_nom_extendable & (cty == c)]
        before = float(g.loc[sel, "p_nom_max"].sum())
        n.generators.loc[sel, "p_nom_max"] = g.loc[sel, "p_nom_max"] * f
        out[c] = dict(factor=f, generators=int(len(sel)), p_nom_max_before_mw=before, p_nom_max_after_mw=float(n.generators.loc[sel, "p_nom_max"].sum()))
    led["by_country"] = out
    return led


def operating_share(n, component: str, p_nom: float, year: int = 2025) -> tuple[float, str]:
    """1-5 (decision 241; Q14): operating share of an existing hydro / ror component = capacity of its identities (n.meta existing_unit_components) that
    are operating with commissioning year <= 2025 (frozen-base author units carry no GEM status: operating) / capacity of all its identities. A component
    without identities (e.g. the V4 D2a PHS-reclassified conventional part) counts as operating. Returns (share, basis)."""
    ids = [z for z in (n.meta.get("existing_unit_components") or {}).values() if z.get("component") == component]
    if not ids:
        return 1.0, "no identity: operating"
    tot = sum(float(z.get("capacity_mw", 0.0)) for z in ids)
    if tot <= 0:
        return 1.0, "identities without capacity: operating"

    def op(z):
        st = z.get("gem_status"); cy = z.get("commissioning_year")
        return (st in (None, "", "operating")) and (cy in (None, "") or float(cy) <= year)
    o = sum(float(z.get("capacity_mw", 0.0)) for z in ids if op(z))
    return o / tot, f"{sum(1 for z in ids if op(z))} of {len(ids)} identities operating (<= {year})"


def hydro_spill_tables(su: pd.DataFrame, inflow: pd.DataFrame, spill: pd.DataFrame, w, country: pd.Series, built_min_mw: float = 1.0) -> dict:
    """1-5 (decision 241): spill of a solved network split into the bookkeeping part and the true spill (X03 section 5.4 definitions).
    New-build reservoirs (carrier 'hydro'): the inflow of the full cap p_nom_max is given and research_new_hydro_inflow forces spill + r p_nom >= inflow,
    so the inflow of the unbuilt part is reported as spill - bookkeeping = sum_x sum_t w inflow_x,t (1 - built_x / p_nom_max_x), built = p_nom_opt
    (0 below built_min_mw); true spill = reported spill - bookkeeping. Existing reservoirs ('hydro existing'): reported spill = true spill. TWh."""
    w = np.asarray(w, dtype=float)
    out, tot = {}, dict(new_inflow_full_cap_twh=0.0, new_spill_reported_twh=0.0, new_spill_bookkeeping_twh=0.0, new_spill_true_twh=0.0, existing_spill_twh=0.0)
    e = lambda df, x: float((df[x].values * w).sum()) / 1e6 if x in df.columns else 0.0   # noqa: E731
    for c in sorted(set(country.reindex(su.index).dropna())):
        s = su[country.reindex(su.index) == c]
        new = s.index[s.carrier == "hydro"]; ex = s.index[s.carrier == "hydro existing"]
        built = s.loc[new, "p_nom_opt"].where(s.loc[new, "p_nom_opt"] >= built_min_mw, 0.0)
        book = sum(e(inflow, x) * (1.0 - float(built[x]) / float(s.at[x, "p_nom_max"])) for x in new if float(s.at[x, "p_nom_max"]) > 0)
        r = dict(new_inflow_full_cap_twh=sum(e(inflow, x) for x in new), new_spill_reported_twh=sum(e(spill, x) for x in new), new_spill_bookkeeping_twh=book,
                 existing_spill_twh=sum(e(spill, x) for x in ex), new_built_mw=float(built.sum()), new_cap_mw=float(s.loc[new, "p_nom_max"].sum()))
        r["new_spill_true_twh"] = r["new_spill_reported_twh"] - book
        out[c] = r
        for k in tot:
            tot[k] += r[k]
    return dict(rule="bookkeeping = sum inflow x (1 - built / p_nom_max) of the new-build reservoirs (built < %.1f MW = 0); true = reported - bookkeeping; TWh" % built_min_mw,
                totals=tot, by_country=out, all_reported_spill_twh=float((spill.values * w[:, None]).sum()) / 1e6 if spill.shape[1] else 0.0)


def hydro_spill_report(n) -> dict:
    """1-5: HYDRO_SPILL.json of a solved network (s2_solve.post_solve, research.demand.v5.enabled)."""
    su = n.storage_units
    rep = hydro_spill_tables(su, n.storage_units_t.inflow, n.storage_units_t.spill, n.snapshot_weightings.generators.values, su.bus.map(n.buses.country))
    rep["new_hydro_inflow_tie_units"] = sorted(n.meta.get("research_new_hydro_inflow_tie", []))
    return rep
