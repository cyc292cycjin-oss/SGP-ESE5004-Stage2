"""DFX v3 probe 5 (read-only): which OLD columns of the sensitivity-mode industry summaries differ from the committed version (expected: none)."""
import subprocess
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

WT = Path("/home/jin/wt_dfx_v3_20261026")


def old(rel):
    return subprocess.run(["git", "show", f"834a0f19:{rel}"], cwd=WT, check=True, capture_output=True, text=True).stdout


for name in ("INDUSTRY_2050_SUMMARY_aeo8_ats_relative.csv", "INDUSTRY_2050_SUMMARY_gdp_OTHER_USEFUL_HEAT_BANDS.csv", "INDUSTRY_2050_SUMMARY_aeo8_ats_relative_level.csv"):
    rel = f"research_inputs/demand_v5/{name}"
    n = pd.read_csv(WT / rel); o = pd.read_csv(StringIO(old(rel)))
    for c in o.columns:
        if c not in n.columns:
            print(name, "MISSING", c); continue
        x, y = o[c], n[c]
        if x.dtype.kind in "fi" and y.dtype.kind in "fi":
            ne = ~(np.isclose(x.astype(float), y.astype(float), rtol=1e-9, atol=1e-9) | (x.isna() & y.isna()))
        else:
            ne = x.astype(str) != y.astype(str)
        if ne.any():
            print(name, "DIFF", c, "rows", int(ne.sum()), "old", x[ne].head(3).tolist(), "new", y[ne].head(3).tolist())
print("done")
