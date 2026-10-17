"""S4C-3 item 2 (user 2026-10-17): research.cost_layer.registry sat under research.corridors from 077ebd0b (S4C-1) to 9a5ea111 (S4C-2).
Empirical check that the S4C-1 / S4C-2 builds were not affected: compare every static attribute and every time series of a reference build made
with the misplaced key against a build with the corrected config whose S4C-3 layer leaves the network untouched (bunkers.attribution =
bunkering_country), plus the active cost table and the research config (key position aside).

    python scripts_project/s4c_3_config_key_check.py --reference <dir/integrated_2920_3h_unsolved.nc> --corrected <...nc> --label <name> --output <json>
           [--costs-only]   (S4C-1 reference: hydro inflows differ by design (S4C-2), compare costs only)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

COST_COLS = ("capital_cost", "marginal_cost", "lifetime", "efficiency", "p_nom_max", "e_nom_max", "s_nom_max", "length")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def diff_frames(a: pd.DataFrame, b: pd.DataFrame, cols=None) -> dict:
    out = {}
    if set(a.index) != set(b.index):
        out["index"] = dict(only_reference=sorted(set(a.index) - set(b.index))[:10], only_corrected=sorted(set(b.index) - set(a.index))[:10])
    idx = a.index.intersection(b.index)
    for c in (cols or sorted(set(a.columns) | set(b.columns))):
        if c not in a.columns or c not in b.columns:
            if cols is None:
                out[c] = "column only in one network"
            continue
        x, y = a.loc[idx, c], b.loc[idx, c]
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            bad = ~np.isclose(x.astype(float), y.astype(float), rtol=0, atol=0, equal_nan=True)
        else:
            bad = (x.astype(str) != y.astype(str)).values
        if bad.any():
            out[c] = dict(n=int(bad.sum()), examples=list(map(str, idx[bad][:5])))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--reference", type=Path, required=True); ap.add_argument("--corrected", type=Path, required=True)
    ap.add_argument("--label", required=True); ap.add_argument("--output", type=Path, required=True); ap.add_argument("--costs-only", action="store_true")
    ap.add_argument("--allow-config-diff", default="", help="comma list of top-level research keys that differ by design (e.g. hydro for a pre-S4C-2 build)")
    a = ap.parse_args()
    import pypsa
    logging.disable(logging.WARNING)
    r, c = pypsa.Network(str(a.reference)), pypsa.Network(str(a.corrected))
    res = dict(label=a.label, reference=dict(path=str(a.reference), sha256=sha(a.reference)), corrected=dict(path=str(a.corrected), sha256=sha(a.corrected)), static={}, series={})
    for comp in ["Bus", "Carrier", "Generator", "Load", "Link", "Line", "Store", "StorageUnit", "Transformer", "GlobalConstraint"]:
        d = diff_frames(r.df(comp), c.df(comp), cols=[x for x in COST_COLS if x in r.df(comp)] if a.costs_only else None)
        if d:
            res["static"][comp] = d
        if a.costs_only:
            continue
        for attr, df in r.pnl(comp).items():
            if df.empty and c.pnl(comp)[attr].empty:
                continue
            d = diff_frames(df.T, c.pnl(comp)[attr].T)
            if d:
                res["series"][f"{comp}.{attr}"] = dict(columns_differing=sorted(set(d) - {"index"})[:5], index=d.get("index"), n_snapshot_columns=len(d))
    ca, cb = a.reference.parent / "costs_active_research.csv", a.corrected.parent / "costs_active_research.csv"
    res["costs_active_research"] = dict(reference=sha(ca), corrected=sha(cb), identical=sha(ca) == sha(cb))
    ra, rb = json.loads(json.dumps(r.meta["research_config"])), json.loads(json.dumps(c.meta["research_config"]))
    moved_ref = ra.get("corridors", {}).pop("registry", None); moved_cor = rb.get("cost_layer", {}).pop("registry", None)
    rb.pop("bunkers", None); ra.pop("config_overrides", None); rb.pop("config_overrides", None)
    for k in [x for x in a.allow_config_diff.split(",") if x]:   # by-design differences, reported separately
        res.setdefault("config_by_design", {})[k] = dict(reference=ra.pop(k, None), corrected=rb.pop(k, None))
    res["research_config"] = dict(reference_key_under_corridors=moved_ref, corrected_key_under_cost_layer=moved_cor,
                                  identical_after_key_position_and_s4c3_block=(ra == rb), differing_top_keys=sorted(k for k in set(ra) | set(rb) if ra.get(k) != rb.get(k)))
    # key values named by the user: wind / solar candidate costs and hydro inflows
    def key_values(n):
        g = n.generators; su = n.storage_units; w = n.snapshot_weightings.generators
        kv = {f"capital_cost_mean_{car}": float(g[(g.carrier == car) & g.p_nom_extendable].capital_cost.mean()) for car in ["onwind", "solar", "solar rooftop", "offwind-ac", "offwind-dc"]}
        inf = n.storage_units_t.inflow
        kv["hydro_inflow_existing_twh"] = float(inf[[x for x in inf.columns if su.at[x, "carrier"] == "hydro existing"]].mul(w, axis=0).sum().sum() / 1e6)
        ror = g[g.carrier == "ror existing"]
        pm = n.get_switchable_as_dense("Generator", "p_max_pu")[ror.index]
        kv["ror_existing_twh"] = float((pm * ror.p_nom).mul(w, axis=0).sum().sum() / 1e6)
        return kv
    res["key_values"] = dict(reference=key_values(r), corrected=key_values(c))
    res["unaffected"] = (not res["static"] and not res["series"] and res["costs_active_research"]["identical"] and res["research_config"]["identical_after_key_position_and_s4c3_block"])
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(res, indent=1, sort_keys=True, default=str))
    print(json.dumps(dict(label=a.label, unaffected=res["unaffected"], static=res["static"], series=list(res["series"])[:8], costs=res["costs_active_research"]["identical"],
                          config=res["research_config"], key_values=res["key_values"]), default=str)[:3000])


if __name__ == "__main__":
    main()
