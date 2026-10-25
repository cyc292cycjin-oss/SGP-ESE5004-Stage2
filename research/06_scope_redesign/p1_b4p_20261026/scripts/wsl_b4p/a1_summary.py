"""B4P A1.3 / A1.4: the F1 / F2 resource estimates at 2920 snapshots (median and range; VERIFIED vs INFERENCE), single-process vs split-process,
and the candidate-configuration table (can run / parallel / hours / cost / risks). Reads evidence/A1_DATA.json and A1_EXTRAPOLATION.json
(a1_analysis.py). Writes evidence/A1_SUMMARY.json (+ the markdown tables come from report_tables.py). Read only; every constant below is an
assumption with its source. Usage: python a1_summary.py <evidence dir>

Model (INFERENCE):
  Factor NZ / Ops at 2920 from the dense-column-regime points (140 / 182 snapshots with the measurement threshold 100, i.e. the regime of the full
  problem), three estimates each: affine (low), the cloud 365x24h anchor (R3 / R4: the same per-snapshot LP with 6486 / 6248 dense columns)
  scaled 365 -> 2920 with the local 182 -> 365 exponent (central), and the local power law (high).
  Process-2 memory = non-factor part (linear in N; local 140 / 182 RSS minus the factor memory Gurobi prints, and the cloud anchor R3 / R4 Gurobi
  share minus its factor) + Factor NZ x 14 bytes (Gurobi's "roughly X GB" lines: 13.3-14.3 B per factor nonzero).
  Seconds per iteration = (cloud T16 seconds per 1e12 factor ops, R3 integrated 3.86 / R4 disconnected 7.11 - the smaller factor runs less
  efficiently; the disconnected rate at 2920 is taken between the two) x Factor Ops / 1e12 x CPU factor.
"""
import json
import sys
from pathlib import Path

N = 2920
GIB = 2**30
CPU = {"8470Q": dict(factor=(1.0, 1.0), note="reference: third batch R1-R10 (AutoDL West-B 8470Q, 25 cores / 92 GiB); R3 / R4 are the T16 runs"),
       "8352V": dict(factor=(1.15, 1.5), note="Ice Lake-SP 2.1 GHz, DDR4; no measurement: 1.15-1.5 x slower than 8470Q assumed (barrier is memory-bandwidth bound; INFERENCE)"),
       "EPYC9754": dict(factor=(1.0, 1.3), note="Zen 4c: R11 on EPYC 9654 ran 10.3 s/it vs R2 10.5 s/it on 8470Q (same model, T8) = 0.98; 9754 has lower clocks and 128 cores/socket -> 1.0-1.3 x (INFERENCE)")}
CONFIGS = [
    dict(id="autodl_cpu_4x8352V", name="AutoDL CPU 4 份（128 核 8352V / 240 GB）", cpu="8352V", cores=128, mem_gb=240, disk_gb=None, price=3.1, disk_note="数据盘按租用配置（每份约 50 GB，需核实）"),
    dict(id="autodl_vgpu48_4x8470Q", name="AutoDL vGPU-48GB 4 卡（100 核 8470Q / 368 GB）", cpu="8470Q", cores=100, mem_gb=368, disk_gb=None, price=11.5, disk_note="数据盘按租用配置（第三批同型 50 GB，可扩）"),
    dict(id="autodl_4090D_4xEPYC9754", name="AutoDL RTX 4090D 4 卡（72 核 EPYC 9754 / 240 GB / 数据盘 ≤ 60 GB）", cpu="EPYC9754", cores=72, mem_gb=240, disk_gb=60, price=7.5, disk_note="数据盘最多 60 GB（补充 1）"),
    dict(id="aliyun_r8i_256", name="阿里云新加坡 r8i 256 GiB（约 32 vCPU）", cpu="8470Q", cores=32, mem_gb=256 * 1.0737, disk_gb=None, price=None, disk_note="云盘按需；单价以控制台为准"),
    dict(id="aliyun_r8i_512", name="阿里云新加坡 r8i 512 GiB（约 64 vCPU）", cpu="8470Q", cores=64, mem_gb=512 * 1.0737, disk_gb=None, price=None, disk_note="云盘按需；单价以控制台为准"),
]
ITERS = {"F1": (253, 350, 465), "F2": (116, 170, 228)}   # third batch 365x24h: integrated 253-465 (R1 253 / R3 260 / R10 465), disconnected 116-228; median = judgement
CLOUD = {"integrated": dict(run="R3", N=365, factor_nz=5.278e8, factor_ops=4.241e12, factor_gb=7.0, rss_gib=22.78, python_gib=10.15, rate_s_per_1e12=3.86, dense_cols=6486),
         "disconnected": dict(run="R4", N=365, factor_nz=2.511e8, factor_ops=1.036e12, factor_gb=5.0, rss_gib=19.29, python_gib=9.5, rate_s_per_1e12=7.11, dense_cols=6248)}
