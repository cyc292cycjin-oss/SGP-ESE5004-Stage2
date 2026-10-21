"""M08a build layers (decisions 129-133; instruction M08A_CLAUDE_CODE_INSTRUCTION.md). Nothing here solves.

A3  apply_existing_vintage_costs: existing stock priced with technology-data v0.15.0 of its commissioning year.
A7  scenario / coalition variants of a built base network (applied only by scripts_project/m08a_variants.py):
    apply_remove_countries (coalition.remove_countries), apply_stock_mode (cross_border.stock_mode),
    apply_co2_shipping (disconnected.co2_shipping_intra_asean), finance.wacc_mode via s4c_layers.apply_wacc_mode.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np
import pandas as pd

# existing-stock carrier -> technology-data v0.15.0 technology (same mapping as the GEM additions, scripts_project/s4a_fleet.py)
VINTAGE_TECH = {"CCGT existing": "CCGT", "OCGT existing": "OCGT", "coal existing": "coal", "lignite existing": "lignite", "oil existing": "oil",
                "ror existing": "ror", "hydro existing": "hydro", "PHS existing": "PHS",
                "onwind existing": "onwind", "offwind existing": "offwind", "solar existing": "solar-utility"}
# conversion efficiency is a model input only for the fuel Links; hydro / ror / PHS / VRE efficiencies (or profiles) stay as built
EFFICIENCY_CARRIERS = {"CCGT existing", "OCGT existing", "coal existing", "lignite existing", "oil existing"}
# not priced by technology-data: geothermal (v0.15.0 has no geothermal investment / VOM; AEO8 D.15, decision 52) keeps its values
VINTAGE_EXCEPTIONS = {"geothermal existing": "AEO8 Table D.15 (decision 52): technology-data v0.15.0 has no geothermal investment / VOM"}
DEFAULT_RULE = dict(step=5, min=2020, max=2050, rounding="nearest")


def vintage_year(year, rule: dict | None = None) -> int:
    """Commissioning year -> technology-data output year: nearest multiple of `step` (ties cannot occur for whole years),
    clipped to [min, max]; units commissioned before `min` use the `min` table."""
    r = dict(DEFAULT_RULE, **(rule or {}))
    if r["rounding"] != "nearest":
        raise ValueError(f"existing_cost_year_rule.rounding must be 'nearest', got {r['rounding']!r}")
    step = int(r["step"])
    y5 = int(math.floor(float(year) / step + 0.5)) * step
    return int(min(int(r["max"]), max(int(r["min"]), y5)))


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def vintage_tables(cfg: dict, repo: Path) -> tuple[dict, dict]:
    """{year: prepared wide table} of the active cost layer's rebase variant (by_year_dir of research.cost_layer)."""
    from s2_costs import layer_files
    cl = cfg["research"]["cost_layer"]
    spec = layer_files(cl["layers"][cl["active"]])
    d = spec.get("by_year_dir")
    if not d:
        raise ValueError("active cost layer has no by_year_dir (needed by research.fleet.existing_cost_basis td_v0_15_0_by_commissioning_year)")
    tables, files = {}, {}
    for p in sorted((Path(repo) / d).glob("costs_*_EUR2020_prepared.csv")):
        y = int(p.name.split("_")[1])
        tables[y] = pd.read_csv(p, index_col=0)
        files[str(y)] = dict(path=str(Path(d) / p.name), sha256=_sha(p))
    if not tables:
        raise ValueError(f"no by-year tables in {d}")
    return tables, files


