"""S4L-1 data (S4L instruction S4L-1; decision 113 (1)): near-zero quantity inventory on the S4K-3 networks, the thresholds with their
PyPSA-Eur references, the use of the listed objects in the L23 first-batch results, the registry fragment s4l_1, and (after the S4L-1 builds)
the component-level comparison of the cleaned networks with the S4K-3 networks.

    python scripts_project/s4l_1_data.py inventory --s4k results_project/s4k/s4k3/builds --l23 <L23 export dir> --out research_inputs/numerics
    python scripts_project/s4l_1_data.py compare   --s4k results_project/s4k/s4k3/builds --s4l results_project/s4l/s4l1/builds --out research_inputs/numerics
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from d1_common import REG_DIR, ROOT, Registry, sha256  # noqa: E402
from s4l_layers import DEFAULT_CAPACITY_MW, DEFAULT_ENERGY_MWH, PYPSA_EUR_REFS, dust_inventory  # noqa: E402

SCRIPT = "scripts_project/s4l_1_data.py"
INSTRUCTION_SHA = "03508400f675304cd0bdfd40ccbd0c61005644e7b2a122dffbe2048e6a5d529b"
SRC = "S4L instruction v1 2026-10-19 10:10 SGT, section S4L-1 (user decision 113 confirmed 2026-10-19 09:57 SGT)"
LOC = "work/p1_step4l_20261019/S4L_CLAUDE_CODE_INSTRUCTION.md"
PE = "research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml"
SCEN = ("integrated", "disconnected")


def net(p):
    import pypsa
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    return pypsa.Network(str(p))


def summarise(T: pd.DataFrame) -> dict:
    fin = T.capacity_mw.astype(float).where(np.isfinite(T.capacity_mw.astype(float)), 0.0)
    d = T.assign(cap=fin, en=T.energy_mwh.fillna(0.0))
    by_class = d.groupby(["dust_class", "action"]).agg(count=("name", "size"), capacity_mw=("cap", "sum"), energy_mwh=("en", "sum")).reset_index().to_dict("records")
    dele = d[d.action.isin(["delete", "merge"])]
    by_country = dele.groupby("country").agg(count=("name", "size"), capacity_mw=("cap", "sum"), energy_mwh=("en", "sum")).reset_index().to_dict("records")
    by_cc = dele.groupby(["country", "dust_class"]).size().unstack(fill_value=0)
    return dict(rows=int(len(T)), by_class_action=by_class, removed_or_merged=dict(count=int(len(dele)), by_country=by_country, by_country_class=by_cc.to_dict("index"),
                                                                                 energy_mwh=float(dele.en.sum()), capacity_mw_finite=float(dele.cap.sum()),
                                                                                 unbounded=int((~np.isfinite(dele.capacity_mw.astype(float))).sum())),
                kept_listed={k: int(v) for k, v in T[T.action == "keep"].dust_class.value_counts().items()})


def l23_usage(n, T: pd.DataFrame) -> dict:
    """How the listed objects were used in a solved L23 network (365x24h): pools, extra-ASEAN stores, FT links, dead-end fuel generators."""
    w = n.snapshot_weightings.stores; out = {}
    pools = T[(T.dust_class == "biomass_pool_below_energy") & T.name.isin(n.stores.index)]
    rows = []
    for name in pools.name:
        e = n.stores_t.e[name]; z = n.stores.loc[name]
        rows.append(dict(store=name, country=str(z.country), e_nom_mwh=float(z.e_nom), used_mwh=float(z.e_initial - e.iloc[-1]), min_level_mwh=float(e.min()),
                         final_level_mwh=float(e.iloc[-1]), share_used=(float(z.e_initial - e.iloc[-1]) / float(z.e_nom) if z.e_nom else None)))
    out["biomass_pools"] = rows
    ex = T[T.dust_class == "kept_extra_asean_co2_store"]
    out["extra_asean_stores"] = [dict(store=k, country=str(n.stores.at[k, "country"]), e_nom_opt_t=float(n.stores.at[k, "e_nom_opt"]), final_level_t=float(n.stores_t.e[k].iloc[-1]),
                                      max_level_t=float(n.stores_t.e[k].max())) for k in ex.name if k in n.stores.index]
    ft = T[(T.dust_class == "kept_zero_capacity_extendable_link") & T.name.isin(n.links.index)]
    g = n.links.loc[ft.name]; p0 = n.links_t.p0[ft.name].mul(w, axis=0).sum()
    byc = pd.DataFrame(dict(country=g.country.astype(str), p_nom_opt_mw=g.p_nom_opt.astype(float), input_mwh=p0.abs().reindex(g.index).astype(float)))
    agg = byc.groupby("country").agg(links=("p_nom_opt_mw", "size"), built=("p_nom_opt_mw", lambda s: int((s > 1.0).sum())), p_nom_opt_mw=("p_nom_opt_mw", "sum"), input_twh=("input_mwh", lambda s: float(s.sum()) / 1e6))
    out["ft_links"] = dict(by_country=agg.reset_index().to_dict("records"), total_links=int(len(g)), built_links_gt_1mw=int((g.p_nom_opt > 1.0).sum()),
                           near_zero_links_lt_1mw=int(((g.p_nom_opt >= 0) & (g.p_nom_opt < 1.0)).sum()), p_nom_opt_min_max=[float(g.p_nom_opt.min()), float(g.p_nom_opt.max())])
    dead = T[(T.dust_class == "single_attachment_fuel_bus_component") & (T.component == "Generator") & T.name.isin(n.generators.index)]
    p = n.generators_t.p[dead.name] if len(dead) else pd.DataFrame()
    out["dead_end_fuel_generators"] = dict(count=int(len(dead)), dispatch_mwh_total=float(p.mul(w, axis=0).sum().sum()) if len(dead) else 0.0, max_abs_p_mw=float(p.abs().max().max()) if len(dead) else 0.0,
                                           p_nom_opt_max=float(n.generators.loc[dead.name, "p_nom_opt"].max()) if len(dead) else 0.0)
    zc = T[(T.dust_class == "zero_upper_candidate")]
    vals = []
    for typ in ("Generator", "StorageUnit", "Link"):
        d = n.df(typ); names = [x for x in zc.name[zc.component == typ] if x in d.index]
        if names:
            vals.append(float(d.loc[names, "p_nom_opt"].abs().max()))
    out["zero_upper_candidates_p_nom_opt_max"] = max(vals) if vals else 0.0
    zl = T[(T.dust_class == "all_zero_load") & T.name.isin(n.loads.index)]
    out["all_zero_loads_in_network"] = int(len(zl))
    out["objective"] = float(n.objective); out["label"] = str(n.meta.get("result_label", ""))
    return out


def inventory(a):
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    thr = dict(energy_mwh=DEFAULT_ENERGY_MWH, capacity_mw=DEFAULT_CAPACITY_MW)
    res = dict(thresholds=thr, pypsa_eur=PYPSA_EUR_REFS, scenarios={}, l23={})
    for sc in SCEN:
        p = Path(a.s4k) / sc / f"{sc}_2920_3h_unsolved.nc"
        n = net(p); T = dust_inventory(n, thr)
        T.to_csv(out / f"DUST_INVENTORY_S4L1_{sc}.csv", index=False)
        from s4l_layers import pool_balance
        res["scenarios"][sc] = dict(network=str(p), sha256=sha256(p), components={c.name: int(len(c.df)) for c in n.iterate_components()},
                                    clip_p_max_pu_applied=(n.meta.get("research_renewable") or {}).get("clip_p_max_pu"), summary=summarise(T), pool_balance=pool_balance(n),
                                    pools_kept_binding=T[T.dust_class == "kept_pool_fixed_demand_binding"][["name", "country", "energy_mwh", "note"]].to_dict("records"),
                                    pools_below_threshold=T[T.dust_class == "biomass_pool_below_energy"][["name", "country", "energy_mwh", "note"]].to_dict("records"),
                                    renewable_below_capacity=T[T.dust_class == "renewable_potential_below_capacity"][["name", "country", "carrier", "capacity_mw", "energy_mwh"]].to_dict("records"),
                                    single_attachment_kept=T[T.dust_class == "single_attachment_fuel_bus_kept"][["name", "country", "carrier", "note"]].to_dict("records"),
                                    merged_groups=T[T.action == "merge_keep"][["name", "country", "note"]].to_dict("records"))
        if a.l23:
            q = Path(a.l23) / sc / f"{sc}_FORMAL_TRIAL_365X24H_solved.nc"
            if q.exists():
                res["l23"][sc] = dict(network=str(q), sha256=sha256(q), usage=l23_usage(net(q), T))
        print(sc, json.dumps(res["scenarios"][sc]["summary"]["removed_or_merged"]["by_country"])[:400])
    (out / "DUST_S4L1.json").write_text(json.dumps(res, indent=1, default=str))
    # registry fragment s4l_1
    reg = Registry(SCRIPT); pe_sha = sha256(ROOT / PE)
    reg.add("s4l1_dust_cleanup_switch", "S4L-1: switch research.numerics.dust_cleanup: on (main-run candidate; the user decides after the S4L report) | off (default, "
            "S4K state); applied at the end of the S2 build (scripts_project/s4l_layers.apply_dust_cleanup) before the static validation; every build writes "
            "<scenario>_DUST_INVENTORY_S4L1.csv and the receipt / metadata research_dust_cleanup", "off", "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="113", status="REFERENCE_ONLY")
    reg.add("s4l1_dust_energy_threshold", "S4L-1 point 2: finite biomass pools and renewable potentials with a yearly energy below this value are near-zero and removed "
            "(dust_cleanup on); project choice - PyPSA-Eur v2025.07.0 has no energy threshold for biomass potentials; 1 GWh/a is about 0.1 MW-year, below the "
            "scale at which any conversion candidate is built, and the scale of the SG / BN / TL pools (0.5-800 MWh) that carried the largest violation ratios in "
            "L23 (SG cassava residues 0.47 MWh: 902 x budget)", DEFAULT_ENERGY_MWH, "MWh/a", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="113", status="REFERENCE_ONLY")
    reg.add("s4l1_dust_capacity_threshold", "S4L-1 point 2: extendable candidates (renewable potentials, storage and conversion candidates) with p_nom_max below this "
            "value (incl. the zero upper bounds of S4I R4) are near-zero and removed; value adopted from PyPSA-Eur v2025.07.0 renewable.hydro.clip_min_inflow: 1.0 "
            "(config line 300: inflow below 1 MW set to zero); PyPSA-Eur existing_capacities.threshold_capacity 10 MW (line 469) drops existing plants and is NOT "
            "adopted (existing stock untouched here); renewable clip_p_max_pu 1e-2 (lines 200-292, applied by S4A) and solving.options.clip_p_max_pu 1e-2 (line 988) "
            "clip profiles, not components", DEFAULT_CAPACITY_MW, "MW", "B", "PyPSA-Eur v2025.07.0 config.default.yaml lines 200, 218, 237, 259, 276, 292, 300, 469, 700, 988",
            PE, pe_sha, decision_ref="113", status="REFERENCE_ONLY")
    reg.add("s4l1_pool_fixed_demand_guard", "S4L-1 rule added after the S4L-2 matrix (s4l_A runs infeasible): a finite pool below the energy threshold is removed only "
            "while the pools of its bus keep covering the fixed demand fed from that bus (Loads on the bus and on the buses of the links leaving it, e.g. the "
            "'<node> ... biomass final' buses behind the meter / CC links); otherwise it is kept and listed as kept_pool_fixed_demand_binding. Finding: in BN, SG and VN "
            "the solid biomass pools equal the fixed biomass final demand exactly (BN 115,935.8 MWh, SG 31,510.2 MWh, VN 125,772,566.2 MWh; zero slack), so every "
            "pool there is needed; the cleanup asserts after the deletions that no pool bus is below its fixed demand", "keep_if_needed", "flag", "B", SRC, LOC,
            INSTRUCTION_SHA, decision_ref="113", status="REFERENCE_ONLY")
    reg.add("s4l1_dust_delete_rule", "S4L-1 point 3: removed when dust_cleanup = on - near-zero finite pools (subject to the fixed-demand guard s4l1_pool_fixed_demand_guard); renewable potentials below the capacity / energy threshold; "
            "all-zero-profile generators (S4I R5); zero-upper candidates and their legacy parameters (S4I R4: pumpable hydro efficiency_store 1, PHS 0.75, ror without "
            "profile, zero-cap geothermal); all-zero loads (S4I R5); single-attachment fuel buses with their dead-end supply generator or flow-less link port (S4I R1); "
            "metadata keyed by name (store_power_rules, research_biomass.stores, demand_owners / demand_identity, research_new_hydro_inflow_tie) pruned; the "
            "per-node required-candidate check skips the (type, carrier, node) triples removed here (recorded as removed_required_structure)",
            "delete", "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="113", status="REFERENCE_ONLY")
    reg.add("s4l1_dust_merge_rule", "S4L-1 point 3: identical parallel links (S4I R3; every static attribute equal, no time series, p_nom = p_nom_min = 0, extendable, no "
            "twin) are merged into one link per group keeping the first name (sorted) with p_nom_max = N x p_nom_max (inf stays inf): capacity and cost equivalent "
            "(same per-MW cost and efficiencies); 97 biomass-to-methanol links -> 11 (one per country)", "merge", "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="113", status="REFERENCE_ONLY")
    reg.add("s4l1_dust_keep_rule", "S4L-1 point 3: NOT removed (listed only): candidates with economic meaning - zero-capacity but extendable Fischer-Tropsch links "
            "(unbounded, capital cost), the uncapped extra-ASEAN CO2 export stores (decision 89), fixed sources below 1 MW (plastic waste: exogenous data), and "
            "single-attachment fuel buses whose only attachment is a zero-efficiency link port", "keep", "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="113", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4l_1.csv")
    print("registry fragment s4l_1 written:", len(reg.rows), "rows;", out / "DUST_S4L1.json")


def compare(a):
    out = Path(a.out); res = {}
    for sc in SCEN:
        k = net(Path(a.s4k) / sc / f"{sc}_2920_3h_unsolved.nc"); l = net(Path(a.s4l) / sc / f"{sc}_2920_3h_unsolved.nc")
        led = l.meta["research_dust_cleanup"]; r = dict(mode=led["mode"], thresholds=led["thresholds"], removed=led["removed"], merged_links_removed=led.get("merged_links_removed"),
                                                        removed_required_structure=len(led.get("removed_required_structure", [])), components_s4k={}, components_s4l={}, surviving_identical={}, differences={})
        for c in k.iterate_components():
            t = c.name; dk, dl = k.df(t), l.df(t)
            r["components_s4k"][t] = int(len(dk)); r["components_s4l"][t] = int(len(dl))
            common = dl.index.intersection(dk.index); extra = dl.index.difference(dk.index)
            cols = [x for x in dk.columns if x in dl.columns]
            A, Bt = dk.loc[common, cols], dl.loc[common, cols]
            diff = {}
            for col in cols:
                x, y = A[col], Bt[col]
                try:
                    neq = ~((x == y) | (x.isna() & y.isna()))
                    if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
                        neq = ~(np.isclose(x.astype(float), y.astype(float), rtol=0, atol=0, equal_nan=True) | (np.isinf(x.astype(float)) & np.isinf(y.astype(float))))
                except Exception:
                    neq = pd.Series(True, index=common)
                if bool(neq.any()):
                    diff[col] = dict(count=int(neq.sum()), examples={str(i): [str(x[i]), str(y[i])] for i in common[neq][:3]})
            r["surviving_identical"][t] = dict(common=int(len(common)), new_in_s4l=int(len(extra)), columns_with_differences=sorted(diff))
            if diff:
                r["differences"][t] = diff
            for attr, dfk in k.pnl(t).items():
                if attr in l.pnl(t) and len(dfk.columns):
                    dfl = l.pnl(t)[attr]; cc = dfk.columns.intersection(dfl.columns)
                    if len(cc) and not np.allclose(dfk[cc].to_numpy(), dfl[cc].to_numpy(), rtol=0, atol=0):
                        r["differences"][f"{t}_t.{attr}"] = "time series differ on surviving components"
        r["meta_keys_differ"] = sorted(set(k.meta) ^ set(l.meta))
        res[sc] = r
        print(sc, "s4k", {t: r["components_s4k"][t] for t in ("Bus", "Generator", "Link", "Load", "Store", "StorageUnit")}, "s4l", {t: r["components_s4l"][t] for t in ("Bus", "Generator", "Link", "Load", "Store", "StorageUnit")}, "diff", list(r["differences"]))
    (out / "DUST_IMPACT_S4L1.json").write_text(json.dumps(res, indent=1, default=str))


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("inventory"); p1.add_argument("--s4k", type=Path, required=True); p1.add_argument("--l23", type=Path, default=None); p1.add_argument("--out", type=Path, required=True)
    p2 = sub.add_parser("compare"); p2.add_argument("--s4k", type=Path, required=True); p2.add_argument("--s4l", type=Path, required=True); p2.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    (inventory if a.cmd == "inventory" else compare)(a)


if __name__ == "__main__":
    main()
