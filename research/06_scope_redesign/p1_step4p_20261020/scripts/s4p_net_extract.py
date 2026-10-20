"""S4P: read-only extraction of structure and (where solved) results from a PyPSA network file.
Usage: python s4p_net_extract.py <label> <network.nc>
Outputs NET_<label>_{generators,links,lines,stores,storage_units,loads,buses,prices,meta}.csv/json under evidence/net/.
Nothing is written to the network; the file is opened read-only."""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4p_paths import OUT, dump_json  # noqa: E402

import pypsa  # noqa: E402

EVID = OUT / "evidence" / "net"


def country_of(n, bus):
    return n.buses.country.reindex(bus).fillna("").astype(str).values


def main(label: str, path: str):
    n = pypsa.Network(path)
    EVID.mkdir(parents=True, exist_ok=True)
    w = n.snapshot_weightings.objective
    solved = len(n.generators_t.p.columns) > 0 and n.generators_t.p.shape[0] == len(n.snapshots)
    meta = {"label": label, "file": path, "snapshots": len(n.snapshots), "weight_sum": float(w.sum()), "solved": bool(solved),
            "objective": float(n.objective) if hasattr(n, "objective") and n.objective is not None else None,
            "n_buses": len(n.buses), "n_generators": len(n.generators), "n_links": len(n.links), "n_lines": len(n.lines), "n_stores": len(n.stores),
            "n_storage_units": len(n.storage_units), "n_loads": len(n.loads)}
    bus_country = n.buses.country.astype(str)
    bus_carrier = n.buses.carrier.astype(str)

    # ---- buses
    b = n.buses[["carrier", "country"]].copy()
    if solved:
        pr = n.buses_t.marginal_price
        b["price_mean_w"] = (pr.mul(w, axis=0).sum() / w.sum()).reindex(b.index)
        b["price_min"] = pr.min().reindex(b.index); b["price_max"] = pr.max().reindex(b.index)
        b["price_std"] = pr.std().reindex(b.index)
    b.to_csv(EVID / f"NET_{label}_buses.csv")

    # ---- generators
    g = n.generators.copy()
    g["country"] = bus_country.reindex(g.bus).values
    g["bus_carrier"] = bus_carrier.reindex(g.bus).values
    cols = ["bus", "carrier", "country", "bus_carrier", "p_nom", "p_nom_extendable", "p_nom_min", "p_nom_max", "marginal_cost", "capital_cost", "efficiency"]
    if solved:
        g["p_nom_opt"] = n.generators.p_nom_opt
        e = n.generators_t.p.mul(w, axis=0).sum()
        g["energy_mwh"] = e.reindex(g.index).fillna(0.0)
        cf_den = (g.p_nom_opt * w.sum()).replace(0, np.nan)
        g["cf"] = g.energy_mwh / cf_den
        # weighted mean availability
        pmax = n.get_switchable_as_dense("Generator", "p_max_pu")
        g["p_max_pu_mean"] = (pmax.mul(w, axis=0).sum() / w.sum()).reindex(g.index)
        cols += ["p_nom_opt", "energy_mwh", "cf", "p_max_pu_mean"]
    else:
        pmax = n.get_switchable_as_dense("Generator", "p_max_pu")
        g["p_max_pu_mean"] = (pmax.mul(w, axis=0).sum() / w.sum()).reindex(g.index)
        cols += ["p_max_pu_mean"]
    for c in ("existing_annual_fixed_om_eur", "build_year", "lifetime"):
        if c in g:
            cols.append(c)
    g[cols].to_csv(EVID / f"NET_{label}_generators.csv")

    # ---- links
    l = n.links.copy()
    l["country0"] = bus_country.reindex(l.bus0).values
    l["country1"] = bus_country.reindex(l.bus1).values
    l["bus0_carrier"] = bus_carrier.reindex(l.bus0).values
    l["bus1_carrier"] = bus_carrier.reindex(l.bus1).values
    if "bus2" in l:
        l["bus2_carrier"] = bus_carrier.reindex(l.bus2.replace("", np.nan)).values
    cols = ["bus0", "bus1", "carrier", "country0", "country1", "bus0_carrier", "bus1_carrier", "p_nom", "p_nom_extendable", "p_nom_min", "p_nom_max",
            "p_min_pu", "p_max_pu", "efficiency", "marginal_cost", "capital_cost", "length"]
    for c in ("border_class", "existing_annual_fixed_om_eur", "bus2", "bus2_carrier", "efficiency2", "bus3", "efficiency3", "subsea_share"):
        if c in l:
            cols.append(c)
    if solved:
        l["p_nom_opt"] = n.links.p_nom_opt
        p0 = n.links_t.p0
        l["energy_p0_pos_mwh"] = p0.clip(lower=0).mul(w, axis=0).sum().reindex(l.index).fillna(0.0)
        l["energy_p0_neg_mwh"] = (-p0.clip(upper=0)).mul(w, axis=0).sum().reindex(l.index).fillna(0.0)
        l["energy_p1_mwh"] = n.links_t.p1.mul(w, axis=0).sum().reindex(l.index).fillna(0.0)
        l["max_abs_p0"] = p0.abs().max().reindex(l.index).fillna(0.0)
        cols += ["p_nom_opt", "energy_p0_pos_mwh", "energy_p0_neg_mwh", "energy_p1_mwh", "max_abs_p0"]
        # settlement at each end (owner pays withdrawals): p0 at bus0 price, p1 at bus1 price
        pr = n.buses_t.marginal_price
        s0 = (p0 * pr.reindex(columns=l.bus0.values).set_axis(l.index, axis=1)).mul(w, axis=0).sum()
        s1 = (n.links_t.p1 * pr.reindex(columns=l.bus1.values).set_axis(l.index, axis=1)).mul(w, axis=0).sum()
        l["settle_bus0_eur"] = s0.reindex(l.index); l["settle_bus1_eur"] = s1.reindex(l.index)
        cols += ["settle_bus0_eur", "settle_bus1_eur"]
    l[cols].to_csv(EVID / f"NET_{label}_links.csv")

    # ---- lines
    ln = n.lines.copy()
    ln["country0"] = bus_country.reindex(ln.bus0).values
    ln["country1"] = bus_country.reindex(ln.bus1).values
    cols = ["bus0", "bus1", "carrier", "country0", "country1", "s_nom", "s_nom_extendable", "s_nom_min", "s_nom_max", "s_max_pu", "capital_cost", "length", "num_parallel", "x", "r"]
    for c in ("border_class", "existing_annual_fixed_om_eur", "subsea_share", "type"):
        if c in ln:
            cols.append(c)
    if solved:
        ln["s_nom_opt"] = n.lines.s_nom_opt
        p0 = n.lines_t.p0
        ln["energy_p0_pos_mwh"] = p0.clip(lower=0).mul(w, axis=0).sum().reindex(ln.index).fillna(0.0)
        ln["energy_p0_neg_mwh"] = (-p0.clip(upper=0)).mul(w, axis=0).sum().reindex(ln.index).fillna(0.0)
        ln["max_abs_p0"] = p0.abs().max().reindex(ln.index).fillna(0.0)
        pr = n.buses_t.marginal_price
        s0 = (p0 * pr.reindex(columns=ln.bus0.values).set_axis(ln.index, axis=1)).mul(w, axis=0).sum()
        s1 = (n.lines_t.p1 * pr.reindex(columns=ln.bus1.values).set_axis(ln.index, axis=1)).mul(w, axis=0).sum()
        ln["settle_bus0_eur"] = s0.reindex(ln.index); ln["settle_bus1_eur"] = s1.reindex(ln.index)
        cols += ["s_nom_opt", "energy_p0_pos_mwh", "energy_p0_neg_mwh", "max_abs_p0", "settle_bus0_eur", "settle_bus1_eur"]
    ln[cols].to_csv(EVID / f"NET_{label}_lines.csv")

    # ---- stores
    s = n.stores.copy()
    s["country"] = bus_country.reindex(s.bus).values
    s["bus_carrier"] = bus_carrier.reindex(s.bus).values
    cols = ["bus", "carrier", "country", "bus_carrier", "e_nom", "e_nom_extendable", "e_nom_min", "e_nom_max", "e_cyclic", "e_initial", "marginal_cost", "capital_cost", "e_min_pu", "e_max_pu"]
    if solved:
        s["e_nom_opt"] = n.stores.e_nom_opt
        s["e_final"] = n.stores_t.e.iloc[-1].reindex(s.index)
        s["e_max_level"] = n.stores_t.e.max().reindex(s.index)
        s["e_min_level"] = n.stores_t.e.min().reindex(s.index)
        s["p_withdraw_mwh"] = n.stores_t.p.clip(lower=0).mul(w, axis=0).sum().reindex(s.index)
        s["p_inject_mwh"] = (-n.stores_t.p.clip(upper=0)).mul(w, axis=0).sum().reindex(s.index)
        s["bus_price_mean_w"] = b["price_mean_w"].reindex(s.bus).values
        cols += ["e_nom_opt", "e_final", "e_max_level", "e_min_level", "p_withdraw_mwh", "p_inject_mwh", "bus_price_mean_w"]
    s[cols].to_csv(EVID / f"NET_{label}_stores.csv")

    # ---- storage units
    su = n.storage_units.copy()
    su["country"] = bus_country.reindex(su.bus).values
    cols = ["bus", "carrier", "country", "p_nom", "p_nom_extendable", "p_nom_max", "max_hours", "marginal_cost", "capital_cost"]
    if solved:
        su["p_nom_opt"] = n.storage_units.p_nom_opt
        su["dispatch_mwh"] = n.storage_units_t.p_dispatch.mul(w, axis=0).sum().reindex(su.index)
        su["inflow_mwh"] = n.storage_units_t.inflow.mul(w, axis=0).sum().reindex(su.index) if len(n.storage_units_t.inflow.columns) else 0.0
        cols += ["p_nom_opt", "dispatch_mwh", "inflow_mwh"]
    else:
        su["inflow_mwh"] = n.storage_units_t.inflow.mul(w, axis=0).sum().reindex(su.index) if len(n.storage_units_t.inflow.columns) else 0.0
        cols += ["inflow_mwh"]
    su[cols].to_csv(EVID / f"NET_{label}_storage_units.csv")

    # ---- loads
    ld = n.loads.copy()
    ld["country_bus"] = bus_country.reindex(ld.bus).values
    ld["bus_carrier"] = bus_carrier.reindex(ld.bus).values
    pset = n.get_switchable_as_dense("Load", "p_set")
    ld["energy_mwh"] = pset.mul(w, axis=0).sum().reindex(ld.index)
    ld["peak_mw"] = pset.max().reindex(ld.index)
    cols = ["bus", "carrier", "country_bus", "bus_carrier", "energy_mwh", "peak_mw"]
    if "country" in ld:
        cols.insert(2, "country")
    if solved:
        ld["bus_price_mean_w"] = b["price_mean_w"].reindex(ld.bus).values
        ld["cost_at_price_eur"] = (pset * n.buses_t.marginal_price.reindex(columns=ld.bus.values).set_axis(ld.index, axis=1)).mul(w, axis=0).sum().reindex(ld.index)
        cols += ["bus_price_mean_w", "cost_at_price_eur"]
    ld[cols].to_csv(EVID / f"NET_{label}_loads.csv")

    # ---- global constraints
    gc = n.global_constraints.copy()
    if len(gc):
        gc.to_csv(EVID / f"NET_{label}_global_constraints.csv")
    meta["research_meta_keys"] = sorted(list(n.meta.keys()))[:200] if isinstance(n.meta, dict) else []
    dump_json(meta, EVID / f"NET_{label}_meta.json")
    print(json.dumps(meta, indent=1)[:1500])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
