"""S4I (item 103) follow-ups after the resume (S4I_RESUME_01): evidence files for the A3/A5/A6 details and sections B2-B4.

    python scripts_project/s4i_followups.py --networks <cloud_package_dist/networks> --out <evidence dir>

* A5: Astar residual electricity per country (Astar 2050 minus the deducted industry / transport electricity of the demand table)
  against the demand table's own non-industry electricity rows (2050 and 2019 base); alternative residuals for scale.
* A3/A6: new hydro / PHS / ror candidates with p_nom_max = 0, the new-hydro inflow tie coverage, existing onshore wind CF vs Ember.
* B2: cross-border losses / compression energy against PyPSA-Eur v2025.07.0 transmission_efficiency, pipeline length ratios with
  node coordinates taken from the bus 'location' (the node AC bus x / y).
* B3: length factor and the cost per km of lines, DC links and pipelines against the active cost table (overhead / submarine mix).
* B4: other settings that change cross-border usable capacity (AC losses option, DC link ends and back-to-back converters, line
  types against bus voltages, existing capacity lower bounds, distribution grid efficiency).
Read only: networks, receipts and repository inputs are not modified. No solve.
"""
from pathlib import Path
import argparse, json, logging, math, sys, warnings
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from s4i_static_audit import COUNTRIES, hav, jsonable, sha, stats

PYPSA_EUR_EFF = {"DC": dict(efficiency_static=0.98, efficiency_per_1000km=0.977), "H2 pipeline": dict(compression_per_1000km=0.018),
                 "gas pipeline": dict(compression_per_1000km=0.01), "electricity distribution grid": dict(efficiency_static=0.97)}
COST_ROWS = {"AC": ("HVAC overhead", "HVAC submarine"), "DC": ("HVDC overhead", "HVDC submarine"), "H2 pipeline": ("H2 (g) pipeline", "H2 (g) submarine pipeline"),
             "gas pipeline": ("CH4 (g) pipeline", "CH4 (g) submarine pipeline"), "CO2 pipeline": ("CO2 pipeline", "CO2 submarine pipeline")}


def a5_astar_residual(rec, dem):
    e = dem[dem.carrier == "electricity"]
    v = e.pivot_table(index="country", columns="sector", values="value_2050_mwh", aggfunc="sum").fillna(0.0) / 1e6
    b = e.pivot_table(index="country", columns="sector", values="base_2019_mwh", aggfunc="sum").fillna(0.0) / 1e6
    non = ["Residential", "Commercial", "AgricultureOthers"]
    rows = []
    for d in rec["demand_s2"]["deductions"]:
        c = d["country"]
        before = d["astar_before_mwh"] / 1e6; after = d["astar_after_mwh"] / 1e6
        ind, tr = d["deducted_industry_mwh"] / 1e6, d["deducted_transport_mwh"] / 1e6
        tab_non = float(v.loc[c, [s for s in non if s in v.columns]].sum()); base_non = float(b.loc[c, [s for s in non if s in b.columns]].sum())
        tab_all = float(v.loc[c].sum())
        prop = before * (1 - (ind + tr) / tab_all) if tab_all > 0 else before   # deduct the industry / transport SHARE of the table, not its level
        rows.append(dict(country=c, astar_2050_twh=before, deducted_industry_twh=ind, deducted_transport_twh=tr, residual_in_network_twh=after, factor=d["factor"],
                         table_non_industry_2050_twh=tab_non, table_non_industry_2019_twh=base_non, table_all_sectors_2050_twh=tab_all,
                         residual_minus_table_non_industry_twh=after - tab_non, residual_over_2019_base=(after / base_non) if base_non else None,
                         alt_proportional_share_twh=prop, alt_table_non_industry_twh=tab_non))
    return pd.DataFrame(rows).set_index("country")


