"""S2 solve driver: one HiGHS smoke solve (SMOKE_TEST_ONLY) or the labelled gap diagnostic (decisions 49, 53).

    python scripts_project/s2_solve.py --network <nc> --scenario integrated --output <dir> --truncate 56 \
        --label SMOKE_TEST_ONLY --authorization "S2 instruction S2-7"

Truncated horizons scale every annual quantity to the horizon: finite biomass pools (Store e_nom /
e_initial) and the national CO2 storage caps (hook horizon_fraction). One optimize call; never retried.
Writes the LP (CSC), raw primal/dual vectors, V5 gates A1-A6 + B1/B2/B3/B8/B11/B12, emissions by
country and source, CO2 flows (capture, sequestration, cross-border pipelines) and, in gap mode, the
per-country electricity and CO2 gaps. Gap-diagnostic products never enter interconnection values.
"""
from pathlib import Path
import argparse, json, platform, sys, time, traceback
import numpy as np
import pandas as pd
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from s1_solve import Sampler, sha, save, export_lp, reduced_costs, structural_supply_diagnosis


def set_representative_weights(n):
    """R4 (decision 58): a truncated run (N snapshots < full year) represents the whole year. Every snapshot weighting
    (objective, generators, stores) is set to 8760 / N so that the weights sum to 8,760 h; annual quantities (CO2
    injection caps, biomass potentials, external annual caps) are NOT scaled. This is the PyPSA-Eur representative-period
    convention: scripts/prepare_network.py average_every_nhours / time-segmentation set snapshot_weightings so that
    their sum stays 8760 (and PyPSA.Network.snapshot_weightings docs: weightings sum to the hours of the year)."""
    N = int(len(n.snapshots)); w = 8760.0 / N
    for col in ["objective", "generators", "stores"]:
        n.snapshot_weightings[col] = w
    if "research_co2_storage" in n.meta:
        n.meta["research_co2_storage"] = dict(n.meta["research_co2_storage"], horizon_fraction=1.0, weights_note="R4: representative weights, annual caps unscaled")
    n.meta["representative_weights"] = dict(snapshots=N, weight_hours_per_snapshot=w, sum_hours=w * N, annual_caps_scaled=False, decision="58",
                                            reference="PyPSA-Eur v2025.07.0 scripts/prepare_network.py (average_every_nhours: snapshot_weightings = n.snapshot_weightings.resample(offset).sum(); segmentation: weightings sum 8760)")
    return dict(method="representative_weights_sum_8760", snapshots=N, weight_hours_per_snapshot=w, horizon_fraction=1.0, scaled_stores=[], annual_caps_scaled=False)


def scale_to_horizon(n):
    """S2 (superseded by set_representative_weights in R4): annual quantities -> truncated horizon (fraction of 8760 h)."""
    frac = float(n.snapshot_weightings.generators.sum() / 8760.0)
    ledger = dict(horizon_fraction=frac, scaled_stores=[])
    if "research_role" in n.stores:
        for name in n.stores.index[n.stores.research_role == "FINITE_RESOURCE"]:
            n.stores.at[name, "e_nom"] = float(n.stores.at[name, "e_nom"]) * frac
            n.stores.at[name, "e_initial"] = float(n.stores.at[name, "e_initial"]) * frac
            ledger["scaled_stores"].append(name)
    if "research_co2_storage" in n.meta:
        n.meta["research_co2_storage"] = dict(n.meta["research_co2_storage"], horizon_fraction=frac)
        for c, cap in n.meta["research_co2_storage"]["caps_t_per_year"].items():
            sb = f"co2 sequestered {c}"
            if sb in n.stores.index:
                n.stores.at[sb, "e_nom_max"] = float(cap) * frac
    return ledger


