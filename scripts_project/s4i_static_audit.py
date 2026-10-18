"""S4I (item 103, 2026-10-18): static pre-cloud audit of the four frozen S4H networks - read only, no solve, no download.

    python scripts_project/s4i_static_audit.py --networks <cloud_package_dist/networks> --out <evidence dir>

Section A (A1-A10 of the S4I instruction), the network side of section B (PyPSA-Eur v2025.07.0 transmission defaults against
the network values, with impact orders), the Kirchhoff coefficient span from the line parameters (section C), the coverage of
PyPSA's objective-bearing attributes by the country ledger (gate B16), and the connected-coalition count of section D.
Writes S4I_STATIC_AUDIT.json and CSV tables to --out. Networks and repository files are only read.
"""
from pathlib import Path
import argparse, hashlib, itertools, json, logging, math, sys, time, warnings
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

NETS = dict(integrated="integrated_365_24h_unsolved.nc", disconnected="disconnected_365_24h_unsolved.nc",
            integrated_nze="integrated_nze_365_24h_unsolved.nc", disconnected_gap="disconnected_gap_diagnostic_365_24h_unsolved.nc")
MAIN = ("integrated", "disconnected", "integrated_nze")
COUNTRIES = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]
ISO3 = dict(BRN="BN", IDN="ID", KHM="KH", LAO="LA", MMR="MM", MYS="MY", PHL="PH", SGP="SG", THA="TH", TLS="TL", VNM="VN")
# buses booked in tonnes CO2 (carbon = 1 t/t); every other bus carrier is energy
CO2_BUS = {"co2 stored", "co2 atmosphere", "co2 sequestered", "co2 sequestered extra-ASEAN", "co2 bunkers", "process emissions", "plastic waste"}
ATMO = {"co2 atmosphere", "co2 bunkers"}
RENEWABLE = ["onwind", "offwind-ac", "offwind-dc", "solar", "solar rooftop", "ror", "onwind existing", "offwind existing", "solar existing", "ror existing"]
CF_RANGE = {"onwind": (0.12, 0.45), "offwind-ac": (0.15, 0.55), "offwind-dc": (0.15, 0.55), "solar": (0.10, 0.25), "solar rooftop": (0.10, 0.25),
            "ror": (0.15, 0.85), "onwind existing": (0.12, 0.45), "offwind existing": (0.15, 0.55), "solar existing": (0.10, 0.25), "ror existing": (0.15, 0.85)}
SLACK_WORDS = ("slack", "gap", "shed", "backstop", "dummy", "lost load", "voll")
# PyPSA 0.30.3 objective terms (pypsa/optimization/optimize.py define_objective) and what s4d_ledger.country_cost_ledger books
OBJECTIVE_ATTRS = {"Generator": ["marginal_cost", "marginal_cost_quadratic", "stand_by_cost", "start_up_cost", "shut_down_cost", "capital_cost"],
                   "Link": ["marginal_cost", "marginal_cost_quadratic", "stand_by_cost", "start_up_cost", "shut_down_cost", "capital_cost"],
                   "Store": ["marginal_cost", "marginal_cost_quadratic", "marginal_cost_storage", "capital_cost"],
                   "StorageUnit": ["marginal_cost", "marginal_cost_quadratic", "marginal_cost_storage", "spill_cost", "capital_cost"],
                   "Line": ["capital_cost"], "Transformer": ["capital_cost"]}
LEDGER_ATTRS = {"marginal_cost", "capital_cost"}
PYPSA_EUR = dict(  # registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml / _prepare_sector_network.py
    lines_s_max_pu=(0.7, "config.default.yaml line 322; applied by scripts/prepare_network.py set_line_s_max_pu (PyPSA-Eur file not in the registry; pypsa-asean scripts/prepare_network.py lines 182-184, 348-350)"),
    lines_max_extension=(20000.0, "config line 324; prepare_sector_network.py limit_individual_line_extension lines 5573-5577, called 6415-6417 (lines and carrier DC links)"),
    links_p_max_pu=(1.0, "config line 337"), links_p_min_pu=(-1.0, "config line 338"), links_max_extension=(30000.0, "config line 340 (not read by the sector workflow)"),
    length_factor=(1.25, "config lines 325 / 341"),
    dc=(dict(efficiency_static=0.98, efficiency_per_1000km=0.977), "config lines 747-755; prepare_sector_network.py lossy_bidirectional_links lines 5727-5774, called 6445-6447"),
    h2_pipeline=(dict(efficiency_per_1000km=1.0, compression_per_1000km=0.018), "config lines 756-758; same function"),
    gas_pipeline=(dict(efficiency_per_1000km=1.0, compression_per_1000km=0.01), "config lines 759-761; same function"),
    distribution_grid=(dict(efficiency_static=0.97), "config lines 762-763; same function"),
    co2_pipeline=(dict(losses="none (not in transmission_efficiency.enable)", p_min_pu=-1), "config lines 714-715, 747-752; prepare_sector_network.py add_co2_network lines 854-910 (p_min_pu=-1 at 908)"),
    transmission_losses=(2, "config solving.options.transmission_losses line 1001 (piecewise-linear AC line losses in n.optimize; lines with num_parallel 0 removed, prepare_sector_network.py 6451-6454)"),
)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jsonable(x):
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [jsonable(v) for v in (sorted(x, key=str) if isinstance(x, set) else x)]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        return None if not np.isfinite(x) else float(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, pd.Series):
        return jsonable(x.to_dict())
    return x


def ports(df):
    return sorted([c for c in df.columns if c.startswith("bus") and c[3:].isdigit()], key=lambda c: int(c[3:]))


def eff_col(p):
    return "efficiency" if p == "bus1" else "efficiency" + p[3:]


def port_bus(series):
    s = series.dropna().astype(str)
    return s[s != ""]


def load(path):
    import pypsa
    n = pypsa.Network(str(path))
    return n


def weights(n):
    return n.snapshot_weightings


def stats(s):
    s = pd.to_numeric(s, errors="coerce")
    fin = s[np.isfinite(s)]
    return dict(n=int(len(s)), nan=int(s.isna().sum()), inf=int(np.isinf(s).sum()), neg=int((s < 0).sum()), zero=int((s == 0).sum()),
                min=float(fin.min()) if len(fin) else None, median=float(fin.median()) if len(fin) else None, max=float(fin.max()) if len(fin) else None)


# ------------------------------------------------------------------------------------------------------------------ A1 time
def a1_time(n):
    sw = n.snapshot_weightings
    out = dict(snapshots=int(len(n.snapshots)), first=str(n.snapshots[0]), last=str(n.snapshots[-1]),
               weights={c: dict(sum=float(sw[c].sum()), min=float(sw[c].min()), max=float(sw[c].max())) for c in sw.columns})
    out["weights_ok"] = bool(len(n.snapshots) == 365 and all(abs(sw[c].sum() - 8760) < 1e-9 and sw[c].min() == sw[c].max() == 24 for c in ("objective", "generators", "stores")))
    st = n.stores; role = st.get("research_role", pd.Series("", index=st.index)).fillna("").astype(str)
    out["stores_cyclic_by_carrier"] = {c: dict(cyclic=int(g.e_cyclic.sum()), non_cyclic=int((~g.e_cyclic).sum()), roles=sorted(set(role[g.index]))) for c, g in st.groupby("carrier")}
    expected_noncyclic = {"FINITE_RESOURCE", "ATMOSPHERE", "BUNKER_ATMOSPHERE", "PERMANENT_STORAGE", "PERMANENT_STORAGE_EXTRA_ASEAN"}
    odd = st.index[(~st.e_cyclic) & (~role.isin(expected_noncyclic))]
    out["stores_non_cyclic_unexpected"] = sorted(odd)
    su = n.storage_units
    out["storage_units_cyclic_by_carrier"] = {c: dict(cyclic=int(g.cyclic_state_of_charge.sum()), non_cyclic=int((~g.cyclic_state_of_charge).sum())) for c, g in su.groupby("carrier")}
    return out


