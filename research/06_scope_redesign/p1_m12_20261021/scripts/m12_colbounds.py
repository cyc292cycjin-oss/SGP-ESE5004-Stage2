"""M12 diagnostic: which linopy variables carry finite non-zero bounds, and their rc x bound terms (smoke 56x3h arrays). No solve."""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

repo = Path("/home/jin/wt_m12_20261021"); sys.path.insert(0, str(repo / "scripts_project"))
from l23_violation_analysis import build_model   # noqa: E402

RP = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
sd = RP / "s4o/s4o3/solves/s4o_integrated"
n, m, cfg = build_model(repo, RP / "s4m/s4m1/builds/integrated/integrated_2920_3h_unsolved.nc", "integrated", 56, "M12_DIAG")
vlab = np.load(sd / "lp/vlabels.npy"); rc = np.load(sd / "solution/RC.npy"); lo = np.load(sd / "lp/col_lower.npy"); hi = np.load(sd / "lp/col_upper.npy")
top = max(int(np.asarray(m.variables[v].labels).max()) for v in m.variables) + 1
vname = np.full(top, -1, dtype=np.int32); names = list(m.variables)
for i, v in enumerate(names):
    lab = np.asarray(m.variables[v].labels).ravel(); vname[lab[lab >= 0]] = i
fam = vname[vlab]
b = np.where(rc > 0, lo, np.where(rc < 0, hi, 0.0)); term = np.where(np.isfinite(b), rc * np.where(np.isfinite(b), b, 0.0), 0.0)
fin = (np.isfinite(lo) & (lo != 0)) | (np.isfinite(hi) & (hi != 0))
df = pd.DataFrame(dict(var=[names[i] for i in fam], term=term, finite_nonzero_bound=fin))
out = df.groupby("var").agg(columns=("term", "size"), bounded=("finite_nonzero_bound", "sum"), term_eur=("term", "sum")).sort_values("term_eur")
print(out.to_string())
for v in names:
    V = m.variables[v]
    print(v, "lower finite nonzero:", int(np.sum(np.isfinite(np.asarray(V.lower)) & (np.asarray(V.lower) != 0))), "upper finite:", int(np.sum(np.isfinite(np.asarray(V.upper)))))