def structural_diagnosis_s2(n):
    """Infeasibility localisation without changing the model: per country, unavoidable CO2 (fixed fossil final
    demand x EF + exogenous process emissions) against the country's access to permanent storage (own store or
    any cross-border CO2 pipeline) and its zero-emission electricity potential; horizon = loaded snapshots."""
    w = n.snapshot_weightings.generators; pset = n.get_switchable_as_dense("Load", "p_set")
    pmax = n.get_switchable_as_dense("Generator", "p_max_pu"); caps = n.meta.get("research_co2_storage", {}).get("caps_t_per_year", {})
    frac = float(w.sum() / 8760.0); out = {}
    xb = n.links[(n.links.carrier == "CO2 pipeline") & (n.links.border_class == "cross_border")] if "border_class" in n.links else n.links.iloc[0:0]
    for c in sorted(set(n.buses.country.dropna()) - {""}):
        buses = set(n.buses.index[n.buses.country == c]); g = n.generators[n.generators.bus.isin(buses)]
        loads_c = n.loads[n.loads.bus.isin(buses)]
        elec = float(sum((pset[l] * w).sum() for l in loads_c.index[loads_c.carrier.isin(["electricity", "land transport EV", "agriculture machinery electric"])]))
        atm = set(n.buses.index[n.buses.carrier == "co2"]) | {f"co2 atmosphere {c}"}
        meters = n.links[(n.links.country == c) & n.links.carrier.str.endswith("final-energy accounting") & n.links.bus2.isin(atm)] if "bus2" in n.links else n.links.iloc[0:0]
        fixed_co2 = 0.0
        for name, z in meters.iterrows():
            dem = [l for l in loads_c.index if n.loads.at[l, "bus"] == z.bus1]
            fixed_co2 += float(sum((pset[l] * w).sum() for l in dem)) * float(z.efficiency2)
        proc = float(sum(n.generators.at[x, "p_nom"] * w.sum() for x in g.index[g.carrier.isin(["process emissions", "plastic waste"])]))
        feed = n.links[(n.links.country == c) & n.links.carrier.str.endswith(" feedstock")]
        feed_co2 = 0.0
        for name, z in feed.iterrows():   # full_release mode only (territorial feedstock links carry no carbon ports)
            dem = [l for l in loads_c.index if n.loads.at[l, "bus"] == z.bus1]
            e = float(sum((pset[l] * w).sum() for l in dem))
            if str(z.get("bus2", "")).endswith(" process emissions"):
                feed_co2 += e * float(z.efficiency2)
            if str(z.get("bus3", "")) == f"co2 atmosphere {c}":
                feed_co2 += e * float(z.efficiency3)
        ren = g[(g.carrier.isin(["solar", "solar rooftop", "onwind", "offwind-ac", "offwind-dc"])) & g.p_nom_extendable]
        potential = float(sum((pmax[k] * w).sum() * min(float(z.p_nom_max), 1e9) for k, z in ren.iterrows()))
        pipes = [x for x in xb.index if c in (str(n.buses.at[xb.at[x, "bus0"], "country"]), str(n.buses.at[xb.at[x, "bus1"], "country"]))]
        pipes += [f"co2 sequestered extra-ASEAN {c}"] if f"co2 sequestered extra-ASEAN {c}" in n.stores.index else []   # S4C-4 (decision 89): uncapped export option
        bio = float(n.stores[(n.stores.country == c) & (n.stores.research_role == "FINITE_RESOURCE")].e_nom.sum()) if "research_role" in n.stores else 0.0
        out[c] = dict(horizon_fraction=frac, electricity_demand_mwh=elec, renewable_potential_mwh=potential,
                      nuclear_or_smr_candidate=bool(((g.carrier.isin(["nuclear", "nuclear SMR"])) & g.p_nom_extendable & (g.p_nom_max > 0)).any()),
                      unavoidable_fossil_final_co2_t=fixed_co2, process_emissions_t=proc, feedstock_carbon_t=feed_co2, biomass_pool_mwh=bio,
                      storage_cap_t=float(caps.get(c, 0.0)) * frac, cross_border_co2_pipelines=len(pipes),
                      can_store_or_export_co2=bool(float(caps.get(c, 0.0)) > 0 or len(pipes) > 0),
                      net_zero_structurally_possible=bool((float(caps.get(c, 0.0)) > 0 or len(pipes) > 0) or (fixed_co2 + proc + feed_co2) <= 1e-6))
    return out