def apply_existing_vintage_costs(n, cfg: dict, repo: Path) -> dict:
    """A3 (decision 131, registry existing_fleet_cost_rule), research.fleet.existing_cost_basis:
    td_v0_15_0_by_commissioning_year (main) - every existing component listed in n.meta['existing_unit_components'] gets the
    technology-data v0.15.0 parameters of its units' commissioning years (vintage_year rule, research.fleet.existing_cost_year_rule):
    FOM = FOM % x investment (EUR2020/MW_el/a), VOM (EUR2020/MWh_el) and, for the fuel Links, efficiency. A component that groups units of
    different years gets the capacity-weighted FOM and VOM and the efficiency that keeps its fuel-input capacity (sum MW_el / sum(MW_el / eff));
    Links keep MW_el = p_nom x efficiency (p_nom = MW_el / efficiency, marginal_cost = VOM x efficiency). The existing-FOM objective constant
    n.meta['existing_annual_fixed_om_eur'] is recomputed from the component columns. Geothermal keeps AEO8 (VINTAGE_EXCEPTIONS).
    author_v0_13_2 = the frozen electric-base values (author technology-data v0.13.2 table, costs year 2030) and the 2050 table for the
    GEM additions (former state, comparison). Scenario-independent by construction (no cross-border input)."""
    F = dict(cfg["research"].get("fleet") or {})
    mode = F.get("existing_cost_basis", "author_v0_13_2")
    led = dict(mode=mode, rule=dict(DEFAULT_RULE, **(F.get("existing_cost_year_rule") or {})), components=0, units=0, by_carrier={}, exceptions=dict(VINTAGE_EXCEPTIONS),
               fom_before_eur=float(n.meta.get("existing_annual_fixed_om_eur", 0.0)))
    if mode == "author_v0_13_2":
        led["fom_after_eur"] = led["fom_before_eur"]
        n.meta["research_existing_vintage_costs"] = led
        return led
    if mode != "td_v0_15_0_by_commissioning_year":
        raise ValueError(f"research.fleet.existing_cost_basis must be td_v0_15_0_by_commissioning_year or author_v0_13_2, got {mode!r}")
    tables, files = vintage_tables(cfg, repo)
    led["tables"] = files
    ident = pd.DataFrame.from_dict(n.meta["existing_unit_components"], orient="index")
    rows = []
    for (typ, comp), g in ident.groupby(["component_type", "component"], sort=True):
        df = n.df(typ)
        carrier = str(df.at[comp, "carrier"])
        if carrier not in VINTAGE_TECH:
            if carrier not in VINTAGE_EXCEPTIONS:
                raise ValueError(f"existing carrier without a technology-data mapping: {carrier} ({comp})")
            continue
        tech = VINTAGE_TECH[carrier]
        mw = g.capacity_mw.astype(float).to_numpy()
        years = [vintage_year(y, led["rule"]) for y in g.commissioning_year]
        par = []
        for y in years:
            t = tables[y]
            if tech not in t.index:
                raise ValueError(f"technology {tech} missing in costs_{y}")
            inv, fom_pct, vom, eff = (float(t.at[tech, k]) for k in ("investment", "FOM", "VOM", "efficiency"))
            par.append((fom_pct / 100.0 * inv, vom, eff))
        par = np.array(par)
        cap = float(mw.sum())
        is_link = typ == "Link"
        old_eff = float(df.at[comp, "efficiency"]) if is_link else 1.0
        built = float(df.at[comp, "p_nom"]) * old_eff if typ != "StorageUnit" else float(df.at[comp, "p_nom"])
        if not np.isclose(built, cap, rtol=1e-9, atol=1e-6):
            raise ValueError(f"existing component capacity differs from its units: {comp} {built} vs {cap}")
        fom = float((mw * par[:, 0]).sum() / cap); vom = float((mw * par[:, 1]).sum() / cap)
        before = dict(efficiency=old_eff, fom=float(df.at[comp, "existing_fixed_om_eur_per_mw_year"]), marginal_cost=float(df.at[comp, "marginal_cost"]))
        if is_link and carrier in EFFICIENCY_CARRIERS:
            eff = float(cap / (mw / par[:, 2]).sum())
            df.at[comp, "efficiency"] = eff
            df.at[comp, "p_nom"] = cap / eff
            df.at[comp, "marginal_cost"] = vom * eff
        else:
            eff = old_eff
            df.at[comp, "marginal_cost"] = vom * eff if is_link else vom
        df.at[comp, "existing_fixed_om_eur_per_mw_year"] = fom
        df.at[comp, "existing_annual_fixed_om_eur"] = fom * cap
        for col, v in (("variable_cost_method", f"technology-data v0.15.0 by commissioning year ({tech}; VOM{' x efficiency' if is_link else ''})"),
                       ("cost_qualification", "TECHNOLOGY_DATA_V015_BY_COMMISSIONING_YEAR_GRADE_C")):
            if col in df:
                df.at[comp, col] = v
        rows.append(dict(component_type=typ, component=comp, carrier=carrier, technology=tech, mw=cap, units=len(g), years=sorted(set(years)),
                         efficiency_before=before["efficiency"], efficiency_after=eff, fom_before=before["fom"], fom_after=fom,
                         marginal_cost_before=before["marginal_cost"], marginal_cost_after=float(df.at[comp, "marginal_cost"])))
    total, seen = 0.0, set()
    for z in n.meta["existing_unit_components"].values():
        key = (z["component_type"], z["component"])
        if key not in seen:
            total += float(n.df(key[0]).at[key[1], "existing_annual_fixed_om_eur"]); seen.add(key)
    n.meta["existing_annual_fixed_om_eur"] = total
    r = pd.DataFrame(rows)
    led.update(components=int(len(r)), units=int(sum(r.units)), fom_after_eur=total)
    for c, g in r.groupby("carrier"):
        led["by_carrier"][c] = dict(components=int(len(g)), mw=float(g.mw.sum()), fom_before_eur=float((g.fom_before * g.mw).sum()), fom_after_eur=float((g.fom_after * g.mw).sum()),
                                    efficiency_before_mw_weighted=float((g.efficiency_before * g.mw).sum() / g.mw.sum()),
                                    efficiency_after_mw_weighted=float((g.efficiency_after * g.mw).sum() / g.mw.sum()),
                                    efficiency_after_values=sorted({round(float(x), 6) for x in g.efficiency_after}),
                                    table_years=sorted({y for ys in g.years for y in ys}))
    led["table"] = rows
    n.meta["research_existing_vintage_costs"] = {k: v for k, v in led.items() if k != "table"}
    return led