# ------------------------------------------------------------------------------------------------------------------ A2 costs
def a2_costs(n, costs):
    rows = []
    for t in ["Generator", "Link", "Store", "StorageUnit", "Line"]:
        d = n.df(t)
        nom = "e_nom" if t == "Store" else ("s_nom" if t == "Line" else "p_nom")
        ext = d[nom + "_extendable"]
        for car, g in d.groupby("carrier"):
            e = ext[g.index]
            cc = stats(g.capital_cost[e]); cc_ex = stats(g.capital_cost[~e])
            r = dict(component=t, carrier=car, n=len(g), extendable=int(e.sum()), cc_ext_min=cc["min"], cc_ext_median=cc["median"], cc_ext_max=cc["max"],
                     cc_ext_zero=cc["zero"], cc_neg=int((g.capital_cost < 0).sum()), cc_nan=int(g.capital_cost.isna().sum()), cc_inf=int(np.isinf(g.capital_cost).sum()),
                     cc_existing_nonzero=int((g.capital_cost[~e] != 0).sum()), cc_existing_max=cc_ex["max"])
            if "marginal_cost" in g:
                mc = n.get_switchable_as_dense(t, "marginal_cost")[g.index] if t != "Line" else None
                r.update(mc_min=float(mc.min().min()) if mc is not None and mc.size else None, mc_max=float(mc.max().max()) if mc is not None and mc.size else None,
                         mc_neg=int((mc < 0).any().sum()) if mc is not None else 0, mc_nan=int(mc.isna().any().sum()) if mc is not None else 0,
                         mc_time_varying=int(len([x for x in g.index if x in n.pnl(t).get("marginal_cost", pd.DataFrame()).columns])))
            if "length" in g and t in ("Line", "Link"):
                L = g.length.where(g.length > 0)
                per = (g.capital_cost / L)[e & L.notna()]
                r.update(cc_per_km_min=float(per.min()) if len(per) else None, cc_per_km_max=float(per.max()) if len(per) else None)
            spread = (cc["max"] / cc["min"]) if cc["min"] and cc["max"] and cc["min"] > 0 else None
            r["cc_ext_spread"] = spread
            rows.append(r)
    tab = pd.DataFrame(rows)
    flags = dict(
        negative_capital_cost=tab[tab.cc_neg > 0][["component", "carrier", "cc_neg"]].to_dict("records"),
        nan_or_inf_capital_cost=tab[(tab.cc_nan > 0) | (tab.cc_inf > 0)][["component", "carrier"]].to_dict("records"),
        negative_marginal_cost=tab[tab.get("mc_neg", 0) > 0][["component", "carrier", "mc_min"]].to_dict("records") if "mc_neg" in tab else [],
        nan_marginal_cost=tab[tab.get("mc_nan", 0) > 0][["component", "carrier"]].to_dict("records") if "mc_nan" in tab else [],
        extendable_zero_capital_cost=tab[(tab.extendable > 0) & (tab.cc_ext_zero > 0)][["component", "carrier", "extendable", "cc_ext_zero", "mc_min", "mc_max"]].to_dict("records"),
        marginal_cost_ge_1000=tab[tab.get("mc_max", 0).fillna(0) >= 1000][["component", "carrier", "mc_max"]].to_dict("records") if "mc_max" in tab else [],
        within_carrier_spread_gt_100=tab[tab.cc_ext_spread.fillna(0) > 100][["component", "carrier", "cc_ext_min", "cc_ext_max"]].to_dict("records"),
        existing_with_capital_cost=tab[tab.cc_existing_nonzero > 0][["component", "carrier", "cc_existing_nonzero", "cc_existing_max"]].to_dict("records"))
    # independent re-derivation of the annualised capital cost from the active cost table ('fixed' = (annuity + FOM) x investment)
    cref = costs.set_index("technology")
    def fixed(tech):
        return float(cref.at[tech, "fixed"]) if tech in cref.index else None
    def effc(tech):
        return float(cref.at[tech, "efficiency"]) if tech in cref.index else None
    checks = [("Generator", "onwind", fixed("onwind"), "onwind fixed"), ("Generator", "solar", fixed("solar-utility"), "solar-utility fixed (decision 82)"),
              ("Generator", "nuclear", fixed("nuclear"), "nuclear fixed"), ("Generator", "nuclear SMR", fixed("nuclear SMR"), "nuclear SMR fixed (AEO8 row)"),
              ("Generator", "ror", fixed("ror"), "ror fixed"), ("Generator", "geothermal", fixed("geothermal"), "geothermal fixed (AEO8 row)"),
              ("Link", "CCGT", fixed("CCGT") * effc("CCGT"), "CCGT fixed x efficiency (per MW gas input)"),
              ("Link", "OCGT", fixed("OCGT") * effc("OCGT"), "OCGT fixed x efficiency"),
              ("Link", "H2 Electrolysis", fixed("electrolysis"), "electrolysis fixed"),
              ("Link", "DAC", (fixed("direct air capture") / (float(cref.at["direct air capture", "electricity-input"]) + float(cref.at["direct air capture", "compression-electricity-input"]))) if "direct air capture" in cref.index else None,
               "direct air capture fixed / (electricity-input + compression-electricity-input) (per MW electricity)"),
              ("Link", "battery charger", fixed("battery inverter"), "battery inverter fixed"), ("Store", "battery", fixed("battery storage"), "battery storage fixed"),
              ("StorageUnit", "PHS", fixed("PHS"), "PHS fixed"), ("StorageUnit", "hydro", fixed("hydro"), "hydro fixed"),
              ("Store", "co2 sequestered", 30.0, "research.s2.co2.sequestration_cost_eur_per_t"), ("Store", "co2 sequestered extra-ASEAN", 54.70, "decision 95 a unified basis 24.70 + 30")]
    cmp = []
    for t, car, ref, src in checks:
        d = n.df(t); nom = "e_nom" if t == "Store" else "p_nom"
        g = d[(d.carrier == car) & d[nom + "_extendable"]]
        if not len(g) or ref is None:
            cmp.append(dict(component=t, carrier=car, reference=ref, source=src, present=bool(len(g))))
            continue
        cmp.append(dict(component=t, carrier=car, network_min=float(g.capital_cost.min()), network_max=float(g.capital_cost.max()), reference=ref,
                        ratio_min=float(g.capital_cost.min() / ref), ratio_max=float(g.capital_cost.max() / ref), source=src))
    return tab, dict(flags=flags, cost_rederivation=cmp)


