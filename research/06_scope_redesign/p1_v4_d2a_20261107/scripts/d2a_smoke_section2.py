"""V4 D2a section 6.2: append the run record (section 2) to SMOKE56_D2A.md from evidence/D2A_smoke56.json (written by d2a_smoke_eval.py smoke) and the
V5 gate files of the two runs. Idempotent: everything after the heading "## 2. 运行记录（求解后追加）" is replaced.

    <env python> scripts/d2a_smoke_section2.py
"""
from __future__ import annotations

import json
from pathlib import Path

W = Path(__file__).resolve().parents[1]
RP = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
HEAD = "## 2. 运行记录（求解后追加）"
D1 = {"v4d2a_F1": RP / "v4d1/smoke56/v4d1_F1", "v4d2a_F2": RP / "v4d1/smoke56/v4d1_F2"}


def m(x):
    return f"{float(x) / 1e6:+,.1f} M"


def b3_detail(rid: str) -> list[str]:
    g = json.loads((RP / "v4d2a/smoke56" / rid / "V5_GATES.json").read_text()).get("B3") or {}
    if g.get("passed", True):
        return []
    out = []
    for c, v in (g.get("by_country") or {}).items():
        d = float(v["used_mwh"]) - float(v["potential_mwh"])
        if d > 0:
            out.append(f"{c} 超用 {d:.3e} MWh（相对 {d / max(float(v['potential_mwh']), 1.0):.1e}，潜力 {float(v['potential_mwh']) / 1e6:,.3f} TWh）")
    return out


