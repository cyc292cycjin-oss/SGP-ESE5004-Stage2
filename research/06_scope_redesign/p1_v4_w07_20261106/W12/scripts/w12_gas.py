"""W12-1: domestic natural-gas production caps use UNSD GROSS production; compare with marketed production and test whether the
caps bind in the solved 56x3h (v3.1) and 365x24h (v3) runs available on this machine.

Reads (read-only): UNdata 2019 export (pypsa-asean), research_inputs/gas_v5/GAS_PRODUCTION_CAPS_2050.csv, the network meta
`external_annual_caps`, generators_t_p x snapshots_generators of each solved network, ResearchImportAnnual-* duals from
DUALS_BY_CONSTRAINT.nc, and the parameter-only meta of the four v3.1 HPC 2920x3h networks.
Writes tables/W12_1_*.csv and evidence/W12_1.json. Nothing is solved.

First-order reading (stated, INFERENCE): for min c'x s.t. a'x <= b the optimal value V(b) is convex and non-increasing, so lowering b by
delta raises V by at least |y| x delta (y = dual of the binding row). Products |y| x delta are therefore LOWER bounds per run; the B6
difference of two lower bounds is only a first-order estimate, not a bound.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w12_common as cm  # noqa: E402

TJ_TO_MWH_NCV = 0.9 / 0.0036   # UNSD GCV TJ x 0.90 -> NCV, / 0.0036 TJ per MWh (d1_fossil_production.py:56)


def unsd_gas():
    u = cm.load_unsd_2019()
    g = u[u.commodity.str.lower().str.startswith("natural gas") & ~u.commodity.str.lower().str.contains("liquids")]
    want = {("natural gas", "gross production"): "gross_tj", ("natural gas (including lng)", "production"): "marketed_tj",
            ("natural gas (including lng)", "flared"): "flared_tj", ("natural gas (including lng)", "vented"): "vented_tj",
            ("natural gas (including lng)", "flared and vented"): "flared_vented_tj", ("natural gas (including lng)", "re-injected"): "reinjected_tj",
            ("natural gas (including lng)", "extraction loss shrinkage"): "shrinkage_tj", ("natural gas (including lng)", "exports"): "exports_tj",
            ("natural gas (including lng)", "imports"): "imports_tj", ("natural gas (including lng)", "energy industries own use"): "energy_own_use_tj",
            ("natural gas (including lng)", "own use by oil and gas extraction"): "own_use_extraction_tj"}
    rows, src = [], {}
    for c in cm.ASEAN:
        r = dict(country=c)
        for (com, tr), col in want.items():
            m = g[(g.ISO == c) & (g.commodity.str.lower() == com) & (g.transaction == tr)]
            r[col] = float(m.q.sum()) if len(m) else 0.0
            if len(m):
                src[(c, col)] = (m.file.iloc[0], m.sha.iloc[0])
        losses = r["flared_vented_tj"] if r["flared_vented_tj"] else r["flared_tj"] + r["vented_tj"]
        r["gross_minus_marketed_tj"] = r["gross_tj"] - r["marketed_tj"]
        r["flared_vented_reinjected_shrinkage_tj"] = losses + r["reinjected_tj"] + r["shrinkage_tj"]
        r["identity_residual_tj"] = r["gross_minus_marketed_tj"] - r["flared_vented_reinjected_shrinkage_tj"]
        r["gross_over_marketed"] = r["gross_tj"] / r["marketed_tj"] if r["marketed_tj"] else None
        r["cap_gross_mwh"] = r["gross_tj"] * TJ_TO_MWH_NCV
        r["cap_marketed_mwh"] = r["marketed_tj"] * TJ_TO_MWH_NCV
        r["cap_delta_mwh"] = r["cap_gross_mwh"] - r["cap_marketed_mwh"]
        r["marketed_minus_extraction_own_use_mwh"] = (r["marketed_tj"] - r["own_use_extraction_tj"]) * TJ_TO_MWH_NCV
        rows.append(r)
    return pd.DataFrame(rows), src


def network_caps(path: Path) -> dict:
    ds = xr.open_dataset(path)
    try:
        meta = cm.nc_meta(ds)
        caps = {k: float(v) for k, v in meta.get("external_annual_caps", {}).items()}
        gi = [str(x) for x in ds["generators_i"].values]
        carrier = dict(zip(gi, [str(x) for x in ds["generators_carrier"].values]))
        country = dict(zip(gi, [str(x) for x in ds["generators_country"].values]))
        prod = [g for g in gi if carrier[g] == "gas production"]
        mc = dict(zip(gi, ds["generators_marginal_cost"].values.astype(float)))
        out = dict(caps={g: caps.get(g) for g in prod}, country={g: country[g] for g in prod}, marginal_cost={g: mc[g] for g in prod},
                   n_caps_total=len(caps), gas_ledger=meta.get("research_gas_network", {}).get("production"))
        if "generators_t_p" in ds:
            cols = [str(x) for x in ds["generators_t_p_i"].values]
            w = ds["snapshots_generators"].values.astype(float)
            p = ds["generators_t_p"].values
            idx = {c: i for i, c in enumerate(cols)}
            out["annual_mwh"] = {g: (float((p[:, idx[g]] * w).sum()) if g in idx else 0.0) for g in prod}
            out["n_snapshots"] = int(len(w)); out["weight_sum_h"] = float(w.sum())
            # network_objective already contains network_objective_constant (= SOLVE_RECEIPT 'objective'; objective_lp = objective - constant)
            out["objective"] = float(ds.attrs.get("network_objective", np.nan)); out["objective_constant"] = float(ds.attrs.get("network_objective_constant", 0.0))
            lng = [g for g in gi if carrier[g] == "LNG import"]
            pn = dict(zip(gi, ds["generators_p_nom_opt"].values.astype(float))); ext = dict(zip(gi, ds["generators_p_nom_extendable"].values.astype(bool)))
            pnmax = dict(zip(gi, ds["generators_p_nom_max"].values.astype(float))); pnmin = dict(zip(gi, ds["generators_p_nom_min"].values.astype(float)))
            pn0 = dict(zip(gi, ds["generators_p_nom"].values.astype(float))); cc = dict(zip(gi, ds["generators_capital_cost"].values.astype(float)))
            out["lng"] = [dict(generator=g, country=country[g], extendable=ext[g], p_nom=pn0[g], p_nom_min=pnmin[g], p_nom_max=pnmax[g], p_nom_opt=pn[g], capital_cost=cc[g],
                               marginal_cost=mc[g], annual_mwh=(float((p[:, idx[g]] * w).sum()) if g in idx else 0.0), capacity_mwh=pn[g] * float(w.sum())) for g in lng]
        return out
    finally:
        ds.close()


def duals(folder: Path, gens: list[str]) -> dict:
    p = folder / "DUALS_BY_CONSTRAINT.nc"
    ds = xr.open_dataset(p)
    try:
        out = {}
        for g in gens:
            k = "ResearchImportAnnual-" + g
            out[g] = float(ds[k].values) if k in ds else None
        return out
    finally:
        ds.close()


def main():
    ev = cm.Evidence("W12_1")
    u, src = unsd_gas()
    caps_csv = cm.REPO / "research_inputs/gas_v5/GAS_PRODUCTION_CAPS_2050.csv"
    rc = pd.read_csv(caps_csv, keep_default_na=False).set_index("country")
    u["repo_cap_mwh"] = [float(rc.at[c, "cap_mwh_per_year"]) if c in rc.index else 0.0 for c in u.country]
    u["repo_cap_equals_gross"] = (u.repo_cap_mwh - u.cap_gross_mwh).abs() <= 1e-3
    cm.write_csv(u.to_dict("records"), cm.TABLES / "W12_1_UNSD_GAS_2019.csv")
    for r in u.itertuples():
        f, s = src.get((r.country, "gross_tj"), ("", ""))
        if r.gross_tj > 0:
            ev.add(f"{r.country}.gross_tj", r.gross_tj, "TJ GCV", "VERIFIED", "A", f"UNdata export {f} (SHA256 {s[:16]})", "Natural gas - Gross production, 2019")
            ev.add(f"{r.country}.marketed_tj", r.marketed_tj, "TJ GCV", "VERIFIED", "A", f"UNdata export {src.get((r.country, 'marketed_tj'), ('', ''))[0]}",
                   "Natural gas (including LNG) - production, 2019")
            ev.add(f"{r.country}.gross_over_marketed", r.gross_over_marketed, "ratio", "EXACT", "A", "W12_1_UNSD_GAS_2019.csv", "gross / marketed")
            ev.add(f"{r.country}.identity_residual_tj", r.identity_residual_tj, "TJ", "EXACT", "A", "W12_1_UNSD_GAS_2019.csv",
                   "gross - marketed - (flared[+vented] + re-injected + extraction loss shrinkage)")
            ev.add(f"{r.country}.cap_gross_mwh", r.cap_gross_mwh, "MWh NCV/a", "EXACT", "B", "d1_fossil_production.py:54-57 rule", "gross TJ x 0.9 / 0.0036")
            ev.add(f"{r.country}.cap_marketed_mwh", r.cap_marketed_mwh, "MWh NCV/a", "EXACT", "B", "same rule on the marketed row", "marketed TJ x 0.9 / 0.0036")
            ev.add(f"{r.country}.repo_cap_equals_gross", bool(r.repo_cap_equals_gross), "bool", "VERIFIED", "A", f"{caps_csv.relative_to(cm.REPO)} SHA256 {cm.sha256(caps_csv)[:16]}")
    ratio = {r.country: (r.cap_marketed_mwh / r.cap_gross_mwh if r.cap_gross_mwh > 0 else 1.0) for r in u.itertuples()}

    # ---- coupled parameter: fugitive factor oil/gas = EDGAR 1.B.2 / (oil + gas production cap) (s2_0_process_emissions.py:66, :103-108) ----
    fp = cm.REPO / "research_inputs/registry_v5/FOSSIL_PRODUCTION_CAPS_2050.csv"
    fpc = pd.read_csv(fp, keep_default_na=False)
    reg = pd.read_csv(cm.REPO / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    fug = []
    for c in cm.ASEAN:
        oil = float(fpc[(fpc.country == c) & (fpc.carrier == "oil")].cap_mwh_per_year.sum()); gas = float(fpc[(fpc.country == c) & (fpc.carrier == "gas")].cap_mwh_per_year.sum())
        k = f"fugitive_factor_oilgas_{c}"
        if k not in reg.index or not reg.at[k, "unit"].startswith("tCO2/MWh"):
            continue
        f0 = float(reg.at[k, "value"]); emis = f0 * (oil + gas)
        gm = gas * ratio[c]
        f1 = emis / (oil + gm)
        fug.append(dict(country=c, oil_cap_mwh=oil, gas_cap_gross_mwh=gas, gas_cap_marketed_mwh=gm, edgar_1B2_t=emis, factor_registry_t_per_mwh=f0,
                        factor_marketed_basis_t_per_mwh=f1, factor_change=f1 / f0 - 1))
        ev.add(f"{c}.fugitive_factor_change_if_marketed", f1 / f0 - 1, "ratio", "EXACT", "B", f"DATA_REGISTRY.csv {k}; FOSSIL_PRODUCTION_CAPS_2050.csv",
               "EDGAR 1.B.2 / (oil + marketed gas) vs / (oil + gross gas)")
    cm.write_csv(fug, cm.TABLES / "W12_1_FUGITIVE_FACTOR_COUPLING.csv")

    # ---- parameters of the v3.1 HPC networks (2920x3h, unsolved) ---------------------------------------------------------------------
    par = []
    for f in sorted(cm.HPC31.glob("*_unsolved.nc")):
        nc = network_caps(f)
        by = pd.Series({g: v for g, v in nc["caps"].items()}).groupby(pd.Series(nc["country"])).sum()
        for c, v in by.items():
            par.append(dict(network=f"hpc_package_v3_1/networks/{f.name}", network_sha256=cm.sha256(f), country=c, cap_mwh=float(v),
                            unsd_gross_cap_mwh=float(u.set_index("country").at[c, "cap_gross_mwh"]),
                            equals_gross=bool(abs(float(v) - float(u.set_index("country").at[c, "cap_gross_mwh"])) <= 1e-2), generators=int((pd.Series(nc["country"]) == c).sum()),
                            marginal_cost_eur_per_mwh=sorted(set(round(x, 6) for g, x in nc["marginal_cost"].items() if nc["country"][g] == c))[0]))
    cm.write_csv(par, cm.TABLES / "W12_1_V31_HPC_NETWORK_CAPS.csv")
    ev.add("v31_hpc.all_caps_equal_gross", all(r["equals_gross"] for r in par), "bool", "VERIFIED", "A", "W12_1_V31_HPC_NETWORK_CAPS.csv",
           f"{len(set(r['network'] for r in par))} networks x {len(set(r['country'] for r in par))} countries")

    # ---- solved runs ---------------------------------------------------------------------------------------------------------------
    gen_rows, run_rows, lng_rows = [], [], []
    for label, (folder, scen, res, ver) in cm.SOLVED.items():
        f = cm.solved_nc(folder)
        nc = network_caps(f)
        dv = duals(folder, list(nc["caps"]))
        for g, cap in nc["caps"].items():
            c = nc["country"][g]; use = nc["annual_mwh"][g]; y = dv[g]
            cap_m = cap * ratio[c]; delta = cap - cap_m
            gen_rows.append(dict(run=label, scenario=scen, resolution=res, model=ver, generator=g, country=c, cap_gross_mwh=cap, cap_marketed_mwh=cap_m,
                                 annual_mwh=use, utilisation=use / cap if cap else None, dual_eur_per_mwh=y, abs_dual=abs(y) if y is not None else None,
                                 binding=bool(use >= cap * (1 - 1e-4) and y is not None and abs(y) > 1e-6),
                                 use_above_marketed_mwh=max(0.0, use - cap_m), first_order_cost_lb_eur=(abs(y) * delta if y is not None else None),
                                 owen_term_y_b_eur=(y * cap if y is not None else None), owen_term_y_bmarketed_eur=(y * cap_m if y is not None else None)))
        run_rows.append(dict(run=label, scenario=scen, resolution=res, model=ver, network=str(f), n_snapshots=nc["n_snapshots"], weight_sum_h=nc["weight_sum_h"],
                             objective_eur=nc["objective"], objective_constant_eur=nc["objective_constant"]))
        for x in nc["lng"]:
            lng_rows.append(dict(run=label, scenario=scen, **x))
    G = pd.DataFrame(gen_rows)
    cm.write_csv(G.to_dict("records"), cm.TABLES / "W12_1_GAS_CAP_BY_GENERATOR_RUN.csv")
    L = pd.DataFrame(lng_rows)
    LC = L.groupby(["run", "scenario", "country"]).agg(terminals=("generator", "count"), extendable_all=("extendable", "all"), p_nom_existing_mw=("p_nom", "sum"),
                                                       p_nom_opt_mw=("p_nom_opt", "sum"), p_nom_max_mw=("p_nom_max", "sum"), capital_cost_max=("capital_cost", "max"),
                                                       marginal_cost=("marginal_cost", "max"), annual_mwh=("annual_mwh", "sum"), capacity_mwh=("capacity_mwh", "sum")).reset_index()
    LC["spare_mwh"] = LC.capacity_mwh - LC.annual_mwh
    cm.write_csv(LC.to_dict("records"), cm.TABLES / "W12_1_LNG_IMPORT_BY_COUNTRY_RUN.csv")
    for r in LC.itertuples():
        ev.add(f"{r.run}.{r.country}.lng_import", dict(annual_mwh=r.annual_mwh, capacity_mwh=r.capacity_mwh, extendable=bool(r.extendable_all), p_nom_max_mw=r.p_nom_max_mw,
                                                        capital_cost_max=r.capital_cost_max, marginal_cost=r.marginal_cost), "mixed", "VERIFIED", "A",
               f"{r.run} solved network generators (carrier 'LNG import')")
    C = G.groupby(["run", "scenario", "resolution", "country"]).agg(cap_gross_mwh=("cap_gross_mwh", "sum"), cap_marketed_mwh=("cap_marketed_mwh", "sum"),
                                                                     annual_mwh=("annual_mwh", "sum"), binding_generators=("binding", "sum"), generators=("generator", "count"),
                                                                     max_abs_dual=("abs_dual", "max"), use_above_marketed_mwh=("use_above_marketed_mwh", "sum"),
                                                                     first_order_cost_lb_eur=("first_order_cost_lb_eur", "sum"),
                                                                     owen_term_y_b_eur=("owen_term_y_b_eur", "sum")).reset_index()
    C["utilisation"] = C.annual_mwh / C.cap_gross_mwh
    C["utilisation_vs_marketed"] = C.annual_mwh / C.cap_marketed_mwh
    cm.write_csv(C.to_dict("records"), cm.TABLES / "W12_1_GAS_CAP_BY_COUNTRY_RUN.csv")
    R = C.groupby(["run", "scenario", "resolution"]).agg(use_above_marketed_mwh=("use_above_marketed_mwh", "sum"), first_order_cost_lb_eur=("first_order_cost_lb_eur", "sum"),
                                                          binding_generators=("binding_generators", "sum")).reset_index()
    R = R.merge(pd.DataFrame(run_rows)[["run", "model", "n_snapshots", "weight_sum_h", "objective_eur"]], on="run")
    cm.write_csv(R.to_dict("records"), cm.TABLES / "W12_1_GAS_CAP_BY_RUN.csv")

    # B6 pairs (B6 = no_new_xb - integrated), first-order
    pairs = [("S56", "S56_F2", "S56_F1"), ("SCR", "SCR_V2", "SCR_V1"), ("S07", "S07_V2", "S07_V1")]
    b6 = []
    for name, a, b in pairs:
        ra, rb = R.set_index("run").loc[a], R.set_index("run").loc[b]
        b6.append(dict(pair=name, no_new_xb=a, integrated=b, B6_eur=float(ra.objective_eur - rb.objective_eur), dC_no_new_xb_lb_eur=float(ra.first_order_cost_lb_eur),
                       dC_integrated_lb_eur=float(rb.first_order_cost_lb_eur), dB6_first_order_eur=float(ra.first_order_cost_lb_eur - rb.first_order_cost_lb_eur),
                       use_above_marketed_no_new_xb_mwh=float(ra.use_above_marketed_mwh), use_above_marketed_integrated_mwh=float(rb.use_above_marketed_mwh)))
        ca = C[C.run == a].set_index("country"); cb = C[C.run == b].set_index("country")
        for c in sorted(set(ca.index) | set(cb.index)):
            b6.append(dict(pair=name + ":" + c, no_new_xb=a, integrated=b, dC_no_new_xb_lb_eur=float(ca.first_order_cost_lb_eur.get(c, 0.0)),
                           dC_integrated_lb_eur=float(cb.first_order_cost_lb_eur.get(c, 0.0)),
                           dB6_first_order_eur=float(ca.first_order_cost_lb_eur.get(c, 0.0) - cb.first_order_cost_lb_eur.get(c, 0.0)),
                           use_above_marketed_no_new_xb_mwh=float(ca.use_above_marketed_mwh.get(c, 0.0)), use_above_marketed_integrated_mwh=float(cb.use_above_marketed_mwh.get(c, 0.0)),
                           owen_y_b_no_new_xb_eur=float(ca.owen_term_y_b_eur.get(c, 0.0)), owen_y_b_integrated_eur=float(cb.owen_term_y_b_eur.get(c, 0.0)),
                           # Owen dual form share_c = sum of y'b over c-owned rows: with y fixed, lowering c's caps raises c's share by |y| x delta in each run,
                           # so c's Owen benefit (no_new_xb share - integrated share) changes by dC_no_new_xb - dC_integrated (first order)
                           d_owen_benefit_first_order_eur=float(ca.first_order_cost_lb_eur.get(c, 0.0) - cb.first_order_cost_lb_eur.get(c, 0.0))))
    cm.write_csv(b6, cm.TABLES / "W12_1_B6_FIRST_ORDER.csv",
                 ["pair", "no_new_xb", "integrated", "B6_eur", "dC_no_new_xb_lb_eur", "dC_integrated_lb_eur", "dB6_first_order_eur", "use_above_marketed_no_new_xb_mwh",
                  "use_above_marketed_integrated_mwh", "owen_y_b_no_new_xb_eur", "owen_y_b_integrated_eur", "d_owen_benefit_first_order_eur"])
    for r in C.itertuples():
        ev.add(f"{r.run}.{r.country}.annual_mwh", r.annual_mwh, "MWh/a", "VERIFIED", "A", f"{r.run} solved network generators_t_p x snapshots_generators")
        ev.add(f"{r.run}.{r.country}.utilisation", r.utilisation, "ratio", "EXACT", "A", "W12_1_GAS_CAP_BY_COUNTRY_RUN.csv")
        ev.add(f"{r.run}.{r.country}.max_abs_dual", r.max_abs_dual, "EUR2020/MWh", "VERIFIED", "A", f"{r.run} DUALS_BY_CONSTRAINT.nc ResearchImportAnnual-*")
        ev.add(f"{r.run}.{r.country}.use_above_marketed_mwh", r.use_above_marketed_mwh, "MWh/a", "EXACT", "A", "W12_1_GAS_CAP_BY_COUNTRY_RUN.csv",
               "sum over generators of max(0, use - cap x marketed/gross)")
        ev.add(f"{r.run}.{r.country}.first_order_cost_lb_eur", r.first_order_cost_lb_eur, "EUR2020/a", "INFERENCE", "C", "W12_1_GAS_CAP_BY_COUNTRY_RUN.csv",
               "sum |dual| x (gross cap - marketed cap); lower bound of the cost increase (convex value function)")
    for r in b6:
        if ":" not in r["pair"]:
            ev.add(f"{r['pair']}.B6_eur", r["B6_eur"], "EUR2020", "VERIFIED", "A", "objective difference of the solved networks (no_new_xb - integrated)")
            ev.add(f"{r['pair']}.dB6_first_order_eur", r["dB6_first_order_eur"], "EUR2020", "INFERENCE", "C", "W12_1_B6_FIRST_ORDER.csv",
                   "difference of two first-order lower bounds; sign only indicative")
    cm.write_json(dict(script="scripts/w12_gas.py", unsd_ratio_marketed_over_gross=ratio, runs=run_rows), cm.EVID / "W12_1_runs.json")
    p = ev.write()
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(u[["country", "gross_tj", "marketed_tj", "gross_over_marketed", "identity_residual_tj", "cap_gross_mwh", "cap_marketed_mwh", "repo_cap_equals_gross"]].to_string())
    print(pd.DataFrame(par).groupby("network").equals_gross.all())
    print(C[["run", "country", "cap_gross_mwh", "cap_marketed_mwh", "annual_mwh", "utilisation", "binding_generators", "max_abs_dual", "use_above_marketed_mwh",
             "first_order_cost_lb_eur"]].to_string())
    print(pd.DataFrame(b6).to_string())
    print(LC[LC.run.isin(["SCR_V1", "SCR_V2", "S56_F1", "S56_F2"])].to_string())
    print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
