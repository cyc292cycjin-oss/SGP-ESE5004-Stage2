"""DFX v3 phase 1: DFX_EVIDENCE.json - light evidence JSON (hashes, counts, receipts, test results, smoke, dry run, package, commits). Read-only on sources.
    python make_evidence.py <package dist dir or -> <full test log or ->"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

WT = Path("/home/jin/wt_dfx_v3_20261026"); MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"); RES = MAIN / "results_project/dfx_v3"
DEL = WT / "research/06_scope_redesign/p1_dfx_20261026"; WORK = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026")
dist = Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "-" else None; full_log = Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "-" else None


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jl(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else None


def git(*a):
    return subprocess.run(["git", "-C", str(WT), *a], capture_output=True, text=True).stdout.strip()


ev = dict(script="work/p1_dfx_20261026/scripts/wsl_dfx3/make_evidence.py", written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
          instruction=dict(file="DFX_CLAUDE_CODE_INSTRUCTION.md", sha256=sha(DEL / "DFX_CLAUDE_CODE_INSTRUCTION.md"), registered=(DEL / "DFX_INSTRUCTION_SHA256.txt").read_text().split()[0]),
          branch=dict(name=git("branch", "--show-current"), head=git("rev-parse", "HEAD"), base="55ab07c0", log=git("log", "--format=%h %cI %s", "55ab07c0..HEAD").splitlines(), dirty=git("status", "--porcelain", "--untracked-files=no").splitlines(),
                      worktree=str(WT)),
          section0=dict(file="SECTION0_LEFTOVERS.md", paused_branch="codex/dfx-20261026 @ b0dbd52c (one commit, docs / scripts only)", paused_worktree="/home/jin/wt_dfx_20261026 (clean, kept)", paused_gurobi_calls=0, processes_found=0, reused=False),
          rules=dict(file="DFX_RULES.md", sha256=sha(DEL / "DFX_RULES.md"), commit=git("log", "--format=%h %cI", "-1", "--", "research/06_scope_redesign/p1_dfx_20261026/DFX_RULES.md"),
                     first_commit=git("log", "--format=%h %cI", "--diff-filter=A", "--", "research/06_scope_redesign/p1_dfx_20261026/DFX_RULES.md")),
          run_plan=dict(file="RUN_PLAN_DFX.md", sha256=sha(DEL / "RUN_PLAN_DFX.md"), first_commit=git("log", "--format=%h %cI", "--diff-filter=A", "--", "research/06_scope_redesign/p1_dfx_20261026/RUN_PLAN_DFX.md")),
          code_map=dict(files=["CODE_MAP.md", "CODE_MAP_TABLE.csv", "CODE_MAP_DATA.json"], sha256={f: sha(DEL / f) for f in ("CODE_MAP.md", "CODE_MAP_TABLE.csv", "CODE_MAP_DATA.json")},
                        dynamic_counts={k: len(v) for k, v in (jl(DEL / "CODE_MAP_DATA.json") or {}).get("dynamic", {}).items()} if (DEL / "CODE_MAP_DATA.json").exists() else None),
          registry=dict(file="research_inputs/registry_v5/DATA_REGISTRY.csv", sha256=sha(WT / "research_inputs/registry_v5/DATA_REGISTRY.csv"), rows=sum(1 for _ in open(WT / "research_inputs/registry_v5/DATA_REGISTRY.csv")) - 1,
                        old_sha256_prefix="4c59adb7", old_rows=2194, changelog="REGISTRY_CHANGELOG_DFX.csv", map="REGISTRY_NETWORK_INPUT_MAP.csv"),
          builds={})
for tag in ("v1", "v2"):
    for sc in ("integrated", "disconnected"):
        d = RES / f"builds_{tag}" / sc; rec = jl(d / f"{sc}_BUILD_RECEIPT.json") or {}
        ev["builds"][f"{tag}_{sc}"] = {k: dict(file=Path((rec.get(k) or {}).get("file", "")).name, sha256=(rec.get(k) or {}).get("sha256"), bytes=(rec.get(k) or {}).get("bytes"), snapshots=(rec.get(k) or {}).get("snapshots")) for k in ("network", "daily_network")} | dict(code_sha=rec.get("code_sha"), build_seconds=rec.get("build_seconds"))
ev["equivalence"] = dict(test="tests/research/test_dfx_demand.py::test_f5_structural_equivalence", networks=4, files=sorted(p.name for p in (RES / "equivalence").glob("*.json")) if (RES / "equivalence").exists() else None)
ev["review"] = dict(d1_checks={t: {k: (jl(WORK / "evidence" / f"DFX_D1_CHECKS_{t}.json") or {}).get(k) for k in ("totals_twh", "coverage_diff_twh", "industry_reconstruction_max_abs_diff_mwh")} for t in ("v1", "v2")},
                    diff=(jl(WORK / "evidence/DFX_DEMAND_DIFF_SUMMARY.json") or {}), bridge_closure=(jl(WORK / "evidence/DFX_BRIDGE_V2.json") or {}).get("closure"),
                    first_order={k: v.get("totals") for k, v in ((jl(WORK / "evidence/DFX_FIRST_ORDER.json") or {}).get("pairs") or {}).items()},
                    first_order_by_country={c: v.get("d_benefit_bn") for c, v in (((jl(WORK / "evidence/DFX_FIRST_ORDER.json") or {}).get("pairs") or {}).get("main (R1 / R2)", {}).get("by_country") or {}).items()})
ev["smoke"] = {k: v for k, v in (jl(RES / "smoke_v2/SMOKE_SUMMARY.json") or {}).items() if k != "status_lines"}
ev["dry_run"] = jl(RES / "dry_run_v8/DRY_RUN_DFX.json")
tests = {}
for name in ("subset.log", "runner.log"):
    p = RES / "tests" / name
    if p.exists():
        last = [l for l in p.read_text().splitlines() if "passed" in l or "failed" in l][-1:]; tests[name] = last[0] if last else None
if full_log and full_log.exists():
    last = [l for l in full_log.read_text(errors="ignore").splitlines() if "passed" in l or "failed" in l][-1:]; tests["full_suite"] = dict(file=str(full_log), result=last[0] if last else None)
ev["tests"] = tests
if dist and dist.exists():
    man = jl(dist / "PACKAGE_MANIFEST.json") or {}
    ev["package_v8"] = dict(dir=str(dist), commit=man.get("commit"), files=len(man.get("files") or []), bytes=man.get("upload_total_bytes_excluding_this_manifest"), sha256sums_sha256=man.get("sha256sums_sha256"),
                            manifest_sha256=sha(dist / "PACKAGE_MANIFEST.json"), networks=man.get("networks", {}).get("files"), run=man.get("run"), dry_run=man.get("dry_run"), upload_hours=man.get("upload", {}).get("hours_at"))
ev["local_gurobi_calls"] = dict(authorised=2, used=2, calls=(ev["smoke"] or {}).get("gurobi_calls"), gap_s=333, paused_session_calls=0)
ev["disk"] = dict(results_dfx_v3=subprocess.run(["du", "-sb", str(RES)], capture_output=True, text=True).stdout.split()[0], worktree=subprocess.run(["du", "-sb", str(WT)], capture_output=True, text=True).stdout.split()[0])
out = DEL / "DFX_EVIDENCE.json"; out.write_text(json.dumps(ev, indent=1, default=str) + "\n")
print("written", out, out.stat().st_size, "bytes"); print(json.dumps(dict(head=ev["branch"]["head"][:8], tests=tests, dry_run_passed=(ev["dry_run"] or {}).get("passed"), smoke=(ev["smoke"] or {}).get("all_optimal"), pkg=ev.get("package_v8", {}).get("files")), indent=1))
