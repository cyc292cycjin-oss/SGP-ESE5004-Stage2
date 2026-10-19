"""S4L model layer (S4L instruction v1, 2026-10-19; decision 113 (1)): near-zero quantities ('dust') - inventory and cleanup.

Switch (configs/research/baseline.yaml):
  research.numerics.dust_cleanup: off (default; S4K state) | on (main-run candidate; the user decides after the S4L report)
  research.numerics.dust_energy_mwh: 1000 (1 GWh per year) and research.numerics.dust_capacity_mw: 1 (1 MW): B-level thresholds (S4L-1 point 2).

Background (L23 first batch, report section 6): the primal violations of the four non-optimal 365x24h runs sit on near-zero quantities -
the SG / BN / TL biomass pools of a few MWh (SG cassava residues 0.47 MWh: violation 0.91 MWh = 902 x budget), the unused extra-ASEAN CO2
stores, the zero-capacity FT links and the H2 bus balances. Relaxing the convergence tolerance only changes the termination label; the
near-zero objects without economic meaning are removed here, the ones with economic meaning (zero-capacity but extendable FT links, the
extra-ASEAN CO2 export stores) are kept and only listed.

Classes (inventory; action = delete unless stated):
  biomass_pool_below_energy        Store research_role FINITE_RESOURCE with e_nom < dust_energy_mwh (SG / BN / TL / MY pools of 0.5-800 MWh) - ONLY while the
                                   pools of the same bus keep covering the fixed demand fed from that bus (S4L-2 finding: in BN, SG and VN the solid biomass pools
                                   equal the fixed biomass final demand exactly, so deleting any pool there makes the model infeasible; such pools are kept and
                                   listed as kept_pool_fixed_demand_binding);
  renewable_potential_below_capacity   extendable renewable Generator with p_nom = 0 and p_nom_max < dust_capacity_mw (incl. the zero caps);
  renewable_potential_below_energy     extendable renewable Generator with p_nom_max >= threshold but p_nom_max x sum(p_max_pu w) < dust_energy_mwh;
  all_zero_profile_generator       Generator with p_max_pu identically 0 and p_nom = 0 (S4I R5: 3 offwind-dc);
  zero_upper_candidate             extendable Generator / StorageUnit / Link / Store (non-renewable or storage / conversion) with p_nom (e_nom) = 0
                                   and p_nom_max (e_nom_max) < threshold (S4I R4: 61 pumpable hydro, 86 PHS at 0.75, 71 ror without profile,
                                   zero-cap geothermal - all p_nom_max = 0);
  all_zero_load                    Load with p_set identically 0 (S4I R5: 38 'shipping domestic methanol');
  single_attachment_fuel_bus       Bus with carrier in FUEL_BUS_CARRIERS and exactly one attachment (S4I R1: 128 coal / lignite / oil buses) - the
                                   bus and its single attachment (a fuel supply Generator or a Link port that cannot carry flow) are removed; a
                                   Link port with zero efficiency on such a bus is kept and only listed (class single_attachment_fuel_bus_kept);
  identical_parallel_link          Links with identical static attributes, no time series, p_nom = p_nom_min = 0, extendable (S4I R3: 94 of the 97
                                   'biomass-to-methanol' links) - action merge: one link per group keeps the first name (sorted), p_nom_max =
                                   N x p_nom_max (inf stays inf); capacity and cost equivalent;
  kept (record only)               Fischer-Tropsch links (p_nom 0, extendable, unbounded; economic candidates), the extra-ASEAN CO2 stores
                                   (uncapped export option, decision 89), fixed Generators with p_nom < dust_capacity_mw (plastic waste sources:
                                   exogenous data, not candidates).
PyPSA-Eur v2025.07.0 (research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml) has no component cleanup step; the nearest
settings are renewable.*.clip_p_max_pu 1e-2 (lines 200 / 218 / 237 / 259 / 276 / 292; applied in this model by S4A, research.renewable.clip_p_max_pu),
solving.options.clip_p_max_pu 1e-2 (line 988), renewable.hydro.clip_min_inflow 1.0 MW (line 300: inflow below 1 MW set to 0 - the capacity
threshold adopted here), existing_capacities.threshold_capacity 10 MW (line 469: existing plants below 10 MW dropped in add_existing_baseyear -
not adopted: existing stock is not touched here) and sector.regional_co2_sequestration_potential.min_size 3 Mt (line 700). The 1 GWh energy
threshold is a project choice (S4L-1 point 2): about 0.1 MW-year, below what any conversion candidate would be built for, and the scale of the
pools that carried the largest violation ratios in L23.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DUST_MODES = ("on", "off")
DEFAULT_ENERGY_MWH = 1000.0
DEFAULT_CAPACITY_MW = 1.0
FUEL_BUS_CARRIERS = ("coal", "lignite", "oil", "gas")
RENEWABLE_CARRIERS = ("solar", "solar rooftop", "onwind", "offwind-ac", "offwind-dc", "ror", "ror_new", "geothermal", "hydro", "hydro_new", "PHS", "PHS_new")
REQUIRED_STRUCTURE = {"Generator": ("nuclear SMR", "geothermal", "ror", "solar", "onwind"), "StorageUnit": ("hydro", "PHS")}   # build_research_network.REQUIRED_PER_NODE
KEEP_CARRIERS = ("Fischer-Tropsch",)
PYPSA_EUR_REFS = dict(config="research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml",
                      renewable_clip_p_max_pu=dict(value=0.01, lines=[200, 218, 237, 259, 276, 292], note="applied in this model by S4A (research.renewable.clip_p_max_pu)"),
                      solving_clip_p_max_pu=dict(value=0.01, line=988), hydro_clip_min_inflow_mw=dict(value=1.0, line=300, adopted_as="dust_capacity_mw"),
                      existing_threshold_capacity_mw=dict(value=10.0, line=469, adopted=False, note="existing stock is not touched"),
                      co2_sequestration_min_size_mt=dict(value=3.0, line=700, adopted=False),
                      energy_threshold="no PyPSA-Eur equivalent: project choice 1 GWh/a (S4L-1 point 2)")


def dust_mode(cfg) -> str:
    raw = (cfg["research"].get("numerics") or {}).get("dust_cleanup", "off")   # YAML 1.1 reads on / off as booleans
    v = ("on" if raw else "off") if isinstance(raw, bool) else str(raw).lower()
    v = {"true": "on", "1": "on", "yes": "on", "false": "off", "0": "off", "no": "off"}.get(v, v)
    if v not in DUST_MODES:
        raise ValueError("Unknown research.numerics.dust_cleanup " + v)
    return v


def thresholds(cfg) -> dict:
    N = cfg["research"].get("numerics") or {}
    e = float(N.get("dust_energy_mwh", DEFAULT_ENERGY_MWH)); c = float(N.get("dust_capacity_mw", DEFAULT_CAPACITY_MW))
    if e <= 0 or c <= 0:
        raise ValueError("research.numerics thresholds must be positive")
    return dict(energy_mwh=e, capacity_mw=c)


def _ports(df) -> list:
    return [c for c in df.columns if c == "bus" or (c.startswith("bus") and c[3:].isdigit())]


def attachments(n) -> dict:
    """bus -> list of (component type, name, port column)."""
    out = {b: [] for b in n.buses.index}
    for t in ("Generator", "Load", "Store", "StorageUnit"):
        d = n.df(t)
        for name, b in d.bus.items():
            if b in out:
                out[b].append((t, name, "bus"))
    for t in ("Line", "Transformer", "Link"):
        d = n.df(t)
        for p in [c for c in _ports(d) if c != "bus"]:
            for name, b in d[p].items():
                if isinstance(b, str) and b and b in out:
                    out[b].append((t, name, p))
    return out


def _node_of(n, bus: str) -> str:
    geo = n.buses.index[n.buses.carrier.isin(["AC", "DC"])]
    if bus in geo:
        return bus
    for g in sorted(geo, key=len, reverse=True):
        if str(bus).startswith(g + " "):
            return g
    loc = str(n.buses.at[bus, "location"]) if "location" in n.buses else ""
    return loc if loc in geo else str(bus)


def pool_fixed_demand(n, bus: str) -> float:
    """Yearly fixed demand (MWh) that the finite pools on `bus` have to cover: Loads on the bus itself plus Loads on every bus fed by a Link
    leaving `bus` (the S2 '... biomass meter' and '... biomass CC' links into the '<node> ... biomass final' buses). Conservative: a downstream
    bus with another supplier is still counted in full."""
    w = n.snapshot_weightings.generators
    ann = n.get_switchable_as_dense("Load", "p_set").mul(w, axis=0).sum()
    down = set(n.links.bus1[n.links.bus0 == bus].astype(str)) | {bus}
    return float(ann[n.loads.index[n.loads.bus.isin(down)]].sum()) if len(n.loads) else 0.0


def pool_balance(n) -> list:
    """Per finite-pool bus: pools, total energy, fixed demand fed from the bus, slack (negative = structurally infeasible), binding flag."""
    st = n.stores
    if "research_role" not in st:
        return []
    out = []
    for bus, grp in st[st.research_role == "FINITE_RESOURCE"].groupby("bus"):
        total = float(grp.e_nom.sum()); dem = pool_fixed_demand(n, str(bus))
        out.append(dict(bus=str(bus), country=str(grp.country.iloc[0]), pools=int(len(grp)), pool_total_mwh=total, fixed_demand_mwh=dem, slack_mwh=total - dem,
                        binding=bool(abs(total - dem) <= 1e-3 * max(dem, 1.0))))
    return out


def identical_link_groups(n) -> list:
    """Groups of links with identical static attributes (every column except the name), no time series, p_nom = p_nom_min = 0, extendable,
    no twin relation. Returns [(kept name, [other members])]."""
    L = n.links
    if not len(L):
        return []
    series = set()
    for df in n.links_t.values():
        series |= set(df.columns)
    cand = L[(L.p_nom_extendable) & (L.p_nom == 0) & (L.p_nom_min == 0) & (~L.index.isin(list(series)))]
    if "twin_of" in cand:
        cand = cand[cand.twin_of.astype(str).isin(["", "nan", "None"])]
    key = cand.astype(str).agg("|".join, axis=1)
    groups = []
    for _, members in key.groupby(key).groups.items():
        names = sorted(members)
        if len(names) >= 2:
            groups.append((names[0], names[1:]))
    return sorted(groups)


def dust_inventory(n, thr: dict) -> pd.DataFrame:
    """One row per near-zero object: component, name, class, action, country, carrier, bus, capacity_mw, energy_mwh, bound, note."""
    e_thr, c_thr = float(thr["energy_mwh"]), float(thr["capacity_mw"])
    w = n.snapshot_weightings.generators
    rows = []

    bus_country = n.buses.country.astype(str) if "country" in n.buses else pd.Series("", index=n.buses.index)

    def add(component, name, cls, action, country="", carrier="", bus="", capacity_mw=np.nan, energy_mwh=np.nan, bound="", note=""):
        c = str(country) if str(country) not in ("", "nan", "None") else str(bus_country.get(str(bus), ""))   # one-port components without a country column: the bus country
        rows.append(dict(component=component, name=str(name), dust_class=cls, action=action, country=c, carrier=str(carrier), bus=str(bus),
                         capacity_mw=capacity_mw, energy_mwh=energy_mwh, bound=bound, note=note))
    st = n.stores
    if "research_role" in st:
        pools = st[st.research_role == "FINITE_RESOURCE"]
        for bus, grp in pools.groupby("bus"):   # fixed-demand guard (S4L-2 finding): the pools of a bus must keep covering the fixed demand they feed
            total = float(grp.e_nom.sum()); dem = pool_fixed_demand(n, str(bus)); remaining = total
            for name, z in grp.sort_values("e_nom").iterrows():
                if float(z.e_nom) >= e_thr:
                    continue
                if remaining - float(z.e_nom) >= dem - 1e-6:
                    remaining -= float(z.e_nom)
                    add("Store", name, "biomass_pool_below_energy", "delete", z.country, z.carrier, z.bus, energy_mwh=float(z.e_nom), bound="e_nom",
                        note=f"finite pool {float(z.e_nom):.3f} MWh/a < {e_thr:g}; category {z.get('s2_category', '')}; bus pools {total:.1f} MWh, fixed demand {dem:.1f} MWh, slack after deletion {remaining - dem:.1f} MWh")
                else:
                    add("Store", name, "kept_pool_fixed_demand_binding", "keep", z.country, z.carrier, z.bus, energy_mwh=float(z.e_nom), bound="e_nom",
                        note=f"finite pool {float(z.e_nom):.3f} MWh/a < {e_thr:g} but needed: bus pools {total:.1f} MWh vs fixed demand {dem:.1f} MWh (slack {total - dem:.1f} MWh); deleting it would make the fixed demand infeasible (S4L-2 s4l_A runs)")
    stx = st[(st.e_nom_extendable) & (st.e_nom == 0) & (st.e_nom_max < e_thr)]
    for name, z in stx.iterrows():
        add("Store", name, "zero_upper_candidate", "delete", z.get("country", ""), z.carrier, z.bus, energy_mwh=float(z.e_nom_max), bound="e_nom_max")
    for name, z in st[st.carrier.astype(str) == "co2 sequestered extra-ASEAN"].iterrows():
        add("Store", name, "kept_extra_asean_co2_store", "keep", z.get("country", ""), z.carrier, z.bus, energy_mwh=float(z.e_nom_max), bound="e_nom_max",
            note="uncapped extra-ASEAN CO2 export option (decision 89): economic meaning, kept")
    g = n.generators; pmax = n.get_switchable_as_dense("Generator", "p_max_pu"); e_per_mw = pmax.mul(w, axis=0).sum()
    zero_prof = set(g.index[(pmax.max() <= 0).reindex(g.index).fillna(False).to_numpy()])
    for name, z in g.iterrows():
        cap = float(z.p_nom_max); ren = str(z.carrier) in RENEWABLE_CARRIERS; epm = float(e_per_mw.get(name, 0.0))
        if bool(z.p_nom_extendable) and float(z.p_nom) == 0:
            if name in zero_prof:
                add("Generator", name, "all_zero_profile_generator", "delete", z.get("country", ""), z.carrier, z.bus, capacity_mw=cap, energy_mwh=0.0, bound="p_max_pu",
                    note="p_max_pu identically zero (S4I R5)")
            elif cap < c_thr:   # zero upper bound -> zero_upper_candidate (S4I R4) whatever the carrier; a small positive renewable cap -> renewable_potential_below_capacity
                add("Generator", name, "renewable_potential_below_capacity" if (ren and cap > 0) else "zero_upper_candidate", "delete", z.get("country", ""), z.carrier, z.bus,
                    capacity_mw=cap, energy_mwh=cap * epm, bound="p_nom_max", note=("zero upper bound (S4I R4)" if cap == 0 else f"p_nom_max {cap:.4f} MW < {c_thr:g}"))
            elif ren and np.isfinite(cap) and cap * epm < e_thr:
                add("Generator", name, "renewable_potential_below_energy", "delete", z.get("country", ""), z.carrier, z.bus, capacity_mw=cap, energy_mwh=cap * epm, bound="p_nom_max x profile")
        elif not bool(z.p_nom_extendable) and 0 < float(z.p_nom) < c_thr:
            add("Generator", name, "kept_fixed_generator_below_capacity", "keep", z.get("country", ""), z.carrier, z.bus, capacity_mw=float(z.p_nom), energy_mwh=float(z.p_nom) * epm,
                bound="p_nom", note="fixed source (exogenous data), not a candidate: kept")
    su = n.storage_units
    for name, z in su[(su.p_nom_extendable) & (su.p_nom == 0) & (su.p_nom_max < c_thr)].iterrows():
        add("StorageUnit", name, "zero_upper_candidate", "delete", z.get("country", ""), z.carrier, z.bus, capacity_mw=float(z.p_nom_max), energy_mwh=0.0, bound="p_nom_max",
            note=f"efficiency_store {float(z.efficiency_store):.4g}, p_min_pu {float(z.p_min_pu):g} (S4I R4)")
    L = n.links
    for name, z in L[(L.p_nom_extendable) & (L.p_nom == 0) & (L.p_nom_max < c_thr)].iterrows():
        add("Link", name, "zero_upper_candidate", "delete", z.get("country", ""), z.carrier, z.bus0, capacity_mw=float(z.p_nom_max), energy_mwh=0.0, bound="p_nom_max")
    for name, z in L[(L.carrier.astype(str).isin(KEEP_CARRIERS)) & (L.p_nom_extendable) & (L.p_nom == 0)].iterrows():
        add("Link", name, "kept_zero_capacity_extendable_link", "keep", z.get("country", ""), z.carrier, z.bus0, capacity_mw=float(z.p_nom_max), bound="p_nom_max",
            note="zero capacity but extendable with capital cost: economic candidate, kept (L23 violations sat on its bounds)")
    pset = n.get_switchable_as_dense("Load", "p_set")
    for name in pset.columns[(pset.abs().max() == 0).to_numpy()]:
        z = n.loads.loc[name]
        add("Load", name, "all_zero_load", "delete", z.get("country", ""), z.carrier, z.bus, energy_mwh=0.0, bound="p_set", note=f"p_set identically zero (S4I R5); sector {z.get('sector', '')}")
    att = attachments(n)
    for b, z in n.buses[n.buses.carrier.astype(str).isin(FUEL_BUS_CARRIERS)].iterrows():
        a = att.get(b, [])
        if len(a) != 1:
            continue
        t, name, port = a[0]
        if t == "Generator":
            gz = g.loc[name]
            add("Bus", b, "single_attachment_fuel_bus", "delete", z.country, z.carrier, b, note=f"only attachment: Generator {name} (S4I R1)")
            add("Generator", name, "single_attachment_fuel_bus_component", "delete", gz.get("country", ""), gz.carrier, b, capacity_mw=float(gz.p_nom_max), energy_mwh=0.0,
                bound="dead-end bus", note="fuel supply without any consumer on its bus: flow structurally zero")
        elif t == "Link":
            lz = L.loc[name]; eff = 1.0 if port == "bus0" else float(lz.get("efficiency" if port == "bus1" else "efficiency" + port[3:], 0.0))
            if eff != 0:
                add("Bus", b, "single_attachment_fuel_bus", "delete", z.country, z.carrier, b, note=f"only attachment: Link {name} port {port} (S4I R1)")
                add("Link", name, "single_attachment_fuel_bus_component", "delete", lz.get("country", ""), lz.carrier, b, capacity_mw=float(lz.p_nom_max), energy_mwh=0.0,
                    bound="dead-end bus", note=f"link port {port} on a dead-end bus: flow structurally zero")
            else:
                add("Bus", b, "single_attachment_fuel_bus_kept", "keep", z.country, z.carrier, b, note=f"only attachment: Link {name} port {port} with zero efficiency (no flow on this port): kept, listed")
        else:
            add("Bus", b, "single_attachment_fuel_bus_kept", "keep", z.country, z.carrier, b, note=f"only attachment: {t} {name}: kept, listed")
    for keep, members in identical_link_groups(n):
        kz = L.loc[keep]
        add("Link", keep, "identical_parallel_link", "merge_keep", kz.get("country", ""), kz.carrier, kz.bus0, capacity_mw=float(kz.p_nom_max), bound="p_nom_max",
            note=f"group of {1 + len(members)} identical links (S4I R3): kept with p_nom_max x {1 + len(members)}")
        for m in members:
            mz = L.loc[m]
            add("Link", m, "identical_parallel_link", "merge", mz.get("country", ""), mz.carrier, mz.bus0, capacity_mw=float(mz.p_nom_max), bound="p_nom_max", note=f"merged into {keep}")
    cols = ["component", "name", "dust_class", "action", "country", "carrier", "bus", "capacity_mw", "energy_mwh", "bound", "note"]
    T = pd.DataFrame(rows, columns=cols)
    return T.sort_values(["dust_class", "component", "name"]).reset_index(drop=True)


def _drop_meta_names(n, names: set):
    rules = n.meta.get("store_power_rules")
    if isinstance(rules, dict):
        n.meta["store_power_rules"] = {k: v for k, v in rules.items() if k not in names}
    bio = n.meta.get("research_biomass")
    if isinstance(bio, dict) and isinstance(bio.get("stores"), dict):
        bio["stores"] = {k: v for k, v in bio["stores"].items() if k not in names}
    for key in ("demand_owners", "demand_identity"):
        d = n.meta.get(key)
        if isinstance(d, dict):
            n.meta[key] = {k: v for k, v in d.items() if k not in names}
    tie = n.meta.get("research_new_hydro_inflow_tie")
    if isinstance(tie, list):
        n.meta["research_new_hydro_inflow_tie"] = [x for x in tie if x not in names]
    caps = n.meta.get("research_nuclear_caps")
    if isinstance(caps, dict):
        for v in caps.values():
            if isinstance(v, dict) and isinstance(v.get("generators"), list):
                v["generators"] = [x for x in v["generators"] if x not in names]


def apply_dust_cleanup(n, cfg) -> dict:
    """S4L-1 (decision 113 (1)). Call after every component-adding layer (end of the build, before the static validation)."""
    mode = dust_mode(cfg); thr = thresholds(cfg)
    before = {c.name: int(len(c.df)) for c in n.iterate_components() if c.name in ("Bus", "Generator", "Load", "Store", "StorageUnit", "Link", "Line")}
    T = dust_inventory(n, thr)
    led = dict(mode=mode, thresholds=thr, pypsa_eur=PYPSA_EUR_REFS, components_before=before,
               inventory=dict(rows=int(len(T)), by_class_action={f"{k[0]}|{k[1]}": int(v) for k, v in T.groupby(["dust_class", "action"]).size().items()}),
               pool_balance_before=pool_balance(n), table=T)
    n.meta["research_dust_cleanup"] = {k: v for k, v in led.items() if k != "table"}
    if mode != "on":
        led.update(removed={}, merged=[], removed_required_structure=[], components_after=before)
        n.meta["research_dust_cleanup"] = {k: v for k, v in led.items() if k != "table"}
        return led
    dele = T[T.action == "delete"]
    removed_struct = []
    for typ in ("Generator", "StorageUnit"):
        d = n.df(typ)
        for name in dele.name[dele.component == typ]:
            car = str(d.at[name, "carrier"])
            if car in REQUIRED_STRUCTURE.get(typ, ()):
                removed_struct.append([typ, car, _node_of(n, str(d.at[name, "bus"]))])
    names_all = set()
    for typ in ("Store", "Generator", "StorageUnit", "Link", "Load"):   # components first, then the dead-end buses
        names = sorted(set(dele.name[dele.component == typ]) & set(n.df(typ).index))
        if names:
            n.mremove(typ, names); names_all |= set(names)
    buses = sorted(set(dele.name[dele.component == "Bus"]) & set(n.buses.index))
    att = attachments(n)
    still = [b for b in buses if att.get(b)]
    if still:
        raise ValueError("dust cleanup: bus still attached after removing its component: " + str(still[:5]))
    if buses:
        n.mremove("Bus", buses)
    _drop_meta_names(n, names_all)
    short = [b for b in pool_balance(n) if b["slack_mwh"] < -1e-6]   # structural check after the deletions (S4L-2 s4l_A finding): no pool bus may fall below its fixed demand
    if short:
        raise ValueError("dust cleanup would leave finite pools below their fixed demand: " + str(short[:3]))
    merged = []
    for keep, members in identical_link_groups(n):
        N = 1 + len(members); cap = float(n.links.at[keep, "p_nom_max"])
        n.links.at[keep, "p_nom_max"] = cap * N if np.isfinite(cap) else cap
        n.mremove("Link", members); merged.append(dict(kept=keep, members=members, p_nom_max=float(n.links.at[keep, "p_nom_max"]), carrier=str(n.links.at[keep, "carrier"])))
    after = {c.name: int(len(c.df)) for c in n.iterate_components() if c.name in ("Bus", "Generator", "Load", "Store", "StorageUnit", "Link", "Line")}
    rem = dele.assign(capacity_finite=dele.capacity_mw.where(np.isfinite(dele.capacity_mw.astype(float)), 0.0), energy=dele.energy_mwh.fillna(0.0))
    by_cc = rem.groupby(["dust_class", "country"]).agg(count=("name", "size"), capacity_mw=("capacity_finite", "sum"), energy_mwh=("energy", "sum")).reset_index()
    by_c = rem.groupby("country").agg(count=("name", "size"), capacity_mw=("capacity_finite", "sum"), energy_mwh=("energy", "sum")).reset_index()
    led.update(removed=dict(count=int(len(dele)), by_component={k: int(v) for k, v in dele.component.value_counts().items()},
                            by_class_country=by_cc.to_dict("records"), by_country=by_c.to_dict("records"),
                            energy_mwh_total=float(rem.energy.sum()), capacity_mw_total_finite=float(rem.capacity_finite.sum()),
                            unbounded_capacity_components=int((~np.isfinite(dele.capacity_mw.astype(float))).sum())),
               merged=merged, merged_links_removed=int(sum(len(m["members"]) for m in merged)), removed_required_structure=removed_struct, components_after=after,
               pool_balance_after=pool_balance(n))
    n.meta["research_dust_cleanup"] = {k: v for k, v in led.items() if k != "table"}
    return led
