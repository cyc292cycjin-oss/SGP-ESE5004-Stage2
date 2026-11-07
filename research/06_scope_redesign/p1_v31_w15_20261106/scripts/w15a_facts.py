"""V31 W15 stage A, sections 1.3 and 2: per-run receipt checks and run facts of the v3.1 2920x3h interim exports (read only; no solver).

  python -I w15a_facts.py --exp <hpc_results_v31/interim_unpacked/export> --pkg <hpc_package_v3_1> --out <work/p1_v31_w15_20261106>

Writes RUN_FACTS.csv, evidence/INTEGRITY_RUNS.json, evidence/RUN_FACTS.json. HPC paths are scrubbed (user and node names never written).
"""
import argparse, csv, json, re, statistics
from datetime import datetime, timezone
from pathlib import Path

SCRUB = [(re.compile(r"/hpctmp/[^/\s\"']+"), "/hpctmp/<user>"), (re.compile(r"/home/svu/[^/\s\"']+"), "/home/svu/<user>"),
         (re.compile(r"cnode[-0-9]+"), "<node>")]
# hpr_status facts quoted in the instruction (section 0); F4 is not quoted there
HPR_STATUS = {"F1": dict(termination="OPTIMAL", barrier_iterations=244, objective_eur=302682094040.97, post_exit=0),
              "F2": dict(termination="OPTIMAL", barrier_iterations=153, objective_eur=314487796437.50, post_exit=0)}
# RUN_PLAN_V3.md section 24.1: v3 LP size extrapolated by snapshots (same method matched D2 exactly on columns and rows); v3.1 adds 82 x 2920 - 1 rows
V3_LP = {"integrated": dict(cols=37480004, rows=82955300), "no_new_xb": dict(cols=36384650, rows=80501958)}
V31_EXTRA_ROWS = 82 * 2920 - 1


def scrub(s: str) -> str:
    for p, r in SCRUB:
        s = p.sub(r, s)
    return s


