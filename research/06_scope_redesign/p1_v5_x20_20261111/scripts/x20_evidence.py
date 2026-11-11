"""X20 §4：EVIDENCE.json —— 全部输入与产出的路径、字节数与 SHA256，分支与提交号；测试、静态检查与 56 时段回归的摘要（只取不含许可证内容的字段）。
只读（除写 EVIDENCE.json 外）；不加载网络（只算文件哈希）。用法：python x20_evidence.py"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

WT = Path("/home/jin/wt_v5_x20"); D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
BASE = "26c2e47d025fdd4e46cb278718d93aeddabbe984"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def rec(p: Path, root: Path) -> dict:
    return dict(path=str(p.relative_to(root)), bytes=p.stat().st_size, sha256=sha(p))


def git(*a) -> str:
    return subprocess.run(["git", "-C", str(WT), *a], capture_output=True, text=True, check=True).stdout.strip()


def jl(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:   # noqa: BLE001
        return None


ev = dict(created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), instruction=rec(D / "V5_X20_INSTRUCTION.md", D),
          branch=git("branch", "--show-current"), base_commit=BASE, head_at_evidence=git("rev-parse", "HEAD"),
          build_and_solve_commit="b05753a1c3e2ebf0689c2c2a5f6550bbafe6d1d7",
          commits=[dict(sha=l.split(" ", 1)[0], subject=l.split(" ", 1)[1]) for l in git("log", "--reverse", "--format=%H %s", f"{BASE}..HEAD").splitlines()],
          note="the delivery commit that carries this file is recorded in PROGRESS.md (last row) and in the ledger entry")
# code, configuration, tests and inputs changed since the W14 package commit
ch = []
for l in git("diff", "--name-status", BASE, "HEAD", "--", "scripts_project", "configs", "tests", "research_inputs").splitlines():
    st, *ps = l.split("\t"); p = WT / ps[-1]
    ch.append(dict(status=st, **(rec(p, WT) if p.exists() else dict(path=ps[-1], bytes=None, sha256=None))))
ev["changed_files_vs_w14"] = ch
ev["changed_files_count"] = {k: sum(1 for x in ch if x["path"].startswith(k)) for k in ("scripts_project", "configs", "tests", "research_inputs")}
# networks (D drive)
ev["networks"] = [rec(p, D) for p in sorted(list((D / "builds/v5main").glob("*/*_unsolved.nc")) + list((D / "builds/v5off").glob("*/*_unsolved.nc")) + list((D / "trunc56").glob("*.nc")))]
# downloads of this step
ev["downloads"] = [rec(p, D) for p in sorted((D / "downloads").rglob("*")) if p.is_file()]
# deliverables, evidence, scripts
ev["deliverables"] = [rec(p, D) for p in sorted(D.glob("*")) if p.is_file() and p.name != "EVIDENCE.json" and not p.name.startswith("REVIEW_")]
ev["evidence_files"] = [rec(p, D) for p in sorted((D / "evidence").glob("*")) if p.is_file()]
ev["scripts"] = [rec(p, D) for p in sorted((D / "scripts").glob("*")) if p.is_file()]
# summaries
ev["tests"] = dict(base=dict(head="e4b590f8", result="1 failed / 875 passed / 56 skipped / 5 deselected", log="logs/ut_full_base.txt"),
                   v5=dict(head="b05753a1", result="1 failed / 919 passed / 55 skipped / 5 deselected", log="logs/ut_full_v5.txt"),
                   failed_both="tests/research/test_s1_built_networks.py::BuiltNetworks::test_static_validation_passes_on_reload")
zs = jl(D / "evidence/ZERO_SLACK_CHECK_V5.json") or {}
ev["static"] = dict(zero_slack_passed=zs.get("passed"), s3_6=(jl(D / "evidence/S3_6_GATES_V5.json") or {}).get("all_passed", "see file"),
                    files=["evidence/V5_STATIC_CHECKS.json", "evidence/V5_STATIC_W14CHECKS.json", "evidence/V5_TRUNC56.json", "evidence/ZERO_SLACK_CHECK_V5.json", "evidence/S3_6_GATES_V5.json", "evidence/V5_BUILD_RECEIPT_CHECK.json"])
sm = {}
for rid in ("F1", "F2"):
    r = jl(D / "smoke56" / rid / "SOLVE_RECEIPT.json")
    if r:
        sm[rid] = {k: r.get(k) for k in ("scenario", "solver_profile", "status", "termination_condition", "objective", "objective_lp", "solve_seconds", "peak_rss_bytes", "decision", "optimize_calls", "retry")}
        sm[rid]["input_network"] = (r.get("input_network") or {}).get("sha256")
        v6 = jl(D / "smoke56" / rid / "V6_ACCEPTANCE.json") or {}
        sm[rid]["v6_label"] = v6.get("label") or v6.get("acceptance") or v6.get("decision")
ev["smoke56"] = sm
ev["smoke56_status_file"] = (D / "smoke56/STATUS.txt").read_text().splitlines() if (D / "smoke56/STATUS.txt").exists() else None
(D / "EVIDENCE.json").write_text(json.dumps(ev, indent=1, default=str) + "\n")
print(json.dumps({k: (v if not isinstance(v, list) else f"{len(v)} items") for k, v in ev.items() if k not in ("smoke56_status_file",)}, indent=1, default=str)[:4000])
