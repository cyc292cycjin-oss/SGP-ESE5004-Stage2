"""V4 D1 section 7.1, extra static checks (no solver):
  C8 network difference D1 vs W08 (same tag, 2920x3h and 365x24h): every component table (static columns) and every time series compared value by value;
     expected: only Store.marginal_cost of the five oil_palm_trunk pools differs (section 3); n.meta keys that differ are listed.
  C9 the five trunk Stores carry the registry proxy biomass_missing_cost_proxy, every other biomass Store the W08 cost; the biomass ledger records the rule.
Writes evidence/D1_NETWORK_DIFF.json.

    PYTHONHASHSEED=0 <env python> scripts/d1_static_extra.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

W = Path(__file__).resolve().parents[1]
R = Path("/home/jin/wt_v4_d1")
B8 = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/builds/main")
B1 = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d1/builds/main")
TRUNK = {f"{c} biomass oil_palm_trunk" for c in ("ID", "KH", "MY", "PH", "TH")}


def same(a, b) -> bool:
    if a.dtype.kind in "fc" or b.dtype.kind in "fc":
        x, y = pd.to_numeric(a, errors="coerce"), pd.to_numeric(b, errors="coerce")
        return bool(((x == y) | (x.isna() & y.isna())).all())
    return bool((a.astype(str) == b.astype(str)).all())


def diff(n8, n1) -> dict:
    out = dict(static={}, series={}, sets={})
    for c in n1.iterate_components():
        a = n8.df(c.name); b = c.df
        if set(a.index) != set(b.index):
            out["sets"][c.name] = dict(only_w08=sorted(set(a.index) - set(b.index))[:20], only_d1=sorted(set(b.index) - set(a.index))[:20])
        idx = a.index.intersection(b.index)
        for col in sorted(set(a.columns) | set(b.columns)):
            if col not in a.columns or col not in b.columns:
                out["static"].setdefault(c.name, {})[col] = "column only in one network"
                continue
            x, y = a.loc[idx, col], b.loc[idx, col]
            if not same(x, y):
                bad = [i for i in idx if not same(x.loc[[i]], y.loc[[i]])]
                out["static"].setdefault(c.name, {})[col] = dict(n=len(bad), names=bad[:20], w08=[x.loc[i] for i in bad[:5]], d1=[y.loc[i] for i in bad[:5]])
        pa, pb = n8.pnl(c.name), c.pnl
        for k in sorted(set(pa) | set(pb)):
            ta, tb = pa.get(k, pd.DataFrame()), pb.get(k, pd.DataFrame())
            cols = sorted(set(ta.columns) | set(tb.columns))
            if not cols:
                continue
            if set(ta.columns) != set(tb.columns) or not np.array_equal(ta[cols].to_numpy(), tb.reindex(columns=cols).to_numpy(), equal_nan=True):
                out["series"].setdefault(c.name, []).append(k)
    sw = n8.snapshot_weightings.equals(n1.snapshot_weightings) and n8.snapshots.equals(n1.snapshots)
    out["snapshots_and_weightings_equal"] = bool(sw)
    mk = sorted(set(n8.meta) | set(n1.meta))
    out["meta_keys_differing"] = [k for k in mk if json.dumps(n8.meta.get(k), sort_keys=True, default=str) != json.dumps(n1.meta.get(k), sort_keys=True, default=str)]
    return out


def main():
    reg = pd.read_csv(R / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    proxy = float(reg.at["biomass_missing_cost_proxy", "value"])
    res = {}
    for sc in ("integrated", "no_new_xb"):
        for z in ("2920_3h", "365_24h"):
            n8 = pypsa.Network(str(B8 / sc / f"{sc}_{z}_unsolved.nc")); n1 = pypsa.Network(str(B1 / sc / f"{sc}_{z}_unsolved.nc"))
            d = diff(n8, n1)
            st = d["static"]
            only_trunk = (not d["sets"] and not d["series"] and set(st) == {"Store"} and set(st["Store"]) == {"marginal_cost"} and set(st["Store"]["marginal_cost"]["names"]) == TRUNK)
            bio = n1.stores[n1.stores.bus.str.startswith(("solid biomass", "biogas"))]
            trunk_ok = bool((n1.stores.loc[sorted(TRUNK), "marginal_cost"] == proxy).all() and (n8.stores.loc[sorted(TRUNK), "marginal_cost"] == 0.0).all())
            others = bio.index.difference(sorted(TRUNK))
            others_ok = bool((n1.stores.loc[others, "marginal_cost"] == n8.stores.loc[others, "marginal_cost"]).all())
            mcl = (n1.meta.get("research_biomass") or {}).get("missing_cost_rule") or {}
            res[f"{sc}_{z}"] = dict(C8_only_trunk_store_cost_differs=only_trunk, C8_diff=d, C9_trunk_at_proxy=trunk_ok, C9_other_biomass_unchanged=others_ok,
                                    C9_ledger_rule=mcl.get("rule"), C9_ledger_stores=sorted(x["store"] for x in mcl.get("stores", [])), proxy_eur_per_mwh=proxy,
                                    v4_meta=dict(switch_sha256=(n1.meta.get("v4_w08") or {}).get("switch_sha256"), tables_dir=(n1.meta.get("v4_w08") or {}).get("tables_dir"),
                                                 missing_cost_rule=((n1.meta.get("v4_w08") or {}).get("switches") or {}).get("missing_cost_rule")))
            print(sc, z, "only trunk cost differs:", only_trunk, "trunk at proxy:", trunk_ok, "others unchanged:", others_ok, "meta keys differing:", d["meta_keys_differing"])
    (W / "evidence").mkdir(exist_ok=True)
    (W / "evidence/D1_NETWORK_DIFF.json").write_text(json.dumps(res, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