def jl(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def utc(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def gurobi_log(p: Path) -> dict:
    t = p.read_text(encoding="utf-8", errors="replace").splitlines()
    out = dict(iterations=[])
    it = re.compile(r"^\s*(\d+)\s+([-+0-9.e]+)\s+([-+0-9.e]+)\s+([-+0-9.e]+)\s+([-+0-9.e]+)\s+([-+0-9.e]+)\s+(\d+)s\s*$")
    for line in t:
        m = it.match(line)
        if m:
            out["iterations"].append(dict(iter=int(m[1]), primal=float(m[2]), dual=float(m[3]), pres=float(m[4]), dres=float(m[5]), compl=float(m[6]), t=int(m[7])))
        if line.startswith("CPU model:"):
            out["cpu"] = line.split(":", 1)[1].strip()
        if line.startswith("Thread count:"):
            out["threads_line"] = line.split(":", 1)[1].strip()
        if line.startswith("Gurobi Optimizer version"):
            out["gurobi_version"] = line.split("version", 1)[1].split("build")[0].strip()
        m = re.match(r"Presolve time: ([0-9.]+)s", line)
        if m: out["presolve_s"] = float(m[1])
        m = re.match(r"Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros", line)
        if m: out["presolved"] = dict(rows=int(m[1]), cols=int(m[2]), nnz=int(m[3]))
        m = re.match(r"Ordering time: ([0-9.]+)s", line)
        if m: out["ordering_s"] = float(m[1])
        m = re.match(r"\s*Dense cols : (\d+)", line)
        if m: out["dense_cols"] = int(m[1])
        m = re.match(r"\s*Factor NZ\s*: ([0-9.e+]+)", line)
        if m: out["factor_nz"] = float(m[1])
        m = re.match(r"\s*Factor Ops\s*: ([0-9.e+]+)", line)
        if m: out["factor_ops"] = float(m[1])
        m = re.match(r"Barrier solved model in (\d+) iterations and ([0-9.]+) seconds \(([0-9.]+) work units\)", line)
        if m: out["barrier_line"] = dict(iterations=int(m[1]), seconds=float(m[2]), work_units=float(m[3]))
        m = re.match(r"Optimal objective\s+([-+0-9.e]+)", line)
        if m: out["optimal_objective_line"] = float(m[1])
        m = re.match(r"Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros", line)
        if m: out["model"] = dict(rows=int(m[1]), cols=int(m[2]), nnz=int(m[3]))
    its = out["iterations"]
    if its:
        first, last = its[0], its[-1]
        out["iter0_time_s"] = first["t"]
        out["last_iter"] = last
        out["last_rel_gap_log"] = abs(last["primal"] - last["dual"]) / abs(last["primal"])
        n = last["iter"] - first["iter"]
        out["mean_s_per_iter"] = (last["t"] - first["t"]) / n if n else None
        tail = [b["t"] - a["t"] for a, b in zip(its[-11:-1], its[-10:])]
        out["mean_s_per_iter_last10"] = statistics.mean(tail) if tail else None
    return out


def time_v(p: Path) -> dict:
    out = {}
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("Elapsed (wall clock) time"):
            v = line.rsplit(": ", 1)[1]; parts = [float(x) for x in v.split(":")]
            out["wall_s"] = parts[0] * 3600 + parts[1] * 60 + parts[2] if len(parts) == 3 else parts[0] * 60 + parts[1]
        elif line.startswith("Maximum resident set size"):
            out["max_rss_kb"] = int(line.rsplit(": ", 1)[1])
        elif line.startswith("User time"):
            out["user_s"] = float(line.rsplit(": ", 1)[1])
        elif line.startswith("System time"):
            out["sys_s"] = float(line.rsplit(": ", 1)[1])
        elif line.startswith("Percent of CPU"):
            out["cpu_pct"] = line.rsplit(": ", 1)[1]
        elif line.startswith("Exit status"):
            out["exit_status"] = int(line.rsplit(": ", 1)[1])
    return out


def resource_phases(p: Path) -> dict:
    """RESOURCE.jsonl of s2_solve.py: process 1 (build) and process 3 (assign) samples, separated by the process-2 gap."""
    rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    e = [r["epoch"] for r in rows]
    gaps = [(e[i + 1] - e[i], i) for i in range(len(e) - 1)]
    g, i = max(gaps)
    p1, p3 = rows[: i + 1], rows[i + 1:]
    return dict(p1_start=p1[0]["epoch"], p1_end=p1[-1]["epoch"], p1_peak_rss_b=max(r["rss"] for r in p1),
                p3_start=p3[0]["epoch"], p3_end=p3[-1]["epoch"], p3_peak_rss_b=max(r["rss"] for r in p3), gap_s=g)


def monitor(p: Path) -> dict:
    if not p.exists():
        return {}
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    f = lambda k: max(float(r[k]) for r in rows if r.get(k) not in (None, ""))
    return dict(samples=len(rows), first_utc=rows[0]["utc"], last_utc=rows[-1]["utc"], rss_group_peak_gib=f("rss_gib_group"),
                cgroup_used_peak_gib=f("cgroup_mem_used_gib"), cgroup_anon_peak_gib=f("cgroup_anon_gib"), cgroup_limit_gib=f("cgroup_mem_limit_gib"),
                host_available_min_gib=min(float(r["host_mem_available_gib"]) for r in rows))


def last_json_line(p: Path):
    if not p.exists():
        return None
    for line in reversed(p.read_text(encoding="utf-8", errors="replace").splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


def nodal_bunker_row(p: Path) -> dict:
    with p.open(encoding="utf-8") as f:
        r = csv.reader(f); head = next(r)
        for row in r:
            if row and row[0] == "co2 bunkers ASEAN":
                d = dict(zip(head, row))
                vals = [v for k, v in d.items() if k not in (head[0], "note")]
                return dict(present=True, values_all_nan=all(v in ("", "nan", "NaN") for v in vals), note_present=bool(d.get("note")))
    return dict(present=False)


def run(rid: str, d: Path, bdef: dict, commit: str) -> tuple[dict, dict]:
    R = jl(d / "RUN.json"); S = jl(d / "SOLVE_RECEIPT.json"); SS = jl(d / "split" / "SPLIT_SOLVE.json"); SB = jl(d / "split" / "SPLIT_BUILD.json")
    V = jl(d / "VIOLATIONS.json"); A = jl(d / "V6_ACCEPTANCE.json"); P = jl(d / "PRECISION.json"); K = jl(d / "kkt_summary.json")
    # stage B (batch result pack): V6_ACCEPTANCE.json is the final label after the batch regrade, V6_ACCEPTANCE_PROVISIONAL.json the provisional one
    AP = jl(d / "V6_ACCEPTANCE_PROVISIONAL.json"); final_pack = AP is not None
    if final_pack:
        A, A_final = AP, A
    else:
        A_final = None
    AL = jl(d / "ALLOCATION.json"); RA = jl(d / "m12_owen" / "RHS_AUDIT.json"); OW = jl(d / "m12_owen" / "OWEN.json"); PJ = jl(d / f"PROJECTION_{rid}.json")
    G = gurobi_log(d / "GUROBI_LOG_SCRUBBED.txt"); T2 = time_v(d / "p2_time.txt"); RP = resource_phases(d / "RESOURCE.jsonl"); M = monitor(d / f"MONITOR_{rid}.csv")
    P1 = last_json_line(d / "p1_log_scrubbed.txt") or {}; P3 = last_json_line(d / "p3_log_scrubbed.txt") or {}
    defn = bdef["runs"][rid]; net_file = defn["base"] + "_unsolved.nc"; reg = bdef["registered_sha"][net_file]
    sc = R["scenario"]; lp = S["lp"]
    integ = dict(
        rid=rid, scenario=sc, network_file=net_file,
        run_json_network_sha256=R["network_sha256"], run_json_registered_sha256=R["registered_sha256"], batch_def_registered_sha=reg,
        network_sha_equal=(R["network_sha256"] == reg == R["registered_sha256"] == S["input_network"]["sha256"] == SB["input_network_sha256"]),
        profile=R["profile"], profile_ok=(R["profile"] == defn["profile"] == "formal_barrier_1e6_t16" == S["solver_profile"]),
        solver_parameters=SS["solver_parameters"],
        code_commit_in_export=None,
        code_commit_note=("no export file records the code commit (RUN.json, SOLVE_RECEIPT.json, split receipts, logs searched); "
                          f"package COMMIT = {commit}; indirect evidence below"),
        indirect_code_evidence=dict(
            code_path=scrub(open(d / "p2_time.txt", encoding="utf-8").read().split("python ", 1)[1].split(" --run-dir")[0]) if (d / "p2_time.txt").exists() else None,
            lp_cols=lp["num_col"], lp_rows=lp["num_row"], v3_predicted_cols=V3_LP[sc]["cols"], v3_predicted_rows=V3_LP[sc]["rows"],
            lp_cols_equal_v3=lp["num_col"] == V3_LP[sc]["cols"], lp_rows_minus_v3=lp["num_row"] - V3_LP[sc]["rows"], v31_extra_rows_expected=V31_EXTRA_ROWS,
            lp_rows_match_v31=(lp["num_row"] - V3_LP[sc]["rows"]) == V31_EXTRA_ROWS,
            nodal_prices_bunker_row=nodal_bunker_row(d / "NODAL_PRICES.csv"),
            research_bunker_row_in_lp="research_bunker_co2_limit" in lp.get("research_constraints", [])),
        solve_receipt=dict(status=S["status"], termination=S["termination_condition"], decision=S["decision"], retry=S["retry"], optimize_calls=S["optimize_calls"],
                           post_solve_complete=S["post_solve_complete"], gurobi_status=S["split"]["gurobi_status_name"], sol_count=S["split"]["sol_count"],
                           p3_post_solve_errors=P3.get("post_solve_errors")),
        violations=dict(termination=V["termination"], rows_over_budget=V["totals"]["rows_over_budget"], columns_over_budget=V["totals"]["columns_over_budget"],
                        row_violation_max=V["totals"]["row_violation_max"], row_max_ratio_to_budget=V["totals"]["row_max_ratio_to_budget"],
                        first_order_cost_eur=V["totals"]["first_order_cost_eur"], rows_without_group=V["label_check"]["rows_without_group"]),
        v6_provisional=dict(file=("V6_ACCEPTANCE_PROVISIONAL.json" if final_pack else "V6_ACCEPTANCE.json (copied to V6_ACCEPTANCE_PROVISIONAL.json only by the batch regrade, run_batch4.sh:524)"),
                            label=A["label"], resolution=A["resolution"], profile=A["profile"], G1=dict(a=A["G1"]["a"], b=A["G1"]["b"], c=A["G1"]["c"]),
                            G1_reference=A["G1"]["reference"][:60], G2=all(A["G2"][k]["passed"] for k in ("G2_1", "G2_2", "G2_3")), solver_runs=A["solver_runs"]),
        v6_final=(dict(file="V6_ACCEPTANCE.json", label=A_final["label"], G1=dict(a=A_final["G1"]["a"], b=A_final["G1"]["b"], c=A_final["G1"]["c"]),
                       G1_reference=scrub(str(A_final["G1"]["reference"]))[:80], G2=all(A_final["G2"][k]["passed"] for k in ("G2_1", "G2_2", "G2_3")))
                  if A_final else None),
        c1=dict(grade=P["grade"]["grade"], a=P["acceptance"]["a"], b=P["acceptance"]["b"], c=P["acceptance"]["c"], optimal=P["acceptance"]["optimal"],
                reference=P["reference"]["source"][:60]),
        postprocessing_outputs=dict(violations=V is not None, precision=P is not None, allocation=AL is not None, owen=OW is not None, v6=A is not None),
    )
    its = G.get("iterations", [])
    fact = dict(
        rid=rid, pair=defn["pair"], scenario=sc, network_sha256=R["network_sha256"][:16],
        termination=S["termination_condition"], gurobi_status=S["split"]["gurobi_status_name"], label_provisional=A["label"],
        label_final=(A_final["label"] if A_final else "batch regrade not yet run"), c1_reference=P["reference"]["source"][:40],
        c1_abc="".join(str(int(bool(P["acceptance"][k]))) for k in "abc"),
        barrier_iterations=S["split"]["bar_iter_count"], log_last_iteration=its[-1]["iter"] if its else None,
        presolve_s=G.get("presolve_s"), ordering_s=G.get("ordering_s"), iter0_log_time_s=G.get("iter0_time_s"),
        barrier_log_seconds=G["barrier_line"]["seconds"], work_units=S["split"]["work_units"],
        mean_s_per_iter=round(G["mean_s_per_iter"], 2), mean_s_per_iter_last10=round(G["mean_s_per_iter_last10"], 2),
        optimize_seconds=round(SS["optimize_seconds"], 2), lp_read_seconds=round(SS["read_seconds"], 2),
        process2_solve_seconds=round(SS["solve_seconds"], 2), process2_wall_time_v_s=T2.get("wall_s"), process2_exit=T2.get("exit_status"),
        process2_start_utc=utc(SS["started_epoch"]), process2_end_utc=utc(SS["finished_epoch"]),
        process1_seconds=round(RP["p1_end"] - RP["p1_start"], 1), process1_start_utc=utc(RP["p1_start"]), lp_build_seconds=round(P1["lp"]["build_seconds"], 1) if P1 else None,
        lp_write_seconds=round(SB["write_seconds"], 1), process1_peak_rss_gib=P1.get("peak_rss_gib"), lp_bytes=SB["problem_bytes"],
        process3_seconds=round(S["finished_epoch"] - S["started_epoch"], 1), process3_peak_rss_gib=P3.get("peak_rss_gib"),
        post_violations_s=round(V["seconds"], 1), post_c1_s=round(P["seconds"], 1), post_m12_s=round(AL["seconds"], 1), post_owen_audit_s=round(RA["seconds"], 1),
        post_steps_sum_s=round(V["seconds"] + P["seconds"] + AL["seconds"] + RA["seconds"], 1),
        gurobi_max_mem_used_gb=S["split"]["max_mem_used_gb"], process2_peak_rss_gib=round(S["split"]["peak_rss_bytes"] / 2**30, 2),
        process2_time_v_max_rss_gib=round(T2["max_rss_kb"] / 2**20, 2) if T2.get("max_rss_kb") else None,
        monitor_cgroup_used_peak_gib=M.get("cgroup_used_peak_gib"), monitor_cgroup_anon_peak_gib=M.get("cgroup_anon_peak_gib"),
        monitor_rss_group_peak_gib=M.get("rss_group_peak_gib"), mem_quota_gib=M.get("cgroup_limit_gib"),
        objective_incl_constant_eur=S["objective"], objective_lp_eur=S["objective_lp"],
        objective_constant_eur=S["scaling"]["objective_constants"]["total_eur"],
        last_iter_rel_gap_log=G.get("last_rel_gap_log"), last_iter_rel_difference_c1=P["a_total_cost"]["last_iteration"]["relative_difference"],
        returned_rel_gap_kkt=K["relative_gap"],
        projection_projected_total_s=PJ["projected_total_s"] if PJ else None, projection_exceeded=PJ["exceeded"] if PJ else None,
        lp_cols=lp["num_col"], lp_rows=lp["num_row"], lp_nnz=lp["nnz"],
        presolved_rows=G["presolved"]["rows"], presolved_cols=G["presolved"]["cols"], presolved_nnz=G["presolved"]["nnz"],
        dense_cols=G.get("dense_cols"), factor_nz=G.get("factor_nz"), factor_ops=G.get("factor_ops"),
        cpu=G.get("cpu"), threads=SS["solver_parameters"]["Threads"], gurobi=G.get("gurobi_version"), time_limit_s=R["time_limit"],
        time_limit_used_share=round(SS["solve_seconds"] / R["time_limit"], 4),
    )
    hs = HPR_STATUS.get(rid)
    if hs:
        fact["hpr_status_termination"] = hs["termination"]; fact["hpr_status_iterations"] = hs["barrier_iterations"]; fact["hpr_status_objective_eur"] = hs["objective_eur"]
        fact["hpr_status_vs_files"] = ("termination " + ("same" if hs["termination"] == S["split"]["gurobi_status_name"] else "DIFFERENT")
                                      + "; iterations " + ("same" if hs["barrier_iterations"] == S["split"]["bar_iter_count"] else "DIFFERENT")
                                      + "; objective = objective_lp (excl. constant) diff %.2f EUR; incl. constant is +%.2f EUR higher" % (
                                          S["objective_lp"] - hs["objective_eur"], S["objective"] - hs["objective_eur"])
                                      + "; post-processing: all outputs present, post_solve_errors " + str(P3.get("post_solve_errors")))
    else:
        fact["hpr_status_termination"] = fact["hpr_status_iterations"] = fact["hpr_status_objective_eur"] = ""
        fact["hpr_status_vs_files"] = "not quoted in the instruction (section 0)"
    return integ, dict(fact, _gurobi_iterations=len(its), _p2_user_s=T2.get("user_s"), _p2_sys_s=T2.get("sys_s"), _p2_cpu=T2.get("cpu_pct"),
                       _monitor=M, _resource=dict((k, utc(v) if k.endswith(("start", "end")) else v) for k, v in RP.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", required=True); ap.add_argument("--pkg", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    exp, pkg, out = Path(a.exp), Path(a.pkg), Path(a.out)
    bdef = jl(pkg / "BATCH_DEF.json"); commit = (pkg / "COMMIT").read_text().strip()
    rids = sorted(p.name for p in exp.iterdir() if p.is_dir() and re.fullmatch(r"F\d", p.name))
    integ, facts = {}, []
    for rid in rids:
        i, f = run(rid, exp / rid, bdef, commit)
        integ[rid] = i; facts.append(f)
    (out / "evidence").mkdir(exist_ok=True)
    (out / "evidence" / "INTEGRITY_RUNS.json").write_text(json.dumps(dict(runs_present=rids, runs_missing=[r for r in bdef["runs"] if r not in rids],
                                                                        package_commit=commit, runs=integ), indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (out / "evidence" / "RUN_FACTS.json").write_text(json.dumps(facts, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    cols = [k for k in facts[0] if not k.startswith("_")]
    with (out / "RUN_FACTS.csv").open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n", extrasaction="ignore"); w.writeheader()
        for f in facts:
            w.writerow(f)
    for rid in rids:
        i = integ[rid]
        print(rid, "sha", i["network_sha_equal"], "profile", i["profile_ok"], "lp_v31", i["indirect_code_evidence"]["lp_rows_match_v31"],
              "receipt", i["solve_receipt"]["termination"], i["solve_receipt"]["post_solve_complete"], "viol_over", i["violations"]["rows_over_budget"],
              "v6", i["v6_provisional"]["label"], "c1", i["c1"]["a"], i["c1"]["b"], i["c1"]["c"])


if __name__ == "__main__":
    main()
