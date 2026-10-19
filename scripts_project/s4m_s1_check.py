"""S4M supplement 01 - S4M-S1 checklist on one solve folder (read only, no solve): duals (bus balances, GlobalConstraints, capacity bounds, research
constraints; assign_all_duals equivalence), hourly flows with country attribution, cost breakdown, full network reload with the B16 identity recomputed
from the exported network. Writes S4M_S1_CHECKLIST.json with 'saved' / 'missing' / 'partial' per item and the evidence behind it.

    python scripts_project/s4m_s1_check.py --solve <solve dir> --out <json> [--costs <costs_active_research.csv>]
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

BOUND_PATTERNS = ("Generator-ext-p_nom-upper", "Generator-ext-p_nom-lower", "Link-ext-p_nom-upper", "Link-ext-p_nom-lower", "Store-ext-e_nom-upper", "Store-ext-e_nom-lower",
                  "StorageUnit-ext-p_nom-upper", "StorageUnit-ext-p_nom-lower", "Line-ext-s_nom-upper", "Line-ext-s_nom-lower")


def jl(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else {}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--solve", type=Path, required=True); ap.add_argument("--out", type=Path, required=True); ap.add_argument("--costs", type=Path, default=None)
    a = ap.parse_args()
    import pypsa, xarray as xr
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    rec = jl(a.solve / "SOLVE_RECEIPT.json"); nc = next(iter(a.solve.glob("*_solved.nc")), None)
    res = dict(solve=str(a.solve), network_file=(nc.name if nc else None), receipt_objective=rec.get("objective"), termination=rec.get("termination_condition"), items={})
    if nc is None:
        res["items"]["4_network"] = dict(status="missing", reason="no *_solved.nc in the solve folder"); a.out.write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1)); return
    n = pypsa.Network(str(nc))
    # ---- 1a bus balance duals
    mp = n.buses_t.marginal_price; miss = [b for b in n.buses.index if b not in mp.columns]
    nan_cols = int(mp.isna().any().sum()) if len(mp.columns) else len(n.buses)
    res["items"]["1a_bus_balance_duals"] = dict(status=("saved" if (not miss and nan_cols == 0) else "partial"), where="network buses_t.marginal_price", buses=int(len(n.buses)), columns=int(mp.shape[1]),
                                                 buses_without_column=len(miss), columns_with_nan=nan_cols, by_carrier=({str(k): int(v) for k, v in n.buses.carrier[mp.columns].value_counts().items()} if len(mp.columns) else {}))
    # ---- 1b GlobalConstraint duals
    gc = n.global_constraints
    duals_nc = a.solve / "DUALS_BY_CONSTRAINT.nc"; D = xr.open_dataset(duals_nc) if duals_nc.exists() else None
    names = list(D.data_vars) if D is not None else []
    co2 = [k for k in names if k.startswith("research_country_co2_limit") or k.startswith("research_gap_co2_limit")]
    if len(gc):
        res["items"]["1b_global_constraint_duals"] = dict(status=("saved" if gc.mu.notna().all() else "partial"), where="network global_constraints.mu", count=int(len(gc)), nan=int(gc.mu.isna().sum()))
    else:
        res["items"]["1b_global_constraint_duals"] = dict(status=("saved" if co2 else "missing"), where=("DUALS_BY_CONSTRAINT.nc (research hooks)" if co2 else "none"),
                                                           note="the model has no GlobalConstraint: the per-country CO2 / net-zero caps are the research hook constraints research_country_co2_limit-<c> (country_carbon.py)",
                                                           research_co2_constraints=co2, values=({k: float(D[k].values) for k in co2} if co2 and D is not None else {}))
    # ---- 1c capacity-bound duals
    bounds = {k: dict(size=int(D[k].size), nan=int(np.isnan(D[k].values).sum())) for k in names if k in BOUND_PATTERNS} if D is not None else {}
    mu_cols = {c: [k for k in n.df(c).columns if k.startswith("mu_")] for c in ("Generator", "Link", "Store", "StorageUnit", "Line")}
    mu_t = {c: [k for k, v in n.pnl(c).items() if k.startswith("mu_") and len(v.columns)] for c in ("Generator", "Link", "Store", "StorageUnit", "Line")}
    res["items"]["1c_capacity_bound_duals"] = dict(status=("saved" if (bounds and all(k in bounds for k in ("Generator-ext-p_nom-upper", "Link-ext-p_nom-upper", "Line-ext-s_nom-upper"))) else ("partial" if (bounds or any(mu_t.values())) else "missing")),
                                                    where=("DUALS_BY_CONSTRAINT.nc (static p_nom / s_nom / e_nom bounds, incl. lines.max_extension via s_nom_max) + network mu_* series (operational bounds)" if D is not None else "raw solution/Pi.npy only (not exported to the cloud results)"),
                                                    bound_constraints_in_dual_file=bounds, network_static_mu_columns=mu_cols, network_time_mu_columns=mu_t,
                                                    note="PyPSA assign_duals maps only snapshot-indexed duals (mu_upper / mu_lower per snapshot) and GlobalConstraints; the static capacity-bound duals (scarcity rents) exist only in the dual file")
    # ---- 1d research constraint duals
    research = {k: dict(size=int(D[k].size), nan=int(np.isnan(D[k].values).sum()), dims=list(D[k].dims)) for k in names if k.lower().startswith("research") or "loss_proxy" in k or "loss_upper" in k} if D is not None else {}
    res["items"]["1d_research_constraint_duals"] = dict(status=("saved" if research else "missing"), where=("DUALS_BY_CONSTRAINT.nc" if research else "raw solution/Pi.npy only"), constraints=research,
                                                         all_constraints_in_dual_file=len(names), receipt_assign_all_duals=(rec.get("duals") or {}).get("assign_all_duals"),
                                                         receipt_dual_export=(rec.get("exports") or {}).get("DUALS_BY_CONSTRAINT.nc"))
    # ---- 2 hourly flows
    flows = dict(lines=[k for k, v in n.lines_t.items() if len(v.columns)], links=[k for k, v in n.links_t.items() if len(v.columns)], storage_units=[k for k, v in n.storage_units_t.items() if len(v.columns)],
                 stores=[k for k, v in n.stores_t.items() if len(v.columns)])
    cty = n.buses.country.astype(str); bad_bus = int((~cty.isin(list(set(cty)) )).sum())
    xb = n.links[n.links.border_class == "cross_border"] if "border_class" in n.links else n.links.iloc[0:0]
    xb_ok = bool(all(cty[z.bus0] != cty[z.bus1] for _, z in xb.iterrows())) if len(xb) else True
    res["items"]["2_hourly_flows"] = dict(status=("saved" if (("p0" in flows["lines"] and "p1" in flows["lines"]) and ("p0" in flows["links"] and "p1" in flows["links"]) and ("p" in flows["storage_units"] and "state_of_charge" in flows["storage_units"]) and ("p" in flows["stores"] and "e" in flows["stores"])) else "partial"),
                                          where="network *_t tables", series=flows, country_attribution=dict(buses_with_country=int((cty != "").sum()), buses=int(len(n.buses)), cross_border_links=int(len(xb)), cross_border_two_countries=xb_ok,
                                                                                                           cross_border_lines=int((n.lines.border_class == "cross_border").sum()) if "border_class" in n.lines else None))
    # ---- 3 cost breakdown
    bd = a.solve / "COMPONENT_COST_BREAKDOWN_SUMMARY.json"; bs = jl(bd)
    if not bs and a.costs is not None:
        from s4m_cost_breakdown import breakdown
        T, bs = breakdown(n, pd.read_csv(a.costs, index_col=0)); T.to_csv(a.solve / "COMPONENT_COST_BREAKDOWN.csv", index=False, float_format="%.10g"); bd.write_text(json.dumps(bs, indent=1, default=str))
    res["items"]["3_cost_breakdown"] = dict(status=("saved" if (bs and bs.get("matched_share") == 1.0) else ("partial" if bs else "missing")),
                                             where=("COMPONENT_COST_BREAKDOWN.csv + costs_active_research.csv" if bs else "none (capital_cost only in the network; the costs table is a build artefact)"),
                                             summary=({k: v for k, v in bs.items() if k not in ("existing_assets_fom",)} if bs else None), existing_assets_fom=(bs.get("existing_assets_fom") if bs else None))
    # ---- 4 full network, reload, B16 recompute
    try:
        from s4d_ledger import country_cost_ledger, ledger_gate, load_length_shares
        rows, ident, diag = country_cost_ledger(n, load_length_shares())
        g = ledger_gate(ident)
        b16 = dict(passed=g["passed"], relative_error=g["relative_error"], objective_network=float(n.objective), objective_receipt=rec.get("objective"),
                   objective_match=(abs(float(n.objective) / rec["objective"] - 1.0) <= 1e-12) if rec.get("objective") else None)
    except Exception as e:
        b16 = dict(error=str(e)[:300])
    nan_audit = {}
    for c in ("Generator", "Link", "Store", "StorageUnit", "Line"):
        for k, v in n.pnl(c).items():
            if k.startswith("mu_") and len(v.columns):
                nan_audit[f"{c}_t.{k}"] = dict(columns=int(v.shape[1]), all_nan=int(v.isna().all().sum()), any_nan=int(v.isna().any().sum()))
    res["items"]["4_full_network"] = dict(status=("saved" if (b16.get("passed") and b16.get("objective_match")) else "partial"), where=nc.name, reload="ok", b16_recomputed=b16, mu_nan_audit=nan_audit,
                                           note="mu_* columns exist only for the component subset of each constraint (extendable vs fixed); other entries are NaN by construction")
    res["summary"] = {k: v["status"] for k, v in res["items"].items()}
    a.out.write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res["summary"], indent=1)); print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ("status", "where", "note")} for k, v in res["items"].items()}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
