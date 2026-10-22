"""M10P-5 diagnosis (read only): R10 variant generated at packaging (dist folder, worktree code) vs in the unpacked package (dry run)."""
import json, logging, math, sys
from pathlib import Path
import numpy as np, pypsa
logging.getLogger("pypsa").setLevel(logging.ERROR)
A = sorted(Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m10p/package_variants/pass1/R10").glob("*_unsolved.nc"))[0]
B = sorted(Path("/home/jin/m10p_dry/pkg/runs/batch3/variants/R10").glob("*_unsolved.nc"))[0]
def walk(a, b, p=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            out += walk(a.get(k), b.get(k), f"{p}.{k}")
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            out += walk(x, y, f"{p}[{i}]")
    elif isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        pass
    elif a != b:
        out.append((p, str(a)[:160], str(b)[:160]))
    return out
na, nb = pypsa.Network(str(A)), pypsa.Network(str(B))
md = walk(json.loads(json.dumps(na.meta, default=str)), json.loads(json.dumps(nb.meta, default=str)))
for x in md: print("META", x)
nd = 0
for c in na.iterate_components():
    da, db = na.df(c.name), nb.df(c.name)
    for col in da.columns:
        if da[col].dtype.kind in "fi":
            if not np.array_equal(da[col].to_numpy(float), db[col].to_numpy(float), equal_nan=True): nd += 1; print("DATA", c.name, col)
        elif not da[col].astype(str).equals(db[col].astype(str)): nd += 1; print("DATA", c.name, col)
print("data differences:", nd)
