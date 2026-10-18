"""S4J model layers (S4J instruction v1, 2026-10-18; decisions 104-106).

S4J-2 (decision 105 a): research.network.transmission_losses = pypsa_eur (main) | none (S4H state, comparison; default when absent).
  pypsa_eur follows PyPSA-Eur v2025.07.0 (registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml lines 747-763 transmission_efficiency,
  line 1001 solving.options.transmission_losses: 2; prepare_sector_network.py lossy_bidirectional_links lines 5727-5774, called at 6445-6447):
  * AC lines: the solver gets transmission_losses = 2 (PyPSA piecewise-linear loss approximation, pypsa.optimization.constraints
    define_loss_constraints); s2_solve.py reads it from n.meta['research_transmission_losses'].
  * DC links: efficiency = 0.98 x 0.977^(length / 1000 km). H2 pipelines: efficiency 1, compression 0.018 MWh_el per MWh and 1000 km; gas
    pipelines: efficiency 1, compression 0.01. CO2 pipelines: no losses (as PyPSA-Eur). The distribution-grid efficiency 0.97 is not used (S4I R10).
  * Every bidirectional link of these carriers (p_min_pu < 0) is split as in lossy_bidirectional_links: the link keeps its capital cost with
    p_min_pu = 0; a copy '<name>-reversed' with bus0 / bus1 swapped, capital_cost 0, length 0 (length_original kept), no existing FOM, reversed =
    True. The compression port bus2 = electricity bus of the sending end (bus0 location) with efficiency2 = -c x length_original / 1000, for the
    forward and the reversed link. One-way links (p_min_pu = 0) get the efficiency / compression but no reverse copy (PyPSA-Eur splits
    'bidirectional links'; the one-way existing gas pipelines of S4I R11 keep their direction).
  * The reverse capacity equals the forward capacity: hook research_lossy_bidirectional_sync (Link-p_nom of '<name>-reversed' == Link-p_nom of
    '<name>' for extendable links). PyPSA-Eur adds the same equality in solve_network.py (add_lossy_bidirectional_link_constraints, constraint
    'Link-bidirectional_sync'); solve_network.py is not in the repository - implemented with the same meaning.
  * Same rule for domestic and cross-border, both scenarios, stock and candidates. Applied after the cross-border switches and the individual
    extension limit (the reverse copy inherits p_nom, p_nom_min, p_nom_max).
S4J-3 (decision 105 b, S4I U2): apply_dc_converter_rule, before apply_transmission_losses, both loss modes.
  * One-way DC links (p_min_pu >= 0; only TH-MY Khlong Ngae - Gurun) become bidirectional (p_min_pu = -1; with pypsa_eur losses then split into a
    lossy forward / reverse pair).
  * Converter-station structure: a DC bus with exactly one DC link and exactly one B2B link. Its B2B converter (fixed 2,000 MW in the frozen base)
    becomes extendable at no capital cost (the DC link cost includes the converter pair, decision-50 cost layer) and follows the DC link: B2B p_nom -
    B2B p_nom_existing = DC p_nom - DC p_nom_existing (hook research_b2b_follows_dc), p_nom_min = existing, p_nom_max = existing + the DC link's
    extension room; bidirectional like the DC link, lossless (PyPSA-Eur applies no transmission efficiency to B2B). The increment form keeps the
    existing 2,000 MW: the DC buses also carry generation candidates (TH21 0: CCGT / OCGT / FT; MY_Peninsular22 0: offshore wind, CCGT / OCGT / FT)
    whose only path to the AC grid is the B2B.
  * DC buses with another structure (e.g. PH_Visayas10 0: two DC links + one B2B) or without a DC link (disconnected scenario) are reported, not changed.
"""
from __future__ import annotations

import pandas as pd

LOSS_EFFICIENCY = {   # PyPSA-Eur v2025.07.0 config.default.yaml sector.transmission_efficiency (enable: DC, H2 pipeline, gas pipeline, distribution grid)
    "DC": dict(efficiency_static=0.98, efficiency_per_1000km=0.977, compression_per_1000km=0.0),
    "H2 pipeline": dict(efficiency_static=1.0, efficiency_per_1000km=1.0, compression_per_1000km=0.018),
    "gas pipeline": dict(efficiency_static=1.0, efficiency_per_1000km=1.0, compression_per_1000km=0.01),
}
AC_TRANSMISSION_LOSSES = 2   # PyPSA-Eur v2025.07.0 config.default.yaml solving.options.transmission_losses (line 1001)
SYNC_HOOK = "research_lossy_bidirectional_sync"
B2B_HOOK = "research_b2b_follows_dc"
REV = "-reversed"