# ------------------------------------------------------------------------------------------------------------------ A3 efficiency / availability
def a3_efficiency(n):
    bc = n.buses.carrier; L = n.links; out = {}
    rows = []
    for p in ports(L)[1:]:
        e = L[eff_col(p)]; b = L[p]
        hit = L.index[(e > 1) & b.notna() & (b.astype(str) != "") & (~b.map(bc).isin(CO2_BUS))]
        for car, idx in pd.Series(hit, index=hit).groupby(L.carrier[hit]).groups.items():
            g = L.loc[idx]
            rows.append(dict(carrier=car, port=p, n=len(idx), bus0_carrier="/".join(sorted(set(g.bus0.map(bc)))), port_carrier="/".join(sorted(set(g[p].map(bc)))),
                             min=float(g[eff_col(p)].min()), max=float(g[eff_col(p)].max())))
    out["link_efficiency_gt1"] = rows
    out["link_efficiency_le0_bus1"] = L.index[(L.efficiency <= 0)].tolist()
    pm = {}
    for t in ["Generator", "Link", "StorageUnit"]:
        d = n.df(t)
        pmax = n.get_switchable_as_dense(t, "p_max_pu"); pmin = n.get_switchable_as_dense(t, "p_min_pu")
        pm[t] = dict(p_max_pu_gt1=sorted(pmax.columns[(pmax > 1 + 1e-12).any()].tolist())[:50], p_max_pu_gt1_count=int((pmax > 1 + 1e-12).any().sum()),
                     p_max_pu_lt0=int((pmax < -1e-12).any().sum()), p_min_gt_p_max=int((pmin > pmax + 1e-12).any().sum()),
                     p_min_pu_lt_minus1=int((pmin < -1 - 1e-12).any().sum()))
    st = n.stores
    pm["Store"] = dict(e_min_pu_lt_minus1=int((st.e_min_pu < -1).sum()), e_max_pu_gt1=int((st.e_max_pu > 1).sum()))
    out["availability"] = pm
    g = n.generators; pmax = n.get_switchable_as_dense("Generator", "p_max_pu")
    ren = g.index[g.carrier.isin(RENEWABLE)]
    zero = [x for x in ren if float(pmax[x].max()) <= 0]
    out["renewables_all_zero_profile"] = dict(count=len(zero), with_positive_p_nom_max=[x for x in zero if float(g.at[x, "p_nom_max"]) > 0 or float(g.at[x, "p_nom"]) > 0][:50],
                                              by_carrier=pd.Series([g.at[x, "carrier"] for x in zero], dtype=object).value_counts().to_dict())
    pset = n.get_switchable_as_dense("Load", "p_set")
    out["loads_all_zero"] = dict(count=int((pset.abs().max() == 0).sum()), names=pset.columns[pset.abs().max() == 0].tolist()[:50],
                                 by_carrier=n.loads.carrier[pset.columns[pset.abs().max() == 0]].value_counts().to_dict())
    out["loads_negative"] = int((pset < 0).any().sum())
    inflow = n.get_switchable_as_dense("StorageUnit", "inflow")
    out["storage_inflow_negative"] = int((inflow < 0).any().sum())
    su = n.storage_units
    out["storage_units"] = [dict(carrier=car, n=len(gg), p_min_pu=sorted(set(gg.p_min_pu.round(6))), efficiency_store=sorted(set(gg.efficiency_store.round(6))),
                                 efficiency_dispatch=sorted(set(gg.efficiency_dispatch.round(6))), max_hours_min=float(gg.max_hours.min()), max_hours_max=float(gg.max_hours.max()),
                                 with_inflow=int(sum(1 for x in gg.index if x in inflow.columns and inflow[x].abs().sum() > 0)),
                                 pumping_and_storing=int(((gg.p_min_pu < 0) & (gg.efficiency_store > 0)).sum()))
                            for car, gg in su.groupby("carrier")]
    return out


# ------------------------------------------------------------------------------------------------------------------ A4 topology
def a4_topology(n):
    bc = n.buses.carrier; cnt = pd.Series(0.0, index=n.buses.index); out = {}
    supply = pd.Series(False, index=n.buses.index); absorb = pd.Series(False, index=n.buses.index)
    dangling = []
    for t in ["Generator", "Load", "Store", "StorageUnit"]:
        d = n.df(t)
        if not len(d):
            continue
        cnt = cnt.add(d.bus.value_counts(), fill_value=0)
        bad = d.index[~d.bus.isin(n.buses.index)]
        dangling += [f"{t}:{x}" for x in bad]
    g = n.generators; pmax = n.get_switchable_as_dense("Generator", "p_max_pu")
    supply[g.bus[(pmax.max() > 0).reindex(g.index).fillna(False)].unique()] = True
    absorb[g.bus[(n.get_switchable_as_dense("Generator", "p_min_pu").min() < 0).reindex(g.index).fillna(False)].unique()] = True
    for t in ["Store", "StorageUnit"]:
        d = n.df(t); supply[d.bus.unique()] = True; absorb[d.bus.unique()] = True
    pset = n.get_switchable_as_dense("Load", "p_set")
    load_pos = n.loads.bus[(pset.max() > 0).reindex(n.loads.index).fillna(False)]
    absorb[load_pos.unique()] = True
    supply[n.loads.bus[(pset.min() < 0).reindex(n.loads.index).fillna(False)].unique()] = True
    for t in ["Line", "Transformer"]:
        d = n.df(t)
        for p in ("bus0", "bus1"):
            if len(d):
                cnt = cnt.add(d[p].value_counts(), fill_value=0); supply[d[p].unique()] = True; absorb[d[p].unique()] = True
                dangling += [f"{t}:{x}:{p}" for x in d.index[~d[p].isin(n.buses.index)]]
    L = n.links
    lpmin = n.get_switchable_as_dense("Link", "p_min_pu").min(); lpmax = n.get_switchable_as_dense("Link", "p_max_pu").max()
    for p in ports(L):
        b = port_bus(L[p]); cnt = cnt.add(b.value_counts(), fill_value=0)
        dangling += [f"Link:{x}:{p}" for x in b.index[~b.isin(n.buses.index)]]
        if p == "bus0":
            absorb[b[lpmax[b.index] > 0].unique()] = True; supply[b[lpmin[b.index] < 0].unique()] = True
        else:
            e = L.loc[b.index, eff_col(p)]
            supply[b[(e > 0) & (lpmax[b.index] > 0)].unique()] = True; absorb[b[(e < 0) & (lpmax[b.index] > 0)].unique()] = True
            absorb[b[(e > 0) & (lpmin[b.index] < 0)].unique()] = True; supply[b[(e < 0) & (lpmin[b.index] < 0)].unique()] = True
    out["dangling_port_references"] = dangling
    iso = cnt.index[cnt == 0]; single = cnt.index[cnt == 1]
    out["isolated_buses"] = dict(count=int(len(iso)), by_carrier=bc[iso].value_counts().to_dict(), names=list(iso[:30]))
    out["single_attachment_buses"] = dict(count=int(len(single)), by_carrier=bc[single].value_counts().to_dict(), names=list(single[:40]))
    nosup = [b for b in load_pos.unique() if not supply.get(b, False)]
    out["loaded_buses_without_supply"] = nosup
    forced = g.bus[(n.get_switchable_as_dense("Generator", "p_min_pu").max() > 0).reindex(g.index).fillna(False)].unique()
    out["forced_generation_buses_without_outlet"] = [b for b in forced if not absorb.get(b, False)]
    # duplicates
    dup = {}
    key_cols = [c for c in ["carrier"] + ports(L) + ["efficiency", "efficiency2", "efficiency3", "efficiency4", "p_nom", "p_nom_extendable", "capital_cost", "marginal_cost", "p_min_pu", "p_max_pu", "length"] if c in L]
    k = L[key_cols].astype(str).agg("|".join, axis=1)
    dl = L[k.duplicated(keep=False)]
    dup["links_identical"] = dict(count=int(len(dl)), by_carrier=dl.carrier.value_counts().to_dict(), examples=list(dl.index[:20]))
    ln = n.lines
    pair = ln.apply(lambda z: "|".join(sorted([z.bus0, z.bus1])), axis=1)
    par = ln[pair.duplicated(keep=False)]
    dup["lines_parallel_same_bus_pair"] = dict(count=int(len(par)), cross_border=int((par.border_class == "cross_border").sum()) if "border_class" in par else None,
                                               both_extendable_groups=int(par.groupby(pair[par.index]).s_nom_extendable.all().sum()) if len(par) else 0,
                                               examples=par.assign(pair=pair[par.index])[["pair", "s_nom", "s_nom_extendable", "border_class", "x", "length"]].head(30).reset_index().to_dict("records"))
    gk = g[["bus", "carrier", "p_nom_extendable", "capital_cost", "marginal_cost", "p_nom", "p_nom_max"]].astype(str).agg("|".join, axis=1)
    prof = pd.Series({x: hashlib.md5(pmax[x].to_numpy().tobytes()).hexdigest() for x in g.index})
    gk = gk + "|" + prof[g.index]
    dg = g[gk.duplicated(keep=False)]
    dup["generators_identical"] = dict(count=int(len(dg)), by_carrier=dg.carrier.value_counts().to_dict(), examples=list(dg.index[:20]))
    out["duplicates"] = dup
    # country attribution
    cty = n.buses.country.astype(str)
    out["bus_country_values"] = cty.value_counts().to_dict()
    out["buses_without_valid_country"] = list(cty.index[~cty.isin(COUNTRIES + ["ASEAN"])])
    mism = {}
    for t in ["Generator", "Load", "Store", "StorageUnit"]:
        d = n.df(t)
        if "country" in d:
            c = d.country.astype(str); bcty = d.bus.map(cty)
            m = d[(c.isin(COUNTRIES)) & (c != bcty)]
            mism[t] = dict(count=int(len(m)), by_carrier_bus_country=m.assign(bus_country=bcty[m.index]).groupby(["carrier", "bus_country"]).size().to_dict())
    out["one_port_country_column_differs_from_bus"] = {k: dict(count=v["count"], by_carrier_bus_country={"|".join(kk): int(vv) for kk, vv in v["by_carrier_bus_country"].items()}) for k, v in mism.items()}
    atmo_b = set(n.buses.index[n.buses.carrier.isin(ATMO)])
    lk = []
    for t in ["Line", "Link"]:
        d = n.df(t)
        for name, z in d.iterrows():
            nat = sorted({cty[z[p]] for p in ports(d) if isinstance(z[p], str) and z[p] and z[p] not in atmo_b and cty[z[p]] != "ASEAN"})
            bcl = str(z.get("border_class", "domestic"))
            if (len(nat) > 1 and bcl not in ("cross_border", "maritime_trade")) or (bcl == "cross_border" and len(nat) != 2):
                lk.append(dict(component=t, name=name, carrier=z.carrier, border_class=bcl, countries=nat))
    out["branch_country_class_inconsistent"] = lk
    try:
        from s4d_ledger import bus_entities, owners
        own = owners(n, bus_entities(n))
        out["ledger_owner_assignment"] = dict(ok=True, entities={t: s.astype(str).str.split("@").str[0].value_counts().to_dict() for t, s in own.items()})
    except Exception as e:
        out["ledger_owner_assignment"] = dict(ok=False, error=str(e)[:500])
    return out


