"""HPR: assemble HPR_EVIDENCE.json from the evidence folder (tests, H4 drill, dry run, package, consistency, leak scan, git) - numbers and file names only.
    python make_evidence_json.py <worktree> <out json>"""
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

WT = Path(sys.argv[1]); OUT = Path(sys.argv[2]); D = WT / "research/06_scope_redesign/p1_hpr_20261027"; E = D / "evidence"
PKG = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_hpr_20261027/hpc_package")
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/hpr")
jl = lambda p: json.loads(Path(p).read_text()) if Path(p).exists() else None
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).exists() else None
git = lambda *a: subprocess.run(["git", "-C", str(WT), *a], capture_output=True, text=True).stdout.strip()


def test_summary(log: Path):
    if not log.exists():
        return None
    t = log.read_text(errors="ignore"); m = re.search(r"(\d+) passed(?:, (\d+) skipped)?(?:, (\d+) failed)?|(\d+) failed, (\d+) passed(?:, (\d+) skipped)?", t)
    failed = re.findall(r"^FAILED (\S+)", t, re.M)
    return dict(file=log.name, summary_line=next((l for l in t.splitlines() if re.search(r"\d+ passed|\d+ failed", l) and " in " in l), None), failed=failed, sha256=sha(log))


h4 = jl(E / "h4" / "H4_DRILL.json"); st_h4 = (E / "h4" / "STATUS.txt").read_text() if (E / "h4" / "STATUS.txt").exists() else ""
gurobi_calls = []
for rid in ("F1", "F2"):
    m = re.search(rf"^SOLVE_{rid}:.*?:(\d{{4}}-\d\d-\d\dT\d\d:\d\d:\d\dZ)$", st_h4, re.M); e = re.search(rf"^GUROBI_{rid}:.*?:(\d+)s:(\d{{4}}-\d\d-\d\dT\d\d:\d\d:\d\dZ)$", st_h4, re.M)
    sp = jl(E / "h4" / rid / "split" / "SPLIT_SOLVE.json") or {}
    gurobi_calls.append(dict(rid=rid, start_utc=m.group(1) if m else None, end_utc=e.group(2) if e else None, process_seconds=int(e.group(1)) if e else None,
                             gurobi_status=sp.get("gurobi_status_name"), termination=sp.get("termination_condition"), iterations=sp.get("bar_iter_count"), runtime_s=sp.get("runtime_s"),
                             max_mem_used_gb=sp.get("max_mem_used_gb"), peak_rss_gib=(sp.get("peak_rss_bytes") or 0) / 2**30, objective_lp=sp.get("objective"), fingerprint=sp.get("fingerprint")))
