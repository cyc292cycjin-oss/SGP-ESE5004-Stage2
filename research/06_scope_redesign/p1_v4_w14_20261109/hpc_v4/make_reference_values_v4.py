"""V4 W14 (RUN_PLAN_HPC_V4.md section 7): REFERENCE_VALUES.json of the v4 package for the batch-level comparison (b4_batch4.py summary, reference_comparison) of
F1 / F2 with (1) the v3.1 2920x3h HPC main pair F1 / F2 (decision 195; the v3.1 baseline of BASELINE_V31.md - main comparison), (2) the v4 D2c local 56-snapshot smoke
(the networks of this package cut to 56 snapshots are component-identical to it; source of the HPC smoke expectation) and (3) the v3.1 local 56-snapshot regression.
NUMBERS ONLY (objective incl. the constant, termination, GATES_V6 label, barrier iterations, Owen dual-form alpha-main shares, B6) read from the run folders given -
no result file, no path, no authorisation text enters the package. Read only, no solver.

    python make_reference_values_v4.py --v31 <hpc_results_v31/unpacked/export> --smoke-d2c <results_project/v4d2c/smoke56> --smoke-v31 <smoke56_v31 run dir> --out <json>
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
    for f in ("GUROBI_LOG_SCRUBBED.txt", "solve_log_scrubbed.txt", "p2_log_scrubbed.txt"):
        p = d / f
        if p.exists():
            m = re.findall(r"Barrier (?:performed|solved model in) (\d+) iterations", p.read_text(errors="ignore"))
            if m:
                return int(m[-1])
    return None


def run(d: Path, rid: str) -> dict:
    r = jl(d / "SOLVE_RECEIPT.json") or {}; a = jl(d / "V6_ACCEPTANCE.json") or {}
    return dict(rid=rid, objective_eur=r.get("objective"), objective_lp_eur=r.get("objective_lp"), termination=r.get("termination_condition"), label=a.get("label"),
                profile=r.get("solver_profile"), barrier_iterations=iterations(d), snapshots=(r.get("input_network") or {}).get("snapshots"), truncated_to=r.get("truncated_to"),
                network_sha256=(r.get("input_network") or {}).get("sha256"), owen_alpha_main_eur=owen_main(d))


def pair(di: Path, dd: Path, ri: str, rd: str, label: str, resolution: str) -> dict:
    i, d = run(di, ri), run(dd, rd)
    b6 = (d["objective_eur"] - i["objective_eur"]) / 1e9 if (i["objective_eur"] is not None and d["objective_eur"] is not None) else None
    return dict(label=label, integrated=i, disconnected=d, b6_bn=b6, resolution=resolution)


ap = argparse.ArgumentParser()
for k in ("v31", "smoke-d2c", "smoke-v31", "out"):
    ap.add_argument(f"--{k}", type=Path, required=True)
a = ap.parse_args()
refs = dict(v31_2920x3h=pair(a.v31 / "F1", a.v31 / "F2", "F1", "F2", "v3.1 2920×3h HPC 主算（第 195 项；v3.1 基线 BASELINE_V31.md，主对照）", "2920x3h"),
            v4_smoke56_d2c=pair(getattr(a, "smoke_d2c") / "v4d2c_F1", getattr(a, "smoke_d2c") / "v4d2c_F2", "v4d2c_F1", "v4d2c_F2",
                                "v4 D2c 本机 56 时段冒烟（本包网络截短后与之逐组件相同；HPC 冒烟期望值来源）", "56x3h"),
            v31_smoke56=pair(getattr(a, "smoke_v31") / "F1", getattr(a, "smoke_v31") / "F2", "F1-56", "F2-56", "v3.1 本机 56 时段回归（第 195 项修正后，截短）", "56x3h"))
res = dict(source="V4 W14 make_reference_values_v4.py: committed v3.1 / v4 results - values only", written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           inputs={k: hashlib.sha256(json.dumps(v, sort_keys=True, default=str).encode()).hexdigest() for k, v in refs.items()}, references=refs,
           note="description only (RUN_PLAN_HPC_V4.md 7): data version (v4 vs v3.1) and resolution (2920x3h vs 56x3h) effects; never an acceptance criterion")
a.out.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
print(json.dumps({k: dict(runs=(v["integrated"]["rid"], v["disconnected"]["rid"]), b6_bn=v["b6_bn"], obj=(v["integrated"]["objective_eur"], v["disconnected"]["objective_eur"]),
                      iters=(v["integrated"]["barrier_iterations"], v["disconnected"]["barrier_iterations"]), labels=(v["integrated"]["label"], v["disconnected"]["label"]),
                      owen=bool(v["integrated"]["owen_alpha_main_eur"])) for k, v in refs.items()}, ensure_ascii=False))
