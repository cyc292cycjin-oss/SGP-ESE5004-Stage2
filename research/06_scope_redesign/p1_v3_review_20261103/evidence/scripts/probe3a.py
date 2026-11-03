"""Independent review probe 3a: solved screening results (light export): gates, precision, Owen dual form, benefit, capacities, emissions, flows."""
import json, glob
import pandas as pd, numpy as np
C = "/home/jin/v3rev/cloud/export"
OUT = "/home/jin/v3rev/out/probe3a.json"
R = {}
def J(p):
    return json.load(open(p))
for run in ("V1", "V2", "V3", "V4", "V5"):
    d = f"{C}/{run}"; z = {}
    rec = J(f"{d}/SOLVE_RECEIPT.json")
    z["receipt"] = {k: rec.get(k) for k in ("termination_condition", "objective", "solver_profile", "scenario", "truncated_to", "snapshots", "iterations", "solve_seconds", "lp", "duals", "input_network")}
    z["receipt_keys"] = sorted(rec.keys())
    P = J(f"{d}/PRECISION.json")
    z["precision"] = {k: P.get(k) for k in ("grade", "termination", "acceptance", "reference")}
    z["precision_a"] = (P.get("a_objective") or P.get("a") or {})
    z["precision_keys"] = sorted(P.keys())
    G = J(f"{d}/V5_GATES.json")
    z["gates_keys"] = sorted(G.keys())[:40]
    gates = G.get("gates") or G
    failed = []
    for k, v in (gates.items() if isinstance(gates, dict) else []):
        if isinstance(v, dict) and v.get("passed") is False:
            failed.append(k)
    z["gates_failed"] = failed
    for k in ("B1", "B6", "B8", "B13", "B16", "B5", "B1_BUNKERS"):
        for kk, v in (gates.items() if isinstance(gates, dict) else []):
            if kk.startswith(k) and isinstance(v, dict):
                z[f"gate_{kk}"] = {a: v.get(a) for a in ("passed", "difference", "relative", "max_rel_dev", "worst", "final_level_tco2", "by_country", "relative_error")}
    A6 = J(f"{d}/V6_ACCEPTANCE.json")
    z["v6"] = {k: A6.get(k) for k in ("label", "g1", "g2", "diagnostics_failed", "d2", "note")}
    z["v6_keys"] = sorted(A6.keys())[:40]
    A = J(f"{d}/ALLOCATION.json")
    z["alloc_market"] = {k: v / 1e9 for k, v in A["allocation_eur"]["0.5"].items()}
    z["alloc_identity"] = A["identity"]
    ow = f"{d}/m12_owen/OWEN.json"
    if glob.glob(ow):
        O = J(ow)
        z["owen"] = dict(alloc={k: v / 1e9 for k, v in O["allocation_eur"]["0.5"].items()}, identity=O["identity"], premise=O["premise"].get("passed"), premise_rows=O["premise"].get("nonzero_rhs_rows_by_class"),
                         coupling_nonhom=O["premise"].get("coupling_families_nonhomogeneous"), shared_rows=[(r.get("constraint"), r.get("rows"), r.get("rhs_sum"), r.get("owners")) for r in O["premise"].get("shared_or_unresolved_rows", [])][:10],
                         usable=O.get("usable_for_allocation"), dual_acc=O.get("dual_acceptance"), mmd=(O.get("market_minus_dual") or {}).get("total_eur"), kvl=(O.get("market_minus_dual") or {}).get("kvl_loop_transfer_eur"), resid=(O.get("market_minus_dual") or {}).get("residual_eur"),
                         method=(O.get("market_minus_dual") or {}).get("method"), interval={k: (v["min"] / 1e9, v["max"] / 1e9) for k, v in O["interval_eur"].items()}, pair_values={k: v / 1e9 for k, v in sorted(O["pair_values_eur"].items(), key=lambda kv: -abs(kv[1]))[:12]},
                         bunker_standalone={k: v for k, v in (O.get("bunker_standalone") or {}).items() if k in ("strict_standalone_cost_eur", "owen_dual_alpha_half_eur", "passed", "notes")})
    for f in ("EMISSIONS_BY_COUNTRY.json", "CO2_FLOWS.json", "BUNKER_ACCOUNT.json", "LEDGER_IDENTITY.json", "INTERIOR_CHECKS.json", "kkt_summary.json"):
        try:
            X = J(f"{d}/{f}"); s = json.dumps(X, default=str)
            z[f] = X if len(s) < 6000 else {k: (v if len(json.dumps(v, default=str)) < 1500 else "...") for k, v in X.items()}
        except Exception as e:
            z[f] = f"ERR {e}"
    cap = J(f"{d}/CAPACITY_BY_TECH_COUNTRY.json")
    z["capacity_keys"] = list(cap.keys())[:20] if isinstance(cap, dict) else type(cap).__name__
    z["capacity_sample"] = json.dumps(cap, default=str)[:3000]
    try:
        xb = pd.read_csv(f"{d}/cross_border_flows.csv")
    except Exception as e:
        xb = pd.DataFrame(); z["xb_flows_err"] = str(e)
    z["xb_flows_columns"] = list(xb.columns); z["xb_flows_head"] = xb.head(3).astype(str).to_dict("records")
    try:
        la = xb[xb.astype(str).apply(lambda r: r.str.contains("LA").any(), axis=1)]
        z["xb_flows_LA"] = la.astype(str).to_dict("records")[:40]
    except Exception as e:
        z["xb_flows_LA"] = str(e)
    try:
        npz = pd.read_csv(f"{d}/NODAL_PRICES.csv")
    except Exception as e:
        npz = pd.DataFrame(); z["nodal_err"] = str(e)
    z["nodal_prices_columns"] = list(npz.columns)[:12]
    el = npz[npz.carrier == "AC"] if "carrier" in npz else npz
    if "country" in el and "mean" in el:
        z["elec_price_mean_by_country"] = {k: float(v) for k, v in el.groupby("country")["mean"].mean().round(2).items()}
        z["elec_price_minmax_by_country"] = {k: [float(g["min"].min()), float(g["max"].max())] for k, g in el.groupby("country")}
    for car in ("methanol", "ammonia", "oil non-fossil", "H2", "oil"):
        q = npz[npz.carrier == car] if "carrier" in npz else npz.iloc[:0]
        if len(q) and "mean" in q:
            z[f"price_{car}_by_country"] = {k: float(v) for k, v in q.groupby("country")["mean"].mean().round(2).items()}
    try:
        ccb = pd.read_csv(f"{d}/COUNTRY_COST_LEDGER.csv")
    except Exception as e:
        ccb = pd.DataFrame(); z["ledger_err"] = str(e)
    z["ledger_columns"] = list(ccb.columns)
    z["ledger_table"] = ccb.round(0).astype(str).to_dict("records")[:16]
    R[run] = z