# ------------------------------------------------------------------------------------------------------------------ A5 demand
def load_country(n):
    cty = n.buses.country.astype(str)
    c = n.loads.country.astype(str) if "country" in n.loads else pd.Series("", index=n.loads.index)
    return c.where(c.isin(COUNTRIES), n.loads.bus.map(cty))


def a5_demand(n, receipt, pop_gdp, demand_table):
    w = n.snapshot_weightings.generators
    pset = n.get_switchable_as_dense("Load", "p_set")
    twh = pset.mul(w, axis=0).sum() / 1e6
    lc = load_country(n)
    tab = pd.DataFrame(dict(country=lc, carrier=n.loads.carrier, twh=twh.reindex(n.loads.index))).groupby(["country", "carrier"]).twh.sum().unstack(fill_value=0.0)
    out = dict(by_country_carrier_twh=tab.round(6).to_dict(orient="index"), total_twh=float(twh.sum()))
    sv = receipt.get("static_validation", {}).get("demand", {})
    out["receipt_annual_twh"] = sv.get("annual_twh"); out["receipt_matches"] = bool(sv.get("annual_twh") is not None and abs(sv["annual_twh"] - twh.sum()) <= 1e-6 * max(1, twh.sum()))
    rc = sv.get("by_carrier_twh", {})
    net_c = tab.sum().to_dict()
    out["by_carrier_vs_receipt"] = {k: dict(network=float(net_c.get(k, 0.0)), receipt=rc.get(k)) for k in sorted(set(net_c) | set(rc))}
    tf = demand_table.groupby("country").value_2050_mwh.sum() / 1e6
    elec_cars = ["electricity", "industry electricity", "land transport EV", "agriculture machinery electric"]
    rows = []
    for c in COUNTRIES:
        tot = float(tab.loc[c].sum()) if c in tab.index else 0.0
        el = float(tab.loc[c, [x for x in elec_cars if x in tab.columns]].sum()) if c in tab.index else 0.0
        p = pop_gdp.loc[c]
        rows.append(dict(country=c, network_load_twh=tot, electric_load_twh=el, demand_table_tfec_twh=float(tf.get(c, np.nan)), ratio_network_to_tfec=tot / float(tf.get(c, np.nan)) if tf.get(c) else None,
                         pop2050_m=float(p.pop2050) / 1e6, gdp2050_bn_ppp2021=float(p.gdp2050) / 1e9,
                         mwh_per_capita=tot * 1e6 / float(p.pop2050), elec_mwh_per_capita=el * 1e6 / float(p.pop2050),
                         kwh_per_usd_ppp=tot * 1e9 / float(p.gdp2050), elec_kwh_per_usd_ppp=el * 1e9 / float(p.gdp2050)))
    d = pd.DataFrame(rows).set_index("country")
    asean = dict(mwh_per_capita=d.network_load_twh.sum() * 1e6 / d.pop2050_m.sum() / 1e6, elec_mwh_per_capita=d.electric_load_twh.sum() * 1e6 / d.pop2050_m.sum() / 1e6,
                 kwh_per_usd_ppp=d.network_load_twh.sum() * 1e9 / (d.gdp2050_bn_ppp2021.sum() * 1e9), elec_kwh_per_usd_ppp=d.electric_load_twh.sum() * 1e9 / (d.gdp2050_bn_ppp2021.sum() * 1e9))
    for k, v in asean.items():
        d[k + "_rel_asean"] = d[k] / v
    out["per_country"] = d.round(6).to_dict(orient="index"); out["asean_average"] = asean
    out["outliers_rel_gt2_or_lt05"] = {c: [k for k in asean if not (0.5 <= d.at[c, k + "_rel_asean"] <= 2.0)] for c in COUNTRIES if any(not (0.5 <= d.at[c, k + "_rel_asean"] <= 2.0) for k in asean)}
    asean_loads = n.loads.index[lc == "ASEAN"]
    out["asean_level_loads_twh"] = {x: float(twh[x]) for x in asean_loads}
    return out, tab


# ------------------------------------------------------------------------------------------------------------------ A6 renewables / hydro
def a6_renewables(n, alpha, hydro_target):
    g = n.generators; cty = n.buses.country.astype(str)
    pmax = n.get_switchable_as_dense("Generator", "p_max_pu"); w = n.snapshot_weightings.generators
    cf = pmax.mul(w, axis=0).sum() / w.sum()
    sel = g[g.carrier.isin(RENEWABLE)].copy()
    sel["cf"] = cf[sel.index]; sel["country"] = sel.bus.map(cty)
    sel["wt"] = np.where(sel.p_nom_extendable, sel.p_nom_max.replace(np.inf, np.nan), sel.p_nom)
    rows = []
    for (c, car), gg in sel.groupby(["country", "carrier"]):
        wt = gg.wt.fillna(0)
        rows.append(dict(country=c, carrier=car, n=len(gg), cf_mean=float(gg.cf.mean()), cf_weighted=float((gg.cf * wt).sum() / wt.sum()) if wt.sum() > 0 else None,
                         cf_min=float(gg.cf.min()), cf_max=float(gg.cf.max()), weight_mw=float(wt.sum())))
    tab = pd.DataFrame(rows)
    def outside(r):
        lo, hi = CF_RANGE.get(r.carrier, (0, 1)); v = r.cf_weighted if r.cf_weighted is not None and not pd.isna(r.cf_weighted) else r.cf_mean
        return not (lo <= v <= hi)
    out = dict(cf_outside_common_range=tab[tab.apply(outside, axis=1)].to_dict("records") if len(tab) else [])
    on = g[g.carrier == "onwind"]
    out["onwind_classes_per_node"] = on.groupby("bus").size().value_counts().to_dict()
    a = alpha.set_index("country").alpha_main
    want = dict(PH=0.910, TH=1.294, VN=0.995)
    out["wind_alpha_check"] = {c: dict(table=float(a[c]), instruction=want.get(c, 1.046), ok=bool(abs(float(a[c]) - want.get(c, 1.046)) <= 5e-4)) for c in COUNTRIES}
    # hydro: inflow energy of the existing stock and the new-build candidates against the national target (Ember median x 1.1)
    su = n.storage_units; infl = n.get_switchable_as_dense("StorageUnit", "inflow").mul(n.snapshot_weightings.stores, axis=0).sum()
    su = su.assign(country=su.bus.map(cty), inflow_mwh=infl.reindex(su.index).fillna(0.0))
    ror = g[g.carrier == "ror existing"]; ror_e = (pmax[ror.index].mul(w, axis=0).sum() * ror.p_nom)
    hrows = []
    for c in COUNTRIES:
        t = hydro_target.set_index("country").target_mwh.get(c, np.nan)
        he = float(su[(su.country == c) & (su.carrier == "hydro existing")].inflow_mwh.sum())
        pe = float(su[(su.country == c) & (su.carrier == "PHS existing")].inflow_mwh.sum())
        re_ = float(ror_e[ror.index[ror.bus.map(cty) == c]].sum())
        hn = float(su[(su.country == c) & (su.carrier == "hydro")].inflow_mwh.sum())
        hrows.append(dict(country=c, target_mwh=float(t), hydro_existing_inflow_mwh=he, phs_existing_inflow_mwh=pe, ror_existing_mwh=re_, existing_total_mwh=he + pe + re_,
                          ratio_existing_total_to_target=(he + pe + re_) / float(t) if t else None, ratio_reservoir_only_to_target=he / float(t) if t else None,
                          new_hydro_candidate_inflow_mwh=hn))
    out["hydro_vs_target"] = hrows
    return out, tab


