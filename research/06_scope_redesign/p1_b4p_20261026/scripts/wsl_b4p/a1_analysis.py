"""B4P A1: resource data of every available run (cloud 365x24h R1-R11, local 56x3h, B4P truncated builds and solves) -> A1_DATA.json;
log-log fits in the snapshot count on the 2920x3h truncations and the extrapolation to 2920 snapshots -> A1_EXTRAPOLATION.json.
Read only. Usage: python a1_analysis.py <evidence dir>"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

RES = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
CLOUD3 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10_20261022/cloud_results/20261023T174135Z_halted/full/unpacked/export")
CLOUD_R11 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10s1_20261024/cloud_results/only_R11/full/unpacked/export/R11")
ITER = re.compile(r"^\s*(\d+)\s+([-+]?\d\.\d+e[+-]\d+)\s+([-+]?\d\.\d+e[+-]\d+)\s+\S+\s+\S+\s+\S+\s+(\d+)s\s*$")


def jl(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def log_facts(p: Path) -> dict:
    if not p.exists():
        return {}
    t = p.read_text(errors="ignore"); f = {}
    for key, pat, conv in (("fingerprint", r"Model fingerprint: (0x[0-9a-f]+)", str), ("threads", r"^Threads\s+(\d+)", int), ("presolve_s", r"Presolve time: ([\d.]+)s", float),
                           ("ordering_s", r"Ordering time: ([\d.]+)s", float), ("dense_cols", r"Dense cols\s*:\s*(\d+)", int), ("free_vars", r"Free vars\s*:\s*(\d+)", int),
                           ("aat_nz", r"AA' NZ\s*:\s*([\d.e+]+)", float), ("factor_nz", r"Factor NZ\s*:\s*([\d.e+]+)", float), ("factor_ops", r"Factor Ops\s*:\s*([\d.e+]+)", float),
                           ("factor_mem_gb_gurobi", r"Factor NZ\s*:\s*[\d.e+]+ \(roughly ([\d.]+) GB", float), ("seconds_per_iter_gurobi", r"Factor Ops\s*:\s*[\d.e+]+ \(roughly ([\d.]+) seconds", float)):
        m = re.search(pat, t, re.M); f[key] = conv(m.group(1)) if m else None
    m = re.search(r"Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros", t); f["model"] = [int(x) for x in m.groups()] if m else None
    m = re.search(r"Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros", t); f["presolved"] = [int(x) for x in m.groups()] if m else None
    m = re.search(r"Barrier (?:solved model in|performed) (\d+) iterations (?:and|in) ([\d.]+) seconds \(([\d.]+) work units\)", t)
    f["iterations"] = int(m.group(1)) if m else None; f["barrier_s"] = float(m.group(2)) if m else None; f["work_units"] = float(m.group(3)) if m else None
    its = [(int(mm.group(1)), int(mm.group(4))) for mm in (ITER.match(l) for l in t.splitlines()) if mm]
    by = {}
    for i, s in its:
        by.setdefault(i, s)
    f["iteration_times"] = by
    if 20 in by and 10 in by:
        f["s_per_iter_11_20"] = (by[20] - by[10]) / 10.0
    if f["iterations"] and f["barrier_s"] and 0 in by:
        f["s_per_iter_mean"] = (f["barrier_s"] - by[0]) / max(f["iterations"], 1)   # excluding presolve / ordering (time at iteration 0)
        f["time_before_iter0_s"] = by[0]
    return f


def time_facts(p: Path) -> dict:
    if not p.exists():
        return {}
    t = p.read_text(errors="ignore"); out = {}
    m = re.search(r"Maximum resident set size \(kbytes\): (\d+)", t); out["max_rss_gib"] = int(m.group(1)) / 2**20 if m else None
    m = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): ([\d:.]+)", t)
    if m:
        parts = [float(x) for x in m.group(1).split(":")]; out["wall_s"] = sum(v * 60 ** (len(parts) - 1 - i) for i, v in enumerate(parts))
    return out


def resource_phases(p: Path, build_seconds: float | None, start_epoch: float | None) -> dict:
    """RESOURCE.jsonl (RSS every second): peak during the build (first build_seconds) and after it."""
    if not p.exists() or not build_seconds or not start_epoch:
        return {}
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    if not rows:
        return {}
    t0 = rows[0]["epoch"]; b = [r["rss"] for r in rows if r["epoch"] - t0 <= build_seconds + 2]; s = [r["rss"] for r in rows if r["epoch"] - t0 > build_seconds + 2]
    return dict(peak_build_gib=(max(b) / 2**30 if b else None), peak_after_build_gib=(max(s) / 2**30 if s else None), rss_at_end_of_build_gib=(b[-1] / 2**30 if b else None), samples=len(rows))


def run_facts(d: Path, tag: str, kind: str, cpu: str, snapshots: int | None = None) -> dict:
    rec = jl(d / "SOLVE_RECEIPT.json") or {}; lp = rec.get("lp") or {}; inp = rec.get("input_network") or {}
    lf = log_facts(d / "GUROBI_LOG_SCRUBBED.txt") if (d / "GUROBI_LOG_SCRUBBED.txt").exists() else log_facts(d / "gurobi.linopy.log")
    tf = time_facts(d / "solve_time.txt") if (d / "solve_time.txt").exists() else time_facts(d / "solve.err")
    out = dict(tag=tag, kind=kind, cpu=cpu, dir=str(d), snapshots=snapshots or inp.get("snapshots"), scenario=rec.get("scenario"), profile=rec.get("solver_profile"),
               threads=(rec.get("solver_parameters") or {}).get("Threads"), termination=rec.get("termination_condition"), objective=rec.get("objective"),
               lp_rows=lp.get("num_row"), lp_cols=lp.get("num_col"), lp_nnz=lp.get("nnz"), build_seconds=lp.get("build_seconds"), solve_seconds=rec.get("solve_seconds"),
               peak_rss_gib_receipt=((rec.get("peak_rss_bytes") or 0) / 2**30 or None), log=lf, time=tf,
               phases=resource_phases(d / "RESOURCE.jsonl", lp.get("build_seconds"), rec.get("started_epoch")))
    lpd = d / "lp"
    if lpd.exists():
        out["lp_array_bytes"] = sum(f.stat().st_size for f in lpd.glob("*.npy"))
    sp = jl(d / "split" / "SPLIT_SOLVE.json"); sb = jl(d / "split" / "SPLIT_BUILD.json")
    if sb:
        out["split_build"] = dict(problem_bytes=sb.get("problem_bytes"), write_seconds=sb.get("write_seconds"), p1=time_facts(d / "p1.err"))
    if sp:
        out["split_solve"] = dict({k: sp.get(k) for k in ("gurobi_status_name", "termination_condition", "objective", "bar_iter_count", "runtime_s", "work_units", "max_mem_used_gb", "mem_used_gb",
                                                           "fingerprint", "read_seconds", "optimize_seconds", "solve_seconds", "num_vars", "num_constrs", "num_nzs", "probe_ordering_only", "probe_iterations",
                                                           "protect_parameters", "measurement_parameters")},
                                  peak_rss_gib=((sp.get("peak_rss_bytes") or 0) / 2**30 or None), p2=time_facts(d / "p2.err"), p3=time_facts(d / "p3.err"))
    return out


def fit_loglog(xs, ys):
    """y = a * x^b on the points with y > 0; returns a, b, and the points used."""
    pts = [(x, y) for x, y in zip(xs, ys) if x and y and y > 0]
    if len(pts) < 2:
        return None
    lx = np.log([p[0] for p in pts]); ly = np.log([p[1] for p in pts]); b, la = np.polyfit(lx, ly, 1)
    return dict(a=float(math.exp(la)), b=float(b), points=pts, n=len(pts))


def extrap(fit, x):
    return None if not fit else fit["a"] * x ** fit["b"]


def fit_affine(xs, ys):
    """y = c + m * x (least squares) on the points with y > 0: the physical form of per-snapshot quantities with a fixed overhead."""
    pts = [(x, y) for x, y in zip(xs, ys) if x and y and y > 0]
    if len(pts) < 2:
        return None
    m, c = np.polyfit([p[0] for p in pts], [p[1] for p in pts], 1)
    return dict(c=float(c), m=float(m), points=pts, n=len(pts))


def extrap_affine(fit, x):
    return None if not fit else fit["c"] + fit["m"] * x


def main():
    E = Path(sys.argv[1]); E.mkdir(parents=True, exist_ok=True)
    runs = []
    for rid in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10"):
        d = CLOUD3 / rid
        if d.exists():
            runs.append(run_facts(d, rid, "cloud_365x24h", "8470Q", 365))
    if CLOUD_R11.exists():
        runs.append(run_facts(CLOUD_R11, "R11", "cloud_365x24h", "EPYC9654", 365))
    for tag, sub in (("M08b_int56", "m08b/smoke_s01/integrated"), ("M08b_disc56", "m08b/smoke_s01/disconnected"), ("M10R_b1_disc56", "m10r/b1_disconnected"),
                     ("M10R_wacc_disc56", "m10r/wacc_disconnected"), ("M10R_keepstock56", "m10r/keepstock_v5"), ("M12b_minusVN56", "m12b/integrated_minusVN")):
        d = RES / sub
        if d.exists():
            runs.append(run_facts(d, tag, "local_56x3h", "i7-13620H", 56))
    builds = []
    for d in sorted((RES / "b4p" / "builds").glob("*_*")):
        rec = jl(d / "SOLVE_RECEIPT.json") or {}
        if not rec:
            continue
        sc, N = d.name.rsplit("_", 1); lp = rec.get("lp") or {}
        builds.append(dict(scenario=sc, snapshots=int(N), lp_rows=lp.get("num_row"), lp_cols=lp.get("num_col"), lp_nnz=lp.get("nnz"), build_seconds=lp.get("build_seconds"),
                           peak_rss_gib_receipt=(rec.get("peak_rss_bytes") or 0) / 2**30, time=time_facts(d / "build.err"), lp_array_bytes=sum(f.stat().st_size for f in (d / "lp").glob("*.npy")) if (d / "lp").exists() else None))
    solves = []
    for d in sorted((RES / "b4p" / "solves").glob("*")):
        if (d / "SOLVE_RECEIPT.json").exists():
            mode = (d / "MODE.txt").read_text().split() if (d / "MODE.txt").exists() else []
            solves.append(dict(run_facts(d, d.name, "b4p_local", "i7-13620H"), mode=(mode[0] if mode else None), N=(int(mode[2]) if len(mode) > 2 else None)))
    data = dict(cloud_and_local_runs=runs, b4p_builds=builds, b4p_solves=solves)
    (E / "A1_DATA.json").write_text(json.dumps(data, indent=1, default=str) + "\n")
    # ---- fits on the 2920x3h truncations (integrated / disconnected separately)
    fits = {}
    for sc in ("integrated", "disconnected"):
        b = [x for x in builds if x["scenario"] == sc]; xs = [x["snapshots"] for x in b]
        f = dict(lp_rows=fit_loglog(xs, [x["lp_rows"] for x in b]), lp_cols=fit_loglog(xs, [x["lp_cols"] for x in b]), lp_nnz=fit_loglog(xs, [x["lp_nnz"] for x in b]),
                 build_peak_gib=fit_loglog(xs, [(x["time"] or {}).get("max_rss_gib") for x in b]), build_seconds=fit_loglog(xs, [x["build_seconds"] for x in b]),
                 lp_array_bytes=fit_loglog(xs, [x["lp_array_bytes"] for x in b]))
        # solves of this scenario: Factor NZ / Ops / process-2 peak / problem file bytes vs N (one point per N: the split run when there is one, else the first).
        # REGIME: with GURO_PAR_BARDENSETHRESH = 200 the coupling columns (a capacity column touches every snapshot) are handled as dense columns only
        # when N > 200 - as in the full 2920x3h problem (and the 365x24h cloud runs: 6486 dense cols); below 200 they stay in AA' (C3 at 112:
        # AA' NZ 3.3e7 for 112 snapshots vs 1.4e7 for the 365 daily snapshots). The Gurobi-side fits therefore use the N >= 200 points only
        # (DENSE_MIN), the build-side fits (LP size, build memory, file sizes) every point.
        def dense_regime(x):   # the coupling columns count as dense when N > GURO_PAR_BARDENSETHRESH (profile 200; measurement override via --measure)
            thr = ((x.get("split_solve") or {}).get("measurement_parameters") or {}).get("GURO_PAR_BARDENSETHRESH", 200)
            return x["N"] > float(thr)
        byN = {}
        for x in sorted((x for x in solves if x["scenario"] == sc and x.get("N") and (x.get("log") or {}).get("factor_nz")), key=lambda x: (x["N"], 0 if dense_regime(x) else 1, 0 if x.get("split_solve") else 1)):
            byN.setdefault((x["N"], dense_regime(x)), x)
        s_all = [byN[k] for k in sorted(byN)]
        s = [x for x in s_all if dense_regime(x)]
        f["dense_regime_points"] = [dict(tag=x["tag"], N=x["N"], threshold=((x.get("split_solve") or {}).get("measurement_parameters") or {}).get("GURO_PAR_BARDENSETHRESH", 200)) for x in s]
        f["sparse_regime_points"] = [dict(tag=x["tag"], N=x["N"]) for x in s_all if not dense_regime(x)]
        f["factor_nz_all_regimes"] = fit_loglog([x["N"] for x in s_all], [(x["log"] or {}).get("factor_nz") for x in s_all])
        f["factor_ops_all_regimes"] = fit_loglog([x["N"] for x in s_all], [(x["log"] or {}).get("factor_ops") for x in s_all])
        f["factor_nz"] = fit_loglog([x["N"] for x in s], [(x["log"] or {}).get("factor_nz") for x in s])
        f["factor_ops"] = fit_loglog([x["N"] for x in s], [(x["log"] or {}).get("factor_ops") for x in s])
        f["aat_nz"] = fit_loglog([x["N"] for x in s], [(x["log"] or {}).get("aat_nz") for x in s])
        f["presolved_rows"] = fit_loglog([x["N"] for x in s], [((x["log"] or {}).get("presolved") or [None])[0] for x in s])
        sp = [x for x in s if x.get("split_solve")]
        spb = {}   # build-side quantities: every folder with a process-1 result (also the ones whose Gurobi call was not made or was terminated)
        for x in sorted((x for x in solves if x["scenario"] == sc and x.get("N") and x.get("split_build")), key=lambda x: x["N"]):
            spb.setdefault(x["N"], x)
        spb = [spb[k] for k in sorted(spb)]
        f["problem_bytes"] = fit_loglog([x["N"] for x in spb], [(x.get("split_build") or {}).get("problem_bytes") for x in spb])
        f["problem_write_seconds"] = fit_loglog([x["N"] for x in spb], [(x.get("split_build") or {}).get("write_seconds") for x in spb])
        f["p2_peak_gib"] = fit_loglog([x["N"] for x in sp], [((x["split_solve"] or {}).get("p2") or {}).get("max_rss_gib") for x in sp])
        f["gurobi_max_mem_gb"] = fit_loglog([x["N"] for x in sp], [(x["split_solve"] or {}).get("max_mem_used_gb") for x in sp])
        f["p1_peak_gib"] = fit_loglog([x["N"] for x in spb], [((x.get("split_build") or {}).get("p1") or {}).get("max_rss_gib") for x in spb])
        f["read_seconds"] = fit_loglog([x["N"] for x in sp], [(x["split_solve"] or {}).get("read_seconds") for x in sp])
        f["presolve_ordering_seconds"] = fit_loglog([x["N"] for x in s], [((x["log"] or {}).get("presolve_s") or 0) + ((x["log"] or {}).get("ordering_s") or 0) or None for x in s])
        f["seconds_per_iter_11_20"] = fit_loglog([x["N"] for x in s], [(x["log"] or {}).get("s_per_iter_11_20") for x in s])
        f["p3_peak_gib"] = fit_loglog([x["N"] for x in sp], [((x["split_solve"] or {}).get("p3") or {}).get("max_rss_gib") for x in sp])
        single = [x for x in solves if x["scenario"] == sc and x.get("N") and x.get("mode") == "current"]
        f["single_peak_gib"] = fit_loglog([x["N"] for x in single], [(x["time"] or {}).get("max_rss_gib") for x in single])
        f["single_seconds_per_iter"] = fit_loglog([x["N"] for x in single], [(x["log"] or {}).get("s_per_iter_mean") for x in single])
        f["split_seconds_per_iter"] = fit_loglog([x["N"] for x in sp], [(x["log"] or {}).get("s_per_iter_mean") for x in sp])
        fits[sc] = {k: v for k, v in f.items()}
    N = 2920
    proj = {}
    for sc, fs in fits.items():
        proj[sc] = {}
        for k, v in fs.items():
            if not isinstance(v, dict):   # point lists (dense_regime_points / sparse_regime_points) are documentation, not fits
                continue
            aff = fit_affine([p[0] for p in (v or {}).get("points", [])], [p[1] for p in (v or {}).get("points", [])]) if v else None
            lo, hi = extrap(v, N), extrap_affine(aff, N)
            both = [x for x in (lo, hi) if x is not None]
            proj[sc][k] = dict(loglog_at_2920=lo, exponent=(v or {}).get("b"), affine_at_2920=hi, affine=({kk: aff[kk] for kk in ("c", "m")} if aff else None),
                               at_2920_low=(min(both) if both else None), at_2920_high=(max(both) if both else None), points=(v or {}).get("points"),
                               note="low = log-log power fit, high = affine fit (fixed overhead + per-snapshot part); the conservative (high) value is used for memory and time")
    (E / "A1_EXTRAPOLATION.json").write_text(json.dumps(dict(fits=fits, projection_2920=proj), indent=1, default=str) + "\n")
    print(json.dumps({sc: {k: [round(v["at_2920_low"], 3), round(v["at_2920_high"], 3), round(v["exponent"], 3)] for k, v in p.items() if v.get("at_2920_low")} for sc, p in proj.items()}, indent=1))


if __name__ == "__main__":
    main()