def co2_flows(n):
    w = n.snapshot_weightings.stores
    out = dict(sequestered_by_country={}, captured_by_carrier={}, vented_by_country={}, cross_border_pipeline={}, dac_by_country={}, extra_asean_by_country={}, intra_asean_shipping={})
    from s4c_layers import extra_asean_report
    from s4d_layers import shipping_report
    out["extra_asean_by_country"] = extra_asean_report(n)   # S4C-4 (decision 89); S4D-1 transit tonnes and freight
    out["intra_asean_shipping"] = shipping_report(n)   # S4D-2 (decision 92): tonnes and freight per exporter -> receiver
    from s4f_layers import lao_vn_store_report
    out["lao_transit_vn_store"] = lao_vn_store_report(n)   # S4F-2 c (decision 97 c): Lao CO2 by rail into the Vietnamese national store
    out["lao_transit_th_store"] = lao_vn_store_report(n, "co2 sequestered TH")   # S4G-2 (decision 99 b): existing_port sensitivity, Thai national store
    for name, z in n.stores[n.stores.carrier == "co2 sequestered"].iterrows():
        out["sequestered_by_country"][str(z.country)] = dict(final_level_t=float(n.stores_t.e[name].iloc[-1]), e_nom_max=float(z.e_nom_max))
    links = n.links
    for carrier in ["CCGT CC", "SMR CC", "biomass EOP CC", "process emissions CC", "DAC", "industry biomass CC", "industry biomass boiler CC"]:
        sel = links[links.carrier == carrier]
        tot = 0.0
        for name, z in sel.iterrows():
            for port in ["bus1", "bus2", "bus3", "bus4"]:
                if port in links and str(z.get(port, "")).endswith(" co2 stored"):
                    flow = n.links_t["p" + port[3:]][name]
                    tot += float((-flow * w).sum())
        out["captured_by_carrier"][carrier] = tot
    for name, z in links[links.carrier == "co2 vent"].iterrows():
        out["vented_by_country"][str(z.country)] = out["vented_by_country"].get(str(z.country), 0.0) + float((n.links_t.p0[name] * w).sum())
    for name, z in links[(links.carrier == "DAC")].iterrows():
        out["dac_by_country"][str(z.country)] = out["dac_by_country"].get(str(z.country), 0.0) + float((-n.links_t.p1[name] * w).sum())
    xb = links[(links.carrier == "CO2 pipeline") & (links.border_class == "cross_border")] if "border_class" in links else links.iloc[0:0]
    for name, z in xb.iterrows():
        p0 = n.links_t.p0[name]
        out["cross_border_pipeline"][name] = dict(from_country=str(n.buses.at[z.bus0, "country"]), to_country=str(n.buses.at[z.bus1, "country"]), capacity_opt_t_per_h=float(z.p_nom_opt),
                                                   net_t_0_to_1=float((p0 * w).sum()), abs_t=float((p0.abs() * w).sum()))
    return out


def gap_table(n, m):
    w = n.snapshot_weightings.generators
    rows = []
    slack = n.generators[n.generators.carrier == "gap slack electricity"] if "gap slack electricity" in set(n.generators.carrier) else n.generators.iloc[0:0]
    co2 = {}
    if "Research_gap_co2_slack" in m.variables:
        sol = m.variables["Research_gap_co2_slack"].solution
        co2 = {str(c): float(sol.sel(country=c).item()) for c in sol.coords["country"].values}
    bslack = n.generators[n.generators.carrier == "gap slack biomass"] if "gap slack biomass" in set(n.generators.carrier) else n.generators.iloc[0:0]
    gslack = n.generators[n.generators.carrier == "gap slack gas"] if "gap slack gas" in set(n.generators.carrier) else n.generators.iloc[0:0]   # S4B-0 (decision 73)
    pset = n.get_switchable_as_dense("Load", "p_set")
    for c in sorted(set(n.buses.country.dropna()) - {""}):
        gens = slack[slack.country == c]
        e = float(sum((n.generators_t.p[g] * w).sum() for g in gens.index if g in n.generators_t.p))
        dem = float(sum((pset[l] * w).sum() for l in n.loads.index[(n.loads.country == c) & (n.loads.carrier.isin(["electricity", "land transport EV", "agriculture machinery electric"]))]))
        bg = bslack[bslack.country == c]
        b = float(sum((n.generators_t.p[g] * w).sum() for g in bg.index if g in n.generators_t.p))
        bdem = float(sum((pset[l] * w).sum() for l in n.loads.index[(n.loads.country == c) & (n.loads.carrier == "biomass final energy")]))
        bpot = float(n.stores[(n.stores.bus == f"solid biomass {c}") & (n.stores.research_role == "FINITE_RESOURCE")].e_nom.sum()) if "research_role" in n.stores else 0.0
        gg = gslack[gslack.country == c]
        gs = float(sum((n.generators_t.p[g] * w).sum() for g in gg.index if g in n.generators_t.p))
        gdem = float(sum((pset[l] * w).sum() for l in n.loads.index[(n.loads.country == c) & (n.loads.carrier.isin(["gas final energy", "gas feedstock"]))]))
        rows.append(dict(country=c, electricity_gap_mwh=e, electricity_demand_mwh=dem, electricity_gap_share=(e / dem if dem else None), co2_gap_t=co2.get(c), cap_tco2=n.meta["research_carbon"]["country_cap_tco2"].get(c),
                         biomass_gap_mwh=b, biomass_final_demand_mwh=bdem, solid_biomass_potential_mwh=bpot, gas_gap_mwh=gs, gas_fixed_demand_mwh=gdem, gas_slack_generators=int(len(gg))))
    return rows


