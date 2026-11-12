"""只读：C 段 56 时段回归的 V5 旧门失败集（与 D2c、B 段对照）与 RUN_STATUS post_solve_errors。用法：python 95_c2_gates.py"""
import json
from pathlib import Path

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")


def failed(p):
    d = json.loads(Path(p).read_text()); g = d.get("gates") or d
    return sorted(k for k, v in g.items() if (v.get("passed") if isinstance(v, dict) else v) is False)


for r in ("F1", "F2"):
    a = failed(D / f"cache/d2c_{r}_V5_GATES.json"); b = failed(D / f"smoke56/{r}/V5_GATES.json"); c = failed(D / f"smoke56_c2/{r}/V5_GATES.json")
    rs = json.loads((D / f"smoke56_c2/{r}/RUN_STATUS.json").read_text())
    print(r, "c2 failed", c, "same as d2c", a == c, "same as B", b == c, "post_solve_errors", rs.get("post_solve_errors"))
