"""V3 HPC package (RUN_PLAN_HPC_V3.md 7.4): REFERENCE_VALUES.json for the batch-level comparison of F1 / F2 (2920x3h, S-A) with the committed v3 results -
the 365x24h rerun after decision 182 (V1 / V2, main reference), the first 365x24h screening (V1 / V2) and the two local 56-snapshot smokes (S-A of this package
step, S-B of supplement 05). NUMBERS ONLY (objective, termination, GATES_V6 label, barrier iterations, Owen dual-form alpha-main shares, B6) read from the run
folders given - no result file, no path, no authorisation text enters the package. Read only, no solver.

    python make_reference_values_v3.py --dmax <dmax_screen dir> --screen <screen dir> --smoke-sa <smoke dir> --smoke-sb <smoke_s5 dir> --out <REFERENCE_VALUES.json>
"""
import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts_project"))
from m10_batch3_summary import jl, owen_main   # noqa: E402


def iterations(d: Path):
    for f in ("GUROBI_LOG_SCRUBBED.txt", "gurobi.linopy.log"):
        p = d / f
        if p.exists():
            m = re.findall(r"Barrier (?:performed|solved model in) (\d+) iterations", p.read_text(errors="ignore"))
            if m:
                return int(m[-1])
    return None


def run(d: Path, rid: str) -> dict:
    r = jl(d / "SOLVE_RECEIPT.json") or {}; a = jl(d / "V6_ACCEPTANCE.json") or {}
    return dict(rid=rid, objective_eur=r.get("objective"), termination=r.get("termination_condition"), label=a.get("label"), profile=r.get("solver_profile"),
                barrier_iterations=iterations(d), snapshots=(r.get("input_network") or {}).get("snapshots"), truncated_to=r.get("truncated_to"), owen_alpha_main_eur=owen_main(d))


def pair(di: Path, dd: Path, ri: str, rd: str, label: str, resolution: str, shipping: str) -> dict:
    i, d = run(di, ri), run(dd, rd)
    b6 = (d["objective_eur"] - i["objective_eur"]) / 1e9 if (i["objective_eur"] is not None and d["objective_eur"] is not None) else None
    return dict(label=label, integrated=i, disconnected=d, b6_bn=b6, resolution=resolution, shipping=shipping)


ap = argparse.ArgumentParser()
for k in ("dmax", "screen", "smoke-sa", "smoke-sb", "out"):
    ap.add_argument(f"--{k}", type=Path, required=True)
a = ap.parse_args()
refs = dict(v3_365x24h_dmax=pair(a.dmax / "V1", a.dmax / "V2", "V1", "V2", "v3 365×24h 重跑（第 182 项后，S-B；主参照，只用于 B6 符号与程序对照，第 176 项第 7 条）", "365x24h", "S-B"),
            v3_365x24h_first=pair(a.screen / "V1", a.screen / "V2", "V1", "V2", "v3 365×24h 第一次筛查（第 182 项前，S-B；并列）", "365x24h", "S-B"),
            v3_smoke56_sa=pair(getattr(a, "smoke_sa") / "integrated", getattr(a, "smoke_sa") / "no_new_xb", "F1-56", "F2-56", "v3 本机 56 时段冒烟（S-A，本包网络的截短）", "56x3h", "S-A"),
            v3_smoke56_sb=pair(getattr(a, "smoke_sb") / "integrated", getattr(a, "smoke_sb") / "no_new_xb", "S5-I", "S5-R", "v3 补充 05 冒烟（S-B，第 180 项网络的截短）", "56x3h", "S-B"))
src = {k: str(v) for k, v in vars(a).items() if k != "out"}
res = dict(source="V3 HPC make_reference_values_v3.py: committed v3 results - values only", written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           inputs={k: hashlib.sha256(json.dumps(v, sort_keys=True, default=str).encode()).hexdigest() for k, v in refs.items()}, references=refs,
           note="description only (RUN_PLAN_HPC_V3.md 7.4): resolution (2920x3h vs 365x24h vs 56x3h) and shipping cost basis (S-A vs S-B) effects; never an acceptance criterion")
a.out.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
print(json.dumps({k: dict(runs=(v["integrated"]["rid"], v["disconnected"]["rid"]), b6_bn=v["b6_bn"], obj=(v["integrated"]["objective_eur"], v["disconnected"]["objective_eur"]),
                      iters=(v["integrated"]["barrier_iterations"], v["disconnected"]["barrier_iterations"]), owen=bool(v["integrated"]["owen_alpha_main_eur"])) for k, v in refs.items()}, ensure_ascii=False))