LICENSE_MARKERS = ("license", "licenseid", "wls", "registered to", "academic", "secret", "accessid", "token")


def gurobi_log_stats(log_path, scrubbed_path):
    """Coefficient statistics and solve summary from the Gurobi log; a scrubbed copy without any licence/credential line is kept, the raw log is not copied anywhere."""
    import re
    if not Path(log_path).exists():
        return dict(error="log missing")
    keep = []
    stats = dict(coefficient_statistics={}, lines={})
    for line in Path(log_path).read_text(errors="ignore").splitlines():
        low = line.lower()
        if any(mk in low for mk in LICENSE_MARKERS):
            continue
        keep.append(line)
        m = re.match(r"\s*(Matrix|Objective|Bounds|RHS) range\s+\[(\S+), (\S+)\]", line)
        if m:
            lo, hi = float(m.group(2)), float(m.group(3)); stats["coefficient_statistics"][m.group(1).lower()] = dict(min=lo, max=hi, ratio=(hi / lo if lo else None))
        for key, pat in [("presolved", r"^Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros"), ("barrier", r"^Barrier solved model in (\d+) iterations and ([\d.]+) seconds"),
                         ("crossover", r"^Solved with (barrier|dual simplex|primal simplex)|^Crossover .*"), ("result", r"^(Optimal objective|Model is infeasible|Model is unbounded|Infeasible or unbounded|Time limit reached|Solved in).*"),
                         ("warning", r"^Warning: .*")]:
            if re.match(pat, line):
                stats["lines"].setdefault(key, []).append(line.strip()[:200])
    Path(scrubbed_path).write_text("\n".join(keep))
    stats["scrubbed_log"] = str(scrubbed_path.name); stats["scrubbed_lines"] = len(keep)
    return stats


