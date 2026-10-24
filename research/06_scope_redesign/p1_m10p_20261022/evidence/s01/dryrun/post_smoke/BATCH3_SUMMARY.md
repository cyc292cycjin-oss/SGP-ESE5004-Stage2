# 第三批汇总（M10P 运行脚本自动生成；只读，未调用求解器）

- 停批（分级停批规则，补充 01 第 2 项：任一运行 G2 不通过；R1、R2 无返回解或 C1 (a) 不通过）：无；安全停止：无
- 记为不可用、继续其余运行（R3–R11 无返回解 nosol 或 C1 (a) 不通过 c1a）：无

## 运行

| 运行 | 作用 | 档案 | 状态 | 终止 | 目标 bn | 求解 s | 峰值 GiB | C1 abc | C1 参照 | 重评次数 | GATES_V6 | 临时标签 | Owen 可用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | 本批参照（一体化）、Owen 分摊、c(N) | formal_barrier | ended | optimal | 307.8474 | 333 | 4.74 | 111 | batch | 1 | ACCEPTED_LAYER2 | ACCEPTED_LAYER2 | True |
| R2 | 本批参照（不互联）、B6 | formal_barrier | ended | optimal | 317.7460 | 333 | 4.38 | 111 | batch | 1 | ACCEPTED_LAYER2 | ACCEPTED_LAYER2 | True |
| R3 | 第二级容差验证，对 R1（第 127 项） | formal_barrier_1e6_t16 | not_started | — | — | — | — | — | — | — | — | — | None |
| R4 | 第二级容差验证，对 R2（第 127 项） | formal_barrier_1e6_t16 | not_started | — | — | — | — | — | — | — | — | — | None |
| R5 | 去 VN 复核（第 133、139 项） | formal_barrier | ended | optimal | 247.4429 | 369 | 4.33 | 111 | batch | 0 | ACCEPTED_LAYER2 | — | True |
| R6 | 去 TH 复核（第 133、139 项） | formal_barrier | ended | optimal | 274.7561 | 335 | 4.24 | 111 | batch | 0 | ACCEPTED_LAYER2 | — | True |
| R7 | 去 LA 复核（第 133、139 项） | formal_barrier | ended | optimal | 308.1878 | 318 | 4.42 | 111 | batch | 0 | ACCEPTED_LAYER2 | — | True |
| R8 | 敏感性 b1：禁止区内 CO2 跨境运输（第 132 项） | formal_barrier | not_started | — | — | — | — | — | — | — | — | — | None |
| R9 | 敏感性：不互联保留存量（第 132 项 2a） | formal_barrier | not_started | — | — | — | — | — | — | — | — | — | None |
| R10 | 敏感性：分国 WACC，一体化（第 132 项第 5 项） | formal_barrier | not_started | — | — | — | — | — | — | — | — | — | None |
| R11 | 敏感性：分国 WACC，不互联（第 132 项第 5 项） | formal_barrier | not_started | — | — | — | — | — | — | — | — | — | None |

## B6（R2 − R1）

- B6 = 9.8985 bn EUR2020（门槛 `B6_INTEGRATED_COST_NOT_ABOVE_DISCONNECTED`：True；标签 R1 ACCEPTED_LAYER2，R2 ACCEPTED_LAYER2）
- M12 受益与比例规则对照：B6 9.8985 bn；负受益 []（`M12_BENEFIT/`）

## 敏感性差额（新 − 基准；两边都非 NOT_ACCEPTED 才可用）

| 对比 | 内容 | 可用 | 目标差 bn | 相对 | 分国账本差 bn（11 国 + ASEAN） | Owen 对偶形式差 bn |
|---|---|---|---|---|---|---|
| R8 − R2 | b1：禁止区内 CO2 跨境运输（不互联） | False | 不可计算 | — | objective missing (run not finished or not solved) | — |
| R9 − R2 | 不互联保留存量 | False | 不可计算 | — | objective missing (run not finished or not solved) | — |
| R10 − R1 | 分国 WACC（一体化） | False | 不可计算 | — | objective missing (run not finished or not solved) | — |
| R11 − R2 | 分国 WACC（不互联） | False | 不可计算 | — | objective missing (run not finished or not solved) | — |
| R11 − R10 | 分国 WACC 下的 B6（信息项，不在事先登记的判定中） | False | 不可计算 | — | objective missing (run not finished or not solved) | — |

## 第二级比较与第四批档案（事先登记规则 3）

- 选择：**formal_barrier**；理由：candidate failed in at least one level-2 scenario -> profile A
- disconnected：C1 {'a': False, 'b': False, 'c': False}，目标相对差 —，通过 False
- integrated：C1 {'a': False, 'b': False, 'c': False}，目标相对差 —，通过 False

## 去一国检查（R1 = c(N)，R5–R7）

- 全部通过：True；不可分成本符号：positive

| 国 | 余量 bn | 容差 bn | 通过 | 市场形式通过 | 同档案 |
|---|---|---|---|---|---|
| LA | 0.8933 | 0.0142 | True | True | True |
| TH | 0.1866 | 0.0129 | True | True | True |
| VN | 1.1734 | 0.0100 | True | True | True |
