"""M10R B1 (read-only): cross-border stock lines / links vs the existing_cross_border_fom_ledger meta of a network file.
Usage: python inspect_xb.py <network.nc> [<network.nc> ...]   (no solve; prints JSON per file)"""
import json
import sys
import warnings

warnings.filterwarnings("ignore")
import pandas as pd
import pypsa


def info(path):
    n = pypsa.Network(path)
    out = dict(file=path, scenario=n.meta.get("scenario"), snapshots=len(n.snapshots))
    led = pd.DataFrame(n.meta.get("existing_cross_border_fom_ledger", []))
    out["fom_eur_meta"] = n.meta.get("existing_cross_border_fom_eur")
    out["ledger_rows"] = int(len(led))
    out["ledger_fom_sum"] = float(led.annual_fom_eur.sum()) if len(led) else 0.0
    out["ledger_zero_capacity_rows"] = int((led.capacity_2025_mw <= 0).sum()) if len(led) else 0
    xl = n.lines[n.lines.border_class == "cross_border"] if "border_class" in n.lines else n.lines.iloc[0:0]
    xk = n.links[n.links.border_class == "cross_border"] if "border_class" in n.links else n.links.iloc[0:0]
    out["xb_lines"] = int(len(xl)); out["xb_links"] = int(len(xk))
    out["xb_lines_s_nom_min_zero"] = int((xl.s_nom_min <= 0).sum())
    missing = []
    for _, r in led.iterrows():
        df = n.df(r.component_type)
        if str(r.component) not in df.index:
            missing.append(dict(component_type=r.component_type, component=str(r.component), capacity_2025_mw=float(r.capacity_2025_mw), annual_fom_eur=float(r.annual_fom_eur)))
    out["ledger_components_missing_from_network"] = missing
    cols = [c for c in ("bus0", "bus1", "s_nom", "s_nom_min", "s_nom_max", "s_nom_extendable", "border_class", "length", "carrier", "capital_cost") if c in n.lines]
    if "59" in n.lines.index:
        z = n.lines.loc["59", cols].to_dict()
        z["country0"] = str(n.buses.at[z["bus0"], "country"]); z["country1"] = str(n.buses.at[z["bus1"], "country"])
        out["line_59"] = {k: (float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else (bool(v) if isinstance(v, bool) else str(v))) for k, v in z.items()}
    else:
        out["line_59"] = "absent"
    row59 = led[led.component.astype(str) == "59"] if len(led) else led
    out["ledger_row_59"] = row59.to_dict("records")
    xl_by_cap = xl.assign(zero=(xl.s_nom_min <= 0))
    out["xb_lines_zero_capacity_names"] = [str(x) for x in xl_by_cap.index[xl_by_cap.zero]][:40]
    v = n.meta.get("research_variant") or {}
    out["variant_sets"] = v.get("sets"); out["variant_stock_mode"] = ((v.get("ledgers") or {}).get("stock_mode") or {})
    if isinstance(out["variant_stock_mode"], dict):
        out["variant_stock_mode"] = {k: val for k, val in out["variant_stock_mode"].items() if k not in ("stock_lines", "stock_links")} | dict(
            stock_lines_n=len(out["variant_stock_mode"].get("stock_lines", [])), stock_links_n=len(out["variant_stock_mode"].get("stock_links", [])))
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(json.dumps(info(p), indent=1, default=str))