# ------------------------------------------------------------------------------------------------------------------ A7 slack
def a7_slack(n):
    out = {}
    for t in ["Generator", "Link", "Store", "StorageUnit", "Load"]:
        d = n.df(t)
        hit = d[d.carrier.astype(str).str.lower().apply(lambda s: any(wd in s for wd in SLACK_WORDS)) | d.index.str.lower().to_series(index=d.index).apply(lambda s: any(wd in s for wd in SLACK_WORDS))]
        if len(hit):
            out[t] = dict(count=int(len(hit)), by_carrier=hit.carrier.value_counts().to_dict(),
                          marginal_cost=sorted(set(hit.marginal_cost.round(6))) if "marginal_cost" in hit else None,
                          p_nom_max=sorted(set(hit.p_nom_max.astype(float).round(3))) if "p_nom_max" in hit else None,
                          extendable=sorted(set(hit.p_nom_extendable)) if "p_nom_extendable" in hit else None, capital_cost=sorted(set(hit.capital_cost.round(6))) if "capital_cost" in hit else None)
    g = n.generators
    free = g[(g.capital_cost == 0) & (g.marginal_cost == 0) & g.p_nom_extendable & np.isinf(g.p_nom_max)]
    out["free_unbounded_generators"] = dict(count=int(len(free)), by_carrier=free.carrier.value_counts().to_dict())
    out["expensive_generators_mc_ge_1000"] = g[g.marginal_cost >= 1000].carrier.value_counts().to_dict()
    out["gap_meta"] = n.meta.get("gap_diagnostic")
    out["hooks"] = n.meta.get("required_constraint_hooks")
    return out


# ------------------------------------------------------------------------------------------------------------------ A8 units / A9 carbon
def a8_units(n, fuel_prices, scen, EF):
    g = n.generators
    fp = fuel_prices[fuel_prices.scenario == scen].set_index("carrier").eur2020_per_mwh_ncv
    sup = {car: sorted(set(gg.marginal_cost.round(6))) for car, gg in g.groupby("carrier") if car in ("coal", "lignite", "LNG import", "gas production", "oil import", "H2 import", "ammonia import", "methanol import", "FT fuel import")}
    expect = {"coal": fp.get("coal"), "LNG import": fp.get("gas"), "gas production": fp.get("gas"), "oil import": fp.get("oil")}
    out = dict(supply_marginal_costs=sup, expected=expect, fuel_price_ok={k: bool(v is not None and sup.get(k) and all(abs(x - v) <= 1e-4 for x in sup[k])) for k, v in expect.items()})
    L = n.links; bc = n.buses.carrier; rows = []
    for p in ports(L)[1:]:
        b = L[p]; m = b.map(bc).isin(ATMO)
        for car, gg in L[m].groupby("carrier"):
            k = gg[eff_col(p)]; f = gg.bus0.map(bc)
            rows.append(dict(carrier=car, port=p, n=len(gg), bus0="/".join(sorted(set(f))), coef_min=float(k.min()), coef_max=float(k.max()),
                             coef_per_bus0_ef=sorted(set((k / f.map(EF).replace(0, np.nan)).round(6).dropna())) if f.map(EF).fillna(0).gt(0).any() else None))
    out["atmosphere_coefficients"] = rows
    st = n.stores; caps = n.meta.get("research_co2_storage", {}).get("caps_t_per_year", {})
    seq = st[st.carrier == "co2 sequestered"]
    out["sequestered_store_e_nom_max_vs_cap"] = {str(z.country): dict(e_nom_max=float(z.e_nom_max), cap_t=float(caps.get(str(z.country), np.nan)), equal=bool(abs(float(z.e_nom_max) - float(caps.get(str(z.country), np.nan))) <= 1e-6 * max(1, float(z.e_nom_max)))) for _, z in seq.iterrows()}
    out["co2_store_attributes"] = {car: dict(e_min_pu=sorted(set(gg.e_min_pu)), e_cyclic=sorted(set(gg.e_cyclic)), e_initial_max=float(gg.e_initial.max()), capital_cost=sorted(set(gg.capital_cost.round(6))),
                                             marginal_cost=sorted(set(gg.marginal_cost.round(6)))) for car, gg in st[st.carrier.isin(CO2_BUS)].groupby("carrier")}
    out["co2_transport_marginal_cost_eur_per_t"] = {car: dict(min=float(gg.marginal_cost.min()), max=float(gg.marginal_cost.max()), n=len(gg)) for car, gg in L[L.bus0.map(bc) == "co2 stored"].groupby("carrier")}
    return out


