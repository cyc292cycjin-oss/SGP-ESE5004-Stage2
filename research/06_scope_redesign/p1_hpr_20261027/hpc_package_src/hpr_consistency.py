"""HPR checklist H-P3: the registered values of RUN_PLAN_HPC.md, scripts_project/b4_batch4.py, run_batch4.sh (R_*), preflight.sh (R_TL), the generated
PBS job scripts and hpr_job.sh (smoke constants) extracted and compared item by item. Prints a table and writes a JSON; exit 0 only when every row is
consistent. Read only; nothing is solved.

    python hpc/hpr_consistency.py --repo <repo root or unpacked code> --plan <RUN_PLAN_HPC.md> --runner <run_batch4.sh> --preflight <preflight.sh> --pbs <pbs dir> --job <hpr_job.sh> --out <json>
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path


def pbs_values(pbs_dir: Path) -> dict:
    out = {}
    for f in sorted(pbs_dir.glob("*.pbs")):
        t = f.read_text(); m = {}
        q = re.search(r"^#PBS -q (\S+)", t, re.M); sel = re.search(r"^#PBS -l select=1:ncpus=(\d+):mem=(\d+)gb", t, re.M); w = re.search(r"^#PBS -l walltime=(\S+)", t, re.M)
        ex = re.search(r"^export (JOB_.*)$", t, re.M)
        kv = dict(x.split("=", 1) for x in ex.group(1).split() if "=" in x) if ex else {}
        m.update(queue=q.group(1) if q else None, ncpus=int(sel.group(1)) if sel else None, mem_gb=int(sel.group(2)) if sel else None, walltime=w.group(1) if w else None,
                 mode=kv.get("JOB_MODE"), rid=kv.get("JOB_RID"), time_limit_s=int(kv["JOB_TIME_LIMIT_S"]) if kv.get("JOB_TIME_LIMIT_S") else None,
                 wall_cap_s=int(kv["JOB_WALL_CAP_S"]) if kv.get("JOB_WALL_CAP_S") else None, gap_s=int(kv["JOB_LICENCE_GAP_S"]) if kv.get("JOB_LICENCE_GAP_S") else None,
                 wait_start_of=kv.get("JOB_WAIT_START_OF", ""), depends=kv.get("JOB_DEPENDS", ""))
        out[kv.get("JOB_KEY", f.stem)] = m
    return out


def main():
    ap = argparse.ArgumentParser()
    for k in ("repo", "plan", "runner", "preflight", "pbs", "job", "out"):
        ap.add_argument(f"--{k}", type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project")); import b4_batch4 as B   # noqa: E402
    plan = a.plan.read_text(); runner = a.runner.read_text(); pre = a.preflight.read_text(); job = a.job.read_text(); pbs = pbs_values(a.pbs)
    rows = []

    def norm(v):
        s = str(v).strip()
        try:
            return repr(float(s))   # 0.80 == 0.8, 864000 == 864000.0
        except ValueError:
            return s

    def row(item, values: dict):
        vals = [v for v in values.values() if v is not None]
        ok = len(vals) > 0 and all(norm(v) == norm(vals[0]) for v in vals)
        rows.append(dict(item=item, values={k: (None if v is None else str(v)) for k, v in values.items()}, consistent=ok))

    def num_in_plan(label_regex: str, pattern: str = r"\*?\*?([\d,]+)\*?\*?") -> str | None:
        m = re.search(label_regex, plan)
        return m.group(1).replace(",", "") if m else None

    rm = re.search(r"^R_TL=(\d+); R_WALL=(\d+); R_GAP=(\d+); R_MODE=(\w+)", runner, re.M)
    r_tl, r_wall, r_gap, r_mode = (int(rm.group(1)), int(rm.group(2)), int(rm.group(3)), rm.group(4)) if rm else (None, None, None, None)
    pm = re.search(r"R_TL=(\d+)", pre); p_tl = int(pm.group(1)) if pm else None
    plan_tl = num_in_plan(r"`R_TL` / `TIME_LIMIT_S` \| \*\*([\d,]+)\*\*"); plan_wall = num_in_plan(r"`R_WALL` / `WALL_CAP_S` \| \*\*([\d,]+)\*\*")
    plan_gap = num_in_plan(r"运行器启动后首次 Gurobi 的间隔 \| ([\d,]+) \|"); plan_wmax = num_in_plan(r"`WAIT_START_MAX_S` \| ([\d,]+) \|")
    plan_b1 = num_in_plan(r"进程 1 超时 `BUILD_TIMEOUT_S` \| ([\d,]+) \|"); plan_a3 = num_in_plan(r"进程 3 超时 `ASSIGN_TIMEOUT_S` \| ([\d,]+) \|")
    plan_post = num_in_plan(r"后处理单步超时 `POST_TIMEOUT_S` \| ([\d,]+) \|"); plan_pack = num_in_plan(r"打包超时 `PACK_TIMEOUT_S` \| ([\d,]+) \|")
    plan_wf1 = num_in_plan(r"\*\*PBS walltime F1\*\* \| \*\*([\d,]+)\*\*"); plan_wf2 = num_in_plan(r"\*\*PBS walltime F2\*\* \| \*\*([\d,]+)\*\*")
    pbs_tl = {k: v["time_limit_s"] for k, v in pbs.items()}; pbs_wc = {k: v["wall_cap_s"] for k, v in pbs.items()}; pbs_gap = {k: v["gap_s"] for k, v in pbs.items()}
    row("TimeLimit s", dict(plan=plan_tl, b4_batch4=B.TIME_LIMIT_S, run_batch4=r_tl, preflight=p_tl, **{f"pbs_{k}": v for k, v in pbs_tl.items()}))
    row("process-2 wall cap s", dict(plan=plan_wall, b4_batch4=B.WALL_CAP_S, run_batch4=r_wall, **{f"pbs_{k}": v for k, v in pbs_wc.items()}))
    row("licence gap s", dict(plan=plan_gap, b4_batch4=B.LICENCE_GAP_S, run_batch4=r_gap, **{f"pbs_{k}": v for k, v in pbs_gap.items()}))
    row("solve mode", dict(plan="split" if "`SOLVE_MODE=split`" in plan else None, run_batch4=r_mode, hpr_job="split" if "SOLVE_MODE=split" in job else None))
    row("wait-start max s", dict(plan=plan_wmax, b4_batch4=B.WAIT_START_MAX_S, run_batch4=(re.search(r"WAIT_START_MAX_S=\$\{WAIT_START_MAX_S:-(\d+)\}", runner) or [None, None])[1]))
    row("process-1 timeout s", dict(plan=plan_b1, b4_batch4=B.BUILD_TIMEOUT_S, run_batch4=(re.search(r"BUILD_TIMEOUT_S=\$\{BUILD_TIMEOUT_S:-(\d+)\}", runner) or [None, None])[1]))
    row("process-3 timeout s", dict(plan=plan_a3, b4_batch4=B.ASSIGN_TIMEOUT_S, run_batch4=(re.search(r"ASSIGN_TIMEOUT_S=\$\{ASSIGN_TIMEOUT_S:-(\d+)\}", runner) or [None, None])[1]))
    row("post step timeout s", dict(plan=plan_post, b4_batch4=B.POST_TIMEOUT_S, run_batch4=(re.search(r"POST_TIMEOUT_S=\$\{POST_TIMEOUT_S:-(\d+)\}", runner) or [None, None])[1]))
    row("pack timeout s", dict(plan=plan_pack, b4_batch4=B.PACK_TIMEOUT_S, run_batch4=(re.search(r"PACK_TIMEOUT_S=\$\{PACK_TIMEOUT_S:-(\d+)\}", runner) or [None, None])[1]))
    row("post memory need GiB", dict(plan=num_in_plan(r"后处理并存内存条件 \| ([\d,]+) GiB"), b4_batch4=B.POST_MEM_NEED_GIB, run_batch4=(re.search(r"POST_MEM_NEED_GIB=\$\{POST_MEM_NEED_GIB:-(\d+)\}", runner) or [None, None])[1]))
    row("memory stop fraction", dict(plan=num_in_plan(r"内存止损分数 \| ([\d.]+) \|", r"([\d.]+)"), b4_batch4=B.MEMORY_STOP_FRACTION, run_batch4=(re.search(r"MEMORY_STOP_FRACTION=\$\{MEMORY_STOP_FRACTION:-([\d.]+)\}", runner) or [None, None])[1]))
    row("projection fraction", dict(plan=(re.search(r"早期测速分数 / 迭代参考 \| ([\d.]+) / ", plan) or [None, None])[1], b4_batch4=B.PROJECTION_FRACTION, run_batch4=(re.search(r"PROJECTION_FRACTION=\$\{PROJECTION_FRACTION:-([\d.]+)\}", runner) or [None, None])[1]))
    it = re.search(r"早期测速分数 / 迭代参考 \| [\d.]+ / ([\d,]+)、([\d,]+) \|", plan)
    row("iterations reference F1", dict(plan=it.group(1) if it else None, b4_batch4=B.RUNS["F1"]["iterations_reference"], run_batch4=(re.search(r"F1\) echo (\d+);;", runner) or [None, None])[1]))
    row("iterations reference F2", dict(plan=it.group(2) if it else None, b4_batch4=B.RUNS["F2"]["iterations_reference"], run_batch4=(re.search(r"F2\) echo (\d+);;", runner) or [None, None])[1]))
    # PBS resources per job: plan table (section 10) vs b4_batch4 HPC_JOBS vs generated scripts
    for key, j in B.HPC_JOBS.items():
        label = {"F1": "PBS F1", "F2": "PBS F2", "batch": "PBS 批级", "smoke56": "PBS 冒烟", "build_only_f1": "PBS BUILD_ONLY", "install": "PBS 安装"}[key]
        m = re.search(re.escape(label) + r" \| (\w+) / (\d+) / (\d+)gb / ([\d:]+) \|", plan)
        p = pbs.get(key, {})
        row(f"{key}: queue / ncpus / mem / walltime", dict(plan=f"{m.group(1)}/{m.group(2)}/{m.group(3)}/{m.group(4)}" if m else None,
                                                             b4_batch4=f"{j['queue']}/{j['ncpus']}/{j['mem_gb']}/{j['walltime']}",
                                                             pbs=f"{p.get('queue')}/{p.get('ncpus')}/{p.get('mem_gb')}/{p.get('walltime')}" if p else None))
    row("F1 walltime s", dict(plan=plan_wf1, b4_batch4=B.walltime_s(B.HPC_JOBS["F1"]["walltime"]), pbs=B.walltime_s(pbs["F1"]["walltime"]) if pbs.get("F1") else None))
    row("F2 walltime s", dict(plan=plan_wf2, b4_batch4=B.walltime_s(B.HPC_JOBS["F2"]["walltime"]), pbs=B.walltime_s(pbs["F2"]["walltime"]) if pbs.get("F2") else None))
    row("F2 wait_start_of", dict(plan="F1" if "`WAIT_START_OF=F1`" in plan else None, b4_batch4=B.HPC_JOBS["F2"]["wait_start_of"], pbs=pbs.get("F2", {}).get("wait_start_of")))
    row("F2 dependency", dict(plan="after:F1" if "depend=after:<F1" in plan else None, b4_batch4=B.HPC_JOBS["F2"]["depends"], pbs=pbs.get("F2", {}).get("depends")))
    row("batch dependency", dict(plan="afterany:F1:F2" if "depend=afterany:<F1>:<F2>" in plan else None, b4_batch4=B.HPC_JOBS["batch"]["depends"], pbs=pbs.get("batch", {}).get("depends")))
    for k, v in B.REGISTERED_SHA.items():
        sc = k.split("_")[0]
        row(f"network SHA256 {sc}", dict(plan=v if v in plan else None, b4_batch4=v))
        row(f"network bytes {sc}", dict(plan=str(B.REGISTERED_BYTES[k]) if f"{B.REGISTERED_BYTES[k]:,}" in plan else None, b4_batch4=B.REGISTERED_BYTES[k]))
    row("runner / preflight check the networks with b4_batch4.py base-check (= the registered SHA256 / bytes)", dict(run_batch4=str("base-check" in runner), preflight=str("base-check" in pre), expected="True"))
    row("build commit", dict(plan=B.BUILD_COMMIT if B.BUILD_COMMIT in plan else None, b4_batch4=B.BUILD_COMMIT, preflight_code_section=B.BUILD_COMMIT if B.BUILD_COMMIT[:8] in pre else None))
    sm = re.search(r"TRUNCATE=56 ALLOW_UNREGISTERED=1 GUROBI_TIME_LIMIT_S=(\d+) WALL_CAP_S=(\d+)", job)
    row("smoke TimeLimit / wall cap s", dict(plan=f"{B.SMOKE['time_limit_s']}/{B.SMOKE['wall_cap_s']}" if "`TRUNCATE=56 ALLOW_UNREGISTERED=1 GUROBI_TIME_LIMIT_S=3000 WALL_CAP_S=3600`" in plan else None,
                                              b4_batch4=f"{B.SMOKE['time_limit_s']}/{B.SMOKE['wall_cap_s']}", hpr_job=f"{sm.group(1)}/{sm.group(2)}" if sm else None))
    wc = B.walltime_components()
    row("F1 walltime >= sum of terms", dict(check=str(wc["registered_f1_s"] >= wc["sum_f1_s"]), expected="True"))
    row("F2 walltime >= sum of terms", dict(check=str(wc["registered_f2_s"] >= wc["sum_f2_s"]), expected="True"))
    row("queue limits (parallel <= 540 GB, <= 96 cores, <= 720 h; F1 + F2 <= 96 cores)",
        dict(check=str(all(j["mem_gb"] <= B.QUEUE_LIMITS[j["queue"]]["mem_gb"] and j["ncpus"] <= B.QUEUE_LIMITS[j["queue"]]["ncpus_max"] and B.walltime_s(j["walltime"]) <= B.QUEUE_LIMITS[j["queue"]]["walltime_h"] * 3600 for j in B.HPC_JOBS.values())
                       and B.HPC_JOBS["F1"]["ncpus"] + B.HPC_JOBS["F2"]["ncpus"] <= B.QUEUE_LIMITS["parallel"]["user_cores"]), expected="True"))
    row("memory >= 1.25 x B4P high estimate (F1 160, F2 149 GiB)", dict(check=str(all(B.HPC_JOBS[r]["mem_gb"] >= 1.25 * B.B4P_HIGH_PEAK_GIB[r] for r in ("F1", "F2"))), expected="True"))
    res = dict(script="hpc/hpr_consistency.py", written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), rows=rows, all_consistent=all(r["consistent"] for r in rows), walltime_components=wc,
               sources=dict(plan=str(a.plan), runner=str(a.runner), preflight=str(a.preflight), pbs=str(a.pbs), job=str(a.job)))
    a.out.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
    w = max(len(r["item"]) for r in rows)
    for r in rows:
        print(f"{'OK ' if r['consistent'] else 'XX '} {r['item']:<{w}}  " + "  ".join(f"{k}={v}" for k, v in r["values"].items()))
    print("ALL_CONSISTENT" if res["all_consistent"] else "INCONSISTENT")
    sys.exit(0 if res["all_consistent"] else 1)


if __name__ == "__main__":
    main()
