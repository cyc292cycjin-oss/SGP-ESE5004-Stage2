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
    out = dict(sequestered_by_country={}, captured_by_carrier={}, vented_by_country={}, cross_border_pipeline={}, dac_by_country={})
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
    pset = n.get_switchable_as_dense("Load", "p_set")
    for c in sorted(set(n.buses.country.dropna()) - {""}):
        gens = slack[slack.country == c]
        e = float(sum((n.generators_t.p[g] * w).sum() for g in gens.index if g in n.generators_t.p))
        dem = float(sum((pset[l] * w).sum() for l in n.loads.index[(n.loads.country == c) & (n.loads.carrier.isin(["electricity", "land transport EV", "agriculture machinery electric"]))]))
        bg = bslack[bslack.country == c]
        b = float(sum((n.generators_t.p[g] * w).sum() for g in bg.index if g in n.generators_t.p))
        bdem = float(sum((pset[l] * w).sum() for l in n.loads.index[(n.loads.country == c) & (n.loads.carrier == "biomass final energy")]))
        bpot = float(n.stores[(n.stores.bus == f"solid biomass {c}") & (n.stores.research_role == "FINITE_RESOURCE")].e_nom.sum()) if "research_role" in n.stores else 0.0
        rows.append(dict(country=c, electricity_gap_mwh=e, electricity_demand_mwh=dem, electricity_gap_share=(e / dem if dem else None), co2_gap_t=co2.get(c), cap_tco2=n.meta["research_carbon"]["country_cap_tco2"].get(c),
                         biomass_gap_mwh=b, biomass_final_demand_mwh=bdem, solid_biomass_potential_mwh=bpot))
    return rows


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
        t0 = time.time(); m = n.optimize.create_model(); install_research_constraint_hooks(n)
        hooks = sorted(k for k in m.constraints if k.startswith("research_") or k.startswith("Research"))
        lp_meta, M = export_lp(m, out / "lp"); build_seconds = time.time() - t0
        run.update(input_network=dict(path=str(a.network), sha256=net_sha, snapshots=int(len(n.snapshots)), truncated_to=a.truncate, horizon_scaling=scaling),
                   lp=dict(num_col=lp_meta["num_col"], num_row=lp_meta["num_row"], nnz=lp_meta["nnz"], build_seconds=build_seconds, research_constraints=hooks))
        save(out / "SOLVE_RECEIPT.json", run)
        params = dict(threads=4, log_file=str(out / "highs.log"), time_limit=float(a.time_limit), solver="ipm" if a.highs_ipm else "choose")
        run["solver_parameters"] = params; run["parameter_source"] = "HiGHS defaults (smoke test / diagnostic only)"
        t1 = time.time(); run["optimize_calls"] = 1; save(out / "SOLVE_RECEIPT.json", run)
        status, condition = n.optimize.solve_model(solver_name=a.solver, solver_options=params, log_fn=str(out / (a.solver + ".linopy.log")))
        run.update(status=status, termination_condition=condition, solve_seconds=time.time() - t1)
        if status != "ok":
            diag = dict(status=status, condition=condition, structural=structural_diagnosis_s2(n),
                        reading="countries with can_store_or_export_co2 == false and positive unavoidable CO2 cannot meet the per-country net-zero cap (decisions 49/53): no relaxation; see the GAP_DIAGNOSTIC run")
            save(out / "INFEASIBILITY_DIAGNOSIS.json", diag); run["decision"] = "STOP_INFEASIBLE_OR_FAILED_NO_RELAXATION"; save(out / "SOLVE_RECEIPT.json", run)
            print(json.dumps(dict(status=status, condition=condition))); return 2
        run["objective"] = float(m.objective.value)
        sol_dir = out / "solution"; sol_dir.mkdir(exist_ok=True)
        X = np.asarray(M.sol, dtype="<f8"); Pi = np.asarray(M.dual, dtype="<f8"); rc_map = reduced_costs(m, a.solver)
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
        try:
            gates["A1_A2"] = gate_a1_a2_kkt(out / "lp", sol_dir, out / "v5", contract)
        except Exception as e:
            gates["A1_A2"] = dict(gate="A1_A2_KKT_AND_BUDGETS", passed=False, error=str(e)[:500])
        try:
            known = {}
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
        gates["B2"] = gate_b2_storage_cap(n); gates["B3"] = gate_b3_biomass(n); gates["B8"] = gate_b8_demand_consistency(n)
        gates["B11"] = gate_b11_supply_routes(n, cfg); gates["B12"] = gate_b12_hash(n, cfg)
        gates["B13"] = gate_b13_imports_one_way(n); gates["B14"] = gate_b14_terminal_caps(n); gates["B15"] = gate_b15_domestic_production_caps(n)   # S3-6
        gates["contract"] = dict(id=contract["contract_id"], status=contract["status"], result_label=a.label)
        gates["all_passed"] = all(v["passed"] for k, v in gates.items() if isinstance(v, dict) and "passed" in v)
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
    p.add_argument("--solver", choices=["highs"], default="highs"); p.add_argument("--truncate", type=int, default=0); p.add_argument("--label", default="SMOKE_TEST_ONLY"); p.add_argument("--authorization", required=True); p.add_argument("--time-limit", type=float, default=3600.0); p.add_argument("--highs-ipm", action="store_true")
    sys.exit(main(p.parse_args()))
