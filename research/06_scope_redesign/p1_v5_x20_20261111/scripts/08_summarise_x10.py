"""X20 A 段：汇总 X10 表格中规格要引用的数（只读，输出到 stdout 与 evidence/）。"""
import sys
from pathlib import Path

import pandas as pd

X10 = Path(r"D:\ResearchWorkspaces\ASEAN\work\p1_v5_x10_checks_20261111")
OUT = Path(r"D:\ResearchWorkspaces\ASEAN\work\p1_v5_x20_20261111\evidence")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)

g = pd.read_csv(X10 / "GAS_CAPS_BY_COUNTRY.csv")
print("== GAS columns:", list(g.columns))
keep = [c for c in g.columns if any(k in c.lower() for k in ("rule", "coef", "cap", "country", "f1_use"))]
print(g[keep].to_string(index=False))

lt = pd.read_csv(X10 / "LIFETIME_BOUNDARY_UNITS.csv")
print("\n== LIFETIME columns:", list(lt.columns))
print("rows", len(lt))
cap_col = next(c for c in lt.columns if "mw" in c.lower() or "capacity" in c.lower())
grp = [c for c in lt.columns if c.lower() in ("country", "iso2", "technology", "type", "carrier", "model_carrier", "group")]
print("cap_col", cap_col, "group cols", grp)
if grp:
    print(lt.groupby(grp)[cap_col].agg(["count", "sum"]).sort_values("sum", ascending=False).head(30).to_string())
print("total MW", lt[cap_col].sum())

ac = pd.read_csv(X10 / "GEM_APPROX_COORDS.csv")
print("\n== APPROX columns:", list(ac.columns))
flag = [c for c in ac.columns if "50" in c or "change" in c.lower() or "flag" in c.lower() or "delta" in c.lower()]
print("flag cols", flag)
print(ac.head(40).to_string(index=False, max_colwidth=40))
sys.exit(0)
