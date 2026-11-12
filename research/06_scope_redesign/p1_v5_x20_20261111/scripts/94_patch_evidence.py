"""一次性修改 x20_evidence.py：加入 C 段（最终构建提交、c2main / c2off 网络、C 段测试、_C2 静态检查、smoke56_c2 回归）。用法：python 94_patch_evidence.py"""
from pathlib import Path
import ast

p = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/scripts/x20_evidence.py"); s = p.read_text(encoding="utf-8")
rep = [
    ('build_and_solve_commit="b05753a1c3e2ebf0689c2c2a5f6550bbafe6d1d7",',
     'build_and_solve_commit="b05753a1c3e2ebf0689c2c2a5f6550bbafe6d1d7", final_build_and_solve_commit_c_segment="645c37e9505baf00bb64df51689d9c89f68ad08a",'),
    ('list((D / "builds/v5off").glob("*/*_unsolved.nc")) + list((D / "trunc56").glob("*.nc")))]',
     'list((D / "builds/v5off").glob("*/*_unsolved.nc")) + list((D / "builds/c2main").glob("*/*_unsolved.nc")) + list((D / "builds/c2off").glob("*/*_unsolved.nc")) + list((D / "trunc56").glob("*.nc")))]'),
    ('                   failed_both=', '                   v5_final_c_segment=dict(head="645c37e9", result="1 failed / 927 passed / 55 skipped / 5 deselected", log="logs/ut_full_v5_C2.txt"),\n                   failed_both='),
    ('ev["smoke56"] = sm\n', 'ev["smoke56"] = sm\nsm2 = {}\nfor rid in ("F1", "F2"):\n    r = jl(D / "smoke56_c2" / rid / "SOLVE_RECEIPT.json")\n    if r:\n        sm2[rid] = {k: r.get(k) for k in ("scenario", "solver_profile", "status", "termination_condition", "objective", "objective_lp", "solve_seconds", "peak_rss_bytes", "decision", "optimize_calls", "retry")}\n        sm2[rid]["input_network"] = (r.get("input_network") or {}).get("sha256")\n        sm2[rid]["v6_label"] = (jl(D / "smoke56_c2" / rid / "V6_ACCEPTANCE.json") or {}).get("label")\nev["smoke56_c_segment"] = sm2\nev["smoke56_c_segment_status_file"] = (D / "smoke56_c2/STATUS.txt").read_text().splitlines() if (D / "smoke56_c2/STATUS.txt").exists() else None\nzs2 = jl(D / "evidence/ZERO_SLACK_CHECK_V5_C2.json") or {}\nev["static_c_segment"] = dict(zero_slack_passed=zs2.get("passed"), files=sorted(str(x.relative_to(D)) for x in (D / "evidence").glob("*_C2.*")))\nev["environment_audit"] = dict(file="evidence/WINDOWS_PYTHON_RERUN.json", all_equal=(jl(D / "evidence/WINDOWS_PYTHON_RERUN.json") or {}).get("all_equal"))\n'),
]
for a, b in rep:
    if a not in s:
        raise SystemExit("pattern not found: " + a[:70])
    s = s.replace(a, b)
ast.parse(s); p.write_text(s, encoding="utf-8"); print("patched")