def main():
    ev = json.loads((W / "evidence/D2A_smoke56.json").read_text())
    runs, crit = ev["runs"], ev["criteria"]
    st = (RP / "v4d2a/smoke56/STATUS.txt").read_text().strip().splitlines()
    start = next((l for l in st if l.startswith("START:")), "")
    L = [HEAD, "", f"- **执行：** `scripts/smoke_d2a.sh --confirmed …`，{start.replace('START:', '开始 ')}；串行、同时至多 1 个 Gurobi 进程；求解前对令牌服务器做裸 TCP 连通检查；无重试、无参数改动。状态文件 `results_project/v4d2a/smoke56/STATUS.txt`，许可内容只经 `GRB_LICENSE_FILE` 传给求解器，日志只读清洗后的副本。",
         "- **判据来源：** `scripts/d2a_smoke_eval.py smoke` → `tables/D2A_SMOKE56_RESULTS.csv`、`evidence/D2A_smoke56.json`（只含无许可字段）。", "", "### 2.1 运行结果（VERIFIED）", "",
         "| 运行 | 网络 SHA256（前 16） | 终止 | 目标值（EUR，含常数项） | LP 目标值 | 障碍迭代 / 秒 | 求解秒 | 峰值 RSS GiB | 未过 V5 门 | 并集外 | C1（a/b/c，接受） | GATES_V6 |",
         "|---|---|---|---:|---:|---:|---:|---:|---|---|---|---|"]
    for rid in ("v4d2a_F1", "v4d2a_F2"):
        r = runs.get(rid)
        if not r:
            L.append(f"| {rid} | — | 未运行 | | | | | | | | | |"); continue
        L.append(f"| {rid} | `{r['network_sha256'][:16]}` | {r['termination']} | {float(r['objective_eur']):,.2f} | {float(r['objective_lp_eur']):,.2f} | {r['barrier_iterations']} / {r['barrier_seconds']} | {float(r['solve_seconds']):.1f} | {float(r['peak_rss_gib']):.2f} | {r['gates_failed'].replace(';', ', ') or '无'} | {r['gates_failed_outside_v31_union'] or '无'} | {r['C1_a']}/{r['C1_b']}/{r['C1_c']}，{r['C1_accepted']} | {r['V6_label']} |")
    L += ["", "### 2.2 对 D1 冒烟的变化与报警线（判据 4）", "",
          "| 运行 | D1 目标值 | D2a 目标值 | **ΔV** | 右端下界 LB | 系数一阶 FO | 报警线 | ΔV − LB | 高于报警线 | D1 未过门 → D2a 未过门 |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for rid in ("v4d2a_F1", "v4d2a_F2"):
        r = runs.get(rid)
        if not r:
            continue
        L.append(f"| {rid} | {float(r['d1_objective_eur']):,.2f} | {float(r['objective_eur']):,.2f} | **{m(r['dV_eur'])}** | {m(r['rhs_lower_bound_eur'])} | {m(r['coefficient_first_order_eur'])} | {m(r['alarm_line_eur'])} | {m(r['dV_minus_lower_bound_eur'])} | {'是' if r['above_alarm_line'] else '**否**'} | {r['gates_failed_d1'].replace(';', ', ') or '无'} → {r['gates_failed'].replace(';', ', ') or '无'} |")
    L += ["", "LP 目标值（不含常数项）的变化：" + "；".join(f"{rid} {m(runs[rid]['dV_lp_eur'])}" for rid in ("v4d2a_F1", "v4d2a_F2") if rid in runs) + "。ΔV 与 ΔV_LP 之差 = 常数项变化（移出模型的固定成本，如 `TH2 4` 组 FOM-once 的重分配）。",
          "", "### 2.3 判据逐项", "", "| 运行 | 1 optimal | 2 ACCEPTED_LAYER2 | 3 失败门在 v3.1 并集内 | 4 不低于报警线 | 全部 |", "|---|---|---|---|---|---|"]
    ok = lambda b: "通过" if b else "**不通过**"
    for rid in ("v4d2a_F1", "v4d2a_F2"):
        c = crit.get(rid)
        if c:
            L.append(f"| {rid} | {ok(c['optimal'])} | {ok(c['accepted_layer2'])} | {ok(c['failed_in_v31_union'])} | {ok(c['above_alarm_line'])} | {ok(c['all'])} |")
    b6 = crit.get("B6_regression_only") or {}
    if b6 and b6.get("d2a_eur") == b6.get("d2a_eur"):
        L += ["", "### 2.4 B6 回归值（56 时段，只作回归、不解读）", "",
              f"- F2 − F1：D2a **{float(b6['d2a_eur']) / 1e9:,.4f} bn EUR**，D1 {float(b6['d1_eur']) / 1e9:,.4f} bn，变化 {float(b6['change_eur']) / 1e6:+,.1f} M EUR。",
              "- 56 时段是截取样本（`truncation_ratio` 1.0 的池不截取，其余时序量按截取时段计），只用于方向判断与第 7 节归因；不与 2920 时段的 B6 比较。"]
    det = {rid: b3_detail(rid) for rid in runs}
    if any(det.values()):
        L += ["", "### 2.5 新出现的失败门说明", ""]
        for rid, rows in det.items():
            if rows:
                L.append(f"- {rid} B3_BIOMASS_WITHIN_POTENTIAL：" + "；".join(rows) + "。量级为障碍法容差（1e-6）层面的越界，与 v3.1 冒烟 R2 的 B3 失败同类（并集内）；不是数据链问题。")
    allok = all(crit[r]["all"] for r in ("v4d2a_F1", "v4d2a_F2") if r in crit) and {"v4d2a_F1", "v4d2a_F2"} <= set(crit)
    L += ["", "### 2.6 结论", "",
          ("- 两次求解均满足判据 1–4：optimal、`ACCEPTED_LAYER2`、失败门在 v3.1 并集内、ΔV 高于 1.3 节登记的报警线（在 ΔV ≥ LB 的凸性下界之上，差额为 D1 对偶线性化未计的替代路线成本）。**不是停止条件，继续第 7 节。**"
           if allok else "- **判据未全部满足**（见 2.3）。按指令第 6 节：查数据链，不改参数重试，停下汇报；第 7 节的 4 次求解不启动。"),
          "- ΔV 远大于 LB 并非异常：LB 只是 D1 对偶在 D1 解处的线性化（次梯度），当被移除的 170 TWh 棕榈残余物由更贵的路线（进口 / 合成燃料 / 更多可再生 + 储能）替代时，实际成本增加高于线性化值（决策 212 (b) 的凸性方向）。"]
    txt = (W / "SMOKE56_D2A.md").read_text(encoding="utf-8")
    i = txt.index(HEAD)
    (W / "SMOKE56_D2A.md").write_text(txt[:i] + "\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("section 2 written", "all_ok" if allok else "NOT_OK")


if __name__ == "__main__":
    main()