B = J(f"{C}/batch/M12_BENEFIT/BENEFIT.json")
R["benefit"] = dict(b6=B["b6_eur"] / 1e9, main_form=B["main_form"], owen_benefit={k: v / 1e9 for k, v in B["owen"]["benefit_eur"].items()}, interval={k: (v["min"] / 1e9, v["max"] / 1e9) for k, v in B["owen"]["benefit_interval_eur"].items()},
                    market_benefit={k: v / 1e9 for k, v in B["market_form"]["benefit_eur"].items()}, negative=B["owen"]["negative_benefit"], neg_interval=B["owen"]["negative_somewhere_in_interval"], bunker=B["bunker"], owen_checks_ir={k: v["passed"] for k, v in B["owen_checks"]["ir"].items()}, usable=B["owen"]["usable"])
R["batch_summary"] = J(f"{C}/batch/DFX_SUMMARY.json")
for f in ("LA_EXPORT_UTILISATION.csv", "ID_LEDGER_DECOMPOSITION.csv"):
    try:
        R[f] = pd.read_csv(f"{C}/batch/{f}").astype(str).to_dict("records")
    except Exception as e:
        R[f] = str(e)
R["VN_BIOMASS_BALANCE"] = J(f"{C}/batch/VN_BIOMASS_BALANCE.json")
for f in glob.glob("/home/jin/v3rev/cloud/analysis/*.json"):
    X = J(f); s = json.dumps(X, default=str); R["analysis/" + f.split("/")[-1]] = X if len(s) < 12000 else {k: (v if len(json.dumps(v, default=str)) < 2500 else "...") for k, v in X.items()}
for f in glob.glob("/home/jin/v3rev/cloud/analysis/*.csv"):
    try:
        R["analysis/" + f.split("/")[-1]] = pd.read_csv(f).astype(str).to_dict("records")[:60]
    except Exception as e:
        R["analysis/" + f.split("/")[-1]] = str(e)
json.dump(R, open(OUT, "w"), indent=1, default=str)
print("done")
