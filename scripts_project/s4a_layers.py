"""S4A-1 (L14, decisions 70-73): rebuilt renewable availability profiles for the electric-base wind / solar candidates.

research.renewable.profile_variant
  original  - the author profiles inherited by the frozen electric base (p_max_pu untouched; former main, kept as comparison)
  fork      - rebuilt from the ASEAN ERA5 2013 cutout (Zenodo 10.5281/zenodo.20325289) with the pypsa-asean defaults
              (method check: same turbines / correction factors as the original chain)
  pypsa_eur - rebuilt with the PyPSA-Eur v2025.07.0 renewable defaults (offshore NREL 2020ATB 5.5 MW @ 120 m x 0.8855,
              solar without the 0.854337 correction, onshore Vestas V112 unchanged; latitude-optimal tilt kept) - main
research.renewable.resource_classes
  1     - one profile per node (PyPSA-Eur default)
  N > 1 - per-node capacity-factor classes (PyPSA-Eur `resource_classes` mechanism): the node p_nom_max of the electric base is
          split by the class potential shares; class k >= 1 is a new generator `<name> c<k>`, class 0 keeps the original name
Profiles come from scripts_project/s4a_profiles.py (hourly atlite output averaged to the 2013 3 h snapshots) exported by
scripts_project/s4a_1_export.py to research_inputs/renewable_v5/profiles_{variant}_c{N}_3h.nc with the class table
S4A_PROFILE_CLASSES_c{N}.csv. The node p_nom_max totals of the electric base are never changed (only split).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

TECHS = ["onwind", "offwind-ac", "offwind-dc", "solar"]
VARIANTS = ("original", "fork", "pypsa_eur", "calibrated_modern")   # S4B-3 (decision 74): calibrated_modern = onshore wind from the Ember-calibrated ERA5 wind speed + DEA 2050 turbine, offshore / solar = pypsa_eur
OFFSHORE_TECHS = ("offwind-ac", "offwind-dc", "offwind-float")
OFFSHORE_RULES = ("author_pypsa_earth", "pypsa_eur_v2025_07")   # M08a A6.2: research.renewable.offshore_rules
OFFSHORE_FILE = "profiles_offshore_pypsa_eur_v2025_07_c{ncls}_3h.nc"
OFFSHORE_CLASSES = "OFFSHORE_CLASSES_pypsa_eur_v2025_07.csv"


def offshore_rule(RN: dict) -> str:
    v = str(RN.get("offshore_rules", "author_pypsa_earth"))
    if v not in OFFSHORE_RULES:
        raise ValueError(f"research.renewable.offshore_rules must be one of {OFFSHORE_RULES}, got {v!r}")
    return v


def offshore_classes(cfg, repo: Path) -> tuple[pd.DataFrame, Path]:
    """M08a A6.2: the node x class table of the active resource-class count (potential, distance, landfall) - also read by the cost layer."""
    RN = dict(cfg["research"].get("renewable") or {}); ncls = int(RN.get("resource_classes", 1))
    p = Path(repo) / str(RN["offshore_dir"]) / OFFSHORE_CLASSES
    t = pd.read_csv(p)
    t = t[(t.rules == "pypsa_eur_v2025_07") & (t.classes == ncls)]
    if t.empty:
        raise ValueError(f"{p.name} has no rows for {ncls} resource classes")
    return t, p


def offshore_distance_table(cfg, repo: Path) -> tuple[pd.DataFrame, Path]:
    """Connection-distance table indexed by (tech, node, cls) of the active offshore rule: the M08a class table (pypsa_eur_v2025_07, incl.
    offwind-float) or research.renewable.offwind_distance_table (S4C-1, author_pypsa_earth)."""
    RN = dict(cfg["research"].get("renewable") or {})
    if offshore_rule(RN) == "pypsa_eur_v2025_07":
        t, p = offshore_classes(cfg, repo)
    else:
        p = Path(repo) / str(RN["offwind_distance_table"]); t = pd.read_csv(p)
    return t.set_index(["tech", "node", "cls"]), p


def apply_offshore_rules(n, cfg, repo: Path) -> dict:
    """M08a A6.2 (M08-7, decisions 129, 131; registry renewable_offshore_rule): research.renewable.offshore_rules =
    pypsa_eur_v2025_07 (MAIN) - the offshore wind candidates follow the PyPSA-Eur v2025.07.0 area rules (fixed-bottom AC <= 30 km / DC >= 30 km
    from shore at depth <= 60 m, floating 60-1,000 m, 2 MW/km2 for all three, shipping lanes (density > 400 x 8760 x 6) and natura excluded,
    open sea only; scripts_project/m08a_offshore_profiles.py): every extendable offwind-ac / offwind-dc candidate of the electric base is
    replaced by one generator per node x resource class of research_inputs/renewable_v5/offshore_m08a (p_nom_max = class potential,
    p_max_pu = class profile clipped at clip_p_max_pu), and the new carrier offwind-float is added the same way; names '<node> <tech>-2025'
    (class 0) and '<node> <tech>-2025 c<k>'; other attributes from the base candidate of the same carrier (offwind-dc for offwind-float);
    capital costs are set by the cost layer (s4c_layers.apply_cost_layer_s4c1: technology-data v0.15.0 offwind / offwind-float + station +
    connection by the class distance). Existing offshore wind ('offwind existing') is not touched. author_pypsa_earth = the author potentials
    (AC 2 MW/km2 / DC 3 MW/km2, depth <= 50 m, no shipping lanes, no floating) as split by the S4A classes (former state, comparison)."""
    RN = dict(cfg["research"].get("renewable") or {}); rule = offshore_rule(RN)
    led = dict(rule=rule)
    if rule == "author_pypsa_earth":
        return led
    ncls = int(RN.get("resource_classes", 1)); clip = float(RN.get("clip_p_max_pu", 0.0))
    t, tp = offshore_classes(cfg, repo)
    f = Path(repo) / str(RN["offshore_dir"]) / OFFSHORE_FILE.format(ncls=ncls)
    ds = xr.open_dataset(f)
    if not pd.DatetimeIndex(n.snapshots).equals(pd.DatetimeIndex(ds.time.values)):
        raise ValueError("M08a offshore profile time index differs from the network snapshots")
    led.update(resource_classes=ncls, files={f.name: _sha(f), tp.name: _sha(tp)}, removed={}, added={}, p_nom_max_mw={})
    g = n.generators
    static_cols = [c for c in g.columns if c not in ("p_nom_opt",)]
    old = g[g.carrier.isin(["offwind-ac", "offwind-dc"]) & g.p_nom_extendable]
    if old.empty:
        raise ValueError("no extendable offwind-ac / offwind-dc candidate to take the attributes from")
    tmpl = {car: old[old.carrier == car].sort_index().iloc[0][static_cols].to_dict() for car in ("offwind-ac", "offwind-dc")}
    tmpl["offwind-float"] = dict(tmpl["offwind-dc"])
    for car in ("offwind-ac", "offwind-dc"):
        sel = old[old.carrier == car]
        led["removed"][car] = dict(generators=int(len(sel)), p_nom_max_mw=float(sel.p_nom_max.sum()))
    n.mremove("Generator", list(old.index))
    from s2_layers import ensure_carrier
    ensure_carrier(n, "offwind-float")
    if "offwind-dc" in n.carriers.index:
        for col in [c for c in ("color", "nice_name") if c in n.carriers.columns]:
            n.carriers.at["offwind-float", col] = "Offshore Wind (Floating)" if col == "nice_name" else n.carriers.at["offwind-dc", col]
    by_country, series = {}, {}
    for tech in OFFSHORE_TECHS:
        prof = ds[tech.replace("-", "_")].to_pandas()
        rows = t[(t.tech == tech) & (t.potential_mw > 0)].sort_values(["node", "cls"])
        names = []
        for r in rows.itertuples():
            key = f"{r.node}|{int(r.cls)}"
            if key not in prof.columns:
                raise ValueError(f"profile {key} of {tech} missing in {f.name}")
            if r.node not in n.buses.index:
                raise ValueError(f"offshore class node {r.node} is not a bus of the network")
            name = f"{r.node} {tech}-2025" + (f" c{int(r.cls)}" if int(r.cls) else "")
            attrs = dict(tmpl[tech]); attrs.update(bus=r.node, carrier=tech, p_nom=0.0, p_nom_min=0.0, p_nom_max=float(r.potential_mw), p_nom_extendable=True)
            for col in ("source_component", "resource_identity"):
                if col in attrs:
                    attrs[col] = name
            attrs = {k: v for k, v in attrs.items() if not (isinstance(v, float) and np.isnan(v))}
            n.add("Generator", name, **attrs)
            s = prof[key].values.astype(float)
            series[name] = np.where(s >= clip, s, 0.0) if clip > 0 else s
            names.append(name)
            by_country.setdefault(tech, {}).setdefault(str(r.country), 0.0)
            by_country[tech][str(r.country)] += float(r.potential_mw)
        led["added"][tech] = dict(generators=len(names), nodes=int(rows.node.nunique()))
        led["p_nom_max_mw"][tech] = float(rows.potential_mw.sum())
    pm = n.generators_t.p_max_pu
    n.generators_t.p_max_pu = pd.concat([pm.drop(columns=[c for c in pm.columns if c in series]), pd.DataFrame(series, index=pm.index if len(pm.index) else n.snapshots)], axis=1)
    led["p_nom_max_mw_by_country"] = {k: {c: round(v, 3) for c, v in sorted(d.items())} for k, d in by_country.items()}
    return led


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def apply_solar_density(n, RN: dict) -> dict:
    """M08a A6.1 (M08-7, decisions 129, 131; registry renewable_capacity_per_sqkm_solar): research.renewable.solar_density - the
    utility-PV candidate potentials of the electric base were computed by the author chain at 4.6 MW/km2 (PyPSA-Earth); the main run
    uses the PyPSA-Eur v2025.07.0 density 5.1 MW/km2 on the SAME eligible land (land classes and protected-area exclusion unchanged),
    i.e. p_nom_max x 5.1 / 4.6 = 1.1087 for every ground-mounted 'solar' candidate in the 11 countries, no raster recomputation;
    rooftop PV ('solar rooftop') and existing PV ('solar existing') unchanged."""
    sd = dict(RN.get("solar_density") or {})
    built, target = float(sd.get("built_mw_per_km2", 4.6)), float(sd.get("target_mw_per_km2", sd.get("built_mw_per_km2", 4.6)))
    scale = target / built
    sel = n.generators.index[n.generators.carrier == "solar"]
    before = float(n.generators.loc[sel, "p_nom_max"].replace(np.inf, np.nan).sum())
    if scale != 1.0:
        n.generators.loc[sel, "p_nom_max"] = n.generators.loc[sel, "p_nom_max"] * scale
    after = float(n.generators.loc[sel, "p_nom_max"].replace(np.inf, np.nan).sum())
    return dict(built_mw_per_km2=built, target_mw_per_km2=target, scale=scale, generators=int(len(sel)), p_nom_max_before_mw=before, p_nom_max_after_mw=after,
                rule="ground-mounted solar p_nom_max x target / built density; land rules unchanged; rooftop and existing PV unchanged")


def apply_renewable_profiles(n, cfg, repo: Path):
    RN = dict(cfg["research"].get("renewable") or {})
    variant = str(RN.get("profile_variant", "original")); ncls = int(RN.get("resource_classes", 1))
    clip = float(RN.get("clip_p_max_pu", 0.0))   # original chain and PyPSA-Eur: profile.where(profile >= clip, 0)
    pdir = Path(repo) / str(RN.get("profile_dir", "research_inputs/renewable_v5"))
    if variant not in VARIANTS:
        raise ValueError("Unknown research.renewable.profile_variant " + variant)
    if ncls < 1:
        raise ValueError("research.renewable.resource_classes must be >= 1")
    led = dict(profile_variant=variant, resource_classes=ncls, clip_p_max_pu=clip, profile_dir=str(pdir.relative_to(repo)), replaced={}, added=[], untouched=[], files={})
    led["solar_density"] = apply_solar_density(n, RN)   # M08a A6 (M08-7, decisions 129, 131): before the class split, so every class keeps its share
    new_offshore = offshore_rule(RN) == "pypsa_eur_v2025_07"   # M08a A6.2: offshore candidates replaced by apply_offshore_rules below
    if variant == "original":
        if new_offshore:
            raise ValueError("research.renewable.offshore_rules pypsa_eur_v2025_07 needs a rebuilt profile variant (not original)")
        n.meta["research_renewable"] = led
        return led
    f = pdir / f"profiles_{variant}_c{ncls}_3h.nc"; f1 = pdir / f"profiles_{variant}_c1_3h.nc"; fc = pdir / f"S4A_PROFILE_CLASSES_c{ncls}.csv"
    for p in (f, f1, fc):
        if not p.exists():
            raise FileNotFoundError("S4A-1 profile input missing: " + str(p))
        led["files"][p.name] = _sha(p)
    ds = xr.open_dataset(f); ds1 = xr.open_dataset(f1)
    cls = pd.read_csv(fc); cls = cls[cls.variant == variant]
    snaps = pd.DatetimeIndex(n.snapshots)
    t = pd.DatetimeIndex(ds.time.values)
    if not snaps.equals(t):
        raise ValueError("S4A-1 profile time index differs from the network snapshots")
    g = n.generators
    static_cols = [c for c in g.columns if c not in ("p_nom_opt",)]
    for tech in TECHS:
        if new_offshore and tech in OFFSHORE_TECHS:
            continue
        prof = ds[tech.replace("-", "_")].to_pandas()   # time x bus ("node|cls"); buses absent for a technology carry NaN after the Dataset alignment -> not applied
        prof = prof.loc[:, ~prof.isna().any()]; prof1 = ds1[tech.replace("-", "_")].to_pandas(); prof1 = prof1.loc[:, ~prof1.isna().any()]
        if clip > 0:
            prof = prof.where(prof >= clip, 0.0); prof1 = prof1.where(prof1 >= clip, 0.0)
        gens = g.index[g.carrier == tech]
        shares = cls[cls.tech == tech].set_index(["node", "cls"]).potential_share if ncls > 1 else None
        for name in gens:
            node = str(g.at[name, "bus"]); key0 = f"{node}|0"
            if key0 not in prof.columns:
                led["untouched"].append(name); continue
            total = float(g.at[name, "p_nom_max"])
            if ncls == 1:
                n.generators_t.p_max_pu[name] = prof[key0].values.astype(float)
                led["replaced"][name] = dict(node=node, tech=tech, classes=1, cf_annual=float((prof[key0].values * n.snapshot_weightings.generators.values).sum() / n.snapshot_weightings.generators.sum()))
                continue
            row = g.loc[name, static_cols].to_dict()
            keys = [k for k in prof.columns if k.startswith(node + "|")]
            n_present = len(keys)
            for k in range(ncls):
                key = f"{node}|{k}"
                if key not in prof.columns:
                    continue
                share = float(shares.get((node, k), 0.0)) if shares is not None else 1.0
                pmax = total * share if np.isfinite(total) else total
                series = prof[key].values.astype(float)
                if k == 0:
                    n.generators.loc[name, "p_nom_max"] = pmax
                    n.generators_t.p_max_pu[name] = series
                    led["replaced"][name] = dict(node=node, tech=tech, classes=n_present, cls=0, potential_share=share, p_nom_max=pmax)
                else:
                    new = f"{name} c{k}"
                    attrs = dict(row); attrs.update(p_nom_max=pmax, p_nom=0.0, p_nom_min=0.0)
                    attrs = {kk: vv for kk, vv in attrs.items() if not (isinstance(vv, float) and np.isnan(vv))}
                    n.add("Generator", new, **attrs)
                    n.generators_t.p_max_pu[new] = series
                    led["added"].append(dict(generator=new, parent=name, node=node, tech=tech, cls=k, potential_share=share, p_nom_max=pmax))
        if tech == "solar":   # rooftop PV uses the node-level (class 1) solar profile of the same variant
            for name in g.index[g.carrier == "solar rooftop"]:
                node = str(name).rsplit(" solar rooftop", 1)[0]; key0 = f"{node}|0"   # rooftop sits on the node low-voltage bus; the node is the name prefix
                if key0 in prof1.columns:
                    n.generators_t.p_max_pu[name] = prof1[key0].values.astype(float)
                    led["replaced"][name] = dict(node=node, tech="solar rooftop", classes=1, source="solar c1 node profile")
                else:
                    led["untouched"].append(name)
    led["offshore"] = apply_offshore_rules(n, cfg, repo)   # M08a A6.2 (author_pypsa_earth: no change)
    led["summary"] = dict(replaced=len(led["replaced"]), added=len(led["added"]), untouched=len(led["untouched"]))
    n.meta["research_renewable"] = led
    return led