# =====================================================================================================================
# A7 (decisions 132, 133): variants of a built base network. Defaults (no change): cross_border.stock_mode remove_all,
# disconnected.co2_shipping_intra_asean allow, coalition.remove_countries [], finance.wacc_mode uniform.
# =====================================================================================================================
VARIANT_DEFAULTS = {"cross_border.stock_mode": "remove_all", "disconnected.co2_shipping_intra_asean": "allow",
                    "coalition.remove_countries": [], "finance.wacc_mode": "uniform"}
INTRA_ASEAN_CO2_CARRIERS = ("CO2 ship", "CO2 transit ship", "CO2 transit rail")   # deliveries into ANOTHER ASEAN country's national store (maritime_trade)
EXTRA_ASEAN_CO2_CARRIERS = ("CO2 export extra-ASEAN", "CO2 transit export extra-ASEAN")   # kept by every variant
PORT_COLUMNS = lambda df: [c for c in df.columns if c == "bus" or (c.startswith("bus") and c[3:].isdigit())]


def variant_values(R: dict) -> dict:
    """The four switch values of a research config (defaults where absent)."""
    out = {}
    for key, default in VARIANT_DEFAULTS.items():
        d = R
        for k in key.split("."):
            d = d.get(k, {}) if isinstance(d, dict) else {}
        out[key] = default if d in ({}, None) else d
    out["coalition.remove_countries"] = sorted(out["coalition.remove_countries"] or [])
    return out


def non_default_variants(R: dict) -> dict:
    v = variant_values(R)
    return {k: x for k, x in v.items() if x != VARIANT_DEFAULTS[k]}


def _component_tables(n):
    return [(c.name, c.df) for c in n.iterate_components(["Generator", "Load", "Store", "StorageUnit", "Link", "Line", "Transformer", "ShuntImpedance"])]


