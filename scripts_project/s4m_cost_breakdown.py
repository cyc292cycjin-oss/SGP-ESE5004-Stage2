"""S4M supplement 01 (S4M-S1 item 3 / S4M-S2): per-component capital-cost breakdown export (read only; no model change).

For every extendable component (Generator / Link / Store / StorageUnit / Line) the cost row it was priced from (network meta research_finance.rates_by_carrier,
S4C-0 decision 90), the row's investment, FOM (% of investment per year), lifetime, discount rate, the annuity factor r / (1 - (1 + r)^-n) (PyPSA-Eur
calculate_annuity), the annualised fixed cost (annuity + FOM / 100) x investment, the component's capital_cost in the network and the ratio between the two.
A component reconstructs exactly (|ratio - 1| <= 1e-6) when its capital_cost is the plain row value; the known scalings of the S2 / S3 layers are tried next
(x efficiency, x length, x efficiency x length, x 1e3 kW -> MW); composite costs (e.g. capture variants, offshore connection cost per node, the decision-89 /
95 CO2 storage prices, decision-96 corridor costs) are reported with the ratio and the formula hint, not forced. Existing (non-extendable) assets keep their
FOM constants in existing_annual_fixed_om_eur (hook research_existing_assets) and are listed separately.

    python scripts_project/s4m_cost_breakdown.py --network <solved or unsolved nc> --costs <costs_active_research.csv> --out <dir>
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

COMPONENTS = (("Generator", "p"), ("Link", "p"), ("Store", "e"), ("StorageUnit", "p"), ("Line", "s"))
TOL = 1e-6
# rows the layers actually priced from where research_finance.rates_by_carrier names a different (or no) row (S2 / S3 / S4C layers; checked on the S4M-1 network)
ALT_ROWS = {"Link:industry biomass boiler": "solid biomass boiler steam", "Link:industry biomass boiler CC": "solid biomass boiler steam", "Line:AC": "HVAC overhead"}
# parameter-priced components (a registered unit price, not an investment / FOM / lifetime composition): decision 89 / 95 CO2 storage service prices, S3-1 LNG
# terminal expansion cost, S3-2 H2 import terminal cost, S3-3 ammonia / methanol store prices
PARAMETER_PRICED = {"Store:co2 sequestered", "Store:co2 sequestered extra-ASEAN", "Store:ammonia store", "Store:methanol store", "Generator:LNG import", "Generator:H2 import"}
COMPOSITE_HINT = {"Generator:offwind-ac": "offwind fixed + per-node connection (offwind-ac-station + distance x offwind-ac-connection; S4C-1 decision 82)",
                  "Generator:offwind-dc": "offwind fixed + per-node connection (S4C-1 decision 82)",
                  "Link:CCGT CC": "CCGT fixed + capture row x CO2 intensity x capture_fraction (S1 fragment)", "Link:biomass EOP CC": "biomass EOP fixed x efficiency + biomass CHP capture fixed x CO2 intensity x capture_fraction (S2-3)",
                  "Link:industry biomass CC": "cement capture fixed x CO2 intensity x capture_fraction (S2-5)", "Link:industry biomass boiler CC": "solid biomass boiler steam fixed x efficiency + biomass boiler capture fixed x CO2 intensity x capture_fraction (S2-5)",
                  "Link:H2 pipeline": "H2 (g) pipeline fixed x length x (1 + subsea share x factor) + compression (S2 R5 / S4C-1 subsea shares)", "Link:CO2 pipeline": "CO2 pipeline fixed x length x subsea factor (S2 R5 / S4C-1)",
                  "Link:gas pipeline": "CH4 (g) pipeline fixed x length x subsea factor (S3-1)", "Link:DC": "HVDC overhead / submarine fixed x length (+ HVDC inverter pair) (S4C-1, S4E)",
                  "Line:AC": "HVAC overhead fixed x length (+ subsea share x (HVAC submarine - overhead)) (S4C-1 decision 82, S4E subsea shares)", "Link:electrobiofuels": "electrobiofuels fixed 0 in the table; network value from the S4B-0 sector alignment"}


def annuity(r: float, n: float) -> float:
    return float(r / (1.0 - (1.0 + r) ** (-n))) if (r and n and r > 0 and n > 0) else (1.0 / n if n else np.nan)


def breakdown(n, costs: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rb = (n.meta.get("research_finance") or {}).get("rates_by_carrier") or {}
    uniform = (n.meta.get("research_finance") or {}).get("uniform_rate") or (n.meta.get("research_finance") or {}).get("rate")
    rows = []
    for comp, nom in COMPONENTS:
        d = n.df(comp)
        if not len(d):
            continue
        ext = d[d[f"{nom}_nom_extendable"].astype(bool)] if f"{nom}_nom_extendable" in d else d.iloc[0:0]
        for name, z in ext.iterrows():
            car = str(z.carrier); key = f"{comp}:{car}"; entry = rb.get(key) or {}
            row = ALT_ROWS.get(key) or entry.get("cost_row"); r = entry.get("discount_rate") or uniform or 0.07
            rec = dict(component=comp, name=name, carrier=car, country=str(z.get("country", "")), cost_row=row, cost_row_source=("layer formula" if key in ALT_ROWS else "research_finance.rates_by_carrier"),
                       discount_rate=r, capital_cost=float(z.capital_cost), lifetime_component=float(z.get("lifetime", np.nan)) if "lifetime" in z else np.nan, extendable=True, nom_max=float(z.get(f"{nom}_nom_max", np.nan)),
                       composite_hint=COMPOSITE_HINT.get(key, ""))
            if key in PARAMETER_PRICED:
                rec.update(match=True, match_rule="parameter_price", note="registered unit price (EUR per unit-year), no investment / FOM / lifetime composition - see DATA_REGISTRY (decisions 89, 95; S3-1 LNG terminal; S3-2 H2 import)")
                rows.append(rec); continue
            if row and row in costs.index:
                c = costs.loc[row]
                inv, fom, life = float(c.get("investment", np.nan)), float(c.get("FOM", np.nan)), float(c.get("lifetime", np.nan))
                rr = float(r) if r is not None else float(c.get("discount rate", np.nan))
                ann = annuity(rr, life); fixed = (ann + (0.0 if np.isnan(fom) else fom / 100.0)) * inv if np.isfinite(inv) else np.nan
                rec.update(investment=inv, fom_pct=fom, lifetime_row=life, annuity_factor=ann, fixed_reconstructed=fixed, fixed_table=float(c.get("fixed", np.nan)),
                           table_fixed_consistent=(abs(fixed / float(c["fixed"]) - 1.0) <= TOL) if (np.isfinite(fixed) and float(c.get("fixed", 0) or 0) != 0) else None)
                cc = float(z.capital_cost)
                if np.isfinite(fixed) and fixed != 0:
                    ratio = cc / fixed; rec["ratio_capital_cost_over_fixed"] = ratio
                    cands = dict(plain=1.0)
                    L = float(z.get("length", np.nan)) if "length" in z else np.nan
                    if comp == "Link":
                        e = float(z.get("efficiency", np.nan))
                        if np.isfinite(e) and e > 0:
                            cands["efficiency"] = e; cands["inverse_efficiency"] = 1.0 / e
                        if np.isfinite(L) and L > 0:
                            cands["length"] = L
                            if np.isfinite(e) and e > 0:
                                cands["efficiency_x_length"] = e * L
                    if comp == "Line" and np.isfinite(L) and L > 0:
                        cands["length"] = L
                    cands["x1000"] = 1000.0
                    hit = [k for k, f in cands.items() if abs(ratio / f - 1.0) <= TOL]
                    rec.update(match=bool(hit), match_rule=(hit[0] if hit else ""), scaling_implied=ratio, residual_eur=(cc - fixed if not hit else 0.0),
                               ratio_per_km=((ratio / L) if (np.isfinite(L) and L > 0) else np.nan))
                else:
                    rec.update(match=(cc == 0.0), match_rule=("zero" if cc == 0.0 else ""))
            else:
                rec.update(match=(float(z.capital_cost) == 0.0), match_rule=("zero_cost_no_row" if float(z.capital_cost) == 0.0 else ""),
                           note=("no cost row in research_finance.rates_by_carrier (import generator / parameter-priced store)" if not row else f"cost row {row} not in the table"))
            rows.append(rec)
    T = pd.DataFrame(rows)
    fix = {}
    for comp, nom in COMPONENTS:
        d = n.df(comp)
        if len(d) and "existing_annual_fixed_om_eur" in d:
            fx = d[~d[f"{nom}_nom_extendable"].astype(bool)] if f"{nom}_nom_extendable" in d else d
            fix[comp] = dict(components=int(len(fx)), with_fom_constant=int((pd.to_numeric(fx.existing_annual_fixed_om_eur, errors="coerce").fillna(0) > 0).sum()),
                             fom_eur_total=float(pd.to_numeric(fx.existing_annual_fixed_om_eur, errors="coerce").fillna(0).sum()))
    summ = dict(extendable=int(len(T)), matched=int(T.match.fillna(False).sum()) if len(T) else 0,
                matched_share=(float(T.match.fillna(False).mean()) if len(T) else None),
                by_rule=({k: int(v) for k, v in T.match_rule.fillna("").value_counts().items()} if len(T) else {}),
                unmatched_by_carrier=({f"{k[0]}:{k[1]}": int(v) for k, v in T[~T.match.fillna(False)].groupby(["component", "carrier"]).size().items()} if len(T) else {}),
                no_cost_row_by_carrier=({f"{k[0]}:{k[1]}": int(v) for k, v in T[T.cost_row.isna()].groupby(["component", "carrier"]).size().items()} if len(T) else {}),
                table_fixed_inconsistent=int((T.table_fixed_consistent == False).sum()) if "table_fixed_consistent" in T else 0,   # noqa: E712
                existing_assets_fom=fix, discount_rate_mode=(n.meta.get("research_finance") or {}).get("mode"), uniform_rate=uniform)
    return T, summ


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--costs", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    import pypsa
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    n = pypsa.Network(str(a.network)); costs = pd.read_csv(a.costs, index_col=0)
    T, summ = breakdown(n, costs)
    T.to_csv(a.out / "COMPONENT_COST_BREAKDOWN.csv", index=False, float_format="%.10g")
    (a.out / "COMPONENT_COST_BREAKDOWN_SUMMARY.json").write_text(json.dumps(summ, indent=1, default=str))
    print(json.dumps(summ, indent=1, default=str))


if __name__ == "__main__":
    main()