def apply_dc_converter_rule(n) -> dict:
    """S4J-3 (decision 105 b): see the module docstring. Call after apply_max_extension and before apply_transmission_losses."""
    if "reversed" in n.links and n.links.reversed.astype(bool).any():
        raise ValueError("the DC converter rule must run before the lossy split")
    dc = n.links[n.links.carrier == "DC"]; b2b = n.links[n.links.carrier == "B2B"]
    oneway = list(dc.index[dc.p_min_pu >= 0])
    n.links.loc[oneway, "p_min_pu"] = -1.0
    pairs, reported = [], []
    for bus in sorted(n.buses.index[n.buses.carrier == "DC"]):
        dcl = [k for k in dc.index if bus in (dc.at[k, "bus0"], dc.at[k, "bus1"])]
        bb = [k for k in b2b.index if bus in (b2b.at[k, "bus0"], b2b.at[k, "bus1"])]
        if not bb:
            continue
        if len(dcl) == 1 and len(bb) == 1:
            k, c = dcl[0], bb[0]
            if not bool(n.links.at[k, "p_nom_extendable"]):
                raise ValueError(f"DC link {k} not extendable")
            room = float(n.links.at[k, "p_nom_max"]) - float(n.links.at[k, "p_nom"])
            p0 = float(n.links.at[c, "p_nom"])
            pairs.append(dict(dc_bus=bus, dc_link=k, b2b=c, b2b_p_nom_existing=p0, dc_p_nom_existing=float(n.links.at[k, "p_nom"]), b2b_p_nom_max=p0 + room,
                              b2b_capital_cost_before=float(n.links.at[c, "capital_cost"]), b2b_extendable_before=bool(n.links.at[c, "p_nom_extendable"])))
            n.links.loc[c, ["p_nom_extendable", "capital_cost", "p_nom_min", "p_nom_max", "p_min_pu"]] = [True, 0.0, p0, p0 + room, -1.0]
        else:
            reported.append(dict(dc_bus=bus, dc_links=dcl, b2b=bb, reason=("no DC link at the bus (removed by the cross-border switch)" if not dcl
                                                                            else "structure differs from a converter station (one DC link + one B2B)")))
    if pairs:
        n.meta["required_constraint_hooks"] = sorted(set(n.meta.get("required_constraint_hooks", [])) | {B2B_HOOK})
    led = dict(one_way_made_bidirectional=oneway, pairs=pairs, reported=reported)
    n.meta["research_dc_converters"] = led
    return led


def install_b2b_follows_dc(n) -> int:
    """research_b2b_follows_dc hook: B2B p_nom - B2B existing = DC link p_nom - DC existing for every converter-station pair."""
    if getattr(n, "_research_b2b_model", None) is n.model:
        raise ValueError("B2B follows DC hook already installed")
    m = n.model; pn = m["Link-p_nom"]; pairs = (n.meta.get("research_dc_converters") or {}).get("pairs", [])
    for i, p in enumerate(pairs):
        m.add_constraints(pn.sel({"Link-ext": p["b2b"]}) - pn.sel({"Link-ext": p["dc_link"]}) == float(p["b2b_p_nom_existing"]) - float(p["dc_p_nom_existing"]),
                          name=f"{B2B_HOOK}-{i}")
    n._research_b2b_model = m
    return len(pairs)


def transmission_losses_mode(cfg) -> str:
    v = str((cfg["research"].get("network") or {}).get("transmission_losses", "none")).lower()
    if v not in ("pypsa_eur", "none"):
        raise ValueError("Unknown research.network.transmission_losses " + v)
    return v


def _electricity_bus(n, bus: str) -> str:
    """Electricity (AC / DC node) bus at the location of a carrier bus: its location, else the node-name prefix ('<node> gas' -> '<node>')."""
    geo = n.buses.index[n.buses.carrier.isin(["AC", "DC"])]
    loc = str(n.buses.at[bus, "location"]) if "location" in n.buses else ""
    if loc in geo:
        return loc
    for g in sorted(geo, key=len, reverse=True):
        if bus.startswith(g + " "):
            return g
    raise ValueError(f"no electricity bus for the compression port of {bus}")


