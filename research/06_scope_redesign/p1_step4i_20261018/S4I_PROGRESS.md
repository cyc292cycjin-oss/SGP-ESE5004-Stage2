# S4I 进度（第 103 项，上云前静态审查，只查不改）

分支 `codex/s4i-preflight-audit-20261018`（从 PR #32 的 `1545067b` 开出）。审查对象：S4H 部署包（代码 `6eead675`），`sha256sum -c SHA256SUMS` 15 个文件全部 OK。

| 节 | 状态 | 证据 | 提交 |
|---|---|---|---|
| A1 时间 | 已完成 | `evidence/static/S4I_STATIC_AUDIT.json` → `A1_time` | 6c88856f |
| A2 年化与成本 | 已完成 | `A2_costs`、`A2_cost_table_*.csv` | 6c88856f |
| A3 效率与出力 | 已完成（水电 / PHS / ror 明细证据已补） | `A3_efficiency_availability`；`evidence/followups/S4I_FOLLOWUPS.json` → `A6_details` | 6c88856f + 本次 |
| A4 拓扑 | 已完成 | `A4_topology` | 6c88856f |
| A5 需求 | 已完成（越南 Astar 残余证据已补） | `A5_demand`、`A5_demand_twh_*.csv`；`evidence/followups/A5_astar_residual.csv` | 6c88856f + 本次 |
| A6 可再生 | 已完成（现有陆上风电容量因子证据已补） | `A6_renewables`、`A6_cf_*.csv`；`A6_details.existing_onwind` | 6c88856f + 本次 |
| A7 松弛 | 已完成 | `A7_slack` | 6c88856f |
| A8 单位 | 已完成 | `A8_units` | 6c88856f |
| A9 净零 | 已完成 | `A9_carbon`、`A9_link_carbon_imbalance_*.csv` | 6c88856f |
| A10 情景差异 | 已完成 | `A10_scenario_differences` | 6c88856f |
| B1 `s_max_pu` / DC `p_max_pu` | 已完成 | `B_transmission` | 6c88856f |
| B2 输送损耗 | 已完成 | `followups/S4I_FOLLOWUPS.json` → `B2`；`B2_cross_border_losses_by_component.csv` | 本次 |
| B3 长度系数与海底份额 | 已完成（交流线、DC、H₂、CO₂ = 1.25；成本 = PyPSA-Eur 公式，比值 1.0） | `B3` | 本次 |
| B4 其他设置 | 已完成（TH–MY 直流单向且受 2,000 MW B2B 限制；线损选项 0 vs 2） | `B4` | 本次 |
| C 求解注意事项 | 已完成（基尔霍夫跨度、截断网络 LP 系数统计、`SOLVER_NOTES.md`） | `C_kvl_span`；`evidence/lp/C_LP_RANGES_*_56.json`；`SOLVER_NOTES.md` | 本次 |
| D 联盟算力 | 部分（383 个连通联盟已核实；估算未开始） | `D_coalitions` | — |
| 报告与交付 | 未开始 | — | — |

**恢复点：** D（`s4i_coalition_estimate.py`）→ 报告（`S4I_REPORT.md`、`S4I_EVIDENCE.json`）→ draft PR。A3/A5/A6 补证据与 B2–B4 由同一脚本 `s4i_followups.py` 一次写出，故合并为一次提交。

**说明：** 中断前在临时目录写的辅助脚本（水电明细、越南电力扣减）已随临时目录清空；其结论只在会话中出现过，现以正式脚本 `scripts_project/s4i_followups.py` 重算并写入证据文件。