def a9_carbon(n, EF):
    from country_carbon import validate_country_attribution
    out = {}
    try:
        v = validate_country_attribution(n)
        out["validate_country_attribution"] = dict(ok=True, atmosphere_buses=v["atmosphere_buses"], emission_ports=v["emission_ports"], ports_by_country=v["ports_by_country"])
    except Exception as e:
        out["validate_country_attribution"] = dict(ok=False, error=str(e)[:500])
    rc = n.meta.get("research_carbon", {})
    hooks = set(n.meta.get("required_constraint_hooks", []))
    out["hooks"] = dict(country_net_zero="research_country_net_zero" in hooks, bunker_net_zero="research_bunker_net_zero" in hooks, co2_storage_cap="research_co2_storage_cap" in hooks,
                        gap_diagnostic="research_gap_diagnostic" in hooks, scope=rc.get("constraint_scope"), caps=rc.get("country_cap_tco2"))
    bc = n.buses.carrier; L = n.links; P = ports(L)
    def ef(b):
        return float(EF.get(bc.get(b, ""), 0.0)) if isinstance(b, str) and b else 0.0
    net = -L.bus0.map(ef)
    for p in P[1:]:
        net = net + L[eff_col(p)].fillna(0.0) * L[p].map(ef)
    def cls(name):
        v = float(net[name]); car = L.at[name, "carrier"]
        if abs(v) <= 1e-9:
            return "balanced"
        if car in ("coal feedstock", "gas feedstock", "oil feedstock") and abs(v + ef(L.at[name, "bus0"])) <= 1e-9:
            return "design_territorial_feedstock"
        if car == "gas production delivery" and v > 0:
            return "design_fugitive_factor"
        return "UNEXPECTED"
    c = pd.Series({x: cls(x) for x in L.index})
    tab = pd.DataFrame(dict(carrier=L.carrier, bus0_carrier=L.bus0.map(bc), net_t_per_mwh_input=net, cls=c))
    out["link_carbon_balance"] = {k: dict(count=int(len(g)), carriers=g.groupby(["carrier", "bus0_carrier"]).net_t_per_mwh_input.agg(["size", "min", "max"]).reset_index().to_dict("records"))
                                  for k, g in tab.groupby("cls") if k != "balanced"}
    out["link_carbon_balance"]["balanced_count"] = int((c == "balanced").sum())
    # loads / stores / generators on carbon-bearing energy buses
    ld = n.loads[n.loads.bus.map(bc).map(lambda x: EF.get(x, 0.0) > 0 and x not in CO2_BUS)]
    out["loads_on_fossil_energy_buses"] = ld.carrier.value_counts().to_dict()
    sto = n.stores[n.stores.bus.map(bc).map(lambda x: EF.get(x, 0.0) > 0 and x not in CO2_BUS)]
    out["stores_on_fossil_energy_buses"] = sto.carrier.value_counts().to_dict()
    gen = n.generators
    gco2 = gen[gen.bus.map(bc).isin(CO2_BUS)]
    out["generators_on_co2_buses"] = {car: dict(n=len(gg), bus=sorted(set(gg.bus.map(bc))), p_min_pu=sorted(set(gg.p_min_pu)), p_max_pu=sorted(set(gg.p_max_pu)), extendable=sorted(set(gg.p_nom_extendable)),
                                             annual_t=float((gg.p_nom * n.snapshot_weightings.generators.sum()).sum())) for car, gg in gco2.groupby("carrier")}
    out["generators_on_fossil_buses"] = {car: dict(n=len(gg), bus=sorted(set(gg.bus.map(bc)))) for car, gg in gen[gen.bus.map(bc).map(lambda x: EF.get(x, 0.0) > 0 and x not in CO2_BUS)].groupby("carrier")}
    # withdrawal from permanent stores / atmosphere-only links
    seqb = set(n.buses.index[bc.isin(["co2 sequestered", "co2 sequestered extra-ASEAN"])])
    wd = []
    for p in P:
        b = L[p]
        if p == "bus0":
            wd += list(L.index[b.isin(seqb)])
        else:
            wd += list(L.index[b.isin(seqb) & (L[eff_col(p)] < 0)])
    out["links_withdrawing_from_permanent_storage"] = sorted(set(wd))
    out["bidirectional_links_into_permanent_storage"] = sorted(L.index[L.bus1.isin(seqb) & (L.p_min_pu < 0)])
    # bunker account
    bunker = set(n.buses.index[bc == "co2 bunkers"])
    bl = [(x, p) for p in P[1:] for x in L.index[L[p].isin(bunker)]]
    out["bunker_ports"] = [dict(link=x, port=p, carrier=L.at[x, "carrier"], coefficient=float(L.at[x, eff_col(p)]), bus0=L.at[x, "bus0"]) for x, p in bl]
    nat_on_bunker = [x for x, _ in bl if any(isinstance(L.at[x, q], str) and L.at[x, q] in set(n.buses.index[bc == "co2 atmosphere"]) for q in P[1:])]
    out["bunker_links_also_booking_national"] = nat_on_bunker
    # oil pool: no link may connect fossil and non-fossil oil buses
    op = L[L.carrier == "oil pool"]
    out["oil_pool_pairs"] = op.assign(c0=op.bus0.map(bc), c1=op.bus1.map(bc)).groupby(["c0", "c1"]).size().reset_index().rename(columns={0: "n"}).to_dict("records")
    # negative-emission routes (removal ports)
    rem = []
    for p in P[1:]:
        m = L[p].map(bc).eq("co2 atmosphere") & (L[eff_col(p)] < 0)
        rem += [dict(carrier=car, port=p, n=len(gg), coef=sorted(set(gg[eff_col(p)].round(6)))) for car, gg in L[m].groupby("carrier")]
    out["removal_ports"] = rem
    return out, tab


# ------------------------------------------------------------------------------------------------------------------ A10 scenario differences
def frame_equal_mask(a, b):
    eq = (a == b)
    try:
        eq = eq | (a.isna() & b.isna())
    except Exception:
        pass
    return eq


def compare(n1, n2):
    out = dict(components={}, series={}, meta_keys_differ=[])
    for c in n1.iterate_components():
        d1, d2 = c.df, n2.df(c.name)
        i1, i2 = set(d1.index), set(d2.index)
        only1, only2 = sorted(i1 - i2), sorted(i2 - i1)
        common = sorted(i1 & i2)
        cols = sorted(set(d1.columns) & set(d2.columns))
        diffs = {}
        if common and cols:
            a, b = d1.loc[common, cols], d2.loc[common, cols]
            ne = ~frame_equal_mask(a, b)
            for col in cols:
                idx = ne.index[ne[col]]
                if len(idx):
                    diffs[col] = dict(count=int(len(idx)), carriers=(d1.loc[idx, "carrier"].value_counts().to_dict() if "carrier" in d1 else {}), examples=list(idx[:5]))
        rec = dict(only_in_first=len(only1), only_in_second=len(only2), column_diffs=diffs)
        if only1 and "carrier" in d1:
            rec["only_in_first_by_carrier_border"] = d1.loc[only1].assign(bc=d1.loc[only1].get("border_class", pd.Series("", index=only1)).fillna("")).groupby(["carrier", "bc"]).size().rename("n").reset_index().to_dict("records")
        if only2 and "carrier" in d2:
            rec["only_in_second_by_carrier"] = d2.loc[only2].carrier.value_counts().to_dict()
        if only1 or only2 or diffs:
            out["components"][c.name] = rec
        p1, p2 = c.pnl, n2.pnl(c.name)
        for attr, f1 in p1.items():
            f2 = p2.get(attr)
            if f2 is None or not (len(f1.columns) or len(f2.columns)):
                continue
            cc = sorted(set(f1.columns) & set(f2.columns))
            ndiff = 0; ex = []
            if cc:
                a, b = f1[cc], f2[cc]
                ne = (~frame_equal_mask(a, b)).any()
                ndiff = int(ne.sum()); ex = list(ne.index[ne][:5])
            if ndiff or set(f1.columns) != set(f2.columns):
                out["series"][f"{c.name}.{attr}"] = dict(columns_differ=ndiff, only_first=len(set(f1.columns) - set(f2.columns)), only_second=len(set(f2.columns) - set(f1.columns)), examples=ex)
    for k in sorted(set(n1.meta) | set(n2.meta)):
        if json.dumps(jsonable(n1.meta.get(k)), sort_keys=True, default=str) != json.dumps(jsonable(n2.meta.get(k)), sort_keys=True, default=str):
            out["meta_keys_differ"].append(k)
    return out


