# Phase5 readiness — 当前索引（Gate6 Baseline 准备后）

2026-10-08。当前准备结果来自 GATE6_3H_NO_SOLVER_TESTS、3h 来源审计与 DEC 逐项证据，不把 mock 或文件检查当作完整模型结果。原版本已逐字保存在 gate6_baseline/PHASE5_READINESS_BEFORE_GATE6_PREPARATION.md；旧 closeout 文档没有改写。

Baseline 与 DEC 均为已冻结研究情景；本轮仅准备 Baseline 全年 3h 验证。首轮正式比较仍是同一区域 Full-SC Integrated/Disconnected，仅改变规定跨境 AC/DC，非电物理/外部商品/区域政策保持一致，不拆分 11 国。DEC 的两个方法家族不阻断 Baseline 本地准备。

| 状态 | 值 |
|---|---|
| GATE5_CLOSED | YES |
| BASELINE_AND_DEC_RETAINED | YES |
| GATE6_BASELINE_INPUT_IDENTITY | PASS |
| GATE6_3H_RUNNER_IMPLEMENTED | YES |
| GATE6_3H_NO_SOLVER_TESTS | PASS |
| GATE6_3H_ROUNDING_AUDIT | PASS |
| CLOUD_INPUT_SYNC | NOT_RUN |
| CLOUD_NO_SOLVER_TESTS | NOT_RUN |
| DEC_ATTRIBUTION_REVIEW | COMPLETE |
| DEC_POLICY_READY | NO |
| DEC_PENDING_DECISIONS | F1: 200项共享H2生产、混合、储存与用途归属; F2: 其中100项SMR CC捕集转移、FT利用与回排归属；与F1重叠，不增加项目数 |
| RESOURCE_AND_COST_BUDGET_APPROVED | NO |
| FULL_GATE6_OPTIMIZATION_MODEL_BUILT | NO |
| NEW_SOLVER_CALLS | 0 |
| NEW_PRESOLVE_CALLS | 0 |
| GATE6_SOLVE_AUTHORIZED | NO |
| GATE6_SOLVE_STATUS | NOT_RUN |
| FORMAL_PHASE5_RUNS | 0 |
| INTEGRATED_RUNS | 0 |
| DISCONNECTED_RUNS | 0 |

Gate5 成功与失败/恢复历史均保留；807 未知固定项和 200 政策权重保持 null，已知 FOM 只计一次；FullSystemCostComplete/FullSystemEmissionsComplete/scientific_results_allowed 仍 false。没有预先宣称未知项在场景间抵消。

后续最少条件：用户准备继续时开机；已提交代码与五个实际输入及必要测试依赖核 SHA、云端同一无求解测试、新鲜 cgroup 资源预检；明确币种/数据盘费用并接受资源/时间/成本方案；另行明确 Gate6 完整构模或一次求解授权。DEC 正式启用另需接受 F1/F2 方法并完成对应实现测试。正式 Integrated/Disconnected 和 Phase5 仍须以后单独授权。

当前 local/remote HEAD、clean、push 见 GATE6_GIT_STATE.json；源码测试绑定提交 4db99a6f098fec954e7d30ec13c4c5b313ff3ea1。当前 cloud HEAD 未测，最后已知 2970979645380a8505076910bf1af227d2a5632c。用户要求保持云端关机。

详细文档：gate6_baseline/GATE6_BASELINE_PREPARATION.md、CURRENT_DECISION_INDEX.json、DEC_ATTRIBUTION_REVIEW.md、GATE6_RESOURCE_AND_COST_PROPOSAL.md。停止在人工审阅；没有授权文件或自动下一轮。
