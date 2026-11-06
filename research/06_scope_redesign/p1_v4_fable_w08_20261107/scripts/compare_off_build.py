"""Fable W08 review, dimension 2 (network level): the network built with the W08 code and every v4 switch off against the v3.1 package network
(hpc_package_v3_1, built at d3b9a3bc). Component tables and time series are compared numerically; meta keys that differ are listed.
usage: compare_off_build.py <off_build.nc> <v31_package.nc> <OUT.json>"""
import json
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
import pypsa  # noqa: E402

A, B, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
na, nb = pypsa.Network(A), pypsa.Network(B)
res = dict(off_build=A, v31_package=B, snapshots=(len(na.snapshots), len(nb.snapshots)))
comp = {}
for ca, cb in zip(na.iterate_components(), nb.iterate_components()):
    assert ca.name == cb.name
    da, db = ca.df, cb.df
    d = dict(rows=(len(da), len(db)), index_equal=bool(set(da.index) == set(db.index)), columns_only_a=sorted(set(da.columns) - set(db.columns)), columns_only_b=sorted(set(db.columns) - set(da.columns)))
    if d["index_equal"] and len(da):
        db = db.reindex(da.index); diffs = {}
        for col in sorted(set(da.columns) & set(db.columns)):
            x, y = da[col], db[col]
            if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
                xx, yy = x.astype(float).fillna(-9e99), y.astype(float).fillna(-9e99)
                m = ~np.isclose(xx.values, yy.values, rtol=1e-12, atol=1e-9)
                if m.any():
                    diffs[col] = dict(n=int(m.sum()), max_abs=float(np.nanmax(np.abs(xx.values[m] - yy.values[m]))), example=str(da.index[m][0]))
            else:
                m = (x.astype(str) != y.astype(str)).values
                if m.any():
                    diffs[col] = dict(n=int(m.sum()), example=str(da.index[m][0]), a=str(x.values[m][0])[:80], b=str(y.values[m][0])[:80])
        d["static_diffs"] = diffs
        # time series
        ts = {}
        for attr, pa in ca.pnl.items():
            pb = cb.pnl.get(attr)
            if pa is None or pa.empty and (pb is None or pb.empty):
                continue
            if pb is None or set(pa.columns) != set(pb.columns):
                ts[attr] = dict(columns_a=len(pa.columns), columns_b=(len(pb.columns) if pb is not None else 0), only_a=sorted(set(pa.columns) - set(pb.columns if pb is not None else []))[:5])
                continue
            pb2 = pb[pa.columns]
            m = ~np.isclose(pa.values, pb2.values, rtol=1e-12, atol=1e-9)
            if m.any():
                ts[attr] = dict(cells=int(m.sum()), max_abs=float(np.nanmax(np.abs(pa.values - pb2.values))))
        d["timeseries_diffs"] = ts
    comp[ca.name] = d
res["components"] = comp
ka, kb = set(na.meta), set(nb.meta)
res["meta_only_in_off_build"] = sorted(ka - kb); res["meta_only_in_v31"] = sorted(kb - ka)
diffm = []
for k in sorted(ka & kb):
    if json.dumps(na.meta[k], sort_keys=True, default=str) != json.dumps(nb.meta[k], sort_keys=True, default=str):
        diffm.append(k)
res["meta_keys_differing"] = diffm
# detail for the gas network ledger and the demand ledger
for k in ("research_gas_network", "s2_demand_ledger", "research_config_sha256", "research_config_subset_sha256", "code_sha"):
    if k in diffm:
        xa, xb = na.meta[k], nb.meta[k]
        if isinstance(xa, dict) and isinstance(xb, dict):
            res[f"meta_{k}_subkeys_differing"] = sorted(kk for kk in set(xa) | set(xb) if json.dumps(xa.get(kk), sort_keys=True, default=str) != json.dumps(xb.get(kk), sort_keys=True, default=str))
        else:
            res[f"meta_{k}"] = dict(off=str(xa)[:120], v31=str(xb)[:120])
json.dump(res, open(OUT, "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in res.items() if k != "components"}, indent=1, default=str))
for k, v in comp.items():
    flag = (v.get("static_diffs") or v.get("timeseries_diffs") or not v["index_equal"] or v["columns_only_a"] or v["columns_only_b"])
    print(k, "rows", v["rows"], "DIFF" if flag else "same", json.dumps({kk: vv for kk, vv in v.items() if kk != "rows" and vv}, default=str)[:600] if flag else "")
