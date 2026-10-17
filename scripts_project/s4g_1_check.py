"""S4G-1 (decision 98) checks on built networks (no solve):
  1. the 19 lines before (author build) / after (main build): num_parallel, x, r, b as stored, and the values PyPSA uses after
     calculate_dependent_values (x recomputed from the type, x_pu_eff);
  2. disconnected build: none of the 19 lines left;
  3. AC line x / x_pu_eff range and the Kirchhoff-voltage-law coefficients 1e5 x x_pu_eff x C over every cycle (pypsa 0.30.3
     optimization/constraints.py 651-652): overall |coefficient| range and the within-row max / min ratio (the row normalisation of
     s3b_scaling.normalise_kvl_rows divides each row by its largest |coefficient|), author vs main;
  4. consistency of the other AC lines (record only): s_nom / (sqrt3 x v_nom x i_nom x num_parallel) by category and country, lines with
     |ratio - 1| > 10 %, and how the x of the zero-capacity candidates is set.

    python scripts_project/s4g_1_check.py --main <dir> --author <dir> --disconnected <dir> --out results_project/s4g/s4g1
"""
from __future__ import annotations

import argparse
import json
import logging
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load(d: Path, sc: str):
    import pypsa
    return pypsa.Network(str(d / f"{sc}_2920_3h_unsolved.nc"))


def kvl_stats(n) -> dict:
    """The KVL coefficient matrix exactly as pypsa 0.30.3 builds it (1e5 x diag(x_pu_eff) x C per AC sub-network)."""
    n.calculate_dependent_values(); n.determine_network_topology()
    vals, ratios, lines_in_cycles = [], [], set()
    for sub in n.sub_networks.obj:
        if n.sub_networks.carrier[sub.name] != "AC" or not sub.C.size:
            continue
        br = sub.branches(); C = (1e5 * np.diag(br.x_pu_eff.values)) @ sub.C.toarray()
        for j in range(C.shape[1]):
            col = np.abs(C[:, j]); nz = col[col > 0]
            if nz.size:
                vals.append(nz); ratios.append(nz.max() / nz.min())
                lines_in_cycles |= {b[1] for b, v in zip(br.index, col) if v > 0}
    a = np.concatenate(vals) if vals else np.array([])
    r = np.array(ratios)
    return dict(cycles=int(len(ratios)), coefficients=int(a.size), abs_min=float(a.min()), abs_max=float(a.max()), span=float(a.max() / a.min()),
                within_row_ratio_max=float(r.max()), within_row_ratio_median=float(np.median(r)), within_row_ratio_p99=float(np.quantile(r, 0.99)),
                rows_ratio_over_1e4=int((r > 1e4).sum()), rows_ratio_over_1e6=int((r > 1e6).sum()), lines_in_cycles=len(lines_in_cycles))


