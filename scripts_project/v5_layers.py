"""V5 X20 build layers (decisions 241, 244, 246; research/06_scope_redesign/p1_v5_x20_20261111/X20_SPEC.md, X20_SPEC_ADDENDUM_246.md). Every layer
returns at once with research.demand.v5 disabled (v5_common.V5_OFF), so a v5-off build equals the 26c2e47d build.

  gem_node_override        2-6  checked coordinates of GEM additions (GEM_COORD_CORRECTIONS_V5.csv): node of the units whose node changes
  apply_offwind_premium    1-3  ASEAN capital-cost premium on extendable offshore wind (after cost layer, cost scaling and typhoon premium)
  apply_solar_cap_scale    1-4  country factor on the ground-mounted solar caps (MY / ID / VN) and the MY open-forest / oil-palm variants
  operating_share          1-5  share of a hydro component's capacity operating in 2025 (identities of existing_unit_components; s4c_layers)
  hydro_spill_tables / hydro_spill_report  1-5  bookkeeping part and true spill of a solved network (s2_solve HYDRO_SPILL.json, v5_hydro_spill.py)
  hydro_candidate_unit_inflow C-1 per-MW annual inflow of the new-build hydro / ror candidates (decision 252; HYDRO_CANDIDATE_UNIT_INFLOW_V5.csv; s4c_layers)
  apply_onwind_reference_level  X21 sensitivity (decision 253): onshore candidate p_max_pu x 1 / (v5 / reference) per country, capped at 1 (off in the main set)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from v5_common import switches

ROOT = Path(__file__).resolve().parents[1]
GEM_COORD_TABLE = "research_inputs/fleet_v5/GEM_COORD_CORRECTIONS_V5.csv"
HYDRO_CANDIDATE_TABLE = "research_inputs/hydro_v5/HYDRO_CANDIDATE_UNIT_INFLOW_V5.csv"
ONWIND_REFERENCE_TABLE = "research_inputs/renewable_v5/ONWIND_REFERENCE_LEVEL_FACTORS_V5.csv"


def apply_onwind_reference_level(n, cfg, repo: Path = ROOT, profile_variant: str | None = None) -> dict:
    """X21 sensitivity switch (decision 253; research.demand.v5.onwind_reference_level): gwa_reference = every extendable onshore-wind candidate ('onwind',
    p_nom_extendable) of country c gets p_max_pu(t) x factor_c, capped at 1 per snapshot, factor_c = 1 / (v5 / reference) of ONWIND_REFERENCE_LEVEL_FACTORS_V5.csv
    (reference = GWA IEC3 gross / r, X20 ONWIND_SANITY rule; scripts_project/v5_onwind_reference_data.py). Existing wind is not changed. The table was derived for
    one profile variant; another variant stops the build. disabled (main) = no change. Returns the ledger (per country: candidates, factor, CF before / after,
    share of capped snapshot values)."""
    s = switches(cfg)
    if not s["enabled"] or s["onwind_reference_level"] == "disabled":
        return dict(switch=s["onwind_reference_level"], applied=False)
    from v5_common import sha256
    p = Path(repo) / ONWIND_REFERENCE_TABLE
    t = pd.read_csv(p, keep_default_na=False)
    var = set(t.profile_variant.astype(str))
    if profile_variant is not None and var != {profile_variant}:
        raise ValueError(f"onwind_reference_level gwa_reference: the factor table belongs to {sorted(var)}, the network uses {profile_variant}")
    fac = {r.country: float(r.factor) for r in t.itertuples()}
    g = n.generators
    cty = g.bus.map(n.buses.country) if "country" in n.buses else g.bus.astype(str).str[:2]
    cand = g.index[(g.carrier == "onwind") & g.p_nom_extendable]
    P = n.generators_t.p_max_pu; w = n.snapshot_weightings.generators
    led = dict(switch=s["onwind_reference_level"], applied=True, table=ONWIND_REFERENCE_TABLE, sha256=sha256(p), profile_variant=sorted(var), countries={})
    for c, names in pd.Series(cand, index=cand).groupby(cty.reindex(cand)):
        if c not in fac:
            raise ValueError(f"onwind_reference_level gwa_reference: no factor for {c}, but {c} has onshore candidates")
        cols = [x for x in names if x in P.columns]
        before = P[cols].copy()
        P[cols] = (before * fac[c]).clip(upper=1.0)
        cap = g.loc[cols, "p_nom_max"].replace(np.inf, np.nan).fillna(0.0)
        cf = lambda D: float(((D.mul(w, axis=0).sum() / w.sum()) * cap).sum() / cap.sum()) if cap.sum() > 0 else float("nan")   # noqa: E731
        led["countries"][str(c)] = dict(candidates=len(cols), factor=fac[c], cf_before=cf(before), cf_after=cf(P[cols]),
                                        capped_share=float(((before * fac[c]) > 1.0).to_numpy().mean()) if len(cols) else 0.0)
    n.generators_t.p_max_pu = P
    return led


def hydro_candidate_unit_inflow(repo: Path = ROOT, multiplier_one: bool = False) -> dict:
    """C-1 (decision 252; L-C10): per-MW annual inflow u_c (MWh / MW / a) of the new-build hydro and ror candidates = national target (Ember median x 1.1,
    the existing stock's target) / national hydro capacity of the same basis (Ember median, IHA 2024 where Ember has none); one rule for the 11 countries
    (scripts_project/v5_hydro_unit_inflow_data.py). multiplier_one (research.demand.v5.hydro_inflow_multiplier 1.0) divides by the table multiplier as for
    the stock. Only REGISTERED rows carry a value. Returns dict(u={country: MWh/MW/a}, cf={country: cf}, source={country: capacity source}, table, sha256)."""
    from v5_common import sha256
    p = Path(repo) / HYDRO_CANDIDATE_TABLE
    t = pd.read_csv(p, keep_default_na=False)
    t = t[t.status == "REGISTERED"]
    u = {r.country: float(r.unit_inflow_mwh_per_mw) / (float(r.multiplier) if multiplier_one else 1.0) for r in t.itertuples()}
    return dict(u=u, cf={c: v / 8760.0 for c, v in u.items()}, source={r.country: r.capacity_source for r in t.itertuples()}, table=HYDRO_CANDIDATE_TABLE, sha256=sha256(p))


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
        if not m.any():   # e.g. Truong Son 1 is in the 2050 stock only under the inclusive lifetime boundary (2-5): nothing to move under strict
            moved.append(dict(gem_unit_id=r.gem_unit_id, plant=r.plant, mw=0.0, node_from=r.gem_node, node_to=r.checked_node, note="not in the addition tables of this switch set"))
            continue
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


def existing_profile_column(n, node: str, cls: str, cfg) -> tuple[str, str]:
    """1-2 (decision 241) and Q12 (decision 246): candidate column whose p_max_pu an existing wind / solar component copies (s4a_fleet.add_gem_fleet).
    class0 (v4): '<node> onwind-2025' / '<node> offwind-ac-2025' / '<node> solar-2025' = class 0, the worst class after the class split;
    best_class: the highest class column '<base> c{k}' present at the node (falling back class by class to class 0);
    node_average (solar, Q12): the one-class node profile of the variant, i.e. the column of '<node> solar rooftop-2025' (s4a_layers gives rooftop PV the
    c1 node solar profile); falls back to class 0 when the node has no rooftop column. Returns (column, basis)."""
    s = switches(cfg)
    base = {"solar existing": f"{node} solar-2025", "onwind existing": f"{node} onwind-2025", "offwind existing": f"{node} offwind-ac-2025"}[cls]
    rule = s["existing_solar_profile"] if cls == "solar existing" else s["existing_wind_profile"]
    cols = n.generators_t.p_max_pu.columns
    if not s["enabled"] or rule == "class0":
        return base, "class 0"
    if rule == "node_average":
        roof = f"{node} solar rooftop-2025"
        return (roof, "node average (c1 node profile = rooftop column)") if roof in cols else (base, "class 0 (no node-average column at the node)")
    for k in range(9, 0, -1):
        if f"{base} c{k}" in cols:
            return f"{base} c{k}", f"best class c{k}"
    return base, "class 0 (no higher class at the node)"


GEOTHERMAL_ID_TABLE = "research_inputs/potentials_v5/GEOTHERMAL_ID_POTENTIAL_V5.csv"


def ph_geothermal_rebuild(n, boundary: str, lifetime: int) -> pd.Series:
    """PH geothermal units operating in GEM GIPT 2026-09 (start year known) that are NOT in service in 2050 under (boundary, lifetime) - rebuilt on
    site (S4B-2, s4b_2_candidates_data.py:89-93: strict / 30 a = 'start + 30 <= 2050'); MW by nearest PH AC node."""
    from d1_common import SRC_DIR
    from s4a_2_fleet_data import GIPT, nearest_node
    from v5_common import in_service
    gem = pd.read_csv(SRC_DIR / GIPT, low_memory=False)
    phg = gem[(gem.iso == "PH") & (gem.Type == "geothermal") & (gem.Status == "operating") & gem["Start year"].notna()].copy()
    phg = phg[[not in_service(float(y), lifetime, boundary) for y in phg["Start year"]]]
    ac = n.buses[n.buses.carrier == "AC"][["x", "y", "country"]]
    phg["node"] = [nearest_node(ac, "PH", la, lo)[0] for la, lo in zip(phg.Latitude, phg.Longitude)]
    return phg.groupby("node")["Capacity (MW)"].sum()


def geothermal_caps_v5(n, caps: pd.DataFrame, cfg, repo: Path = ROOT) -> tuple[pd.DataFrame, dict]:
    """1-6 (decision 241; Q16) with 2-5: geothermal rows of the S4B-2 caps table at build time (s4b_candidates.apply_candidate_caps).
    ID: total = potential of research.demand.v5.geothermal_cap_id (GEOTHERMAL_ID_POTENTIAL_V5.csv: reserves_2017 17,506 main | proven_probable 5,460 |
        resource_potential 23,590 = v4) - the ID 'geothermal existing' p_nom of this network, split over the ID rows by their table shares, so cap + stock =
        the chosen potential under every lifetime switch;
    PH: the rebuild part (existing units retiring before 2050 rebuilt on site) re-derived with the v5 lifetime / boundary; the per-node difference to the
        table's strict / 30 a rebuild is added to the PH rows. Other rows unchanged."""
    s = switches(cfg)
    led = dict(geothermal_cap_id=s["geothermal_cap_id"], lifetime=int(s["geothermal_existing_lifetime"]), boundary=s["lifetime_boundary"])
    if not s["enabled"]:
        return caps, led
    caps = caps.copy()
    t = pd.read_csv(Path(repo) / GEOTHERMAL_ID_TABLE).set_index("case")
    pot = float(t.at[s["geothermal_cap_id"], "potential_mw"])
    g = n.generators
    stock = float(g.loc[(g.carrier == "geothermal existing") & (g.bus.map(n.buses.country) == "ID"), "p_nom"].sum())
    sel = (caps.carrier == "geothermal") & (caps.country == "ID")
    old = float(caps.loc[sel, "p_nom_max_mw"].sum()); total = max(0.0, pot - stock)
    if old > 0:
        caps.loc[sel, "p_nom_max_mw"] = caps.loc[sel, "p_nom_max_mw"] * (total / old)
    import hashlib
    led["ID"] = dict(potential_mw=pot, table=GEOTHERMAL_ID_TABLE, table_sha256=hashlib.sha256((Path(repo) / GEOTHERMAL_ID_TABLE).read_bytes()).hexdigest(),
                     stock_mw=stock, cap_before_mw=old, cap_after_mw=float(caps.loc[sel, "p_nom_max_mw"].sum()), rows=int(sel.sum()))
    v4 = ph_geothermal_rebuild(n, "strict", 30); v5 = ph_geothermal_rebuild(n, s["lifetime_boundary"], int(s["geothermal_existing_lifetime"]))
    rows = []
    for node in sorted(set(v4.index) | set(v5.index)):
        d = float(v5.get(node, 0.0)) - float(v4.get(node, 0.0))
        if d == 0.0:
            continue
        m = (caps.carrier == "geothermal") & (caps.node == node)
        if m.sum() != 1:
            raise ValueError(f"PH geothermal rebuild: node {node} has {int(m.sum())} cap rows")
        before = float(caps.loc[m, "p_nom_max_mw"].iloc[0])
        caps.loc[m, "p_nom_max_mw"] = max(0.0, before + d)
        rows.append(dict(node=node, rebuild_v4_mw=float(v4.get(node, 0.0)), rebuild_v5_mw=float(v5.get(node, 0.0)), cap_before_mw=before, cap_after_mw=max(0.0, before + d)))
    led["PH_rebuild"] = dict(v4_mw=float(v4.sum()), v5_mw=float(v5.sum()), nodes=rows)
    return caps, led


PH_DC_TABLE = "research_inputs/corridors/PH_DC_STOCK_V5.csv"


def apply_ph_dc_stock(n, corridors: pd.DataFrame, cfg, repo: Path = ROOT):
    """2-1 (decision 244; Q8): PH inter-island DC stock = NGCP TDP 2025-2050 (PH_DC_STOCK_V5.csv, scripts_project/v5_ph_dc_data.py): Leyte-Luzon 440 MW on
    both segments through the Visayas10 DC junction, MVIP 450 MW, the two Mindoro 'DC' rows 0 MW and still extendable, the 2000 MW B2B placeholder 0 MW and
    not extendable (the component is kept for the DC / AC bus map). Called right after s4f_layers.apply_th_my_stock (s2_network), so the extension limit,
    the converter rule and the lossy split follow the new stock. The frozen-base value (p_nom_min of an extendable link, p_nom otherwise) is checked first."""
    s = switches(cfg); led = dict(mode=s["ph_dc_stock"])
    if not s["enabled"] or s["ph_dc_stock"] == "frozen_base":
        return corridors, led
    t = pd.read_csv(Path(repo) / PH_DC_TABLE, dtype={"component": str})
    rows = []
    for _, r in t.iterrows():
        name = str(r.component)
        if r.component_type != "Link" or name not in n.links.index:
            raise ValueError(f"PH DC stock: Link {name} not in the frozen base")
        ext = bool(n.links.at[name, "p_nom_extendable"])
        before = float(n.links.at[name, "p_nom_min" if ext else "p_nom"])
        if abs(before - float(r.frozen_base_mw)) > 1e-6:
            raise ValueError(f"PH DC stock: {name} has {before} MW, the table says {r.frozen_base_mw}")
        v = float(r.corrected_mw)
        if r.action == "set_capacity":
            n.links.loc[name, "p_nom"] = v
            if ext:
                n.links.loc[name, "p_nom_min"] = v
        elif r.action == "set_zero_fixed":
            n.links.loc[name, ["p_nom", "p_nom_min"]] = [0.0, 0.0]; n.links.loc[name, "p_nom_extendable"] = False
        else:
            raise ValueError("unknown PH DC action " + str(r.action))
        if "component" in corridors.columns:
            sel = corridors.component.astype(str) == name
            if sel.any():
                raise ValueError(f"PH DC stock: {name} is a corridor-table row (not expected for a domestic PH link)")
        rows.append(dict(component=name, action=str(r.action), extendable=ext, frozen_base_mw=before, corrected_mw=v, grade=str(r.grade), source_page=str(r.source_page)))
    led.update(table=PH_DC_TABLE, rows=rows, total_before_mw=float(sum(x["frozen_base_mw"] for x in rows)), total_after_mw=float(sum(x["corrected_mw"] for x in rows)))
    return corridors, led


AC_DEDUP_TABLE = "research_inputs/corridors/AC_DEDUP_V5.csv"


def apply_ac_dedup(n, cfg, repo: Path = ROOT) -> dict:
    """2-2 (decision 244; Q6 (a)): domestic AC corridors carrying OSM duplicate rows (same way, end buses, voltage, length) get s_nom = frozen s_nom x
    factor (AC_DEDUP_V5.csv, scripts_project/v5_ac_dedup_data.py: deduplicated / counted OSM capacity of the corridor; dedup_cables also recounts
    circuits = cables / 3 where the OSM API tag exists); s_nom_min follows when it was the stock bound; num_parallel / x / r / b follow the S4G-1 rule
    (npar = s_nom / (sqrt 3 v_nom i_nom), x = x_per_length l / npar, r likewise, b = 2 pi f c_per_length l npar 1e-9). Only rows with applied = True
    (reconstruction check counted / model s_nom in [0.8, 1.25]); corridors that fail the check stay unchanged (limitation)."""
    import math
    s = switches(cfg); mode = s["ac_dedup"]; led = dict(mode=mode)
    if not s["enabled"] or mode == "frozen_base":
        return led
    t = pd.read_csv(Path(repo) / AC_DEDUP_TABLE, dtype={"line": str})
    t = t[t.applied.astype(str).str.lower() == "true"]
    col = "factor_dedup_cables" if mode == "dedup_cables" else "factor_dedup_only"
    lt = n.line_types; rows = []
    for _, r in t.iterrows():
        k = r.line
        if k not in n.lines.index:
            raise ValueError(f"AC dedup: line {k} not in the network")
        z = n.lines.loc[k]
        if abs(float(z.s_nom) - float(r.frozen_s_nom_mw)) > 1e-6 * max(1.0, float(r.frozen_s_nom_mw)):
            raise ValueError(f"AC dedup: line {k} has s_nom {z.s_nom}, the table says {r.frozen_s_nom_mw}")
        f = float(r[col]); new = float(z.s_nom) * f
        t_ = lt.loc[z.type]; v = float(n.buses.at[z.bus0, "v_nom"])
        npar = new / (math.sqrt(3) * v * float(t_.i_nom))
        x = float(t_.x_per_length) * float(z.length) / npar; rr = float(t_.r_per_length) * float(z.length) / npar
        b = 2 * math.pi * 1e-9 * float(t_.f_nom) * float(t_.c_per_length) * float(z.length) * npar
        rows.append(dict(line=k, country=str(r.country), factor=f, s_nom_before=float(z.s_nom), s_nom_after=new, num_parallel_before=float(z.num_parallel),
                         num_parallel_after=npar, x_before=float(z.x), x_after=x))
        n.lines.loc[k, ["s_nom", "num_parallel", "x", "r", "b"]] = [new, npar, x, rr, b]
        if float(z.s_nom_min) > 0:
            n.lines.loc[k, "s_nom_min"] = new
    led.update(table=AC_DEDUP_TABLE, column=col, lines=len(rows), rows=rows, s_nom_before_mw=float(sum(x["s_nom_before"] for x in rows)),
               s_nom_after_mw=float(sum(x["s_nom_after"] for x in rows)))
    return led


LV_LOAD_MATCH = "electric"   # PyPSA-Eur v2025.07.0 prepare_sector_network.py:1567-1570: loads whose carrier contains "electric"
LV_LINK_CARRIERS_BUS0 = ("BEV charger", "BEV charger uncontrolled", "industry heat pump", "industry electric boiler", "cooking electric")   # decision 246 Q3 (b), Q5 (a)
DIST = "electricity distribution grid"
DIST_EFFICIENCY = 0.97   # PyPSA-Eur v2025.07.0 config.default.yaml transmission_efficiency.electricity distribution grid.efficiency_static (L762-763)


def apply_distribution_grid_v5(n, cfg, demand: dict | None = None) -> dict:
    """3-4 (decision 244; Q3 (b), Q4 (a), Q5 (a)): research.demand.v5.distribution_grid = lv_pypsa_eur moves to the node's low-voltage bus every Load
    with 'electric' in its carrier on an AC node (Astar base load 'electricity', 'industry electricity', 'agriculture machinery electric') and bus0 of the
    BEV chargers (smart and uncontrolled), industrial heat pumps, industrial electric boilers and electric cooking; electrolysis, DAC, Haber-Bosch and grid
    batteries stay on the high-voltage node; rooftop PV and home batteries are on LV already. The distribution grid link of each node (bidirectional,
    efficiency 1.0 in the frozen base) becomes a forward link (HV -> LV, p_min_pu 0, efficiency 0.97) plus a '-reversed' twin (LV -> HV, efficiency 0.97,
    capital cost 0, length 0, no FOM) whose capacity equals the forward one (hook research_lossy_bidirectional_sync collects every extendable reversed
    link). Loads are not scaled (Q4 (a)). Called after apply_transmission_losses / apply_ac_losses (s2_network: that layer refuses existing reversed
    links and lengths <= 0). An AC node with a moved load but no LV bus stops the build. LV buses without a location get their node."""
    from s4j_layers import REV, SYNC_HOOK
    s = switches(cfg); mode = s["distribution_grid"]; led = dict(mode=mode)
    if not s["enabled"] or mode == "hv_lossless":
        return led
    lvb = set(n.buses.index[n.buses.carrier == "low voltage"])

    def lv(bus):
        b = f"{bus} low voltage"
        if b not in lvb:
            raise ValueError(f"distribution grid v5: no low-voltage bus for {bus}")
        return b
    nodes = set(n.buses.index[n.buses.carrier == "AC"])
    L = n.loads
    mv_loads = L.index[(L.carrier.astype(str).str.contains(LV_LOAD_MATCH) | (L.carrier.astype(str) == "land transport EV uncontrolled")) & L.bus.isin(nodes)]   # + the 3-3 uncontrolled EV load (Q5 (a): the charger's bus)
    new_bus = {k: lv(L.at[k, "bus"]) for k in mv_loads}
    for k, b in new_bus.items():
        n.loads.at[k, "bus"] = b
    ledger_rows = 0
    if demand is not None:
        for r in demand.get("loads", []):
            if r.get("load") in new_bus:
                r["bus"] = new_bus[r["load"]]; ledger_rows += 1
    K = n.links
    mv_links = K.index[K.carrier.isin(LV_LINK_CARRIERS_BUS0) & K.bus0.isin(nodes)]
    for k in mv_links:
        n.links.at[k, "bus0"] = lv(K.at[k, "bus0"])
    if "location" in n.buses.columns:   # LV buses carry their node as location (bus_location / per-node reports)
        emp = [b for b in lvb if str(n.buses.at[b, "location"]) in ("", "nan", "None")]
        for b in emp:
            n.buses.at[b, "location"] = b[: -len(" low voltage")]
        led["lv_location_filled"] = len(emp)
    K = n.links
    dist = K.index[(K.carrier == DIST) & ~K.index.str.endswith(REV)]
    if "reversed" not in n.links:
        n.links["reversed"] = False
    if "length_original" not in n.links:
        n.links["length_original"] = n.links["length"]
    rev = n.links.loc[dist].copy().rename(columns={"bus0": "bus1", "bus1": "bus0"})
    rev["capital_cost"] = 0.0; rev["length"] = 0.0; rev["reversed"] = True; rev["p_min_pu"] = 0.0; rev["efficiency"] = DIST_EFFICIENCY
    for c in ("existing_annual_fixed_om_eur", "existing_fixed_om_eur_per_mw_year"):
        if c in rev:
            rev[c] = 0.0
    rev.index = [x + REV for x in dist]; rev.index.name = "Link"
    if set(rev.index) & set(n.links.index):
        raise ValueError("distribution grid v5: reverse link exists already")
    n.links.loc[dist, ["p_min_pu", "efficiency"]] = [0.0, DIST_EFFICIENCY]
    n.import_components_from_dataframe(rev[[c for c in rev.columns if c in n.links.columns]], "Link")
    n.links.loc[rev.index, "reversed"] = True
    n.links["reversed"] = n.links["reversed"].fillna(False).astype(bool)
    if (n.links.loc[rev.index, "p_nom_extendable"].astype(bool)).any():
        n.meta["required_constraint_hooks"] = sorted(set(n.meta.get("required_constraint_hooks", [])) | {SYNC_HOOK})
    by = lambda idx, col: {str(k): int(v) for k, v in pd.Series(col).loc[idx].value_counts().items()}   # noqa: E731
    led.update(loads_moved=int(len(mv_loads)), loads_by_carrier=by(mv_loads, n.loads.carrier), demand_ledger_rows_updated=ledger_rows, links_moved=int(len(mv_links)),
               links_by_carrier=by(mv_links, n.links.carrier), distribution_links=int(len(dist)), reversed_twins=int(len(rev)), efficiency=DIST_EFFICIENCY,
               load_scaling="none (decision 246 Q4 (a): the loads are final-energy based)")
    return led