def a6_details(n, alpha):
    cty = n.buses.country.astype(str); su = n.storage_units
    infl = n.get_switchable_as_dense("StorageUnit", "inflow")
    su = su.assign(country=su.bus.map(cty), inflow_twh=(infl.mul(n.snapshot_weightings.stores, axis=0).sum() / 1e6).reindex(su.index).fillna(0.0))
    tie = set(n.meta.get("research_new_hydro_inflow_tie", []))
    h = su[su.carrier == "hydro"].assign(has_inflow=lambda d: d.inflow_twh > 0, in_tie=lambda d: d.index.isin(list(tie)))
    grp = h.groupby(["p_min_pu", "efficiency_store", "has_inflow", "in_tie"]).agg(n=("p_nom_max", "size"), p_nom_max_sum=("p_nom_max", "sum"),
                                                                                    max_hours_min=("max_hours", "min"), max_hours_max=("max_hours", "max")).reset_index()
    p = su[su.carrier == "PHS"]
    phs = p.groupby(["efficiency_store", "efficiency_dispatch"]).agg(n=("p_nom_max", "size"), p_nom_max_sum=("p_nom_max", "sum")).reset_index()
    g = n.generators; pm = n.generators_t.p_max_pu
    ror = g[g.carrier == "ror"]; noprof = ror[~ror.index.isin(pm.columns)]
    geo = g[g.carrier == "geothermal"]
    on = g[g.carrier == "onwind existing"]
    obs = alpha.set_index("country").cf_obs
    onx = pd.DataFrame(dict(country=on.bus.map(cty), p_nom=on.p_nom, cf_model=pm[on.index].mean().reindex(on.index)))
    onx["cf_ember_obs"] = onx.country.map(obs)
    energy_gap = float(((onx.cf_ember_obs.fillna(onx.cf_model) - onx.cf_model) * onx.p_nom * 8760).sum() / 1e6)
    return dict(hydro_candidate_groups=grp.to_dict("records"), new_hydro_inflow_tie=dict(names=len(tie), hydro_with_inflow=int(h.has_inflow.sum()),
                inflow_not_tied=list(h.index[h.has_inflow & ~h.in_tie]), tied_without_inflow=[x for x in tie if su.at[x, "inflow_twh"] == 0]),
                phs_candidate_groups=phs.to_dict("records"), ror_candidates_without_profile=dict(n=int(len(noprof)), with_positive_p_nom_max=int((noprof.p_nom_max > 0).sum())),
                ror_with_profile_p_nom_max_mw=float(ror[ror.index.isin(pm.columns)].p_nom_max.sum()),
                geothermal=dict(p_max_pu=sorted(set(geo.p_max_pu.round(4))), p_max_pu_by_cap={str(k): int(v) for k, v in geo.groupby(geo.p_nom_max > 0).p_max_pu.apply(lambda s: (s < 1).sum()).items()}),
                nuclear_p_max_pu=sorted(set(g[g.carrier.isin(["nuclear", "nuclear SMR"])].p_max_pu)),
                existing_onwind=onx.reset_index().rename(columns={"index": "generator"}).to_dict("records"), existing_onwind_energy_gap_twh_if_ember_cf=energy_gap,
                corrections_meta=n.meta.get("research_candidates_s4b2", {}).get("corrections"))


def node_xy(n):
    """Coordinates of every bus: own x / y when set, else those of its 'location' bus (the node AC bus), else of the node named by
    the bus name without its carrier suffix ('<node> gas' -> '<node>')."""
    x, y = n.buses.x.copy(), n.buses.y.copy()
    loc = n.buses.location.fillna("").astype(str) if "location" in n.buses else pd.Series("", index=n.buses.index)
    miss = ((x == 0) & (y == 0)) | x.isna() | y.isna()
    src = pd.Series("own", index=n.buses.index)
    ok = lambda l: bool(l) and l in n.buses.index and not (n.buses.at[l, "x"] == 0 and n.buses.at[l, "y"] == 0)
    for b in n.buses.index[miss]:
        l = loc[b]; car = str(n.buses.at[b, "carrier"])
        stem = b[: -len(car) - 1] if b.endswith(" " + car) else ""
        if ok(l):
            x[b], y[b] = n.buses.at[l, "x"], n.buses.at[l, "y"]; src[b] = "location"
        elif ok(stem):
            x[b], y[b] = n.buses.at[stem, "x"], n.buses.at[stem, "y"]; src[b] = "name_stem"
        else:
            src[b] = "missing"
    return x, y, src


