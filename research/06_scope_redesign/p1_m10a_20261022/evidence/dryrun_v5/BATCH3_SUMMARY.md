# 第三批汇总（M10P 运行脚本自动生成；只读，未调用求解器）

- 停批（分级停批规则，补充 01 第 2 项：任一运行 G2 不通过；R1、R2 无返回解或 C1 (a) 不通过）：无；安全停止：无
- 记为不可用、继续其余运行（R3–R11 无返回解 nosol 或 C1 (a) 不通过 c1a）：无
- 后处理步骤异常或超时（M10A；只记录，不改变调度；可用 `POST_ONLY=1` 补做）：无

## 运行

| 运行 | 作用 | 档案 | 状态 | 终止 | 目标 bn | 求解 s | 峰值 GiB | C1 abc | C1 参照 | 重评次数 | GATES_V6 | 临时标签 | Owen 可用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | 本批参照（一体化）、Owen 分摊、c(N) | formal_barrier | built_stopped_before_solve | stopped_before_solve | — | — | 10.11 | — | — | — | — | — | None |
| R2 | 本批参照（不互联）、B6 | formal_barrier | built_stopped_before_solve | stopped_before_solve | — | — | 10.06 | — | — | — | — | — | None |
| R3 | 第二级容差验证，对 R1（第 127 项） | formal_barrier_1e6_t16 | built_stopped_before_solve | stopped_before_solve | — | — | 10.12 | — | — | — | — | — | None |
| R4 | 第二级容差验证，对 R2（第 127 项） | formal_barrier_1e6_t16 | built_stopped_before_solve | stopped_before_solve | — | — | 9.99 | — | — | — | — | — | None |
| R5 | 去 VN 复核（第 133、139 项） | formal_barrier | built_stopped_before_solve | stopped_before_solve | — | — | 10.00 | — | — | — | — | — | None |
| R6 | 去 TH 复核（第 133、139 项） | formal_barrier | built_stopped_before_solve | stopped_before_solve | — | — | 10.06 | — | — | — | — | — | None |
| R7 | 去 LA 复核（第 133、139 项） | formal_barrier | built_stopped_before_solve | stopped_before_solve | — | — | 10.09 | — | — | — | — | — | None |
| R8 | 敏感性 b1：禁止区内 CO2 跨境运输（第 132 项） | formal_barrier | built_stopped_before_solve | stopped_before_solve | — | — | 7.70 | — | — | — | — | — | None |
| R9 | 敏感性：不互联保留存量（第 132 项 2a） | formal_barrier | built_stopped_before_solve | stopped_before_solve | — | — | 9.94 | — | — | — | — | — | None |
| R10 | 敏感性：分国 WACC，一体化（第 132 项第 5 项） | formal_barrier | built_stopped_before_solve | stopped_before_solve | — | — | 10.17 | — | — | — | — | — | None |
| R11 | 敏感性：分国 WACC，不互联（第 132 项第 5 项） | formal_barrier | built_stopped_before_solve | stopped_before_solve | — | — | 9.97 | — | — | — | — | — | None |

## B6（R2 − R1）

- 不可计算（R1 或 R2 无目标值）

## 敏感性差额（新 − 基准；两边都非 NOT_ACCEPTED 才可用）

| 对比 | 内容 | 可用 | 目标差 bn | 相对 | 分国账本差 bn（11 国 + ASEAN） | Owen 对偶形式差 bn |
|---|---|---|---|---|---|---|
| R8 − R2 | b1：禁止区内 CO2 跨境运输（不互联） | False | 不可计算 | — | objective missing (run not finished or not solved) | — |
| R9 − R2 | 不互联保留存量 | False | 不可计算 | — | objective missing (run not finished or not solved) | — |
| R10 − R1 | 分国 WACC（一体化） | False | 不可计算 | — | objective missing (run not finished or not solved) | — |
| R11 − R2 | 分国 WACC（不互联） | False | 不可计算 | — | objective missing (run not finished or not solved) | — |
| R11 − R10 | 分国 WACC 下的 B6（信息项，不在事先登记的判定中） | False | 不可计算 | — | objective missing (run not finished or not solved) | — |

## 第二级比较与第四批档案（事先登记规则 3）

- 选择：**—**；理由：—

## 去一国检查（R1 = c(N)，R5–R7）

- 不可计算或未运行：无去一国结果