def apply_remove_countries(n, countries) -> dict:
    """coalition.remove_countries (decision 132): the listed countries leave the network ENTIRELY - every bus with that country
    (nodes, carrier buses, national atmosphere, national CO2 store, biomass pools ...), every component with a port on such a bus
    (lines and links incl. its half of the cross-border lines, the liquid-pool access, CO2 shipping to / from it, LNG / H2 import
    points located in it) and every component tagged with that country (e.g. its loads on the regional ASEAN buses). Components
    of the regional pools that belong to no country (international bunker loads, ASEAN import generators) stay. The metadata used by
    the solve hooks and ledgers is filtered the same way; n.meta['research_countries'] lists the remaining countries.
    NOT the decision-91 cross_border.coalition switch (that keeps the country and only cuts corridors)."""
    from carrier_architecture import COUNTRIES, network_countries
    X = sorted(set(countries or []))
    led = dict(removed_countries=X, removed={}, demand_removed_mwh=0.0)
    if not X:
        return led
    if set(X) - set(COUNTRIES):
        raise ValueError(f"unknown countries {sorted(set(X) - set(COUNTRIES))}")
    remaining = sorted(network_countries(n) - set(X))
    if not remaining:
        raise ValueError("coalition.remove_countries would remove every country")
    gone_bus = set(n.buses.index[n.buses.country.astype(str).isin(X)])
    w = n.snapshot_weightings.generators
    load = n.get_switchable_as_dense("Load", "p_set")
    removed = {}
    for typ, df in _component_tables(n):
        if not len(df):
            continue
        hit = df[PORT_COLUMNS(df)].isin(gone_bus).any(axis=1)
        if "country" in df:
            hit |= df.country.astype(str).isin(X)
        names = list(df.index[hit])
        if typ == "Load" and names:
            led["demand_removed_mwh"] = float(load[names].mul(w, axis=0).sum().sum())
        if names:
            n.mremove(typ, names)
        removed[typ] = names
    n.mremove("Bus", sorted(gone_bus))
    removed["Bus"] = sorted(gone_bus)
    led["removed"] = {k: len(v) for k, v in removed.items()}
    gone = {(t, x) for t, v in removed.items() for x in v}
    # --- metadata of the solve hooks and ledgers --------------------------------------------------------------------------
    m = n.meta
    if m.get("existing_unit_components"):
        m["existing_unit_components"] = {u: z for u, z in m["existing_unit_components"].items() if (z["component_type"], z["component"]) not in gone}
        tot, seen = 0.0, set()
        for z in m["existing_unit_components"].values():
            k = (z["component_type"], z["component"])
            if k not in seen:
                tot += float(n.df(k[0]).at[k[1], "existing_annual_fixed_om_eur"]); seen.add(k)
        led["existing_fom_before_eur"], m["existing_annual_fixed_om_eur"] = float(m.get("existing_annual_fixed_om_eur", 0.0)), tot
    if m.get("existing_cross_border_fom_ledger"):
        keep = [r for r in m["existing_cross_border_fom_ledger"] if (r["component_type"], r["component"]) not in gone]
        m["existing_cross_border_fom_ledger"] = keep; m["existing_cross_border_fom_eur"] = float(sum(r["annual_fom_eur"] for r in keep))
    if m.get("existing_resource_groups"):
        groups = {}
        for g, e in m["existing_resource_groups"].items():
            cands = [c for c in e.get("candidates", []) if (c["ComponentType"], c["Name"]) not in gone]
            if cands:
                groups[g] = dict(e, candidates=cands)
        m["existing_resource_groups"] = groups
    if m.get("battery_inverter_pairs"):
        m["battery_inverter_pairs"] = [p for p in m["battery_inverter_pairs"] if p.get("charger") in n.links.index and p.get("discharger") in n.links.index]
    for key, typ in (("store_power_rules", "Store"), ("external_annual_caps", "Generator"), ("demand_owners", "Load")):
        if isinstance(m.get(key), dict):
            m[key] = {k: v for k, v in m[key].items() if k in n.df(typ).index}
    if isinstance(m.get("research_new_hydro_inflow_tie"), list):
        m["research_new_hydro_inflow_tie"] = [x for x in m["research_new_hydro_inflow_tie"] if x in n.storage_units.index]
    if isinstance(m.get("research_nuclear_caps"), dict):
        m["research_nuclear_caps"] = {c: v for c, v in m["research_nuclear_caps"].items() if c not in X}
    if isinstance(m.get("research_co2_storage"), dict):
        cs = m["research_co2_storage"]
        cs["caps_t_per_year"] = {c: v for c, v in cs.get("caps_t_per_year", {}).items() if c not in X}
        if isinstance(cs.get("potentials_gt"), dict):
            cs["potentials_gt"] = {c: v for c, v in cs["potentials_gt"].items() if c not in X}
    m["research_countries"] = remaining
    # --- invariants ----------------------------------------------------------------------------------------------------
    for typ, df in _component_tables(n):
        if len(df) and df[PORT_COLUMNS(df)].isin(gone_bus).any().any():
            raise AssertionError(f"{typ} still references a removed bus")
    if (n.buses.country.astype(str).isin(X)).any():
        raise AssertionError("bus of a removed country left")
    led["remaining_countries"] = remaining
    return led


