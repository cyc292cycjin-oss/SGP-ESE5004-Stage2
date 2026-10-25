"""B4P evidence collector -> work/p1_b4p_20261026/B4P_EVIDENCE.json (read only): instruction hash, git state, builds, Gurobi usage ledger (every
local call with start / end UTC, gap, network, mode, result), compute-time ledger, the solve comparisons (equivalence), A1 data / extrapolation,
drill, regression, tests, package, dry run. Usage: python b4p_evidence.py"""
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

W = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_b4p_20261026"); E = W / "evidence"
RES = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/b4p")
WT = Path("/home/jin/wt_b4p_20261026")


def jl(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def git(*a):
    return subprocess.run(["git", *a], cwd=WT, capture_output=True, text=True).stdout.strip()


def gurobi_ledger():
    st = (RES / "SOLVES_STATUS.txt").read_text().splitlines() if (RES / "SOLVES_STATUS.txt").exists() else []
    calls = []
    for d in sorted((RES / "solves").glob("*")):
        if not (d / ".call_start").exists():
            continue
        mode = (d / "MODE.txt").read_text().split()
        start = (d / ".call_start").read_text().strip(); end = (d / ".call_end").read_text().strip() if (d / ".call_end").exists() else None
        sp = jl(d / "split" / "SPLIT_SOLVE.json") or {}; rec = jl(d / "SOLVE_RECEIPT.json") or {}
        tf = (d / ("p2.err" if (d / "p2.err").exists() else "solve.err"))
        m = re.search(r"Maximum resident set size \(kbytes\): (\d+)", tf.read_text(errors="ignore")) if tf.exists() else None
        log = d / "gurobi.linopy.log"; it = None; wu = None
        if log.exists():
            mm = re.search(r"Barrier (?:solved model in|performed) (\d+) iterations (?:and|in) ([\d.]+) seconds \(([\d.]+) work units\)", log.read_text(errors="ignore"))
            if mm:
                it, wu = int(mm.group(1)), float(mm.group(3))
        calls.append(dict(tag=d.name, mode=mode[0], scenario=mode[1], snapshots=int(mode[2]), profile=mode[3], extra=" ".join(mode[4:]), call_start_utc=start, call_end_utc=end,
                          gurobi_process=("b4_split_solve.py" if mode[0] in ("split", "probe") else "s2_solve.py"), gurobi_status=sp.get("gurobi_status_name"),
                          termination=sp.get("termination_condition") or rec.get("termination_condition"), objective=(sp.get("objective") if sp else rec.get("objective")),
                          iterations=(sp.get("bar_iter_count") if sp else it), work_units=(sp.get("work_units") if sp else wu), runtime_s=sp.get("runtime_s"),
                          max_mem_used_gb=sp.get("max_mem_used_gb"), fingerprint=sp.get("fingerprint"), peak_rss_gib_gurobi_process=(int(m.group(1)) / 2**20 if m else None)))
    calls.sort(key=lambda c: c["call_start_utc"])
    for i, c in enumerate(calls):
        c["call_number"] = i + 1
        c["gap_from_previous_end_s"] = (ts(c["call_start_utc"]) - ts(calls[i - 1]["call_end_utc"])).total_seconds() if i and calls[i - 1]["call_end_utc"] else None
        c["duration_s"] = (ts(c["call_end_utc"]) - ts(c["call_start_utc"])).total_seconds() if c["call_end_utc"] else None
    refused = [l for l in st if l.startswith("REFUSED_")]
    return dict(calls=calls, count=len(calls), authorised=8, calls_used_file=((RES / ".calls_used").read_text().strip() if (RES / ".calls_used").exists() else None), refused_attempts=refused,
                all_truncated=all(c["snapshots"] <= 365 for c in calls), max_duration_s=max((c["duration_s"] or 0) for c in calls) if calls else None,
                min_gap_s=min((c["gap_from_previous_end_s"] for c in calls if c["gap_from_previous_end_s"] is not None), default=None))


def compute_ledger():
    rows = []
    bs = (RES / "BUILDS_STATUS.txt").read_text().splitlines() if (RES / "BUILDS_STATUS.txt").exists() else []
    for l in bs:
        m = re.match(r"BUILD_(\w+)_(\d+):\S+:exit=\d+:(\d+)s", l)
        if m:
            rows.append(dict(item=f"build {m.group(1)} {m.group(2)}", seconds=int(m.group(3))))
    for d in sorted((RES / "solves").glob("*")):
        for f in ("solve.err", "p1.err", "p2.err", "p3.err"):
            p = d / f
            if p.exists():
                m = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): ([\d:.]+)", p.read_text(errors="ignore"))
                if m:
                    parts = [float(x) for x in m.group(1).split(":")]; rows.append(dict(item=f"{d.name} {f[:-4]}", seconds=sum(v * 60 ** (len(parts) - 1 - i) for i, v in enumerate(parts))))
    for p in sorted((E / "tests").glob("*.log")) if (E / "tests").exists() else []:
        m = re.search(r"in ([\d.]+)s", p.read_text(errors="ignore"))
        if m:
            rows.append(dict(item=f"tests {p.stem}", seconds=float(m.group(1))))
    for name, p in (("drill_b4", RES / "drill" / "DRILL_B4.json"), ("regress9", E / "regress" / "drill9.log")):
        if p.exists():
            if p.suffix == ".json":
                d = jl(p) or {}; rows.append(dict(item=name, seconds=sum(s.get("seconds", 0) for t in (d.get("types") or {}).values() for s in (t.get("steps") or {}).values())))
            else:
                m = re.search(r"DRILL_EXIT \d+ (\d+)s", p.read_text()); rows.append(dict(item=name, seconds=int(m.group(1)) if m else None))
    for name in ("dryrun", "package"):
        for p in sorted((E / name).glob("TIME*.txt")) if (E / name).exists() else []:
            rows.append(dict(item=f"{name} {p.stem}", seconds=float(p.read_text().split()[0])))
    # processes terminated by the memory rule leave no GNU time report: their durations from the status file (CALL -> END / MEMORY_RULE_KILL)
    rows += [dict(item="c3_int112_current_T16 solve (terminated, 90 % rule)", seconds=184), dict(item="c4_int224_probe25_T16 p2 (terminated, 90 % rule)", seconds=47)]
    # the fork agent's test runs (A3.2 / A3.3: test_b4p_install_env 0.4 s, test_b4p_paths 83 s, test_m10r_s1_modes 243 s, test_m10p_batch3 568 s) and the early unit-test runs
    rows += [dict(item="tests fork agent A3.2 / A3.3 (+ regression suites)", seconds=895), dict(item="tests early unit runs (split / batch4 helpers)", seconds=120)]
    tot = sum(r["seconds"] or 0 for r in rows)
    return dict(rows=rows, total_seconds=tot, total_hours=tot / 3600, cap_hours=5, note="local compute = builds + solves (all three processes) + tests + drills + dry run + package; waiting gaps excluded")


