"""B4P report tables (markdown) from the evidence JSONs -> evidence/REPORT_TABLES.md. Read only. Usage: python report_tables.py <evidence dir>"""
import json
import sys
from pathlib import Path


def jl(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None


def f(x, fmt="{:.2f}"):
    return "—" if x is None else (fmt.format(x) if isinstance(x, (int, float)) else str(x))


def g(d, *keys, default=None):
    for k in keys:
        d = (d or {}).get(k) if isinstance(d, dict) else None
    return default if d is None else d


def main():
    E = Path(sys.argv[1]); data = jl(E / "A1_DATA.json") or {}; ext = jl(E / "A1_EXTRAPOLATION.json") or {}; summ = jl(E / "A1_SUMMARY.json") or {}
    L = []
    # 1. existing runs
    L += ["### 已有运行（VERIFIED）", "", "| 运行 | 类型 / CPU | 时段 | Threads | 行 / 列 / 非零（原始） | 预求解后行 / 列 / 非零 | Factor NZ | Factor Ops | 迭代 | barrier s | s/次（均） | s/次（11–20） | 终止 | 峰值 RSS GiB | 构建 s |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in data.get("cloud_and_local_runs", []):
        lg = r.get("log") or {}; tf = r.get("time") or {}
        L.append(f"| {r['tag']} | {r['kind']} / {r['cpu']} | {r.get('snapshots')} | {r.get('threads')} | {'/'.join(str(x) for x in (lg.get('model') or ['—']))} | {'/'.join(str(x) for x in (lg.get('presolved') or ['—']))} | "
                 f"{f(lg.get('factor_nz'), '{:.3e}')} | {f(lg.get('factor_ops'), '{:.3e}')} | {f(lg.get('iterations'), '{}')} | {f(lg.get('barrier_s'), '{:.0f}')} | {f(lg.get('s_per_iter_mean'))} | {f(lg.get('s_per_iter_11_20'))} | "
                 f"{r.get('termination')} | {f(tf.get('max_rss_gib') or r.get('peak_rss_gib_receipt'))} | {f(r.get('build_seconds'), '{:.0f}')} |")
    # 2. builds
    L += ["", "### B4P 截短构建（`--stop-before-solve`，VERIFIED）", "", "| 情景 | 时段 | 行 | 列 | 非零 | 构建 s | 峰值 RSS GiB | lp/ 数组 MB |", "|---|---|---|---|---|---|---|---|"]
    for b in data.get("b4p_builds", []):
        L.append(f"| {b['scenario']} | {b['snapshots']} | {b['lp_rows']:,} | {b['lp_cols']:,} | {b['lp_nnz']:,} | {f(b['build_seconds'], '{:.1f}')} | {f((b.get('time') or {}).get('max_rss_gib'))} | {f((b.get('lp_array_bytes') or 0) / 1e6, '{:.0f}')} |")
    # 3. solves
    L += ["", "### B4P 本机求解 / 探针（VERIFIED）", "", "| 标签 | 方式 | 情景 | 时段 | 档案 | 终止 | 迭代 | barrier s | s/次 | Factor NZ | Factor Ops | Fingerprint | 单进程峰值 GiB | 进程 1 / 2 / 3 峰值 GiB | Gurobi MaxMemUsed GB | LP 文件 MB | 写出 / 读入 s |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in data.get("b4p_solves", []):
        lg = s.get("log") or {}; sb = s.get("split_build") or {}; ss = s.get("split_solve") or {}
        p1 = (sb.get("p1") or {}).get("max_rss_gib"); p2 = (ss.get("p2") or {}).get("max_rss_gib"); p3 = (ss.get("p3") or {}).get("max_rss_gib")
        L.append(f"| {s['tag']} | {s.get('mode')} | {s.get('scenario')} | {s.get('N')} | {s.get('profile')} | {ss.get('gurobi_status_name') or s.get('termination')} | {f(lg.get('iterations'), '{}')} | {f(lg.get('barrier_s'), '{:.0f}')} | {f(lg.get('s_per_iter_mean'))} | "
                 f"{f(lg.get('factor_nz'), '{:.3e}')} | {f(lg.get('factor_ops'), '{:.3e}')} | {lg.get('fingerprint') or ss.get('fingerprint') or '—'} | {f((s.get('time') or {}).get('max_rss_gib')) if s.get('mode') == 'current' else '—'} | "
                 f"{f(p1)} / {f(p2)} / {f(p3)} | {f(ss.get('max_mem_used_gb'))} | {f((sb.get('problem_bytes') or 0) / 1e6, '{:.0f}')} | {f(sb.get('write_seconds'), '{:.1f}')} / {f(ss.get('read_seconds'), '{:.1f}')} |")
    # 4. fits
    L += ["", "### 对时段数的拟合与 2920 外推（INFERENCE；低 = 对数-对数幂律，高 = 仿射 c + m·N）", "", "| 情景 | 量 | 数据点（N, 值） | 幂指数 | 2920 低 | 2920 高 |", "|---|---|---|---|---|---|"]
    for sc, fs in (ext.get("projection_2920") or {}).items():
        for k, v in fs.items():
            if not v.get("points"):
                continue
            pts = ", ".join(f"({int(x)}, {y:.4g})" for x, y in v["points"])
            L.append(f"| {sc} | {k} | {pts} | {f(v.get('exponent'), '{:.3f}')} | {f(v.get('at_2920_low'), '{:.4g}')} | {f(v.get('at_2920_high'), '{:.4g}')} |")
    # 5. summary / candidates
    if summ:
        lch = lambda d, fmt="{:.1f}": "—" if not isinstance(d, dict) or d.get("low") is None else " / ".join(fmt.format(d[k]) for k in ("low", "central", "high") if k in d and isinstance(d[k], (int, float)))
        L += ["", "### F1 / F2 在 2920×3h 的估计（低 / 中 / 高；INFERENCE）", "", "| 运行 | Factor NZ | Factor Ops | 进程 1 峰值 GiB | 进程 2 峰值 GiB | 进程 3 峰值 GiB | 分进程最大 GiB | 单进程峰值 GiB | 8470Q s/次 | 8470Q barrier h | 8352V barrier h | EPYC 9754 barrier h | 预求解+排序 s | LP 文件 GB | lp/ 数组 GB | 解数组 GB |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for rid, s in (summ.get("scenarios") or {}).items():
            m = s["memory_gib"]; d = s["disk_gb"]; pc = s["per_cpu"]
            L.append(f"| {rid} | {lch(s['factor_nz'], '{:.2e}')} | {lch(s['factor_ops'], '{:.2e}')} | {lch(m['split_process1_build'])} | {lch(m['split_process2_gurobi'])} | {lch(m['split_process3_assign'])} | {lch(m['split_max'])} | {lch(m['single_process'])} | "
                     f"{lch(pc['8470Q']['s_per_iter'], '{:.0f}')} | {lch(pc['8470Q']['barrier_hours'])} | {lch(pc['8352V']['barrier_hours'])} | {lch(pc['EPYC9754']['barrier_hours'])} | {lch(s['presolve_ordering_s'], '{:.0f}')} | {lch(d['problem_file_gb'])} | {lch(d['lp_arrays_gb'])} | {f(d['solution_arrays_gb'])} |")
        dn = summ.get("disk_need_gb") or {}
        L += ["", f"磁盘（两个运行）：持久 {f(dn.get('persistent_gb'), '{:.0f}')} GB + 瞬时 LP 文件 {f(dn.get('transient_extra_gb'))} GB（保留两份 LP 文件时 {f(dn.get('with_lp_files_kept_gb'), '{:.0f}')} GB）。"]
        L += ["", "### 候选配置（INFERENCE）", "", "| 配置 | CPU | 核 | 内存 GB | 配额 GiB | 分进程 F1 可跑（中 / 高） | 单进程可跑（中 / 高） | F2 并行（中 / 高） | P1 探针通过（中 / 高） | 总用时 h（低 / 中 / 高） | 费用 ¥（低 / 中 / 高） | 风险 |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        tf = lambda d: f"{'是' if d['central'] else '否'} / {'是' if d['high'] else '否'}"
        for c in summ.get("candidates") or []:
            L.append(f"| {c['name']} | {c['cpu']} | {c['cores']} | {c['mem_gb']:.0f} | {c['quota_gib']:.0f} | {tf(c['can_run_split'])} | {tf(c['can_run_single'])} | {tf(c['parallel_split'])} | {tf(c['p1_probe_passes'])} | {lch(c['hours'], '{:.0f}')} | {lch(c['cost_cny'], '{:.0f}') if c['cost_cny'] else '以控制台为准'} | {'；'.join(c['risks']) or '—'} |")
        L += ["", f"推荐顺序（能跑且最稳 → 最省钱）：{' → '.join(summ.get('recommendation', {}).get('ranked', []))}"]
    (E / "REPORT_TABLES.md").write_text("\n".join(L) + "\n")
    print("tables:", len(L), "lines")


if __name__ == "__main__":
    main()