def apply_stock_mode(n, mode: str) -> dict:
    """cross_border.stock_mode (decision 132): remove_all (main) = the disconnected network as built (every ASEAN-internal cross-border fixed
    network removed incl. the 2025 stock; nothing to do on a disconnected base); keep_stock_no_new (sensitivity, base = an INTEGRATED network):
    the 2025 cross-border stock stays - AC lines with s_nom_min > 0, electricity links with p_nom_min > 0 and the existing gas pipelines
    (gas_pipeline_kind existing_2025), each with its '-reversed' twin of the lossy split - pinned at its 2025 capacity (nominal = min = max,
    the extendable flag kept so the objective treats the stock as in the base); every other cross-border line / link (candidates, H2 / CO2
    pipelines, gas candidates) is removed; maritime trade and extra-ASEAN options unchanged; the existing cross-border FOM constant stays."""
    led = dict(mode=mode)
    xbm = lambda df: (df["border_class"] == "cross_border") if "border_class" in df else pd.Series(False, index=df.index)
    if mode == "remove_all":
        xb = int(xbm(n.lines).sum() + xbm(n.links).sum())
        if xb:
            raise ValueError("stock_mode remove_all applies to a disconnected base network (cross-border components present)")
        return led
    if mode != "keep_stock_no_new":
        raise ValueError(f"cross_border.stock_mode must be remove_all or keep_stock_no_new, got {mode!r}")
    L, K = n.lines, n.links
    xl = L[xbm(L)]; xk = K[xbm(K)]
    if not len(xl) and not len(xk):
        raise ValueError("stock_mode keep_stock_no_new needs an integrated base network")
    rev = xk["reversed"].astype(bool) if "reversed" in xk else pd.Series(False, index=xk.index)
    kind = xk["gas_pipeline_kind"].astype(str) if "gas_pipeline_kind" in xk else pd.Series("", index=xk.index)
    stock_lines = list(xl.index[xl.s_nom_min > 0])
    stock_fwd = list(xk.index[~rev & ((xk.p_nom_min > 0) | (kind == "existing_2025"))])
    twins = {f"{x}-reversed": x for x in stock_fwd if f"{x}-reversed" in xk.index}
    keep_links = set(stock_fwd) | set(twins)
    out_l = sorted(set(xl.index) - set(stock_lines)); out_k = sorted(set(xk.index) - keep_links)
    n.mremove("Line", out_l); n.mremove("Link", out_k)
    for x in stock_lines:
        cap = float(n.lines.at[x, "s_nom_min"])
        n.lines.loc[x, ["s_nom", "s_nom_min", "s_nom_max"]] = [cap, cap, cap]
    for x in stock_fwd:
        cap = float(n.links.at[x, "p_nom_min"]) if float(n.links.at[x, "p_nom_min"]) > 0 else float(n.links.at[x, "p_nom"])
        n.links.loc[x, ["p_nom", "p_nom_min", "p_nom_max"]] = [cap, cap, cap]
    for r, f in twins.items():
        cap = float(n.links.at[f, "p_nom"])
        n.links.loc[r, ["p_nom", "p_nom_min", "p_nom_max"]] = [cap, cap, cap]
    by = lambda d: {str(k): int(v) for k, v in d.items()}
    kept_k = n.links.loc[sorted(keep_links)]
    led.update(kept_lines=len(stock_lines), kept_links_forward=len(stock_fwd), kept_reversed_twins=len(twins), removed_lines=len(out_l), removed_links=len(out_k),
               kept_by_carrier=by(kept_k.carrier.value_counts()), kept_capacity_mw=dict(lines=float(n.lines.loc[stock_lines, "s_nom"].sum()),
                                                                                       links=float(n.links.loc[stock_fwd, "p_nom"].sum())),
               existing_cross_border_fom_eur=float(n.meta.get("existing_cross_border_fom_eur", 0.0)), stock_lines=stock_lines, stock_links=sorted(stock_fwd))
    return led


def apply_co2_shipping(n, mode: str) -> dict:
    """disconnected.co2_shipping_intra_asean (b1, decision 132): allow (main) | forbid - in a disconnected network, every delivery of CO2 into
    ANOTHER ASEAN country's national store is removed (carriers CO2 ship, CO2 transit ship and CO2 transit rail - the Lao rail leg into the
    Vietnamese / Thai store is the land part of the same trade); exports to extra-ASEAN storage (CO2 export extra-ASEAN, CO2 transit export
    extra-ASEAN) stay. Applies to disconnected networks only."""
    led = dict(mode=mode)
    if mode == "allow":
        return led
    if mode != "forbid":
        raise ValueError(f"disconnected.co2_shipping_intra_asean must be allow or forbid, got {mode!r}")
    if (n.meta.get("scenario") or (n.meta.get("research_config") or {}).get("scenario")) != "disconnected":
        raise ValueError("co2_shipping_intra_asean forbid applies to disconnected networks only")
    K = n.links
    sel = K[K.carrier.isin(INTRA_ASEAN_CO2_CARRIERS)]
    for x, z in sel.iterrows():
        b1 = str(z.bus1)
        if n.buses.at[b1, "carrier"] != "co2 sequestered" or str(n.buses.at[b1, "country"]) == str(z.country):
            raise AssertionError(f"{x}: not a delivery into another country's national store")
    n.mremove("Link", list(sel.index))
    keep = K.index[K.carrier.isin(EXTRA_ASEAN_CO2_CARRIERS)] if len(K) else []
    led.update(removed=int(len(sel)), removed_by_carrier={str(k): int(v) for k, v in sel.carrier.value_counts().items()},
               extra_asean_links_kept=int(len(keep)))
    return led
