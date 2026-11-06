#!/usr/bin/env python3
"""V4 W10-5: markdown tables for REPORT.md from the W10 CSV outputs (no number typed by hand). Writes evidence/REPORT_TABLES.md."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


def m(x, nd=1):
    return "" if pd.isna(x) else f"{x / 1e6:,.{nd}f}"


def short(s):
    s = s if isinstance(s, str) else ""
    keys = re.findall(r"(bound_switch|would_enter|investment_F1_F2_differs|degenerate|large_change|discrete_alternative|rank_unstable_vs_\w+|proxy|upper_bound|inference|not_representable|scenario_choice)", s)
    zh = {"bound_switch": "约束状态改变", "would_enter": "候选会进入", "investment_F1_F2_differs": "F1/F2 投资差大", "degenerate": "零余量/退化对偶",
          "large_change": "变动过大", "discrete_alternative": "规则切换", "proxy": "代理值", "upper_bound": "上界", "inference": "推断映射",
          "not_representable": "无候选", "scenario_choice": "情景选择"}
    out = []
    for k in sorted(set(keys)):
        out.append(zh.get(k, k.replace("rank_unstable_vs_", "名次不稳:")))
    return "、".join(out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True)
    d = Path(ap.parse_args().dir)
    imp = pd.read_csv(d / "IMPACT_FIRST_ORDER.csv"); top = pd.read_csv(d / "TOP30.csv"); dl = pd.read_csv(d / "W10_DOWNLOAD_CANDIDATES.csv")
    inv = pd.read_csv(d / "C_GRADE_INVENTORY.csv", dtype=str, keep_default_na=False)
    L = []
    L.append("### T1 TOP30（参照组 s07；EUR 百万；方向 = |ΔB6| 较大的一端）\n")
    L.append("| # | 参数 | 主值 | 一档（低 / 高） | 方向 | ΔZ(F1) | ΔZ(F2) | **ΔB6** | Owen 最大（国） | 筛查名次 | 冒烟名次 | 一阶可靠性标记 |")
    L.append("|---:|---|---:|---|---|---:|---:|---:|---|---:|---:|---|")
    for i, r in top.reset_index(drop=True).iterrows():
        def fv(x):
            if x is None or (isinstance(x, float) and pd.isna(x)):
                return "备选规则"
            try:
                return f"{float(x):.4g}"
            except (TypeError, ValueError):
                return str(x)
        L.append(f"| {i + 1} | `{r.param_id}` | {fv(r.value)} | {fv(r.notch_low)} / {fv(r.notch_high)} | {'低' if r.direction_max == 'low' else '高'} | {m(r.dZ_F1)} | {m(r.dZ_F2)} | **{m(r.dB6)}** | "
                 f"{m(r.owen_max_eur)}（{r.owen_max_country if isinstance(r.owen_max_country, str) else '—'}） | {int(r.rank_screen) if pd.notna(r.rank_screen) else ''} | {int(r.rank_smoke56v31) if pd.notna(r.rank_smoke56v31) else ''} | {short(r['flags'])} |")
    L.append("")
    r_ = imp[imp.ranked].copy(); r_["ao"] = r_.owen_max_eur.abs()
    L.append("### T2 按 Owen 分摊影响排序的前 10（可排序行；EUR 百万）\n")
    L.append("| # | 参数 | Owen 最大（国） | ΔZ(F1) | ΔB6 | B6 名次 | 标记 |")
    L.append("|---:|---|---|---:|---:|---:|---|")
    for i, r in r_.sort_values("ao", ascending=False).head(10).reset_index(drop=True).iterrows():
        L.append(f"| {i + 1} | `{r.param_id}` | {m(r.owen_max_eur)}（{r.owen_max_country}） | {m(r.dZ_F1)} | {m(r.dB6)} | {int(r['rank'])} | {short(r['flags'])} |")
    L.append("")
    fam = imp.copy(); fam["absB6"] = fam.abs_dB6.fillna(0); fam["absZ"] = fam.abs_dZ_max.fillna(0)
    fam["absB6r"] = fam.absB6.where(fam.ranked, 0.0)
    g = fam.groupby("family_201").agg(rows=("param_id", "size"), ranked=("ranked", "sum"), s=("absB6r", "sum"), mx=("absB6r", "max"), mz=("absZ", "max"),
                                      n10=("absB6r", lambda s: int((s >= 10e6).sum())))
    tot = fam[fam.ranked].absB6.sum()
    L.append("### T3 分族汇总（第 201 项分族；EUR 百万）\n")
    L.append("| 族 | 行数 | 可排序 | Σ\\|ΔB6\\| | 占比 | 最大 \\|ΔB6\\| | ≥ 10 M 的行 | 最大 \\|ΔZ\\| |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k, r in g.sort_values("s", ascending=False).iterrows():
        L.append(f"| {k} | {int(r.rows)} | {int(r.ranked)} | {m(r.s)} | {r.s / tot:.1%} | {m(r.mx)} | {int(r.n10)} | {m(r.mz)} |")
    L.append(f"| **合计** | {int(g.rows.sum())} | {int(g.ranked.sum())} | {m(tot)} | 100 % | | {int(g.n10.sum())} | |\n")
    cats = [("would_enter", "候选会进入（未建候选的进入缺口小于变动）"), ("large_change", "变动过大（一档 ≥ 50 % 作用在紧约束上、或 ≥ 20 % 的载体转移、或 |ΔCF/CF| > 20 %）"),
            ("investment_F1_F2_differs", "受影响的新增容量在 F1 / F2 相差 > 50 %"), ("bound_switch", "约束由紧变松或由松变紧"), ("degenerate", "零余量 / 退化对偶"),
            ("rank_unstable", "名次在另一组结果中进出前 30 的两倍"), ("not_representable", "网络中无对应候选"), ("scenario_choice", "情景选择（0→1）"),
            ("proxy", "用了代理价格或代理候选"), ("upper_bound", "上界估计"), ("new_resource", "网络中不存在的资源")]
    u = pd.read_csv(d / "UNRELIABLE_FIRST_ORDER.csv")
    L.append("### T4 不可靠一阶估计的类别（一行可有多个标记）\n")
    L.append("| 类别 | 行数 | 其中 TOP30 |")
    L.append("|---|---:|---:|")
    for k, z in cats:
        mm = u["flags"].fillna("").str.contains(k)
        L.append(f"| {z} | {int(mm.sum())} | {int((mm & (u['rank'] <= 30)).sum())} |")
    L.append(f"| 离散规则 / 开关（无一阶） | {int((u.mechanism == 'discrete').sum())} | 0 |")
    L.append(f"| **不可靠表合计** | {len(u)} | {int((u['rank'] <= 30).sum())} |\n")
    rem = pd.read_csv(d / "REMAINING_C_TREATMENT.csv")
    def grp(k):
        for pre, lab in [("|ΔB6| < 1", "\|ΔB6\| < 1 M EUR，影响小"), ("1–10", "1–10 M EUR，影响小"), ("10 M", "≥ 10 M EUR 但未进前 30"), ("需求侧", "需求侧（第 211 项，I2 已排）"),
                         ("主算中不起作用", "主算中不起作用（开关关闭、未被读取、退化区间等）"), ("离散", "离散规则 / 开关"), ("与 ", "与主参数同一机制（重复）"),
                         ("网络中没有", "网络中无对应候选（DATA_PENDING → p_nom_max 0）"), ("情景", "情景选择（0→1）")]:
            if k.startswith(pre):
                return lab
        return k[:40]
    rem["grp"] = rem.reason_key.map(grp)
    gg = rem.groupby("grp").agg(rows=("rows", "sum"), s=("sum_abs_dB6_meur", "sum"), mx=("max_abs_dB6_meur", "max"), sens=("suggested_sensitivity", "first")).sort_values("rows", ascending=False)
    L.append("### T5 其余 432 行的处理（`REMAINING_C_TREATMENT.csv` 按理由归并；EUR 百万）\n")
    L.append("| 理由 | 行数 | Σ\\|ΔB6\\| | 最大 \\|ΔB6\\| | 建议的敏感性处理 |")
    L.append("|---|---:|---:|---:|---|")
    for k, r in gg.iterrows():
        L.append(f"| {k} | {int(r.rows)} | {r.s:,.1f} | {r.mx:,.1f} | {r.sens} |")
    L.append("")
    L.append("### T6 TOP30 的升级路径（`W10_DOWNLOAD_CANDIDATES.csv` 摘要；来源全部 INFERENCE，待核实网址）\n")
    L.append("| # | 参数 | 现等级 → 可升级到 | 难度 | 主要候选来源（节选） |")
    L.append("|---:|---|---|---|---|")
    for _, r in dl.iterrows():
        segs = str(r.candidate_sources).split("；")
        cc = r.param_id.rsplit("_", 1)[-1] if r.param_id.rsplit("_", 1)[-1] in ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN") else ""
        pick = [x for x in segs if cc and (x.startswith(cc + " ") or x.startswith(cc + "：") or (" " + cc + " ") in x[:12])]
        src = (pick[0] if pick else segs[0])[:90]
        L.append(f"| {r['rank']} | `{r.param_id}` | {r.current_grade} → {r.target_grade} | {r.difficulty} | {src} |")
    L.append("")
    mech = inv.mechanism.value_counts()
    L.append("### T7 机制分布（462 行）\n")
    L.append("| 机制 | 行数 | 机制 | 行数 |")
    L.append("|---|---:|---|---:|")
    items = list(mech.items())
    for i in range(0, len(items), 2):
        a = items[i]; b = items[i + 1] if i + 1 < len(items) else ("", "")
        L.append(f"| `{a[0]}` | {a[1]} | {('`' + b[0] + '`') if b[0] else ''} | {b[1]} |")
    (d / "evidence" / "REPORT_TABLES.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)[:200])


if __name__ == "__main__":
    main()
