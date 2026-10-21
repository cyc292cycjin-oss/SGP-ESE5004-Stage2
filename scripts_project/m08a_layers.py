"""M08a build layers (decisions 129-133; instruction M08A_CLAUDE_CODE_INSTRUCTION.md). Nothing here solves.

A3  apply_existing_vintage_costs: existing stock priced with technology-data v0.15.0 of its commissioning year.
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
