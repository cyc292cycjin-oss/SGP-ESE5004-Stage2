"""M10P-2 diagnosis (read only): content comparison of the rebuilt networks (b46fc23d, worktree wt_m10p) with the M08b supplement 01 builds
(ec80668f, worktree wt_m08b): n.meta walked key by key (NaN == NaN), every static and time-varying component table compared."""
import json, logging, math, sys
from pathlib import Path
import numpy as np, pandas as pd, pypsa
logging.getLogger("pypsa").setLevel(logging.ERROR)
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
def walk(a, b, path=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            out += walk(a.get(k), b.get(k), f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            out += walk(x, y, f"{path}[{i}]")
    elif isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        pass
    elif a != b:
        out.append(dict(path=path, reference=str(b)[:200], new=str(a)[:200]))
    return out
res = {}
for sc, res_ in (("integrated", "365_24h"), ("disconnected", "365_24h"), ("integrated", "2920_3h"), ("disconnected", "2920_3h")):
    fn = f"{sc}_{res_}_unsolved.nc"
    a = pypsa.Network(str(MAIN / "m10p/builds" / sc / fn)); b = pypsa.Network(str(MAIN / "m08b/builds_s01" / sc / fn))
    md = walk(json.loads(json.dumps(a.meta, default=str)), json.loads(json.dumps(b.meta, default=str)))
    data = []
    for c in a.iterate_components():
        da, db = a.df(c.name), b.df(c.name)
        if not (da.index.equals(db.index) and list(da.columns) == list(db.columns)):
            data.append(dict(component=c.name, kind="static_index_or_columns")); continue
        for col in da.columns:
            x, y = da[col], db[col]
            if x.dtype.kind in "fi":
                if not np.array_equal(x.to_numpy(float), y.to_numpy(float), equal_nan=True):
                    data.append(dict(component=c.name, attr=col, kind="static", max_abs=float(np.nanmax(np.abs(x.to_numpy(float) - y.to_numpy(float))))))
            elif not x.astype(str).equals(y.astype(str)):
                data.append(dict(component=c.name, attr=col, kind="static_text"))
        for attr, ta in a.pnl(c.name).items():
            tb = b.pnl(c.name).get(attr)
            if tb is None or not (ta.index.equals(tb.index) and list(ta.columns) == list(tb.columns)):
                if not (len(ta.columns) == 0 and (tb is None or len(tb.columns) == 0)):
                    data.append(dict(component=c.name, attr=attr, kind="dynamic_shape"))
                continue
            if not np.array_equal(ta.to_numpy(float), tb.to_numpy(float), equal_nan=True):
                data.append(dict(component=c.name, attr=attr, kind="dynamic", max_abs=float(np.nanmax(np.abs(ta.to_numpy(float) - tb.to_numpy(float))))))
    sw = [col for col in a.snapshot_weightings.columns if not a.snapshot_weightings[col].equals(b.snapshot_weightings[col])]
    res[fn] = dict(meta_differences=md, meta_differences_count=len(md), data_differences=data, data_differences_count=len(data),
                   snapshots_equal=bool(a.snapshots.equals(b.snapshots)), snapshot_weightings_differ=sw)
    print(fn, "meta_diffs", len(md), "data_diffs", len(data), "| first meta:", [d["path"] for d in md[:8]], "| data:", data[:5])
Path(sys.argv[1]).write_text(json.dumps(res, indent=1) + "\n")
