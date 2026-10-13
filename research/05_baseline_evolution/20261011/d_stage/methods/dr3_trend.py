"""DR3 下一轮规则（只读）：TIME_LIMIT 前最后 7,200 秒（日志计时）内 Crossover 清理阶段 Dual Inf. 的趋势判定。

规则（D_STAGE_CLAUDE_CODE_INSTRUCTION.md，用户 2026-10-13 08:27 确认，结果出现前写定）：
- 对 log10(Dual Inf.) 与时间做线性回归；统计每 1,800 秒窗口的中位数；同时报告原始不可行度、目标值、迭代速度。
- 情况 1（有下降趋势）：回归斜率 < 0 且外推到 1e-6 所需时间 <= 12 小时；或 4 个窗口中位数整体单调下降。
- 情况 2：不满足情况 1。
- 超时时仍处于 Barrier 或推进阶段（未进入清理）：按情况 1 处理并注明。
Usage: python dr3_trend.py <gurobi.log> <out json>
"""
import sys, re, json, math
from pathlib import Path
import numpy as np

log = Path(sys.argv[1]).read_text(errors='replace').splitlines()
i0 = next((i for i, s in enumerate(log) if s.strip().startswith('Push phase complete')), None)
end_time = None
for s in log:
    m = re.match(r'\s*(?:Stopped|Solved) in (\d+) iterations and ([\d.]+) seconds', s)
    if m: end_time = float(m.group(2))
status_lines = [s.strip() for s in log if re.search(r'Time limit reached|Optimal objective|Infeasible|Stopped in|Solved in|Sub-optimal|Barrier performed|Barrier solved', s)]
out = {'rule': 'DR3_NEXT_ROUND_RULE_PREREGISTERED_20261013_0827', 'log_status_lines': status_lines}
if i0 is None:
    out.update(stage_at_end='BARRIER_OR_PUSH_NOT_CLEANUP', case='CASE_1_BY_RULE_4', note='超时时尚未进入清理阶段，按规则第 4 条按情况 1 处理')
else:
    rec = []
    for s in log[i0 + 1:]:
        m = re.match(r'\s*(\d+)\s+([-\d.e+]+)\s+([\d.e+-]+)\s+([\d.e+-]+)\s+(\d+)s\s*$', s)
        if m: rec.append([int(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5))])
    a = np.array(rec, dtype=float); tend = end_time if end_time is not None else a[-1, 4]
    sel = a[a[:, 4] >= tend - 7200]; t, d = sel[:, 4], sel[:, 3]
    pos = d > 0; lt = np.log10(d[pos]); tt = t[pos]
    slope, icpt = np.polyfit(tt, lt, 1)
    extra = ((-6.0 - icpt) / slope - tend) if slope < 0 else math.inf
    edges = [tend - 7200 + 1800 * k for k in range(5)]
    wins = []
    for k in range(4):
        w = sel[(sel[:, 4] >= edges[k]) & (sel[:, 4] < edges[k + 1] + (1e-9 if k == 3 else 0))]
        wins.append({'from_s': edges[k], 'to_s': edges[k + 1], 'records': int(len(w)), 'dual_inf_median': float(np.median(w[:, 3])) if len(w) else None,
                     'primal_inf_max': float(w[:, 2].max()) if len(w) else None, 'objective_first_last': [float(w[0, 1]), float(w[-1, 1])] if len(w) else None,
                     'iterations': int(w[-1, 0] - w[0, 0]) if len(w) > 1 else 0})
    med = [w['dual_inf_median'] for w in wins if w['dual_inf_median'] is not None]
    mono = len(med) == 4 and all(med[k + 1] < med[k] for k in range(3))
    c1a = bool(slope < 0 and extra <= 12 * 3600)
    out.update(stage_at_end='CLEANUP', cleanup_start_s=float(a[0, 4]), end_s=tend, records_in_window=int(len(sel)), records_total=int(len(a)),
               regression={'slope_log10_per_s': float(slope), 'intercept': float(icpt), 'extrapolated_seconds_to_1e-6_after_end': float(extra) if math.isfinite(extra) else None,
                           'condition_slope_neg_and_le_12h': c1a},
               windows_1800s=wins, condition_window_medians_monotone_decreasing=mono,
               iteration_speed_per_s=float((sel[-1, 0] - sel[0, 0]) / max(1.0, sel[-1, 4] - sel[0, 4])),
               primal_inf_max_in_window=float(sel[:, 2].max()), objective_first_last=[float(sel[0, 1]), float(sel[-1, 1])],
               case='CASE_1_DOWNWARD_TREND' if (c1a or mono) else 'CASE_2_NO_DOWNWARD_TREND')
    if a[0, 4] > tend - 7200: out['note'] = '清理阶段开始晚于窗口起点；窗口内只含清理阶段记录（推进阶段无 Dual Inf. 列）'
Path(sys.argv[2]).write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in out.items() if k != 'windows_1800s'}, indent=1, ensure_ascii=False)); print(json.dumps(out.get('windows_1800s'), indent=1))
