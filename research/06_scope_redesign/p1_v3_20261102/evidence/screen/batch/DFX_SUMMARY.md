# DFX 365×24h 筛查汇总（run_dfx.sh 自动生成；只读，未调用求解器）

- 停批（RUN_PLAN_DFX 3.3：任一运行 G2 不通过；V1 / V2 无返回解或 C1 (a) 不通过）：无；安全停止：无
- 后处理步骤异常或超时（只记录，不改变调度；可用 `POST_ONLY=1` 补做）：无

## 运行

| 运行 | 作用 | 档案 | 状态 | 终止 | 目标 bn | 求解 s | 峰值 GiB | C1 abc | C1 参照 | 重评次数 | GATES_V6 | 临时标签 | Owen 可用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V1 | 本批参照（v3 一体化）、Owen 分摊 | formal_barrier_1e6_t16 | ended | optimal | 263.5966 | 3255 | 25.10 | 111 | batch | 1 | ACCEPTED_LAYER2 | ACCEPTED_LAYER2 | True |
| V2 | 本批参照（v3 no_new_xb）、B6 = V2 − V1 | formal_barrier_1e6_t16 | ended | optimal | 277.9447 | 1137 | 19.49 | 111 | batch | 1 | ACCEPTED_LAYER2 | ACCEPTED_LAYER2 | True |
| V3 | 存量与专线的价值 = V3 − V2（第 174 项） | formal_barrier_1e6_t16 | ended | optimal | 279.0895 | 1476 | 20.76 | 111 | batch | 0 | ACCEPTED_LAYER2 | — | True |
| V4 | 修订桥：第 160–162 项 | formal_barrier_1e6_t16 | ended | optimal | 271.2321 | 4693 | 25.18 | 111 | batch | 0 | ACCEPTED_LAYER2 | — | True |
| V5 | 修订桥：第 160–164 项 | formal_barrier_1e6_t16 | ended | optimal | 268.7261 | 3561 | 24.60 | 111 | batch | 0 | ACCEPTED_LAYER2 | — | True |

## B6（V2 − V1）

- B6 = 14.3481 bn EUR2020（门槛 `B6_INTEGRATED_COST_NOT_ABOVE_DISCONNECTED`：True；标签 V1 ACCEPTED_LAYER2，V2 ACCEPTED_LAYER2）
- M12 受益与比例规则对照：B6 14.3481 bn；负受益 ['BUNKER']（`M12_BENEFIT/`）

## 修订桥与存量价值（只描述）

| 步骤 | 总成本变化 bn |
|---|---:|
| v2 -> 160-162 | +0.4468 |
| 160-162 -> 160-164 | -2.5060 |
| 160-164 -> all | -5.1295 |

- 完全隔离 − `no_new_xb`（存量与专线的价值）：1.1448 bn；v2 B6 14.6153 bn

## 与第三批及一阶预测的对比（只描述，不作验收依据；RUN_PLAN_DFX 3.4 第 5–6 项；主参照 R3 / R4 同档案 optimal，R1 / R2 并列）

- 未提供第三批参照文件（`--reference`）
