"""HPR checklist H-P3: the registered values of RUN_PLAN_HPC.md, scripts_project/b4_batch4.py, run_batch4.sh (R_*), preflight.sh (R_TL), the generated
PBS job scripts and hpr_job.sh (smoke constants) extracted and compared item by item. Prints a table and writes a JSON; exit 0 only when every row is
consistent. Read only; nothing is solved.

    python hpc/hpr_consistency.py --repo <repo root or unpacked code> --plan <RUN_PLAN_HPC.md> --runner <run_batch4.sh> --preflight <preflight.sh> --pbs <pbs dir> --job <hpr_job.sh> --out <json>

V3 HPC (RUN_PLAN_HPC_V3.md; BATCH_DEF set to the package definition): the runner and the preflight take the limits from b4_batch4.py hpc-plan and the reference iterations
from b4_batch4.py runmeta (single source), so their values are the b4_batch4.py values when they read them; the rows for jobs, dependencies, walltimes and reference
iterations are generated from the registered table (F1-F4, batch); the status of the limits (PROPOSED / REGISTERED) is compared with the plan.
"""
import argparse
import json
import os
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
    v3 = "BATCH_DEF" in os.environ
    reads_plan = v3 and "scripts_project/b4_batch4.py hpc-plan" in runner        # V3 HPC: the runner's limits are the b4_batch4.py values
    reads_meta = "runmeta" in runner and "ITERS[$1]" in runner                     # the runner's reference iterations are b4_batch4.py runmeta
    pre_reads_plan = v3 and "b4_batch4.py hpc-plan" in pre
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

    def num_in_plan(label_regex: str) -> str | None:
        m = re.search(label_regex, plan)
        return m.group(1).replace(",", "") if m else None

    def runner_default(name: str, rname: str):
        """the runner's default of NAME: a literal ${NAME:-123}, or ${NAME:-$R_X} with the literal R_X=123 (HPR line); with a definition the b4_batch4.py value"""
        m = re.search(name + r"=\$\{" + name + r":-(\d+)\}", runner)
        if m:
            return m.group(1)
        m = re.search(name + r"=\$\{" + name + r":-\$" + rname + r"\}", runner); r = re.search(r"\b" + rname + r"=(\d+)", runner)
        return r.group(1) if (m and r) else None

    rm = re.search(r"^R_TL=(\d+); R_WALL=(\d+); R_GAP=(\d+); R_MODE=(\w+)", runner, re.M)
    r_tl, r_wall, r_gap, r_mode = (int(rm.group(1)), int(rm.group(2)), int(rm.group(3)), rm.group(4)) if rm else (None, None, None, None)
    if reads_plan:
        r_tl, r_wall, r_gap = B.TIME_LIMIT_S, B.WALL_CAP_S, B.LICENCE_GAP_S
    pm = re.search(r"R_TL=(\d+)", pre); p_tl = (B.TIME_LIMIT_S if pre_reads_plan else (int(pm.group(1)) if pm else None))
    plan_tl = num_in_plan(r"`R_TL` / `TIME_LIMIT_S` \| \*\*([\d,]+)\*\*"); plan_wall = num_in_plan(r"`R_WALL` / `WALL_CAP_S` \| \*\*([\d,]+)\*\*")
    plan_gap = num_in_plan(r"运行器启动后首次 Gurobi 的间隔 \| ([\d,]+) \|"); plan_wmax = num_in_plan(r"`WAIT_START_MAX_S` \| ([\d,]+) \|")
    plan_b1 = num_in_plan(r"进程 1 超时 `BUILD_TIMEOUT_S` \| \*?\*?([\d,]+)\*?\*? \|"); plan_a3 = num_in_plan(r"进程 3 超时 `ASSIGN_TIMEOUT_S` \| ([\d,]+) \|")
    plan_post = num_in_plan(r"后处理单步超时 `POST_TIMEOUT_S` \| ([\d,]+) \|"); plan_pack = num_in_plan(r"打包超时 `PACK_TIMEOUT_S` \| ([\d,]+) \|")
    pbs_tl = {k: v["time_limit_s"] for k, v in pbs.items()}; pbs_wc = {k: v["wall_cap_s"] for k, v in pbs.items()}; pbs_gap = {k: v["gap_s"] for k, v in pbs.items()}
    rv = lambda name, rname, bval: (bval if reads_plan else runner_default(name, rname))
    row("TimeLimit s", dict(plan=plan_tl, b4_batch4=B.TIME_LIMIT_S, run_batch4=r_tl, preflight=p_tl, **{f"pbs_{k}": v for k, v in pbs_tl.items()}))
    row("process-2 wall cap s", dict(plan=plan_wall, b4_batch4=B.WALL_CAP_S, run_batch4=r_wall, **{f"pbs_{k}": v for k, v in pbs_wc.items()}))
    row("licence gap s", dict(plan=plan_gap, b4_batch4=B.LICENCE_GAP_S, run_batch4=r_gap, **{f"pbs_{k}": v for k, v in pbs_gap.items()}))
    row("solve mode", dict(plan="split" if "`SOLVE_MODE=split`" in plan else None, run_batch4=r_mode, hpr_job="split" if "SOLVE_MODE=split" in job else None))
    row("wait-start max s", dict(plan=plan_wmax, b4_batch4=B.WAIT_START_MAX_S, run_batch4=rv("WAIT_START_MAX_S", "R_WMAX", B.WAIT_START_MAX_S)))
    row("process-1 timeout s", dict(plan=plan_b1, b4_batch4=B.BUILD_TIMEOUT_S, run_batch4=rv("BUILD_TIMEOUT_S", "R_BUILD", B.BUILD_TIMEOUT_S)))
    row("process-3 timeout s", dict(plan=plan_a3, b4_batch4=B.ASSIGN_TIMEOUT_S, run_batch4=rv("ASSIGN_TIMEOUT_S", "R_ASSIGN", B.ASSIGN_TIMEOUT_S)))
    row("post step timeout s", dict(plan=plan_post, b4_batch4=B.POST_TIMEOUT_S, run_batch4=rv("POST_TIMEOUT_S", "R_POST", B.POST_TIMEOUT_S)))
    row("pack timeout s", dict(plan=plan_pack, b4_batch4=B.PACK_TIMEOUT_S, run_batch4=rv("PACK_TIMEOUT_S", "R_PACK", B.PACK_TIMEOUT_S)))
    row("post memory need GiB", dict(plan=num_in_plan(r"后处理并存内存条件 \| ([\d,]+) GiB"), b4_batch4=B.POST_MEM_NEED_GIB, run_batch4=(re.search(r"POST_MEM_NEED_GIB=\$\{POST_MEM_NEED_GIB:-(\d+)\}", runner) or [None, None])[1]))
    row("memory stop fraction", dict(plan=num_in_plan(r"内存止损分数 \| ([\d.]+) \|"), b4_batch4=B.MEMORY_STOP_FRACTION, run_batch4=(re.search(r"MEMORY_STOP_FRACTION=\$\{MEMORY_STOP_FRACTION:-([\d.]+)\}", runner) or [None, None])[1]))
    it = re.search(r"早期测速分数 / 迭代参考[^|]*\| ([\d.]+) / ([\d,、]+) \|", plan)
    row("projection fraction", dict(plan=it.group(1) if it else None, b4_batch4=B.PROJECTION_FRACTION, run_batch4=(re.search(r"PROJECTION_FRACTION=\$\{PROJECTION_FRACTION:-([\d.]+)\}", runner) or [None, None])[1]))
    plan_it = it.group(2).replace(",", "").split("、") if it else []
    for i, rid in enumerate(B.RUNS):
        lit = (re.search(rid + r"\) echo (\d+);;", runner) or [None, None])[1]
        row(f"iterations reference {rid}", dict(plan=plan_it[i] if i < len(plan_it) else None, b4_batch4=B.RUNS[rid]["iterations_reference"],
                                                run_batch4=(B.RUNS[rid]["iterations_reference"] if reads_meta else lit)))
    # PBS resources per job: plan table (section 10) vs b4_batch4 HPC_JOBS vs generated scripts
    labels = {"F1": "PBS F1", "F2": "PBS F2", "F3": "PBS F3", "F4": "PBS F4", "batch": "PBS 批级", "smoke56": "PBS 冒烟", "build_only_f1": "PBS BUILD_ONLY", "install": "PBS 安装"}
    for key, j in B.HPC_JOBS.items():
        m = re.search(re.escape(labels.get(key, key)) + r" \| (\w+) / (\d+) / (\d+)gb / ([\d:]+) \|", plan)
        p = pbs.get(key, {})
        row(f"{key}: queue / ncpus / mem / walltime", dict(plan=f"{m.group(1)}/{m.group(2)}/{m.group(3)}/{m.group(4)}" if m else None,
                                                             b4_batch4=f"{j['queue']}/{j['ncpus']}/{j['mem_gb']}/{j['walltime']}",
                                                             pbs=f"{p.get('queue')}/{p.get('ncpus')}/{p.get('mem_gb')}/{p.get('walltime')}" if p else None))
    formal = [k for k, j in B.HPC_JOBS.items() if j["mode"] == "formal"]
    for k in formal:
        row(f"{k} walltime s", dict(plan=num_in_plan(r"\*\*PBS walltime " + re.escape(k) + r"\*\* \| \*\*([\d,]+)\*\*"), b4_batch4=B.walltime_s(B.HPC_JOBS[k]["walltime"]),
                                     pbs=B.walltime_s(pbs[k]["walltime"]) if pbs.get(k) else None))
    for k, j in B.HPC_JOBS.items():
        if j.get("wait_start_of"):
            row(f"{k} wait_start_of", dict(plan=j["wait_start_of"] if f"`WAIT_START_OF={j['wait_start_of']}`" in plan else None, b4_batch4=j["wait_start_of"], pbs=pbs.get(k, {}).get("wait_start_of")))
        if j.get("depends") and j["mode"] in ("formal", "batch"):
            t, *ks = j["depends"].split(":")
            pat = r"depend=" + re.escape(t) + ":" + ":".join(r"<" + re.escape(x) + r"[^>]*>" for x in ks)
            row(f"{k} dependency", dict(plan=j["depends"] if re.search(pat, plan) else None, b4_batch4=j["depends"], pbs=pbs.get(k, {}).get("depends")))
    for k, v in B.REGISTERED_SHA.items():
        sc = k[: -len("_2920_3h_unsolved.nc")] if k.endswith("_2920_3h_unsolved.nc") else k.split("_")[0]
        row(f"network SHA256 {sc}", dict(plan=v if v in plan else None, b4_batch4=v))
        row(f"network bytes {sc}", dict(plan=str(B.REGISTERED_BYTES[k]) if f"{B.REGISTERED_BYTES[k]:,}" in plan else None, b4_batch4=B.REGISTERED_BYTES[k]))
    row("runner / preflight check the networks with b4_batch4.py base-check (= the registered SHA256 / bytes)", dict(run_batch4=str("base-check" in runner), preflight=str("base-check" in pre), expected="True"))
    row("build commit", dict(plan=B.BUILD_COMMIT if B.BUILD_COMMIT in plan else None, b4_batch4=B.BUILD_COMMIT, preflight_code_section=(None if v3 else (B.BUILD_COMMIT if B.BUILD_COMMIT[:8] in pre else None))))
    sm = re.search(r"TRUNCATE=56 ALLOW_UNREGISTERED=1 GUROBI_TIME_LIMIT_S=(\d+) WALL_CAP_S=(\d+)", job)
    row("smoke TimeLimit / wall cap s", dict(plan=f"{B.SMOKE['time_limit_s']}/{B.SMOKE['wall_cap_s']}" if "`TRUNCATE=56 ALLOW_UNREGISTERED=1 GUROBI_TIME_LIMIT_S=3000 WALL_CAP_S=3600`" in plan else None,
                                              b4_batch4=f"{B.SMOKE['time_limit_s']}/{B.SMOKE['wall_cap_s']}", hpr_job=f"{sm.group(1)}/{sm.group(2)}" if sm else None))
    wc = B.walltime_components()
    for k, v in wc["per_job"].items():
        row(f"{k} walltime >= sum of terms", dict(check=str(v["registered_s"] >= v["sum_s"]), expected="True"))
        if v3:   # V3 HPC (RUN_PLAN_HPC_V3.md 14, decided 2026-11-04): every formal job keeps >= 2 h above the sum of its terms
            row(f"{k} walltime margin >= 7,200 s", dict(check=str(v["margin_s"] >= 7200), expected="True"))
    two = sorted((B.HPC_JOBS[k]["ncpus"] for k in formal), reverse=True)[:2]   # at most two formal jobs at a time (v2: F1 + F2; V3: F1 / F3 and F2 / F4 chained)
    row("queue limits (parallel <= 540 GB, <= 96 cores, <= 720 h; two formal jobs together <= 96 cores)",
        dict(check=str(all(j["mem_gb"] <= B.QUEUE_LIMITS[j["queue"]]["mem_gb"] and j["ncpus"] <= B.QUEUE_LIMITS[j["queue"]]["ncpus_max"] and B.walltime_s(j["walltime"]) <= B.QUEUE_LIMITS[j["queue"]]["walltime_h"] * 3600 for j in B.HPC_JOBS.values())
                       and sum(two) <= B.QUEUE_LIMITS["parallel"]["user_cores"]), expected="True"))
    hp = {r: v for r, v in B.B4P_HIGH_PEAK_GIB.items() if r in B.HPC_JOBS}
    row(f"memory >= 1.25 x high estimate ({', '.join(f'{r} {v:g}' for r, v in hp.items())} GiB)", dict(check=str(all(B.HPC_JOBS[r]["mem_gb"] >= 1.25 * v for r, v in hp.items())), expected="True"))
    if v3:
        st = re.search(r"登记状态 \| \*\*(\w+)\*\*", plan)
        row("limits status (PROPOSED until the reviewer and the user register the values)", dict(plan=st.group(1) if st else None, b4_batch4=B.LIMITS_STATUS))
        row("pairs (integrated / reference)", dict(plan=";".join(f"{p}:{i}/{d}" for p, (i, d) in B.pairs().items()) if all(f"{i} / {d}" in plan for i, d in B.pairs().values()) else None,
                                                    b4_batch4=";".join(f"{p}:{i}/{d}" for p, (i, d) in B.pairs().items())))
        row("every run stops the batch (G2 / no solution / C1 (a))", dict(check=str(set(B.STOP_ALWAYS) == set(B.RUNS)), expected="True"))
    res = dict(script="hpc/hpr_consistency.py", written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), rows=rows, all_consistent=all(r["consistent"] for r in rows), walltime_components=wc,
               batch_def=os.environ.get("BATCH_DEF"), sources=dict(plan=str(a.plan), runner=str(a.runner), preflight=str(a.preflight), pbs=str(a.pbs), job=str(a.job)))
    a.out.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
    w = max(len(r["item"]) for r in rows)
    for r in rows:
        print(f"{'OK ' if r['consistent'] else 'XX '} {r['item']:<{w}}  " + "  ".join(f"{k}={v}" for k, v in r["values"].items()))
    print("ALL_CONSISTENT" if res["all_consistent"] else "INCONSISTENT")
    sys.exit(0 if res["all_consistent"] else 1)


if __name__ == "__main__":
    main()