def main(a):
    import pypsa, logging
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
    run = dict(label=a.label, scenario=a.scenario, authorization=a.authorization, solver=a.solver, started_epoch=time.time(), optimize_calls=0, retry=False, stage="S2")
    sampler = Sampler(out / "RESOURCE.jsonl"); sampler.start()
    try:
        net_sha = sha(a.network); n = pypsa.Network(str(a.network))
        if n.meta.get("scenario") != a.scenario:
            raise ValueError("Network scenario tag differs from --scenario")
        gap = bool(n.meta.get("gap_diagnostic", {}).get("enabled"))
        if gap and a.label != "GAP_DIAGNOSTIC":
            raise ValueError("Gap-diagnostic networks must be solved with --label GAP_DIAGNOSTIC")
        if a.truncate:
            sns = n.snapshots[:a.truncate]; n.set_snapshots(sns)
            if a.label not in ("SMOKE_TEST_ONLY", "GAP_DIAGNOSTIC"):
                raise ValueError("Truncated horizons are smoke tests or diagnostics only")
        scaling = set_representative_weights(n) if a.truncate else dict(method="full_year", snapshots=int(len(n.snapshots)), horizon_fraction=1.0, annual_caps_scaled=False)
        n.meta.update(solver_allowed=True, artifact_role=a.label + "_UNSOLVED", s2_solve_authorization=a.authorization, s2_solve_label=a.label)
        from assembly_components import install_research_constraint_hooks
        from phase4_static import config
        cfg = config(a.repo, a.scenario)
        tl = int((n.meta.get("research_transmission_losses") or {}).get("ac_transmission_losses", 0))   # S4J-2 (decision 105 a): PyPSA-Eur solving.options.transmission_losses = 2
        t0 = time.time(); m = n.optimize.create_model(transmission_losses=tl); install_research_constraint_hooks(n)
        run["transmission_losses"] = dict(ac_tangents=tl, loss_variables=("Line-loss" in m.variables), network=(n.meta.get("research_transmission_losses") or {}).get("mode", "none"),
                                          ac_losses=(n.meta.get("research_ac_losses") or {}).get("mode", "pypsa_tangent" if tl else "none"),   # S4K-1 (decision 108)
                                          ac_loss_proxy=n.meta.get("research_ac_loss_proxy_model"))
        hooks = sorted(k for k in m.constraints if k.startswith("research_") or k.startswith("Research"))
        SV = cfg["research"].get("solver", {})
        profile = a.solver_profile or SV.get("profile")
        scaling_on = (a.scaling == "on") if a.scaling else bool(SV.get("scaling", {}).get("enabled", False))
        const_led, store_led = None, None
        if scaling_on and SV.get("scaling", {}).get("objective_constants_out", True):   # S3B R4 (a)
            from s3b_scaling import remove_objective_constants
            const_led = remove_objective_constants(m)
        lp_meta, M = export_lp(m, out / "lp"); build_seconds = time.time() - t0
        if const_led:   # exported LP is in original units without the constant columns; record the removed constants as the objective offset
            lp_meta["offset"] = float(lp_meta.get("offset", 0.0)) + const_led["total_eur"]; lp_meta["offset_source"] = "S3B R4 (a): objective constant columns moved out of the LP"
            save(out / "lp" / "MATH_PROBLEM.json", lp_meta)
        if scaling_on and SV.get("scaling", {}).get("store_energy_units", True):   # S3B R4 (b)
            from s3b_scaling import select_stores, scale_store_energy
            groups = SV.get("scaling", {}).get("store_groups", ["biomass_pools", "sequestration", "capture_buffers"])
            sel = select_stores(n, groups); allst = sorted({s for v in sel.values() for s in v})
            store_led = scale_store_energy(m, allst, float(SV.get("scaling", {}).get("store_energy_factor", 1000.0)))
            store_led["by_group"] = {k: len(v) for k, v in sel.items()}
        kvl_led = None
        kvl_on = (a.kvl_norm == "on") if a.kvl_norm else bool(scaling_on and SV.get("scaling", {}).get("kirchhoff_row_normalisation", False))
        if kvl_on:   # S4C-5 (decision 69 c / 84): KVL row normalisation after the export (exported LP in original units), duals restored after the solve
            from s3b_scaling import normalise_kvl_rows
            kvl_led = normalise_kvl_rows(m)
        from s3b_scaling import public as _pub
        run["solver_profile"] = profile; run["scaling"] = dict(enabled=scaling_on, objective_constants=const_led, store_energy=(_pub(store_led) if store_led else None),
                                                               kirchhoff_row_normalisation=(_pub(kvl_led) if kvl_led else dict(applied=False)))
        run.update(input_network=dict(path=str(a.network), sha256=net_sha, snapshots=int(len(n.snapshots)), truncated_to=a.truncate, horizon_scaling=scaling),
                   lp=dict(num_col=lp_meta["num_col"], num_row=lp_meta["num_row"], nnz=lp_meta["nnz"], build_seconds=build_seconds, research_constraints=hooks))
        save(out / "SOLVE_RECEIPT.json", run)
        if a.solver == "gurobi" and profile:   # S3B R4 (decision 69): research.solver.profiles (PyPSA-Eur v2025.07.0 gurobi-default lines 1056-1064 as basis)
            params = dict(SV["profiles"][profile]); params["TimeLimit"] = float(a.time_limit)
            run["parameter_source"] = f"decision 69: research.solver.profiles.{profile} (PyPSA-Eur gurobi-default basis; differences registered) + TimeLimit (stop-loss)"
        elif a.solver == "gurobi":   # decision 65: PyPSA-Eur numeric-robust style; license via GRB_LICENSE_FILE (read-only, never copied or logged)
            params = dict(Method=2, NumericFocus=3, BarHomogeneous=1, Crossover=1, Threads=8, TimeLimit=float(a.time_limit))
            run["parameter_source"] = "decision 65: Gurobi Method 2 (barrier), NumericFocus 3, BarHomogeneous 1 (separates true infeasibility from numerics), Crossover 1 (on), Threads 8, TimeLimit; log file via linopy log_fn"
        else:
            params = dict(threads=4, log_file=str(out / "highs.log"), time_limit=float(a.time_limit), solver="ipm" if a.highs_ipm else "choose")
            run["parameter_source"] = "HiGHS defaults (smoke test / diagnostic only)"
        run["solver_parameters"] = params
        t1 = time.time(); run["optimize_calls"] = 1; save(out / "SOLVE_RECEIPT.json", run)
        status, condition = m.solve(solver_name=a.solver, **params, log_fn=str(out / (a.solver + ".linopy.log")))   # = PyPSA solve_model without the assignment step
        if status == "ok":
            if store_led:
                from s3b_scaling import unscale_solution
                unscale_solution(m, store_led)
            if kvl_led:
                from s3b_scaling import unscale_kvl_duals
                unscale_kvl_duals(m, kvl_led)
            n.optimize.assign_solution(); n.optimize.assign_duals(); n.optimize.post_processing()
            if const_led:
                n.objective = float(m.objective.value) + const_led["total_eur"]   # total-cost definition unchanged (constants added back)
        run.update(status=status, termination_condition=condition, solve_seconds=time.time() - t1)
        if a.solver == "gurobi":
            run["gurobi_log_stats"] = gurobi_log_stats(out / (a.solver + ".linopy.log"), out / "GUROBI_LOG_SCRUBBED.txt")
        if status != "ok":
            diag = dict(status=status, condition=condition, structural=structural_diagnosis_s2(n),
                        reading="countries with can_store_or_export_co2 == false and positive unavoidable CO2 cannot meet the per-country net-zero cap (decisions 49/53): no relaxation; see the GAP_DIAGNOSTIC run")
            save(out / "INFEASIBILITY_DIAGNOSIS.json", diag); run["decision"] = "STOP_INFEASIBLE_OR_FAILED_NO_RELAXATION"; save(out / "SOLVE_RECEIPT.json", run)
            print(json.dumps(dict(status=status, condition=condition))); return 2
        run["objective"] = float(n.objective); run["objective_lp"] = float(m.objective.value)
        sol_dir = out / "solution"; sol_dir.mkdir(exist_ok=True)
        X = np.asarray(M.sol, dtype="<f8"); Pi = np.asarray(M.dual, dtype="<f8"); rc_map = reduced_costs(m, a.solver)
        if store_led:
            from s3b_scaling import unscale_reduced_costs
            rc_map = unscale_reduced_costs(rc_map, store_led)
        RC = np.array([rc_map.get(int(l), np.nan) for l in M.vlabels], dtype="<f8")
        for k, v in [("X", X), ("Pi", Pi), ("RC", RC)]:
            np.save(sol_dir / (k + ".npy"), v)
        run["solution"] = {k: dict(count=int(len(v)), sha256=sha(sol_dir / (k + ".npy"))) for k, v in [("X", X), ("Pi", Pi), ("RC", RC)]}
        from v5.v5_gates import (load_contract, gate_a1_a2_kkt, gate_a3_a5_physics, gate_a4_readback, gate_a6_binding, gate_b1_country_net_zero, gate_b12_hash,
                                 gate_b2_storage_cap, gate_b3_biomass, gate_b8_demand_consistency, gate_b11_supply_routes, capacity_reduced_costs, nodal_prices, cross_border_flows,
                                 gate_b13_imports_one_way, gate_b14_terminal_caps, gate_b15_domestic_production_caps)
        from country_carbon import emission_report
        n.meta["artifact_role"] = a.label + "_SOLVED"; n.meta["result_label"] = a.label
        capacity_reduced_costs(n, m, rc_map).to_csv(out / "capacity_reduced_costs.csv", index=False)
        prices, full = nodal_prices(n); prices.to_csv(out / "nodal_prices_summary.csv", index=False)
        cross_border_flows(n).to_csv(out / "cross_border_flows.csv", index=False)
        emis = emission_report(n); save(out / "EMISSIONS_BY_COUNTRY.json", emis)
        flows = co2_flows(n); save(out / "CO2_FLOWS.json", flows)
        caps = {typ: n.df(typ).groupby(["carrier", "country"])[nom + "_opt"].sum().reset_index().to_dict("records") for typ, nom in [("Generator", "p_nom"), ("Link", "p_nom"), ("StorageUnit", "p_nom"), ("Store", "e_nom")] if "country" in n.df(typ)}
        save(out / "CAPACITY_BY_TECH_COUNTRY.json", caps)
        contract = load_contract(); gates = {}
        interior = a.solver == "gurobi" and int(params.get("Crossover", 1)) == 0
        try:
            if interior:   # S3B R4.4: interior-point criteria tied to BarConvTol
                from v5.v5_gates import gate_a1_a2_interior
                I = SV.get("interior", {})
                gates["A1_A2"] = gate_a1_a2_interior(out / "lp", sol_dir, out / "v5", contract, float(params["BarConvTol"]), float(I.get("gap_factor", 10)), float(I.get("dual_factor", 100)))
            else:
                gates["A1_A2"] = gate_a1_a2_kkt(out / "lp", sol_dir, out / "v5", contract)
        except Exception as e:
            gates["A1_A2"] = dict(gate="A1_A2_KKT_AND_BUDGETS", passed=False, error=str(e)[:500])
        if a.solver == "gurobi":   # S3B R4.4: cleanup thresholds (reporting) and simultaneous charge/discharge
            from s3b_interior import cleanup_thresholds, simultaneous_charge_discharge
            thr = cleanup_thresholds(n, float(params.get("BarConvTol", 1e-8)), float(SV.get("interior", {}).get("cleanup_factor", 10)))
            save(out / "INTERIOR_CHECKS.json", dict(cleanup_thresholds=thr, simultaneous_charge_discharge=simultaneous_charge_discharge(n, thr), interior_solution=interior))
        known = {}
        try:
            if gap and "Research_gap_co2_slack" in m.variables:
                sol = m.variables["Research_gap_co2_slack"].solution
                known["gap_co2_slack_x_penalty_eur"] = float(sol.sum().item()) * float(n.meta["gap_diagnostic"]["penalty_eur_per_tco2"])
            a3, a5 = gate_a3_a5_physics(n, known_terms=known, ignore_checks=("COUNTRY_CO2_CAP:",) if gap else ()); gates["A3"] = a3; gates["A5"] = a5
        except Exception as e:
            gates["A3"] = dict(gate="A3_PHYSICS", passed=False, error=str(e)[:500]); gates["A5"] = dict(gate="A5_FOM_ONCE", passed=False, error=str(e)[:500])
        gates["A4"] = gate_a4_readback(n, out / (a.scenario + "_" + a.label + "_solved.nc"))
        gates["A6"] = gate_a6_binding(run, lp_meta, net_sha)
        if not gap:
            gates["B1"] = gate_b1_country_net_zero(n)
        if "research_bunker_net_zero" in n.meta.get("required_constraint_hooks", []):   # S4C-3 (decision 88): ASEAN bunker account, net zero on its own (also in the gap diagnostic)
            from s4c_layers import bunker_account_report
            from s4b_acceptance import ABS_FLOOR
            gates["B1_BUNKERS"] = bunker_account_report(n, float(SV.get("interior", {}).get("solver_tol_factor", 10)) * float(SV.get("interior", {}).get("feasibility_tol", 1e-6)), ABS_FLOOR)
            save(out / "BUNKER_ACCOUNT.json", gates["B1_BUNKERS"])
        gates["B2"] = gate_b2_storage_cap(n); gates["B3"] = gate_b3_biomass(n); gates["B8"] = gate_b8_demand_consistency(n)
        gates["B11"] = gate_b11_supply_routes(n, cfg); gates["B12"] = gate_b12_hash(n, cfg)
        gates["B13"] = gate_b13_imports_one_way(n); gates["B14"] = gate_b14_terminal_caps(n); gates["B15"] = gate_b15_domestic_production_caps(n)   # S3-6
        try:   # S4D-3 (decision 91a): country cost ledger, nodal prices, identity gate B16_LEDGER (exported with the run)
            from s4d_ledger import country_cost_ledger, ledger_gate, ledger_table, load_length_shares, nodal_prices
            led_rows, led_id, led_diag = country_cost_ledger(n, load_length_shares(), extra_terms=(known if gap else None))
            ledger_table(led_rows).to_csv(out / "COUNTRY_COST_LEDGER.csv", float_format="%.6f"); led_rows.to_csv(out / "COUNTRY_COST_LEDGER_DETAIL.csv", index=False, float_format="%.6f")
            nodal_prices(n).to_csv(out / "NODAL_PRICES.csv", float_format="%.6g")
            save(out / "LEDGER_IDENTITY.json", dict(identity=led_id, diagnostics=led_diag))
            gates["B16_LEDGER"] = ledger_gate(led_id)
        except Exception as e:
            gates["B16_LEDGER"] = dict(gate="B16_LEDGER", passed=False, error=str(e)[:500], traceback=traceback.format_exc()[-1500:])
        gates["contract"] = dict(id=contract["contract_id"], status=contract["status"], result_label=a.label)
        # S4B-0 (decision 71, option 1): budgets tied to Gurobi FeasibilityTol / OptimalityTol with row-activity relative terms (s4b_acceptance.py);
        # the S3B gates above stay unchanged for comparison and both verdicts are recorded; research.solver.interior.acceptance_basis selects all_passed.
        I = SV.get("interior", {}); basis = str(I.get("acceptance_basis", "barconvtol"))
        if a.solver == "gurobi":
            try:
                from s4b_acceptance import evaluate as s4b_evaluate
                gates.update(s4b_evaluate(n, out / "lp", sol_dir, out / "v5", I, float(params.get("BarConvTol", 1e-8)), m=m, gap=gap, known_terms=(known if gap else None)))
            except Exception as e:
                gates["A1_A2_S4B"] = dict(gate="A1_A2_SOLVER_TOLERANCES", passed=False, error=str(e)[:500], traceback=traceback.format_exc()[-1500:])
        from s4b_acceptance import all_passed as acceptance_all_passed
        gates["acceptance_basis"] = basis
        gates["all_passed_barconvtol"] = acceptance_all_passed(gates, "barconvtol"); gates["all_passed_solver_tolerances"] = acceptance_all_passed(gates, "solver_tolerances")
        gates["all_passed"] = gates["all_passed_" + basis] if basis in ("barconvtol", "solver_tolerances") else all(v["passed"] for k, v in gates.items() if isinstance(v, dict) and "passed" in v)
        save(out / "V5_GATES.json", gates)
        if gap:
            table = gap_table(n, m); save(out / "GAP_TABLE.json", dict(label="GAP_DIAGNOSTIC_NOT_FOR_INTERCONNECTION_VALUE", rows=table, penalties=n.meta["gap_diagnostic"]))
            run["gap_table"] = table
        run.update(gates={k: v["passed"] for k, v in gates.items() if isinstance(v, dict) and "passed" in v}, peak_rss_bytes=sampler.peak, finished_epoch=time.time(),
                   solved_network=gates["A4"]["file"], decision="SOLVED_" + a.label, emissions_by_country=emis["by_country"], co2_flows=flows)
        save(out / "SOLVE_RECEIPT.json", run)
        print(json.dumps(dict(status=status, objective=run["objective"], gates=run["gates"], peak_rss_gib=round(sampler.peak / 2**30, 2)))); return 0
    except BaseException as e:
        run.update(failure=dict(error=type(e).__name__, detail=str(e)[:2000], traceback=traceback.format_exc()[-4000:]), peak_rss_bytes=sampler.peak, finished_epoch=time.time()); save(out / "SOLVE_RECEIPT.json", run); raise
    finally:
        sampler.stop.set()


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--repo", type=Path, default=HERE.parent); p.add_argument("--network", type=Path, required=True); p.add_argument("--scenario", required=True); p.add_argument("--output", type=Path, required=True)
    p.add_argument("--solver-profile", default=None, help="research.solver.profiles key (S3B R4); default research.solver.profile"); p.add_argument("--scaling", choices=["on", "off"], default=None, help="S3B R4 scaling override; default research.solver.scaling.enabled")
    p.add_argument("--kvl-norm", choices=["on", "off"], default=None, help="S4C-5 Kirchhoff row normalisation override; default research.solver.scaling.kirchhoff_row_normalisation (with scaling on)")
    p.add_argument("--solver", choices=["highs", "gurobi"], default="highs"); p.add_argument("--truncate", type=int, default=0); p.add_argument("--label", default="SMOKE_TEST_ONLY"); p.add_argument("--authorization", required=True); p.add_argument("--time-limit", type=float, default=3600.0); p.add_argument("--highs-ipm", action="store_true")
    sys.exit(main(p.parse_args()))
