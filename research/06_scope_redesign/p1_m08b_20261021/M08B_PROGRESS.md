# M08B 进度（随进度更新）

- 指令：`M08B_CLAUDE_CODE_INSTRUCTION.md` v1，SHA256 `dde52c9284eb1fa9767a6f059d425bd6658e926891de3ce189e0905e6b7059b2`（与 `M08B_INSTRUCTION_SHA256.txt` 一致，2026-10-21 核对）。
- 边界：不连云；本机 56×3h 冒烟（Gurobi）须在第 4 节另行取得用户授权；单元测试中的 scipy / HiGHS 玩具 LP 允许。
- 工作树：`/home/jin/wt_m08b_20261021`，分支 `codex/m08b-demand-20261021`（自 M08a 头 `820c2cae`，PR #45）。M12 会话可能并行，各用独立 worktree。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| 1 | 开分支 / worktree；M11 台账草稿并入总台账（用户选择：标"无项号"、按时间插在 M08a 前） | 完成 | 见 git log |
| B1 | 需求锚定（活动量、基础负荷、交通服务量、工业物理产量） | 未开始 | |
| B2 | 工业有用热三档与生物质溢出 | 未开始 | |
| B3 | 注册表 16 行 + 新规则行；单元测试；`tests/research` 全量 | 未开始 | |
| 3 | 重建四个网络、变体生成测试、静态检查、对比报告、网络 SHA256 | 未开始 | |
| 4 | 本机冒烟（须用户授权） | 未授权 | |
| 5 | 交付 | 未开始 | |

## 接续点

- 当前：第 1 节完成，下一步代码探查（`d1_demand_2050.py`、`s3_0_industry.py`、`s2_layers.py`、`build_research_network.py`、`configs/research/baseline.yaml`）。