# ------------------------------------------------------------------------------------------------------------------ B transmission defaults
def hav(lon1, lat1, lon2, lat2):
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2); dphi = p2 - p1; dl = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def b_transmission(n):
    cty = n.buses.country.astype(str); x, y = n.buses.x, n.buses.y
    out = dict(pypsa_eur=PYPSA_EUR)
    ln = n.lines.copy()
    ln["c0"], ln["c1"] = ln.bus0.map(cty), ln.bus1.map(cty)
    ln["gc_km"] = hav(ln.bus0.map(x), ln.bus0.map(y), ln.bus1.map(x), ln.bus1.map(y))
    ln["length_over_gc"] = ln.length / ln.gc_km.replace(0, np.nan)
    v = ln.bus0.map(n.buses.v_nom)
    ln["v_nom"] = v
    # full-load loss fraction of one line: r (ohm, all circuits) x P / V^2, P = s_max_pu x s_nom (existing) or one 380 kV 4-bundle circuit for zero-capacity candidates
    import pypsa
    lt = pypsa.Network().line_types
    i_nom = float(lt.at["Al/St 240/40 4-bundle 380.0", "i_nom"]); r_km = float(lt.at["Al/St 240/40 4-bundle 380.0", "r_per_length"])
    s_circ = math.sqrt(3) * 380.0 * i_nom
    ln["rating_mw"] = np.where(ln.s_nom > 0, ln.s_nom, s_circ * ln.num_parallel.clip(lower=1e-9))
    ln["full_load_loss_frac"] = ln.r * ln.s_max_pu * ln.rating_mw / (v ** 2)
    xb = ln[ln.border_class == "cross_border"]
    out["lines"] = dict(count=int(len(ln)), cross_border=int(len(xb)), s_max_pu={k: sorted(set(g.s_max_pu)) for k, g in ln.groupby("border_class")},
                        extension_above_stock=sorted(set((ln.s_nom_max - ln.s_nom).round(6))), length_over_gc=dict(min=float(ln.length_over_gc.min()), median=float(ln.length_over_gc.median()), max=float(ln.length_over_gc.max())),
                        xb_length_over_gc=dict(min=float(xb.length_over_gc.min()), median=float(xb.length_over_gc.median()), max=float(xb.length_over_gc.max())),
                        underwater_fraction=stats(ln.get("underwater_fraction", pd.Series(dtype=float))), s_circuit_mva=s_circ, r_per_km_one_circuit=r_km,
                        xb_full_load_loss_frac=stats(xb.full_load_loss_frac))
    L = n.links.copy(); L["c0"], L["c1"] = L.bus0.map(cty), L.bus1.map(cty)
    L["gc_km"] = hav(L.bus0.map(x), L.bus0.map(y), L.bus1.map(x), L.bus1.map(y))
    L["length_over_gc"] = L.length / L.gc_km.replace(0, np.nan)
    res = {}
    for car in ["DC", "H2 pipeline", "gas pipeline", "CO2 pipeline", "electricity distribution grid", "B2B"]:
        g = L[L.carrier == car]
        if not len(g):
            continue
        res[car] = dict(count=int(len(g)), cross_border=int((g.border_class == "cross_border").sum()), p_min_pu=sorted(set(g.p_min_pu)), p_max_pu=sorted(set(g.p_max_pu)),
                        efficiency=sorted(set(g.efficiency.round(6))), has_bus2=int(g.bus2.notna().sum() - (g.bus2.astype(str) == "").sum()) if "bus2" in g else 0,
                        extension_above_stock=sorted(set((g.p_nom_max - g.p_nom).replace(np.inf, -1).round(3))),
                        length_over_gc=dict(min=float(g.length_over_gc.min()), median=float(g.length_over_gc.median()), max=float(g.length_over_gc.max())),
                        underwater_fraction=stats(g.get("underwater_fraction", pd.Series(dtype=float))), length_km=stats(g.length))
    out["links"] = res
    # impacts per country pair (cross-border only)
    rows = []
    for _, z in xb.iterrows():
        rows.append(dict(kind="AC line", name=z.name, pair="-".join(sorted([z.c0, z.c1])), length_km=float(z.length), s_nom=float(z.s_nom), num_parallel=float(z.num_parallel),
                         loss_or_energy_frac=float(z.full_load_loss_frac), basis="r x s_max_pu x rating / V^2 at full rated load (transmission_losses = 2 in PyPSA-Eur; 0 here)"))
    for car in ["DC", "H2 pipeline", "gas pipeline"]:
        for _, z in L[(L.carrier == car) & (L.border_class == "cross_border")].iterrows():
            if car == "DC":
                val = 1 - 0.98 * 0.977 ** (z.length / 1000.0); basis = "1 - 0.98 x 0.977^(L/1000)"
            elif car == "H2 pipeline":
                val = 0.018 * z.length / 1000.0; basis = "MWh_el per MWh_H2 = 0.018 x L/1000"
            else:
                val = 0.01 * z.length / 1000.0; basis = "MWh_el per MWh_CH4 = 0.01 x L/1000"
            rows.append(dict(kind=car, name=z.name, pair="-".join(sorted([z.c0, z.c1])), length_km=float(z.length), s_nom=float(z.p_nom), num_parallel=None, loss_or_energy_frac=float(val), basis=basis))
    imp = pd.DataFrame(rows, columns=["kind", "name", "pair", "length_km", "s_nom", "num_parallel", "loss_or_energy_frac", "basis"])
    out["impact_by_pair"] = [] if imp.empty else imp.groupby(["kind", "pair"]).agg(n=("name", "size"), length_km_min=("length_km", "min"), length_km_max=("length_km", "max"), stock_mw=("s_nom", "sum"),
                                                          frac_min=("loss_or_energy_frac", "min"), frac_max=("loss_or_energy_frac", "max")).reset_index().to_dict("records")
    # existing distribution grid losses (PyPSA-Eur 3 %): annual flow is a solve output; static reference = LV-side loads
    lv = set(n.buses.index[n.buses.carrier == "low voltage"])
    out["lv_loads"] = int(n.loads.bus.isin(lv).sum())
    return out, imp


def kvl_span(n):
    """Kirchhoff coefficient span from the line parameters (PyPSA cycle rows: C x x_pu_eff; scale factors cancel)."""
    from pypsa.pf import find_cycles
    n.calculate_dependent_values(); n.determine_network_topology()
    rows = []; allc = []
    for sub in n.sub_networks.obj:
        find_cycles(sub)
        C = sub.C
        if C is None or not C.size:
            continue
        br = sub.branches()
        wgt = br.x_pu_eff if n.sub_networks.at[sub.name, "carrier"] == "AC" else br.r_pu_eff
        Cd = pd.DataFrame(C.todense(), index=br.index)
        for j in Cd.columns:
            col = Cd[j]; nz = col[col != 0].index
            coef = (col[nz] * wgt[nz]).abs()
            if not len(coef):
                continue
            allc += list(coef)
            rows.append(dict(sub=str(sub.name), cycle=int(j), branches=int(len(nz)), ratio=float(coef.max() / coef.min()), cmax=float(coef.max()), cmin=float(coef.min()),
                             worst_branches=[f"{t}:{k}" for t, k in coef.sort_values().index[:1].tolist() + coef.sort_values().index[-1:].tolist()]))
    tab = pd.DataFrame(rows)
    allc = np.array(allc)
    out = dict(cycles=int(len(tab)), global_ratio=float(allc.max() / allc.min()) if len(allc) else None, max_cycle_ratio=float(tab.ratio.max()) if len(tab) else None,
               median_cycle_ratio=float(tab.ratio.median()) if len(tab) else None, after_row_normalisation_min_coef=float(1.0 / tab.ratio.max()) if len(tab) else None,
               worst_cycles=tab.sort_values("ratio", ascending=False).head(10).to_dict("records") if len(tab) else [])
    ln = n.lines
    out["x_pu_eff"] = stats(ln.x_pu_eff); out["num_parallel"] = stats(ln.num_parallel)
    out["smallest_num_parallel"] = ln.sort_values("num_parallel")[["bus0", "bus1", "num_parallel", "s_nom", "length", "border_class"]].head(8).reset_index().to_dict("records")
    return out


def ledger_coverage(n):
    out = {}
    for t, attrs in OBJECTIVE_ATTRS.items():
        d = n.df(t)
        if not len(d):
            continue
        for a in attrs:
            if a in LEDGER_ATTRS:
                continue
            nz = int((pd.to_numeric(d[a], errors="coerce").fillna(0) != 0).sum()) if a in d else 0
            ts = n.pnl(t).get(a)
            nzt = int((ts.fillna(0) != 0).any().sum()) if ts is not None and len(ts.columns) else 0
            if nz or nzt:
                out[f"{t}.{a}"] = dict(static_nonzero=nz, series_nonzero=nzt)
    com = {t: int(n.df(t).committable.sum()) for t in ("Generator", "Link") if "committable" in n.df(t)}
    return dict(non_ledger_objective_attributes_nonzero=out, committable=com)


