"""S4M supplement 01 (S4M-S1 item 3 / S4M-S2): per-component capital-cost breakdown export (read only; no model change).

For every extendable component (Generator / Link / Store / StorageUnit / Line) the cost row it was priced from (network meta research_finance.rates_by_carrier,
S4C-0 decision 90), the row's investment, FOM (% of investment per year), lifetime, discount rate, the annuity factor r / (1 - (1 + r)^-n) (PyPSA-Eur
calculate_annuity), the annualised fixed cost (annuity + FOM / 100) x investment, the component's capital_cost in the network and the ratio between the two.
A component reconstructs exactly (|ratio - 1| <= 1e-6) when its capital_cost is the plain row value; the known scalings of the S2 / S3 layers are tried next
(x efficiency, x length, x efficiency x length, x 1e3 kW -> MW); then the composite formulas of the layers, rebuilt from the cost rows and the component's
own attributes (length, underwater_fraction = corridor subsea share, efficiency, efficiency3 = captured CO2 per MWh input, capture_cost_row) or the
offshore-wind connection-distance table referenced in the network meta (research_cost_layer_s4c1.offwind_distance_table, SHA256 checked):
  * offwind-ac / -dc: offwind + <car>-station + line_length_factor x (distance x <car>-connection-submarine + landfall x <car>-connection-underground) (S4C-1)
  * AC lines, H2 / CO2 / gas pipelines: length x ((1 - s) x onshore row + s x submarine row); DC links: the same + HVDC inverter pair; zero-cost reversed twins
  * CCGT CC: CCGT fixed x CCGT efficiency + capture fixed x efficiency3; biomass EOP CC: biomass EOP fixed x efficiency + biomass CHP capture fixed x efficiency3;
    industry biomass boiler CC: solid biomass boiler steam fixed x efficiency + capture fixed x efficiency3; industry biomass CC: capture fixed x efficiency3
  * electrobiofuels: BtL fixed x BtL efficiency + BtL "C stored" x Fischer-Tropsch fixed x Fischer-Tropsch efficiency (S4B-0, PyPSA-Eur)
Every term of a composite is written to composite_terms (JSON) so the split can be re-done from the row values. Parameter-priced components (decision-89 /
95 CO2 storage prices, S3 terminals) are listed with their rule. Existing (non-extendable) assets keep their FOM constants in existing_annual_fixed_om_eur
(hook research_existing_assets) and are listed separately.

    python scripts_project/s4m_cost_breakdown.py --network <solved or unsolved nc> --costs <costs_active_research.csv> --out <dir> [--repo <repo root>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

COMPONENTS = (("Generator", "p"), ("Link", "p"), ("Store", "e"), ("StorageUnit", "p"), ("Line", "s"))
TOL = 1e-6
PIPELINE_ROWS = {"H2 pipeline": ("H2 (g) pipeline", "H2 (g) submarine pipeline"), "CO2 pipeline": ("CO2 pipeline", "CO2 submarine pipeline"),
                 "gas pipeline": ("CH4 (g) pipeline", "CH4 (g) submarine pipeline")}   # s4c_layers.PIPELINE_ROWS
# rows the layers actually priced from where research_finance.rates_by_carrier names a different (or no) row (S2 / S3 / S4C layers; checked on the S4M-1 network)
ALT_ROWS = {"Link:industry biomass boiler": "solid biomass boiler steam", "Link:industry biomass boiler CC": "solid biomass boiler steam", "Line:AC": "HVAC overhead"}
# parameter-priced components (a registered unit price, not an investment / FOM / lifetime composition): decision 89 / 95 CO2 storage service prices, S3-1 LNG
# terminal expansion cost, S3-2 H2 import terminal cost, S3-3 ammonia / methanol store prices
PARAMETER_PRICED = {"Store:co2 sequestered", "Store:co2 sequestered extra-ASEAN", "Store:ammonia store", "Store:methanol store", "Generator:LNG import", "Generator:H2 import"}
COMPOSITE_HINT = {"Generator:offwind-ac": "offwind fixed + per-node connection (offwind-ac-station + distance x offwind-ac-connection; S4C-1 decision 82)",
                  "Generator:offwind-dc": "offwind fixed + per-node connection (S4C-1 decision 82)",
                  "Generator:offwind-float": "offwind-float fixed + per-node connection (offwind-float-station + distance x offwind-float-connection; M08a A6.2)",
                  "Link:CCGT CC": "CCGT fixed + capture row x CO2 intensity x capture_fraction (S1 fragment)", "Link:biomass EOP CC": "biomass EOP fixed x efficiency + biomass CHP capture fixed x CO2 intensity x capture_fraction (S2-3)",
                  "Link:industry biomass CC": "cement capture fixed x CO2 intensity x capture_fraction (S2-5)", "Link:industry biomass boiler CC": "solid biomass boiler steam fixed x efficiency + biomass boiler capture fixed x CO2 intensity x capture_fraction (S2-5)",
                  "Link:H2 pipeline": "H2 (g) pipeline fixed x length x (1 + subsea share x factor) + compression (S2 R5 / S4C-1 subsea shares)", "Link:CO2 pipeline": "CO2 pipeline fixed x length x subsea factor (S2 R5 / S4C-1)",
                  "Link:gas pipeline": "CH4 (g) pipeline fixed x length x subsea factor (S3-1)", "Link:DC": "HVDC overhead / submarine fixed x length (+ HVDC inverter pair) (S4C-1, S4E)",
                  "Line:AC": "HVAC overhead fixed x length (+ subsea share x (HVAC submarine - overhead)) (S4C-1 decision 82, S4E subsea shares)", "Link:electrobiofuels": "electrobiofuels fixed 0 in the table; network value from the S4B-0 sector alignment"}


def annuity(r: float, n: float) -> float:
    return float(r / (1.0 - (1.0 + r) ** (-n))) if (r and n and r > 0 and n > 0) else (1.0 / n if n else np.nan)


def _fx(costs: pd.DataFrame, row: str) -> float:
    return float(costs.at[row, "fixed"]) if (row in costs.index and "fixed" in costs.columns) else np.nan


def _par(costs: pd.DataFrame, row: str, col: str) -> float:
    return float(costs.at[row, col]) if (row in costs.index and col in costs.columns) else np.nan


def _class_of(name: str) -> int:
    """Resource class of an S4A class generator: '<name> c<k>' -> k, else 0 (s4c_layers._class_of)."""
    head, _, tail = str(name).rpartition(" c")
    return int(tail) if head and tail.isdigit() else 0


def _capture_row(z, costs: pd.DataFrame, default: str) -> str:
    """The capture cost row of a CC link: the longest cost-row name the capture_cost_row attribute starts with, else the layer default."""
    v = str(z.get("capture_cost_row", "") or "") if "capture_cost_row" in z else ""
    for r in sorted((str(x) for x in costs.index), key=len, reverse=True):
        if v and v.startswith(r):
            return r
    return default


def _boiler_or_chp_capture(costs: pd.DataFrame) -> str:
    return "biomass boiler capture" if np.isfinite(_fx(costs, "biomass boiler capture")) else "biomass CHP capture"


def load_offwind_table(n, repo) -> tuple[pd.DataFrame | None, dict]:
    """The S4C-1 offshore connection-distance table referenced in the network meta, resolved under the repo and SHA256-checked."""
    info = ((n.meta.get("research_cost_layer_s4c1") or {}).get("offwind_distance_table") or {})
    if not info:
        return None, dict(status="not_referenced", reason="no research_cost_layer_s4c1.offwind_distance_table in the network meta")
    if repo is None:
        return None, dict(status="not_resolved", reason="no repo path given", file=info.get("file"))
    p = Path(repo) / str(info["file"])
    if not p.exists():
        return None, dict(status="missing", file=str(info["file"]))
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    if sha != info.get("sha256"):
        return None, dict(status="sha_mismatch", file=str(info["file"]), expected=info.get("sha256"), actual=sha)
    t = pd.read_csv(p)
    if "classes" in t:   # M08a A6.2 class table (one block per resource-class count): the block of the network
        t = t[t.classes == int((n.meta.get("research_renewable") or {}).get("resource_classes", 1))]
    t = t.set_index(["tech", "node", "cls"])
    return t, dict(status="ok", file=str(info["file"]), sha256=sha, rows=int(len(t)))


def composite(comp: str, car: str, name: str, z, cc: float, costs: pd.DataFrame, offwind) -> tuple[float, dict, str]:
    """(reconstructed value, terms, rule) of the layer formulas for the composite capital costs; (nan, {}, '') when no formula applies."""
    L = float(z.get("length", np.nan)) if "length" in z else np.nan
    s = float(z.get("underwater_fraction", 0.0) or 0.0) if "underwater_fraction" in z else 0.0
    e3 = float(z.get("efficiency3", np.nan)) if "efficiency3" in z else np.nan
    if comp == "Generator" and car in ("offwind-ac", "offwind-dc", "offwind-float"):   # offwind-float: M08a A6.2
        if offwind is None:
            return np.nan, {}, "offwind_connection_table_unavailable"
        k = (car, str(z.bus), _class_of(name))
        if k not in offwind.index:
            return np.nan, dict(node=k[1], cls=k[2]), "offwind_connection_node_class_missing"
        d = offwind.loc[k]; llf = float(d.line_length_factor); dist = float(d.average_distance_km); land = float(d.landfall_km)
        turbine = "offwind-float" if car == "offwind-float" else "offwind"
        terms = {turbine: _fx(costs, turbine), f"{car}-station": _fx(costs, f"{car}-station"),
                 f"{car}-connection-submarine x line_length_factor x distance_km": llf * dist * _fx(costs, f"{car}-connection-submarine"),
                 f"{car}-connection-underground x line_length_factor x landfall_km": llf * land * _fx(costs, f"{car}-connection-underground")}
        return float(sum(terms.values())), dict(terms, line_length_factor=llf, distance_km=dist, landfall_km=land, cls=k[2]), "offwind_connection"
    if comp == "Line" and car == "AC":
        terms = {"HVAC overhead x length x (1 - s)": L * (1 - s) * _fx(costs, "HVAC overhead"), "HVAC submarine x length x s": L * s * _fx(costs, "HVAC submarine")}
        return float(sum(terms.values())), dict(terms, length_km=L, subsea_share=s), "length_x_subsea_mix"
    if comp == "Link" and car == "DC":
        twin = str(z.get("twin_of", "") or "") if "twin_of" in z else ""
        if cc == 0.0 and (twin or str(name).endswith("-reversed")):
            return 0.0, dict(twin_of=twin or str(name)[: -len("-reversed")]), "zero_cost_reversed_twin"
        terms = {"HVDC overhead x length x (1 - s)": L * (1 - s) * _fx(costs, "HVDC overhead"), "HVDC submarine x length x s": L * s * _fx(costs, "HVDC submarine"),
                 "HVDC inverter pair": _fx(costs, "HVDC inverter pair")}
        return float(sum(terms.values())), dict(terms, length_km=L, subsea_share=s), "length_x_subsea_mix_plus_inverter_pair"
    if comp == "Link" and car in PIPELINE_ROWS:
        on, sub = PIPELINE_ROWS[car]
        terms = {f"{on} x length x (1 - s)": L * (1 - s) * _fx(costs, on), f"{sub} x length x s": L * s * _fx(costs, sub)}
        return float(sum(terms.values())), dict(terms, length_km=L, subsea_share=s), "length_x_subsea_mix"
    if comp == "Link" and car == "CCGT CC":
        cap = _capture_row(z, costs, "biomass CHP capture")
        terms = {"CCGT x CCGT efficiency": _fx(costs, "CCGT") * _par(costs, "CCGT", "efficiency"), f"{cap} x efficiency3 (t CO2 captured per MWh fuel)": _fx(costs, cap) * e3}
        return float(sum(terms.values())), dict(terms, capture_row=cap, efficiency3=e3), "base_x_efficiency_plus_capture_x_co2"
    if comp == "Link" and car == "biomass EOP CC":
        terms = {"biomass EOP x biomass EOP efficiency": _fx(costs, "biomass EOP") * _par(costs, "biomass EOP", "efficiency"), "biomass CHP capture x efficiency3": _fx(costs, "biomass CHP capture") * e3}
        return float(sum(terms.values())), dict(terms, capture_row="biomass CHP capture", efficiency3=e3), "base_x_efficiency_plus_capture_x_co2"
    if comp == "Link" and car == "industry biomass boiler CC":
        cap = _capture_row(z, costs, _boiler_or_chp_capture(costs)); eff = float(z.get("efficiency", np.nan))
        terms = {"solid biomass boiler steam x efficiency": _fx(costs, "solid biomass boiler steam") * eff, f"{cap} x efficiency3": _fx(costs, cap) * e3}
        return float(sum(terms.values())), dict(terms, capture_row=cap, efficiency=eff, efficiency3=e3), "base_x_efficiency_plus_capture_x_co2"
    if comp == "Link" and car == "industry direct firing biomass CC":   # M08b B2: high-band biomass with capture, same rule as the boiler CC
        cap = _capture_row(z, costs, _boiler_or_chp_capture(costs)); eff = float(z.get("efficiency", np.nan))
        terms = {"direct firing solid fuels x efficiency": _fx(costs, "direct firing solid fuels") * eff, f"{cap} x efficiency3": _fx(costs, cap) * e3}
        return float(sum(terms.values())), dict(terms, capture_row=cap, efficiency=eff, efficiency3=e3), "base_x_efficiency_plus_capture_x_co2"
    if comp == "Link" and car == "industry biomass CC":
        cap = _boiler_or_chp_capture(costs)
        terms = {f"{cap} x efficiency3": _fx(costs, cap) * e3}
        return float(sum(terms.values())), dict(terms, capture_row=cap, efficiency3=e3), "capture_x_co2"
    if comp == "Link" and car == "electrobiofuels":
        terms = {"BtL x BtL efficiency": _fx(costs, "BtL") * _par(costs, "BtL", "efficiency"),
                 "BtL C stored x Fischer-Tropsch x Fischer-Tropsch efficiency": _par(costs, "BtL", "C stored") * _fx(costs, "Fischer-Tropsch") * _par(costs, "Fischer-Tropsch", "efficiency")}
        return float(sum(terms.values())), dict(terms), "btl_plus_scaled_fischer_tropsch"
    return np.nan, {}, ""


def breakdown(n, costs: pd.DataFrame, repo=None) -> tuple[pd.DataFrame, dict]:
    rb = (n.meta.get("research_finance") or {}).get("rates_by_carrier") or {}
    uniform = (n.meta.get("research_finance") or {}).get("uniform_rate") or (n.meta.get("research_finance") or {}).get("rate")
    offwind, offwind_info = load_offwind_table(n, repo)
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
            cc = float(z.capital_cost); hit = ""; fixed = np.nan
            if row and row in costs.index:
                c = costs.loc[row]
                inv, fom, life = float(c.get("investment", np.nan)), float(c.get("FOM", np.nan)), float(c.get("lifetime", np.nan))
                rr = float(r) if r is not None else float(c.get("discount rate", np.nan))
                ann = annuity(rr, life); fixed = (ann + (0.0 if np.isnan(fom) else fom / 100.0)) * inv if np.isfinite(inv) else np.nan
                rec.update(investment=inv, fom_pct=fom, lifetime_row=life, annuity_factor=ann, fixed_reconstructed=fixed, fixed_table=float(c.get("fixed", np.nan)),
                           table_fixed_consistent=(abs(fixed / float(c["fixed"]) - 1.0) <= TOL) if (np.isfinite(fixed) and float(c.get("fixed", 0) or 0) != 0) else None)
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
                    hits = [k for k, f in cands.items() if abs(ratio / f - 1.0) <= TOL]
                    hit = hits[0] if hits else ""
                    rec.update(scaling_implied=ratio, ratio_per_km=((ratio / L) if (np.isfinite(L) and L > 0) else np.nan))
            else:
                rec["note"] = "no cost row in research_finance.rates_by_carrier (import generator / parameter-priced store)" if not row else f"cost row {row} not in the table"
            if not hit:   # the layer composites (offshore connection, subsea mix, capture variants, electrobiofuels, reversed twins)
                val, terms, rule = composite(comp, car, name, z, cc, costs, offwind)
                if rule:
                    rec.update(composite_rule=rule, composite_terms=json.dumps(terms, default=float), composite_reconstructed=val)
                    if (np.isfinite(val) and val != 0 and abs(cc / val - 1.0) <= TOL) or (val == 0.0 and cc == 0.0):
                        hit = "composite:" + rule
            if not hit and cc == 0.0:
                hit = "zero" if (row and row in costs.index) else "zero_cost_no_row"
            rec.update(match=bool(hit), match_rule=hit, residual_eur=(0.0 if hit else (cc - (fixed if np.isfinite(fixed) else 0.0))))
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
                composite_rules=({k: int(v) for k, v in T[T.match_rule.fillna("").str.startswith("composite:")].composite_rule.value_counts().items()} if ("composite_rule" in T and len(T)) else {}),
                offwind_distance_table=offwind_info, tolerance=TOL,
                existing_assets_fom=fix, discount_rate_mode=(n.meta.get("research_finance") or {}).get("mode"), uniform_rate=uniform)
    return T, summ


def write_breakdown(n, costs: pd.DataFrame, out: Path, repo=None) -> dict:
    """COMPONENT_COST_BREAKDOWN.csv + _SUMMARY.json under out; EXPORTS.json / SOLVE_RECEIPT.json there are updated when present (bytes, SHA256)."""
    T, summ = breakdown(n, costs, repo=repo)
    T.to_csv(out / "COMPONENT_COST_BREAKDOWN.csv", index=False, float_format="%.10g")
    (out / "COMPONENT_COST_BREAKDOWN_SUMMARY.json").write_text(json.dumps(summ, indent=1, default=str))
    if (out / "EXPORTS.json").exists():
        ex = json.loads((out / "EXPORTS.json").read_text())
        for f in ("COMPONENT_COST_BREAKDOWN.csv", "COMPONENT_COST_BREAKDOWN_SUMMARY.json"):
            ex[f] = dict(bytes=(out / f).stat().st_size, sha256=hashlib.sha256((out / f).read_bytes()).hexdigest())
        (out / "EXPORTS.json").write_text(json.dumps(ex, indent=2))
        if (out / "SOLVE_RECEIPT.json").exists():
            rec = json.loads((out / "SOLVE_RECEIPT.json").read_text()); rec["exports"] = ex; rec["cost_breakdown"] = summ
            (out / "SOLVE_RECEIPT.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False, default=str) + "\n")
    return summ


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--costs", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent, help="repo root for the offshore connection-distance table referenced in the network meta")
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    import pypsa
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    n = pypsa.Network(str(a.network)); costs = pd.read_csv(a.costs, index_col=0)
    summ = write_breakdown(n, costs, a.out, repo=a.repo)
    print(json.dumps(summ, indent=1, default=str))


if __name__ == "__main__":
    main()