def apply_transmission_losses(n, cfg) -> dict:
    """S4J-2 (decision 105 a): see the module docstring. Call after apply_max_extension."""
    mode = transmission_losses_mode(cfg)
    led = dict(mode=mode, ac_transmission_losses=(AC_TRANSMISSION_LOSSES if mode == "pypsa_eur" else 0))
    if mode == "none":
        n.meta["research_transmission_losses"] = led
        return led
    if "reversed" in n.links and n.links.reversed.astype(bool).any():
        raise ValueError("transmission losses applied twice")
    n.links["reversed"] = False
    n.links["length_original"] = n.links["length"]
    rows, rev_all = {}, []
    for car, par in LOSS_EFFICIENCY.items():
        idx = n.links.index[n.links.carrier == car]
        if idx.empty:
            continue
        L = n.links.loc[idx, "length"].astype(float)
        if (L <= 0).any():
            raise ValueError(f"{car} links without length: {list(idx[L <= 0])[:3]}")
        n.links.loc[idx, "efficiency"] = par["efficiency_static"] * par["efficiency_per_1000km"] ** (L / 1e3)
        bidir = idx[n.links.loc[idx, "p_min_pu"] < 0]
        oneway = idx.difference(bidir)
        n.links.loc[bidir, "p_min_pu"] = 0.0
        rev = n.links.loc[bidir].copy().rename(columns={"bus0": "bus1", "bus1": "bus0"})
        rev["capital_cost"] = 0.0; rev["length"] = 0.0; rev["reversed"] = True
        if "existing_annual_fixed_om_eur" in rev:
            rev["existing_annual_fixed_om_eur"] = 0.0
        rev.index = [x + REV for x in bidir]; rev.index.name = "Link"
        if set(rev.index) & set(n.links.index):
            raise ValueError(f"{car}: reverse link name exists already")
        rev_all.append(rev)
        rows[car] = dict(links=int(len(idx)), bidirectional_split=int(len(bidir)), one_way_kept=sorted(map(str, oneway)), **par,
                         efficiency_min=float(n.links.loc[idx, "efficiency"].min()), efficiency_max=float(n.links.loc[idx, "efficiency"].max()))
    if rev_all:
        R = pd.concat(rev_all)
        n.import_components_from_dataframe(R[[c for c in R.columns if c in n.links.columns]], "Link")
        n.links.loc[R.index, "reversed"] = True
    n.links["reversed"] = n.links["reversed"].fillna(False).astype(bool)
    n.links["length_original"] = n.links["length_original"].astype(float)
    for car, par in LOSS_EFFICIENCY.items():   # compression after the copy: electricity drawn at bus0 in either direction (PyPSA-Eur)
        c = par["compression_per_1000km"]
        if c <= 0:
            continue
        idx = n.links.index[n.links.carrier == car]
        n.links.loc[idx, "bus2"] = [_electricity_bus(n, b) for b in n.links.loc[idx, "bus0"]]
        n.links.loc[idx, "efficiency2"] = -c * n.links.loc[idx, "length_original"].astype(float) / 1e3
        rows[car].update(compression_links=int(len(idx)), efficiency2_min=float(n.links.loc[idx, "efficiency2"].min()),
                         efficiency2_max=float(n.links.loc[idx, "efficiency2"].max()))
    rev_ext = n.links.index[n.links.reversed & n.links.p_nom_extendable]
    if len(rev_ext):
        n.meta["required_constraint_hooks"] = sorted(set(n.meta.get("required_constraint_hooks", [])) | {SYNC_HOOK})
    led.update(carriers=rows, reversed_links=int(n.links.reversed.sum()), reversed_extendable=int(len(rev_ext)),
               sources="PyPSA-Eur v2025.07.0 config.default.yaml 747-763, 1001; prepare_sector_network.py 5727-5774 (lossy_bidirectional_links), 6445-6447; "
                       "solve_network.py add_lossy_bidirectional_link_constraints not in the repository (same meaning: reverse p_nom = forward p_nom)")
    n.meta["research_transmission_losses"] = led
    return led


def install_lossy_bidirectional_sync(n) -> int:
    """research_lossy_bidirectional_sync hook: Link-p_nom['<x>-reversed'] == Link-p_nom['<x>'] for every extendable reversed link."""
    if getattr(n, "_research_sync_model", None) is n.model:
        raise ValueError("lossy bidirectional sync hook already installed")
    m = n.model
    rev = [x for x in n.links.index[n.links.reversed.astype(bool) & n.links.p_nom_extendable]]
    pn = m["Link-p_nom"]
    for i, x in enumerate(rev):   # one scalar row per pair (no coordinate alignment between the two labels)
        f = x[: -len(REV)]
        if not bool(n.links.at[f, "p_nom_extendable"]):
            raise ValueError(f"forward link {f} not extendable while {x} is")
        m.add_constraints(pn.sel({"Link-ext": x}) - pn.sel({"Link-ext": f}) == 0, name=f"{SYNC_HOOK}-{i}")
    n._research_sync_model = m
    return len(rev)


def loss_summary(n) -> dict:
    """Post-solve: losses by carrier (TWh) - AC lines from p0 + p1, links from p0 + p1 (+ compression p2 for pipelines, reported apart)."""
    w = n.snapshot_weightings.objective; out = {}
    if len(n.lines) and "p0" in n.lines_t and len(n.lines_t.p0.columns):
        out["AC"] = float(((n.lines_t.p0 + n.lines_t.p1).mul(w, axis=0)).sum().sum() / 1e6)
    for car in LOSS_EFFICIENCY:
        idx = n.links.index[n.links.carrier == car]
        if idx.empty:
            continue
        p0 = n.links_t.p0.reindex(columns=idx, fill_value=0.0); p1 = n.links_t.p1.reindex(columns=idx, fill_value=0.0)
        out[car] = float(((p0 + p1).mul(w, axis=0)).sum().sum() / 1e6)
        if "p2" in n.links_t and car != "DC":
            out[car + " compression electricity"] = float((n.links_t.p2.reindex(columns=idx, fill_value=0.0).mul(w, axis=0)).sum().sum() / 1e6)
    return out
