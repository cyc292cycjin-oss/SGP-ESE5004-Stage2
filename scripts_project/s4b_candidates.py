"""S4B-2 (decisions 78, 79): apply the geothermal / new hydro / new PHS caps to the S1 site candidates and the nuclear plan caps.

Caps from research_inputs/potentials_v5/CANDIDATE_CAPS_S4B2_BY_NODE.csv (scripts_project/s4b_2_candidates_data.py) for
research.candidates.hydro_geothermal_cap (mode) x pipeline_cap_statuses (variant). Candidates with a positive cap get status
REGISTERED_S4B2; candidates whose cap is 0 get ZERO_CAP_S4B2 (no longer DATA_PENDING). Representation (decision 78 c, grade C proxies):
  * geothermal: availability 0.7194 (decision 52 AEO8 C.4/C.5 capacity factor, as the existing units; S1 left 1.0);
  * run-of-river: availability = capacity-weighted availability of the same-node existing ROR, else same country, else ASEAN;
  * reservoir hydro: inflow per MW and max_hours = capacity-weighted same-node existing reservoirs, else same country, else ASEAN; the
    inflow attribute holds the series for the full cap and the research_new_hydro_inflow hook ties the usable inflow to the built capacity
    (spill_t >= inflow_t - r_t x p_nom with r_t = inflow_t / p_nom_max), so an unbuilt or partly built reservoir gets no free energy;
    no pumping (p_min_pu 0, efficiency_store 0; S1 left p_min_pu -1 with efficiency_store 1);
  * PHS: 6 h, round trip 0.75 = sqrt(0.75) per leg (S1 applied the technology-data round trip 0.75 on both legs = 0.5625).
Nuclear (decision 79): research.candidates.nuclear_cap = none (main) | national_plans: countries without a plan get p_nom_max 0 on every
nuclear / nuclear SMR candidate; the others get one constraint sum(p_nom) <= cap through the research_nuclear_national_cap hook.
Candidate costs are untouched (decisions 46, 50, 52).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

AEO8_GEOTHERMAL_CF = 0.719443559520017
NAMES = {"geothermal": ("Generator", "geothermal"), "ror": ("Generator", "ror_new"), "hydro": ("StorageUnit", "hydro_new"), "PHS": ("StorageUnit", "PHS_new")}
INFLOW_HOOK = "research_new_hydro_inflow"; NUCLEAR_HOOK = "research_nuclear_national_cap"


def _proxy(n, node, country, rows, series):
    """Capacity-weighted series of existing units at the node, else the country, else ASEAN; returns (per-MW series, scope)."""
    for scope, sel in [("node", rows[rows.bus == node]), ("country", rows[rows.bus.map(n.buses.country) == country]), ("ASEAN", rows)]:
        sel = sel[sel.index.isin(series.columns)]
        if len(sel) and float(sel.p_nom.sum()) > 0:
            return series[sel.index].sum(axis=1) / float(sel.p_nom.sum()) if series is not None else None, scope, sel
    return None, "none", rows.iloc[0:0]


def apply_candidate_caps(n, cfg, repo: Path, nodes):
    C = dict(cfg["research"].get("candidates") or {})
    mode = str(C.get("hydro_geothermal_cap", "zero")); variant = str(C.get("pipeline_cap_statuses", "announced_preconstruction"))
    led = dict(mode=mode, variant=variant, set=[], by_carrier_mw={}, proxies={}, corrections=[], nuclear={})
    table = Path(repo) / str(C.get("caps_table", "research_inputs/potentials_v5/CANDIDATE_CAPS_S4B2_BY_NODE.csv"))
    caps = pd.read_csv(table); caps = caps[(caps["mode"] == mode) & (caps.variant == variant)]
    led["table"] = dict(path=str(table.relative_to(repo)), sha256=hashlib.sha256(table.read_bytes()).hexdigest(), rows=int(len(caps)))
    if mode != "zero" and not len(caps):
        raise ValueError(f"no candidate caps for mode {mode} / variant {variant}")
    g, su = n.generators, n.storage_units
    ror_ex = g[g.carrier == "ror existing"]; hyd_ex = su[su.carrier == "hydro existing"]
    tie = []
    for carrier, (typ, key) in NAMES.items():
        df = n.df(typ)
        for node in nodes:
            name = f"{node} {key}"
            if name not in df.index:
                continue
            row = caps[(caps.node == node) & (caps.carrier == carrier)]
            cap = float(row.p_nom_max_mw.sum()) if len(row) else 0.0
            df.at[name, "p_nom_max"] = cap
            df.at[name, "s1_candidate_status"] = "REGISTERED_S4B2" if cap > 0 else "ZERO_CAP_S4B2"
            if cap <= 0:
                continue
            c = str(n.buses.at[node, "country"])
            if carrier == "geothermal":
                df.at[name, "p_max_pu"] = AEO8_GEOTHERMAL_CF; scope = "decision 52 AEO8 CF"
            elif carrier == "ror":
                prof, scope, sel = _proxy(n, node, c, ror_ex, n.generators_t.p_max_pu)
                if prof is None:
                    raise ValueError("no ROR availability proxy for " + name)
                prof = (n.generators_t.p_max_pu[sel.index] * sel.p_nom).sum(axis=1) / float(sel.p_nom.sum())
                n.generators_t.p_max_pu[name] = prof.values
            elif carrier == "hydro":
                inflow_per_mw, scope, sel = _proxy(n, node, c, hyd_ex, n.storage_units_t.inflow)
                if inflow_per_mw is None:
                    raise ValueError("no reservoir inflow proxy for " + name)
                hours = float((sel.max_hours * sel.p_nom).sum() / sel.p_nom.sum())
                df.at[name, "max_hours"] = hours; df.at[name, "p_min_pu"] = 0.0; df.at[name, "efficiency_store"] = 0.0
                df.at[name, "max_hours_basis"] = f"capacity-weighted existing reservoirs of the {scope} (grade C)"
                n.storage_units_t.inflow[name] = (inflow_per_mw * cap).values
                tie.append(name)
            else:   # PHS
                eff = float(np.sqrt(0.75)); df.at[name, "efficiency_store"] = eff; df.at[name, "efficiency_dispatch"] = eff; df.at[name, "max_hours"] = 6.0; scope = "6 h, round trip 0.75"
            led["set"].append(dict(component=name, carrier=carrier, country=c, p_nom_max_mw=cap, proxy_scope=scope))
            led["by_carrier_mw"][carrier] = led["by_carrier_mw"].get(carrier, 0.0) + cap
    led["corrections"] = ["new PHS efficiency per leg sqrt(0.75) (S1 candidate: 0.75 per leg = round trip 0.5625)", "new reservoir hydro p_min_pu 0 and efficiency_store 0 (S1 candidate: p_min_pu -1, efficiency_store 1 = pumping)",
                          "new geothermal availability 0.7194 (S1 candidate: 1.0)", "new run-of-river availability from existing ROR (S1 candidate: 1.0)"]
    if tie:
        n.meta["research_new_hydro_inflow_tie"] = sorted(tie)
        n.meta["required_constraint_hooks"] = sorted(set(n.meta.get("required_constraint_hooks", [])) | {INFLOW_HOOK})
    # nuclear plan caps (decision 79)
    ncap = str(C.get("nuclear_cap", "none"))
    led["nuclear"]["mode"] = ncap
    if ncap == "national_plans":
        plans = pd.read_csv(Path(repo) / str(C.get("nuclear_caps_table", "research_inputs/potentials_v5/NUCLEAR_NATIONAL_PLAN_CAPS_S4B2.csv"))).set_index("country").cap_mw.to_dict()
        nuc = g[g.carrier.isin(["nuclear", "nuclear SMR"]) & g.p_nom_extendable]
        caps_meta = {}
        for c, cap in plans.items():
            sel = nuc.index[nuc.bus.map(n.buses.country) == c]
            if float(cap) <= 0:
                n.generators.loc[sel, "p_nom_max"] = 0.0
            else:
                caps_meta[c] = dict(cap_mw=float(cap), generators=sorted(sel))
        n.meta["research_nuclear_caps"] = caps_meta
        n.meta["required_constraint_hooks"] = sorted(set(n.meta.get("required_constraint_hooks", [])) | {NUCLEAR_HOOK})
        led["nuclear"]["caps"] = {c: v["cap_mw"] for c, v in caps_meta.items()}
    elif ncap != "none":
        raise ValueError("Unknown research.candidates.nuclear_cap " + ncap)
    n.meta["research_candidates_s4b2"] = led
    return led


def install_new_hydro_inflow_tie(n):
    """Usable inflow of every capped new reservoir <= inflow per MW x built capacity: spill_t + r_t p_nom >= inflow_t."""
    if getattr(n, "_research_hydro_tie_model", None) is n.model:
        raise ValueError("New hydro inflow hook already installed")
    m = n.model; names = n.meta.get("research_new_hydro_inflow_tie", [])
    inflow = n.get_switchable_as_dense("StorageUnit", "inflow")
    spill = m["StorageUnit-spill"]; p_nom = m["StorageUnit-p_nom"]
    import xarray as xr
    for name in names:
        cap = float(n.storage_units.at[name, "p_nom_max"]); q = inflow[name]
        r = xr.DataArray((q / cap).values, coords={"snapshot": n.snapshots}, dims=["snapshot"]); rhs = xr.DataArray(q.values, coords={"snapshot": n.snapshots}, dims=["snapshot"])
        m.add_constraints(spill.sel(StorageUnit=name) + r * p_nom.sel({"StorageUnit-ext": name}) >= rhs, name=f"research_new_hydro_inflow-{name}")
    n._research_hydro_tie_model = m


def install_nuclear_national_cap(n):
    if getattr(n, "_research_nuclear_cap_model", None) is n.model:
        raise ValueError("Nuclear cap hook already installed")
    m = n.model; p_nom = m["Generator-p_nom"]
    for c, v in n.meta.get("research_nuclear_caps", {}).items():
        gens = [x for x in v["generators"] if x in p_nom.coords["Generator-ext"].values]
        if gens:
            m.add_constraints(p_nom.sel({"Generator-ext": gens}).sum() <= float(v["cap_mw"]), name=f"research_nuclear_national_cap-{c}")
    n._research_nuclear_cap_model = m