def b2_b3_b4(n, costs):
    cty = n.buses.country.astype(str); x, y, src = node_xy(n)
    cref = costs.set_index("technology")
    fixed = lambda t: float(cref.at[t, "fixed"]) if t in cref.index else np.nan
    L = n.links.copy(); L["c0"], L["c1"] = L.bus0.map(cty), L.bus1.map(cty)
    L["gc_km"] = hav(L.bus0.map(x), L.bus0.map(y), L.bus1.map(x), L.bus1.map(y))
    L["coord_source"] = L.bus0.map(src) + "/" + L.bus1.map(src)
    L["length_over_gc"] = L.length / L.gc_km.replace(0, np.nan)
    uw = L.get("underwater_fraction", pd.Series(0.0, index=L.index)).fillna(0.0)
    out = dict(b2={}, b3={}, b4={})
    rows = []
    for car in ["DC", "H2 pipeline", "gas pipeline", "CO2 pipeline"]:
        g = L[L.carrier == car]
        xb = g[g.border_class == "cross_border"]
        ov, sub = COST_ROWS[car]
        ref = g.length * ((1 - uw[g.index]) * fixed(ov) + uw[g.index] * fixed(sub)) + (fixed("HVDC inverter pair") if car == "DC" else 0.0)
        ratio = (g.capital_cost / ref.replace(0, np.nan))
        out["b3"][car] = dict(length_over_gc=stats(g.length_over_gc), xb_length_over_gc=stats(xb.length_over_gc), coord_source=g.coord_source.value_counts().to_dict(),
                              underwater_fraction_xb=stats(uw[xb.index]), cost_ratio_to_pypsa_eur_formula=stats(ratio[g.p_nom_extendable]),
                              cost_rows=[ov, sub] + (["HVDC inverter pair"] if car == "DC" else []), fixed_per_km=dict(overhead=fixed(ov), submarine=fixed(sub)))
        out["b2"][car] = dict(model=dict(efficiency=sorted(set(g.efficiency.round(6))), p_min_pu=sorted(set(g.p_min_pu)), compression_port=bool("bus2" in g and (g.bus2.fillna("").astype(str) != "").any())),
                              pypsa_eur=PYPSA_EUR_EFF.get(car, "no losses (CO2 pipeline not in transmission_efficiency.enable)"),
                              p_min_pu_zero=g.index[g.p_min_pu == 0].tolist()[:30], p_min_pu_zero_count=int((g.p_min_pu == 0).sum()),
                              p_min_pu_zero_cross_border=int(((g.p_min_pu == 0) & (g.border_class == "cross_border")).sum()))
        for _, z in xb.iterrows():
            if car == "DC":
                f = 1 - 0.98 * 0.977 ** (z.length / 1000); basis = "loss share of the sent power"
            elif car == "H2 pipeline":
                f = 0.018 * z.length / 1000; basis = "MWh_el per MWh_H2 sent"
            elif car == "gas pipeline":
                f = 0.01 * z.length / 1000; basis = "MWh_el per MWh_CH4 sent"
            else:
                f = 0.0; basis = "none in PyPSA-Eur"
            rows.append(dict(kind=car, name=z.name, pair="-".join(sorted([z.c0, z.c1])), length_km=float(z.length), gc_km=float(z.gc_km), stock=float(z.p_nom), frac=float(f), basis=basis))
    ln = n.lines.copy(); ln["c0"], ln["c1"] = ln.bus0.map(cty), ln.bus1.map(cty)
    ln["gc_km"] = hav(ln.bus0.map(x), ln.bus0.map(y), ln.bus1.map(x), ln.bus1.map(y))
    v = ln.bus0.map(n.buses.v_nom); v1 = ln.bus1.map(n.buses.v_nom)
    import pypsa
    lt = pypsa.Network().line_types
    i_nom = float(lt.at["Al/St 240/40 4-bundle 380.0", "i_nom"]); s_circ = math.sqrt(3) * 380.0 * i_nom
    rating = np.where(ln.s_nom > 0, ln.s_nom, s_circ * ln.num_parallel.clip(lower=1e-9))
    ln["loss_full"] = ln.r * ln.s_max_pu * rating / v ** 2
    xbl = ln[ln.border_class == "cross_border"]
    uwl = ln.get("underwater_fraction", pd.Series(0.0, index=ln.index)).fillna(0.0)
    refl = ln.length * ((1 - uwl) * fixed("HVAC overhead") + uwl * fixed("HVAC submarine"))
    implied_sub = ((ln.capital_cost / ln.length) - fixed("HVAC overhead")) / (fixed("HVAC submarine") - fixed("HVAC overhead"))
    out["b3"]["AC"] = dict(length_over_gc=stats(ln.length / ln.gc_km), xb_length_over_gc=stats(xbl.length / xbl.gc_km), cost_ratio_to_overhead_only=stats(ln.capital_cost / (ln.length * fixed("HVAC overhead"))),
                           cost_ratio_to_pypsa_eur_formula=stats(ln.capital_cost / refl), xb_implied_subsea_share=stats(implied_sub[xbl.index]),
                           xb_cost_per_km=stats(xbl.capital_cost / xbl.length), fixed_per_km=dict(overhead=fixed("HVAC overhead"), submarine=fixed("HVAC submarine")))
    for _, z in xbl.iterrows():
        rows.append(dict(kind="AC line", name=z.name, pair="-".join(sorted([z.c0, z.c1])), length_km=float(z.length), gc_km=float(z.gc_km), stock=float(z.s_nom),
                         frac=float(z.loss_full), basis="I2R loss share at s_max_pu x rating (half of it at half load); transmission_losses 2 in PyPSA-Eur, 0 here"))
    imp = pd.DataFrame(rows)
    imp["frac_x_len"] = imp.frac * imp.length_km
    pair = imp.groupby(["kind", "pair"]).agg(n=("name", "size"), stock=("stock", "sum"), length_min=("length_km", "min"), length_max=("length_km", "max"),
                                            frac_min=("frac", "min"), frac_max=("frac", "max"), frac_len_weighted=("frac_x_len", "sum"), len_sum=("length_km", "sum")).reset_index()
    pair["frac_len_weighted"] = pair.frac_len_weighted / pair.len_sum
    out["b2"]["by_pair"] = pair.drop(columns="len_sum").to_dict("records")
    out["b2"]["ac_loss_per_100km_full_load"] = float((xbl.loss_full / xbl.length * 100).median())
    # B4: other settings
    b4 = {}
    b4["transmission_losses"] = dict(model=0, model_source="scripts_project/s2_solve.py line 209: n.optimize.create_model() without transmission_losses (PyPSA 0.30.3 default 0)",
                                     pypsa_eur=2, pypsa_eur_source="config.default.yaml solving.options.transmission_losses line 1001")
    dc = L[L.carrier == "DC"]
    bc = n.buses.carrier
    dcb = set(n.buses.index[bc == "DC"])
    b2b = L[L.carrier == "B2B"]
    ends = []
    for name, z in dc.iterrows():
        for p in ("bus0", "bus1"):
            b = z[p]
            if b in dcb:
                conv = b2b[(b2b.bus0 == b) | (b2b.bus1 == b)]
                other = [k for k in dc.index[(dc.bus0 == b) | (dc.bus1 == b)] if k != name]
                ends.append(dict(dc_link=name, border_class=z.border_class, port=p, dc_bus=b, b2b=list(conv.index), b2b_p_nom=float(conv.p_nom.sum()), b2b_extendable=bool(conv.p_nom_extendable.any()) if len(conv) else None,
                                 other_dc_links=other, dc_link_p_nom=float(z.p_nom), dc_link_extendable=bool(z.p_nom_extendable)))
    b4["dc_link_ends_on_dc_buses"] = ends
    b4["dc_buses"] = {b: dict(country=cty[b], links=list(L.index[(L.bus0 == b) | (L.bus1 == b)]), generators=list(n.generators.index[n.generators.bus == b]), loads=list(n.loads.index[n.loads.bus == b]))
                      for b in sorted(dcb)}
    vv = pd.DataFrame(dict(v0=v, v1=v1, type=ln.type, border=ln.border_class))
    b4["line_voltage_vs_type"] = vv.groupby(["v0", "v1", "type", "border"]).size().rename("n").reset_index().to_dict("records")
    b4["existing_capacity_lower_bound"] = dict(lines_s_nom_min_lt_s_nom=int((ln.s_nom_min < ln.s_nom - 1e-6).sum()), dc_p_nom_min_lt_p_nom=int((dc.p_nom_min < dc.p_nom - 1e-6).sum()),
                                               pipelines_p_nom_min_lt_p_nom=int((L[L.carrier.isin(["gas pipeline", "H2 pipeline", "CO2 pipeline"])].p_nom_min < L[L.carrier.isin(["gas pipeline", "H2 pipeline", "CO2 pipeline"])].p_nom - 1e-6).sum()))
    dg = L[L.carrier == "electricity distribution grid"]
    lv = set(n.buses.index[bc == "low voltage"])
    b4["distribution_grid"] = dict(efficiency=sorted(set(dg.efficiency)), p_min_pu=sorted(set(dg.p_min_pu)), loads_on_lv=int(n.loads.bus.isin(lv).sum()),
                                   lv_attached=dict(generators=n.generators[n.generators.bus.isin(lv)].carrier.value_counts().to_dict(), links=L[L.bus0.isin(lv) | L.bus1.isin(lv)].carrier.value_counts().to_dict()))
    b4["pipelines_p_nom_max"] = {c: sorted(set(L[L.carrier == c].p_nom_max.replace(np.inf, -1))) for c in ["H2 pipeline", "gas pipeline", "CO2 pipeline"]}
    b4["meta_transmission_limit"] = n.meta.get("transmission_limit"); b4["meta_max_extension"] = n.meta.get("research_max_extension")
    b4["global_constraints"] = int(len(n.global_constraints))
    out["b4"] = b4
    return out, imp