BYTES_PER_NZ = (13.3, 14.3)   # Gurobi "roughly X GB of memory" / Factor NZ on the local probes
OVERHEAD_H = dict(p1_build_write=(0.25, 0.5), p2_read=(0.03, 0.05), p2_presolve_ordering=(0.45, 1.6), p3_rebuild_assign_export=(1.5, 3.0), postprocessing=(0.5, 1.5),
                  note="per run; process 1 / 3 and the post-processing run outside the Gurobi TimeLimit; presolve + ordering inside it; scaled from 56-224 local measurements x 1.35 (slower cloud cores)")


def jl(p):
    return json.loads(Path(p).read_text())


def pts(fit):
    return {int(x): y for x, y in (fit or {}).get("points", [])} if fit else {}


def main():
    E = Path(sys.argv[1]); data = jl(E / "A1_DATA.json"); ext = jl(E / "A1_EXTRAPOLATION.json"); fits = ext["fits"]; proj = ext["projection_2920"]
    out = dict(method=__doc__, cpu=CPU, iterations=ITERS, cloud_anchor=CLOUD, bytes_per_factor_nz=BYTES_PER_NZ, overhead_hours=OVERHEAD_H, scenarios={})
    for rid, sc in (("F1", "integrated"), ("F2", "disconnected")):
        f = fits[sc]; c = CLOUD[sc]; nz = pts(f.get("factor_nz")); ops = pts(f.get("factor_ops")); p2 = pts(f.get("p2_peak_gib")); fgb = {}
        for s in data["b4p_solves"]:
            if s["scenario"] == sc and (s.get("log") or {}).get("factor_mem_gb_gurobi") and s["N"] in nz:
                fgb[s["N"]] = s["log"]["factor_mem_gb_gurobi"]
        n_lo, n_hi = sorted(nz)[0], sorted(nz)[-1]
        # exponents: local (140 -> 182) and local-to-cloud (182 -> 365)
        b_nz_local = f["factor_nz"]["b"]; b_ops_local = f["factor_ops"]["b"]
        import math
        b_nz_cloud = math.log(c["factor_nz"] / nz[n_hi]) / math.log(c["N"] / n_hi); b_ops_cloud = math.log(c["factor_ops"] / ops[n_hi]) / math.log(c["N"] / n_hi)
        NZ = dict(low=proj[sc]["factor_nz"]["affine_at_2920"], central=c["factor_nz"] * (N / c["N"]) ** b_nz_cloud, high=proj[sc]["factor_nz"]["loglog_at_2920"],
                  exponents=dict(local_140_182=b_nz_local, local182_to_cloud365=b_nz_cloud))
        OPS = dict(low=proj[sc]["factor_ops"]["affine_at_2920"], central=c["factor_ops"] * (N / c["N"]) ** b_ops_cloud, high=proj[sc]["factor_ops"]["loglog_at_2920"],
                   exponents=dict(local_140_182=b_ops_local, local182_to_cloud365=b_ops_cloud))
        # memory: non-factor part (RSS - printed factor memory) linear in N; cloud anchor
        nf = {n: p2[n] - fgb[n] * 1e9 / GIB for n in p2 if n in fgb}
        ns = sorted(nf); slope = (nf[ns[-1]] - nf[ns[0]]) / (ns[-1] - ns[0]); icpt = nf[ns[0]] - slope * ns[0]
        nf_local = icpt + slope * N
        nf_cloud = (c["rss_gib"] - c["python_gib"] - c["factor_gb"] * 1e9 / GIB) * (N / c["N"])
        nf_lo, nf_hi = sorted((nf_local, nf_cloud)); nf_hi = max(nf_hi, nf_lo * 1.2)
        fac = {k: NZ[k] * BYTES_PER_NZ[1 if k == "high" else 0] / GIB for k in ("low", "central", "high")}
        P2 = dict(low=nf_lo + fac["low"], central=(nf_lo + nf_hi) / 2 + fac["central"], high=nf_hi + fac["high"], non_factor_gib=dict(local_affine=nf_local, cloud_anchor=nf_cloud, points=nf), factor_gib=fac)
        P1 = dict(low=proj[sc]["p1_peak_gib"]["at_2920_low"], high=proj[sc]["p1_peak_gib"]["at_2920_high"])
        P3 = dict(low=P1["low"] * 1.1, high=P1["high"] * 1.25, note="process 3 = rebuild (as process 1) + the arrays and exports: 56-snapshot measurement 2.64 vs 2.19 GiB (x 1.2)")
        SINGLE = dict(low=P1["low"] + P2["low"], central=(P1["low"] + P1["high"]) / 2 + P2["central"], high=P1["high"] + P2["high"], note="single process = Python model (process-1 peak stays resident) + the Gurobi part; C3 at 112 (sparse regime) exceeded 10.5 GiB where the split process 2 at 140 / 182 (dense regime) peaked at 6.7 / 7.8 GiB")
        rate = c["rate_s_per_1e12"] if sc == "integrated" else (CLOUD["integrated"]["rate_s_per_1e12"], c["rate_s_per_1e12"])
        it_lo, it_md, it_hi = ITERS[rid]; per_cpu = {}
        for cpu, cc in CPU.items():
            r_lo, r_hi = (rate, rate) if isinstance(rate, float) else rate
            s_lo = r_lo * OPS["low"] / 1e12 * cc["factor"][0]; s_md = (r_lo + r_hi) / 2 * OPS["central"] / 1e12 * (cc["factor"][0] + cc["factor"][1]) / 2; s_hi = r_hi * OPS["high"] / 1e12 * cc["factor"][1]
            per_cpu[cpu] = dict(s_per_iter=dict(low=s_lo, central=s_md, high=s_hi), barrier_hours=dict(low=s_lo * it_lo / 3600, central=s_md * it_md / 3600, high=s_hi * it_hi / 3600),
                                exceeds_72h_time_limit=dict(central=(s_md * it_md / 3600 > 72), high=(s_hi * it_hi / 3600 > 72)))
        local_rate = {n: (f["seconds_per_iter_11_20"]["points"] and dict(f["seconds_per_iter_11_20"]["points"]).get(n)) for n in nz}
        disk = dict(problem_file_gb=dict(low=proj[sc]["problem_bytes"]["at_2920_low"] / 1e9, high=proj[sc]["problem_bytes"]["at_2920_high"] / 1e9, removed_after_read=True),
                    lp_arrays_gb=dict(low=proj[sc]["lp_array_bytes"]["at_2920_low"] / 1e9, high=proj[sc]["lp_array_bytes"]["at_2920_high"] / 1e9),
                    solution_arrays_gb=(2 * proj[sc]["lp_cols"]["at_2920_high"] + proj[sc]["lp_rows"]["at_2920_high"]) * 8 / 1e9,
                    duals_nc_gb=0.077 * 8, solved_network_gb=0.166 * 8, export_copy_gb=0.26 * 8, note="DUALS / solved network / export scaled x 8 from the 365x24h cloud exports (77 / 166 / 257 MB)")
        disk["per_run_persistent_gb"] = disk["lp_arrays_gb"]["high"] + disk["solution_arrays_gb"] + disk["duals_nc_gb"] + disk["solved_network_gb"] + disk["export_copy_gb"]
        disk["per_run_transient_gb"] = disk["problem_file_gb"]["high"]
        out["scenarios"][rid] = dict(scenario=sc, dense_regime_points=f.get("dense_regime_points"), factor_nz=NZ, factor_ops=OPS, memory_gib=dict(split_process1_build=P1, split_process2_gurobi=P2, split_process3_assign=P3,
                                     split_max=dict(low=max(P1["low"], P2["low"]), central=max((P1["low"] + P1["high"]) / 2, P2["central"]), high=max(P1["high"], P2["high"], P3["high"])), single_process=SINGLE),
                                     seconds_per_1e12_ops_cloud_T16=rate, local_seconds_per_iter_11_20=local_rate, per_cpu=per_cpu, iterations=ITERS[rid], disk_gb=disk,
                                     presolve_ordering_s=dict(low=proj[sc]["presolve_ordering_seconds"]["at_2920_low"], high=proj[sc]["presolve_ordering_seconds"]["at_2920_high"]),
                                     read_s=dict(low=proj[sc]["read_seconds"]["at_2920_low"], high=proj[sc]["read_seconds"]["at_2920_high"]))
    # ---- candidate configurations
    F1, F2 = out["scenarios"]["F1"], out["scenarios"]["F2"]; oh = OVERHEAD_H
    oh_lo = sum(v[0] for k, v in oh.items() if k != "note"); oh_hi = sum(v[1] for k, v in oh.items() if k != "note")
    env_gb = 3.3 + 0.75 + 0.4; packs_gb = 2 * (F1["disk_gb"]["export_copy_gb"] + F2["disk_gb"]["export_copy_gb"])
    disk_need = dict(persistent_gb=F1["disk_gb"]["per_run_persistent_gb"] + F2["disk_gb"]["per_run_persistent_gb"] + env_gb + packs_gb, transient_extra_gb=max(F1["disk_gb"]["per_run_transient_gb"], F2["disk_gb"]["per_run_transient_gb"]),
                     with_lp_files_kept_gb=F1["disk_gb"]["per_run_persistent_gb"] + F2["disk_gb"]["per_run_persistent_gb"] + env_gb + packs_gb + F1["disk_gb"]["per_run_transient_gb"] + F2["disk_gb"]["per_run_transient_gb"],
                     note="environment 3.3 GB + conda cache 0.75 + package 0.4; results packs (light + full) ~2 x export; LP problem files removed after the read (REMOVE_LP=1)")
    out["disk_need_gb"] = disk_need
    table = []
    for c in CONFIGS:
        q = c["mem_gb"] / 1.0737; lim = 0.80 * q
        m1 = F1["memory_gib"]; m2 = F2["memory_gib"]
        can_split = dict(central=m1["split_max"]["central"] <= lim, high=m1["split_max"]["high"] <= lim)
        can_single = dict(central=m1["single_process"]["central"] <= lim, high=m1["single_process"]["high"] <= lim)
        par = dict(central=(m1["split_process2_gurobi"]["central"] + m2["split_process2_gurobi"]["central"] <= lim) and c["cores"] >= 33, high=(m1["split_process2_gurobi"]["high"] + m2["split_process2_gurobi"]["high"] <= lim) and c["cores"] >= 33)
        p1 = dict(central=m1["split_process2_gurobi"]["central"] <= 0.40 * q, high=m1["split_process2_gurobi"]["high"] <= 0.40 * q)   # the P1 probe threshold
        h1 = F1["per_cpu"][c["cpu"]]["barrier_hours"]; h2 = F2["per_cpu"][c["cpu"]]["barrier_hours"]
        tl_h = 72.0
        h1c = {k: min(v, tl_h) for k, v in h1.items()}   # a run never exceeds the TimeLimit (it stops without a usable solution)
        serial = dict(low=h1["low"] + h2["low"] + 2 * oh_lo, central=h1c["central"] + h2["central"] + 2 * (oh_lo + oh_hi) / 2, high=h1c["high"] + h2["high"] + 2 * oh_hi)
        parallel = dict(low=max(h1["low"], h2["low"]) + 1.5 * oh_lo, central=max(h1c["central"], h2["central"]) + 1.5 * (oh_lo + oh_hi) / 2, high=max(h1c["high"], h2["high"]) + 1.5 * oh_hi)
        hours = parallel if par["central"] else serial
        risks = []
        if not can_split["central"]: risks.append("内存：分进程 F1 中值已超过 80 % 配额")
        elif not can_split["high"]: risks.append("内存：分进程 F1 高值超过 80 % 配额（区间上端不保险）")
        if not can_single["central"]: risks.append("内存：单进程方式不可行")
        if F1["per_cpu"][c["cpu"]]["exceeds_72h_time_limit"]["central"]: risks.append("时间：F1 中值估计超过 72 h TimeLimit（早期测速会止损）")
        elif F1["per_cpu"][c["cpu"]]["exceeds_72h_time_limit"]["high"]: risks.append("时间：F1 高值估计超过 72 h TimeLimit")
        if CPU[c["cpu"]]["factor"] != (1.0, 1.0): risks.append("每次迭代耗时无该 CPU 实测（因子为假设）")
        if c["cores"] < 33: risks.append("核数 < 33：F2 必须等 F1")
        if c.get("disk_gb") and c["disk_gb"] <= 60: risks.append(f"数据盘 60 GB：需要 REMOVE_LP=1（持久用量约 {disk_need['persistent_gb']:.0f} GB + 瞬时 LP 文件 {disk_need['transient_extra_gb']:.1f} GB）")
        table.append(dict(c, quota_gib=q, limit_80_gib=lim, can_run_split=can_split, can_run_single=can_single, parallel_split=par, p1_probe_passes=p1, hours_serial=serial, hours_parallel=parallel, hours=hours,
                          cost_cny=({k: v * c["price"] for k, v in hours.items()} if c["price"] else None), f1_barrier_hours=h1, f2_barrier_hours=h2, risks=risks))
    out["candidates"] = table
    best = sorted(table, key=lambda c: (not c["can_run_split"]["high"], not c["parallel_split"]["central"], (c["cost_cny"] or {}).get("central", 1e9)))
    out["recommendation"] = dict(order="能跑且最稳（分进程高值仍在 80 % 配额内、CPU 有实测）→ 最省钱", ranked=[c["id"] for c in best],
                                 note="see B4P_REPORT.md section 2 for the reasoning; the user decides the machine")
    (E / "A1_SUMMARY.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    for rid in ("F1", "F2"):
        s = out["scenarios"][rid]; m = s["memory_gib"]
        print(rid, "NZ", {k: f"{v:.3g}" for k, v in s["factor_nz"].items() if k != "exponents"}, "OPS", {k: f"{v:.3g}" for k, v in s["factor_ops"].items() if k != "exponents"})
        print("   P2 GiB", {k: round(v, 1) for k, v in m["split_process2_gurobi"].items() if isinstance(v, float)}, "P1", {k: round(v, 1) for k, v in m["split_process1_build"].items()}, "single", {k: round(v, 1) for k, v in m["single_process"].items() if isinstance(v, float)})
        print("   8470Q s/it", {k: round(v) for k, v in s["per_cpu"]["8470Q"]["s_per_iter"].items()}, "barrier h", {k: round(v, 1) for k, v in s["per_cpu"]["8470Q"]["barrier_hours"].items()})
    print("disk", {k: (round(v, 1) if isinstance(v, float) else v) for k, v in disk_need.items() if k != "note"})
    for c in table:
        print(c["id"], "split", c["can_run_split"], "single", c["can_run_single"], "par", c["parallel_split"], "hours", {k: round(v) for k, v in c["hours"].items()}, "cost", ({k: round(v) for k, v in c["cost_cny"].items()} if c["cost_cny"] else None))
    print("ranked", out["recommendation"]["ranked"])


if __name__ == "__main__":
    main()
