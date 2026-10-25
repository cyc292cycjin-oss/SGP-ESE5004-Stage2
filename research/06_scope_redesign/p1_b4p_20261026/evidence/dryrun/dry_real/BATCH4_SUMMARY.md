# 第四批汇总（run_batch4.sh 自动生成；只读，未调用求解器）

- 停批（RUN_PLAN_B4 3.5）：F1；安全停止：无；不可用：F1（nosol）
- 后处理步骤异常或超时（只记录；`POST_ONLY=1` 补做）：无
- P1 探针：{"parallel": false, "peak_gib": null, "threshold_gib": 4.276, "cores": 25, "reason": "window not covered"}
- 早期测速：{"F1": null, "F2": null}

## 运行

| 运行 | 作用 | 档案 | 状态 | Gurobi 状态 | 终止 | 迭代 | 目标 bn | 求解 s | 求解进程峰值 GiB | Gurobi MaxMemUsed GB | C1 abc | GATES_V6 | 求解后异常 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F1 | 一体化 2920×3h：c(N)、Owen 分摊、B6 基准 | formal_barrier_1e6_t16 | ended | — | none | — | — | — | 2.13 | — | 000 | NOT_ACCEPTED | 无 |
| F2 | 不互联 2920×3h：B6 = F2 − F1 | formal_barrier_1e6_t16 | ended | — | optimal | — | 317.7460 | 333 | 4.38 | — | — | — | 无 |

## B6（F2 − F1）与 Owen 对偶形式受益

- 不可计算（F1 或 F2 无目标值）

## 与第三批 365×24h 同名结果的对比（只描述，分辨率影响的证据；不判定）

- 未提供第三批导出目录（--batch3），或 F1 / F2 未完成