def main(a):
    warnings.filterwarnings("ignore"); logging.disable(logging.WARNING)
    import pypsa
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True); nets = Path(a.networks)
    rin = REPO / "research_inputs"
    rec = json.loads((nets / "integrated_BUILD_RECEIPT.json").read_text())
    dem = pd.read_csv(rin / "demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv")
    alpha = pd.read_csv(rin / "renewable_v5/WIND_CALIBRATION_ALPHA.csv")
    costs_p = REPO / "results_project/s4h/s4h4/builds/integrated/costs_active_research.csv"
    costs = pd.read_csv(costs_p)
    res = dict(script="scripts_project/s4i_followups.py", inputs={"costs_active_sha256": sha(costs_p), "demand_table_sha256": sha(rin / "demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"),
                                                                 "integrated_receipt_sha256": sha(nets / "integrated_BUILD_RECEIPT.json"), "integrated_network_sha256": sha(nets / "integrated_365_24h_unsolved.nc")})
    ar = a5_astar_residual(rec, dem); ar.to_csv(out / "A5_astar_residual.csv", float_format="%.6f")
    res["A5_astar_residual"] = ar.round(6).to_dict(orient="index")
    n = pypsa.Network(str(nets / "integrated_365_24h_unsolved.nc"))
    net_el = n.loads[n.loads.carrier == "electricity"]
    w = n.snapshot_weightings.generators
    pset = n.get_switchable_as_dense("Load", "p_set")
    res["A5_network_electricity_load_twh"] = {c: float((pset[net_el.index[net_el.bus.map(n.buses.country) == c]].mul(w, axis=0)).sum().sum() / 1e6) for c in COUNTRIES}
    res["A6_details"] = a6_details(n, alpha)
    b, imp = b2_b3_b4(n, costs); imp.to_csv(out / "B2_cross_border_losses_by_component.csv", index=False, float_format="%.6f")
    res.update({"B2": b["b2"], "B3": b["b3"], "B4": b["b4"]})
    try:
        import resource
        res["peak_rss_gib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20
    except Exception:
        pass
    (out / "S4I_FOLLOWUPS.json").write_text(json.dumps(jsonable(res), indent=1, sort_keys=True, default=str))
    print(json.dumps(dict(out=str(out / "S4I_FOLLOWUPS.json"), peak_rss_gib=round(res.get("peak_rss_gib", 0), 2))))


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--networks", required=True, type=Path); p.add_argument("--out", required=True, type=Path)
    sys.exit(main(p.parse_args()))