dry = (E / "dry_run" / "DRYRUN_STATUS.txt").read_text() if (E / "dry_run" / "DRYRUN_STATUS.txt").exists() else ""
ref = [l.split("|") for l in (E / "dry_run" / "refusals" / "REFUSALS.txt").read_text().splitlines()] if (E / "dry_run" / "refusals" / "REFUSALS.txt").exists() else []
man = jl(PKG / "HPC_PACKAGE_MANIFEST.json")
res = dict(step="HPR", written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           instruction=dict(file="HPR_CLAUDE_CODE_INSTRUCTION.md", sha256=sha(D / "HPR_CLAUDE_CODE_INSTRUCTION.md"), registered_sha256_file=(D / "HPR_INSTRUCTION_SHA256.txt").read_text().split()[0]),
           git=dict(branch=git("branch", "--show-current"), head=git("rev-parse", "HEAD"), base="82c32c53c64047638989dee39b16135646ffcf1a", commits=git("log", "--format=%H %cI %s", "82c32c53..HEAD").splitlines(),
                    merges=git("log", "--merges", "--oneline", "82c32c53..HEAD").splitlines(), status_tracked=git("status", "--porcelain", "--untracked-files=no"), remote_head=git("ls-remote", "--heads", "origin", "codex/hpr-20261027").split()[:1]),
           run_plan=dict(file="RUN_PLAN_HPC.md", sha256=sha(D / "RUN_PLAN_HPC.md"), commit=git("log", "--format=%H %cI", "--diff-filter=A", "--", "research/06_scope_redesign/p1_hpr_20261027/RUN_PLAN_HPC.md").splitlines()[-1:]),
           networks=jl(E / "h4" / "BASE_CHECK_F1.json"),
           tests=dict(standin_first=test_summary(E / "tests" / "standin.log"), standin_hpr_b4p=test_summary(E / "tests" / "hpr_b4p.log"), full=test_summary(E / "tests" / "full.log"),
                      full_commit=(E / "tests" / "full_commit.txt").read_text().strip() if (E / "tests" / "full_commit.txt").exists() else None,
                      full_rs_a955ab59=test_summary(E / "tests" / "full_rs_a955ab59.log"), full_rs_a955ab59_commit=(E / "tests" / "full_rs_commit_a955ab59.txt").read_text().strip() if (E / "tests" / "full_rs_commit_a955ab59.txt").exists() else None,
                      full_rs_final=test_summary(E / "tests" / "full_rs.log"), full_rs_final_commit=(E / "tests" / "full_rs_commit.txt").read_text().strip() if (E / "tests" / "full_rs_commit.txt").exists() else None,
                      full_rs_skips_identical=((E / "tests" / "full_rs_skips.txt").read_text() == (E / "tests" / "full_rs_skips_a955ab59.txt").read_text()) if (E / "tests" / "full_rs_skips.txt").exists() and (E / "tests" / "full_rs_skips_a955ab59.txt").exists() else None),
           h4_drill=h4, h4_gurobi_calls=gurobi_calls, h4_status_sha256=sha(E / "h4" / "STATUS.txt"),
           dry_run=dict(status=dry.splitlines(), refusals=[dict(tag=r[0], exit=r[1], status=r[2]) for r in ref if len(r) >= 3], all_nonzero=all(r[1] != "exit=0" for r in ref if len(r) >= 3) if ref else None,
                        none_wrote_status=all(r[2] == "status=absent" for r in ref if len(r) >= 3) if ref else None, build_only_status=(E / "dry_run" / "BUILD_ONLY_STATUS.txt").read_text().splitlines() if (E / "dry_run" / "BUILD_ONLY_STATUS.txt").exists() else None),
           package=dict(dist=str(PKG), commit=(PKG / "COMMIT").read_text().strip() if (PKG / "COMMIT").exists() else None, files=len(man["files"]) if man else None, bytes=man.get("upload_total_bytes_excluding_this_manifest") if man else None,
                        sha256sums_sha256=man.get("sha256sums_sha256") if man else None, manifest_sha256=sha(PKG / "HPC_PACKAGE_MANIFEST.json"), networks=man.get("networks") if man else None, jobs=list((man.get("run") or {}).get("jobs", {})) if man else None),
           consistency=jl(E / "CONSISTENCY.json"), leak_scan=jl(E / "leak_scan" / "HPR_LEAK_SCAN.json"),
           reference_values_sha256=sha(D / "REFERENCE_VALUES.json"), operator_guide_sha256=sha(D / "HPC_OPERATOR_GUIDE.md"), checklist_sha256=sha(D / "PRE_HPC_CHECKLIST.md"), review_sha256=sha(D / "INDEPENDENT_REVIEW.md"))
if res["leak_scan"]:
    ls = res["leak_scan"]; res["leak_scan"] = dict(clean=ls.get("clean"), n_secret_values=ls.get("n_secret_values"), patterns_supplied=ls.get("patterns_supplied"), n_commits=ls.get("n_commits"),
                                                  targets={k: dict(files=v["files"], n_hit_files=v["n_hit_files"], hits=[h["file"] for h in v["hits"]], excluded=v["excluded"]) for k, v in ls["targets"].items()},
                                                  commits_with_hits={k: v for k, v in ls["commits"].items() if v["value_hits"] or v["pattern_hits"]})
if res["consistency"]:
    c = res["consistency"]; res["consistency"] = dict(all_consistent=c["all_consistent"], rows=len(c["rows"]), inconsistent=[r["item"] for r in c["rows"] if not r["consistent"]], walltime_components=c["walltime_components"])
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str) + "\n")
print(json.dumps(dict(head=res["git"]["head"][:8], tests={k: (v.get("summary_line") if isinstance(v, dict) else v) for k, v in res["tests"].items()}, h4=(h4 or {}).get("bitwise_equal_to_dfx_smoke"), package_files=res["package"]["files"], consistency=(res["consistency"] or {}).get("all_consistent"), leak_clean=(res["leak_scan"] or {}).get("clean")), ensure_ascii=False))