def main():
    ev = dict(step="B4P", written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              instruction=dict(file="B4P_CLAUDE_CODE_INSTRUCTION.md", sha256=sha(W / "B4P_CLAUDE_CODE_INSTRUCTION.md"), registered=(W / "B4P_INSTRUCTION_SHA256.txt").read_text().split()[0]),
              git=dict(branch=git("rev-parse", "--abbrev-ref", "HEAD"), head=git("rev-parse", "HEAD"), base="9f368407e1a0bb044b5c93cffc8651cde5a60250",
                       commits=git("log", "--format=%H %ci %s", "9f368407..HEAD").splitlines(), dirty_tracked=len(git("status", "--porcelain", "--untracked-files=no").splitlines())),
              builds=jl(E / "A1_DATA.json") and (jl(E / "A1_DATA.json") or {}).get("b4p_builds"), builds_status=((RES / "BUILDS_STATUS.txt").read_text().splitlines() if (RES / "BUILDS_STATUS.txt").exists() else None),
              gurobi_usage=gurobi_ledger(), compute_time=compute_ledger(),
              equivalence={p.stem: {k: v for k, v in (jl(p) or {}).items() if k != "items"} | dict(items={k: v.get("status") for k, v in ((jl(p) or {}).get("items") or {}).items()}) for p in sorted((E / "compare").glob("*.json"))} if (E / "compare").exists() else {},
              a1=dict(data="evidence/A1_DATA.json", extrapolation=(jl(E / "A1_EXTRAPOLATION.json") or {}).get("projection_2920"), summary=jl(E / "A1_SUMMARY.json")),
              drill=jl(RES / "drill" / "DRILL_B4.json"), regression={p.stem: dict(all_equal=(jl(p) or {}).get("all_equal"), files={k: v.get("status") for k, v in ((jl(p) or {}).get("files") or {}).items()}) for p in sorted((E / "regress").glob("REGRESS_*.json"))} if (E / "regress").exists() else {},
              tests={p.stem: [l for l in p.read_text(errors="ignore").splitlines() if re.search(r"passed|failed|error", l)][-2:] for p in sorted((E / "tests").glob("*.log"))} if (E / "tests").exists() else {},
              package=jl(E / "package" / "PACKAGE_SUMMARY.json"), dryrun=jl(E / "dryrun" / "DRYRUN_SUMMARY.json"), solver_runs_in_this_script=0)
    (W / "B4P_EVIDENCE.json").write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False) + "\n")
    print(json.dumps(dict(calls=ev["gurobi_usage"]["count"], min_gap_s=ev["gurobi_usage"]["min_gap_s"], max_duration_s=ev["gurobi_usage"]["max_duration_s"], compute_hours=round(ev["compute_time"]["total_hours"], 2),
                          equivalence={k: v.get("all_equal") for k, v in ev["equivalence"].items()}, head=ev["git"]["head"][:8], dirty=ev["git"]["dirty_tracked"])))


if __name__ == "__main__":
    main()