def coalitions(n):
    cty = n.buses.country.astype(str); edges = {}
    for t in ["Line", "Link"]:
        d = n.df(t)
        d = d[d.get("border_class", pd.Series("", index=d.index)) == "cross_border"]
        for _, z in d.iterrows():
            a, b = cty[z.bus0], cty[z.bus1]
            if a != b and a in COUNTRIES and b in COUNTRIES:
                edges.setdefault(tuple(sorted([a, b])), set()).add(str(z.carrier))
    adj = {c: set() for c in COUNTRIES}
    for a, b in edges:
        adj[a].add(b); adj[b].add(a)
    def connected(s):
        s = set(s); start = next(iter(s)); seen = {start}; stack = [start]
        while stack:
            u = stack.pop()
            for v in adj[u] & s:
                if v not in seen:
                    seen.add(v); stack.append(v)
        return seen == s
    count = {k: 0 for k in range(2, 12)}
    for k in range(2, 12):
        for s in itertools.combinations(COUNTRIES, k):
            if connected(s):
                count[k] += 1
    tot = sum(count.values())
    ac_edges = {e for e, cs in edges.items() if cs & {"AC", "DC"}}
    return dict(edges={f"{a}-{b}": sorted(cs) for (a, b), cs in sorted(edges.items())}, connected_by_size=count, connected_total_ge2=tot,
                connected_ge2_excluding_grand=tot - count[11], electricity_edges=sorted(f"{a}-{b}" for a, b in ac_edges), isolated_countries=[c for c in COUNTRIES if not adj[c]])


# ------------------------------------------------------------------------------------------------------------------ main
def main(a):
    warnings.filterwarnings("ignore"); logging.disable(logging.WARNING)
    t0 = time.time(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    nets = Path(a.networks)
    res = dict(script="scripts_project/s4i_static_audit.py", networks_dir=str(nets), inputs={}, sections={})
    costs_p = REPO / "results_project/s4h/s4h4/builds/integrated/costs_active_research.csv"
    rec = {k: json.loads((nets / f"{k if k != 'disconnected_gap' else 'disconnected_gap_diagnostic'}_BUILD_RECEIPT.json").read_text()) for k in NETS}
    res["inputs"]["costs_active"] = dict(path=str(costs_p.relative_to(REPO)), sha256=sha(costs_p), receipt_sha256=rec["integrated"]["inputs"]["costs_active"]["sha256"])
    res["inputs"]["costs_active"]["matches_receipt"] = res["inputs"]["costs_active"]["sha256"] == res["inputs"]["costs_active"]["receipt_sha256"]
    costs = pd.read_csv(costs_p)
    ci = costs.set_index("technology")["CO2 intensity"]
    EF = {c: 1.0 for c in CO2_BUS}
    EF.update({"gas": float(ci["gas"]), "gas wellhead": float(ci["gas"]), "oil": float(ci["oil"]), "coal": float(ci["coal"]), "lignite": float(ci["lignite"])})
    res["inputs"]["emission_factors_t_per_mwh"] = dict(EF, semantics="final-energy / feedstock buses = 0 (load sinks; carbon booked at the meter); oil non-fossil, methanol, biogas, solid biomass = 0 (origin-neutral / biogenic, decision 64); CO2 buses = 1 t/t")
    rin = REPO / "research_inputs"
    fuel = pd.read_csv(rin / "registry_v5/FUEL_PRICES_2050_EUR2020.csv"); fuel["scenario"] = fuel.scenario.str.lower()
    alpha = pd.read_csv(rin / "renewable_v5/WIND_CALIBRATION_ALPHA.csv"); hyd = pd.read_csv(rin / "hydro_v5/HYDRO_NATIONAL_TARGET_S4C2.csv")
    gc = pd.read_csv(rin / "registry_v5/sources/GROWTH_CHAIN_2019_2050_WDI_SSP2.csv")
    gc["country"] = gc["Country Code"].map(ISO3); gc = gc.dropna(subset=["country"]).set_index("country")
    gc["pop2050"] = gc.pop2019_WDI * gc.pop_19_50; gc["gdp2050"] = gc["gdp2019_WDI_2021intl$"] * gc.gdp_19_50
    dem = pd.read_csv(rin / "demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv")
    for p in [rin / "registry_v5/FUEL_PRICES_2050_EUR2020.csv", rin / "renewable_v5/WIND_CALIBRATION_ALPHA.csv", rin / "hydro_v5/HYDRO_NATIONAL_TARGET_S4C2.csv",
              rin / "registry_v5/sources/GROWTH_CHAIN_2019_2050_WDI_SSP2.csv", rin / "demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"]:
        res["inputs"][str(p.relative_to(REPO))] = sha(p)
    res["inputs"]["demand_table_matches_receipt"] = res["inputs"]["research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"] == rec["integrated"]["inputs"]["demand_table"]["sha256"]
    loaded = {}
    for key, fn in NETS.items():
        t1 = time.time(); n = load(nets / fn); loaded[key] = n
        scen = n.meta.get("research_fuel_prices", {}).get("scenario", "steps")
        sec = dict(file=fn, sha256=sha(nets / fn), scenario_tag=n.meta.get("scenario"), fuel_price_scenario=scen,
                   components={c.name: int(len(c.df)) for c in n.iterate_components() if len(c.df)})
        sec["A1_time"] = a1_time(n)
        ctab, sec["A2_costs"] = a2_costs(n, costs); ctab.to_csv(out / f"A2_cost_table_{key}.csv", index=False)
        sec["A3_efficiency_availability"] = a3_efficiency(n)
        sec["A4_topology"] = a4_topology(n)
        sec["A5_demand"], dtab = a5_demand(n, rec[key], gc, dem); dtab.to_csv(out / f"A5_demand_twh_{key}.csv")
        sec["A6_renewables"], rtab = a6_renewables(n, alpha, hyd); rtab.to_csv(out / f"A6_cf_{key}.csv", index=False)
        sec["A7_slack"] = a7_slack(n)
        sec["A8_units"] = a8_units(n, fuel, scen, EF)
        sec["A9_carbon"], cbt = a9_carbon(n, EF)
        cbt[cbt.cls != "balanced"].to_csv(out / f"A9_link_carbon_imbalance_{key}.csv")
        sec["ledger_coverage"] = ledger_coverage(n)
        if key in ("integrated", "disconnected"):
            sec["B_transmission"], imp = b_transmission(n); imp.to_csv(out / f"B_impact_by_component_{key}.csv", index=False)
            sec["C_kvl_span"] = kvl_span(n)
        if key == "integrated":
            sec["D_coalitions"] = coalitions(n)
        sec["seconds"] = time.time() - t1
        res["sections"][key] = sec
        if key not in ("integrated",):
            pass
    cmp = {}
    cmp["integrated_vs_integrated_nze"] = compare(loaded["integrated"], loaded["integrated_nze"])
    cmp["integrated_vs_disconnected"] = compare(loaded["integrated"], loaded["disconnected"])
    cmp["disconnected_vs_disconnected_gap"] = compare(loaded["disconnected"], loaded["disconnected_gap"])
    # trade links (maritime_trade, extra-ASEAN, pools) present in both scenarios
    li, ld_ = loaded["integrated"].links, loaded["disconnected"].links
    trade = li.index[(li.border_class.isin(["maritime_trade"])) | li.carrier.isin(["CO2 export extra-ASEAN", "CO2 transit export extra-ASEAN", "oil pool", "CO2 transit rail", "CO2 transit ship", "CO2 ship"])]
    cmp["trade_links_integrated"] = int(len(trade)); cmp["trade_links_missing_in_disconnected"] = sorted(set(trade) - set(ld_.index))
    xb_left = {t: int((loaded["disconnected"].df(t).get("border_class", pd.Series(dtype=str)) == "cross_border").sum()) for t in ("Line", "Link")}
    cmp["cross_border_components_left_in_disconnected"] = xb_left
    res["A10_scenario_differences"] = cmp
    res["seconds_total"] = time.time() - t0
    try:
        import resource
        res["peak_rss_gib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20
    except Exception:
        pass
    (out / "S4I_STATIC_AUDIT.json").write_text(json.dumps(jsonable(res), indent=1, sort_keys=True, default=str))
    print(json.dumps(dict(seconds=round(res["seconds_total"], 1), peak_rss_gib=round(res.get("peak_rss_gib", 0), 2), out=str(out / "S4I_STATIC_AUDIT.json"))))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--networks", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    sys.exit(main(p.parse_args()))