def main():
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser()
    for k in ("main", "author", "disconnected", "out"):
        ap.add_argument(f"--{k}", type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    T = pd.read_csv(ROOT / "research_inputs/corridors/READJUST_IMPEDANCE_S4G1.csv", dtype={"line": str}).set_index("line")
    m, o, d = load(a.main, "integrated"), load(a.author, "integrated"), load(a.disconnected, "disconnected")
    stored = {tag: net.lines.loc[T.index, ["num_parallel", "x", "r", "b"]].copy() for tag, net in (("author", o), ("main", m))}
    # 3. KVL statistics (calculate_dependent_values recomputes x / r / b from the type and fills x_pu_eff)
    kv = {tag: kvl_stats(net) for tag, net in (("author", o), ("main", m))}
    rows = []
    for k, t in T.iterrows():
        rows.append(dict(line=k, country_pair=t.country_pair, s_nom_mw=float(m.lines.at[k, "s_nom"]),
                         num_parallel_author=float(stored["author"].at[k, "num_parallel"]), num_parallel_main=float(stored["main"].at[k, "num_parallel"]),
                         x_author=float(stored["author"].at[k, "x"]), x_main_stored=float(stored["main"].at[k, "x"]), x_main_used=float(m.lines.at[k, "x"]),
                         x_author_used=float(o.lines.at[k, "x"]), x_pu_eff_main=float(m.lines.at[k, "x_pu_eff"]), x_pu_eff_author=float(o.lines.at[k, "x_pu_eff"]),
                         r_author=float(stored["author"].at[k, "r"]), r_main=float(stored["main"].at[k, "r"]), b_author=float(stored["author"].at[k, "b"]), b_main=float(stored["main"].at[k, "b"]),
                         s_nom_max_main=float(m.lines.at[k, "s_nom_max"]), rating_main_mw=math.sqrt(3) * float(m.lines.at[k, "v_nom"]) * float(m.line_types.at[m.lines.at[k, "type"], "i_nom"]) * float(m.lines.at[k, "num_parallel"])))
    R = pd.DataFrame(rows)
    used_ok = bool(np.allclose(R.x_main_used, R.x_main_stored, rtol=1e-12) and np.allclose(R.x_main_used, T.loc[R.line, "x_s4g"].values, rtol=1e-12)
                   and np.allclose(R.x_pu_eff_main, R.x_main_used / 380.0 ** 2, rtol=1e-12))
    author_ok = bool(np.allclose(R.x_author_used, R.x_author, rtol=1e-12))
    R.to_csv(a.out / "READJUST_IMPEDANCE_CHECK_S4G1.csv", index=False)
    # 2. disconnected
    left = sorted(set(T.index) & set(d.lines.index))
    # x ranges (after calculate_dependent_values; all AC lines)
    xr = {tag: dict(x_min=float(net.lines.x.min()), x_max=float(net.lines.x.max()), x_pu_eff_min=float(net.lines.x_pu_eff.min()), x_pu_eff_max=float(net.lines.x_pu_eff.max()),
                    x_max_line=str(net.lines.x.idxmax()), x_min_line=str(net.lines.x.idxmin())) for tag, net in (("author", o), ("main", m))}
    # 4. consistency of the other AC lines (main build, after the correction)
    L = m.lines.copy(); cty = m.buses.country
    L["country0"] = L.bus0.map(cty); L["country1"] = L.bus1.map(cty)
    L["i_nom"] = L.type.map(m.line_types.i_nom); L["rating"] = math.sqrt(3) * L.v_nom * L.i_nom * L.num_parallel
    L["ratio"] = L.s_nom / L.rating
    def cat(k, z):
        if k in T.index:
            return "cross_border_readjusted_19"
        if str(k).startswith("S4E1"):
            return "candidate_s4e1"
        if str(k).startswith("APG"):
            return f"apg_{k}"
        if z.country0 != z.country1:
            return "cross_border_other"
        return "domestic_stock" if z.s_nom_min > 0 else "domestic_zero_stock"
    L["category"] = [cat(k, z) for k, z in L.iterrows()]
    L["dev_over_10pct"] = (L.s_nom > 0) & ((L.ratio - 1).abs() > 0.10)
    q = lambda s: dict(n=int(len(s)), min=float(s.min()), p10=float(s.quantile(0.1)), median=float(s.median()), p90=float(s.quantile(0.9)), max=float(s.max())) if len(s) else {}
    by_cat = {c: dict(ratio=q(g.ratio[g.s_nom > 0]), lines=int(len(g)), zero_capacity=int((g.s_nom == 0).sum()), over_10pct=int(g.dev_over_10pct.sum())) for c, g in L.groupby("category")}
    dom = L[L.category.isin(["domestic_stock"])]
    by_cty = {c: dict(ratio=q(g.ratio), over_10pct=int(g.dev_over_10pct.sum())) for c, g in dom.groupby("country0")}
    cand = L[L.s_nom == 0]
    cand_x = dict(count=int(len(cand)), num_parallel_values=sorted({round(float(v), 6) for v in cand.num_parallel}), types=sorted(set(cand.type)),
                  template=str(next((x.get("template_line") for x in m.meta.get("apg_corridor_additions", []) if x.get("template_line")), "")),
                  x_rule="x = x_per_length(type) x length / num_parallel(template) at every optimisation (pf.apply_line_types); the template is the existing cross-border AC line "
                         "closest to the median num_parallel (s2_layers.add_apg_corridor_lines), taken before the S4G-1 correction")
    L[["bus0", "bus1", "country0", "country1", "category", "type", "length", "num_parallel", "s_nom", "s_nom_min", "rating", "ratio", "x", "dev_over_10pct"]].to_csv(a.out / "AC_LINE_CONSISTENCY_S4G1.csv")
    summ = dict(lines_19=dict(used_values_recomputed=used_ok, author_build_uses_author_x=author_ok, x_factor_min=float((R.x_main_used / R.x_author).min()),
                              x_factor_max=float((R.x_main_used / R.x_author).max()), ratio_after_min=float((R.s_nom_mw / R.rating_main_mw).min()), ratio_after_max=float((R.s_nom_mw / R.rating_main_mw).max())),
                disconnected=dict(lines_19_left=left, cross_border_lines=int((d.lines.border_class == "cross_border").sum())),
                x_range=xr, kvl=kv, consistency=dict(by_category=by_cat, domestic_by_country=by_cty, over_10pct_list=L[L.dev_over_10pct].index.astype(str).tolist(),
                                                    zero_capacity_lines=cand_x))
    (a.out / "READJUST_CHECK_S4G1.json").write_text(json.dumps(summ, indent=1, default=str))
    pd.set_option("display.width", 250)
    print(R[["line", "country_pair", "num_parallel_author", "num_parallel_main", "x_author", "x_main_used", "x_pu_eff_main"]].round(5).to_string())
    print(json.dumps({k: summ[k] for k in ("lines_19", "disconnected", "x_range", "kvl")}, indent=1))
    print(json.dumps(by_cat, indent=1)); print(json.dumps(cand_x, indent=1))


if __name__ == "__main__":
    main()
